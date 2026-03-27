; REDSEC TOOLBOX v7.2 - Inno Setup Script
; Gera um instalador profissional setup.exe
; Download Inno Setup: https://jrsoftware.org/isdl.php
; ══════════════════════════════════════════════════════════════

#define MyAppName      "REDSEC TOOLBOX"
#define MyAppVersion   "7.2"
#define MyAppPublisher "GabrielRj6"
#define MyAppExeName   "REDSEC_TOOLBOX_v7.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=OUTPUT
OutputBaseFilename=REDSEC_TOOLBOX_v7_SETUP
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Cores do instalador (estilo dark/hacker)
WizardResizable=no
PrivilegesRequired=admin

; Tela de boas-vindas customizada
SetupAppRunningFile={#MyAppExeName}
UninstallDisplayName={#MyAppName} v{#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "startmenuicon"; Description: "Criar atalho no Menu Iniciar";      GroupDescription: "Atalhos:"

[Files]
Source: "OUTPUT\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Inclui assets se existirem
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\assets'))

[Icons]
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar Toolbox";   Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autostartmenu}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir REDSEC TOOLBOX agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Página de boas-vindas customizada
procedure InitializeWizard;
begin
  WizardForm.Color := clBlack;
  WizardForm.Font.Color := clLime;
end;
