"""
fn_rekap_mentah.py — Mirror persis fnRekapMentah di M code.
Membaca folder Rekap Mentah (SO + BARANG MASUK), unpivot kolom tanggal.
"""
import pandas as pd
import numpy as np
from typing import Optional, List
from .helpers import fn_combine_folder, table_select_columns, safe_to_str, safe_to_numeric


def fn_rekap_mentah(folder_path: str, mode: str, jenis_filter: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Mirror M: fnRekapMentah(folderPath, mode, optional jenisFilter).

    mode: "berjalan" (tanggal 1..31) atau "lalu" (tanggal 25..31, dinegasikan).
    jenis_filter: list JENIS yang di-keep (e.g., {"BARANG MASUK", "SO"}). None = no filter.

    Output columns: NAMA RESTO, SOURCE DATA, JENIS, STATUS, NAMA BARANG, SATUAN, Attribute, Value
    Attribute: int (berjalan: 1..31, lalu: -25..-31)
    """
    # expand = fnCombineFolder(folderPath, "REKAP MENTAH") — no doPromote
    # prom = Table.PromoteHeaders(expand) — first row jadi header
    # Di pandas: header=0 (baca dengan row pertama sebagai header)
    expand = fn_combine_folder(folder_path, "REKAP MENTAH", header_row=0)
    if expand.empty:
        return pd.DataFrame()

    prom = expand.copy()

    # firstColumn = Table.ColumnNames(prom){0}
    first_column = prom.columns[0]

    # ren = Table.RenameColumns(prom, {{firstColumn, "NAMA RESTO"}})
    ren = prom.rename(columns={first_column: "NAMA RESTO"})

    # clean = Table.TransformColumns(ren, {{"NAMA RESTO", each Text.BeforeDelimiter(_, "."), type text}})
    ren["NAMA RESTO"] = ren["NAMA RESTO"].apply(
        lambda x: None if pd.isna(x) else str(x).split(".")[0]
    )

    # base = {"NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS", "NAMA BARANG", "SATUAN"}
    base = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS", "NAMA BARANG", "SATUAN"]

    # days = berjalan: {"1".."31"}, lalu: {"25".."31"}
    if mode == "berjalan":
        days = [str(d) for d in range(1, 32)]
    else:  # "lalu"
        days = [str(d) for d in range(25, 32)]

    # sel = Table.SelectColumns(clean, base & days) — only keep available columns
    all_cols = base + days
    available = [c for c in all_cols if c in ren.columns]
    sel = ren[available].copy()

    # fil = if jenisFilter = null then sel else Table.SelectRows(sel, each List.Contains(jenisFilter, [JENIS]))
    if jenis_filter is not None:
        sel_jenis = sel["JENIS"].astype(str)
        sel = sel[sel_jenis.isin([str(j) for j in jenis_filter])].copy()

    # Type cast: base → text, days → number
    for col in base:
        if col in sel.columns:
            sel[col] = safe_to_str(sel[col])
    for col in days:
        if col in sel.columns:
            sel[col] = safe_to_numeric(sel[col])

    # up = Table.Unpivot(typed, days, "Attribute", "Value")
    available_days = [d for d in days if d in sel.columns]
    if not available_days:
        return pd.DataFrame(columns=base + ["Attribute", "Value"])

    up = sel.melt(
        id_vars=[c for c in base if c in sel.columns],
        value_vars=available_days,
        var_name="Attribute",
        value_name="Value"
    )

    # final: berjalan → Attribute as Int64; lalu → Attribute = -Number.From(Attribute)
    up["Attribute"] = safe_to_numeric(up["Attribute"])
    if mode == "berjalan":
        up["Attribute"] = up["Attribute"].astype("Int64")
    else:
        up["Attribute"] = (-up["Attribute"]).astype("Int64")

    # Value → numeric
    up["Value"] = safe_to_numeric(up["Value"])

    # Drop rows where Value is null (Table.Unpivot di M tidak membuat row untuk null)
    # Actually, M's Table.Unpivot keeps rows even if Value is 0 (after ReplaceValue).
    # But it drops rows where the value was null BEFORE unpivot.
    # Since we read with pandas, nulls in day columns → melt creates rows with NaN Value.
    # We drop NaN Value rows to match M behavior (null cells are not unpivoted).
    up = up.dropna(subset=["Value"]).reset_index(drop=True)

    return up
