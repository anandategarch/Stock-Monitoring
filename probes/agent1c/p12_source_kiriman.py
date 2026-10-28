"""P12 — SOURCE KIRIMAN classification + LANGKAH 5b merge (unit + E2E).

Unit: _source_kiriman_per_pair over a tagged in_df:
  P1 only 42.05        -> Internal
  P2 only 32.24/9901   -> Eksternal
  P3 42.05 + 9901      -> Campuran
  P4 no IN rows        -> absent (left-merge leaves None)
Also '42.05 (Bulan Lalu)' counts as Internal.

E2E: build_append1 tree with 4205 IN for barang I1, 3224 IN for barang E1,
rekap SO for both -> final long rows must carry SOURCE KIRIMAN Internal /
Eksternal respectively, and a rekap-only barang must have None/NaN.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.append1 import (  # noqa: E402
    _source_kiriman_per_pair, build_append1)


def unit():
    print("=== unit: classification ===")
    in_df = pd.DataFrame({
        "Nama Barang": ["P1", "P1", "P2", "P2", "P2", "P3", "P3", "P1"],
        "NAMA RESTO": ["R"] * 8,
        "SOURCE IN": ["42.05", "42.05 (Bulan Lalu)", "32.24",
                      "32.24 (Bulan Lalu)", "99.01", "42.05", "99.01",
                      "42.05"],
    })
    g = _source_kiriman_per_pair(in_df)
    m = {(r["Nama Barang"], r["NAMA RESTO"]): r["SOURCE KIRIMAN"]
         for _, r in g.iterrows()}
    print(f"  map = {m}")
    exp = {("P1", "R"): "Internal", ("P2", "R"): "Eksternal",
           ("P3", "R"): "Campuran"}
    ok = all(m.get(k) == v for k, v in exp.items()) and ("P4", "R") not in m
    print(f"  classification ok: {ok}")
    return ok


def e2e():
    print("=== E2E: LANGKAH 5b merge onto long output ===")
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("I1", "KG", "SO", "input so harian", {1: 10}),
        ("E1", "KG", "SO", "input so harian", {1: 10}),
        ("N1", "KG", "SO", "input so harian", {1: 10}),
    ])
    b_2205(root, [])
    b_4205(root, [("IT.2026.10.1", "GUDANG HO (MLGPAR)", "2026-10-05",
                   "I1", 4, "2026-10-05 08:00:00")])
    b_3224(root, [("2026-10-05", 6, "E1", "GUDANG X (MLGPAR)",
                   "RI.2026.10.0001", "PO.2026.09.001", "2026-10-05 08:00")])
    b_4217(root, [("I1", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 3}),
                  ("E1", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 3}),
                  ("N1", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 3})])
    b_dbs(root, [("I1", "COM DEVIASI - RESTO", "AKTIF"),
                 ("E1", "COM DEVIASI - RESTO", "AKTIF"),
                 ("N1", "COM DEVIASI - RESTO", "AKTIF")])
    final = build_append1(Config(make_config(root)))

    got = {}
    for b in ("I1", "E1", "N1"):
        rows = final[(final["Nama Barang"] == b) & (final["NAMA RESTO"]
                                                    == "MLGPAR")]
        v = rows["SOURCE KIRIMAN"].dropna().unique().tolist()
        got[b] = v[0] if v else None
    print(f"  SOURCE KIRIMAN: I1={got['I1']!r} E1={got['E1']!r} "
          f"N1={got['N1']!r}")
    exp = {"I1": "Internal", "E1": "Eksternal", "N1": None}
    ok = all(got[k] == v for k, v in exp.items())
    print(f"  merge ok: {ok}")
    return ok


if __name__ == "__main__":
    a = unit()
    b = e2e()
    print("\nEXPECTED: Internal/Eksternal/Campuran/None all correct")
    print("VERDICT:", "NOT-BUG" if (a and b) else "BUG — SOURCE KIRIMAN "
          "classification or 5b merge broken")
