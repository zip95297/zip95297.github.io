---
title: "回顾overlap实现细节"
date: 2026-02-08 04:04:42
updated: 2026-02-08 04:04:42
mathjax: true
tags: 
    - 深度学习
categories: 深度学习
comments: false
---
normalLoop 全部都在 EngineStream 上面完成

```python
# scheduler 里面 这个是纯在 engine Stream 里面完成
def normal_loop(self) -> None:
	# 没有可以执行的请求就 block
	blocking = not (self.prefill_manager.runnable or self.decode_manager.runnable)
	for msg in self.receive_msg(blocking=blocking):
		# 处理 发送过来的消息 CPU 处理新请求 
		self._process_one_msg(msg)

	forward_input = self._schedule_next_batch()
	ongoing_data = None
	if forward_input is not None:
		# GPU 推理
		ongoing_data = (forward_input, self._forward(forward_input))

	# 处理结果并发回
    self._process_last_data(ongoing_data)
```

# OVERLAP

```python
class Scheduler :
	def __init__() :
		self.engine = Engine()
        self.stream = torch.cuda.Stream(device=self.device)
        self.engine_stream_ctx = torch.cuda.stream(self.engine.stream)
        torch.cuda.set_stream(self.stream)

class Engine :
	def __init__() :
		self.stream = torch.cuda.Stream()
		torch.cuda.set_stream(self.stream)
```

Q1 ： 为什么是 `self.eng_stream_ctx = torch.cuda.stream(self.engine.stream)` 而不是 `= self.engine.stream`
因为 `torch.cuda.stream(stream)` 返回的不是 Stream，而是一个上下文管理器（Context Manager）它不是流本身，而是用来切换流作用域的工具，这样封装了 ctx 之后 有 `__enter__ & __exit__` 用于切入切出流，相当于 `with torch.cuda.stream(self.engine.stream) : `


run_forever
```python
# Scheduler 里面
@torch.inference_mode()
def run_forever(self) -> NoReturn:
	# normal
	if ENV.DISABLE_OVERLAP_SCHEDULING:
		with self.engine_stream_ctx: # 进入 engine stream 的上下文
			self.engine.stream.wait_stream(self.stream) # 同步一次
			while True: # 之后的操作在 engine stream 上完成
				self.normal_loop() # 整个操作都在 engine stream 上
	else:
		assert torch.cuda.current_stream() == self.stream
		data = None
		while True:
			data = self.overlap_loop(data) # 只有 推理在 engine stream 上，其他操作 在 self.stream 上
```

OVERLAP_LOOP
```python
def overlap_loop(self, last_data: ForwardData | None) -> ForwardData | None:
	# 只有 没上个结果 prefill 和 decode 都没有需要执行的请求时候才 block
	blocking = not (
		last_data is not None
		or self.prefill_manager.runnable
		or self.decode_manager.runnable
	)
	for msg in self.receive_msg(blocking=blocking):
		self._process_one_msg(msg)

	forward_input = self._schedule_next_batch()
	ongoing_data = None
	if forward_input is not None:
		with self.engine_stream_ctx:  # run the batch in the engine's stream
			self.engine.stream.wait_stream(self.stream)
			ongoing_data = (forward_input, self._forward(forward_input))
	
	self._process_last_data(last_data)
	return ongoing_data
```

参考normal，loop中 流程如下： 
1. CPU Msg&Sch -> ForwardData 
2. GPU Forward -> ForwardOutput
3. Process

但是会 出现 CPU 在等带 GPU 计算的情况 时延很大（GPU 计算利用率很低），如何解决这个时延？
 
 在 GPU 的角度上，GPU 在 forward 之后产生了 ForwardOutput ，这是 只需要把 结果交给 CPU 处理，自己可以计算下一个Batch

 但是显然这样的方式存在两个  Read After Write 数据竞争！！！ 
 1. GPU 必须要等待 CPU Msg&Sch 过后 才能够进行计算
 2. process last data 必须要等待 GPU 完成了对上一个结果的写入 才能够计算。

## RAW1 CPU-GPU

