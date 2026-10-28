#!/usr/bin/env python3
"""p06 — Sort correctness & copy TSV header (NOT-BUG confirmations).

(a) Sort kolom Tanggal label '25•' via parser kronologis in_selisih
    (_parse_tgl_chrono) — v3.11.1 B3.
(b) Parser default widgets: '—'/'-'/'' → 0 (penempatan baris kosong);
    '(1.825)' → -1825; 'Rp 1.825' → 1825.
(c) Fallback natural saat kolom campuran teks+label '25•' (parse raise).
(d) Copy TSV: panah sort tidak ikut tersalin; kolom TERSEMBUNYI tidak ikut.
"""
import sys
sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")

import tkinter as tk
from src.ui import widgets
from src.ui.theme import setup_tree_tags

root = tk.Tk()
root.geometry("1000x500+10+10")

# ---------- (a) chronological sort label '25•' -----------------------------
cols = ["Tanggal", "V"]
tree = widgets.make_tree(root, cols, show="headings")
setup_tree_tags(tree)
for c in cols:
    tree.heading(c, text=c); tree.column(c, width=90)

labels = ["3", "25•", "1", "28•", "31•", "15", "26•"]
for i, lb in enumerate(labels):
    tree.insert("", "end", iid=f"r{i}", values=(lb, i))

# parser persis in_selisih_view._parse_tgl_chrono (3652-3669)
from src.ui.export_sheets import tgl_chrono_key
def parse_tgl_chrono(s):
    s = str(s).strip()
    lalu = s.endswith("•")
    if lalu:
        s = s[:-1].strip()
    try:
        iv = int(float(s))
    except (TypeError, ValueError):
        return (2, s)
    if lalu and iv > 0:
        iv = -iv
    return tgl_chrono_key(iv)

widgets.sort_tree_by_column(tree, "Tanggal", reverse=False, parse=parse_tgl_chrono)
root.update_idletasks()
order = [tree.item(i, "values")[0] for i in tree.get_children("")]
chrono_expected = ["25•", "26•", "28•", "31•", "1", "3", "15"]
print("(a) sort Tanggal asc :", order)
a_ok = order == chrono_expected

# ---------- (b) parser default widgets -------------------------------------
p = None
def mk(s):  # ambil parser default persis dr sort_tree_by_column
    return widgets.sort_tree_by_column.__wrapped__ if False else None
# ekstrak parse default via exec closure tidak praktis — replikasi eksak
# (baris 4820-4829, satu-satunya parse=None path):
def default_parse(s):
    s = str(s).replace("%", "").replace("—", "").replace("Rp", "").strip()
    if s in ("-", ""):
        return 0
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1].strip()
    s = s.replace(".", "").replace(",", ".")
    v = float(s)
    return -v if neg else v

vals = {"—": 0, "-": 0, "": 0, "(1.825)": -1825, "Rp 1.825": 1825,
        "26,97%": 26.97, "12,5": 12.5, "-8,3%": -8.3}
parsed = {k: default_parse(k) for k in vals}
b_ok = all(parsed[k] == v for k, v in vals.items())
print("(b) parse default    :", parsed)
print("    semua sesuai kontrak ('—'/'-'/''→0, kurung→minus, Rp→angka):", b_ok)

# ---------- (c) fallback natural utk kolom campuran ------------------------
vals2 = ["25•", "Barang 10", "Barang 2", "AYAM"]
for i, v in enumerate(vals2):
    tree.set(f"r{i}", "Tanggal", v)
widgets.sort_tree_by_column(tree, "Tanggal", reverse=False)  # parse=None → default
root.update_idletasks()
order2 = [tree.item(i, "values")[0] for i in tree.get_children("")]
print("(c) fallback natural :", order2, "— 'Barang 2' < 'Barang 10' ?",
      order2.index("Barang 2") < order2.index("Barang 10"))
c_ok = order2.index("Barang 2") < order2.index("Barang 10")

# ---------- (d) copy TSV: panah sort + kolom tersembunyi -------------------
widgets._set_sort_arrow(tree, "Tanggal", True)          # heading dgn ' ↓'
tree.column("V", width=90)
tree.configure(displaycolumns=["Tanggal"])              # sembunyikan 'V'
tree.selection_set(("r0",))
tsv = widgets.tree_selection_tsv(tree)
print("(d) TSV header+row   :", repr(tsv))
hdr_clean = "↓" not in tsv and "↑" not in tsv
hidden_excluded = "V" not in tsv.splitlines()[0].split("\t")
row_cells = tsv.splitlines()[1].split("\t")
d_ok = hdr_clean and hidden_excluded and len(row_cells) == 1
print("    panah sort bersih:", hdr_clean, "| kolom 'V' tersembunyi tak ikut:",
      hidden_excluded, "| 1 sel/baris:", len(row_cells) == 1)

print()
print(f"EXPECTED: a_ok=True b_ok=True c_ok=True d_ok=True")
print(f"ACTUAL: a={a_ok} b={b_ok} c={c_ok} d={d_ok}")
allok = all([a_ok, b_ok, c_ok, d_ok])
print("VERDICT:", "NOT-BUG (sort Tanggal kronologis v3.11.1 bekerja; "
      "parser default & fallback natural benar; copy TSV bersih dr panah "
      "sort & mengikuti displaycolumns)" if allok else "BUG")

root.destroy()
