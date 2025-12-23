#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading
from concurrent.futures import ThreadPoolExecutor

from src.utils import cache_utils

class AudioProcessor:
    def __init__(self, audio_cache, duration_cache, duration_cache_file, program_dir):
        self.audio_cache = audio_cache
        self.duration_cache = duration_cache
        self.duration_cache_file = duration_cache_file
        self.library_files = set()
        self.library_dir = os.path.join(program_dir, "曲库")
        self.program_dir = program_dir
    
    def preload_audio(self, file_path):
        """预加载音频文件到缓存"""
        try:
            abs_file = os.path.abspath(file_path)
            if abs_file not in self.audio_cache:
                try:
                    from pydub import AudioSegment
                    # 支持多种音频格式
                    audio = AudioSegment.from_file(abs_file)
                    # 添加渐强渐弱效果
                    audio = audio.fade_in(2000).fade_out(2000)
                    # 添加到缓存
                    self.audio_cache.put(abs_file, audio)
                except Exception as e:
                    # 预加载失败不影响主流程，仅记录日志
                    print(f"预加载音频失败 {os.path.basename(abs_file)}: {e}")
            
            # 确保音频文件已缓存时长信息
            self.get_audio_duration(abs_file)
            return True
        except Exception as e:
            print(f"预加载音频文件 {os.path.basename(file_path)} 失败：{e}")
            return False
    
    def get_audio_duration(self, file_path):
        """获取音频文件的时长，优先从缓存获取，没有时计算并更新缓存"""
        return cache_utils.get_audio_duration(file_path, self.duration_cache)
    
    def save_duration_cache(self):
        """保存时长缓存到文件"""
        cache_utils.save_duration_cache(self.duration_cache_file, self.duration_cache)
    
    def process_library_file(self, file_path, status_signal=None):
        """处理单个曲库文件的加载"""
        try:
            # 检查是否已在缓存中
            if file_path not in self.duration_cache:
                # 计算时长并加入缓存
                self.get_audio_duration(file_path)
            return True
        except Exception as e:
            if status_signal:
                status_signal.emit(f"加载曲库文件 {os.path.basename(file_path)} 失败：{e}")
            return False
    
    def load_library_files(self, progress_signal=None, status_signal=None):
        """加载根目录下固定名为"曲库"的目录中的所有音频文件"""
        # 清空曲库文件集合
        self.library_files.clear()
        
        # 检查缓存文件是否存在且不为空
        import os
        if os.path.exists(self.duration_cache_file) and os.path.getsize(self.duration_cache_file) > 0 and len(self.duration_cache) > 0:
            if status_signal:
                status_signal.emit("缓存文件已存在，跳过曲库文件加载")
            return
        
        # 支持的音频文件扩展名
        audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma']
        
        try:
            # 检查曲库目录是否存在
            if not os.path.exists(self.library_dir):
                if status_signal:
                    status_signal.emit("曲库目录不存在")
                return
            
            # 遍历曲库目录中的所有文件
            all_files = []
            for root, dirs, files in os.walk(self.library_dir):
                for file in files:
                    # 检查文件扩展名
                    if any(file.lower().endswith(ext) for ext in audio_extensions):
                        # 获取文件的绝对路径
                        file_path = os.path.abspath(os.path.join(root, file))
                        all_files.append(file_path)
            
            # 更新曲库文件集合
            self.library_files = set(all_files)
            total_files = len(all_files)
            
            # 将曲库中的所有歌曲加入缓存
            success_count = 0
            fail_count = 0
            
            def _process_file(file_path):
                nonlocal success_count, fail_count
                if self.process_library_file(file_path, status_signal):
                    success_count += 1
                    return True
                else:
                    fail_count += 1
                    return False
            
            # 使用线程池并发加载曲库文件
            if total_files > 0:
                # 默认使用并发，后续可以根据需要添加参数控制
                use_concurrency = True
                
                if use_concurrency:
                    if status_signal:
                        status_signal.emit(f"开始并发加载曲库文件，共 {total_files} 个")
                    
                    # 并发处理所有文件，但会定期检查并发设置是否变化
                    results = []
                    # 分批处理
                    batch_size = max(1, total_files // 10)
                    batches = [all_files[i:i+batch_size] for i in range(0, total_files, batch_size)]
                    
                    current_index = 0
                    for batch in batches:
                        # 使用线程池处理当前批次
                        with ThreadPoolExecutor(max_workers=4) as executor:
                            batch_results = list(executor.map(_process_file, batch))
                            results.extend(batch_results)
                        
                        # 更新进度
                        current_index += len(batch)
                        progress = int(current_index / total_files * 50)  # 曲库加载占总进度的50%
                        if progress_signal:
                            progress_signal.emit(progress)
            
            # 保存更新后的缓存
            self.save_duration_cache()
            
            # 更新状态
            status_msg = f"已加载曲库，成功：{success_count} 个文件，失败：{fail_count} 个文件"
            if status_signal:
                status_signal.emit(status_msg)
            
        except Exception as e:
            if status_signal:
                status_signal.emit(f"加载曲库目录失败：{e}")
            self.library_files.clear()
    
    def auto_load_dance_files(self, progress_signal=None, status_signal=None, use_concurrency=True):
        """自动读取随舞目录下的所有音频文件并随机排序"""
        import random
        
        dance_dir = os.path.join(self.program_dir, "随舞")
        audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma']
        
        try:
            # 检查目录是否存在
            if not os.path.exists(dance_dir):
                if status_signal:
                    status_signal.emit(f"未找到{dance_dir}目录")
                return []
            
            # 获取目录下所有音频文件
            audio_files = []
            for file in os.listdir(dance_dir):
                file_path = os.path.join(dance_dir, file)
                if os.path.isfile(file_path):
                    if any(file.lower().endswith(ext) for ext in audio_extensions):
                        # 使用绝对路径
                        abs_path = os.path.abspath(file_path)
                        audio_files.append(abs_path)
            
            if not audio_files:
                if status_signal:
                    status_signal.emit(f"{dance_dir}目录下未找到音频文件")
                return []
            
            # 随机排序文件
            random.shuffle(audio_files)
            
            total_files = len(audio_files)
            
            # 只获取时长信息，不立即加载完整音频到缓存
            def _get_file_duration(abs_path):
                try:
                    # 只获取时长信息（会自动复用曲库缓存）
                    self.get_audio_duration(abs_path)
                    return True
                except Exception as e:
                    if status_signal:
                        status_signal.emit(f"获取随舞文件时长 {os.path.basename(abs_path)} 失败：{e}")
                    return False
            
            # 获取随舞文件时长信息，无论是否使用并发
            processed_count = 0
            if audio_files:
                if status_signal:
                    status_signal.emit(f"开始获取随舞文件时长，共 {len(audio_files)} 个")
                
                if use_concurrency:
                    # 使用线程池并发获取时长，减少线程数避免卡顿
                    with ThreadPoolExecutor(max_workers=4) as executor:
                        results = list(executor.map(_get_file_duration, audio_files))
                        processed_count = sum(results)
                else:
                    # 不使用并发，顺序获取时长
                    for file_path in audio_files:
                        if _get_file_duration(file_path):
                            processed_count += 1
                
                # 更新进度
                if progress_signal:
                    progress_signal.emit(100)  # 完成
                
                if status_signal:
                    status_signal.emit(f"成功获取 {processed_count}/{len(audio_files)} 个随舞文件时长")
            
            # 保存时长缓存
            self.save_duration_cache()
            
            # 音频文件将在实际播放时再加载
            return audio_files
        except Exception as e:
            if status_signal:
                status_signal.emit(f"加载音频文件失败：{e}")
            return []
    
    def calculate_total_duration(self, file_list, countdown_file=None):
        """计算预计的总音频时长"""
        print(f"calculate_total_duration被调用，文件列表：{file_list}")
        print(f"文件列表长度：{len(file_list)}")
        if not file_list:
            print("文件列表为空，返回0")
            return 0
        
        total_seconds = 0
        countdown_duration = 0
        
        # 计算倒计时音频时长（如果有）
        if countdown_file and os.path.exists(countdown_file):
            try:
                countdown_duration = self.get_audio_duration(countdown_file)
                print(f"倒计时音频时长：{countdown_duration}")
            except Exception as e:
                print(f"计算倒计时时长失败：{e}")
        else:
            print(f"没有倒计时音频文件或文件不存在：{countdown_file}")
        
        # 计算所有音频文件的时长
        print("开始计算所有音频文件的时长：")
        for file in file_list:
            try:
                duration = self.get_audio_duration(file)
                print(f"文件{os.path.basename(file)}的时长：{duration}")
                total_seconds += duration
            except Exception as e:
                print(f"计算{os.path.basename(file)}时长失败：{e}")
        
        print(f"所有音频文件总时长（不含倒计时）：{total_seconds}")
        
        # 计算总时长（每个音频之间插入一个倒计时音频）
        if countdown_file and len(file_list) > 1:
            countdown_total = countdown_duration * (len(file_list) - 1)
            print(f"倒计时总时长：{countdown_total}")
            total_seconds += countdown_total
        
        print(f"最终总时长：{total_seconds}")
        return total_seconds
