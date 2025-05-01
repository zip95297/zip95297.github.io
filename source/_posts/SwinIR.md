---
title: SwinIR 代码阅读
date: 2025-03-16 15:32:09
updated: 2025-04-30 00:42:24
mathjax: true
tags: 
    - 深度学习
    - ViT
    - SwinTransformer
categories: 深度学习
description: 阅读SwinIR论文，在BasicSR详细阅读了一下SwinIR的代码
---


# pipeline

输入x = \[ B, C, H, W\]
## ClassicSR  (pixcelShuffle)
 
### 1.ConvFirst： 仅仅提高输入的纬度 （也是浅层特征提取 UpSample

先用一个卷积`Conv2d(in_C,emd_dim,3,1,1)` 把输入通道数（一般是3）扩到embedding的channel 得到` embedding` 在这个过程中 输入图像的H, W都没有变化 `embedding` 大小为  \[B, emd_dim, H, W\]

### 2. ForwardFeature

```python
def forward_features(self, x):
	x_size = (x.shape[2], x.shape[3])
	x = self.patch_embed(x)
	if self.ape:
		x = x + self.absolute_pos_embed
	x = self.pos_drop(x)
	for layer in self.layers:
		x = layer(x, x_size)
	x = self.norm(x) # b seq_len c
	x = self.patch_unembed(x, x_size)
	return x
```
#### 1)PatchEmbedding
先将x后两个维度展平 \[B,emd_dim,H,W\] $\rightarrow$ \[B,emd_dim,H\*W\]  
然后将第1个和第二个纬度交换位置 即\[B,H\*W, emd_dim]  

