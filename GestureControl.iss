; Instalador de GestureControl (Inno Setup 6)
; Uso: ISCC.exe GestureControl.iss
; Requiere haber compilado antes con PyInstaller (carpeta dist\GestureControl)

#define MyAppName "GestureControl"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "pepehalfonso"
#define MyAppURL "https://github.com/pepehalfonso/app-gestos-webcam"
#define MyAppExeName "GestureControl.exe"

[Setup]
AppId={{8F3A2B1C-7D4E-4A5F-9C1D-GESTURE01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Setup_GestureControl_v1.0.0
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} - controla tu PC con gestos de la mano
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher} (MIT)
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Iconos:"; Flags: unchecked
Name: "startup"; Description: "Iniciar con Windows"; GroupDescription: "Arranque:"; Flags: unchecked

[Files]
Source: "dist\GestureControl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar GestureControl ahora"; Flags: nowait postinstall skipifsilent
