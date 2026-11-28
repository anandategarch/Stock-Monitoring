"""
anomali_shift.py — Engine deteksi ANOMALI SHIFT DEVIASI (tab 🚨 Radar
Anomali + label CEK "Shift Deviasi" tab 📦/🧩 — v3.18).

POLA YANG DIDETEKSI (kasus nyata user: BJMHAS · CUP 14 (V.20) PCS —
deviasi stabil (177)-(259) tgl 2-22, melompat (1.293) tgl 23 bersama
IN 1.000 hari itu, lalu KONSTAN (1.343)/(1.390) tgl 24-25): lompatan
LEVEL yang BERTAHAN. Baris 10.% Growth Deviasi menangkap tgl 23
(+282%) tapi tgl 24-25 "tenang" lagi (+3-4%) padahal masalah justru
LEVEL BARU yang menempel — growth harian mendeteksi lompatan, bukan
pergeseran level; label CEK Naik/Turun Drastis menilai SO (stok), bukan
seri deviasi. Engine ini menutup celah itu.

Metode — perbandingan DUA-JENDELA per pasangan (barang × resto ×
satuan) atas seri |3.DEVIASI| harian 1..H:
- split kandidat t: baseline = nilai tanggal < t; level = nilai ≥ t.
- baseline & level = MEDIAN (robust — anomali tidak ikut merusak
  baseline pasangan itu sendiri, beda dari mean/std); sebaran baseline
  = MAD (1,4826×MAD ≈ σ robust utk z).
- SHIFT NAIK bila median(level) ≥ RATIO_CUT × median(baseline)
  (default ×2) DAN delta > 0; split terpilih = perbedaan median
  TERBESAR (tgl lompatan asli — bukan tanggal ramp naik).
- Guard: ≥ MIN_BASELINE hari baseline (5) · ≥ MIN_DURASI hari di level
  baru (2 — spike 1 hari insidental BUKAN pergeseran level, tidak
  dilaporkan) · median baseline ≥ LEVEL_FLOOR (1,0 — rasio tak
  bermakna di sekitar nol; pasangan ber-baseline nol punya label CEK
  lain yang lebih tepat) · rekaman terakhir ≥ H−STALE_GAP (pasangan
  yang berhenti direkam jauh sebelum H = alarm basi).
- z = (level − median) ÷ 1,4826×MAD — INFO keparahan, bukan gerbang
  (MAD 0 → z tak hingga, baseline datar sempurna).

Hint penyebab — KECOCOKAN KIRIMAN: IN sistem (JENIS 4.IN) tanggal
shift ±1 dibandingkan Δlevel (toleransi ±IN_TOL × |Δ|): cocok →
"cocok kiriman" (pola cut-off — barang masuk fisik/sistem tapi SO tidak
ikut naik; persis kelas yang diproses engine audit Rekap Selisih IN).
BM rekap resto (5.BARANG MASUK) tanggal ±1 dilampirkan pembanding; Nomor
(IT/RI) + Nomor PO baris IN dibawa utk drill-down bukti.

Kunci pasangan KANONIK (norm_nama_barang_key × norm_nama_resto_key ×
SATUAN strip+upper — konvensi v3.11.59): drift ejaan pasangan tetap
cocok di kedua konsumen (radar & CEK deviasi). Output kolom kb/kr/satn
disiapkan utk lookup; barang/resto/satuan RAW dipertahankan utk display
& popup (persis ejaan frame).
"""
from __future__ import annotations

import bisect
import math

import numpy as np
import pandas as pd

from ..pipeline.helpers import norm_nama_barang_key, norm_nama_resto_key

# -- ambang deteksi (ClassVar-style konstanta modul — v1 tanpa UI) --------
MIN_BASELINE = 5      # minimal hari terekam pra-shift (median stabil)
MIN_DURASI = 2        # minimal hari di level baru (1 hari = spike ≠ shift)
RATIO_CUT = 2.0       # level ≥ ×2 baseline median → shift naik
LEVEL_FLOOR = 1.0     # median baseline < 1.0 → rasio tak bermakna → skip
STALE_GAP = 3         # rekaman terakhir < H−3 → pasangan basi → skip
IN_TOL = 0.35         # |IN − Δ| ≤ 35% × |Δ| → "cocok kiriman"
IN_WINDOW = (-1, 0, 1)  # tanggal IN/BM dilihat shift−1..shift+1 (cut-off 1 hari)

