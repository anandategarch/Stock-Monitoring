#!/usr/bin/env python3
"""
benchmark_pipeline.py — Pipeline end-to-end benchmark (P1).

Mengukur TIAP tahap pipeline (fungsi PRODUKSI yang sama persis dengan
run_pipeline — urutan & argumen di-mirror dari src/main.py; TIDAK ada
kode produksi yang dimodifikasi) pada dataset sintetis (synth_data.py):

  stage 1  Config load
  stage 2  build_append1           (semua baca Excel + Append1 + lookup)
  stage 3  build_rincian_po
  stage 4  maps + periode          (_extract_append1_maps etc.)
  stage 5  audit penuh             (build_audit_from_app bulan_lalu=True)
  stage 6  audit bulan ini         (build_audit_from_app bulan_lalu=False)
  stage 7  harga 41.09             (fn_4109 + build_harga_map)

Skenario cache (dalam SATU proses — membedakan cache-benar-dipakai dari
replay-hasil: pipeline PENUH dijalankan ulang; cache hit dihitung dari
read_cache_stats, bukan asumsi):
  cold          — read_cache_invalidate(None) → semua file dibaca disk
  warm          — run ulang tanpa invalidate (file tak berubah)
  refresh_one   — invalidate 1 file rekap resto pertama saja
  refresh_all   — invalidate(None) ulang

RAM: psutil RSS level-PROSES/OS (bukan tracemalloc — alokasi NumPy/
Pandas di luar Python heap tidak tercermin). Sampler thread 50ms →
peak RSS; snapshot RSS di tiap checkpoint tahap.

Kesetaraan hasil cold vs warm diverifikasi fingerprint (jumlah baris
per JENIS append1 + audit KPI + jumlah baris PO) — cache tidak boleh
mengubah hasil analisis.

Output JSON: benchmarks/results/pipeline_<tag>_<timestamp>.json
psutil adalah tooling benchmark, BUKAN dependency runtime app
(requirements.txt tidak diubah).
"""
import argparse
import gc
import json
import os
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psutil

PROC = psutil.Process()


def rss_mb() -> float:
    return PROC.memory_info().rss / (1024 * 1024)


class PeakSampler:
    """Sampler RSS 50ms — peak real OS-level (thread daemon)."""

    def __init__(self):
        self.peak = rss_mb()
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            self.peak = max(self.peak, rss_mb())
            time.sleep(0.05)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        self._t.join(timeout=1.0)


def df_mem_mb(df) -> float:
    """Perkiraan memori DataFrame via memory_usage(deep) bila tersedia."""
    try:
        return float(df.memory_usage(deep=True).sum()) / (1024 * 1024)
    except Exception:  # noqa: BLE001 — pengukuran opsional, bukan jalur bisnis
        return -1.0


def fingerprint(append1_df, po_df, audit_result) -> dict:
    """Ringkasan hasil untuk verifikasi kesetaraan cold vs warm
    (TIDAK menyimpan data — hanya count per JENIS + KPI + rows)."""
    fp = {"append1_rows": len(append1_df)}
    if not append1_df.empty and "JENIS" in append1_df.columns:
        vc = append1_df["JENIS"].astype(str).value_counts().to_dict()
        fp["append1_per_jenis"] = {str(k): int(v)
                                   for k, v in vc.items()}
    fp["po_rows"] = len(po_df) if po_df is not None else 0
    fp["audit_rows"] = len(audit_result.get("df", []))
    fp["audit_rows_bulan_ini"] = len(audit_result.get(
        "df_bulan_ini", []))
    kpi = audit_result.get("kpi") or {}
    fp["audit_kpi"] = {k: int(v) for k, v in kpi.items()
                       if isinstance(v, (int, float))}
    return fp