如果有的话 用 [[torch#nn. LayerNorm (embedding_dim)|nn.LayerNorm]] 对 x 做归一化

```python
def forward(self, x):
	x = x.flatten(2).transpose(1, 2) # b Ph*Pw c
	if self.norm is not None:
		x = self.norm(x)
	return x
```

然后对 x 做 [[torch#Dropout|Dropout]] 

#### 2) Transformer Layer （**Residual Swin Transformer Block**）
通过 设置个数 层layer 每层layer 是一个 **Residual Swin Transformer Block**
RSTB 由 一个 BasicLayer 作为主要部分 ，还有一些对数据流残差链接 以及卷积的基本模块
对于BasicLayer中有depth个 **SwinTransformerBlock** 
输入到这一层的 x 的 shape 是 \[ B, H\*W, emd_dim]
##### ResidulSwinTranformerBlock - RSTB

一层 layer 包括 一个 RSTB ，在RSTB中：
1. x = basicLayer(x)  
2. x = patch_unembed(x)
3. x = conv(x)
4. x = patch_embed(x)
###### BasicLayer
一个BL中有depth个 SwinTransformerBlock 在通过这些 SwinTransformerBlock 前后 x 的shape不发生改变
###### PatchUnEmbeded
在PatchEmbed中\[ B,  C, H, W] 的 张量 被 patchEmbed 为 \[ B, H\*W, emd_dim] 这一步是将这个张量重新view成 \[ B,  emd_dim, H, W] 的形状来做下一步卷积
```python
def forward(self, x, x_size):
	x = x.transpose(1, 2).view(x.shape[0], self.embed_dim, x_size[0], x_size[1])
	return x
```

#### 3）UnEmbeded
对经过了注意力的 x LN之后 重新转换成 \[ B,  emd_dim, H, W]  这个形状

### 3. 残差链接

在 \[1.ConvFirst] 中将原本的3通道图像转换成了 60通道 
在 \[2.ForwardFeature] 中的transformer 依旧保持 60通道以及输入大小

将 \[1.ConvFirst] 与 \[2.ForwardFeature] 的输出相加
张量的大小依然是 \[B, emd_dim, H, W\]

然后将残差链接后的 x 在进行一次卷积，这个卷积的定义如下：
```python 
if resi_connection == '1conv':
	self.conv_after_body = nn.Conv2d(embed_dim, embed_dim, 3, 1, 1)
elif resi_connection == '3conv':
	# to save parameters and memory
	self.conv_after_body = nn.Sequential(
		nn.Conv2d(embed_dim, embed_dim // 4, 3, 1, 1),  
		nn.LeakyReLU(negative_slope=0.2, inplace=True),
		nn.Conv2d(embed_dim // 4, embed_dim // 4, 1, 1, 0), 
		nn.LeakyReLU(negative_slope=0.2, inplace=True),
		nn.Conv2d(embed_dim // 4, embed_dim, 3, 1, 1)
		)
```

这个卷积起到了局部特征融合的作用

第二种方式增加了模型的非线性建模能力：
1. 第一个 3×3 卷积：降维到 embed_dim // 4（压缩通道）
2. 中间 1×1 卷积：保持通道数不变（增加非线性建模能力）
3. 最后一个 3×3 卷积：恢复通道到原始 embed_dim

### 4. UpSample

下面是关于pixelShuffle的一些函数定义
```python
self.conv_before_upsample = nn.Sequential(
	nn.Conv2d(embed_dim, num_feat, 3, 1, 1), nn.LeakyReLU(inplace=True)
)
self.upsample = Upsample(upscale, num_feat)
self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
```

在上采样之前 先做一个卷积和ReLU，然后进行上采样：
```python
class Upsample(nn.Sequential):
"""上采样模块
Args:
scale (int): 缩放因子。支持的缩放因子：2^n和3
num_feat (int): 中间特征的通道数
"""
def __init__(self, scale, num_feat):
	m = []
	if (scale & (scale - 1)) == 0: # scale = 2^n
		for _ in range(int(math.log(scale, 2))):
			# 先变深再 pixelshuffle
			m.append(nn.Conv2d(num_feat, 4 * num_feat, 3, 1, 1))
			m.append(nn.PixelShuffle(2))
	elif scale == 3:
			m.append(nn.Conv2d(num_feat, 9 * num_feat, 3, 1, 1))
			m.append(nn.PixelShuffle(3))
	else:
		raise ValueError(f'scale {scale} is not supported.\
						 Supported scales: 2^n and 3.')
	super(Upsample, self).__init__(*m)
```
先变深再[[torch#PixelShiffle|PixelShuffle]] 和下面轻量SR的很像 区别在于 对于scale = 2**n 这个逐步2倍放大，这一步仅仅把特征图的HW对其为scale之后的 但是通道数并没有对齐，之后还要再用一个卷积，达到目标通道数3
```python
self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
```

而下面LWSR的是 一步直接上采样到目标的通道数 pixelshuffle之后直接是目标图像


##  LightWeightSR   (pixcelShuffleDirect)

### 1.ConvFirst： 仅仅提高输入的纬度 （也是浅层特征提取 UpSample

先用一个卷积`Conv2d(in_C,emd_dim,3,1,1)` 把输入通道数（一般是3）扩到embedding的channel 得到` embedding` 在这个过程中 输入图像的H, W都没有变化 `embedding` 大小为  \[B, emd_dim, H, W\]

### 2. ForwardFeature

```python
def forward_features(self, x):
	x_size = (x.shape[2], x.shape[3])
	x = self.patch_embed(x)
	if self.ape:
		x = x + self.absolute_pos_embed
	x = self.pos_drop(x)
	for layer in self.layers:
		x = layer(x, x_size)
	x = self.norm(x) # b seq_len c
	x = self.patch_unembed(x, x_size)
	return x
```
#### 1)PatchEmbedding
先将x后两个维度展平 \[B,emd_dim,H,W\] $\rightarrow$ \[B,emd_dim,H\*W\]  
然后将第1个和第二个纬度交换位置 即\[B,H\*W, emd_dim]  

如果有的话 用 [[torch#nn. LayerNorm (embedding_dim)|nn.LayerNorm]] 对 x 做归一化

```python
def forward(self, x):
	x = x.flatten(2).transpose(1, 2) # b Ph*Pw c
	if self.norm is not None:
		x = self.norm(x)
	return x
```

然后对 x 做 [[torch#Dropout|Dropout]] 

#### 2) Transformer Layer （**Residual Swin Transformer Block**）
通过 设置个数 层layer 每层layer 是一个 **Residual Swin Transformer Block**
RSTB 由 一个 BasicLayer 作为主要部分 ，还有一些对数据流残差链接 以及卷积的基本模块
对于BasicLayer中有depth个 **SwinTransformerBlock** 
输入到这一层的 x 的 shape 是 \[ B, H\*W, emd_dim]
##### ResidulSwinTranformerBlock - RSTB

一层 layer 包括 一个 RSTB ，在RSTB中：
1. x = basicLayer(x)  
2. x = patch_unembed(x)
3. x = conv(x)
4. x = patch_embed(x)
###### BasicLayer
一个BL中有depth个 SwinTransformerBlock 在通过这些 SwinTransformerBlock 前后 x 的shape不发生改变
###### PatchUnEmbeded
在PatchEmbed中\[ B,  C, H, W] 的 张量 被 patchEmbed 为 \[ B, H\*W, emd_dim] 这一步是将这个张量重新view成 \[ B,  emd_dim, H, W] 的形状来做下一步卷积
```python
def forward(self, x, x_size):
	x = x.transpose(1, 2).view(x.shape[0], self.embed_dim, x_size[0], x_size[1])
	return x
```

#### 3）UnEmbeded
对经过了注意力的 x LN之后 重新转换成 \[ B,  emd_dim, H, W]  这个形状

### 3. 残差链接

在 \[1.ConvFirst] 中将原本的3通道图像转换成了 60通道 
在 \[2.ForwardFeature] 中的transformer 依旧保持 60通道以及输入大小

将 \[1.ConvFirst] 与 \[2.ForwardFeature] 的输出相加
张量的大小依然是 \[B, emd_dim, H, W\]

然后将残差链接后的 x 在进行一次卷积，这个卷积的定义如下：
```python 
if resi_connection == '1conv':
	self.conv_after_body = nn.Conv2d(embed_dim, embed_dim, 3, 1, 1)
elif resi_connection == '3conv':
	# to save parameters and memory
	self.conv_after_body = nn.Sequential(
		nn.Conv2d(embed_dim, embed_dim // 4, 3, 1, 1),  
		nn.LeakyReLU(negative_slope=0.2, inplace=True),
		nn.Conv2d(embed_dim // 4, embed_dim // 4, 1, 1, 0), 
		nn.LeakyReLU(negative_slope=0.2, inplace=True),
		nn.Conv2d(embed_dim // 4, embed_dim, 3, 1, 1)
		)
```

这个卷积起到了局部特征融合的作用

第二种方式增加了模型的非线性建模能力：
1. 第一个 3×3 卷积：降维到 embed_dim // 4（压缩通道）
2. 中间 1×1 卷积：保持通道数不变（增加非线性建模能力）
3. 最后一个 3×3 卷积：恢复通道到原始 embed_dim

### 4. UpSampleOneStep (为了节省参数 在 LightWerightSR 中 用 OneStep)

经过残差相加之后，张量大小保持为 \[B, emd_dim, H, W]，接下来通过 UpsampleOneStep 模块进行上采样以恢复图像的原始分辨率。该模块的设计目标是**参数量小、结构简单、适用于轻量化模型**，整体包括：

1. 一个 Conv2d 层：将 emd_dim 通道映射到 (scale_factor^2) × num_out_ch 通道。(OneStep的体现)

2. 一个 [[torch#PixelShiffle|PixelShuffle]] 层：把通道还原为输出图像的通道数，并进行空间上采样。

```python
class UpsampleOneStep(nn.Sequential):
"""UpsampleOneStep模块（与Upsample的区别在于它总是只有1conv + 1pixelshuffle）
用于轻量级SR以节省参数
Args:
scale (int): 缩放因子。支持的缩放因子：2^n和3
num_feat (int): 中间特征的通道数
"""
def __init__(self, scale, num_feat, num_out_ch, input_resolution=None):
	self.num_feat = num_feat
	self.input_resolution = input_resolution
	m = []
	m.append(nn.Conv2d(num_feat, (scale**2) * num_out_ch, 3, 1, 1))
	m.append(nn.PixelShuffle(scale))
	super(UpsampleOneStep, self).__init__(*m)
