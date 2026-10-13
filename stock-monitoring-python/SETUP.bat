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
echo  Menginstall dependency dari requirements.txt
echo  (pandas, openpyxl, numpy, python-calamine, pyxlsb, ...)
echo.
echo  python-calamine = Rust-based Excel reader (10-20x faster)
echo.
pause

python --version >nul 2>nul
if errorlevel 1 goto :fail_python

python -m pip install --upgrade pip
if errorlevel 1 goto :fail_pip

python -m pip install -r requirements.txt
if errorlevel 1 goto :fail_dep

echo.
echo ============================================================
echo   SELESAI! Jalankan MULAI.bat untuk membuka aplikasi.
echo ============================================================
echo.
pause
endlocal
exit /b 0

:fail_python
color 0C
echo.
echo [ERROR] Python tidak ditemukan di PATH.
echo   - Install Python dari https://python.org (centang "Add to PATH")
echo   - Atau jalankan: python --version  untuk mengecek
echo.
pause
endlocal
exit /b 1

:fail_pip
color 0C
echo.
echo [ERROR] pip gagal di-upgrade. Cek koneksi internet /
echo   proxy, lalu jalankan ulang SETUP.bat.
echo.
pause
endlocal
exit /b 1

:fail_dep
color 0C
echo.
echo [ERROR] Instalasi dependency GAGAL. Aplikasi belum siap!
echo   - Cek koneksi internet / proxy (mirror alternatif:
echo     python -m pip install -r requirements.txt -i https://pypi.org/simple)
echo   - Atau install manual satu per satu, lalu jalankan ulang
echo     SETUP.bat sampai sukses.
echo.
pause
endlocal
exit /b 1
