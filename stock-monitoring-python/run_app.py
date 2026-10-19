"""run_app.py — entry FROZEN PyInstaller (v3.9.62) + jalur dev alternatif.

Kenapa ada file ini:
- Entry release `python -m src.ui` memakai konteks PACKAGE (-m) — PyInstaller
  menganalisis SCRIPT top-level: entry langsung `src/ui/__main__.py` membuat
  package `src` tak terlacak dari dir skrip. Entry di ROOT proyek ini
  meng-import `src.ui.app.main` → seluruh grafik import (pandas, openpyxl,
  python-calamine, pyxlsb) terlacak penuh oleh Analysis.
- Proteksi kegagalan IMPORT tetap ada (paritas src/ui/__main__.py v3.9.43):
  console exe = False (GUI) → traceback ditulis ke crash.log DI SAMPING
  .exe (app_base_dir frozen-aware) + dialog best-effort — exe tidak bisa
  mati senyap.
- Proteksi runtime DI DALAM main() (v3.9.42 F1) tidak diduplikasi.
"""
import contextlib
import sys
import traceback
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _report_import_failure(tb_text: str) -> None:
    with open(_base_dir() / "crash.log", "w", encoding="utf-8") as f:
        f.write(tb_text)
    # dialog best-effort (pola __main__.py): pelapor tak boleh menimpa
    # error asli — kegagalan dialog dilewati senyap (crash.log tetap ada)
    with contextlib.suppress(Exception):
        import tkinter as tk
        from tkinter import messagebox
        _r = tk.Tk()
        _r.withdraw()
        messagebox.showerror(
            "Stock Monitoring — Gagal Memulai",
            "Terjadi error saat memuat modul aplikasi.\n\n"
            "Detail tersimpan di crash.log:\n" + tb_text[-600:])
        _r.destroy()


if __name__ == "__main__":
    try:
        from src.ui.app import main
    except Exception:  # noqa: BLE001 — launcher: tangkap semua import-failure
        _report_import_failure(traceback.format_exc())
        raise SystemExit(1)
    main()
