"""
fn_2205.py — Mirror persis fn2205 di M code.
Rincian Penjualan per Barang (modul 22.05) → sumber OUT.
OPTIMIZED: vectorized text operations via .str accessor.
"""
import pandas as pd

from .helpers import (
    date_to_day,
    fn_combine_folder,
    safe_to_numeric,
    safe_to_str,
    vec_text_between_delimiters,
)


def fn_2205(folder_path: str) -> pd.DataFrame:
    """
    Mirror M: fn2205(folderPath).
    Output columns: Tanggal, NAMA RESTO, Nama Barang, Value
    """
    # expand = fnCombineFolder(folderPath, sheet, true) + Skip(3) + PromoteHeaders = header=4
    prom = fn_combine_folder(folder_path, "#22.05. Rincian Penjualan per B", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # sel = Table.SelectColumns(prom, {"Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"})
    needed = ["Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # fil = Table.SelectRows(sel, each Text.StartsWith([#"Nomor #"], "ACR"))
    # Vectorized: .str.startswith
    sel["Nomor #"] = safe_to_str(sel["Nomor #"])
    fil = sel[sel["Nomor #"].str.startswith("ACR", na=False)].copy()

    # typed: vectorized
    fil["Nama Pelanggan"] = safe_to_str(fil["Nama Pelanggan"])
    fil["Nama Barang"] = safe_to_str(fil["Nama Barang"])
    fil["Kuantitas"] = safe_to_numeric(fil["Kuantitas"])

    # ext: Tanggal → Date.Day (Int64), Nama Pelanggan → BetweenDelimiters("(", ")")
    # Vectorized: .str.extract for between delimiters
    fil["Tanggal"] = date_to_day(fil["Tanggal"])
    fil["NAMA RESTO"] = vec_text_between_delimiters(fil["Nama Pelanggan"], "(", ")")

    # ren: Kuantitas → Value
    fil = fil.rename(columns={"Kuantitas": "Value"})

    # fin = Table.SelectColumns(ren, {"Tanggal", "NAMA RESTO", "Nama Barang", "Value"})
    fin = fil[["Tanggal", "NAMA RESTO", "Nama Barang", "Value"]].copy()

    # Drop rows dengan NAMA RESTO null
    fin = fin.dropna(subset=["NAMA RESTO"]).reset_index(drop=True)

    return fin
