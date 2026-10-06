"""
fn_dbs_kategori.py — Mirror persis fnDBSKategori di M code.
Master kategori barang (Sheet1) → dipakai untuk merge KATEGORI & SOURCE KIRIMAN.
+ Column E: AKTIF/NON status (added for CEK anomaly detection).
"""
import pandas as pd
from .helpers import fn_combine_folder, safe_to_str


def fn_dbs_kategori(folder_path: str) -> pd.DataFrame:
    """
    Mirror M: fnDBSKategori(folderPath).

    Output columns: NAMA BARANG, KATEGORI, JENIS, SOURCE KIRIMAN, AKTIF/NON (all text)
    """
    # src = fnCombineFolder(folderPath, "Sheet1", false) + PromoteHeaders
    # = pandas header=0
    src = fn_combine_folder(folder_path, "Sheet1", header_row=0)
    if src.empty:
        return pd.DataFrame(columns=["NAMA BARANG", "KATEGORI", "JENIS", "SOURCE KIRIMAN", "AKTIF/NON"])

    prom = src.copy()

    # Core columns (always needed)
    core = ["NAMA BARANG", "KATEGORI", "JENIS", "SOURCE KIRIMAN"]
    available = [c for c in core if c in prom.columns]

    # Also find AKTIF/NON column (column E, might have different header names)
    aktif_col = None
    for col in prom.columns:
        col_upper = str(col).upper()
        if "AKTIF" in col_upper or "STATUS" in col_upper:
            aktif_col = col
            break
    # Fallback: 5th column (index 4) if no header match
    if aktif_col is None and len(prom.columns) >= 5:
        aktif_col = prom.columns[4]

    keep_cols = available + ([aktif_col] if aktif_col and aktif_col not in available else [])
    keep = prom[keep_cols].copy()

    # Rename aktif_col to standard name
    if aktif_col and aktif_col != "AKTIF/NON":
        keep = keep.rename(columns={aktif_col: "AKTIF/NON"})

    # typed: all to text
    for col in keep.columns:
        keep[col] = safe_to_str(keep[col])

    # FIX: drop duplicates on NAMA BARANG (was missing → duplicates caused
    # doubled values in pivot when merged via LeftOuter join).
    # Keep first occurrence per NAMA BARANG.
    if "NAMA BARANG" in keep.columns:
        before = len(keep)
        keep = keep.drop_duplicates(subset=["NAMA BARANG"], keep="first").reset_index(drop=True)
        if before != len(keep):
            print(f"  [fn_dbs_kategori] Dropped {before - len(keep)} duplicate rows")

    return keep.reset_index(drop=True)
