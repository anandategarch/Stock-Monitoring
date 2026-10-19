# -*- mode: python ; coding: utf-8 -*-
# v3.9.62 — PyInstaller spec ONEDIR (build_exe.py / GitHub Actions
# .github/workflows/release-windows.yml).
#
# Kebijakan:
# - ONEDIR (bukan onefile): startup cepat (tanpa ekstraksi temporer),
#   ramah antivirus, dan folder dist = "aplikasi portabel" (zip & pakai).
# - console=False: aplikasi GUI; kegagalan ditangani crash.log + dialog
#   (run_app.py / main() v3.9.42 F1) — bukan console.
# - config.json TIDAK dibundel ke _internal: build_exe.py menyalinnya ke
#   SAMPING .exe (app_base_dir() frozen-aware membacanya di sana — file
#   runtime harus editable/tahan-update oleh user).
# - hiddenimports: engine Excel pandas 2.x di-import LAZILY di dalam
#   read_excel(engine=...) — analisis statis PyInstaller bisa melewatkannya.
# - Jalankan dari folder stock-monitoring-python: pyinstaller --clean
#   stock-monitoring.spec  (atau cukup: python build_exe.py).

a = Analysis(
    ["run_app.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "python_calamine",   # engine "calamine" (Rust) — lazy di pandas
        "pyxlsb",            # engine ".xlsb" — lazy di pandas
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StockMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX sering memicu false-positive antivirus
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="StockMonitor",
)
