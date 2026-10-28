"""
probe_po_keterangan_nominal.py —
(A) po_keterangan "Potensi PO belum dibuat" trigger semantics;
(B) nominal_common.hitung_nominal_pairs: saldo-sistem override, qty-0
    -> Nominal 0.0, deviasi_only filter;
(C) fn_audit SA anchor di baris pertama bulan berjalan (AYAM, fixture).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, "/home/z/stock-audit/probes/agent1a")

import pandas as pd

from src.ui.po_keterangan import potensi_po_map, POTENSI_PO_LABEL
from src.ui.nominal_common import hitung_nominal_pairs

# =========================================================== (A) po_keterangan
def L(barang, resto, t, jenis, nilai, sk="Eksternal"):
    return {"Nama Barang": barang, "NAMA RESTO": resto, "Tanggal": t,
            "JENIS": jenis, "NILAI": nilai, "SOURCE KIRIMAN": sk,
            "SATUAN": "GR"}

data = pd.DataFrame([
    # DONALD: BM t4, SO naik 10->20, tanpa 32.24/9901 -> TRIGGER t4
    L("DONALD (V.20)", "BDGUKU", 2, "1.SO", 10),
    L("DONALD (V.20)", "BDGUKU", 4, "1.SO", 20),
    L("DONALD (V.20)", "BDGUKU", 4, "5.BARANG MASUK", 8),
    # SIERRA: sama tapi ADA 32.24 di t4 -> NO trigger
    L("SIERRA (V.20)", "BDGUKU", 2, "1.SO", 10),
    L("SIERRA (V.20)", "BDGUKU", 4, "1.SO", 20),
    L("SIERRA (V.20)", "BDGUKU", 4, "5.BARANG MASUK", 6),
    # TANGO: BM t3, SO naik -> TRIGGER t3
    L("TANGO (V.20)", "BDGUKU", 2, "1.SO", 10),
    L("TANGO (V.20)", "BDGUKU", 3, "1.SO", 20),
    L("TANGO (V.20)", "BDGUKU", 3, "5.BARANG MASUK", 6),
    # LIMA: blok bulan lalu — hari KRONOLOGIS: day 26 (-26) < day 27 (-27).
    # SO -26=10 -> -27=20 (naik), BM -27, tanpa RI lalu utk pasangan ini;
    # 32.24 lalu ADA (pair lain, t -27) -> _lalu_max=27, jendela [23..27]
    # -> verifiable -> TRIGGER -27
    L("LIMA (V.20)", "BDGUKU", -26, "1.SO", 10),
    L("LIMA (V.20)", "BDGUKU", -27, "1.SO", 20),
    L("LIMA (V.20)", "BDGUKU", -27, "5.BARANG MASUK", 6),
    # ENAM: hari 22 (-22) DI LUAR jendela verifiable [23..27] -> NO trigger
    # (SO -21=10 -> -22=20 naik, BM -22, tanpa RI) — guard jendela lalu.
    L("ENAM (V.20)", "BDGUKU", -21, "1.SO", 10),
    L("ENAM (V.20)", "BDGUKU", -22, "1.SO", 20),
    L("ENAM (V.20)", "BDGUKU", -22, "5.BARANG MASUK", 6),
])
in_detail = pd.DataFrame([
    {"Nama Barang": "OTHER", "NAMA RESTO": "BDGUKU", "Tanggal": 1,
     "Value": 5, "SOURCE IN": "42.05", "Nomor": "IT.1", "Nomor PO": None},
    {"Nama Barang": "SIERRA (V.20)", "NAMA RESTO": "BDGUKU", "Tanggal": 4,
     "Value": 6, "SOURCE IN": "32.24", "Nomor": "RI.1", "Nomor PO": "PO.1"},
    {"Nama Barang": "OTHER2", "NAMA RESTO": "BDGUKU", "Tanggal": -27,
     "Value": 3, "SOURCE IN": "32.24 (Bulan Lalu)", "Nomor": "RI.2",
     "Nomor PO": None},
])
m = potensi_po_map(data, in_detail)
print("potensi_po_map:", {k: sorted(v) for k, v in m.items()})

exp = {("DONALD (V.20)", "BDGUKU"): {4},
       ("TANGO (V.20)", "BDGUKU"): {3},
       ("LIMA (V.20)", "BDGUKU"): {-27}}
act = {k: set(v) for k, v in m.items()}
ok_a = act == exp
print(f"EXPECTED {exp}")
print(f"ACTUAL   {act}")
print("VERDICT po_keterangan: " + ("NOT-BUG" if ok_a else "BUG"))

# ================================================== (B) hitung_nominal_pairs
def D(barang, resto, t, jenis, nilai, kat="COM DEVIASI - RESTO"):
    return {"Nama Barang": barang, "NAMA RESTO": resto, "Tanggal": t,
            "JENIS": jenis, "NILAI": nilai, "SATUAN": "GR",
            "KATEGORI": kat}

ndata = pd.DataFrame([
    # ALFA: 3.DEVIASI(h) = -99 TAPI saldo sistem 100 + SO_H 88 -> override -12
    D("ALFA (V.20)", "MLGPAR", 5, "3.DEVIASI", -99),
    D("ALFA (V.20)", "MLGPAR", 5, "1.SO", 88),
    D("ALFA (V.20)", "MLGPAR", 5, "9.ACR", 40),
    # BETA: qty deviasi 0 -> Nominal 0.0 tanpa harga
    D("BETA (V.20)", "MLGPAR", 5, "3.DEVIASI", 0),
    D("BETA (V.20)", "MLGPAR", 5, "9.ACR", 10),
    # GAMMA: tanpa 9.ACR + kategori tanpa COM/PACKAGING (deviasi_only drop)
    D("GAMMA (V.20)", "MLGPAR", 5, "3.DEVIASI", 5, kat="SUPPLIES LAIN"),
])
harga = {"ALFA (V.20)": (10.0, "GR"), "BETA (V.20)": (7.0, "GR")}
ss = {("ALFA (V.20)", "MLGPAR"): 100.0}

res = hitung_nominal_pairs(ndata, 5, harga, None,
                           saldo_sistem_map=ss, deviasi_only=False)
print("\nnominal pairs (tanpa deviasi_only):")
print(res.to_string(index=False))
alfa = res[res["Nama Barang"] == "ALFA (V.20)"].iloc[0]
ok_b1 = abs(alfa["Qty Deviasi"] - (88 - 100)) < 1e-9 \
    and abs(alfa["Nominal"] - (10.0 * -12)) < 1e-9
print(f"ALFA override: EXPECTED Qty=-12 Nominal=-120, ACTUAL "
      f"Qty={alfa['Qty Deviasi']} Nominal={alfa['Nominal']} -> "
      f"{'NOT-BUG' if ok_b1 else 'BUG'}")
beta = res[res["Nama Barang"] == "BETA (V.20)"].iloc[0]
ok_b2 = beta["Nominal"] == 0.0 and pd.isna(beta["Harga"])
print(f"BETA qty-0: EXPECTED Nominal=0.0 Harga=NaN, ACTUAL "
      f"Nominal={beta['Nominal']} Harga={beta['Harga']} -> "
      f"{'NOT-BUG' if ok_b2 else 'BUG'}")

res2 = hitung_nominal_pairs(ndata, 5, harga, None,
                            saldo_sistem_map=ss, deviasi_only=True)
print("\ndeviasi_only=True rows:", list(res2["Nama Barang"]))
dropped = res2.attrs.get("deviasi_only_dropped")
ok_b3 = (list(res2["Nama Barang"]) == ["ALFA (V.20)", "BETA (V.20)"]
         and dropped == 1)
print(f"EXPECTED [ALFA, BETA] + dropped=1, ACTUAL "
      f"{list(res2['Nama Barang'])} dropped={dropped} -> "
      f"{'NOT-BUG' if ok_b3 else 'BUG'}")

# ============================================ (C) fn_audit SA anchor (AYAM)
from fixture_lib import build
from src.main import _extract_append1_maps
from src.pipeline.fn_audit import build_audit_from_app
final, det, rek, cfg, tmp = build()
sa_map, bk_map = _extract_append1_maps(final)
audit, kpi, desc = build_audit_from_app(rek, det, bulan_lalu=True,
                                        saldo_awal_map=sa_map,
                                        bk_map=bk_map)
ay = audit[audit["Nama Item"] == "AYAM (V.20)"].sort_values("Tanggal")
r1 = ay[ay["Tanggal"] == 1].iloc[0]
ok_c = abs(r1["Qty SO Kemarin"] - 200.0) < 1e-9 \
    and abs(r1["Qty Delta SO"] - (190 - 200)) < 1e-9
print(f"\nAYAM t=1 SO-kemarin: EXPECTED 200 (SA anchor), ACTUAL "
      f"{r1['Qty SO Kemarin']} (dSO={r1['Qty Delta SO']}) -> "
      f"{'NOT-BUG' if ok_c else 'BUG'}")
