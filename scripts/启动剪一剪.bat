@echo off
echo 正在启动剪一剪...
echo.

cd /d "D:\表情包工具\剪一剪\安装包\剪一剪"
if %errorlevel% == 0 (
    echo 已切换到工作目录
) else (
    echo 切换工作目录失败
    pause
    exit /b 1
)

echo 正在启动程序...
"剪一剪.exe"

if %errorlevel% == 0 (
    echo 程序启动成功
) else (
    echo 程序启动失败
    echo 错误代码: %errorlevel%
)

echo.
echo 按任意键退出...
pause >nul
