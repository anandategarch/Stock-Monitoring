"""
fn_4217.py — Mirror persis fn4217 di M code.
Kuantitas Barang per Gudang (modul 42.17) → SALDO AWAL.
"""
import pandas as pd
import numpy as np
from .helpers import fn_combine_folder, safe_to_str, text_between_delimiters


def fn_4217(folder_path: str) -> pd.DataFrame:
    """
    Mirror M: fn4217(folderPath).

    Output columns: Nama Barang, NAMA RESTO, Value, Tanggal, JENIS
    - Tanggal: Int64 = 1 (saldo awal selalu tanggal 1)
    - JENIS: text = "SALDO AWAL"
    """
    # expand + Skip(3) + Promote = header=4
    prom = fn_combine_folder(folder_path, "#42.17. Kuantitas Barang per Gu", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=["Nama Barang", "NAMA RESTO", "Value", "Tanggal", "JENIS"])

    # up = Table.UnpivotOtherColumns(prom, {"Nama Barang"}, "NAMA RESTO", "Value")
    # Cari kolom "Nama Barang" (handle jika ada perbedaan kapitalisasi/spasi)
    nama_barang_col = None
    for c in prom.columns:
        if str(c).strip().lower() == "nama barang":
            nama_barang_col = c
            break

    if nama_barang_col is None:
        # Fallback: anggap kolom pertama adalah Nama Barang
        nama_barang_col = prom.columns[0]

    # Rename ke "Nama Barang" jika perlu
    if nama_barang_col != "Nama Barang":
        prom = prom.rename(columns={nama_barang_col: "Nama Barang"})

    up = prom.melt(id_vars=["Nama Barang"], var_name="NAMA RESTO", value_name="Value")

    # ext = NAMA RESTO → BetweenDelimiters(_, "(", ")")
    up["NAMA RESTO"] = up["NAMA RESTO"].apply(lambda x: text_between_delimiters(x, "(", ")"))

    # addT = Tanggal = 1
    up["Tanggal"] = pd.array([1] * len(up), dtype="Int64")

    # addJ = JENIS = "SALDO AWAL"
    up["JENIS"] = "SALDO AWAL"

    # Value → numeric
    up["Value"] = pd.to_numeric(up["Value"], errors="coerce")

    # fil = Table.SelectRows(addJ, each [Value] <> 0 and [Value] <> null and [NAMA RESTO] <> "")
    mask = (
        up["Value"].notna() &
        (up["Value"] != 0) &
        up["NAMA RESTO"].notna() &
        (up["NAMA RESTO"].astype(str).str.strip() != "")
    )
    fil = up[mask].reset_index(drop=True)

    return fil
