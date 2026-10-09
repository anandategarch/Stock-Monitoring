"""
screenshot_ui.py — Render app v3.3 + screenshot tiap tab & fitur baru.
Jalankan di bawah Xvfb (DISPLAY=:99).

Output: /tmp/shots/*.png
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

from src.ui.app import StockMonitorApp
from test_ui_redesign import (
    make_mock_append1,
    make_mock_rincian,
    select_and_wait,
    wait_view,
)

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)


def shot(name, delay=0.35):
    time.sleep(delay)
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(xdisplay=os.environ.get("DISPLAY", ":99"))
        img.save(OUT / f"{name}.png")
        print(f"  📸 {name}.png ({img.size})")
    except Exception as e:
        print(f"  ! screenshot gagal {name}: {e}")


def pump(root, seconds=0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def main():
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    root.geometry("1440x900+0+0")
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real_stdout, real_stderr

    append1 = make_mock_append1()
    rincian = make_mock_rincian()

    pump(root, 0.3)
    shot("1-config")

    # Proses tab (spinner idle)
    app.notebook.select(app.tab_proses)
    pump(root, 0.3)
    shot("2-proses")

    # Load data — pivot default mode RESTO (v3.2: lazy → select+wait)
    app.pivot_view.load_data(append1)
    select_and_wait(root, app, app.tab_pivot, app.pivot_view)
    shot("3-pivot-resto")

    # Header filter popup terbuka (klik heading #0)
    root.update()
    app.pivot_view.tree.event_generate("<Button-1>", x=20, y=10)
    pump(root, 0.4)
    shot("4-pivot-resto-headerfilter-open")

    # aktifkan filter (hanya 1 barang) → corong teal
    hf = app.pivot_view.header_filter
    if hf._popup is not None and hf._popup.winfo_exists():
        for v, var in hf._vars.items():
            var.set(v == "ADONAN GORENG MEKAR")
        hf._update_count()
        hf._emit()
        wait_view(root, app.pivot_view)
        pump(root, 0.4)
        shot("5-pivot-resto-filtered")
        hf._close()
        pump(root, 0.2)

    # Pivot mode TANGGAL
    app.pivot_view._on_mode_change(1)
    wait_view(root, app.pivot_view)
    shot("6-pivot-tanggal")

    # Perbesar (maximize) pivot resto
    app.pivot_view._on_mode_change(0)
    wait_view(root, app.pivot_view)
    win, mtree = app.pivot_view._maximize()
    pump(root, 1.0)
    shot("7-pivot-maximized")
    win.destroy()
    pump(root, 0.2)

    # Deviasi GR (v3.2: lazy + kolom ✓ + tanpa KPI row)
    app.deviasi_gr_view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    shot("8-deviasi-gr")

    # v3.2: centang ✓ 2 baris pertama → ikut screenshot (☑ + badge tab)
    tree = app.deviasi_gr_view.tree
    class _Ev:
        pass
    for iid in list(tree.get_children(""))[:2]:
        bbox = tree.bbox(iid)
        if bbox:
            ev = _Ev()
            ev.widget = tree
            ev.x, ev.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
            app.deviasi_gr_view._on_tree_click(ev)
    pump(root, 0.3)
    shot("8b-deviasi-gr-followup-checked")

    # Deviasi PCS
    app.deviasi_pcs_view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_pcs, app.deviasi_pcs_view)
    shot("9-deviasi-pcs")

    # Laporan
    app.laporan_view.load_data(append1)
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    shot("10-laporan")

    # v3.2: tab Follow Up (badge + snapshot rows)
    select_and_wait(root, app, app.tab_followup, app.followup_view)
    pump(root, 0.4)
    shot("10b-followup")

    # v3.4: tab Rekap Selisih IN + drill-down popup rincian dokumen
    from test_ui_redesign import make_mock_in_detail
    in_detail = make_mock_in_detail()
    app.in_selisih_view.load_data(append1, in_detail)
    select_and_wait(root, app, app.tab_in_selisih, app.in_selisih_view)
    shot("10c-rekap-selisih-in")

    # drill-down: double-click baris MLGPAR/AYAM FILET/Tgl 10
    from src.ui.in_selisih_view import InDetailPopup
    itree = app.in_selisih_view.tree
    for iid in itree.get_children(""):
        vals = itree.item(iid, "values")
        if vals[0] == "MLGPAR" and vals[1] == "10" and vals[2] == "AYAM FILET":
            bbox = itree.bbox(iid)
            class _Ev2:
                pass
            ev = _Ev2()
            ev.widget = itree
            ev.x, ev.y = bbox[0] + 10, bbox[1] + bbox[3] // 2
            app.in_selisih_view._on_double_click(ev)
            break
    pump(root, 0.5)
    shot("10d-rincian-in-popup")
    popups = [w for w in root.winfo_children()
              if isinstance(w, InDetailPopup) and w.winfo_exists()]
    if popups:
        popups[-1].destroy()
    pump(root, 0.2)

    # v3.4: ↔ Auto-Fit pada Rekap Selisih IN (kolom menyesuaikan konten)
    app.in_selisih_view._auto_fit()
    pump(root, 0.4)
    shot("10e-rekap-selisih-autofit")

    # Rincian PO
    app.rincian_view.load_data(rincian)
    select_and_wait(root, app, app.tab_rincian, app.rincian_view)
    shot("11-rincian")

    # Details popup (dari pivot resto — double-click style)
    from src.ui.details_popup import show_details_popup
    popup = show_details_popup(root, append1,
                               nama_barang="ADONAN GORENG MEKAR",
                               jenis="1.SO", filters={"NAMA RESTO": "MLGPAR"})
    wait_view(root, popup)
    pump(root, 0.4)
    shot("12-popup-detail")

    # Popup maximized
    pwin, pmtree = popup._maximize()
    pump(root, 1.0)
    shot("13-popup-maximized")
    pwin.destroy()
    pump(root, 0.2)

    # Loading overlay terlihat saat refresh (force show tanpa delay)
    popup.destroy()
    pump(root, 0.2)
    app.notebook.select(app.tab_pivot)
    pump(root, 0.2)
    app.pivot_view.overlay.show("Menghitung matrix pivot…", delay_ms=0)
    pump(root, 0.5)
    shot("14-loading-overlay")
    app.pivot_view.overlay.hide()

    pump(root, 0.2)
    root.destroy()
    print("SELESAI — semua screenshot di", OUT)


if __name__ == "__main__":
    main()
