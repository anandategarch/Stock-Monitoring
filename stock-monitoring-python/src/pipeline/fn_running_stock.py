"""
fn_running_stock.py — Mirror SANGAT PERSIS fnRunningStock di M code.
Algoritma running balance per (Nama Barang, NAMA RESTO).

LOGIKA (dari M code List.Generate):
- Tanggal < 1  (bulan lalu)  → SALDO AKHIR = 0
- Tanggal >= 1 (bulan berjalan):
  - Jika BELUM pernah started (first time tgl >= 1):
      SALDO AKHIR = SaldoAwal + IN - OUT
  - Jika SUDAH started:
      SALDO AKHIR = previous_saldo + IN - OUT
- Flag 'started' sekali True, tetap True.

ULTRA-OPTIMIZED untuk data besar:
- Vectorized dengan numpy cumsum trick (no Python loop!)
- Pre-sort sekali di luar
- Groupby di caller pakai sort-based approach
"""
import pandas as pd
import numpy as np
from typing import List


def fn_running_stock(t: pd.DataFrame) -> pd.DataFrame:
    """
    Mirror M: fnRunningStock(t).

    Input: t dengan minimal kolom Tanggal, IN, OUT, SALDO AWAL.
    Output: t dengan tambahan kolom "SALDO AKHIR".
    """
    if t is None or t.empty:
        result = t.copy() if t is not None else pd.DataFrame()
        result["SALDO AKHIR"] = pd.Series(dtype="float64")
        return result

    # 1. SALDO AWAL = List.Max(t[SALDO AWAL])
    if "SALDO AWAL" in t.columns:
        saldo_awal = t["SALDO AWAL"].max()
        if pd.isna(saldo_awal):
            saldo_awal = 0.0
    else:
        saldo_awal = 0.0

    # 2. SORT by Tanggal ascending
    srt = t.sort_values("Tanggal", ascending=True, na_position="last").reset_index(drop=True)

    # 3. CONVERT to numpy arrays
    n = len(srt)
    dates_arr = srt["Tanggal"].to_numpy(dtype="float64")  # NaN for null
    ins_arr = srt["IN"].fillna(0).to_numpy(dtype="float64") if "IN" in srt.columns else np.zeros(n)
    outs_arr = srt["OUT"].fillna(0).to_numpy(dtype="float64") if "OUT" in srt.columns else np.zeros(n)

    if n == 0:
        srt["SALDO AKHIR"] = []
        return srt

    # 4. VECTORIZED running stock (no Python loop!)
    # Logic:
    #   - For Tanggal < 1: saldo = 0
    #   - For Tanggal >= 1 (first time): saldo = SaldoAwal + IN - OUT
    #   - For Tanggal >= 1 (after started): saldo = prev_saldo + IN - OUT
    #
    # Equivalent to:
    #   net = IN - OUT
    #   For rows where Tanggal >= 1: saldo = SaldoAwal + cumsum(net) from start_idx onward
    #   For rows where Tanggal < 1: saldo = 0
    #   BUT: once started, ALL subsequent rows (even if Tanggal < 1 again) keep accumulating.
    #   Since data is sorted by Tanggal ascending, once Tanggal >= 1, all subsequent are >= 1.
    #   So: find first index where Tanggal >= 1 → start_idx
    #   saldo[0:start_idx] = 0
    #   saldo[start_idx] = SaldoAwal + net[start_idx]
    #   saldo[start_idx+1:] = saldo[start_idx] + cumsum(net[start_idx+1:])

    # Find start_idx: first index where Tanggal >= 1
    # Handle NaN in dates_arr: np.isnan → treat as < 1
    valid_dates = np.where(np.isnan(dates_arr), -np.inf, dates_arr)
    started_mask = valid_dates >= 1
    saldo_arr = np.zeros(n, dtype="float64")

    if started_mask.any():
        start_idx = np.argmax(started_mask)  # first True index
        net = ins_arr - outs_arr

        # saldo[start_idx] = SaldoAwal + net[start_idx]
        # saldo[start_idx+1:] = SaldoAwal + cumsum(net[start_idx:])
        cumsum_net = np.cumsum(net[start_idx:])
        saldo_arr[start_idx:] = saldo_awal + cumsum_net
        # Rows before start_idx remain 0 (already initialized)

    # 5. GABUNGKAN KEMBALI
    srt["SALDO AKHIR"] = saldo_arr

    return srt


def fn_running_stock_grouped(df: pd.DataFrame, group_keys: list) -> pd.DataFrame:
    """
    OPTIMIZED: apply fn_running_stock to all groups at once.
    Pre-sort by (group_keys + Tanggal), then iterate groups with C-level groupby.
    """
    if df.empty:
        result = df.copy()
        result["SALDO AKHIR"] = pd.Series(dtype="float64")
        return result

    # Pre-sort by group_keys + Tanggal
    sort_cols = group_keys + ["Tanggal"]
    df_sorted = df.sort_values(sort_cols, ascending=True, na_position="last").reset_index(drop=True)

    # Apply fn_running_stock per group
    results = []
    for group_vals, group_df in df_sorted.groupby(group_keys, sort=False, dropna=False):
        result = fn_running_stock(group_df)
        results.append(result)

    if results:
        combined = pd.concat(results, ignore_index=True)
    else:
        combined = df_sorted.copy()
        combined["SALDO AKHIR"] = 0.0

    return combined
