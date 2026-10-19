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


def _utf8_stdio() -> None:
    """FIX run GHA #39188486096: console Windows default cp1252/cp437 tak
    bisa meng-encode karakter '→' di pesan log → UnicodeEncodeError SETELAH
    build sukses (PyInstaller selesai, print terakhir yang crash).
    Reconfigure stdout/stderr ke UTF-8 (Python ≥3.7; best-effort — gagal
    reconfigure = diam, pesan berikut tetap ASCII aman)."""
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


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
    _utf8_stdio()
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
