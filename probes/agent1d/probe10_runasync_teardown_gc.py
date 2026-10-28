"""PROBE 10 — run_async teardown & GC-shield release (audit 19-c #1 fix
re-verified): destroy the OWNING widget while work() is still running in its
worker thread →
  - poll (hosted on root) must still release the GC shield once the thread
    dies (gc.disable() must NOT stick forever)
  - on_done/on_error must NOT run (widget gone)
  - no TclError escapes, process stays alive

Also verifies _spawn_worker bookkeeping stays bounded (<= _MAX_KEPT_THREADS
kept + 20).

EXPECTED : gc re-enabled after teardown; no callback fires; no crash
ACTUAL   : (see output)
"""
import gc
import sys
import threading
import time

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
from _harness import REPO, out  # noqa: E402

sys.path.insert(0, str(REPO))
import tkinter as tk  # noqa: E402
from src.ui import widgets as W  # noqa: E402

root = tk.Tk()
root.geometry("1000x700")

results = []
for i in range(6):
    top = tk.Toplevel(root)
    tree = tk.ttk.Treeview(top, columns=["a"])
    tree.pack()

    release = threading.Event()
    ran = {"done": False, "err": False}

    def work(release=release):
        release.wait(5)
        return 42

    def done(v, ran=ran):
        ran["done"] = True

    def on_error(e, ran=ran):
        ran["err"] = True

    gc_was = gc.isenabled()
    job = W.run_async(tree, work, done, on_error=on_error)
    root.update()
    top.destroy()                 # owner destroyed MID-work
    root.update()
    # let the worker finish, pump the host-root poll (70ms)
    release.set()
    t0 = time.monotonic()
    while time.monotonic() - t0 < 3:
        root.update()
        if not job["_thread"].is_alive():
            # one extra pump cycle for the poll to fire
            t1 = time.monotonic()
            while time.monotonic() - t1 < 0.3:
                root.update()
                time.sleep(0.01)
            break
        time.sleep(0.01)
    gc_now = gc.isenabled()
    ok = (gc_now and not ran["done"] and not ran["err"])
    results.append((f"iter {i}: gc_enabled={gc_now} done_fired={ran['done']} "
                    f"err_fired={ran['err']}", ok))

kept = len(W._worker_threads)
all_ok = all(ok for _, ok in results) and kept <= W._MAX_KEPT_THREADS + 20
for label, ok in results:
    out(f"[{'OK ' if ok else 'FAIL'}] {label}")
out(f"spawned-thread bookkeeping: kept={kept} "
    f"(cap {W._MAX_KEPT_THREADS}, hard-bounded list)")
out("EXPECTED : gc re-enabled, no callbacks after teardown, no crash")
out(f"ACTUAL   : all_iters_ok={all(ok for _, ok in results)}, kept={kept}")
out("VERDICT  :", "NOT-BUG" if all_ok else "BUG")
root.destroy()
sys.exit(0 if all_ok else 1)
