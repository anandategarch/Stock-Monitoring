"""P01 — fn_9901 drop_duplicates() drops LEGITIMATE identical transaction rows.

Scenario: one 9901 sheet with 2 IDENTICAL lines of the same PI (same date,
same barang, same resto, same qty). Two lines of the same purchase doc with
identical qty is a normal PO/PI. v3.9.33 added a GLOBAL prom.drop_duplicates()
to defend against duplicated backup SHEETS — but it also silently deletes
legit duplicate lines IN THE SAME SHEET → IN 99.01 undercount → Selisih IN /
deviasi wrong with only a generic log line.

EXPECTED: 2 rows out, total Value = 2*qty.
ACTUAL:   1 row out, total Value = 1*qty (one transaction silently deleted).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_9901, make_config, make_root)

sys.path.insert(0, PROJECT)
from src.pipeline.fn_9901 import fn_9901  # noqa: E402


def run():
    root = make_root()
    cfg_path = make_config(root)
    from src.config import Config
    cfg = Config(cfg_path)

    qty = 7.0
    row = {
        "Nomor #": "PI.2026.09.30973",
        "Tanggal": "01/10/2026",
        "Nama barang": "AIR MINERAL 600ML",
        "Nama cabang": "1137.CKGPAH",
        "#Prime.Qty": qty,
        "Nomor # Penerimaan Barang": None,   # blank -> 9901 candidate
        "Jenis Barang Barang & Jasa": "Persediaan",
        "Nomor # Pesanan Pembelian": "PO.2026.09.00181",
    }
    # TWO identical lines on the same PI (same item twice, same qty)
    b_9901(root, [dict(row), dict(row)])

    out = fn_9901(cfg.folder("Data9901"))

    n_rows = len(out)
    total = float(out["Value"].sum()) if not out.empty else 0.0

    print(f"rows out            = {n_rows}")
    print(f"total Value (99.01) = {total}")
    print(f"EXPECTED: 2 rows, total = {2 * qty}")
    print(f"ACTUAL  : {n_rows} rows, total = {total}")

    ok = (n_rows == 2) and abs(total - 2 * qty) < 1e-9
    print("VERDICT:", "NOT-BUG" if ok else
          "BUG (P1) — legit duplicate transaction line silently dropped by "
          "global drop_duplicates(); IN 99.01 undercount -> Selisih IN / "
          "deviasi salah tanpa data-level trace")

    # Control: the case v3.9.33 actually targeted (same sheet duplicated as
    # a backup sheet) must still be deduped — confirms the trade-off is real.
    root2 = make_root()
    cfg2 = Config(make_config(root2))
    b_9901(root2, [dict(row), dict(row)], fname="a.xlsx")
    b_9901(root2, [dict(row), dict(row)], fname="b.xlsx")  # salinan file
    out2 = fn_9901(cfg2.folder("Data9901"))
    print(f"\n[control] duplicate FILE pair -> rows={len(out2)} "
          f"(dedup working as designed for that case)")


if __name__ == "__main__":
    run()
