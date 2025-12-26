#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""常量配置文件"""

import os

# 倒计时音频文件常量
COUNTDOWN_FILENAMES = [
    "倒计时.mp3",
    "倒计时.MP3"
]

# 曲库目录名称
LIBRARY_DIR_NAME = "曲库"

# 随舞目录名称
DANCE_DIR_NAME = "随舞"

# 输出文件名前缀
OUTPUT_FILE_PREFIX = "output"

# 输出文件扩展名
OUTPUT_FILE_EXTENSION = ".mp3"

# 缓存过期时间（秒）- 30天
CACHE_EXPIRATION = 30 * 24 * 60 * 60

# 并行合并默认参数
PARALLEL_MERGE_DEFAULT_WORKERS = 8
PARALLEL_MERGE_DEFAULT_MIN_SEGMENTS = 50

# 并发控制默认参数
DEFAULT_MAX_WORKERS = min(os.cpu_count() + 1, 12) if os.cpu_count() else 8
DEFAULT_LOW_LOAD_WORKERS = max(2, int(DEFAULT_MAX_WORKERS / 2))
DEFAULT_HIGH_LOAD_WORKERS = DEFAULT_MAX_WORKERS

# 状态更新频率
STATUS_UPDATE_FREQUENCY = 10  # 每10个文件更新一次状态
PROGRESS_UPDATE_FREQUENCY = 5  # 每5%更新一次进度
