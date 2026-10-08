"""
config.py — Load konfigurasi dari config.json.
Menggantikan record Config di Power Query M code.
Path bisa diubah user tanpa mengubah kode.
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
        self.Sheets = data["Sheets"]

    # --- Helper: gabungkan RootPath + subfolder ---
    def folder(self, key: str) -> str:
        """Return full path untuk folder key (e.g., 'RekapBerjalan')."""
        return os.path.join(self.RootPath, self.Folders[key])

    def sheet(self, key: str) -> str:
        """Return sheet name untuk key (e.g., 'Penjualan2205')."""
        return self.Sheets[key]
