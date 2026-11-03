; TRAKKSTUDIO installer (Inno Setup 6).
; Version comes from the command line: ISCC /DMyVersion=1.0 installer/trakkstudio.iss
; (build_installer.py does this automatically from STABLE_VERSION).
; Expects dist/TRAKKSTUDIO.exe already built (python build_exe.py).

#ifndef MyVersion
  #define MyVersion "1.0"
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
OutputDir=..\dist
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
Source: "..\dist\TRAKKSTUDIO.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\NOTICE.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\THIRD-PARTY-NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\icon.ico"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\TRAKKSTUDIO"; Filename: "{app}\TRAKKSTUDIO.exe"
Name: "{group}\User manual"; Filename: "{app}\README.md"
Name: "{autodesktop}\TRAKKSTUDIO"; Filename: "{app}\TRAKKSTUDIO.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TRAKKSTUDIO.exe"; Description: "{cm:LaunchProgram,TRAKKSTUDIO}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Installed files only; per-user data (library.db) is left behind on purpose.
Type: files; Name: "{app}\README.md"
