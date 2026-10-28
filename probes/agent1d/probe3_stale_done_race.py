"""PROBE 3 — STALE _on_pipeline_done races a NEW run started via F5 in the
gap between worker-thread death and the after(0) callback firing.

Window (real app): user clicks ⏹ Stop (is_running=False, MULAI still
disabled, but F5/Ctrl+R is bind_all and only checks is_running), then a
main-thread handler is busy (e.g. zoom-burst refit ~60ms, batched insert
chunk) while the worker hits its stop checkpoint, schedules
root.after(0, _on_pipeline_done) and dies. The F5 keypress event is
already queued → Tcl services the queued X event BEFORE the not-yet-
enqueued timer event → _start_pipeline passes BOTH guards (is_running
False, old worker dead) → run #2 starts. THEN the stale after(0) fires
_on_pipeline_done of run #1 → it cancels run #2's elapsed timer, stops
progress/spinner, sets is_running=False and disables ⏹ — run #2 becomes
UNSTOPPABLE (its ⏹ is dead: _stop_pipeline guards on is_running).

Deterministic simulation: _schedule_to_main is monkeypatched to CAPTURE the
callback instead of letting the (real) event loop run it — this pins the
interleaving "worker finished, callback not yet delivered".

EXPECTED : during run #2: is_running True, ⏹ enabled, elapsed timer alive,
           ⏹ still able to stop run #2 (stop_event gets set)
ACTUAL   : is_running False, ⏹ disabled, _elapsed_after_id None (tick loop
           killed), _stop_pipeline() is a NO-OP — run #2 unstoppable
"""
import sys
import threading
import time

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

H.out("building app (isolated tmp persistence)…")
tmp = H.make_tmp_base()

import tkinter as tk  # noqa: E402
import src.ui.app as appmod  # noqa: E402

# silence modal dialogs
dialogs = {"info": 0, "warn": 0, "error": 0}
appmod.messagebox.showinfo = lambda *a, **k: dialogs.__setitem__(
    "info", dialogs["info"] + 1)
appmod.messagebox.showwarning = lambda *a, **k: dialogs.__setitem__(
    "warn", dialogs["warn"] + 1)
appmod.messagebox.showerror = lambda *a, **k: dialogs.__setitem__(
    "error", dialogs["error"] + 1)

fake = H.FakePipeline()
H.out("fake run_pipeline installed:", appmod.run_pipeline == fake._run)

root, app = H.make_app(tmp)

# ---- capture scheduled main-thread callbacks (deterministic interleave) ----
pending = []
app._schedule_to_main = lambda fn: pending.append(fn)


def run_pending():
    while pending:
        pending.pop(0)()


# ---------- run #1: started, then stopped by user ----------
app._start_pipeline(refresh_files=False)
H.out("run1 started: is_running =", app.is_running,
      "worker alive =", app.worker_thread.is_alive())
H.out("toplevel dialogs so far (none expected):", dialogs["info"])

app._stop_pipeline()                      # user clicks ⏹
H.out("after STOP click: is_running =", app.is_running)

app.worker_thread.join(10)                # worker hits checkpoint & dies
H.out("run1 worker dead. stale callbacks captured:", len(pending))
assert app.worker_thread is not None and not app.worker_thread.is_alive()

# ---------- the race: F5 lands before the stale callback is delivered ------
app._on_run_shortcut()                    # F5 — only checks is_running
H.out("F5 pressed: dialog count =", dialogs["info"],
      "| new worker alive =",
      app.worker_thread.is_alive() if app.worker_thread else None)
run2 = app.worker_thread
assert run2 is not None and run2.is_alive()
H.out("run2 running: is_running =", app.is_running)

# ---------- the stale after(0) from run #1 finally fires -------------------
H.out("delivering STALE _on_pipeline_done of run #1 …")
run_pending()

stop_state = str(app.btn_stop.cget("state"))
elapsed_alive = app._elapsed_after_id is not None
running_during = app.is_running   # v3.11.10: simpan SEBELUM ⏹ — _stop_pipeline memang menurunkan is_running
H.out(f"state during run #2 : is_running={running_during} "
      f"btn_stop={stop_state} elapsed_after_id_set={elapsed_alive}")

# can the user still stop run #2?
app._stop_pipeline()
stoppable = app.stop_event.is_set()
H.out("⏹ clicked during run #2 → stop_event set?", stoppable)

ok_state = (running_during is True and stop_state == "normal"
            and elapsed_alive and stoppable)
H.out("EXPECTED : is_running=True, btn_stop=normal, elapsed timer alive, "
      "stop works")
H.out(f"ACTUAL   : is_running={running_during}, btn_stop={stop_state}, "
      f"elapsed_after_id_set={elapsed_alive}, stop works={stoppable}")
verdict = "NOT-BUG" if ok_state else "BUG"
H.out("VERDICT  :", verdict)

# ---------- cleanup: let run #2 finish, deliver its callbacks --------------
fake.release_run2.set()
t0 = time.monotonic()
while run2.is_alive() and time.monotonic() - t0 < 10:
    root.update()
    time.sleep(0.005)
run_pending()
while pending:
    run_pending()
root.update()
H.out("run2 finished; state recovered: is_running =", app.is_running,
      "btn_mulai =", str(app.btn_mulai.cget("state")))
root.destroy()
sys.exit(0 if verdict == "BUG" else 1)
