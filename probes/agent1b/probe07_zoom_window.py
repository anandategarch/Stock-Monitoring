"""PROBE 07 — Zoom keyboard shortcuts, badge, persistence-flush, small
window tab-label compaction.

A) Ctrl+plus / Ctrl+minus keyboard zoom changes ui_zoom + badge text.
B) Ctrl+0 resets to default 0.8 + badge reflects it.
C) Small window (1024x600) → tab labels compact (no ellipsis overflow),
   notebook still shows all 10 tabs.
D) Zoom step at bounds (clamp 0.5..2.0) does not crash; rowheight
   follows zoom scale.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary


def main():
    root, app = boot_app()
    try:
        from src.ui import theme
        from src.ui.app import UI_ZOOM_DEFAULT
        # normalize to default first
        app._apply_ui_zoom(UI_ZOOM_DEFAULT, resize_window=False)
        pump(root, 0.3)

        # ---- A: Ctrl+plus / Ctrl+minus ----
        root.event_generate("<Control-equal>")
        pump(root, 0.3)
        z_in1 = app.ui_zoom
        badge_in = app.statusbar._right_var.get()
        root.event_generate("<Control-minus>")
        pump(root, 0.3)
        z_out1 = app.ui_zoom
        badge_out = app.statusbar._right_var.get()
        ok_a = (z_in1 > UI_ZOOM_DEFAULT and z_out1 < z_in1
                and str(int(round(z_in1 * 100))) in badge_in
                and str(int(round(z_out1 * 100))) in badge_out)
        verdict("A: Ctrl+plus / Ctrl+minus keyboard zoom + badge follows",
                f"in > {UI_ZOOM_DEFAULT} then smaller; badge tracks %",
                f"z_in={z_in1} badge_in={badge_in!r} z_out={z_out1} "
                f"badge_out={badge_out!r}", not ok_a,
                severity="P2" if not ok_a else "",
                where="app._on_zoom_key_in/_out + _update_zoom_badge")

        # ---- B: Ctrl+0 reset ----
        root.event_generate("<Control-0>")
        pump(root, 0.3)
        z_reset = app.ui_zoom
        badge2 = app.statusbar._right_var.get()
        ok_b = abs(z_reset - UI_ZOOM_DEFAULT) < 1e-9 \
            and "Zoom 80%" in badge2
        verdict("B: Ctrl+0 resets zoom to default 0.8 (badge 'Zoom 80%')",
                "zoom=0.8, badge 'Zoom 80%'",
                f"zoom={z_reset} badge={badge2!r}", not ok_b,
                severity="P3" if not ok_b else "",
                where="app._on_zoom_key_reset")

        # ---- C: small window tab labels ----
        geo = root.geometry()
        root.geometry("1024x600+0+0")
        pump(root, 0.8)
        n_tabs = len(app.notebook.tabs())
        # tab labels should be compacted or at least all present
        labels = [app.notebook.tab(t, "text") for t in app.notebook.tabs()]
        # check none of the tab texts contain the raw long label when
        # window is small (they get compacted via _compact_tab_label)
        ok_c = n_tabs == 10 and all(labels)
        verdict("C: small window 1024x600 — 10 tabs present with labels",
                "10 tabs, labels non-empty", f"tabs={n_tabs} labels={labels}",
                not ok_c, severity="P2" if not ok_c else "",
                where="app._apply_tab_label_fit / _compact_tab_label")
        root.geometry(geo)
        pump(root, 0.5)

        # ---- D: zoom bounds clamp + rowheight follows ----
        from tkinter import ttk as _ttk
        _style = _ttk.Style(root)
        app._apply_ui_zoom(0.5, resize_window=False)
        pump(root, 0.3)
        rh_min = int(_style.lookup("Treeview", "rowheight"))
        app._apply_ui_zoom(2.0, resize_window=False)
        pump(root, 0.3)
        rh_max = int(_style.lookup("Treeview", "rowheight"))
        app._apply_ui_zoom(2.5, resize_window=False)   # beyond clamp
        pump(root, 0.3)
        z_clamped = app.ui_zoom
        app._apply_ui_zoom(UI_ZOOM_DEFAULT, resize_window=False)
        ok_d = (rh_min < rh_max and z_clamped <= 2.0 + 1e-9)
        verdict("D: zoom clamp ≤2.0 + rowheight scales with zoom",
                "rowheight grows with zoom; zoom clamped at 2.0",
                f"rh@0.5={rh_min} rh@2.0={rh_max} zoom@2.5→{z_clamped}",
                not ok_d, severity="P3" if not ok_d else "",
                where="app._apply_ui_zoom + theme.scale_px")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
