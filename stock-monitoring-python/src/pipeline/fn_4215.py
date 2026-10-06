"""
fn_4215.py — Mirror persis fn4215 di M code.
Pemindahan Barang (modul 42.15) → sumber OUT (kirim) atau IN (terima).
"""
import pandas as pd
from .helpers import (
    fn_combine_folder, safe_to_str, safe_to_numeric,
    date_to_day, text_between_delimiters
)


def fn_4215(folder_path: str, side: str) -> pd.DataFrame:
    """
    Mirror M: fn4215(folderPath, side).

    side: "kirim" (Gudang Pengirim → NAMA RESTO) atau "terima" (Gudang Tujuan → NAMA RESTO).
    Output columns: Tanggal, NAMA RESTO, Nama Barang, Value
    """
    # expand = fnCombineFolder(folderPath, sheet, true) + Skip(3) + PromoteHeaders = header=4
    prom = fn_combine_folder(folder_path, "#42.15. Pemindahan Barang (KIRI", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    if side == "kirim":
        # sel = {"Tanggal", "Gudang Pengirim", "Nama Barang", "Kts Diterima"}
        needed = ["Tanggal", "Gudang Pengirim", "Nama Barang", "Kts Diterima"]
        available = [c for c in needed if c in prom.columns]
        sel = prom[available].copy()

        # typed
        sel["Gudang Pengirim"] = safe_to_str(sel["Gudang Pengirim"])
        sel["Nama Barang"] = safe_to_str(sel["Nama Barang"])
        sel["Kts Diterima"] = safe_to_numeric(sel["Kts Diterima"])

        # ext: Tanggal → Date.Day, Gudang Pengirim → BetweenDelimiters("(", ")")
        sel["Tanggal"] = date_to_day(sel["Tanggal"])
        sel["NAMA RESTO"] = sel["Gudang Pengirim"].apply(lambda x: text_between_delimiters(x, "(", ")"))

        # ren
        sel = sel.rename(columns={"Kts Diterima": "Value"})
    else:
        # side = "terima"
        needed = ["Tanggal", "Nama Barang", "Kts Diterima", "Gudang Tujuan"]
        available = [c for c in needed if c in prom.columns]
        sel = prom[available].copy()

        # typed
        sel["Nama Barang"] = safe_to_str(sel["Nama Barang"])
        sel["Kts Diterima"] = safe_to_numeric(sel["Kts Diterima"])
        sel["Gudang Tujuan"] = safe_to_str(sel["Gudang Tujuan"])

        # ext: Tanggal → Date.Day, Gudang Tujuan → BetweenDelimiters("(", ")")
        sel["Tanggal"] = date_to_day(sel["Tanggal"])
        sel["NAMA RESTO"] = sel["Gudang Tujuan"].apply(lambda x: text_between_delimiters(x, "(", ")"))

        # ren
        sel = sel.rename(columns={"Kts Diterima": "Value"})

    # Final columns (urutan konsisten)
    final_cols = ["Tanggal", "NAMA RESTO", "Nama Barang", "Value"]
    for c in final_cols:
        if c not in sel.columns:
            sel[c] = pd.NA
    result = sel[final_cols].reset_index(drop=True)

    return result
