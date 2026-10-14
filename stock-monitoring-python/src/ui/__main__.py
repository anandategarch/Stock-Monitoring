"""
__main__.py — Entry launcher `python -m src.ui` (MULAI.bat v3.9.43).

Kenapa ada file ini (audit launcher v3.9.43 — "mulai.bat tidak bisa
launch"):
- pythonw TIDAK punya console: kegagalan IMPORT (sebelum main()
  berjalan — mis. pandas belum ter-install via SETUP.bat, DLL
  tkinter rusak) dulu mati SENYAP: traceback dikirim ke stderr lalu
  dibuang OS — tidak ada dialog, tidak ada file, tidak ada jejak.
  v3.9.42 mencoba mendeteksinya dari LUAR (MULAI.bat memanggil
  powershell Start-Process -PassThru + tunggu 5 detik + fallback
  python) — wrapper itu sendiri rapuh dan menjadi AKAR "tidak bisa
  launch": AV / SmartScreen / PowerShell Constrained-Language memblokir
  powershell satu-baris ber-Start-Process (pola launcher malware),
  PowerShell dingin >5 detik dijadikan 'gagal', race ExitCode-null
  salah dibaca 'sukses', plus file .bat ber-line-ending LF-Unix +
  karakter UTF-8 + goto/label membuat parser cmd.exe goyah.
- Kini deteksi mati pindah KE DALAM Python: modul ini hanya import
  STDLIB di level atas (sys/traceback/contextlib/pathlib — bawaan
  Python, tidak mungkin gagal), lalu meng-import app DI DALAM
  try → kegagalan import apa pun → traceback di-print ke stderr
  (terlihat di jalur fallback python), ditulis ke crash.log (di
  samping config.json — satu-satunya jejak saat pythonw), dialog
  ramah (best-effort), exit code 1 (bukan senyap).
- MULAI.bat kembali ke pola sederhana TERBUKTI v3.9.33:
  `start "" pythonw -m src.ui` — tanpa powershell, tanpa goto label,
  CRLF + ASCII murni (.gitattributes mengunci eol=crlf permanen).
- `python -m src.ui.app` TETAP berjalan seperti biasa (main()
  punya proteksi crash sendiri sejak v3.9.42 F1: exception DI DALAM
  main() sudah di-dialog + crash.log; modul ini hanya menutup celah
  IMPORT yang main() tidak bisa lihat).
"""
import contextlib
import sys
import traceback
from pathlib import Path

# Lokasi crash.log = di samping config.json (root proyek) — konsisten
# dengan CONFIG_PATH app.py (kebijakan v3.9.42 F1: saat pythonw mati
# tanpa console, file = satu-satunya jejak yang tersisa).
_CRASH_LOG = Path(__file__).resolve().parent.parent.parent / "crash.log"


def _report_import_failure(tb_text: str) -> None:
    """Kegagalan import → stderr + crash.log + dialog (best-effort).

    Jalur console (python): traceback LANGSUNG terbaca di layar.
    Jalur pythonw: stderr dibuang OS — crash.log + dialog yang
    bicara. Semua langkah best-effort: kegagalan pelapor sendiri
    (mis. tkinter hilang) tidak boleh menimpa error asli.
    """
    with contextlib.suppress(Exception):
        sys.stderr.write(tb_text + "\n")
    with contextlib.suppress(Exception):
        _CRASH_LOG.write_text(tb_text, encoding="utf-8")
    with contextlib.suppress(Exception):
        # tkinter LAZY: bila tkinter sendiri rusak/hilang, dialog
        # dilewati — crash.log di atas tetap tertulis.
        import tkinter as tk
        _root = tk.Tk()
        _root.withdraw()
        from tkinter import messagebox
        messagebox.showerror(
            "Stock Monitoring — Gagal Memulai",
            "Terjadi error saat memuat modul aplikasi.\n\n"
            "Detail tersimpan di crash.log:\n" + tb_text[-600:])
        with contextlib.suppress(Exception):
            _root.destroy()


if __name__ == "__main__":
    try:
        from src.ui.app import main
    except Exception:  # noqa: BLE001 — launcher: tugasnya menangkap semua
        # Import-time failure — celah yang v3.9.42 coba tangkap dari
        # luar via PowerShell; kini ditangkap dari dalam (selalu jalan,
        # tanpa tergantung powershell/AV/kebijakan mesin).
        _report_import_failure(traceback.format_exc())
        raise SystemExit(1)
    # main() sendiri sudah ber-try/except + crash.log + dialog +
    # re-raise (v3.9.42 F1) — exception main() dibiarkan mengalir
    # alami agar exit code != 0 (fallback python MULAI.bat memakai
    # traceback console-nya untuk diagnosis).
    main()
