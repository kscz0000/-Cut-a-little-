@echo off
chcp 65001 >nul
title 下载 Inno Setup

echo.
echo ========================================
echo        下载 Inno Setup 6
echo ========================================
echo.

set "INNO_URL=https://jrsoftware.org/download/6/InnoSetup.exe"
set "INNO_INSTALLER=tools\InnoSetup.exe"

echo 正在下载 Inno Setup 安装程序...
echo 下载地址: %INNO_URL%
echo.

:: 使用 PowerShell 下载文件
powershell -Command "(New-Object Net.WebClient).DownloadFile('%INNO_URL%', '%INNO_INSTALLER%')"

if exist "%INNO_INSTALLER%" (
    echo.
    echo ✓ 下载完成！
    echo 文件位置: %CD%\%INNO_INSTALLER%
    echo.
    echo 下一步：
    echo   1. 运行 %INNO_INSTALLER% 进行安装
    echo   2. 安装完成后，回到此目录
    echo   3. 双击 "编译安装包.bat"
    echo.
    pause
) else (
    echo.
    echo ✗ 下载失败！
    echo.
    echo 手动下载方法：
    echo   1. 浏览器打开：https://jrsoftware.org/isdl.php
    echo   2. 点击 "Download Inno Setup 6"
    echo   3. 将下载的文件保存到 tools\ 目录
    echo   4. 双击安装
    echo.
    pause
)
