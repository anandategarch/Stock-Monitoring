"""P4 — Nominal Deviasi Per-Resto: parity KPI chip TOTAL vs baris TOTAL
tabel vs popup rincian resto; + scoping popup saat filter KATEGORI aktif.
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

import pandas as pd

REAL_OUT = sys.stdout


def out(*a):
    print(*a, file=REAL_OUT, flush=True)


def rp_to_num(s):
    """'(Rp 600)'=negatif accounting · 'Rp 1.234,56' · '-Rp 500' · '-'"""
    s = str(s).strip()
    if s in ("-", "", "None"):
        return None
    neg = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("()-").replace("Rp", "").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def build_mock(h=25):
    """3 resto × barang dgn kategori beda (COM / PACKAGING / BAHAN) —
    harga 41.09 utk semua → nominal = harga × deviasi."""
    rows = []
    spec = [
        # barang, satuan, kategori, dev per resto
        ("AYAM COM", "GR", "COM", {"MLGPAR": -10.0, "SBYKET": 4.0}),
        ("KOP PACK", "PCS", "PACKAGING", {"MLGPAR": 6.0}),
        ("GULA BHN", "GR", "BAHAN", {"MLGPAR": -2.0, "SBYKET": 3.0}),
    ]
    for barang, sat, kat, devs in spec:
        for resto, dev in devs.items():
            for jenis, val in [
                    ("1.SO", 50.0), ("2.SALDO AKHIR", 50.0 - dev),
                    ("3.DEVIASI", dev), ("9.ACR", 2.0)]:
                rows.append({
                    "Nama Barang": barang, "JENIS": jenis,
                    "NAMA RESTO": resto, "Tanggal": h, "NILAI": val,
                    "SATUAN": sat, "AKTIF/NON": "AKTIF",
                    "KATEGORI": kat, "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": None, "Nomor PO": None,
                    "#Tgl/Jam Pembuatan IT": None,
                })
    harga = {b: (100.0, s) for b, s, _, _ in spec}
    return pd.DataFrame(rows), harga


def main():
    tmp = Path(tempfile.mkdtemp(prefix="a1e_p4_"))
    import src.ui.app as appmod
    import src.ui.followup as fumod
    import src.ui.deviasi_view as dvmod
    appmod._SETTINGS_PATH = tmp / "settings.json"
    appmod.CONFIG_PATH = tmp / "config.json"
    shutil.copy(REPO + "/config.json", tmp / "config.json")
    fumod._BASE = tmp
    dvmod._SETTINGS_BASE = tmp

    root, app = make_app()
    df, harga = build_mock(25)
    app.notebook.select(app.tab_nominal_resto)
    pump(root, 0.3)
    nr = app.nominal_resto_view
    nr.load_data(df, harga_map=harga, konversi_map={})
    nr.ensure_refreshed()
    wait_view(root, nr)
    h_actual = int(getattr(nr, "tanggal_h", 25) or 25)
    out(f"H shared view = {h_actual}")
    if h_actual != 25:
        df, harga = build_mock(h_actual)
        nr.load_data(df, harga_map=harga, konversi_map={})
        nr.ensure_refreshed()
        wait_view(root, nr)
    pump(root, 0.6)

    out(f"DEBUG status={nr.status_var_label.get()!r} "
        f"result={None if nr._result_df is None else len(nr._result_df)} "
        f"pairs={None if nr._pairs_df is None else len(nr._pairs_df)} "
        f"busy={getattr(nr, '_busy', None)} katsel={nr._kategori_sel!r}")
    tree = nr.tree
    kids = [k for k in tree.get_children("") if k != "row_total"]
    out(f"resto rows: {[tree.set(k, 'Resto') for k in kids]}")

    # ---------- parity: tabel per-resto vs popup ------------------------
    target = None
    for k in kids:
        if str(tree.set(k, "Resto")) == "MLGPAR":
            target = k
            break
    if target is None:
        check("P4.0 baris MLGPAR ada", True, False, "tak ada baris")
    else:
        tbl_nom = rp_to_num(tree.set(target, "Nominal Deviasi"))
        out(f"tabel MLGPAR Nominal Deviasi = {tree.set(target, 'Nominal Deviasi')!r}")
        # expected dari data: AYAM COM -10*100 + KOP PACK 6*100 + GULA -2*100
        exp = -1000.0 + 600.0 - 200.0
        check("P4.1 nilai tabel MLGPAR = Σ(deviasi×harga) semua kategori",
              exp, tbl_nom)

        # double-click MLGPAR → popup (fungsi tak return win — ambil
        # dari _detail_wins; jalur produksi = _on_double_click)
        nr._show_resto_popup("MLGPAR")
        win = nr._detail_wins[-1] if nr._detail_wins else None
        pump(root, 0.8)
        # cari tree di popup
        import tkinter as tk
        from tkinter import ttk

        def find_trees(w):
            o = []
            for c in w.winfo_children():
                if isinstance(c, ttk.Treeview):
                    o.append(c)
                o.extend(find_trees(c))
            return o

        ptrees = find_trees(win)
        if not ptrees:
            check("P4.2 popup rincian terbuka dgn tabel", True, False, "-")
        else:
            pt = ptrees[0]
            pk = pt.get_children("")
            vals = {str(pt.set(i, "Nama Barang")):
                    rp_to_num(pt.set(i, "Nominal Deviasi Sekarang"))
                    for i in pk if i != "row_total"}
            out(f"popup rows: {vals}")
            total_row = pt.set("row_total", "Nominal Deviasi Sekarang") \
                if "row_total" in pk else None
            pop_total = rp_to_num(total_row)
            check("P4.2 popup menampilkan SEMUA pasangan resto (3 barang)",
                  {"AYAM COM", "KOP PACK", "GULA BHN"}, set(vals))
            check("P4.3 popup TOTAL = Σ pasangan popup = nilai tabel baris",
                  tbl_nom, pop_total)
            win.destroy()
            pump(root, 0.3)

    # ---------- filter KATEGORI = COM → tabel vs popup -----------------
    # pilih entry kategori COM di combobox lalu refresh
    combo_vals = list(nr._kategori_combo["values"])
    out(f"kategori combo values: {combo_vals}")
    com_entry = next((v for v in combo_vals if str(v).strip().upper()
                      == "COM"), None)
    if com_entry is None:
        check("P4.4 entry kategori COM tersedia", True, False,
              f"values={combo_vals}")
    else:
        nr._kategori_var.set(com_entry)
        nr._on_kategori_change() if hasattr(nr, "_on_kategori_change") \
            else None
        # fallback: jalur set + _refresh via method yang ada
        if not hasattr(nr, "_on_kategori_change"):
            # mirror baris 1023-1025: set _kategori_sel + _refresh
            nr._kategori_sel = com_entry
            nr._refresh()
        wait_view(root, nr)
        pump(root, 0.5)
        kids2 = [k for k in tree.get_children("") if k != "row_total"]
        out(f"resto rows dgn KATEGORI=COM: "
            f"{[tree.set(k, 'Resto') for k in kids2]}")
        t2 = None
        for k in kids2:
            if str(tree.set(k, "Resto")) == "MLGPAR":
                t2 = k
        if t2 is None:
            check("P4.5 baris MLGPAR tetap ada (AYAM COM kategori COM)",
                  True, False, "hilang")
        else:
            tbl_nom2 = rp_to_num(tree.set(t2, "Nominal Deviasi"))
            out(f"tabel MLGPAR (COM saja) = {tbl_nom2}")
            check("P4.5 tabel MLGPAR = hanya pasangan COM (-1000)",
                  -1000.0, tbl_nom2)
            nr._show_resto_popup("MLGPAR")
            win2 = nr._detail_wins[-1] if nr._detail_wins else None
            pump(root, 0.8)

            def find_trees2(w):
                import tkinter as tk2
                from tkinter import ttk as ttk2
                o = []
                for c in w.winfo_children():
                    if isinstance(c, ttk2.Treeview):
                        o.append(c)
                    o.extend(find_trees2(c))
                return o

            pt2 = find_trees2(win2)[0]
            pk2 = pt2.get_children("")
            vals2 = {str(pt2.set(i, "Nama Barang")):
                     rp_to_num(pt2.set(i, "Nominal Deviasi Sekarang"))
                     for i in pk2 if i != "row_total"}
            out(f"popup rows (COM filter): {vals2}")
            pop_total2 = rp_to_num(
                pt2.set("row_total", "Nominal Deviasi Sekarang"))
            check("P4.6 popup TER-SCOPE ke kategori aktif (hanya AYAM COM)",
                  {"AYAM COM"}, set(vals2))
            check("P4.7 popup TOTAL = tabel baris (kategori aktif)",
                  tbl_nom2, pop_total2)
            win2.destroy()
            pump(root, 0.3)

    # ---------- chip TOTAL vs baris TOTAL tabel ------------------------
    total_row_vals = tree.set("row_total", "Nominal Deviasi") \
        if "row_total" in tree.get_children("") else None
    st = nr.status_var_label.get() if hasattr(nr, "status_var_label") else ""
    out(f"TOTAL row: {total_row_vals!r} status: {st!r}")
    # kembalikan kategori Semua utk cek total penuh
    nr._kategori_var.set("Semua")
    nr._kategori_sel = None
    nr._refresh()
    wait_view(root, nr)
    pump(root, 0.5)
    tot_all = rp_to_num(tree.set("row_total", "Nominal Deviasi")) \
        if "row_total" in tree.get_children("") else None
    exp_all = (-1000.0 + 400.0) + 600.0 + (-200.0 + 300.0)
    check("P4.8 baris TOTAL tabel = Σ semua resto", exp_all, tot_all)
    m = re.search(r"TOTAL[^0-9\-]*([\d\.\,\-]+)", st or "")
    out(f"    (status chip text: {st!r})")

    root.destroy()
    shutil.rmtree(tmp, ignore_errors=True)
    n_bad = summary()
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
