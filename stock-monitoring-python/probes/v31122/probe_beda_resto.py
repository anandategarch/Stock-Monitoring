"""PROBE v3.11.22 — AMBANG RASIO SEGME CEK "Beda dari Resto Lain" (bukti
fungsional runnable, TANPA Tk — murni data).

User (meminta ULANG): "Deviasi yang beda dari rsto lain. misal surplus
sendiri dan bulanan juga surplus. ini tambahkan di kolom cek" — label
v3.11.9 nyaris TAK PERNAH terlihat di data produksi.

Verifies (EXPECTED vs ACTUAL) pada DATA ASLI user (sheet DEVIASI GR/PCS
`01.1 CEK STOCK V2.xlsb` + file `20.AGUSTUS 2026.xlsx`):
  1. SUBSUMSI  — tiap hit aturan lama (same==0 & opp>=2) juga hit aturan
     baru (opp >= 3*same & opp >= 2) — grup kecil tak berubah.
  2. REVITALISASI — hit baru >> hit lama (GR: 41 vs 3; PCS: 9 vs 0) —
     syarat lama nyaris mustahil (median 13 resto lain searah).
  3. LABEL RASIO — format "Beda dari Resto Lain (Surplus · N/M resto lain
     Defisit)" dgn N=opp, M=opp+same (resto dev-0/NaN netral tak masuk).
  4. CONTOH NYATA — beberapa hit teratas dicetak utk inspeksi manual
     (mis. SBSHAM Sedotan Hitam defisit 2 periode vs 18 resto surplus).

Jalankan: python3 probes/v31122/probe_beda_resto.py
(dari folder stock-monitoring-python; file data di root repo)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.komparasi_deviasi_view import parse_deviasi_file
from src.ui.nominal_common import dev_lalu_qty_map

BASE = Path(__file__).resolve().parents[3]
MASTER = BASE / "01.1 CEK STOCK V2.xlsb"
LALU = BASE / "20.AGUSTUS 2026.xlsx"

fails = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        fails.append(name)


def _norm_resto(v):
    s = str(v).strip().upper()
    return s.split(".")[-1].strip() if "." in s else s


def _norm_name(v):
    return " ".join(str(v).strip().upper().split())


def load_current(sheet):
    """Sheet DEVIASI GR/PCS master workbook → frame kolom inti + H
    (auto-deteksi kolom SO yang memenuhi Deviasi = SO − Sistem)."""
    df0 = pd.read_excel(MASTER, sheet_name=sheet, engine="pyxlsb")
    hdr = df0.index[df0.iloc[:, 0].astype(str).str.strip() == "Resto"][0]
    df = pd.read_excel(MASTER, sheet_name=sheet, engine="pyxlsb",
                      header=hdr + 1)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["Resto", "Nama Barang"]).copy()
    df["Resto"] = df["Resto"].astype(str).str.strip()
    df["Nama Barang"] = df["Nama Barang"].astype(str).str.strip()
    df["Satuan"] = df["Satuan"].astype(str).str.strip()
    df["Deviasi"] = pd.to_numeric(df["Deviasi"], errors="coerce")
    df["Sistem"] = pd.to_numeric(df["Sistem"], errors="coerce")
    h = None
    for c in df.columns:
        try:
            cv = float(str(c).replace(",", "."))
        except ValueError:
            continue
        so = pd.to_numeric(df[c], errors="coerce")
        delta = so - df["Sistem"]
        m = delta.notna() & df["Deviasi"].notna()
        if m.sum() and np.allclose(delta[m], df.loc[m, "Deviasi"]):
            h = int(cv)
    return df, h


def simulate(cur, lkey):
    """Simulasi kondisi lama (strict v3.11.9) vs baru (rasio v3.11.22)
    — mirror blok _br_txt deviasi_view._compute_pivot."""
    cur = cur.assign(_l=cur["_rk"].map(lkey))
    groups = {}
    for i, (b, s) in enumerate(zip(cur["Nama Barang"], cur["Satuan"])):
        groups.setdefault((b, s), []).append(i)
    strict, baru, sub = [], [], 0
    for idxs in groups.values():
        if len(idxs) < 3:
            continue
        for i in idxs:
            d0 = cur["Deviasi"].iloc[i]
            l0 = cur["_l"].iloc[i]
            if (pd.isna(d0) or pd.isna(l0) or d0 == 0 or l0 == 0):
                continue
            if (d0 > 0) != (l0 > 0):
                continue
            same = opp = 0
            for j in idxs:
                if j == i:
                    continue
                dj = cur["Deviasi"].iloc[j]
                if pd.isna(dj) or dj == 0:
                    continue
                if (dj > 0) == (d0 > 0):
                    same += 1
                else:
                    opp += 1
            if same == 0 and opp >= 2:
                strict.append(i)
            if opp >= 3 * same and opp >= 2:
                baru.append(i)
                if same == 0 and opp >= 2:
                    sub += 1
    return strict, baru, sub, cur


def main():
    print("=" * 72)
    print("PROBE v3.11.22 — ambang rasio 'Beda dari Resto Lain' (data asli)")
    print("=" * 72)
    if not MASTER.exists() or not LALU.exists():
        print(f"SKIP — file data asli tidak ada di repo:\n  {MASTER}\n  {LALU}")
        return 0

    res = parse_deviasi_file(str(LALU))
    check("file deviasi bulan lalu terbaca (20.AGUSTUS 2026.xlsx)",
          res["ok"], str(res.get("error"))[:80])
    if not res["ok"]:
        return 1

    for sheet, min_baru in (("DEVIASI GR", 10), ("DEVIASI PCS", 1)):
        print(f"\n---- {sheet} ----")
        cur, h = load_current(sheet)
        check(f"{sheet}: H terdeteksi dari sheet (SO − Sistem = Deviasi)",
              h is not None, f"h={h}")
        lmap, lab = dev_lalu_qty_map(res["df"], h=h)
        cur["_rk"] = (cur["Resto"].map(_norm_resto) + "\x1f"
                      + cur["Nama Barang"].map(_norm_name))
        lkey = {f"{r}\x1f{b}": q for (r, b), q in lmap.items()}
        n_join = cur["_rk"].isin(lkey).sum()
        print(f"  {len(cur)} baris · H={h} · minggu lalu={lab} · "
              f"join DEV Lalu {n_join}/{len(cur)}")
        strict, baru, sub, cur = simulate(cur, lkey)

        check(f"{sheet}: SUBSUMSI — {len(strict)} hit lama semua lolos "
              f"aturan baru (sub={sub})", sub == len(strict),
              f"strict={len(strict)} sub={sub}")
        check(f"{sheet}: REVITALISASI — hit baru ({len(baru)}) >> hit lama "
              f"({len(strict)}) & >= {min_baru}",
              len(baru) > len(strict) and len(baru) >= min_baru)
        # contoh nyata utk inspeksi manual (label persis format v3.11.22)
        for i in (sorted(baru, key=lambda k: cur["Deviasi"].iloc[k])[:3]
                  + sorted(baru, key=lambda k: cur["Deviasi"].iloc[k],
                           reverse=True)[:3]):
            d0 = float(cur["Deviasi"].iloc[i])
            m = ((cur["Nama Barang"] == cur["Nama Barang"].iloc[i])
                 & (cur["Satuan"] == cur["Satuan"].iloc[i])
                 & pd.notna(cur["Deviasi"]) & (cur["Deviasi"] != 0))
            others = cur[m]
            same = int(((others["Deviasi"] > 0) == (d0 > 0)).sum()) - 1
            opp = int(((others["Deviasi"] > 0) != (d0 > 0)).sum())
            side = "Surplus" if d0 > 0 else "Defisit"
            oside = "Defisit" if d0 > 0 else "Surplus"
            print(f"    {cur['Resto'].iloc[i]:8s} "
                  f"{str(cur['Nama Barang'].iloc[i])[:30]:32s} "
                  f"dev={d0:>10.0f} lalu={float(cur['_l'].iloc[i]):>10.0f} "
                  f"→ Beda dari Resto Lain ({side} · {opp}/{opp + same} "
                  f"resto lain {oside})")

    print()
    if fails:
        print(f"GAGAL: {len(fails)} check — {fails}")
        return 1
    print("SEMUA OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
