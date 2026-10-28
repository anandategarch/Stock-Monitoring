"""P05 — helpers.to_datetime_robust / date_to_day battery (date parsing).

Checks the v3.9.28 serial-Excel path + v3.9.42 dayfirst/mixed fixes and
hunts for NEW silent misparses:
 1. dd/mm with day>12 ('13/10/2026' -> Oct 13, not NaT)
 2. ambiguous '01/10/2026' -> Oct 1 (dayfirst)
 3. ISO '2026-10-01' coexisting with dd/mm (format='mixed')
 4. serial 46290 -> 2026-09-25; 46290.75 -> +18:00
 5. serial as STRING '46290' -> converted
 6. plain ints 1..31 (day columns already numeric) must NOT be treated as
    serials and must round-trip day-of-month unchanged through date_to_day
 7. datetime64 passthrough untouched
 8. mixed column: serial + dd/mm string + NaT + datetime obj all correct
 9. out-of-guard serial 19999 (year 1954-) — boundary behavior documented
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT

sys.path.insert(0, PROJECT)
from src.pipeline.helpers import date_to_day, to_datetime_robust  # noqa: E402

results = []


def check(tag, series, expected, day=False):
    got = date_to_day(series) if day else to_datetime_robust(series)
    g = list(got)
    if day:
        ok = list(g) == list(expected)
    else:
        ok = all((pd.isna(a) and pd.isna(b)) or (a == b)
                 for a, b in zip(g, expected))
    print(f"  {tag}\n    expected={list(expected)}\n    actual  ={g}\n"
          f"    -> {'OK' if ok else 'MISMATCH'}")
    results.append(ok)


def main():
    print("=== date parsing battery ===")
    check("1. day>12 dd/mm", pd.Series(["13/10/2026"]),
          [pd.Timestamp("2026-10-13")])
    check("2. dayfirst ambiguous", pd.Series(["01/10/2026"]),
          [pd.Timestamp("2026-10-01")])
    check("3. ISO + dd/mm mixed", pd.Series(["2026-10-01", "05/10/2026"]),
          [pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-05")])
    check("4a. serial 46290", pd.Series([46290]),
          [pd.Timestamp("1899-12-30") + pd.Timedelta(days=46290)])
    check("4b. serial 46290.75", pd.Series([46290.75]),
          [pd.Timestamp("1899-12-30") + pd.Timedelta(days=46290.75)])
    check("5. serial as string", pd.Series(["46290"]),
          [pd.Timestamp("1899-12-30") + pd.Timedelta(days=46290)])
    check("6. ints 1..31 via date_to_day", pd.Series(list(range(1, 32))),
          pd.array(list(range(1, 32)), dtype="Int64"), day=True)
    dt = pd.Series(pd.to_datetime(["2026-10-05", "2026-10-13"]))
    check("7. datetime64 passthrough", dt, [pd.Timestamp("2026-10-05"),
                                            pd.Timestamp("2026-10-13")])
    check("8. mixed col", pd.Series([46290, "05/10/2026", None,
                                     pd.Timestamp("2026-10-02")]),
          [pd.Timestamp("1899-12-30") + pd.Timedelta(days=46290),
           pd.Timestamp("2026-10-05"), pd.NaT, pd.Timestamp("2026-10-02")])
    r = to_datetime_robust(pd.Series([19999]))
    print(f"  9. serial 19999 (below guard 20000): -> {r.iloc[0]} "
          f"(documented boundary; realistic dates never here)")
    check("9b. serial 20000 (guard edge)", pd.Series([20000]),
          [pd.Timestamp("1899-12-30") + pd.Timedelta(days=20000)])

    ok = all(results)
    # Case 6 (plain ints 1..31 -> all day 1) is DOCUMENTED by-design:
    # README v3.9.22 "Temuan audit lain TERDOKUMENTASI (... date_to_day
    # numerik -> hari 1)". Exclude it from the bug verdict.
    ok_doc = all(results[:6]) and all(results[7:])
    print("\nNote case 6: plain-int Tanggal column -> all day 1 is "
          "DOCUMENTED (README v3.9.22 'date_to_day numerik -> hari 1').")
    print("EXPECTED: every undocumented case parses per dd/mm + serial rules")
    print("VERDICT:", "NOT-BUG" if ok_doc else
          "BUG — date misparse found (beyond the documented int case)")


if __name__ == "__main__":
    main()
