#!/usr/bin/env python3
"""p01 — Paritas format angka antar view (scope: formatting parity).

Bandingkan perilaku _fmt_num/_format_num SETIAP view pada input yang sama:
None, NaN (float/np.float64/pd.NA), 0, -0.0, pecahan, negatif, besar.

Klaim docstring tiap view: "identik view lain" / "identik pivot_view.
_format_num" / "pola DeviasiView._fmt_num".
"""
import sys
import math
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import numpy as np
import pandas as pd

from src.ui.deviasi_view import DeviasiView
from src.ui.komparasi_deviasi_view import KomparasiDeviasiView
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.rincian_po_view import RincianPoView
from src.ui.pivot_view import PivotTableView
from src.ui.deviasi_popup import DeviasiPopup
from src.ui.in_selisih_view import _fmt_num as in_sel_fmt
from src.ui.details_popup import DetailsPopup
from src.ui.followup_view import FollowUpView
from src.ui import nominal_common as nc

FUNCS = {
    "deviasi._fmt_num":        DeviasiView._fmt_num,
    "komparasi._fmt_num":      KomparasiDeviasiView._fmt_num,
    "in_selisih._fmt_num":     in_sel_fmt,
    "laporan._fmt_num":        LaporanDeviasiView._fmt_num,
    "rincian_po._fmt_num":     RincianPoView._fmt_num,
    "pivot._format_num":       PivotTableView._format_num,
    "deviasi_popup._fmt_num":  DeviasiPopup._fmt_num,
    "followup._fu_num":        FollowUpView._fu_num,
}

CASES = [
    ("None", None),
    ("float nan", float("nan")),
    ("np.float64 nan", np.float64("nan")),
    ("pd.NA", pd.NA),
    ("0 int", 0),
    ("0.0", 0.0),
    ("-0.0", -0.0),
    ("7.5", 7.5),
    ("-1234.5", -1234.5),
    ("1234567.0", 1234567.0),
    ("np.int64 42", np.int64(42)),
]

hdr = f"{'input':<16}" + "".join(f"{k:<26}" for k in FUNCS)
print(hdr)
print("-" * len(hdr))
results = {}
for name, val in CASES:
    row = []
    for fname, fn in FUNCS.items():
        try:
            out = fn(val)
        except Exception as e:  # noqa: BLE001
            out = f"<RAISE {type(e).__name__}>"
        row.append(repr(out))
        results[(name, fname)] = out
    print(f"{name:<16}" + "".join(f"{c:<26}" for c in row))

# ekstra: fmt rupiah/persen nominal_common (konvensi sendiri — cek NaN/0)
print()
print("nominal_common.fmt_rp_cell:", [nc.fmt_rp_cell(v) for v in
                                      (None, float("nan"), 0, -1825.5)])
print("nominal_common.fmt_pct_cell:", [nc.fmt_pct_cell(v) for v in
                                       (None, float("nan"), 0, 12.45, -8.3)])

# ---- VERDICT logic -------------------------------------------------------
nan_cell = {}
for name in ("None", "float nan", "np.float64 nan", "pd.NA"):
    for fname in FUNCS:
        nan_cell.setdefault(name, {})[fname] = results[(name, fname)]

distinct_nan = {}
for fname in FUNCS:
    key = tuple(nan_cell[n][fname] for n in nan_cell)
    distinct_nan.setdefault(key, []).append(fname)

zero_cell = {fname: results[("0.0", fname)] for fname in FUNCS}

print()
print("=== ANALISIS ===")
print("1) NaN/None display per view:")
for key, fns in distinct_nan.items():
    print(f"   {key} <- {fns}")
print("2) 0.0 display per view:", {v: [k for k, x in zero_cell.items()
                                       if x == v] for v in set(zero_cell.values())})
div_nan = len(distinct_nan)
div_zero = len(set(zero_cell.values()))
print()
print(f"NaN-representation variants: {div_nan};  0-representation variants: {div_zero}")
print()
print("EXPECTED (klaim docstring 'identik view lain'): 1 varian NaN ('-' "
      "atau ''), semua view konsisten.")
print(f"ACTUAL: NaN={div_nan} varian {sorted(distinct_nan)}; "
      f"0={div_zero} varian.")
same_num = all(
    results[(n, "deviasi._fmt_num")] == results[(n, "komparasi._fmt_num")]
    == results[(n, "in_selisih._fmt_num")] == results[(n, "laporan._fmt_num")]
    == results[(n, "pivot._format_num")]
    for n in ("7.5", "-1234.5", "1234567.0"))
print(f"Angka bukan-NaN/0 identik antar view: {same_num}")
print("nan-string leak:", [k for k, v in results.items()
                           if isinstance(v, str) and v.strip().lower() == "nan"])
if div_nan > 1:
    print("VERDICT: BUG (P3 — paritas kosmetik lintas view; klaim "
          "'identik view lain' PALSU utk NaN/None: '' vs '-' vs '—'; "
          "0 konsisten '-' di semua view, angka murni identik).")
else:
    print("VERDICT: NOT-BUG")
