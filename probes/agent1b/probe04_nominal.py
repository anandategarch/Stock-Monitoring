"""PROBE 04 — 🧮 Nominal Deviasi (per resto) — v3.11.9 surface.

Setup: 3.DEVIASI rows @H=25 + 9.ACR (deviasi_only), harga_map, plus a
crafted deviasi FILE (WEEK 4) driving 'Nominal Deviasi Bulan Lalu' +
'Persen Kenaikan/Penurunan'.

A) Table values: per-resto Nominal (Rp 20 / Rp 180 / Rp 30), Lalu
   (Rp 15 / Rp 300), Persen (+33,3% / -40,0%), TOTAL pinned.
B) Sort by Persen desc numeric ('+' prefix parsed).
C) Sort by Nominal desc → TOTAL row stays at END.
D) non-deviasi pair (no 9.ACR, kategori non COM/Packaging) excluded and
   COUNTED in status (v3.11.9 deviasi_only honest status).
E) Anak tab 'Tanpa Harga': KOPI row with Kuantiti '(5)' + neg_cell tag.
F) Double-click resto → rincian popup opens.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary

import pandas as pd


def craft_dev_df():
    rows = []
    spec = [
        ("AYAM FILET", "MLGPAR", "GR", 2.0, "COM DEVIASI - RESTO"),
        ("GULA PASIR", "SBYKET", "GR", 12.0, "COM DEVIASI - RESTO"),
        ("KOPI BUBUK 100G", "MLGPAR", "PCS", -5.0, "COM DEVIASI - RESTO"),
        ("AYAM FILET", "BDGSET", "GR", 3.0, "COM DEVIASI - RESTO"),
        ("NONDEV BRG", "MLGPAR", "GR", 7.0, "OPERASIONAL"),  # no 9.ACR
        # NOCR: passes kategori filter (COM DEVIASI) but has NO 9.ACR row
        # → dropped by v3.11.9 deviasi_only (status must mention it)
        ("NOCR BRG", "MLGPAR", "GR", 9.0, "COM DEVIASI - RESTO"),
    ]
    for b, r, s, v, k in spec:
        rows.append({"Nama Barang": b, "NAMA RESTO": r, "SATUAN": s,
                     "Tanggal": 25, "JENIS": "3.DEVIASI", "NILAI": v,
                     "KATEGORI": k})
    # 9.ACR rows so pairs pass deviasi_only (except NONDEV BRG)
    for b, r, s in (("AYAM FILET", "MLGPAR", "GR"),
                    ("GULA PASIR", "SBYKET", "GR"),
                    ("KOPI BUBUK 100G", "MLGPAR", "PCS"),
                    ("AYAM FILET", "BDGSET", "GR")):
        rows.append({"Nama Barang": b, "NAMA RESTO": r, "SATUAN": s,
                     "Tanggal": 2, "JENIS": "9.ACR", "NILAI": 5.0,
                     "KATEGORI": "X"})
    return pd.DataFrame(rows)


def craft_deviasi_file(path):
    from openpyxl import Workbook
    hdr = ["Akun Penyesuaian Persediaan", "STATUS", "RESTO", "NAMA BAHAN",
           "Satuan", "QTY BOM", "QTY COM", "QTY DEVIASI", "QTY WASTE",
           "QTY SUSUT", "QTY TRIAL", "QTY LOSS SURPLUS", "NOMINAL DEVIASI",
           "NOMINAL WASTE", "NOMINAL SUSUT", "NOMINAL TRIAL",
           "NOMINAL LOSS/SURPLUS", "QTY WASTE + SUSUT", "% WASTE + SUSUT",
           "%TOLERANSI", "% QTY DEVIASI TO BOM", "QTY WASTE TO BOM",
           "QTY SUSUT TO BOM", "QTY TRIAL  TO BOM",
           "QTY LOSS/ SURPLUS TO BOM", "AREA", "BULAN", "PENJUALAN",
           "STATUS BULAN", "BULAN 2"]
    data = [
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "AYAM FILET",
         "GR", -80, -31, 2, 0, 0, 0, 2, 15, 0, 0, 0, 15, 0, 0,
         "BELUM ADA TOLERANSI", 0.02, 0, 0, 0, 0, "JAWA TIMUR",
         "204.OKT 26", 4000, "WEEK 4", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1002.SBYKET", "GULA PASIR",
         "GR", -200, -50, 12, 0, 0, 0, 12, 300, 0, 0, 0, 300, 0, 0,
         "BELUM ADA TOLERANSI", 0.06, 0, 0, 0, 0, "JAWA TIMUR",
         "204.OKT 26", 4000, "WEEK 4", "8.OKTOBER"],
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(hdr)
    for row in data:
        ws.append(row)
    wb.save(path)


def main():
    root, app = boot_app()
    try:
        from test_ui_redesign import wait_view
        dev = craft_dev_df()
        harga = {"AYAM FILET": (10.0, "GR"), "GULA PASIR": (15.0, "GR")}
        konv = {"rasio": {}, "terkecil": {}}

        # komparasi needs app data before loading file
        app.komparasi_view.load_data(dev, harga_map=harga,
                                     konversi_map=konv)
        app.komparasi_view._auto_loaded = True
        app.komparasi_view._show_all_weeks.set(True)
        import tempfile, os
        fpath = os.path.join(tempfile.gettempdir(),
                             "probe04_deviasi_file.xlsx")
        craft_deviasi_file(fpath)
        app.komparasi_view._load_paths([fpath], interactive=False)
        wait_view(root, app.komparasi_view)
        pump(root, 0.2)

        # set shared H = 25 BEFORE loading nominal view data
        app._shared_h.set(25)
        app.nominal_resto_view.load_data(dev, harga_map=harga,
                                         konversi_map=konv)
        app.notebook.select(app.tab_nominal_resto)
        pump(root, 0.3)
        app.nominal_resto_view.ensure_refreshed()
        wait_view(root, app.nominal_resto_view)
        nt = app.nominal_resto_view.tree

        def rowmap():
            out = {}
            for i in nt.get_children(""):
                out[str(nt.set(i, "Resto"))] = {
                    "nominal": nt.set(i, "Nominal Deviasi"),
                    "lalu": nt.set(i, "Nominal Deviasi Bulan Lalu"),
                    "pct": nt.set(i, "Persen Kenaikan/Penurunan"),
                }
            return out

        rm = rowmap()
        ok_a = (rm.get("MLGPAR", {}).get("nominal") == "Rp 20"
                and rm.get("SBYKET", {}).get("nominal") == "Rp 180"
                and rm.get("BDGSET", {}).get("nominal") == "Rp 30"
                and rm.get("MLGPAR", {}).get("lalu") == "Rp 15"
                and rm.get("SBYKET", {}).get("lalu") == "Rp 300"
                and rm.get("TOTAL", {}).get("nominal") == "Rp 230")
        verdict("A1: per-resto Nominal + Lalu from file + TOTAL",
                "MLGPAR Rp20/Rp15 · SBYKET Rp180/Rp300 · BDGSET Rp30 · "
                "TOTAL Rp230", str(rm), not ok_a,
                severity="P1" if not ok_a else "",
                where="nominal_resto_view._compute_resto")
        pct_m = rm.get("MLGPAR", {}).get("pct")
        pct_s = rm.get("SBYKET", {}).get("pct")
        ok_a2 = (pct_m == "+33,3%" and pct_s == "-40,0%")
        verdict("A2: Persen Kenaikan/Penurunan +33,3% / -40,0%",
                "+33,3% / -40,0%", f"{pct_m!r} / {pct_s!r}", not ok_a2,
                severity="P2" if not ok_a2 else "",
                where="nominal_common.hitung_persen_kenaikan + fmt_pct_cell")

        # ---- B: sort by Persen desc ----
        app.nominal_resto_view._sort_by("Persen Kenaikan/Penurunan",
                                        reverse=True)
        pump(root, 0.4)
        order = [str(nt.set(i, "Resto")) for i in nt.get_children("")]
        ok_b = (order.index("MLGPAR") < order.index("BDGSET")
                if "BDGSET" in order else True) and \
               (order.index("BDGSET") < order.index("SBYKET")
                if "BDGSET" in order and "SBYKET" in order else True)
        verdict("B: sort Persen desc numeric (+33,3% > '-' > -40,0%)",
                "MLGPAR, BDGSET, SBYKET, TOTAL", str(order), not ok_b,
                severity="P2" if not ok_b else "",
                where="nominal_resto_view._sort_by parse pct")

        # ---- C: sort Nominal desc → TOTAL at end ----
        app.nominal_resto_view._sort_by("Nominal Deviasi", reverse=True)
        pump(root, 0.4)
        order2 = [str(nt.set(i, "Resto")) for i in nt.get_children("")]
        total_last = order2[-1] == "TOTAL" if order2 else False
        verdict("C: sort Nominal desc → TOTAL pinned at END",
                "[..., 'TOTAL']", str(order2), not total_last,
                severity="P2" if not total_last else "",
                where="nominal_resto_view._pin_total_row")

        # ---- D: deviasi_only honest status (kategori=Semua so the
        # kategori mask does not pre-drop the non-deviasi pair) ----
        app.nominal_resto_view._kategori_var.set("Semua")
        app.nominal_resto_view._on_kategori_changed()
        wait_view(root, app.nominal_resto_view)
        status = app.nominal_resto_view.status_var_label.get()
        rm2 = rowmap()
        nondev_hidden = all("NONDEV" not in k and "NOCR" not in k
                            for k in rm2)
        ok_d = nondev_hidden and "non-deviasi dikecualikan" in status
        verdict("D: non-deviasi pair excluded + mentioned in status "
                "(v3.11.9 honest counter; kategori=Semua)",
                "no NONDEV/NOCR rows + status 'pasangan non-deviasi "
                "dikecualikan'",
                f"hidden={nondev_hidden} status={status!r}", not ok_d,
                severity="P3" if not ok_d else "",
                where="nominal_common hitung_nominal_pairs deviasi_only")

        # ---- E: anak tab Tanpa Harga ----
        app.nominal_resto_view._sub_nb.select(
            app.nominal_resto_view._tab_noharga)
        pump(root, 0.5)
        nht = app.nominal_resto_view.tree_noharga
        nh_rows = {}
        for i in nht.get_children(""):
            vals = nht.item(i, "values")
            nh_rows[vals[0]] = vals
        kopi = None
        for i in nht.get_children(""):
            if str(nht.set(i, "Nama Barang")) == "KOPI BUBUK 100G":
                kopi = nht.set(i, "Kuantiti Deviasi")
                kopi_tags = nht.item(i, "tags")
                # per-cell neg tag check (Tk9 native)
                try:
                    has_negcell = bool(int(nht.tk.call(
                        str(nht), "tag", "cell", "has", "neg_cell",
                        (str(i), "Kuantiti Deviasi"))))
                except Exception:
                    ov = getattr(nht, "_cell_color_overlay", None)
                    has_negcell = (ov is not None and (str(i),
                                    "Kuantiti Deviasi")
                                   in ov._tag_cells.get("neg_cell", set()))
        ok_e = kopi == "(5)" and has_negcell
        verdict("E: Tanpa Harga subtab KOPI qty '(5)' + neg_cell red",
                "'(5)' with neg_cell tag", f"qty={kopi!r} negcell={has_negcell}",
                not ok_e, severity="P2" if not ok_e else "",
                where="nominal_resto_view._render_noharga + N9 fix")

        # ---- F: double-click resto → popup ----
        app.nominal_resto_view._sub_nb.select(
            app.nominal_resto_view._tab_main)
        pump(root, 0.3)
        target = None
        for i in nt.get_children(""):
            if str(nt.set(i, "Resto")) == "MLGPAR":
                target = i
                break
        class Ev:
            pass
        ev = Ev()
        ev.widget = nt
        bbox = nt.bbox(target, column="Nominal Deviasi")
        ev.x, ev.y = bbox[0] + 4, bbox[1] + bbox[3] // 2
        app.nominal_resto_view._on_double_click(ev)
        pump(root, 0.4)
        # popup is tk.Toplevel(self) — child of the VIEW, not root
        dwins = [w for w in app.nominal_resto_view._detail_wins
                 if w.winfo_exists()]
        ok_f = bool(dwins)
        if dwins:
            dwins[-1].destroy()
        verdict("F: double-click resto opens rincian popup",
                "Toplevel popup (view._detail_wins)", f"popups={len(dwins)}",
                not ok_f,
                severity="P2" if not ok_f else "",
                where="nominal_resto_view._show_resto_popup")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
