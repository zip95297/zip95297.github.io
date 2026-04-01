---
title: "MacOS&Linux中的工具"
date: 2026-1-02 04:14:55
updated: 2026-1-02 04:14:55
mathjax: true
tags: 
    - 终端工具
    - 常用软件
categories: 实用技巧
comments: false
---
# 一些 CLI 小工具

* [x-cmd](https://cn.x-cmd.com/start/)
* **proxychains**: 用于代理 CLI 中的命令。在 Clash 中如果不打开增强模式，CLI 中的应用流量不会被代理，使用 proxychains 可以为 CLI 应用添加代理。注意：在 macOS 中，由于 SIP（系统完整性保护），`/usr/bin` 中的命令行程序并不会被代理。在局域网中，proxychains 的 `ip:port` 配置可以是一个开了允许局域网连接的代理设备上的代理端口。
* **bat**: `cat` plusplus，可以用 `-l` 参数指定语法。
* **btop**: TUI top 软件。
* **ranger**: CLI 中的文件 explorer。
* **yazi**: 比 ranger 更好用，功能更丰富。
* **eza**: 可以显示 Nerd Font 的 `ls` 工具，可以用 `alias` 替代 `ls`, `ll`, `la` 等。
* **fastfetch**: 展示系统的一些信息。
* **fzf**: 模糊搜索 (fuzzyfind)。可以配合管道交互式查找，如果仅输入 `fzf` 则是查找文件。
* **starship**: 用于配置 SHELL PROMPT。
* **zoxide**: 比 zsh plugin 的 jump 更好用的快速跳转。
* **thefuck**: 输错命令了可以 `fuck` 一下自动纠正。
* **ncdu**: 用于查看目录中项目的大小。
* **tldr**: `man` 手册的易读版本。
* **tmux**: 终端复用工具，无须多言。
* **neovim**: `vim` plus plus。
* **tree**: 树状展示目录结构。
* **sshfs**: 挂载远程目录。
* **sudo cupsctl WebInterface=yes**: 打开 Command Line 打印的网页接口。
* **pgrep**: 专门查进程的 grep，例如 `pgrep -au zjb frp`。
* **ffmpeg**: 音视频处理工具。
* **7-zip (sevenzip)**: 压缩工具。安装：`brew install 7-zip`，用法：`7zz`。
* **d (mac 自带)**: 先用 `d` 列出来最近访问的文件夹，输入前面的数字进入该文件夹。
* **where / which**: 查找命令路径。
* **whence -v / type**: 显示函数在哪个文件。
* **iperf3**: 用于测试网速的小工具。

### Zsh 配置参考

**插件配置 (`~/.zshrc`)**:
```sh
plugins=(
  git
  web-search
  zsh-autosuggestions
  sudo
  # autojump
  autoupdate
  zsh-syntax-highlighting
)
```

**Prompt 与耗时统计配置**:
```bash
source $ZSH/oh-my-zsh.sh
  
export PS1="%(?.%F{green}√.%F{red}?%?)%f -> zjb @ %B%F{white}%1~%f%b %# "
export RPROMPT="%*"
  
# 记录命令开始时间（毫秒）
preexec() {
  timer_start=$(perl -MTime::HiRes=time -e 'printf("%.0f\n", time * 1000)')
}
  
# 命令执行后计算耗时并更新右提示符
precmd() {
  if [[ -n "$timer_start" ]]; then
    local timer_end=$(perl -MTime::HiRes=time -e 'printf("%.0f\n", time * 1000)')
    local elapsed=$((timer_end - timer_start))
    elapsed=$((elapsed-21))
    local mins=$((elapsed / 60000))
    local secs=$(( (elapsed % 60000) / 1000 ))
    local ms=$((elapsed % 1000))
    
    local duration=""
    [[ $mins -gt 0 ]] && duration+="${mins}m "
    [[ $secs -gt 0 ]] && duration+="${secs}s "
    [[ $ms -gt 0 ]] && duration+="${ms}ms"
    
    if [[ -n "$duration" ]]; then
      RPROMPT="%(?.%F{green}󱄛 .%F{red}󱄛 )${duration}%f %*"
    else
      RPROMPT="%*"
    fi
    
    unset timer_start
  else
    RPROMPT="%*"
  fi
}
```

---

# Mac 上的软件

* **ice**: Menu bar 管理软件。
* **loop**: 窗口管理软件。
* **itsycal**: Menu bar 上的日历小软件。
* **AlDente**: 高级电池管理。
* **AppCleaner**: 软件卸载辅助。
* **AutoRaise**: 激活 cursor 下的窗口。
* **BetterDisplay**: 显示器 DDC 控制。
* **ClashX Pro**: 代理工具，无须多言。
* **Easydict**: 好用的全局调用的翻译软件。
* **Folder Preview**: Space 预览目录内容。
* **IINA**: 视频播放软件。
* **Input Source Pro**: 自动输入法切换。
* **iTerm2**: 第一个使用的 Mac 终端软件。
* **kitty**: 很好用的终端，第二个使用的。
* **LuLu**: Mac 中的防火墙，可以高度自定义。
* **Mac Mouse Fix**: 鼠标加强工具，可以为使用鼠标和触控板时单独设置自然滚动的开关。
* **Maccy**: 剪贴板管理（已被 Raycast 代替）。
* **MediaMate**: Notch bar 美化。
* **Microsoft To Do**: 待办事项管理。
* **OBS**: 录屏软件。[配置教程](https://www.bilibili.com/opus/1044838772918714377)（注：记得把视频中的画布分辨率设置成显示器硬件分辨率，然后 10bit 屏幕设置为 main10）。
* **Obsidian**: Markdown 笔记软件。
* **Raycast**: Spotlight 的代替软件。
* **Snipaste**: 截图软件。
* **Topit**: 窗口置顶软件，用的很少但是不能没有。
* **VS Code**: 代码编辑器，无须多言。
* **RWTS PDFwriter**: 虚拟打印机。[GitHub Repo](https://github.com/rodyager/RWTS-PDFwriter)。卸载路径：`/Library/Printers/RWTS/PDFwriter/uninstall`（注：只能新建一个目录打印）。

### 系统清理与优化

如果用的时间长变卡了，可以执行以下操作：

```shell
# 重启 Dock 和 Finder
killall Dock Finder

# 清理缓存内存 inactive
sudo purge

# 注意：不要用 sudo
# 删除用户目录下的应用缓存文件
rm -rf ~/Library/Caches/*

# 清理用户缓存但更安全的方式
find ~/Library/Caches -type f -delete
```

---

# Mac 上的快捷键与系统配置

### 常用快捷键

| 快捷键 | 功能 |
| :--- | :--- |
| `Cmd + Opt + V` | Notch |
| `Cmd + Opt + B` | 启动台 |
| `Cmd + Opt + D` | Dock |
| `Cmd + Opt + T` | 台前调度 |
| `Opt + Space` | 拖拽预览中的 PDF |

### 系统配置与命令记录

2. **SSH 访问**: 系统设置 -> 共享 -> 远程登录，设置手机 SSH 到电脑。
3. **重要文件**: `~/Respository/OS_study.dmg`
4. **DNS 屏蔽**: 在 `/etc/hosts` 中修改本地 DNS 屏蔽 Apple 的更新。
5. **Dock 自动隐藏延迟控制**:
   ```sh
   # 取消延迟
   defaults write com.apple.dock "autohide-delay" -float "0" && killall Dock
   # 恢复默认
   defaults delete com.apple.dock "autohide-delay" && killall Dock
   ```
6. **手势拖动窗口配置**:
   ```sh
   # 用 Ctrl + Cmd 拖动窗口
   defaults write -g NSWindowShouldDragOnGesture -bool true
   # 恢复默认
   defaults delete -g NSWindowShouldDragOnGesture
   ```
7. **关闭 Cursor View UI 特效**:
   ```sh
   sudo defaults write /Library/Preferences/FeatureFlags/Domain/UIKit.plist redesigned_text_cursor -dict-add Enabled -bool NO
   ```
8. **关闭输入法切换动画**（似乎无效）:
   ```sh
   defaults write kCFPreferencesAnyApplication TSMLanguageIndicatorEnabled -bool false
   ```
9. **参考文档**: [Mac 张](https://qnswkjn28n.feishu.cn/wiki/T8uJwQH4YiIy7BkHyQpczpyDnug)

---

# 一些 Tips

* **静态路由配置**: 如果 `en0` 连接了 WiFi，`en12` 连接了有线网络，直接 `ssh 10.10.5.4` 可能根据路由表（使用 `route -rn` 查看）走默认的 `en12`。如果这个 IP 实际在 WiFi 环境下，可以用以下命令向路由表中添加静态路由，指定访问 `10.10.5.4` 的网关：
  ```sh
  sudo route -n add 10.10.5.4 10.11.3.254
  ```
  *(注：后面的 IP 是该 WiFi 环境中的网关，可以在 `netstat` 中查看。)*

* **UI 异常记录**: 有时候这个图标消失，怀疑是 CursorUI 进程出问题了。
