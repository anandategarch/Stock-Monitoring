"""PROBE v3.11.11-A — DETAIL ANALISA (fitur #1 user).

User: "rekap selisih in itu bagian tab analisa detailkan lagi, resto mana
dan tanggal mana dan selisih berapa di semua analisa."

Verifies (EXPECTED vs ACTUAL):
  A. seksi 1 UMUR   → payload umur_top: top-8 baris gantung TERTUA, each
                      {resto, barang, tgl, umur, selisih}.
  B. seksi 2 RESTO  → payload resto[i].detail: per-tanggal {tgl, net, n}
                      top-4 |net| (resto mana · tanggal mana · selisih).
  C. seksi 3 SISTEMIK → payload items[i].detail: per-resto {resto, net,
                      n, tgls} top-4 (barang lintas ≥3 resto).
  D. seksi 4 RESOLVE → payload resolve.masih_top: pasangan MASIH GANTUNG
                      {resto, barang, tgl, selisih} top-8.
  E. seksi 5/6      → top 8 baris + field 'selisih' di tiap baris.
  F. RENDER         → _render_analisa jalan tanpa exception & panel berisi
                      teks '↳' (baris detail resto) + kolom SELISIH.

Jalankan: DISPLAY=:99 python3 probes/v31111/probe_analisa_detail.py
"""
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd  # noqa: E402

from src.ui.in_selisih_view import InSelisihView  # noqa: E402

ROWS = []


def _r(barang, resto, tgl, selisih, in_=0.0, bm=0.0, dso=0.0, bk=0.0,
       com=0.0):
    ROWS.append({
        "Resto": resto, "Nama Barang": barang, "Tanggal": tgl,
        "Selisih IN": selisih, "IN": in_, "Qty BK": bk, "COM": com,
        "Delta SO": dso, "Qty BM": bm,
    })


# --- seksi 1: umur — baris tanggal 1 harus TERTUA (umur = 30−1 = 29) ------
_r("BRG TUA", "R-ALPHA", 1, -9.0)          # umur terbesar → umur_top[0]
_r("BRG TUA", "R-ALPHA", 30, 0.0)          # resolved (terakhir 0)
# --- seksi 2: resto dengan selisih di 3 tanggal ---------------------------
_r("BRG A", "R-BETA", 5, 10.0)
_r("BRG A", "R-BETA", 7, -30.0)            # |net| terbesar utk R-BETA
_r("BRG A", "R-BETA", 20, 4.0)
_r("BRG B", "R-BETA", 7, -2.0)
# --- seksi 3: barang sistemik (≥3 resto) ----------------------------------
for rs in ("R-GAMMA", "R-DELTA", "R-EPS"):
    _r("BRG SIS", rs, 10, 6.0)
    _r("BRG SIS", rs, 14, -8.0)
# --- seksi 4: masih gantung -----------------------------------------------
_r("BRG HANG", "R-ZETA", 25, 77.0)         # last row nonzero → masih
# --- seksi 5: anomali ΔSO besar -------------------------------------------
_r("BRG DSO", "R-ETA", 12, 3.0, dso=250.0)
_r("BRG DSO", "R-ETA", 13, 0.0, dso=-180.0)
# --- seksi 6: COM minus ----------------------------------------------------
_r("BRG COM", "R-THETA", 9, -1.0, com=-42.0)

DF = pd.DataFrame(ROWS)

root = tk.Tk()
root.withdraw()
view = InSelisihView(tk.Toplevel(root))
view._month_len = 30
view._lalu_month_len = 31

fails = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        fails.append(name)


# ---- A/B/C/D/E: payload --------------------------------------------------
p = view._compute_analisa(DF)

# A. umur_top
ut = p.get("umur_top") or []
check("A1 umur_top hadir (top-8 tertua)", isinstance(ut, list) and len(ut) >= 1,
      f"len={len(ut)}")
top1 = ut[0] if ut else {}
check("A2 baris tertua = BRG TUA @ R-ALPHA tgl 1 selisih -9",
      top1.get("barang") == "BRG TUA" and top1.get("resto") == "R-ALPHA"
      and top1.get("tgl") == 1 and top1.get("selisih") == -9.0,
      f"got {top1}")
