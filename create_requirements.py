# -*- coding: utf-8 -*-

# 定义requirements内容
requirements_content = """# 音频处理库
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
Pillow>=9.0.0"""

# 以UTF-8 BOM格式保存文件，这样Windows下的程序就能正确识别编码
with open('requirements.txt', 'w', encoding='utf-8-sig') as f:
    f.write(requirements_content)

print("requirements.txt 文件已创建，包含中文注释并使用UTF-8 BOM编码")
