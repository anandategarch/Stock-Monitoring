"""
fn_4205.py — Mirror persis fn4205 di M code.
Pemindahan Barang (modul 42.05) → sumber IN.
OPTIMIZED: vectorized text operations + removed redundant pd.to_datetime.
"""
import pandas as pd
from .helpers import (
    fn_combine_folder, safe_to_str, safe_to_numeric,
    date_to_day, vec_text_between_delimiters
)


def fn_4205(folder_path: str, sheet_name: str = "#42.05. Rincian Pemindahan Bara") -> pd.DataFrame:
    """
    Mirror M: fn4205(folderPath).
    Output columns: Nomor, NAMA RESTO, Tanggal, Nama Barang, Value, #Tgl/Jam Pembuatan IT
    """
    # Source + Skip(3) + Promote = header=4
    prom = fn_combine_folder(folder_path, sheet_name, header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Nomor", "NAMA RESTO", "Tanggal", "Nama Barang",
                                      "Value", "#Tgl/Jam Pembuatan IT"])

    # Selected
    needed = ["Nomor #Terima", "Gudang #Terima", "Tanggal #Terima", "Nama Barang",
              "#Qty. Terkecil", "#Tgl/Jam Pembuatan IT"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # Typed: text columns (vectorized)
    for col in ["Nomor #Terima", "Gudang #Terima", "Nama Barang"]:
        if col in sel.columns:
            sel[col] = safe_to_str(sel[col])
    # Numeric
    if "#Qty. Terkecil" in sel.columns:
        sel["#Qty. Terkecil"] = safe_to_numeric(sel["#Qty. Terkecil"])
    # Datetime (only for #Tgl/Jam — NOT Tanggal #Terima, which goes through date_to_day)
    if "#Tgl/Jam Pembuatan IT" in sel.columns:
        sel["#Tgl/Jam Pembuatan IT"] = pd.to_datetime(sel["#Tgl/Jam Pembuatan IT"], errors="coerce")

    # Transformed: Tanggal#Terima → Date.Day, Gudang#Terima → BetweenDelimiters
    # date_to_day internally calls pd.to_datetime, so no need for separate conversion
    if "Tanggal #Terima" in sel.columns:
        sel["Tanggal #Terima"] = date_to_day(sel["Tanggal #Terima"])
    if "Gudang #Terima" in sel.columns:
        sel["NAMA RESTO"] = vec_text_between_delimiters(sel["Gudang #Terima"], "(", ")")

    # Renamed
    rename_map = {
        "Nomor #Terima": "Nomor",
        "Tanggal #Terima": "Tanggal",
        "#Qty. Terkecil": "Value",
    }
    sel = sel.rename(columns={k: v for k, v in rename_map.items() if k in sel.columns})

    # Final
    final_cols = ["Nomor", "NAMA RESTO", "Tanggal", "Nama Barang", "Value", "#Tgl/Jam Pembuatan IT"]
    for c in final_cols:
        if c not in sel.columns:
            sel[c] = pd.NA
    final = sel[final_cols].reset_index(drop=True)

    return final
