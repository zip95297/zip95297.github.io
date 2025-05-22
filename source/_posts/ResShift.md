---
title: "ResShift 论文阅读"
date: 2025-05-15 20:04:50
updated: 2025-05-15 20:05:12
mathjax: true
tags: 
    - 深度学习
    - 超分重建
    - 论文阅读
    - Diffusion
categories: 深度学习
comments: false
---
# ResShift

## Motivation

主要想法：缩短马氏链，加速反向传播过程

传统的方法是：从高斯分布中采样 Pure Noise 然后逐步 reverse 得到 一个图像。

主要问题都是 沿用了 原本 DDPM 中的马氏链 （太长，从 pure noise 开始还原）导致要经过很多次迭代才能 生成出一张图片。而且 reverse 过程过长 还会导致 生成的图像过于平滑。
（？可能是因为 纹理细节被当做噪声给 过滤掉 ？ 如何 balance 高频 和 噪声？）
（？多次经过 diffusion 的reverse 相当于 过了很多次低通滤波？ ）

> One common approach involves inserting the LR image into the input of current diffusion model. and retraining the model from scratch on the training data for SR. 一种方法是 把 LR 插入到输入中 （在Google的Image Super-Resolution via Iterative Refinement ）论文中 将 Pure Noise 和 LR concat 然后在 Unet 中 做 reverse

> Another popular way is to use an unconditional pre-trained diffusion model as a prior and modify its reverse path to generate the expected HR image. 通过 LR 引导 反向过程 ，类似于 LDM 中的 Attn 的作用，但是也是从 Pure Noise 开始的

在 超分 任务中 目标是生成 HR ， 有先验数据 LR 。通过利用 LR 来得到 生成的HR图像，来缩短马氏链：类似于 直接截断  Pure Noise -> LR（这个LR 不直接是 LR 而是马氏链中接近的一个 节点） ，从 LR 开始进行 reverse 得到 HR。

## 前向过程

记：
	HR 为 $x_0$  ， LR 为 $y_0$ ，两者之间距离 Error 为 $e_0$ 

论文 的 核心想法 是：transit from $x_0$ to $y_0$ by gradually shifting their residual $e_0$ through a Markov chain with length T. 

参数序列 $\{\eta_t\}^T_{t-1}$ 随 t 单调增，t=1 时$\eta=0$，t=T 时$\eta=1$

逐步加噪：
$$
q(x_t\mid x_{t-1},y_0)=N(x_t;x_{t-1}+\alpha_te_0,k^2\alpha_tI)
$$
其中 $\alpha_t=\eta_t-\eta_{t-1}$ , $k$ 用来控制方差。通过逐步加噪的公式(正态分布可加性)可得到：（论文中证明任意步长t的边际分布解析可积）

一步加噪：
$$
q(x_t\mid x_0,y_0) = N(x_t;x_0+\eta_t e_0,k^2\eta_t I)
$$
## 反向过程

$$
p(x_0\left|y_0\right.)=\int p(x_T\left|y_0\right.)\prod_{t=1}^Tp_\theta\left(x_{t-1}\left|x_t\right.,y_0\right.)dx_{1:T}
$$
在这个 式子中 $p(x_T\left|y_0\right.)\approx N(x_T\left|y_0\right.,k^2I)$ , $p_\theta\left(x_{t-1}\left|x_t\right.,y_0\right.)$ 是 diffusion模型 其中 $\theta$ 就是可学习参数。

反向过程 的目的就是为了 估计 给出 $y_0$ 为条件 的 $x_0$ 的后验分布。

其中的 $x_T$ 在这个里就是 加噪T步 的图像，整个过程就是从 $x_t$ 还原到 $x_0$ 

## 参数的优化

根据 扩散模型文献中 的假设 $p_\theta$ 为：
$$
p_{{\theta}}({x}_{t-1}|{x}_t,{y}_0)={N}({x}_{t-1};{\mu}_{{\theta}}({x}_t,{y}_0,t),{\Sigma}_{{\theta}}({x}_t,{y}_0,t))
$$

优化目标就是，最小化证据下界：
$$
\min_{{\theta}}\sum_tD_{{KL}}\left[q({x}_{t-1}|{x}_t,{x}_0,{y}_0)\|p_{{\theta}}({x}_{t-1}|{x}_t,{y}_0)\right]
$$

其实就是让模型 **预测的** 前一时刻 图像 靠近 **真实的**前一时刻图像的 分布。

反向过程和参数的优化和传统的 Diffusion 几乎没什么区别

##  噪声策略 Noise Schedule

根据前项过程的式子可以看出，噪声的方差由 $\kappa\sqrt{\eta_T}$ 控制 。在LDM中提到第一步加噪的方差应该足够小（e.g., 0.04 in LDM），从而确保 $q(x_1|x_0,y_0)\approx q(x_0)$ ， $\eta_T$ 应该尽可能接近1 （前向过程中的均值）。所以文中的 $\eta_T$ Schedule 如下：
	当T=1 时： $\eta_1=min((\frac{0.04}{k})^2,0.001)$
	当 $T\in[2,T-1]$ , $\sqrt{\eta_t} = \sqrt{\eta_1} \times b_0^{\beta_t}$ , $\beta_t= (\frac{t-1}{T-1})^p \times (T-1) , b_0=exp[\frac{1}{2(T-1)}log \frac{\eta_T}{\eta_1}]$   ，p 是超参数

 

# 代码中的细节

[ResShift Repo](https://github.com/zsyOAOA/ResShift) 原文仓库在此处

用了 VQ-VAE 作为 autoencoder

LPIPS 通常是一个训练好的 感知相似度模型 一个计算相似度的方法

UNetModelSwin 用这个作为 diffusion model 

## 数据

### 训练数据

训练时候用的 256x256的 HR 图像 根据 LDM 从 ImageNet 的训练集中随机裁剪出，然后使用 RealESRGAN 的 退化流程 合成的 LR 图像。

![](https://cdn.jsdelivr.net/gh/zip95297/zip95297.github.io@main/source/images/ResShift/Pasted%20image%2020250515211826.webp?raw=true)

### 测试数据

基于常用退化模型合成了一个测试数据集，用了 ImageNet中取3000张，还有RealSR，和自己收集的

## 模型

使用 Unet 作为 Diffusion 的网络结构，用 Swin Transformer 块儿  替换 UNet中的 自关注层 
