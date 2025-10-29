@echo off
chcp 65001 >nul
title 剪一剪 - 生成安装包

echo.
echo ========================================
echo      剪一剪 安装包生成工具 V2.0
echo ========================================
echo.

:: 获取当前日期时间作为版本号
for /f "tokens=2-4 delims=/ " %%A in ('date /t') do (
    set mydate=%%C%%B%%A
)
for /f "tokens=1-2 delims=: " %%A in ('time /t') do (
    set mytime=%%A%%B
)
set version=%mydate%_%mytime%
set version=%version:/=%

echo 当前版本号：%version%
echo.

:: 检查打包文件是否存在
if not exist "dist\剪一剪\剪一剪.exe" (
    echo ✗ 错误：未找到可执行文件
    echo   请先运行 "一键打包.bat" 完成打包
    echo.
    pause
    exit /b 1
)

echo ✓ 可执行文件检查通过
echo.

:: 创建发布目录
set release_dir=releases\v2.0\剪一剪V2.0_%version%安装包
if exist "%release_dir%" (
    rd /s /q "%release_dir%" 2>nul
)
mkdir "%release_dir%" 2>nul

echo 1. 复制可执行文件...
mkdir "%release_dir%\剪一剪" 2>nul
xcopy /E /Y /Q "dist\剪一剪\*" "%release_dir%\剪一剪\" >nul
echo    ✓ 已复制到 %release_dir%\剪一剪\

echo.
echo 2. 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title 剪一剪
echo echo 正在启动剪一剪表情包分割器...
echo "%~dp0剪一剪\剪一剪.exe"
) > "%release_dir%\启动剪一剪.bat"

echo    ✓ 已创建启动脚本

echo.
echo 3. 生成使用说明...
(
echo 剪一剪 V2.0 - 表情包分割器
echo.
echo ========================================
echo.
echo 如何使用：
echo.
echo 方法一：双击 "启动剪一剪.bat"
echo 方法二：直接运行 "剪一剪\剪一剪.exe"
echo.
echo 系统要求：
echo   - Windows 7/8/10/11
echo   - 不需要安装Python或其他依赖
echo.
echo 功能特点：
echo   ✨ 支持四宫格、九宫格分割
echo   ✨ 自定义行列数（1-18）
echo   ✨ 任意角度旋转
echo   ✨ 双屏实时预览
echo   ✨ 批量处理
echo   ✨ 智能边缘检测
echo.
echo 使用步骤：
echo   1. 运行剪一剪.exe
echo   2. 添加要分割的图片
echo   3. 调整行列数和旋转角度
echo   4. 点击"开始处理"
echo   5. 查看输出文件夹
echo.
echo 技术支持：
echo   - 如遇问题请查看应用内的帮助文档
echo   - 常见问题可参考 docs\ 目录下的文档
echo.
echo 版本信息：
echo   Build: %version%
echo   Date: %date% %time%
echo ========================================
) > "%release_dir%\使用说明.txt"

echo    ✓ 已生成使用说明

echo.
echo 4. 复制文档...
if exist "README.md" (
    copy "README.md" "%release_dir%\README.txt" >nul
    echo    ✓ 已复制 README
)
if exist "CHANGELOG.md" (
    copy "CHANGELOG.md" "%release_dir%\更新日志.txt" >nul
    echo    ✓ 已复制 更新日志
)

echo.
echo 5. 计算文件大小...
for /f "tokens=3" %%A in ('dir "%release_dir%" /-c ^| find "个文件"') do set file_count=%%A
for /f "tokens=3" %%B in ('dir "%release_dir%" /-c ^| find "个字节"') do set byte_count=%%B

echo    ✓ 文件数量：%file_count%
echo    ✓ 目录大小：%byte_count% 字节

echo.
echo ========================================
echo          ✓ 安装包生成完成！
echo ========================================
echo.
echo 安装包位置：
echo   %CD%\%release_dir%
echo.
echo 内容包含：
echo   - 剪一剪.exe（主程序）
echo   - 启动剪一剪.bat（启动脚本）
echo   - 使用说明.txt（使用指南）
echo   - README.txt（项目说明）
echo   - 更新日志.txt（版本更新）
echo.
echo 现在可以：
echo   1. 将整个安装包目录复制到其他电脑使用
echo   2. 压缩为zip文件分发
echo   3. 进一步测试应用功能
echo.
echo ========================================
echo.

pause
