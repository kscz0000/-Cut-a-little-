@echo off
chcp 65001 >nul
title 剪一剪 - 一键打包工具

echo.
echo ========================================
echo        剪一剪 表情包分割器 V2.0
echo           PyInstaller 一键打包
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 错误：未检测到Python，请先安装Python 3.8+
    echo   下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ 检测到Python环境

:: 检查PyInstaller是否安装
pip show PyInstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠ PyInstaller未安装，正在自动安装...
    pip install PyInstaller
    if %errorlevel% neq 0 (
        echo ✗ PyInstaller安装失败
        pause
        exit /b 1
    )
    echo ✓ PyInstaller安装成功
) else (
    echo ✓ PyInstaller已安装
)

echo.
echo 1. 清理旧的打包目录...
if exist "dist" (
    rd /s /q "dist" 2>nul
    echo    ✓ 已删除 dist 目录
)
if exist "build" (
    rd /s /q "build" 2>nul
    echo    ✓ 已删除 build 目录
)
if exist "*.spec" (
    del /q "*.spec" 2>nul
    echo    ✓ 已清理旧配置
)

echo.
echo 2. 验证依赖...
pip list | findstr "PyQt6\|Pillow\|opencv\|numpy" >nul
if %errorlevel% neq 0 (
    echo ⚠ 检测到依赖缺失，正在安装基础依赖...
    pip install -r requirements.txt
    echo ✓ 依赖安装完成
) else (
    echo ✓ 依赖检查通过
)

echo.
echo 3. 执行PyInstaller打包...
echo    配置文件：剪一剪.spec
echo    源码目录：src\main_qt.py
echo.

pyinstaller --clean --noconfirm 剪一剪.spec

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo         ✓ 打包成功完成！
    echo ========================================
    echo.

    :: 验证打包结果
    if exist "dist\剪一剪\剪一剪.exe" (
        echo ✓ 主程序文件：dist\剪一剪\剪一剪.exe

        :: 检查文件大小
        for %%A in ("dist\剪一剪\剪一剪.exe") do set size=%%~zA
        set /a size_mb=%size%/1024/1024
        echo ✓ 文件大小：%size_mb% MB

        echo.
        echo ========================================
        echo          可执行文件位置
        echo ========================================
        echo   %CD%\dist\剪一剪\剪一剪.exe
        echo.
        echo   双击上述路径即可运行应用
        echo ========================================
    ) else (
        echo ✗ 警告：未找到剪一剪.exe文件
    )
) else (
    echo.
    echo ========================================
    echo         ✗ 打包失败！
    echo ========================================
    echo.
    echo   常见错误及解决方案：
    echo.
    echo   1. 模块导入错误
    echo      - 检查 requirements.txt 是否完整
    echo      - 运行：pip install -r requirements.txt
    echo.
    echo   2. 权限不足
    echo      - 以管理员身份运行此脚本
    echo.
    echo   3. 防病毒软件干扰
    echo      - 将项目目录加入白名单
    echo      - 临时关闭实时防护
    echo.
    echo   4. 其他错误
    echo      - 查看上方的错误信息
    echo      - 运行：python -c "import src.main_qt"
    echo        检查源码是否有语法错误
)

echo.
pause
