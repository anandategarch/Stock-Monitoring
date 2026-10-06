"""
fn_3224.py — Mirror persis fn3224 di M code.
Rincian Penerimaan Barang (modul 32.24) → sumber IN.
OPTIMIZED: vectorized text operations + NA-safe mask.
"""
import pandas as pd
from .helpers import (
    fn_combine_folder, safe_to_str, safe_to_numeric,
    date_to_day, vec_text_between_delimiters
)


def fn_3224(folder_path: str, mode: str) -> pd.DataFrame:
    """
    Mirror M: fn3224(folderPath, mode).
    mode: "berjalan" atau "lalu".
    """
    # expand = fnCombineFolder + Skip(3) + PromoteHeaders = header=4
    prom = fn_combine_folder(folder_path, "#32.24. Rincian Penerimaan Bara", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value",
                                      "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"])

    # sel = Table.SelectColumns(prom, {...})
    needed = ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
              "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # typed: vectorized
    sel["Nama Barang"] = safe_to_str(sel["Nama Barang"])
    sel["Nama Gudang"] = safe_to_str(sel["Nama Gudang"])
    sel["Kts (Unit#1)"] = safe_to_numeric(sel["Kts (Unit#1)"])

    # ext: Nama Gudang → BetweenDelimiters("(", ")"), Tanggal → Date.Day
    # Vectorized
    sel["NAMA RESTO"] = vec_text_between_delimiters(sel["Nama Gudang"], "(", ")")
    sel["Tanggal"] = date_to_day(sel["Tanggal"])

    # ren
    rename_map = {
        "Kts (Unit#1)": "Value",
        "Nomor # RI": "Nomor",
        "Nomor # PO": "Nomor PO",
        "Tgl/Jam Pembuatan": "#Tgl/Jam Pembuatan IT",
    }
    sel = sel.rename(columns={k: v for k, v in rename_map.items() if k in sel.columns})

    # fil = Table.SelectRows(ren, each [NAMA RESTO] <> null and [NAMA RESTO] <> "")
    mask = sel["NAMA RESTO"].notna() & (sel["NAMA RESTO"].astype(str).str.strip() != "")
    fil = sel[mask].copy()

    # final: berjalan → as-is; lalu → filter 5 hari terakhir + negate Tanggal
    if mode == "berjalan":
        final = fil.reset_index(drop=True)
    else:  # "lalu"
        # maxT = List.Max(fil[Tanggal])
        max_t = fil["Tanggal"].max()
        if pd.isna(max_t):
            final = fil.iloc[0:0].copy()
        else:
            # fil5 = Table.SelectRows(fil, each [Tanggal] >= maxT - 4)
            # NA-safe mask: .fillna(False) for pandas < 2.1 compatibility
            mask5 = (fil["Tanggal"] >= (max_t - 4)).fillna(False)
            fil5 = fil[mask5].copy()
            # neg = Tanggal → -Tanggal
            fil5["Tanggal"] = (-fil5["Tanggal"]).astype("Int64")
            final = fil5.reset_index(drop=True)

    return final
