# -*- mode: python ; coding: utf-8 -*-
# macOS 版本打包配置

import os
import sys

# 检查 ffmpeg 是否在系统中可用
ffmpeg_available = os.system('which ffmpeg > /dev/null 2>&1') == 0
ffprobe_available = os.system('which ffprobe > /dev/null 2>&1') == 0

binaries = []
if ffmpeg_available and ffprobe_available:
    # 获取系统 ffmpeg 路径
    import subprocess
    ffmpeg_path = subprocess.check_output(['which', 'ffmpeg']).decode().strip()
    ffprobe_path = subprocess.check_output(['which', 'ffprobe']).decode().strip()
    binaries = [(ffmpeg_path, '.'), (ffprobe_path, '.')]
    print(f"包含系统 ffmpeg: {ffmpeg_path}")
    print(f"包含系统 ffprobe: {ffprobe_path}")
else:
    print("警告: 系统未安装 ffmpeg/ffprobe，请先运行: brew install ffmpeg")

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=[('src/', 'src')],
    hiddenimports=[
        'src.utils',
        'src.utils.cache_utils', 
        'src.utils.fix_encoding', 
        'src.utils.update_cache', 
        'src.threads.worker_threads', 
        'src.core.audio_processor', 
        'src.ui.ui_components'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='音乐剪辑器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # Apple Silicon
    codesign_identity=None,
    entitlements_file=None,
)

# 创建 macOS .app 包
app = BUNDLE(
    exe,
    name='音乐剪辑器.app',
    icon=None,  # 可以添加 .icns 图标
    bundle_identifier='com.otakudance.cutter',
    version='0.1.5',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '0.1.5',
        'CFBundleVersion': '0.1.5',
    },
)
