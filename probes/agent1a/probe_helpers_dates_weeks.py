"""
probe_helpers_dates_weeks.py —
(A) helpers.to_datetime_robust / date_to_day: dayfirst + serial Excel;
(B) nominal_common._pilih_minggu_lalu / _h_to_week_target fallback;
(C) com_analisa threshold: >=3 valid days & strict > / < median
    (frame TANPA gap — semua hari ber-baris SO sungguhan);
(D) deviasi_popup._chrono_key float parse ('-25.0').
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import numpy as np
import pandas as pd

from src.pipeline.helpers import date_to_day, to_datetime_robust
from src.ui.nominal_common import _pilih_minggu_lalu, _h_to_week_target
from src.ui.com_analisa import com_gap_map
from src.ui.deviasi_popup import _chrono_key

# ---------------------------------------------------------------- (A)
s = pd.Series(["01/10/2026", "13/10/2026", "2026-10-01", "31/12/2026"])
days = date_to_day(s)
print("date_to_day:", days.tolist())
ok_a1 = days.tolist() == [1, 13, 1, 31]
print("VERDICT dayfirst: " + ("NOT-BUG" if ok_a1 else "BUG"))

serial = pd.Series([46290, 46291.5])
d2 = to_datetime_robust(serial)
print("serial 46290 ->", d2.iloc[0], "| 46291.5 ->", d2.iloc[1])
ok_a2 = str(d2.iloc[0])[:10] == "2026-09-25"
print("VERDICT serial excel (46290 = 2026-09-25): "
      + ("NOT-BUG" if ok_a2 else "BUG"))

mixed = pd.Series(["01/10/2026", 46290])
d3 = to_datetime_robust(mixed)
print("mixed:", d3.tolist())
ok_a3 = str(d3.iloc[0])[:10] == "2026-10-01" and str(d3.iloc[1])[:10] == "2026-09-25"
print("VERDICT mixed serial+string: " + ("NOT-BUG" if ok_a3 else "BUG"))

# ---------------------------------------------------------------- (B)
print("\n_h_to_week_target: 5->%s 12->%s 15->%s 26->%s 31->%s" % (
    _h_to_week_target(5), _h_to_week_target(12), _h_to_week_target(15),
    _h_to_week_target(26), _h_to_week_target(31)))
cases = [
    ([7, 14, 25], 5, 7),        # exact W1
    ([7, 14, 25], 15, 25),      # target 25 exact
    ([7, 14, 21, 28], 15, 21),  # target 25 absen -> terbesar <= 25
    ([14, 21], 5, 14),          # semua > target -> terkecil
    ([7, 14, 25], None, 25),    # h None -> minggu terbesar
]
ok_b = all(_pilih_minggu_lalu(w, h) == e for w, h, e in cases)
for w, h, e in cases:
    print(f"  weeks={w} h={h}: EXPECTED {e}, ACTUAL {_pilih_minggu_lalu(w, h)}")
print("VERDICT minggu lalu fallback: " + ("NOT-BUG" if ok_b else "BUG"))

# ---------------------------------------------------------------- (C)
def row(b, t, jenis, v):
    return {"Nama Barang": b, "NAMA RESTO": "R", "Tanggal": t,
            "JENIS": jenis, "NILAI": v, "SATUAN": "GR"}

# Pair P1: SO tiap hari 1..8; com(t)=2 stabil, d(8)=2 == median -> no label
# Pair P2: com(2..7)=0 (so datar), com(8)=100-50=50 -> d(8)=50, median 0
#          -> COM Tinggi gap 50 (t=1 invalid: tanpa SA/penutupan)
# Pair P3: window valid utk H=4 hanya {2} (<3) -> no label
# Pair P4: d(2..7)=2 (so turun 2/hari), com(8)=88-156=-68 -> d(8)=-68
#          -> COM Rendah gap 2-(-68)=70
rows = []
def add_pair(name, so_vals, acr_vals):
    for t, v in so_vals.items():
        rows.append(row(name, t, "1.SO", v))
    for t, v in acr_vals.items():
        rows.append(row(name, t, "9.ACR", v))
    for t in so_vals:
        rows.append(row(name, t, "4.IN", 0))
        rows.append(row(name, t, "8.BARANG KELUAR", 0))

# P1: com(t) = so(t-1)-so(t) = 2 (so 100->98->...), acr 0 -> d = 2 semua
add_pair("P1", {t: 100 - 2 * (t - 1) for t in range(1, 9)}, {})
# P2: so datar 100..100 (com 0) t1..7, t8: so 50 -> com(8)=50, acr 0
add_pair("P2", {**{t: 100 for t in range(1, 8)}, 8: 50}, {})
# P3: SO hanya hari 1,2,4 (H=4): window valid {1,2} saja (<3)
add_pair("P3", {1: 100, 2: 90, 4: 10}, {})
# P4: d(1..7)=2 semua, d(8) = -30 -> COM Rendah gap 32
add_pair("P4", {**{t: 100 - 2 * (t - 1) for t in range(1, 8)}, 8: 156}, {})

data = pd.DataFrame(rows)
m = com_gap_map(data, 8)
print("\ncom_gap_map h=8:", m)
ok_c = (m.get(("P1", "R")) is None
        and m.get(("P2", "R")) == ("tinggi", 50.0)
        and m.get(("P3", "R")) is None
        and m.get(("P4", "R")) == ("rendah", 70.0))
print("EXPECTED P1 None, P2 ('tinggi',50), P3 None (window <3 hari), "
      "P4 ('rendah',70)")
print("VERDICT com threshold & strict median: "
      + ("NOT-BUG" if ok_c else "BUG"))

# P1 cek d(H) == median persis -> tanpa label (strict dua sisi) — sudah
# termasuk di P1 (d semua 2, median 2, d(8)=2) -> None ✓

# ---------------------------------------------------------------- (D)
vals = [-25, -25.0, "-25.0", "-25", 1, 1.0, "31", None, "abc"]
print("\n_chrono_key:", [(repr(v), _chrono_key(v)) for v in vals])
ok_d = (_chrono_key(-25) == 25 and _chrono_key("-25.0") == 25
        and _chrono_key(1) == 101 and _chrono_key(None) == 999999)
print("VERDICT chrono_key float-parse: " + ("NOT-BUG" if ok_d else "BUG"))
