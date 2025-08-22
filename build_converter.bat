@echo off
setlocal EnableExtensions

rem ====== Nastavení ======
set "NAME=BatchConverter"
set "ENTRY=BatchConverter.py"
set "OUTDIR=dist"
set "EXE=%OUTDIR%\%NAME%.exe"

echo === Mazu stare build/dist ===
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
if exist "%NAME%.spec" del "%NAME%.spec"

rem ====== Poskladej volitelne add-binary bez pouziti () bloků ======
set "ADD_BIN="
if exist "ffmpeg.exe"    set "ADD_BIN=%ADD_BIN% --add-binary=ffmpeg.exe;."
if exist "ffprobe.exe"   set "ADD_BIN=%ADD_BIN% --add-binary=ffprobe.exe;."
if exist "MediaInfo.dll" set "ADD_BIN=%ADD_BIN% --add-binary=MediaInfo.dll;."

if not defined ADD_BIN goto NOBIN
echo === Pribalim: %ADD_BIN%
goto BUILD

:NOBIN
echo === Zadne lokalni binarky (ffmpeg/ffprobe/MediaInfo.dll) nenalezeny - EXE si je pripadne stahne

:BUILD
echo === Build ONEFILE (%NAME%.exe) ===
pyinstaller --clean --noconfirm --onefile --console --name "%NAME%" %ADD_BIN% "%ENTRY%"
if errorlevel 1 goto ERR

echo === Pripravuju slozku input vedle EXE ===
if not exist "%OUTDIR%\input" mkdir "%OUTDIR%\input"

echo === Hotovo ===
echo Spust: "%EXE%"
echo.
pause
goto :EOF

:ERR
echo.
echo BUILD SELHAL
pause
