import os, sys, time
from pathlib import Path
import pandas as pd
sys.path.insert(0, '/home/z/stock-audit/stock-monitoring-python')
import tkinter as tk
from src.ui.deviasi_view import DeviasiView
os.environ.setdefault("DISPLAY", ":99")

rows = []
jenis = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "4.IN", "9.ACR"]
# 1 grup raksasa: BARANG BESAR di 100 resto + 1 barang kecil setelahnya
for idx, resto in enumerate([f"R{i:03d}" for i in range(100)]):
    for tgl in (24, 25, 26, 27):
        for j, v in (("1.SO", 20.0), ("2.SALDO AKHIR", 20.0),
                     ("SALDO AWAL", 10.0 if tgl == 24 else 0.0),
                     ("4.IN", 2.0), ("9.ACR", 1.0)):
            rows.append({"Nama Barang": "BARANG BESAR", "JENIS": j,
                         "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": v,
                         "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                         "KATEGORI": "COM DEVIASI - RESTO",
                         "SOURCE KIRIMAN": "GUDANG"})
for resto in ("R000",):
    for tgl in (24, 25, 26, 27):
        for j, v in (("1.SO", 5.0), ("2.SALDO AKHIR", 5.0),
                     ("SALDO AWAL", 5.0), ("4.IN", 0.0), ("9.ACR", 0.0)):
            rows.append({"Nama Barang": "ZZ BARANG KECIL", "JENIS": j,
                         "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": v,
                         "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                         "KATEGORI": "COM DEVIASI - RESTO",
                         "SOURCE KIRIMAN": "GUDANG"})

root = tk.Tk(); root.geometry("1400x800+5+5")
dv = DeviasiView(root, satuan_mode="GR"); dv.pack(fill="both", expand=True)
dv.data = pd.DataFrame(rows); dv._show_content(); dv._refresh(sync=True)
t0 = time.time()
while time.time() - t0 < 15:
    root.update()
    if list(dv.tree.get_children("")): break
    time.sleep(0.02)
for _ in range(80): root.update(); time.sleep(0.01)

tree = dv.tree; kids = list(tree.get_children(""))
n = len(kids)
print(f"total baris tree: {n}")

def probe(frac, label):
    tree.yview_moveto(frac)
    for _ in range(60): root.update()
    time.sleep(0.35)  # beri waktu poller 150ms jalan
    for _ in range(30): root.update()
    vis = [k for k in kids if tree.bbox(k) and 0 <= tree.bbox(k)[1] < tree.winfo_height()]
    named = [(i, str(tree.set(k, "Nama Barang"))) for i, k in enumerate(kids) if str(tree.set(k, "Nama Barang")).strip()]
    vis_named = [x for x in named if kids[x[0]] in vis]
    print(f"\n[{label}] yview={tree.yview()} baris terlihat={len(vis)} "
          f"indeks terlihat={kids.index(vis[0]) if vis else '-'}..{kids.index(vis[-1]) if vis else '-'}")
    print(f"  seluruh sel nama terisi (seluruh tree): {len(named)} -> idx {[i for i,_ in named][:6]}")
    print(f"  nama terlihat DI VIEWPORT: {len(vis_named)} -> {[(i, v[:20]) for i, v in vis_named[:4]]}")

probe(0.0, "TOP")
probe(0.30, "30% (tengah grup besar)")
probe(0.50, "50% (tengah grup besar)")
probe(0.90, "90% (akhir grup besar)")
probe(1.0, "BOTTOM")
root.destroy()
