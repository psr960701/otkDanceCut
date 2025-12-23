#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs

# 读取文件内容
file_path = 'requirements.txt'

try:
    # 尝试用UTF-8读取
    with codecs.open(file_path, 'r', 'utf-8') as f:
        content = f.read()
    print('文件已用UTF-8成功读取')
except UnicodeDecodeError:
    try:
        # 尝试用GBK读取
        with codecs.open(file_path, 'r', 'gbk') as f:
            content = f.read()
        print('文件已用GBK成功读取')
    except UnicodeDecodeError:
        print('无法读取文件，请检查文件编码')
        exit(1)

# 用Windows默认编码(通常是GBK)重新保存文件
with codecs.open(file_path, 'w', 'gbk') as f:
    f.write(content)

print('文件已转换为GBK编码，可以正确处理中文注释了')
