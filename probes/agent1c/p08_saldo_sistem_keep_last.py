"""P08 — saldo-sistem 42.17 'keep=last by filename order' uses LEXICOGRAPHIC
sort, so unpadded numeric snapshot names pick the WRONG 'latest' file.

append1 (v3.11) builds saldo_sistem_out['map'] with
drop_duplicates(subset=[pair], keep='last') over frames concatenated in
_list_excel_files() order = sorted() (lexicographic). The docstring claims
'snapshot TERAKHIR (urutan nama file) menang — file 42.17 ditarik berkali-
kali sepanjang bulan'. With human-typed unpadded names
('snapshot 2.xlsx' vs 'snapshot 10.xlsx'), lexicographic order puts
'2' AFTER '10' — the app overrides the kolom Sistem with the OLDER snapshot.

Files: snapshot 1.xlsx (saldo 10) / snapshot 10.xlsx (saldo 99) /
       snapshot 2.xlsx (saldo 20) for pair GULA/MLGPAR.
EXPECTED (user intent, 'latest snapshot wins'): 99 (snapshot 10).
ACTUAL: 20 (snapshot 2 — lexicographically last).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.append1 import build_append1  # noqa: E402

KAT = "10.FOOD [RM] - COM V.2"


def main():
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("GULA (V.20)", "KG", "SO", "input so harian", {1: 100}),
    ])
    b_2205(root, [])
    b_4205(root, [])
    b_3224(root, [])
    b_4217(root, [("GULA (V.20)", KAT, "KG", {"RESTO MALANG (MLGPAR)": 80})])
    b_dbs(root, [("GULA (V.20)", "COM DEVIASI - RESTO", "AKTIF")])

    # saldo sistem snapshots: 1 -> 10, 10 -> 99, 2 -> 20 (numeric latest=10)
    for fname, saldo in (("snapshot 1.xlsx", 10), ("snapshot 10.xlsx", 99),
                         ("snapshot 2.xlsx", 20)):
        b_4217(root, [("GULA (V.20)", KAT, "KG",
                       {"RESTO MALANG (MLGPAR)": saldo})],
               folder="6. 42.17", fname=fname)

    out = {}
    build_append1(Config(make_config(root)), saldo_sistem_out=out)
    ss = out.get("map", {})
    got = ss.get(("GULA (V.20)", "MLGPAR"))

    # what the view would do with it (deviasi_view override value)
    print(f"s map = {ss}")
    print("EXPECTED: 99 (snapshot 10 = numerically latest pull)")
    print(f"ACTUAL  : {got}")
    print("VERDICT:", "NOT-BUG" if got == 99 else
          "BUG (P3) — keep='last' over lexicographically sorted filenames: "
          "unpadded numeric snapshot names ('2' > '10') make an OLDER "
          "snapshot win the Sistem override silently (zero-padded/ISO-dated "
          "names unaffected)")


if __name__ == "__main__":
    main()
