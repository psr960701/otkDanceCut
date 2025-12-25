#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor

# 禁止子进程弹出窗口

def suppress_libpng_warnings():
    """抑制libpng警告"""
    import os
    import logging
    import warnings
    
    # 设置环境变量来抑制libpng警告
    os.environ['PNG_SKIP_sRGB_CHECK'] = '1'
    os.environ['PNG_SKIP_iCCP_CHECK'] = '1'
    
    # 过滤掉libpng相关的警告
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="png")
    warnings.filterwarnings("ignore", category=UserWarning, module="png")
    
    # 配置日志记录器
    logger = logging.getLogger()
    for handler in logger.handlers:
        handler.addFilter(lambda record: "libpng" not in record.getMessage())


def suppress_subprocess_windows():
    if hasattr(subprocess, 'CREATE_NO_WINDOW'):
        create_no_window = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        
        # 保存原始函数
        subprocess._old_popen = subprocess.Popen
        subprocess._old_run = subprocess.run
        subprocess._old_call = subprocess.call
        subprocess._old_check_call = subprocess.check_call
        subprocess._old_check_output = subprocess.check_output
        subprocess._old_getstatusoutput = subprocess.getstatusoutput if hasattr(subprocess, 'getstatusoutput') else None
        subprocess._old_getoutput = subprocess.getoutput if hasattr(subprocess, 'getoutput') else None
        
        # 重写Popen
        def _new_popen(*args, **kwargs):
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | create_no_window
            return subprocess._old_popen(*args, **kwargs)
        subprocess.Popen = _new_popen
        
        # 重写run
        def _new_run(*args, **kwargs):
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | create_no_window
            return subprocess._old_run(*args, **kwargs)
        subprocess.run = _new_run
        
        # 重写call
        def _new_call(*args, **kwargs):
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | create_no_window
            return subprocess._old_call(*args, **kwargs)
        subprocess.call = _new_call
        
        # 重写check_call
        def _new_check_call(*args, **kwargs):
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | create_no_window
            return subprocess._old_check_call(*args, **kwargs)
        subprocess.check_call = _new_check_call
        
        # 重写check_output
        def _new_check_output(*args, **kwargs):
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | create_no_window
            return subprocess._old_check_output(*args, **kwargs)
        subprocess.check_output = _new_check_output
        
        # 重写getstatusoutput
        if subprocess._old_getstatusoutput:
            def _new_getstatusoutput(cmd, *args, **kwargs):
                # getstatusoutput内部会调用Popen，所以不需要额外设置creationflags
                return subprocess._old_getstatusoutput(cmd, *args, **kwargs)
            subprocess.getstatusoutput = _new_getstatusoutput
        
        # 重写getoutput
        if subprocess._old_getoutput:
            def _new_getoutput(cmd, *args, **kwargs):
                # getoutput内部会调用Popen，所以不需要额外设置creationflags
                return subprocess._old_getoutput(cmd, *args, **kwargs)
            subprocess.getoutput = _new_getoutput

        # 尝试覆盖可能存在的其他子进程创建函数
        for func_name in ['subprocess', 'call', 'run', 'check_call', 'check_output', 'getstatusoutput', 'getoutput']:
            if hasattr(subprocess, func_name):
                original_func = getattr(subprocess, func_name)
                if callable(original_func) and not func_name.startswith('_old_'):
                    def wrapper(*args, **kwargs):
                        kwargs['creationflags'] = kwargs.get('creationflags', 0) | create_no_window
                        return original_func(*args, **kwargs)
                    setattr(subprocess, func_name, wrapper)

        # 对于直接使用os模块创建进程的情况
        if hasattr(os, 'system'):
            os._old_system = os.system
            def _new_system(cmd):
                import subprocess
                return subprocess.run(cmd, shell=True, creationflags=create_no_window)
            os.system = _new_system

        # 对于os.startfile，确保不创建控制台窗口
        if hasattr(os, 'startfile'):
            os._old_startfile = os.startfile
            def _new_startfile(path, operation=None):
                import subprocess
                subprocess.Popen(path, creationflags=subprocess.CREATE_NO_WINDOW)
            os.startfile = _new_startfile

def get_unique_filename(base_name, extension):
    """生成唯一的文件名，避免覆盖已存在的文件"""
    counter = 1
    new_name = f"{base_name}{extension}"
    while os.path.exists(new_name):
        new_name = f"{base_name}_{counter}{extension}"
        counter += 1
    return new_name


def extract_song_name(file_name):
    """从文件名中提取纯净的歌曲名：直接提取第一个空格前的字符串"""
    # 移除文件扩展名
    base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
    
    # 直接提取第一个空格前的字符串作为歌曲名
    # 如果没有空格，则使用整个文件名（移除扩展名后的部分）
    if ' ' in base_name:
        cleaned = base_name.split(' ', 1)[0]
    else:
        cleaned = base_name
    
    return cleaned


def next_power_of_2(n):
    """获取大于等于n的最小2的幂次方"""
    return 1 << (n - 1).bit_length()


def merge_segments(seg_list):
    """递归合并音频片段，采用2的n次方合并策略"""
    if len(seg_list) == 1:
        return seg_list[0]
    elif len(seg_list) == 2:
        return seg_list[0] + seg_list[1]
    else:
        mid = len(seg_list) // 2
        left = merge_segments(seg_list[:mid])
        right = merge_segments(seg_list[mid:])
        return left + right


def parallel_merge(segments, num_workers=8, min_segments=50, use_concurrency=True, status_callback=None):
    """使用线程池并行合并音频片段"""
    # 如果禁用了并发或者音频数量不足，不使用并发优化
    if not use_concurrency or len(segments) < min_segments:
        if status_callback:
            status_callback(f"{'禁用并发' if not use_concurrency else f'音频数量不足{min_segments}个'}，使用串行合并")
        return merge_segments(segments)
    
    if status_callback:
        status_callback(f"音频数量超过{min_segments}个，使用并行合并")
    
    # 确保分块数是2的幂次方
    num_chunks = next_power_of_2(len(segments))
    if num_chunks < 4:
        num_chunks = 4  # 至少8块
    
    # 计算每块的大小
    chunk_size = (len(segments) + num_chunks - 1) // num_chunks
    
    # 分块
    chunks = []
    for i in range(0, len(segments), chunk_size):
        chunks.append(segments[i:i+chunk_size])
    
    # 使用线程池合并每个块
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        merged_chunks = list(executor.map(merge_segments, chunks))
    
    # 递归合并所有块结果
    return merge_segments(merged_chunks)
