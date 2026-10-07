"""
test_ui_redesign.py — Verifikasi UI v3.0 redesign dengan mock data.

Jalankan di bawah Xvfb:
    xvfb-run -a python test_ui_redesign.py

Memverifikasi:
1. App shell terbangun (toolbar, 7 tab, status bar) tanpa error
2. Semua view menerima mock data & merender baris ke Treeview
3. KPI cards ter-update
4. Filter + reset bekerja
5. Empty state ↔ content switching
6. Details popup terbangun
"""
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

from src.ui.app import StockMonitorApp
from src.ui.pivot_view import PivotTableView
from src.ui.deviasi_view import DeviasiView
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.rincian_po_view import RincianPoView
from src.ui.theme import apply_theme

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  ✓ {name}")
    else:
        FAIL.append(name)
        print(f"  ✗ {name} {detail}")


def make_mock_append1() -> pd.DataFrame:
    """Mock Append1 long-format: kolom minimal yang dipakai semua view."""
    rows = []
    barangs = [("AYAM FILET", "GR"), ("GULA PASIR", "GR"),
               ("KOPI BUBUK 100G", "PCS"), ("SUSU UHT 1L", "PCS")]
    restos = ["MLGPAR", "SBYKET"]
    jenis_list = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
                  "4.IN", "5.BARANG MASUK", "8.BARANG KELUAR", "9.OUT"]
    for barang, satuan in barangs:
        for resto in restos:
            for jenis in jenis_list:
                for tgl in range(1, 31):
                    val = 0.0
                    if jenis == "1.SO":
                        val = 10.0 + (tgl % 7) + (hash(barang) % 5)
                        if tgl == 25 and barang == "AYAM FILET" and resto == "MLGPAR":
                            val = 80.0  # anomali besar untuk CEK
                    elif jenis == "2.SALDO AKHIR":
                        val = 10.0
                    elif jenis == "4.IN" and tgl % 5 == 0:
                        val = 5.0
                    elif jenis == "9.OUT" and tgl % 3 == 0:
                        val = 3.0
                    elif jenis == "SALDO AWAL" and tgl == 1:
                        val = 10.0
                    rows.append({
                        "Nama Barang": barang, "JENIS": jenis,
                        "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": val,
                        "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                        "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                        "Nomor": f"RI-00{tgl}", "Nomor PO": f"PO-00{tgl}",
                        "#Tgl/Jam Pembuatan IT": None,
                    })
    return pd.DataFrame(rows)


def make_mock_rincian() -> pd.DataFrame:
    rows = []
    for i in range(1, 13):
        for j in range(1, 4):
            rows.append({
                "Nomor #": f"PO-2024-{i:03d}",
                "Tanggal": pd.Timestamp("2024-06-01") + pd.Timedelta(days=i),
                "Nama Barang": ["AYAM FILET", "GULA PASIR", "SUSU UHT 1L"][j - 1],
                "Keterangan PO": "Rutin",
                "Pemasok": ["PT Sumber", "CV Maju", "UD Jaya"][j - 1],
                "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-01 09:00") +
                                     pd.Timedelta(days=i),
                "Satuan": "GR",
                "Kuantitas": 10.0 * j,
                "Cabang PO": "MLGPAR" if i % 2 else "SBYKET",
                "Status Pesanan Pembelian": "Selesai",
            })
    return pd.DataFrame(rows)


