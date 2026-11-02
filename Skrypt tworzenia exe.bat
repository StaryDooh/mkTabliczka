@echo off
chcp 65001 >nul
REM Tworzenie gry Strzelnica "Mnożenie" w trybie katalogu (onedir)
cd /d "%~dp0"

echo Usuwanie poprzedniej wersji...
REM Folder z grą: dist\tabliczka\tabliczka.exe + dist\tabliczka\_internal
if exist "dist\tabliczka" rmdir /s /q "dist\tabliczka"
REM Stary plik z trybu --onefile
if exist "dist\tabliczka.exe" del /f /q "dist\tabliczka.exe"
REM Pliki tymczasowe PyInstallera
if exist "build" rmdir /s /q "build"
if exist "tabliczka.spec" del /f /q "tabliczka.spec"

if exist "dist\tabliczka" (
    echo BŁĄD: Nie można usunąć dist\tabliczka - czy gra jest uruchomiona?
    pause
    exit /b 1
)

echo Kompilacja...
python -m PyInstaller --noconfirm --clean --onedir --noconsole ^
  --icon="ikona.ico" ^
  --version-file="wersja.txt" ^
  --add-data "strzal.wav;." ^
  --add-data "dobrze.wav;." ^
  --add-data "zle.wav;." ^
  tabliczka.py

if errorlevel 1 (
    echo.
    echo BŁĄD kompilacji - sprawdź komunikaty powyżej.
) else (
    echo.
    echo Gotowe: dist\tabliczka\tabliczka.exe
)
pause