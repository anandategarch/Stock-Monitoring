"""
probe_running_stock.py — property test: fn_running_stock_grouped (v3.7
"ENGINE TURBO", claimed output IDENTIK vs implementasi lama) vs
fn_running_stock (per-group M-mirror) on randomized synthetic data.

Random groups x dates (incl. negatives, NaN dates, NaN keys, duplicate
dates, all-NaN saldo awal) — 200 trials.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import numpy as np
import pandas as pd

from src.pipeline.fn_running_stock import fn_running_stock, \
    fn_running_stock_grouped

rng = np.random.default_rng(42)


def make_case():
    n_groups = rng.integers(1, 6)
    rows = []
    for g in range(n_groups):
        barang = rng.choice(["A", "B", np.nan])
        resto = rng.choice(["R1", "R2", np.nan])
        n = rng.integers(1, 12)
        for _ in range(n):
            t = rng.choice([1, 2, 3, 5, -25, -28, -31, np.nan])
            rows.append({
                "Nama Barang": barang,
                "NAMA RESTO": resto,
                "Tanggal": t,
                "IN": rng.choice([0, 5, 10.5, np.nan]),
                "OUT": rng.choice([0, 3, 7.25, np.nan]),
                "BARANG KELUAR": rng.choice([0, 2, np.nan]),
                "SALDO AWAL": rng.choice([np.nan, 0, 50, 100]),
            })
    return pd.DataFrame(rows)


n_bad = 0
for trial in range(200):
    df = make_case()
    grouped = fn_running_stock_grouped(df, ["Nama Barang", "NAMA RESTO"])
    # old path: per group (sorted the same way) via fn_running_stock
    srt = df.sort_values(["Nama Barang", "NAMA RESTO", "Tanggal"],
                         ascending=True, na_position="last") \
        .reset_index(drop=True)
    keys = list(zip(srt["Nama Barang"].astype(str),
                    srt["NAMA RESTO"].astype(str)))
    bounds, start = [], 0
    for i in range(1, len(srt) + 1):
        if i == len(srt) or keys[i] != keys[start]:
            bounds.append((start, i))
            start = i
    old_parts = []
    for a, b in bounds:
        old_parts.append(fn_running_stock(srt.iloc[a:b].reset_index(drop=True)))
    old = pd.concat(old_parts, ignore_index=True) if old_parts else grouped

    g2 = grouped.sort_values(
        ["Nama Barang", "NAMA RESTO", "Tanggal"], ascending=True,
        na_position="last").reset_index(drop=True)
    o2 = old.sort_values(
        ["Nama Barang", "NAMA RESTO", "Tanggal"], ascending=True,
        na_position="last").reset_index(drop=True)
    try:
        same = (len(g2) == len(o2)
                and np.allclose(g2["SALDO AKHIR"].fillna(-999),
                                o2["SALDO AKHIR"].fillna(-999), atol=1e-9))
    except (ValueError, KeyError):
        same = False
    if not same:
        n_bad += 1
        if n_bad <= 3:
            print(f"TRIAL {trial} MISMATCH")
            print("grouped:\n", g2[["Nama Barang", "NAMA RESTO", "Tanggal",
                                    "SALDO AKHIR"]].to_string())
            print("old:\n", o2[["Nama Barang", "NAMA RESTO", "Tanggal",
                                "SALDO AKHIR"]].to_string())

print(f"\ntrials=200, mismatch={n_bad}")
print("VERDICT running-stock turbo equivalence: "
      f"{'BUG' if n_bad else 'NOT-BUG (identik)'}")
