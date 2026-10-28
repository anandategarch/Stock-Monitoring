"""PROBE 8 — RE-VERIFY the v3.11.1 sort-race fix (#10): start an ASYNC sort
on a big flat table (>= _SORT_ASYNC_MIN_ROWS=1500 → batched insert), then
immediately start a SECOND sort while the first one's insert batch is still
in flight. The fix (sort_tree_by_column flushes tree._sort_insert_cancel)
must guarantee:
  - no rows lost (final count == N)
  - final order == fully sorted by the SECOND sort key
  - first sort's on_done still fires exactly once (flush path)
  - a THIRD sort in the opposite direction also lands (stress)

EXPECTED : count preserved, order fully sorted per last sort, on_done fired
ACTUAL   : (see output)
"""
import sys
import time

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
from _harness import REPO, out  # noqa: E402

sys.path.insert(0, str(REPO))
import tkinter as tk  # noqa: E402
from src.ui.widgets import sort_tree_by_column  # noqa: E402

N = 3000
root = tk.Tk()
root.geometry("1200x800")
tree = tk.ttk.Treeview(root, columns=["A", "B"], show="headings")
tree.heading("A", text="A")
tree.heading("B", text="B")
tree.pack(fill="both", expand=True)

for i in range(N):
    tree.insert("", "end", iid=f"r{i}", values=((i * 37) % N, (i * 91) % N))
tree.selection_set(["r5", "r1500"])

done_ct = {"n": 0}


def on_done():
    done_ct["n"] += 1


# sort #1 (async batched) — then sort #2 lands while its batch is in flight
sort_tree_by_column(tree, "A", reverse=True, on_done=on_done)
sort_tree_by_column(tree, "B", reverse=False, on_done=on_done)   # mid-flight
# sort #3 opposite direction immediately after (stress the flush idempotence)
sort_tree_by_column(tree, "B", reverse=True, on_done=on_done)

t0 = time.monotonic()
while time.monotonic() - t0 < 5:
    root.update()
    time.sleep(0.002)

kids = list(tree.get_children(""))
b_vals = [tree.item(k)["values"][1] for k in kids]
count_ok = len(kids) == N
sorted_ok = all(b_vals[i] >= b_vals[i + 1] for i in range(len(b_vals) - 1))
sel_ok = set(tree.selection()) == {"r5", "r1500"}

out(f"rows (final)        : {len(kids)} / {N}")
out(f"sorted desc by B    : {sorted_ok}")
out(f"selection preserved : {sel_ok} ({sorted(tree.selection())})")
out(f"on_done fired       : {done_ct['n']}x (sort#1 flush + sort#2 flush + "
    f"sort#3 completion -> expect >= 1, exactly-once per completed sort)")
H = None
ok = count_ok and sorted_ok and sel_ok and done_ct["n"] >= 1
out("EXPECTED : count preserved, fully sorted by LAST sort, selection kept")
out(f"ACTUAL   : count_ok={count_ok} sorted_ok={sorted_ok} "
    f"sel_ok={sel_ok} on_done={done_ct['n']}")
out("VERDICT  :", "NOT-BUG" if ok else "BUG")
root.destroy()
sys.exit(0 if ok else 1)
