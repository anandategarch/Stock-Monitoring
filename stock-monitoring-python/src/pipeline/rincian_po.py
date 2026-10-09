"""
rincian_po.py — Mirror persis query #"Rincian PO" di M code.
Rincian Pesanan Pembelian (modul 32.43) → filter KATEGORI = "DEVIASI".
"""
import pandas as pd

from .helpers import fn_combine_folder, safe_to_numeric, safe_to_str
from .queries import query_dbs_kategori


def build_rincian_po(config) -> pd.DataFrame:
    """
    Mirror M: shared #"Rincian PO".

    Output columns: Nomor #, Tanggal, Cabang PO, Pemasok, Nama Barang, Satuan,
    Kuantitas, @Harga, Total Harga, Keterangan PO, Status Pesanan Pembelian,
    Tgl/Jam Pembuatan, DBS_Kategori.KATEGORI
    (filtered: DBS_Kategori.KATEGORI = "DEVIASI")
    """
    # Source = fnCombineFolder(RincianPO, PesananPO, false) + Skip(3) + Skip(1) + Promote
    # = pandas header=4
    sheet_name = config.sheet("PesananPO")
    prom = fn_combine_folder(config.folder("RincianPO"), sheet_name, header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=[
            "Nomor #", "Tanggal", "Cabang PO", "Pemasok", "Nama Barang",
            "Satuan", "Kuantitas", "@Harga", "Total Harga", "Keterangan PO",
            "Status Pesanan Pembelian", "Tgl/Jam Pembuatan", "DBS_Kategori.KATEGORI"
        ])

    # Selected = Table.SelectColumns(Promote, {...}, MissingField.Ignore)
    needed = [
        "Nomor #", "Tanggal", "Cabang PO", "Pemasok", "Nama Barang",
        "Satuan", "Kuantitas", "@Harga", "Total Harga", "Keterangan PO",
        "Status Pesanan Pembelian", "Tgl/Jam Pembuatan"
    ]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # Typed
    text_cols = ["Nomor #", "Cabang PO", "Pemasok", "Nama Barang", "Satuan",
                 "Keterangan PO", "Status Pesanan Pembelian"]
    num_cols = ["Kuantitas", "@Harga", "Total Harga"]
    date_cols = ["Tanggal"]
    datetime_cols = ["Tgl/Jam Pembuatan"]

    for col in text_cols:
        if col in sel.columns:
            sel[col] = safe_to_str(sel[col])
    for col in num_cols:
        if col in sel.columns:
            sel[col] = safe_to_numeric(sel[col])
    for col in date_cols:
        if col in sel.columns:
            sel[col] = pd.to_datetime(sel[col], errors="coerce")
    for col in datetime_cols:
        if col in sel.columns:
            sel[col] = pd.to_datetime(sel[col], errors="coerce")

    # BufferedKategori + Merged (LeftOuter on Nama Barang = NAMA BARANG)
    dbs_kategori = query_dbs_kategori(config)
    if len(dbs_kategori) > 0 and "Nama Barang" in sel.columns:
        kat = dbs_kategori[["NAMA BARANG", "KATEGORI"]].copy()
        kat = kat.rename(columns={"NAMA BARANG": "Nama Barang", "KATEGORI": "DBS_Kategori.KATEGORI"})
        sel["Nama Barang"] = sel["Nama Barang"].astype(str)
        kat["Nama Barang"] = kat["Nama Barang"].astype(str)
        merged = sel.merge(kat, on="Nama Barang", how="left")
    else:
        merged = sel.copy()
        merged["DBS_Kategori.KATEGORI"] = None

    # Filtered = Table.SelectRows(Expanded, each [DBS_Kategori.KATEGORI] = "DEVIASI")
    if "DBS_Kategori.KATEGORI" in merged.columns:
        filtered = merged[merged["DBS_Kategori.KATEGORI"] == "DEVIASI"].reset_index(drop=True)
    else:
        filtered = merged.iloc[0:0].copy()

    return filtered
