"""P03 — pd.merge NA-key semantics vs append1 LANGKAH 3 (information merge).

append1 merges `renamed` (pivot output; keeps NA Tanggal groups because the
groupby uses dropna=False) with `information_grouped` (_group_info_columns;
also built with dropna=False) on KeyColumns = [Nama Barang, NAMA RESTO,
Tanggal]. Rows whose Tanggal is NA (e.g. 32.24/9901 rows with blank date)
only keep their Nomor/Nomor PO if pandas merge MATCHES NA==NA on join keys.

Part 1: establish pandas 2.2.3 merge behavior for NaN / pd.NA keys.
Part 2: E2E — 32.24 file with one row dated, one row blank-date, distinct
         Nomor RI each. Check the blank-date IN row survives AND keeps its
         Nomor in append1 long output.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    long_subset, make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.append1 import build_append1  # noqa: E402


def part1():
    print("=== Part 1: pd.merge NA-key semantics (pandas", pd.__version__, ") ===")
    left = pd.DataFrame({"k": [np.nan, 1.0], "v": ["L-na", "L-1"]})
    right = pd.DataFrame({"k": [np.nan, 1.0], "w": ["R-na", "R-1"]})
    m = left.merge(right, on="k", how="left")
    print("float-NaN keys ->", m.to_dict("records"))

    li = pd.DataFrame({"k": pd.array([pd.NA, 1], dtype="Int64"),
                       "v": ["L-na", "L-1"]})
    ri = pd.DataFrame({"k": pd.array([pd.NA, 1], dtype="Int64"),
                       "w": ["R-na", "R-1"]})
    mi = li.merge(ri, on="k", how="left")
    print("Int64-NA keys  ->", mi.to_dict("records"))
    nan_match = m.loc[m["v"] == "L-na", "w"].notna().all()
    na_match = mi.loc[mi["v"] == "L-na", "w"].notna().all()
    print(f"NaN-key matched: {nan_match}; pd.NA(Int64)-key matched: {na_match}")


def part2():
    print("\n=== Part 2: E2E blank-date 32.24 row keeps its Nomor? ===")
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("GULA (V.20)", "KG", "SO", "input so harian", {1: 100}),
        ("GULA (V.20)", "KG", "BARANG MASUK", "input so harian", {1: 50}),
    ])
    b_2205(root, [])
    b_4205(root, [])
    # one dated RI row + one blank-date RI row, distinct doc numbers
    b_3224(root, [
        ("2026-10-05", 20, "GULA (V.20)", "GUDANG X (MLGPAR)",
         "RI.2026.10.0001", "PO.2026.09.001", "2026-10-05 08:00:00"),
        (None, 13, "GULA (V.20)", "GUDANG X (MLGPAR)",
         "RI.2026.10.0002", "PO.2026.09.002", "2026-10-06 08:00:00"),
    ])
    b_4217(root, [("GULA (V.20)", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 80})])
    b_dbs(root, [("GULA (V.20)", "COM DEVIASI - RESTO", "AKTIF")])
    cfg = Config(make_config(root))
    final = build_append1(cfg)

    ins = final[final["JENIS"] == "4.IN"][
        ["Nama Barang", "NAMA RESTO", "Tanggal", "NILAI", "Nomor"]]
    print("IN rows:")
    print(ins.to_string(index=False))
    na_rows = ins[ins["Tanggal"].isna()]
    dated = ins[ins["Tanggal"] == 5]
    print("EXPECTED: 2 IN rows — t=5 with Nomor 'RI.2026.10.0001', "
          "t=NA with Nomor 'RI.2026.10.0002'")
    got_na_nomor = (len(na_rows) == 1
                    and str(na_rows["Nomor"].iloc[0]) == "RI.2026.10.0002")
    got_dated = (len(dated) == 1
                 and str(dated["Nomor"].iloc[0]) == "RI.2026.10.0001")
    print(f"ACTUAL  : dated row ok={got_dated}; NA-date row present="
          f"{len(na_rows) == 1}, Nomor="
          f"{na_rows['Nomor'].iloc[0] if len(na_rows) else None!r}")
    print("VERDICT:", "NOT-BUG" if (got_na_nomor and got_dated) else
          "BUG — NA-Tanggal group loses its Nomor in LANGKAH 3 merge "
          "(merge does not match NA keys)")


if __name__ == "__main__":
    part1()
    part2()
