"""P09 — fn_rekap_mentah._combined_to_long duplicate day-column resolution
(FIX 6f-03) + min_count semantics.

Sheet pivot exports can carry BOTH a plain day column and a 'Sum of N'
aggregate for the same day (or two plain duplicates after header mangling).
Rules implemented (v3.6f-03):
 - exactly ONE 'Sum of N' among duplicates -> USE the aggregate, skip plain
 - otherwise (2+ plain / 2+ aggregates) -> SUM(min_count=1): all-NaN stays
   NaN (row dropped), any data present -> summed.

Cases:
 A. day 5 duplicated as ['5', 'Sum of 5'] with DIFFERENT values -> aggregate
    must win, plain ignored (no double count).
 B. day 7 duplicated as ['7', '7.1'] (pd.read_excel mangling) -> SUM.
 C. all-NaN duplicate day -> NaN (dropped from long output), NOT 0.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT

sys.path.insert(0, PROJECT)
from src.pipeline.fn_rekap_mentah import _combined_to_long  # noqa: E402


def main():
    cols = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS", "NAMA BARANG",
            "SATUAN", "KATEGORI",
            "1", "2", "3", "4", "5", "Sum of 5", "7", "7.1", "30", "31"]
    rows = [
        #                   d1   d2   d3   d4  d5 sum5  d7  d7.1  d30  d31
        ["MLGPAR.001", "input so harian", "SO", "OK", "GULA", "KG", "COM",
         10, None, None, None, 3, 4, None, None, None, 2],
        ["MLGPAR.001", "input so harian", "SO", "OK", "TEH", "GR", "COM",
         None, None, None, None, None, None, None, None, None, None],
    ]
    df = pd.DataFrame(rows, columns=cols)
    out = _combined_to_long(df, "berjalan", ["BARANG MASUK", "SO"])

    g = out[out["NAMA BARANG"] == "GULA"]
    t = out[out["NAMA BARANG"] == "TEH"]

    d5 = g[g["Attribute"] == 5]["Value"].tolist()
    d7 = g[g["Attribute"] == 7]["Value"].tolist()
    d1 = g[g["Attribute"] == 1]["Value"].tolist()
    t_rows = len(t)

    print(f"day5 (['5'=3, 'Sum of 5'=4]) -> {d5}")
    print(f"day7 (['7'=None, '7.1'=None]) -> {d7}")
    print(f"day1 -> {d1}")
    print(f"TEH rows surviving (all days NaN) -> {t_rows}")
    print("EXPECTED: day5=[4] (aggregate wins, 3 ignored); day7=[] (all-NaN "
          "dropped); day1=[10]; TEH rows=0")
    ok_a = d5 == [4]
    ok_b = d7 == []
    ok_c = t_rows == 0
    ok_d = d1 == [10]
    print(f"ACTUAL: A={'OK' if ok_a else 'FAIL'} B={'OK' if ok_b else 'FAIL'} "
          f"C={'OK' if ok_c else 'FAIL'} D={'OK' if ok_d else 'FAIL'}")
    verdict = ok_a and ok_b and ok_c and ok_d
    print("VERDICT:", "NOT-BUG" if verdict else
          "BUG — duplicate day-column resolution / min_count broken")


if __name__ == "__main__":
    main()
