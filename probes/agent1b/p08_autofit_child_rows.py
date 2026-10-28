#!/usr/bin/env python3
"""p08 — auto_fit_columns TIDAK mengukur baris ANAK (tree hierarki 2-level).

pivot_view (matrix): baris DATA (metric '1.SO' dst + nilai matrix) adalah
ANAK dari parent barang; parent punya values ['']*kolom. auto_fit_columns
hanya meng-sample tree.get_children('') (= PARENT) → nilai matrix TIDAK
PERNAH terukur → lebar kolom tanggal ≈ lebar HEADER '25•' saja (~64px),
 nilai '1.234.567' butuh ~99px → TERPOTONG.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import tkinter as tk
import tkinter.ttk as ttk
from src.ui import widgets
from src.ui.theme import setup_tree_tags, font

root = tk.Tk()
root.geometry("1200x500+10+10")

cols = ["25", "1", "2"]
tree = ttk.Treeview(root, columns=cols, show="tree headings",
                    selectmode="extended")
setup_tree_tags(tree)
tree.pack(fill="both", expand=True)
tree.column("#0", width=0, minwidth=0, stretch=False)
tree.heading("#0", text="Nama Barang")
tree._autofit_skip = {"#0"}                       # persis pivot kanan
for c in cols:
    # persis pivot_view:1407-1393 — width 70, stretch hanya utk ≤6 kolom
    tree.column(c, width=70, minwidth=50, anchor="e", stretch=False)
    ci = int(float(c))
    tree.heading(c, text=f"{abs(ci)}•" if ci < 0 else str(ci))

# struktur PERSIS pivot_view._compute (1198-1277): parent values kosong,
# anak = metric + nilai matrix
tree.insert("", "end", iid="item_0", text="BEBEK",
            values=["" for _ in cols], tags=("item_header",), open=True)
tree.insert("item_0", "end", iid="item_0_so", text="1.SO",
            values=("1.234.567", "990", "950"), tags=(), open=False)
tree.insert("item_0", "end", iid="item_0_in", text="4.IN",
            values=("12.345", "60", "40"), tags=(), open=False)

meas = font(10).measure
need_px = max(meas("1.234.567"), meas("12.345")) + 24   # pad auto-fit

widgets.auto_fit_columns(tree)
root.update_idletasks()
w_after = [int(tree.column(c, "width")) for c in cols]
print("nilai matrix terlebar  : '1.234.567' butuh ~%dpx (incl pad)" % need_px)
print("width kolom pasca auto-fit :", dict(zip(cols, w_after)))
print("width header-only acuan    :",
      {c: meas(tree.heading(c, "text")) + 24 + 10 for c in cols})

clipped = [c for c, w in zip(cols, w_after) if w < need_px]
print()
print("EXPECTED: kolom '25' (berisi '1.234.567') ≥ ~%dpx — nilai terbaca utuh" % need_px)
print(f"ACTUAL: kolom terpotong = {clipped} (width {w_after[0]}px utk nilai "
      f"'1.234.567' — auto-fit hanya mengukur PARENT yang values-nya kosong)")
print("VERDICT:", "BUG (P3): auto_fit_columns mengabaikan baris ANAK — "
      "kolom matrix pivot (baris data = anak) di-fit hanya dari teks header "
      "'25•' → nilai ribuan terpotong; tombol ↔ Auto-Fit & auto-fit pertama "
      "sama-sama terdampak" if clipped else "NOT-BUG")

root.destroy()
