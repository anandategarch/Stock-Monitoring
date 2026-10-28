"""
probe_merge_app.py — probe audit v3.11.15 MERGE-VERTIKAL di LEVEL APP
(lengkap: jalur load_data + select_and_wait, BUKAN view standalone).

Motivasi: probe_merge_vertikal.py menguji DeviasiView standalone
(dv.data = ...; _refresh). Audit app-level diperlukan karena jalur
load_data app bisa berbeda (kategori filter, shared state, urutan
render). Ditambah setelah VLM salah-baca screenshot harness pertama
(menyebut 'setiap baris bernama') — bukti programatik jalur yang SAMA
dengan harness screenshot_ui.py inilah yang autoritatif.

Jalankan di bawah Xvfb:
  DISPLAY=:99 python3 probes/v31115/probe_merge_app.py

Fixture make_mock_append1 (konvensi repo):
  GR: ADONAN GORENG MEKAR (MLGPAR saja — singleton) · AYAM FILET &
      GULA PASIR (MLGPAR+SBYKET — grup 2 baris) · BARANG ACR (MLGPAR —
      singleton) → 6 baris GR.
  PCS: KOPI BUBUK 100G & SUSU UHT 1L (MLGPAR+SBYKET) → 4 baris PCS.

Verifikasi per tab:
  (1) _vmerge aktif n = jumlah baris;
  (2) layout 'Nama Barang' = kontrak head-run dari RAW snapshot
      (baris lanjutan run kosong; singleton bernama sendiri);
  (3) layout 'Rank' + 'CEK' = kontrak head-run dari _rank_map/_cek_map;
  (4) RAW utuh per-baris (key ada di ketiga map — teks boleh kosong:
      rank dev-0 → '' kontrak v3.9.65).

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
    """{iid: teks} — layout head-run dari RAW (baris lanjutan '')."""
    snaps = view._row_snaps
    rk = view._rank_map
    ck = view._cek_map
    out, prev = {}, None
    for k in tree.get_children(""):
        ks = str(k)
        b = str((snaps.get(ks) or {}).get("barang", ""))
        if col == "Nama Barang":
            key, text = b, b
        elif col == "Rank":
            t = str(rk.get(ks, ""))
            key, text = (b, t), t
        else:
            t = str(ck.get(ks, ""))
            key, text = (b, t), t
        out[k] = text if key != prev else ""
        prev = key
    return out


def check_tab(root, app, tab, view, label, expect_n, expect_groups2):
    print(f"== {label} (jalur load_data app) ==")
    kids = list(view.tree.get_children(""))
    ok(f"{label}: jumlah baris {expect_n}",
       len(kids) == expect_n, f"n={len(kids)}")
    vm = getattr(view.tree, "_vmerge", None)
    ok(f"{label}: _vmerge aktif n={expect_n}",
       isinstance(vm, dict) and vm.get("n") == expect_n,
       f"vm={type(vm).__name__}")
    # jumlah grup 2-baris (merge nyata terlihat)
    disp = [str(view.tree.set(k, "Nama Barang")) for k in kids]
    n_empty = sum(1 for d in disp if not d.strip())
    ok(f"{label}: grup 2-baris ter-merge ({expect_groups2} baris lanjutan "
       "kosong)",
       n_empty == expect_groups2, f"empty={n_empty}")
    for col in ("Nama Barang", "Rank", "CEK"):
        exp = head_expected(view, view.tree, col)
        ok(f"{label}: layout head-run kolom {col!r}",
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
    # GULA PASIR(2) → 2 baris lanjutan kosong.
    app.deviasi_gr_view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    for _ in range(40):
        root.update()
        time.sleep(0.01)
    check_tab(root, app, app.tab_deviasi_gr, app.deviasi_gr_view,
              "GR", expect_n=6, expect_groups2=2)

    # PCS: 4 baris — KOPI BUBUK(2) · SUSU UHT(2) → 2 baris lanjutan
    # kosong.
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
    print("PROBE v3.11.15 MERGE APP-LEVEL: SEMUA OK")


if __name__ == "__main__":
    main()
