; Inno Setup betiği - Plaka Tanıma Sistemi kurulum paketi.
; Derlemek için: Inno Setup Compiler (ISCC.exe) kurulu olmalıdır.
; https://jrsoftware.org/isdl.php
;
; build.bat bu betiği otomatik çalıştırır (ISCC PATH'te ise).
; Önkoşul: dist\PlakaTanimaSistemi\ klasörü (plakatanima.spec ile üretilir).

#define MyAppName "Plaka Tanima Sistemi"
#define MyAppVersion "1.0.0"
#define MyAppExeName "PlakaTanimaSistemi.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\PlakaTanimaSistemi
DefaultGroupName={#MyAppName}
OutputDir=..\installer_output
OutputBaseFilename=PlakaTanimaSistemi_Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Files]
Source: "..\dist\PlakaTanimaSistemi\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Uygulamayı başlat"; Flags: nowait postinstall skipifsilent
