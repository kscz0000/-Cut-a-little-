@echo off
chcp 65001 >nul
title 剪一剪 - 错误诊断工具

echo.
echo ========================================
echo        剪一剪 错误诊断工具
echo     用于排查打包和运行问题
echo ========================================
echo.

set error_count=0

echo 1. 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ Python未安装或未添加到PATH
    set /a error_count+=1
) else (
    for /f "tokens=2" %%A in ('python --version 2^>^&1') do set pyver=%%A
    echo    ✓ Python版本：%pyver%
)

echo.
echo 2. 检查当前目录...
if not exist "src\main_qt.py" (
    echo    ✗ 未找到 src\main_qt.py，请在项目根目录运行
    set /a error_count+=1
) else (
    echo    ✓ 源代码目录正确
)

echo.
echo 3. 检查依赖包...
echo    检查中...

pip show PyQt6 >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ PyQt6 未安装
    set /a error_count+=1
) else (
    for /f "tokens=2" %%A in ('pip show PyQt6 ^| findstr "Version"') do set qtv=%%A
    echo    ✓ PyQt6 版本：%qtv%
)

pip show Pillow >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ Pillow 未安装
    set /a error_count+=1
) else (
    for /f "tokens=2" %%A in ('pip show Pillow ^| findstr "Version"') do set pilv=%%A
    echo    ✓ Pillow 版本：%pilv%
)

pip show opencv-python-headless >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ opencv-python-headless 未安装
    set /a error_count+=1
) else (
    for /f "tokens=2" %%A in ('pip show opencv-python-headless ^| findstr "Version"') do set cvv=%%A
    echo    ✓ OpenCV 版本：%cvv%
)

pip show numpy >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ numpy 未安装
    set /a error_count+=1
) else (
    for /f "tokens=2" %%A in ('pip show numpy ^| findstr "Version"') do set npv=%%A
    echo    ✓ numpy 版本：%npv%
)

pip show PyInstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ PyInstaller 未安装
    set /a error_count+=1
) else (
    for /f "tokens=2" %%A in ('pip show PyInstaller ^| findstr "Version"') do set piv=%%A
    echo    ✓ PyInstaller 版本：%piv%
)

echo.
echo 4. 检查资源文件...
if not exist "assets\app_icon.ico" (
    echo    ✗ app_icon.ico 不存在
    set /a error_count+=1
) else (
    echo    ✓ 图标文件存在
)

if not exist "剪一剪.spec" (
    echo    ⚠ 配置文件剪一剪.spec 不存在
) else (
    echo    ✓ 配置文件存在
)

echo.
echo 5. 测试源代码语法...
cd src
python -m py_compile main_qt.py >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ 源代码语法错误
    set /a error_count+=1
) else (
    echo    ✓ 源代码语法正确
)
cd ..

echo.
echo 6. 检查模块导入...
python -c "from PyQt6.QtWidgets import QApplication" >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ PyQt6 导入失败
    set /a error_count+=1
) else (
    echo    ✓ PyQt6 导入正常
)

python -c "from PIL import Image" >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ Pillow 导入失败
    set /a error_count+=1
) else (
    echo    ✓ Pillow 导入正常
)

python -c "import cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo    ✗ OpenCV 导入失败
    set /a error_count+=1
) else (
    echo    ✓ OpenCV 导入正常
)

echo.
echo ========================================
echo            诊断结果汇总
echo ========================================
echo.

if %error_count% equ 0 (
    echo    ✓ 环境检查全部通过！
    echo.
    echo    建议下一步：
    echo      1. 运行 "一键打包.bat"
    echo      2. 如仍有问题，查看上方详细日志
) else (
    echo    ✗ 发现 %error_count% 个问题
    echo.
    echo    解决方案：
    echo.
    if pip show PyQt6 >nul 2>&1 (
    ) else (
        echo    1. 安装PyQt6：
        echo       pip install PyQt6
    )

    if pip show Pillow >nul 2>&1 (
    ) else (
        echo    2. 安装Pillow：
        echo       pip install Pillow
    )

    if pip show opencv-python-headless >nul 2>&1 (
    ) else (
        echo    3. 安装OpenCV：
        echo       pip install opencv-python-headless
    )

    if pip show numpy >nul 2>&1 (
    ) else (
        echo    4. 安装numpy：
        echo       pip install numpy
    )

    if pip show PyInstaller >nul 2>&1 (
    ) else (
        echo    5. 安装PyInstaller：
        echo       pip install PyInstaller
    )

    echo.
    echo    一键修复（推荐）：
    echo       pip install -r requirements.txt
)

echo.
echo ========================================
echo.
echo 如需更多信息，请查看：
echo   - requirements.txt （依赖列表）
echo   - README.md （项目文档）
echo   - scripts\ （打包脚本）
echo.
echo ========================================
echo.

pause
