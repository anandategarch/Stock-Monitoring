#!/usr/bin/env python3
"""probe audit v3.11.23 — screenshot DEFAULT view (tanpa sort) Deviasi GR/PCS.
Bukti visual apa yang user lihat di default render (sort by Nama Barang, |Dev| desc).
"""
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

import pandas as pd

from src.ui.deviasi_view import DeviasiView

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)


def pump(root, seconds=0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def make_fixture():
    rows = []
    # kelompok dengan berbagai ukuran: 1, 2, 3, 5 baris + label CEK panjang
    data = [
        ("AYAM FILET", "MLGPAR", 60.0, 100.0),
        ("AYAM FILET", "SBYKET", 30.0, 5.0),
        ("GULA PASIR", "MLGPAR", 20.0, -5.0),
        ("GULA PASIR", "SBYKET", 80.0, 10.0),
        ("GULA PASIR", "PWKTAM", 50.0, 30.0),
        ("KOPI BUBUK", "MLGPAR", 10.0, 2.0),
        ("SUSU UHT", "MLGPAR", 1.0, 9.0),
        ("SUSU UHT", "SBYKET", 2.0, 8.0),
        ("SUSU UHT", "PWKTAM", 3.0, 7.0),
        ("SUSU UHT", "MLGKUL", 4.0, 6.0),
        ("SUSU UHT", "SMGBAN", 5.0, 5.0),
    ]
    for b, resto, so, saldo in data:
        for j, v in [("1.SO", so), ("2.SALDO AKHIR", saldo),
                     ("SALDO AWAL", 10.0), ("4.IN", 2.0)]:
            for t in range(20, 28):
                rows.append({
                    "Nama Barang": b, "JENIS": j, "NAMA RESTO": resto,
                    "Tanggal": t, "NILAI": float(v if j != "1.SO"
                                                 or t == 26 else 0.0),
                    "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                    "KATEGORI": "BAHAN",
                    "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": None, "Nomor PO": None,
                    "#Tgl/Jam Pembuatan IT": None,
                    "SOURCE DATA": "input so harian"})
    return pd.DataFrame(rows)


def dump_cells(dv, label):
    t = dv.tree
    kids = list(t.get_children(""))
    print(f"\n=== {label} — {len(kids)} baris (urutan visual) ===")
    for k in kids:
        ks = str(k)
        nb = str(t.set(k, "Nama Barang"))
        resto = str(t.set(k, "Resto"))
        snap = dv._row_snaps.get(ks) or {}
        raw = str(snap.get("barang", ""))
        flag = "  <-- ANOTASI (nama barang asli tak terlihat)" \
            if not nb.startswith(raw) and raw else ""
        print(f"  {resto:8s} | display={nb!r}{flag}")


def main():
    root = tk.Tk()
    root.geometry("1600x900+0+0")
    df = make_fixture()
    top = tk.Toplevel(root)
    top.geometry("1600x900+5+5")
    dv = DeviasiView(top, satuan_mode="GR")
    dv.pack(fill="both", expand=True)
    pump(root, 0.4)
    dv.load_data(df)
    t0 = time.time()
    while time.time() - t0 < 15:
        root.update()
        time.sleep(0.01)
        if not dv._busy and len(dv.tree.get_children("")):
            break
    pump(root, 0.8)   # tunggu autofit + layout selesai

    dump_cells(dv, "DEFAULT VIEW Deviasi GR")

    # screenshot full
    from PIL import Image, ImageGrab
    top.lift()
    top.attributes("-topmost", True)
    pump(root, 0.6)
    img = ImageGrab.grab(xdisplay=os.environ.get("DISPLAY", ":61"))
    img.save(OUT / "audit_default_dev_gr.png")
    print(f"\n📸 {OUT}/audit_default_dev_gr.png ({img.size})")

    # crop kolom kiri (Nama Barang area) diperbesar
    w, h = img.size
    crop = img.crop((0, int(h * 0.12), int(w * 0.42), h))
    crop = crop.resize((crop.width * 2, crop.height * 2),
                       Image.LANCZOS)
    crop.save(OUT / "audit_default_dev_gr_crop.png")
    print(f"📸 {OUT}/audit_default_dev_gr_crop.png ({crop.size})")

    top.destroy()
    root.destroy()


if __name__ == "__main__":
    main()
