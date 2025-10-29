# 剪一剪 PowerShell 安装脚本
# 需要管理员权限运行

param(
    [string]$InstallPath = "",
    [switch]$CreateDesktopIcon = $true,
    [switch]$CreateStartMenu = $true,
    [switch]$RunAfterInstall = $false
)

# 颜色设置
$ForegroundColor = "Cyan"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$ErrorColor = "Red"

Write-Host "`n========================================" -ForegroundColor $ForegroundColor
Write-Host "        剪一剪 安装程序 V2.0" -ForegroundColor $ForegroundColor
Write-Host "========================================`n" -ForegroundColor $ForegroundColor

# 检查管理员权限
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "⚠ 警告：建议以管理员身份运行以获得最佳体验" -ForegroundColor $WarningColor
    Write-Host "  右键点击此文件 → 以管理员身份运行`n" -ForegroundColor $WarningColor
}

# 配置信息
$appName = "剪一剪"
$appVersion = "2.0"
$exeName = "jianyijian.exe"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($InstallPath -eq "") {
    $InstallPath = "$env:ProgramFiles\$appName"
}

Write-Host "安装配置：" -ForegroundColor $ForegroundColor
Write-Host "  应用名称：$appName" -ForegroundColor $ForegroundColor
Write-Host "  版本：$appVersion" -ForegroundColor $ForegroundColor
Write-Host "  目标路径：$InstallPath" -ForegroundColor $ForegroundColor
Write-Host ""

# 确认安装
$confirm = Read-Host "是否开始安装？(Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "安装已取消" -ForegroundColor $WarningColor
    exit 0
}

# 创建安装目录
Write-Host "`n[1/4] 正在创建安装目录..." -ForegroundColor $ForegroundColor
try {
    if (!(Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    }
    Write-Host "✓ 安装目录创建成功" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ 创建目录失败：$($_.Exception.Message)" -ForegroundColor $ErrorColor
    exit 1
}

# 复制文件
Write-Host "`n[2/4] 正在复制文件..." -ForegroundColor $ForegroundColor
try {
    Copy-Item -Path "$scriptDir\$exeName" -Destination $InstallPath -Force
    Copy-Item -Path "$scriptDir\README.txt" -Destination $InstallPath -Force
    Copy-Item -Path "$scriptDir\启动剪一剪.bat" -Destination $InstallPath -Force
    Write-Host "✓ 文件复制完成" -ForegroundColor $SuccessColor
} catch {
    Write-Host "✗ 文件复制失败：$($_.Exception.Message)" -ForegroundColor $ErrorColor
    exit 1
}

# 创建桌面快捷方式
if ($CreateDesktopIcon) {
    Write-Host "`n[3/4] 正在创建快捷方式..." -ForegroundColor $ForegroundColor
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $desktopPath = [Environment]::GetFolderPath('Desktop')
        $shortcut = $WshShell.CreateShortcut("$desktopPath\$appName.lnk")
        $shortcut.TargetPath = "$InstallPath\$exeName"
        $shortcut.WorkingDirectory = $InstallPath
        $shortcut.Description = "剪一剪 - 表情包分割器 V2.0"
        # 尝试设置图标（如果图标文件存在）
        if (Test-Path "$scriptDir\..\assets\app_icon.ico") {
            $shortcut.IconLocation = "$scriptDir\..\assets\app_icon.ico"
        }
        $shortcut.Save()

        Write-Host "  ✓ 桌面快捷方式创建成功" -ForegroundColor $SuccessColor
    } catch {
        Write-Host "  ✗ 桌面快捷方式创建失败：$($_.Exception.Message)" -ForegroundColor $ErrorColor
    }
}

