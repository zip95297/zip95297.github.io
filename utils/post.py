#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import os
import subprocess
import sys

class NoteSelector:
    def __init__(self, base_dir):
        self.base_dir = os.path.expanduser(base_dir)
        self.current_pos = 0
        self.start_line = 0
        self.tree_data = []
        self.expanded = set()  # 存储已展开的目录
        self.note_path = None
        self.img_path = None
        self.max_lines = 0
        self.max_cols = 0
        
    def build_tree(self, dir_path=None, level=0):
        """递归构建目录树"""
        if dir_path is None:
            dir_path = self.base_dir
            self.tree_data = []
        
        try:
            items = os.listdir(dir_path)
            # 先显示目录，再显示文件
            dirs = sorted([i for i in items if os.path.isdir(os.path.join(dir_path, i))])
            # 忽略 个人 文件夹
            dirs = [d for d in dirs if not d.startswith('个人')]
            files = sorted([i for i in items if i.endswith('.md')])
            
            for d in dirs:
                # 跳过隐藏目录
                if d.startswith('.'):
                    continue
                full_path = os.path.join(dir_path, d)
                self.tree_data.append({
                    'type': 'dir',
                    'name': d,
                    'path': full_path,
                    'level': level,
                    'expanded': full_path in self.expanded
                })
                
                if full_path in self.expanded:
                    self.build_tree(full_path, level + 1)
            
            for f in files:
                if f.startswith('.'):
                    continue
                self.tree_data.append({
                    'type': 'file',
                    'name': f,
                    'path': os.path.join(dir_path, f),
                    'level': level
                })
        except PermissionError:
            pass  # 忽略权限错误
    
    def draw_tree(self, stdscr):
        """绘制目录树"""
        stdscr.clear()
        
        header = "笔记发布工具 - 使用↑↓键导航，Enter键选择，Space展开/折叠，q退出，p发布"
        stdscr.addstr(0, 0, header, curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * min(len(header), self.max_cols-1))
        
        display_lines = min(len(self.tree_data), self.max_lines - 6)
        end_line = min(self.start_line + display_lines, len(self.tree_data))
        
        for i in range(self.start_line, end_line):
            item = self.tree_data[i]
            prefix = "  " * item['level']
            
            if item['type'] == 'dir':
                if item['expanded']:
                    icon = "📂 "
                else:
                    icon = "📁 "
            else:
                icon = "📄 "
            
            line = f"{prefix}{icon}{item['name']}"
            
            # 截断过长的行
            if len(line) > self.max_cols - 1:
                line = line[:self.max_cols - 4] + "..."
            
            if i == self.current_pos:
                stdscr.addstr(i - self.start_line + 3, 0, line, curses.A_REVERSE)
            else:
                stdscr.addstr(i - self.start_line + 3, 0, line)
        
        # 显示当前选择的路径
        footer_line = self.max_lines - 3
        stdscr.addstr(footer_line, 0, "=" * (self.max_cols-1))
        
        if self.note_path:
            note_display = f"笔记: {self.note_path}"
            if len(note_display) > self.max_cols - 1:
                note_display = note_display[:self.max_cols - 4] + "..."
            stdscr.addstr(footer_line + 1, 0, note_display)
        
        if self.img_path:
            img_display = f"图片: {self.img_path}"
            if len(img_display) > self.max_cols - 1:
                img_display = img_display[:self.max_cols - 4] + "..."
            stdscr.addstr(footer_line + 2, 0, img_display)
        
        stdscr.refresh()
    
    def find_img_dir(self, note_path):
        """查找笔记同目录下的图片目录"""
        dir_path = os.path.dirname(note_path)
        
        # 先检查是否有imgs目录
        imgs_path = os.path.join(dir_path, 'imgs')
        if os.path.isdir(imgs_path):
            return imgs_path
        
        # 再检查是否有img目录
        img_path = os.path.join(dir_path, 'img')
        if os.path.isdir(img_path):
            return img_path
        
        return None
    
    def run(self, stdscr):
        """主循环"""
        curses.curs_set(0)  # 隐藏光标
        stdscr.timeout(100)  # 设置getch超时，使循环持续运行
        
        # 获取终端大小
        self.max_lines, self.max_cols = stdscr.getmaxyx()
        
        # 初始化目录树
        self.build_tree()
        
        while True:
            self.draw_tree(stdscr)
            
            try:
                key = stdscr.getch()
            except:
                continue
            
            if key == curses.KEY_UP:
                self.current_pos = max(0, self.current_pos - 1)
                # 如果光标移出可视区域，滚动显示
                if self.current_pos < self.start_line:
                    self.start_line = self.current_pos
            
            elif key == curses.KEY_DOWN:
                self.current_pos = min(len(self.tree_data) - 1, self.current_pos + 1)
                # 如果光标移出可视区域，滚动显示
                if self.current_pos >= self.start_line + self.max_lines - 6:
                    self.start_line = self.current_pos - (self.max_lines - 7)
            
            elif key == ord(' '):  # 空格键
                # 展开/折叠目录
                if self.current_pos < len(self.tree_data):
                    item = self.tree_data[self.current_pos]
                    if item['type'] == 'dir':
                        if item['path'] in self.expanded:
                            self.expanded.remove(item['path'])
                        else:
                            self.expanded.add(item['path'])
                        # 重建树
                        current_path = item['path']
                        self.build_tree()
                        # 找回当前位置
                        for i, item in enumerate(self.tree_data):
                            if item['path'] == current_path:
                                self.current_pos = i
                                break
            
            elif key == 10:  # Enter键
                # 选择文件
                if self.current_pos < len(self.tree_data):
                    item = self.tree_data[self.current_pos]
                    if item['type'] == 'file' and item['name'].endswith('.md'):
                        self.note_path = item['path']
                        self.img_path = self.find_img_dir(item['path'])
            
            elif key == ord('p'):  # p键发布
                if self.note_path:
                    # 退出curses模式以执行命令
                    curses.endwin()
                    
                    cmd = f"/Users/zip95297/Repository/BLOG/zjb-blog/utils/post_cli -n \"{self.note_path}\""
                    if self.img_path:
                        cmd += f" -i \"{self.img_path}\""
                    
                    print(f"执行命令: {cmd}")
                    
                    try:
                        # 执行命令
                        subprocess.run(cmd, shell=True)
                        input("\n按Enter继续...")
                    except Exception as e:
                        print(f"错误: {e}")
                        input("\n按Enter继续...")
                    
                    # 恢复curses模式
                    stdscr.clear()
                    curses.curs_set(0)
                else:
                    # 在底部显示错误消息
                    stdscr.addstr(self.max_lines-1, 0, "错误: 请先选择一个笔记文件!", curses.A_BOLD)
                    stdscr.refresh()
                    stdscr.getch()  # 等待按键
            
            elif key == ord('q'):  # q键退出
                break
            
            # 刷新终端大小
            try:
                new_max_lines, new_max_cols = stdscr.getmaxyx()
                if new_max_lines != self.max_lines or new_max_cols != self.max_cols:
                    self.max_lines, self.max_cols = new_max_lines, new_max_cols
                    stdscr.clear()
            except:
                pass

def main():
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = "/Users/zip95297/Repository/DocumentLibrary/ObsidianNote"
    
    selector = NoteSelector(base_dir)
    curses.wrapper(selector.run)

if __name__ == "__main__":
    main()
