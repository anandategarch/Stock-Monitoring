"""PROBE 1 — clone ⛶ opened while the MAIN tree's batched render is still
in-flight → clone copies only the PARTIAL tree (rows not yet inserted by
insert_tree_items are missing from the clone forever).

Real-world flow mirrored (deviasi_view):
    load_data -> _refresh (async compute) -> done -> _render_rows ->
    insert_tree_items(tree, items, batch=500, on_done=render_done)   # batched!
    ... user clicks "⛶ Layar Penuh" BETWEEN chunks (event loop is free) ->
    open_tree_maximized(self.tree, ...) snapshots get_children("") NOW.

open_tree_maximized never flushes/cancels a pending insert batch on the
SOURCE tree (it only manages its own copy batches), so _index("") sees only
the rows inserted so far.

EXPECTED : clone contains all 3000 rows (same as source table)
ACTUAL   : clone contains only the rows present at click time (~500)
"""
import sys
import time

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
from _harness import REPO, out  # noqa: E402

sys.path.insert(0, str(REPO))
import tkinter as tk  # noqa: E402
from src.ui.widgets import insert_tree_items, open_tree_maximized  # noqa: E402

N_ROWS = 3000
BATCH = 500

root = tk.Tk()
root.geometry("1200x800")

src_tree = tk.ttk.Treeview(root, columns=["Nama", "Val"], show="headings")
src_tree.heading("Nama", text="Nama")
src_tree.heading("Val", text="Val")
src_tree.pack(fill="both", expand=True)

items = [("", f"r{i}", {"values": (f"barang {i}", i)})
         for i in range(N_ROWS)]

state = {"render_done": False, "clone": None, "win": None,
         "rows_at_click": None}


def on_render_done():
    state["render_done"] = True


def on_chunk(n, total):
    # Simulates the user clicking ⛶ between insert chunks (this callback runs
    # in the same event-loop context a Button-1 handler would).
    if state["clone"] is None and n >= BATCH:
        state["rows_at_click"] = n
        win, clone = open_tree_maximized(src_tree, "Probe Deviasi")
        state["win"], state["clone"] = win, clone


cancel = insert_tree_items(src_tree, items, batch=BATCH, delay=10,
                           on_done=on_render_done, chunk_callback=on_chunk)

# Pump until: source render done AND clone copy finalized
t0 = time.monotonic()
while not (state["render_done"]
           and state["clone"] is not None
           and getattr(state["clone"], "_copy_finalized", False)):
    root.update()
    if time.monotonic() - t0 > 20:
        break
    time.sleep(0.005)

n_src = len(src_tree.get_children(""))
n_clone = len(state["clone"].get_children("")) \
    if state["clone"] is not None else -1

out(f"rows at click time : {state['rows_at_click']}")
out(f"source rows (final): {n_src}")
out(f"clone rows (final) : {n_clone}")
out(f"EXPECTED : clone rows == source rows == {N_ROWS}")
out(f"ACTUAL   : clone rows = {n_clone}, source rows = {n_src}")
verdict = "BUG" if (n_src == N_ROWS and 0 < n_clone < n_src) else "NOT-BUG"
out(f"VERDICT  : {verdict}")

try:
    state["win"].destroy()
except Exception:
    pass
root.destroy()
sys.exit(0 if verdict == "BUG" else 1)
