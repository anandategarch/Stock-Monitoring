"""
config.py — Load konfigurasi dari config.json.
Menggantikan record Config di Power Query M code.
Path bisa diubah user tanpa mengubah kode.

v3.9.20 (deep audit 34-d/fix 35-d): setdefault
Sheets["Pemindahan4205Lalu"] (default = nilai sheet berjalan — config
lama tanpa key tetap jalan tanpa KeyError).
"""
import json
import os
from pathlib import Path


class Config:
    """Konfigurasi yang dimuat dari config.json. Mirror persis record Config di M code."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default: config.json di folder yang sama dengan file ini
            base = Path(__file__).resolve().parent.parent
            config_path = base / "config.json"

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.RootPath = data["RootPath"]
        # v3.5: LightMode DIHAPUS — pipeline selalu mode FULL
        # (SO bulan lalu tanggal -25..-31 selalu terbaca). Key "LightMode"
        # lama di config.json diabaikan dengan aman.
        self.Folders = data["Folders"]
        # v3.9.17: key baru di-DEFAULT (config lokal pra-v3.9.17 yang belum
        # memuat 'Pemindahan4205Lalu' — mis. hasil git pull dgn config
        # ter-modifikasi — tetap jalan tanpa KeyError; nama folder kanonis).
        self.Folders.setdefault("Pemindahan4205Lalu",
                                "4.1 4205 Bulan Lalu")
        self.Sheets = data["Sheets"]
        # FIX R-3 (audit 34-d): key sheet khusus folder 42.05 bulan lalu —
        # di-default ke nilai sheet berjalan (pola 32.24: nama sheet sama utk
        # folder berjalan & lalu; config lama tanpa key tetap aman — tidak
        # KeyError; default in-memory, mirror pola Folders di atas).
        self.Sheets.setdefault(
            "Pemindahan4205Lalu",
            self.Sheets.get("Pemindahan4205",
                            "#42.05. Rincian Pemindahan Bara"))

    # --- Helper: gabungkan RootPath + subfolder ---
    def folder(self, key: str) -> str:
        """Return full path untuk folder key (e.g., 'RekapBerjalan')."""
        return os.path.join(self.RootPath, self.Folders[key])

    def sheet(self, key: str) -> str:
        """Return sheet name untuk key (e.g., 'Penjualan2205')."""
        return self.Sheets[key]
