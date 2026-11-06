"""
laporan_versus_view.py — Tab ⚖ Laporan Versus (v3.12.0).

USER: "yang komparasi laporan yang dua Resto — misalnya BKS gold sama
CGK Pak — itu kan ada di poin 13, dan poin 1 sampai poin 12 itu data
Resto itu sendiri atau resto se-areanya. Nah aku mau sekarang dari
poin 1 sampai poin 12 itu adalah LAPORAN VERSUS. Jadi ada dua mode:
poin 1 sampai 12-nya resto itu sendiri VERSUS area / VERSUS resto lain
yang banyak, dan mode satunya lagi satu resto VERSUS satu resto
lainnya."

Sumber data = FILE LAPORAN RESMI (file deviasi '{12+bulan}.{BULAN}
{TAHUN}.xlsx' — parser parse_deviasi_file; kolom baru v3.12.0: 12
ukuran QTY/NOMINAL lengkap + AREA + PENJUALAN + Akun). Struktur poin
MIRROR STRUKTUR KOLOM laporan resmi persis:

  Poin 1  · QTY BOM              Poin 8  · NOMINAL DEVIASI
  Poin 2  · QTY COM              Poin 9  · NOMINAL WASTE
  Poin 3  · QTY DEVIASI          Poin 10 · NOMINAL SUSUT
  Poin 4  · QTY WASTE            Poin 11 · NOMINAL TRIAL
  Poin 5  · QTY SUSUT            Poin 12 · NOMINAL LOSS/SURPLUS
  Poin 6  · QTY TRIAL
  Poin 7  · QTY LOSS SURPLUS
  Poin 13 · KOMPARASI DUA RESTO (A vs B — skor 12 ukuran nominal +
           PENJUALAN + rincian per bahan; pasangan bebas mode,
           contoh user: 1084.BKSGOL "BKS gold" vs 1137.CKGPAH
           "CGK Pak").

DUA MODE utk poin 1-12 (tabel per bahan — satuan SETIAP baris sama
utk kedua sisi; QTY antar-bahan TIDAK dijumlahkan karena satuan campur
GR/PCS/PACK/BOTOL — baris TOTAL bawah HANYA ukuran nominal Rp):
  Mode 1 — 🏆 vs Area / Banyak Resto:
      pembanding 'se-Area'   : Σ · rata-rata/resto · median resto
                                se-area (otomatis dari kolom AREA file
                                laporan — 'JAWA BARAT 1' dst);
      pembanding 'Semua Resto Lain': Σ · rata-rata/resto · median
                                semua resto ≠ fokus.
      Statistik grup per bahan dihitung atas resto yang MEMBAWA bahan
      itu saja (mirror semantik 'Beda dari Resto Lain' v3.11.59 —
      non-carrier tidak menyeret rata-rata).
  Mode 2 — 🆚 vs 1 Resto Lain: nilai resto fokus vs nilai resto
      pembanding per bahan + selisih + % ((A−B) ÷ |B| × 100 — mirror
      rumus Persen Kenaikan/Penurunan tab 🧮 Nominal Deviasi). Sisi
      tanpa baris bahan = 0 (resto tidak membawa bahan itu; tampil '-').

Minggu = cut-off laporan (WEEK 1/2/4 — snapshot kumulatif s/d H);
default minggu TERAKHIR. Bulan = bulan TERBARU dari file dimuat
(multi-bulan digabung app — _load_lalu_paths). PENJUALAN = kolom file
(kumulatif resto s/d minggu, konstan per resto × minggu).

Format angka identik era komparasi (fmt_nominal_cell: minus kurung;
fmt_rp_cell: Rp; fmt_pct_cell: '+12,5%'); minus merah per-cell
(Tk 9 tag cell; fallback Tk 8 baris); sort kolom klik judul;
💾 Export Excel (semua 13 poin + meta).
"""
from __future__ import annotations

import contextlib
import re
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk
from typing import ClassVar

import numpy as np
import pandas as pd

from .deviasi_file import bulan_label
from .nominal_common import (
    _norm_name_lalu,
    _norm_resto_lalu,
    fmt_nominal_cell,
    fmt_pct_cell,
    fmt_rp_cell,
    hitung_persen_kenaikan,
)
from .theme import C_BG, C_CARD, C_HEADER, C_TEXT_MUTED, font
from .widgets import (
    CELL_TAGS_SUPPORTED,
    AccentButton,
    Card,
    EmptyState,
    GhostButton,
    LoadingOverlay,
    apply_cell_tag,
    enable_col_resize,
    enable_multi_select,
    insert_tree_items,
    run_async,
    sort_tree_by_column,
)

# ---------------------------------------------------------------------------
# KONSTANTA POIN (mirror urutan kolom laporan resmi persis)
# ---------------------------------------------------------------------------
# (poin, label ukuran, kolom parse_deviasi_file, kind 'qty'|'rp')
POIN_MEASURES: tuple = (
    (1, "QTY BOM", "BOM Lalu", "qty"),
    (2, "QTY COM", "COM Lalu", "qty"),
    (3, "QTY DEVIASI", "DEV Lalu", "qty"),
    (4, "QTY WASTE", "QTY WASTE Lalu", "qty"),
    (5, "QTY SUSUT", "QTY SUSUT Lalu", "qty"),
    (6, "QTY TRIAL", "QTY TRIAL Lalu", "qty"),
    (7, "QTY LOSS SURPLUS", "QTY LOSS SURPLUS Lalu", "qty"),
    (8, "NOMINAL DEVIASI", "Nominal Deviasi Lalu", "rp"),
    (9, "NOMINAL WASTE", "NOMINAL WASTE Lalu", "rp"),
    (10, "NOMINAL SUSUT", "NOMINAL SUSUT Lalu", "rp"),
    (11, "NOMINAL TRIAL", "NOMINAL TRIAL Lalu", "rp"),
    (12, "NOMINAL LOSS/SURPLUS", "NOMINAL LOSS/SURPLUS Lalu", "rp"),
)

MODE_VS_GROUP = "group"     # Mode 1 — vs Area / Banyak Resto
MODE_VS_SATU = "satu"       # Mode 2 — 1 resto vs 1 resto
BASELINE_AREA = "area"      #   Mode 1a — se-Area (kolom AREA file)
BASELINE_LAIN = "lain"      #   Mode 1b — Semua Resto Lain

_TOT_TAG = "lv_total"       # baris TOTAL (tebal)
_NEG = "#dc2626"            # minus merah (konstanta tema view lain)


# ---------------------------------------------------------------------------
# FORMAT & helper kecil
# ---------------------------------------------------------------------------
def _fmt_ratio_pct(v) -> str:
    """Rasio (mis. %NomDev ÷ Penj): desimal koma 2 digit TANPA '+'
    (bukan delta — % delta ber-tanda pakai fmt_pct_cell)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "-"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if np.isinf(v) or pd.isna(v):
        return "-"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s + "%"


def _nz(v) -> float:
    """NaN/None → 0.0 (selisih sisi tanpa baris bahan = 0)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if pd.isna(f) else f


