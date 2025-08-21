@echo off
setlocal
set OUTDIR=dist\BatchConverter

echo === Mazu stare build/dist ===
rmdir /s /q build  2>nul
rmdir /s /q dist   2>nul

echo === Build (ONEDIR, podle .spec) ===
pyinstaller --clean --noconfirm BatchConverter.spec || goto :err

echo === Kopiruju ffmpeg.exe a mediainfo.exe vedle EXE ===
if exist ffmpeg.exe     copy /y ffmpeg.exe     "%OUTDIR%" >nul
if exist mediainfo.exe  copy /y mediainfo.exe  "%OUTDIR%" >nul

echo === Hotovo ===
echo %OUTDIR%\BatchConverter.exe
dir "%OUTDIR%" | findstr /i /c:"ffmpeg.exe" /c:"mediainfo.exe"
pause
goto :eof

:err
echo BUILD SELHAL
pause
