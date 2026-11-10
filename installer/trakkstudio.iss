; TRAKKSTUDIO installer (Inno Setup 6).
; Version comes from the command line: ISCC /DMyVersion=1.0.2 installer/trakkstudio.iss
; (build_installer.py does this automatically from STABLE_VERSION).
; Expects the one-dir build in dist/portable/TRAKKSTUDIO (python build_portable.py).

#ifndef MyVersion
  #define MyVersion "1.0.2"
#endif

[Setup]
AppName=TRAKKSTUDIO
AppVersion={#MyVersion}
AppVerName=TRAKKSTUDIO {#MyVersion}
AppPublisher=ShardBeats
AppPublisherURL=https://github.com/shardbeats/TRAKKSTUDIO
DefaultDirName={autopf}\TRAKKSTUDIO
DefaultGroupName=TRAKKSTUDIO
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist-installer
OutputBaseFilename=TRAKKSTUDIO-Setup-{#MyVersion}
Compression=lzma2/max
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayName=TRAKKSTUDIO {#MyVersion}
; Portable data stays per-user, nothing is written to the install folder.

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\portable\TRAKKSTUDIO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TRAKKSTUDIO"; Filename: "{app}\TRAKKSTUDIO.exe"
Name: "{group}\User manual"; Filename: "{app}\README.md"
Name: "{autodesktop}\TRAKKSTUDIO"; Filename: "{app}\TRAKKSTUDIO.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TRAKKSTUDIO.exe"; Description: "{cm:LaunchProgram,TRAKKSTUDIO}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Installed files only; per-user data (library.db) is left behind on purpose.
Type: files; Name: "{app}\README.md"
