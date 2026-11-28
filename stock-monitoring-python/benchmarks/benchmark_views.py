#!/usr/bin/env python3
"""
benchmark_views.py — Benchmark lapisan VIEW/UI (P1) di bawah Xvfb.

Dataset: append1-like IN-MEMORY (synth_data.make_big_append1 — tanpa
Excel; skala baris parametrik 100k..900k).

Yang diukur (fungsi/widget PRODUKSI, tanpa modifikasi):
  1.  Pivot compute (mode 📅 tanggal & 🏪 resto)  — _compute_payload
  2.  Pivot render penuh                            — load_data→ensure_refreshed
  3.  Pivot filter kolom barang (25% subset) + reset  — recompute+render
  4.  Deviasi GR compute + render                    — _refresh(sync)
  5.  Sort kolom tree                                 — sort_tree_by_column
  6.  Nominal Deviasi (HEADLESS, tanpa Tk)            — nominal_common
  7.  Export pivot ke Excel                           — write_pivot_display_sheet
  8.  Responsivitas event loop selama render async — max gap root.update()

Jendela popup detail & fullscreen table window TIDAK diukur di sini
(memerlukan interaksi seleksi baris sintetis lintas modul; keterbatasan
dijelaskan di laporan). psutil = tooling benchmark, bukan dependency
runtime app.
"""
import argparse
import json
import os
import sys
import tempfile
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


