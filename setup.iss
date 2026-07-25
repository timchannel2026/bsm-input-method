; BSM 筆順碼輸入法 — Inno Setup 安裝腳本
; 用於創建 Windows 安裝程序

[Setup]
AppName=BSM 筆順碼輸入法
AppVersion=2.0.0
AppPublisher=Community Rebuild
AppPublisherURL=https://github.com/yourusername/bsm-input-method
AppSupportURL=https://github.com/yourusername/bsm-input-method/issues
AppUpdatesURL=https://github.com/yourusername/bsm-input-method/releases
DefaultDirName={autopf}\BSM_InputMethod
DefaultGroupName=BSM 筆順碼輸入法
OutputDir=.\installer_output
OutputBaseFilename=BSM_筆順碼_v2.0.0_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesetraditional"; MessagesFile: "compiler:Languages\Chinese Traditional.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\BSM_筆順碼.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "bsm_final.db"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\BSM 筆順碼輸入法"; Filename: "{app}\BSM_筆順碼.exe}"
Name: "{group}\{cm:UninstallProgram,BSM 筆順碼輸入法}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\BSM 筆順碼輸入法"; Filename: "{app}\BSM_筆順碼.exe}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\BSM 筆順碼輸入法"; Filename: "{app}\BSM_筆順碼.exe}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\BSM_筆順碼.exe}"; Description: "{cm:LaunchProgram,BSM 筆順碼輸入法}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 可以在此添加註冊表項或其他安裝後操作
  end;
end;
