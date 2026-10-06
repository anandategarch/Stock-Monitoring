"""
fn_pi.py — Mirror persis fnPI di M code.
Faktur Pembelian (modul 32.42) → sumber IN dengan konversi satuan.
OPTIMIZED: vectorized text operations + fix Kuantitas null handling.
"""
import pandas as pd
from .helpers import (
    fn_combine_folder, safe_to_str, safe_to_numeric,
    date_to_day, vec_text_after_delimiter
)


def fn_pi(folder_path: str, konversi: pd.DataFrame) -> pd.DataFrame:
    """
    Mirror M: fnPI(folderPath, konversi).
    Output columns: Tanggal, NAMA RESTO, Nama Barang, Value
    - Value = Kuantitas × Rasio (konversi ke unit terkecil)
    """
    # expand + Skip(3) + Promote = header=4
    prom = fn_combine_folder(folder_path, "#32.42. Rincian Faktur Pembelia", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # sel = Table.SelectColumns(prom, {...})
    needed = ["Nama Cabang#", "Tgl Pengiriman", "Nama Barang", "Kuantitas", "Nama Satuan"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # typed: vectorized
    for col in ["Nama Cabang#", "Nama Barang", "Nama Satuan"]:
        if col in sel.columns:
            sel[col] = safe_to_str(sel[col])
    if "Kuantitas" in sel.columns:
        sel["Kuantitas"] = safe_to_numeric(sel["Kuantitas"])

    # extDay: Tgl Pengiriman → Date.Day
    if "Tgl Pengiriman" in sel.columns:
        sel["Tgl Pengiriman"] = date_to_day(sel["Tgl Pengiriman"])

    # fil = Table.SelectRows(extDay, each [#"Nama Cabang#"] <> null)
    if "Nama Cabang#" in sel.columns:
        mask = sel["Nama Cabang#"].notna() & (sel["Nama Cabang#"].astype(str).str.strip() != "")
        sel = sel[mask].copy()

    # extCab: Nama Cabang# → Text.AfterDelimiter(_, ".") — vectorized
    # Format: "1370.MLGPAR" → "MLGPAR" (after FIRST ".")
    if "Nama Cabang#" in sel.columns:
        sel["NAMA RESTO"] = vec_text_after_delimiter(sel["Nama Cabang#"], ".")

    # LEFT JOIN with konversi
    if konversi is not None and not konversi.empty and "Nama Barang" in sel.columns and "Nama Satuan" in sel.columns:
        konv = konversi[["Nama Barang", "Satuan", "Rasio"]].copy()
        konv["Nama Barang"] = konv["Nama Barang"].astype(str)
        konv["Satuan"] = konv["Satuan"].astype(str)
        sel["Nama Barang"] = sel["Nama Barang"].astype(str)
        sel["Nama Satuan"] = sel["Nama Satuan"].astype(str)

        merged = sel.merge(konv, how="left",
                           left_on=["Nama Barang", "Nama Satuan"],
                           right_on=["Nama Barang", "Satuan"],
                           suffixes=("", "_konv"))
    else:
        merged = sel.copy()
        merged["Rasio"] = pd.NA

    # rep = Table.ReplaceValue(exp, null, 1, {"Rasio"})
    merged["Rasio"] = merged["Rasio"].fillna(1)

    # add = Value = Kuantitas * Rasio
    # FIX BUG-15: M's null propagation — if Kuantitas is null, result is null (not 0)
    # M: each [Kuantitas] * [Rasio] — null * number = null in M
    # Python: NaN * number = NaN (correct! no .fillna(0) needed)
    if "Kuantitas" in merged.columns:
        merged["Value"] = merged["Kuantitas"] * merged["Rasio"]
    else:
        merged["Value"] = pd.NA

    # ren: Tgl Pengiriman → Tanggal
    merged = merged.rename(columns={"Tgl Pengiriman": "Tanggal"})

    # fin
    final_cols = ["Tanggal", "NAMA RESTO", "Nama Barang", "Value"]
    for c in final_cols:
        if c not in merged.columns:
            merged[c] = pd.NA
    fin = merged[final_cols].reset_index(drop=True)

    return fin
