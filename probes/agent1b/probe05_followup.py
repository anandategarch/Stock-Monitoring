"""PROBE 05 — ☑ Follow Up + auto-resolve + export button state sync.

A) ✓ in Deviasi GR → followup row appears in ☑ tab; badge count on tab.
B) Toggle row out via ✓ in followup table → row removed incrementally,
   store shrinks, badge syncs.
C) AUTO-RESOLVE (v3.11.6): pending entry whose pair no longer deviates
   in new append1 → resolved AUTO + 'AUTO-DONE' note + Status TL Selesai.
D) _sync_export_buttons: no data → export disabled; data present →
   enabled (persis guard _export_excel).
E) Clear-all asks confirmation (destructive action guard).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary

import pandas as pd

COLS = ["Nama Barang", "JENIS", "NAMA RESTO", "Tanggal", "NILAI",
        "SATUAN", "AKTIF/NON", "KATEGORI", "SOURCE KIRIMAN",
        "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"]


def r(barang, jenis, resto, tgl, nilai, satuan):
    return dict(zip(COLS, [barang, jenis, resto, tgl, nilai, satuan,
                           "AKTIF", "COM DEVIASI - RESTO", "GUDANG",
                           None, None, None]))


def craft_df(dev_value=30.0):
    rows = [
        r("AYAM FILET", "SALDO AWAL", "MLGPAR", 1, 100.0, "GR"),
    ]
    for t in range(1, 8):
        rows.append(r("AYAM FILET", "1.SO", "MLGPAR", t, 100.0, "GR"))
        rows.append(r("AYAM FILET", "2.SALDO AKHIR", "MLGPAR", t,
                      100.0 - dev_value if t == 7 else 100.0, "GR"))
    rows.append(r("AYAM FILET", "9.ACR", "MLGPAR", 2, 5.0, "GR"))
    return pd.DataFrame(rows)


def main():
    root, app = boot_app()
    try:
        from test_ui_redesign import wait_view
        from src.ui.followup import CHECK_ON
        app.followup_store.clear()
        df = craft_df()
        app.deviasi_gr_view.load_data(df)
        app.notebook.select(app.tab_deviasi_gr)
        pump(root, 0.2)
        app.deviasi_gr_view.ensure_refreshed()
        wait_view(root, app.deviasi_gr_view)
        tree = app.deviasi_gr_view.tree

        # ---- A: ✓ → followup row ----
        first = tree.get_children("")[0]
        bbox = tree.bbox(first, column="✓")
        class Ev:
            pass
        ev = Ev()
        ev.widget = tree
        ev.x, ev.y = bbox[0] + 3, bbox[1] + bbox[3] // 2
        app.deviasi_gr_view._on_tree_click(ev)
        pump(root, 0.3)
        n_store = len(app.followup_store)
        app.notebook.select(app.tab_followup)
        pump(root, 0.5)
        ft = app.followup_view.tree
        fu_rows = ft.get_children("")
        badge = app.notebook.tab(app.tab_followup, "text")
        ok_a = n_store == 1 and len(fu_rows) == 1 and "1" in badge
        verdict("A: ✓ adds row to ☑ Follow Up + tab badge",
                "store 1 · 1 row · badge '☑ (1)'",
                f"store={n_store} rows={len(fu_rows)} badge={badge!r}",
                not ok_a, severity="P1" if not ok_a else "",
                where="deviasi_view ✓ → FollowUpStore → followup_view render")

        # ---- B: toggle out via ✓ in followup table ----
        if len(fu_rows):
            fu_first = fu_rows[0]
            bbox = ft.bbox(fu_first, column="✓")
            ev.widget = ft
            ev.x, ev.y = bbox[0] + 3, bbox[1] + bbox[3] // 2
            app.followup_view._on_tree_click(ev)
            pump(root, 0.5)   # debounce flush 200ms
            root.update()
        n_after = len(app.followup_store)
        rows_after = len(ft.get_children(""))
        badge_after = app.notebook.tab(app.tab_followup, "text")
        ok_b = n_after == 0 and rows_after == 0
        verdict("B: ✓ in followup table removes row (incremental) + badge",
                "store 0 · 0 rows", f"store={n_after} rows={rows_after} "
                f"badge={badge_after!r}",
                not ok_b, severity="P2" if not ok_b else "",
                where="followup_view._toggle_row_incremental")

        # ---- C: AUTO-RESOLVE (v3.11.6) ----
        # re-add entry, then feed new data WITHOUT the deviation
        app.notebook.select(app.tab_deviasi_gr)
        pump(root, 0.2)
        first = tree.get_children("")[0]
        bbox = tree.bbox(first, column="✓")
        ev.widget = tree
        ev.x, ev.y = bbox[0] + 3, bbox[1] + bbox[3] // 2
        app.deviasi_gr_view._on_tree_click(ev)
        pump(root, 0.3)
        assert len(app.followup_store) == 1, "re-add failed"
        # new data: no deviation (saldo == SO)
        df2 = craft_df(dev_value=0.0)
        app._auto_resolve_followup(df2)
        pump(root, 0.3)
        resolved = app.followup_store.resolved
        store_rows = list(app.followup_store.rows.values())
        auto_done = [v for v in resolved.values()
                     if any("AUTO-DONE" in str(x) for x in v.values())]
        ok_c = len(auto_done) == 1
        app.notebook.select(app.tab_followup)
        pump(root, 0.5)
        # status TL of that row
        fu_status = None
        for i in ft.get_children(""):
            vals = ft.item(i, "values")
            fu_status = vals
        ok_c = ok_c and fu_status and "Selesai" in str(fu_status) \
            and "AUTO-DONE" in str(fu_status)
        verdict("C: auto-resolve marks entry AUTO-DONE (v3.11.6)",
                "1 resolved entry with AUTO-DONE note + Status TL Selesai",
                f"resolved={len(resolved)} auto_done={len(auto_done)} "
                f"row={fu_status}",
                not ok_c, severity="P2" if not ok_c else "",
                where="app._auto_resolve_followup → store.auto_resolve_pending")

        # ---- D: export button state sync (app-level datasets — real flow
        # sets app.append1_df via _on_pipeline_done) ----
        app.notebook.select(app.tab_deviasi_gr)
        pump(root, 0.2)
        app.append1_df = df          # simulate real pipeline flow
        app._sync_export_buttons()
        st_with = str(app.btn_export.cget("state"))
        # simulate no-data: fresh sub-app? cheaper: temporarily null data
        _saved = (app.append1_df, app.rincian_po_df,
                  app.in_detail_df, app.audit_result)
        app.append1_df = None
        app.rincian_po_df = None
        app.in_detail_df = None
        app.audit_result = None
        app._sync_export_buttons()
        st_without = str(app.btn_export.cget("state"))
        (app.append1_df, app.rincian_po_df,
         app.in_detail_df, app.audit_result) = _saved
        app._sync_export_buttons()
        ok_d = (st_with == "normal" and st_without == "disabled")
        verdict("D: export button disabled when no data (state sync)",
                "normal with data → disabled without",
                f"with={st_with!r} without={st_without!r}", not ok_d,
                severity="P2" if not ok_d else "",
                where="app._sync_export_buttons")

        # ---- E: clear-all confirmation ----
        import tkinter.messagebox as mb
        asked = {}
        orig_ask = mb.askyesno

        def fake_ask(title, msg=None, **kw):
            asked["title"] = title
            asked["msg"] = msg
            return False  # cancel

        mb.askyesno = fake_ask
        try:
            app.followup_view._on_clear()
        finally:
            mb.askyesno = orig_ask
        ok_e = bool(asked) and len(app.followup_store) == 1  # cancelled
        verdict("E: Clear-all asks confirmation (cancel keeps rows)",
                "askyesno dialog + rows intact on cancel",
                f"asked={bool(asked)} store={len(app.followup_store)}",
                not ok_e, severity="P2" if not ok_e else "",
                where="followup_view._on_clear")
        app.followup_store.clear()
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
