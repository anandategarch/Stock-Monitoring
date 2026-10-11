"""
fn_4205.py — Mirror persis fn4205 di M code.
Pemindahan Barang (modul 42.05) → sumber IN.
OPTIMIZED: vectorized text operations + removed redundant pd.to_datetime.
v3.9.17: mode "lalu" — mirror fn_3224(mode="lalu"): 5 hari terakhir file
bulan lalu + Tanggal dinegasikan (folder "4.1 4205 Bulan Lalu" = penambah
IN periode ujung bulan lalu, "sama seperti 32.24 bulan lalu").
v3.9.20 (deep audit 34-d/fix 35-d): mode "lalu" filter baris resto-valid
SEBELUM max_t (mirror PERSIS fn_3224 — baris NA-resto tak lagi menggeser
jendela 5 hari).
"""
import pandas as pd

from .helpers import (
    date_to_day,
    fn_combine_folder,
    safe_to_numeric,
    safe_to_str,
    vec_text_between_delimiters,
)


def fn_4205(folder_path: str, sheet_name: str = "#42.05. Rincian Pemindahan Bara",
            mode: str = "berjalan") -> pd.DataFrame:
    """
    Mirror M: fn4205(folderPath).
    mode: "berjalan" (as-is) atau "lalu" (v3.9.17 — 5 hari terakhir +
    Tanggal dinegasikan, mirror fn_3224).
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

    # v3.9.17: mode "lalu" — MIRROR PERSIS fn_3224(mode="lalu"): 5 hari
    # terakhir file bulan lalu (Tanggal >= maxT - 4) + Tanggal dinegasikan
    # (hari negatif = bulan lalu) → penambah IN periode ujung bulan lalu
    # (folder "4.1 4205 Bulan Lalu", permintaan user: "sama seperti 32.24
    # bulan lalu").
    # FIX R-4 (audit 34-d): mirror fn_3224 — baris resto-valid difilter
    # DULU sebelum max_t (filter & window identik fn_3224.py:54,68):
    # baris tanpa NAMA RESTO bertanggal akhir bulan tidak lagi menggeser
    # jendela 5 hari dan membuang semua baris resto. Output lalu = baris
    # resto-valid dalam jendela (identik bentuk output fn_3224 lalu);
    # mode berjalan TIDAK berubah (NA-resto tetap lolos — M-mirror asal).
    if mode == "lalu":
        # fil = Table.SelectRows(final, each [NAMA RESTO] <> null and <> "")
        mask = final["NAMA RESTO"].notna() & (
            final["NAMA RESTO"].astype(str).str.strip() != "")
        fil = final[mask].copy()
        # maxT = List.Max(fil[Tanggal])
        max_t = fil["Tanggal"].max()
        if pd.isna(max_t):
            return fil.iloc[0:0].copy()
        # fil5 = Table.SelectRows(fil, each [Tanggal] >= maxT - 4)
        # NA-safe mask: .fillna(False) for pandas < 2.1 compatibility
        mask5 = (fil["Tanggal"] >= (max_t - 4)).fillna(False)
        fil5 = fil[mask5].copy()
        # neg = Tanggal → -Tanggal
        fil5["Tanggal"] = (-fil5["Tanggal"]).astype("Int64")
        return fil5.reset_index(drop=True)

    return final
