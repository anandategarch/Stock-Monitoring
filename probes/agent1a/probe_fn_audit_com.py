"""
probe_fn_audit_com.py — Qty COM fn_audit vs popup/Anomali COM parity.

fn_audit docstring: "Qty COM — pemakaian aktual kanonik: COM(t) =
SO(t-1) + IN(t) - BK(t) - SO(t) (PERSIS formula 6.PEMAKAIAN (COM) pivot /
Laporan Deviasi / Komparasi — jangan bikin rumus keempat)".

v3.11.10 (audit 3-a): canonical basis setelah fix —
  * t=1   : SA(1) bila ada baris SA asli, else SO penutupan (kolom
            negatif kronologis TERAKHIR yang merekam 1.SO);
  * t>1   : SO BARIS AKTIVITAS sebelumnya HANYA bila tercatat di baris
            itu (raw shift — bukan ffill observasi terakhir);
  * SO(t) tak direkam -> NaN (undefined, BUKAN 0-based garbage).

Fixture BEBEK (SO 1,2,4,5,6; IN day3=10 tanpa SO; penutupan -28=40;
no SA): EXPECTED com row = {1: 10, 2: 5, 3: undef, 4: undef, 5: 5,
6: 2} — SAMA di fn_audit dan popup (parity; t3/t4 undefined, NaN-NaN
dihitung sama). v3.11.10: probe disesuaikan — popup .get default NaN
(dulu None membuat diff TypeError) + block EXPECTED eksplisit; verdict
paritas tetap sama-rumus.
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

# EXPECTED (audit 3-a, hand-derived): com(1)=penutupan 40-30=10;
# com(2)=SO(1) 30-25=5; t3 & t4 undefined (SO(3) tak direkam);
# com(5)=SO(4) 15-10=5; com(6)=SO(5) 10-8=2.
EXPECTED_COM = {1: 10.0, 2: 5.0, 5: 5.0, 6: 2.0}

rows = []
for _, r in be.iterrows():
    t = int(r["Tanggal"])
    if t < 1:
        continue
    rows.append({
        "t": t,
        "fn_audit_COM": r["Qty COM"],
        "popup_COM": com_popup.get(float(t), float("nan")),
    })
cmp_df = pd.DataFrame(rows)
cmp_df["diff"] = cmp_df["fn_audit_COM"] - cmp_df["popup_COM"]
print("\nCOM parity (fn_audit vs popup):")
print(cmp_df.to_string(index=False))

# NaN-NaN = sama-sama undefined (bukan beda rumus)
n_diff = int((cmp_df["diff"].abs() > 1e-9).sum())
print(f"\nbaris dgn COM beda: {n_diff} dari {len(cmp_df)}")
print("VERDICT parity claim 'PERSIS formula pivot': "
      f"{'BUG (rumus keempat hidup)' if n_diff else 'NOT-BUG'}")

ok_exp = True
for t, exp in EXPECTED_COM.items():
    fa = cmp_df.loc[cmp_df["t"] == t, "fn_audit_COM"].iloc[0]
    po = cmp_df.loc[cmp_df["t"] == t, "popup_COM"].iloc[0]
    if not (abs(fa - exp) < 1e-9 and abs(po - exp) < 1e-9):
        ok_exp = False
        print(f"  MISMATCH t={t}: fn_audit={fa} popup={po} EXPECTED={exp}")
for t in (3, 4):
    fa = cmp_df.loc[cmp_df["t"] == t, "fn_audit_COM"].iloc[0]
    po = cmp_df.loc[cmp_df["t"] == t, "popup_COM"].iloc[0]
    if not (pd.isna(fa) and pd.isna(po)):
        ok_exp = False
        print(f"  MISMATCH t={t}: fn_audit={fa} popup={po} EXPECTED=undefined")
print("VERDICT BEBEK com row {1:10, 2:5, 3:undef, 4:undef, 5:5, 6:2}: "
      f"{'NOT-BUG' if ok_exp else 'BUG'}")

# sanity: v3.11.5 basis selisih = BM - IN (BEBEK t=3: BM 0 - IN 10 = -10)
r3 = be[be["Tanggal"] == 3].iloc[0]
print(f"\nSelisih Harian BEBEK t=3 (BM-IN): EXPECTED = -10, "
      f"ACTUAL = {r3['Selisih Harian']} -> "
      f"{'NOT-BUG' if r3['Selisih Harian'] == -10 else 'BUG'}")
