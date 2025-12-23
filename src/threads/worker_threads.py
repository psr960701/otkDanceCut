#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from PyQt5.QtCore import QThread, pyqtSignal

from src.utils import utils
from src.utils import cache_utils

class BackgroundLoader(QThread):
    finished = pyqtSignal()
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    
    def __init__(self, load_library_func, load_dance_func):
        super().__init__()
        self.load_library_func = load_library_func
        self.load_dance_func = load_dance_func
    
    def run(self):
        import time
        time.sleep(1)  # 等待1秒，让用户有机会在加载开始前修改并发设置
        
        # 执行耗时的加载操作
        self.status_updated.emit("正在加载曲库文件...")
        self.load_library_func(self.progress_updated, self.status_updated)
        
        # 只有当load_dance_func不为None时，才尝试加载随舞目录文件
        if self.load_dance_func is not None:
            self.status_updated.emit("正在加载随舞目录文件...")
            self.load_dance_func(self.progress_updated, self.status_updated)
        
        # 发送完成信号
        self.status_updated.emit("缓存构建完成")
        self.finished.emit()

class SplicingThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, file_list, mode, countdown_file, output_file, cache, use_concurrency=True):
        super().__init__()
        self.file_list = file_list
        self.mode = mode
        self.countdown_file = countdown_file
        self.output_file = output_file
        self.cache = cache  # 接收外部缓存
        self.use_concurrency = use_concurrency
    
    def run(self):
        try:
            self.status_updated.emit("开始拼接音频...")
            
            # 加载倒计时音频
            countdown = None
            if self.countdown_file and os.path.exists(self.countdown_file):
                try:
                    # 检查缓存中是否有倒计时音频
                    countdown = self.cache.get(self.countdown_file)
                    if countdown:
                        self.status_updated.emit(f"从缓存加载倒计时音频：{os.path.basename(self.countdown_file)}")
                    else:
                        from pydub import AudioSegment
                        # 支持多种音频格式
                        countdown = AudioSegment.from_file(self.countdown_file)
                        # 添加到缓存
                        self.cache.put(self.countdown_file, countdown)
                        self.status_updated.emit(f"已加载倒计时音频：{os.path.basename(self.countdown_file)}")
                except Exception as e:
                    self.status_updated.emit(f"加载倒计时音频失败：{e}")
            
            # 根据模式排序文件
            if self.mode == "random":
                random.shuffle(self.file_list)
                self.status_updated.emit("已随机排序音频文件")
            # 否则保持UI中拖动后的顺序
            else:
                self.status_updated.emit("使用UI中设置的音频顺序")
            
            # 开始拼接
            segments = []  # 收集所有要拼接的音频片段
            total_files = len(self.file_list)
            playlist = []
            
            for i, file in enumerate(self.file_list):
                try:
                    abs_file = os.path.abspath(file)
                    # 检查缓存中是否已有该音频
                    audio = self.cache.get(abs_file)
                    if audio:
                        if i % 5 == 0:  # 每5个文件更新一次状态
                            self.status_updated.emit(f"从缓存加载：{os.path.basename(file)}")
                    else:
                        from pydub import AudioSegment
                        # 支持多种音频格式
                        audio = AudioSegment.from_file(abs_file)
                        # 添加渐强渐弱效果（2000ms）
                        audio = audio.fade_in(2000).fade_out(2000)
                        # 添加到缓存
                        self.cache.put(abs_file, audio)
                        if i % 5 == 0:  # 每5个文件更新一次状态
                            self.status_updated.emit(f"已加载：{os.path.basename(file)}")
                    
                    # 添加到播放列表
                    playlist.append(os.path.basename(file))
                    
                    # 添加音频片段到列表
                    segments.append(audio)
                    
                    # 如果有倒计时音频且不是第一个片段，添加倒计时
                    if countdown and i > 0:
                        segments.append(countdown)
                    
                    # 更新进度
                    progress = int((i + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                    self.status_updated.emit(f"已添加：{os.path.basename(file)}")
                    
                except Exception as e:
                    self.status_updated.emit(f"处理{os.path.basename(file)}失败：{e}")
                    continue
            
            # 批量拼接所有音频片段
            if segments:
                self.status_updated.emit("开始拼接所有音频片段...")
                
                # 使用utils模块中的并行合并函数
                try:
                    result = utils.parallel_merge(
                        segments, 
                        use_concurrency=self.use_concurrency,
                        status_callback=self.status_updated.emit
                    )
                except Exception as e:
                    self.status_updated.emit(f"并行合并失败，将使用串行合并: {e}")
                    # 降级到串行合并
                    result = segments[0]
                    if len(segments) > 1:
                        result = sum(segments[1:], start=result)
                
                self.status_updated.emit("音频片段拼接完成")
            else:
                result = None
            
            if result is None:
                self.finished.emit(False, "没有成功拼接任何音频文件")
                return
            
            # 保存结果
            self.status_updated.emit(f"正在保存到 {self.output_file}...")
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    self.status_updated.emit(f"已创建输出目录：{output_dir}")
                except Exception as e:
                    self.status_updated.emit(f"创建输出目录失败：{e}")
            result.export(self.output_file, format="mp3")
            
            # 生成音乐顺序文件
            base_name = "音乐顺序"
            extension = ".txt"
            playlist_file = utils.get_unique_filename(base_name, extension)
            try:
                # 确保输出目录存在
                playlist_dir = os.path.dirname(playlist_file)
                if playlist_dir and not os.path.exists(playlist_dir):
                    os.makedirs(playlist_dir)
                with open(playlist_file, "w", encoding="utf-8") as f:
                    f.write("拼接音乐顺序：\n\n")
                    for song in playlist:
                        # 提取纯净的歌曲名
                        pure_song_name = utils.extract_song_name(song)
                        f.write(f"{pure_song_name}\n")
                    self.status_updated.emit(f"已生成音乐顺序文件：{playlist_file}")
            except Exception as e:
                self.status_updated.emit(f"生成音乐顺序文件失败：{e}")
            
            # 计算总时长
            total_duration = len(result) / 1000
            duration_str = str(timedelta(seconds=int(total_duration)))
            
            self.finished.emit(True, f"拼接完成！总时长：{duration_str}\n输出文件：{self.output_file}\n音乐顺序已保存到：{playlist_file}")
            
        except Exception as e:
            self.finished.emit(False, f"拼接过程中发生错误：{e}")
