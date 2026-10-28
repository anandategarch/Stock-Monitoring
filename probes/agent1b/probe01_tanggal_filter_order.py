"""PROBE 01 — ⧩ filter value-list ordering for Tanggal column with
'25•' last-month labels (convention used by in_selisih_view / pivot).

The app convention (v3.6/v3.8/v3.11.1): date order is CHRONOLOGICAL —
25•, 26•, ..., 31•, 1, 2, 3 ... (pivot headers, table sort, export).
Question: does the HeaderFilter popup value list follow the same
convention, or do numeric-group values (1..31) come first with the
'25•' text-group values dumped at the bottom?

Checks:
 A) widget level: HeaderFilter.open_popup over values ['1','2','25•','26•']
 B) real view: in_selisih_view loaded with data containing negative dates,
    open the real Tanggal ⧩ filter, read offered order.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary, PROJ

import pandas as pd


def check_A():
    import tkinter as tk
    from tkinter import ttk
    from src.ui.widgets import HeaderFilter

    root = tk.Tk()
    root.geometry("400x300+0+0")
    tree = ttk.Treeview(root, columns=["Tanggal"], show="headings")
    tree.heading("Tanggal", text="Tanggal")
    tree.column("Tanggal", width=100)
    tree.pack(fill="both", expand=True)
    for v in ["1", "2", "25•", "26•", "3"]:
        tree.insert("", "end", values=(v,))

    hf = HeaderFilter(tree, "Tanggal", get_values=lambda: ["1", "2", "25•", "26•", "3"],
                      on_apply=lambda sel: None, label="Tanggal")
    hf.open_popup()
    root.update_idletasks()
    offered = list(hf._values_list)
    hf._close()
    root.destroy()

    expected = ["25•", "26•", "1", "2", "3"]      # chronological convention
    is_bug = offered != expected
    verdict("A: ⧩ popup Tanggal values in chronological order (25• first)",
            expected, offered, is_bug,
            severity="P3" if is_bug else "",
            where="src/ui/widgets.py _filter_value_sort_key ('•' not parsed → text group)")


def check_B():
    root, app = boot_app()
    try:
        # Realistic path: build audit df from rekap SO + in_detail via the
        # real pipeline fn (same as test_ui_redesign §3), with LAST-MONTH
        # rows (negative Tanggal) in the rekap.
        from test_ui_redesign import make_mock_append1, make_mock_in_detail, wait_view
        from src.pipeline.fn_audit import build_audit_from_app
        rows = []
        for barang, resto, tgl, so, bm in [
            ("AYAM FILET", "MLGPAR", -26, 100.0, 50.0),
            ("AYAM FILET", "MLGPAR", -25, 150.0, 60.0),
            ("AYAM FILET", "MLGPAR", 4, 400.0, 0.0),
            ("AYAM FILET", "MLGPAR", 5, 900.0, 500.0),
            ("GULA PASIR", "SBYKET", -27, 80.0, 30.0),
            ("GULA PASIR", "SBYKET", 5, 1300.0, 1200.0),
        ]:
            rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                         "JENIS": "SO", "Tanggal": tgl, "Value": so})
            if bm:
                rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                             "JENIS": "BARANG MASUK", "Tanggal": tgl,
                             "Value": bm})
        rekap_so = pd.DataFrame(rows)
        in_detail = make_mock_in_detail()
        audit_df, audit_kpi, audit_desc = build_audit_from_app(
            rekap_so, in_detail, bulan_lalu=True)
        df = make_mock_append1()
        app.in_selisih_view.load_data(df, in_detail,
                                      audit_result={"df": audit_df,
                                                    "kpi": audit_kpi,
                                                    "desc": audit_desc})
        app.notebook.select(app.tab_in_selisih)
        pump(root, 0.2)
        app.in_selisih_view.ensure_refreshed()
        wait_view(root, app.in_selisih_view)
        # widen range to include last month via REAL user path
        app.in_selisih_view.tgl_start_var.set("-27")
        app.in_selisih_view._on_tanggal_change()
        wait_view(root, app.in_selisih_view)

        # gather what the table actually shows in Tanggal column
        tgl_vals = [app.in_selisih_view.tree.item(i, "values")[1]
                    for i in app.in_selisih_view.tree.get_children("")]
        # open the real filter popup for Tanggal
        hf = app.in_selisih_view.header_filters._filters.get("Tanggal")
        if hf is None:
            verdict("B: in_selisih Tanggal ⧩ exists", "filter present", "missing", True, "P2")
            return
        hf.open_popup()
        root.update_idletasks()
        offered = list(hf._values_list)
        hf._close()
        expected = ["26•", "27•", "25•", "4", "5"]  # chrono: 26•,27• BEFORE 4,5
        # chronological convention => all • values must precede plain numbers
        nums = [v for v in offered if not v.endswith("•")]
        bullets = [v for v in offered if v.endswith("•")]
        is_bug = bool(nums and bullets and offered.index(nums[0]) < offered.index(bullets[0]))
        verdict("B: in_selisih ⧩ Tanggal offered order (table shows "
                + repr(tgl_vals) + ")",
                "all 'n•' (bulan lalu) values BEFORE plain numbers (chronological)",
                offered, is_bug,
                severity="P3" if is_bug else "",
                where="src/ui/widgets.py HeaderFilter.open_popup sort via _filter_value_sort_key")
    finally:
        root.destroy()


if __name__ == "__main__":
    check_A()
    check_B()
    summary()
