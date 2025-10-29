; 剪一剪 安装程序脚本
; 使用 Inno Setup 6 创建

#define MyAppName "剪一剪"
#define MyAppVersion "2.0"
#define MyAppPublisher "表情包工具开发团队"
#define MyAppURL "https://github.com/your-repo/jianyijian"
#define MyAppExeName "jianyijian.exe"

[Setup]
; 基本信息
AppId={{A1B2C3D4-E5F6-7890-ABCD-123456789ABC}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=README.txt
InfoBeforeFile=README.txt
OutputDir=.
OutputBaseFilename=剪一剪_V2.0_Setup
; SetupIconFile=assets\app_icon.ico  ; 注释掉，如果需要图标请取消注释
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; 界面设置（可选）
; WizardImageFile=@AGI.png
; WizardSmallImageFile=assets\app_icon.ico

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1
Name: "addtopath"; Description: "添加到系统PATH环境变量（可选）"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "启动剪一剪.bat"; DestDir: "{app}"; Flags: ignoreversion
; 注意: 不需要复制依赖文件，因为EXE已经自包含

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{{cm:ProgramOnTheWeb,{#MyAppName}}}"; Filename: "{#MyAppURL}"
Name: "{group}\{{cm:UninstallProgram,{#MyAppName}}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; 可选：添加PATH环境变量
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
