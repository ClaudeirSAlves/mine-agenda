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
Name: "portuguese"; MessagesFile: "compiler:Languages\\Portuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais"; Flags: unchecked

[Files]
; Executável final
Source: "{#MySourceDir}\\dist\\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Apenas pastas importantes do projeto (copiadas como estão no projeto real)
Source: "{#MySourceDir}\\assets\\*"; DestDir: "{app}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MySourceDir}\\gui\\*"; DestDir: "{app}\\gui"; Flags: ignoreversion recursesubdirs createallsubdirs

; Arquivos principais do projeto
Source: "{#MySourceDir}\\AgendaCompPro.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}\\config.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}\\models.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}\\services.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}\\utils.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MySourceDir}\\main.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent
