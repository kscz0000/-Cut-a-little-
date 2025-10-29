@echo off
taskkill /f /im explorer.exe
cd %userprofile%\AppData\Local\Microsoft\Windows\Explorer
del iconcache* /a
start explorer.exe
echo 图标缓存已清理！
pause