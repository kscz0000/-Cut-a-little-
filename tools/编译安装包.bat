@echo off
chcp 65001 >nul
title 编译 Inno Setup 安装包

echo.
echo ========================================
echo        编译 Inno Setup 安装包
echo ========================================
echo.

:: 获取当前脚本目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..
set "RELEASE_DIR=%PROJECT_DIR%\releases\v2.0\jianyijian_v2.0_20251029_124038"

:: 检查是否有 Inno Setup
echo [1/3] 检查 Inno Setup 环境...

set "ISCC_PATH="
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "ISCC.exe" (
    set "ISCC_PATH=ISCC.exe"
) else (
    echo ✗ 未找到 Inno Setup
    echo.
    echo 请先安装 Inno Setup 6：
    echo   1. 访问：https://jrsoftware.org/isdl.php
    echo   2. 下载并安装 Inno Setup 6
    echo   3. 重新运行此脚本
    echo.
    echo 详细说明请查看：tools\手动安装InnoSetup.txt
    pause
    exit /b 1
)

echo ✓ 找到 Inno Setup: %ISCC_PATH%
echo.

:: 检查 setup.iss 文件
echo [2/3] 检查安装脚本...
if not exist "%RELEASE_DIR%\setup.iss" (
    echo ✗ 未找到 setup.iss 文件
    echo   路径: %RELEASE_DIR%\setup.iss
    pause
    exit /b 1
)
echo ✓ 安装脚本存在
echo.

:: 执行编译
echo [3/3] 开始编译安装包...
echo   输入目录: %RELEASE_DIR%
echo   脚本文件: setup.iss
echo.
echo 正在编译，请稍候...
echo ========================================
echo.

cd /d "%RELEASE_DIR%"
"%ISCC_PATH%" "setup.iss"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo          ✓ 编译成功完成！
    echo ========================================
    echo.
    echo 生成的安装包：
    echo   位置: %RELEASE_DIR%\剪一剪_V2.0_Setup.exe
    echo.
    dir "剪一剪_V2.0_Setup.exe" 2>nul
    echo.
    echo 您可以将此安装程序分发给用户！
    echo.
    echo 用户安装方法：
    echo   1. 双击运行 剪一剪_V2.0_Setup.exe
    echo   2. 按照安装向导完成安装
    echo   3. 安装后可在桌面和开始菜单找到
    echo.
) else (
    echo.
    echo ========================================
    echo          ✗ 编译失败！
    echo ========================================
    echo.
    echo 错误代码: %errorlevel%
    echo.
    echo 请检查：
    echo   1. setup.iss 脚本是否有错误
    echo   2. 所有依赖文件是否存在
    echo   3. 是否有足够的磁盘空间
    echo.
    echo 解决方案：
    echo   - 查看上方错误信息
    echo   - 检查 setup.iss 配置
    echo   - 确保 jianyijian.exe 文件完整
    echo.
)

pause
