#!/usr/bin/env python3
"""p04 — TreeFindPopup (Ctrl+F): case-insensitive, wrap-around, persistensi
highlight lewat sort_tree_by_column & re-render (insert_tree_items),
single-active antar tree, dan find di clone ⛶ (open_tree_maximized).
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import tkinter as tk
from src.ui import widgets
from src.ui.theme import (setup_tree_tags, FIND_HIT_TAG, FIND_CUR_TAG)

root = tk.Tk()
root.geometry("900x500+10+10")
root.update_idletasks()

cols = ["Nama Barang", "Qty"]
tree = widgets.make_tree(root, cols, show="headings")
setup_tree_tags(tree)
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=150)
names = ["BEBEK Ayam", "bebek goreng", "CITRA", "Ayam Bebek", "GULA"]
for i, nm in enumerate(names):
    tree.insert("", "end", iid=f"r{i}", values=(nm, i * 10),
                tags=("evenrow",))

# ---- 1. case-insensitive + tag priority (zebra dulu, find belakangan) ----
pop = widgets.open_tree_find(tree)
pop.var.set("bebek")
pop._recompute()
hits = list(pop._matches)
print("query 'bebek' (huruf kecil) cocok:", [tree.item(i, "values")[0] for i in hits])
case_ok = len(hits) == 3

# tag find harus MENANG atas zebra (prioritas create: register_find_tags dulu)
tags_r0 = tree.item("r0", "tags")
print("tags r0 setelah find          :", tags_r0)
find_wins = FIND_HIT_TAG in tags_r0 or FIND_CUR_TAG in tags_r0
zebra_kept = "evenrow" in tags_r0

# ---- 2. wrap-around -------------------------------------------------------
pop._cur = len(pop._matches) - 1
pop._nav(1)          # next dari match terakhir → harus wrap ke 0
cur_after_wrap = pop._cur
pop._nav(-1)         # prev dari 0 → wrap ke akhir
cur_after_wrap2 = pop._cur
print("wrap forward (last→0)        :", cur_after_wrap, "| wrap back (0→last):", cur_after_wrap2)
wrap_ok = cur_after_wrap == 0 and cur_after_wrap2 == len(pop._matches) - 1

# ---- 3. persistensi highlight melewati SORT (delete+reinsert) ------------
widgets.sort_tree_by_column(tree, "Qty", reverse=True)
root.update_idletasks()
tags_after_sort = {i: tree.item(i, "tags") for i in tree.get_children("")}
n_find_tagged = sum(1 for t in tags_after_sort.values()
                    if FIND_HIT_TAG in t or FIND_CUR_TAG in t)
print("baris dgn tag find pasca sort:", n_find_tagged, "(matches =", len(pop._matches), ")")
sort_keeps_tags = n_find_tagged == len(pop._matches)

# ---- 4. re-render penuh (insert_tree_items) → recompute otomatis ---------
tree.delete(*tree.get_children(""))
items = [("", f"r{i}", {"values": (nm, i), "tags": ("evenrow",)})
         for i, nm in enumerate(["bebek x", "AYAM", "bebek y"])]
cancel_ins = widgets.insert_tree_items(tree, items, batch=2)
import time
_deadline = time.time() + 3.0
while time.time() < _deadline:
    root.update()
    time.sleep(0.01)
    if len(tree.get_children("")) == len(items) and pop._after_id is None:
        break
hits2 = [i for i in pop._matches if tree.exists(i)]
print("matches pasca re-render      :", [tree.item(i, "values")[0] for i in hits2])
stale_iids = [i for i in pop._matches if not tree.exists(i)]
print("iid basi tersisa di _matches :", stale_iids)
rerender_ok = len(hits2) == 2 and not stale_iids

# ---- 5. single-active: buka find utk tree LAIN → popup lama ditutup -----
tree2 = widgets.make_tree(root, ["A"], show="headings")
setup_tree_tags(tree2)
tree2.heading("A", text="A")
tree2.insert("", "end", iid="z0", values=("bebek",))
pop2 = widgets.open_tree_find(tree2)
old_alive = pop.win.winfo_exists()
print("popup #1 masih hidup saat #2 dibuka (harus False):", old_alive)
single_ok = (not old_alive) and pop2.win.winfo_exists()

# ---- 6. find di CLONE ⛶ ---------------------------------------------------
tree3 = widgets.make_tree(root, cols, show="headings")
setup_tree_tags(tree3)
tree3.heading("Nama Barang", text="Nama Barang")
tree3.heading("Qty", text="Qty")
for i, nm in enumerate(["bebek clone", "GULA"]):
    tree3.insert("", "end", iid=f"c{i}", values=(nm, i))
win, clone = widgets.open_tree_maximized(
    tree3, "CloneTest", setup_tags=setup_tree_tags)
root.update_idletasks()
popc = widgets.open_tree_find(clone)
popc.var.set("bebek")
popc._recompute()
clone_hits = list(popc._matches)
print("clone matches                :", len(clone_hits))
clone_find_ok = len(clone_hits) == 1
clone_tags = clone.item(clone_hits[0], "tags") if clone_hits else ()
print("clone tag find menang zebra? :", FIND_HIT_TAG in clone_tags
      or FIND_CUR_TAG in clone_tags, tuple(clone_tags))
win.destroy()

print()
print("EXPECTED: case_ok=True wrap_ok=True sort_keeps_tags=True "
      "rerender_ok=True single_ok=True clone_find_ok=True")
print(f"ACTUAL: case={case_ok} wrap={wrap_ok} sort_keeps_tags="
      f"{sort_keeps_tags} rerender={rerender_ok} single={single_ok} "
      f"clone_find={clone_find_ok} find_wins_zebra={find_wins} "
      f"zebra_kept={zebra_kept}")
allok = all([case_ok, wrap_ok, sort_keeps_tags, rerender_ok, single_ok,
             clone_find_ok, find_wins, zebra_kept])
print("VERDICT:", "NOT-BUG (semua kontrak Ctrl+F terpenuhi di widget level, "
      "termasuk clone ⛶)" if allok else "BUG")

root.destroy()
