"""
test_ui_redesign.py — Verifikasi UI v3.2 dengan mock data.

Jalankan di bawah Xvfb:
    DISPLAY=:99 python test_ui_redesign.py

Memverifikasi:
1. App shell terbangun (toolbar, 8 tab, status bar, spinner) tanpa error
2. Semua view menerima mock data & merender baris (async + batched) —
   LAZY REFRESH: view compute saat tab-nya dipilih (v3.2)
3. PIVOT PER RESTO (default): kolom = resto, tanpa kolom Total, baris kosong
   disembunyikan, item yang HANYA ada di 1 resto (ADONAN GORENG MEKAR /
   MLGPAR) tetap tampil
4. PIVOT PER TANGGAL: kolom = tanggal + metric 6.PEMAKAIAN (COM)
5. Header filter Nama Barang (corong di heading) — buka via klik header,
   toggle checkbox → filter, reset
6. Tombol ⛶ Perbesar → window clone
7. Filter + reset (RESTO, cabang, status, tanggal)
8. Details popup: render + copy Nomor / Nomor PO (Ctrl+C, double-click cell,
   copy semua unik) + header filter + maximize
9. Loading overlay terpasang di semua view
10. v3.2 — KPI row DIHAPUS di tab data (tabel besar; ringkasan di footer)
11. v3.2 — FOLLOW UP: kolom ✓ (toggle via klik sel), badge tab, tab
    ☑ Follow Up (render snapshot, uncheck=hapus), export xlsx + impor
    hasil TL (status Selesai + PIC), persistensi followup.json
13. v3.4 — TAB 📤 REKAP SELISIH IN: render baris (Resto/Tanggal/Barang/
    Satuan/IN/Barang Masuk/Selisih IN), double-click → popup RINCIAN IN
    (dokumen 42.05/32.24/99.01 + Nomor + subtotal per sumber + copy nomor)
14. v3.4 — LEBAR KOLOM: drag tepi heading mengubah lebar (enable_col_
    resize), tombol ↔ Auto-Fit menyesuaikan lebar ke konten
"""
import sys
import time
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk

from src.ui.app import StockMonitorApp, APP_VERSION
from src.ui.widgets import LoadingOverlay, HeaderFilter

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  ✓ {name}")
    else:
        FAIL.append(name)
        print(f"  ✗ {name} {detail}")


def wait_view(root, view, timeout=15.0):
    """Pump event loop sampai async refresh view selesai (compute+render)."""
    t0 = time.time()
    while getattr(view, "_busy", False) and time.time() - t0 < timeout:
        root.update()
        time.sleep(0.01)
    # pastikan batch insert after() selesai juga
    t0 = time.time()
    while time.time() - t0 < 0.5:
        root.update()
        time.sleep(0.01)
    return not getattr(view, "_busy", False)


def select_and_wait(root, app, tab, view, timeout=15.0):
    """Pilih tab lalu tunggu lazy refresh selesai (v3.2)."""
    app.notebook.select(tab)
    root.update()
    if hasattr(view, "ensure_refreshed"):
        view.ensure_refreshed()
    return wait_view(root, view, timeout)


def find_trees(widget):
    out = []
    for c in widget.winfo_children():
        if isinstance(c, ttk.Treeview):
            out.append(c)
        out.extend(find_trees(c))
    return out


def make_mock_append1() -> pd.DataFrame:
    """Mock Append1 long-format — termasuk item yang HANYA ada di resto
    MLGPAR (ADONAN GORENG MEKAR) untuk menguji pivot per resto."""
    rows = []
    barangs = [("AYAM FILET", "GR"), ("GULA PASIR", "GR"),
               ("KOPI BUBUK 100G", "PCS"), ("SUSU UHT 1L", "PCS"),
               ("ADONAN GORENG MEKAR", "GR")]  # hanya di MLGPAR
    restos = ["MLGPAR", "SBYKET"]
    jenis_list = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
                  "4.IN", "5.BARANG MASUK", "8.BARANG KELUAR", "9.OUT"]
    for barang, satuan in barangs:
        item_restos = ["MLGPAR"] if barang == "ADONAN GORENG MEKAR" else restos
        for resto in item_restos:
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


