@echo off
setlocal
chcp 65001 >nul
title Stock Monitoring - Python Edition
color 0A
cls
echo ============================================================
echo   STOCK MONITORING - PYTHON EDITION
echo ============================================================
echo.
echo  Membuka aplikasi...
echo.
echo  Pastikan SETUP.bat sudah dijalankan minimal sekali.
echo.
cd /d "%~dp0"
python -m src.ui.app
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal menjalankan UI. Pastikan:
    echo   - Python terinstall (python --version)
    echo   - SETUP.bat sudah dijalankan
    pause
)
endlocal
