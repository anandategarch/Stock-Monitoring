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
rem v3.9.42 — AUDIT FIX (61-c, pasangan F1 app.py): `start` (detached) tidak
rem pernah melihat exit code pythonw — pythonw yang mati di AWAL (dependency
rem hilang / error sebelum main() — belum tertangkap dialog crash app)
rem tetap mati SENYAP. Kini: pythonw di-spawn via PowerShell -PassThru lalu
rem ditunggu 5 detik; bila sudah mati dgn exit != 0 → jalankan ulang via
rem `python` supaya traceback terlihat di console ini (pola pythonw || python).
rem Bila masih hidup → console langsung tutup (UX v3.9.33 tetap: tanpa
rem console mengganggu selama app berjalan). Exit code NEGATIF (crash
rem keras) ikut terdeteksi lewat perbandingan string %errorlevel%==0.
where pythonw >nul 2>nul
if not %errorlevel%==0 goto run_python

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process pythonw -ArgumentList '-m','src.ui.app' -PassThru; Start-Sleep -Seconds 5; if ($p.HasExited) { exit $p.ExitCode } else { exit 0 }"
if %errorlevel%==0 (
    endlocal
    exit /b 0
)

rem pythonw GAGAL (exit != 0) — tampilkan penyebab via python (console)
color 0C
echo.
echo [ERROR] pythonw gagal memulai aplikasi — mencoba ulang dengan
echo python supaya penyebabnya terlihat di console ini
echo (detail juga tersimpan di crash.log):
echo.
python -m src.ui.app
echo.
echo Pastikan:
echo   - Python terinstall (python --version)
echo   - SETUP.bat sudah dijalankan minimal sekali
pause
endlocal
exit /b 0

:run_python
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
