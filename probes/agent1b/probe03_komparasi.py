"""PROBE 03 — Komparasi ⚖ file load + cross-tab 'Dev. Bulan Lalu' staleness.

A) Load mock deviasi file via real path (komparasi._load_paths, all weeks
   ON) → main table rows show MATCH/SELISIH statuses and formatted values.
B) CROSS-TAB: after file load, tab 📦 Deviasi GR 'Dev. Bulan Lalu' column
   must refresh from the file (on_lalu_file_changed via app
   _on_dev_file_loaded) — GULA PASIR MLGPAR should show 150 (file WEEK 4
   at H=25); before load it showed '—'.
C) Sort komparasi 'GR Saat Ini' desc numeric.
D) Status cell tags configured (st_match/st_diff colors exist).
E) Drill-down popup opens with app-side names (DetailsPopup).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary


def main():
    root, app = boot_app()
    try:
        # neutralize AUTO-LOAD last file (state pollution from earlier
        # runs — komparasi_last.json may point at the mock file)
        app.komparasi_view._auto_loaded = True
        from test_ui_redesign import (
            make_mock_komparasi_df, make_mock_deviasi_file, wait_view)
        det = make_mock_komparasi_df()
        app.komparasi_view.load_data(det)
        # load_data RESETS the auto-load guard — set it AFTER load_data,
        # BEFORE ensure_refreshed (which triggers maybe_auto_load_last)
        app.komparasi_view._auto_loaded = True
        app.notebook.select(app.tab_komparasi) if hasattr(app, "tab_komparasi") else None
        # komparasi lives under tab_laporan with mode selector
        pump(root, 0.3)
        app.komparasi_view.ensure_refreshed()
        wait_view(root, app.komparasi_view)

        # pre-load state of deviasi GR 'Dev. Bulan Lalu'
        app.deviasi_gr_view.load_data(det)
        app.notebook.select(app.tab_deviasi_gr)
        pump(root, 0.2)
        app.deviasi_gr_view.ensure_refreshed()
        wait_view(root, app.deviasi_gr_view)

        def dev_lalu_map():
            out = {}
            for i in app.deviasi_gr_view.tree.get_children(""):
                v = app.deviasi_gr_view.tree.item(i, "values")
                out[(v[1], v[2])] = app.deviasi_gr_view.tree.set(
                    i, "Dev. Bulan Lalu")
            return out

        pre = dev_lalu_map()
        pre_gula = pre.get(("MLGPAR", "GULA PASIR"))

        # ---- A: load file via real path (all weeks) ----
        app.komparasi_view._show_all_weeks.set(True)
        pump(root, 0.1)
        xlsx = make_mock_deviasi_file()
        app.komparasi_view._load_paths([xlsx], interactive=False)
        wait_view(root, app.komparasi_view)
        pump(root, 0.3)

        kt = app.komparasi_view.tree
        rows = []
        for i in kt.get_children(""):
            rows.append({
                "resto": kt.set(i, "Resto"),
                "barang": kt.set(i, "Nama Barang"),
                "dev_lalu": kt.set(i, "DEV Lalu"),
                "gr": kt.set(i, "GR Saat Ini"),
                "status": kt.set(i, "Status"),
            })
        n_match = sum(1 for r in rows if r["status"] == "MATCH")
        n_diff = sum(1 for r in rows if r["status"] == "SELISIH")
        # oracle: AYAM MLGPAR W1 49=MATCH, AYAM SBYKET W1 74 vs 49=SELISIH,
        # AYAM MLGPAR W2 113=MATCH, GULA MLGPAR W4 150=MATCH, XYZZZ excluded,
        # BARANG TAK ADA excluded, WEEK 5 = WEEK 5 beyond H? (all weeks ON →
        # included only if H filter inactive) — assert ≥3 MATCH and 1 SELISIH
        ok_a = n_match >= 3 and n_diff == 1
        verdict("A: komparasi file load → MATCH/SELISIH rows (status kolom)",
                "≥3 MATCH + 1 SELISIH", f"MATCH={n_match} SELISIH={n_diff} "
                f"rows={[(r['barang'], r['resto'], r['status']) for r in rows]}",
                not ok_a, severity="P1" if not ok_a else "",
                where="komparasi_deviasi_view._load_paths/_refresh")
        sel_rows = [r for r in rows if r["status"] == "SELISIH"]
        ok_a2 = (not sel_rows
                 or (sel_rows[0]["dev_lalu"] == "74"
                     and sel_rows[0]["gr"] == "49"))
        verdict("A2: SELISIH row DEV Lalu=74 vs GR Saat Ini=49 (formatted)",
                "74 / 49", str((sel_rows[0]["dev_lalu"], sel_rows[0]["gr"]))
                if sel_rows else "no row", not ok_a2,
                severity="P2" if not ok_a2 else "",
                where="komparasi _fmt_num columns")

        # ---- B: cross-tab Dev. Bulan Lalu refresh ----
        app.notebook.select(app.tab_deviasi_gr)
        pump(root, 0.4)
        app.deviasi_gr_view.ensure_refreshed()
        wait_view(root, app.deviasi_gr_view)
        post = dev_lalu_map()
        post_gula = post.get(("MLGPAR", "GULA PASIR"))
        ok_b = (pre_gula in ("—", "-", "") and post_gula == "150")
        verdict("B: Deviasi GR 'Dev. Bulan Lalu' refreshed after file load "
                "(GULA PASIR MLGPAR → 150)",
                "'—' before → '150' after", f"before={pre_gula!r} "
                f"after={post_gula!r} all={post}",
                not ok_b, severity="P1" if not ok_b else "",
                where="app._on_dev_file_loaded → deviasi_view.on_lalu_file_changed")

        # ---- C: sort GR Saat Ini desc ----
        app.notebook.select(app.tab_laporan)
        app.show_laporan_mode(0)  # komparasi mode
        pump(root, 0.3)
        app.komparasi_view._sort_by("GR Saat Ini", reverse=True)
        pump(root, 0.5)
        def num(s):
            s = str(s)
            if s in ("-", "", "—"):
                return 0.0
            if s.startswith("(") and s.endswith(")"):
                return -float(s[1:-1].replace(".", "").replace(",", "."))
            return float(s.replace(".", "").replace(",", "."))
        grs = [num(kt.set(i, "GR Saat Ini")) for i in kt.get_children("")]
        ok_c = grs == sorted(grs, reverse=True)
        verdict("C: komparasi sort 'GR Saat Ini' desc numeric",
                str(sorted(grs, reverse=True)), str(grs), not ok_c,
                severity="P2" if not ok_c else "",
                where="komparasi _sort_by parse")

        # ---- D: status tag colors ----
        def _tagfg(tree, tag):
            try:
                cfg = tree.tag_configure(tag)
            except Exception:
                return None
            if isinstance(cfg, dict):
                return cfg.get("foreground")
            return None
        fg_match = _tagfg(kt, "st_match")
        fg_diff = _tagfg(kt, "st_diff")
        has_tags = bool(fg_match) and bool(fg_diff)
        verdict("D: status tags st_match/st_diff configured",
                "both tags have foreground color",
                f"st_match.fg={fg_match} st_diff.fg={fg_diff}", not has_tags,
                severity="P3" if not has_tags else "",
                where="komparasi _setup_tags")

        # ---- E: drill-down popup ----
        target = kt.get_children("")[0] if kt.get_children("") else None
        if target:
            class Ev:
                pass
            ev = Ev()
            ev.widget = kt
            bbox = kt.bbox(target, column="Nama Barang")
            ev.x, ev.y = bbox[0] + 4, bbox[1] + bbox[3] // 2
            app.komparasi_view._on_double_click(ev)
            pump(root, 0.4)
            from src.ui.details_popup import DetailsPopup
            pops = [w for w in root.winfo_children()
                    if isinstance(w, DetailsPopup) and w.winfo_exists()]
            ok_e = bool(pops)
            if pops:
                pops[-1].destroy()
            verdict("E: komparasi double-click opens DetailsPopup",
                    "popup opens", f"popups={len(pops)}", not ok_e,
                    severity="P2" if not ok_e else "",
                    where="komparasi _on_double_click → show_details_popup")
        # cleanup
        app.komparasi_view._close_file() if hasattr(
            app.komparasi_view, "_close_file") else None
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
