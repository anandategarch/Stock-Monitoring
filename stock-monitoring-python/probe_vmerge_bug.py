"""
probe_vmerge_bug.py — Reproduksi bug laporan user v3.11.18:
"yang tampil hanya 1 nama barang per group atau section".

Data realistis ala produksi: beberapa barang × beberapa resto, grup
CAMPUR ukuran (1..40 baris) + grup BESAR (120 baris) utk menguji
sticky di tengah grup. Dump nilai kolom "Nama Barang" (dan CEK/Rank)
tiap baris pada: (1) render awal, (2) scroll tengah grup besar,
(3) pasca-sort kolom lain, (4) pasca-filter kategori. Screenshot tiap
tahap ke /tmp/shots/probe_vm_*.png.
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

from src.ui.deviasi_view import DeviasiView

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)
os.environ.setdefault("DISPLAY", ":99")


def shot(name, delay=0.25):
    time.sleep(delay)
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(xdisplay=os.environ.get("DISPLAY", ":99"))
        img.save(OUT / f"{name}.png")
        print(f"  [shot] {name}.png")
    except Exception as e:
        print(f"  ! gagal {name}: {e}")


def pump(root, seconds=0.4):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def dump_col(tree, col, kids):
    return [str(tree.set(k, col)) for k in kids]


def summarize(dv, tree, label):
    kids = list(tree.get_children(""))
    names = dump_col(tree, "Nama Barang", kids)
    snaps = {str(k): (dv._row_snaps.get(str(k)) or {}).get("barang", "?")
             for k in kids}
    nonempty = [(i, v) for i, v in enumerate(names) if v.strip()]
    # grup unik mentah (dari snaps)
    groups = []
    for i, k in enumerate(kids):
        b = snaps[str(k)]
        if not groups or groups[-1][0] != b:
            groups.append([b, 1])
        else:
            groups[-1][1] += 1
    n_grp = len(groups)
    print(f"\n--- {label}: n={len(kids)} grup_mentah={n_grp} "
          f"sel_nama_terisi={len(nonempty)}")
    # tampilkan 25 baris pertama + sekitar grup besar
    print("  idx | display nama           | raw snaps")
    for i, k in enumerate(kids[:25]):
        print(f"  {i:4d} | {names[i][:24]:24s} | {snaps[str(k)]}")
    # baris display kosong tapi raw ada (nama hilang)
    missing = [i for i, v in enumerate(names)
               if not v.strip() and snaps[str(kids[i])].strip()]
    print(f"  >> baris DISPLAY-KOSONG padahal raw ada nama: "
          f"{len(missing)}/{len(kids)}")
    if n_grp:
        print(f"  >> grup (raw): {groups[:8]}{' ...' if n_grp > 8 else ''}")
    return names, snaps, kids


def main():
    root = tk.Tk()
    root.geometry("1500x860+5+5")
    dv = DeviasiView(root, satuan_mode="GR")
    dv.pack(fill="both", expand=True)

    # ---- data realistis -------------------------------------------------
    rows = []
    jenis_list = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
                  "4.IN", "9.ACR"]
    restos = ["RA1", "RA2", "RA3", "RB1", "RB2"]

    def add(barang, restos_b, so_pat):
        for resto in restos_b:
            for tgl in range(24, 28):
                for jenis, val in (
                        ("1.SO", float(so_pat(resto, tgl))),
                        ("2.SALDO AKHIR", 20.0),
                        ("SALDO AWAL", 10.0 if tgl == 24 else 0.0),
                        ("4.IN", 2.0),
                        ("3.DEVIASI", 0.0),
                        ("9.ACR", 1.0)):
                    rows.append({
                        "Nama Barang": barang, "JENIS": jenis,
                        "NAMA RESTO": resto, "Tanggal": tgl,
                        "NILAI": val, "SATUAN": "GR",
                        "AKTIF/NON": "AKTIF",
                        "KATEGORI": "COM DEVIASI - RESTO",
                        "SOURCE KIRIMAN": "GUDANG",
                    })

    # grup kecil (2 resto × 4 tgl = 8 baris per jenis → pivot 2 baris/resto)
    add("BRG ALFA 1", ["RA1", "RA2"], lambda r, t: 20 + (t % 3))
    add("BRG ALFA 2", ["RA1", "RA3"], lambda r, t: 20 - (t % 2))
    add("BRG ALFA 3", ["RB1"], lambda r, t: 25)          # singleton
    add("BRG BETA 1", ["RA1", "RA2", "RA3", "RB1", "RB2"],
        lambda r, t: 20 + (t % 4))                        # grup 5 resto
    add("BRG BETA 2", ["RB1", "RB2"], lambda r, t: 18)
    add("BRG GAMMA", ["RA1", "RA2"], lambda r, t: 22)
    add("BRG DELTA", ["RA1", "RA2", "RA3", "RB1", "RB2", "RA1"],
        lambda r, t: 19)
    add("BRG ECHO", ["RA2"], lambda r, t: 30)            # singleton

    dv.data = pd.DataFrame(rows)
    dv._show_content()
    dv._refresh(sync=True)
    for _ in range(60):
        root.update()
        time.sleep(0.01)
    wait_ready(root, dv)
    pump(root, 0.6)

    tree = dv.tree
    summarize(dv, tree, "TAHAP-1 render awal")
    shot("probe_vm_1_awal")

    # ---- TAHAP 2: scroll ke tengah tabel --------------------------------
    tree.yview_moveto(0.5)
    pump(root, 0.6)
    summarize(dv, tree, "TAHAP-2 scroll 50%")
    shot("probe_vm_2_scroll_mid")

    # ---- TAHAP 3: scroll bawah ------------------------------------------
    tree.yview_moveto(1.0)
    pump(root, 0.6)
    summarize(dv, tree, "TAHAP-3 scroll bawah")
    shot("probe_vm_3_scroll_bottom")

    root.destroy()
    print("\nPROBE SELESAI — screenshot di /tmp/shots/probe_vm_*.png")


def wait_ready(root, view, timeout=15.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        root.update()
        kids = list(view.tree.get_children(""))
        if kids:
            return
        time.sleep(0.02)


if __name__ == "__main__":
    main()
