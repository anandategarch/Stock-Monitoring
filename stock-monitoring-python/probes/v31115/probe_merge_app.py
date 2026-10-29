"""
probe_merge_app.py — probe audit MERGE-VERTIKAL di LEVEL APP (lengkap:
jalur load_data + select_and_wait, BUKAN view standalone).

v3.11.15: kontrak per-kolom run (Rank ikat-tie, CEK label identik).
v3.11.16: kontrak KELOMPOK — TIGA kolom (Nama Barang · CEK · Rank) merge
atas SPAN KELOMPOK BARANG yang sama; teks kolom: nama barang · CEK
GABUNGAN kelompok (_gcek_map) · RANK KELOMPOK (_grank_map). Port ini
menyinkronkan probe ke kontrak kelompok (probe versi v3.11.15 permanen
GAGAL di HEAD ≥ v3.11.16 — run lama tidak lagi valid).

Jalankan di bawah Xvfb:
  DISPLAY=:99 python3 probes/v31115/probe_merge_app.py

Fixture make_mock_append1 (konvensi repo):
  GR: ADONAN GORENG MEKAR (MLGPAR saja — singleton) · AYAM FILET &
      GULA PASIR (MLGPAR+SBYKET — grup 2 baris) · BARANG ACR (MLGPAR —
      singleton) → 6 baris GR.
  PCS: KOPI BUBUK 100G & SUSU UHT 1L (MLGPAR+SBYKET) → 4 baris PCS.

Verifikasi per tab:
  (1) _vmerge aktif n = jumlah baris;
  (2) layout 'Nama Barang' = kontrak KELOMPOK (span barang; baris
      lanjutan kosong; singleton bernama sendiri);
  (3) layout 'Rank' = _grank_map (rank kelompok) · 'CEK' = _gcek_map
      (gabungan kelompok) — sejajar DI BARIS HEAD yang sama;
  (4) RAW per-baris utuh (_row_snaps/_rank_map/_cek_map — paritas sheet).

EXPECTED: 2 blok OK (GR + PCS). Exit code 0 bila semua lulus.
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

from src.ui.app import StockMonitorApp
from test_ui_redesign import (
    make_mock_append1,
    select_and_wait,
)

FAILED = []


def ok(nama, kondisi, detail=""):
    print(("  OK " if kondisi else "  GAGAL ") + nama
          + (f" — {detail}" if detail else ""))
    if not kondisi:
        FAILED.append(nama)


def head_expected(view, tree, col):
    """{iid: teks} — kontrak KELOMPOK v3.11.16: nilai di baris HEAD
    kelompok barang; baris lanjutan ''. Rank/CEK = nilai KELOMPOK
    (_grank_map/_gcek_map — sejajar di head yang sama)."""
    snaps = view._row_snaps
    grk = view._grank_map
    gck = view._gcek_map
    out, prev = {}, None
    for k in tree.get_children(""):
        ks = str(k)
        b = str((snaps.get(ks) or {}).get("barang", ""))
        if col == "Nama Barang":
            text = b
        elif col == "Rank":
            text = str(grk.get(ks, ""))
        else:
            text = str(gck.get(ks, ""))
        out[k] = text if b != prev else ""
        prev = b
    return out


def check_tab(root, app, tab, view, label, expect_n, expect_groups2):
    print(f"== {label} (jalur load_data app) ==")
    kids = list(view.tree.get_children(""))
    ok(f"{label}: jumlah baris {expect_n}",
       len(kids) == expect_n, f"n={len(kids)}")
    vm = getattr(view.tree, "_vmerge", None)
    ok(f"{label}: _vmerge aktif n={expect_n} (3 kolom run)",
       isinstance(vm, dict) and vm.get("n") == expect_n
       and set(vm.get("runs", {})) == {"Nama Barang", "Rank", "CEK"},
       f"vm={type(vm).__name__}")
    # jumlah grup 2-baris (merge nyata terlihat)
    disp = [str(view.tree.set(k, "Nama Barang")) for k in kids]
    n_empty = sum(1 for d in disp if not d.strip())
    ok(f"{label}: grup 2-baris ter-merge ({expect_groups2} baris lanjutan "
       "kosong)",
       n_empty == expect_groups2, f"empty={n_empty}")
    heads = [k for k in kids if str(view.tree.set(k, "Nama Barang")).strip()]
    ok(f"{label}: jumlah head = jumlah kelompok",
       len(heads) == expect_n - expect_groups2,
       f"heads={len(heads)}")
    for col in ("Nama Barang", "Rank", "CEK"):
        exp = head_expected(view, view.tree, col)
        ok(f"{label}: layout KELOMPOK kolom {col!r} (nilai sejajar di head)",
           all(str(view.tree.set(k, col)) == exp[k] for k in kids))
    ok(f"{label}: RAW snapshot/_rank_map/_cek_map lengkap (key ada)",
       all(str(k) in view._row_snaps
           and str((view._row_snaps.get(str(k)) or {})
                   .get("barang", ""))
           and str(k) in view._rank_map
           and str(k) in view._cek_map
           for k in kids))


def main():
    real = sys.stdout, sys.stderr
    root = tk.Tk()
    root.geometry("1440x900+0+0")
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real
    append1 = make_mock_append1()

    # GR: 6 baris — ADONAN(1) · AYAM FILET(2) · BARANG ACR(1) ·
    # GULA PASIR(2) → 2 baris lanjutan kosong, 4 kelompok.
    app.deviasi_gr_view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    for _ in range(40):
        root.update()
        time.sleep(0.01)
    check_tab(root, app, app.tab_deviasi_gr, app.deviasi_gr_view,
              "GR", expect_n=6, expect_groups2=2)

    # PCS: 4 baris — KOPI BUBUK(2) · SUSU UHT(2) → 2 baris lanjutan
    # kosong, 2 kelompok.
    app.deviasi_pcs_view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_pcs, app.deviasi_pcs_view)
    for _ in range(40):
        root.update()
        time.sleep(0.01)
    check_tab(root, app, app.tab_deviasi_pcs, app.deviasi_pcs_view,
              "PCS", expect_n=4, expect_groups2=2)

    root.destroy()
    print()
    if FAILED:
        print(f"PROBE GAGAL: {FAILED}")
        sys.exit(1)
    print("PROBE v3.11.15 MERGE APP-LEVEL (kontrak kelompok v3.11.16): "
          "SEMUA OK")


if __name__ == "__main__":
    main()
