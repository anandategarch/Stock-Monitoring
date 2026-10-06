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
- Flag 'started' sekali True, tetap True (tidak bisa un-start).

OPTIMIZED untuk data besar:
- Pakai numpy arrays (bukan pandas loop) untuk speed
- Pre-sort sekali di luar, bukan di dalam fungsi
- Groupby di caller pakai sort-based approach
"""
import pandas as pd
import numpy as np
from typing import List


def fn_running_stock(t: pd.DataFrame) -> pd.DataFrame:
    """
    Mirror M: fnRunningStock(t).

    Input: t dengan minimal kolom Tanggal, IN, OUT, SALDO AWAL.
           (sudah grouped by Nama Barang + NAMA RESTO oleh caller)

    Output: t dengan tambahan kolom "SALDO AKHIR" (numeric).
    """
    # Edge case: empty group
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

    # 2. SORT by Tanggal ascending (mirror Table.Sort)
    srt = t.sort_values("Tanggal", ascending=True, na_position="last").reset_index(drop=True)

    # 3. CONVERT to numpy arrays (much faster than pandas loop)
    dates_arr = srt["Tanggal"].to_numpy(dtype="float64")  # NaN untuk null
    ins_arr = srt["IN"].fillna(0).to_numpy(dtype="float64") if "IN" in srt.columns else np.zeros(len(srt))
    outs_arr = srt["OUT"].fillna(0).to_numpy(dtype="float64") if "OUT" in srt.columns else np.zeros(len(srt))
    n = len(srt)

    # 4. RUNNING STOCK — vectorized-ish loop (single pass, minimal allocations)
    # Mirror M List.Generate dengan state [started, saldo]
    if n == 0:
        srt["SALDO AKHIR"] = []
        return srt

    saldo_arr = np.zeros(n, dtype="float64")
    started = False
    saldo = 0.0

    for i in range(n):
        tgl = dates_arr[i]
        # Handle NaN (np.isnan) → treat as 0 (which is < 1 → saldo = 0)
        if np.isnan(tgl):
            tgl = 0.0

        # isStarted = if tgl >= 1 then true else [started]
        if tgl >= 1:
            is_started = True
        else:
            is_started = started  # keep previous

        # newSaldo logic
        if is_started:
            if started:
                # Already started → continue accumulating
                saldo = saldo + ins_arr[i] - outs_arr[i]
            else:
                # Just starting → seed with SaldoAwal
                saldo = saldo_awal + ins_arr[i] - outs_arr[i]
        else:
            # Not started → saldo = 0
            saldo = 0.0

        started = is_started
        saldo_arr[i] = saldo

    # 5. GABUNGKAN KEMBALI: tambah kolom "SALDO AKHIR"
    srt["SALDO AKHIR"] = saldo_arr

    return srt


def fn_running_stock_grouped(df: pd.DataFrame, group_keys: list) -> pd.DataFrame:
    """
    OPTIMIZED version: apply fn_running_stock to all groups at once.
    Lebih cepat dari df.groupby(keys).apply(fn_running_stock) karena:
    - Pre-sort sekali by (group_keys + Tanggal)
    - Iterasi grup dengan loop C-level (pandas groupby)
    - Hindari overhead apply per grup

    Args:
        df: DataFrame with columns group_keys + [Tanggal, IN, OUT, SALDO AWAL]
        group_keys: list of column names to group by

    Returns:
        DataFrame with added "SALDO AKHIR" column.
    """
    if df.empty:
        result = df.copy()
        result["SALDO AKHIR"] = pd.Series(dtype="float64")
        return result

    # Pre-sort by group_keys + Tanggal (single sort, faster than per-group sort)
    sort_cols = group_keys + ["Tanggal"]
    df_sorted = df.sort_values(sort_cols, ascending=True, na_position="last").reset_index(drop=True)

    # Apply fn_running_stock per group using groupby (C-level iteration)
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
