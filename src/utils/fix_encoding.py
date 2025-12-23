# -*- coding: utf-8 -*-
import sys
import os

# 定义requirements.txt的内容
content = """# 音频处理库
pydub>=0.25.1
# 视频处理库
moviepy>=1.0.3
# GUI框架
PyQt5>=5.15.7
# 环境变量管理
python-dotenv>=1.0.0
# 日志库
loguru>=0.7.0
# 测试框架
pytest>=7.0.0
# 数值计算
numpy>=1.21.0
# 图像处理
Pillow>=9.0.0
# 交互式命令行工具
questionary>=1.10.0
"""

# 将内容保存为GBK编码
with open('requirements.txt', 'w', encoding='gbk') as f:
    f.write(content)

print("requirements.txt已保存为GBK编码，包含中文注释")
