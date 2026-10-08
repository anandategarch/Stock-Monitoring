"""
main.py — Pipeline runner (orchestrator).
Menjalankan pipeline: build Append1 + Rincian PO → return DataFrames.
Tidak ada Excel output — data ditampilkan langsung di UI.

Bisa dipanggil langsung (CLI) atau dari UI Tkinter.
"""
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

# Suppress openpyxl noise warnings (no default style, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Tambah parent dir ke sys.path untuk import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.pipeline.append1 import build_append1
from src.pipeline.rincian_po import build_rincian_po


class PipelineStopped(Exception):
    """Raised when user requests stop via UI Stop button."""
    pass


def run_pipeline(config_path: str = None, verbose: bool = True, stop_event=None):
    """
    Jalankan pipeline lengkap. Return DataFrames (no Excel output).

    Args:
        config_path: Path ke config.json (default: config.json di root project)
        verbose: Print progress
        stop_event: threading.Event — jika set, pipeline akan berhenti di checkpoint
                    berikutnya dengan raise PipelineStopped

    Returns:
        Tuple (append1_df, rincian_po_df, in_detail_df)
        v3.4: in_detail_df = detail IN per dokumen (42.05 / 32.24 / 99.01
        + nomor) untuk tab "Rekap Selisih IN".
    """
    start_time = time.time()

    # 1. Load config
    if verbose:
        print("=" * 60)
        print("  STOCK MONITORING - PIPELINE RUNNER")
        print("=" * 60)

    config = Config(config_path)

    if verbose:
        print(f"\n  RootPath: {config.RootPath}")
        print(f"  Mode: {'LIGHT' if config.LightMode else 'FULL'}")

    # 2. Build Append1 (+ IN detail v3.4)
    if verbose:
        print("\n" + "-" * 60)
        print("  [1/2] Building Append1 (main pipeline)...")
        print("-" * 60)

    in_detail_holder: dict = {}
    append1_df = build_append1(config, stop_event=stop_event,
                               in_detail_out=in_detail_holder)

    # FIX: check stop_event after Append1 build
    if stop_event is not None and stop_event.is_set():
        raise PipelineStopped("Pipeline dihentikan oleh user setelah Append1")

    if verbose:
        print(f"\n  Append1 result: {len(append1_df)} rows")
        if not append1_df.empty:
            print(f"  Columns: {list(append1_df.columns)}")

    # 3. Build Rincian PO
    if verbose:
        print("\n" + "-" * 60)
        print("  [2/2] Building Rincian PO...")
        print("-" * 60)

    rincian_po_df = build_rincian_po(config)

    # FIX: check stop_event after Rincian PO build
    if stop_event is not None and stop_event.is_set():
        raise PipelineStopped("Pipeline dihentikan oleh user setelah Rincian PO")

    if verbose:
        print(f"\n  Rincian PO result: {len(rincian_po_df)} rows")

    in_detail_df = in_detail_holder.get("df")
    if in_detail_df is None:
        in_detail_df = pd.DataFrame()
    if verbose:
        print(f"  IN detail (v3.4): {len(in_detail_df)} rows")

    elapsed = time.time() - start_time
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"  SELESAI dalam {elapsed:.1f} detik")
        print(f"  Append1: {len(append1_df)} rows | Rincian PO: {len(rincian_po_df)} rows"
              f" | IN detail: {len(in_detail_df)} rows")
        print(f"{'=' * 60}")

    return append1_df, rincian_po_df, in_detail_df


if __name__ == "__main__":
    # CLI mode — just run pipeline and print summary
    import argparse
    parser = argparse.ArgumentParser(description="Stock Monitoring Pipeline")
    parser.add_argument("--config", default=None, help="Path ke config.json")
    args = parser.parse_args()

    try:
        append1_df, rincian_po_df, in_detail_df = run_pipeline(
            config_path=args.config)
        print(f"\nAppend1: {len(append1_df)} rows")
        print(f"Rincian PO: {len(rincian_po_df)} rows")
        print(f"IN detail: {len(in_detail_df)} rows")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
