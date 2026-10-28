#!/usr/bin/env python3
"""p02 — Urutan daftar nilai popup filter ⧩ utk label tanggal '25•' + duplikat spasi.

Scope item 2/3: '25•' date-label sorting; nilai dgn trailing space tampil sbg
entri berbeda. Sort kolom Tanggal in_selisih sudah kronologis (v3.11.1 B3),
tapi daftar nilai popup ⧩ memakai _filter_value_sort_key (widgets) — apakah
'25•' terurut kronologis di sana?
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import tkinter as tk
from src.ui import widgets
from src.ui.theme import setup_tree_tags

root = tk.Tk()
root.geometry("900x400+10+10")
root.update_idletasks()

cols = ["Tanggal", "Satuan"]
tree = widgets.make_tree(root, cols, show="headings")
setup_tree_tags(tree)
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=110)

# data persis konvensi label: bulan lalu '25•'..'31•', bulan berjalan '1'..'31'
tgl_vals = ["25•", "26•", "30•", "31•", "1", "2", "15", "31"]
sat_vals = ["GR", "GR ", "GR", "PCS"]
for i in range(8):
    tree.insert("", "end", iid=f"r{i}",
                values=(tgl_vals[i], sat_vals[i % len(sat_vals)]))

# HeaderFilter NYATA dgn get_values = nilai TERFORMAT tree (kontrak view)
hf = widgets.HeaderFilter(
    tree, "Tanggal",
    get_values=lambda: [str(tree.set(i, "Tanggal")) for i in tree.get_children("")],
    on_apply=lambda sel: None, label="Tanggal")
hf2 = widgets.HeaderFilter(
    tree, "Satuan",
    get_values=lambda: [str(tree.set(i, "Satuan")) for i in tree.get_children("")],
    on_apply=lambda sel: None, label="Satuan")

hf.open_popup()
root.update_idletasks()

# urutan checkbox = urutan `values` yang diurutkan _filter_value_sort_key
tgl_order = list(hf._checks.keys())
print("Tanggal filter-list order :", tgl_order)

# pembanding: urutan kronologis konvensi app (in_selisih _parse_tgl_chrono)
def chrono(lbl):
    s = str(lbl).strip()
    lalu = s.endswith("•")
    if lalu:
        s = s[:-1]
    iv = int(float(s))
    if lalu and iv > 0:
        iv = -iv
    return (0, -iv) if iv < 0 else (1, iv)

chrono_order = sorted(tgl_vals, key=chrono)
print("Chronological expectation  :", chrono_order)
ok_chrono = tgl_order == sorted(tgl_order, key=chrono)
print("Filter-list chronological? ", ok_chrono)

hf._close()
hf2.open_popup()
root.update_idletasks()
sat_order = list(hf2._checks.keys())
print()
print("Satuan filter-list order   :", sat_order)
dupe = len(sat_order) != len(set(v.strip() for v in sat_order))
print("Distinct after strip       :", sorted(set(v.strip() for v in sat_order)))
print("Tampil sbg entri berbeda?  ", dupe, "( nilai:", sat_order, ")")
# sort key 'GR ' vs 'GR': apakah bersebelahan?
hf2._close()

print()
print("EXPECTED: Tanggal list kronologis (25•,26•,30•,31•,1,2,15,31) "
      "— konsisten dgn sort kolom v3.11.1; Satuan 1 entri 'GR'.")
print(f"ACTUAL: Tanggal={tgl_order}; Satuan={sat_order}.")
verdict_parts = []
if not ok_chrono:
    verdict_parts.append("BUG (P3): daftar nilai ⧩ kolom Tanggal TIDAK "
                         "kronologis — '1'..'15' duluan, blok '•' di tengah "
                         "(urutan display 1,15,2,25•,26•,30•,31•,31) — "
                         "tidak konsisten dgn sort kolom (v3.11.1) & export")
if dupe:
    verdict_parts.append("BUG (P3/UX): 'GR' vs 'GR ' tampil sbg DUA checkbox "
                         "identik — user tak bisa membedakan (nilai data "
                         "1-c p16: 'GR ' nyata di rekap user)")
print("VERDICT:", " | ".join(verdict_parts) if verdict_parts else "NOT-BUG")

root.destroy()
