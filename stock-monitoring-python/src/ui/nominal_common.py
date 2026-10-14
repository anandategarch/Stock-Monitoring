"""
nominal_common.py — v3.9.34 helper BERSAMA perhitungan Nominal Deviasi
(Harga 41.09 × Qty Deviasi). Sebelum v3.9.34 logika ini hanya hidup di
nominal_deviasi_view.py (mode 💰 Nominal (H)); kini dipakai 4 tempat:

  1. mode  💰 Nominal (H)        tab 📋 Laporan Deviasi (per pasangan)
  2. kolom Nominal               tab 📦 Deviasi GR & 🧩 Deviasi PCS
  3. kolom Nominal               mode ⚖ Komparasi (tab Laporan Deviasi —
                                  harga × GR Saat Ini)
  4. tab   🧮 Nominal Deviasi    (BARU — Σ per resto + popup rincian)

v3.9.36 — TAMBAHAN: hitung_nominal_lalu_pairs — pasangan per-barang
dari FILE deviasi (parse_deviasi_file tab ⚖ Komparasi, diteruskan app
lewat lalu_provider): bulan TERBARU di file + minggu TERAKHIR per
pasangan (penutupan bulan) → Nominal Lalu = harga × DEV Lalu. Dipakai
popup rincian tab 🧮 (kolom 'Nominal Deviasi Bulan Lalu').

v3.9.38 — ATURAN "QTY DEVIASI 0 TAK PERLU CARI HARGA" (user:
"Kuantiti Deviasi 0 takperlu cari harga. Cek juga keseluruhan
terkait ini"): pasangan ber-qty-deviasi PERSIS 0 → lookup harga
DILEWATI (Harga None, Harga Tampil '-', tanpa label '*') dan
Nominal = 0.0 (BUKAN None) → pasangan itu TIDAK dihitung sebagai
'tanpa harga' (kolom Tanpa Harga / popup tanpa harga / footer mode
💰) dan tetap netral di Σ — dulu baris qty-0 tanpa harga ikut
terhitung 'tanpa harga' menyesatkan. Berlaku di hitung_nominal_pairs,
hitung_nominal_lalu_pairs, kolom Nominal tab 📦 Deviasi GR/PCS
dan mode ⚖ Komparasi.

v3.9.38 — SUMBER UTAMA 'Nominal Lalu' = KOLOM NOMINAL DEVIASI MILIK
FILE (angka resmi laporan bulan lalu; parse_deviasi_file → 'Nominal
Deviasi Lalu'). Dulu v3.9.36 menghitung ulang harga 41.09 SEKARANG ×
DEV Lalu → harga snapshot beda bulan → nominal menyimpang dari
laporan resmi (temuan user BUMBU PASTA KUAH (V.20): 41.09 sekarang
107,6386854/GR — SAMA dgn hitungan manual user — vs file
20.AGUSTUS ±113,048/GR → selisih nominal ±2,34jt utk 1 baris MLGPAR
W4). Kolom file kosong/NaN → fallback hitung ulang (perilaku lama).

v3.9.41 — MINGGU TER-COCOK (user: "Nominal deviasi pembanding dari
bulan lalu sesuaikan week nya jika week 1 maka ambil data week 1
juga"): param h (tanggal analisa) → minggu file yang MEMUAT H
(H 1-7 → WEEK 1 / cut-off 7; 8-14 → WEEK 2 / 14; 15-31 → WEEK 3-4 /
25 — mirror _h_to_week_target komparasi v3.9.22). Baris minggu
persis itu yang dipilih; minggu itu tidak ada di file → fallback
minggu TERBESAR ≤ target (perbandingan periode terdekat), lalu
TERKECIL > target (file hanya punya minggu setelahnya). h=None →
perilaku lama (minggu terakhir = penutupan bulan — kompatibilitas
pemanggil lama). Kolom internal '_minggu' = label minggu terpilih
(dipakai label popup/footer supaya minggu pembanding JELIHAT).

ATURAN HARGA (identik sejak v3.9.32, kini satu sumber kebenaran):
  - harga_map   : {barang: (harga|None, satuan41-upper)} — global dari
                  file 41.09 (folder 09.Harga); Harga = Nilai Saldo
                  Akhir ÷ Kuantitas Saldo Akhir.
  - satuan sama (atau salah satu tak diketahui) → harga langsung.
  - satuan beda → normalisasi via peta rasio v3.9.31 (42.05+32.24):
        harga_rekap = harga41 × rasio(satuanRekap) / rasio(satuan41.09)
  - rasio tak men-cover → harga AS-IS berlabel satuan asli + penanda
    '*' dan nominal TIDAK dihitung (None) — transparan, bukan angka
    keliru; tidak ikut TOTAL.
  - barang tak ada di 41.09 / harga None → nominal None (tampil '-').
  - Qty Deviasi PERSIS 0 → TANPA lookup harga; Nominal 0.0 (bukan
    None — tak dihitung 'tanpa harga'; v3.9.38).

Qty Deviasi untuk pasangan = JENIS '3.DEVIASI' baris Tanggal H
(= SO − SALDO AKHIR sistem — nilai kolom Deviasi tab 📦 Deviasi GR).
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from src.pipeline.konversi_satuan import lookup_rasio


# ---------------------------------------------------------------------------
# NORMALISASI SATELIT
# ---------------------------------------------------------------------------
def norm_sat(v) -> str:
    """Satuan → upper/strip; NaN/None → ''."""
    try:
        s = str(v).strip().upper()
    except Exception:
        return ""
    return "" if s in ("NAN", "NONE") else s


# ---------------------------------------------------------------------------
# FORMAT ANGKA INDONESIA (dipakai kolom Nominal/Harga semua tabel)
# ---------------------------------------------------------------------------
def fmt_harga_id(v) -> str:
    """Harga: pecahan → 2 desimal (18,25); bulat → 1.234 (fmt_int_id)."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    av = abs(v)
    if av == int(av):
        # fmt_int_id lokal (hindari import widgets — modul UI-agnostic;
        # hasil identik: titik ribuan)
        s = f"{av:,.0f}".replace(",", ".")
        return s
    return f"{av:,.2f}".replace(",", "X").replace(".", ",") \
        .replace("X", ".")


