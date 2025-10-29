# 创建"剪一剪"安装包
Write-Host "正在创建'剪一剪'安装包..." -ForegroundColor Green
Write-Host ""

# 定义路径
$SourcePath = "D:\表情包工具\剪一剪\build\exe.win-amd64-3.13"
$InstallPath = "D:\表情包工具\剪一剪\安装包\剪一剪"
$DesktopPath = [Environment]::GetFolderPath("Desktop")

# 创建安装包目录
if (!(Test-Path "D:\表情包工具\剪一剪\安装包")) {
    New-Item -ItemType Directory -Path "D:\表情包工具\剪一剪\安装包" | Out-Null
}

# 删除旧的安装目录（如果存在）
if (Test-Path $InstallPath) {
    Remove-Item -Path $InstallPath -Recurse -Force
}

# 创建新的安装目录
New-Item -ItemType Directory -Path $InstallPath | Out-Null

# 复制所有文件到安装目录
Write-Host "正在复制文件..." -ForegroundColor Yellow
Copy-Item -Path "$SourcePath\*" -Destination $InstallPath -Recurse

# 创建桌面快捷方式
Write-Host "正在创建桌面快捷方式..." -ForegroundColor Yellow
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\剪一剪.lnk")
$Shortcut.TargetPath = "$InstallPath\剪一剪.exe"
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.IconLocation = "$InstallPath\assets\app_icon.ico"
$Shortcut.Save()

Write-Host ""
Write-Host "安装包创建完成！" -ForegroundColor Green
Write-Host "安装目录: $InstallPath" -ForegroundColor Cyan
Write-Host "桌面快捷方式已创建" -ForegroundColor Cyan
Write-Host ""

Write-Host "按任意键退出..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")