"""
fn_3224.py — Mirror persis fn3224 di M code.
Rincian Penerimaan Barang (modul 32.24) → sumber IN.
OPTIMIZED: vectorized text operations + NA-safe mask.
v3.9.20: param sheet_name (default konstanta) — resolusi sheet folder
bulan-lalu (fallback prefiks "#32.24" — sheet lalu beda nama ≠ 0 baris
senyap; zero behavior change utk pemanggil lama).
v3.9.31: kolom konversi satuan 'Satuan'/'Rasio Satuan' (barang
Eksternal RI — 6 barang eksternal murni + 5 satuan khusus RI TIDAK
ter-cover peta 42.05) ikut terbaca → dibakukan SATUAN DOK / RASIO
SATUAN / SATUAN TERKECIL (peta konversi PO Menunggu → satuan terkecil
— konversi_satuan.build_konversi_map; kolom ekstra TIDAK ikut pivot
append1, pola 'SOURCE IN' v3.9.29).
"""
import pandas as pd

from .helpers import (
    date_to_day,
    fn_combine_folder,
    safe_to_numeric,
    safe_to_str,
    vec_text_between_delimiters,
)
from .konversi_satuan import (
    KOL_RASIO,
    KOL_SATUAN_DOK,
    KOL_TERKECIL,
    resolve_konversi_kolom,
)

# Nama sheet standar 32.24 (export Accurate) — konstanta M-mirror,
# dipakai bersama oleh folder berjalan & bulan lalu.
SHEET_3224 = "#32.24. Rincian Penerimaan Bara"


def fn_3224(folder_path: str, mode: str,
            sheet_name: str = SHEET_3224) -> pd.DataFrame:
    """
    Mirror M: fn3224(folderPath, mode).
    mode: "berjalan" atau "lalu".
    sheet_name: default SHEET_3224 (FIX R-3 audit 34-d — query lalu bisa
    me-resolve nama sheet folder bulan lalu; jalur berjalan tak berubah).
    """
    # expand = fnCombineFolder + Skip(3) + PromoteHeaders = header=4
    prom = fn_combine_folder(folder_path, sheet_name, header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value",
                                      "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT",
                                      KOL_SATUAN_DOK, KOL_RASIO, KOL_TERKECIL])

    # v3.9.31 — resolusi kolom konversi ('Satuan' + 'Rasio Satuan';
    # terkecil biasanya tak ada di export 32.24 → kolom NA tetap dibuat)
    konv = resolve_konversi_kolom(prom.columns, "3224")

    # sel = Table.SelectColumns(prom, {...})
    needed = ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
              "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan"] + list(konv.values())
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
    # v3.9.31 — kolom konversi dibakukan ke nama standar (join key map)
    rename_map.update({orig: std for std, orig in konv.items()})
    sel = sel.rename(columns={k: v for k, v in rename_map.items() if k in sel.columns})

    # v3.9.31 — typed kolom konversi (setelah rename ke nama baku)
    for _std in (KOL_SATUAN_DOK, KOL_TERKECIL):
        if _std in sel.columns:
            sel[_std] = safe_to_str(sel[_std])
    if KOL_RASIO in sel.columns:
        sel[KOL_RASIO] = safe_to_numeric(sel[KOL_RASIO])
    # v3.9.31 — kolom baku TETAP ADA walau file lama tak memuat kolomnya
    # (NA) — schema concat query_in konsisten (pola final_cols fn_4205)
    for _std in (KOL_SATUAN_DOK, KOL_RASIO, KOL_TERKECIL):
        if _std not in sel.columns:
            sel[_std] = pd.NA

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
