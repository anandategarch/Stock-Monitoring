"""
main.py — Pipeline runner (orchestrator).
Menjalankan seluruh pipeline: build Append1 + Rincian PO → generate Excel output.

Bisa dipanggil langsung (CLI) atau dari UI Tkinter.
"""
import sys
import os
import time
import warnings
from pathlib import Path

# Suppress openpyxl noise warnings (no default style, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Tambah parent dir ke sys.path untuk import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.pipeline.append1 import build_append1
from src.pipeline.rincian_po import build_rincian_po
from src.excel.excel_output import generate_output


def run_pipeline(config_path: str = None, output_path: str = None, verbose: bool = True) -> str:
    """
    Jalankan pipeline lengkap.

    Args:
        config_path: Path ke config.json (default: config.json di root project)
        output_path: Path output xlsx (default: dari config)
        verbose: Print progress

    Returns:
        Path ke output file.
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
        print(f"  Output: {output_path or config.default_output()}")

    # 2. Build Append1
    if verbose:
        print("\n" + "-" * 60)
        print("  [1/3] Building Append1 (main pipeline)...")
        print("-" * 60)

    append1_df = build_append1(config)

    if verbose:
        print(f"\n  Append1 result: {len(append1_df)} rows")
        if not append1_df.empty:
            print(f"  Columns: {list(append1_df.columns)}")

    # 3. Build Rincian PO
    if verbose:
        print("\n" + "-" * 60)
        print("  [2/3] Building Rincian PO...")
        print("-" * 60)

    rincian_po_df = build_rincian_po(config)

    if verbose:
        print(f"\n  Rincian PO result: {len(rincian_po_df)} rows")

    # 4. Generate Excel output
    if verbose:
        print("\n" + "-" * 60)
        print("  [3/3] Generating Excel output...")
        print("-" * 60)

    if output_path is None:
        output_path = config.default_output()

    result_path = generate_output(append1_df, rincian_po_df, config.template_path(), output_path)

    elapsed = time.time() - start_time
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"  SELESAI dalam {elapsed:.1f} detik")
        print(f"  Output: {result_path}")
        print(f"{'=' * 60}")

    return result_path


if __name__ == "__main__":
    # CLI mode
    import argparse
    parser = argparse.ArgumentParser(description="Stock Monitoring Pipeline")
    parser.add_argument("--config", default=None, help="Path ke config.json")
    parser.add_argument("--output", default=None, help="Path output xlsx")
    args = parser.parse_args()

    try:
        run_pipeline(config_path=args.config, output_path=args.output)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
