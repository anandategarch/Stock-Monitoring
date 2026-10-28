"""PROBE 02 — Deviasi GR/PCS interactions (v3.11.9 surface):

A) DeviasiPopup (double-click) — new ACR / Avg COM / Avg ACR columns:
   hand-computed oracle on crafted data:
     SA=100@1, SO(t)=100-5t for t=1..6, IN=20@3, ACR=10@2 & 7@4, H=6
     com(1..5) = 5,5,25,5,5 → Avg COM = 9 ; ACR avg = (0+10+0+7+0)/5 = 3,4
   → row Tanggal 6 must show Avg COM '9', Avg ACR '3,4'; other rows blank;
   footer mentions '5 hari valid'.
B) Popup satuan scoping: item with GR and PCS rows → GR tab popup shows
   only GR numbers.
C) Sort by 'Deviasi' (formatted '(5)' etc.) numeric descending.
D) ✓ follow-up toggle via real click on cell; badge + store state;
   toggle survives sort.
E) H-row highlight present (tag h_row on row Tanggal == H).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary

import pandas as pd


def craft_df():
    rows = []
    # Pair 1: AVGTEST / MLGPAR / GR — deterministic oracle
    p = ("AVGTEST", "MLGPAR", "GR")
    rows.append(dict(zip(
        ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
         "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
         "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
        [p[0], "SALDO AWAL", p[1], 1, 100.0, p[2], "AKTIF", "BAHAN",
         "GUDANG", None, None, None])))
    for t in range(1, 7):
        so = 100.0 - 5.0 * t
        rows.append(dict(zip(
            ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
             "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
             "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
            [p[0], "1.SO", p[1], t, so, p[2], "AKTIF", "BAHAN",
             "GUDANG", None, None, None])))
        rows.append(dict(zip(
            ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
             "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
             "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
            [p[0], "2.SALDO AKHIR", p[1], t, so, p[2], "AKTIF", "BAHAN",
             "GUDANG", None, None, None])))
    rows.append(dict(zip(
        ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
         "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
         "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
        [p[0], "4.IN", p[1], 3, 20.0, p[2], "AKTIF", "BAHAN",
         "GUDANG", "IT.001", "PO.001", None])))
    for t, v in ((2, 10.0), (4, 7.0)):
        rows.append(dict(zip(
            ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
             "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
             "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
            [p[0], "9.ACR", p[1], t, v, p[2], "AKTIF", "BAHAN",
             "GUDANG", None, None, None])))

    # Pair 2: DUA SATUAN — GR and PCS rows for same pair
    for sat, dev in (("GR", 30.0), ("PCS", 4.0)):
        rows.append(dict(zip(
            ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
             "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
             "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
            ["BRG DUA", "1.SO", "MLGPAR", 6, 100.0, sat, "AKTIF", "BAHAN",
             "GUDANG", None, None, None])))
        rows.append(dict(zip(
            ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
             "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
             "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
            ["BRG DUA", "2.SALDO AKHIR", "MLGPAR", 6, 100.0 - dev, sat,
             "AKTIF", "BAHAN", "GUDANG", None, None, None])))

    # Pair 3: NEG / SBYKET / GR — negative deviasi (paren display)
    rows.append(dict(zip(
        ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
         "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
         "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
        ["NEG", "1.SO", "SBYKET", 6, 50.0, "GR", "AKTIF", "BAHAN",
         "GUDANG", None, None, None])))
    rows.append(dict(zip(
        ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
         "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
         "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"],
        ["NEG", "2.SALDO AKHIR", "SBYKET", 6, 62.0, "GR", "AKTIF",
         "BAHAN", "GUDANG", None, None, None])))
    return pd.DataFrame(rows)


COLS = ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
        "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
        "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"]


def r(barang, jenis, resto, tgl, nilai, satuan):
    return dict(zip(COLS, [barang, jenis, resto, tgl, nilai, satuan,
                           "AKTIF", "BAHAN", "GUDANG", None, None, None]))


def main():
    root, app = boot_app()
    try:
        from test_ui_redesign import wait_view
        df = craft_df()
        app.followup_store.clear()
        app.deviasi_gr_view.load_data(df)
        app.notebook.select(app.tab_deviasi_gr)
        pump(root, 0.2)
        app.deviasi_gr_view.ensure_refreshed()
        wait_view(root, app.deviasi_gr_view)

        tree = app.deviasi_gr_view.tree
                # ---- A: popup oracle via REAL double-click on AVGTEST row ----
        target = None
        for i in tree.get_children(""):
            vals = tree.item(i, "values")
            if vals[2] == "AVGTEST":
                target = i
                break
        assert target, "AVGTEST row not found"

        class Ev:
            pass
        ev = Ev()
        ev.widget = tree
        bbox = tree.bbox(target, column="Deviasi")
        ev.x, ev.y = bbox[0] + 4, bbox[1] + bbox[3] // 2
        app.deviasi_gr_view._on_double_click(ev)
        pump(root, 0.3)

        from src.ui.deviasi_popup import DeviasiPopup
        pops = [w for w in root.winfo_children()
                if isinstance(w, DeviasiPopup) and w.winfo_exists()]
        if not pops:
            verdict("A: DeviasiPopup opens on double-click",
                    "popup window", "none", True, "P1")
            return
        pop = pops[-1]
        ptree = pop.tree
        pdata = {}
        for i in ptree.get_children(""):
            v = ptree.item(i, "values")
            pdata[v[0]] = dict(zip(["Tanggal", "SO", "Saldo Akhir", "Deviasi",
                                    "COM", "ACR", "Avg COM", "Avg ACR", "IN"],
                                   v[:9]))
        row6 = pdata.get("6", {})
        avg_com_vals = [pdata[t].get("Avg COM", "") for t in pdata]
        ok_a = (row6.get("Avg COM") == "9" and row6.get("Avg ACR") == "3,4"
                and all(v == "" for t, v in zip(pdata, avg_com_vals) if t != "6"))
        footer = pop.status_var.get()
        ok_footer = "5 hari valid" in footer
        verdict("A1: popup row H Avg COM='9' Avg ACR='3,4', other rows blank",
                "Avg COM 9 / Avg ACR 3,4 only on row 6",
                f"row6={row6} all_avg={avg_com_vals}", not ok_a,
                severity="P2" if not ok_a else "",
                where="src/ui/deviasi_popup.py build_popup_rows/_com_acr_avg")
        verdict("A2: popup footer '5 hari valid'",
                "… rata-rata tgl 1–5: 5 hari valid", footer, not ok_footer,
                severity="P3" if not ok_footer else "",
                where="src/ui/deviasi_popup.py _render footer")
        # ACR column spot values
        acr2, acr4 = pdata.get("2", {}).get("ACR"), pdata.get("4", {}).get("ACR")
        verdict("A3: popup ACR col shows 9.ACR per date (t2=10, t4=7)",
                "10 / 7", f"{acr2} / {acr4}",
                not (acr2 == "10" and acr4 == "7"),
                severity="P2" if not (acr2 == "10" and acr4 == "7") else "",
                where="src/ui/deviasi_popup.py _acr_series")
        # H row highlight tag
        h_iid = None
        for i in ptree.get_children(""):
            if ptree.item(i, "values")[0] == "6":
                h_iid = i
                break
        h_ok = h_iid and "h_row" in (ptree.item(h_iid, "tags") or ())
        verdict("A4: popup row Tanggal H highlighted (tag h_row)",
                "h_row tag on row 6",
                ptree.item(h_iid, "tags") if h_iid else "no row", not h_ok,
                severity="P3" if not h_ok else "",
                where="src/ui/deviasi_popup.py _render")
        pop.destroy()
        pump(root, 0.2)

        # ---- B: satuan scoping on BRG DUA (GR tab) ----
        target_b = None
        for i in tree.get_children(""):
            vals = tree.item(i, "values")
            if vals[2] == "BRG DUA":
                target_b = i
                break
        bbox = tree.bbox(target_b, column="Deviasi")
        ev.x, ev.y = bbox[0] + 4, bbox[1] + bbox[3] // 2
        app.deviasi_gr_view._on_double_click(ev)
        pump(root, 0.3)
        pops = [w for w in root.winfo_children()
                if isinstance(w, DeviasiPopup) and w.winfo_exists()]
        pop = pops[-1]
        pt = pop.tree
        vals_b = [pt.item(i, "values") for i in pt.get_children("")]
        # GR row: SO 100, SA 70 → deviasi 30 (PCS row would show 4)
        dev_cells = [v[3] for v in vals_b]
        b_ok = dev_cells == ["30"]
        verdict("B: popup GR tab scoped to GR satuan (Deviasi 30, not 34/4)",
                "['30']", str(dev_cells), not b_ok,
                severity="P2" if not b_ok else "",
                where="src/ui/deviasi_popup.py build_popup_rows satuan param")
        pop.destroy()
        pump(root, 0.2)

        # ---- C: sort by Deviasi desc numeric ----
        app.deviasi_gr_view._sort_by("Deviasi", reverse=True)
        pump(root, 0.4)
        devs = []
        for i in tree.get_children(""):
            v = tree.item(i, "values")
            devs.append((v[2], tree.set(i, "Deviasi")))
        # numeric values: AVGTEST dev 0 (SO=70? SO(6)=70, SA(6)=70 → 0)
        # BRG DUA 30, NEG (12) negative
        def num(s):
            s = str(s)
            if s in ("-", "", "—"):
                return 0
            if s.startswith("(") and s.endswith(")"):
                return -float(s[1:-1].replace(".", "").replace(",", "."))
            return float(s.replace(".", "").replace(",", "."))
        nums = [num(d) for _, d in devs]
        sorted_ok = nums == sorted(nums, reverse=True)
        verdict("C: sort by Deviasi desc numeric (parens=neg)",
                f"sorted desc {sorted(nums, reverse=True)}", str(nums),
                not sorted_ok, severity="P2" if not sorted_ok else "",
                where="src/ui/deviasi_view.py _sort_by + _parse_num_id")

        # ---- D: ✓ follow-up toggle real click ----
        app.followup_store.clear()
        pump(root, 0.1)
        first = tree.get_children("")[0]
        bbox = tree.bbox(first, column="✓")
        ev.x, ev.y = bbox[0] + 3, bbox[1] + bbox[3] // 2
        app.deviasi_gr_view._on_tree_click(ev)
        pump(root, 0.2)
        cell = tree.set(first, "✓")
        n_store = len(app.followup_store)
        verdict("D1: ✓ click adds follow-up entry + cell shows ✓",
                "cell ✓ + store 1", f"cell={cell!r} store={n_store}",
                not (cell and n_store == 1),
                severity="P1" if not (cell and n_store == 1) else "",
                where="src/ui/deviasi_view.py _on_tree_click")
        # survives sort
        app.deviasi_gr_view._sort_by("Nama Barang", reverse=False)
        pump(root, 0.4)
        from src.ui.followup import CHECK_ON
        cell_after = None
        for i in tree.get_children(""):
            if tree.set(i, "✓") == CHECK_ON:
                cell_after = tree.set(i, "✓")
        verdict("D2: ✓ state survives sort",
                "still " + CHECK_ON + " on the row", f"checked={cell_after!r}",
                cell_after != CHECK_ON,
                severity="P2" if cell_after != CHECK_ON else "",
                where="deviasi_view sort → cell tags reapply path")
        # uncheck
        for i in tree.get_children(""):
            if tree.set(i, "✓") == CHECK_ON:
                bbox = tree.bbox(i, column="✓")
                ev.x, ev.y = bbox[0] + 3, bbox[1] + bbox[3] // 2
                app.deviasi_gr_view._on_tree_click(ev)
                break
        pump(root, 0.2)
        verdict("D3: second ✓ click removes entry",
                "store 0", f"store={len(app.followup_store)}",
                len(app.followup_store) != 0,
                severity="P2" if len(app.followup_store) != 0 else "",
                where="deviasi_view _on_tree_click toggle")
        app.followup_store.clear()
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
