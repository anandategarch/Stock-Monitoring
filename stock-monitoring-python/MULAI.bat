@echo off
setlocal
chcp 65001 >nul
title Stock Monitoring - Python Edition
color 0A
cd /d "%~dp0"

rem v3.9.33 — AUDIT FIX (48-f): app redirect stdout/stderr ke log internal,
rem jadi console ini tidak menampilkan apa pun. Menutup console SEBELUM fix
rem mematikan Python di tengah analisa. Kini: luncurkan TANPA console
rem (pythonw) bila tersedia — fallback python hanya utk menampilkan error
rem startup (Python/dependency hilang) supaya user tahu penyebabnya.
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw -m src.ui.app
    endlocal
    exit /b 0
)

python -m src.ui.app
if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Gagal menjalankan UI. Pastikan:
    echo   - Python terinstall (python --version)
    echo   - SETUP.bat sudah dijalankan minimal sekali
    pause
)
endlocal
