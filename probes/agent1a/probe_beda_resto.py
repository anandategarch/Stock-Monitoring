"""
probe_beda_resto.py — CEK segment "Beda dari Resto Lain" (v3.11.9):
pasangan searah DUA periode (deviasi H & deviasi bulan lalu sama
surplus/defisit) sementara >=2 resto lain berlawanan arah & tak ada yang
searah -> label.

Mini-fixture: 3 resto x barang ZEUS (V.20), SO hanya hari 6:
  MLGPAR SO(6)=10, BDGUKU SO(6)=3, SMG SO(6)=4.
Saldo sistem map (override kolom Sistem): MLGPAR 0, BDGUKU 6, SMG 8
  -> Deviasi = +10, -3, -4.
lalu_map: MLGPAR +5 (surplus lalu), BDGUKU -2, SMG -1 (defisit lalu).
EXPECTED: MLGPAR -> "Beda dari Resto Lain (Surplus · 2 resto lain
Defisit)"; BDGUKU & SMG -> TIDAK berlabel (ada resto lain searah).
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, "/home/z/stock-audit/probes/agent1a")

from fixture_lib import FOLDERS, SHEETS, _write_rekap, make_config

from src.config import Config
from src.pipeline.append1 import build_append1
from src.ui.deviasi_view import DeviasiView

tmp = tempfile.mkdtemp(prefix="a1a_br_")
root = os.path.join(tmp, "root")
os.makedirs(root)
for resto, so6 in (("MLGPAR", 10), ("BDGUKU", 3), ("SMG", 4)):
    _write_rekap(os.path.join(root, FOLDERS["RekapBerjalan"],
                              f"{resto}.xlsx"),
                 "berjalan", [("SO", "ZEUS (V.20)", {6: so6})])
cfg = Config(make_config(root))
final = build_append1(cfg)
print("append1 rows:", len(final))

ss = {("ZEUS (V.20)", "MLGPAR"): 0.0,
      ("ZEUS (V.20)", "BDGUKU"): 6.0,
      ("ZEUS (V.20)", "SMG"): 8.0}
lalu = {("MLGPAR", "ZEUS (V.20)"): 5.0,
        ("BDGUKU", "ZEUS (V.20)"): -2.0,
        ("SMG", "ZEUS (V.20)"): -1.0}

v = object.__new__(DeviasiView)
v.satuan_mode = "GR"
v.tanggal_h = 6
v.data = final
v._tnum = None
v._tnum_data = None
v.in_detail = None
v._ri_bal_cache = None
v.acr_threshold = 80.0
v.harga_map = {}
v.konversi_map = None
v._harga_pair_cache = None
v.saldo_sistem_map = ss

res = v._compute_pivot(final, 6, lalu_map=lalu, lalu_label="WEEK 1 · TEST")
print(res[["Resto", "Nama Barang", "SO_H", "Sistem", "Deviasi",
           "Dev. Bulan Lalu", "CEK"]].to_string(index=False))

rows = {r["Resto"]: r for _, r in res.iterrows()}
mlg = str(rows["MLGPAR"]["CEK"])
bdg = str(rows["BDGUKU"]["CEK"])
smg = str(rows["SMG"]["CEK"])
exp_seg = "Beda dari Resto Lain (Surplus · 2 resto lain Defisit)"
ok = (exp_seg in mlg and exp_seg not in bdg and exp_seg not in smg)
print(f"\nMLGPAR CEK memuat segmen: EXPECTED ya, ACTUAL "
      f"{exp_seg in mlg!r} (CEK penuh: {mlg!r})")
print(f"BDGUKU/SMG CEK tanpa segmen: ACTUAL {bdg!r} / {smg!r}")
print("VERDICT Beda dari Resto Lain: " + ("NOT-BUG" if ok else "BUG"))
