"""PROBE 2 — header SORT on a clone ⛶ while the clone's own copy batch is
still inserting → final clone order is a MIX (sorted head + original-order
tail), permanently (nothing re-sorts afterwards).

v3.11.1 fixed sort-vs-sort (sort_tree_by_column flushes tree.
_sort_insert_cancel) and v3.9.72 fixed filter-vs-copy (apply_tree_row_
filters cancels tree._row_filter_cancel) — but SORT-vs-COPY is NOT covered:
sort_tree_by_column never touches _row_filter_cancel (the clone copy batch
handle), so it snapshots the PARTIAL tree, sorts it, and the copy's
remaining chunks keep appending unsorted rows afterwards.

In the real app the clone's funnel/sort bindings are installed immediately
(open_tree_maximized calls on_filter_setup BEFORE the copy starts) and the
event loop is free between copy chunks, so a heading click mid-copy is
reachable.

EXPECTED : final clone order fully sorted descending by 'Val' + 3000 rows
ACTUAL   : first K rows sorted, then the untouched tail in original order
"""
import sys
import time

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
from _harness import REPO, out  # noqa: E402

sys.path.insert(0, str(REPO))
import tkinter as tk  # noqa: E402
from src.ui.widgets import open_tree_maximized, sort_tree_by_column  # noqa: E402

N_ROWS = 3000

root = tk.Tk()
root.geometry("1200x800")

src_tree = tk.ttk.Treeview(root, columns=["Nama", "Val"], show="headings")
src_tree.heading("Nama", text="Nama")
src_tree.heading("Val", text="Val")
src_tree.pack(fill="both", expand=True)

# ascending values — any descending sort must visibly reorder everything
for i in range(N_ROWS):
    src_tree.insert("", "end", iid=f"r{i}",
                    values=(f"barang {i}", i))

win, clone = open_tree_maximized(src_tree, "Probe Deviasi")

state = {"sorted": False, "rows_at_sort": None}


def maybe_sort():
    """Poll like a user click landing between copy insert chunks."""
    if not state["sorted"]:
        n = len(clone.get_children(""))
        if 0 < n < N_ROWS:
            state["rows_at_sort"] = n
            state["sorted"] = True
            # heading click on the clone -> view's on_sort -> _sort_by(tree=clone)
            sort_tree_by_column(clone, "Val", reverse=True)
    if not getattr(clone, "_copy_finalized", False):
        root.after(2, maybe_sort)


root.after(2, maybe_sort)

t0 = time.monotonic()
while not getattr(clone, "_copy_finalized", False):
    root.update()
    if time.monotonic() - t0 > 20:
        break
    time.sleep(0.002)
# let the sort's own batched insert finish too
t0 = time.monotonic()
while time.monotonic() - t0 < 1.0:
    root.update()
    time.sleep(0.002)

kids = list(clone.get_children(""))
vals = [clone.item(k)["values"][1] for k in kids]
n_clone = len(kids)
fully_sorted = all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))

out(f"rows present at sort click: {state['rows_at_sort']}")
out(f"clone rows (final)       : {n_clone}")
out(f"first 5 vals : {vals[:5]}  last 5 vals : {vals[-5:]}")
out(f"EXPECTED : 3000 rows AND fully sorted descending (all vals[i] >= vals[i+1])")
out(f"ACTUAL   : {n_clone} rows, fully_sorted={fully_sorted}")
verdict = "BUG" if (n_clone == N_ROWS and not fully_sorted) else "NOT-BUG"
out(f"VERDICT  : {verdict}")

try:
    win.destroy()
except Exception:
    pass
root.destroy()
sys.exit(0 if verdict == "BUG" else 1)