def fmt_nominal_cell(val) -> str:
    """Nominal/qty: bulat → fmt ribuan titik; pecahan → 2 desimal koma;
    negatif dalam kurung; None/NaN/0 → '-'."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "-"
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if v == 0:
        return "-"
    neg = v < 0
    av = abs(v)
    if av == int(av):
        s = f"{av:,.0f}".replace(",", ".")
    else:
        s = f"{av:,.2f}".replace(",", "X").replace(".", ",") \
            .replace("X", ".")
    return f"({s})" if neg else s


# ---------------------------------------------------------------------------
# LOOKUP HARGA PER PASANGAN (barang, satuan-rekap)
# ---------------------------------------------------------------------------
def lookup_harga_pair(harga_map: dict | None,
                      konversi_map: dict | None,
                      barang, satuan_rekap) -> tuple:
    """→ (harga_norm: float | None, label: str, bintang: bool)

    harga_norm = harga per SATUAN REKAP pasangan (siap × qty deviasi).
      None  → nominal tak bisa dihitung (tanpa harga / tak terkonversi)
      label → satuan hasil normalisasi (utk display harga)
      bintang → True bila satuan tak ter-cover rasio (fallback '*')
    """
    b = str(barang).strip()
    entry = (harga_map or {}).get(b)
    if entry is None:
        return None, "-", False
    h41, sat41 = entry
    if h41 is None:
        return None, "-", False
    sat_rekap = norm_sat(satuan_rekap)
    if not sat41 or not sat_rekap or sat41 == sat_rekap \
            or sat_rekap == "-":
        # satuan sama (atau tak diketahui) → harga langsung
        return float(h41), (sat41 or sat_rekap or ""), False
    r_rekap, _t1 = lookup_rasio(konversi_map, b, sat_rekap)
    r_41, _t2 = lookup_rasio(konversi_map, b, sat41)
    if r_rekap and r_41:
        return float(h41) * r_rekap / r_41, sat_rekap, False
    # tak bisa dikonversi → harga as-is berpenanda '*'
    return None, f"{fmt_harga_id(float(h41))} {sat41}*", True


# ---------------------------------------------------------------------------
# NORMALISASI KUNCI FILE DEVIASI (mirror komparasi — v3.9.36)
# ---------------------------------------------------------------------------
def _norm_resto_lalu(v) -> str:
    """Mirror komparasi_deviasi_view._norm_resto: '1041.BDGUKU' /
    'B.1001.MLGPAR' / 'BDGUKU' → 'BDGUKU' (upper + strip + segmen
    setelah titik TERAKHIR). Duplikat LOKAL — nominal_common tidak
    boleh import komparasi_deviasi_view (komparasi sudah meng-import
    nominal_common sejak v3.9.34 → circular)."""
    s = str(v).strip().upper()
    if "." in s:
        s = s.split(".")[-1].strip()
    return s


def _norm_name_lalu(v) -> str:
    """Mirror komparasi_deviasi_view._norm_name: upper + rapat spasi
    ganda (duplikat lokal — alasan _norm_resto_lalu)."""
    return re.sub(r"\s+", " ", str(v).strip().upper())


# ---------------------------------------------------------------------------
# PASANGAN NOMINAL TANGGAL H (port inti _compute_nominal v3.9.32)
# ---------------------------------------------------------------------------
def hitung_nominal_pairs(data: pd.DataFrame | None, h: int,
                         harga_map: dict | None,
                         konversi_map: dict | None) -> pd.DataFrame:
    """Frame per pasangan tanggal H:
    [Nama Barang, Resto, Satuan, Harga, Harga Tampil, Qty Deviasi,
     Nominal] — urut |Nominal| MENURUN (pasangan tanpa nominal paling
    bawah, urut |qty deviasi|).

    Qty deviasi = JENIS '3.DEVIASI' Tanggal H (jumlah per pasangan).
    Dtype float64 EKSPLISIT utk Harga/Nominal (semua-None → kolom
    object → .abs() TypeError di worker — bug v3.9.32, dijaga di sini).
    DataFrame kosong bila tak ada baris DEVIASI tanggal H.
    """
    if data is None or data.empty:
        return pd.DataFrame()
    h = int(h)

    tnum = pd.to_numeric(data["Tanggal"], errors="coerce")
    dev = data[(data["JENIS"].astype(str) == "3.DEVIASI") & (tnum == h)]
    if dev.empty:
        return pd.DataFrame()
    dev = dev.copy()
    dev["NILAI"] = pd.to_numeric(dev["NILAI"], errors="coerce").fillna(0)

    # v3.9.42 — audit 61-a P3: SATUAN dinormalkan SEBELUM groupby —
    # 'GR' vs 'GR ' dulu membuat 2 grup → 2 baris pasangan KEMBAR di
    # popup per-resto (Σ tetap benar tapi baris dobel membingungkan).
    if "SATUAN" in dev.columns:
        dev["SATUAN"] = dev["SATUAN"].map(
            lambda v: norm_sat(v) if norm_sat(v) else "")

    grouped = (dev.groupby(["Nama Barang", "NAMA RESTO", "SATUAN"],
                           as_index=False, dropna=False)["NILAI"].sum())
    grouped = grouped.rename(columns={
        "NAMA RESTO": "Resto", "SATUAN": "Satuan",
        "NILAI": "Qty Deviasi"})
    grouped["Nama Barang"] = grouped["Nama Barang"].astype(str)
    grouped["Resto"] = grouped["Resto"].astype(str)
    grouped["Satuan"] = grouped["Satuan"].map(
        lambda v: norm_sat(v) if norm_sat(v) else "-")

    harga_vals = []
    harga_disp = []
    nominal_vals = []
    for _, r in grouped.iterrows():
        b = str(r["Nama Barang"]).strip()
        sat_rekap = norm_sat(r["Satuan"])
        # v3.9.38 — Kuantiti Deviasi 0 → TAK PERLU CARI HARGA (user:
        # "Kuantiti Deviasi 0 takperlu cari harga"): nominal pasti 0;
        # Harga None + Harga Tampil '-' (tanpa label '*') + Nominal
        # 0.0 — pasangan TIDAK dihitung 'tanpa harga' (isna) sehingga
        # kolom Tanpa Harga / popup tanpa harga / footer mode 💰 tak
        # menyesatkan (dulu qty-0 tanpa harga ikut terhitung).
        if float(r["Qty Deviasi"]) == 0.0:
            harga_vals.append(None)
            harga_disp.append("-")
            nominal_vals.append(0.0)
            continue
        harga, label, _bintang = lookup_harga_pair(
            harga_map, konversi_map, b, sat_rekap)
        if harga is not None:
            nom = harga * float(r["Qty Deviasi"])
            harga_disp.append(f"{fmt_harga_id(harga)} {label}")
        else:
            nom = None
            harga_disp.append(label or "-")
        harga_vals.append(harga)
        nominal_vals.append(nom)

    grouped["Harga"] = pd.Series(harga_vals, dtype="float64")
    grouped["Harga Tampil"] = harga_disp
    grouped["Nominal"] = pd.Series(nominal_vals, dtype="float64")

    grouped["_absnom"] = grouped["Nominal"].abs().fillna(0)
    grouped["_absqty"] = grouped["Qty Deviasi"].abs()
    grouped = (grouped.sort_values(
        ["_absnom", "_absqty"], ascending=[False, False],
        kind="mergesort").drop(columns=["_absnom", "_absqty"]))
    grouped = grouped.reset_index(drop=True)
    return grouped[["Nama Barang", "Resto", "Satuan", "Harga",
                    "Harga Tampil", "Qty Deviasi", "Nominal"]]


# ---------------------------------------------------------------------------
# AGREGASI PER RESTO (tab 🧮 Nominal Deviasi — v3.9.34)
# ---------------------------------------------------------------------------
def agregasi_nominal_per_resto(data: pd.DataFrame | None, h: int,
                               harga_map: dict | None,
                               konversi_map: dict | None) -> tuple:
    """→ (frame_per_resto, frame_pasangan).

    frame_per_resto: [Resto, N Barang, Tanpa Harga, Nominal Deviasi]
    urut |Nominal Deviasi| MENURUN. Σ nominal skipna (pasangan tanpa
    harga tidak dihitung — transparan). frame_pasangan = output
    hitung_nominal_pairs (utk popup rincian per resto).
    """
    pairs = hitung_nominal_pairs(data, h, harga_map, konversi_map)
    if pairs.empty:
        return pd.DataFrame(columns=["Resto", "N Barang", "Tanpa Harga",
                                     "Nominal Deviasi"]), pairs
    g = (pairs.groupby("Resto", as_index=False)
         .agg(**{
             "N Barang": ("Nominal", "size"),
             "Tanpa Harga": ("Nominal",
                             lambda s: int(pd.isna(s).sum())),
             "Nominal Deviasi": ("Nominal", "sum")}))
    g["_abs"] = g["Nominal Deviasi"].abs().fillna(0)
    g = g.sort_values("_abs", ascending=False,
                      kind="mergesort").drop(columns=["_abs"])
    g = g.reset_index(drop=True)
    g["N Barang"] = g["N Barang"].astype(int)
    g["Tanpa Harga"] = g["Tanpa Harga"].astype(int)
    return g, pairs


# ---------------------------------------------------------------------------
# PASANGAN NOMINAL BULAN LALU — FILE DEVIASI (v3.9.36)
# ---------------------------------------------------------------------------
_LALU_COLS = ["Resto", "Nama Barang", "Satuan", "Qty Deviasi Lalu",
              "Harga", "Nominal Lalu", "_resto_norm", "_bahan_norm",
              "_minggu"]


def _h_to_week_target(h: int) -> int:
    """v3.9.41 — H analisa → CUT-OFF minggu yang MEMUAT H (mirror
    komparasi_deviasi_view._h_to_week_target v3.9.22; duplikat LOKAL —
    nominal_common tak boleh import komparasi (circular)):
    H 1-7 → 7 (WEEK 1) · H 8-14 → 14 (WEEK 2) · H 15-31 → 25
    (WEEK 3/4 — 26..31 juga 25: minggu yang memuat H 26 = WEEK 4)."""
    h = int(h)
    if h <= 7:
        return 7
    if h <= 14:
        return 14
    return 25


def _pilih_minggu_lalu(weeks_avail: list, h: int | None) -> int | None:
    """v3.9.41 — pilih _h minggu pembanding dari minggu yang tersedia
    di file (bulan terbaru):
    - h None → minggu TERBESAR (perilaku lama — penutupan bulan);
    - h ada → target = _h_to_week_target(h):
        (1) minggu PERSIS target bila ada;
        (2) minggu TERBESAR ≤ target (periode terdekat sebelumnya);
        (3) minggu TERKECIL > target (file hanya punya minggu
            setelahnya — satu-satunya pilihan).
    None bila tak ada minggu sama sekali."""
    if not weeks_avail:
        return None
    if h is None:
        return max(weeks_avail)
    target = _h_to_week_target(h)
    if target in weeks_avail:
        return target
    below = [w for w in weeks_avail if w < target]
    if below:
        return max(below)
    return min(weeks_avail)


def hitung_nominal_lalu_pairs(file_df: pd.DataFrame | None,
                              harga_map: dict | None,
                              konversi_map: dict | None,
                              h: int | None = None) -> pd.DataFrame:
    """Frame per pasangan dari FILE deviasi (tab ⚖ Komparasi):
    [_resto_norm, _bahan_norm, Resto, Nama Barang, Satuan,
    Qty Deviasi Lalu, Harga, Nominal Lalu, _minggu].

    file_df = output parse_deviasi_file (kolom internal _bulan_num /
    _h / _resto_norm / _bahan_norm milik komparasi). Seleksi:
      - BULAN TERBARU di file (nomor bulan terbesar — multi-file
        History: bulan paling akhir = 'bulan lalu');
      - v3.9.41 MINGGU TER-COCOK dgn H analisa (param h — user:
        "jika week 1 maka ambil data week 1 juga"; lihat
        _pilih_minggu_lalu); h=None → minggu terakhir (perilaku lama).
    Nominal Lalu = SUMBER UTAMA kolom resmi file (v3.9.38) — harga
    snapshot saat laporan dibuat; kolom kosong/NaN/format lama →
    fallback Harga 41.09 (dinormalkan ke SATUAN BARIS FILE via peta
    rasio) × DEV Lalu.
    Tanpa harga / satuan tak terkonversi → None (tampil '-').
    Urut |Nominal Lalu| MENURUN (pasangan tanpa nominal paling
    bawah, urut |qty|). Frame kosong bila file kosong / kolom internal
    tak ada (file format lama).
    """
    empty = pd.DataFrame(columns=_LALU_COLS)
    if file_df is None or getattr(file_df, "empty", True):
        return empty
    need = ("_bulan_num", "_h", "_resto_norm", "_bahan_norm",
            "DEV Lalu", "Resto", "Nama Barang")
    missing = [c for c in need if c not in file_df.columns]
    if missing:
        return empty

    out = pd.DataFrame({
        "Resto": file_df["Resto"].astype(str).values,
        "Nama Barang": file_df["Nama Barang"].astype(str).values,
        "Satuan": (file_df["Satuan"].astype(str).values
                   if "Satuan" in file_df.columns else ""),
        # v3.9.41 — label minggu asli file (utk display minggu terpilih)
        "Minggu": (file_df["Minggu"].astype(str).str.strip().str.upper()
                   .values
                   if "Minggu" in file_df.columns
                   else np.full(len(file_df), "")),
        "_bulan_num": (pd.to_numeric(file_df["_bulan_num"],
                                    errors="coerce").fillna(0)
                       .astype(int).values),
        "_h": pd.to_numeric(file_df["_h"], errors="coerce")
            .fillna(0).values,
        "_resto_norm": file_df["_resto_norm"].astype(str).values,
        "_bahan_norm": file_df["_bahan_norm"].astype(str).values,
        "Qty Deviasi Lalu": (pd.to_numeric(file_df["DEV Lalu"],
                                           errors="coerce")
                             .fillna(0.0).values),
        # v3.9.38 — nominal RESMI milik file (parse_deviasi_file;
        # kolom tak ada di file format lama → NaN → fallback recompute)
        "Nominal Deviasi Lalu": (
            pd.to_numeric(file_df["Nominal Deviasi Lalu"],
                          errors="coerce").values
            if "Nominal Deviasi Lalu" in file_df.columns
            else np.full(len(file_df), np.nan)),
    })
    # (a) bulan TERBARU di file
    out = out[out["_bulan_num"] == out["_bulan_num"].max()].copy()
    if out.empty:
        return empty
    # (b) v3.9.41 — MINGGU TER-COCOK dgn H analisa (user: "jika week 1
    # maka ambil data week 1 juga"): minggu yang MEMUAT H dipilih;
    # minggu itu tak ada di file → minggu terdekat ≤ target, lalu
    # terkecil > target (lihat _pilih_minggu_lalu). h=None → minggu
    # terakhir (penutupan bulan — perilaku lama, kompatibilitas).
    _weeks_avail = sorted(int(w) for w in out["_h"].dropna().unique()
                          if pd.notna(w))
    _wk_sel = _pilih_minggu_lalu(_weeks_avail, h)
    if _wk_sel is None:
        return empty
    out = out[pd.to_numeric(out["_h"], errors="coerce") == _wk_sel].copy()
    # v3.9.42 — audit 61-a/61-b: WEEK 3 dan WEEK 4 sama-sama dipetakan
    # _h=25 (mirror komparasi v3.9.22). File yang memuat KEDUA label →
    # dedup keep="first" memilih baris file pertama (minggu tercampur
    # ARBITRER per pasangan). Fix: pilih SATU label minggu DETERMINISTIK
    # — label dgn NOMOR minggu TERBESAR (penutupan — semantik 'minggu
    # terakhir' v3.9.36) — lalu filter baris label itu SEBELUM dedup.
    if "Minggu" in out.columns and not out.empty:
        _labs = [str(x).strip().upper()
                 for x in out["Minggu"].dropna().unique()
                 if str(x).strip().upper() not in ("", "NAN", "NONE")]
        if len(_labs) > 1:
            def _lab_num(lab):
                m = re.search(r"(\d+)", lab)
                return int(m.group(1)) if m else 0
            _lab_sel = max(_labs, key=_lab_num)
            out = out[out["Minggu"].astype(str).str.strip()
                      .str.upper() == _lab_sel].copy()
    # label minggu terpilih utk display (label asli file; fallback
    # label cut-off bila kolom Minggu tak terbawa)
    _wk_fallback = {7: "WEEK 1", 14: "WEEK 2", 25: "WEEK 3/4"}.get(
        _wk_sel, f"WEEK cut-off H{_wk_sel}")
    _wk_label = _wk_fallback
    if "Minggu" in out.columns and len(out):
        _cand = str(out["Minggu"].iloc[0]).strip().upper()
        if _cand and _cand not in ("NAN", "NONE"):
            _wk_label = _cand
    out = out.drop_duplicates(subset=["_resto_norm", "_bahan_norm"],
                              keep="first")
    out = out.reset_index(drop=True)
    out["_minggu"] = _wk_label
    out = out.drop(columns=["Minggu"], errors="ignore")

    # (c) NOMINAL LALU — SUMBER UTAMA kolom resmi file (v3.9.38):
    # nilai file dipakai APA ADANYA (harga snapshot saat laporan dibuat —
    # angka resmi bulan lalu); kolom kosong/NaN / file format lama →
    # fallback hitung ulang harga 41.09 sekarang × DEV Lalu (lookup per
    # baris — pola komparasi v3.9.34a: TANPA cache persisten lintas-file).
    harga_vals = []
    nominal_vals = []
    for _, r in out.iterrows():
        b = str(r["Nama Barang"]).strip()
        sat_file = norm_sat(r["Satuan"])
        # v3.9.38 — nilai resmi file ADA → pakai langsung (harga lookup
        # tetap ditarik utk kolom Harga display; None bila tak ada).
        _fnom = r.get("Nominal Deviasi Lalu")
        _has_file_nom = _fnom is not None and not pd.isna(_fnom)
        if _has_file_nom:
            nominal_vals.append(float(_fnom))
            _hg, _lbl, _b = lookup_harga_pair(
                harga_map, konversi_map, b, sat_file)
            harga_vals.append(_hg)
            continue
        # v3.9.38 — DEV Lalu PERSIS 0 → tak perlu cari harga (mirror
        # hitung_nominal_pairs): Nominal Lalu 0.0 (bukan None → tak
        # dihitung 'tanpa pasangan/harga' di footer popup).
        if float(r["Qty Deviasi Lalu"]) == 0.0:
            harga_vals.append(None)
            nominal_vals.append(0.0)
            continue
        harga, _label, _bintang = lookup_harga_pair(
            harga_map, konversi_map, b, sat_file)
        if harga is not None:
            nominal_vals.append(harga * float(r["Qty Deviasi Lalu"]))
        else:
            nominal_vals.append(None)
        harga_vals.append(harga)
    out["Harga"] = pd.Series(harga_vals, dtype="float64")
    out["Nominal Lalu"] = pd.Series(nominal_vals, dtype="float64")

    out["_absnom"] = out["Nominal Lalu"].abs().fillna(0)
    out["_absqty"] = out["Qty Deviasi Lalu"].abs()
    out = (out.sort_values(["_absnom", "_absqty"],
                           ascending=[False, False],
                           kind="mergesort")
           .drop(columns=["_absnom", "_absqty"]))
    out = out.reset_index(drop=True)
    return out[_LALU_COLS]
