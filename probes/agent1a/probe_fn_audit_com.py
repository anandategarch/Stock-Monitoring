"""
probe_fn_audit_com.py — Qty COM fn_audit vs popup/Anomali COM parity.

fn_audit docstring: "Qty COM — pemakaian aktual kanonik: COM(t) =
SO(t-1) + IN(t) - BK(t) - SO(t) (PERSIS formula 6.PEMAKAIAN (COM) pivot /
Laporan Deviasi / Komparasi — jangan bikin rumus keempat)".

BUT fn_audit's "SO(t-1)" = ffill LAST OBSERVED SO (sparse gap -> prev
recorded SO), while pivot/popup "SO(t-1)" = previous GLOBAL date column
(0-filled when SO not recorded there).

Fixture BEBEK: SO recorded 1,2,4,5,6; IN(42.05) day3=10 (day 3 has no SO).
At t=4: fn_audit COM = SO(2)=25 + 0 - 0 - SO(4)=15 = 10.
        popup COM  = so(3)=0 (fill) + 0 - 0 - 15  = -15.
Same pair, same date, two different numbers shown to the user.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, "/home/z/stock-audit/probes/agent1a")

import pandas as pd
from fixture_lib import build

final, det, rek, cfg, tmp = build()

from src.main import _extract_append1_maps
from src.pipeline.fn_audit import build_audit_from_app
from src.ui import deviasi_popup as dp

sa_map, bk_map = _extract_append1_maps(final)
print("saldo_awal_map:", sa_map)

audit, kpi, desc = build_audit_from_app(
    rek, det, po_pending_df=None, bulan_lalu=True,
    konversi=None, saldo_awal_map=sa_map, bk_map=bk_map)

be = audit[audit["Nama Item"] == "BEBEK (V.20)"][
    ["Tanggal", "Hasil SO", "Qty SO Kemarin", "Qty Delta SO",
     "Penerimaan Sistem", "Selisih Harian", "Qty COM",
     "Status Analisis Audit"]].sort_values("Tanggal")
print("\nfn_audit BEBEK:")
print(be.to_string(index=False))

com_popup = dp._compute_com_series(final, "BEBEK (V.20)", "MLGPAR", "GR")

rows = []
for _, r in be.iterrows():
    t = int(r["Tanggal"])
    if t < 1:
        continue
    rows.append({
        "t": t,
        "fn_audit_COM": r["Qty COM"],
        "popup_COM": com_popup.get(float(t)),
    })
cmp_df = pd.DataFrame(rows)
cmp_df["diff"] = cmp_df["fn_audit_COM"] - cmp_df["popup_COM"]
print("\nCOM parity (fn_audit vs popup):")
print(cmp_df.to_string(index=False))

n_diff = int((cmp_df["diff"].abs() > 1e-9).sum())
print(f"\nbaris dgn COM beda: {n_diff} dari {len(cmp_df)}")
print("VERDICT parity claim 'PERSIS formula pivot': "
      f"{'BUG (rumus keempat hidup)' if n_diff else 'NOT-BUG'}")

# sanity: v3.11.5 basis selisih = BM - IN (BEBEK t=3: BM 0 - IN 10 = -10)
r3 = be[be["Tanggal"] == 3].iloc[0]
print(f"\nSelisih Harian BEBEK t=3 (BM-IN): EXPECTED = -10, "
      f"ACTUAL = {r3['Selisih Harian']} -> "
      f"{'NOT-BUG' if r3['Selisih Harian'] == -10 else 'BUG'}")
