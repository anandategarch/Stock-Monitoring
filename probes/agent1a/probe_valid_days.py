"""
probe_valid_days.py — AVG COM/AVG ACR "HARI VALID" window & com(1) basis.

README claim (v3.11.9): "Avg COM / Avg ACR (rata-rata COM/ACR jendela 1..H-1
HARI VALID — SO tercatat kedua ujung, mirror com_analisa; t=1 basis SALDO
AWAL / penutupan bulan lalu)".

Fixture (see fixture_lib): BEBEK (V.20) @MLGPAR — SO recorded days
1,2,4,5,6 (NOT 3); rekap-lalu penutupan SO(-28)=40; IN(42.05) day3=10;
ACR days 2,4,5,6 = 3,4,5,6; NOT in 42.17 (no saldo awal).

EXPECTED (documented semantics):
  valid days 1..H-1 (H=6) = {1,2,5}  (day 3: SO not recorded; day 4: SO(3)
  not recorded) -> Avg COM = (com1+com2+com5)/3 with
  com(1) = penutupan 40 + 0 - 30 = 10 ; com(2) = 30-25 = 5 ; com(5) = 15-10 = 5
  => Avg COM = 6.667, Avg ACR = (0+3+5)/3 = 2.667, n_valid = 3
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, "/home/z/stock-audit/probes/agent1a")

from fixture_lib import build

final, det, rek, cfg, tmp = build()

from src.ui import deviasi_popup as dp

B, R, S = "BEBEK (V.20)", "MLGPAR", "GR"

# ---------------------------------------------------------------- presence
pres = dp._pair_presence(final, B, R, "1.SO", S)
print("1.SO presence dates (BEBEK):", sorted(pres))
print("  -> t=3 in presence (SO NOT recorded that day)?", 3.0 in pres)

# ---------------------------------------------------------------- com series
com = dp._compute_com_series(final, B, R, S)
print("\ncom series (BEBEK):", {int(k): v for k, v in sorted(com.items())})
com1 = com.get(1.0)
exp_com1 = 40.0 + 0.0 - 30.0     # penutupan bulan lalu + IN(1) - BK(1) - SO(1)
print(f"com(1): EXPECTED (basis penutupan -28 = 40) = {exp_com1}, ACTUAL = {com1}")
print(f"VERDICT com(1) basis: {'BUG' if abs(com1 - exp_com1) > 1e-9 else 'NOT-BUG'}")

# ---------------------------------------------------------------- avg window
avg_com, avg_acr, n = dp._com_acr_avg(final, B, R, S, 6)
# clean expected
exp_vals = {1: (40 - 30, 0.0), 2: (30 - 25, 3.0), 5: (15 - 10, 5.0)}
exp_n = len(exp_vals)
exp_avg_com = sum(v[0] for v in exp_vals.values()) / exp_n
exp_avg_acr = sum(v[1] for v in exp_vals.values()) / exp_n
print(f"\nAvg COM  : EXPECTED = {exp_avg_com:.4f} (n={exp_n}), "
      f"ACTUAL = {avg_com:.4f} (n={n})")
print(f"Avg ACR  : EXPECTED = {exp_avg_acr:.4f}, ACTUAL = {avg_acr:.4f}")
print(f"n valid  : EXPECTED = {exp_n}, ACTUAL = {n}")
ok = (abs(avg_com - exp_avg_com) < 1e-9 and abs(avg_acr - exp_avg_acr) < 1e-9
      and n == exp_n)
print(f"VERDICT avg window: {'BUG' if not ok else 'NOT-BUG'}")

# ---------------------------------------------------------------- popup rows
rows = dp.build_popup_rows(final, B, R, satuan=S, in_detail=det, h=6)
print("\npopup rows (BEBEK):")
print(rows.to_string(index=False))
print("attrs avg_days =", rows.attrs.get("avg_days"),
      "avg_h =", rows.attrs.get("avg_h"))
