; =========================================================
;  Instalator gry Strzelnica "Mnożenie" (mkTabliczka)
;  Wymaga wcześniejszej kompilacji w trybie --onedir:
;    dist\tabliczka\tabliczka.exe
;    dist\tabliczka\_internal\...
;  Plik zapisany jako UTF-8 z BOM (polskie znaki).
; =========================================================

#define MyAppName      "mkTabliczka"
#define MyAppVersion   "1.6.0.0"
#define MyAppPublisher "Krzysztof Markowski"
#define MyAppExeName   "tabliczka.exe"
#define MyBuildDir     "dist\tabliczka"

[Setup]
AppId={{B1E0AA10-F609-46DC-9791-370176F92ED1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion={#MyAppVersion}

; Plik licencji
LicenseFile=Licencja.txt

; Domyślny folder instalacji
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Instalacja dla wszystkich użytkowników
PrivilegesRequired=admin

; 64-bitowy Python -> instalacja do "Program Files", a nie "Program Files (x86)"
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Folder docelowy i nazwa pliku instalatora
OutputDir=GitHub
OutputBaseFilename=Setup_{#MyAppName}_{#MyAppVersion}

; Ikony instalatora i wpisu w "Aplikacje i funkcje"
SetupIconFile=ikona.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Kompresja plików
Compression=lzma2/max
SolidCompression=yes

; Wygląd instalatora
WizardStyle=modern

; Zamyka działającą grę przed aktualizacją
CloseApplications=yes

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"

[Tasks]
; Opcja utworzenia skrótu na pulpicie (domyślnie zaznaczona)
Name: "desktopicon"; Description: "Utwórz skrót na Pulpicie"; GroupDescription: "Dodatkowe ikony:"

[Dirs]
; Wspólny folder rekordów - zapis dozwolony dla wszystkich użytkowników komputera
Name: "{commonappdata}\{#MyAppName}"; Permissions: users-modify

[InstallDelete]
; Przy aktualizacji: usuwa stary katalog _internal, żeby nie zostały w nim nieaktualne biblioteki
Type: filesandordirs; Name: "{app}\_internal"
; Pozostałości po wersji 1.4 (tryb --onefile, dźwięki obok .exe)
Type: files; Name: "{app}\dobrze.wav"
Type: files; Name: "{app}\zle.wav"
Type: files; Name: "{app}\strzal.wav"

[Files]
; Program po kompilacji PyInstallerem (ścieżki względem folderu ze skryptem .iss)
Source: "{#MyBuildDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Ikona dla skrótów
Source: "ikona.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Skrót w Menu Start
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\ikona.ico"
; Skrót do deinstalatora w Menu Start
Name: "{group}\Odinstaluj {#MyAppName}"; Filename: "{uninstallexe}"
; Skrót na pulpicie wszystkich użytkowników
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\ikona.ico"; Tasks: desktopicon

[Run]
; Opcja uruchomienia gry od razu po zakończeniu instalacji
Filename: "{app}\{#MyAppExeName}"; Description: "Uruchom grę {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Usuwa wspólną tabelę rekordów wszystkich użytkowników (C:\ProgramData\mkTabliczka)
Type: filesandordirs; Name: "{commonappdata}\{#MyAppName}"
