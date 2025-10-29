@echo off
chcp 65001 >nul
title 剪一剪 - 安装程序

echo.
echo ========================================
echo        剪一剪 安装程序 V2.0
echo ========================================
echo.
echo 正在安装剪一剪到您的电脑...
echo.

:: 获取当前脚本目录
set "INSTALL_DIR=%~dp0"
set "APP_NAME=剪一剪"
set "EXE_NAME=jianyijian.exe"

:: 默认安装路径
set "TARGET_DIR=%ProgramFiles%\%APP_NAME%"

:: 提示用户选择安装位置
echo 默认安装路径: %TARGET_DIR%
echo.
set /p "INSTALL_PATH=请输入安装路径（直接回车使用默认路径）: "
if "%INSTALL_PATH%"=="" set "INSTALL_PATH=%TARGET_DIR%"

:: 检查是否有管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ⚠ 警告：建议以管理员身份运行以获得最佳体验
    echo   右键点击此文件 ^> 以管理员身份运行
    echo.
    pause
)

:: 创建安装目录
echo.
echo 正在创建安装目录...
if not exist "%INSTALL_PATH%" mkdir "%INSTALL_PATH%"

:: 复制文件
echo 正在复制文件...
copy /Y "%INSTALL_DIR%%EXE_NAME%" "%INSTALL_PATH%\" >nul
if %errorlevel% neq 0 (
    echo ✗ 文件复制失败！
    pause
    exit /b 1
)

copy /Y "%INSTALL_DIR%README.txt" "%INSTALL_PATH%\" >nul
copy /Y "%INSTALL_DIR%启动剪一剪.bat" "%INSTALL_PATH%\" >nul

echo ✓ 文件复制完成
echo.

:: 创建桌面快捷方式
echo 正在创建桌面快捷方式...
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%UserProfile%\Desktop\%APP_NAME%.lnk'); $Shortcut.TargetPath = '%INSTALL_PATH%\%EXE_NAME%'; $Shortcut.WorkingDirectory = '%INSTALL_PATH%'; $Shortcut.Description = '剪一剪 - 表情包分割器'; $Shortcut.Save()}" >nul 2>&1

if exist "%UserProfile%\Desktop\%APP_NAME%.lnk" (
    echo ✓ 桌面快捷方式创建成功
) else (
    echo ✗ 桌面快捷方式创建失败
)

:: 创建开始菜单项
echo 正在创建开始菜单项...
set "START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs"
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\%APP_NAME%\%APP_NAME%.lnk'); $Shortcut.TargetPath = '%INSTALL_PATH%\%EXE_NAME%'; $Shortcut.WorkingDirectory = '%INSTALL_PATH%'; $Shortcut.Description = '剪一剪 - 表情包分割器'; $Shortcut.Save()}" >nul 2>&1

if exist "%START_MENU%\%APP_NAME%\%APP_NAME%.lnk" (
    echo ✓ 开始菜单项创建成功
) else (
    echo ✗ 开始菜单项创建失败
)

:: 创建卸载程序
echo 正在创建卸载程序...
(
echo @echo off
echo chcp 65001 ^>nul
echo title 卸载剪一剪
echo.
echo 确认要卸载剪一剪吗？
echo.
set /p "UNINSTALL=输入 Y 确认卸载，其他键取消: "
echo.
if /i "%%UNINSTALL%%"=="Y" ^(
    echo 正在卸载...
    del /q "%START_MENU%\%APP_NAME%\%APP_NAME%.lnk" 2^>nul
    rmdir "%START_MENU%\%APP_NAME%" 2^>nul
    del /q "%UserProfile%\Desktop\%APP_NAME%.lnk" 2^>nul
    echo.
    echo 是否删除程序文件？
    set /p "DELETE_FILES=输入 Y 删除程序文件: "
    if /i "%%DELETE_FILES%%"=="Y" ^(
        rmdir /s /q "%INSTALL_PATH%"
        echo 程序文件已删除
    ^)
    echo.
    echo 卸载完成！
    pause
^)
) > "%INSTALL_PATH%\卸载.bat"

echo ✓ 卸载程序创建完成
echo.

:: 安装完成
echo ========================================
echo          ✓ 安装完成！
echo ========================================
echo.
echo 安装信息：
echo   安装路径：%INSTALL_PATH%
echo   可执行文件：%INSTALL_PATH%\%EXE_NAME%
echo.
echo 启动方式：
echo   1. 双击桌面快捷方式 "%APP_NAME%"
echo   2. 在开始菜单中搜索 "%APP_NAME%"
echo   3. 直接运行 "%INSTALL_PATH%\%EXE_NAME%"
echo.
echo 卸载方式：
echo   运行 "%INSTALL_PATH%\卸载.bat"
echo   或在控制面板 ^> 程序中卸载
echo.
echo ========================================
echo.

:: 询问是否立即运行
set /p "RUN_APP=是否立即运行剪一剪？(Y/N): "
if /i "%RUN_APP%"=="Y" (
    start "" "%INSTALL_PATH%\%EXE_NAME%"
)

echo 感谢使用剪一剪！
pause
