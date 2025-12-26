#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import argparse
from pydub import AudioSegment
from datetime import timedelta
import sys

# 导入常量配置
from src.constants import COUNTDOWN_FILENAMES, DANCE_DIR_NAME, OUTPUT_FILE_PREFIX, OUTPUT_FILE_EXTENSION

def get_audio_files(directory):
    """获取目录下所有音频文件"""
    audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma']
    audio_files = []
    
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(file_path)
    
    return audio_files

def load_audio(file_path):
    """根据文件扩展名加载音频文件"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.mp3':
            return AudioSegment.from_mp3(file_path)
        elif file_ext == '.wav':
            return AudioSegment.from_wav(file_path)
        elif file_ext == '.ogg':
            return AudioSegment.from_ogg(file_path)
        elif file_ext == '.flac':
            return AudioSegment.from_file(file_path, format='flac')
        elif file_ext in ['.aac', '.m4a']:
            return AudioSegment.from_file(file_path, format='m4a')
        elif file_ext == '.wma':
            return AudioSegment.from_file(file_path, format='wma')
        else:
            # 尝试自动检测格式
            return AudioSegment.from_file(file_path)
    except Exception as e:
        raise Exception(f"加载音频文件失败: {e}")

def normalize_volume(audio, target_dBFS=-20.0):
    """归一化音频音量"""
    return audio.apply_gain(target_dBFS - audio.dBFS)

def progress_bar(current, total, title="处理中"):
    """显示进度条"""
    percent = current / total
    bar_length = 50
    progress = "█" * int(bar_length * percent)
    spaces = " " * (bar_length - len(progress))
    sys.stdout.write(f"\r{title}: [{progress}{spaces}] {percent:.1%} ({current}/{total})")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")

def format_time(seconds):
    """格式化时间为HH:MM:SS格式"""
    return str(timedelta(seconds=int(seconds)))

def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='音频拼接工具')
    parser.add_argument('--mode', choices=['random', 'sequential'], default='random',
                      help='拼接模式：random（随机）或 sequential（顺序）')
    parser.add_argument('--output', default=f'{OUTPUT_FILE_PREFIX}{OUTPUT_FILE_EXTENSION}', help='输出文件名')
    
    args = parser.parse_args()
    
    # 检查倒计时文件是否存在
    countdown = None
    countdown_filename = None
    for filename in COUNTDOWN_FILENAMES:
        if os.path.exists(filename):
            countdown_filename = filename
            break
    
    if not countdown_filename:
        print(f"警告：未找到倒计时音频文件，将不添加过渡效果")
    else:
        try:
            countdown = AudioSegment.from_mp3(countdown_filename)
            print(f"已加载倒计时音频：{countdown_filename} ({format_time(len(countdown)/1000)})")
        except Exception as e:
            print(f"加载{countdown_filename}失败：{e}")
            countdown = None
    
    # 获取随舞目录下的音频文件
    dance_dir = DANCE_DIR_NAME
    audio_files = get_audio_files(dance_dir)
    
    if not audio_files:
        print(f"错误：{dance_dir}目录下未找到音频文件")
        return
    
    print(f"\n找到{len(audio_files)}个音频文件：")
    for i, file in enumerate(audio_files, 1):
        try:
            audio = AudioSegment.from_mp3(file)
            print(f"{i}. {os.path.basename(file)} ({format_time(len(audio)/1000)})")
        except Exception as e:
            print(f"{i}. {os.path.basename(file)} (加载失败: {e})")
    
    # 根据模式排序文件
    if args.mode == 'random':
        random.shuffle(audio_files)
        print("\n随机排序完成")
    else:
        # 按文件名顺序排序
        audio_files.sort()
        print("\n按顺序排序完成")
    
    # 开始拼接
    print("\n开始拼接音频...")
    result = None
    total_duration = 0
    playlist = []
    
    for i, file in enumerate(audio_files):
        try:
            # 加载音频
            audio = AudioSegment.from_mp3(file)
            file_duration = len(audio) / 1000
            total_duration += file_duration
            
            # 添加到播放列表
            playlist.append(os.path.basename(file))
            
            # 拼接音频
            if result is None:
                result = audio
            else:
                # 如果有倒计时文件，添加过渡
                if countdown:
                    result += countdown
                result += audio
            
            print(f"已添加: {os.path.basename(file)} ({format_time(file_duration)})")
            
        except Exception as e:
            print(f"添加{os.path.basename(file)}失败: {e}")
    
    if result is None:
        print("错误：没有成功拼接任何音频文件")
        return
    
    # 输出结果
    print(f"\n拼接完成！")
    print(f"总时长: {format_time(total_duration)}")
    print(f"输出文件: {args.output}")
    
    # 保存结果
    try:
        result.export(args.output, format='mp3')
        print(f"音频文件已保存到: {args.output}")
    except Exception as e:
        print(f"保存音频失败: {e}")
        return
    
    # 输出播放列表
    print("\n播放顺序:")
    for i, song in enumerate(playlist, 1):
        print(f"{i}. {song}")

if __name__ == '__main__':
    main()