RESULT_COLUMNS = [
    "barang", "resto", "satuan",           # RAW — display & popup
    "kb", "kr", "satn",                    # kanonik — lookup konsumen
    "tgl_shift", "durasi", "n_baseline",   # peristiwa
    "baseline", "mad", "level",            # statistik (|dev|)
    "delta", "ratio", "z",                 # ukuran pergeseran
    "in_qty", "in_tgl", "in_nomor", "in_nomor_po", "in_match",
    "bm_qty", "bm_tgl",
]


def _med_sorted(s: list) -> float:
    """Median dari list TER-SORTIR (incremental split-scan — O(1))."""
    n = len(s)
    mid = n // 2
    if n % 2:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def _remove_sorted(s: list, v: float) -> None:
    """Buang SATU kemunculan v dari list ter-sortir (split-scan maju)."""
    i = bisect.bisect_left(s, v)
    if i < len(s) and s[i] == v:
        s.pop(i)


def detect_shift_anomalies(df: pd.DataFrame | None, h: int | None,
                            *, min_baseline: int = MIN_BASELINE,
                            min_durasi: int = MIN_DURASI,
                            ratio_cut: float = RATIO_CUT,
                            level_floor: float = LEVEL_FLOOR,
                            stale_gap: int = STALE_GAP,
                            in_tol: float = IN_TOL) -> pd.DataFrame:
    """Deteksi pergeseran level |3.DEVIASI| per pasangan × satuan 1..H.

    Input: frame long append1 (kolom Nama Barang / NAMA RESTO / Tanggal
    / JENIS / NILAI [/ SATUAN / Nomor / Nomor PO]). h = tanggal analisa
    (None → tgl terakhir data). Output: DataFrame RESULT_COLUMNS — satu
    baris per pasangan ber-shift naik aktif; kosong bila tak ada / data
    kurang (bukan error). Murni pandas/angka — TANPA widget (dipanggil
    worker thread radar + _compute_pivot deviasi_view)."""
    empty = pd.DataFrame(columns=RESULT_COLUMNS)
    if df is None or getattr(df, "empty", True):
        return empty
    cols = set(df.columns)
    if not {"Nama Barang", "NAMA RESTO", "JENIS", "NILAI"} <= cols:
        return empty

    tnum = pd.to_numeric(df["Tanggal"], errors="coerce")
    nilai = pd.to_numeric(df["NILAI"], errors="coerce")
    jenis = df["JENIS"].astype(str)
    _in_range = tnum.notna() & (tnum >= 1)
    if h is not None:
        _in_range &= (tnum <= int(h))

    # --- seri deviasi + peta IN/BM per pasangan-kanonik --------------
    has_sat = "SATUAN" in cols
    satuan_raw = (df["SATUAN"].fillna("").astype(str).str.strip()
                  if has_sat else pd.Series([""] * len(df), index=df.index))
    kb_s = df["Nama Barang"].astype(str).map(norm_nama_barang_key)
    kr_s = df["NAMA RESTO"].astype(str).map(norm_nama_resto_key)
    satn_s = satuan_raw.str.upper()

    series: dict[tuple, dict] = {}   # (kb,kr,satn) → {tgl: |dev|}
    raw_name: dict[tuple, tuple] = {}  # (kb,kr,satn) → (barang,resto,satuan)
    in_map: dict[tuple, dict] = {}   # → {tgl: (qty, nomor, nomor po)}
    bm_map: dict[tuple, dict] = {}   # → {tgl: qty}

    _m_dev = _in_range & (jenis == "3.DEVIASI")
    _m_in = _in_range & (jenis == "4.IN") & (nilai.fillna(0) != 0)
    _m_bm = _in_range & (jenis == "5.BARANG MASUK")
    _t = tnum.astype("Int64")

    for m, sink in ((_m_dev, "dev"), (_m_in, "in"), (_m_bm, "bm")):
        if not bool(m.any()):
            continue
        sub = df.loc[m, ["Nama Barang", "NAMA RESTO"]]
        keys = zip(kb_s[m].tolist(), kr_s[m].tolist(), satn_s[m].tolist())
        tgls = _t[m].tolist()
        vals = nilai[m].fillna(0).tolist()
        raws_b = sub["Nama Barang"].astype(str).tolist()
        raws_r = sub["NAMA RESTO"].astype(str).tolist()
        raws_s = satuan_raw[m].tolist()
        if sink == "dev":
            for k, t, v, rb, rr, rs in zip(keys, tgls, vals,
                                           raws_b, raws_r, raws_s):
                series.setdefault(k, {})[int(t)] = abs(float(v))
                raw_name.setdefault(k, (rb, rr, rs))
        elif sink == "in":
            _nom = (df.loc[m, "Nomor"].astype(str) if "Nomor" in cols
                    else pd.Series([""] * int(m.sum())))
            _po = (df.loc[m, "Nomor PO"].astype(str)
                   if "Nomor PO" in cols
                   else pd.Series([""] * int(m.sum())))
            for k, t, v, nm, po in zip(keys, tgls, vals,
                                        _nom.tolist(), _po.tolist()):
                in_map.setdefault(k, {})[int(t)] = (float(v),
                                                    "" if nm == "nan" else nm,
                                                    "" if po == "nan" else po)
        else:
            for k, t, v in zip(keys, tgls, vals):
                bm_map.setdefault(k, {})[int(t)] = float(v)

    if not series:
        return empty
    if h is None:
        h = int(max(max(s) for s in series.values()))

    # --- split-scan dua-jendela per pasangan --------------------------
    min_base_n = max(1, int(min_baseline))
    min_dur_n = max(1, int(min_durasi))
    rows: list[dict] = []
    for key, sv in series.items():
        tgls = sorted(sv)
        n = len(tgls)
        if n < min_base_n + min_dur_n:
            continue
        if tgls[-1] < h - stale_gap:
            continue  # pasangan berhenti direkam jauh sebelum H — basi
        vals = [sv[t] for t in tgls]

        best_diff, best_i = 0.0, -1
        left_s = sorted(vals[:min_base_n])
        right_s = sorted(vals[min_base_n:])
        for i in range(min_base_n, n - min_dur_n + 1):
            med_l = _med_sorted(left_s)
            if med_l >= level_floor:
                med_r = _med_sorted(right_s)
                diff = med_r - med_l
                if diff > best_diff:
                    best_diff, best_i = diff, i
            if i < n - min_dur_n:          # majukan split: pindah v[i]
                v = vals[i]
                _remove_sorted(right_s, v)
                bisect.insort(left_s, v)
        if best_i < 0 or best_diff <= 0:
            continue
        i = best_i
        med_l = float(np.median(vals[:i]))
        med_r = float(np.median(vals[i:]))

        # v3.18 — REFINEMENT tarik-balik: median-split dapat MENYERAP hari
        # lompatan PERTAMA ke baseline (median tahan 1 outlier — kasus
        # nyata user: split jatuh tgl 24 padahal lompatan tgl 23). Tarik
        # split mundur selama hari terakhir baseline ≥ baseline + ½Δ —
        # hari pertama level baru kembali masuk jendela post-shift.
        # Baseline asli bisa jadi < minimum bila seluruh hari awal ikut
        # tertarik → guard sesudahnya (tak cukup bukti baseline — skip).
        _thr = med_l + 0.5 * (med_r - med_l)
        while i > 0 and vals[i - 1] >= _thr:
            i -= 1
        if i < min_base_n:
            continue

        med_l = float(np.median(vals[:i]))
        med_r = float(np.median(vals[i:]))
        ratio = med_r / med_l if med_l > 0 else float("inf")
        if ratio < ratio_cut:
            continue
        mad = float(np.median(np.abs(np.asarray(vals[:i]) - med_l))) \
            * 1.4826
        delta = med_r - med_l
        z = (float("inf") if mad <= 0 else delta / mad)

        # v3.18 — DURASI = hari yang BENAR-BENAR di level baru (nilai ≥
        # baseline + ½Δ — bukan sekadar ukuran jendela): spike 1 hari
        # (kasus: 23 hari di 100 lalu 1 hari 1.200 → jendela 2 hari tapi
        # hanya 1 hari tinggi) BUKAN pergeseran level — tidak dilaporkan.
        _thr_lvl = med_l + 0.5 * delta
        durasi = sum(1 for v in vals[i:] if v >= _thr_lvl)
        if durasi < min_dur_n:
            continue

        # --- hint kiriman: IN & BM di sekitar tgl shift ---------------
        tgl_shift = int(tgls[i])
        in_qty = in_tgl = float("nan")
        in_nomor = in_nomor_po = ""
        in_match = False
        cand = [(dt, ent) for dt in IN_WINDOW
                if (ent := in_map.get(key, {}).get(tgl_shift + dt))]
        if cand:
            dt, ent = min(cand, key=lambda d: abs(d[1][0] - delta))
            in_tgl, in_qty = float(tgl_shift + dt), ent[0]
            in_nomor, in_nomor_po = ent[1], ent[2]
            in_match = abs(in_qty - delta) <= in_tol * delta
        bm_qty = bm_tgl = float("nan")
        cand_bm = [(dt, q) for dt in IN_WINDOW
                   if (q := bm_map.get(key, {}).get(tgl_shift + dt))
                   is not None]
        if cand_bm:
            dt, q = max(cand_bm, key=lambda d: d[1])
            bm_tgl, bm_qty = float(tgl_shift + dt), q

        barang, resto, satuan = raw_name.get(key, (key[0], key[1], key[2]))
        rows.append({
            "barang": barang, "resto": resto, "satuan": satuan,
            "kb": key[0], "kr": key[1], "satn": key[2],
            "tgl_shift": tgl_shift, "durasi": durasi, "n_baseline": i,
            "baseline": med_l, "mad": mad, "level": med_r,
            "delta": delta, "ratio": ratio, "z": z,
            "in_qty": in_qty, "in_tgl": in_tgl,
            "in_nomor": in_nomor, "in_nomor_po": in_nomor_po,
            "in_match": in_match, "bm_qty": bm_qty, "bm_tgl": bm_tgl,
        })

    if not rows:
        return empty
    out = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    return out.sort_values(["ratio", "delta"], ascending=False,
                           kind="mergesort").reset_index(drop=True)


