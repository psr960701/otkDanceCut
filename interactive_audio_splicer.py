#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式音频拼接工具

功能：
- 读取随舞目录下的所有音频文件
- 使用倒计时.mp3作为音频之间的过渡
- 支持随机拼接和顺序拼接两种模式
- 交互式选择拼接模式和输出文件名
- 输出拼接后的歌曲顺序和总时长
"""

import os
import random
import time
import questionary
import sys
from pydub import AudioSegment

# 确保当前目录在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入常量配置
from src.constants import COUNTDOWN_FILENAMES, DANCE_DIR_NAME


def get_audio_files(directory):
    """获取指定目录下的所有音频文件"""
    if not os.path.exists(directory):
        print(f"错误：目录 '{directory}' 不存在")
        return []
    
    audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
    audio_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(root, file))
    
    return audio_files


def format_duration(seconds):
    """将秒数格式化为分:秒的形式"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def main():
    print("=" * 60)
    print("欢迎使用交互式音频拼接工具".center(60))
    print("=" * 60)
    print()
    
    # 等待用户准备
    time.sleep(1)
    
    # 1. 选择拼接模式
    mode = questionary.select(
        "请选择拼接模式：",
        choices=[
            questionary.Choice("随机拼接", "random"),
            questionary.Choice("顺序拼接", "sequential")
        ]
    ).ask()
    
    print()
    
    # 2. 输入输出文件名
    default_output = "output.mp3"
    output_file = questionary.text(
        "请输入输出文件名（默认：output.mp3）：",
        default=default_output
    ).ask()
    
    # 确保输出文件有.mp3扩展名
    if not output_file.lower().endswith('.mp3'):
        output_file += '.mp3'
    
    print()
    
    # 3. 确认选择
    confirm = questionary.confirm(
        f"拼接模式：{'随机' if mode == 'random' else '顺序'}\n输出文件：{output_file}\n是否开始拼接？"
    ).ask()
    
    if not confirm:
        print("\n已取消拼接操作")
        return
    
    print("\n开始拼接音频...")
    
    # 4. 拼接音频的核心逻辑
    dance_dir = DANCE_DIR_NAME
    
    # 获取音频文件列表
    audio_files = get_audio_files(dance_dir)
    if not audio_files:
        print("错误：没有找到音频文件")
        return
    
    # 加载倒计时音频
    countdown = None
    countdown_filename = None
    for filename in COUNTDOWN_FILENAMES:
        if os.path.exists(filename):
            countdown_filename = filename
            break
    
    if countdown_filename:
        countdown = AudioSegment.from_mp3(countdown_filename)
        print(f"已加载倒计时音频：{countdown_filename}")
    else:
        print(f"警告：未找到倒计时音频文件，将不添加过渡")
        countdown = None
    
    print()
    
    # 根据选择的模式处理音频文件
    if mode == "random":
        print("正在随机打乱音频顺序...")
        random.shuffle(audio_files)
    else:
        print("正在按文件名顺序排列音频...")
        audio_files.sort()
    
    print()
    print("拼接顺序：")
    print("-" * 40)
    
    total_duration = 0
    result = None
    
    for i, file_path in enumerate(audio_files):
        # 获取文件名（不包含路径）
        file_name = os.path.basename(file_path)
        print(f"{i+1}. {file_name}")
        
        # 加载音频文件
        audio = AudioSegment.from_mp3(file_path)
        total_duration += len(audio) / 1000.0
        
        # 拼接音频
        if result is None:
            result = audio
        else:
            # 添加倒计时过渡
            if countdown:
                result += countdown
                total_duration += len(countdown) / 1000.0
            result += audio
    
    print("-" * 40)
    print(f"总时长：{format_duration(total_duration)}")
    print()
    
    # 5. 导出拼接后的音频
    try:
        print(f"正在导出拼接后的音频到 {output_file}...")
        result.export(output_file, format="mp3")
        print("\n" + "=" * 60)
        print("音频拼接完成！".center(60))
        print(f"输出文件：{output_file}".center(60))
        print(f"总时长：{format_duration(total_duration)}".center(60))
        print("=" * 60)
    except Exception as e:
        print(f"\n导出音频时出错：{e}")
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消操作")
    except Exception as e:
        print(f"\n程序出错：{e}")
