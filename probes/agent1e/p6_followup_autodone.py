"""P6 — Follow-up UX: toggle ✓ optimistic, auto-done v3.11.6 saat deviasi
hilang pada refresh, notes tidak hilang, badge/status menyusul.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import make_app, pump, check, summary, wait_view  # noqa: E402

REPO = "/home/z/stock-audit/stock-monitoring-python"
sys.path.insert(0, REPO)

import shutil
import tempfile
from pathlib import Path

import pandas as pd

REAL_OUT = sys.stdout


def out(*a):
    print(*a, file=REAL_OUT, flush=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="a1e_p6_"))
    import src.ui.app as appmod
    import src.ui.followup as fumod
    import src.ui.deviasi_view as dvmod
    appmod._SETTINGS_PATH = tmp / "settings.json"
    appmod.CONFIG_PATH = tmp / "config.json"
    shutil.copy(REPO + "/config.json", tmp / "config.json")
    fumod._BASE = tmp
    dvmod._SETTINGS_BASE = tmp

    from test_ui_redesign import make_mock_append1

    root, app = make_app()
    dv = app.deviasi_gr_view
    a1 = make_mock_append1()
    app.notebook.select(app.tab_deviasi_gr)
    pump(root, 0.3)
    dv.load_data(a1)
    dv.ensure_refreshed()
    wait_view(root, dv)
    pump(root, 0.5)

    tree = dv.tree
    kids = [k for k in tree.get_children("")][:1]
    iid = kids[0]
    vals = tree.item(iid, "values")
    snap = dv._row_snaps.get(iid) or {}
    out(f"row: {snap.get('barang')} / {snap.get('resto')} "
        f"dev={snap.get('deviasi')} h={snap.get('h')} vals0={vals[0]!r}")

    # --- (1) toggle ✓ via klik sel kolom ✓ (jalur produksi) ------------
    store = app.followup_store
    n0 = len(store.rows)
    bb = tree.bbox(iid)
    ev = type("E", (), {})()
    ev.widget = tree
    ev.x, ev.y = bb[0] + 6, bb[1] + bb[3] // 2
    dv._on_tree_click(ev)
    pump(root, 0.4)
    n1 = len(store.rows)
    check("F1 toggle ✓ → entry store LANGSUNG (optimistic)",
          n0 + 1, n1)
    check("F2 sel ✓ baris berubah jadi ☑",
          "☑", str(tree.set(iid, "✓")))
    fps = list(store.rows)
    fp = fps[-1]
    snap_stored = store.rows[fp]
    check("F3 snapshot entry utuh (barang/resto/deviasi/h utk Follow Up)",
          (snap.get("barang"), snap.get("resto")),
          (snap_stored.get("barang"), snap_stored.get("resto")))

    # --- (2) un-toggle lalu re-toggle: resolved bersih -----------------
    dv._on_tree_click(ev)
    pump(root, 0.3)
    check("F4 un-✓ → entry dihapus + resolved ikut bersih",
          (n0, fp not in store.resolved), (len(store.rows), True))
    dv._on_tree_click(ev)
    pump(root, 0.3)
    fps = list(store.rows)
    fp = fps[-1] if store.rows else None

    # --- (3) auto-done: deviasi HILANG di data revisi ------------------
    # revisi: buang SEMUA baris 3.DEVIASI pasangan tsb + pasangan tetap ada
    resto, barang = snap.get("resto"), snap.get("barang")
    mask = ~((a1["Nama Barang"].astype(str) == str(barang))
             & (a1["NAMA RESTO"].astype(str) == str(resto))
             & (a1["JENIS"].astype(str) == "3.DEVIASI"))
    revised = a1[mask].copy()
    done = store.auto_resolve_pending(revised)
    out(f"auto_resolve → {done}")
    check("F5 deviasi hilang → baris AUTO-DONE",
          1, len(done))
    res = store.resolved.get(fp) or {}
    check("F6 entri resolved ber-PIC AUTO + Cek FU AUTO-DONE",
          ("AUTO", True),
          (res.get("PIC"), "AUTO-DONE" in str(res.get("Cek FU", ""))),
          ok=(res.get("PIC") == "AUTO"
              and "AUTO-DONE" in str(res.get("Cek FU", ""))))
    check("F7 entry rows TETAP ADA (riwayat/notes tidak lenyap)",
          True, fp in store.rows, ok=fp in store.rows)

    # --- (4) manual-resolved (PIC user) TIDAK ditimpa auto-done --------
    # pasangan lain: tandai ✓ lalu resolve manual dgn PIC 'Budi'
    kids2 = [k for k in tree.get_children("")]
    iid2 = None
    for k in kids2:
        s2 = dv._row_snaps.get(k) or {}
        if (s2.get("barang"), s2.get("resto")) != (barang, resto):
            iid2 = k
            break
    if iid2 is None:
        check("F8 pasangan kedua tersedia", True, False, "-")
    else:
        bb2 = tree.bbox(iid2)
        ev2 = type("E", (), {})()
        ev2.widget = tree
        ev2.x, ev2.y = bb2[0] + 6, bb2[1] + bb2[3] // 2
        dv._on_tree_click(ev2)
        pump(root, 0.3)
        fp2 = [f for f in store.rows if f != fp][-1]
        store.resolved[fp2] = {"PIC": "Budi", "Cek FU": "OK manual",
                               "ts": "2026", "auto": False}
        done2 = store.auto_resolve_pending(a1)   # deviasi MASIH ada
        res2 = store.resolved.get(fp2) or {}
        check("F8 entry manual-resolved tidak disentuh auto-done",
              ("Budi", 0), (res2.get("PIC"), len(done2)),
              ok=(res2.get("PIC") == "Budi" and len(done2) == 0))

    # --- (5) deviasi MASIH ADA (3.DEVIASI != 0) → tetap menunggu -----
    # entri pending baru via toggle() dgn snapshot sintetis (asal DEVIASI GR)
    fp_live = "probe-live-fp"
    store.rows[fp_live] = {
        "asal": "DEVIASI GR", "resto": "R1", "barang": "BRG LIVE",
        "satuan": "GR", "aktif": "AKTIF", "h": 25,
        "so": 100.0, "sistem": 90.0, "deviasi": 10.0, "cek": "",
        "so_m2": 0.0, "so_m1": 0.0, "so_p1": 0.0, "so_p2": 0.0,
        "loss_bom": 0.0, "fp": fp_live, "added_at": "2026",
    }
    live_df = pd.DataFrame([
        {"Nama Barang": "BRG LIVE", "JENIS": "1.SO", "NAMA RESTO": "R1",
         "Tanggal": 25, "NILAI": 100.0},
        {"Nama Barang": "BRG LIVE", "JENIS": "3.DEVIASI",
         "NAMA RESTO": "R1", "Tanggal": 25, "NILAI": 10.0},
    ])
    done3 = store.auto_resolve_pending(live_df)
    check("F9 deviasi masih != 0 -> TETAP menunggu (0 auto-done)",
          0, len(done3))
    check("F9b entri masih pending (tak masuk resolved)",
          True, fp_live not in store.resolved,
          ok=fp_live not in store.resolved)

    # --- (6) status KPI auto-done via jalur app ------------------------
    # pasangan HILANG total dari data revisi → auto-done → kpi menyusul
    gone_df = pd.DataFrame([
        {"Nama Barang": "BARANG LAIN", "JENIS": "1.SO",
         "NAMA RESTO": "R2", "Tanggal": 25, "NILAI": 5.0},
    ])
    app._auto_resolve_followup(gone_df)
    pump(root, 0.4)
    kpi_val = app.kpi_status._value_var.get()
    kpi_sub = app.kpi_status._sub_var.get()
    out(f"kpi_status: {kpi_val!r} / {kpi_sub!r}")
    check("F10 KPI status menyebut auto-done follow-up",
          True, "auto-done" in kpi_sub.lower(),
          ok="auto-done" in kpi_sub.lower())

    # --- (7) followup_view menampilkan status Selesai -------------------
    app.notebook.select(app.tab_followup)
    pump(root, 0.6)
    fv = app.followup_view
    ftree = fv.tree
    fkids = ftree.get_children("")
    stat_texts = []
    for k in fkids:
        try:
            stat_texts.append(str(ftree.set(k, "Status TL")))
        except Exception:
            pass
    out(f"followup rows: {len(fkids)} statusTL: {stat_texts}")
    check("F11 tab Follow Up memunculkan baris auto-done dgn Status Selesai",
          True, any("Selesai" in t for t in stat_texts),
          ok=any("Selesai" in t for t in stat_texts))

    root.destroy()
    shutil.rmtree(tmp, ignore_errors=True)
    n_bad = summary()
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