我们先梳理一下 一次loop中发生了什么: 
1. schedule_next_batch 中 
	- PrefillManager DecodeManager : 选择被调度的 Req 包装成一个 Batch
	- prepare_next_batch : 根据 Req 完成了 pageTable，inputids，positions 等 GPU tensor的写入
		类似于这样： 其中一个例子
		`mapping_host = torch.tensor(mapping_list, dtype=torch.int64, pin_memory=True)`
		`return mapping_host.to(device, non_blocking=True)` 也就是现在 CPU 创建 然后非阻塞传输到 GPU 上 这样的话 CPU 完全不等待 CPU 和 GPU 的传输
		to 底层调用的是这个 cudaMemcpyAsync

看来如果 如果在 overlap  `with self.engine_stream_ctx:`  中 直接 `ongoing_data = (forward_input, self._forward(forward_input))` 可能会导致 GPU 计算 使用了还没准备好的 forward_input ，所以要等待，怎么等待呢？

`cpu_tensor.to(device, non_block=True)` 发生了什么？在当前 CUDA Stream 里发射了一条 GPU 异步拷贝命令（H2D DMA）

所以在 GPU 执行流里面，我们要让GPU等待 CPU数据prepare 流的完成，等待方式有：
1. torch.cuda.synchronize() 这个是全局的 GPU 同步 GPU 到达一个状态之前一直block，这个调用是向所有GPU 发射同步指令 要求每个GPU 所有流里面的 指令全部 执行完之后才能继续执行。
2. 在 self.steam 里面创建一个event，然后调用 event.record() （在流中打一时间戳）然后 event.synchronize() 这个也会用到。【这种方式怎么保证 record 和 nonblock copy是同步顺序发生的？copy也就是 to nonblocking 相当于在 stream 里发射了一个命令，然后record也是发射了一个命令，自然就保证了顺序性。 】
3. self.engine.stream.wait_stream(self.stream) 就是让GPU执行流 等 CPU处理流完成才能继续 然是这个是非阻塞的 往 GPU 推理流中发射 wait 指令。

到此为止，我们解决了 第一个 RAW 数据竞争，那么第二个呢？

## RAW2 GPU-CPU

我们也先来分析一下 foward 里面发生了什么，forward 中计算出了 next_token_gpu 然后用 类似上面的方式完成 D2H 传输 `next_token_gpu.to('cpu',non_blocking=True)` 但是如果 D2H 传输还没结束，已经走到了下一个 loop 的 process 就会导致 RAW 数据冒险，那么我们如何解决这个冒险呢？

自然想到 像前面的方式 waitStream 但是 不妨推理一下，如果我们使用了 `self.stream.wait_stream(self.engine.stream)` 会发生什么，我们首先明确一点，此时的 engine stream 里面 指令队列中 包含了 当前batch的计算 也就是下个 loop 才会处理，如果在这里wait 就会让 处理上一个 func 干等到这一个batch 也计算出来，就没法做到 process last data 和 GPU 计算的 overlap了。

所以 我们考虑 在 GPU 完成计算以及 D2H transport 之后 加入一个 时间戳，然后 在process 的时候就等待 这个时间戳 同步就可以，也就是 在forward to device nonblocking 之后 加一个 copy_done_event=torch.cuda.Event() copy_done_event.record() 然后将 这个 event 随这个 forward output 一起返回就可以了。然后在 process last data中 用 copy_done_event.synchronize() 就消除了这个 数据冒险。

到最后 消除 两个 RAW 的代码 like this :
```python
def overlap_loop(self, last_data: ForwardData | None) -> ForwardData | None:
	# 只有 没上个结果 prefill 和 decode 都没有需要执行的请求时候才 block
	blocking = not (
		last_data is not None
		or self.prefill_manager.runnable
		or self.decode_manager.runnable
	)
	for msg in self.receive_msg(blocking=blocking):
		self._process_one_msg(msg)

	forward_input = self._schedule_next_batch() # 这里面 有 H2D copy RAW1
	ongoing_data = None
	if forward_input is not None:
		with self.engine_stream_ctx:  # run the batch in the engine's stream
			self.engine.stream.wait_stream(self.stream) # 非阻塞等待第一个 copy完成 消除 RAW1 
			ongoing_data = (forward_input, self._forward(forward_input)) # 这里面 有 D2H copy RAW2
			# 在 _forward 的return中 打包 copy_done_event 一起 return 返回的是张量引用和event
	
	self._process_last_data(last_data) # copy_done_event.synchronize() 阻塞等待 D2H copy 完成 消除 RAW2
	return ongoing_data
```

