"""
fn_2205.py — Mirror persis fn2205 di M code.
Rincian Penjualan per Barang (modul 22.05) → sumber OUT.
"""
import pandas as pd
from .helpers import (
    fn_combine_folder, table_select_columns, table_rename_columns,
    safe_to_str, safe_to_numeric, date_to_day, text_between_delimiters
)


def fn_2205(folder_path: str) -> pd.DataFrame:
    """
    Mirror M: fn2205(folderPath).

    Baca folder "2. 22.05", sheet "#22.05. Rincian Penjualan per B".
    Output columns: Tanggal, NAMA RESTO, Nama Barang, Value
    - Tanggal: Int64 (day-of-month)
    - NAMA RESTO: text (kode resto dari "Nama Pelanggan (KODE)")
    - Value: number (Kuantitas)
    """
    # expand = fnCombineFolder(folderPath, sheet, true) + Skip(3) + PromoteHeaders
    # = pandas header=4
    prom = fn_combine_folder(folder_path, "#22.05. Rincian Penjualan per B", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # sel = Table.SelectColumns(prom, {"Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"})
    needed = ["Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # fil = Table.SelectRows(sel, each Text.StartsWith([#"Nomor #"], "ACR"))
    sel_nomor = sel["Nomor #"].apply(lambda x: "" if pd.isna(x) else str(x))
    fil = sel[sel_nomor.str.startswith("ACR", na=False)].copy()

    # typed: Nomor# → text, Tanggal → date, Nama Pelanggan → text, Nama Barang → text, Kuantitas → number
    fil["Nomor #"] = safe_to_str(fil["Nomor #"])
    fil["Nama Pelanggan"] = safe_to_str(fil["Nama Pelanggan"])
    fil["Nama Barang"] = safe_to_str(fil["Nama Barang"])
    fil["Kuantitas"] = safe_to_numeric(fil["Kuantitas"])

    # ext: Tanggal → Date.Day (Int64), Nama Pelanggan → BetweenDelimiters("(", ")")
    fil["Tanggal"] = date_to_day(fil["Tanggal"])
    fil["NAMA RESTO"] = fil["Nama Pelanggan"].apply(lambda x: text_between_delimiters(x, "(", ")"))

    # ren: Nama Pelanggan → NAMA RESTO (sudah dibuat kolom baru di atas), Kuantitas → Value
    fil = fil.rename(columns={"Kuantitas": "Value"})

    # fin = Table.SelectColumns(ren, {"Tanggal", "NAMA RESTO", "Nama Barang", "Value"})
    fin = fil[["Tanggal", "NAMA RESTO", "Nama Barang", "Value"]].copy()

    # Drop rows dengan NAMA RESTO null (mirror: filter implicit dari BetweenDelimiters null)
    fin = fin.dropna(subset=["NAMA RESTO"]).reset_index(drop=True)

    return fin
