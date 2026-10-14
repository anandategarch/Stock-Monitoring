"""
nominal_common.py — v3.9.34 helper BERSAMA perhitungan Nominal Deviasi
(Harga 41.09 × Qty Deviasi). Sebelum v3.9.34 logika ini hanya hidup di
nominal_deviasi_view.py (mode 💰 Nominal (H)); kini dipakai 4 tempat:

  1. mode  💰 Nominal (H)        tab 📋 Laporan Deviasi (per pasangan)
  2. kolom Nominal               tab 📦 Deviasi GR & 🧩 Deviasi PCS
  3. kolom Nominal               mode ⚖ Komparasi (tab Laporan Deviasi —
                                  harga × GR Saat Ini)
  4. tab   🧮 Nominal Deviasi    (BARU — Σ per resto + popup rincian)

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

Qty Deviasi untuk pasangan = JENIS '3.DEVIASI' baris Tanggal H
(= SO − SALDO AKHIR sistem — nilai kolom Deviasi tab 📦 Deviasi GR).
"""

from __future__ import annotations

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
