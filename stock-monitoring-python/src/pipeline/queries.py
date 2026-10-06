"""
queries.py — Semua query antara (mirror M code shared queries).
Setiap function = 1 shared query di M code.
"""
import pandas as pd
import numpy as np
from typing import Optional
from .fn_rekap_mentah import fn_rekap_mentah
from .fn_2205 import fn_2205
from .fn_3224 import fn_3224
from .fn_4215 import fn_4215
from .fn_4205 import fn_4205
from .fn_4217 import fn_4217
from .fn_pi import fn_pi
from .fn_konversi_satuan import fn_konversi_satuan
from .fn_dbs_kategori import fn_dbs_kategori


# =============================================================================
# MASTER QUERIES (dari Config)
# =============================================================================

def query_27_konversi_satuan(config) -> pd.DataFrame:
    """Mirror M: shared #"27 Konversi Satuan Dex" = fnKonversiSatuan(Config[RootPath] & Config[Folders][KonversiSatuan])"""
    return fn_konversi_satuan(config.folder("KonversiSatuan"))


def query_dbs_kategori(config) -> pd.DataFrame:
    """Mirror M: shared DBS_Kategori = fnDBSKategori(Config[RootPath] & Config[Folders][DBSKategori])"""
    return fn_dbs_kategori(config.folder("DBSKategori"))


def query_4217(config) -> pd.DataFrame:
    """Mirror M: shared #"4217" = fn4217(Config[RootPath] & Config[Folders][SaldoAwal4217])"""
    return fn_4217(config.folder("SaldoAwal4217"))


# =============================================================================
# TRANSACTION QUERIES
# =============================================================================

def query_2205(config) -> pd.DataFrame:
    """Mirror M: shared #"2205" = fn2205(Config[RootPath] & Config[Folders][Penjualan2205])"""
    return fn_2205(config.folder("Penjualan2205"))


def query_4215_gudang_kirim(config) -> pd.DataFrame:
    """
    Mirror M: shared #"4215_Gudang Kirim" = let
        fn4215(Kirim4215, "kirim"), filter NAMA RESTO <> ""
    """
    result = fn_4215(config.folder("Kirim4215"), "kirim")
    if not result.empty and "NAMA RESTO" in result.columns:
        mask = result["NAMA RESTO"].notna() & (result["NAMA RESTO"].astype(str).str.strip() != "")
        result = result[mask].reset_index(drop=True)
    return result


def query_3224(config) -> pd.DataFrame:
    """
    Mirror M: shared #"3224" = let
        fn3224(RI3224, "berjalan"), Changed Type #Tgl/Jam Pembuatan IT → datetime
    """
    result = fn_3224(config.folder("RI3224"), "berjalan")
    if "#Tgl/Jam Pembuatan IT" in result.columns:
        result["#Tgl/Jam Pembuatan IT"] = pd.to_datetime(result["#Tgl/Jam Pembuatan IT"], errors="coerce")
    return result


def query_3224_bulan_lalu(config) -> pd.DataFrame:
    """
    Mirror M: shared #"3224_Bulan Lalu" = let
        fn3224(RI3224Lalu, "lalu"), Changed Type #Tgl/Jam Pembuatan IT → datetime
    """
    result = fn_3224(config.folder("RI3224Lalu"), "lalu")
    if "#Tgl/Jam Pembuatan IT" in result.columns:
        result["#Tgl/Jam Pembuatan IT"] = pd.to_datetime(result["#Tgl/Jam Pembuatan IT"], errors="coerce")
    return result


def query_4205(config) -> pd.DataFrame:
    """Mirror M: shared #"4205" = fn4205(Config[RootPath] & Config[Folders][Pemindahan4205])"""
    sheet_name = config.sheet("Pemindahan4205")
    return fn_4205(config.folder("Pemindahan4205"), sheet_name=sheet_name)


def query_pi(config, konversi: pd.DataFrame) -> pd.DataFrame:
    """Mirror M: shared PI = fnPI(Config[RootPath] & Config[Folders][PI], #"27 Konversi Satuan Dex")"""
    return fn_pi(config.folder("PI"), konversi)


