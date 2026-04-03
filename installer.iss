; DEDSEC TOOLBOX v10.0 GOLD - Inno Setup Script
; Gera um instalador profissional setup.exe
; Download Inno Setup: https://jrsoftware.org/isdl.php
; ══════════════════════════════════════════════════════════════

#define MyAppName      "DEDSEC TOOLBOX"
#define MyAppVersion   "10.0"
#define MyAppPublisher "GabrielRj6"
#define MyAppExeName   "DEDSEC_TOOLBOX_v10.exe"

[Setup]
AppId={{DED5EC10-F6E2-4D90-A1B2-C3D4E5F67890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=OUTPUT
OutputBaseFilename=DEDSEC_TOOLBOX_v10_SETUP
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
PrivilegesRequired=admin

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "startmenuicon"; Description: "Criar atalho no Menu Iniciar";      GroupDescription: "Atalhos:"

[Files]
Source: "OUTPUT\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "meus_scripts\*"; DestDir: "{app}\meus_scripts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar DEDSEC";   Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autostartmenu}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir DEDSEC TOOLBOX agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure InitializeWizard;
begin
  WizardForm.Color := clBlack;
  WizardForm.Font.Name := 'Courier New';
end;
