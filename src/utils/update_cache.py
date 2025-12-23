#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from src.utils import cache_utils

# 缓存文件路径
duration_cache_file = "duration_cache.json"

# 读取原始缓存
original_cache = cache_utils.load_duration_cache(duration_cache_file)

# 创建新的缓存，使用文件名作为键
new_cache = {}

for file_path, duration in original_cache.items():
    # 提取文件名
    file_name = os.path.basename(file_path)
    
    # 如果文件名已经在新缓存中，跳过（保留第一个出现的）
    if file_name not in new_cache:
        new_cache[file_name] = duration

# 统计转换结果
original_count = len(original_cache)
new_count = len(new_cache)
duplicate_count = original_count - new_count

print(f"原始缓存条目数: {original_count}")
print(f"新缓存条目数: {new_count}")
print(f"移除的重复条目数: {duplicate_count}")

# 保存新的缓存
cache_utils.save_duration_cache(duration_cache_file, new_cache)

print(f"已成功更新缓存文件: {duration_cache_file}")