至此 实现了 CPU GPU overlap 以及 两个相关的数据冒险。

## 状态一致

但是 这样的实现，显然出现了 调度当前Batch（ Sch N+1） 发生在处理上一个Batch （ Process N） 之前

我们来看一下 N 号 batch的周期 
1. Sch N -> Compute N -> Process N-1
2. Sch N+1 -> Compute N+1 -> Process N
我们发现 Schedue N+1 的时候 N 还没有被 Process，一个req 可能在 Compute N 时候就已经 EOS 了，但是又被错误的 Schedule 一次 ，所以我们在 process 的时候 检查 req 还有没有在 decode set里面 如果在才 free source（free slot & cache_req），discard From Decoding Set。

## 补充 Gemini

在操作系统中，常规内存是 Pageable（可分页）的，操作系统随时可能将其换出到磁盘。GPU 的 DMA（直接内存访问）控制器无法直接从 Pageable 内存中安全地拉取数据，因为物理地址可能会变。

当调用 cudaMemcpyAsync 复制 Pageable 内存时：
CUDA 驱动会偷偷在主机端分配一块临时的 Pinned Memory 缓冲区，先由 CPU 将数据同步复制到这个缓冲区，然后再启动 DMA 异步传输。这个 CPU 复制过程是同步阻塞的，破坏了 CPU/GPU Overlap。

当你调用 .to(device, non_blocking=True) 时：
PyTorch 做了严格的限制。它会先检查源 Tensor 是否在 Pinned Memory 中（即 tensor.is_pinned() 是否为 True）。
是 Pinned Memory：PyTorch 调用 cudaMemcpyAsync，立即返回，CPU 继续执行下一行代码。
不是 Pinned Memory：PyTorch 直接忽略 non_blocking=True 参数，调用同步的 cudaMemcpy（或表现为同步的行为），CPU 卡死在这里等待数据传输完成。

代码示例与后果：

```Python
# 错误做法（无异步效果）
host_tensor = torch.randn(1024, 1024) # 默认分配在 Pageable 内存
# 这里的 non_blocking=True 是无效的，CPU 会在这里被阻塞，直到传输完成
gpu_tensor = host_tensor.to('cuda', non_blocking=True) 

# 正确做法（实现真正的 Overlap）
host_tensor = torch.randn(1024, 1024).pin_memory() # 显式分配为锁页内存
# CPU 瞬间返回，真正触发底层的 cudaMemcpyAsync
gpu_tensor = host_tensor.to('cuda', non_blocking=True) 
```

流（Stream）的管理逻辑
cudaMemcpyAsync 强制要求你管理流。你必须告诉它这个传输任务扔进哪个 GPU 硬件队列：
cudaMemcpyAsync(dst, src, size, cudaMemcpyHostToDevice, stream)

PyTorch 的 .to(non_blocking=True) 屏蔽了流参数，它会自动获取当前上下文的流。
如果你在 Overlap 调度中，希望在背景流进行数据准备，必须配合上下文管理器：

```Python
# 假设 self.stream 是专门用于数据传输的背景流
with torch.cuda.stream(self.stream):
    # PyTorch 会捕获 self.stream，底层调用 cudaMemcpyAsync(..., self.stream.cuda_stream)
    forward_input.input_ids = host_input_ids.to(device, non_blocking=True)
```

# overlap 通信冲突

GPU 在运行的时候 占用了 NCCL 通信，Msg&Sch 的处理 也需要 CPU tensor 传递保证信息同步，用了Gloo Tensor 的 cpu 通信 
torch distribute 建立 进程通信组的时候 仅 指定握手 地址。gloo 简历 C(4,2) 个 tcp 链接

nccl 通过 tcp 握手 传递元信息，然后 数据交换 几乎不通过 内核态 走 PCIE NVLINK

为什么用 gloo 而不是 shm ？

