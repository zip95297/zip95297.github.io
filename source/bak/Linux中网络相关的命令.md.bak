---
title: "Linux中网络相关的命令"
date: 2025-05-07 20:51:47
updated: 2025-05-07 20:59:43
tags: 
    - 网络
    - 常用软件
    - 终端工具
categories: 终端相关
comments: false
---
# 写在前面

目前用到的有：
- ping
- ifconfig
- curl
- netstat
- nc
- route
- lsof

软件：
- frp
- chisel
- rsync & scp
- proxychains

# 命令介绍

## route

如果有多张网卡启用：
- en0 wifi 
- en12 有线宽带

使用这个命令添加路由：使 向 10.10.5.4 的流量 走 10.11.3.254 网关 gate_way
```shell
sudo route -n add 10.10.5.4 10.11.3.254
```

查看路由表：[netstat](#netstat)

## netstat

查看路由表：
```shell
netstat -rn
```

## lsof

查看端口被哪个进程占用：
```shell
lsof -i :<port>
```

## curl

几个好用的URL：
- cip.cc
- ifconfig.me
- ipinfo.io


## nc

