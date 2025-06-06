---
title: "Kitty 终端模拟器"
date: 2025-05-04 05:16:18
updated: 2025-05-04 05:16:34
tags: 
    - 常用软件
    - 终端模拟器
    - kitty
categories: 终端相关
description: kitty 是一个特别好用的终端模拟器 之前用的是iTerm2 换成kitty后更好用了！
comments: true
---
# 写在前面

最近在用 kitty 终端 在研究怎么把它配置的更好用，dotfile打包到github上面 ，挂一个官方链接：[Kitty](https://sw.kovidgoyal.net/kitty/) 。 引用一篇写的很好的 博客 [BLOG](https://www.escapelife.site/posts/8e342b57.html)

> Warning:
	在配置mapping时候某个键不生效 检查一下是不是 后面的配置覆盖了的问题

如果在 source 时候 exit 1 可以用 `bash -x ~/.bashrc` 或者 `zsh -x ~/.zshrc` 进入debug

# Kitty - GPU 加速的终端

## kitten copyboard

可以在所有服务器上面 `alias copy='kitten copyboard'` 然后就可以像 pbcopy 一样使用，具体请参阅官方文档 ： [kitten clipboard](https://sw.kovidgoyal.net/kitty/kittens/clipboard/)

一些常用用法：

```shell
# Copy an image to the clipboard:
kitten clipboard picture.png

# Copy an image and some text to the clipboard:
kitten clipboard picture.jpg text.txt

# Copy text from STDIN and an image to the clipboard:
echo hello | kitten clipboard picture.png /dev/stdin

# Copy any raster image available on the clipboard to a PNG file:
kitten clipboard -g picture.png

# Copy an image to a file and text to STDOUT:
kitten clipboard -g picture.png /dev/stdout

# List the formats available on the system clipboard
kitten clipboard -g -m . /dev/stdout
```