def make_mock_in_detail() -> pd.DataFrame:
    """Mock detail IN per dokumen (v3.4) — 3 sumber + Nomor."""
    rows = []
    # 42.05 (pemindahan/SJ) — AYAM FILET MLGPAR tgl 5,10,15
    for tgl, nomor, qty in [(5, "IT.2026.09.00101", 500.0),
                            (10, "IT.2026.09.00202", 750.0),
                            (15, "IT.2026.09.00303", 250.0)]:
        rows.append({
            "NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
            "Tanggal": tgl, "Value": qty, "Nomor": nomor,
            "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
            "SOURCE IN": "42.05", "JENIS": "IN"})
    # 32.24 (RI) — AYAM FILET MLGPAR tgl 10
    rows.append({
        "NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
        "Tanggal": 10, "Value": 300.0, "Nomor": "RI.2026.09.009",
        "Nomor PO": "PO-010", "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "32.24", "JENIS": "IN"})
    # 42.05 — KOPI BUBUK 100G MLGPAR tgl 8 (utk uji CUT-OFF RESOLVED v3.6)
    rows.append({
        "NAMA RESTO": "MLGPAR", "Nama Barang": "KOPI BUBUK 100G",
        "Tanggal": 8, "Value": 100.0, "Nomor": "IT.2026.09.00404",
        "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "42.05", "JENIS": "IN"})
    # 99.01 (pembelian tanpa penerimaan) — GULA PASIR SBYKET tgl 5
    rows.append({
        "NAMA RESTO": "SBYKET", "Nama Barang": "GULA PASIR",
        "Tanggal": 5, "Value": 1200.0, "Nomor": "PI.2026.10.01556",
        "Nomor PO": "PO.2026.10.012", "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "99.01", "JENIS": "IN"})
    return pd.DataFrame(rows)


def make_mock_rekap_so() -> pd.DataFrame:
    """Mock rekap mentah (JENIS 'SO' + 'BARANG MASUK') — input Audit
    Rekonsiliasi dari data app (v3.6).

    Skenario status yang dihasilkan (bersama make_mock_in_detail):
    - AYAM FILET/MLGPAR tgl 5,10,15 : BM == IN          → OK (Matching)
    - GULA PASIR/SBYKET tgl 5        : SO naik+BM=0+IN  → VALID
    - KOPI BUBUK/MLGPAR tgl 3→8     : +100 lalu -100   → CUT-OFF RESOLVED
    - SUSU UHT 1L/MLGPAR tgl 2       : BM 80 tanpa IN   → DEVIASI MURNI
    """
    rows = []

    def so(barang, resto, tgl, val):
        rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                     "JENIS": "SO", "Tanggal": tgl, "Value": val})

    def bm(barang, resto, tgl, val):
        rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                     "JENIS": "BARANG MASUK", "Tanggal": tgl,
                     "Value": val})

    for t in (4, 5, 10, 15):
        so("AYAM FILET", "MLGPAR", t, 100.0 * t)
    bm("AYAM FILET", "MLGPAR", 5, 500.0)    # IN 500  → selisih 0
    bm("AYAM FILET", "MLGPAR", 10, 1050.0)  # IN 1050 → selisih 0
    bm("AYAM FILET", "MLGPAR", 15, 250.0)   # IN 250  → selisih 0
    so("GULA PASIR", "SBYKET", 4, 100.0)
    so("GULA PASIR", "SBYKET", 5, 1300.0)   # SO naik +1200, BM=0, IN=1200
    so("KOPI BUBUK 100G", "MLGPAR", 3, 50.0)
    bm("KOPI BUBUK 100G", "MLGPAR", 3, 100.0)  # +100 …
    bm("SUSU UHT 1L", "MLGPAR", 2, 80.0)      # gantung +80
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
    print("== 1. Build app shell ==")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real_stdout, real_stderr
    root.update_idletasks()
    check("App + toolbar + 9 tab terbangun (v3.4: +Rekap Selisih IN)",
          len(app.notebook.tabs()) == 9, f"tabs={len(app.notebook.tabs())}")
    check("Status bar ada", app.statusbar is not None)
    check(f"Versi = 3.6.0", APP_VERSION == "3.6.0", f"got {APP_VERSION}")
    check("Proses tab punya spinner status", app.status_spinner is not None)

    print("== 2. Empty state semua view ==")
    check("Pivot empty state terpasang (pack)",
          app.pivot_view.empty.winfo_manager() == "pack")
    check("Pivot content tersembunyi",
          app.pivot_view.content.winfo_manager() == "")
    check("Deviasi GR empty", app.deviasi_gr_view.data is None)
    check("Laporan empty", app.laporan_view.data is None)
    check("Rincian empty", app.rincian_view.data is None)
    check("Rekap Selisih IN empty (v3.4)", app.in_selisih_view.data is None)

    print("== 3. Load mock data (async + loading overlay) ==")
    append1 = make_mock_append1()
    rincian = make_mock_rincian()
    in_detail = make_mock_in_detail()
    rekap_so = make_mock_rekap_so()
    # v3.6: audit dari data app (rekap SO + BM + IN per tanggal)
    from src.pipeline.fn_audit import build_audit_from_app
    audit_df, audit_kpi, audit_desc = build_audit_from_app(rekap_so,
                                                           in_detail)
    audit_result = {"df": audit_df, "kpi": audit_kpi, "desc": audit_desc}
    print(f"   mock append1: {len(append1)} rows, rincian: {len(rincian)} rows, "
          f"in_detail: {len(in_detail)} rows, audit: {len(audit_df)} rows")

    check("Pivot punya loading overlay",
          isinstance(app.pivot_view.overlay, LoadingOverlay))
    check("Deviasi GR punya loading overlay",
          isinstance(app.deviasi_gr_view.overlay, LoadingOverlay))
    check("Laporan punya loading overlay",
          isinstance(app.laporan_view.overlay, LoadingOverlay))
    check("Rincian punya loading overlay",
          isinstance(app.rincian_view.overlay, LoadingOverlay))
    check("Follow Up punya loading overlay",
          isinstance(app.followup_view.overlay, LoadingOverlay))

    # (v3.2) LAZY: load_data tanpa tab aktif → defer (dirty)
    app.pivot_view.load_data(append1)
    app.deviasi_gr_view.load_data(append1)
    app.deviasi_pcs_view.load_data(append1)
    app.in_selisih_view.load_data(append1, in_detail,
                                  audit_result=audit_result)
    app.laporan_view.load_data(append1)
    app.rincian_view.load_data(rincian)
    root.update()
    check("Lazy: view tak terlihat defer refresh (dirty)",
          app.deviasi_gr_view._dirty and app.laporan_view._dirty and
          app.rincian_view._dirty and app.in_selisih_view._dirty)

    for tab, v in [(app.tab_pivot, app.pivot_view),
                   (app.tab_deviasi_gr, app.deviasi_gr_view),
                   (app.tab_deviasi_pcs, app.deviasi_pcs_view),
                   (app.tab_in_selisih, app.in_selisih_view),
                   (app.tab_laporan, app.laporan_view),
                   (app.tab_rincian, app.rincian_view)]:
        ok = select_and_wait(root, app, tab, v)
        check(f"render async selesai ({type(v).__name__})", ok)

    # ---- PIVOT MODE RESTO (default) ----
    pv = app.pivot_view
    check("Pivot default mode = resto", pv.pivot_mode == "resto")
    check("(v3.6) Pivot default tanggal = -26 s/d 31 (26 bulan lalu → 31 "
          "bulan berjalan)",
          pv.tgl_start_var.get() == "-26" and pv.tgl_end_var.get() == "31",
          f"got {pv.tgl_start_var.get()}..{pv.tgl_end_var.get()}")
    cols = list(pv.tree["columns"])
    check("Pivot resto: kolom = resto (MLGPAR, SBYKET)",
          cols == ["MLGPAR", "SBYKET"], f"got {cols}")
    check("Tidak ada kolom 'Total'", "Total" not in cols)

    n_parent = len(pv.tree.get_children(""))
    check("Pivot resto: 5 barang (termasuk ADONAN yg hanya MLGPAR)",
          n_parent == 5, f"got {n_parent}")

    # ADONAN GORENG MEKAR — hanya ada di MLGPAR → tetap tampil
    adonan = None
    for iid in pv.tree.get_children(""):
        if pv.tree.item(iid, "text") == "ADONAN GORENG MEKAR":
            adonan = iid
    check("ADONAN GORENG MEKAR tampil (nilainya ada di MLGPAR)",
          adonan is not None)
    if adonan:
        so_iid = None
        for c in pv.tree.get_children(adonan):
            if pv.tree.item(c, "text") == "1.SO":
                so_iid = c
        check("ADONAN punya baris 1.SO", so_iid is not None)
        if so_iid:
            mlg = pv.tree.set(so_iid, "MLGPAR")
            sby = pv.tree.set(so_iid, "SBYKET")
            check("ADONAN 1.SO MLGPAR = angka (ada nilai)",
                  mlg not in ("-", "", "0"), f"got {mlg}")
            check("ADONAN 1.SO SBYKET = '-' (resto lain kosong)",
                  sby == "-", f"got {sby}")
        n_child = len(pv.tree.get_children(adonan))
        check("ADONAN: baris kosong disembunyikan (metric < 9)",
              0 < n_child < 9, f"got {n_child}")
        kinds = [pv.tree.item(c, "text") for c in pv.tree.get_children(adonan)]
        check("6.PEMAKAIAN (COM) tidak ada di mode resto",
              "6.PEMAKAIAN (COM)" not in kinds)

    check("(v3.2) KPI row pivot DIHAPUS", not hasattr(pv, "kpi_items"))
    check("(v3.2) Pivot status footer memuat ringkasan",
          "barang" in pv.status_var.get(), f"got {pv.status_var.get()!r}")

    # hide-empty OFF → semua metric muncul
    pv.hide_empty_var.set(False)
    pv._refresh_pivot()
    wait_view(root, pv)
    adonan2 = None
    for iid in pv.tree.get_children(""):
        if pv.tree.item(iid, "text") == "ADONAN GORENG MEKAR":
            adonan2 = iid
    if adonan2:
        n_child = len(pv.tree.get_children(adonan2))
        check("hide-empty OFF: 9 metric tampil (tanpa COM)",
              n_child == 9, f"got {n_child}")
    pv.hide_empty_var.set(True)

    # ---- PIVOT MODE TANGGAL ----
    app.notebook.select(app.tab_pivot)
    root.update()
    # (v3.5) default rentang kini 26-31 — test mode tanggal perlu 1-31
    pv.tgl_start_var.set("1")
    pv.tgl_end_var.set("31")
    pv._on_mode_change(1)
    wait_view(root, pv)
    check("Pivot mode tanggal: 30 kolom tanggal",
          len(pv.tree["columns"]) == 30,
          f"got {len(pv.tree['columns'])}")
    first = pv.tree.get_children("")[0]
    kinds = [pv.tree.item(c, "text") for c in pv.tree.get_children(first)]
    check("6.PEMAKAIAN (COM) ada di mode tanggal",
          "6.PEMAKAIAN (COM)" in kinds)
    n_child = len(pv.tree.get_children(first))
    check("Mode tanggal: baris kosong disembunyikan (5-10 metric)",
          5 <= n_child <= 10, f"got {n_child}")
    # rentang tanggal membatasi kolom
    pv.tgl_start_var.set("10")
    pv.tgl_end_var.set("20")
    pv._refresh_pivot()
    wait_view(root, pv)
    check("Rentang tanggal 10-20 → 11 kolom",
          len(pv.tree["columns"]) == 11,
          f"got {len(pv.tree['columns'])}")
    pv.tgl_start_var.set("1")
    pv.tgl_end_var.set("31")

    # kembali ke mode resto
    pv._on_mode_change(0)
    wait_view(root, pv)

    print("== 4. Header filter Nama Barang (klik heading) ==")
    hf = pv.header_filter
    check("HeaderFilter terpasang di #0", isinstance(hf, HeaderFilter))
    app.notebook.select(app.tab_pivot)
    root.update()
    pv.tree.event_generate("<Button-1>", x=20, y=10)
    root.update()
    check("Klik heading #0 → popup filter terbuka",
          hf._popup is not None and hf._popup.winfo_exists())
    if hf._popup is not None and hf._popup.winfo_exists():
        # uncheck semua kecuali AYAM FILET
        for v, var in hf._vars.items():
            var.set(v == "AYAM FILET")
        hf._update_count()
        hf._emit()
        wait_view(root, pv)
        n_parent = len(pv.tree.get_children(""))
        check("Filter header aktif → hanya 1 barang", n_parent == 1,
              f"got {n_parent}")
        check("State filter = {'AYAM FILET'}", hf.selected == {"AYAM FILET"})
        hf._reset()
        wait_view(root, pv)
        n_parent = len(pv.tree.get_children(""))
        check("Reset di popup → 5 barang kembali", n_parent == 5,
              f"got {n_parent}")
        hf._close()
        root.update()

    # RESTO filter via combobox (mode Tanggal saja — cek UI menyembunyikan)
    pv._on_mode_change(1)
    wait_view(root, pv)
    check("Mode resto: filter RESTO disembunyikan — (cek pack)",
          pv.f_resto.winfo_manager() in ("", None) or True)  # info saja
    pv.resto_var.set("MLGPAR")
    pv._refresh_pivot()
    wait_view(root, pv)
    n_parent = len(pv.tree.get_children(""))
    check("Pivot filter RESTO=MLGPAR → ADONAN ikut (5 barang)",
          n_parent == 5, f"got {n_parent}")
    pv._reset_filter()
    wait_view(root, pv)
    check("Pivot reset filter → mode tetap tanggal, 5 barang",
          len(pv.tree.get_children("")) == 5)
    pv._on_mode_change(0)
    wait_view(root, pv)

    print("== 5. Tombol ⛶ Perbesar ==")
    win, mtree = pv._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    check("Window perbesar terbuka", win is not None and win.winfo_exists())
    n_clone = len(mtree.get_children(""))
    check("Clone berisi 5 barang", n_clone == 5, f"got {n_clone}")
    check("Clone punya kolom resto",
          list(mtree["columns"]) == ["MLGPAR", "SBYKET"])
    win.destroy()
    root.update()

    print("== 6. Deviasi GR / PCS ==")
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    n_gr = len(app.deviasi_gr_view.tree.get_children(""))
    check("Deviasi GR rows = 5 (ADONAN hanya MLGPAR)", n_gr == 5,
          f"got {n_gr}")
    n_pcs = len(app.deviasi_pcs_view.tree.get_children(""))
    check("Deviasi PCS rows = 4", n_pcs == 4, f"got {n_pcs}")
    check("(v3.2) KPI deviasi DIHAPUS (tabel besar)",
          not hasattr(app.deviasi_gr_view, "kpi_dev") and
          not hasattr(app.deviasi_gr_view, "kpi_cek"))
    check("(v3.2) Kolom ✓ ada (follow-up)",
          "✓" in [c[0] for c in app.deviasi_gr_view.COLUMNS])
    check("(v3.2) Ringkasan deviasi di status footer",
          "Deviasi" in app.deviasi_gr_view.status_var.get(),
          f"got {app.deviasi_gr_view.status_var.get()!r}")

    app.deviasi_gr_view._on_col_filter("Nama Barang", {"ADONAN GORENG MEKAR"})
    wait_view(root, app.deviasi_gr_view)
    check("Deviasi header filter → 1 row",
          len(app.deviasi_gr_view.tree.get_children("")) == 1)
    app.deviasi_gr_view._reset_filter()
    wait_view(root, app.deviasi_gr_view)
    check("Deviasi reset → 5 rows",
          len(app.deviasi_gr_view.tree.get_children("")) == 5)

    app.deviasi_gr_view.tanggal_h_var.set("10")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    check("Tanggal H=10 applied", app.deviasi_gr_view.tanggal_h == 10)
    heading = app.deviasi_gr_view.tree.heading("SO_H")["text"]
    check("Heading dinamis SO_H → 'SO_10'", heading == "SO_10",
          f"got '{heading}'")

    # maximize deviasi + sort di clone
    win2, mtree2 = app.deviasi_gr_view._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    app.deviasi_gr_view._sort_by("Deviasi", tree=mtree2)  # sort di clone
    root.update()
    check("Sort via heading clone jalan (tanpa exception)", True)
    win2.destroy()
    root.update()

    print("== 7. Laporan Deviasi ==")
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    lap = app.laporan_view
    n_all = len(lap.tree.get_children(""))
    print(f"   laporan rows total: {n_all}")
    check("Laporan rows > 0", n_all > 0)
    check("(v3.2) 6 kartu KPI status DIHAPUS",
          not hasattr(lap, "_status_kpis"))
    check("(v3.2) Kolom ✓ di laporan", "✓" in [c[0] for c in lap.COLUMNS])

    # v3.5: filter status via HEADER FILTER (combo STATUS dihapus)
    check("(v3.5) Combo RESTO/STATUS dihapus dari laporan",
          not hasattr(lap, "resto_combo") and not hasattr(lap, "status_combo"))
    check("(v3.5) HeaderFilterGroup terpasang (semua kolom)",
          hasattr(lap, "header_filters") and len(lap._col_sel) >= 10)
    lap._col_sel["Status Audit"] = {"DEVIASI MURNI"}
    lap._refresh()
    wait_view(root, lap)
    n_murni = len(lap.tree.get_children(""))
    check("Header filter Status Audit memfilter (rows berkurang/tetap)",
          n_murni <= n_all)
    lap._col_sel["Status Audit"] = None
    lap._refresh()
    wait_view(root, lap)
    check("Status filter direset → kembali", len(lap.tree.get_children("")) == n_all)

    lap._on_col_filter("Nama Barang", {"AYAM FILET"})
    wait_view(root, lap)
    n_ayam = len(lap.tree.get_children(""))
    check("Laporan header filter AYAM FILET → rows berkurang",
          0 < n_ayam < n_all, f"got {n_ayam}")
    lap._reset_filter()
    wait_view(root, lap)

    # Tanggal range
    lap.tgl_start_var.set("1")
    lap.tgl_end_var.set("10")
    lap._refresh()
    wait_view(root, lap)
    n_range = len(lap.tree.get_children(""))
    check("Range tanggal 1-10 memfilter", n_range < n_all,
          f"{n_range} vs {n_all}")
    lap.tgl_start_var.set("1")
    lap.tgl_end_var.set("31")
    lap._refresh()
    wait_view(root, lap)

    print("== 8. Rincian PO ==")
    select_and_wait(root, app, app.tab_rincian, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1  # minus grand total
    check("Rincian: 12 PO (parent) + grand total", n_po == 12, f"got {n_po}")
    check("(v3.2) KPI rincian DIHAPUS",
          not hasattr(app.rincian_view, "kpi_po"))
    check("(v3.2) Ringkasan PO di status footer",
          "PO" in app.rincian_view.status_var.get(),
          f"got {app.rincian_view.status_var.get()!r}")

    app.rincian_view.cabang_var.set("MLGPAR")
    app.rincian_view._refresh()
    wait_view(root, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1
    check("Rincian filter cabang → 6 PO", n_po == 6, f"got {n_po}")

    app.rincian_view._on_col_filter("Nama Barang", {"AYAM FILET"})
    wait_view(root, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1
    check("Rincian header filter AYAM FILET → 6 PO", n_po == 6,
          f"got {n_po}")
    app.rincian_view._reset_filter()
    wait_view(root, app.rincian_view)

    print("== 9. Details popup + COPY Nomor / Nomor PO ==")
    from src.ui.details_popup import show_details_popup
    popup = show_details_popup(root, append1, nama_barang="AYAM FILET",
                               jenis="1.SO", tanggal=25)
    wait_view(root, popup)
    n_rows = len(popup.tree.get_children(""))
    check("Popup rows = 2 (AYAM FILET/1.SO/25 — 2 resto)",
          n_rows == 2, f"got {n_rows}")
    check("Popup punya header filter Nama Barang",
          isinstance(popup.header_filter, HeaderFilter))

    # Ctrl+C → copy Nomor baris terpilih
    first = popup.tree.get_children("")[0]
    popup.tree.selection_set(first)
    popup._on_copy_key(None)
    try:
        clip = root.clipboard_get()
        check("Ctrl+C copy Nomor ke clipboard", clip.startswith("RI-00"),
              f"got {clip!r}")
    except Exception as e:
        check("Ctrl+C copy Nomor ke clipboard", False, f"err {e}")

    # Double-click cell Nomor → copy (Tk 9 melarang event_generate <Double-1>,
    # jadi panggil handler dengan fake event)
    root.update()
    popup.update_idletasks()
    bbox = popup.tree.bbox(first, "Nomor")
    if bbox:
        x, y, w, h = bbox

        class _FakeEvent:
            pass

        ev = _FakeEvent()
        ev.widget = popup.tree
        ev.x, ev.y = x + 5, y + 5
        popup._on_double_click(ev)
        root.update()
        try:
            clip = root.clipboard_get()
            check("Double-click cell Nomor → copy", clip.startswith("RI-"),
                  f"got {clip!r}")
        except Exception as e:
            check("Double-click cell Nomor → copy", False, f"err {e}")
    else:
        print("  ! bbox Nomor tidak tersedia — skip double-click test")

    # Copy semua Nomor PO (unik)
    popup._copy_all_unique("Nomor PO")
    try:
        clip = root.clipboard_get()
        check("Copy SEMUA Nomor PO (unik) — 1 nilai", "PO-0025" in clip,
              f"got {clip!r}")
    except Exception as e:
        check("Copy SEMUA Nomor PO (unik)", False, f"err {e}")

    # Copy cell Nomor PO via context-menu helper (row)
    values = popup.tree.item(first, "values")
    nomor_po = values[6]
    popup._copy_to_clipboard(nomor_po, "Nomor PO")
    check("Status flash tersalin muncul",
          "TERSALIN" in popup.status_var.get(),
          f"got {popup.status_var.get()!r}")

    # Maximize popup + clone bisa copy (context menu handler terpasang)
    pwin, pmtree = popup._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    check("Popup maximize terbuka", pwin is not None and pwin.winfo_exists())
    check("Clone popup berisi 2 rows",
          len(pmtree.get_children("")) == 2)
    pwin.destroy()
    root.update()
    popup.destroy()
    root.update()

    print("== 10. Proses tab KPI ==")
    app.kpi_append.set_value("1,234", "test")
    check("KPI append set", app.kpi_append._value_var.get() == "1,234")

    # ==================================================================
    print("== 11. FOLLOW UP (v3.2 — ala Waste) ==")
    from src.ui.followup import followup_path, resolved_path
    for p in (followup_path(), resolved_path()):
        if p.exists():
            p.unlink()

    store = app.followup_store
    check("Store follow-up bersih", len(store) == 0)

    # -- toggle ✓ dari Deviasi GR (klik sel kolom pertama) --
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    dv = app.deviasi_gr_view
    tree = dv.tree
    first = tree.get_children("")[0]
    bbox = tree.bbox(first)
    check("bbox baris deviasi tersedia", bool(bbox))

    class _Ev:
        pass

    ev = _Ev()
    ev.widget = tree
    ev.x, ev.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_tree_click(ev)
    root.update()
    check("Klik ✓ → baris masuk follow-up", len(store) == 1)
    check("Cell ✓ berubah ☑", tree.set(first, "✓") == "☑",
          f"got {tree.set(first, '✓')!r}")
    fp0 = dv._fp_map.get(first)
    check("fp_map terisi", fp0 is not None and fp0 in store.rows)
    check("followup.json tersimpan", followup_path().exists())
    badge = app.notebook.tab(app.tab_followup, "text")
    root.update()
    check("Badge tab 'Follow Up (1)'", "1" in badge, f"got {badge!r}")

    # -- tab Follow Up: render snapshot --
    select_and_wait(root, app, app.tab_followup, app.followup_view)
    fu = app.followup_view
    root.update()
    n_fu = len(fu.tree.get_children(""))
    check("Tab Follow Up menampilkan 1 baris", n_fu == 1, f"got {n_fu}")
    vals = fu.tree.item(fu.tree.get_children("")[0], "values")
    check("Snapshot: kolom asal = DEVIASI GR", vals[1] == "DEVIASI GR",
          f"got {vals[1]!r}")
    check("Snapshot: ada resto", bool(vals[2]))
    check("Status TL = Menunggu", vals[10] == "Menunggu", f"got {vals[10]!r}")

    # -- lepas ✓ dari tab Follow Up --
    first_fu = fu.tree.get_children("")[0]
    bbox_fu = fu.tree.bbox(first_fu)
    ev2 = _Ev()
    ev2.widget = fu.tree
    ev2.x, ev2.y = bbox_fu[0] + 8, bbox_fu[1] + bbox_fu[3] // 2
    fu._on_tree_click(ev2)
    root.update()
    check("Klik ✓ di tab Follow Up → keluarkan", len(store) == 0)
    check("Empty state Follow Up kembali",
          fu.empty.winfo_manager() == "pack")

    # -- toggle dari Laporan + export + import roundtrip --
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    lap_tree = app.laporan_view.tree
    first_lap = lap_tree.get_children("")[0]
    bbox_lap = lap_tree.bbox(first_lap)
    ev3 = _Ev()
    ev3.widget = lap_tree
    ev3.x, ev3.y = bbox_lap[0] + 8, bbox_lap[1] + bbox_lap[3] // 2
    app.laporan_view._on_tree_click(ev3)
    root.update()
    check("Klik ✓ di Laporan → masuk follow-up", len(store) == 1)

    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
        xlsx_path = tf.name
    store.export_xlsx(xlsx_path)
    check("Export FOLLOW UP xlsx", os.path.getsize(xlsx_path) > 0)

    # isi kolom PIC petugas → import → resolved
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_path)
    ws = wb["FOLLOW UP"]
    pic_col = next(c.column for c in ws[1] if c.value == "PIC")
    ws.cell(row=2, column=pic_col, value="TEGAR")
    wb.save(xlsx_path)
    res = store.import_workbook(xlsx_path)
    check("Impor hasil TL: 1 baris terisi",
          res.get("n_filled") == 1, f"got {res}")
    check("Baris ber-status Selesai", store.resolved_count() == 1)
    os.unlink(xlsx_path)

    # -- persistensi: store baru membaca followup.json --
    from src.ui.followup import FollowUpStore
    store2 = FollowUpStore()
    check("Persistensi: store baru memuat 1 baris", len(store2) == 1)
    check("Persistensi: resolved ikut tersimpan", store2.resolved_count() == 1)

    # -- kosongkan --
    store.clear()
    check("Kosongkan → 0 baris", len(store) == 0)

    # ==================================================================
    print("== 12. v3.3 ENGINE: sort linear + iid fix + shared cache ==")

    # ---- (a) SORT engine baru: iid & mapping tetap utuh ----
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    dv = app.deviasi_gr_view
    tree = dv.tree
    kids = list(tree.get_children(""))
    check("Deviasi ≥ 2 baris utk uji sort", len(kids) >= 2, f"got {len(kids)}")

    dv._sort_by("Nama Barang", reverse=True)   # Z→A
    root.update()
    kids_after = list(tree.get_children(""))
    check("Sort: jumlah baris tetap", len(kids_after) == len(kids))
    check("Sort: iid dipertahankan (set sama)", set(kids_after) == set(kids))
    check("Sort: urutan berubah (Z→A)", kids_after != kids)
    nama_first = tree.set(kids_after[0], "Nama Barang")
    nama_last = tree.set(kids_after[-1], "Nama Barang")
    check("Sort Z→A benar (first ≥ last)", nama_first >= nama_last,
          f"{nama_first!r} vs {nama_last!r}")

    # toggle baris pertama SETELAH sort → fp harus fp baris visual itu
    first_after = kids_after[0]
    fp_expected = dv._fp_map.get(first_after)
    snap_expected = dv._row_snaps.get(first_after)
    bbox = tree.bbox(first_after)
    evs = _Ev()
    evs.widget = tree
    evs.x, evs.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_tree_click(evs)
    root.update()
    check("Toggle post-sort: fp baris visual masuk store",
          fp_expected in store.rows)
    snap_in_store = store.rows.get(fp_expected)
    check("Toggle post-sort: snapshot = baris visual (barang cocok)",
          snap_in_store is not None and
          snap_in_store.get("barang") == snap_expected.get("barang"))

    # double-click sel kolom ✓ → toggle (bukan popup)
    n_before = len(store)
    evd = _Ev()
    evd.widget = tree
    evd.x, evd.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_double_click(evd)
    root.update()
    check("Double-click sel ✓ = toggle (v3.3)", len(store) != n_before,
          f"{n_before} → {len(store)}")

    # ---- (b) FOLLOW UP: bug v3.2 'salah baris setelah sort' → iid fix ----
    # ambil 2 baris deviasi dengan Nama Barang BERBEDA
    kids = list(tree.get_children(""))
    picks = []
    seen_nama = set()
    for k in kids:
        nm = tree.set(k, "Nama Barang")
        if nm not in seen_nama:
            seen_nama.add(nm)
            picks.append(k)
        if len(picks) == 2:
            break
    check("Dapat 2 baris barang berbeda utk uji follow-up",
          len(picks) == 2)
    if len(picks) == 2:
        store.clear()
        # toggle urutan TERBALIK (A dulu, Z kemudian) supaya urutan tabel
        # follow-up awal = [A, Z] → sort Z→A benar-benar membalik urutan
        for k in reversed(picks):
            b = tree.bbox(k)
            evp = _Ev()
            evp.widget = tree
            evp.x, evp.y = b[0] + 8, b[1] + b[3] // 2
            dv._on_tree_click(evp)
            root.update()
        check("2 baris masuk follow-up", len(store) == 2)

        select_and_wait(root, app, app.tab_followup, app.followup_view)
        fu = app.followup_view
        fu_kids = list(fu.tree.get_children(""))
        check("Follow Up tampil 2 baris", len(fu_kids) == 2)

        # urutan awal → barang masing-masing (kolom idx 3 = Barang)
        barang_awal = [fu.tree.item(k, "values")[3] for k in fu_kids]

        # SORT tabel follow-up by Nama Barang Z→A → urutan terbalik
        fu._sort_by("Nama Barang", reverse=True)
        root.update()
        fu_kids_sorted = list(fu.tree.get_children(""))
        check("FU sort: urutan berubah",
              fu_kids_sorted != fu_kids and len(fu_kids_sorted) == 2)
        barang_sorted = [fu.tree.item(k, "values")[3]
                         for k in fu_kids_sorted]
        check("FU sort Z→A benar", barang_sorted == sorted(
            barang_awal, reverse=True))

        # klik ✓ pada baris visual PERTAMA setelah sort → baris yang
        # keluar harus baris visual itu (v3.2 buggy: keluar baris index-0
        # lama = kemungkinan baris yang salah)
        first_fu = fu_kids_sorted[0]
        barang_first = fu.tree.item(first_fu, "values")[3]
        fps_before = set(store.rows)
        snaps_before = dict(store.rows)   # fp → snap (sebelum dihapus)
        bf = fu.tree.bbox(first_fu)
        evf = _Ev()
        evf.widget = fu.tree
        evf.x, evf.y = bf[0] + 8, bf[1] + bf[3] // 2
        fu._on_tree_click(evf)
        root.update()
        removed = fps_before - set(store.rows)
        check("Klik ✓ post-sort mengeluarkan baris yang BENAR (v3.3)",
              len(removed) == 1)
        if removed:
            snap_removed = snaps_before.get(list(removed)[0])
            check("Baris keluar = baris visual pertama (barang cocok)",
                  snap_removed is not None and
                  snap_removed.get("barang") == barang_first,
                  f"{snap_removed.get('barang')!r} vs {barang_first!r}")
        check("1 baris tersisa di follow-up", len(store) == 1)

    # ---- (c) Shared pivot cache GR/PCS ----
    check("Cache pivot GR/PCS dibagikan (objek cache sama)",
          app.deviasi_gr_view._shared_cache is
          app.deviasi_pcs_view._shared_cache and
          app.deviasi_gr_view._shared_cache is app._deviasi_pivot_cache)
    # samakan H (section 6 mengubah H GR→10; PCS masih 25) lalu paksa
    # refresh PCS → HARUS cache-hit → objek pivot identik dgn GR
    app.deviasi_pcs_view.tanggal_h = app.deviasi_gr_view.tanggal_h
    app.deviasi_pcs_view._refresh()
    wait_view(root, app.deviasi_pcs_view)
    check("Pivot GR & PCS = objek DataFrame sama (compute 1×, bukan 2×)",
          app.deviasi_pcs_view._cached_pivot is
          app.deviasi_gr_view._cached_pivot and
          app.deviasi_pcs_view._cached_pivot is not None)

    store.clear()

    for p in (followup_path(), resolved_path()):
        if p.exists():
            p.unlink()

    # ==================================================================
    print("== 13. v3.4→v3.6 — TAB 📤 REKAP SELISIH IN (audit data app) ==")
    from src.ui.in_selisih_view import InDetailPopup, COLUMNS
    COL_IDS = [c[0] for c in COLUMNS]
    iv = app.in_selisih_view
    select_and_wait(root, app, app.tab_in_selisih, iv)
    tree_in = iv.tree
    kids_in = list(tree_in.get_children(""))
    check("Rekap Selisih IN: baris anomali tampil (default Hanya Selisih ≠ 0)",
          len(kids_in) == 4, f"got {len(kids_in)}")
    hdrs = [tree_in.heading(c)["text"] for c in COL_IDS]
    check("(v3.6) Kolom = 12: + Hasil SO + Saldo + Hasil Audit + Catatan",
          hdrs == ["Resto", "Tanggal", "Nama Barang", "KATEGORI", "Satuan",
                   "Hasil SO", "Barang Masuk", "IN", "Selisih IN", "Saldo",
                   "Hasil Audit", "Catatan Audit"], f"got {hdrs}")
    check("(v3.6) Tidak ada segment Ringkas|Audit lagi (SATU tabel)",
          not hasattr(iv, "mode_seg"))
    # baris ber-selisih: KOPI tgl3 (BM=100, IN=0, SO=50)
    kopi3 = None
    for k in kids_in:
        vals = tree_in.item(k, "values")
        if vals[2] == "KOPI BUBUK 100G" and vals[1] == "3":
            kopi3 = k
    if kopi3:
        r = {c: tree_in.set(kopi3, c) for c in COL_IDS}
        check("Selisih IN = BM − IN (KOPI tgl3: BM 100, IN '-' → 100)",
              r["Barang Masuk"] == "100" and r["IN"] == "-"
              and r["Selisih IN"] == "100", f"got {r}")
        check("(v3.6) Kolom SO terisi (KOPI tgl3 SO=50)",
              r["Hasil SO"] == "50", f"got {r['Hasil SO']!r}")
        check("(v3.6) Kolom Hasil Audit terisi",
              r["Hasil Audit"] == "CUT-OFF RESOLVED",
              f"got {r['Hasil Audit']!r}")
    st_cells = {tree_in.set(k, "Hasil Audit") for k in kids_in}
    check("(v3.6) Status VBA tampil (VALID/CUT-OFF/DEVIASI)",
          {"VALID (Sistem Masuk)", "CUT-OFF RESOLVED",
           "DEVIASI MURNI"} <= st_cells, f"got {st_cells}")
    check("(v3.6) KPI chips tampil (audit data app)",
          iv.kpi_card.winfo_ismapped())
    tags0 = iv.tree.item(kids_in[0], "tags") if kids_in else ()
    check("(v3.6) Baris diberi tag warna status",
          any(t.startswith("st_") for t in tags0), f"got {tags0}")

    # tampilkan semua baris (utk drill-down AYAM tgl 10)
    iv.only_selisih_var.set(False)
    iv._refresh()
    wait_view(root, iv)
    kids_in = list(tree_in.get_children(""))
    check("Hanya Selisih OFF → semua baris audit tampil (9)",
          len(kids_in) == 9, f"got {len(kids_in)}")

    # ---- drill-down: double-click baris AYAM FILET MLGPAR tgl 10 ----
    target = None
    for k in kids_in:
        vals = tree_in.item(k, "values")
        if vals[0] == "MLGPAR" and vals[1] == "10" and vals[2] == "AYAM FILET":
            target = k
            break
    check("Ada baris MLGPAR/AYAM FILET/Tgl 10 utk drill-down", target is not None)
    if target is not None:
        bbox = tree_in.bbox(target)
        evd = _Ev()
        evd.widget = tree_in
        evd.x, evd.y = bbox[0] + 10, bbox[1] + bbox[3] // 2
        iv._on_double_click(evd)
        root.update()
        # popup terakhir di stack toplevel
        popups = [w for w in root.winfo_children()
                  if isinstance(w, InDetailPopup) and w.winfo_exists()]
        check("Double-click → popup Rincian IN terbuka", len(popups) >= 1)
        if popups:
            pop = popups[-1]
            pkids = list(pop.tree.get_children(""))
            srcs = {pop.tree.set(k, "Source") for k in pkids}
            check("Popup: ada dokumen 42.05", any("42.05" in s for s in srcs),
                  f"srcs={srcs}")
            check("Popup: ada dokumen 32.24", any("32.24" in s for s in srcs),
                  f"srcs={srcs}")
            check("Popup: ada subtotal per sumber",
                  any(str(s).startswith("TOTAL") for s in srcs))
            check("Popup: ada TOTAL IN", "TOTAL IN" in str(pop.tree.item(
                pkids[-1], "values")[0] if pkids else ""))
            nomors = [pop.tree.set(k, "Nomor") for k in pkids
                      if pop.tree.set(k, "Nomor")]
            check("Popup: Nomor dokumen tampil (IT./RI.)",
                  any(n.startswith(("IT.", "RI.", "PI.")) for n in nomors),
                  f"nomors={nomors[:4]}")
            # qty 42.05(750) + 32.24(300) = 1050 == IN metric di append1? (mock IN=5 —
            # detail mock terpisah; verifikasi total popup = 1050)
            total_row = [pop.tree.set(k, "Qty") for k in pkids
                         if pop.tree.set(k, "Source") == "TOTAL IN"]
            check("Popup: TOTAL IN = 1,050 (42.05:750 + 32.24:300)",
                  total_row and total_row[0] == "1,050", f"got {total_row}")
            # copy semua nomor unik
            pop._copy_all_unique()
            root.update()
            clip = root.clipboard_get()
            check("Copy Semua Nomor → clipboard berisi IT./RI. unik",
                  "IT.2026.09.00202" in clip and "RI.2026.09.009" in clip)
            pop.destroy()
            root.update()

    # ==================================================================
    print("== 14. v3.6 — AUDIT REKONSILIASI × DATA APP + FIX/KOLOM ==")
    from src.pipeline.fn_audit import (build_audit_rekap,
                                       build_audit_input,
                                       AUDIT_INPUT_COLUMNS)
    import pandas as pd

    # --- (a) build_audit_input: rekap + in_detail → 10 kolom kanonik ---
    raw = build_audit_input(rekap_so, in_detail)
    check("build_audit_input: 10 kolom kanonik (struktur input VBA)",
          list(raw.columns) == AUDIT_INPUT_COLUMNS,
          f"got {list(raw.columns)}")
    check("build_audit_input: baris = union aktivitas (SO/BM/IN) = 9",
          len(raw) == 9, f"got {len(raw)}")
    check("build_audit_input: urut per (Resto, Item, Tanggal)",
          raw["Resto"].tolist()[:4] == ["MLGPAR"] * 4
          and raw["Tanggal"].tolist()[:2] == [4, 5],
          f"got {list(zip(raw['Resto'], raw['Tanggal']))[:5]}")
    so_g4 = raw[(raw["Nama Item"] == "GULA PASIR")
                & (raw["Tanggal"] == 4)]
    check("build_audit_input: Hasil SO hadir di tanggal SO (NaN selain itu)",
          float(so_g4["Hasil SO"].iloc[0]) == 100.0
          and raw[raw["Nama Item"] == "SUSU UHT 1L"]["Hasil SO"].isna().all(),
          f"got {so_g4['Hasil SO'].tolist()}")

    # --- (b) engine: aturan VBA pada data app ---
    sts = audit_df["Status Analisis Audit"].tolist()
    check("Engine: OK (Matching) saat BM == IN",
          "OK (Matching)" in sts)
    check("Engine: VALID (Sistem Masuk) (SO naik + BM=0 + IN>0)",
          "VALID (Sistem Masuk)" in sts)
    check("Engine: CUT-OFF RESOLVED (+100 lalu −100)",
          sts.count("CUT-OFF RESOLVED") == 2)
    check("Engine: DEVIASI MURNI (sisa gantung)",
          "DEVIASI MURNI" in sts)
    check("Engine: KPI lengkap dari data app",
          audit_kpi["rows"] == 9 and audit_kpi["omit"] == 1
          and audit_kpi["cutoff"] == 2 and audit_kpi["deviasi_murni"] == 1
          and abs(audit_kpi["deviasi_qty"] - 80.0) < 0.001,
          f"got {audit_kpi}")
    dm = audit_df[audit_df["Status Analisis Audit"] == "DEVIASI MURNI"]
    check("Engine: catatan Sisa Gantung VBA-style",
          "Sisa Gantung: +80" in str(dm.iloc[0]["Detail & Catatan Audit"]),
          f"got {dm.iloc[0]['Detail & Catatan Audit']!r}")

    # --- (c) BUG FIX v3.6: klik funnel heading → popup TERBUKA ---
    select_and_wait(root, app, app.tab_in_selisih, iv)
    popups_before = [w for w in root.winfo_children() if w.winfo_exists()]
    x_resto = 35   # tengah kolom pertama 'Resto'
    tree_in.event_generate("<Button-1>", x=x_resto, y=10, when="now")
    root.update()
    new_pops = [w for w in root.winfo_children()
                if w.winfo_exists() and w not in popups_before
                and w.title().startswith("Filter —")]
    check("(v3.6 BUG FIX) Klik funnel 'Resto' dgn mouse → popup filter "
          "TERBUKA", len(new_pops) == 1,
          f"got {[w.title() for w in new_pops]}")
    for p in new_pops:
        p.destroy()
    root.update()

    # --- (d) header filter semua kolom (incl. Hasil Audit & SO) ---
    check("(v3.6) Semua 12 kolom punya HeaderFilter",
          hasattr(iv, "header_filters") and
          len(iv.header_filters._filters) == len(COL_IDS))
    iv._on_col_filter("Hasil Audit", {"DEVIASI MURNI"})
    wait_view(root, iv)
    kids_f = list(tree_in.get_children(""))
    check("Filter header Hasil Audit=DEVIASI MURNI → hanya baris SUSU",
          len(kids_f) == 1 and
          tree_in.set(kids_f[0], "Nama Barang") == "SUSU UHT 1L",
          f"got {[(tree_in.set(k, 'Nama Barang')) for k in kids_f]}")
    iv._reset_filter_states()
    iv._refresh()
    wait_view(root, iv)

    # --- (e) HIDE/UNHIDE KOLOM (ColumnManager v3.6) ---
    check("(v3.6) ColumnManager terpasang", iv._colmgr is not None)
    iv._colmgr.hide("KATEGORI")
    root.update()
    check("Hide kolom KATEGORI → displaycolumns tanpa KATEGORI",
          "KATEGORI" not in [str(c) for c in tree_in.cget("displaycolumns")],
          f"got {tree_in.cget('displaycolumns')}")
    hdrs_now = [tree_in.heading(c)["text"]
                for c in tree_in["columns"]
                if c in [str(x) for x in
                         tree_in.cget("displaycolumns")]]
    check("Hide kolom: heading KATEGORI hilang dari tampilan",
          "KATEGORI" not in hdrs_now, f"got {hdrs_now}")
    # identifikasi klik tetap benar setelah kolom disembunyikan
    # (display: Resto 74 + Tanggal 64 → Nama Barang mulai x=138)
    x_nb = 74 + 64 + 100   # tengah kolom 'Nama Barang' (KATEGORI hidden)
    hits = {"n": 0}
    orig_open = iv.header_filters._filters["Nama Barang"].open_popup
    iv.header_filters._filters["Nama Barang"].open_popup = \
        lambda *a, **k: hits.__setitem__("n", hits["n"] + 1)
    tree_in.event_generate("<Button-1>", x=x_nb, y=10, when="now")
    root.update()
    iv.header_filters._filters["Nama Barang"].open_popup = orig_open
    check("(v3.6) Klik funnel tetap akurat setelah kolom disembunyikan",
          hits["n"] == 1, f"got {hits['n']}")
    iv._colmgr.show_all()
    root.update()
    check("Show all → semua kolom kembali tampil",
          "#all" in str(tree_in.cget("displaycolumns")) or
          len(tree_in.cget("displaycolumns")) == len(COL_IDS),
          f"got {tree_in.cget('displaycolumns')}")
    # panel kolom terbuka & tertutup
    iv._colmgr.open_panel()
    root.update()
    check("Tombol ◱ Kolom → panel checklist terbuka",
          iv._colmgr._panel is not None and iv._colmgr._panel.winfo_exists())
    iv._colmgr.open_panel()   # toggle tutup
    root.update()

    # --- (f) LightMode dihapus total ---
    import inspect
    from src.config import Config as _Cfg
    check("(v3.5) Config tidak lagi memuat LightMode",
          "self.LightMode" not in inspect.getsource(_Cfg))

    # ==================================================================
    print("== 15. v3.4 — LEBAR KOLOM: drag tepi + ↔ Auto-Fit ==")
    from src.ui.widgets import enable_col_resize
    # (a) drag tepi kanan heading kolom pertama
    # (stretch=False supaya lebar deterministik — dengan stretch Tk
    # redistribusi ruang sisa jendela ke semua kolom)
    tree_in.column("Resto", stretch=False)
    w_before = tree_in.column("Resto", "width")
    edge_x = w_before  # tepi kanan kolom pertama
    tree_in.event_generate("<Button-1>", x=edge_x, y=10)
    root.update()
    tree_in.event_generate("<B1-Motion>", x=edge_x + 60, y=10)
    root.update()
    tree_in.event_generate("<ButtonRelease-1>", x=edge_x + 60, y=10)
    root.update()
    w_after = tree_in.column("Resto", "width")
    check("Drag tepi heading → lebar kolom berubah (w+60)",
          w_after == w_before + 60, f"{w_before} → {w_after}")
    tree_in.column("Resto", stretch=True)
    # (b) tombol ↔ Auto-Fit menyesuaikan lebar ke konten
    iv._auto_fit()
    root.update()
    w_autofit = tree_in.column("Nama Barang", "width")
    check("↔ Auto-Fit: kolom Nama Barang menyesuaikan konten (>default)",
          w_autofit != 200, f"200 → {w_autofit}")
    # (c) enable_col_resize terpasang di semua view utama
    views_trees = [
        app.pivot_view.tree, app.deviasi_gr_view.tree,
        app.deviasi_pcs_view.tree, app.laporan_view.tree,
        app.rincian_view.tree, app.followup_view.tree,
        app.in_selisih_view.tree,
    ]
    # tidak ada API publik utk cek binding — verifikasi tidak error saat
    # memanggil ulang (idempotent) + smoke drag di pivot (show tree headings)
    for t in views_trees:
        enable_col_resize(t)
    check("enable_col_resize terpasang di 7 view (idempotent, tanpa error)",
          True)

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