# 创建开始菜单项
if ($CreateStartMenu) {
    try {
        $startMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
        if (!(Test-Path "$startMenuPath\$appName")) {
            New-Item -ItemType Directory -Path "$startMenuPath\$appName" -Force | Out-Null
        }

        $WshShell = New-Object -ComObject WScript.Shell
        $shortcut = $WshShell.CreateShortcut("$startMenuPath\$appName\$appName.lnk")
        $shortcut.TargetPath = "$InstallPath\$exeName"
        $shortcut.WorkingDirectory = $InstallPath
        $shortcut.Description = "剪一剪 - 表情包分割器 V2.0"
        if (Test-Path "$scriptDir\..\assets\app_icon.ico") {
            $shortcut.IconLocation = "$scriptDir\..\assets\app_icon.ico"
        }
        $shortcut.Save()

        Write-Host "  ✓ 开始菜单项创建成功" -ForegroundColor $SuccessColor
    } catch {
        Write-Host "  ✗ 开始菜单项创建失败：$($_.Exception.Message)" -ForegroundColor $ErrorColor
    }

    # 创建卸载程序
    try {
        $uninstallScript = @"
@echo off
chcp 65001 >nul
title 卸载 $appName

cls
echo.
echo ========================================
echo           卸载 $appName
echo ========================================
echo.
echo 确认要卸载 $appName 吗？
echo.

set /p "UNINSTALL=输入 Y 确认卸载，其他键取消: "
if /i "%UNINSTALL%"=="Y" (
    echo.
    echo 正在卸载...

    :: 删除开始菜单项
    del /q "$startMenuPath\$appName\$appName.lnk" 2>nul
    rmdir "$startMenuPath\$appName" 2>nul

    :: 删除桌面快捷方式
    del /q "$desktopPath\$appName.lnk" 2>nul

    echo.
    echo 是否删除程序文件？
    set /p "DELETE=输入 Y 删除程序文件: "
    if /i "%DELETE%"=="Y" (
        rmdir /s /q "$InstallPath"
        echo 程序文件已删除
    )

    echo.
    echo 卸载完成！
    pause
)
"@
        $uninstallScript | Out-File -FilePath "$InstallPath\卸载.bat" -Encoding UTF8
        Write-Host "  ✓ 卸载程序创建成功" -ForegroundColor $SuccessColor
    } catch {
        Write-Host "  ✗ 卸载程序创建失败：$($_.Exception.Message)" -ForegroundColor $ErrorColor
    }
}

# 安装完成
Write-Host "`n========================================" -ForegroundColor $SuccessColor
Write-Host "          ✓ 安装完成！" -ForegroundColor $SuccessColor
Write-Host "========================================`n" -ForegroundColor $SuccessColor

Write-Host "安装信息：" -ForegroundColor $ForegroundColor
Write-Host "  安装路径：$InstallPath" -ForegroundColor $ForegroundColor
Write-Host "  可执行文件：$InstallPath\$exeName" -ForegroundColor $ForegroundColor
Write-Host ""
Write-Host "启动方式：" -ForegroundColor $ForegroundColor
Write-Host "  • 双击桌面快捷方式 ""$appName""" -ForegroundColor $ForegroundColor
Write-Host "  • 在开始菜单中搜索 ""$appName""" -ForegroundColor $ForegroundColor
Write-Host "  • 直接运行 ""$InstallPath\$exeName""" -ForegroundColor $ForegroundColor
Write-Host ""
Write-Host "卸载方式：" -ForegroundColor $ForegroundColor
Write-Host "  • 运行 ""$InstallPath\卸载.bat""" -ForegroundColor $ForegroundColor
Write-Host "  • 在控制面板 → 程序中卸载" -ForegroundColor $ForegroundColor
Write-Host ""
Write-Host "========================================" -ForegroundColor $SuccessColor

# 询问是否立即运行
if ($RunAfterInstall) {
    $response = "Y"
} else {
    $response = Read-Host "是否立即运行 $appName？(Y/N)"
}

if ($response -eq "Y" -or $response -eq "y") {
    Start-Process -FilePath "$InstallPath\$exeName"
    Write-Host "`n正在启动应用..." -ForegroundColor $SuccessColor
}

Write-Host "`n感谢使用 $appName！" -ForegroundColor $SuccessColor
Write-Host "按任意键退出..." -ForegroundColor $ForegroundColor
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
