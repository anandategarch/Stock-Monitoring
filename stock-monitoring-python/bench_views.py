"""bench_views.py — Benchmark compute + render view (baseline perf analysis).

Ukur hotspot v3.1: deviasi _compute_pivot (iterrows), laporan _compute_audit
(apply axis=1), pivot _compute_payload (loc per item×metric), tree insert.
Tanpa display (Xvfb opsional) — compute-only + insert tree dummy.
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

import numpy as np
import pandas as pd

np.random.seed(42)

BARANG = [f"BARANG {i:03d} (V.20)" for i in range(120)]
RESTO = ["MLGPAR", "BDGUKU", "KWGGAL", "DPKMAR", "PWKTAM", "CKGPAH",
         "BKSALT", "GGPDAA", "SBRTUP", "KWGTEL", "BJMHAS", "TGRBIN"]
JENIS = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI", "4.IN",
         "5.BARANG MASUK", "7.Selisih IN", "8.BARANG KELUAR", "9.OUT"]


def make_append1(n: int) -> pd.DataFrame:
    df = pd.DataFrame({
        "Nama Barang": np.random.choice(BARANG, n),
        "NAMA RESTO": np.random.choice(RESTO, n),
        "Tanggal": np.random.choice(list(range(1, 32)), n),
        "JENIS": np.random.choice(JENIS, n),
        "NILAI": np.random.randint(-5000, 10000, n).astype("float64"),
        "SATUAN": np.random.choice(["GR", "PCS"], n),
        "AKTIF/NON": np.random.choice(["AKTIF", "NON AKTIF", None], n, p=[.7, .1, .2]),
    })
    return df


def bench(label, fn, n=1):
    t0 = time.perf_counter()
    r = fn()
    dt = (time.perf_counter() - t0) / n
    print(f"  {label:<42} {dt*1000:9.1f} ms")
    return r, dt


def main():
    n = 200_000
    print(f"== BASELINE BENCH — data {n:,} rows, {len(BARANG)} barang × "
          f"{len(RESTO)} resto ==")
    df = make_append1(n)

    root = tk.Tk()
    root.withdraw()

    from src.ui.deviasi_view import DeviasiView
    from src.ui.laporan_deviasi_view import LaporanDeviasiView
    from src.ui.pivot_view import PivotTableView

    dv = DeviasiView(root, satuan_mode="GR")
    dv.data = df
    r, t_dev = bench("Deviasi GR  _compute_pivot (H=25)", dv._compute_pivot)

    lv = LaporanDeviasiView(root)
    lv.data = df
    r, t_lap = bench("Laporan     _compute_audit", lv._compute_audit)

    pv = PivotTableView(root)
    pv.data = df
    pv.pivot_mode = "resto"
    st = pv._filter_state()
    r, t_pr = bench("Pivot resto _compute_payload", lambda: pv._compute_payload(st))

    pv.pivot_mode = "tanggal"
    st = pv._filter_state()
    r, t_pt = bench("Pivot tgl   _compute_payload", lambda: pv._compute_payload(st))

    # --- tree insert benchmark ---
    from tkinter import ttk

    from src.ui.widgets import insert_tree_items
    tree = ttk.Treeview(root, columns=["c1", "c2", "c3"], show="headings")
    for rows_n in (5_000, 20_000):
        items = [("", f"r{i}", {"values": (i, "abc", 12.5)})
                 for i in range(rows_n)]
        t0 = time.perf_counter()
        insert_tree_items(tree, items, batch=400, delay=0)
        # pump events until done
        deadline = time.time() + 120
        while len(tree.get_children("")) < rows_n and time.time() < deadline:
            root.update()
        dt = time.perf_counter() - t0
        print(f"  {'tree insert %s rows (batch 400)' % f'{rows_n:,}':<42} "
              f"{dt*1000:9.1f} ms  ({rows_n/dt:,.0f} rows/s)")
        tree.delete(*tree.get_children(""))

    root.destroy()
    print("\n== RANKING (compute) ==")
    for label, t in sorted([("deviasi", t_dev), ("laporan", t_lap),
                            ("pivot-resto", t_pr), ("pivot-tanggal", t_pt)],
                           key=lambda x: -x[1]):
        print(f"  {label:<14} {t*1000:9.1f} ms")


if __name__ == "__main__":
    main()
