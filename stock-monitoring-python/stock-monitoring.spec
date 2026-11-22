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
#
# v3.15 — VERSION STAMPING + IKON (audit gap-analysis packaging):
# - Properti file .exe dulu KOSONG (0.0.0.0) — user tak bisa cek versi
#   build tanpa menjalankan app (akar kasus "tetap sama aja" v3.11.45).
#   Kini resource versi dibaca OTOMATIS dari APP_VERSION src/ui/app.py
#   (sumber tunggal — tanpa sinkron manual) → filevers/prodvers +
#   StringTable FileVersion/ProductVersion; ditulis ke
#   build/version_info.txt (build/ di-gitignore, dibuat ulang tiap
#   build — aman terhadap --clean karena spec dieksekusi SETELAH
#   pembersihan).
# - icon= assets/icon.ico — ikon proper (dulu generic PyInstaller;
#   memperparah false-positive antivirus & sulit dibedakan di taskbar).
# - version/icon hanya dipasang di Windows (EXE Windows-only resource —
#   jalur dev Linux/macOS untuk smoke build tetap polos, tanpa error).
import re as _re
import sys as _sys
from pathlib import Path as _Path

_spec_dir = _Path(SPECPATH)


def _app_version() -> str:
    """Baca APP_VERSION dari src/ui/app.py — sumber tunggal versi."""
    _src = (_spec_dir / "src" / "ui" / "app.py").read_text(encoding="utf-8")
    _m = _re.search(r'APP_VERSION\s*=\s*"(\d+)\.(\d+)\.(\d+)"', _src)
    if _m is None:
        raise SystemExit(
            "[spec] APP_VERSION tidak ditemukan di src/ui/app.py — "
            "version stamping butuh format APP_VERSION = \"X.Y.Z\"")
    return _m.group(0).split('"')[1]


def _make_version_file() -> _Path:
    """Tulis VSVersionInfo (format pyi_grab_version PyInstaller)."""
    _ver = _app_version()
    _nums = ", ".join(_ver.split("."))
    _dest = _spec_dir / "build" / "version_info.txt"
    _dest.parent.mkdir(parents=True, exist_ok=True)
    _dest.write_text(
        "# UTF-8\n"
        "# DIBUAT OTOMATIS oleh stock-monitoring.spec dari APP_VERSION\n"
        "# (jangan edit manual — ditimpa tiap build).\n"
        "VSVersionInfo(\n"
        "  ffi=FixedFileInfo(\n"
        f"    filevers=({_nums}, 0),\n"
        f"    prodvers=({_nums}, 0),\n"
        "    mask=0x3f,\n"
        "    flags=0x0,\n"
        "    OS=0x40004,\n"
        "    fileType=0x1,\n"
        "    subtype=0x0,\n"
        "    date=(0, 0)\n"
        "  ),\n"
        "  kids=[\n"
        "    StringFileInfo(\n"
        "      [\n"
        "      StringTable(\n"
        "        '040904B0',\n"
        "        [StringStruct('CompanyName', 'Stock Monitoring'),\n"
        "        StringStruct('FileDescription', "
        "'Stock Monitoring - Aplikasi monitoring stok resto'),\n"
        f"        StringStruct('FileVersion', '{_ver}'),\n"
        "        StringStruct('InternalName', 'StockMonitor'),\n"
        "        StringStruct('LegalCopyright', 'Internal use'),\n"
        "        StringStruct('OriginalFilename', 'StockMonitor.exe'),\n"
        "        StringStruct('ProductName', 'Stock Monitoring'),\n"
        f"        StringStruct('ProductVersion', '{_ver}')])\n"
        "      ]),\n"
        "    VarFileInfo([VarStruct('Translation', [1033, 1200])])\n"
        "  ]\n"
        ")\n",
        encoding="utf-8")
    return _dest


# Resource versi + ikon = Windows-only (EXE resource); jalur dev
# Linux/macOS (smoke build build_exe.py) tetap jalan tanpa keduanya.
_is_win = _sys.platform == "win32"
_version_file = _make_version_file() if _is_win else None
_icon_file = (_spec_dir / "assets" / "icon.ico"
              if _is_win and (_spec_dir / "assets" / "icon.ico").exists()
              else None)

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
    version=str(_version_file) if _version_file is not None else None,
    icon=str(_icon_file) if _icon_file is not None else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="StockMonitor",
)
