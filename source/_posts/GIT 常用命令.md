---
title: "GIT 常用命令"
date: 2025-05-02 04:20:18
updated: 2025-05-02 04:25:00
tags: 
    - GIT
    - 常用软件
    - 终端命令
categories: 终端相关
comments: false
---
# 写在前面

`git` 作为 版本管理软件 还是很常用的 但是感觉每次要用什么的时候都不太熟练 还要麻烦去查 所以记录一下常用的 如果以后还有的话继续补充 。

目前我常用的命令主要分为 [本地](#本地命令) 和 [远程](#远程命令) ，还有一些在新设备上的 [配置](#配置命令) 命令 这个就放在最后 使用频率很低。

---
# 本地命令

## git-add

`add` 就是把 本地的 文件修改 添加到 暂存区（stage），只是加到暂存区 还没有 `commit` 就没有添加到版本库 没有提交的 `commit id` ，stage 如果不想要了可以用 [reset](#git-reset) 恢复。
```shell
git add .
git add <filename>
git add -p # 这个是交互式 添加文件的部分到 stage
```
还有一个 把本地和远程仓库连接起来的在 [add remote](#git-add-remote) 
## git-commit

`commit` 就是把 stage 中的修改 提交到 本地 版本库 中。
```shell
git commit -m "commit msg"
git commit --amend # 修改上一次的提交信息 把新的更改 合并到上一次提交
```

## git-checkout

`checkout` 用于 对 分支 的操作：切换分支
```shell
# 切换到 branch 分支上
git checkout <branch>

# 撤销 仓库中 被追踪（不包括新建的文件）文件的修改（无论有没有 add）
git checkout . 

# 创建一个新分支并立即切换到该分支
git checkout -b <new-branch>
```

创建并且切换
```shell
git checkout -b <new-branch>
```

把文件切换到 指定的 commit-id 的状态 这个可以用 [diff](#git-diff)
```shell
git checkout <commit-hash> -- <file-path>
```

## git-branch

`git branch` 用于查看、创建或删除分支:
```shell
# 查看本地所有分支
git branch

# 查看本地和远程的所有分支
git branch -a

# 查看本地分支及其最新提交
git branch -v

# 查看分支的详细信息（包括分支的最后一次提交、状态等）
git branch -vv

# 创建一个新分支，但不切换
git branch <new-branch>

# 创建一个新分支并立即切换到该分支
git checkout -b <new-branch>

# 删除本地分支
git branch -d <branch>  # 删除已合并的分支
git branch -D <branch>  # 强制删除未合并的分支

# 重命名当前分支
git branch -m <new-branch>

# 查看分支之间的差异
git diff <branch1> <branch2>
```

## git-log

`git log` 用于查看提交历史。列出从当前分支的最新提交开始，按时间倒序排列的所有提交记录。可以查看每个提交的详细信息，提交哈希、作者、日期以及提交信息。
```shell
# 查看当前分支的提交历史
git log

# 查看简洁的提交历史（只显示提交哈希和提交信息）
git log --oneline

# 显示提交历史，并且包括每个提交的修改差异
git log -p

# 查看某个特定文件的提交历史
git log <file-path>

# 查看某个范围内的提交记录，比如最近10个提交
git log -n 10

# 查看某个作者的提交历史
git log --author="author-name"

# 查看某个提交后所有的提交记录
git log <commit-id>..
```


## git-diff

`git diff` 用于查看工作区、暂存区与版本库之间的差异。它可以帮助你在提交之前查看文件修改内容，或者查看某次提交和当前工作区的区别。
```shell
# 查看工作区和暂存区之间的差异 就是上次 add 之后又改了什么
git diff

# 查看暂存区和最近一次提交之间的差异（ add 比 上次 commit 改了什么
git diff --cached

# 查看工作区与某次提交之间的差异 
git diff <commit-id>

# 查看两个提交之间的差异
git diff <commit-id-1> <commit-id-2>

# 查看某个文件的差异
git diff <file-path>

# 查看某个文件在暂存区和当前工作区的差异
git diff <file-path> --cached
```

## git-status

查看当前 仓库  状态：分支 有哪些 更改 暂存 未被追踪
```shell
git status
```

## git-reset

`reset` 用于撤销提交和修改 重置 stage 或者当前分支，下面这种 `HEAD~1` 的用法 就是上一个 commit ， 也可以直接用 `commit-id` 回退到指定版本
```shell
# 撤销 当前 branch 的最后一次 commit 和 add， commit 还是修改过的
git reset HEAD~1 # 这个就是 --mixed

# 撤销最后一次 commit ，add 还在，文件修改也还在
git reset --soft HEAD~1

# 撤销 commit 和 add 恢复文件到上个状态 ！！！会把文件修改也给删掉
git reset --hard HEAD~1 
```

## git-merge

合并分支到当前分支 ：
```shell
# 把指定 branch 的 提交 合并到当前的 分支
git merge <branch>

# 如果有无法解决的冲突 就放弃合并
git merge --abort

# 非快进合并，将合并历史记录保留下来，方便回溯
git merge --no-ff <branch>
```

## git-rebase

把一个分支的修改应用到另一个分支
```shell
# 将 当前分支 的提交 应用到 指定分支 branch 上，达到合并的效果，但不会生成多余的合并提交。
git rebase <branch>

# 当 rebase 中遇到 冲突 并解决后，继续rebase
git rebase --continue

# 取消 rebase 恢复到 rebase 之前的状态
git rebase --abort
```

---
# 远程命令
## git-add-remote

`git add remote` 用于将远程仓库链接到本地仓库，以便可以推送和拉取代码。每个远程仓库会有一个名字（通常为 `origin`），可以通过这个命令将本地仓库与远程仓库建立连接。`name` 一般是 `origin`
```shell
# 添加远程仓库
git remote add <name> <url>

# 查看远程仓库信息
git remote -v

# 修改远程仓库的 URL
git remote set-url <name> <new-url>

# 移除远程仓库
git remote remove <name>
```

## git-push

`git push` 用于将本地的提交推送到远程仓库。默认情况下，`git push` 会将当前分支的提交推送到远程仓库中对应的分支。
```shell
# 将本地的当前分支推送到远程仓库的相应分支
git push

# 将本地的指定分支推送到远程仓库
git push <remote> <branch>
git push origin main
# 第一次要加上 -u 参数 --set-upstream
# 将本地分支与远程分支建立跟踪关系。-u 后 origin/main 就和本地 main 关联了
# 之后就可以直接 git push / pull

# 强制推送，覆盖远程仓库的历史
git push --force

# 推送所有本地分支
git push --all
```

## git-pull

`git pull` 用于从远程仓库拉取最新的更改并自动合并到本地分支。它实际上是 `git fetch` 和 `git merge` 的组合，先拉取远程的更改，再将其合并到当前分支。
```shell
# 从远程仓库拉取当前分支的最新提交并合并
git pull

# 拉取并合并指定分支的更改
git pull <remote> <branch>

# 只拉取远程仓库的更新，不进行合并
git pull --no-merge

# 拉取并与当前分支重新合并（常用于避免合并提交）
git pull --rebase
```


---
# 配置命令

git 的 下载 [Download git](https://git-scm.com/downloads)

版本检查：
```shell
git --version
```

## git-config

列出当前的 config 信息：
```shell
git config --list
```

设置 **全局** 信息 ，第三个是对 git 设置全局代理 ：
```shell
git config --global user.name "zip95297"
git config --global user.email "zip95297@gmail.com"
git config --global http.proxy socks5://127.0.0.1:7890 
```
 这个代理端口的位置 要查看科学上网的 开放端口，或者 科学上网软件 打开了允许局域网连接 也可以用 局域网中开了代理的设备（一般用于服务器）

对某一个仓库设置信息（需要在 仓库目录 下使用）：
```shell
git config --local user.name "zip95297"
git config --local user.email "zip95297@gmail.com"
```

还有一个 `init.defaultbranch` 的变量记得设置为 main （好像下载之后就会有这个）

配置对 `github.com` 的 ssh 连接，之后就可以用 ssh 的 URL 访问了：
```shell
ssh-keygen -t rsa -C "zip95297@gmail.com" # 创建 公私钥 对
# 然后在 github > settings > ssh and gpg keys 中添加自己的公钥，之后测试链接就通了
√ -> zip @ ~ % ssh -T git@github.com                                          
Hi zip95297! You've successfully authenticated, but GitHub does not provide shell access.
```
