"""
probe_rank.py — v3.9.65 Rank per-baris semantics via REAL
DeviasiView._prepare_rows: Rank = RANK |Deviasi| baris ini dalam grup
NAMA BARANG (1 = terbesar, per resto), method="min" (seri berbagi rank,
rank berikut meloncat), Deviasi 0/NaN -> rank KOSONG.

Fixture pivot (H=6, real _compute_pivot):
  AYAM   dev -35 ; BEBEK dev 16 ; CITRA dev 75
Group 'AYAM (V.20)' hanya 1 resto -> rank 1.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, "/home/z/stock-audit/probes/agent1a")

from fixture_lib import build
from src.ui.deviasi_view import DeviasiView

final, det, rek, cfg, tmp = build()


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
    v.store = None
    v._cell_tags = False
    return v


v6 = make_view(6)
res6 = v6._compute_pivot(final, 6)

# tambah resto sintetik utk grup barang sama (AYAM) supaya rank
# dalam-grup teruji: MLGPAR -35, BDGUKU -35 (IKAT), SMG 0 (kosong),
# JKT -10 (rank meloncat ke 3 karena ikat 1,1)
extra = res6[res6["Nama Barang"] == "AYAM (V.20)"].copy()
import pandas as pd  # noqa: E402
rows = [extra.iloc[0]]
for resto, dev in (("BDGUKU", -35.0), ("SMG", 0.0), ("JKT", -10.0)):
    r = extra.iloc[0].copy()
    r["Resto"] = resto
    r["Deviasi"] = dev
    rows.append(r)
res6 = pd.concat([res6[res6["Nama Barang"] != "AYAM (V.20)"],
                  pd.DataFrame(rows)], ignore_index=True)

v6._cached_pivot = res6
st = {"kategori": None, "aktif": None, "col_sel": {}, "tanggal_h": 6}
out = v6._prepare_rows(st)
print("status:", out.get("status"))

col_ids = [c[0] for c in DeviasiView.COLUMNS]
i_rank = col_ids.index("Rank")
i_barang = col_ids.index("Nama Barang")
i_resto = col_ids.index("Resto")
i_dev = col_ids.index("Deviasi")
print(f"\n{'Barang':<14}{'Resto':<10}{'Dev':>8}{'Rank':>6}")
shown = []
for it in out["items"]:
    values = it[2]["values"]
    shown.append((values[i_barang], values[i_resto], values[i_dev],
                  values[i_rank]))
for s in sorted(shown):
    print(f"{s[0]:<14}{s[1]:<10}{s[2]:>8}{s[3]:>6}")

r = {(b, rs): rk for b, rs, _, rk in shown}
exp = {("AYAM (V.20)", "MLGPAR"): "1",     # |35| ikat dgn BDGUKU
       ("AYAM (V.20)", "BDGUKU"): "1",     # ikat method=min
       ("AYAM (V.20)", "SMG"): "",         # dev 0 -> kosong
       ("AYAM (V.20)", "JKT"): "3",         # rank meloncat (1,1,_,3)
       ("BEBEK (V.20)", "MLGPAR"): "1",    # grup 1 resto
       ("CITRA (V.20)", "MLGPAR"): "1"}
ok = all(r.get(k) == v for k, v in exp.items())
print("\nEXPECTED:", exp)
print("ACTUAL:  ", r)
print("VERDICT rank per-baris (v3.9.65): " + ("NOT-BUG" if ok else "BUG"))
