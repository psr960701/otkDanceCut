# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[('ffmpeg/ffmpeg.exe', 'ffmpeg'), ('ffmpeg/ffprobe.exe', 'ffmpeg')],
    datas=[('src/', 'src')],
    hiddenimports=['src.utils', 'src.utils.cache_utils', 'src.utils.fix_encoding', 'src.utils.update_cache', 'src.threads.worker_threads', 'src.core.audio_processor', 'src.ui.ui_components'],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
