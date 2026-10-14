@echo off
setlocal
title Stock Monitoring - Python Edition
color 0A
cd /d "%~dp0"

rem v3.9.43 -- LAUNCHER SEDERHANA + KOKOH (fix: "mulai.bat tidak bisa
rem launch" di v3.9.42). AKAR: wrapper PowerShell Start-Process -PassThru
rem + tunggu 5 detik + goto label itu RAPUH -- AV/SmartScreen/PowerShell
rem Constrained-Language memblokir powershell satu-baris ber-Start-Process
rem (pola launcher malware), PS dingin >5 detik salah dibaca, race
rem ExitCode-null dibaca "sukses" = mati senyap; PLUS file ini berisi
rem line-ending LF-Unix + karakter UTF-8 (parser cmd.exe sensitif pada
rem goto/label + blok kurung). FIX:
rem   (1) kembali ke pola TERBUKTI v3.9.33: start "" pythonw -m src.ui
rem       -- TANPA powershell, TANPA goto, TANPA label;
rem   (2) entry baru src.ui.__main__ = bootstrap stdlib-murni yang
rem       menangkap JUGA kegagalan import (pandas/tkinter hilang):
rem       dialog + crash.log + exit 1 -- pythonw tidak bisa mati senyap
rem       lagi, deteksi PINDAH ke dalam Python (tidak tergantung
rem       powershell/AV/kebijakan mesin);
rem   (3) CRLF + ASCII murni; .gitattributes repo mengunci eol=crlf
rem       untuk *.bat/*.cmd supaya launcher tidak bisa rusak lagi;
rem   (4) fallback python (console terlihat) + petunjuk pemecah:
rem       PATH, SETUP.bat, Unblock ZIP, App Execution Aliases.
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw -m src.ui
    endlocal
    exit /b 0
)

rem pythonw tidak ada -- jalankan via python supaya error startup
rem TERLIHAT di console ini (entry bootstrap sama persis; error juga
rem tersimpan di crash.log + dialog dari dalam Python).
python -m src.ui
if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Gagal menjalankan UI. Pastikan:
    echo   - Python terinstall dan ada di PATH (cek: python --version)
    echo   - SETUP.bat sudah dijalankan minimal sekali
    echo   - Bila folder ini hasil download ZIP: klik kanan folder,
    echo     Properties, centang Unblock; atau saat dialog SmartScreen
    echo     muncul pilih "More info" lalu "Run anyway"
    echo   - Bila muncul "Python was not found": Windows memakai stub
    echo     Store -- matikan App Execution Aliases (Settings, Apps,
    echo     Advanced app settings) lalu install dari python.org dan
    echo     centang "Add Python to PATH"
    echo.
    echo Detail error juga tersimpan di crash.log.
    pause
)
endlocal
