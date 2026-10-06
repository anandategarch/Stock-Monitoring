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
echo  Menginstall: pandas, openpyxl, numpy, python-calamine
echo.
echo  python-calamine = Rust-based Excel reader (10-20x faster)
echo.
pause
python -m pip install --upgrade pip
python -m pip install pandas openpyxl numpy python-calamine
echo.
echo  Selesai! Jalankan MULAI.bat untuk membuka aplikasi.
pause
endlocal
