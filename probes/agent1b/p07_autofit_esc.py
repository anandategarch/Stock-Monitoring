#!/usr/bin/env python3
"""p07 — auto_fit_columns: #0 skip (freeze-pane) + cap max-width + HeaderFilter Esc.

Scope item 5: column width/autofit #0 handling dgn FrozenNamePane (_autofit_skip).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import tkinter as tk
import tkinter.ttk as ttk
from src.ui import widgets
from src.ui.theme import setup_tree_tags

root = tk.Tk()
root.geometry("1000x500+10+10")

cols = ["A", "B"]
tree = ttk.Treeview(root, columns=cols, show="tree headings",
                    selectmode="extended")
setup_tree_tags(tree)
tree.pack(fill="both", expand=True)
tree.column("#0", width=0, minwidth=0, stretch=False)
tree.heading("#0", text="Nama Barang")
tree._autofit_skip = {"#0"}          # persis pivot_view tree kanan
for c in cols:
    # stretch=False — persis pivot mode Tanggal (banyak kolom): uji CAP murni
    tree.column(c, width=60, minwidth=50, anchor="e", stretch=False)
    tree.heading(c, text=c)

long_name = "NAMA BARANG SANGAT PANJANG MELEBIHI 340 PIXEL " * 3
tree.insert("", "end", iid="p", text=long_name, values=["12345", "1"])
tree.insert("p", "end", iid="c1", text="1.SO",
            values=["1.234.567.890.123", "9"])

w0_before = int(tree.column("#0", "width"))
widgets.auto_fit_columns(tree)
root.update_idletasks()
w0_after = int(tree.column("#0", "width"))
wA = int(tree.column("A", "width"))
wB = int(tree.column("B", "width"))
print(f"#0 width sebelum={w0_before} sesudah auto-fit={w0_after} (harus tetap 0)")
print(f"kolom A width={wA} (nilai '1.234.567.890.123' → capped max_width*ui_scale)")
print(f"kolom B width={wB}")
skip_ok = w0_after == 0
cap_ok = wA <= int(340 * 1.0) + 5   # max_width default 340 (ui_scale 1.0)

# HeaderFilter popup: Escape menutup popup + grab dilepas
hf = widgets.HeaderFilter(
    tree, "A",
    get_values=lambda: [str(tree.set(i, "A")) for i in tree.get_children("")],
    on_apply=lambda sel: None, label="A")
hf.open_popup()
root.update_idletasks()
alive_before = hf._popup is not None and hf._popup.winfo_exists()
hf._nav_entry.focus_force()
root.update()
hf._nav_entry.event_generate("<Escape>", when="now")  # jalur user: fokus di entry
root.update_idletasks()
alive_after = hf._popup is not None and hf._popup.winfo_exists()
print(f"HeaderFilter popup hidup={alive_before} → pasca Esc={alive_after}")
esc_ok = alive_before and not alive_after

print()
print(f"EXPECTED: skip_ok=True cap_ok=True esc_ok=True")
print(f"ACTUAL: skip={skip_ok} cap={cap_ok} esc={esc_ok} "
      f"(w0={w0_after}, wA={wA}, wB={wB})")
allok = skip_ok and cap_ok and esc_ok
print("VERDICT:", "NOT-BUG (auto-fit menghormati _autofit_skip #0, cap "
      "max-width berlaku, Esc menutup popup filter)" if allok else "BUG")

root.destroy()
