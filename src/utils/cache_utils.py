#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import os
import json
import sys
import time
import platform
from collections import OrderedDict

# 跨平台 ffmpeg/ffprobe 路径获取
def get_ffprobe_path():
    """
    根据运行环境和操作系统动态获取ffprobe路径
    macOS/Linux: 使用系统的 ffprobe (需 brew/apt 安装)
    Windows: 使用项目内的 ffmpeg/ffprobe.exe
    """
    system = platform.system()
    
    # 打包环境
    if getattr(sys, 'frozen', False):
        if system == 'Darwin':  # macOS
            # 尝试打包后的路径
            base_path = os.path.dirname(sys.executable)
            bundled = os.path.join(base_path, 'ffprobe')
            if os.path.exists(bundled):
                return bundled
            # PyInstaller onedir 模式
            bundled2 = os.path.join(base_path, '..', 'Resources', 'ffprobe')
            if os.path.exists(bundled2):
                return bundled2
            # 降级到系统 ffprobe
            return 'ffprobe'
        elif system == 'Windows':
            base_path = sys._MEIPASS
            return os.path.join(base_path, 'ffmpeg', 'ffprobe.exe')
        else:  # Linux
            return 'ffprobe'
    
    # 开发环境
    if system == 'Windows':
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ffprobe_path = os.path.join(base_path, 'ffmpeg', 'ffprobe.exe')
        if os.path.exists(ffprobe_path):
            return ffprobe_path
    
    # macOS/Linux 使用系统 ffprobe
    return 'ffprobe'


def get_ffmpeg_path():
    """
    根据运行环境和操作系统动态获取ffmpeg路径
    macOS/Linux: 使用系统的 ffmpeg (需 brew/apt 安装)
    Windows: 使用项目内的 ffmpeg/ffmpeg.exe
    """
    system = platform.system()
    
    # 打包环境
    if getattr(sys, 'frozen', False):
        if system == 'Darwin':  # macOS
            base_path = os.path.dirname(sys.executable)
            bundled = os.path.join(base_path, 'ffmpeg')
            if os.path.exists(bundled):
                return bundled
            bundled2 = os.path.join(base_path, '..', 'Resources', 'ffmpeg')
            if os.path.exists(bundled2):
                return bundled2
            return 'ffmpeg'
        elif system == 'Windows':
            base_path = sys._MEIPASS
            return os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')
        else:  # Linux
            return 'ffmpeg'
    
    # 开发环境
    if system == 'Windows':
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ffmpeg_path = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path
    
    # macOS/Linux 使用系统 ffmpeg
    return 'ffmpeg'

class LRUCache:
    def __init__(self, capacity=100):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            else:
                self.cache.move_to_end(key)
                return self.cache[key]
    
    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            elif len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = value
    
    def __contains__(self, key):
        with self.lock:
            return key in self.cache
    
    def clear(self):
        with self.lock:
            self.cache.clear()

def load_duration_cache(cache_file, ttl=30*24*60*60):  # 默认TTL为30天
    """从JSON文件加载时长缓存，并应用TTL过滤"""
    duration_cache = {}
    try:
        old_cache = {}
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                old_cache = json.load(f)
        
        current_time = time.time()
        
        # 处理旧缓存数据，转换为新格式并应用TTL过滤
        for old_key, old_value in old_cache.items():
            try:
                # 提取文件名作为新的缓存键
                if isinstance(old_value, dict) and "duration" in old_value:
                    # 已经是新格式
                    cache_key = os.path.basename(old_key)
                    # 检查TTL
                    if "cache_time" in old_value and (current_time - old_value["cache_time"]) <= ttl:
                        duration_cache[cache_key] = old_value
                    elif "cache_time" not in old_value:
                        # 没有缓存时间的旧条目，保留但更新缓存时间
                        duration_cache[cache_key] = {
                            "duration": old_value["duration"],
                            "cache_time": current_time
                        }
                else:
                    # 旧格式，转换为新格式
                    cache_key = os.path.basename(old_key)
                    duration_cache[cache_key] = {
                        "duration": old_value,
                        "cache_time": current_time  # 使用当前时间作为缓存时间
                    }
            except Exception as e:
                print(f"转换缓存键 {old_key} 失败：{e}")
                # 保留原键作为后备
                cache_key = os.path.basename(old_key)
                duration_cache[cache_key] = {
                    "duration": old_value,
                    "cache_time": current_time
                }
    except Exception as e:
        print(f"加载时长缓存失败：{e}")
    return duration_cache

def save_duration_cache(cache_file, duration_cache):
    """将时长缓存保存到JSON文件"""
    try:
        # 保存缓存（已经是按文件名唯一的格式）
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(duration_cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"保存时长缓存失败：{e}")

def get_audio_duration(file_path, duration_cache, ttl=30*24*60*60):  # 默认TTL为30天
    """获取音频文件的时长，优先从缓存获取（考虑TTL），没有时计算并更新缓存"""
    # 仅使用文件名作为缓存键
    abs_path = os.path.abspath(file_path)
    cache_key = os.path.basename(abs_path)
    
    # 检查缓存并验证TTL
    if cache_key in duration_cache:
        cached_entry = duration_cache[cache_key]
        # 检查缓存是否过期
        if "cache_time" in cached_entry and (time.time() - cached_entry["cache_time"]) <= ttl:
            return cached_entry["duration"]
        # 缓存过期，需要重新计算
    
    try:
        from pydub import AudioSegment
        # 支持多种音频格式，而不仅仅是MP3
        audio = AudioSegment.from_file(abs_path)
        duration = len(audio) / 1000
        
        # 保存到缓存，增加缓存时长属性
        duration_cache[cache_key] = {
            "duration": duration,
            "cache_time": time.time()
        }
        
        return duration
    except Exception as e:
        print(f"计算{os.path.basename(abs_path)}时长失败：{e}")
        # 尝试使用ffprobe命令行工具获取时长
        try:
            import subprocess
            import json
            
            # 使用ffprobe获取时长
            cmd = [
                get_ffprobe_path(),
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                abs_path
            ]
            # 不使用check=True，避免命令失败时抛出异常
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                duration = float(info['format']['duration'])
                
                # 保存到缓存，增加缓存时长属性
                duration_cache[cache_key] = {
                    "duration": duration,
                    "cache_time": time.time()
                }
                return duration
            else:
                print(f"使用ffprobe计算{os.path.basename(abs_path)}时长失败，返回码：{result.returncode}")
                return 0
        except Exception as e2:
            print(f"使用ffprobe计算{os.path.basename(abs_path)}时长也失败：{e2}")
            return 0
