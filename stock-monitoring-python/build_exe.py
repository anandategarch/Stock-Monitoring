"""build_exe.py — build aplikasi jadi folder .exe portabel (v3.9.62).

Pemakaian (dev, dari folder stock-monitoring-python):
    python build_exe.py

Perilaku:
1. Pastikan PyInstaller ter-install di environment aktif (auto pip bila
   belum — requirements.txt TIDAK diubah: pyinstaller = dependensi BUILD,
   bukan runtime).
2. PyInstaller ONEDIR via stock-monitoring.spec → dist/StockMonitor/
   (StockMonitor.exe + _internal/).
3. Salin config.json ke SAMPING .exe (app_base_dir() frozen-aware
   membacanya di sana — user tetap bisa mengedit RootPath dgn editor
   teks / tab ⚙️ Config).
4. Windows → .exe asli; Linux/macOS → binary dev (untuk SMOKE TEST
   build di sandbox: jalankan di bawah Xvfb dgn timeout — GUI hidup
   berarti bundling import pandas/calamine/pyxlsb sehat).

RILIS OTOMATIS: .github/workflows/release-windows.yml menjalankan
langkah yang sama di windows-latest setiap tag v* → artefak + GitHub
Release (zip StockMonitor-windows-x64).
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST_APP = HERE / "dist" / "StockMonitor"


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
        return
    except ImportError:
        pass
    print("[build] PyInstaller belum ada — memasang ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "pyinstaller"])


def main() -> int:
    _ensure_pyinstaller()
    print("[build] menjalankan PyInstaller (onedir) ...")
    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
         str(HERE / "stock-monitoring.spec")],
        cwd=str(HERE))

    cfg_src = HERE / "config.json"
    if cfg_src.exists():
        shutil.copy2(cfg_src, DIST_APP / "config.json")
        print(f"[build] config.json → {DIST_APP / 'config.json'}")

    exe = DIST_APP / ("StockMonitor.exe" if sys.platform == "win32"
                      else "StockMonitor")
    if exe.exists():
        print(f"[build] OK → {exe}")
        print("[build] folder dist/StockMonitor siap di-zip / dipakai.")
        return 0
    print("[build] GAGAL — binary tidak ditemukan di dist/StockMonitor/")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
