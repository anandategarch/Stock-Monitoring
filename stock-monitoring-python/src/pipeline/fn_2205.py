"""
fn_2205.py — Mirror persis fn2205 di M code.
Rincian Penjualan per Barang (modul 22.05) → sumber OUT.
OPTIMIZED: vectorized text operations via .str accessor.

v3.9.33 — AUDIT FIX (48-a):
- guard kolom — identitas ('Nomor #' = kunci filter ACR, 'Nama
  Pelanggan' → NAMA RESTO, 'Nama Barang') hilang → WARNING keras +
  baris dibuang (degradasi per-sumber, bukan KeyError total);
  VALUE ('Kuantitas'/'Tanggal') hilang → NA (schema output tetap).
- sheet_name param — queries.query_2205 me-resolve key config
  Sheets['Penjualan2205'] (config lama tanpa key tetap dapat default).
"""
import pandas as pd

from .helpers import (
    date_to_day,
    fn_combine_folder,
    safe_to_numeric,
    safe_to_str,
    vec_text_between_delimiters,
)

# Nama sheet standar 22.05 (export Accurate) — v3.9.33 default param
SHEET_2205 = "#22.05. Rincian Penjualan per B"


def fn_2205(folder_path: str, sheet_name: str = SHEET_2205) -> pd.DataFrame:
    """
    Mirror M: fn2205(folderPath).

    sheet_name: v3.9.33 — AUDIT FIX (48-a): default SHEET_2205; query
    berjalan me-resolve config Sheets['Penjualan2205'].

    Output columns: Tanggal, NAMA RESTO, Nama Barang, Value
    """
    # expand = fnCombineFolder(folderPath, sheet, true) + Skip(3) + PromoteHeaders = header=4
    prom = fn_combine_folder(folder_path, sheet_name, header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # sel = Table.SelectColumns(prom, {"Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"})
    needed = ["Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # v3.9.33 — AUDIT FIX (48-a): kolom IDENTITAS hilang (header file
    # bergeser/versi export beda) → dulu KeyError mematikan SELURUH
    # pipeline. Sekarang: WARNING keras (nama kolom + jumlah baris) +
    # baris dibuang → frame kosong ber-schema standar (degradasi
    # per-sumber: sumber lain tetap jalan; schema output IDENTIK —
    # concat query_out/append1 tak berubah). VALUE hilang → NA.
    _ident_hilang = [c for c in ("Nomor #", "Nama Pelanggan", "Nama Barang")
                     if c not in sel.columns]
    if _ident_hilang:
        print(f"  [fn_2205] WARNING: kolom identitas hilang "
              f"{_ident_hilang} — {len(sel)} baris dibuang (header file "
              f"bergeser? pipeline lanjut tanpa sumber 22.05 ini)")
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # fil = Table.SelectRows(sel, each Text.StartsWith([#"Nomor #"], "ACR"))
    # Vectorized: .str.startswith
    sel["Nomor #"] = safe_to_str(sel["Nomor #"])
    fil = sel[sel["Nomor #"].str.startswith("ACR", na=False)].copy()

    # typed: vectorized
    fil["Nama Pelanggan"] = safe_to_str(fil["Nama Pelanggan"])
    fil["Nama Barang"] = safe_to_str(fil["Nama Barang"])
    # v3.9.33 — AUDIT FIX (48-a): VALUE hilang → NA (bukan KeyError)
    if "Kuantitas" in fil.columns:
        fil["Kuantitas"] = safe_to_numeric(fil["Kuantitas"])

    # ext: Tanggal → Date.Day (Int64), Nama Pelanggan → BetweenDelimiters("(", ")")
    # Vectorized: .str.extract for between delimiters
    if "Tanggal" in fil.columns:
        fil["Tanggal"] = date_to_day(fil["Tanggal"])
    else:
        fil["Tanggal"] = pd.array([pd.NA] * len(fil), dtype="Int64")
    fil["NAMA RESTO"] = vec_text_between_delimiters(fil["Nama Pelanggan"], "(", ")")

    # ren: Kuantitas → Value
    if "Kuantitas" in fil.columns:
        fil = fil.rename(columns={"Kuantitas": "Value"})
    if "Value" not in fil.columns:
        fil["Value"] = pd.Series([float("nan")] * len(fil), index=fil.index)

    # fin = Table.SelectColumns(ren, {"Tanggal", "NAMA RESTO", "Nama Barang", "Value"})
    fin = fil[["Tanggal", "NAMA RESTO", "Nama Barang", "Value"]].copy()

    # Drop rows dengan NAMA RESTO null
    fin = fin.dropna(subset=["NAMA RESTO"]).reset_index(drop=True)

    return fin
