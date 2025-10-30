Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShellLink = WshShell.CreateShortcut(strDesktop & "\剪一剪.lnk")
oShellLink.TargetPath = "D:\表情包工具\剪一剪\安装包\剪一剪\剪一剪.exe"
oShellLink.WorkingDirectory = "D:\表情包工具\剪一剪\安装包\剪一剪"
oShellLink.IconLocation = "D:\表情包工具\剪一剪\安装包\剪一剪\assets\app_icon.ico"
oShellLink.Save