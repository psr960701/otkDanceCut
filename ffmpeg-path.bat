@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM 获取当前脚本所在的目录
set "script_dir=%~dp0"
set "ffmpeg_path=%script_dir%ffmpeg"

REM 检查ffmpeg文件夹是否存在
if exist "!ffmpeg_path!" (
    REM 检查系统PATH中是否已包含ffmpeg路径
    echo !PATH! | find /i "!ffmpeg_path!" > nul
    if errorlevel 1 (
        REM 路径不存在，添加到系统PATH
        set "new_path=!ffmpeg_path!;!PATH!"
        PowerShell.exe -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c setx PATH \"!new_path!\" /M'"
        echo ffmpeg文件夹已成功添加到系统PATH中。
        echo 请重启命令行或系统使设置生效。
    ) else (
        echo ffmpeg文件夹已经在系统PATH中。
    )
) else (
    echo 未找到ffmpeg文件夹，请确保脚本与ffmpeg文件夹在同一目录下。
)

endlocal

pause