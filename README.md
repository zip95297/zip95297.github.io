# Zip95297's Homepage with Hexo and Obsidian

# 工具

## Note Application

Obsidian

## hexo

用了github deploy action  之后有时间可以做一个帮助大家一键部署的脚本 或者 可以直接参考官方文档自己来

## utils

由于本地笔记仓库ObsidianNote中有一些不想 post 上来 所以做了一些小工具联动  
通过这种方式 我就可以在本地 写一篇文章 并不把 任何附件上传 只 post 我想公开的记录  
或者对于已经有 obsidian 通过这些命令进行 homepage 的推送

在obsidian中 一篇笔记的结构如下：
```shell
√ -> zjb @ 课程笔记 % tree 随机过程及其应用
随机过程及其应用
├── 随机过程及其应用.md
└── img
    ├── Pasted image 20241227212820.png
    └── Pasted image 20241227213221.png
```

所以 当我准备post一篇来自 Obsidian 仓库中的文章 时，做如下操作：  
1. 复制 `{name}.md` 文件 到 `source/_post` 目录
2. 复制 `{name}/imgs` 目录 到 `source/images/{name}` 目录
3. [x] 对 复制过来的 `{name}.md` 添加 笔记头文件 记录：推送时间、分类、tag ...
4. [x] 对 复制过来的 `{name}.md` 中的 `![[{URL}]]` 进行格式替换  
  说明： 用当前仓库中的 `source/images` 当做图床 然后在 [Github CDN](https://www.jsdelivr.com/github) 对这个仓库进行加速，并且通过 `utils/chURL` 对url格式进行替换
5. [x] 用 `ffmpeg` ?之类的对 images 中的图片资源进行压缩 （因为github中一个仓库的大小限制是1G 单个文件限制是 10MB）
  最后选择用的是 cwebp
6. [x] 一键部署 当前的本地仓库 push & github actions

计划将 1-5 步 做成交互式的脚本 在 `utils` 中，在 tui 中选择要 post 的 ObsidianNoteDir

部署步骤分离出来

# 其他

最近事情有点多 之后在写 shell 做吧

# 使用方法

现在已经写完了为了方便自己记忆 写下使用方法 （因为当时写的时候忘记统一路径格式。。。以后一定要注意）

- ./post
  交互式在 ObsidianNote 中选择要推送的笔记 （要求笔记的附件 imgs or img 在同目录下）
- utils/addAttribute : 给一个笔记添加属性
  直接在根目录中: zjb—blog % `utils/addAttribute ./source/_posts/first.md`
  到post中(可以自动补全): _posts % `../../utils/addAttribute first.md `
- utils/chURL ： 把 md 笔记中的 ObsidianNote \!\[\[\]\]  转换为 CDN 加速后的图床 地址
  直接在根目录中: zjb—blog % `utils/chURL 随机过程及其应用.md`
  到post中(可以自动补全): _posts % `../../utils/chURL SwinIR.md`
- utils/cleanBAK : 清理 chURL 时候的备份文件
  在任意位置
- utils/deploy: push 到 github 仓库 （自动执行 github action ）
  这个就在根目录zjb-blog用吧
- utils/extractIMG 压缩图像
  可以在根目录 ：zjb-blog % `utils/extractIMG profile`
  在 source/images 里面用： images % `../../utils/extractIMG profile`
- utils/list\* : 在任何位置
  \*=Post 显示 所有推送的笔记
  \*=Obsidian 显示 Obsidian 中的笔记
- utils/rmPost :
  这个填的是 没有后缀的(防止误删 自己打吧) `utils/rmPost -n|--note <md file name without .md>`
- utils/post_cli :
  Usage: utils/post_cli -n|--note <md file path> [-i|--img <image file path>]
  后面的用绝对路径吧还是

忘记怎么用可以只输个命令 会有 `usage` 