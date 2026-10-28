"""P2 — Komparasi: double-click popup scoping (resto/barang/tanggal H benar?).
P3 — Laporan (Anomali COM): idem. Popup harus men-scope data ke baris yang
diklik, bukan SEMUA data.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import (make_app, pump, check, summary,  # noqa: E402
                      select_and_wait, wait_view)

REPO = "/home/z/stock-audit/stock-monitoring-python"
sys.path.insert(0, REPO)

import shutil
import tempfile
from pathlib import Path

REAL_OUT = sys.stdout


def out(*a):
    print(*a, file=REAL_OUT, flush=True)


def find_detail_popups(root):
    from src.ui.details_popup import DetailsPopup
    return [w for w in root.winfo_children()
            if isinstance(w, DetailsPopup) and w.winfo_exists()]


class _Ev:
    def __init__(self, tree, iid):
        self.widget = tree
        try:
            b = tree.bbox(iid, column="#3")   # kolom 'Resto' — jauh dari ✓
        except Exception:
            b = None
        if not b:
            b = tree.bbox(iid)
        self.x, self.y = (b[0] + 8, b[1] + b[3] // 2) if b else (300, 20)
        # pastikan BUKAN kolom ✓ (handler ✓ = toggle follow-up)
        from src.ui.widgets import identify_to_column
        _guard = 0
        while (identify_to_column(tree, tree.identify_column(self.x))
               == "✓" and _guard < 20):
            self.x += 60
            _guard += 1


def main():
    tmp = Path(tempfile.mkdtemp(prefix="a1e_p2_"))
    import src.ui.app as appmod
    import src.ui.followup as fumod
    import src.ui.deviasi_view as dvmod
    appmod._SETTINGS_PATH = tmp / "settings.json"
    appmod.CONFIG_PATH = tmp / "config.json"
    shutil.copy(REPO + "/config.json", tmp / "config.json")
    fumod._BASE = tmp
    dvmod._SETTINGS_BASE = tmp

    from test_ui_redesign import (make_mock_append1,
                                  make_mock_deviasi_file)

    root, app = make_app()
    append1 = make_mock_append1()

    # ================= KOMPARASI (mode 0 di tab 📋 Laporan) ========
    app.notebook.select(app.tab_laporan)
    pump(root, 0.3)
    app.show_laporan_mode(0)
    app.komparasi_view.load_data(append1, harga_map={}, konversi_map={})
    pump(root, 0.3)
    if hasattr(app.komparasi_view, "ensure_refreshed"):
        app.komparasi_view.ensure_refreshed()
    wait_view(root, app.komparasi_view)
    kv = app.komparasi_view
    kv._load_paths([make_mock_deviasi_file()], interactive=False)
    wait_view(root, kv)
    pump(root, 0.6)

    tree = kv.tree
    kids = tree.get_children("")
    out(f"komparasi rows: {len(kids)}")
    target = None
    for iid in kids:
        vals = tree.item(iid, "values")
        if vals and str(vals[0]) not in ("", "TOTAL"):
            target = (iid, vals)
            break
    if target is None:
        check("P2 ada baris komparasi utk diklik", True, False, "0 baris")
    else:
        iid, vals = target
        col_ids = [c[0] for c in kv.COLUMNS]
        row = dict(zip(col_ids, vals))
        snap = kv._row_snaps.get(iid) or {}
        out(f"row: {row.get('Nama Barang')} / {row.get('Resto')} "
            f"snap-h={snap.get('h')}")
        kv._on_double_click(_Ev(tree, iid))
        pump(root, 1.0)
        pops = find_detail_popups(root)
        check("P2.1 popup DetailsPopup terbuka", 1, len(pops))
        if pops:
            pop = pops[0]
            out(f"    title: {pop.title()!r}")
            dfp = pop.df
            barang = row.get("Nama Barang")
            resto = row.get("Resto")
            h = snap.get("h")
            exp_rows = append1[
                (append1["Nama Barang"].astype(str) == str(barang))
                & (append1["NAMA RESTO"].astype(str) == str(resto))]
            out(f"    popup rows={len(dfp)} expected-pair-rows~"
                f"{len(exp_rows)} (tgl filter H={h})")
            check("P2.2 popup TER-SCOPE ke barang baris (bukan semua)",
                  True,
                  set(dfp["Nama Barang"].astype(str)) == {str(barang)},
                  ok=set(dfp["Nama Barang"].astype(str)) == {str(barang)})
            rr = set(dfp["NAMA RESTO"].astype(str))
            from src.ui.komparasi_deviasi_view import _norm_resto as _nresto
            resto_norm = _nresto(resto)
            check("P2.3 popup TER-SCOPE ke resto baris (nama app-normalized)",
                  True, rr == {resto_norm}, ok=rr == {resto_norm})
            tg = set(pd := __import__("pandas").to_numeric(
                dfp["Tanggal"], errors="coerce").dropna().astype(int))
            check("P2.4 popup TER-SCOPE ke tanggal H snapshot",
                  True, tg == {int(h)}, f"tanggal popup: {tg} vs H={h}")
            check("P2.5 popup tidak kosong (data nyata utk baris)",
                  True, len(dfp) > 0, f"{len(dfp)} baris")
            pop.destroy()
    pump(root, 0.3)

    # ================= LAPORAN (Anomali COM — mode 1) ==============
    app.show_laporan_mode(1)
    pump(root, 0.3)
    app.laporan_view.load_data(append1)
    if hasattr(app.laporan_view, "ensure_refreshed"):
        app.laporan_view.ensure_refreshed()
    wait_view(root, app.laporan_view)
    lv = app.laporan_view
    pump(root, 0.5)
    ltree = lv.tree
    lk = ltree.get_children("")
    out(f"laporan rows: {len(lk)}")
    tgt2 = None
    for iid in lk:
        vals = ltree.item(iid, "values")
        if vals:
            tgt2 = (iid, vals)
            break
    if tgt2 is None:
        check("P3 ada baris anomali COM utk diklik", True, False, "0 baris")
    else:
        iid, vals = tgt2
        col_ids = [c[0] for c in lv.COLUMNS]
        row = dict(zip(col_ids, vals))
        out(f"row: {row.get('Nama Barang')} / {row.get('Resto')} "
            f"H={lv.tanggal_h}")
        lv._on_double_click(_Ev(ltree, iid))
        pump(root, 1.0)
        pops = find_detail_popups(root)
        check("P3.1 popup terbuka", 1, len(pops))
        if pops:
            pop = pops[0]
            out(f"    title: {pop.title()!r}")
            dfp = pop.df
            import pandas as pd2  # noqa: F401
            import pandas as pd
            barang = row.get("Nama Barang")
            tg = set(pd.to_numeric(
                dfp["Tanggal"], errors="coerce").dropna().astype(int))
            check("P3.2 popup ter-scope barang baris",
                  True,
                  set(dfp["Nama Barang"].astype(str)) == {str(barang)})
            check("P3.3 popup tanggal = H view",
                  True, tg == {int(lv.tanggal_h)},
                  f"tanggal popup: {tg} vs H={lv.tanggal_h}")
            pop.destroy()

    root.destroy()
    shutil.rmtree(tmp, ignore_errors=True)
    n_bad = summary()
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