def pump(root, cond, timeout=300.0, gap_recorder=None):
    """Pompa event loop sampai cond() True; rekam max gap antar update
    (proxy responsivitas: gap kecil = UI tidak membeku)."""
    t0 = time.perf_counter()
    last = t0
    max_gap = 0.0
    n = 0
    while time.perf_counter() - t0 < timeout:
        root.update()
        n += 1
        now = time.perf_counter()
        max_gap = max(max_gap, now - last)
        last = now
        if cond():
            if gap_recorder is not None:
                gap_recorder.append(max_gap)
            return True, round(time.perf_counter() - t0, 3), n, round(max_gap, 4)
        time.sleep(0.002)
    if gap_recorder is not None:
        gap_recorder.append(max_gap)
    return False, round(time.perf_counter() - t0, 3), n, round(max_gap, 4)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--restos", type=int, default=10)
    ap.add_argument("--barang", type=int, default=20)
    ap.add_argument("--tag", default="views")
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip-render", action="store_true",
                    help="Lewati render GUI (compute-only)")
    a = ap.parse_args()

    import tkinter as tk

    import numpy as np
    import pandas as pd

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import synth_data

    from src.ui import widgets as W
    from src.ui.widgets import sort_tree_by_column

    out = {
        "kind": "benchmark_views",
        "tag": a.tag,
        "started_utc": datetime.now(UTC).isoformat(),
        "machine": {"cpu": os.cpu_count(),
                    "ram_total_mb": round(
                        psutil.virtual_memory().total / (1024 * 1024), 1),
                    "python": sys.version.split()[0]},
        "env": {"pandas": pd.__version__, "numpy": np.__version__,
                "tk": str(tk.TkVersion),
                "display": os.environ.get("DISPLAY", ""),
                "cell_tags": bool(getattr(W, "CELL_TAGS_SUPPORTED", False))},
        "params": {"restos": a.restos, "barang": a.barang,
                   "skip_render": a.skip_render},
        "measures": {},
        "notes": [
            ("Dataset append1-like IN-MEMORY SINTETIS (make_big_append1) — "
             "meniru skema output pipeline, bukan workbook operasional."),
            ("Popup detail & jendela fullscreen tabel tidak diukur "
             "(butuh interaksi seleksi baris; keterbatasan dijelaskan di "
             "AUDIT_PERFORMANCE_REPORT.md)."),
        ],
    }

    t0 = time.perf_counter()
    df, n_pairs = synth_data.make_big_append1(a.restos, a.barang)
    out["data"] = {"rows": len(df), "pairs": n_pairs,
                   "gen_s": round(time.perf_counter() - t0, 3),
                   "mem_mb": round(float(df.memory_usage(deep=True).sum())
                                   / (1024 * 1024), 1)}
    print(f"dataset: {len(df)} rows ({n_pairs} pairs), "
          f"{out['data']['mem_mb']}MB, gen {out['data']['gen_s']}s")
    rec = out["measures"]

    # ------------------------------------------------------------------
    # 6. Nominal Deviasi — HEADLESS (nominal_common, tanpa Tk)
    # ------------------------------------------------------------------
    from src.ui.nominal_common import agregasi_nominal_per_resto, hitung_nominal_pairs
    harga_map = {b: (15.0, sat) for b, sat in
                 [(f"BRG SYN {i:04d} (V.20)",
                   "KG" if i % 2 == 0 else "PCS")
                  for i in range(a.barang)]}
    t = time.perf_counter()
    npairs_df = hitung_nominal_pairs(df, h=25, harga_map=harga_map,
                                     konversi_map=None)
    rec["nominal_compute_s"] = round(time.perf_counter() - t, 3)
    rec["nominal_rows"] = len(npairs_df)
    t = time.perf_counter()
    per_resto, _per_pair = agregasi_nominal_per_resto(
        df, h=25, harga_map=harga_map, konversi_map=None)
    rec["nominal_agregasi_s"] = round(time.perf_counter() - t, 3)
    rec["nominal_agregasi_resto_rows"] = len(per_resto)
    print(f"nominal: pairs={len(npairs_df)} compute={rec['nominal_compute_s']}s "
          f"agregasi={rec['nominal_agregasi_s']}s")

    if a.skip_render:
        print("(skip render GUI — selesai)")
        _save(out, a.out)
        return

    # ------------------------------------------------------------------
    # GUI (hidden root di Xvfb)
    # ------------------------------------------------------------------
    root = tk.Tk()
    root.withdraw()

    from src.ui.deviasi_view import DeviasiView
    from src.ui.pivot_view import PivotTableView

    # --- 1-4: PIVOT -------------------------------------------------
    pv = PivotTableView(root)
    pv.pack(fill="both", expand=True)
    # load data DULU (compute butuh self.data terisi)
    t = time.perf_counter()
    pv.load_data(df)
    pv.ensure_refreshed()
    ok, dt, _nup, mg = pump(root, lambda: not pv._busy and
                            len(pv.tree.get_children("")) > 0)
    rec["pivot_render_s"] = round(dt, 3)
    rec["pivot_render_rows"] = len(pv.tree.get_children(""))
    rec["pivot_render_eventloop_maxgap_s"] = mg
    rec["pivot_tree_cells"] = int(len(pv.tree.get_children("")) *
                                  len(pv.tree["columns"]))
    print(f"pivot render (resto): {dt}s rows={rec['pivot_render_rows']} "
          f"maxgap={mg}s")

    # compute-only (pure pandas) — mode resto
    t = time.perf_counter()
    st = pv._filter_state()
    payload = pv._compute_payload(st)
    rec["pivot_compute_resto_s"] = round(time.perf_counter() - t, 3)
    rec["pivot_rows"] = len(payload.get("items", []))
    # mode tanggal
    pv.pivot_mode = "tanggal"
    t = time.perf_counter()
    st = pv._filter_state()
    payload_tgl = pv._compute_payload(st)
    rec["pivot_compute_tanggal_s"] = round(time.perf_counter() - t, 3)
    rec["pivot_compute_tanggal_rows"] = len(payload_tgl.get("items", []))
    print(f"pivot compute: resto={rec['pivot_compute_resto_s']}s "
          f"tanggal={rec['pivot_compute_tanggal_s']}s "
          f"rows={rec['pivot_rows']}")
    pv.pivot_mode = "resto"

    # filter kolom barang — 25% subset nama
    names = sorted({str(x) for x in df["Nama Barang"].unique()})
    subset = set(names[:max(1, len(names) // 4)])
    t = time.perf_counter()
    pv._name_selected = subset
    pv.ensure_refreshed()
    ok, dt, _nup, mg = pump(root, lambda: not pv._busy)
    rec["pivot_filter25_s"] = round(dt, 3)
    rec["pivot_filter25_rows"] = len(pv.tree.get_children(""))
    # reset filter
    t = time.perf_counter()
    pv._name_selected = None
    pv.ensure_refreshed()
    ok, dt, _nup, mg = pump(root, lambda: not pv._busy)
    rec["pivot_filter_reset_s"] = round(dt, 3)
    print(f"pivot filter25: {rec['pivot_filter25_s']}s "
          f"({rec['pivot_filter25_rows']} rows) reset: "
          f"{rec['pivot_filter_reset_s']}s")

    # export excel pivot (sesuai tampilan)
    exp_path = os.path.join(tempfile.mkdtemp(), "bench_pivot.xlsx")
    t = time.perf_counter()
    from src.ui.export_sheets import write_pivot_display_sheet
    n_rows_written = write_pivot_display_sheet(
        exp_path, pv._last_payload, visible_cols=None)
    rec["pivot_export_s"] = round(time.perf_counter() - t, 3)
    rec["pivot_export_rows"] = int(n_rows_written)
    rec["pivot_export_size_mb"] = round(
        os.path.getsize(exp_path) / (1024 * 1024), 2)
    print(f"pivot export: {rec['pivot_export_s']}s "
          f"({rec['pivot_export_size_mb']}MB)")

    # --- 5: DEVIASI GR ----------------------------------------------
    dv = DeviasiView(root, satuan_mode="GR")
    dv.pack(fill="both", expand=True)
    t = time.perf_counter()
    dv.data = df
    dv._show_content()
    dv._refresh(sync=True)
    for _ in range(5000):
        root.update()
        if not dv._busy and len(dv.tree.get_children("")):
            break
        time.sleep(0.002)
    rec["deviasi_compute_render_s"] = round(time.perf_counter() - t, 3)
    rec["deviasi_rows"] = len(dv.tree.get_children(""))
    print(f"deviasi GR compute+render: {rec['deviasi_compute_render_s']}s "
          f"rows={rec['deviasi_rows']}")

    # sort kolom (NILAI kolom terurut numerik)
    cols = list(dv.tree["columns"])
    sort_col = cols[-1] if cols else "#0"
    t = time.perf_counter()
    done = threading.Event()
    sort_tree_by_column(dv.tree, sort_col, reverse=True,
                        parse=float, on_done=lambda: done.set())
    ok, dt, _nup, mg = pump(root, lambda: done.is_set(), timeout=120)
    rec["deviasi_sort_s"] = round(dt, 3)
    print(f"deviasi sort kolom '{sort_col}': {dt}s (ok={ok})")

    # --- RAM -----------------------------------------------------------
    rec["rss_peak_mb"] = round(rss_mb(), 1)
    out["finished_utc"] = datetime.now(UTC).isoformat()

    root.destroy()
    _save(out, a.out)


def _save(out, path=None):
    path = path or str(Path(__file__).resolve().parent / "results" /
                      f"views_{out['tag']}_{int(time.time())}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"JSON: {path}")


if __name__ == "__main__":
    main()
