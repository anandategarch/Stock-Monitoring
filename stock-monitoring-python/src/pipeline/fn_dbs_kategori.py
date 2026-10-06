"""
fn_dbs_kategori.py — Mirror persis fnDBSKategori di M code.
Master kategori barang (Sheet1) → dipakai untuk merge KATEGORI & SOURCE KIRIMAN.
"""
import pandas as pd
from .helpers import fn_combine_folder, safe_to_str


def fn_dbs_kategori(folder_path: str) -> pd.DataFrame:
    """
    Mirror M: fnDBSKategori(folderPath).

    Output columns: NAMA BARANG, KATEGORI, JENIS, SOURCE KIRIMAN (all text)
    """
    # src = fnCombineFolder(folderPath, "Sheet1", false) + PromoteHeaders
    # = pandas header=0
    src = fn_combine_folder(folder_path, "Sheet1", header_row=0)
    if src.empty:
        return pd.DataFrame(columns=["NAMA BARANG", "KATEGORI", "JENIS", "SOURCE KIRIMAN"])

    prom = src.copy()

    # keep = Table.SelectColumns(prom, {"NAMA BARANG", "KATEGORI", "JENIS", "SOURCE KIRIMAN"})
    needed = ["NAMA BARANG", "KATEGORI", "JENIS", "SOURCE KIRIMAN"]
    available = [c for c in needed if c in prom.columns]
    keep = prom[available].copy()

    # typed: all to text
    for col in needed:
        if col in keep.columns:
            keep[col] = safe_to_str(keep[col])

    return keep.reset_index(drop=True)
