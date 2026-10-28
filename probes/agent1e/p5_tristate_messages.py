"""P5 — Tri-state 'seleksi kosong' → pesan jujur di SEMUA view ber-⧩
(fix v3.9.68; verifikasi view yang ditambah belakangan: komparasi,
rincian PO, rekap selisih IN, nominal resto) + kontrol deviasi GR.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import make_app, pump, check, summary, wait_view  # noqa: E402

REPO = "/home/z/stock-audit/stock-monitoring-python"
sys.path.insert(0, REPO)

import shutil
import tempfile

import pandas as pd
from pathlib import Path

REAL_OUT = sys.stdout


def out(*a):
    print(*a, file=REAL_OUT, flush=True)


HONEST = "tidak dipilih pada filter"


def probe_view(root, app, name, tab, view, load, status_get, col):
    app.notebook.select(tab)
    pump(root, 0.3)
    load()
    if hasattr(view, "ensure_refreshed"):
        view.ensure_refreshed()
    wait_view(root, view)
    pump(root, 0.3)
    base = status_get()
    # set seleksi ⧩ KOSONG
    view._col_sel[col] = set()
    if getattr(view, "header_filters", None) is not None:
        try:
            view.header_filters.set_selected(col, set())
        except Exception as e:
            out(f"    set_selected err: {e}")
    try:
        view._refresh(sync=True)
    except TypeError:
        view._refresh()
    wait_view(root, view)
    pump(root, 0.4)
    st = status_get()
    out(f"[{name}] base={base!r}")
    out(f"[{name}] empty-sel={st!r}")
    check(f"{name}: seleksi ⧩ kosong → pesan jujur eksplisit",
          True, HONEST in str(st), ok=HONEST in str(st))
    # pulihkan
    view._col_sel[col] = None
    if getattr(view, "header_filters", None) is not None:
        try:
            view.header_filters.set_selected(col, None)
        except Exception:
            pass
    try:
        view._refresh(sync=True)
    except TypeError:
        view._refresh()
    wait_view(root, view)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="a1e_p5_"))
    import src.ui.app as appmod
    import src.ui.followup as fumod
    import src.ui.deviasi_view as dvmod
    appmod._SETTINGS_PATH = tmp / "settings.json"
    appmod.CONFIG_PATH = tmp / "config.json"
    shutil.copy(REPO + "/config.json", tmp / "config.json")
    fumod._BASE = tmp
    dvmod._SETTINGS_BASE = tmp

    from test_ui_redesign import (make_mock_append1, make_mock_rincian,
                                  make_mock_in_detail, make_mock_rekap_so)
    from src.pipeline.fn_audit import build_audit_from_app
    _rk = make_mock_rekap_so()
    audit_df, audit_kpi, audit_desc = build_audit_from_app(
        _rk, pd.DataFrame(), pd.DataFrame())
    audit_result = {"df": audit_df, "kpi": audit_kpi, "desc": audit_desc}

    root, app = make_app()
    a1 = make_mock_append1()

    probe_view(root, app, "Deviasi GR (kontrol v3.9.68)",
               app.tab_deviasi_gr, app.deviasi_gr_view,
               lambda: app.deviasi_gr_view.load_data(a1),
               lambda: app.deviasi_gr_view.status_var.get(),
               "Nama Barang")

    probe_view(root, app, "Komparasi (mode di tab Laporan)",
               app.tab_laporan, app.komparasi_view,
               lambda: (app.show_laporan_mode(0),
                        app.komparasi_view.load_data(
                            a1, harga_map={}, konversi_map={})),
               lambda: app.komparasi_view.status_var_label.get(),
               "Nama Barang")

    probe_view(root, app, "Rincian PO",
               app.tab_rincian, app.rincian_view,
               lambda: app.rincian_view.load_data(make_mock_rincian()),
               lambda: app.rincian_view.status_var.get(),
               "Nama Barang")

    probe_view(root, app, "Rekap Selisih IN",
               app.tab_in_selisih, app.in_selisih_view,
               lambda: app.in_selisih_view.load_data(
                   a1, make_mock_in_detail(),
                   audit_result=audit_result),
               lambda: app.in_selisih_view.status_var.get(),
               "Nama Barang")

    # Nominal resto: col 'Resto'
    probe_view(root, app, "Nominal Deviasi Per-Resto",
               app.tab_nominal_resto, app.nominal_resto_view,
               lambda: app.nominal_resto_view.load_data(
                   a1, harga_map={}, konversi_map={}),
               lambda: app.nominal_resto_view.status_var_label.get(),
               "Resto")

    root.destroy()
    shutil.rmtree(tmp, ignore_errors=True)
    n_bad = summary()
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