check("A3 tiap baris umur_top punya resto+barang+tgl+umur+selisih",
      all({"resto", "barang", "tgl", "umur", "selisih"} <= set(d) for d in ut))

# B. resto detail
lb = p.get("resto") or []
beta = next((d for d in lb if d["resto"] == "R-BETA"), None)
check("B1 R-BETA hadir di leaderboard", beta is not None)
det = (beta or {}).get("detail") or []
check("B2 detail R-BETA = 3 tanggal (5,7,20)", len(det) == 3,
      f"len={len(det)}")
if det:
    check("B3 detail top-1 = tgl 7 net -32 (BRG A -30 + BRG B -2), 2 item",
          det[0]["tgl"] == 7 and det[0]["net"] == -32.0 and det[0]["n"] == 2,
          f"got {det[0]}")
    check("B4 tiap detail punya tgl+net+n",
          all({"tgl", "net", "n"} <= set(x) for x in det))

# C. sistemik detail
s3 = (p.get("sistemik") or {}).get("items") or []
sis = next((d for d in s3 if d["barang"] == "BRG SIS"), None)
check("C1 BRG SIS hadir (3 resto)", sis is not None and sis.get("n_resto") == 3)
sdet = (sis or {}).get("detail") or []
check("C2 detail BRG SIS = 3 resto", len(sdet) == 3, f"len={len(sdet)}")
if sdet:
    check("C3 tiap resto net -2 (6−8) + tgls [10,14]",
          all(x["net"] == -2.0 and x["tgls"] == [10, 14] for x in sdet),
          f"got {sdet}")

# D. resolve masih_top
mt = (p.get("resolve") or {}).get("masih_top") or []
check("D1 masih_top hadir", len(mt) >= 1, f"len={len(mt)}")
hang = next((d for d in mt if d["barang"] == "BRG HANG"), None)
check("D2 BRG HANG masih gantung tgl 25 selisih 77 @ R-ZETA",
      hang is not None and hang.get("tgl") == 25
      and hang.get("selisih") == 77.0 and hang.get("resto") == "R-ZETA",
      f"got {hang}")

# E. anomali & com_minus: 8 slot + field selisih
a5 = (p.get("anomali") or {}).get("top") or []
check("E1 anomali top maks 8 + tiap baris punya 'selisih'",
      len(a5) <= 8 and a5 and all("selisih" in d for d in a5),
      f"len={len(a5)}")
c6 = (p.get("com_minus") or {}).get("top") or []
check("E2 com_minus top maks 8 + tiap baris punya 'selisih'",
      len(c6) <= 8 and c6 and all("selisih" in d for d in c6),
      f"len={len(c6)}")
dso1 = next((d for d in a5 if d["barang"] == "BRG DSO" and d["tgl"] == 12),
            None)
check("E3 anomali row BRG DSO tgl 12 dso 250 selisih 3",
      dso1 is not None and dso1.get("dso") == 250.0
      and dso1.get("selisih") == 3.0, f"got {dso1}")

# F. render penuh (mode 📈 Analisa) — panel berisi baris detail
try:
    view._analisa_payload = p
    view._render_analisa(p)
    texts = []

    def _walk(w):
        if isinstance(w, tk.Label):
            texts.append(w.cget("text"))
        for c in w.winfo_children():
            _walk(c)

    _walk(view._analisa_card)
    joined = "\n".join(texts)
    check("F1 render jalan + ada baris detail '↳ tgl' (seksi resto)",
          "↳ tgl" in joined)
    check("F2 render berisi header kolom SELISIH (seksi umur/masih/com)",
          any("SELISIH" in t for t in texts))
    check("F3 render seksi sistemik '↳ R-' + '(tgl",
          "↳ R-" in joined and "(tgl" in joined)
    print("F-info: contoh baris detail:",
          next((t for t in texts if t.startswith("↳")), "<tidak ada>"))
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check("F render tanpa exception", False, repr(e))

view.destroy()
root.destroy()
print()
if fails:
    print(f"VERDICT: FAIL ({len(fails)}): {fails}")
    sys.exit(1)
print("VERDICT: ALL PASS — detail resto·tanggal·selisih hadir di SEMUA "
      "seksi analisa (umur/resto/sistemik/resolve/anomali/com-minus).")