def _first_penjualan(dfw: pd.DataFrame, norm: str):
    """PENJUALAN resto (kumulatif s/d minggu) — konstan per resto×minggu;
    nilai non-NaN pertama baris resto itu."""
    if dfw is None or dfw.empty or not norm:
        return None
    sub = dfw[dfw["_resto_norm"] == norm]
    if sub.empty:
        return None
    vals = sub["PENJUALAN"].dropna() if "PENJUALAN" in sub.columns \
        else pd.Series(dtype=float)
    return float(vals.iloc[0]) if not vals.empty else None


def _ratio_pct(nom, penj):
    """(Nominal ÷ PENJUALAN) × 100 — None bila penj kosong/0/NaN."""
    if nom is None or pd.isna(nom) or penj is None or pd.isna(penj):
        return None
    if float(penj) == 0.0:
        return None
    return (float(nom) / float(penj)) * 100.0


def poin_table_spec(meta: dict, mode: str) -> tuple:
    """Header dinamis + urutan kolom tabel poin 1-12 — SATU SUMBER
    utk render UI + export Excel (mode 1: A/Σ/Rata-rata/Median; mode 2:
    A/B/Selisih)."""
    if mode == MODE_VS_SATU:
        heads = {"A": meta["a_label"], "B": meta["b_label"],
                 "Δ": "Selisih (A−B)", "%": "% (A−B)÷|B|"}
        show = ["Akun", "Nama Bahan", "Satuan", "A", "B", "Δ", "%"]
    else:
        gl = meta["group_label"].split(" · ")[0]
        heads = {"A": meta["a_label"], "Σ": f"Σ {gl}",
                 "Rata²": f"Rata-rata {gl}", "Med": f"Median {gl}",
                 "Δ": "Δ (A − Rata-rata)",
                 "%": "% (A−Rata-rata)÷|Rata-rata|"}
        show = ["Akun", "Nama Bahan", "Satuan", "A", "Σ", "Rata²",
                "Med", "Δ", "%"]
    return heads, show


# pemetaan kolom display → kolom raw numerik (payload *_raw — utk
# export Excel nilai mentah yang bisa dihitung, bukan string format)
RAW_COL_MAP = {"A": "A_raw", "B": "B_raw", "Σ": "Σ_raw",
               "Rata²": "Rata²_raw", "Med": "Med_raw", "Δ": "Δ_raw",
               "%": "pct_raw", "A QTY": "A QTY_raw", "B QTY": "B QTY_raw",
               "Δ QTY": "Δ QTY_raw", "A NOM": "A NOM_raw",
               "B NOM": "B NOM_raw", "Δ NOM": "Δ NOM_raw"}


