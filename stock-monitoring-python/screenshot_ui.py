"""
screenshot_ui.py — Render app v3 + screenshot tiap tab (untuk review visual).
Jalankan di bawah Xvfb DISPLAY=:99.
"""
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from src.ui.app import StockMonitorApp

from test_ui_redesign import make_mock_append1, make_mock_rincian

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)


def shot(root, name):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(xdisplay=":99")
        img.save(OUT / f"{name}.png")
        print(f"  📸 {name}.png ({img.size})")
    except Exception as e:
        print(f"  ! screenshot gagal: {e}")


def main():
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    root.geometry("1440x900+0+0")
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real_stdout, real_stderr

    append1 = make_mock_append1()
    rincian = make_mock_rincian()
    app.pivot_view.load_data(append1)
    app.deviasi_gr_view.load_data(append1)
    app.deviasi_pcs_view.load_data(append1)
    app.laporan_view.load_data(append1)
    app.rincian_view.load_data(rincian)
    root.update()

    # Simulasi log console
    app._append_log_batched(
        "=" * 60 + "\n  STOCK MONITORING - PIPELINE RUNNER\n" + "=" * 60 +
        "\n  RootPath: C:\\KERJA\\1. RESTO\\9.NEW QUERY\\\n  Mode: LIGHT\n" +
        "-" * 60 + "\n  [1/2] Building Append1...\n  Rekap Berjalan: 9901 rows OK\n" +
        "  22.05: 4.221 rows OK\n  42.15: 8.730 rows OK\n" +
        "\n  Append1 result: 1920 rows\n" +
        "-" * 60 + "\n  [2/2] Building Rincian PO...\n  Rincian PO: 36 rows\n" +
        "\n  SELESAI dalam 12.4 detik\n" + "=" * 60 + "\n")
    app.kpi_status.set_value("SELESAI", "data siap dianalisis", "#16a34a")
    app.kpi_append.set_value("1,920", "baris pivot siap")
    app.kpi_rincian.set_value("36", "baris PO siap")
    app.kpi_elapsed.set_value("12.4 dtk", "total waktu proses")
    app.statusbar.set_status("SELESAI — Append1: 1,920 rows · Rincian PO: 36 rows",
                             "#16a34a")
    app.btn_export.configure(state="normal")  # GhostButton = ttk.Button
    app.btn_export_tb.configure(state="normal")
    root.update()

    tabs = [
        (app.tab_config, "1-config"),
        (app.tab_proses, "2-proses"),
        (app.tab_pivot, "3-pivot"),
        (app.tab_deviasi_gr, "4-deviasi-gr"),
        (app.tab_deviasi_pcs, "5-deviasi-pcs"),
        (app.tab_laporan, "6-laporan"),
        (app.tab_rincian, "7-rincian"),
    ]
    for tab, name in tabs:
        app.notebook.select(tab)
        root.update()
        root.after(150)
        root.update()
        shot(root, name)

    # Popup detail
    from src.ui.details_popup import show_details_popup
    popup = show_details_popup(root, append1, nama_barang="AYAM FILET")
    root.update()
    root.after(150)
    root.update()
    shot(root, "8-popup")
    popup.destroy()

    # Empty state (tab pivot sebelum data — buat app kecil terpisah)
    root2 = tk.Tk()
    root2.geometry("1440x900+0+0")
    real_stdout2, real_stderr2 = sys.stdout, sys.stderr
    app2 = StockMonitorApp(root2)
    sys.stdout, sys.stderr = real_stdout2, real_stderr2
    app2.notebook.select(app2.tab_pivot)
    root2.update()
    root2.after(150)
    root2.update()
    shot(root2, "9-empty-state")
    root2.destroy()

    root.destroy()
    print(f"Selesai — screenshot di {OUT}")


if __name__ == "__main__":
    main()
