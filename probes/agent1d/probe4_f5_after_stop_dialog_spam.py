"""PROBE 4 — F5/Ctrl+R keyboard auto-repeat AFTER ⏹ Stop (worker still
alive, is_running already False) → MODAL "Masih Menghentikan" dialog per
keypress — contradicting the handler's own contract
(app.py _on_run_shortcut: "no-op senyap saat sedang berjalan — TANPA dialog
spam, beda dgn klik tombol yang informatif — anti dialog spam dari
keyboard repeat").

While is_running is True the shortcut IS silent (verified here as the
NOT-BUG control). The stopping phase (⏹ clicked, worker walking to its
checkpoint — can take seconds on big files) falls through to
_start_pipeline's guard-2 messagebox: holding F5 during that window spams
one modal dialog per auto-repeat event (~30/s), each running its own modal
event loop.

EXPECTED : F5 auto-repeat after ⏹ → 0 modal dialogs (silent no-op like the
           running phase)
ACTUAL   : 1 modal dialog per keypress
"""
import sys
import time

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

H.out("building app…")
tmp = H.make_tmp_base()

import src.ui.app as appmod  # noqa: E402

dialogs = {"info": 0}
appmod.messagebox.showinfo = lambda *a, **k: dialogs.__setitem__(
    "info", dialogs["info"] + 1)
appmod.messagebox.showwarning = lambda *a, **k: None
appmod.messagebox.showerror = lambda *a, **k: None

fake = H.FakePipeline()
root, app = H.make_app(tmp)

app._start_pipeline(refresh_files=False)
H.out("run started: is_running =", app.is_running,
      "worker alive =", app.worker_thread.is_alive())

# --- control: F5 auto-repeat while is_running=True -------------------------
for _ in range(3):
    app._on_run_shortcut()
H.out("F5 x3 while RUNNING      -> dialogs:", dialogs["info"],
      "(EXPECTED 0 — silent no-op)")

# --- the case: ⏹ clicked, worker still walking to its checkpoint ----------
app._stop_pipeline()
H.out("STOP clicked: is_running =", app.is_running,
      "worker alive =", app.worker_thread.is_alive())
for _ in range(3):
    app._on_run_shortcut()
n_after = dialogs["info"]
H.out("F5 x3 after STOP (worker still alive) -> dialogs:", n_after)

root.update()
fake.release_run2.set()          # let the (single) run finish
t0 = time.monotonic()
while app.worker_thread.is_alive() and time.monotonic() - t0 < 10:
    root.update()
    time.sleep(0.005)
root.update()
root.destroy()

H.out("EXPECTED : 0 dialogs for keyboard auto-repeat in the stopping phase")
H.out(f"ACTUAL   : {n_after} modal dialogs "
      f"(1 per keypress; plus {0} while running — control)")
verdict = "BUG" if n_after > 0 else "NOT-BUG"
H.out("VERDICT  :", verdict)
sys.exit(0 if verdict == "BUG" else 1)