# ---------------------------------------------------------------------------
# COMPUTE MURNI (tanpa Tk — dipanggil view di worker thread)
# ---------------------------------------------------------------------------
def compute_laporan_versus(df: pd.DataFrame | None, resto_a: str,
                           mode: str, baseline: str, resto_b: str,
                           minggu: str | None) -> dict:
    """Hitung SEMUA 13 poin sekaligus (payload di-cache view; ganti poin
    = render dari cache TANPA recompute; export memakai payload sama).

    df      : frame parse_deviasi_file (SEMUA bulan+minggu digabung app).
    resto_a : label RESTO mentah fokus (mis. '1084.BKSGOL').
    mode    : MODE_VS_GROUP | MODE_VS_SATU.
    baseline: BASELINE_AREA | BASELINE_LAIN (hanya mode group).
    resto_b : label RESTO pembanding (mode 2 + poin 13).
    minggu  : label 'WEEK n' (None → minggu TERAKHIR).

    Return {'ok', 'error', 'meta', 'poin': {1..12: df display},
    'poin13_score': df, 'poin13_bahan': df} — kolom display sudah
    string terformat; baris TOTAL paling bawah (poin 8-12 Rp +
    poin13 kolom Rp; sel TOTAL QTY = '-')."""
    empty = {"poin": {}, "poin13_score": None, "poin13_bahan": None}
    meta: dict = {"a_label": str(resto_a), "b_label": str(resto_b),
                  "mode": mode, "baseline": baseline, "minggu": "",
                  "minggu_h": None, "bulan_raw": "", "bulan_label": "",
                  "group_label": "", "area_a": "", "area_b": "",
                  "n_resto": 0, "n_bahan_a": 0, "n_bahan_b": 0,
                  "penjualan_a": None, "penjualan_b": None,
                  "minggu_values": [], "resto_values": []}
    if df is None or df.empty:
        return {"ok": False, "error": "Belum ada file laporan "
                "(file deviasi bulan lalu belum dimuat).", "meta": meta,
                **empty}
    need = {"_resto_norm", "Minggu", "_h", "_bulan_num"}
    if not need.issubset(set(df.columns)):
        return {"ok": False, "error": "Frame file laporan tidak dikenal "
                "(kolom parse hilang).", "meta": meta, **empty}
    d = df.copy()
    d["_bahan_norm"] = d["Nama Barang"].map(_norm_name_lalu)
    d["_resto_norm"] = d["Resto"].map(_norm_resto_lalu)

    # --- bulan terbaru (multi-bulan digabung app) -----------------------
    mnum = d["_bulan_num"].max()
    dfm = d[d["_bulan_num"] == mnum]
    _raws = [b for b in dfm["BULAN"].unique().tolist()
             if b and str(b).lower() != "nan"]
    bulan_raw = str(_raws[0]) if _raws else ""
    meta["bulan_raw"] = bulan_raw
    meta["bulan_label"] = bulan_label(bulan_raw) if bulan_raw else ""

    # --- minggu (cut-off laporan; default TERAKHIR) ----------------------
    wk = dfm.groupby("Minggu")["_h"].first().sort_values(ascending=True)
    meta["minggu_values"] = [(str(lbl), int(h)) for lbl, h in wk.items()]
    if wk.empty:
        return {"ok": False, "error": "File laporan tanpa minggu valid.",
                "meta": meta, **empty}
    if minggu is None or str(minggu) not in wk.index:
        minggu = str(wk.index[-1])
    minggu = str(minggu)
    dfw = dfm[dfm["Minggu"] == minggu].copy()
    if dfw.empty:
        return {"ok": False, "error": f"Tidak ada baris minggu {minggu}.",
                "meta": meta, **empty}
    meta["minggu"] = minggu
    try:
        meta["minggu_h"] = int(wk.get(minggu))
    except (TypeError, ValueError):
        meta["minggu_h"] = None

    # --- semesta resto + area + label display ---------------------------
    resto_values: list = []
    seen_norm: dict = {}
    for raw in dfw["Resto"].astype(str):
        nrm = _norm_resto_lalu(raw)
        if nrm and nrm not in seen_norm:
            seen_norm[nrm] = str(raw).strip()
    for nrm, raw in sorted(seen_norm.items(), key=lambda kv: kv[1]):
        resto_values.append((raw, nrm))
    meta["resto_values"] = resto_values
    meta["n_resto"] = len(resto_values)
    if "AREA" in dfm.columns:
        area_map = (dfm.drop_duplicates("_resto_norm")
                    .set_index("_resto_norm")["AREA"].astype(str)
                    .replace("nan", ""))
    else:   # frame lama tanpa kolom AREA (parser selalu menambah —
            # guard utk df eksternal/test): area tak dikenal → fallback
            # baseline 'Semua Resto Lain' di blok grup bawah.
        area_map = pd.Series(dtype=object)

    a_norm = _norm_resto_lalu(resto_a)
    b_norm = _norm_resto_lalu(resto_b)
    if a_norm not in seen_norm:
        return {"ok": False, "error": f"Resto fokus {resto_a!r} tidak "
                f"ada di data minggu {minggu}.", "meta": meta, **empty}
    meta["a_label"] = seen_norm.get(a_norm, str(resto_a))
    meta["b_label"] = seen_norm.get(b_norm, str(resto_b))
    meta["area_a"] = str(area_map.get(a_norm, ""))
    meta["area_b"] = str(area_map.get(b_norm, ""))
    # --- 12 ukuran wajib ADA sebelum slicing (file lama tanpa kolom
    #     opsional → NaN; assign SEKALI di sini supaya a_rows/b_rows/
    #     sub_g (slice di BAWAH) tidak kehilangan kolom)
    for _num, _label, _col, _kind in POIN_MEASURES:
        if _col not in dfw.columns:
            dfw = dfw.assign(**{_col: np.nan})
    if "PENJUALAN" not in dfw.columns:
        dfw = dfw.assign(PENJUALAN=np.nan)

    meta["penjualan_a"] = _first_penjualan(dfw, a_norm)
    meta["penjualan_b"] = _first_penjualan(dfw, b_norm)
    a_rows = dfw[dfw["_resto_norm"] == a_norm]
    b_rows = dfw[dfw["_resto_norm"] == b_norm]
    meta["n_bahan_a"] = int(a_rows["_bahan_norm"].nunique())
    meta["n_bahan_b"] = int(b_rows["_bahan_norm"].nunique())

    # --- definisi grup pembanding ---------------------------------------
    if mode == MODE_VS_SATU:
        group_norms = [b_norm] if b_norm in seen_norm else []
        group_label = meta["b_label"]
    else:
        area_a = meta["area_a"]
        if baseline == BASELINE_AREA and area_a:
            group_norms = [r for r in seen_norm
                           if str(area_map.get(r, "")) == area_a]
            group_label = f"se-Area {area_a}"
        else:
            group_norms = [r for r in seen_norm if r != a_norm]
            group_label = "Semua Resto Lain"
    meta["group_label"] = (f"{group_label} · {len(group_norms)} resto"
                           if group_norms else group_label)
    sub_g = (dfw[dfw["_resto_norm"].isin(group_norms)]
             if group_norms else dfw.iloc[0:0])

    # display bahan: nama mentah + satuan + akun (prioritas baris fokus);
    # kolom opsional (Akun) boleh absen di frame eksternal — guard.
    _disp_cols = [c for c in ("Nama Barang", "Satuan", "Akun")
                  if c in dfw.columns]
    disp = (pd.concat([a_rows, b_rows, sub_g, dfw])
            .drop_duplicates("_bahan_norm")
            .set_index("_bahan_norm")[_disp_cols])

    # --- POIN 1-12: tabel per bahan per ukuran ---------------------------
    poin: dict = {}
    for num, label, col, kind in POIN_MEASURES:
        a_val = a_rows.groupby("_bahan_norm")[col].sum()
        if mode == MODE_VS_SATU:
            b_val = b_rows.groupby("_bahan_norm")[col].sum()
            g_sum = g_mean = g_med = None
        else:
            per = sub_g.groupby(["_bahan_norm", "_resto_norm"])[col].sum()
            g_sum = per.groupby("_bahan_norm").sum()
            g_mean = per.groupby("_bahan_norm").mean()
            g_med = per.groupby("_bahan_norm").median()
            b_val = None
        idx = set(a_val.index) | set(
            b_val.index if b_val is not None else
            (g_sum.index if g_sum is not None else set()))
        # urutan default: |nilai fokus| menurun
        idx = sorted(idx, key=lambda b: -_nz(a_val.get(b, np.nan)))
        rows = []
        for bhn in idx:
            info = disp.loc[bhn] if bhn in disp.index else None
            nama = str(info.get("Nama Barang", bhn)) if info is not None else bhn
            sat = str(info.get("Satuan", "-")) if info is not None else "-"
            ak = str(info.get("Akun", "-")) if info is not None else "-"
            av = _nz(a_val.get(bhn, np.nan))
            if mode == MODE_VS_SATU:
                bv = _nz(b_val.get(bhn, np.nan))
                rows.append({
                    "Akun": ak, "Nama Bahan": nama, "Satuan": sat,
                    "A": fmt_nominal_cell(av or np.nan),
                    "B": fmt_nominal_cell(bv or np.nan),
                    "Δ": fmt_nominal_cell((av - bv) or np.nan),
                    "%": fmt_pct_cell(hitung_persen_kenaikan(
                        av or np.nan, bv or np.nan)),
                    "A_raw": av or np.nan, "B_raw": bv or np.nan,
                    "Δ_raw": av - bv,
                    "pct_raw": hitung_persen_kenaikan(
                        av or np.nan, bv or np.nan)})
            else:
                gs = g_sum.get(bhn, np.nan) if g_sum is not None else np.nan
                gm = g_mean.get(bhn, np.nan) if g_mean is not None else np.nan
                gd = g_med.get(bhn, np.nan) if g_med is not None else np.nan
                rows.append({
                    "Akun": ak, "Nama Bahan": nama, "Satuan": sat,
                    "A": fmt_nominal_cell(av or np.nan),
                    "Σ": fmt_nominal_cell(gs),
                    "Rata²": fmt_nominal_cell(gm),
                    "Med": fmt_nominal_cell(gd),
                    "Δ": fmt_nominal_cell((av - _nz(gm)) or np.nan),
                    "%": fmt_pct_cell(hitung_persen_kenaikan(
                        av or np.nan, gm)),
                    "A_raw": av or np.nan, "Σ_raw": gs,
                    "Rata²_raw": gm, "Med_raw": gd,
                    "Δ_raw": av - _nz(gm),
                    "pct_raw": hitung_persen_kenaikan(
                        av or np.nan, gm)})
        # TOTAL — hanya ukuran nominal Rp (QTY antar-bahan satuan campur)
        if kind == "rp" and rows:
            a_tot = _nz(a_rows[col].sum())
            if mode == MODE_VS_SATU:
                b_tot = _nz(b_rows[col].sum())
                tot = {"Akun": "", "Nama Bahan": "TOTAL", "Satuan": "",
                       "A": fmt_rp_cell(a_tot or np.nan),
                       "B": fmt_rp_cell(b_tot or np.nan),
                       "Δ": fmt_rp_cell((a_tot - b_tot) or np.nan),
                       "%": fmt_pct_cell(hitung_persen_kenaikan(
                           a_tot or np.nan, b_tot or np.nan)),
                       "A_raw": a_tot or np.nan, "B_raw": b_tot or np.nan,
                       "Δ_raw": a_tot - b_tot,
                       "pct_raw": hitung_persen_kenaikan(
                           a_tot or np.nan, b_tot or np.nan),
                       "_total": True}
            else:
                per = sub_g.groupby(["_bahan_norm", "_resto_norm"])[col].sum()
                per_resto = per.groupby("_resto_norm").sum()
                gs_tot = _nz(per.sum())
                gm_tot = _nz(per_resto.mean()) if len(per_resto) else 0.0
                tot = {"Akun": "", "Nama Bahan": "TOTAL", "Satuan": "",
                       "A": fmt_rp_cell(a_tot or np.nan),
                       "Σ": fmt_rp_cell(gs_tot or np.nan),
                       "Rata²": fmt_rp_cell(gm_tot or np.nan),
                       "Med": "",
                       "Δ": fmt_rp_cell((a_tot - gm_tot) or np.nan),
                       "%": fmt_pct_cell(hitung_persen_kenaikan(
                           a_tot or np.nan, gm_tot or np.nan)),
                       "A_raw": a_tot or np.nan, "Σ_raw": gs_tot or np.nan,
                       "Rata²_raw": gm_tot or np.nan, "Med_raw": np.nan,
                       "Δ_raw": a_tot - gm_tot,
                       "pct_raw": hitung_persen_kenaikan(
                           a_tot or np.nan, gm_tot or np.nan),
                       "_total": True}
            rows.append(tot)
        poin[num] = pd.DataFrame(rows)

    # --- POIN 13a: skor ringkasan (nominal Rp + penjualan) ---------------
    score_rows = []
    for num, label, col, kind in POIN_MEASURES:
        if kind != "rp" or col not in dfw.columns:
            continue
        a_tot = _nz(a_rows[col].sum())
        b_tot = _nz(b_rows[col].sum())
        score_rows.append({
            "Ukuran": f"Poin {num} · {label}",
            "A": fmt_rp_cell(a_tot or np.nan),
            "B": fmt_rp_cell(b_tot or np.nan),
            "Δ": fmt_rp_cell((a_tot - b_tot) or np.nan),
            "%": fmt_pct_cell(hitung_persen_kenaikan(
                a_tot or np.nan, b_tot or np.nan)),
            "A_raw": a_tot or np.nan, "B_raw": b_tot or np.nan,
            "Δ_raw": a_tot - b_tot,
            "pct_raw": hitung_persen_kenaikan(
                a_tot or np.nan, b_tot or np.nan)})
    pa, pb = meta["penjualan_a"], meta["penjualan_b"]
    score_rows.append({
        "Ukuran": "PENJUALAN (s/d minggu)",
        "A": fmt_rp_cell(pa), "B": fmt_rp_cell(pb),
        "Δ": fmt_rp_cell((pa - pb) if pa is not None and pb is not None
                         else np.nan),
        "%": fmt_pct_cell(hitung_persen_kenaikan(pa, pb)),
        "A_raw": pa if pa is not None else np.nan,
        "B_raw": pb if pb is not None else np.nan,
        "Δ_raw": (pa - pb) if pa is not None and pb is not None else np.nan,
        "pct_raw": hitung_persen_kenaikan(pa, pb)})
    nom_a = _nz(a_rows["Nominal Deviasi Lalu"].sum()) \
        if "Nominal Deviasi Lalu" in a_rows.columns else 0.0
    nom_b = _nz(b_rows["Nominal Deviasi Lalu"].sum()) \
        if "Nominal Deviasi Lalu" in b_rows.columns else 0.0
    ra, rb = _ratio_pct(nom_a, pa), _ratio_pct(nom_b, pb)
    score_rows.append({
        "Ukuran": "% NOM DEVIASI ÷ PENJUALAN",
        "A": _fmt_ratio_pct(ra), "B": _fmt_ratio_pct(rb),
        "Δ": _fmt_ratio_pct(
            (ra - rb) if ra is not None and rb is not None else None),
        "%": "-",
        "A_raw": (ra / 100.0) if ra is not None else np.nan,
        "B_raw": (rb / 100.0) if rb is not None else np.nan,
        "Δ_raw": ((ra - rb) / 100.0)
        if ra is not None and rb is not None else np.nan,
        "pct_raw": np.nan})
    poin13_score = pd.DataFrame(score_rows)

    # --- POIN 13b: rincian per bahan (QTY + NOMINAL DEVIASI) -------------
    aq = a_rows.groupby("_bahan_norm")["DEV Lalu"].sum()
    bq = b_rows.groupby("_bahan_norm")["DEV Lalu"].sum()
    an = a_rows.groupby("_bahan_norm")["Nominal Deviasi Lalu"].sum()
    bn = b_rows.groupby("_bahan_norm")["Nominal Deviasi Lalu"].sum()
    idx13 = set(aq.index) | set(bq.index)
    idx13 = sorted(idx13, key=lambda b: -abs(
        _nz(an.get(b, np.nan)) - _nz(bn.get(b, np.nan))))
    rows13 = []
    for bhn in idx13:
        info = disp.loc[bhn] if bhn in disp.index else None
        nama = str(info.get("Nama Barang", bhn)) if info is not None else bhn
        sat = str(info.get("Satuan", "-")) if info is not None else "-"
        ak = str(info.get("Akun", "-")) if info is not None else "-"
        av, bv = _nz(aq.get(bhn, np.nan)), _nz(bq.get(bhn, np.nan))
        nv, mv = _nz(an.get(bhn, np.nan)), _nz(bn.get(bhn, np.nan))
        rows13.append({
            "Akun": ak, "Nama Bahan": nama, "Satuan": sat,
            "A QTY": fmt_nominal_cell(av or np.nan),
            "B QTY": fmt_nominal_cell(bv or np.nan),
            "Δ QTY": fmt_nominal_cell((av - bv) or np.nan),
            "A NOM": fmt_rp_cell(nv or np.nan),
            "B NOM": fmt_rp_cell(mv or np.nan),
            "Δ NOM": fmt_rp_cell((nv - mv) or np.nan),
            "%": fmt_pct_cell(hitung_persen_kenaikan(
                nv or np.nan, mv or np.nan)),
            "A QTY_raw": av or np.nan, "B QTY_raw": bv or np.nan,
            "Δ QTY_raw": av - bv,
            "A NOM_raw": nv or np.nan, "B NOM_raw": mv or np.nan,
            "Δ NOM_raw": nv - mv,
            "pct_raw": hitung_persen_kenaikan(nv or np.nan, mv or np.nan)})
    if rows13:
        an_t, bn_t = _nz(an.sum()), _nz(bn.sum())
        rows13.append({
            "Akun": "", "Nama Bahan": "TOTAL", "Satuan": "",
            "A QTY": "-", "B QTY": "-", "Δ QTY": "-",
            "A NOM": fmt_rp_cell(an_t or np.nan),
            "B NOM": fmt_rp_cell(bn_t or np.nan),
            "Δ NOM": fmt_rp_cell((an_t - bn_t) or np.nan),
            "%": fmt_pct_cell(hitung_persen_kenaikan(
                an_t or np.nan, bn_t or np.nan)),
            "A QTY_raw": np.nan, "B QTY_raw": np.nan,
            "Δ QTY_raw": np.nan,
            "A NOM_raw": an_t or np.nan, "B NOM_raw": bn_t or np.nan,
            "Δ NOM_raw": an_t - bn_t,
            "pct_raw": hitung_persen_kenaikan(
                an_t or np.nan, bn_t or np.nan), "_total": True})
    poin13_bahan = pd.DataFrame(rows13)

    return {"ok": True, "error": None, "meta": meta, "poin": poin,
            "poin13_score": poin13_score,
            "poin13_bahan": poin13_bahan}


