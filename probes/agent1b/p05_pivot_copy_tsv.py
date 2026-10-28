#!/usr/bin/env python3
"""p05 — Ctrl+C (copy_tree_selection_tsv) di tab Pivot (tree kanan freeze-pane).

pivot_view membangun: parent (barang) text=#0 values=['']*kolom; anak
(metric '1.SO' dst) text=metric + values matrix. Tree kanan: #0 width=0
TAPI heading('#0', 'Nama Barang') TERSET (pivot_view.py:1366-1367).
tree_selection_tsv → use_tree_col=True → kolom pertama TSV = "Nama Barang"
berisi tree.item(iid,'text') = NAMA METRIC utk baris anak (bukan nama
barang); nama barang hanya ada di baris parent yang values-nya kosong.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import tkinter as tk
from src.ui import widgets
from src.ui.theme import setup_tree_tags

root = tk.Tk()
root.geometry("1100x500+10+10")

# replika persis pivot kanan: show tree headings, #0 hidden, kolom matrix
cols = ["-25", "1", "2"]
tree = ttk_tree = __import__("tkinter.ttk", fromlist=["Treeview"]).Treeview(
    root, columns=cols, show="tree headings", selectmode="extended")
setup_tree_tags(tree)                     # sama dgn pivot_view._setup_tags
tree.pack(fill="both", expand=True)
tree.column("#0", width=0, minwidth=0, stretch=False)   # pivot_view:1366
tree.heading("#0", text="Nama Barang")                  # pivot_view:1367
for c in cols:
    tree.column(c, width=80, anchor="e")
    ci = int(float(c))
    tree.heading(c, text=f"{abs(ci)}•" if ci < 0 else str(ci))

# struktur item persis pivot_view._compute (1198-1277)
tree.insert("", "end", iid="item_0", text="BEBEK",
            values=["" for _ in cols], tags=("item_header",), open=True)
tree.insert("item_0", "end", iid="item_0_so", text="1.SO",
            values=("1.000", "990", "950"), tags=(), open=False)
tree.insert("item_0", "end", iid="item_0_in", text="4.IN",
            values=("50", "60", "40"), tags=(), open=False)
tree.insert("", "end", iid="item_1", text="GULA",
            values=["" for _ in cols], tags=("item_header",), open=True)
tree.insert("item_1", "end", iid="item_1_so", text="1.SO",
            values=("20", "18", "15"), tags=(), open=False)

# ---- copy BARIS ANAK (kasus umum: user seleksi baris metric di matrix) ---
tree.selection_set(("item_0_so", "item_1_so"))
tsv_children = widgets.tree_selection_tsv(tree)
print("=== Ctrl+C seleksi 2 baris ANAK (metric) di tree kanan pivot ===")
print(tsv_children)
first_col = [ln.split("\t")[0] for ln in tsv_children.splitlines()[1:]]
hdr0 = tsv_children.splitlines()[0].split("\t")[0]
print()
print(f"Header kolom pertama : {hdr0!r}")
print(f"Isi kolom pertama    : {first_col}")

# ---- copy SEMUA (Ctrl+A → Ctrl+C) ----------------------------------------
all_iids = []
def _walk(p=""):
    for ch in tree.get_children(p):
        all_iids.append(ch); _walk(ch)
_walk()
tree.selection_set(all_iids)
tsv_all = widgets.tree_selection_tsv(tree)
print()
print("=== Ctrl+A + Ctrl+C (parent+anak) ===")
print(tsv_all)
parent_rows = [ln for ln in tsv_all.splitlines()[1:]
               if ln.split("\t")[0] in ("BEBEK", "GULA")]
print("Baris parent (nama barang):", parent_rows)

print()
print("EXPECTED (semantik Excel/label): baris anak memuat NAMA BARANG "
      "(BEBEK/GULA) — atau minimal label kolom #0 bukan 'Nama Barang' "
      "bila isinya metric; baris utuh berguna saat di-paste.")
print(f"ACTUAL: header[0]={hdr0!r} tapi baris anak kolom[0]={first_col} "
      f"(nama METRIC, nama barang HILANG); baris parent = {parent_rows} "
      f"(nama barang ada, semua sel matrix kosong).")
bad = (hdr0 == "Nama Barang" and set(first_col) == {"1.SO"})
print("VERDICT:", "BUG (P3): Ctrl+C di tab Pivot — kolom pertama "
      "berlabel 'Nama Barang' berisi nama METRIC ('1.SO'); nama barang "
      "hilang dari baris data (hanya ada di baris parent yang sel-nya "
      "kosong) — paste ke Excel menghasilkan tabel yang menyesatkan"
      if bad else "NOT-BUG")

root.destroy()