def main():
    import os
    print("== 1. Build app shell ==")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    app = StockMonitorApp(root)
    # App mem-redirect stdout/stderr ke log queue — kembalikan untuk
    # output test (pipeline tidak dijalankan di test ini).
    sys.stdout, sys.stderr = real_stdout, real_stderr
    root.update_idletasks()
    check("App + toolbar + 7 tab terbangun", len(app.notebook.tabs()) == 7,
          f"tabs={len(app.notebook.tabs())}")
    check("Status bar ada", app.statusbar is not None)
    check("KPI proses awal: SIAP",
          app.kpi_status._value_var.get() == "SIAP")

    print("== 2. Empty state semua view ==")
    check("Pivot empty state terpasang (pack)",
          app.pivot_view.empty.winfo_manager() == "pack")
    check("Pivot content tersembunyi",
          app.pivot_view.content.winfo_manager() == "")
    check("Deviasi GR empty", app.deviasi_gr_view.data is None)
    check("Laporan empty", app.laporan_view.data is None)
    check("Rincian empty", app.rincian_view.data is None)

    print("== 3. Load mock data ==")
    append1 = make_mock_append1()
    rincian = make_mock_rincian()
    print(f"   mock append1: {len(append1)} rows, rincian: {len(rincian)} rows")

    app.pivot_view.load_data(append1)
    app.deviasi_gr_view.load_data(append1)
    app.deviasi_pcs_view.load_data(append1)
    app.laporan_view.load_data(append1)
    app.rincian_view.load_data(rincian)
    root.update_idletasks()

    # Pivot: parent = 4 barang → 4 parent + 4×10 metric children
    n_parent = len(app.pivot_view.tree.get_children(""))
    check("Pivot: 4 barang (parent)", n_parent == 4, f"got {n_parent}")
    first = app.pivot_view.tree.get_children("")[0]
    n_child = len(app.pivot_view.tree.get_children(first))
    check("Pivot: 10 metric per barang", n_child == 10, f"got {n_child}")
    check("Pivot KPI barang = 4",
          app.pivot_view.kpi_items._value_var.get() == "4")
    check("Pivot KPI tanggal = 30",
          app.pivot_view.kpi_days._value_var.get() == "30")

    # Deviasi GR: baris GR = 2 barang × 2 resto = 4
    n_gr = len(app.deviasi_gr_view.tree.get_children(""))
    check("Deviasi GR rows = 4", n_gr == 4, f"got {n_gr}")
    # Deviasi PCS: 2 barang × 2 resto = 4
    n_pcs = len(app.deviasi_pcs_view.tree.get_children(""))
    check("Deviasi PCS rows = 4", n_pcs == 4, f"got {n_pcs}")
    # Anomali CEK terdeteksi (AYAM FILET MLGPAR @ H=25 besar)
    cek_val = app.deviasi_gr_view.kpi_cek._value_var.get()
    print(f"   CEK count (GR): {cek_val}")

    print("== 4. Filter + reset ==")
    app.pivot_view.resto_var.set("MLGPAR")
    app.pivot_view._refresh_pivot()
    root.update_idletasks()
    n_parent = len(app.pivot_view.tree.get_children(""))
    check("Pivot filter RESTO=MLGPAR → 4 barang (barang sama, resto beda)",
          n_parent == 4, f"got {n_parent}")

    app.pivot_view.search_var.set("ayam")
    app.pivot_view._refresh_pivot()
    root.update_idletasks()
    n_parent = len(app.pivot_view.tree.get_children(""))
    check("Pivot search 'ayam' → 1 barang", n_parent == 1, f"got {n_parent}")

    app.pivot_view._reset_filter()
    root.update_idletasks()
    n_parent = len(app.pivot_view.tree.get_children(""))
    check("Pivot reset → 4 barang", n_parent == 4, f"got {n_parent}")

    # Laporan: toggle status via KPI
    n_all = len(app.laporan_view.tree.get_children(""))
    print(f"   laporan rows total: {n_all}")
    app.laporan_view._toggle_status("DEVIASI MURNI")
    root.update_idletasks()
    n_murni = len(app.laporan_view.tree.get_children(""))
    print(f"   laporan DEVIASI MURNI: {n_murni}")
    check("KPI toggle status memfilter (rows berkurang / tetap valid)",
          n_murni <= n_all)
    app.laporan_view._toggle_status("DEVIASI MURNI")  # toggle off
    root.update_idletasks()
    n_back = len(app.laporan_view.tree.get_children(""))
    check("Toggle off → kembali", n_back == n_all,
          f"{n_back} vs {n_all}")

    # Tanggal range
    app.laporan_view.tgl_start_var.set("1")
    app.laporan_view.tgl_end_var.set("10")
    app.laporan_view._refresh()
    root.update_idletasks()
    n_range = len(app.laporan_view.tree.get_children(""))
    check("Range tanggal 1-10 memfilter", n_range < n_all,
          f"{n_range} vs {n_all}")

    # Rincian
    n_po = len(app.rincian_view.tree.get_children("")) - 1  # minus grand total
    check("Rincian: 12 PO (parent) + grand total", n_po == 12,
          f"got {n_po}")
    check("Rincian KPI PO = 12",
          app.rincian_view.kpi_po._value_var.get() == "12")

    # Cabang filter
    app.rincian_view.cabang_var.set("MLGPAR")
    app.rincian_view._refresh()
    root.update_idletasks()
    n_po = len(app.rincian_view.tree.get_children("")) - 1
    check("Rincian filter cabang → 6 PO", n_po == 6, f"got {n_po}")
    app.rincian_view._reset_filter()

    print("== 5. Deviasi Tanggal H change ==")
    app.deviasi_gr_view.tanggal_h_var.set("10")
    app.deviasi_gr_view._on_tanggal_h_change()
    root.update_idletasks()
    check("Tanggal H=10 applied",
          app.deviasi_gr_view.tanggal_h == 10)
    heading = app.deviasi_gr_view.tree.heading("SO_H")["text"]
    check(f"Heading dinamis SO_H → 'SO_10'", heading == "SO_10",
          f"got '{heading}'")

    print("== 6. Details popup ==")
    from src.ui.details_popup import show_details_popup
    popup = show_details_popup(root, append1, nama_barang="AYAM FILET",
                               jenis="1.SO", tanggal=25)
    root.update_idletasks()
    n_rows = len(popup.tree.get_children(""))
    check("Popup rows > 0 (AYAM FILET/1.SO/25)",
          n_rows == 2, f"got {n_rows}")  # 2 resto
    popup.destroy()

    print("== 7. Sort kolom ==")
    app.deviasi_gr_view._sort_by("Deviasi")
    root.update_idletasks()
    first_vals = app.deviasi_gr_view.tree.item(
        app.deviasi_gr_view.tree.get_children("")[0])["values"]
    print(f"   baris pertama setelah sort Deviasi: {first_vals[15]}")
    check("Sort Deviasi jalan (tanpa exception)", True)

    print("== 8. Proses tab KPI ==")
    app.kpi_append.set_value("1,234", "test")
    check("KPI append set", app.kpi_append._value_var.get() == "1,234")

    # Cleanup
    root.destroy()

    print()
    print(f"HASIL: {len(PASS)} PASS, {len(FAIL)} FAIL")
    if FAIL:
        print("GAGAL:", FAIL)
        sys.exit(1)
    print("SEMUA TEST UI LULUS ✔")


if __name__ == "__main__":
    main()