# =============================================================================
# OUT & IN (combine queries)
# =============================================================================

def query_out(config) -> pd.DataFrame:
    """
    Mirror M: shared OUT = let
        Source = Table.Combine({#"2205", #"4215_Gudang Kirim"}),
        Added Custom JENIS = "OUT"
    """
    q2205 = query_2205(config)
    q4215_kirim = query_4215_gudang_kirim(config)

    # Combine — align by column name
    parts = []
    if not q2205.empty:
        parts.append(q2205)
    if not q4215_kirim.empty:
        parts.append(q4215_kirim)

    if not parts:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value", "JENIS"])

    source = pd.concat(parts, ignore_index=True, sort=False)
    # Added Custom: JENIS = "OUT"
    source["JENIS"] = "OUT"
    return source


def query_in(config, konversi: pd.DataFrame) -> pd.DataFrame:
    """
    Mirror M: shared IN = let
        Source = Table.Combine({#"3224", #"3224_Bulan Lalu", PI, #"4205"}),
        Added Custom JENIS = "IN"

    LightMode: skip #"3224_Bulan Lalu" (hemat ~50% data IN).
    """
    q3224 = query_3224(config)
    # LightMode: skip bulan lalu
    q3224_lalu = pd.DataFrame() if config.LightMode else query_3224_bulan_lalu(config)
    qpi = query_pi(config, konversi)
    q4205 = query_4205(config)

    parts = []
    for df in [q3224, q3224_lalu, qpi, q4205]:
        if not df.empty:
            parts.append(df)

    if not parts:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value", "JENIS"])

    source = pd.concat(parts, ignore_index=True, sort=False)
    source["JENIS"] = "IN"
    return source


# =============================================================================
# Full Rekap Mentah SO
# =============================================================================

def query_full_rekap_mentah_so(config) -> pd.DataFrame:
    """
    Mirror M: shared #"Full Rekap Mentah SO" = let
        a = fnRekapMentah(RekapBerjalan, "berjalan", {"BARANG MASUK", "SO"}),
        b = fnRekapMentah(RekapLalu, "lalu", {"BARANG MASUK", "SO"}),
        c = Table.Combine({b, a}),  ← b first, then a
        d = rename Attribute→Tanggal, NAMA BARANG→Nama Barang,
        e = select {NAMA RESTO, Nama Barang, JENIS, Tanggal, Value},
        f = Tanggal → Int64

    LightMode: skip b (RekapLalu) — hemat ~50% data.
    """
    jenis_filter = ["BARANG MASUK", "SO"]

    a = fn_rekap_mentah(config.folder("RekapBerjalan"), "berjalan", jenis_filter=jenis_filter)
    # LightMode: skip bulan lalu
    b = pd.DataFrame() if config.LightMode else fn_rekap_mentah(config.folder("RekapLalu"), "lalu", jenis_filter=jenis_filter)

    # c = Table.Combine({b, a}) — b first
    parts = []
    if not b.empty:
        parts.append(b)
    if not a.empty:
        parts.append(a)

    if not parts:
        return pd.DataFrame(columns=["NAMA RESTO", "Nama Barang", "JENIS", "Tanggal", "Value"])

    c = pd.concat(parts, ignore_index=True, sort=False)

    # d = rename: Attribute → Tanggal, NAMA BARANG → Nama Barang
    c = c.rename(columns={"Attribute": "Tanggal", "NAMA BARANG": "Nama Barang"})

    # e = select {NAMA RESTO, Nama Barang, JENIS, Tanggal, Value, SATUAN}
    # SATUAN ditambahkan untuk DEVIASI GR/PCS split (perlu satuan per barang)
    needed = ["NAMA RESTO", "Nama Barang", "JENIS", "Tanggal", "Value", "SATUAN"]
    available = [col for col in needed if col in c.columns]
    e = c[available].copy()

    # f = Tanggal → Int64
    if "Tanggal" in e.columns:
        e["Tanggal"] = pd.to_numeric(e["Tanggal"], errors="coerce").astype("Int64")

    return e
