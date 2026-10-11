"""
komparasi_deviasi_view.py — v3.9.4: KOMPARASI FILE DEVIASI vs TAB DEVIASI GR.

v3.9.19 — KOLOM ANALISA + HAPUS 2 BAGIAN (permintaan user):
    (1) KOLOM ANALISA (1 kolom saja) di bagian 📊 Top & Flip — tabel
        Top Selisih & Perubahan Arah kini punya keterangan analisa
        per baris: Kenaikan Tertinggi (tanda sama, |saat ini| >
        |lalu|) · Penurunan Tertinggi (tanda sama, |saat ini| <
        |lalu|) · Stabil (Selisih dalam toleransi MATCH) · Berubah
        Arah (tanda berlawanan, disparitas < 40% — pembalikan tuntas)
        · Potensi Flip Flop (tanda berlawanan, disparitas ≥ 40% —
        pembalikan parsial: sisi dominan besar, arah baru rawan
        berbalik lagi; ambang sama dgn Kategori flip Sempurna/
        Dominan vs Parsial).
    (2) BAGIAN ⚡ Risiko Flip & 💰 Benchmark DIHAPUS (permintaan
        user: "hapus tab resiko flip dan bencmark") — baris BAGIAN
        kini 3 bagian: Top & Flip · Arah Minoritas · Liga Deviasi.
        Arah Minoritas & Liga Deviasi TIDAK berubah.

v3.9.16 — TOP SELISIH: ABSOLUT + MEDIAN MULTI-FILE (permintaan user,
khusus mode 📈 Analisa di tab 📋 Laporan Deviasi; tabel utama ⛖ &
bagian analisa lain TIDAK berubah):
    (1) ABSOLUT: Selisih = |GR Saat Ini| − |DEV Lalu| — DEV Lalu &
        GR Saat Ini DIABSOLUTKAN DULU saat menghitung Selisih
        (pembalikan tanda mis. −50 → +30 tidak lagi menggembungkan
        selisih: dulu 80, kini 20); kolom DEV Lalu / GR Saat Ini yang
        DITAMPILKAN tetap NILAI ASLI (bukan absolut). Status
        MATCH/SELISIH (hanya tabel Top Selisih) ikut toleransi Selisih
        absolut; status TIDAK ADA DI DATA SAAT INI / H TIDAK ADA tetap.
    (2) MEDIAN MULTI-FILE: file deviasi >1 → nilai Lalu per pasangan
        (resto × bahan × minggu sama) = MEDIAN antar-file — SATU baris
        per pasangan (bukan satu baris per file); yang ditampilkan
        nilai median saja, bukan semua file. Kolom Periode kini kolom
        NYATA: 'Median n file · Minggu' (≥2 nilai) / 'BULAN · Minggu'
        (1 nilai — format lama). Rumus bisnis lain 0 berubah.

v3.9.15 — GELOMBANG 1 ANALISA (adopsi rumus repo Inventory-Control
user; analisa tambahan sebagai BAGIAN di mode 📈 Analisa — baris
"BAGIAN" SegmentBar v3.9.19: Top & Flip · Arah Minoritas · Liga
Deviasi [Risiko Flip & Benchmark DIHAPUS v3.9.19]; hanya bagian
AKTIF yang dirender):
    (1) ARAH MINORITAS PER BAHAN — resto yang arah DEV-nya
        MELAWAN mayoritas resto lain pada bahan sama (mayoritas
        ketat: mayoritas > minoritas) — kandidat salah-input/
        salah-satuan. Klik-2× → popup resto minoritas.
    (2) LIGA DEVIASI-RATE PER BAHAN — rate = |DEV| / |BOM| per
        resto pada bahan sama (adil antar resto); baseline populasi
        MEDIAN + MAD → robust-z = (rate − median) / (1,4826 × MAD)
        (kebal outlier); guard populasi ≥ 5 resto ber-BOM & MAD > 0
        (z "—" bila tak terdefinisi); resto ber-BOM dengan DEV 0
        ikut populasi (jujur) tapi tidak diranking.
    Semua analisa per-periode (1/2) memakai BULAN TERBARU + SATU
    minggu snapshot (preferensi minggu yang memuat H — minggu file
    kumulatif sehingga menjumlah lintas minggu = menghitung ganda).
    Semua komputasi VEKTOR (pola PERF v3.9.14 — tanpa iterrows).

v3.9.14 — PERF TAB ANALISA + MINGGU IKUT H + ISTILAH (permintaan user:
"tab analisa kenapa lemot sekali" / "week di tab analisa harusnya
menyesuaikan juga dengan kolom H — jika 7 berarti week 1" / "ganti
istilah app menjadi Saat ini dan File menjadi Lalu"):
    (1) PERF: tabel analisa hanya dirender saat mode 📈 Analisa AKTIF
        (dulu dirender JUGA saat tersembunyi → ±4,8 dtk freeze UI PER
        refresh di file 40rb baris); flip kini VEKTOR — sort sekali +
        shift(-1) per grup (dulu groupby + sort_values PER GRUP + zip
        per baris = 4,7 dtk → ±50ms, hasil identik); nilai app per
        baris via MERGE vektor app_long (dulu loop Python + Series.get
        = 2,9 dtk → ±60ms — terverifikasi identik baris-per-baris);
        Top Selisih tanpa iterrows/copy penuh.
    (2) MINGGU: Top Selisih & Perubahan Arah kini difilter MINGGU yang
        MEMUAT H — konsisten tabel utama (H=7 → hanya WEEK 1; centang
        "Tampilkan semua minggu" utk semua minggu).
    (3) ISTILAH: kolom *File → *Lalu, *App → *Saat Ini (BOM Lalu, COM
        Lalu, DEV Lalu, %TO BOM Lalu, BOM Saat Ini, COM Saat Ini, DEV
        Saat Ini, GR Saat Ini); status "TIDAK ADA DI DATA APP" →
        "TIDAK ADA DI DATA SAAT INI"; label/title ikut ("Tampilkan
        resto di luar data saat ini", "Komparasi Deviasi — Lalu vs
        Saat Ini").

v3.9.13 — MULTI-FILE + ANALISA + KOLOM (permintaan user):
    (1) MULTI-FILE: 📂 kini multi-select (askopenfilenames); semua file
        diparse di worker & digabung (kolom BULAN ikut dedup-key sehingga
        baris bulan lain TIDAK lagi dibuang). Default tabel difilter ke
        BULAN TERBARU (checkbox "Tampilkan semua bulan" = perilaku lama).
    (2) ALAMAT FILE tersimpan & bisa DIUBAH: entry path (editable, ";"
        pemisah multi-file) + 📂 + ↻; path tersimpan di komparasi_last.json
        {"paths": [...]} (tulis atomik; FIX BUG v3.9.10: .with_suffix pada
        str → AttributeError ditelan → json TIDAK PERNAH tersimpan); file
        terakhir AUTO-LOAD saat tab pertama kali terlihat.
    (3) KOLOM (permintaan user "hapus kolom H di tab laporan deviasi,
    minggu juga hapus. Dev to bom itu harusnya persen"): kolom Minggu & H
        DIHAPUS dari tabel (data internal tetap — filter minggu, join,
        popup, snapshot); "DEV App" kini %TO BOM — App = DEV·App / |BOM·App|
        (persen, konsisten %TO BOM File — dulu kuantitas).
    (4) MODE 📈 ANALISA (adopsi rumus repo Inventory-Control user):
        - TOP SELISIH: peringkat |Selisih| (GR App − DEV File)
          tertinggi (Top-N, default 100; 0 = semua).
        - PERUBAHAN ARAH ("flip"): pasangan bulan berurutan MINGGU SAMA
          (W4 vs W4 — minggu file kumulatif, perbandingan lintas bulan
          jujur hanya minggu sama) dengan tanda DEV berlawanan (minus
          bulan lalu → surplus sekarang); Disparitas = |P1+P2| /
          max(|P1|,|P2|); kategori: Sempurna <10% (pembalikan penuh —
          patut dicek manual), Dominan 10–40%, Parsial ≥40%.

Permintaan user: "Di file sampel kan ada Dev to bom ini kok gak ada ya?
Padahal data udah lengkap 2205 itu bom. Aku barusan upload file deviasi.
Nah aku mau compare file deviasi itu dengan yang deviasi di Tab deviasi GR
terus coba cek kolom status week 1 itu sama dengan 7 week 2 = 14 dan
week = 25. Itu buat kolom h."

KONSEP
------
File deviasi (contoh: "20.AGUSTUS 2026.xlsx" — "File Komparasi Deviasi
History Sampel") berisi laporan resmi per (RESTO × NAMA BAHAN × MINGGU):
    QTY BOM      = pemakaian teoretis dari penjualan  (minus)
    QTY COM      = pemakaian aktual                   (minus)
    QTY DEVIASI  = COM − BOM                          (±, plus = surplus)
    % QTY DEVIASI TO BOM = DEVIASI / |BOM|
Minggu = CUT-OFF KUMULATIF dari tanggal 1 (WEEK 2 ≈ 2× WEEK 1) — sama
dengan semantik TANGGAL H di aplikasi:
    STATUS BULAN  →  KOLOM H
    WEEK 1        →  7      (permintaan user)
    WEEK 2        →  14     (permintaan user)
    WEEK 3 / WEEK 4 → 25    (permintaan user "week = 25"; file sampel
                             memakai WEEK 4 — tidak ada WEEK 3)

SISI SAAT INI (dari data pipeline / append1, tanpa file tambahan —
"data udah lengkap, 2205 itu BOM"; dulu dilabel *App):
    BOM·Saat Ini = −Σ 9.ACR (penjualan 22.05) tanggal 1..H — konvensi file
    COM·Saat Ini = −Σ pemakaian com(t) tanggal 1..H, dengan
                com(1) = SALDO AWAL + IN(1) − BK(1) − SO(1)  (SA pair,
                          baris ber-Tanggal=1 — fn_4217; fallback
                          SO(t-1) bila SA tidak ada)
                com(t>1) = SO(t-1) + IN(t) − BK(t) − SO(t)  (formula
                          identik baris 6.PEMAKAIAN (COM) pivot & tab
                          🚨 Anomali COM)
    DEV·Saat Ini = COM·Saat Ini − BOM·Saat Ini ("Dev to BOM" versi app)
    GR·Saat Ini  = SO_H − Sistem_H (2.SALDO AKHIR) — PERSIS kolom Deviasi
                di tab 📦 Deviasi GR pada H minggu tsb.

    v3.9.5: karena Sistem (fn_running_stock) berbasis SALDO AWAL dan com(1)
    kini juga berbasis SA → GR·Saat Ini == DEV·Saat Ini secara ALJABAR
    PERSIS (dua jalur hitung saling cek internal; dulu menyimpang sebesar
    SO(−31)−SA saat data memuat tanggal negatif bulan lalu).

VERDIK: Selisih = GR·Saat Ini − DEV·Lalu → Status MATCH (dalam toleransi)
/ SELISIH / TIDAK ADA DI DATA SAAT INI / H TIDAK ADA DI DATA.

v3.9.7 — FILTER MINGGU MENGIKUTI H BERSAMA (permintaan user:
"STATUS BULAN itu berguna buat filter. misal H aku input 7 maka
hanya tampilkan week 1 aja"): view kini berlangganan SharedTanggalH
(chip read-only, pola tab Anomali COM). Rentang minggu yang MEMUAT H:
    H 1–7 → WEEK 1 (cut-off 7)      H 8–14  → WEEK 2 (cut-off 14)
    H 15–25 → WEEK 3/4 (cut-off 25) H 26–31 → WEEK 5 (cut-off 31)
Default: hanya baris minggu tsb yang tampil (chip minggu aktif
di-highlight). Centang "Tampilkan semua minggu" utk perilaku lama.
File tanpa minggu tsb → 0 baris + pesan jujur (minggu di file
didaftar).

RESTO: file memakai kode bercabang ("1041.BDGUKU", "B.1001.MLGPAR") —
dinormalkan ke segmen setelah titik terakhir ("BDGUKU") lalu dicocokkan
ke NAMA RESTO data app (upper + strip).

INFRASTRUKTUR (dipertahankan dari view lain): ✓ follow-up, filter header
⧩ semua kolom, sort engine linear (parser angka Indonesia), ⛶ Layar Penuh,
⤢ Perbesar Tabel, ◱ Kolom, ↔ Auto-Fit, loading overlay + compute async +
on_error reset _busy (FIX B-01), minus merah PER CELL (v3.9.2 apply_cell_tag),
sel Status berwarna per-cell (MATCH hijau / SELISIH amber / lainnya merah).
"""

import contextlib
import json
import os
import re
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk

import numpy as np
import pandas as pd

from .followup import CHECK_OFF, CHECK_ON, FollowUpStore, row_fingerprint
from .theme import (
    C_ACCENT,
    C_AMBER,
    C_BG,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    font,
)
from .widgets import (
    CELL_TAGS_SUPPORTED,
    Card,
    ColumnManager,
    EmptyState,
    GhostButton,
    HeaderFilterGroup,
    LoadingOverlay,
    SegmentBar,
    TableExpander,
    apply_cell_tag,
    attach_clone_filters,
    auto_fit_columns,
    enable_col_resize,
    fmt_int_id,
    identify_to_column,
    insert_tree_items,
    open_tree_maximized,
    run_async,
    sort_tree_by_column,
)

# ---------------------------------------------------------------------------
# Konstanta pemetaan minggu → kolom H (permintaan user, lihat docstring)
# ---------------------------------------------------------------------------
WEEK_TO_H = {
    "WEEK 1": 7,
    "WEEK 2": 14,
    "WEEK 3": 25,   # user: "week = 25"
    "WEEK 4": 25,   # file sampel memakai WEEK 4 utk cut-off 25
}

# v3.9.13: nama bulan Indonesia → nomor (urutan kronologis lintas file);
# varian typo umum ikut (pola MONTH_MAP repo Inventory-Control user).
# v3.9.13: SINGKATAN 2-4 huruf WAJIB — file asli memakai kode periode
# "201.OKT 26" (OKT = Oktober; tanpa singkatan, semua bulan terparse 0).
_BULAN_NUM = {
    "JANUARI": 1, "JAN": 1, "FEBRUARI": 2, "FEB": 2, "PEBRUARI": 2,
    "PEB": 2, "MARET": 3, "MAR": 3, "APRIL": 4, "APR": 4, "MEI": 5,
    "JUNI": 6, "JUN": 6, "JULI": 7, "JUL": 7, "AGUSTUS": 8, "AGUST": 8,
    "AGU": 8, "AGT": 8, "AGST": 8, "SEPTEMBER": 9, "SEP": 9,
    "OKTOBER": 10, "OKTEBER": 10, "OKTO": 10, "OKT": 10,
    "NOVEMBER": 11, "NOPEMBER": 11, "NOV": 11, "NOPE": 11,
    "DESEMBER": 12, "DESE": 12, "DES": 12,
}
_BULAN_NAME = {
    1: "JANUARI", 2: "FEBRUARI", 3: "MARET", 4: "APRIL", 5: "MEI",
    6: "JUNI", 7: "JULI", 8: "AGUSTUS", 9: "SEPTEMBER", 10: "OKTOBER",
    11: "NOVEMBER", 12: "DESEMBER",
}


def _bulan_num(v) -> int:
    """Nomor bulan dari nilai kolom BULAN — TOKEN-SCAN karena file
    asli memakai kode periode: '201.OKT 26' → 10 (OKT), '8.OKTOBER' → 8,
    'JULI' / 'AGUSTUS 2026' → 7 / 8; angka 1..12 → bulan; tak dikenal → 0.
    (dipakai filter bulan-terbaru, dedup multi-bulan & pasangan flip)."""
    s = str(v).strip().upper()
    if not s or s == "NAN":
        return 0
    for tok in re.split(r"[^A-Z0-9]+", s):
        if not tok:
            continue
        if tok in _BULAN_NUM:
            return _BULAN_NUM[tok]
        with contextlib.suppress(ValueError, TypeError):
            iv = int(tok)
            if 1 <= iv <= 12:
                return iv
    return 0


def _bulan_label(v) -> str:
    """Label bulan kanonik dari nilai BULAN ('205.OKT 26' → 'OKTOBER';
    tak terparse → string mentah)."""
    n = _bulan_num(v)
    return _BULAN_NAME.get(n, str(v).strip())


def _h_to_week_target(h: int) -> int:
    """v3.9.7: H input → CUT-OFF minggu yang MEMUAT tanggal H
    (minggu file = rentang kumulatif dari tanggal 1):
        H 1–7 → 7 (WEEK 1) · H 8–14 → 14 (WEEK 2) ·
        H 15–25 → 25 (WEEK 3/4) · H 26–31 → 31 (WEEK 5)
    Total: semua H 1..31 terpetakan (H=7 → WEEK 1 persis permintaan
    user "H aku input 7 maka hanya tampilkan week 1")."""
    h = int(h)
    if h <= 7:
        return 7
    if h <= 14:
        return 14
    if h <= 25:
        return 25
    return 31

# Toleransi MATCH: |selisih| <= TOL_ABS + TOL_REL * |nilai file|
TOL_ABS = 1.0
TOL_REL = 0.0001

# v3.9.15 — konstanta analisa Gelombang 1 (pola repo Inventory-
# Control user): liga robust-z butuh populasi minimal & skala MAD.
LIGA_MIN_POPULASI = 5     # resto ber-BOM minimum per bahan (MIN_OUTLETS)
LIGA_MAD_SCALE = 1.4826   # Φ⁻¹(0.75) — MAD → setara simpangan baku

# File kecil utk mengingat path file deviasi terakhir (initialdir dialog)
_LAST_FILE_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "komparasi_last.json")


def _chrono(v):
    """Urutan kronologis kolom tanggal: -25 → -31 lalu 1 → 31
    (identik pivot_view._chrono — hari negatif = bulan lalu)."""
    try:
        iv = int(v)
        return (0, -iv) if iv < 0 else (1, iv)
    except (TypeError, ValueError):
        return (2, str(v))


def _norm_resto(v) -> str:
    """'1041.BDGUKU' / 'B.1001.MLGPAR' / 'BDGUKU' → 'BDGUKU'
    (upper + strip + segmen setelah titik TERAKHIR)."""
    s = str(v).strip().upper()
    if "." in s:
        s = s.split(".")[-1].strip()
    return s


def _norm_name(v) -> str:
    """Normalisasi nama barang utk pencocokan: upper + rapat spasi ganda."""
    return re.sub(r"\s+", " ", str(v).strip().upper())


def _week_h(label) -> "int | None":
    """'WEEK 1' → 7. Label tak dikenal → heuristik 7×n (maks 31),
    tanpa angka → None."""
    s = str(label).strip().upper()
    if s in WEEK_TO_H:
        return WEEK_TO_H[s]
    m = re.search(r"(\d+)", s)
    if m:
        return min(7 * int(m.group(1)), 31)
    return None


def _norm_col_map(df: pd.DataFrame) -> dict:
    """Peta kolom ternormalisasi (case/spasi diabaikan) → kolom asli."""
    cols = {}
    for c in df.columns:
        cols[str(c).strip().upper().replace(" ", "")] = c
    return cols


def _find_col(cols: dict, *cands):
    for cand in cands:
        key = cand.upper().replace(" ", "")
        if key in cols:
            return cols[key]
    return None


def _missing_required_columns(df: pd.DataFrame) -> list:
    """Label kolom wajib yang hilang dari df ([] = lengkap)."""
    cols = _norm_col_map(df)
    got = {
        "RESTO": _find_col(cols, "RESTO", "NAMARESTO", "CABANG"),
        "NAMA BAHAN": _find_col(cols, "NAMABAHAN", "NAMABARANG", "BARANG",
                                "ITEM"),
        "STATUS BULAN": _find_col(cols, "STATUSBULAN", "STATUSMINGGU",
                                  "WEEK", "MINGGU", "STATUS"),
        "QTY BOM": _find_col(cols, "QTYBOM", "BOM"),
        "QTY COM": _find_col(cols, "QTYCOM", "COM"),
        "QTY DEVIASI": _find_col(cols, "QTYDEVIASI", "DEVIASI"),
    }
    return [label for label, c in got.items() if c is None]


