@echo off
setlocal

rem ====== Nastavení ======
set NAME=BatchConverter
set ENTRY=BatchConverter.py
set OUTDIR=dist
set EXE=%OUTDIR%\%NAME%.exe

echo === Mazu stare build/dist ===
rmdir /s /q build  2>nul
rmdir /s /q dist   2>nul
del "%NAME%.spec"  2>nul

echo === Build ONEFILE (%NAME%.exe) ===
pyinstaller --clean --noconfirm --onefile --console --name %NAME% %ENTRY%
if errorlevel 1 goto :err

echo === Pripravuju slozku input vedle EXE ===
if not exist "%OUTDIR%\input" mkdir "%OUTDIR%\input"

echo === Hotovo ===
echo Spust: "%EXE%"
echo.
pause
goto :eof

:err
echo.
echo BUILD SELHAL
pause
