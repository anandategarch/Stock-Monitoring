"""P1 — First-run experience & config-path degradation (app shell).

Skenario user Linux/fresh-machine: config.json berisi path Windows
C:\\KERJA\\... (repo asli) → app HARUS tetap terbuka, jujur soal folder,
dan run menghasilkan status non-hijau-polos. Ditambah kasus config.json
TIDAK ADA sama sekali (fresh install).
"""
import os
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import make_app, pump, check, summary, VERDICTS  # noqa: E402

REPO = Path("/home/z/stock-audit/stock-monitoring-python")
sys.path.insert(0, str(REPO))

import shutil
import tempfile  # noqa: E402

REAL_OUT = sys.stdout


def out(*a):
    print(*a, file=REAL_OUT, flush=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="a1e_p1_"))
    shutil.copy(REPO / "config.json", tmp / "config.json")

    import src.ui.app as appmod
    import src.ui.followup as fumod
    import src.ui.deviasi_view as dvmod
    appmod._SETTINGS_PATH = tmp / "settings.json"
    appmod.CONFIG_PATH = tmp / "config.json"
    fumod._BASE = tmp
    dvmod._SETTINGS_BASE = tmp

    # --- patch messagebox: capture, jangan block ------------------------
    dialogs = []
    orig = {}

    def _cap(name):
        def _f(title, msg=None, **kw):
            dialogs.append((name, title, msg))
            return "ok"
        return _f

    for n in ("showwarning", "showerror", "showinfo"):
        orig[n] = getattr(messagebox, n)
        setattr(messagebox, n, _cap(n))

    root, app = make_app()
    pump(root, 0.4)

    out("[A] Info Config dengan path Windows — konten TAMPIBILI")
    items = [app.info_tree.item(i, "values")
             for i in app.info_tree.get_children("")]
    for _top in app.info_tree.get_children(""):
        items += [app.info_tree.item(c, "values")
                  for c in app.info_tree.get_children(_top)]
    sec_rows = [v for v in items if str(v[0]).startswith("==")]
    leaf = [v for v in items if not str(v[0]).startswith("==")]
    check("A1 info tree punya section FOLDERS/SHEETS",
          True, any("FOLDERS" in str(v[0]) for v in sec_rows))
    out(f"    {len(leaf)} entri: {leaf[:2]}")
    check("A2 info tree menampilkan entri folder config (>= 5)",
          True, len(leaf) >= 5, ok=len(leaf) >= 5)
    check("A3 tidak ada baris ERROR saat config valid",
          0, sum(1 for v in items if str(v[0]) == "ERROR"))

    out("[B] preflight NYATA utk config path-Windows di Linux")
    from src.config import Config
    from src.pipeline.helpers import preflight_folders
    missing, counts = preflight_folders(Config(str(tmp / "config.json")))
    out(f"    missing={missing[:3]} counts={counts[:3]}")
    check("B1 folder Windows terdeteksi hilang (jujur, bukan senyap)",
          True, len(missing) >= 3, f"{len(missing)} folder missing")

    out("[C] _show_preflight_result → dialog + statusbar amber")
    app.is_running = True
    app._show_preflight_result(missing, [])
    pump(root, 0.3)
    warn = [d for d in dialogs if d[0] == "showwarning"]
    check("C1 dialog peringatan folder muncul",
          1, len(warn), f"dialogs={[(w[0], w[1]) for w in warn]}")
    if warn:
        body = str(warn[0][2])
        check("C2 dialog menyebut folder yg hilang",
              True, any(k in body for k, _ in missing[:3]), ok=any(
                  k in body for k, _ in missing[:3]))
        check("C3 dialog memberi panduan perbaikan (tab Config)",
              True, "Config" in body, ok="Config" in body)
    sb_text = app.statusbar.dot._full
    sb_color = app.statusbar.dot._color
    out(f"    statusbar: {sb_text!r} color={sb_color!r}")
    check("C4 statusbar AMBER menyebut folder tidak ditemukan",
          True, ("tidak ditemukan" in str(sb_text).lower()
                 and str(sb_color) != str(appmod.C_GREEN)),
          f"text={sb_text!r} color={sb_color!r}")
    app.is_running = False

    out("[D] config.json TIDAK ADA (fresh install)")
    cfg2 = tmp / "kosong"
    cfg2.mkdir()
    old_cfg = appmod.CONFIG_PATH
    appmod.CONFIG_PATH = cfg2 / "config.json"
    app._load_config_to_form()
    pump(root, 0.2)
    items_d = [app.info_tree.item(i, "values")
               for i in app.info_tree.get_children("")]
    err_rows = [v for v in items_d if str(v[0]) == "ERROR"]
    check("D1 info config menampilkan ERROR jujur (bukan kosong diam2)",
          1, len(err_rows), f"{err_rows[:1]}")
    if err_rows:
        check("D2 pesan menyebut lokasi config",
              True, "config.json" in str(err_rows[0][1]),
              ok="config.json" in str(err_rows[0][1]))
    check("D3 RootPath dikosongkan (tidak memasang path mati)",
          "", app.rootpath_var.get())
    appmod.CONFIG_PATH = old_cfg

    out("[E] Status akhir run jujur saat folder hilang (0 baris data)")
    import pandas as pd
    app._pre_missing = list(missing)
    app.append1_df = None
    dialogs.clear()
    app._on_pipeline_done(pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                          {"df": pd.DataFrame(), "kpi": {}, "desc": "",
                           "period": [2026, 1], "month_len": 31,
                           "lalu_month_len": 31},
                          None, False)
    pump(root, 1.2)
    kpi_txt = ""
    try:
        kpi_txt = app.kpi_status.value_var.get() \
            if hasattr(app.kpi_status, "value_var") else ""
    except Exception:
        pass
    st_txt = app.status_var.get()
    sb2 = app.statusbar.dot._full
    out(f"    status_var={st_txt!r} statusbar={sb2!r} kpi={kpi_txt!r}")
    combined = f"{st_txt} | {sb2}"
    check("E1 status akhir BUKAN hijau-polos 'SELESAI' saat folder missing",
          True, ("PERINGATAN" in combined.upper()
                 or "PARSIAL" in combined.upper()
                 or "GAGAL" in combined.upper()
                 or "ERROR" in combined.upper()),
          ok=("PERINGATAN" in combined.upper()
              or "PARSIAL" in combined.upper()
              or "GAGAL" in combined.upper()
              or "ERROR" in combined.upper()))

    for n, f in orig.items():
        setattr(messagebox, n, f)
    root.destroy()
    shutil.rmtree(tmp, ignore_errors=True)
    n_bad = summary()
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
