
Set WshShell = CreateObject("WScript.Shell")
Set shortcut = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") & "\表情包分割器.lnk")
shortcut.TargetPath = "D:\表情包工具\dist\表情包分割器.exe"
shortcut.WorkingDirectory = "D:\表情包工具\dist"
shortcut.IconLocation = "D:\表情包工具\dist\表情包分割器.exe"
shortcut.Description = "表情包四宫格分割器"
shortcut.Save
