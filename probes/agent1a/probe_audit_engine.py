"""
probe_audit_engine.py — build_audit_rekap (VBA port) core math:
cut-off resolution, VALID (Sistem Masuk), deviasi murni, saldo kumulatif.
Direct input in the 10 canonical AUDIT_INPUT_COLUMNS.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import pandas as pd

from src.pipeline.fn_audit import (AUDIT_INPUT_COLUMNS, build_audit_rekap,
                                   ST_CUTOFF, ST_IN_CUTOFF, ST_VALID,
                                   ST_DEV_MURNI, ST_OK_MATCH, ST_OK)


def frame(rows):
    df = pd.DataFrame(rows, columns=[
        "Resto", "Nama Item", "UoM", "Tanggal", "Hasil SO",
        "Qty SO Harian", "Qty SJ", "Qty RI", "Qty Pembelian", "Selisih Qty"])
    return df


def show(title, df, kpi):
    out, k = build_audit_rekap(df)
    print(f"\n== {title}")
    print(out[["Tanggal", "Hasil SO", "Qty SO Harian", "Qty SJ",
               "Penerimaan Sistem", "Selisih Harian", "Saldo Kumulatif",
               "Status Analisis Audit"]].to_string(index=False))
    print("KPI:", {kk: k[kk] for kk in ("cutoff", "omit", "deviasi_murni",
                                        "deviasi_qty", "ok")})
    return out, k


# ---- S1: cut-off resolve (+5 lalu -5, jeda 2 hari)
df1 = frame([
    ("R", "X", "GR", 1, None, 0, 5, 0, 0, -5),
    ("R", "X", "GR", 2, None, 0, 0, 0, 0, 0),
    ("R", "X", "GR", 3, None, 5, 0, 0, 0, 5),
])
out1, k1 = show("S1 cut-off (selisih -5 t1, +5 t3)", df1, None)
s = out1["Status Analisis Audit"].tolist()
exp_s1 = [ST_CUTOFF, ST_IN_CUTOFF, ST_CUTOFF]
ok1 = s == exp_s1 and "Beda 2 Hari" in out1["Detail & Catatan Audit"].iloc[0]
print(f"EXPECTED statuses {exp_s1}, ACTUAL {s} -> "
      f"{'NOT-BUG' if ok1 else 'BUG'}")

# ---- S2: VALID (Sistem Masuk): SO naik + BM 0 + IN > 0
df2 = frame([
    ("R", "X", "GR", 1, 100, 0, 0, 0, 0, 0),
    ("R", "X", "GR", 2, 150, 0, 50, 0, 0, -50),
])
out2, k2 = show("S2 VALID (SO 100->150, BM 0, IN 50)", df2, None)
ok2 = (out2["Status Analisis Audit"].tolist() == [ST_OK_MATCH, ST_VALID]
       and k2["omit"] == 1)
print(f"EXPECTED [OK (Matching), VALID], ACTUAL "
      f"{out2['Status Analisis Audit'].tolist()} -> "
      f"{'NOT-BUG' if ok2 else 'BUG'}")

# ---- S3: deviasi murni (IN tanpa BM, tak pernah resolve)
df3 = frame([
    ("R", "X", "GR", 1, None, 0, 10, 0, 0, -10),
    ("R", "X", "GR", 2, None, 0, 0, 0, 0, 0),
])
out3, k3 = show("S3 deviasi murni (IN 10 tanpa BM)", df3, None)
ok3 = (out3["Status Analisis Audit"].tolist() == [ST_DEV_MURNI, ST_OK]
       and k3["deviasi_murni"] == 1
       and abs(k3["deviasi_qty"] - (-10.0)) < 1e-9)
print(f"EXPECTED [DEVIASI MURNI, OK] + deviasi_qty -10, ACTUAL "
      f"{out3['Status Analisis Audit'].tolist()} qty={k3['deviasi_qty']} -> "
      f"{'NOT-BUG' if ok3 else 'BUG'}")

# ---- S4: saldo kumulatif lintas baris + group boundary (2 pasangan)
df4 = frame([
    ("R1", "X", "GR", 1, None, 3, 0, 0, 0, 3),
    ("R1", "X", "GR", 2, None, 0, 1, 0, 0, -1),
    ("R2", "Y", "GR", 1, None, 7, 0, 0, 0, 7),   # grup lain — tak menyambung
])
out4, k4 = show("S4 group boundary (saldo tak bocor antar pasangan)", df4, None)
ok4 = (out4["Saldo Kumulatif"].tolist() == [3.0, 2.0, 7.0]
       and out4["Status Analisis Audit"].tolist()
       == [ST_DEV_MURNI, ST_DEV_MURNI, ST_DEV_MURNI])
print(f"EXPECTED saldo [3, 2, 7] (cumsum selisih per grup), ACTUAL "
      f"{out4['Saldo Kumulatif'].tolist()} -> "
      f"{'NOT-BUG' if ok4 else 'BUG'}")
