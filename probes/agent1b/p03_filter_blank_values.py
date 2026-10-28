#!/usr/bin/env python3
"""p03 — Nilai KOSONG ('') di daftar nilai popup filter ⧩ + apply_tree_row_filters.

widgets.HeaderFilter.open_popup membangun daftar nilai:
    sorted({str(v) for v in get_values() if str(v) and str(v) != "nan"})
→ baris dgn sel kosong (NaN diformat '' oleh _fmt_num deviasi/popup dll.)
TIDAK PERNAH muncul sbg entri. Konsekuensi:
  (a) user membuka ⧩ kolom itu, mencentang SEMUA nilai yang tampil →
      apply_tree_row_filters membuang baris kosong SENYAP
      (v='' tidak ada di sel terpilih);
  (b) kolom yang SEMUA-nya kosong → "Tidak ada nilai yang bisa difilter"
      (showinfo — tidak bisa dibuka sama sekali).
Excel AutoFilter punya checkbox "(Blanks)".
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import tkinter as tk
from src.ui import widgets
from src.ui.theme import setup_tree_tags

root = tk.Tk()
root.geometry("900x400+10+10")

cols = ["Nama Barang", "Deviasi"]
tree = widgets.make_tree(root, cols, show="headings")
setup_tree_tags(tree)
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=130)

# Deviasi diformat _fmt_num deviasi: NaN→'', 0→'-', -5→'(5)'
rows = [("BEBEK", "(5)"), ("AYAM", "-"), ("CITRA", ""), ("GULA", "10")]
for i, (nm, dv) in enumerate(rows):
    tree.insert("", "end", iid=f"r{i}", values=(nm, dv))

hf = widgets.HeaderFilter(
    tree, "Deviasi",
    get_values=lambda: [str(tree.set(i, "Deviasi")) for i in tree.get_children("")],
    on_apply=lambda sel: None, label="Deviasi")

hf.open_popup()
root.update_idletasks()
shown = list(hf._checks.keys())
print("Daftar nilai ⧩ kolom Deviasi :", shown)
print("Baris dgn sel kosong ('')    : CITRA")
blank_listed = "" in hf._all_values
print("'' masuk daftar?             :", blank_listed)
hf._close()

# --- simulasikan user "centang semua yang tampil" lalu APPLY -------------
sel_all_visible = set(shown)                    # semua nilai yang DITAWARKAN
cancel = widgets.apply_tree_row_filters(tree, {"Deviasi": sel_all_visible})
root.update()                                    # selesaikan batch insert sinkron
remaining = [tree.item(i, "values")[0] for i in tree.get_children("")]
print()
print("User mencentang SEMUA nilai yang ditawarkan:", sorted(sel_all_visible))
print("Baris tersisa di tree                     :", remaining)
citra_kept = "CITRA" in remaining
print("CITRA (Deviasi kosong) bertahan?           :", citra_kept)

# --- kolom yang seluruhnya kosong -----------------------------------------
tree2 = widgets.make_tree(root, ["Nama Barang", "X"], show="headings")
setup_tree_tags(tree2)
tree2.heading("X", text="X"); tree2.column("X", width=80)
for i, nm in enumerate(["A", "B"]):
    tree2.insert("", "end", iid=f"s{i}", values=(nm, ""))
hf2 = widgets.HeaderFilter(
    tree2, "X",
    get_values=lambda: [str(tree2.set(i, "X")) for i in tree2.get_children("")],
    on_apply=lambda sel: None, label="X")
import src.ui.widgets as W
_msgs = []
_orig_showinfo = W._mb.showinfo
W._mb.showinfo = lambda *a, **k: (_msgs.append((a, k)), "ok")[1]
hf2.open_popup()
W._mb.showinfo = _orig_showinfo
print()
print("Kolom X (semua sel kosong) → open_popup memunculkan pesan:",
      [m[0][1] for m in _msgs])
popup_opened = hf2._popup is not None and hf2._popup.winfo_exists()
print("Popup nilai terbuka? :", popup_opened)

print()
print("EXPECTED: '' terwakili (mis. checkbox '(Kosong)' ala Excel) — "
      "centang-semua mempertahankan SEMUA 4 baris; kolom all-blank tetap "
      "bisa dibuka (atau minimal diberi tahu jumlah baris kosong).")
print(f"ACTUAL: daftar={shown} (tanpa ''); centang-semua → baris "
      f"tersisa {remaining} (CITRA HILANG senyap); kolom all-blank → "
      f"showinfo {_msgs[0][0][1] if _msgs else None}, popup={popup_opened}.")
ok = blank_listed and citra_kept and popup_opened
print("VERDICT:", "NOT-BUG" if ok else
      "BUG (P3 — UX): nilai kosong tak terwakili di ⧩; "
      "'centang semua nilai yang ada' membuang baris sel-kosong senyap; "
      "kolom all-blank tak bisa difilter sama sekali (tidak ada jalur "
      "memilih/mengecualikan baris kosong)")

root.destroy()
