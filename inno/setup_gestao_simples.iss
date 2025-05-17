; Script para Inno Setup - Gestão Simples
[Setup]
AppName=Gestão Simples
AppVersion=0.2.2
AppPublisher=WolkerDias
AppPublisherURL=https://github.com/WolkerDias/gestao-simples
AppSupportURL=https://github.com/WolkerDias/gestao-simples/blob/main/README.md
AppUpdatesURL=https://github.com/WolkerDias/gestao-simples
DefaultDirName={autopf}\GestaoSimples
PrivilegesRequired=admin
DefaultGroupName=Gestão Simples
OutputDir=..\dist\v{#SetupSetting("AppVersion")}
OutputBaseFilename=GestaoSimples_v{#SetupSetting("AppVersion")}_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=..\icon.ico
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog


ShowLanguageDialog=yes
LanguageDetectionMethod=locale

[Languages]
Name: "brazilianportuguese"; MessagesFile: "BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
; Concede permissões modificadas (ler/escrever) para todos os usuários
Name: "{app}\gestao_simples\tmp"; Permissions: users-modify

[Files]
Source: "..\build\exe.win-amd64-3.11\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Inclui todos os arquivos necessários
Source: "..\gestao_simples\.env"; DestDir: "{app}\gestao_simples"; Flags: ignoreversion; 

; Adicione esta linha para incluir o ícone no pacote de instalação
Source: "..\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Adicione outros arquivos necessários aqui

[Icons]
Name: "{group}\Gestão Simples"; Filename: "{app}\gestao-simples.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\Gestão Simples"; Filename: "{app}\gestao-simples.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\gestao-simples.exe"; Description: "{cm:LaunchProgram,Gestão Simples}"; Flags: nowait postinstall skipifsilent
; Oculta o arquivo .env após a instalação
Filename: "attrib.exe"; Parameters: "+H ""{app}\gestao_simples\.env"""; Flags: runhidden

[UninstallRun]
Filename: "{app}\stop_server.bat"; Flags: runhidden; RunOnceId: "StopServer"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"