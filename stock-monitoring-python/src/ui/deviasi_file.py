"""deviasi_file — BACA FILE DEVIASI RESMI (parser murni, tanpa Tk).

v3.11.30 — RELOKASI dari komparasi_deviasi_view.py (tab 📋 Laporan
Deviasi DIHAPUS — user: "Hapus tab laporan deviasi dan dead code nya").
Tab 📋 berisi 3 mode (⚖ Komparasi File Deviasi · 🚨 Anomali COM ·
💰 Nominal (H)) — semuanya dibongkar. Yang DIPERTAHANKAN hanyalah
fungsi murni yang masih dipakai fitur lain:

  - parse_deviasi_file        → sumber kolom 'Dev. Bulan Lalu' tab
                                📦 Deviasi GR / 🧩 PCS + analisa CEK
                                lalu-kini + popup 'Nominal Deviasi
                                Bulan Lalu' tab 🧮 Nominal Deviasi
                                (auto-load app-level: _auto_load_lalu
                                + tombol 📂 kartu DEV BULANAN ⚙️ Config);
  - bulan_mundur_list         → transparansi bulan kartu ⚙️ Config;
  - auto_bulanan_paths        → resolusi path '20.{BULAN} {TAHUN}'
                                N bulan mundur (auto-load).

Membaca file = TANPA UI; pemanggil menjalankan fungsi ini di thread
worker (pola anti-beku v3.9.5 — file 9,4MB ±8 detik).
"""
import contextlib
import os
import re

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Konstanta minggu/bulan (identik era komparasi)
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


def bulan_mundur_list(period, jumlah) -> list:
    """v3.11.12 — daftar (tahun, bulan) N bulan MUNDUR dari period
    (urut KRONOLOGIS lama→baru; wrap tahun otomatis — Januari mundur
    1 = Desember tahun sebelumnya). Dipakai auto_bulanan_paths +
    status kartu 'Auto File Deviasi Bulan Lalu' tab ⚙️ Config
    (transparansi "sekarang September → file Agustus" — user: "gimana
    cara tau misal sekarang bulan september apakah program otomatis
    ambil yang agustus?"). Invalid (period bukan (y, m) dgn m 1..12 /
    jumlah < 1) → [] (degrade jujur)."""
    try:
        y, m = int(period[0]), int(period[1])
        n = int(jumlah)
    except (TypeError, ValueError, IndexError):
        return []
    if not (1 <= m <= 12) or n < 1:
        return []
    out = []
    for _ in range(min(n, 12)):
        m -= 1
        if m < 1:
            m = 12
            y -= 1
        out.append((y, m))
    out.reverse()   # kronologis lama → baru
    return out


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


def bulan_label(v) -> str:
    """Label bulan kanonik dari nilai BULAN ('205.OKT 26' → 'OKTOBER';
    tak terparse → string mentah)."""
    n = _bulan_num(v)
    return _BULAN_NAME.get(n, str(v).strip())


def h_to_week_target(h: int) -> int:
    """H input → CUT-OFF minggu yang MEMUAT tanggal H (minggu file =
    rentang kumulatif dari tanggal 1; bulan bisnis berakhir tanggal 25):
        H 1–7 → 7 (WEEK 1) · H 8–14 → 14 (WEEK 2) ·
        H 15–31 → 25 (WEEK 3/4 — rentang 15..akhir bulan bisnis)
    v3.9.22: 26..31 kini juga → 25 (dulu → 31 "WEEK 5" — label minggu
    yang tak pernah ada di file → tabel analisa minggu-terfilter KOSONG
    saat H default dinamis 26 dari data user; minggu yang memuat H 26
    = WEEK 4)."""
    h = int(h)
    if h <= 7:
        return 7
    if h <= 14:
        return 14
    return 25


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
    # v3.9.38 — NOMINAL DEVIASI milik FILE sendiri (angka RESMI laporan:
    # harga snapshot saat laporan dibuat). Dipakai nominal_common.
    # hitung_nominal_lalu_pairs sebagai SUMBER UTAMA 'Nominal Lalu'
    # (dulu dihitung ulang harga 41.09 SEKARANG × DEV Lalu → beda harga
    # snapshot → nominal bulan-lalu menyimpang dari laporan resmi —
    # temuan user "harga per gr nya berbeda" BUMBU PASTA KUAH (V.20):
    # 41.09 sekarang 107,6386854/GR vs file 20.AGUSTUS ±113,048/GR).
    col_nom = _find_col(cols, "NOMINALDEVIASI")
    col_pct = None
    for k, orig in cols.items():
        if k.startswith("%") and "DEVIASI" in k and "BOM" in k:
            col_pct = orig
            break
    col_bulan = _find_col(cols, "BULAN", "MONTH")

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
        # v3.9.38 — kolom nominal resmi file (exact-match key
        # 'NOMINALDEVIASI' — bukan NOMINAL WASTE/SUSUT/TRIAL/LOSS;
        # file tanpa kolom → NaN → konsumen fallback hitung ulang).
        "Nominal Deviasi Lalu": (
            pd.to_numeric(df[col_nom], errors="coerce")
            if col_nom is not None else np.nan),
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


def auto_bulanan_paths(cfg) -> list:
    """v3.11.9 → v3.11.30 — daftar path file deviasi bulan lalu utk N
    bulan mundur dari periode data (urut KRONOLOGIS lama→baru).

    cfg = (folder, (tahun, bulan), jumlah):
      - folder    : path absolut folder DEVIASI_BULANAN (config key
                    DeviasiBulananFolder; kartu ⚙️ Config);
      - (t, b)    : periode data BERJALAN (audit_result['period'] —
                    bulan lalu = b−1, wrap tahun);
      - jumlah    : 1..12 — berapa bulan mundur (user: "aku bisa
                    setting jumlah file").

    Nama file = '20.{BULAN} {TAHUN}' (mis. '20.AGUSTUS 2026') —
    case-insensitive (uppercase), ext .xlsx (prioritas) / .xlsm /
    .xls / .xlsb. Folder tak ada / cfg invalid / 0 file → []
    (degrade jujur)."""
    try:
        folder = str(cfg[0])
        _period = cfg[1]
        tahun = int(_period[0])
        bulan = int(_period[1])
        jumlah = int(cfg[2])
    except (TypeError, ValueError, IndexError):
        return []
    if not folder or not os.path.isdir(folder):
        return []
    if not (1 <= bulan <= 12):
        return []
    if not (1 <= jumlah <= 12):
        jumlah = 1
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    # base (tanpa ext) → path; ext favorit .xlsx dulu (setdefault
    # menyimpan yang PERTAMA dijumpai — urut prioritas ext).
    _ext_rank = {".xlsx": 0, ".xlsm": 1, ".xls": 2, ".xlsb": 3}
    names = sorted(
        (n for n in names
         if os.path.splitext(n)[1].lower() in _ext_rank),
        key=lambda n: (_ext_rank[os.path.splitext(n)[1].lower()], n))
    by_base: dict = {}
    for nm in names:
        base = os.path.splitext(nm)[0].strip().upper()
        by_base.setdefault(base, os.path.join(folder, nm))
    # v3.11.12 — daftar bulan via helper bersama bulan_mundur_list
    # (dipakai juga status kartu ⚙️ Config — transparansi bulan).
    out = []
    for y, m in bulan_mundur_list((tahun, bulan), jumlah):
        want = f"20.{_BULAN_NAME[m]} {y}".upper()
        p = by_base.get(want)
        if p:
            out.append(p)
    return out   # kronologis lama → baru
