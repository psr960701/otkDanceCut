@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ==================================================
echo ffmpeg环境变量配置工具
echo ==================================================
echo.

REM 检查是否以管理员权限运行
net session > nul 2>&1
if %errorlevel% neq 0 (
    echo 权限不足：需要管理员权限来修改系统环境变量！
    echo.
    echo 请按照以下步骤操作：
    echo 1. 右键点击本脚本文件
    echo 2. 选择 "以管理员身份运行"
    echo 3. 重新执行本脚本
    echo.
    goto :end
)

REM 获取当前脚本所在的目录
set "script_dir=%~dp0"
set "ffmpeg_path=%script_dir%ffmpeg"

REM 检查ffmpeg文件夹是否存在
if exist "!ffmpeg_path!" (
    echo 已找到ffmpeg文件夹：!ffmpeg_path!
    echo.
    
    REM 检查系统PATH中是否已包含ffmpeg路径
    echo !PATH! | find /i "!ffmpeg_path!" > nul
    if errorlevel 1 (
        REM 路径不存在，添加到系统PATH
        echo 正在将ffmpeg添加到系统PATH环境变量...
        echo.
        set "new_path=!ffmpeg_path!;!PATH!"
        PowerShell.exe -Command "setx PATH \"!new_path!\" /M"
        
        if !errorlevel! equ 0 (
            echo 成功：ffmpeg文件夹已添加到系统PATH中！
            echo.
            echo 注意：请重启所有打开的命令行窗口或系统使设置生效。
        ) else (
            echo 失败：添加系统PATH环境变量时出错。
            echo 请手动将以下路径添加到系统环境变量PATH中：
            echo !ffmpeg_path!
        )
    ) else (
        echo 信息：ffmpeg文件夹已经在系统PATH中，无需重复添加。
    )
) else (
    echo 错误：未找到ffmpeg文件夹！
    echo 请确保ffmpeg文件夹与本脚本位于同一目录下。
    echo 预期路径：!script_dir!ffmpeg
)

echo.
echo ==================================================

:end
endlocal

pause