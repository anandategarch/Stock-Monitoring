"""P7 — Deviasi footer parity: 'n dari N baris' / 'Total |Deviasi|' /
'CEK n' vs ISI TABEL nyata (filter aktif) + pivot mode-switch state.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import make_app, pump, check, summary, wait_view  # noqa: E402

REPO = "/home/z/stock-audit/stock-monitoring-python"
sys.path.insert(0, REPO)

import re
import shutil
import tempfile
from pathlib import Path

REAL_OUT = sys.stdout


def out(*a):
    print(*a, file=REAL_OUT, flush=True)


CEK_LABELS = {
    "Promix 04", "RI Balancing", "Kosong/Non Aktif", "Beda Tanggal",
    "Hitung Manual", "Hilang dari Pencatatan", "Turun Drastis",
    "Naik Drastis", "ACR to BOM", "BOM 0",
}


def num(s):
    s = str(s).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def verify_footer(dv, label):
    st = dv.status_var.get()
    out(f"[{label}] status: {st}")
    m = re.search(r"(\d+) dari (\d+) baris \w+ · Total \|Deviasi\| ([\d\.,\-]+) · CEK (\d+)", st)
    if not m:
        check(f"{label}: format footer 'n dari N · Total |Deviasi| · CEK n'",
              True, False, st)
        return
    n_f, N_f, tot_f, cek_f = (int(m.group(1)), int(m.group(2)),
                              num(m.group(3)), int(m.group(4)))
    tree = dv.tree
    kids = [k for k in tree.get_children("")]
    rows_n = len(kids)
    # hitung ulang dari sel tabel
    tot_t = 0.0
    cek_t = 0
    for k in kids:
        d = num(tree.set(k, "Deviasi"))
        if d is not None:
            tot_t += abs(d)
        cek_first = str(tree.set(k, "CEK")).split(" · ")[0].strip()
        if cek_first in CEK_LABELS:
            cek_t += 1
    out(f"    footer: n={n_f} N={N_f} tot={tot_f} cek={cek_f}")
    out(f"    tabel: rows={rows_n} tot={round(tot_t, 6)} cek={cek_t}")
    check(f"{label}: footer n == jumlah baris tabel", rows_n, n_f)
    check(f"{label}: footer 'Total |Deviasi|' == Σ|Dev| tabel",
          round(tot_t, 4), round(float(tot_f or 0), 4))
    check(f"{label}: footer 'CEK n' == baris ber-label anomali check",
          cek_t, cek_f)
    return n_f, N_f


def main():
    tmp = Path(tempfile.mkdtemp(prefix="a1e_p7_"))
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
    a1 = make_mock_append1()

    # ---------- Deviasi GR: footer parity ------------------------------
    app.notebook.select(app.tab_deviasi_gr)
    pump(root, 0.3)
    dv = app.deviasi_gr_view
    dv.load_data(a1)
    dv.ensure_refreshed()
    wait_view(root, dv)
    pump(root, 0.4)
    r0 = verify_footer(dv, "base GR")

    # aktifkan ⧩ satu barang → n menyusut, N tetap
    dv._col_sel["Nama Barang"] = {"AYAM FILET"}
    dv.header_filters.set_selected("Nama Barang", {"AYAM FILET"})
    dv._refresh(sync=True)
    wait_view(root, dv)
    pump(root, 0.4)
    r1 = verify_footer(dv, "filter 1 barang GR")
    if r0 and r1:
        check("filter aktif: n menyusut, N (total pra-filter) tetap",
              (r1[0] < r0[0], r1[1] == r0[1]), (True, True))
    # pulihkan
    dv._col_sel["Nama Barang"] = None
    dv.header_filters.set_selected("Nama Barang", None)
    dv._refresh(sync=True)
    wait_view(root, dv)

    # ---------- Pivot: mode switch preserve state ----------------------
    pv = app.pivot_view
    app.notebook.select(app.tab_pivot)
    pump(root, 0.3)
    pv.load_data(a1)
    pv.ensure_refreshed()
    wait_view(root, pv)
    pump(root, 0.4)
    pv._on_mode_change(1)          # ke mode TANGGAL dulu
    wait_view(root, pv)
    pump(root, 0.3)
    pv.tgl_start_var.set("-31")
    pv.tgl_end_var.set("10")
    pv._refresh_pivot()
    wait_view(root, pv)
    pump(root, 0.3)
    st_tgl = pv.status_var.get()
    out(f"[pivot tanggal -31..10] {st_tgl}")
    # switch ke resto lalu balik ke tanggal
    pv._on_mode_change(0)
    wait_view(root, pv)
    pump(root, 0.3)
    st_resto = pv.status_var.get()
    out(f"[pivot resto] {st_resto}")
    pv._on_mode_change(1)
    wait_view(root, pv)
    pump(root, 0.3)
    st_back = pv.status_var.get()
    out(f"[pivot tanggal lagi] {st_back}")
    check("pivot: rentang tanggal bertahan lintas mode switch",
          ("-31", "10"), (pv.tgl_start_var.get(), pv.tgl_end_var.get()),
          ok=(pv.tgl_start_var.get() == "-31"
              and pv.tgl_end_var.get() == "10"))
    check("pivot: status tanggal-mode konsisten sebelum/sesudah switch",
          True, st_tgl == st_back, ok=st_tgl == st_back)

    root.destroy()
    shutil.rmtree(tmp, ignore_errors=True)
    n_bad = summary()
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
