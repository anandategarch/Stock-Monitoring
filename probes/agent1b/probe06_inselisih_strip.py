"""PROBE 06 — 📤 Rekap Selisih IN: strip '🎯 SELISIH TERBANYAK — BARANG ×
RESTO' (v3.11.8) chip CLICK via REAL mouse event.

The chip handlers are bound with the MALFORMED pattern "Button-1>"
(missing leading '<') at in_selisih_view.py:3354/3357 — Tk silently
accepts the pattern but it NEVER matches a real click. The sibling resto
scoreboard rows use the correct "<Button-1>" (line 3215).

A) REAL click (event_generate <Button-1> on chip widget) → table must be
   filtered to that barang (⧩ Nama Barang active, 1 distinct barang).
B) Direct handler call (control) → filter works (proves only the BINDING
   is dead, not the handler).
C) Real click on scoreboard resto row (control — correct pattern) →
   filter Resto works via real click.
D) View mode 📈 Analisa toggle: strip hidden, sections visible; toggle
   back 📋: strip + KPI return (v3.11.9 layout integrity).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary

import pandas as pd


def main():
    root, app = boot_app()
    try:
        from test_ui_redesign import make_mock_append1, make_mock_in_detail, wait_view
        from src.pipeline.fn_audit import build_audit_from_app
        # audit with several pairs having selisih ≠ 0
        rows = []
        for barang, resto, tgl, so, bm in [
            ("AYAM FILET", "MLGPAR", 4, 400.0, 0.0),
            ("AYAM FILET", "MLGPAR", 5, 900.0, 500.0),
            ("KOPI BUBUK 100G", "MLGPAR", 3, 100.0, 0.0),
            ("KOPI BUBUK 100G", "MLGPAR", 5, 300.0, 150.0),
            ("SUSU UHT 1L", "MLGPAR", 2, 100.0, 0.0),
            ("SUSU UHT 1L", "MLGPAR", 5, 260.0, 160.0),
            ("GULA PASIR", "SBYKET", 4, 100.0, 0.0),
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
        audit_df, kpi, desc = build_audit_from_app(rekap_so, in_detail,
                                                   bulan_lalu=False)
        df = make_mock_append1()
        app.in_selisih_view.load_data(df, in_detail,
                                      audit_result={"df": audit_df,
                                                    "kpi": kpi,
                                                    "desc": desc})
        app.notebook.select(app.tab_in_selisih)
        pump(root, 0.3)
        app.in_selisih_view.ensure_refreshed()
        wait_view(root, app.in_selisih_view)
        isv = app.in_selisih_view
        tree = isv.tree

        def distinct(col):
            vals = set()
            for i in tree.get_children(""):
                vals.add(str(tree.set(i, col)))
            return vals

        base_barangs = distinct("Nama Barang")
        # find chip widgets in _barang_zone (frames with cursor hand2)
        chips = []

        def collect(w):
            for c in w.winfo_children():
                try:
                    if str(c.cget("cursor")) == "hand2":
                        chips.append(c)
                except tk_err:
                    pass
                collect(c)
        import tkinter as tk  # noqa
        global tk_err
        tk_err = tk.TclError
        collect(isv._barang_zone)
        chips = [c for c in chips if c.winfo_class() == "Frame"]

        # ---- A: REAL click on first chip ----
        if not chips:
            verdict("A: strip chip present (rendered)", "≥1 chip", "none",
                    True, "P1")
            return
        chip = chips[0]
        # capture chip text BEFORE any re-render destroys the widget
        lbl = [w for w in chip.winfo_children() if w.winfo_class() == "Label"]
        chip_txt = str(lbl[0].cget("text")) if lbl else ""
        barang_name = ""
        if chip_txt.startswith("#") and " @ " in chip_txt:
            barang_name = chip_txt[chip_txt.index(" ") + 1:
                             chip_txt.index(" @ ")]
        chip.event_generate("<Button-1>", x=3, y=3)
        pump(root, 0.6)
        wait_view(root, isv)
        barang_after_click = distinct("Nama Barang")
        sel_state = isv._col_sel.get("Nama Barang")
        ok_a = (len(barang_after_click) == 1
                and isinstance(sel_state, list) and len(sel_state) == 1)
        verdict("A: REAL click on strip chip filters table (⧩ Nama Barang)",
                "table shows 1 barang + filter active",
                f"barangs={barang_after_click} sel={sel_state} "
                f"chip_txt={chip_txt!r}",
                not ok_a, severity="P1" if not ok_a else "",
                where="in_selisih_view.py:3354 chip.bind('Button-1>' — "
                      "malformed pattern, never fires)")

        # reset filter state (direct — A failed leaves nothing to reset,
        # but be safe)
        isv._col_sel["Nama Barang"] = None
        isv.header_filters.set_selected("Nama Barang", None)

        # ---- B: direct handler call (control) ----
        isv._on_barang_row_click(barang_name)
        wait_view(root, isv)
        barang_after_direct = distinct("Nama Barang")
        ok_b = len(barang_after_direct) == 1
        verdict("B: direct _on_barang_row_click filters table (control)",
                "table shows 1 barang", f"barangs={barang_after_direct}",
                not ok_b, severity="P2" if not ok_b else "",
                where="in_selisih_view._on_barang_row_click (handler OK)")
        # toggle off
        isv._on_barang_row_click(barang_name)
        wait_view(root, isv)

        # ---- C: real click on resto scoreboard row (correct pattern) ----
        score_rows = []

        def collect2(w):
            for c in w.winfo_children():
                try:
                    if str(c.cget("cursor")) == "hand2" \
                            and c.winfo_class() == "Frame":
                        score_rows.append(c)
                except tk.TclError:
                    pass
                collect2(c)
        # _skor zone — find via attribute
        zone = getattr(isv, "_skor_zone", None) or getattr(
            isv, "_score_zone", None)
        # fall back: search all frames in view
        zone = zone if zone is not None else isv
        collect2(zone)
        resto_filtered = None
        if score_rows:
            score_rows[0].event_generate("<Button-1>", x=5, y=3)
            pump(root, 0.6)
            wait_view(root, isv)
            restos = distinct("Resto")
            ok_c = len(restos) == 1
            resto_filtered = restos
            # toggle off via direct
            if ok_c:
                isv._on_skor_row_click(list(restos)[0])
                wait_view(root, isv)
        else:
            ok_c = False
        verdict("C: REAL click on resto scoreboard row filters (control "
                "— correct <Button-1> pattern)",
                "table shows 1 resto",
                f"restos={resto_filtered} found_rows={len(score_rows)}",
                not ok_c, severity="P2" if not ok_c else "",
                where="in_selisih_view.py:3215 row.bind('<Button-1>')")

        # ---- D: view mode 📈 Analisa toggle ----
        isv._on_view_mode_change(1)
        pump(root, 0.6)
        wait_view(root, isv)
        analisa_mapped = (isv._analisa_card.winfo_manager() == "pack")
        strip_hidden = (isv._barang_zone.winfo_manager() == "")
        kpi_hidden = (isv.kpi_card.winfo_manager() == "")
        ok_d1 = analisa_mapped and strip_hidden
        isv._on_view_mode_change(0)
        pump(root, 0.6)
        wait_view(root, isv)
        strip_back = (isv._barang_zone.winfo_manager() == "pack")
        kpi_back = (isv.kpi_card.winfo_manager() == "pack")
        ok_d = ok_d1 and strip_back and kpi_back
        verdict("D: 📈 Analisa hides strip/KPI; 📋 restores them",
                "analisa: strip+KPI hidden → back: both packed",
                f"analisa card={analisa_mapped} strip_hidden={strip_hidden} "
                f"kpi_hidden={kpi_hidden} → strip_back={strip_back} "
                f"kpi_back={kpi_back}",
                not ok_d, severity="P2" if not ok_d else "",
                where="in_selisih_view._apply_view_mode / v3.11.9")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