# ---------------------------------------------------------------------------
# VIEW
# ---------------------------------------------------------------------------
class LaporanVersusView(tk.Frame):
    """Tab ⚖ Laporan Versus — 13 poin laporan resmi format versus
    (2 mode) — data file laporan resmi bulan lalu (app _lalu_file_df
    via lalu_provider; ganti file → app panggil on_lalu_file_changed)."""

    MODE_LABELS: ClassVar[dict] = {
        MODE_VS_GROUP: "Mode 1 — 🏆 vs Area / Banyak Resto",
        MODE_VS_SATU: "Mode 2 — 🆚 vs 1 Resto Lain (1v1)",
    }
    BASELINE_LABELS: ClassVar[dict] = {
        BASELINE_AREA: "se-Area (otomatis)",
        BASELINE_LAIN: "Semua Resto Lain",
    }
    POIN13_LABEL = "Poin 13 · Komparasi Dua Resto"

    def __init__(self, parent, go_to_config: Callable | None = None,
                 lalu_provider: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self._lalu_provider = lalu_provider
        self._go_to_config = go_to_config
        # state pilihan (label mentah file)
        self._resto_a = ""
        self._resto_b = ""
        self._mode = MODE_VS_GROUP
        self._baseline = BASELINE_AREA
        self._minggu: str | None = None
        self._poin = 13
        # cache
        self._payload: dict | None = None
        self._src_identity: int | None = None
        self._busy = False
        self._pending = False
        self._dirty = False
        self._neg_cells: dict = {}   # tree → [(iid, col), ...]
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # --- kartu kontrol --------------------------------------------
        ctrl = Card(self, title="⚖ Laporan Versus",
                    subtitle="Poin 1-12 laporan resmi dalam format versus "
                             "· Poin 13 = komparasi dua resto · sumber: "
                             "file laporan resmi (file deviasi)")
        ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        body = ctrl.body()

        r1 = tk.Frame(body, bg=C_CARD)
        r1.pack(fill="x")

        def _lbl(parent, text):
            tk.Label(parent, text=text, bg=C_CARD, fg=C_TEXT_MUTED,
                     font=font(9)).pack(side="left", padx=(12, 3))

        # Resto Fokus
        f_a = tk.Frame(r1, bg=C_CARD)
        f_a.pack(side="left")
        _lbl(f_a, "Resto Fokus")
        self._lbl_a_head = tk.Label(f_a, text="", bg=C_CARD,
                                    fg=C_HEADER, font=font(9, "bold"))
        self._lbl_a_head.pack(side="left")
        self._combo_a = ttk.Combobox(f_a, width=17, state="readonly")
        self._combo_a.pack(side="left")
        self._combo_a.bind("<<ComboboxSelected>>", self._on_pick_a)

        # Mode
        f_m = tk.Frame(r1, bg=C_CARD)
        f_m.pack(side="left")
        _lbl(f_m, "Mode")
        self._combo_mode = ttk.Combobox(f_m, width=30, state="readonly")
        self._combo_mode.pack(side="left")
        self._combo_mode.bind("<<ComboboxSelected>>", self._on_pick_mode)

        # Pembanding (slot ganda: mode 1 = grup, mode 2 = resto B)
        f_b = tk.Frame(r1, bg=C_CARD)
        f_b.pack(side="left")
        self._lbl_b = tk.Label(f_b, text="Pembanding:", bg=C_CARD,
                               fg=C_TEXT_MUTED, font=font(9))
        self._lbl_b.pack(side="left", padx=(12, 3))
        self._combo_base = ttk.Combobox(f_b, width=22, state="readonly")
        self._combo_base.bind("<<ComboboxSelected>>", self._on_pick_base)
        self._combo_b = ttk.Combobox(f_b, width=17, state="readonly")
        self._combo_b.bind("<<ComboboxSelected>>", self._on_pick_b)

        # Minggu
        f_w = tk.Frame(r1, bg=C_CARD)
        f_w.pack(side="left")
        _lbl(f_w, "Minggu")
        self._combo_w = ttk.Combobox(f_w, width=14, state="readonly")
        self._combo_w.pack(side="left")
        self._combo_w.bind("<<ComboboxSelected>>", self._on_pick_w)

        # Poin
        f_p = tk.Frame(r1, bg=C_CARD)
        f_p.pack(side="left")
        _lbl(f_p, "Poin")
        self._combo_p = ttk.Combobox(f_p, width=30, state="readonly")
        self._combo_p.pack(side="left")
        self._combo_p.bind("<<ComboboxSelected>>", self._on_pick_poin)
        self._combo_p.configure(values=self._poin_values())
        self._combo_p.set(self.POIN13_LABEL)

        r2 = tk.Frame(body, bg=C_CARD)
        r2.pack(fill="x", pady=(6, 0))
        GhostButton(r2, text="↻ Segarkan",
                    command=self.refresh).pack(side="left")
        AccentButton(r2, text="💾 Export Excel (13 poin)",
                     command=self._export_excel).pack(side="left",
                                                     padx=(6, 0))
        self._file_var = tk.StringVar(value="")
        tk.Label(r2, textvariable=self._file_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9), anchor="w",
                 justify="left").pack(side="left", padx=(10, 0),
                                      fill="x", expand=True)

        # --- konten: empty state / kartu poin -------------------------
        self._empty = EmptyState(
            self, title="Belum ada file laporan",
            subtitle="Muat file laporan resmi (file deviasi bulan lalu) "
                     "lewat tab ⚙️ Config → 📂 Muat Sekarang.",
            cta_text="Buka Tab Config",
            on_cta=self._go_to_config if self._go_to_config else None)
        self._empty.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        self._card_poin = Card(self, padding=10)
        self._build_poin_card(self._card_poin)
        self._card_p13 = Card(self, padding=10)
        self._build_p13_card(self._card_p13)

        self.overlay = LoadingOverlay(self, "Menghitung laporan versus…")
        self._sync_pembanding_ui()

    def _build_poin_card(self, card: Card):
        body = card.body()
        self._poin_title_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._poin_title_var, bg=C_CARD,
                 fg=C_HEADER, font=font(11, "bold")).pack(anchor="w")
        self._poin_note_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._poin_note_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9)).pack(anchor="w")
        tbody = tk.Frame(body, bg=C_CARD)
        tbody.pack(fill="both", expand=True, pady=(6, 0))
        tbody.grid_rowconfigure(0, weight=1)
        tbody.grid_columnconfigure(0, weight=1)
        cols = ["Akun", "Nama Bahan", "Satuan", "A", "B", "Σ", "Rata²",
                "Med", "Δ", "%"]
        self.tree = ttk.Treeview(tbody, columns=cols, show="headings",
                                 selectmode="extended")
        for c in cols:
            self.tree.column(c, width=110, minwidth=40, anchor="e")
            self.tree.heading(c, text=c,
                              command=lambda cc=c: self._sort(self.tree,
                                                             cc))
        self.tree.column("Nama Bahan", anchor="w", width=210)
        self.tree.column("Akun", anchor="w", width=150)
        self.tree.column("Satuan", anchor="w", width=56)
        vsb = ttk.Scrollbar(tbody, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                             xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        enable_col_resize(self.tree)
        enable_multi_select(self.tree)
        self.tree.tag_configure("evenrow", background="#f8fafc")
        self.tree.tag_configure(_TOT_TAG, font=font(9, "bold"))
        foot = tk.Frame(body, bg=C_CARD)
        foot.pack(fill="x", pady=(6, 0))
        self._poin_status_var = tk.StringVar(value="")
        tk.Label(foot, textvariable=self._poin_status_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9)).pack(side="left")

    def _build_p13_card(self, card: Card):
        body = card.body()
        self._p13_title_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._p13_title_var, bg=C_CARD,
                 fg=C_HEADER, font=font(11, "bold")).pack(anchor="w")
        self._p13_note_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._p13_note_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9)).pack(anchor="w")

        tk.Label(body, text="Skor ringkasan (ukuran nominal Rp + "
                 "penjualan — QTY per bahan: buka Poin 1-7)",
                 bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(9, "bold")).pack(anchor="w", pady=(8, 0))
        t13a = tk.Frame(body, bg=C_CARD)
        t13a.pack(fill="x")
        cols = ["Ukuran", "A", "B", "Δ", "%"]
        self.tree13a = ttk.Treeview(t13a, columns=cols, show="headings",
                                    height=9)
        for c in cols:
            self.tree13a.column(c, width=150, minwidth=60, anchor="e")
            self.tree13a.heading(c, text=c,
                                 command=lambda cc=c: self._sort(
                                     self.tree13a, cc))
        self.tree13a.column("Ukuran", anchor="w", width=240)
        self.tree13a.pack(side="left", fill="both", expand=True)
        enable_col_resize(self.tree13a)
        self.tree13a.tag_configure("evenrow", background="#f8fafc")

        tk.Label(body, text="Rincian per bahan (QTY & NOMINAL DEVIASI — "
                 "urut |Δ NOM| menurun)", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(9, "bold")).pack(anchor="w", pady=(10, 0))
        t13b = tk.Frame(body, bg=C_CARD)
        t13b.pack(fill="both", expand=True)
        t13b.grid_rowconfigure(0, weight=1)
        t13b.grid_columnconfigure(0, weight=1)
        cols = ["Akun", "Nama Bahan", "Satuan", "A QTY", "B QTY",
                "Δ QTY", "A NOM", "B NOM", "Δ NOM", "%"]
        self.tree13b = ttk.Treeview(t13b, columns=cols, show="headings",
                                    selectmode="extended")
        for c in cols:
            self.tree13b.column(c, width=110, minwidth=40, anchor="e")
            self.tree13b.heading(c, text=c,
                                 command=lambda cc=c: self._sort(
                                     self.tree13b, cc))
        self.tree13b.column("Nama Bahan", anchor="w", width=210)
        self.tree13b.column("Akun", anchor="w", width=150)
        self.tree13b.column("Satuan", anchor="w", width=56)
        vsb = ttk.Scrollbar(t13b, orient="vertical",
                            command=self.tree13b.yview)
        hsb = ttk.Scrollbar(t13b, orient="horizontal",
                            command=self.tree13b.xview)
        self.tree13b.configure(yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set)
        self.tree13b.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        enable_col_resize(self.tree13b)
        enable_multi_select(self.tree13b)
        self.tree13b.tag_configure("evenrow", background="#f8fafc")
        self.tree13b.tag_configure(_TOT_TAG, font=font(9, "bold"))
        foot = tk.Frame(body, bg=C_CARD)
        foot.pack(fill="x", pady=(6, 0))
        self._p13_status_var = tk.StringVar(value="")
        tk.Label(foot, textvariable=self._p13_status_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9)).pack(side="left")

    # ------------------------------------------------------------------
    # handler kontrol
    # ------------------------------------------------------------------
    def _on_pick_a(self, _e=None):
        self._resto_a = self._combo_a.get().strip()
        if self._resto_b == self._resto_a:
            vals = [v for v in self._combo_b.cget("values")
                    if str(v) != self._resto_a]
            if vals:
                self._resto_b = str(vals[0])
                self._combo_b.set(self._resto_b)
        self.refresh()

    def _on_pick_b(self, _e=None):
        self._resto_b = self._combo_b.get().strip()
        self.refresh()

    def _on_pick_mode(self, _e=None):
        txt = self._combo_mode.get()
        self._mode = (MODE_VS_SATU
                      if txt == self.MODE_LABELS[MODE_VS_SATU]
                      else MODE_VS_GROUP)
        self._sync_pembanding_ui()
        self.refresh()

    def _on_pick_base(self, _e=None):
        txt = self._combo_base.get()
        self._baseline = (BASELINE_LAIN
                           if txt == self.BASELINE_LABELS[BASELINE_LAIN]
                           else BASELINE_AREA)
        self.refresh()

    def _on_pick_w(self, _e=None):
        m = re.match(r"^(.*?)\s*\(H=", self._combo_w.get().strip())
        self._minggu = m.group(1).strip() if m else None
        self.refresh()

    def _on_pick_poin(self, _e=None):
        txt = self._combo_p.get()
        m = re.match(r"^Poin (\d+)", txt)
        n = int(m.group(1)) if m else 13
        self._poin = n if 1 <= n <= 13 else 13
        # ganti poin TIDAK recompute — render dari cache (payload basi
        # bila file berganti → _payload None → jalur refresh penuh)
        if self._payload is not None and self._payload.get("ok"):
            self._render()
        else:
            self.refresh()

    def _sync_pembanding_ui(self):
        """Slot pembanding: mode 1 → combo grup (se-Area/Semua Resto
        Lain); mode 2 → combo resto pembanding (Poin 13 & poin 1-12)."""
        if self._mode == MODE_VS_SATU:
            self._combo_base.pack_forget()
            self._lbl_b.configure(text="Resto Pembanding:")
            if not self._combo_b.winfo_ismapped():
                self._combo_b.pack(side="left")
        else:
            self._combo_b.pack_forget()
            self._lbl_b.configure(text="Pembanding:")
            if not self._combo_base.winfo_ismapped():
                self._combo_base.pack(side="left")

    # ------------------------------------------------------------------
    # refresh plumbing (pola nominal_resto_view)
    # ------------------------------------------------------------------
    def refresh(self):
        """Tombol ↻ / perubahan kontrol / on_lalu_file_changed."""
        if self._busy:
            self._pending = True
            return
        if not self.winfo_ismapped():
            self._dirty = True
            return
        self._do_refresh()

    def ensure_refreshed(self):
        """Lazy refresh (v3.2): compute hanya saat tab ini terlihat."""
        if self._dirty:
            self._dirty = False
            self._do_refresh()

    def on_lalu_file_changed(self):
        """File laporan berganti (app _notify_lalu_consumers) → payload
        cache basi; refresh bila terlihat, dirty bila tersembunyi."""
        self._payload = None
        self._src_identity = None
        self.refresh()

    def _do_refresh(self):
        """Selalu RECOMPUTE (mode/resto/minggu/baseline bisa berubah);
        ganti poin TIDAK lewat sini (lihat _on_pick_poin — render cache)."""
        df = (self._lalu_provider() if self._lalu_provider is not None
              else None)
        self._ensure_selections(df)
        self._compute_async(df)

    def _compute_async(self, df):
        a, b, mode, baseline = self._resto_a, self._resto_b, \
            self._mode, self._baseline
        minggu = self._minggu

        def work():
            return compute_laporan_versus(df, a, mode, baseline, b,
                                          minggu)

        def done(payload):
            self._busy = False
            if self._pending:
                self._pending = False
                self._do_refresh()
                return
            self._payload = payload
            self._src_identity = None if df is None else id(df)
            self._render()

        def on_error(err):
            self._busy = False
            with contextlib.suppress(tk.TclError):
                messagebox.showerror("Laporan Versus",
                                     f"Gagal menghitung: {err}")

        self._busy = True
        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung laporan versus…",
                  on_error=on_error)

    def _ensure_selections(self, df):
        """Isi combobox dari data (idempoten — dipanggil tiap refresh);
        pertahankan pilihan lama bila masih valid."""
        if df is None or df.empty:
            return
        if not {"_resto_norm", "Minggu", "_bulan_num"}.issubset(
                set(df.columns)):
            return
        d = df
        dfm = d[d["_bulan_num"] == d["_bulan_num"].max()]
        wk = dfm.groupby("Minggu")["_h"].first().sort_values()

        vals, seen = [], set()
        for raw in dfm["Resto"].astype(str):
            nrm = _norm_resto_lalu(raw)
            if nrm and nrm not in seen:
                seen.add(nrm)
                vals.append(str(raw).strip())
        vals = sorted(set(vals))
        if not vals:
            return
        self._combo_a.configure(values=vals)
        self._combo_b.configure(values=[v for v in vals
                                         if v != self._resto_a])
        if not self._resto_a or self._resto_a not in vals:
            self._resto_a = vals[0]
        if (not self._resto_b or self._resto_b not in vals
                or self._resto_b == self._resto_a):
            rest = [v for v in vals if v != self._resto_a]
            self._resto_b = rest[0] if rest else ""
        self._combo_a.set(self._resto_a)
        self._combo_b.set(self._resto_b)
        self._lbl_a_head.configure(
            text=f"({(self._resto_a.split('.')[-1] or '-').strip()})")
        # mode & pembanding grup
        self._combo_mode.configure(
            values=list(self.MODE_LABELS.values()))
        self._combo_mode.set(self.MODE_LABELS[self._mode])
        self._combo_base.configure(
            values=list(self.BASELINE_LABELS.values()))
        self._combo_base.set(self.BASELINE_LABELS[self._baseline])
        # minggu
        if self._minggu not in wk.index:
            self._minggu = str(wk.index[-1]) if len(wk) else None
        self._combo_w.configure(values=[
            f"{lbl} (H={int(h)})" for lbl, h in wk.items()])
        try:
            h = int(wk.get(self._minggu))
        except (TypeError, ValueError):
            h = 0
        self._combo_w.set(f"{self._minggu} (H={h})")
        # poin
        self._combo_p.configure(values=self._poin_values())
        self._combo_p.set(self._poin_label(self._poin))

    def _poin_values(self) -> list:
        return [self._poin_label(n) for n, _l, _c, _k in POIN_MEASURES] \
            + [self.POIN13_LABEL]

    def _poin_label(self, n: int) -> str:
        for num, label, _c, _k in POIN_MEASURES:
            if num == n:
                return f"Poin {num} · {label}"
        return self.POIN13_LABEL

    # ------------------------------------------------------------------
    # RENDER
    # ------------------------------------------------------------------
    def _render(self):
        p = self._payload
        if p is None or not p.get("ok"):
            err = (p or {}).get("error") or "Belum ada file laporan."
            self._card_poin.grid_forget()
            self._card_p13.grid_forget()
            self._empty.grid()
            self._file_var.set(f"⚠ {err}")
            return
        self._empty.grid_forget()
        meta = p["meta"]
        if self._mode == MODE_VS_SATU:
            grp = f"1v1 · {meta['a_label']} vs {meta['b_label']}"
        else:
            grp = meta["group_label"]
        self._file_var.set(
            f"📄 {meta['bulan_raw'] or '-'} · {meta['minggu']} "
            f"(H={meta['minggu_h'] or '-'}) · {meta['n_resto']} resto · "
            f"{grp}")
        if self._poin == 13:
            self._card_poin.grid_forget()
            self._card_p13.grid(row=2, column=0, sticky="nsew",
                                padx=10, pady=10)
            self._render_p13(p)
        else:
            self._card_p13.grid_forget()
            self._card_poin.grid(row=2, column=0, sticky="nsew",
                                 padx=10, pady=10)
            self._render_poin(p)

    def _render_poin(self, p):
        meta = p["meta"]
        num = self._poin
        dfp = p["poin"].get(num, pd.DataFrame())
        kind = "rp" if num >= 8 else "qty"
        all_cols = ["Akun", "Nama Bahan", "Satuan", "A", "B", "Σ",
                    "Rata²", "Med", "Δ", "%"]
        heads, show = poin_table_spec(meta, self._mode)
        if self._mode == MODE_VS_SATU:
            note = (f"{meta['a_label']} ({meta['area_a'] or '-'}) vs "
                    f"{meta['b_label']} ({meta['area_b'] or '-'}) · "
                    f"{meta['n_bahan_a']} vs {meta['n_bahan_b']} bahan · "
                    "per bahan (satuan baris sama kedua sisi)")
        else:
            note = (f"{meta['a_label']} ({meta['area_a'] or '-'}) vs "
                    f"{meta['group_label']} — per bahan")
        self._poin_title_var.set(
            f"{self._poin_label(num)} — "
            f"{'NOMINAL (Rp)' if kind == 'rp' else 'QTY'} · "
            f"minggu {meta['minggu']} · {meta['bulan_raw']}")
        self._poin_note_var.set(note)
        for c in ["A", "B", "Σ", "Rata²", "Med", "Δ", "%"]:
            with contextlib.suppress(tk.TclError):
                self.tree.heading(c, text=heads.get(c, c))
        with contextlib.suppress(tk.TclError):
            self.tree.configure(
                displaycolumns=[c for c in all_cols if c in show])
        self._fill_tree(self.tree, dfp, show)
        tot_txt = ""
        if not dfp.empty:
            mask = (dfp["Nama Bahan"] == "TOTAL") if "Nama Bahan" in dfp \
                else pd.Series(dtype=bool)
            if mask.any():
                trow = dfp[mask].iloc[0]
                side = ("B " + str(trow.get("B", "-"))
                        if self._mode == MODE_VS_SATU
                        else "Σ " + str(trow.get("Σ", "-")))
                tot_txt = f"TOTAL — A {trow.get('A', '-')} · {side}"
        self._poin_status_var.set(
            (tot_txt + " · " if tot_txt else "")
            + ("Total antar-bahan hanya ukuran nominal Rp "
               "(QTY satuan campur tidak dijumlahkan)" if kind == "rp"
               else "QTY antar-bahan tidak dijumlahkan "
                    "(satuan campur GR/PCS/PACK/BOTOL)"))

    def _render_p13(self, p):
        meta = p["meta"]
        self._p13_title_var.set(
            f"Poin 13 · Komparasi Dua Resto — {meta['a_label']} "
            f"({meta['area_a'] or '-'}) vs {meta['b_label']} "
            f"({meta['area_b'] or '-'}) · minggu {meta['minggu']} · "
            f"{meta['bulan_raw']}")
        pa = fmt_rp_cell(meta["penjualan_a"])
        pb = fmt_rp_cell(meta["penjualan_b"])
        ra_txt = rb_txt = "-"
        if p["poin13_score"] is not None:
            hit = p["poin13_score"]
            sel = hit[hit["Ukuran"] == "% NOM DEVIASI ÷ PENJUALAN"]
            if not sel.empty:
                ra_txt, rb_txt = sel.iloc[0]["A"], sel.iloc[0]["B"]
        self._p13_note_var.set(
            f"PENJUALAN s/d minggu: A {pa} · B {pb} · "
            f"% NOM DEVIASI ÷ PENJUALAN: A {ra_txt} · B {rb_txt} · "
            f"{meta['n_bahan_a']} vs {meta['n_bahan_b']} bahan")
        for c, v in (("A", meta["a_label"]), ("B", meta["b_label"]),
                     ("Δ", "Selisih (A−B)"), ("%", "% (A−B)÷|B|")):
            with contextlib.suppress(tk.TclError):
                self.tree13a.heading(c, text=v)
        self._fill_tree(self.tree13a, p["poin13_score"],
                        ["Ukuran", "A", "B", "Δ", "%"])
        for c, v in (("A QTY", f"{meta['a_label']} QTY"),
                     ("B QTY", f"{meta['b_label']} QTY"),
                     ("A NOM", f"{meta['a_label']} NOM"),
                     ("B NOM", f"{meta['b_label']} NOM"),
                     ("Δ QTY", "Δ QTY (A−B)"),
                     ("Δ NOM", "Δ NOM (A−B)"),
                     ("%", "% (A NOM)÷|B NOM|")):
            with contextlib.suppress(tk.TclError):
                self.tree13b.heading(c, text=v)
        self._fill_tree(self.tree13b, p["poin13_bahan"],
                        ["Akun", "Nama Bahan", "Satuan", "A QTY", "B QTY",
                         "Δ QTY", "A NOM", "B NOM", "Δ NOM", "%"])
        self._p13_status_var.set(
            "TOTAL QTY antar-bahan tidak dijumlahkan (satuan campur) — "
            "TOTAL hanya kolom NOM (Rp)")

    def _fill_tree(self, tree, dfp: pd.DataFrame, cols: list):
        """Isi tree dari frame display (kolom string terformat) +
        tag minus merah per-cell + zebra + baris TOTAL tebal."""
        negs: list = []
        numericish = {"A", "B", "Σ", "Rata²", "Med", "Δ", "%", "A QTY",
                      "B QTY", "Δ QTY", "A NOM", "B NOM", "Δ NOM"}
        items = []
        for i, (_ix, r) in enumerate(dfp.iterrows()):
            vals = []
            for c in cols:
                v = r.get(c, "-")
                vals.append("" if v is None or (
                    isinstance(v, float) and pd.isna(v)) else str(v))
            is_tot = bool(r.get("_total", False)) or (
                "Nama Bahan" in r.index
                and str(r.get("Nama Bahan")) == "TOTAL")
            tags = [_TOT_TAG] if is_tot else (
                ["evenrow"] if i % 2 == 1 else [])
            iid = f"lv{i}"
            items.append(("", iid, {"values": vals, "tags": tags}))
            if not is_tot:
                for j, c in enumerate(cols):
                    if c in numericish and vals[j].startswith("("):
                        negs.append((iid, c))
        tree.delete(*tree.get_children())
        self._neg_cells[tree] = negs
        insert_tree_items(tree, items,
                          on_done=lambda: self._reapply_neg(tree, negs))

    def _reapply_neg(self, tree, negs):
        with contextlib.suppress(tk.TclError):
            tree.tag_configure("neg_cell", foreground=_NEG)
        if CELL_TAGS_SUPPORTED:
            apply_cell_tag(tree, "neg_cell", negs)
        else:
            for iid, _c in negs:
                with contextlib.suppress(tk.TclError):
                    cur = list(tree.item(iid, "tags"))
                    if "neg_cell" not in cur:
                        cur.append("neg_cell")
                        tree.item(iid, tags=cur)

    def _sort(self, tree, col):
        reverse = not getattr(tree, "_lv_desc", False)
        tree._lv_desc = reverse
        sort_tree_by_column(
            tree, col, reverse=reverse,
            on_done=lambda: self._reapply_neg(
                tree, self._neg_cells.get(tree, [])))

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------
    def _export_excel(self):
        p = self._payload
        if p is None or not p.get("ok"):
            messagebox.showinfo(
                "Laporan Versus", "Belum ada hasil untuk di-export.")
            return
        from .export_sheets import write_laporan_versus_book
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile="Laporan Versus.xlsx")
        if not path:
            return
        try:
            write_laporan_versus_book(path, p, self._mode)
            messagebox.showinfo("Laporan Versus",
                                f"Export tersimpan:\n{path}")
        except Exception as exc:  # noqa: BLE001 — error user jujur
            messagebox.showerror("Laporan Versus",
                                 f"Gagal export: {exc}")

    # ------------------------------------------------------------------
    # API kecil utk app
    # ------------------------------------------------------------------
    def primary_tree(self):
        """Fallback roda router (app._primary_scrollable)."""
        if self._poin == 13:
            return self.tree13b
        return self.tree
