@echo off
chcp 65001 >nul
echo 使用PyInstaller打包剪一剪应用程序...
echo.

echo 1. 清理旧的打包目录
if exist "dist" (
    rd /s /q "dist"
    echo    已删除dist目录
)

if exist "build" (
    rd /s /q "build"
    echo    已删除build目录
)

echo.
echo 2. 运行PyInstaller打包命令
pyinstaller 剪一剪.spec

if %errorlevel% == 0 (
    echo.
    echo ✓ PyInstaller打包成功完成!
    
    echo.
    echo 3. 复制打包结果到安装包目录
    if not exist "安装包\剪一剪" mkdir "安装包\剪一剪"
    xcopy /E /Y /Q "dist\剪一剪\*" "安装包\剪一剪\"
    
    echo.
    echo 4. 验证打包结果
    if exist "安装包\剪一剪\剪一剪.exe" (
        echo    ✓ 剪一剪.exe 文件存在
        echo.
        echo 现在可以运行 安装包\剪一剪\剪一剪.exe 来启动应用程序
    ) else (
        echo    ✗ 剪一剪.exe 文件不存在
    )
) else (
    echo.
    echo ✗ PyInstaller打包失败，错误代码: %errorlevel%
)

echo.
pause