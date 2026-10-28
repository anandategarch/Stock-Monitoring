"""PROBE 7 — follow-up JSON debounce (v3.9.72 FIX 3): a ✓-toggle executed
in deferred mode (dirty flag set, NO write yet) must be FLUSHED when the
FollowUpView is destroyed (<Destroy> binding → _on_view_destroy →
store.flush_saves()), incl. the app-close path (root.destroy()). Without
the flush, toggles made <200ms before close are lost.

Sequence tested:
  1. seed followup.json with 1 row (synchronous toggle path)
  2. deferred toggle (removes the row) — simulates the view's
     _toggle_row_incremental defer window — then DESTROY the view
     IMMEDIATELY (before the 200ms debounce fires)
  3. verify followup.json reflects the removal (flush happened)
  4. re-add a row deferred, then root.destroy() (app close path)
  5. verify flush again + timers cancelled without TclError

EXPECTED : file state matches memory after destroy in both paths
ACTUAL   : (see output)
"""
import sys

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

tmp = H.make_tmp_base()
import tkinter as tk  # noqa: E402
from src.ui.followup import FollowUpStore, followup_path, row_fingerprint  # noqa: E402
from src.ui.followup_view import FollowUpView  # noqa: E402

root = tk.Tk()
root.geometry("1200x800")

store = FollowUpStore()
row = {"asal": "DEVIASI GR", "resto": "R1", "barang": "B1",
       "satuan": "GR", "h": 25, "so": 10, "sistem": 4, "deviasi": -6,
       "cek": "RI Balancing"}
fp = row_fingerprint(row)
store.toggle(fp, row)                       # synchronous save (2 files)
H.out("seeded rows:", len(store.rows),
      "| file rows:", len(H.read_json(followup_path())["rows"]))

view = FollowUpView(root, store, get_data=lambda: None,
                    go_to_proses=None)
view.pack(fill="both", expand=True)
root.update()

# ---- deferred toggle (the view's own ✓-click path) + IMMEDIATE destroy ----
store.set_defer_saves(True)
store.toggle(fp, row)                       # marks dirty, no write
store.set_defer_saves(False)
n_file_before = len(H.read_json(followup_path())["rows"])
view.destroy()                              # <Destroy> -> flush_saves()
root.update()
d1 = H.read_json(followup_path())["rows"]
ok1 = (len(d1) == 0 and n_file_before == 1)
H.out(f"deferred toggle + view.destroy(): file had {n_file_before} row(s) "
      f"before destroy, {len(d1)} after (memory: {len(store.rows)})")

# ---- app-close path: deferred re-add + root.destroy() ---------------------
store.set_defer_saves(True)
store.toggle(fp, row)                       # re-add, deferred
store.set_defer_saves(False)
view2 = FollowUpView(root, store, get_data=lambda: None, go_to_proses=None)
view2.pack(fill="both", expand=True)
root.update()
# simulate the view scheduling its 200ms debounce then the app closing
try:
    view2._save_after = view2.after(200, view2._flush_followup_saves)
except Exception as e:  # noqa: BLE001
    H.out("scheduling debounce failed:", repr(e))
root.destroy()                              # pending after() dropped, <Destroy> fires
d2 = H.read_json(followup_path())["rows"]
ok2 = len(d2) == 1 and d2.get(fp, {}).get("resto") == "R1"
H.out(f"deferred re-add + root.destroy(): file rows after close = {len(d2)} "
      f"(memory: {len(store.rows)})")

H.out("EXPECTED : followup.json == memory state after destroy in BOTH paths")
H.out(f"ACTUAL   : path1 ok={ok1}, path2 ok={ok2}")
ok = ok1 and ok2
H.out("VERDICT  :", "NOT-BUG" if ok else "BUG")
sys.exit(0 if ok else 1)
