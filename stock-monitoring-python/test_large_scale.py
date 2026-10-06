"""
test_large_scale.py — Benchmark pipeline dengan data besar (855k records simulated).
Validasi memory & speed untuk skala production.
"""
import os
import sys
import time
import shutil
import tempfile
import json
import tracemalloc
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

# Set random seed for reproducible results
np.random.seed(42)


def generate_large_append1_data(n_records: int = 855976) -> pd.DataFrame:
    """Generate DataFrame mirip output Append1 dengan n_records rows."""
    print(f"  Generating {n_records:,} mock Append1 records...")

    # Realistic domain (from sample analysis)
    barang_list = [
        "GULA (V.20)", "FRUCTOSE SYRUP (V.20)", "CINCAU (V.20)",
        "BUAH APEL (V.20)", "BUAH PEER (V.20)", "CABE RAWIT (V.20)",
        "KEJU (V.20)", "MIE (V.20)", "TEA GOPEK (V.20)", "SUSU (V.20)",
        "MINYAK GORENG (V.20)", "KECAP (V.20)", "SIRUP (V.20)",
        "KRUPUK (V.20)", "SENDOK PLASTIK (V.20)", "CUP 16 (V.20)",
    ]
    resto_list = [
        "MLGPAR", "BDGUKU", "KWGGAL", "DPKMAR", "PWKTAM", "CKGPAH",
        "BKSALT", "GGPDAA", "SBRTUP", "KWGTEL", "BJMHAS", "TGRBIN",
        "BKSSUD", "TGRGEL", "GRTSUM", "CKRBOS", "SBMOTI", "SBSHAM",
        "DPKLIM", "KGNSUD",
    ]
    tanggal_list = list(range(-25, 0)) + list(range(1, 32))  # 56 tanggal
    jenis_list = ["1.SO", "2.SALDO AKHIR", "3.DEVIASI", "4.IN",
                  "5.BARANG MASUK", "6.Selisih IN", "7.OUT", "SALDO AWAL"]
    kategori_list = ["DEVIASI", "USAGE", "CONSUME"]
    source_list = ["INTERNAL", "EKSTERNAL"]

    # Generate random combinations
    n = n_records
    df = pd.DataFrame({
        "Nama Barang": np.random.choice(barang_list, n),
        "NAMA RESTO": np.random.choice(resto_list, n),
        "Tanggal": np.random.choice(tanggal_list, n),
        "JENIS": np.random.choice(jenis_list, n),
        "NILAI": np.random.randint(-1000000, 1000000, n).astype("float64"),
        "Nomor": np.random.choice([None, "IT.2026.09.0001", "IT.2026.09.0002", ""], n, p=[0.7, 0.1, 0.1, 0.1]),
        "Nomor PO": np.random.choice([None, "PO.2026.09.0001", ""], n, p=[0.8, 0.1, 0.1]),
        "#Tgl/Jam Pembuatan IT": np.random.choice([None, "05/09/2026 16:52:12", ""], n, p=[0.7, 0.2, 0.1]),
        "KATEGORI": np.random.choice(kategori_list + [None], n, p=[0.3, 0.3, 0.3, 0.1]),
        "SOURCE KIRIMAN": np.random.choice(source_list + [None], n, p=[0.45, 0.45, 0.1]),
    })

    print(f"  Generated: {len(df):,} rows, {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    return df


def generate_large_rincian_po_data(n_records: int = 5000) -> pd.DataFrame:
    """Generate DataFrame mirip output Rincian PO."""
    print(f"  Generating {n_records:,} mock Rincian PO records...")
    n = n_records
    df = pd.DataFrame({
        "Nomor #": [f"PO.2026.09.{i:05d}" for i in np.random.randint(1, 1000, n)],
        "Tanggal": pd.to_datetime(np.random.choice(
            pd.date_range("2026-08-01", "2026-09-29"), n
        )),
        "Cabang PO": np.random.choice(["1370.MLGPAR", "1370.BDGUKU", "1370.KWGGAL"] * 7, n),
        "Pemasok": np.random.choice([
            "PT KREASI REMPAH INDONESIA", "PT SUMBER MAKMUR", "PT JAYA ABADI"
        ], n),
        "Nama Barang": np.random.choice(["GULA (V.20)", "FRUCTOSE SYRUP (V.20)", "CINCAU (V.20)"] * 5, n),
        "Satuan": np.random.choice(["KG", "LITER", "BKS"], n),
        "Kuantitas": np.random.randint(1, 100, n),
        "@Harga": np.random.choice([27000, 15000, 50000], n),
        "Total Harga": np.random.randint(14000, 16000000, n),
        "Keterangan PO": np.random.choice(["REP", "RESTO", "STOCK"], n),
        "Status Pesanan Pembelian": np.random.choice(
            ["Menunggu diproses", "Diproses", "Selesai"], n
        ),
        "Tgl/Jam Pembuatan": pd.to_datetime(np.random.choice(
            pd.date_range("2026-07-27", "2026-09-25"), n
        )),
        "DBS_Kategori.KATEGORI": "DEVIASI",
    })
    df["Total Harga"] = df["Kuantitas"] * df["@Harga"]
    print(f"  Generated: {len(df):,} rows, {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    return df


def run_benchmark():
    """Run large-scale benchmark."""
    print("=" * 70)
    print("  LARGE-SCALE BENCHMARK (855k records simulation)")
    print("=" * 70)

    # Track memory
    tracemalloc.start()

    # 1. Generate large mock data (matches sample scale)
    print("\n  [1] Generating large mock data...")
    t0 = time.time()
    append1_df = generate_large_append1_data(855976)
    rincian_po_df = generate_large_rincian_po_data(5000)
    t_gen = time.time() - t0
    print(f"  Generation time: {t_gen:.2f}s")

    current, peak = tracemalloc.get_traced_memory()
    print(f"  Memory after generation: {peak / 1024 / 1024:.0f} MB peak")

    # 2. Generate Excel output (the real benchmark)
    # FIX: Excel output was removed in commit 01940a5 ("hapus Excel output,
    # tampilkan pivot table langsung di UI"). Skip this section gracefully.
    print("\n  [2] Skipping Excel output benchmark (feature removed — pipeline now displays in-app)")
    t_excel = 0.0
    result = None

    current, peak = tracemalloc.get_traced_memory()
    print(f"\n  Excel generation time: SKIPPED")
    print(f"  Peak memory during gen: {peak / 1024 / 1024:.0f} MB")

    # 3. Verify output (skipped — no Excel file to verify)
    print("\n  [3] Verifying output (skipped — no Excel file)")
    output_size = 0
    print(f"  Output file size: N/A")

    # FIX: skip zipfile verification — no Excel file to inspect (feature removed)

    # 4. Performance summary
    print("\n" + "=" * 70)
    print("  BENCHMARK RESULTS")
    print("=" * 70)
    print(f"  Records processed:  {len(append1_df):,} (Append1) + {len(rincian_po_df):,} (Rincian PO)")
    print(f"  Data gen time:      {t_gen:.2f} seconds")
    print(f"  Peak memory:        {peak / 1024 / 1024:.0f} MB")
    print(f"  Excel output:       SKIPPED (feature removed)")
    print("=" * 70)

    # Cleanup
    tracemalloc.stop()

    # Performance targets
    print("\n  Performance assessment:")
    # FIX: skip Excel gen target (feature removed)
    print(f"  • Excel gen target: SKIPPED (feature removed)")

    if peak < 2048 * 1024 * 1024:
        print(f"  ✓ PEAK MEMORY < 2 GB (target met: {peak / 1024 / 1024:.0f} MB)")
    else:
        print(f"  ⚠ PEAK MEMORY > 2 GB ({peak / 1024 / 1024:.0f} MB)")

    return True


if __name__ == "__main__":
    try:
        success = run_benchmark()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
