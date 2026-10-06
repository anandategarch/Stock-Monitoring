@echo off
setlocal
chcp 65001 >nul
title SETUP - Install Dependencies (One-Time)
color 0B
cls
echo ============================================================
echo   SETUP - Install Dependencies (One-Time)
echo ============================================================
echo.
echo  Menginstall: pandas, openpyxl, numpy
echo.
pause
python -m pip install --upgrade pip
python -m pip install pandas openpyxl numpy
echo.
echo  Selesai! Jalankan MULAI.bat untuk membuka aplikasi.
pause
endlocal