def parse_deviasi_file(path: str) -> dict:
    """Baca & validasi file deviasi (pure — tanpa Tk; mudah diuji).

    Return dict:
        ok: bool
        error: str (bila not ok)
        df: DataFrame ternormalisasi (kolom _resto_norm, _bahan_norm,
            _week, _h) atau None
        meta: {weeks, n_rows, n_resto, bulan, file_name, sheet,
               n_unknown_week, n_duplicates}

    v3.9.5 (audit 19-a #5/#11): duplikat lintas bulan DIHITUNG & dilaporkan
    via meta.n_duplicates (dulu dibuang diam-diam — file "History"
    multi-bulan); sheet dicoba satu per satu sampai ketemu sheet dengan
    kolom wajib (dulu hanya sheet pertama — data di sheet lain → error
    kolom yang menyesatkan).
    """
    meta = {"file_name": os.path.basename(path), "sheet": None,
            "weeks": [], "n_rows": 0, "n_resto": 0, "bulan": []}
    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        return {"ok": False, "error": f"Gagal membaca file: {e}",
                "df": None, "meta": meta}

    # v3.9.5 (audit 19-a #11): pilih sheet PERTAMA yang punya kolom wajib
    # & berisi baris; bila tidak ada → pakai sheet pertama utk pesan error.
    df = None
    sheet = None
    for sh in xl.sheet_names:
        cand = None
        with contextlib.suppress(Exception):
            cand = xl.parse(sh)
        if cand is None or cand.empty:
            if df is None:
                df, sheet = cand, sh
            continue
        if not _missing_required_columns(cand):
            df, sheet = cand, sh
            break
        if df is None or df.empty:
            df, sheet = cand, sh
    if df is None:
        return {"ok": False, "error": "File kosong (tidak ada baris).",
                "df": None, "meta": meta}
    meta["sheet"] = sheet

    if df.empty:
        return {"ok": False, "error": "File kosong (tidak ada baris).",
                "df": None, "meta": meta}

    missing = _missing_required_columns(df)
    if missing:
        return {"ok": False,
                "error": "Kolom wajib tidak ditemukan: "
                         + ", ".join(missing)
                         + ". Kolom file (sheet " + str(sheet) + "): "
                         + ", ".join(str(c) for c in df.columns[:12]),
                "df": None, "meta": meta}

    # --- deteksi kolom (nama fleksibel, case/space-insensitive) ---
    cols = _norm_col_map(df)
    col_resto = _find_col(cols, "RESTO", "NAMARESTO", "CABANG")
    col_bahan = _find_col(cols, "NAMABAHAN", "NAMABARANG", "BARANG", "ITEM")
    col_week = _find_col(cols, "STATUSBULAN", "STATUSMINGGU", "WEEK",
                         "MINGGU", "STATUS")
    col_bom = _find_col(cols, "QTYBOM", "BOM")
    col_com = _find_col(cols, "QTYCOM", "COM")
    col_dev = _find_col(cols, "QTYDEVIASI", "DEVIASI")
    col_sat = _find_col(cols, "SATUAN", "UOM", "UNIT")
    col_pct = None
    for k, orig in cols.items():
        if k.startswith("%") and "DEVIASI" in k and "BOM" in k:
            col_pct = orig
            break
    col_bulan = _find_col(cols, "BULAN", "MONTH")

    # v3.9.14 (istilah user): kolom sisi file kini bernama *Lalu
    # ("File" → "Lalu") — konsisten seluruh view & tabel analisa.
    out = pd.DataFrame({
        "Resto": df[col_resto].astype(str),
        "Nama Barang": df[col_bahan].astype(str),
        # v3.9.5 (audit 19-a #13): NaN → '' (astype(str) menghasilkan
        # literal 'nan')
        "Satuan": (df[col_sat].fillna("").astype(str)
                   if col_sat is not None else ""),
        "Minggu": df[col_week].astype(str).str.strip().str.upper(),
        "BOM Lalu": pd.to_numeric(df[col_bom], errors="coerce"),
        "COM Lalu": pd.to_numeric(df[col_com], errors="coerce"),
        "DEV Lalu": pd.to_numeric(df[col_dev], errors="coerce"),
    })
    out["%TO BOM Lalu"] = (pd.to_numeric(df[col_pct], errors="coerce")
                           if col_pct is not None else np.nan)
    out["BULAN"] = (df[col_bulan].fillna("").astype(str).str.strip()
                    if col_bulan is not None else "")

    # v3.9.13: BULAN dinormalisasi (upper/strip) + nomor urut bulan —
    # dipakai filter bulan-terbaru & analisa perubahan arah.
    out["BULAN"] = out["BULAN"].astype(str).str.strip().str.upper()
    out["_bulan_num"] = out["BULAN"].map(_bulan_num)

    out["_resto_norm"] = out["Resto"].map(_norm_resto)
    out["_bahan_norm"] = out["Nama Barang"].map(_norm_name)
    out["_h"] = out["Minggu"].map(_week_h)

    # minggu tak dikenal → baris dibuang (dilaporkan via meta)
    bad_week = out["_h"].isna()
    n_bad = int(bad_week.sum())
    out = out[~bad_week].copy()

    # duplikat (BULAN-num, minggu, resto, bahan) → keep first (file sampel
    # unik). v3.9.13: NOMOR BULAN masuk dedup-key — baris bulan lain TIDAK
    # lagi dibuang sebagai "duplikat" (dibutuhkan multi-file & analisa arah;
    # v3.9.5 dulu: baris bulan lain dibuang & dihitung di meta). Nomor
    # bulan (bukan string mentah) — file asli memakai kode periode
    # ("201.OKT 26" vs "202.OKT 26" = bulan SAMA).
    before_dedup = len(out)
    out = out.drop_duplicates(
        subset=["_bulan_num", "Minggu", "_resto_norm", "_bahan_norm"],
        keep="first")
    n_dup = before_dedup - len(out)

    # rapatkan index setelah filter
    out = out.reset_index(drop=True)

    weeks = sorted(out["Minggu"].unique().tolist())
    meta["weeks"] = weeks
    meta["n_rows"] = len(out)
    meta["n_resto"] = int(out["_resto_norm"].nunique())
    if "BULAN" in out.columns:
        bulan = [b for b in out["BULAN"].unique().tolist()
                 if b and b.lower() != "nan"]
        meta["bulan"] = sorted(bulan)[:6]
    meta["n_unknown_week"] = n_bad
    meta["n_duplicates"] = n_dup
    return {"ok": True, "error": None, "df": out, "meta": meta}


