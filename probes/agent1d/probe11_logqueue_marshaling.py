"""PROBE 11 — StreamToQueue → _poll_log_queue marshaling: pipeline worker
threads print via redirected stdout; the main-thread poller drains with
caps (MAX_CHUNKS_PER_POLL=200 chunks / MAX_CHARS_PER_POLL=50k chars per
pass). Verify:
  - nothing is ever DROPPED (chunks beyond the cap stay queued and arrive
    on a later poll)
  - per-producer ORDER is preserved (queue FIFO)
  - the poller keeps rescheduling (finally-block fix v3.9.42) — a raising
    handler body must not kill the poll loop permanently

EXPECTED : all lines arrive in order; poll survives a handler exception
ACTUAL   : (see output)
"""
import sys
import threading

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

tmp = H.make_tmp_base()
import src.ui.app as appmod  # noqa: E402

root, app = H.make_app(tmp)

N_PER = 150            # 2 producers x 150 > 200-chunk cap → spillover
lines_sent = []
lock = threading.Lock()


def producer(tag):
    for i in range(N_PER):
        s = f"[{tag}] line {i:04d}\n"
        with lock:
            lines_sent.append((tag, i))
        print(s, end="")


t1 = threading.Thread(target=producer, args=("A",))
t2 = threading.Thread(target=producer, args=("B",))
t1.start(); t2.start(); t1.join(); t2.join()

# one poll pass = capped drain
app._poll_log_queue()
queued_after_one = app.log_queue.qsize()
H.out(f"queue size after ONE capped poll pass: {queued_after_one} "
      f"(cap = {appmod.MAX_CHUNKS_PER_POLL} chunks)")

# poll to exhaustion
for _ in range(40):
    if app.log_queue.qsize() == 0:
        break
    app._poll_log_queue()
H.out(f"queue size after polling to exhaustion: {app.log_queue.qsize()}")

content = app.log_text.get("1.0", "end-1c")
got_a = [ln for ln in content.splitlines() if ln.startswith("[A] line")]
got_b = [ln for ln in content.splitlines() if ln.startswith("[B] line")]


def seq(lines):
    return [int(ln.rsplit(" ", 1)[1]) for ln in lines]


ok_count = (len(got_a) == N_PER and len(got_b) == N_PER)
ok_order = (seq(got_a) == sorted(seq(got_a))
            and seq(got_b) == sorted(seq(got_b)))
H.out(f"lines arrived: A={len(got_a)}/{N_PER} B={len(got_b)}/{N_PER}; "
      f"per-producer order preserved: {ok_order}")

# --- poller must survive an exception in the handler body -----------------
app.log_text.configure(state="normal")
app.log_text.delete("1.0", "end")
app.log_text.configure(state="disabled")
real_append = app._append_log_batched
app._append_log_batched = lambda text: (_ for _ in ()).throw(
    RuntimeError("boom"))
n_scheduled = len(root.tk.call("after", "info"))
try:
    app._poll_log_queue()          # body raises -> finally must reschedule
except RuntimeError:
    pass
app._append_log_batched = real_append
after_ids = root.tk.call("after", "info")
rescheduled = len(after_ids) > 0
H.out(f"poller rescheduled after handler exception: {rescheduled} "
      f"(pending timers: {len(after_ids)})")

ok = ok_count and ok_order and rescheduled and queued_after_one > 0
H.out("EXPECTED : no loss, per-producer order kept, poller survives errors")
H.out(f"ACTUAL   : count_ok={ok_count} order_ok={ok_order} "
      f"rescheduled={rescheduled} spillover_queued={queued_after_one > 0}")
H.out("VERDICT  :", "NOT-BUG" if ok else "BUG")
root.destroy()
sys.exit(0 if ok else 1)
