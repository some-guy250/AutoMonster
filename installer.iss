#define MyAppName "AutoMonster"
#define MyAppPublisher "some-guy250"
#define MyAppURL "https://github.com/some-guy250/AutoMonster"
#define MyAppExeName "LauncherAutoMonster.exe"

; Read launcher version from launcher_version.txt
#define FileHandle
#define FileLine
#if FileExists("launcher_version.txt")
    #define FileHandle = FileOpen("launcher_version.txt")
    #define FileLine = FileRead(FileHandle)
    #define MyAppVersion = FileLine
    #expr FileClose(FileHandle)
#else
    #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{9C832C97-2F5E-4807-AA45-38B25DD77D6D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=AutoMonster_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "final_dist\LauncherAutoMonster.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "final_dist\AutoMonster.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "version.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent