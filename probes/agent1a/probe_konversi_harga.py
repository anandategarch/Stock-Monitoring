"""
probe_konversi_harga.py — unit conversion (konversi_satuan) + price
normalization (nominal_common.lookup_harga_pair) + persen kenaikan.

Doc claims:
- konversi: "harga_rekap = harga41 x rasio(satuanRekap) / rasio(satuan41.09)"
  (contoh data user: GULA 18,25/GR, rekap KG -> 18.250/KG)
- lookup_rasio: exact key -> rasio; satuan == terkecil -> 1.0 implisit;
  tak ketemu -> None.
- hitung_persen_kenaikan: (H - Lalu) / |Lalu| * 100.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import pandas as pd

from src.pipeline.konversi_satuan import build_konversi_map, lookup_rasio
from src.ui.nominal_common import (hitung_persen_kenaikan, fmt_pct_cell,
                                   lookup_harga_pair)

# ---- build_konversi_map dari frame IN-like
in_df = pd.DataFrame({
    "Nama Barang": ["GULA (V.20)", "GULA (V.20)", "AIR MINERAL",
                    "AIR MINERAL", "AIR MINERAL", "SUMPIT"],
    "SATUAN DOK": ["KG", "KG", "KARTON", "BOTOL", "BOTOL", "KARUNG"],
    "RASIO SATUAN": [1000, 1000, 24, 1, 1, 3000],
    "SATUAN TERKECIL": ["GR", "GR", "BOTOL", "BOTOL", "BOTOL", "PCS"],
})
km = build_konversi_map(in_df)
print("rasio map:", km["rasio"])
print("terkecil :", km["terkecil"], "conflict:", km["n_conflict"])

r_kg, t_gula = lookup_rasio(km, "GULA (V.20)", "KG")
r_gr, _ = lookup_rasio(km, "GULA (V.20)", "GR")
r_miss, _ = lookup_rasio(km, "GULA (V.20)", "LITER")
r_botol, _ = lookup_rasio(km, "AIR MINERAL", "BOTOL")
r_karung, _ = lookup_rasio(km, "SUMPIT", "KARUNG")
print(f"\nlookup KG={r_kg} GR={r_gr} LITER={r_miss} BOTOL={r_botol} "
      f"KARUNG={r_karung}")
ok = (r_kg == 1000.0 and r_gr == 1.0 and r_miss is None
      and r_botol == 1.0 and r_karung == 3000.0)
print("VERDICT lookup_rasio: " + ("NOT-BUG" if ok else "BUG"))

# ---- lookup_harga_pair: GULA 18,25/GR, rekap KG -> 18.250/KG
harga_map = {"GULA (V.20)": (18.25, "GR"),
             "AIR MINERAL": (6000.0, "KARTON")}
h1, lab1, b1 = lookup_harga_pair(harga_map, km, "GULA (V.20)", "KG")
h2, lab2, b2 = lookup_harga_pair(harga_map, km, "AIR MINERAL", "BOTOL")
h3, lab3, b3 = lookup_harga_pair(harga_map, km, "GULA (V.20)", "GR")
print(f"\nGULA  harga/KG : EXPECTED 18250.0, ACTUAL {h1} ({lab1!r})")
print(f"AIR   harga/BOT: EXPECTED 250.0 (6000/24), ACTUAL {h2} ({lab2!r})")
print(f"GULA  harga/GR : EXPECTED 18.25, ACTUAL {h3} ({lab3!r})")
ok2 = (abs(h1 - 18250.0) < 1e-9 and abs(h2 - 250.0) < 1e-9
       and abs(h3 - 18.25) < 1e-9 and not b1 and not b2)
print("VERDICT arah konversi harga: " + ("NOT-BUG" if ok2 else "BUG"))

# satuan rekap tak ter-cover rasio (42.05/32.24 tak kenal) -> '*' + None
h4, lab4, b4 = lookup_harga_pair({"SUMPIT": (10.0, "PCS")}, km,
                                  "SUMPIT", "KARUNG")
print(f"SUMPIT KARUNG (tanpa rasio KARUNG utk harga PCS?): "
      f"h={h4} label={lab4!r} bintang={b4}")

# ---- hitung_persen_kenaikan
cases = [
    ((150.0, 100.0), 50.0),          # (150-100)/100*100
    ((50.0, 100.0), -50.0),
    ((150.0, -100.0), 250.0),        # |lalu| pembagi, arah dari H-L
    ((0.0, 0.0), 0.0),
    ((5.0, 0.0), None),              # div-0 -> None
    ((None, 100.0), None),
]
allok = True
for (h, l), exp in cases:
    act = hitung_persen_kenaikan(h, l)
    good = (act is None and exp is None) or abs(act - exp) < 1e-9
    allok &= good
    print(f"persen({h}, {l}): EXPECTED {exp}, ACTUAL {act} "
          f"-> {'OK' if good else 'BUG'}")
print("VERDICT persen kenaikan: " + ("NOT-BUG" if allok else "BUG"))

print("\nfmt_pct_cell(1234.56) =", fmt_pct_cell(1234.56),
      "| fmt_pct_cell(0.04) =", fmt_pct_cell(0.04),
      "| fmt_pct_cell(-0.04) =", fmt_pct_cell(-0.04))
