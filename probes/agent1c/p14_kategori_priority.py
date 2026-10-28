"""P14 — KATEGORI priority chain: manual (5d) > rekap (5c) > master (5),
all via normalized Nama Barang keys.

Scenario (drift everywhere):
  master DBS  : 'GULA (V.20)'  -> 'MASTER KAT'
  rekap       : 'gula (v.20) ' -> 'REKAP KAT'   (case + trailing space)
  manual (cfg): 'Gula  (V.20)' -> 'MANUAL KAT'  (double space, mixed case)
  barang E1   : only in master -> stays 'MASTER KAT'

EXPECTED (with KategoriManual): GULA -> 'MANUAL KAT'; E1 -> 'MASTER KAT'.
EXPECTED (without manual)     : GULA -> 'REKAP KAT'; E1 -> 'MASTER KAT'.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.append1 import build_append1  # noqa: E402


def run(manual):
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("gula (v.20) ", "KG", "SO", "input so harian", {1: 10},
         "REKAP KAT"),
        ("E1", "KG", "SO", "input so harian", {1: 4}),
    ])
    b_2205(root, [])
    b_4205(root, [])
    b_3224(root, [])
    b_4217(root, [("GULA (V.20)", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 3}),
                  ("E1", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 1})])
    b_dbs(root, [("GULA (V.20)", "MASTER KAT", "AKTIF"),
                 ("E1", "MASTER KAT", "AKTIF")])
    extra = {"KategoriManual": {"Gula (V.20)": "MANUAL KAT"}} if manual \
        else None
    final = build_append1(Config(make_config(root, extra=extra)))

    def kat(b):
        r = final[(final["Nama Barang"] == b) & (final["JENIS"] == "1.SO")]
        return r["KATEGORI"].iloc[0] if len(r) else None

    return kat("GULA (V.20)"), kat("E1")


if __name__ == "__main__":
    g_m, e_m = run(manual=True)
    g_r, e_r = run(manual=False)
    print(f"with manual    : GULA={g_m!r} E1={e_m!r}")
    print(f"without manual : GULA={g_r!r} E1={e_r!r}")
    print("EXPECTED: manual -> ('MANUAL KAT', 'MASTER KAT'); "
          "no manual -> ('REKAP KAT', 'MASTER KAT')")
    ok = (g_m == "MANUAL KAT" and e_m == "MASTER KAT"
          and g_r == "REKAP KAT" and e_r == "MASTER KAT")
    print("VERDICT:", "NOT-BUG" if ok else
          "BUG — kategori priority chain / normalized keys broken")
