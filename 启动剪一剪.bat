@echo off
chcp 65001 >nul
title 剪一剪 - 表情包分割器

echo.
echo ========================================
echo      剪一剪 表情包分割器 V2.0
echo ========================================
echo.

:: 检查依赖
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 错误：未检测到Python
    echo.
    echo   请先安装Python 3.8+ 并添加到PATH
    echo   下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 检查源码文件
if not exist "src\main_qt.py" (
    echo ✗ 错误：未找到源代码
    echo   请确保在项目根目录运行
    echo.
    pause
    exit /b 1
)

:: 检查依赖包
echo 检查依赖包...
python -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ PyQt6 未安装，正在安装...
    pip install PyQt6
    if %errorlevel% neq 0 (
        echo ✗ 安装失败，请手动运行：
        echo    pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo ✓ 环境检查通过
echo.
echo 正在启动剪一剪...
echo.

:: 启动应用
cd /d "%~dp0"
python src\main_qt.py

:: 检查退出码
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo            程序异常退出
    echo ========================================
    echo.
    echo 可能的解决方案：
    echo   1. 查看上方错误信息
    echo   2. 运行 "scripts\错误诊断.bat" 进行诊断
    echo   3. 确保所有依赖已安装：
    echo      pip install -r requirements.txt
    echo.
    pause
)
