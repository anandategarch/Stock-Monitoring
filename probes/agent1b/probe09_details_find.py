"""PROBE 09 — DetailsPopup scope + Ctrl+F find + copy TSV + po_keterangan.

A) show_details_popup with filters (NAMA RESTO) scopes rows to that resto
   only (drill-down scope).
B) Ctrl+F find in popup opens TreeFindPopup; typing + Enter navigates;
   find tags visible on matched row.
C) Ctrl+C multi-row copies TSV (tab-separated, values match display).
D) po_keterangan.potensi_po_label_for: BM>0 + SO naik + tanpa 32.24/99.01
   → 'Potensi PO belum dibuat' label; negative control (dengan 32.24) → ''.
E) doc_codes._doc_code_str / _ri_balancing pure behavior spot-check.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary

import pandas as pd


def main():
    root, app = boot_app()
    try:
        from test_ui_redesign import make_mock_append1, make_mock_in_detail
        from src.ui.details_popup import show_details_popup, DetailsPopup
        append1 = make_mock_append1()
        in_detail = make_mock_in_detail()

        # ---- A: popup scoped by resto filter ----
        popup = show_details_popup(root, append1,
                                   nama_barang="AYAM FILET",
                                   jenis=None,
                                   filters={"NAMA RESTO": "MLGPAR"})
        pump(root, 0.6)
        # wait async render
        for _ in range(50):
            root.update()
            if not getattr(popup, "_busy", False):
                break
        pump(root, 0.3)
        tree = popup.tree
        rows = tree.get_children("")
        restos = {tree.set(i, "NAMA RESTO") for i in rows}
        barangs = {tree.set(i, "Nama Barang") for i in rows}
        ok_a = restos == {"MLGPAR"} and barangs == {"AYAM FILET"} \
            and len(rows) > 0
        verdict("A: DetailsPopup scope (barang+resto filter)",
                "only AYAM FILET @ MLGPAR rows",
                f"n={len(rows)} restos={restos} barangs={barangs}",
                not ok_a, severity="P1" if not ok_a else "",
                where="details_popup.show_details_popup filters")

        # ---- B: Ctrl+F find ----
        from src.ui.widgets import open_tree_find, FIND_HIT_TAG
        find_pop = open_tree_find(tree)
        pump(root, 0.4)
        if find_pop is None:
            verdict("B: Ctrl+F opens TreeFindPopup in details popup",
                    "TreeFindPopup window", "none", True, "P2")
        else:
            find_pop.var.set("500")   # IN value 500 exists in data
            find_pop._recompute()
            pump(root, 0.3)
            matches = list(find_pop._matches)
            find_pop._nav(1)
            pump(root, 0.2)
            highlighted = []
            for i in tree.get_children(""):
                tags = tree.item(i, "tags") or ()
                if FIND_HIT_TAG in tags or "__find_cur" in tags:
                    highlighted.append(i)
            ok_b = bool(matches) and bool(highlighted)
            verdict("B: find in details popup finds value & highlights",
                    "matches > 0, find tag applied",
                    f"matches={len(matches)} highlighted={len(highlighted)}",
                    not ok_b, severity="P2" if not ok_b else "",
                    where="widgets.TreeFindPopup + details_popup find bind")
            find_pop.close()
            pump(root, 0.2)

        # ---- C: Ctrl+C TSV copy (binding on the popup TREE) ----
        sel = list(tree.get_children(""))[:2]
        tree.selection_set(sel)
        root.update()
        tree.event_generate("<Control-c>")
        root.update()
        pump(root, 0.3)
        try:
            clip = root.clipboard_get()
        except Exception:
            clip = ""
        lines = clip.splitlines()
        ok_c = len(lines) == 2 and "\t" in lines[0]
        verdict("C: Ctrl+C copies selected rows as TSV",
                "2 lines, tab-separated", f"lines={len(lines)} "
                f"first={lines[0][:70]!r}", not ok_c,
                severity="P2" if not ok_c else "",
                where="widgets.copy_tree_selection_tsv (popup bind)")
        popup.destroy()
        pump(root, 0.2)

        # ---- D: po_keterangan ----
        from src.ui.po_keterangan import potensi_po_label_for
        # craft data: BM 100 at t5, SO 100→200 (naik), no 32.24/99.01 IN
        data = pd.DataFrame([
            {"Nama Barang": "BRGP", "JENIS": "1.SO", "NAMA RESTO": "R1",
             "Tanggal": 4, "NILAI": 100.0, "SATUAN": "GR",
             "KATEGORI": "K", "SOURCE KIRIMAN": "G", "Nomor": None,
             "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None},
            {"Nama Barang": "BRGP", "JENIS": "1.SO", "NAMA RESTO": "R1",
             "Tanggal": 5, "NILAI": 200.0, "SATUAN": "GR",
             "KATEGORI": "K", "SOURCE KIRIMAN": "G", "Nomor": None,
             "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None},
            {"Nama Barang": "BRGP", "JENIS": "5.BARANG MASUK",
             "NAMA RESTO": "R1", "Tanggal": 5, "NILAI": 100.0,
             "SATUAN": "GR", "KATEGORI": "K", "SOURCE KIRIMAN": "G",
             "Nomor": None, "Nomor PO": None,
             "#Tgl/Jam Pembuatan IT": None},
        ])
        # in_detail WITHOUT 32.24/99.01 for this pair
        in_det = pd.DataFrame([
            {"NAMA RESTO": "R1", "Nama Barang": "BRGP", "Tanggal": 5,
             "Value": 0.0, "Nomor": "X", "Nomor PO": None,
             "#Tgl/Jam Pembuatan IT": None, "SOURCE IN": "42.05",
             "JENIS": "IN"},
        ])
        lab = potensi_po_label_for(data, in_det, "BRGP", "R1", 5)
        # negative control: with 32.24 present
        in_det2 = pd.DataFrame([
            {"NAMA RESTO": "R1", "Nama Barang": "BRGP", "Tanggal": 5,
             "Value": 100.0, "Nomor": "RI.1", "Nomor PO": "PO.1",
             "#Tgl/Jam Pembuatan IT": None, "SOURCE IN": "32.24",
             "JENIS": "IN"},
        ])
        lab2 = potensi_po_label_for(data, in_det2, "BRGP", "R1", 5)
        ok_d = bool(lab) and not lab2
        verdict("D: po_keterangan label (BM+SO naik tanpa 32.24/99.01)",
                "label present; empty when 32.24 exists",
                f"label={lab!r} control={lab2!r}", not ok_d,
                severity="P2" if not ok_d else "",
                where="po_keterangan.potensi_po_label_for")

        # ---- E: doc_codes spot check ----
        from src.ui.doc_codes import _doc_code_str, _ri_balancing
        s = _doc_code_str("RI.2026.09.009", "PO.2026.10.012")
        ri = _ri_balancing("RI.2026.09.009", "PO.2026.10.012")
        ri_same = _ri_balancing("RI.2026.09.009", "PO.2026.09.009")
        ok_e = isinstance(s, str) and ri and not ri_same
        verdict("E: doc_codes _ri_balancing month mismatch detect",
                "RI Sep vs PO Okt → True; same month → False",
                f"ri={ri} ri_same={ri_same} docstr={s!r}", not ok_e,
                severity="P3" if not ok_e else "",
                where="doc_codes._ri_balancing")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
