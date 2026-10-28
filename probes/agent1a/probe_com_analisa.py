"""
probe_com_analisa.py — CEK label "COM Tinggi/Rendah" (com_gap_map) +
laporan Anomali COM matrix com(1) + AYAM sanity (SA present).

Fixture: see fixture_lib. BEBEK: SO days 1,2,4,5,6; IN day3; ACR 2,4,5,6.
AYAM: SA=200 (real 42.17 row), SO days 1,2,4,5,6, no IN/ACR.

EXPECTED (documented semantics — median over VALID days 1..H-1, SO
tercatat kedua ujung, t=1 basis SA/penutupan):
  BEBEK valid window (H=6) = {1,2,5} -> d = {10-0, 5-3, 5-5} = {10,2,0}
  median = 2; d(6) = com(6)-acr(6) = (10-8)-6 = -4 < 2 -> "rendah", gap 6.
  AYAM com(1) = SA 200 - SO(1) 190 = 10 (SA-present path works).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, "/home/z/stock-audit/probes/agent1a")

from fixture_lib import build

final, det, rek, cfg, tmp = build()

from src.ui import com_analisa

# ---------------------------------------------------------------- com_gap_map
m = com_analisa.com_gap_map(final, 6)
print("com_gap_map (h=6):", m)

exp_bebek = ("rendah", 2.0 - (-4.0))          # median 2 - d(6) -4 -> gap 6
act_bebek = m.get(("BEBEK (V.20)", "MLGPAR"))
print(f"BEBEK gap: EXPECTED = {exp_bebek}, ACTUAL = {act_bebek}")
print(f"VERDICT com_gap_map BEBEK: "
      f"{'BUG' if act_bebek != exp_bebek else 'NOT-BUG'}")

# ---------------------------------------------------------------- AYAM (SA ada)
com_ayam = com_analisa._CACHE["mat"]["com"]
ay = com_ayam.loc[("AYAM (V.20)", "MLGPAR")]
print("\nAYAM com row:", {int(c): v for c, v in ay.items()})
exp_ayam_c1 = 200.0 - 190.0
act_ayam_c1 = float(ay[1])
print(f"AYAM com(1): EXPECTED (SA basis) = {exp_ayam_c1}, "
      f"ACTUAL = {act_ayam_c1}")
print(f"VERDICT AYAM SA-basis: "
      f"{'NOT-BUG' if abs(act_ayam_c1 - exp_ayam_c1) < 1e-9 else 'BUG'}")

be = com_ayam.loc[("BEBEK (V.20)", "MLGPAR")]
print("\nBEBEK com row (com_analisa matrix):",
      {int(c): v for c, v in be.items()})
print(f"BEBEK com(1) EXPECTED (penutupan 40 basis) = 10.0, "
      f"ACTUAL = {float(be[1])} -> "
      f"{'BUG' if abs(float(be[1]) - 10.0) > 1e-9 else 'NOT-BUG'}")

# ------------------------------------------------- laporan _compute_com_matrix
from src.ui.laporan_deviasi_view import LaporanDeviasiView
lv = object.__new__(LaporanDeviasiView)
lv.data = final
lv._satuan_lookup = {}
lv._aktif_lookup = {}
com_matrix = lv._compute_com_matrix(final)
be_lap = com_matrix.loc[("BEBEK (V.20)", "MLGPAR")]
print("\nBEBEK com row (laporan _compute_com_matrix):",
      {int(c): v for c, v in be_lap.items()})
print(f"laporan com(1): EXPECTED (penutupan 40) = 10.0, "
      f"ACTUAL = {float(be_lap[1])} -> "
      f"{'BUG' if abs(float(be_lap[1]) - 10.0) > 1e-9 else 'NOT-BUG'}")
ay_lap = com_matrix.loc[("AYAM (V.20)", "MLGPAR")]
print(f"laporan AYAM com(1): EXPECTED (SA 200) = 10.0, "
      f"ACTUAL = {float(ay_lap[1])} -> "
      f"{'NOT-BUG' if abs(float(ay_lap[1]) - 10.0) < 1e-9 else 'BUG'}")
