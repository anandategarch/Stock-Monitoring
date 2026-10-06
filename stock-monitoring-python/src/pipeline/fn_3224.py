"""
fn_3224.py — Mirror persis fn3224 di M code.
Rincian Penerimaan Barang (modul 32.24) → sumber IN.
"""
import pandas as pd
from .helpers import (
    fn_combine_folder, safe_to_str, safe_to_numeric,
    date_to_day, text_between_delimiters
)


def fn_3224(folder_path: str, mode: str) -> pd.DataFrame:
    """
    Mirror M: fn3224(folderPath, mode).

    mode: "berjalan" atau "lalu".
    Output columns: Tanggal, NAMA RESTO, Nama Barang, Value, Nomor, Nomor PO, #Tgl/Jam Pembuatan IT
    - Tanggal: Int64 (berjalan: 1..31, lalu: -(5 hari terakhir))
    """
    # expand = fnCombineFolder(folderPath, sheet, true) + Skip(3) + PromoteHeaders = header=4
    prom = fn_combine_folder(folder_path, "#32.24. Rincian Penerimaan Bara", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value",
                                      "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"])

    # sel = Table.SelectColumns(prom, {...})
    needed = ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
              "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # typed: Tanggal → date, Kts(Unit#1) → number, Nama Barang → text, Nama Gudang → text
    sel["Nama Barang"] = safe_to_str(sel["Nama Barang"])
    sel["Nama Gudang"] = safe_to_str(sel["Nama Gudang"])
    sel["Kts (Unit#1)"] = safe_to_numeric(sel["Kts (Unit#1)"])

    # ext: Nama Gudang → BetweenDelimiters("(", ")"), Tanggal → Date.Day
    sel["NAMA RESTO"] = sel["Nama Gudang"].apply(lambda x: text_between_delimiters(x, "(", ")"))
    sel["Tanggal"] = date_to_day(sel["Tanggal"])

    # ren: multiple renames
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
        # fil5 = Table.SelectRows(fil, each [Tanggal] >= maxT - 4)
        fil5 = fil[fil["Tanggal"] >= (max_t - 4)].copy()
        # neg = Tanggal → -Tanggal
        fil5["Tanggal"] = (-fil5["Tanggal"]).astype("Int64")
        final = fil5.reset_index(drop=True)

    return final