def shift_segment_text(rec: dict, fmt_num) -> str:
    """Segmen teks CEK/radar dari record hasil deteksi (fmt_num = callable
    format angka gaya Indonesia milik pemanggil — pola _fmt_num
    deviasi_view/radar; dipakai label CEK 'Shift Deviasi' & kolom radar
    supaya narasi IDENTIK di kedua tempat):
    'Level ×6,0 tgl 23 (224 → 1.343 · 3 hari · cocok IN 1.000)'."""
    ratio = rec.get("ratio")
    try:
        ratio = float(ratio)
    except (TypeError, ValueError):
        return ""
    if math.isnan(ratio):          # NaN — tanpa teks
        return ""
    if math.isinf(ratio):          # pembagi ~0 → rasio tak hingga
        ratio_txt = "×∞"
    else:
        ratio_txt = f"×{ratio:,.1f}".replace(",", "\u00a0").replace(
            ".", ",").replace("\u00a0", ".")
    base = fmt_num(rec.get("baseline"))
    lvl = fmt_num(rec.get("level"))
    dur = rec.get("durasi")
    tgl = rec.get("tgl_shift")
    seg = f"Level {ratio_txt} tgl {fmt_num(tgl) if tgl is not None else '?'}"
    if base and lvl:
        seg += f" ({base} → {lvl}"
        if dur:
            seg += f" · {int(dur)} hari"
        seg += ")"
    if rec.get("in_match") and rec.get("in_qty"):
        seg += f" · cocok IN {fmt_num(rec.get('in_qty'))}"
    return seg