class KomparasiDeviasiView(tk.Frame):
    """Pane ⚖ Komparasi File Deviasi — pembanding file deviasi resmi
    vs hitungan app (Tab 📦 Deviasi GR) per (Resto × Barang × Minggu)."""

    COLUMNS = [
        ("✓", 34, "center"),
        ("Resto", 100, "w"),
        ("Nama Barang", 190, "w"),
        ("Satuan", 50, "w"),
        # v3.9.13 (permintaan user: "hapus kolom H di tab laporan deviasi,
        # minggu juga hapus"): kolom Minggu & H DIHAPUS dari TABEL — data
        # internal fdf["_h"]/"Minggu"/"BULAN" tetap hidup (filter minggu
        # ikut H bersama, join nilai app, popup detail, snapshot follow-up).
        # v3.9.14 (istilah user): *File → *Lalu, *App → *Saat Ini.
        ("BOM Lalu", 95, "e"),
        ("COM Lalu", 95, "e"),
        ("DEV Lalu", 100, "e"),
        ("%TO BOM Lalu", 85, "e"),
        ("BOM Saat Ini", 95, "e"),
        ("COM Saat Ini", 95, "e"),
        # v3.9.13 (user: "Dev to bom itu harusnya persen"): DEV versi app
        # kini RASIO = DEV·Saat Ini / |BOM·Saat Ini| (format persen —
        # konsisten kolom %TO BOM Lalu; dulu kuantitas COM−BOM).
        ("DEV Saat Ini", 85, "e"),
        ("GR Saat Ini", 100, "e"),
        ("Selisih", 100, "e"),
        ("Status", 120, "w"),
    ]

    NUMERIC_COLS = ("BOM Lalu", "COM Lalu", "DEV Lalu", "%TO BOM Lalu",
                    "BOM Saat Ini", "COM Saat Ini", "DEV Saat Ini",
                    "GR Saat Ini", "Selisih")

    # v3.9.13 — mode 📈 Analisa: kolom tabel Top Selisih & Perubahan Arah
    # v3.9.14 (istilah user): DEV File → DEV Lalu, GR App → GR Saat Ini,
    # DEV Sekarang → DEV Saat Ini.
    TOP_COLS = [
        ("Peringkat", 64, "e"),
        ("Periode", 170, "w"),
        ("Resto", 100, "w"),
        ("Nama Barang", 190, "w"),
        ("Satuan", 50, "w"),
        ("DEV Lalu", 95, "e"),
        ("GR Saat Ini", 95, "e"),
        ("Selisih", 95, "e"),
        # v3.9.16: 165 — memuat 'TIDAK ADA DI DATA SAAT INI' utuh
        # (156px @ font 10; dulu 120 → terpotong)
        ("Status", 165, "w"),
        # v3.9.19 — keterangan analisa per baris (1 kolom saja):
        # Kenaikan Tertinggi · Penurunan Tertinggi · Stabil ·
        # Berubah Arah · Potensi Flip Flop
        ("ANALISA", 150, "w"),
    ]
    FLIP_COLS = [
        ("Periode", 190, "w"),
        ("Resto", 100, "w"),
        ("Nama Barang", 190, "w"),
        ("Satuan", 50, "w"),
        ("DEV Bulan Lalu", 100, "e"),
        ("DEV Saat Ini", 100, "e"),
        ("Δ", 90, "e"),
        ("Disparitas", 85, "e"),
        ("Kategori", 90, "w"),
        # v3.9.19 — keterangan analisa per baris (1 kolom saja);
        # baris flip = semua perubahan arah → hanya Berubah Arah
        # (disparitas < 40%) / Potensi Flip Flop (≥ 40%)
        ("ANALISA", 150, "w"),
    ]

    # v3.9.19 — label & warna kolom ANALISA (Top Selisih & Flip)
    ANALISA_NAIK = "Kenaikan Tertinggi"
    ANALISA_TURUN = "Penurunan Tertinggi"
    ANALISA_STABIL = "Stabil"
    ANALISA_ARAH = "Berubah Arah"
    ANALISA_FFLOP = "Potensi Flip Flop"

    # v3.9.15 — GELOMBANG 1: kolom tabel analisa (bagian Risiko Flip &
    # Benchmark DIHAPUS v3.9.19 — RISK_COLS/BENCH_COLS ikut dihapus)
    MIN_COLS = [
        ("Peringkat", 64, "e"),
        ("Nama Barang", 190, "w"),
        ("Satuan", 50, "w"),
        ("Resto Mayoritas", 95, "e"),
        ("Resto Minoritas", 95, "e"),
        ("Arah Mayoritas", 105, "w"),
        ("Σ|DEV| Minoritas", 115, "e"),
        ("% Minoritas", 85, "e"),
    ]
    LIGA_COLS = [
        ("Peringkat", 64, "e"),
        ("Resto", 110, "w"),
        ("BOM", 90, "e"),
        ("DEV", 90, "e"),
        ("Arah", 70, "w"),
        ("Rate", 85, "e"),
        ("z", 70, "e"),
    ]

    def __init__(self, parent, go_to_proses: Callable | None = None,
                 followup_store: FollowUpStore | None = None,
                 initial_dir: str = "", h_state=None):
        super().__init__(parent, bg=C_BG)
        self.data: pd.DataFrame | None = None
        self.go_to_proses = go_to_proses
        self.store = followup_store
        self._initial_dir = initial_dir
        # v3.9.7: TANGGAL H = state bersama (dari tab 📦 Deviasi GR) —
        # dipakai FILTER MINGGU file (H=7 → hanya WEEK 1; pola chip
        # read-only tab Anomali COM). Komparasi TIDAK punya input H.
        self._h_state = h_state
        self.tanggal_h = int(h_state.h) if h_state is not None else 25
        self._fp_map: dict[str, str] = {}
        self._row_snaps: dict[str, dict] = {}
        self._busy = False
        self._pending = False
        self._dirty = False                 # lazy refresh
        # v3.9.5 (audit 19-a #1): generation counter — job async yang
        # sudah kedaluwarsa (file ditutup/diganti, data baru) dibuang di
        # done() supaya hasil file lama tidak muncul kembali.
        self._render_gen = 0
        self._insert_cancel = None         # batch insert yang berjalan
        # v3.9.13: file yang antre saat busy — LIST (multi-file)
        self._pending_paths: list | None = None
        self._pending_sort = None          # (col, reverse) antre saat busy
        # file deviasi yang sedang dibandingkan
        # v3.9.13: MULTI-FILE — daftar path + meta per-file + df gabungan
        self._file_df: pd.DataFrame | None = None
        self._file_meta: dict = {}
        self._file_metas: list = []        # meta per file (label per-file)
        self._file_paths: list = []
        # v3.9.13: join PENUH (semua bulan/minggu) utk mode 📈 Analisa
        # (Top Selisih & Perubahan Arah — tidak terpotong filter tampilan)
        self._join_df: pd.DataFrame | None = None
        # v3.9.13: default tabel = BULAN TERBARU (permintaan multi-file;
        # checkbox "Tampilkan semua bulan" = semua)
        self._show_all_months = tk.BooleanVar(value=False)
        # v3.9.13: sub-mode kartu filter — ⚖ Tabel / 📈 Analisa
        self._analisa_mode = False
        # v3.9.14 (PERF): analisa dirender MALAS — dirty saat data/join/
        # file baru; dirender saat mode 📈 Analisa aktif (dulu dirender
        # walau tersembunyi → freeze per refresh).
        self._analisa_dirty = True
        # v3.9.19 — bagian analisa aktif (0=Top&Flip, 1=Arah Minoritas,
        # 2=Liga Deviasi — Risiko Flip & Benchmark DIHAPUS v3.9.19)
        # + set bagian yang perlu render ulang saat data berubah
        # (hanya bagian AKTIF yang dirender — pola malas v3.9.14).
        self._anasec_idx = 0
        self._anasec_stale = {0, 1, 2}
        # v3.9.15a (audit P1-2): handle cancel batch insert per tabel
        # analisa — render ulang tabel yg sama membatalkan sisa batch
        # LAMA (batch 400-baris berjalan via after() bisa menambahkan
        # baris basi ke render baru bila re-render menembak di tengah
        # jendela antar-batch; pola _render_rows_inner tabel utama).
        self._anasec_cancel = {}
        # v3.9.13: file terakhir di-auto-load SEKALI saat tab terlihat
        self._auto_loaded = False
        # cache matriks app — per objek data + file
        self._cached_mats = None
        self._cached_signature = None
        # v3.9.5 (audit 19-b #4): identitas df utk cache (id() bisa
        # dipakai ulang CPython setelah GC; identitas objek lebih aman)
        self._cached_data = None
        self._satuan_lookup: dict = {}
        self._aktif_lookup: dict = {}   # v3.9.5 (audit 19-b #5): AKTIF/NON
        self._result_df = None
        # v3.9.5 (audit 19-a #2): (bahan_norm, resto_norm) → nama barang &
        # resto versi APP — dipakai popup detail (nama file RAW tidak
        # selalu cocok exact dgn nama app).
        self._pair_index: dict = {}
        # opsi tampilan
        self._show_all_resto = tk.BooleanVar(value=False)
        # v3.9.7: filter minggu mengikuti H bersama (default AKTIF);
        # checkbox "Tampilkan semua minggu" = perilaku lama (semua minggu)
        self._show_all_weeks = tk.BooleanVar(value=False)
        # v3.9.2: minus merah PER CELL
        self._cell_tags = CELL_TAGS_SUPPORTED
        self._neg_cells: list = []      # [(iid, col)] nilai < 0
        self._st_match_cells: list = []
        self._st_diff_cells: list = []
        self._st_missing_cells: list = []

        self._build_ui()
        self._setup_tags()
        self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="⚖", title="Belum ada data komparasi",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card: pemilih file + opsi ---
        fcard = Card(self.content,
                     title="⚖ Komparasi Deviasi — Lalu vs Saat Ini")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        self._fcard = fcard
        fbody = fcard.body()

        # v3.9.13 (permintaan user: "alamat file deviasi bisa tersimpan dan
        # bisa aku ubah"): ENTRY PATH — editable (multi-file dipisah ";"),
        # 📂 memilih file (multi-select), ↻ memuat ulang dari entry,
        # ✕ menutup. Path tersimpan di komparasi_last.json (auto-load
        # saat tab pertama terlihat).
        r1 = tk.Frame(fbody, bg=C_CARD)
        r1.pack(fill="x")
        btn_pick = GhostButton(r1, text="📂 Pilih File Deviasi…",
                               command=self._pick_file)
        btn_pick.pack(side="left")
        self._path_var = tk.StringVar(value="")
        self._path_entry = ttk.Entry(r1, textvariable=self._path_var)
        self._path_entry.pack(side="left", padx=(8, 6), fill="x",
                              expand=True)
        self._path_entry.bind("<Return>", lambda e: self._reload_file())
        self._btn_reload = GhostButton(r1, text="↻ Muat Ulang File",
                                       command=self._reload_file)
        self._btn_reload.pack(side="right")
        self._btn_close = GhostButton(r1, text="✕ Tutup File",
                                      command=self._close_file)
        self._btn_close.pack(side="right", padx=(0, 6))
        self._btn_close.configure(state="disabled")

        # v3.9.13: label info file (pindah ke baris sendiri — multi-file
        # butuh ruang; menampilkan ringkasan per-file + bulan).
        r1b = tk.Frame(fbody, bg=C_CARD)
        r1b.pack(fill="x", pady=(4, 0))
        self._file_label_var = tk.StringVar(
            value="Belum ada file dipilih.")
        self._file_label = tk.Label(
            r1b, textvariable=self._file_label_var, bg=C_CARD,
            fg=C_TEXT_MUTED, font=font(9), anchor="w", justify="left",
            wraplength=760)
        self._file_label.pack(side="left", fill="x", expand=True)

        # baris ke-2: TANGGAL H (read-only, bersama) + filter minggu +
        # opsi resto
        r2 = tk.Frame(fbody, bg=C_CARD)
        r2.pack(fill="x", pady=(6, 0))
        tk.Label(r2, text="TANGGAL H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        # v3.9.7: chip read-only — H dibagikan dari tab 📦 Deviasi GR
        # (pola tab Anomali COM; komparasi tanpa input H sendiri)
        self._h_chip_var = tk.StringVar(value=str(self.tanggal_h))
        hchip = tk.Frame(r2, bg="#f1f5f9", highlightbackground="#e2e8f0",
                         highlightthickness=1)
        hchip.pack(side="left", padx=(6, 8))
        tk.Label(hchip, textvariable=self._h_chip_var, bg="#f1f5f9",
                 fg=C_ACCENT, font=font(11, "bold")).pack(
            padx=10, pady=(2, 3))
        # label minggu aktif (dinamis — file & H)
        self._week_filter_var = tk.StringVar(
            value="belum ada file")
        self._week_filter_label = tk.Label(
            r2, textvariable=self._week_filter_var, bg=C_CARD,
            fg=C_TEXT_MUTED, font=font(9), anchor="w")
        self._week_filter_label.pack(side="left", padx=(2, 12))
        self._chk_all_weeks = tk.Checkbutton(
            r2, text="Tampilkan semua minggu", variable=self._show_all_weeks,
            bg=C_CARD, fg=C_HEADER, font=font(9), selectcolor="#ffffff",
            activebackground=C_CARD, activeforeground=C_HEADER,
            command=self._on_option_changed)
        self._chk_all_weeks.pack(side="left")
        # v3.9.13: multi-file — default hanya BULAN TERBARU; centang =
        # semua bulan (perilaku v3.9.12 saat file tunggal tanpa filter).
        self._chk_all_months = tk.Checkbutton(
            r2, text="Tampilkan semua bulan", variable=self._show_all_months,
            bg=C_CARD, fg=C_HEADER, font=font(9), selectcolor="#ffffff",
            activebackground=C_CARD, activeforeground=C_HEADER,
            command=self._on_option_changed)
        self._chk_all_months.pack(side="left", padx=(16, 0))
        self._chk_all = tk.Checkbutton(
            r2, text="Tampilkan resto di luar data saat ini",
            variable=self._show_all_resto, bg=C_CARD, fg=C_HEADER,
            font=font(9), selectcolor="#ffffff", activebackground=C_CARD,
            activeforeground=C_HEADER, command=self._on_option_changed)
        self._chk_all.pack(side="left", padx=(16, 0))

        GhostButton(r2, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="right",
                                                     padx=(0, 6))

        # baris ke-3: chip pemetaan minggu→H (minggu aktif di-highlight)
        # + chip BULAN aktif (v3.9.13 — multi-file)
        r3 = tk.Frame(fbody, bg=C_CARD)
        r3.pack(fill="x", pady=(6, 0))
        tk.Label(r3, text="MINGGU → H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._week_chips = tk.Frame(r3, bg=C_CARD)
        self._week_chips.pack(side="left", padx=(6, 16))
        tk.Label(r3, text="BULAN", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._month_chip_var = tk.StringVar(value="—")
        mchip = tk.Frame(r3, bg="#f1f5f9",
                         highlightbackground="#e2e8f0",
                         highlightthickness=1)
        mchip.pack(side="left", padx=(6, 0))
        tk.Label(mchip, textvariable=self._month_chip_var, bg="#f1f5f9",
                 fg=C_ACCENT, font=font(9, "bold")).pack(
            padx=8, pady=(2, 3))
        self._render_week_chips()

        # baris ke-4 (v3.9.13): sub-mode — ⚖ Tabel komparasi / 📈 Analisa
        # (Top Selisih + Perubahan Arah — adopsi rumus repo Inventory-
        # Control user).
        r4 = tk.Frame(fbody, bg=C_CARD)
        r4.pack(fill="x", pady=(8, 0))
        tk.Label(r4, text="MODE", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._mode_segment = SegmentBar(
            r4, ["⚖ Tabel", "📈 Analisa"],
            command=lambda idx: self._on_mode_change(idx))
        self._mode_segment.pack(side="left", padx=(6, 0))

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        self.tcard = tcard   # v3.9.13: mode 📈 Analisa pack/unpack
        tbody = tcard.body()

        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._title_label = tk.Label(
            head, text="Komparasi Deviasi — Lalu vs Saat Ini",
            bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        self._title_label.pack(side="left")
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel")
        btn_expand.pack(side="right", padx=(0, 6))
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="browse")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name)
        # heading penjelas tiap sisi
        self._update_headings()

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        enable_col_resize(self.tree)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.status_var_label = tk.StringVar(value="Belum ada file.")
        tk.Label(foot, textvariable=self.status_var_label, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold")).pack(side="right")

        self.overlay = LoadingOverlay(tbody, "Membandingkan deviasi…")

        _filter_cols = [c[0] for c in self.COLUMNS if c[0] != "✓"]
        self._col_sel: dict = {c: None for c in _filter_cols}
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))

        self._expander = TableExpander(btn_expand,
                                       [fcard, self._title_label])

        self.tree.bind("<Double-1>", self._on_double_click, add="+")  # FIX B-04
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

        # v3.9.13: mode 📈 Analisa (Top Selisih + Perubahan Arah) — dibangun
        # sekali, di-pack hanya saat sub-mode Analisa aktif.
        self._build_analisa_ui()

        # v3.9.7: berlangganan perubahan H bersama (filter minggu file
        # mengikuti H — "H aku input 7 maka hanya tampilkan week 1")
        if self._h_state is not None:
            self._h_state.subscribe(self._on_shared_h_changed)
            # pola laporan_deviasi_view (audit 19-b #3): lepas listener
            # saat view di-destroy (anti listener zombie)
            self.bind("<Destroy>", self._on_view_destroy, add="+")

    def _on_view_destroy(self, event):
        """v3.9.7: lepas langganan H bersama saat view di-destroy
        (hanya event utk view ini sendiri, bukan anak)."""
        if event.widget is self and self._h_state is not None:
            with contextlib.suppress(Exception):
                self._h_state.unsubscribe(self._on_shared_h_changed)

    # =========================================================================
    # TANGGAL H BERSAMA (v3.9.7) — filter minggu file
    # =========================================================================
    def _on_shared_h_changed(self, new_h: int):
        """Listener H bersama: H di-apply di tab 📦 Deviasi GR → chip H +
        label minggu + highlight chip diperbarui, tabel di-refresh dgn
        filter minggu baru (H=7 → WEEK 1 saja). Pane tersembunyi →
        cukup dirty (pola audit 19-c #3 — tidak compute yang tak terlihat)."""
        self.tanggal_h = int(new_h)
        self._update_h_chip()
        if self._dirty:
            return          # belum pernah dirender — refresh saat terlihat
        if not self.winfo_ismapped():
            self._dirty = True   # tersembunyi — refresh saat terlihat lagi
            return
        if (self.data is not None and not self.data.empty
                and self._file_df is not None):
            self._refresh()

    def _update_h_chip(self):
        """Chip H + label minggu aktif + highlight chip minggu."""
        if hasattr(self, "_h_chip_var"):
            self._h_chip_var.set(str(self.tanggal_h))
        self._update_week_filter_label()
        self._render_week_chips()

    def _update_week_filter_label(self):
        """Label '→ minggu: WEEK X' di kartu filter (dinamis: file + H)."""
        if not hasattr(self, "_week_filter_var"):
            return
        if self._file_df is None:
            self._week_filter_var.set("belum ada file")
        elif self._show_all_weeks.get():
            self._week_filter_var.set(
                "filter minggu NONAKTIF — semua minggu tampil")
        else:
            wt = _h_to_week_target(self.tanggal_h)
            weeks = [w for w in (self._file_meta.get("weeks") or [])
                     if _week_h(w) == wt]
            if weeks:
                self._week_filter_var.set(
                    f"→ minggu: {', '.join(weeks)}")
            else:
                self._week_filter_var.set(
                    f"→ minggu cut-off H {wt} TIDAK ADA di file")

    def _render_week_chips(self):
        """Chip 'WEEK 1→H 7' sesuai minggu yang ada di file (atau default).
        v3.9.7: minggu yang MEMUAT H aktif di-highlight teal (bila filter
        minggu aktif)."""
        for c in self._week_chips.winfo_children():
            c.destroy()
        weeks = (self._file_meta.get("weeks")
                 or ["WEEK 1", "WEEK 2", "WEEK 4"])
        wt = (None if self._show_all_weeks.get()
              else _h_to_week_target(self.tanggal_h))
        for w in weeks:
            h = _week_h(w)
            active = wt is not None and h is not None and int(h) == wt
            bg = C_ACCENT if active else "#f1f5f9"
            fg = "#ffffff" if active else C_ACCENT
            chip = tk.Frame(self._week_chips, bg=bg,
                            highlightbackground=(C_ACCENT if active
                                                 else "#e2e8f0"),
                            highlightthickness=1)
            chip.pack(side="left", padx=(0, 6))
            tk.Label(chip, text=f"{w} → H {h if h is not None else '?'}",
                     bg=bg, fg=fg, font=font(9, "bold")).pack(
                padx=8, pady=(2, 3))

    def _update_headings(self):
        """Heading dua sisi (File vs App) — jelas dari mana angka berasal.
        v3.9.13: DEV App kini RASIO (persen) — heading mengikuti."""
        # v3.9.14 (istilah user): App → Saat Ini, File → Lalu
        heads = {
            "BOM Lalu": "BOM — Lalu",
            "COM Lalu": "COM — Lalu",
            "DEV Lalu": "DEVIASI — Lalu",
            "%TO BOM Lalu": "% TO BOM — Lalu",
            "BOM Saat Ini": "BOM — Saat Ini (Σ jual 22.05)",
            "COM Saat Ini": "COM — Saat Ini (Σ pakai)",
            "DEV Saat Ini": "% TO BOM — Saat Ini",
            "GR Saat Ini": "DEVIASI — Saat Ini (Tab GR)",
            "Selisih": "Selisih (GR Saat Ini − DEV Lalu)",
        }
        for col, text in heads.items():
            self.tree.heading(col, text=text)
        if getattr(self, "header_filters", None) is not None:
            self.header_filters.refresh_icons()

    # =========================================================================
    # ✓ FOLLOW-UP (klik sel ✓) — pola identik view lain
    # =========================================================================
    def _on_tree_click(self, event):
        tree = event.widget
        try:
            if tree.identify_region(event.x, event.y) != "cell":
                return
            col = identify_to_column(tree, tree.identify_column(event.x))
            if col != "✓":
                return
            row_iid = tree.identify_row(event.y)
        except Exception:
            return
        if not row_iid or self.store is None:
            return
        fp = self._fp_map.get(row_iid)
        snap = self._row_snaps.get(row_iid)
        if not fp or snap is None:
            return
        added = self.store.toggle(fp, snap)
        try:
            tree.set(row_iid, "✓", CHECK_ON if added else CHECK_OFF)
        except tk.TclError:
            pass
        n = len(self.store)
        self.status_var_label.set(
            f"{'Masuk' if added else 'Keluar'} daftar Follow Up — total "
            f"{n} baris" if n else "Dikeluarkan — daftar Follow Up kosong")

    def ensure_refreshed(self):
        """Lazy refresh: compute hanya saat pane terlihat.
        v3.9.13: pemanggilan PERTAMA dengan data app + belum ada file →
        AUTO-LOAD file deviasi terakhir (komparasi_last.json; parse di
        worker — tidak membekukan UI; file hilang → status saja)."""
        if self._dirty and self.data is not None and not self.data.empty:
            self._dirty = False
            self._refresh()
        if (not self._auto_loaded and self.data is not None
                and not self.data.empty and not self._file_paths):
            self._auto_loaded = True
            paths = [p for p in self._read_last_paths()
                     if os.path.isfile(p)]
            if paths:
                self._load_paths(paths, interactive=False)

    def _col_values(self, col: str) -> list:
        result = self._result_df
        if result is None or result.empty or col not in result.columns:
            return []
        return self._format_col_series(col, result[col]).unique().tolist()

    def _format_col_series(self, col: str, series):
        if col in self.NUMERIC_COLS:
            # v3.9.13: DEV versi app kini RASIO — format persen (konsisten
            # %TO BOM Lalu). v3.9.14: nama kolom baru.
            if col in ("%TO BOM Lalu", "DEV Saat Ini"):
                return series.map(self._fmt_pct)
            return series.map(self._fmt_num)
        return series.astype(str)

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
        self._refresh()

    def _on_option_changed(self):
        # v3.9.7: label minggu + highlight chip ikut opsi semua-minggu
        # v3.9.13: chip bulan ikut opsi semua-bulan
        self._update_week_filter_label()
        self._render_week_chips()
        self._update_month_chip()
        self._refresh()

    def _update_month_chip(self):
        """v3.9.13: chip BULAN aktif — bulan TERBARU di file (per NOMOR
        bulan) / SEMUA / — bila belum ada file."""
        if not hasattr(self, "_month_chip_var"):
            return
        if self._file_df is None:
            self._month_chip_var.set("—")
        elif self._show_all_months.get():
            self._month_chip_var.set("SEMUA")
        else:
            nums = sorted({int(n) for n in
                           self._file_df["_bulan_num"].unique()
                           if int(n) > 0})
            self._month_chip_var.set(
                _BULAN_NAME.get(nums[-1], "—") if nums else "—")

    def _show_empty(self):
        self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        # fallback Tk 8 (tanpa tag cell): warna per BARIS
        tree.tag_configure("negative", foreground="#dc2626")
        # per-cell
        tree.tag_configure("neg_cell", foreground="#dc2626")
        tree.tag_configure("st_match", foreground="#15803d")
        tree.tag_configure("st_diff", foreground=C_AMBER)
        tree.tag_configure("st_missing", foreground="#dc2626")
        # v3.9.19 — warna keterangan kolom ANALISA (Top Selisih & Flip;
        # dipasang di sini supaya clone ⛶ kedua tabel + tabel utama juga
        # punya definisi tag — _setup_flip_tags memanggil _setup_tags):
        # kenaikan = merah (deviasi membesar), penurunan = hijau,
        # stabil = abu, berubah arah = ungu, potensi flip flop = amber.
        tree.tag_configure("ana_naik", foreground="#dc2626")
        tree.tag_configure("ana_turun", foreground="#15803d")
        tree.tag_configure("ana_stabil", foreground="#64748b")
        tree.tag_configure("ana_arah", foreground="#7c3aed")
        tree.tag_configure("ana_fflop", foreground="#b45309")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        # v3.9.5 (audit 19-a #1): data berganti → job lama dibuang
        self._render_gen += 1
        # v3.9.15a (audit P2-6): data app berganti → tabel analisa ikut
        # basi (join GR/BOM/COM Saat Ini) — _refresh jalur data-kosong
        # TIDAK menyentuh analisa; tandai dirty + stale semua bagian.
        self._analisa_dirty = True
        self._anasec_stale = {0, 1, 2}
        if self._insert_cancel is not None:
            self._insert_cancel()
            self._insert_cancel = None
        self._cached_mats = None
        self._cached_signature = None
        self._cached_data = None
        self._satuan_lookup = {}
        self._aktif_lookup = {}
        self._result_df = None
        self._join_df = None
        self._pair_index = {}
        if getattr(self, "_expander", None) is not None:
            self._expander.reset()
        self._show_content()
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        # lazy refresh — compute hanya bila pane terlihat
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    # =========================================================================
    # FILE DEVIASI
    # =========================================================================
    def _read_last_paths(self) -> list:
        """v3.9.13: baca komparasi_last.json — format baru {"paths": [...]}
        (multi-file) ATAU lama {"path": "..."} (v3.9.4-3.9.12)."""
        if not os.path.isfile(_LAST_FILE_JSON):
            return []
        try:
            with open(_LAST_FILE_JSON, "r", encoding="utf-8") as f:
                last = json.load(f)
        except Exception:
            return []
        if isinstance(last.get("paths"), list):
            return [str(p) for p in last["paths"] if str(p)]
        p = str(last.get("path") or "")
        return [p] if p else []

    def _pick_file(self):
        if self.data is None or self.data.empty:
            messagebox.showinfo(
                "Belum ada data saat ini",
                "Jalankan pipeline dulu (tab 🚀 Proses) supaya ada data "
                "saat ini untuk dibandingkan dengan file deviasi.",
                parent=self.winfo_toplevel())
            return
        initialdir = self._initial_dir or None
        # ingat folder terakhir bila ada (v3.9.13: daftar multi-file)
        last_paths = self._read_last_paths()
        if last_paths:
            d = os.path.dirname(last_paths[0])
            if d and os.path.isdir(d):
                initialdir = d
        # v3.9.13 (permintaan user: "bisa multi file di file deviasi"):
        # MULTI-SELECT — semua file diparse & digabung dalam 1 job worker.
        paths = filedialog.askopenfilenames(
            parent=self.winfo_toplevel(),
            title="Pilih File Deviasi (bisa lebih dari satu)",
            initialdir=initialdir,
            filetypes=[("Excel", "*.xlsx *.xlsm *.xls *.xlsb"),
                       ("Semua file", "*.*")])
        if not paths:
            return
        self._load_paths(list(paths))

    def _load_paths(self, paths, interactive: bool = True):
        """v3.9.13: MULTI-FILE — parse SEMUA file dalam SATU job worker
        (pola anti-beku v3.9.5 tetap; file 9,4MB ±8 detik/file).
        Filter header file LAMA direset DI SINI (sebelum job) — payload
        memakai snapshot state saat job mulai (audit 19-c #5).
        interactive=False (auto-load startup): error → status, tanpa dialog."""
        if self.data is None or self.data.empty:
            if interactive:
                messagebox.showinfo(
                    "Belum ada data saat ini",
                    "Jalankan pipeline dulu (tab 🚀 Proses) supaya ada data "
                    "saat ini untuk dibandingkan dengan file deviasi.",
                    parent=self.winfo_toplevel())
            else:
                self.status_var_label.set(
                    "Belum ada data saat ini — jalankan pipeline "
                    "(tab 🚀 Proses).")
            return
        paths = [str(p).strip() for p in paths if str(p).strip()]
        if not paths:
            return
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._refresh(parse_paths=paths, interactive=interactive)

    def _apply_file_state(self, new_file: dict, paths: list | None):
        """Simpan state file yang baru selesai diparse (main thread).
        v3.9.13: MULTI-FILE — daftar path + meta per-file; path list
        tersimpan di komparasi_last.json {"paths": [...]} (format baru).
        FIX BUG v3.9.10 (D-06): `.with_suffix()` dipanggil pada STR
        (os.path.join) → AttributeError ditelan `except Exception: pass`
        → json TIDAK PERNAH tersimpan sejak v3.9.10 ("ingat file terakhir"
        mati senyap). Kini tmp via konkatenasi string murni (nama file
        hasil identik: komparasi_last.json.tmp)."""
        self._file_df = new_file["df"]
        self._file_meta = new_file["meta"]
        self._file_metas = new_file.get("metas") or []
        if paths:
            self._file_paths = [str(p) for p in paths]
            try:
                tmp = _LAST_FILE_JSON + ".json.tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({"paths": self._file_paths}, f)
                os.replace(tmp, _LAST_FILE_JSON)
            except Exception:
                pass
            # entry mencerminkan file aktif — TETAP EDITABLE user
            # (permintaan: "alamat file deviasi bisa tersimpan dan bisa
            # aku ubah"; multi-file dipisah ";")
            self._path_var.set("; ".join(self._file_paths))
        self._btn_close.configure(state="normal")
        self._render_week_chips()
        self._update_week_filter_label()
        self._update_month_chip()
        if len(self._file_metas) > 1:
            parts = [f"{m['file_name']} ({m.get('n_rows', 0)} baris)"
                     for m in self._file_metas]
            info = (f"{len(self._file_metas)} file · " + " · ".join(parts)
                    + f" · total {self._file_meta['n_rows']} baris · "
                    + f"{self._file_meta['n_resto']} resto")
        else:
            meta = self._file_meta
            info = (f"{meta['file_name']} · {meta['n_rows']} baris · "
                    f"{meta['n_resto']} resto · "
                    + f"{', '.join(meta['weeks'])}")
        if self._file_meta.get("bulan"):
            info += f" · BULAN: {', '.join(self._file_meta['bulan'])}"
        if self._file_meta.get("n_skipped"):
            info += (f" · ⚠ {self._file_meta['n_skipped']} file gagal "
                     "dibaca (dilewati)")
        if self._file_meta.get("n_unknown_week"):
            info += (f" · {self._file_meta['n_unknown_week']} baris minggu "
                     f"tak dikenal dibuang")
        if self._file_meta.get("n_duplicates"):
            info += (f" · {self._file_meta['n_duplicates']} baris duplikat "
                     f"(bulan+minggu+resto+bahan sama) dibuang")
        self._file_label_var.set(info)
        self._file_label.configure(fg=C_HEADER)

    def _close_file(self):
        # v3.9.5 FIX (audit 19-a #1 — P1): ✕ Tutup saat job komparasi masih
        # berjalan → job lama harus dibuang. Tanpa ini, hasil compute file
        # yang barusan ditutup tetap di-render kembali oleh done() (3.418
        # baris + footer file lama muncul lagi padahal label "Belum ada
        # file"). Generation counter + pembatalan batch insert.
        self._render_gen += 1
        self._pending = False
        self._pending_paths = None
        self._pending_sort = None
        if self._insert_cancel is not None:
            self._insert_cancel()
            self._insert_cancel = None
        self._file_df = None
        self._file_meta = {}
        self._file_metas = []
        self._file_paths = []
        self._join_df = None
        self._pair_index = {}
        self._btn_close.configure(state="disabled")
        self._file_label_var.set("Belum ada file dipilih.")
        self._file_label.configure(fg=C_TEXT_MUTED)
        self._path_var.set("")
        self._render_week_chips()
        # v3.9.7: label minggu kembali 'belum ada file'
        self._update_week_filter_label()
        self._update_month_chip()
        self.tree.delete(*self.tree.get_children())
        self._result_df = None
        self._neg_cells = []
        self._st_match_cells = []
        self._st_diff_cells = []
        self._st_missing_cells = []
        # v3.9.5 (audit 19-c #5): reset filter header saat file ditutup
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self.status_var_label.set("File ditutup.")
        # v3.9.13: tabel analisa ikut dibersihkan.
        # v3.9.14 (PERF): hanya render bila mode Analisa aktif — tersembunyi
        # → dirty (dibersihkan saat pengguna masuk mode Analisa).
        # v3.9.15: state bagian analisa ikut dikosongkan (Risiko Flip &
        # Benchmark dihapus v3.9.19).
        self._min_df = None
        self._min_scope_df = None
        self._min_maj_sign = None
        self._liga_df = None
        self._liga_stats = {}
        self._liga_bahan_norm = None
        self._anasec_stale = {0, 1, 2}
        # v3.9.15a (audit P1-2): batalkan sisa batch insert tabel analisa.
        for _c in self._anasec_cancel.values():
            if _c is not None:
                _c()
        self._anasec_cancel = {}
        if self._analisa_mode:
            self._refresh_analisa()
        else:
            self._analisa_dirty = True

    def _reload_file(self):
        """v3.9.13: sumber reload = ENTRY (editable — user bisa mengubah
        path tanpa dialog; multi-file dipisah ";"); fallback file aktif
        / dialog. (permintaan: "alamat file deviasi bisa aku ubah")"""
        raw = (self._path_var.get() or "").strip()
        paths = [p.strip() for p in raw.split(";") if p.strip()]
        if paths:
            self._load_paths(paths)
        elif self._file_paths:
            self._load_paths(list(self._file_paths))
        else:
            self._pick_file()

    # =========================================================================
    # COMPUTATION — matriks app (H-independen, cache per data)
    # =========================================================================
    def _compute_matrices(self, data: pd.DataFrame | None = None) -> "dict | None":
        """FIX D-01 (audit 2-d): data bisa di-pass eksplisit (identitas
        pra-capture worker) — default membaca self.data (kompatibel test)."""
        """Pivot data app per (Nama Barang × NAMA RESTO) × tanggal untuk
        JENIS yang dipakai komparasi. Formula com identik
        laporan_deviasi_view._compute_com_matrix / pivot 6.PEMAKAIAN (COM):
            com(t=1)  = SALDO AWAL + IN(1) − BK(1) − SO(1)   (bila SA ada)
            com(t>1)  = SO(t-1) + IN(t) − BK(t) − SO(t)
        Ditambah matriks so / sis (2.SALDO AKHIR) / out (9.ACR).

        v3.9.5 FIX (audit 19-a #6 / 19-b #2): base com di TANGGAL 1 kini
        SALDO AWAL milik pair (baris SA ber-Tanggal=1, fn_4217) bila ada;
        fallback SO(t-1) via shift (tanggal negatif bulan lalu), fallback 0.
        SEMANTIK LAMA: SA ditempel ke kolom kronologis PERTAMA GLOBAL —
        saat data memuat tanggal negatif (pipeline FULL), kolom pertama =
        −25 (SA=0 di situ) → SA tidak pernah terpakai, com(1) memakai
        SO(−31), dan pair TANPA data bulan lalu mendapat com(1) =
        IN−BK−SO ≈ −SO(1) = MINUS PALSU (431/654 anomali H=1 di data
        real). Dengan SA sebagai base: GR·App == DEV·App secara aljabar
        (Sistem fn_running_stock juga berbasis SA). Fix diterapkan ke 3
        tempat sekaligus (pivot, laporan, komparasi) supaya formula COM
        tetap identik antar view.
        """
        df = self.data if data is None else data
        if df is None or df.empty:
            return None

        jenis_needed = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "4.IN",
                        "8.BARANG KELUAR", "9.ACR"]
        d = df[df["JENIS"].astype(str).isin(jenis_needed)].copy()
        if d.empty:
            self._build_satuan_lookup(df)
            return None
        d["_tgl"] = pd.to_numeric(d["Tanggal"], errors="coerce")
        d = d.dropna(subset=["_tgl"])
        d["NILAI"] = pd.to_numeric(d["NILAI"], errors="coerce")
        if d.empty:
            self._build_satuan_lookup(df)
            return None

        try:
            pivot = d.pivot_table(
                index=["Nama Barang", "NAMA RESTO", "JENIS"],
                columns="_tgl", values="NILAI",
                aggfunc="sum", fill_value=0,
            )
        except Exception:
            self._build_satuan_lookup(df)
            return None
        if pivot.empty:
            self._build_satuan_lookup(df)
            return None

        col_keys = sorted(pivot.columns.tolist(), key=_chrono)
        pairs = pivot.index.droplevel("JENIS").unique()

        def jenis_df(jenis: str, fill: bool = True) -> pd.DataFrame:
            try:
                sub = pivot.xs(jenis, level="JENIS")
            except KeyError:
                sub = pd.DataFrame()
            out = (sub.reindex(index=pairs, columns=col_keys)
                   .astype("float64"))
            return out.fillna(0.0) if fill else out

        so = jenis_df("1.SO")
        sis = jenis_df("2.SALDO AKHIR")
        bm = jenis_df("4.IN")
        bk = jenis_df("8.BARANG KELUAR")
        out = jenis_df("9.ACR")

        so_prev = so.shift(1, axis=1).fillna(0.0)
        # v3.9.5 (audit 19-a #6 / 19-b #2): base com tanggal 1 = SALDO
        # AWAL pair (tanpa fillna — membedakan 'SA ada, nilainya 0' dari
        # 'SA tidak ada') bila ada; fallback SO(t-1) shift; kolom pertama
        # tanpa SA → 0 (tidak ada data sebelumnya).
        if len(col_keys):
            so_prev.iloc[:, 0] = 0.0
        pos1 = [c for c in col_keys if int(float(c)) == 1]
        if pos1:
            sa_raw = jenis_df("SALDO AWAL", fill=False)
            key1 = pos1[0]
            so_prev[key1] = sa_raw[key1].fillna(so_prev[key1])
        com = so_prev + bm - bk - so

        self._build_satuan_lookup(df)
        self._build_aktif_lookup(df)
        return {"pairs": pairs, "col_keys": col_keys, "com": com,
                "out": out, "so": so, "sis": sis}

    def _build_aktif_lookup(self, df: pd.DataFrame):
        """v3.9.5 (audit 19-b #5): lookup AKTIF/NON per barang — mengisi
        snapshot follow-up (kolom AKTIF/NON di tab ☑ Follow Up; sebelumnya
        kosong utk baris asal KOMPARASI)."""
        self._aktif_lookup = {}
        if "AKTIF/NON" in df.columns and "Nama Barang" in df.columns:
            adf = (df[["Nama Barang", "AKTIF/NON"]]
                   .dropna(subset=["AKTIF/NON"])
                   .drop_duplicates(subset=["Nama Barang"], keep="first"))
            self._aktif_lookup = dict(zip(
                adf["Nama Barang"].astype(str),
                adf["AKTIF/NON"].astype(str)))

    def _build_satuan_lookup(self, df: pd.DataFrame):
        self._satuan_lookup = {}
        if "SATUAN" in df.columns and "Nama Barang" in df.columns \
                and "NAMA RESTO" in df.columns:
            sat = (df[["Nama Barang", "NAMA RESTO", "SATUAN"]]
                   .dropna(subset=["SATUAN"])
                   .drop_duplicates(subset=["Nama Barang", "NAMA RESTO"],
                                    keep="first"))
            self._satuan_lookup = {
                (nb, nr): s
                for nb, nr, s in zip(sat["Nama Barang"].astype(str),
                                     sat["NAMA RESTO"].astype(str),
                                     sat["SATUAN"].astype(str))
            }

    def _per_h_values(self, mats: dict, h_list: list) -> dict:
        """Nilai app per H: gr (SO_H − Sistem_H), bom_app, com_app, dev_app.

        bom_app / com_app memakai KONVENSI FILE (pemakaian = minus)
        supaya kolom berdampingan langsung bisa dibandingkan:
            bom_app = −Σ out[t], com_app = −Σ com[t], t = 1..H
            dev_app = com_app − bom_app (formula identik file)
            gr      = so[H] − sis[H]  (persis tab 📦 Deviasi GR)
        """
        out = {}
        col_keys = mats["col_keys"]
        com, outm, so, sis = (mats["com"], mats["out"],
                              mats["so"], mats["sis"])
        for h in h_list:
            h = int(h)
            pos = [t for t in col_keys if 1 <= float(t) <= h]
            has_h = any(int(float(t)) == h for t in col_keys)
            entry = {"has_h": has_h, "h": h}
            if has_h:
                key_h = next(t for t in col_keys if int(float(t)) == h)
                entry["gr"] = (so[key_h] - sis[key_h]).astype("float64")
                entry["so_h"] = so[key_h]
                entry["sis_h"] = sis[key_h]
            else:
                entry["gr"] = None
            if pos:
                com_app = -com[pos].sum(axis=1).astype("float64")
                bom_app = -outm[pos].sum(axis=1).astype("float64")
            else:
                com_app = pd.Series(0.0, index=com.index)
                bom_app = pd.Series(0.0, index=com.index)
            entry["com_app"] = com_app
            entry["bom_app"] = bom_app
            entry["dev_app"] = com_app - bom_app
            out[h] = entry
        return out

    # =========================================================================
    # RENDER (async + batched)
    # =========================================================================
    def _refresh(self, sync: bool = False, parse_paths: list | None = None,
                 interactive: bool = True):
        if self.data is None or self.data.empty:
            # v3.9.5 (audit 19-a #12): bersihkan baris basi — dulu early-
            # return meninggalkan baris render lama tetap tampil
            if self._insert_cancel is not None:
                self._insert_cancel()
                self._insert_cancel = None
            try:
                self.tree.delete(*self.tree.get_children())
            except tk.TclError:
                pass
            self.status_var_label.set(
                "Belum ada data. Jalankan pipeline di tab Proses.")
            return
        if parse_paths is None and self._file_df is None:
            if self._insert_cancel is not None:
                self._insert_cancel()
                self._insert_cancel = None
            try:
                self.tree.delete(*self.tree.get_children())
            except tk.TclError:
                pass
            self._result_df = None
            self.status_var_label.set("Belum ada file deviasi.")
            return

        if self._busy:
            self._pending = True
            if parse_paths is not None:
                self._pending_paths = list(parse_paths)
            return
        self._busy = True
        # v3.9.7 FIX (ditemukan test §22): _dirty di-CLEAR saat refresh
        # BERJALAN — dulu hanya ensure_refreshed yang me-clear →
        # load_data saat PANE TERLIHAT me-render tabel tapi _dirty tetap
        # True → listener H berikutnya salah menganggap 'belum pernah
        # dirender' & SKIP refresh (tabel basi menampilkan minggu lama).
        self._dirty = False
        # v3.9.5 (audit 19-a #1): gen naik tiap job — done() membuang job
        # yang kedaluwarsa (file ditutup/diganti/data baru).
        gen = self._render_gen = self._render_gen + 1

        st = {
            # v3.9.13: seleksi kosong = filter AKTIF (0 baris —
            # search-to-select Enter; jangan ditelan truthiness).
            "col_sel": {c: s for c, s in self._col_sel.items()
                        if s is not None},
            "show_all": bool(self._show_all_resto.get()),
            # v3.9.7: filter minggu sesuai H bersama (None = semua minggu)
            "week_target": (None if self._show_all_weeks.get()
                            else _h_to_week_target(int(self.tanggal_h))),
            "h_label": int(self.tanggal_h),
            # v3.9.13: filter bulan aktif? (target dihitung dari file di
            # _prepare_rows — st dibuat SEBELUM file baru selesai diparse)
            "month_filter": bool(self._show_all_months.get() is False
                                  and not self._show_all_months.get()),
        }
        paths = list(parse_paths) if parse_paths is not None else None

        def work():
            # v3.9.5 (audit 19-a #4): parse file ikut di thread worker —
            # file 9,4MB tadinya membekukan UI ±8 detik (tanpa overlay).
            # v3.9.13: MULTI-FILE — semua file diparse berurutan; file
            # gagal DILEWATI (dilaporkan) selama ≥1 file berhasil.
            new_file = None
            if paths is not None:
                dfs = []
                metas = []
                errors = []
                for p in paths:
                    res = parse_deviasi_file(p)
                    if not res["ok"]:
                        errors.append(f"{os.path.basename(p)}: "
                                      f"{res['error']}")
                        continue
                    res["meta"]["path"] = p
                    dfs.append(res["df"])
                    metas.append(res["meta"])
                if not dfs:
                    return {"gen": gen, "parse_error":
                            "Semua file gagal dibaca:\n" + "\n".join(errors)}
                combined = (dfs[0] if len(dfs) == 1
                            else pd.concat(dfs, ignore_index=True))
                # dedup LINTAS file (key sama dgn parse — keep first)
                before = len(combined)
                combined = combined.drop_duplicates(
                    subset=["_bulan_num", "Minggu", "_resto_norm",
                            "_bahan_norm"], keep="first")
                n_cross = before - len(combined)
                agg = {
                    "file_name": (f"{len(metas)} file"
                                  if len(metas) > 1
                                  else metas[0]["file_name"]),
                    "sheet": metas[0].get("sheet"),
                    "weeks": sorted({w for m in metas
                                     for w in (m.get("weeks") or [])}),
                    "n_rows": len(combined),
                    "n_resto": int(combined["_resto_norm"].nunique()),
                    "bulan": sorted({b for m in metas
                                     for b in (m.get("bulan") or [])}),
                    "n_unknown_week": int(sum(
                        m.get("n_unknown_week", 0) for m in metas)),
                    "n_duplicates": int(sum(
                        m.get("n_duplicates", 0) for m in metas) + n_cross),
                }
                if errors:
                    agg["n_skipped"] = len(errors)
                new_file = {"ok": True, "error": None, "df": combined,
                            "meta": agg, "metas": metas}
            # FIX D-01 (audit 2-d): capture identitas SEKALI di awal job —
            # dulu _cached_data dibaca ULANG setelah compute; bila self.data
            # ditukar main thread (load_data pipeline selesai) di tengah
            # compute, cache berlabel data BARU berisi matrix data LAMA →
            # refresh berikutnya SKIP recompute (angka basi senyap;
            # gen-guard hanya membuang RENDER basi, bukan cache salah-label).
            data = self.data
            if (self._cached_mats is None
                    or self._cached_data is not data):
                self._cached_mats = self._compute_matrices(data)
                self._cached_data = data
                self._cached_signature = id(data)
            return self._prepare_rows(st, new_file, gen)

        def done(payload):
            if payload.get("gen") != self._render_gen:
                # v3.9.5 (audit 19-a #1): job kedaluwarsa — buang hasil;
                # jalankan yang mengantre (file baru / refresh data baru)
                # supaya state tidak macet.
                self._busy = False
                p = self._pending_paths
                self._pending_paths = None
                if p:
                    self._load_paths(p)
                elif self._pending:
                    self._pending = False
                    self._refresh()
                return
            if payload.get("parse_error"):
                self._busy = False
                self._pending = False
                self._pending_paths = None
                if interactive:
                    messagebox.showerror(
                        "File deviasi tidak valid",
                        payload["parse_error"],
                        parent=self.winfo_toplevel())
                self.status_var_label.set(f"⚠ {payload['parse_error']}")
                return
            if payload.get("new_file"):
                self._apply_file_state(payload["new_file"], paths)
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Memuat & membandingkan deviasi…", sync=sync,
                  on_error=self._on_error)

    def _on_error(self, err):
        """FIX B-01: _busy di-reset di jalur error supaya view tidak
        mati permanen setelah 1x gagal compute."""
        self._busy = False
        self._pending = False
        self._pending_paths = None
        self.status_var_label.set(f"⚠ Gagal membandingkan: {err}")

    def _prepare_rows(self, st: dict, new_file: dict | None = None,
                      gen: int = 0) -> dict:
        """Pure pandas: gabung file × matriks app → baris komparasi
        (delegasi ke implementasi vektor — thread-safe).

        v3.9.5: fdf/new_file diteruskan EKSPLISIT (bukan membaca
        self._file_df dari thread — mutasi UI thread di tengah compute
        = sumber race ✕ Tutup File).
        v3.9.7: FILTER MINGGU sesuai H bersama (st['week_target'] — None
        bila 'Tampilkan semua minggu') — v3.9.13 dipindah SETELAH join
        (join penuh disimpan dulu utk mode 📈 Analisa).
        v3.9.13: MULTI-FILE — target BULAN TERBARU dihitung di sini dari
        fdf aktual (st dibuat SEBELUM file baru selesai diparse, jadi
        target tidak bisa dihitung di _refresh).
        """
        fdf = new_file["df"] if new_file else self._file_df
        mats = self._cached_mats
        if fdf is None:
            return {"gen": gen, "items": [],
                    "status": "Belum ada file."}
        if mats is None:
            self._result_df = None
            return {"gen": gen, "items": [], "status":
                    "Data saat ini tidak punya JENIS yang dibutuhkan "
                    "(SO / SALDO AKHIR / IN / OUT). Jalankan ulang pipeline."}

        # v3.9.13: bulan TERBARU dari file aktual — berdasarkan NOMOR bulan
        # (kode periode "201.OKT"/"204.OKT" = bulan SAMA); tanpa bulan →
        # tanpa filter. (checkbox "Tampilkan semua bulan" → None).
        target = None
        label = None
        if st.get("month_filter"):
            nums = sorted({int(n) for n in fdf["_bulan_num"].unique()
                           if int(n) > 0})
            if nums:
                target = nums[-1]
                label = _BULAN_NAME.get(target, str(target))
        st["month_target"] = target
        st["month_label"] = label

        col_keys = mats["col_keys"]
        avail_pos = sorted(int(float(t)) for t in col_keys
                           if float(t) >= 1)
        avail_max = avail_pos[-1] if avail_pos else 0

        # v3.9.13: h_list dari fdf PENUH (semua bulan & minggu) — join
        # dibuat penuh dulu (sumber 📈 Analisa), tabel memfilter salinan.
        h_list = sorted({int(v) for v in fdf["_h"]})
        per_h = self._per_h_values(mats, h_list)

        # lookup app: (bahan_norm, resto_norm) → pasangan (barang, resto)
        pair_index = {}
        for (nb, nr) in mats["pairs"]:
            pair_index[(_norm_name(nb), _norm_resto(nr))] = (nb, nr)
        resto_set = {_norm_resto(nr) for (_, nr) in mats["pairs"]}

        return self._prepare_rows_vec(fdf, per_h, pair_index, resto_set,
                                      st, avail_max, gen, new_file)

    def _prepare_rows_vec(self, fdf, per_h, pair_index, resto_set,
                          st, avail_max, gen=0, new_file=None) -> dict:
        """Implementasi vektor _prepare_rows — akses kolom berspasi aman
        via DataFrame pandas (tanpa itertuples).

        v3.9.13: (a) join PENUH (semua bulan & minggu) disimpan ke
        self._join_df — sumber mode 📈 Analisa (Top Selisih & Perubahan
        Arah tidak terpotong filter tampilan); (b) filter BULAN (terbaru)
        + MINGGU (cut-off H bersama) diterapkan SETELAH join (urutan:
        resto → bulan → minggu — resto dipakai mask posisi fdf); (c)
        kolom Minggu/H/BULAN INTERNAL — tidak ditampilkan (permintaan
        user); (d) DEV App = RASIO persen (DEV·App / |BOM·App|)."""
        df = pd.DataFrame({
            "Resto": fdf["Resto"].astype(str).values,
            "Nama Barang": fdf["Nama Barang"].astype(str).values,
            "Satuan": fdf["Satuan"].astype(str).values,
            # v3.9.13: INTERNAL — kolom Minggu/H dihapus dari TABEL
            # (permintaan user); tetap dipakai filter/snapshot/popup.
            "Minggu": fdf["Minggu"].astype(str).values,
            "BULAN": fdf["BULAN"].astype(str).values,
            "_bulan_num": fdf["_bulan_num"].astype(int).values,
            "H": fdf["_h"].astype(int).values,
            # v3.9.14: kunci merge (nilai app per baris) + istilah *Lalu
            "_bahan_norm": fdf["_bahan_norm"].astype(str).values,
            "_resto_norm": fdf["_resto_norm"].astype(str).values,
            "BOM Lalu": pd.to_numeric(fdf["BOM Lalu"],
                                      errors="coerce").fillna(0.0).values,
            "COM Lalu": pd.to_numeric(fdf["COM Lalu"],
                                      errors="coerce").fillna(0.0).values,
            "DEV Lalu": pd.to_numeric(fdf["DEV Lalu"],
                                      errors="coerce").fillna(0.0).values,
            "%TO BOM Lalu": pd.to_numeric(fdf["%TO BOM Lalu"],
                                          errors="coerce").values,
        })

        # --- v3.9.14 (PERF): nilai app per baris via MERGE VEKTOR ------
        # app_long = satu baris per (bahan_norm, resto_norm, H) berisi
        # nilai app (bom/com/dev/gr + has_h). Dulu: loop Python per baris
        # file dengan Series.get per sel — 40rb baris = ±2,9 dtk; merge
        # = ±60ms, hasil terverifikasi IDENTIK baris-per-baris ( nilai +
        # status + urutan). Duplikat kunci ternormalisasi → keep LAST
        # (semantik dict pair_index lama).
        frames = []
        for h, ph in per_h.items():
            s = ph["bom_app"]
            pidx = s.index.to_frame(index=False)
            pidx.columns = ["nb", "nr"]
            bn = (pidx["nb"].astype(str).str.strip().str.upper()
                  .str.replace(r"\s+", " ", regex=True))
            rn = (pidx["nr"].astype(str).str.strip().str.upper()
                  .str.replace(r"\s+", " ", regex=True)
                  .str.split(".").str[-1].str.strip())
            if ph["has_h"]:
                bom_v = s.to_numpy(dtype="float64")
                com_v = ph["com_app"].to_numpy(dtype="float64")
                dev_v = ph["dev_app"].to_numpy(dtype="float64")
                gr_v = ph["gr"].to_numpy(dtype="float64")
            else:
                # H tidak ada di data → SEMUA nilai app NaN (perilaku
                # lama: assignment di-skip → tampil '—' + status
                # 'H TIDAK ADA DI DATA').
                n0 = len(s)
                bom_v = np.full(n0, np.nan)
                com_v = np.full(n0, np.nan)
                dev_v = np.full(n0, np.nan)
                gr_v = np.full(n0, np.nan)
            frames.append(pd.DataFrame({
                "_bahan_norm": bn.to_numpy(),
                "_resto_norm": rn.to_numpy(),
                "H": int(h),
                "bom_app": bom_v,
                "com_app": com_v,
                "dev_app": dev_v,
                "gr_app": gr_v,
                "has_h": bool(ph["has_h"]),
            }))
        app_long = (pd.concat(frames, ignore_index=True) if frames else
                    pd.DataFrame(columns=["_bahan_norm", "_resto_norm",
                                          "H", "bom_app", "com_app",
                                          "dev_app", "gr_app", "has_h"]))
        app_long = app_long.drop_duplicates(
            subset=["_bahan_norm", "_resto_norm", "H"], keep="last")

        # join kiri (urutan baris file dipertahankan; baris tanpa
        # pasangan app → NaN → 'TIDAK ADA DI DATA SAAT INI')
        df = df.merge(app_long, on=["_bahan_norm", "_resto_norm", "H"],
                      how="left")
        in_app = df["has_h"].notna().to_numpy()
        # v3.9.15b (audit-2 FIX): .eq(True) — NaN → False TANPA fillna
        # (pandas 2.2: fillna pada kolom object hasil merge memuntahkan
        # FutureWarning downcasting di stderr; hasil identik: True→True,
        # False→False, NaN→False).
        has_h = df["has_h"].eq(True).to_numpy(dtype=bool)
        bom_app = df["bom_app"].to_numpy(dtype="float64")
        com_app = df["com_app"].to_numpy(dtype="float64")
        dev_app = df["dev_app"].to_numpy(dtype="float64")
        gr_app = df["gr_app"].to_numpy(dtype="float64")
        dev_lalu = df["DEV Lalu"].to_numpy(dtype="float64")
        selisih = gr_app - dev_lalu

        # status vektor — PRESEDENSI identik jalur lama: (1) pasangan
        # tak ada → TIDAK ADA DI DATA SAAT INI; (2) H tak ada →
        # H TIDAK ADA DI DATA; (3) toleransi → MATCH / SELISIH.
        status = np.where(
            ~in_app, "TIDAK ADA DI DATA SAAT INI",
            np.where(~has_h, "H TIDAK ADA DI DATA",
                     np.where(np.abs(selisih) <= TOL_ABS + TOL_REL *
                              np.abs(dev_lalu), "MATCH", "SELISIH")))

        df["BOM Saat Ini"] = bom_app
        df["COM Saat Ini"] = com_app
        # v3.9.13 (permintaan user: "Dev to bom itu harusnya persen"):
        # DEV versi app kini RASIO = DEV·Saat Ini / |BOM·Saat Ini| —
        # format persen, konsisten kolom %TO BOM Lalu (dulu kuantitas
        # COM−BOM). BOM 0/NaN → NaN → tampil '—'.
        with np.errstate(divide="ignore", invalid="ignore"):
            df["DEV Saat Ini"] = np.where(
                (bom_app != 0) & ~np.isnan(bom_app),
                dev_app / np.abs(bom_app), np.nan)
        df["GR Saat Ini"] = gr_app
        # NaN otomatis menjalar dari gr_app (baris tanpa nilai app)
        df["Selisih"] = selisih
        df["Status"] = status
        # buang kolom bantu merge (join_df bersih skema lama + kunci norm)
        df = df.drop(columns=["bom_app", "com_app", "dev_app", "gr_app",
                              "has_h"])

        # v3.9.13: join PENUH — SEMUA bulan & minggu (sebelum filter
        # resto/bulan/minggu) — sumber mode 📈 Analisa.
        self._join_df = df.copy()

        # default: sembunyikan resto di luar data saat ini
        # (dipakai mask POSISI fdf — harus sebelum filter bulan/minggu
        # yang me-reset index; merge kiri mempertahankan urutan baris)
        in_app_resto = np.array([r in resto_set for r in
                                 fdf["_resto_norm"].astype(str).values])
        if not st["show_all"]:
            # v3.9.5 (audit 19-c #9): istilah "| Status == H TIDAK ADA"
            # dihapus — status itu hanya diberi SETELAH pasangan ditemukan
            # (resto sudah pasti in_app), jadi tidak pernah menambah baris.
            keep = in_app_resto
            df = df[keep].reset_index(drop=True)
            n_hidden = int((~keep).sum())
        else:
            n_hidden = 0

        # v3.9.13: filter BULAN (default: BULAN TERBARU — per NOMOR bulan;
        # None bila 'Tampilkan semua bulan' / file tanpa bulan terparse)
        target = st.get("month_target")
        if target is not None:
            df = df[df["_bulan_num"] == target].reset_index(drop=True)

        # v3.9.7 (permintaan user "misal H aku input 7 maka hanya tampilkan
        # week 1 aja"): hanya baris minggu yang MEMUAT H yang tampil.
        # v3.9.13: dipindah ke sini (setelah join — join penuh utk analisa
        # tersimpan dulu); minggu di file diambil dari join penuh.
        wt = st.get("week_target")
        if wt is not None:
            weeks_in_file = sorted({str(v) for v in
                                    self._join_df["Minggu"]})
            df = df[df["H"] == wt]
            if df.empty:
                self._result_df = None
                return {"gen": gen, "new_file": new_file, "items": [],
                        "status": (
                            f"0 baris — file tidak punya minggu cut-off "
                            f"H {wt} (minggu di file: "
                            f"{', '.join(weeks_in_file)}). Input H di "
                            f"tab 📦 Deviasi GR (H sekarang "
                            f"{st.get('h_label', wt)} → minggu cut-off "
                            f"{wt}) atau centang 'Tampilkan semua "
                            f"minggu'.")}

        # snapshot utk filter header (SEBELUM filter header)
        self._result_df = df.copy()

        # filter header ⧩ — kecocokan nilai TERFORMAT
        filtered = df
        for col, sel in st["col_sel"].items():
            # v3.9.13: seleksi KOSONG = filter aktif (0 baris — hasil
            # search-to-select Enter; jangan ditelan truthiness)
            if col in filtered.columns and sel is not None:
                fmt = self._format_col_series(col, filtered[col])
                filtered = filtered[fmt.isin(sel)]
        if filtered.empty:
            return {"gen": gen, "new_file": new_file,
                    "items": [], "status":
                    "Tidak ada baris setelah filter."}

        # v3.9.5 (audit 19-a #7): hitungan status diambil SETELAH filter
        # header — footer "174 baris · MATCH: 7" padahal MATCH=0 di baris
        # yang tampil itu menyesatkan.
        m = len(filtered)
        n_match = int((filtered["Status"] == "MATCH").sum())
        n_sel = int((filtered["Status"] == "SELISIH").sum())
        n_noapp = int((filtered["Status"] ==
                       "TIDAK ADA DI DATA SAAT INI").sum())
        n_noh = int((filtered["Status"] == "H TIDAK ADA DI DATA").sum())

        # sort default: Resto, Nama Barang, H
        filtered = filtered.sort_values(
            ["Resto", "Nama Barang", "H"],
            ascending=[True, True, True], kind="stable")

        cols_np = {c: filtered[c].to_numpy() for c in
                   ("Resto", "Nama Barang", "Satuan", "Minggu", "H",
                    "BULAN",
                    "BOM Lalu", "COM Lalu", "DEV Lalu", "%TO BOM Lalu",
                    "BOM Saat Ini", "COM Saat Ini", "DEV Saat Ini",
                    "GR Saat Ini", "Selisih", "Status")}
        items = []
        fp_map = {}
        row_snaps = {}
        neg_cells = []
        st_match_cells = []
        st_diff_cells = []
        st_missing_cells = []
        store = self.store
        for i in range(m):
            resto = str(cols_np["Resto"][i])
            barang = str(cols_np["Nama Barang"][i])
            h = int(cols_np["H"][i])
            status = str(cols_np["Status"][i])
            fmt_vals = {
                "BOM Lalu": self._fmt_num(cols_np["BOM Lalu"][i]),
                "COM Lalu": self._fmt_num(cols_np["COM Lalu"][i]),
                "DEV Lalu": self._fmt_num(cols_np["DEV Lalu"][i]),
                "%TO BOM Lalu": self._fmt_pct(
                    cols_np["%TO BOM Lalu"][i]),
                "BOM Saat Ini": self._fmt_num(
                    cols_np["BOM Saat Ini"][i]),
                "COM Saat Ini": self._fmt_num(
                    cols_np["COM Saat Ini"][i]),
                # v3.9.13: DEV versi app = RASIO (persen)
                "DEV Saat Ini": self._fmt_pct(
                    cols_np["DEV Saat Ini"][i]),
                "GR Saat Ini": self._fmt_num(cols_np["GR Saat Ini"][i]),
                "Selisih": self._fmt_num(cols_np["Selisih"][i]),
            }
            # v3.9.13: kolom Minggu & H TIDAK ditampilkan (permintaan
            # user) — 14 kolom (data internal tetap di snapshot).
            values = ["", resto, barang, str(cols_np["Satuan"][i]),
                      fmt_vals["BOM Lalu"], fmt_vals["COM Lalu"],
                      fmt_vals["DEV Lalu"], fmt_vals["%TO BOM Lalu"],
                      fmt_vals["BOM Saat Ini"], fmt_vals["COM Saat Ini"],
                      fmt_vals["DEV Saat Ini"], fmt_vals["GR Saat Ini"],
                      fmt_vals["Selisih"], status]

            snap = {
                "asal": "KOMPARASI",
                "resto": _norm_resto(resto),
                "barang": barang,
                "satuan": str(cols_np["Satuan"][i]),
                # v3.9.5 (audit 19-b #5): AKTIF/NON utk kolom Follow Up
                "aktif": self._aktif_lookup.get(barang, ""),
                "h": h,
                "so": (None if np.isnan(cols_np["GR Saat Ini"][i])
                       else float(cols_np["GR Saat Ini"][i])),
                "sistem": float(cols_np["DEV Lalu"][i]),
                "deviasi": (None if np.isnan(cols_np["Selisih"][i])
                            else float(cols_np["Selisih"][i])),
                "cek": status,
                "minggu": str(cols_np["Minggu"][i]),
                # v3.9.13: bulan asal baris (multi-file; field snapshot
                # tambahan — TIDAK mengubah fingerprint follow-up).
                "bulan": str(cols_np["BULAN"][i]),
            }
            fp = row_fingerprint(snap)
            checked = store is not None and store.has(fp)
            values[0] = CHECK_ON if checked else CHECK_OFF
            fp_map[f"row_{i}"] = fp
            row_snaps[f"row_{i}"] = snap

            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            # sel status per-cell
            if status == "MATCH":
                st_match_cells.append((f"row_{i}", "Status"))
            elif status == "SELISIH":
                st_diff_cells.append((f"row_{i}", "Status"))
            elif status:
                st_missing_cells.append((f"row_{i}", "Status"))
            # nilai minus per-cell di kolom numerik
            if self._cell_tags:
                for col in self.NUMERIC_COLS:
                    v = cols_np[col][i]
                    if v is not None and not (isinstance(v, float)
                                              and np.isnan(v)) and v < 0:
                        neg_cells.append((f"row_{i}", col))
            else:
                raw_vals = [cols_np[c][i] for c in self.NUMERIC_COLS]
                if any((v is not None and not (isinstance(v, float)
                        and np.isnan(v)) and v < 0) for v in raw_vals):
                    tags.append("negative")

            items.append(("", f"row_{i}",
                          {"values": values, "tags": tuple(tags)}))

        status = (f"{m} baris · MATCH: {n_match} · SELISIH: {n_sel} · "
                  f"H tdk ada: {n_noh} · di luar data saat ini: "
                  f"{n_noapp}")
        # v3.9.13: prefiks bulan aktif (filter bulan-terbaru — multi-file)
        if st.get("month_label") is not None:
            status = f"BULAN {st['month_label']} · {status}"
        # v3.9.7: prefiks minggu aktif (filter minggu sesuai H)
        if st.get("week_target") is not None:
            wlabels = sorted({str(v) for v in filtered["Minggu"]})
            if wlabels:
                status = (f"Minggu {', '.join(wlabels)} (cut-off H "
                          f"{st['week_target']}) · {status}")
        if n_hidden:
            # FIX C-06 (audit 2-c): "(centang utk lihat)" = instruksi
            # cara-pakai → cukup data (opsi ada di kartu Filter).
            status += f" · {n_hidden} resto file disembunyikan"
        if avail_max:
            status += f" · tanggal data s/d {avail_max}"
        return {"gen": gen, "new_file": new_file, "items": items,
                "status": status, "fp_map": fp_map,
                "row_snaps": row_snaps, "pair_index": pair_index,
                "neg_cells": neg_cells,
                "st_match_cells": st_match_cells,
                "st_diff_cells": st_diff_cells,
                "st_missing_cells": st_missing_cells}

    def _render_rows(self, payload: dict):
        try:
            self._render_rows_inner(payload)
        except tk.TclError:
            # v3.9.5: view di-destroy di tengah render (popup/job async
            # menembak setelah widget mati) — pastikan state bersusih.
            self._busy = False
            self._pending = False

    def _render_rows_inner(self, payload: dict):
        if self._insert_cancel is not None:
            # batch insert lama masih berjalan (race) → stop dulu
            self._insert_cancel()
            self._insert_cancel = None
        self.tree.delete(*self.tree.get_children())
        self._update_headings()
        self._fp_map = payload.get("fp_map", {})
        self._row_snaps = payload.get("row_snaps", {})
        # v3.9.5 (audit 19-a #2): simpan pair index utk popup detail
        self._pair_index = payload.get("pair_index", {})
        self._neg_cells = payload.get("neg_cells", [])
        self._st_match_cells = payload.get("st_match_cells", [])
        self._st_diff_cells = payload.get("st_diff_cells", [])
        self._st_missing_cells = payload.get("st_missing_cells", [])
        self.status_var_label.set(payload["status"])

        def render_done():
            self._reapply_cell_tags(self.tree)
            self._busy = False
            if self._pending:
                self._pending = False
                p = self._pending_paths
                self._pending_paths = None
                self._pending_sort = None
                if p:
                    self._load_paths(p)   # file yang antre saat busy
                else:
                    self._refresh()
            elif self._pending_sort:
                # v3.9.5 (audit 19-b #6): sort yang diklik saat render
                # batch berjalan kini diantrekan (dulu dibuang diam-diam)
                col, rev = self._pending_sort
                self._pending_sort = None
                self._sort_by(col, reverse=rev)

        self._insert_cancel = insert_tree_items(
            self.tree, payload["items"], batch=500, on_done=render_done)
        # v3.9.13: mode 📈 Analisa ikut diisi (dari _join_df — join PENUH;
        # tabel analisa tidak menunggu batch insert tabel utama).
        # v3.9.14 (PERF): HANYA saat mode 📈 aktif — dulu dirender juga
        # saat tersembunyi (freeze ±4,8 dtk per refresh di file 40rb
        # baris); mode ⚖ → dirty, dirender saat masuk mode Analisa.
        if self._analisa_mode:
            self._refresh_analisa()
        else:
            self._analisa_dirty = True

    def _reapply_cell_tags(self, tree):
        """v3.9.2 — pasang ulang tag per-cell (sort = delete+reinsert)."""
        if not self._cell_tags:
            return
        if self._neg_cells:
            apply_cell_tag(tree, "neg_cell", self._neg_cells)
        if self._st_match_cells:
            apply_cell_tag(tree, "st_match", self._st_match_cells)
        if self._st_diff_cells:
            apply_cell_tag(tree, "st_diff", self._st_diff_cells)
        if self._st_missing_cells:
            apply_cell_tag(tree, "st_missing", self._st_missing_cells)

    def _reset_filter(self):
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._refresh()

    # =========================================================================
    # v3.9.13 — MODE 📈 ANALISA (Top Selisih + Perubahan Arah)
    # (rumus adopsi repo Inventory-Control user: flip-metrics & top-rank)
    # =========================================================================
    def _build_analisa_ui(self):
        """Bangun semua kartu analisa SEKALI (di-pack hanya saat sub-mode
        📈 Analisa aktif — _on_mode_change).
        v3.9.19: baris BAGIAN (SegmentBar) — 3 bagian (Risiko Flip &
        Benchmark dihapus); hanya frame
        bagian aktif yang di-pack di _anaview (render-malas per
        bagian: data baru → semua bagian stale, dirender saat
        ditampilkan)."""
        self._analisa_frame = tk.Frame(self.content, bg=C_BG)

        # v3.9.19 — baris BAGIAN: pemilih bagian analisa (3 bagian)
        rsec = tk.Frame(self._analisa_frame, bg=C_BG)
        rsec.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(rsec, text="BAGIAN", bg=C_BG, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._anasec_segment = SegmentBar(
            rsec,
            # v3.9.19: Risiko Flip & Benchmark DIHAPUS (permintaan user
            # "hapus tab resiko flip dan bencmark") — 3 bagian tersisa.
            ["📊 Top & Flip", "🧭 Arah Minoritas", "🏆 Liga Deviasi"],
            command=lambda idx: self._on_anasec_change(idx),
            bg=C_BG)
        self._anasec_segment.pack(side="left", padx=(6, 0))
        # wadah bagian — frame per bagian di-pack/di-swap
        # v3.9.15a (audit P2-4): padx 12 — kartu bagian kembali sejajar
        # margin kartu lain (dulu flush x=0 saat kartu pindah parent).
        self._anaview = tk.Frame(self._analisa_frame, bg=C_BG)
        self._anaview.pack(fill="both", expand=True, padx=12)
        self._anasec_frames = [
            tk.Frame(self._anaview, bg=C_BG),
            tk.Frame(self._anaview, bg=C_BG),
            tk.Frame(self._anaview, bg=C_BG),
        ]
        self._anasec_frames[0].pack(fill="both", expand=True)

        # --- Bagian 0 — Kartu 1: Top Selisih ---
        tc = Card(self._anasec_frames[0],
                  title="📈 Top Selisih — |Selisih| Tertinggi")
        tc.pack(fill="both", expand=True, padx=0, pady=(10, 0))
        tb = tc.body()
        head = tk.Frame(tb, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew",
                  pady=(0, 6))
        self._top_status_var = tk.StringVar(value="Belum ada file deviasi.")
        tk.Label(head, textvariable=self._top_status_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9), anchor="w").pack(
            side="left", fill="x", expand=True)
        tk.Label(head, text="TOP N", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left", padx=(10, 0))
        self._topn_var = tk.StringVar(value="100")
        topn_entry = ttk.Entry(head, textvariable=self._topn_var, width=6)
        topn_entry.pack(side="left", padx=(4, 4))
        topn_entry.bind("<Return>", lambda e: self._render_top_selisih())
        GhostButton(head, text="↻ Terapkan",
                    command=self._render_top_selisih).pack(side="left")
        GhostButton(head, text="⛶ Layar Penuh",
                    command=self._maximize_top).pack(side="right")

        cols = [c[0] for c in self.TOP_COLS]
        self._top_tree = ttk.Treeview(tb, columns=cols, show="headings",
                                      selectmode="browse")
        for name, width, anchor in self.TOP_COLS:
            self._top_tree.column(name, width=width, minwidth=34,
                                  anchor=anchor)
            self._top_tree.heading(name, text=name)
        vsb = ttk.Scrollbar(tb, orient="vertical",
                            command=self._top_tree.yview)
        self._top_tree.configure(yscrollcommand=vsb.set)
        self._top_tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        tb.grid_rowconfigure(1, weight=1)
        tb.grid_columnconfigure(0, weight=1)
        enable_col_resize(self._top_tree)
        self._setup_tags(self._top_tree)
        self._top_df = None
        self._top_sel = {c: None for c in cols}
        self._top_neg_cells = []
        self._top_st_match = []
        self._top_st_diff = []
        self._top_st_missing = []
        self._top_ana_cells = {}   # v3.9.19 — warna kolom ANALISA
        self._top_filters = HeaderFilterGroup(
            self._top_tree, cols,
            get_values=self._top_col_values,
            on_apply=self._on_top_filter,
            on_sort=lambda c, d: self._sort_top(c, reverse=d))

        # --- Bagian 0 — Kartu 2: Perubahan Arah (flip) ---
        fc = Card(self._anasec_frames[0],
                  title="📈 Perubahan Arah — Bulan Lalu vs Bulan Saat Ini")
        fc.pack(fill="both", expand=True, padx=0, pady=(10, 0))
        fb = fc.body()
        fhead = tk.Frame(fb, bg=C_CARD)
        fhead.grid(row=0, column=0, columnspan=2, sticky="ew",
                   pady=(0, 6))
        self._flip_summary_var = tk.StringVar(value="")
        tk.Label(fhead, textvariable=self._flip_summary_var, bg=C_CARD,
                 fg=C_HEADER, font=font(9, "bold"), anchor="w").pack(
            side="left", fill="x", expand=True)
        self._flip_status_var = tk.StringVar(value="")
        tk.Label(fhead, textvariable=self._flip_status_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9), anchor="w").pack(
            side="left", padx=(10, 0))
        GhostButton(fhead, text="⛶ Layar Penuh",
                    command=self._maximize_flip).pack(side="right")

        cols = [c[0] for c in self.FLIP_COLS]
        self._flip_tree = ttk.Treeview(fb, columns=cols, show="headings",
                                       selectmode="browse")
        for name, width, anchor in self.FLIP_COLS:
            self._flip_tree.column(name, width=width, minwidth=34,
                                   anchor=anchor)
            self._flip_tree.heading(name, text=name)
        fvsb = ttk.Scrollbar(fb, orient="vertical",
                             command=self._flip_tree.yview)
        self._flip_tree.configure(yscrollcommand=fvsb.set)
        self._flip_tree.grid(row=1, column=0, sticky="nsew")
        fvsb.grid(row=1, column=1, sticky="ns")
        fb.grid_rowconfigure(1, weight=1)
        fb.grid_columnconfigure(0, weight=1)
        enable_col_resize(self._flip_tree)
        self._setup_flip_tags(self._flip_tree)
        self._flip_df = None
        self._flip_sel = {c: None for c in cols}
        self._flip_neg_cells = []
        self._flip_kat_cells = {"Sempurna": [], "Dominan": [],
                                "Parsial": []}
        self._flip_ana_cells = {}   # v3.9.19 — warna kolom ANALISA
        self._flip_filters = HeaderFilterGroup(
            self._flip_tree, cols,
            get_values=self._flip_col_values,
            on_apply=self._on_flip_filter,
            on_sort=lambda c, d: self._sort_flip(c, reverse=d))

        # v3.9.19 — bangun 2 bagian analisa tersisa (Risiko Flip &
        # Benchmark dihapus).
        self._build_min_ui()
        self._build_liga_ui()

    def _setup_flip_tags(self, tree):
        """Tag tabel flip — dasar + warna kategori per-cell."""
        self._setup_tags(tree)
        tree.tag_configure("flip_sempurna", foreground="#dc2626")
        tree.tag_configure("flip_dominan", foreground=C_AMBER)
        tree.tag_configure("flip_parsial", foreground=C_ACCENT)

    def _on_mode_change(self, idx: int):
        """v3.9.13: ganti sub-mode kartu filter — ⚖ Tabel / 📈 Analisa
        (dipakai SegmentBar & test).
        v3.9.14 (PERF): masuk mode 📈 → render hanya bila dirty (data/
        join/file baru sejak render terakhir) — toggle bolak-balik tanpa
        perubahan data tidak me-render ulang."""
        self._analisa_mode = idx == 1
        if self._analisa_mode:
            self.tcard.pack_forget()
            self._analisa_frame.pack(fill="both", expand=True)
            if self._analisa_dirty:
                self._refresh_analisa()
        else:
            self._analisa_frame.pack_forget()
            self.tcard.pack(fill="both", expand=True, padx=12,
                            pady=(10, 0))

    def _refresh_analisa(self):
        """Hitung & render tabel analisa — dari _join_df (join PENUH
        semua bulan/minggu) & _file_df (flip butuh nilai DEV per bulan;
        tidak terpotong filter tampilan tabel utama).
        v3.9.14: kedua tabel kini difilter MINGGU yang memuat H (aturan
        kolom H — H=7 → WEEK 1) + dirty di-reset di sini.
        v3.9.15: hanya BAGIAN AKTIF yang dirender (semua bagian
        ditandai stale — dirender saat ditampilkan — pola malas).
        """
        self._analisa_dirty = False
        self._anasec_stale = {0, 1, 2}
        self._render_analisa_section(self._anasec_idx)

    # -- Top Selisih -------------------------------------------------------
    def _top_col_values(self, col: str) -> list:
        d = self._filtered_analisa_df(self._top_df, self._top_sel, col)
        if d is None or d.empty or col not in d.columns:
            return []
        return self._fmt_analisa_series(col, d[col]).unique().tolist()

    @staticmethod
    def _filtered_analisa_df(d, sel_map: dict, col: str):
        """v3.9.19 — baris tabel analisa yang TAMPIL SAAT INI (filter
        kolom LAIN diterapkan; kolom `col` sendiri dikecualikan —
        perilaku AutoFilter Excel; permintaan user: "isi filter harus
        menampilkan data yang ada aja")."""
        if d is None or d.empty:
            return d
        f = d
        for c, sel in sel_map.items():
            if sel is None or c == col or c not in f.columns:
                continue
            fmt = KomparasiDeviasiView._fmt_analisa_series(c, f[c])
            f = f[fmt.isin(sel)]
        return f

    def _on_top_filter(self, col: str, selected):
        self._top_sel[col] = selected
        self._render_top_selisih()

    def _sort_top(self, col: str, reverse: bool = True, tree=None):
        tree = tree if tree is not None else self._top_tree
        parse = (self._parse_num_id if col in
                 ("DEV Lalu", "GR Saat Ini", "Selisih", "Peringkat")
                 else None)
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_top_tags(tree)

    def _reapply_top_tags(self, tree):
        if not self._cell_tags:
            return
        if self._top_neg_cells:
            apply_cell_tag(tree, "neg_cell", self._top_neg_cells)
        if self._top_st_match:
            apply_cell_tag(tree, "st_match", self._top_st_match)
        if self._top_st_diff:
            apply_cell_tag(tree, "st_diff", self._top_st_diff)
        if self._top_st_missing:
            apply_cell_tag(tree, "st_missing", self._top_st_missing)
        self._reapply_ana_tags(tree, self._top_ana_cells)   # v3.9.19

    def _ana_empty_cells(self) -> dict:
        """v3.9.19 — wadah sel ANALISA per label (Top Selisih & Flip)."""
        return {
            self.ANALISA_NAIK: [],
            self.ANALISA_TURUN: [],
            self.ANALISA_STABIL: [],
            self.ANALISA_ARAH: [],
            self.ANALISA_FFLOP: [],
        }

    def _reapply_ana_tags(self, tree, cells: dict):
        """v3.9.19 — pasang ulang warna per-cell kolom ANALISA (juga utk
        clone ⛶ — pola FIX B-03/B-12)."""
        if not self._cell_tags:
            return
        for label, tag in ((self.ANALISA_NAIK, "ana_naik"),
                           (self.ANALISA_TURUN, "ana_turun"),
                           (self.ANALISA_STABIL, "ana_stabil"),
                           (self.ANALISA_ARAH, "ana_arah"),
                           (self.ANALISA_FFLOP, "ana_fflop")):
            cl = cells.get(label) or []
            if cl:
                apply_cell_tag(tree, tag, cl)

    def _top_aggregate(self, d: pd.DataFrame) -> pd.DataFrame:
        """v3.9.16 — agregat join → SATU baris per pasangan (resto ×
        bahan × minggu sama) utk tabel Top Selisih (khusus mode 📈
        Analisa — permintaan user):
        - DEV Lalu = MEDIAN antar-file/bulan (1 file → nilai itu
          sendiri; ≥2 file → median — "nilai deviasi pakai median aja,
          jangan semua file"); minggu tetap kunci grup (aturan minggu
          sama antar bulan);
        - Selisih = |GR Saat Ini| − |DEV Lalu| — kedua nilai
          DIABSOLUTKAN dulu (pembalikan tanda tidak menggembungkan
          selisih); kolom DEV Lalu / GR Saat Ini tetap NILAI ASLI;
        - Status: pasangan tak ada di data app → status join lama
          (TIDAK ADA DI DATA SAAT INI / H TIDAK ADA DI DATA — konstanta
          per grup: sisi app digabung per resto × bahan × H); ada →
          MATCH/SELISIH atas Selisih absolut (toleransi sama);
        - Periode: 'Median n file · Minggu' (≥2 nilai) / 'BULAN ·
          Minggu' (1 nilai — format lama) — kolom NYATA (filter header
          Periode kini bekerja).
        - v3.9.19 ANALISA (1 kolom keterangan): Kenaikan Tertinggi ·
          Penurunan Tertinggi · Stabil · Berubah Arah · Potensi Flip
          Flop — prioritas: tanda berlawanan (disparitas = |P1+P2|/
          max(|P1|,|P2|) — ambang sama dgn Kategori flip: < 40% →
          Berubah Arah, ≥ 40% → Potensi Flip Flop) → Stabil (|Selisih|
          ≤ toleransi MATCH) → Kenaikan/Penurunan Tertinggi (arah
          Selisih). Pasangan tanpa data app → '—'.
        VEKTOR penuh (groupby + numpy, tanpa iterrows — pola PERF
        v3.9.14)."""
        g = d.groupby(["_resto_norm", "_bahan_norm", "Minggu"],
                      sort=False)
        agg = g.agg(
            dev=("DEV Lalu", "median"),
            n=("DEV Lalu", "count"),
            gr=("GR Saat Ini", "first"),
            st=("Status", "first"),
            bln=("BULAN", "first"),
            resto=("Resto", "first"),
            bahan=("Nama Barang", "first"),
            sat=("Satuan", "first"),
        ).reset_index()
        gr = agg["gr"].to_numpy(dtype="float64")
        dev = agg["dev"].to_numpy(dtype="float64")
        # v3.9.16: absolut DULU — tanda berlawanan tidak menggembungkan
        # selisih (kolom DEV Lalu / GR Saat Ini tetap nilai ASLI)
        sel = np.abs(gr) - np.abs(dev)
        tol = TOL_ABS + TOL_REL * np.abs(dev)
        st0 = agg["st"].astype(str).to_numpy()
        status = np.where(
            np.isnan(gr), st0,
            np.where(np.abs(sel) <= tol, "MATCH", "SELISIH"))
        n = agg["n"].to_numpy(dtype="int64")
        bln = agg["bln"].astype(str).to_numpy()
        mg = agg["Minggu"].astype(str).to_numpy()
        # label periode: pasangan ada di >1 bulan/file → nilai median
        # (file didedup per bulan — jumlah nilai = jumlah file)
        periode = [f"Median {int(c)} file · {m}" if c > 1
                   else f"{b} · {m}"
                   for c, b, m in zip(n, bln, mg)]
        # v3.9.19 — keterangan ANALISA per pasangan (VEKTOR):
        # tanda berlawanan → disparitas (rumus flip) dgn ambang 40%
        # (sama dgn Kategori Sempurna/Dominan vs Parsial) →
        # Berubah Arah / Potensi Flip Flop; tanda sama → Stabil bila
        # Selisih dalam toleransi MATCH, selain itu arah Selisih →
        # Kenaikan / Penurunan Tertinggi; tanpa data app → '—'.
        with np.errstate(divide="ignore", invalid="ignore"):
            disp = (np.abs(dev + gr)
                    / np.maximum(np.abs(dev), np.abs(gr)))
        sign_flip = (dev * gr) < 0.0
        ana = np.where(
            np.isnan(gr), "—",
            np.where(
                sign_flip,
                np.where(disp >= 0.40, self.ANALISA_FFLOP,
                         self.ANALISA_ARAH),
                np.where(
                    np.abs(sel) <= tol, self.ANALISA_STABIL,
                    np.where(sel > 0, self.ANALISA_NAIK,
                             self.ANALISA_TURUN))))
        return pd.DataFrame({
            "Periode": periode,
            "Resto": agg["resto"].to_numpy(),
            "Nama Barang": agg["bahan"].to_numpy(),
            "Satuan": agg["sat"].to_numpy(),
            "DEV Lalu": dev,
            "GR Saat Ini": gr,
            "Selisih": sel,
            "Status": status,
            "ANALISA": ana,   # v3.9.19
        })

    def _render_top_selisih(self):
        """Top-N |Selisih| TERTINGGI — dari join PENUH, kini DIFILTER
        MINGGU yang memuat H (v3.9.14 — aturan kolom H: H=7 → hanya
        WEEK 1; "Tampilkan semua minggu" = semua minggu). N = 0 → semua.
        v3.9.14 (PERF): tanpa copy penuh + tanpa iterrows (argsort numpy
        + kolom to_numpy).
        v3.9.16 (permintaan user, khusus mode 📈 Analisa): (1) DEV Lalu
        & GR Saat Ini DIABSOLUTKAN dulu saat menghitung Selisih —
        pembalikan tanda (mis. −50 → +30) tidak lagi menggembungkan
        selisih (dulu 80, kini 20); kolom DEV Lalu / GR Saat Ini tetap
        menampilkan NILAI ASLI (bukan absolut). (2) Bila file deviasi
        >1: nilai Lalu = MEDIAN antar-file per pasangan (resto × bahan
        × minggu sama) — SATU baris per pasangan; yang ditampilkan
        nilai median saja, bukan semua file (lihat _top_aggregate)."""
        tree = self._top_tree
        tree.delete(*tree.get_children())
        j = self._join_df
        if j is None or j.empty:
            self._top_df = None
            self._top_status_var.set("Belum ada file deviasi.")
            return
        d = j
        # v3.9.14: minggu cut-off H — konsisten dgn tabel utama
        wt = (None if self._show_all_weeks.get()
              else _h_to_week_target(int(self.tanggal_h)))
        prefix = ""
        if wt is not None:
            weeks_all = sorted({str(v) for v in j["Minggu"]})
            d = d[d["H"] == wt]
            if d.empty:
                self._top_df = None
                self._top_status_var.set(
                    f"0 baris — file tidak punya minggu cut-off H {wt} "
                    f"(minggu di file: {', '.join(weeks_all)}).")
                return
            wlab = ", ".join(sorted({str(v) for v in d["Minggu"]}))
            prefix = f"Minggu {wlab} (H {wt}) · "
        # v3.9.16: agregat per pasangan — DEV Lalu = median antar-file,
        # Selisih = |GR Saat Ini| − |DEV Lalu| (absolut dulu)
        d = self._top_aggregate(d)
        multi = bool(d["Periode"].astype(str)
                     .str.startswith("Median").any())
        # urut |Selisih| menurun — numpy argsort (tanpa kolom _abs)
        _abs = (pd.to_numeric(d["Selisih"], errors="coerce")
                .fillna(0).abs().to_numpy())
        d = d.iloc[np.argsort(-_abs, kind="stable")]
        try:
            n = int(float(self._topn_var.get() or 0))
        except (TypeError, ValueError):
            n = 100
        if n > 0:
            d = d.head(n)
        self._top_df = d
        # filter header ⧩ — kecocokan nilai TERFORMAT (seleksi kosong =
        # 0 baris — v3.9.13 search-to-select)
        for col, sel in self._top_sel.items():
            if d.empty:
                break
            if col in d.columns and sel is not None:
                fmt = self._fmt_analisa_series(col, d[col])
                d = d[fmt.isin(sel)]
        if d.empty:
            self._top_status_var.set("0 baris setelah filter.")
            return
        m = len(d)
        # v3.9.16: catatan median bila Lalu digabung antar >1 file
        self._top_status_var.set(
            f"{prefix}{m} baris · Top {'semua' if n <= 0 else n}"
            + (" · Lalu = median antar-file" if multi else ""))
        # v3.9.14 (PERF): values dari kolom numpy (dulu iterrows —
        # Series per baris)
        cols_np = {c: d[c].to_numpy() for c in
                   ("Periode", "Resto", "Nama Barang", "Satuan",
                    "DEV Lalu", "GR Saat Ini", "Selisih", "Status",
                    "ANALISA")}
        items = []
        neg_cells = []
        st_match = []
        st_diff = []
        st_missing = []
        ana_cells = self._ana_empty_cells()   # v3.9.19 — warna ANALISA
        for i in range(m):
            iid = f"top_{i}"
            values = [str(i + 1),
                      str(cols_np["Periode"][i]),
                      str(cols_np["Resto"][i]),
                      str(cols_np["Nama Barang"][i]),
                      str(cols_np["Satuan"][i]),
                      self._fmt_num(cols_np["DEV Lalu"][i]),
                      self._fmt_num(cols_np["GR Saat Ini"][i]),
                      self._fmt_num(cols_np["Selisih"][i]),
                      str(cols_np["Status"][i]),
                      str(cols_np["ANALISA"][i])]   # v3.9.19
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            for col in ("DEV Lalu", "GR Saat Ini", "Selisih"):
                v = cols_np[col][i]
                if v is not None and not (isinstance(v, float)
                                          and np.isnan(v)) and v < 0:
                    neg_cells.append((iid, col))
            stv = str(cols_np["Status"][i])
            if stv == "MATCH":
                st_match.append((iid, "Status"))
            elif stv == "SELISIH":
                st_diff.append((iid, "Status"))
            elif stv:
                st_missing.append((iid, "Status"))
            # v3.9.19: warna per-cell keterangan ANALISA
            av = str(cols_np["ANALISA"][i])
            if av in ana_cells:
                ana_cells[av].append((iid, "ANALISA"))
            items.append(("", iid, {"values": values,
                                    "tags": tuple(tags)}))
        self._top_neg_cells = neg_cells
        self._top_st_match = st_match
        self._top_st_diff = st_diff
        self._top_st_missing = st_missing
        self._top_ana_cells = ana_cells   # v3.9.19
        self._anasec_insert(
            tree, items, on_done=lambda: self._reapply_top_tags(tree))

    # -- Perubahan Arah (flip) ----------------------------------------------
    def _flip_col_values(self, col: str) -> list:
        d = self._filtered_analisa_df(self._flip_df, self._flip_sel, col)
        if d is None or d.empty or col not in d.columns:
            return []
        return self._fmt_analisa_series(col, d[col]).unique().tolist()

    def _on_flip_filter(self, col: str, selected):
        self._flip_sel[col] = selected
        self._render_flip()

    def _sort_flip(self, col: str, reverse: bool = True, tree=None):
        tree = tree if tree is not None else self._flip_tree
        parse = (self._parse_num_id if col in ("DEV Bulan Lalu",
                                              "DEV Saat Ini", "Δ",
                                              "Disparitas") else None)
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_flip_tags(tree)

    def _reapply_flip_tags(self, tree):
        if not self._cell_tags:
            return
        if self._flip_neg_cells:
            apply_cell_tag(tree, "neg_cell", self._flip_neg_cells)
        for kat, tag in (("Sempurna", "flip_sempurna"),
                         ("Dominan", "flip_dominan"),
                         ("Parsial", "flip_parsial")):
            cells = self._flip_kat_cells.get(kat) or []
            if cells:
                apply_cell_tag(tree, tag, cells)
        self._reapply_ana_tags(tree, self._flip_ana_cells)   # v3.9.19

    def _flip_pair_core(self):
        """v3.9.15 — inti VEKTOR komputasi pasangan bulan-berurutan
        minggu-sama (v3.9.14); dipakai _render_flip (event flip;
        dulu juga _render_risk — bagian itu dihapus v3.9.19):
        satu sumber kebenaran pasangan — sort (resto, bahan, minggu,
        bulan) sekali + shift(-1) dalam grup.

        Return dict:
            ok=False → reason "no_file" | "no_bulan" | "no_week"
                        (+ "weeks_all" utk pesan no_week)
            ok=True  → d (ter-sort; kolom _dev_next/_bnum_next/_blbl_next
                        + kolom tampil per grup), msk (mask FLIP — tanda
                        DEV berlawanan), pm (mask SEMUA pasangan bulan
                        berurutan — flip + konsisten), prefix (label
                        minggu utk status).
        """
        fdf = self._file_df
        if fdf is None or fdf.empty:
            return {"ok": False, "reason": "no_file"}
        d = fdf.copy()
        d["DEV Lalu"] = pd.to_numeric(d["DEV Lalu"],
                                      errors="coerce").fillna(0.0)
        d = d[d["BULAN"].astype(str) != ""]
        if d.empty:
            return {"ok": False, "reason": "no_bulan"}
        # v3.9.14: minggu cut-off H (H=7 → hanya pasangan WEEK 1)
        wt = (None if self._show_all_weeks.get()
              else _h_to_week_target(int(self.tanggal_h)))
        prefix = ""
        if wt is not None:
            weeks_all = sorted({str(v) for v in fdf["Minggu"]})
            d = d[d["_h"] == wt]
            if d.empty:
                return {"ok": False, "reason": "no_week",
                        "weeks_all": weeks_all}
            wlab = ", ".join(sorted({str(v) for v in d["Minggu"]}))
            prefix = f"Minggu {wlab} (H {wt}) · "
        # --- VEKTOR: urut (grup, bulan) → pasangan via shift(-1) -------
        d = d.sort_values(["_resto_norm", "_bahan_norm", "Minggu",
                           "_bulan_num"], kind="stable")
        g = d.groupby(["_resto_norm", "_bahan_norm", "Minggu"], sort=False)
        d["_dev_next"] = g["DEV Lalu"].shift(-1)
        d["_bnum_next"] = g["_bulan_num"].shift(-1)
        d["_blbl_next"] = g["BULAN"].shift(-1)
        # nilai tampil per grup = baris PERTAMA grup (perilaku lama
        # sub[...].iloc[0])
        d["_resto_d"] = g["Resto"].transform("first")
        d["_barang_d"] = g["Nama Barang"].transform("first")
        d["_satuan_d"] = g["Satuan"].transform("first")
        msk = (d["_dev_next"].notna()
               & (d["DEV Lalu"] != 0) & (d["_dev_next"] != 0)
               & ((d["DEV Lalu"] > 0) != (d["_dev_next"] > 0))
               & (d["_bulan_num"] != d["_bnum_next"]))
        # v3.9.15: SEMUA pasangan bulan berurutan (flip ATAU konsisten) —
        # pm = pasangan bulan berurutan semuanya (dulu dasar agregat
        # Risiko Flip — bagian dihapus v3.9.19; msk ⊂ pm).
        pm = (d["_bnum_next"].notna()
              & (d["_bulan_num"] != d["_bnum_next"]))
        return {"ok": True, "d": d, "msk": msk, "pm": pm, "prefix": prefix}

    def _render_flip(self):
        """Perubahan arah (v3.9.13 — rumus flip repo Inventory-Control
        user): pasangan bulan BERURUTAN pada MINGGU SAMA per (resto ×
        barang) dengan tanda DEV berlawanan (minus bulan lalu → surplus
        sekarang / sebaliknya). Disparitas = |P1+P2|/max(|P1|,|P2|):
        Sempurna <10% (pembalikan penuh — patut dicek manual), Dominan
        10–40%, Parsial ≥40%. Default urut disparitas NAIK.

        v3.9.14: (PERF) komputasi VEKTOR — sort sekali lalu pasangan
        berurutan via shift(-1) dalam grup (dulu groupby + sort_values
        PER GRUP + zip per baris = 4,7 dtk di file 40rb baris; vektor =
        ±50ms — pasangan/urutan identik); (MINGGU) hanya pasangan pada
        minggu yang MEMUAT H (aturan kolom H — H=7 → WEEK 1).
        v3.9.19: kolom ANALISA (1 keterangan) — Berubah Arah (Sempurna/
        Dominan, disparitas < 40%) vs Potensi Flip Flop (Parsial,
        disparitas ≥ 40%)."""
        tree = self._flip_tree
        tree.delete(*tree.get_children())
        # v3.9.15: inti komputasi pasangan diekstrak ke _flip_pair_core
        # (satu sumber kebenaran; pesan
        # status & hasil IDENTIK v3.9.14).
        res = self._flip_pair_core()
        if not res["ok"]:
            self._flip_df = None
            self._flip_summary_var.set("")
            if res["reason"] == "no_bulan":
                self._flip_status_var.set(
                    "File tanpa kolom BULAN — muat ≥2 bulan (file bulan lalu "
                    "+ sekarang) utk analisa perubahan arah.")
            elif res["reason"] == "no_week":
                wt = _h_to_week_target(int(self.tanggal_h))
                self._flip_status_var.set(
                    f"File tidak punya minggu cut-off H {wt} (minggu di "
                    f"file: {', '.join(res.get('weeks_all') or [])}).")
            else:
                self._flip_status_var.set("Belum ada file deviasi.")
            return
        d, msk, prefix = res["d"], res["msk"], res["prefix"]
        if not bool(msk.any()):
            self._flip_df = None
            self._flip_summary_var.set("")
            self._flip_status_var.set(
                "Tidak ada perubahan arah terdeteksi — butuh ≥2 bulan pada "
                "minggu sama dgn tanda DEV berlawanan.")
            return
        md = d.loc[msk]
        p1 = md["DEV Lalu"].to_numpy(dtype=float)
        p2 = md["_dev_next"].to_numpy(dtype=float)
        disp = np.abs(p1 + p2) / np.maximum(np.abs(p1), np.abs(p2))
        kat = np.select([disp < 0.10, disp < 0.40],
                        ["Sempurna", "Dominan"], default="Parsial")
        # v3.9.19 — keterangan ANALISA (1 kolom saja): semua baris flip
        # = perubahan arah; pembalikan PARSIAL (disparitas ≥ 40% —
        # sisi dominan besar) rawan berbalik lagi → Potensi Flip Flop.
        ana = np.where(disp >= 0.40, self.ANALISA_FFLOP,
                       self.ANALISA_ARAH)
        fd = pd.DataFrame({
            "Periode": [
                f"{_BULAN_NAME.get(int(n1), str(b1))} {mg} → "
                f"{_BULAN_NAME.get(int(n2), str(b2))} {mg}"
                for n1, b1, n2, b2, mg in zip(
                    md["_bulan_num"], md["BULAN"],
                    md["_bnum_next"], md["_blbl_next"], md["Minggu"])],
            "Resto": md["_resto_d"].to_numpy(),
            "Nama Barang": md["_barang_d"].to_numpy(),
            "Satuan": md["_satuan_d"].to_numpy(),
            "DEV Bulan Lalu": p1,
            "DEV Saat Ini": p2,
            "Δ": p2 - p1,
            "Disparitas": disp,
            "Kategori": kat,
            "ANALISA": ana,   # v3.9.19
        })
        fd = fd.sort_values("Disparitas", ascending=True, kind="stable")
        self._flip_df = fd
        # filter header ⧩ (seleksi kosong = 0 baris — v3.9.13)
        for col, sel in self._flip_sel.items():
            if fd.empty:
                break
            if col in fd.columns and sel is not None:
                fmt = self._fmt_analisa_series(col, fd[col])
                fd = fd[fmt.isin(sel)]
        if fd.empty:
            self._flip_summary_var.set("")
            self._flip_status_var.set("0 baris setelah filter.")
            return
        m = len(fd)
        n_s = int((fd["Kategori"] == "Sempurna").sum())
        n_d = int((fd["Kategori"] == "Dominan").sum())
        n_p = int((fd["Kategori"] == "Parsial").sum())
        self._flip_summary_var.set(
            f"{prefix}{m} FLIP · {n_s} Sempurna · {n_d} Dominan · "
            f"{n_p} Parsial")
        self._flip_status_var.set(
            f"{m} baris · urut disparitas (pembalikan terbaik dulu)")
        # v3.9.14 (PERF): values dari kolom numpy (dulu iterrows)
        cols_np = {c: fd[c].to_numpy() for c in
                   ("Periode", "Resto", "Nama Barang", "Satuan",
                    "DEV Bulan Lalu", "DEV Saat Ini", "Δ", "Disparitas",
                    "Kategori", "ANALISA")}
        items = []
        neg_cells = []
        kat_cells = {"Sempurna": [], "Dominan": [], "Parsial": []}
        ana_cells = self._ana_empty_cells()   # v3.9.19
        for i in range(m):
            iid = f"flip_{i}"
            values = [str(cols_np["Periode"][i]),
                      str(cols_np["Resto"][i]),
                      str(cols_np["Nama Barang"][i]),
                      str(cols_np["Satuan"][i]),
                      self._fmt_num(cols_np["DEV Bulan Lalu"][i]),
                      self._fmt_num(cols_np["DEV Saat Ini"][i]),
                      self._fmt_num(cols_np["Δ"][i]),
                      self._fmt_pct(cols_np["Disparitas"][i]),
                      str(cols_np["Kategori"][i]),
                      str(cols_np["ANALISA"][i])]   # v3.9.19
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            kv = str(cols_np["Kategori"][i])
            if kv in kat_cells:
                kat_cells[kv].append((iid, "Kategori"))
            av = str(cols_np["ANALISA"][i])   # v3.9.19
            if av in ana_cells:
                ana_cells[av].append((iid, "ANALISA"))
            for col in ("DEV Bulan Lalu", "DEV Saat Ini", "Δ"):
                v = cols_np[col][i]
                if v is not None and not (isinstance(v, float)
                                          and np.isnan(v)) and v < 0:
                    neg_cells.append((iid, col))
            items.append(("", iid, {"values": values,
                                    "tags": tuple(tags)}))
        self._flip_neg_cells = neg_cells
        self._flip_kat_cells = kat_cells
        self._flip_ana_cells = ana_cells   # v3.9.19
        self._anasec_insert(
            tree, items, on_done=lambda: self._reapply_flip_tags(tree))


    # =========================================================================
    # v3.9.15 — GELOMBANG 1: BAGIAN ANALISA TAMBAHAN
    # (🧭 Arah Minoritas · 🏆 Liga Deviasi — bagian ⚡ Risiko Flip & 💰
    # Benchmark DIHAPUS v3.9.19; Top & Flip dibangun di atas)
    # Semua komputasi VEKTOR (pola PERF v3.9.14 — tanpa iterrows); hanya
    # bagian AKTIF yang dirender (render-malas per bagian).
    # =========================================================================

    # -- Bangun UI bagian ----------------------------------------------------
    def _build_min_ui(self):
        """Bagian 2 — 🧭 Arah Minoritas per Bahan (resto yang melawan
        mayoritas — pola item-anomali-outlets repo)."""
        mc = Card(self._anasec_frames[1],
                  title="🧭 Arah Minoritas per Bahan — resto melawan "
                        "mayoritas")
        mc.pack(fill="both", expand=True, padx=0, pady=(10, 0))
        mb = mc.body()
        mhead = tk.Frame(mb, bg=C_CARD)
        mhead.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._min_status_var = tk.StringVar(value="Belum ada file deviasi.")
        tk.Label(mhead, textvariable=self._min_status_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9), anchor="w").pack(
            side="left", fill="x", expand=True)
        cols = [c[0] for c in self.MIN_COLS]
        self._min_tree = ttk.Treeview(mb, columns=cols, show="headings",
                                      selectmode="browse")
        for name, width, anchor in self.MIN_COLS:
            self._min_tree.column(name, width=width, minwidth=34,
                                  anchor=anchor)
            self._min_tree.heading(name, text=name)
        vsb = ttk.Scrollbar(mb, orient="vertical",
                            command=self._min_tree.yview)
        self._min_tree.configure(yscrollcommand=vsb.set)
        self._min_tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        mb.grid_rowconfigure(1, weight=1)
        mb.grid_columnconfigure(0, weight=1)
        enable_col_resize(self._min_tree)
        self._setup_tags(self._min_tree)
        self._min_tree.tag_configure("min_minus", foreground="#dc2626")
        self._min_tree.tag_configure("min_surplus", foreground="#15803d")
        self._min_df = None
        self._min_scope_df = None
        self._min_maj_sign = None
        self._min_bahan_map = {}
        self._min_sel = {c: None for c in cols}
        self._min_arah_cells = {"MINUS": [], "SURPLUS": []}
        self._min_filters = HeaderFilterGroup(
            self._min_tree, cols,
            get_values=self._min_col_values,
            on_apply=self._on_min_filter,
            on_sort=lambda c, d: self._sort_min(c, reverse=d))
        mfoot = tk.Frame(mb, bg=C_CARD)
        mfoot.grid(row=2, column=0, columnspan=2, sticky="ew")
        tk.Label(
            mfoot,
            text="Mayoritas ketat (mayoritas > minoritas) · bulan terbaru "
                 "+ satu minggu snapshot",
            bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(side="left")
        self._min_tree.bind("<Double-1>", self._on_min_double_click,
                            add="+")

    def _build_liga_ui(self):
        """Bagian 3 — 🏆 Liga Deviasi-Rate per Bahan (|DEV|/|BOM| vs
        median + MAD populasi — pola waste-rate-league repo)."""
        lc = Card(self._anasec_frames[2],
                  title="🏆 Liga Deviasi-Rate per Bahan — |DEV| / |BOM| "
                        "vs median populasi resto")
        lc.pack(fill="both", expand=True, padx=0, pady=(10, 0))
        lb = lc.body()
        lhead = tk.Frame(lb, bg=C_CARD)
        lhead.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._liga_status_var = tk.StringVar(value="Belum ada file deviasi.")
        tk.Label(lhead, textvariable=self._liga_status_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9), anchor="w").pack(
            side="left", fill="x", expand=True)
        tk.Label(lhead, text="BAHAN", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left", padx=(10, 0))
        self._liga_bahan_var = tk.StringVar(value="")
        self._liga_combo = ttk.Combobox(
            lhead, textvariable=self._liga_bahan_var, state="readonly",
            width=32)
        self._liga_combo.pack(side="left", padx=(4, 0))
        self._liga_combo.bind("<<ComboboxSelected>>",
                              self._on_liga_bahan_changed)
        # baris kedua: baseline populasi (metode — jujur)
        lbase = tk.Frame(lb, bg=C_CARD)
        lbase.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._liga_base_var = tk.StringVar(value="")
        tk.Label(lbase, textvariable=self._liga_base_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(8), anchor="w",
                 wraplength=860, justify="left").pack(
            side="left", fill="x", expand=True)
        cols = [c[0] for c in self.LIGA_COLS]
        self._liga_tree = ttk.Treeview(lb, columns=cols, show="headings",
                                       selectmode="browse")
        for name, width, anchor in self.LIGA_COLS:
            self._liga_tree.column(name, width=width, minwidth=34,
                                   anchor=anchor)
            self._liga_tree.heading(name, text=name)
        vsb = ttk.Scrollbar(lb, orient="vertical",
                            command=self._liga_tree.yview)
        self._liga_tree.configure(yscrollcommand=vsb.set)
        self._liga_tree.grid(row=2, column=0, sticky="nsew")
        vsb.grid(row=2, column=1, sticky="ns")
        lb.grid_rowconfigure(2, weight=1)
        lb.grid_columnconfigure(0, weight=1)
        enable_col_resize(self._liga_tree)
        self._setup_tags(self._liga_tree)
        # zTone (pola repo): z > 2 merah · z > 1 amber
        self._liga_tree.tag_configure("z_high", foreground="#dc2626")
        self._liga_tree.tag_configure("z_warn", foreground=C_AMBER)
        self._liga_df = None
        self._liga_stats = {}
        self._liga_bahan_norm = None
        self._liga_sel = {c: None for c in cols}
        self._liga_z_cells = {"high": [], "warn": []}
        self._liga_neg_cells = []
        self._liga_filters = HeaderFilterGroup(
            self._liga_tree, cols,
            get_values=self._liga_col_values,
            on_apply=self._on_liga_filter,
            on_sort=lambda c, d: self._sort_liga(c, reverse=d))

    # -- Pergantian bagian ---------------------------------------------------
    def _on_anasec_change(self, idx: int):
        """v3.9.15: ganti bagian analisa (SegmentBar BAGIAN) — tampilkan
        frame bagian; bila bagian belum dirender dengan data sekarang
        (stale) → render sekarang (render-malas per bagian: data baru
        menandai SEMUA bagian stale; hanya bagian aktif dihitung)."""
        self._anasec_idx = idx
        for i, fr in enumerate(self._anasec_frames):
            if i == idx:
                fr.pack(fill="both", expand=True)
            else:
                fr.pack_forget()
        if idx in self._anasec_stale:
            self._render_analisa_section(idx)

    def _anasec_insert(self, tree, items, on_done):
        """v3.9.15a (audit P1-2): insert batch utk tabel analisa + simpan
        handle cancel per tabel — render ulang tabel YANG SAMA
        membatalkan sisa batch lama dulu (tanpa ini, re-render yang
        menembak di tengah jendela 10ms antar-batch meninggalkan baris
        basi dari render sebelumnya; tabel utama sudah ber-guard sejak
        v3.9.5 — kini keenam tabel analisa juga)."""
        cancel = self._anasec_cancel.get(tree)
        if cancel is not None:
            cancel()
        self._anasec_cancel[tree] = insert_tree_items(
            tree, items, batch=400, on_done=on_done)

    def _render_analisa_section(self, idx: int):
        """Render SATU bagian analisa. Tiap render menghitung ulang dari
        _file_df/_join_df (semua vektor ±10-60ms — stateless: tidak ada
        state basi antar bagian)."""
        self._anasec_stale.discard(idx)
        # v3.9.19: 0=Top&Flip, 1=Arah Minoritas, 2=Liga Deviasi
        if idx == 0:
            self._render_top_selisih()
            self._render_flip()
        elif idx == 1:
            self._render_minoritas()
        elif idx == 2:
            self._render_liga()

    def _anasec_scope(self):
        """v3.9.15: baris file utk analisa per-periode (Arah Minoritas /
        Liga Deviasi): BULAN TERBARU + SATU minggu snapshot.
        Minggu file KUMULATIF (WEEK 2 ⊇ WEEK 1) → menjumlah lintas minggu
        = menghitung ganda — karena itu agregat per-resto SELALU satu
        minggu: preferensi minggu yang MEMUAT H (aturan kolom H); bila
        tidak ada di bulan tsb → minggu terakhir (dgn catatan jujur).
        Return (df | None, label | pesan)."""
        fdf = self._file_df
        if fdf is None or fdf.empty:
            return None, "Belum ada file deviasi."
        bl = pd.to_numeric(fdf["_bulan_num"], errors="coerce").fillna(0)
        if not bool((bl > 0).any()):
            return None, ("File tanpa kolom BULAN — analisa per-periode "
                          "butuh label bulan.")
        bmax = int(bl.max())
        d = fdf.loc[bl == bmax]
        bulan_lbl = _BULAN_NAME.get(bmax, str(bmax))
        hs = pd.to_numeric(d["_h"], errors="coerce")
        note = ""
        wk_sel = None
        if not self._show_all_weeks.get():
            wt = _h_to_week_target(int(self.tanggal_h))
            if bool((hs == wt).any()):
                wk_sel = wt
            else:
                note = (f" (minggu cut-off H {wt} tak ada di bulan ini — "
                        "pakai minggu terakhir)")
        else:
            note = (" (snapshot satu minggu — minggu file kumulatif, "
                    "menjumlah lintas minggu = menghitung ganda)")
        if wk_sel is None:
            wk_sel = int(hs.max())
        d = d.loc[hs == wk_sel]
        # v3.9.15a (audit ulang P1-1): >1 label Minggu bisa memetakan ke
        # H SAMA (WEEK 3 & WEEK 4 → 25; file bisa memuat keduanya) —
        # agregat per-resto WAJIB SATU snapshot (menjumlahkan W3+W4 =
        # menghitung ganda, krn minggu file kumulatif). Pertahankan label
        # TERAKHIR (snapshot paling lengkap) — dilaporkan di label.
        wl_all = sorted({str(v) for v in d["Minggu"]})
        if len(wl_all) > 1:
            d = d.loc[d["Minggu"] == wl_all[-1]]
            note += (f" (H {wk_sel} memuat {len(wl_all)} minggu — dipakai "
                     f"{wl_all[-1]} saja)")
        wl = ", ".join(sorted({str(v) for v in d["Minggu"]}))
        label = f"Bulan {bulan_lbl} · Minggu {wl} (H {wk_sel}){note}"
        return d, label

    # -- 🧭 Arah Minoritas (A4) ----------------------------------------------
    def _render_minoritas(self):
        """🧭 Arah Minoritas per Bahan (v3.9.15 — pola item-anomali-outlets
        repo): resto yang arah DEV-nya MELAWAN mayoritas resto lain pada
        bahan sama (mayoritas ketat: mayoritas > minoritas — kandidat
        salah-input/salah-satuan). Scope = bulan terbaru + satu minggu
        (lihat _anasec_scope). VEKTOR penuh."""
        tree = self._min_tree
        tree.delete(*tree.get_children())
        self._min_df = None
        self._min_scope_df = None
        self._min_maj_sign = None
        self._min_bahan_map = {}
        self._min_arah_cells = {"MINUS": [], "SURPLUS": []}
        d, label = self._anasec_scope()
        if d is None:
            self._min_status_var.set(label)
            return
        if d.empty:
            self._min_status_var.set(f"{label} · 0 baris.")
            return
        dev = pd.to_numeric(d["DEV Lalu"], errors="coerce").fillna(0.0)
        dev_n = dev.to_numpy(dtype=float)
        sgn = np.sign(dev_n)
        tmp = pd.DataFrame({
            "b": d["_bahan_norm"].to_numpy(),
            "sgn": sgn,
            "abs": np.abs(dev_n),
            "is_pos": sgn > 0,
            "is_neg": sgn < 0,
        })
        agg = tmp.groupby("b").agg(pos=("is_pos", "sum"),
                                   neg=("is_neg", "sum"))
        pos_a = agg["pos"].to_numpy()
        neg_a = agg["neg"].to_numpy()
        maj = np.where(neg_a > pos_a, -1,
                       np.where(pos_a > neg_a, 1, 0))
        min_cnt = np.minimum(pos_a, neg_a)
        keep = (maj != 0) & (min_cnt >= 1)
        if not bool(keep.any()):
            self._min_status_var.set(
                f"{label} · tidak ada bahan dengan arah minoritas "
                "(semua bahan searah).")
            return
        maj_map = pd.Series(maj, index=agg.index)
        tmp["maj"] = tmp["b"].map(maj_map)
        msk_min = (tmp["maj"] != 0) & (tmp["sgn"] == -tmp["maj"])
        abs_min = tmp.loc[msk_min].groupby("b")["abs"].sum()
        idx = agg.index[keep]
        nama = d.groupby("_bahan_norm")["Nama Barang"].first().reindex(idx)
        sat = d.groupby("_bahan_norm")["Satuan"].first().reindex(idx)
        pos_r = agg["pos"].reindex(idx).to_numpy()
        neg_r = agg["neg"].reindex(idx).to_numpy()
        maj_r = maj_map.reindex(idx).to_numpy()
        mcount = min_cnt[keep]
        tot = pos_r + neg_r
        mdf = pd.DataFrame({
            "_bahan_norm": idx.to_numpy(),
            "Nama Barang": nama.to_numpy(),
            "Satuan": sat.to_numpy(),
            "Resto Mayoritas": np.maximum(pos_r, neg_r),
            "Resto Minoritas": mcount,
            "Arah Mayoritas": np.where(maj_r < 0, "MINUS", "SURPLUS"),
            "Σ|DEV| Minoritas": abs_min.reindex(idx).fillna(0.0).to_numpy(),
            "% Minoritas": mcount / tot,
        })
        mdf = mdf.sort_values(["Σ|DEV| Minoritas", "_bahan_norm"],
                              ascending=[False, True], kind="stable")
        self._min_df = mdf
        self._min_scope_df = d
        self._min_maj_sign = maj_map
        # filter header ⧩
        df = mdf
        for col, sel in self._min_sel.items():
            if df.empty:
                break
            if col in df.columns and sel is not None:
                fmt = self._fmt_analisa_series(col, df[col])
                df = df[fmt.isin(sel)]
        if df.empty:
            self._min_status_var.set("0 baris setelah filter.")
            return
        self._min_status_var.set(
            f"{label} · {len(df)} bahan ber-arah-minoritas")
        m = len(df)
        cols_np = {c: df[c].to_numpy() for c in
                   ("Nama Barang", "Satuan", "Resto Mayoritas",
                    "Resto Minoritas", "Arah Mayoritas",
                    "Σ|DEV| Minoritas", "% Minoritas", "_bahan_norm")}
        items = []
        arah_cells = {"MINUS": [], "SURPLUS": []}
        bahan_map = {}
        for i in range(m):
            iid = f"min_{i}"
            values = [str(i + 1),
                      str(cols_np["Nama Barang"][i]),
                      str(cols_np["Satuan"][i]),
                      str(int(cols_np["Resto Mayoritas"][i])),
                      str(int(cols_np["Resto Minoritas"][i])),
                      str(cols_np["Arah Mayoritas"][i]),
                      self._fmt_num(cols_np["Σ|DEV| Minoritas"][i]),
                      self._fmt_pct(cols_np["% Minoritas"][i])]
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            av = str(cols_np["Arah Mayoritas"][i])
            if av in arah_cells:
                arah_cells[av].append((iid, "Arah Mayoritas"))
            bahan_map[iid] = str(cols_np["_bahan_norm"][i])
            items.append(("", iid, {"values": values, "tags": tuple(tags)}))
        self._min_arah_cells = arah_cells
        self._min_bahan_map = bahan_map
        self._anasec_insert(
            tree, items, on_done=lambda: self._reapply_min_tags(tree))

    def _min_col_values(self, col: str) -> list:
        d = self._min_df
        if d is None or d.empty or col not in d.columns:
            return []
        return self._fmt_analisa_series(col, d[col]).unique().tolist()

    def _on_min_filter(self, col: str, selected):
        self._min_sel[col] = selected
        self._render_minoritas()

    def _sort_min(self, col: str, reverse: bool = True, tree=None):
        tree = tree if tree is not None else self._min_tree
        parse = (self._parse_num_id if col in
                 ("Peringkat", "Resto Mayoritas", "Resto Minoritas",
                  "Σ|DEV| Minoritas", "% Minoritas") else None)
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_min_tags(tree)

    def _reapply_min_tags(self, tree):
        if not self._cell_tags:
            return
        for av, tag in (("MINUS", "min_minus"), ("SURPLUS", "min_surplus")):
            cells = self._min_arah_cells.get(av) or []
            if cells:
                apply_cell_tag(tree, tag, cells)

    def _on_min_double_click(self, event):
        tree = event.widget
        iid = tree.identify_row(event.y)
        if not iid:
            return
        bahan = self._min_bahan_map.get(iid)
        if bahan:
            self._minoritas_drilldown(bahan)

    def _minoritas_drilldown(self, bahan_norm: str):
        """Popup resto minoritas utk satu bahan (klik-2×)."""
        scope = self._min_scope_df
        maj = self._min_maj_sign
        if scope is None or maj is None or bahan_norm not in maj.index:
            return
        m = float(maj.loc[bahan_norm])
        if m == 0:
            return
        dev = pd.to_numeric(scope["DEV Lalu"],
                            errors="coerce").fillna(0.0).to_numpy(float)
        sel = ((scope["_bahan_norm"].to_numpy() == bahan_norm)
               & (np.sign(dev) == -m))
        sub = scope.loc[sel]
        if sub.empty:
            return
        nama = str(sub["Nama Barang"].iloc[0])
        dev_s = dev[sel]
        ordd = np.argsort(-np.abs(dev_s), kind="stable")
        sub = sub.iloc[ordd]
        dev_s = dev_s[ordd]
        arah_min = "SURPLUS" if -m > 0 else "MINUS"
        arah_may = "MINUS" if m < 0 else "SURPLUS"
        cols_spec = [("Resto", 110, "w"), ("Minggu", 90, "w"),
                     ("DEV", 100, "e"), ("Arah", 110, "w")]
        rows = []
        neg = []
        resn = sub["Resto"].to_numpy()
        mgn = sub["Minggu"].to_numpy()
        for i in range(len(sub)):
            iid = f"md{i}"
            rows.append([str(resn[i]), str(mgn[i]),
                         self._fmt_num(dev_s[i]),
                         f"MINORITAS ({arah_min})"])
            if dev_s[i] < 0:
                neg.append((iid, "DEV"))
        return self._popup_table(
            f"🧭 Arah Minoritas — {nama} (mayoritas {arah_may})",
            cols_spec, rows, cell_tags={"neg_cell": neg})

    # -- 🏆 Liga Deviasi (A1) ------------------------------------------------
    def _render_liga(self):
        """🏆 Liga Deviasi-Rate per Bahan (v3.9.15 — pola waste-rate-league
        repo): rate = |DEV|/|BOM| per resto pada SATU bahan (adil antar
        resto); baseline populasi MEDIAN + MAD → robust-z = (rate −
        median)/(1,4826 × MAD) — kebal outlier. Guard: populasi ≥ 5 resto
        ber-BOM (MIN_OUTLETS) & MAD > 0 (z "—" bila tak terdefinisi);
        resto ber-BOM dengan DEV 0 ikut populasi (jujur — feed median)
        tapi tidak diranking; resto DEV≠0 tanpa BOM = orphan (dilaporkan).
        Urut rate ↓ · resto ↑. VEKTOR penuh."""
        tree = self._liga_tree
        tree.delete(*tree.get_children())
        self._liga_df = None
        self._liga_stats = {}
        self._liga_z_cells = {"high": [], "warn": []}
        self._liga_neg_cells = []
        d, label = self._anasec_scope()
        if d is None:
            self._liga_status_var.set(label)
            self._liga_base_var.set("")
            # v3.9.15a (audit P2-3): combobox ikut dikosongkan (dulu
            # menampilkan daftar bahan file yang sudah ditutup).
            self._liga_combo["values"] = []
            self._liga_bahan_var.set("")
            self._liga_bahan_norm = None
            return
        bom = pd.to_numeric(d["BOM Lalu"], errors="coerce").fillna(0.0)
        dev = pd.to_numeric(d["DEV Lalu"], errors="coerce").fillna(0.0)
        bom_abs = bom.abs().to_numpy(dtype=float)
        dev_n = dev.to_numpy(dtype=float)
        pop_mask = bom_abs > 0
        b_arr = d["_bahan_norm"].to_numpy()
        if not bool(pop_mask.any()):
            self._liga_status_var.set(f"{label} · tidak ada baris ber-BOM.")
            self._liga_base_var.set("")
            self._liga_combo["values"] = []
            self._liga_bahan_var.set("")
            self._liga_bahan_norm = None
            return
        # urutan bahan combobox: Σ|DEV| menurun (populasi ber-BOM saja)
        tmp = pd.DataFrame({"b": b_arr, "abs": np.abs(dev_n)})
        tmp = tmp.loc[pop_mask]
        order = (tmp.groupby("b")["abs"].sum()
                 .sort_values(ascending=False, kind="stable"))
        vals = order.index.tolist()
        cur = list(self._liga_combo["values"])
        if cur != vals:
            self._liga_combo["values"] = vals
        if self._liga_bahan_norm not in vals:
            self._liga_bahan_norm = vals[0]
        self._liga_bahan_var.set(self._liga_bahan_norm)
        b = self._liga_bahan_norm
        bmask = (b_arr == b) & pop_mask
        sub = d.loc[bmask]
        bom_s = bom_abs[bmask]
        dev_s = dev_n[bmask]
        n = len(sub)
        if n < LIGA_MIN_POPULASI:
            self._liga_status_var.set(
                f"Populasi {n} resto ber-BOM < {LIGA_MIN_POPULASI} — liga "
                f"dilewati (MIN_OUTLETS).")
            self._liga_base_var.set("")
            return
        rate = np.abs(dev_s) / bom_s
        med = float(np.median(rate))
        mad = float(np.median(np.abs(rate - med)))
        # v3.9.15a (audit P2-1): np.where mengevaluasi KEDUA cabang →
        # pembagian MAD=0 memuntahkan RuntimeWarning walau hasil benar —
        # errstate membungkam (NaN tetap dihasilkan utk jalur guard).
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(mad > 0, (rate - med) / (LIGA_MAD_SCALE * mad),
                         np.nan)
        league_mask = dev_s != 0
        orphan = int(((b_arr == b) & ~pop_mask
                      & (dev_n != 0)).sum())
        ldf = pd.DataFrame({
            "Resto": sub["Resto"].to_numpy(),
            "_resto_norm": sub["_resto_norm"].to_numpy(),
            "BOM": bom_s, "DEV": dev_s,
            "Arah": np.where(dev_s < 0, "MINUS",
                             np.where(dev_s > 0, "SURPLUS", "NOL")),
            "Rate": rate, "z": z,
        })
        self._liga_stats = {"n": n, "median": med, "mad": mad, "sel": b,
                            "zero": int((~league_mask).sum()),
                            "orphan": orphan}
        ldf = ldf.loc[league_mask]
        # v3.9.15b (audit-2 FIX): baseline populasi DISUSUN & DITAMPILKAN
        # SEBELUM cabang kosong — pindah ke bahan lain dgn semua DEV 0
        # tidak lagi MEMBIARKAN baseline BAHAN LAMA tampil (stale — median/
        # MAD bahan sebelumnya, menyesatkan; status benar tapi baseline
        # salah bahan).
        base = (f"Populasi {n} resto ber-BOM · median rate "
                f"{self._fmt_pct(med)} · MAD {self._fmt_pct(mad)} · "
                f"z = (rate − median)/(1,4826 × MAD)")
        if mad <= 0:
            base += " · MAD 0 → z tak terdefinisi (tampil '—')"
        if self._liga_stats["zero"]:
            base += (f" · {self._liga_stats['zero']} resto rate 0 "
                     "(DEV 0 — dihitung di populasi, tak diranking)")
        if orphan:
            base += f" · {orphan} resto DEV≠0 tanpa BOM (tak masuk liga)"
        self._liga_base_var.set(base)
        # v3.9.15a (audit P2-7): pesan jujur saat liga kosong KARENA semua
        # DEV 0 (bukan salah dibaca '0 baris setelah filter').
        if ldf.empty and not any(v is not None
                                 for v in self._liga_sel.values()):
            self._liga_df = ldf
            self._liga_status_var.set(
                f"{label} · semua DEV 0 — tak ada resto utk diranking")
            return
        ldf = ldf.sort_values(["Rate", "_resto_norm"],
                              ascending=[False, True], kind="stable")
        self._liga_df = ldf
        # filter header ⧩
        df = ldf
        for col, sel in self._liga_sel.items():
            if df.empty:
                break
            if col in df.columns and sel is not None:
                fmt = self._fmt_analisa_series(col, df[col])
                df = df[fmt.isin(sel)]
        if df.empty:
            self._liga_status_var.set("0 baris setelah filter.")
            return
        self._liga_status_var.set(
            f"{label} · {len(df)} resto diranking (dari {n} populasi)")
        m = len(df)
        cols_np = {c: df[c].to_numpy() for c in
                   ("Resto", "BOM", "DEV", "Arah", "Rate", "z")}
        items = []
        z_cells = {"high": [], "warn": []}
        neg_cells = []
        for i in range(m):
            iid = f"liga_{i}"
            zv = cols_np["z"][i]
            values = [str(i + 1),
                      str(cols_np["Resto"][i]),
                      self._fmt_num(cols_np["BOM"][i]),
                      self._fmt_num(cols_np["DEV"][i]),
                      str(cols_np["Arah"][i]),
                      self._fmt_pct(cols_np["Rate"][i]),
                      self._fmt_dec2(zv)]
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            if zv is not None and not (isinstance(zv, float)
                                       and np.isnan(zv)):
                if zv > 2:
                    z_cells["high"].append((iid, "z"))
                elif zv > 1:
                    z_cells["warn"].append((iid, "z"))
            dv = cols_np["DEV"][i]
            if dv is not None and not (isinstance(dv, float)
                                       and np.isnan(dv)) and dv < 0:
                neg_cells.append((iid, "DEV"))
            items.append(("", iid, {"values": values, "tags": tuple(tags)}))
        self._liga_z_cells = z_cells
        self._liga_neg_cells = neg_cells
        self._anasec_insert(
            tree, items, on_done=lambda: self._reapply_liga_tags(tree))

    def _liga_col_values(self, col: str) -> list:
        d = self._liga_df
        if d is None or d.empty or col not in d.columns:
            return []
        return self._fmt_analisa_series(col, d[col]).unique().tolist()

    def _on_liga_filter(self, col: str, selected):
        self._liga_sel[col] = selected
        self._render_liga()

    def _sort_liga(self, col: str, reverse: bool = True, tree=None):
        tree = tree if tree is not None else self._liga_tree
        parse = (self._parse_num_id if col in
                 ("Peringkat", "BOM", "DEV", "Rate", "z") else None)
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_liga_tags(tree)

    def _reapply_liga_tags(self, tree):
        if not self._cell_tags:
            return
        if self._liga_neg_cells:
            apply_cell_tag(tree, "neg_cell", self._liga_neg_cells)
        for k, tag in (("high", "z_high"), ("warn", "z_warn")):
            cells = self._liga_z_cells.get(k) or []
            if cells:
                apply_cell_tag(tree, tag, cells)

    def _on_liga_bahan_changed(self, _event=None):
        """Combobox bahan liga berganti → render ulang liga bahan tsb."""
        b = (self._liga_bahan_var.get() or "").strip()
        if b:
            self._liga_bahan_norm = b
        self._render_liga()

    # -- Popup drilldown generik ----------------------------------------------
    def _popup_table(self, title: str, cols_spec: list, rows: list,
                     cell_tags: dict | None = None,
                     tag_colors: dict | None = None,
                     geometry: str = "1000x430"):
        """Popup drill-down generik (v3.9.15 — dipakai Arah
        Minoritas): Toplevel + tree (heading, resize) + footer jumlah +
        ✕ Tutup + ESC. rows = nilai TERFORMAT per baris; cell_tags =
        {tag: [(iid, kolom)]} (tag warna via tag_colors / _setup_tags)."""
        win = tk.Toplevel(self.winfo_toplevel())
        win.title(title)
        win.geometry(geometry)
        win.configure(bg=C_BG)
        with contextlib.suppress(tk.TclError):
            win.transient(self.winfo_toplevel())
        body = tk.Frame(win, bg=C_BG)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        cols = [c[0] for c in cols_spec]
        tree = ttk.Treeview(body, columns=cols, show="headings",
                            selectmode="browse")
        for name, width, anchor in cols_spec:
            tree.column(name, width=width, minwidth=34, anchor=anchor)
            tree.heading(name, text=name)
        vsb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(body, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        enable_col_resize(tree)
        self._setup_tags(tree)
        if tag_colors:
            for tag, color in tag_colors.items():
                tree.tag_configure(tag, foreground=color)
        for i, vals in enumerate(rows):
            tree.insert("", "end", iid=f"p{i}", values=vals,
                        tags=("evenrow" if i % 2 == 0 else "oddrow",))
        if cell_tags:
            for tag, cells in cell_tags.items():
                if cells:
                    apply_cell_tag(tree, tag, cells)
        foot = tk.Frame(body, bg=C_BG)
        foot.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Label(foot, text=f"{len(rows)} baris", bg=C_BG,
                 fg=C_TEXT_MUTED, font=font(8, "bold")).pack(side="left")
        GhostButton(foot, text="✕ Tutup",
                    command=win.destroy).pack(side="right")

        def _close(_e=None):
            win.destroy()

        win.bind("<Escape>", _close)
        # v3.9.15a (audit P2-5): ambil fokus supaya ESC langsung bekerja
        # tanpa harus mengetik area popup dulu (pola open_tree_maximized).
        with contextlib.suppress(tk.TclError):
            win.focus_set()
        return win, tree

    @staticmethod
    def _fmt_analisa_series(col, series):
        """Format kolom tabel analisa (filter/sort konsisten tampilan).
        v3.9.15: kolom tabel analisa (Min/Liga; Risk/Bench dihapus
        v3.9.19)."""
        if col in ("Disparitas", "Disparitas Rerata", "Rate",
                   "% Minoritas"):
            return series.map(KomparasiDeviasiView._fmt_pct)
        if col in ("DEV Lalu", "GR Saat Ini", "Selisih", "DEV Bulan Lalu",
                   "DEV Saat Ini", "Δ", "BOM", "DEV",
                   "Loss (Σ|DEV−|)", "Median Kelompok", "Opportunity",
                   "Σ|DEV| Minoritas"):
            return series.map(KomparasiDeviasiView._fmt_num)
        if col in ("z",):
            return series.map(KomparasiDeviasiView._fmt_dec2)
        return series.astype(str)

    def _maximize_top(self):
        def filter_setup(new_tree):
            attach_clone_filters(
                new_tree, [c[0] for c in self.TOP_COLS],
                get_values=self._top_col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_top(
                    c, reverse=d, tree=t),
                on_after_filter=lambda t=new_tree: self._reapply_top_tags(t))

        return open_tree_maximized(
            self._top_tree, "Analisa — Top Selisih",
            setup_tags=lambda t: self._setup_tags(t),
            on_filter_setup=filter_setup,
            on_render_done=self._reapply_top_tags)

    def _maximize_flip(self):
        def filter_setup(new_tree):
            attach_clone_filters(
                new_tree, [c[0] for c in self.FLIP_COLS],
                get_values=self._flip_col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_flip(
                    c, reverse=d, tree=t),
                on_after_filter=lambda t=new_tree: self._reapply_flip_tags(t))

        return open_tree_maximized(
            self._flip_tree, "Analisa — Perubahan Arah",
            setup_tags=lambda t: self._setup_flip_tags(t),
            on_filter_setup=filter_setup,
            on_render_done=self._reapply_flip_tags)

    # =========================================================================
    # ⛶ PERBESAR (fullscreen)
    # =========================================================================
    def _maximize(self):
        def filter_setup(new_tree):
            attach_clone_filters(
                new_tree,
                [c[0] for c in self.COLUMNS if c[0] != "✓"],
                get_values=self._col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_by(c, reverse=d,
                                                               tree=t),
                # v3.9.5 FIX (audit 19-a #3): filter di clone ⛶ rebuild
                # baris (delete+insert) → tag per-cell harus dipasang
                # ulang setelahnya — dulu minus-merah & warna Status
                # hilang setelah memfilter di window besar.
                on_after_filter=lambda t=new_tree: self._reapply_cell_tags(t))

        win, new_tree = open_tree_maximized(
            self.tree, "Komparasi Deviasi — Lalu vs Saat Ini",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_filter_setup=filter_setup,
            on_render_done=self._reapply_cell_tags)
        new_tree.bind("<Button-1>", self._on_tree_click, add="+")
        return win, new_tree

    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        if self._busy and tree is None:
            # v3.9.5 (audit 19-b #6): antre sort saat render batch masih
            # berjalan (dulu dibuang diam-diam tanpa umpan balik)
            self._pending_sort = (col, reverse)
            return
        tree = tree if tree is not None else self.tree
        parse = self._parse_num_id if col in self.NUMERIC_COLS else None
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_cell_tags(tree)

    def _auto_fit(self):
        auto_fit_columns(self.tree)

    # =========================================================================
    # DOUBLE-CLICK → POPUP DETAIL (difilter barang + resto + tanggal H)
    # =========================================================================
    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return
        tree = event.widget
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return
        try:
            if identify_to_column(tree, tree.identify_column(event.x)) == "✓":
                self._on_tree_click(event)
                return
        except Exception:
            pass
        values = tree.item(row_iid, "values")
        if not values:
            return
        col_ids = [c[0] for c in self.COLUMNS]
        row_data = dict(zip(col_ids, values))
        nama_barang = row_data.get("Nama Barang")
        if not nama_barang:
            return
        # v3.9.13: kolom H dihapus dari TABEL — tanggal H popup diambil
        # dari SNAPSHOT baris (kolom internal; identik utk clone ⛶ yang
        # mempertahankan iid — toggle ✓ follow-up clone sudah bukti).
        snap = self._row_snaps.get(row_iid) or {}
        try:
            h = int(snap.get("h") or 0)
        except (TypeError, ValueError):
            h = 0

        # v3.9.5 FIX (audit 19-a #2 / 19-c #8): pakai nama barang & resto
        # versi APP — popup memfilter Nama Barang secara EXACT; nama file
        # (kapital/spasi beda) cocok di tabel via normalisasi tapi popup
        # kosong bila nama RAW dipakai.
        resto_raw = row_data.get("Resto")
        pair = self._pair_index.get(
            (_norm_name(nama_barang), _norm_resto(resto_raw)))
        nb_app, nr_app = (pair if pair is not None
                          else (nama_barang, _norm_resto(resto_raw)))

        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()
        active_filters = {}
        if nr_app:
            active_filters["NAMA RESTO"] = nr_app
        show_details_popup(
            root, self.data,
            nama_barang=nb_app,
            jenis=None,
            tanggal=h,
            filters=active_filters,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _fmt_num(val) -> str:
        """Format angka gaya Indonesia: 1.234.567 / 1.234,5, negatif
        kurung, 0/NaN → '-' (identik view lain)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        if val == 0:
            return "-"
        if val == int(val):
            s = fmt_int_id(val)
        else:
            s = f"{val:,.1f}".replace(",", "\u00a0").replace(".", ",").replace(
                "\u00a0", ".")
        if val < 0:
            return f"({s[1:]})"
        return s

    @staticmethod
    def _fmt_pct(val) -> str:
        """Ratio (0.2697) → '26,97%'; NaN → '—'.

        v3.9.5 (audit 19-a #8): -0.0 → '0,00%' (dulu '-0,00%' — tanda
        nol negatif bocor karena '-0.0 < 0' adalah False di Python)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        if val == 0:
            return "0,00%"
        s = f"{val * 100:,.2f}".replace(",", "\u00a0").replace(
            ".", ",").replace("\u00a0", ".")
        if val < 0:
            return f"({s[1:]})%"
        return f"{s}%"

    @staticmethod
    def _fmt_dec2(val) -> str:
        """z-score dkk: '1,94' / '(1,94)' / '—' — koma desimal Indonesia
        (v3.9.15 — kolom z liga)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        s = f"{val:,.2f}".replace(",", "\u00a0").replace(".", ",").replace(
            "\u00a0", ".")
        if val < 0:
            return f"({s[1:]})"
        return s

    @staticmethod
    def _parse_num_id(s):
        """Parser sort utk format Indonesia: '1.234' = 1234,
        '(1.234)' = -1234, '-' = 0, '12,5' = 12.5, '26,97%' = 26.97."""
        s = str(s).replace("%", "").replace("—", "").strip()
        if s in ("-", ""):
            return 0.0
        neg = s.startswith("(") and s.endswith(")")
        if neg:
            s = s[1:-1]
        s = s.replace(".", "").replace(",", ".")
        try:
            v = float(s)
        except ValueError:
            return 0.0
        return -v if neg else v