def run_stages(config_path: str, rec: dict, rss_marks: list):
    """Jalankan tahap pipeline (mirror urutan run_pipeline src/main.py,
    fungsi produksi yang sama — hasil = produksi)."""

    import pandas as pd  # noqa: F401 — import produksi path

    t0 = time.perf_counter()
    from src.config import Config
    from src.main import _extract_append1_maps
    from src.pipeline.append1 import build_append1
    from src.pipeline.fn_4109 import build_harga_map, fn_4109
    from src.pipeline.fn_audit import (
        build_audit_from_app,
        detect_data_period,
        extract_po_pending,
    )
    from src.pipeline.rincian_po import build_rincian_po
    rec["imports_s"] = round(time.perf_counter() - t0, 3)

    def stage(name, fn):
        t = time.perf_counter()
        out = fn()
        rec[f"stage_{name}_s"] = round(time.perf_counter() - t, 3)
        rss_marks.append((name, round(rss_mb(), 1)))
        return out

    config = stage("1_config", lambda: Config(config_path))
    in_detail_holder: dict = {}
    rekap_so_holder: dict = {}
    konversi_holder: dict = {}
    saldo_sistem_holder: dict = {}
    append1_df = stage("2_append1", lambda: build_append1(
        config, stop_event=None,
        in_detail_out=in_detail_holder,
        rekap_so_out=rekap_so_holder,
        konversi_out=konversi_holder,
        saldo_sistem_out=saldo_sistem_holder))
    rec["append1_rows"] = len(append1_df)
    rec["in_detail_rows"] = len(in_detail_holder.get("df", []))
    rec["append1_mem_mb"] = round(df_mem_mb(append1_df), 1)

    po_semua: dict = {}
    rincian_po_df = stage("3_rincian_po", lambda: build_rincian_po(
        config, semua_out=po_semua, stop_event=None))
    po_pending_df = extract_po_pending(po_semua.get("df"))
    rec["po_rows"] = len(rincian_po_df) if rincian_po_df is not None else 0

    in_detail_df = in_detail_holder.get("df")
    if in_detail_df is None:
        import pandas as pd2
        in_detail_df = pd2.DataFrame()

    def maps_stage():
        sa, bk = _extract_append1_maps(append1_df)
        period = detect_data_period(in_detail_df)
        if period is None:
            now = datetime.now()
            period = (now.year, now.month)
        return sa, bk, period

    saldo_awal_map, bk_map, period = stage("4_maps", maps_stage)
    rec["period"] = f"{period[0]:04d}-{period[1]:02d}"

    def audit_full():
        df, kpi, desc = build_audit_from_app(
            rekap_so_holder.get("df"), in_detail_df,
            po_pending_df=po_pending_df,
            konversi=konversi_holder.get("map"),
            saldo_awal_map=saldo_awal_map, bk_map=bk_map,
            period=period, stop_event=None)
        return df, kpi, desc

    (audit_df, audit_kpi, audit_desc) = stage("5_audit_full", audit_full)

    def audit_bulan_ini():
        df2, kpi2, desc2 = build_audit_from_app(
            rekap_so_holder.get("df"), in_detail_df,
            po_pending_df=po_pending_df, bulan_lalu=False,
            konversi=konversi_holder.get("map"),
            saldo_awal_map=saldo_awal_map, bk_map=bk_map,
            period=period, stop_event=None)
        return df2, kpi2, desc2

    (audit_df2, _k2, _d2) = stage("6_audit_bulan_ini", audit_bulan_ini)

    def harga():
        try:
            h = fn_4109(config.folder("Harga"),
                       config.sheet("Harga"), stop_event=None)
            return build_harga_map(h)
        except Exception as e:  # noqa: BLE001 — degradasi anggun by-design (run_pipeline)
            print(f"  [benchmark] harga 41.09 dilewati: {e}")
            return {}

    harga_map = stage("7_harga_4109", harga)
    rec["harga_map_n"] = len(harga_map) if hasattr(harga_map, "__len__") else 0

    audit_result = {"df": audit_df, "kpi": audit_kpi, "desc": audit_desc,
                    "df_bulan_ini": audit_df2, "kpi_bulan_ini": _k2,
                    "desc_bulan_ini": _d2,
                    "saldo_sistem_map": saldo_sistem_holder.get("map") or {},
                    "harga_map": harga_map,
                    "konversi_map": konversi_holder.get("map")}
    return append1_df, rincian_po_df, in_detail_df, audit_result


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", required=True,
                    help="Dir dataset sintetis (synth_data.py --out)")
    ap.add_argument("--config", required=True, help="config.json benchmark")
    ap.add_argument("--tag", default="custom", help="Label hasil (mis. 100k)")
    ap.add_argument("--rekap-file", default=None,
                    help="Path 1 file rekap utk skenario refresh_one "
                         "(default: file resto pertama di data-dir)")
    ap.add_argument("--scenarios", default="cold,warm,refresh_one,refresh_all",
                    help="Skenario dipisah koma")
    ap.add_argument("--out", default=None, help="Path JSON keluaran")
    a = ap.parse_args()
    scenarios = [s.strip() for s in a.scenarios.split(",") if s.strip()]

    from src.pipeline.helpers import (
        read_cache_invalidate,
        read_cache_reset_counters,
        read_cache_stats,
    )

    # File rekap utk refresh_one
    rekap_file = a.rekap_file
    if not rekap_file:
        cand = Path(a.data_dir) / "1. DEVIASI WEEKLY"
        xs = sorted(cand.glob("*.xlsx")) if cand.exists() else []
        rekap_file = str(xs[0]) if xs else None

    out = {
        "kind": "benchmark_pipeline",
        "tag": a.tag,
        "started_utc": datetime.now(UTC).isoformat(),
        "machine": {
            "cpu": os.cpu_count(),
            "ram_total_mb": round(
                psutil.virtual_memory().total / (1024 * 1024), 1),
            "python": sys.version.split()[0],
        },
        "env": {
            "pandas": __import__("pandas").__version__,
            "numpy": __import__("numpy").__version__,
            "tk": None,
        },
        "data": {"data_dir": a.data_dir, "rekap_refresh_one": rekap_file},
        "scenarios": {},
        "notes": [
            ("Dataset SINTETIS (synth_data.py) — BUKAN data operasional "
             "user; hasil ini mengukur pipeline, bukan klaim performa "
             "workbook nyata."),
            ("Skenario menjalankan pipeline PENUH ulang (fungsi produksi "
             "src/main.py urutan sama) — cache hit dari read_cache_stats, "
             "bukan replay hasil."),
        ],
    }
    try:
        import tkinter as tk
        out["env"]["tk"] = str(tk.TkVersion)
    except Exception:  # noqa: BLE001 — opsional (headless tanpa Tk)
        out["env"]["tk"] = "tidak tersedia"

    prev_fp = None
    for scen in scenarios:
        print(f"\n===== SKENARIO {scen} ({a.tag}) =====")
        if scen == "cold" or scen == "refresh_all":
            read_cache_invalidate(None)
        elif scen == "warm":
            pass  # cache dari skenario sebelumnya tetap valid
        elif scen == "refresh_one":
            if not rekap_file:
                print("  (lewat — refresh_one tanpa file rekap)")
                continue
            read_cache_invalidate([rekap_file])
        read_cache_reset_counters()

        rec = {"rss_before_mb": round(rss_mb(), 1)}
        rss_marks = []
        t_all = time.perf_counter()
        with PeakSampler() as sampler:
            try:
                a1, po, ind, audit = run_stages(a.config, rec, rss_marks)
                ok = True
            except Exception as e:  # noqa: BLE001 — dicatat di JSON hasil
                import traceback
                traceback.print_exc()
                rec["error"] = str(e)
                ok = False
                a1 = po = ind = audit = None
        rec["total_s"] = round(time.perf_counter() - t_all, 3)
        rec["rss_after_mb"] = round(rss_mb(), 1)
        rec["peak_rss_mb"] = round(sampler.peak, 1)
        rec["rss_marks"] = rss_marks
        if ok:
            rec["fingerprint"] = fingerprint(a1, po, audit)
            entries, files, hits, misses = read_cache_stats()
            rec["cache"] = {"entries": entries, "files": files,
                            "hit_files": hits, "miss_files": misses}
            if prev_fp is not None:
                rec["fingerprint_match_prev"] = (
                    rec["fingerprint"] == prev_fp)
            prev_fp = rec["fingerprint"]
            rec["stage_sum_s"] = round(
                sum(v for k, v in rec.items()
                    if k.startswith("stage_")), 3)
            print(f"  total {rec['total_s']}s | peak RSS "
                  f"{rec['peak_rss_mb']}MB | cache hit/miss "
                  f"{hits}/{misses} | fingerprint "
                  f"{'OK' if rec.get('fingerprint_match_prev', True) is not False else 'MISMATCH!'}")
            del a1, po, ind, audit
        gc.collect()
        rec["rss_after_gc_mb"] = round(rss_mb(), 1)
        out["scenarios"][scen] = rec

    out["finished_utc"] = datetime.now(UTC).isoformat()

    # Simpan
    outpath = a.out or str(Path(__file__).resolve().parent / "results" /
                           f"pipeline_{a.tag}_{int(time.time())}.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"\nJSON: {outpath}")

    # Ringkasan console
    print("\n===== RINGKASAN =====")
    for scen, rec in out["scenarios"].items():
        if "error" in rec:
            print(f"{scen:14s} ERROR: {rec['error']}")
            continue
        print(f"{scen:14s} total={rec['total_s']:>8.2f}s "
              f"peakRSS={rec['peak_rss_mb']:>8.1f}MB "
              f"append1={rec.get('append1_rows', '?')}rows "
              f"cache hit/miss={rec['cache']['hit_files']}/"
              f"{rec['cache']['miss_files']}")


if __name__ == "__main__":
    main()
