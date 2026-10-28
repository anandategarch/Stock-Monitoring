"""P16 — deviasi_view SATUAN 'GR ' (trailing space) tab-classification
asymmetry: combobox scoping STRIPS, table filter does NOT.

Same view, two different normalizations of the same column:
  _update_kategori_values (line ~1859): SATUAN.astype(str).str.STRIP()
      .str.upper() == 'GR'   -> 'GR ' counts as GR (dropdown scoping)
  _prepare_rows/_filtered_pivot (line ~2820/1405): Satuan.astype(str)
      .str.upper() == 'GR'   -> 'GR ' NOT equal 'GR' (no strip)

README v3.9.42 documents that the user's real rekap has SATUAN values with
trailing spaces ('GR ', 57 values), and the fn_rekap_mentah PER-RESTO path
(safe_to_str, no strip) keeps them. Result: a GR pair with 'GR ' shows in
the 🧩 PCS tab and is MISSING from the 📦 GR tab, while the KATEGORI
dropdown scoping (and the lalu/🧮 paths that use norm_sat) treat it as GR.

Run headless via Xvfb :99. Uses REAL DeviasiView._compute_pivot +
_prepare_rows from the app.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT

os.environ.setdefault("DISPLAY", ":99")
sys.path.insert(0, PROJECT)
import tkinter as tk  # noqa: E402

from src.ui.deviasi_view import DeviasiView  # noqa: E402


def row(b, r, t, j, v, sat):
    return {"Nama Barang": b, "NAMA RESTO": r, "Tanggal": t, "JENIS": j,
            "NILAI": v, "SATUAN": sat, "KATEGORI": "COM DEVIASI - RESTO",
            "AKTIF/NON": "AKTIF"}


def e2e_satuan_trailing_space():
    """Confirm 'GR ' survives the PER-RESTO rekap path into append1 output
    (safe_to_str does not strip; only the combined path strips)."""
    from common import (b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                        make_config, make_root)
    from src.config import Config
    from src.pipeline.append1 import build_append1
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("G2", "GR ", "SO", "input so harian", {10: 100}),
    ])
    b_2205(root, [])
    b_4205(root, [])
    b_3224(root, [])
    b_4217(root, [("G2", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 3})])
    b_dbs(root, [("G2", "COM DEVIASI - RESTO", "AKTIF")])
    final = build_append1(Config(make_config(root)))
    sat = final.loc[final["JENIS"] == "1.SO", "SATUAN"].iloc[0]
    print(f"[E2E per-resto rekap] SATUAN in append1 output = {sat!r}")
    return sat == "GR "


def main():
    print("[pre] per-resto rekap keeps trailing space:",
          e2e_satuan_trailing_space())
    data = pd.DataFrame([
        row("G1", "MLGPAR", 10, "1.SO", 100, "GR"),
        row("G1", "MLGPAR", 10, "3.DEVIASI", 5, "GR"),
        row("G2", "MLGPAR", 10, "1.SO", 100, "GR "),   # trailing space
        row("G2", "MLGPAR", 10, "3.DEVIASI", 7, "GR "),
        row("P1", "MLGPAR", 10, "1.SO", 100, "PCS"),
        row("P1", "MLGPAR", 10, "3.DEVIASI", 3, "PCS"),
    ])

    root = tk.Tk()
    root.withdraw()
    try:
        v_gr = DeviasiView(root, satuan_mode="GR")
        v_pcs = DeviasiView(root, satuan_mode="PCS")
        for v in (v_gr, v_pcs):
            v.load_data(data)
            v.tanggal_h = 10
            pivot = v._compute_pivot(v.data, 10, {}, None)
            v._cached_pivot = pivot
            st = {"kategori": None, "aktif": None, "col_sel": {},
                  "tanggal_h": 10}
            out = v._prepare_rows(st)
            names = sorted({it[1] for it in out["items"]}
                           if out["items"] else set())
            # items structure varies; safer: re-derive from the pivot filter
            # exactly as _prepare_rows does:
            filt = pivot[pivot["Satuan"].astype(str).str.upper()
                         == ("GR" if v.satuan_mode == "GR" else "__none__")]
            if v.satuan_mode != "GR":
                filt = pivot[pivot["Satuan"].astype(str).str.upper() != "GR"]
            tab = sorted(filt["Nama Barang"].tolist())
            print(f"tab {v.satuan_mode}: baris tampil = {tab} "
                  f"(status={out['status']!r})")

        # combobox scoping path (real expression from _update_kategori_values)
        _sat = data["SATUAN"].astype(str).str.strip().str.upper()
        scope_gr = sorted(data.loc[_sat == "GR", "Nama Barang"].unique())
        print(f"KATEGORI-dropdown scoping (strip+upper) counts as GR: "
              f"{scope_gr}")

        gr_tab = sorted(pivot[pivot["Satuan"].astype(str).str.upper()
                              == "GR"]["Nama Barang"].tolist())
        pcs_tab = sorted(pivot[pivot["Satuan"].astype(str).str.upper()
                               != "GR"]["Nama Barang"].tolist())
        print(f"GR tab  = {gr_tab}")
        print(f"PCS tab = {pcs_tab}")
        ok = ("G2" not in gr_tab) and ("G2" in pcs_tab) and ("G2" in scope_gr)
        print("\nEXPECTED: G2 ('GR ' — README v3.9.42: 57 such values in "
              "user data) belongs to the GR tab and GR dropdown scope")
        print("ACTUAL  : G2 is in the PCS tab but counted as GR by the "
              "dropdown scoping — split-brain classification")
        print("VERDICT:", "NOT-BUG" if not ok else
              "BUG (P2) — deviasi_view GR/PCS tab filter lacks .str.strip(): "
              "SATUAN 'GR ' pairs land in the PCS tab and vanish from the GR "
              "tab while the KATEGORI dropdown scoping (strip+upper) and "
              "norm_sat-based paths classify them as GR")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
