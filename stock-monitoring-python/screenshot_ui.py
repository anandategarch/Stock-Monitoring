"""
screenshot_ui.py — Render app v3.1 + screenshot tiap tab & fitur baru.
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

from test_ui_redesign import make_mock_append1, make_mock_rincian, wait_view

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

    # Load data — pivot default mode RESTO
    app.pivot_view.load_data(append1)
    app.notebook.select(app.tab_pivot)
    wait_view(root, app.pivot_view)
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

    # Deviasi GR
    app.deviasi_gr_view.load_data(append1)
    app.notebook.select(app.tab_deviasi_gr)
    wait_view(root, app.deviasi_gr_view)
    shot("8-deviasi-gr")

    # Deviasi PCS
    app.deviasi_pcs_view.load_data(append1)
    app.notebook.select(app.tab_deviasi_pcs)
    wait_view(root, app.deviasi_pcs_view)
    shot("9-deviasi-pcs")

    # Laporan
    app.laporan_view.load_data(append1)
    app.notebook.select(app.tab_laporan)
    wait_view(root, app.laporan_view)
    shot("10-laporan")

    # Rincian PO
    app.rincian_view.load_data(rincian)
    app.notebook.select(app.tab_rincian)
    wait_view(root, app.rincian_view)
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
