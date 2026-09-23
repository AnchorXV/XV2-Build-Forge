#define MyAppName        "DBXV2 Build Forge"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "DBXV2Modding"
#define MyAppExeName     "DBXV2_Build_Forge.exe"
#define MySourceDir      "main.dist"
#define MyOutputDir      "build\installer"

[Setup]
AppId={{51C2C90A-9B3B-4D30-80E2-BCDA4CA7B3AF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=no
PrivilegesRequired=admin
OutputDir={#MyOutputDir}
OutputBaseFilename=Setup_{#MyAppName}_v{#MyAppVersion}
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[UninstallDelete]
Type: filesandordirs; Name: "{app}\*"

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
