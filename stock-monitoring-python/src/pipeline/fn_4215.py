"""
fn_4215.py — Mirror persis fn4215 di M code.
Pemindahan Barang (modul 42.15) → sumber OUT (kirim) atau IN (terima).
OPTIMIZED: vectorized text operations.
"""
import pandas as pd

from .helpers import (
    date_to_day,
    fn_combine_folder,
    safe_to_numeric,
    safe_to_str,
    vec_text_between_delimiters,
)


def fn_4215(folder_path: str, side: str) -> pd.DataFrame:
    """
    Mirror M: fn4215(folderPath, side).
    side: "kirim" (Gudang Pengirim → NAMA RESTO) atau "terima" (Gudang Tujuan → NAMA RESTO).
    """
    prom = fn_combine_folder(folder_path, "#42.15. Pemindahan Barang (KIRI", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    if side == "kirim":
        needed = ["Tanggal", "Gudang Pengirim", "Nama Barang", "Kts Diterima"]
        available = [c for c in needed if c in prom.columns]
        sel = prom[available].copy()

        # typed: vectorized
        sel["Gudang Pengirim"] = safe_to_str(sel["Gudang Pengirim"])
        sel["Nama Barang"] = safe_to_str(sel["Nama Barang"])
        sel["Kts Diterima"] = safe_to_numeric(sel["Kts Diterima"])

        # ext: vectorized
        sel["Tanggal"] = date_to_day(sel["Tanggal"])
        sel["NAMA RESTO"] = vec_text_between_delimiters(sel["Gudang Pengirim"], "(", ")")

        sel = sel.rename(columns={"Kts Diterima": "Value"})
    else:
        needed = ["Tanggal", "Nama Barang", "Kts Diterima", "Gudang Tujuan"]
        available = [c for c in needed if c in prom.columns]
        sel = prom[available].copy()

        sel["Nama Barang"] = safe_to_str(sel["Nama Barang"])
        sel["Kts Diterima"] = safe_to_numeric(sel["Kts Diterima"])
        sel["Gudang Tujuan"] = safe_to_str(sel["Gudang Tujuan"])

        sel["Tanggal"] = date_to_day(sel["Tanggal"])
        sel["NAMA RESTO"] = vec_text_between_delimiters(sel["Gudang Tujuan"], "(", ")")

        sel = sel.rename(columns={"Kts Diterima": "Value"})

    final_cols = ["Tanggal", "NAMA RESTO", "Nama Barang", "Value"]
    for c in final_cols:
        if c not in sel.columns:
            sel[c] = pd.NA
    result = sel[final_cols].reset_index(drop=True)

    return result
