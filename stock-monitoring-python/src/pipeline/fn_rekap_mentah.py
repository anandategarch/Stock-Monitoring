"""
fn_rekap_mentah.py — Mirror persis fnRekapMentah di M code.
Membaca folder Rekap Mentah (SO + BARANG MASUK), unpivot kolom tanggal.

CRITICAL FIX: NAMA RESTO berasal dari FILE NAME (bukan sheet column).
Mirror M: fnCombineFolder → Name column → PromoteHeaders → firstColumn = file1's name
           → rename → "NAMA RESTO" → Text.BeforeDelimiter(_, ".")

OPTIMIZED: vectorized text operations.
"""
import pandas as pd
import numpy as np
from typing import Optional, List
from .helpers import (
    fn_combine_folder, promote_headers, safe_to_str, safe_to_numeric
)


def fn_rekap_mentah(folder_path: str, mode: str, jenis_filter: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Mirror M: fnRekapMentah(folderPath, mode, optional jenisFilter).

    mode: "berjalan" (tanggal 1..31) atau "lalu" (tanggal 25..31, dinegasikan).
    jenis_filter: list JENIS yang di-keep. None = no filter.

    Output columns: NAMA RESTO, SOURCE DATA, JENIS, STATUS, NAMA BARANG, SATUAN, Attribute, Value
    """
    # === STEP 1: fnCombineFolder(folderPath, "REKAP MENTAH") dengan doPromote=null ===
    # raw=True: baca tanpa header, add_name_col=True: tambah kolom "Name" (file name)
    expand = fn_combine_folder(folder_path, "REKAP MENTAH", raw=True, add_name_col=True)
    if expand.empty:
        return pd.DataFrame()

    # === STEP 2: prom = Table.PromoteHeaders(expand, [PromoteAllScalars = true]) ===
    # Row 0 (file1's header row) → column names
    # Name column → renamed to file1's name (e.g., "MLGPAR.xlsx")
    prom = promote_headers(expand)

    # === STEP 3: firstColumn = Table.ColumnNames(prom){0} ===
    # firstColumn = file1's name (e.g., "MLGPAR.xlsx")
    first_column = prom.columns[0]

    # === STEP 4: ren = Table.RenameColumns(prom, {{firstColumn, "NAMA RESTO"}}) ===
    ren = prom.rename(columns={first_column: "NAMA RESTO"})

    # === STEP 4b: Handle duplicate "NAMA RESTO" columns ===
    # After rename, there may be TWO "NAMA RESTO" columns:
    #   1. Former Name column (file names) at position 0 — this is the one we want
    #   2. Sheet's original "NAMA RESTO" column (from PromoteHeaders) at position 1
    # M's Table.SelectColumns keeps the FIRST occurrence.
    # In pandas, we select by POSITION (not name) to keep only the first.
    cols = ren.columns.tolist()
    keep_positions = []
    seen_nama_resto = False
    for i, c in enumerate(cols):
        if c == "NAMA RESTO":
            if not seen_nama_resto:
                seen_nama_resto = True
                keep_positions.append(i)
            # else: skip duplicate (position 1+)
        else:
            keep_positions.append(i)
    ren = ren.iloc[:, keep_positions]

    # === STEP 5: clean = NAMA RESTO → Text.BeforeDelimiter(_, ".") ===
    # NAMA RESTO column berisi file names (e.g., "MLGPAR.xlsx", "BDGUKU.xlsx")
    # Text.BeforeDelimiter(_, ".") → "MLGPAR", "BDGUKU"
    # Vectorized: .str.split(".").str[0]
    nama_resto_series = ren["NAMA RESTO"]
    if isinstance(nama_resto_series, pd.DataFrame):
        # Still a DataFrame if duplicate wasn't resolved — take first column
        nama_resto_series = nama_resto_series.iloc[:, 0]
    ren["NAMA RESTO"] = nama_resto_series.astype(str).str.split(".").str[0]

    # === STEP 6: base columns + days ===
    base = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS", "NAMA BARANG", "SATUAN"]
    if mode == "berjalan":
        days = [str(d) for d in range(1, 32)]
    else:  # "lalu"
        days = [str(d) for d in range(25, 32)]

    # === STEP 7: sel = Table.SelectColumns(clean, base & days) ===
    all_cols = base + days
    available = [c for c in all_cols if c in ren.columns]
    sel = ren[available].copy()

    # === STEP 8: fil = filter JENIS (if jenisFilter given) ===
    if jenis_filter is not None:
        sel_jenis = sel["JENIS"].astype(str)
        sel = sel[sel_jenis.isin([str(j) for j in jenis_filter])].copy()

    # === STEP 9: Type cast: base → text, days → number ===
    # Vectorized text conversion
    for col in base:
        if col in sel.columns:
            sel[col] = safe_to_str(sel[col])
    for col in days:
        if col in sel.columns:
            sel[col] = safe_to_numeric(sel[col])

    # === STEP 10: up = Table.Unpivot(typed, days, "Attribute", "Value") ===
    available_days = [d for d in days if d in sel.columns]
    if not available_days:
        return pd.DataFrame(columns=base + ["Attribute", "Value"])

    up = sel.melt(
        id_vars=[c for c in base if c in sel.columns],
        value_vars=available_days,
        var_name="Attribute",
        value_name="Value"
    )

    # === STEP 11: final type conversion ===
    # berjalan → Attribute as Int64; lalu → Attribute = -Number.From(Attribute)
    up["Attribute"] = safe_to_numeric(up["Attribute"])
    if mode == "berjalan":
        up["Attribute"] = up["Attribute"].astype("Int64")
    else:
        up["Attribute"] = (-up["Attribute"]).astype("Int64")

    # Value → numeric
    up["Value"] = safe_to_numeric(up["Value"])

    # Drop rows where Value is null (M's Table.Unpivot doesn't create rows for nulls)
    up = up.dropna(subset=["Value"]).reset_index(drop=True)

    return up
