#define MyAppName "File Searcher"
#define MyAppExeName "FileSearcher.exe"
#define MyAppVersion "1.0.0"

[Setup]
AppId={{7B1D8C36-7B1F-4D0A-9F7A-0F2F7A3A9B1E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="fp" 
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=output
OutputBaseFilename=FileSearcher-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Tareas adicionales:"; Flags: unchecked

[Files]
; Asegúrate de construir con PyInstaller (onedir) antes: dist\FileSearcher
Source: "..\\dist\\FileSearcher\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

