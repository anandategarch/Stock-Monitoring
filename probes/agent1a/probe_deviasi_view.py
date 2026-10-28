"""
probe_deviasi_view.py — CEK labels & pivot math via REAL
DeviasiView._compute_pivot (instance created with object.__new__, only
data-attributes set — no Tk needed).

Checks (README claims):
1. "BOM 0": Total ACR sebulan (Σ 9.ACR 1..H) = 0 & SO(H) > 0
   -> AYAM (no ACR at all, SO(6)=165) MUST have label "BOM 0".
2. "Naik Drastis": SO(H) > 150%·SO(H-1) -> CITRA SO(5)=100, SO(6)=160.
3. "Selisih IN = BM - IN" (v3.11.5) -> CITRA t=2: BM 7, IN 5 -> 2.
4. SO_H-1 at H=1 = penutupan bulan lalu (kunci negatif terkecil
   ber-baris SO) -> BEBEK penutupan SO(-28)=40; fixture also has BM at
   -30 (no SO recorded there). EXPECTED SO_H-1 = 40.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, "/home/z/stock-audit/probes/agent1a")

import numpy as np
from fixture_lib import build

final, det, rek, cfg, tmp = build()

from src.ui.deviasi_view import DeviasiView


def make_view(h):
    v = object.__new__(DeviasiView)
    v.satuan_mode = "GR"
    v.tanggal_h = h
    v.data = final
    v._tnum = None
    v._tnum_data = None
    v.in_detail = det
    v._ri_bal_cache = None
    v.acr_threshold = 80.0
    v.harga_map = {}
    v.konversi_map = None
    v._harga_pair_cache = None
    v.saldo_sistem_map = {}
    return v


def row_of(res, barang):
    r = res[res["Nama Barang"] == barang]
    assert len(r) == 1, f"{barang}: {len(r)} rows"
    return r.iloc[0]


# ------------------------------------------------------------------ H = 6
v6 = make_view(6)
res6 = v6._compute_pivot(final, 6)
print("columns:", list(res6.columns))
print(res6[["Nama Barang", "SO_H-1", "SO_H", "Sistem", "Deviasi",
            "Total ACR", "CEK"]].to_string(index=False))

ay = row_of(res6, "AYAM (V.20)")
ok_bom0 = "BOM 0" in str(ay["CEK"]) and ay["Total ACR"] == 0 \
    and ay["SO_H"] == 165
print(f"\n[1] BOM 0 (AYAM): Total ACR={ay['Total ACR']}, SO_H={ay['SO_H']}, "
      f"CEK={ay['CEK']!r} -> {'NOT-BUG (label fires)' if ok_bom0 else 'BUG'}")

ci = row_of(res6, "CITRA (V.20)")
ok_naik = "Naik Drastis" in str(ci["CEK"])
print(f"[2] Naik Drastis (CITRA): SO_H-1={ci['SO_H-1']}, SO_H={ci['SO_H']}, "
      f"CEK={ci['CEK']!r} -> "
      f"{'NOT-BUG (160 > 1.5*100 fires)' if ok_naik else 'BUG'}")

# Selisih IN = BM - IN (append1 output row check)
sel = final[(final["Nama Barang"] == "CITRA (V.20)")
            & (final["JENIS"] == "7.Selisih IN")
            & (final["Tanggal"] == 2)]["NILAI"].sum()
print(f"[3] Selisih IN CITRA t=2: EXPECTED = 2 (BM 7 - IN 5), "
      f"ACTUAL = {sel} -> {'NOT-BUG' if sel == 2 else 'BUG'}")

# ------------------------------------------------------------------ H = 1
v1 = make_view(1)
res1 = v1._compute_pivot(final, 1)
print("\nH=1 pivot:")
print(res1[["Nama Barang", "SO_H-2", "SO_H-1", "SO_H", "Sistem",
            "Deviasi", "CEK"]].to_string(index=False))
be1 = row_of(res1, "BEBEK (V.20)")
exp_so_m1 = 40.0
print(f"\n[4] BEBEK SO_H-1 @H=1 (penutupan bulan lalu): EXPECTED = "
      f"{exp_so_m1} (SO(-28)=40, SO recorded), ACTUAL = {be1['SO_H-1']} "
      f"-> {'BUG' if abs(be1['SO_H-1'] - exp_so_m1) > 1e-9 else 'NOT-BUG'}")
print(f"    BEBEK CEK @H=1: {be1['CEK']!r} "
      f"(dengan basis benar 40: stok=40-30=10, ratio=|30-40|/40 tidak "
      f"memicu 'Hitung Manual')")
