#define MyAppName "AgendaCompPro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Claudeir de Souza Alves"
#define MyAppExeName "AgendaCompPro.exe"
#define MySourceDir "D:\Python\Agenda_comp_pro"
#define MyIconFile "D:\Python\Agenda_comp_pro\assets\agenda.ico"

[Setup]
AppId={{A1B2C3D4-E5F6-4711-8899-000000000000}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=AgendaCompPro_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#MyIconFile}
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=admin
DisableWelcomePage=no

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais"; Flags: unchecked

[Files]
Source: "D:\Python\Agenda_comp_pro\dist\AgendaCompPro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\services"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\ui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\utils"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\reports"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}*"; DestDir: "{app}\backups"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent