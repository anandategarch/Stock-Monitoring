"""PROBE 08 — ⚙️ Config tab & refresh dialog degrade on Linux (config
points to C:\\KERJA\\ Windows paths).

A) Config form loads RootPath from config.json without crash.
B) Kategori manual section (v3.11.8) placeholder without 42.17 data.
C) Dev bulanan card (v3.11.9): folder entry + Jumlah File spinbox exist;
   _dev_bulanan_cfg returns None on missing folder (feature off, honest).
D) RefreshSourcesDialog lists MISSING folders as 'Hilang' rows (no
   crash, no silent skip).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/probes/agent1b")
from harness import boot_app, pump, verdict, summary


def main():
    root, app = boot_app()
    try:
        # ---- A: config form populated ----
        rootval = str(app.root_path_var.get()) if hasattr(
            app, "root_path_var") else None
        if rootval is None:
            # find entry by other name
            for attr in ("root_var", "rootpath_var", "entry_root"):
                if hasattr(app, attr):
                    rootval = str(getattr(app, attr).get())
                    break
        ok_a = bool(rootval) and (":" in rootval or "/" in rootval)
        verdict("A: Config form RootPath populated (no crash on Linux)",
                "non-empty path", f"root={rootval!r}", not ok_a,
                severity="P1" if not ok_a else "",
                where="app._load_config_to_form")

        # ---- B: kategori manual placeholder ----
        # find labels in config tab mentioning 42.17 placeholder
        def all_texts(w, out):
            try:
                for c in w.winfo_children():
                    if c.winfo_class() == "Label":
                        t = c.cget("text")
                        if isinstance(t, str):
                            out.append(t)
                    all_texts(c, out)
            except tk_TclError:
                pass
        import tkinter as tk
        global tk_TclError
        tk_TclError = tk.TclError
        texts = []
        all_texts(app.tab_config, texts)
        has_placeholder = any("42.17" in t for t in texts)
        ok_b = has_placeholder
        verdict("B: kategori manual section renders (42.17 mentioned) "
                "without data",
                "'belum ada data 42.17' placeholder present",
                f"found={[t for t in texts if '42.17' in t][:2]}", not ok_b,
                severity="P3" if not ok_b else "",
                where="app._refresh_kategori_manual_card / _kat_4217")

        # ---- C: dev bulanan card ----
        spin = getattr(app, "_devbulanan_jumlah_spin", None) or getattr(
            app, "_dev_bulanan_jumlah", None)
        # find spinbox widgets in config tab
        spins = []

        def find_spin(w):
            try:
                for c in w.winfo_children():
                    if c.winfo_class() == "TSpinbox":
                        spins.append(c)
                    find_spin(c)
            except tk.TclError:
                pass
        find_spin(app.tab_config)
        cfg_res = app._dev_bulanan_cfg(None)
        ok_c = len(spins) >= 1 and cfg_res is None
        verdict("C: Dev bulanan card spinbox present + cfg None on "
                "missing folder",
                "≥1 TSpinbox + _dev_bulanan_cfg(None) → None",
                f"spinboxes={len(spins)} cfg={cfg_res}", not ok_c,
                severity="P3" if not ok_c else "",
                where="app._build_config_tab dev bulanan card")

        # ---- D: refresh dialog degrade ----
        from src.ui.refresh_sources import RefreshSourcesDialog
        from src.config import Config
        cfg = Config()
        dlg = RefreshSourcesDialog(root, cfg, last_run_at=None,
                                   on_refresh=None)
        pump(root, 0.5)
        # inspect entries
        entries = dlg._entries
        missing = [e for e in entries if e.get("missing")]
        present = [e for e in entries if not e.get("missing")]
        # tree rows
        rows = dlg.tree.get_children("")
        ok_d = len(rows) >= 1 and len(missing) >= 1
        verdict("D: Refresh dialog lists missing Windows-path folders as "
                "'Hilang' rows (graceful)",
                "≥1 row, missing folders listed 'Hilang'",
                f"rows={len(rows)} missing={len(missing)} "
                f"present={len(present)} "
                f"sample={[(e.get('label'), e.get('missing')) for e in entries[:4]]}",
                not ok_d, severity="P2" if not ok_d else "",
                where="refresh_sources._scan_sources (FIX 2f-06)")
        dlg.destroy()
        pump(root, 0.2)
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
    summary()
