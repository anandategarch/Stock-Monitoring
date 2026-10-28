"""PROBE 5 — read-cache (src/pipeline/helpers.py _READ_CACHE*) thread-safety
stress: the cache IS reachable from >1 thread at a time (pipeline worker +
komparasi auto-load worker spawned from _on_pipeline_done can overlap a new
run's worker). Verify under bounded stress (2 threads x 200 ops):
  - no exception
  - accounting invariant: _READ_CACHE_CELLS == sum(entry.cells)
  - get() returns an independent copy (mutating it must not poison the cache)
  - invalidate keeps counter consistent

EXPECTED : all invariants hold
ACTUAL   : (see output)
"""
import random
import sys
import threading

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
from _harness import REPO, out  # noqa: E402

sys.path.insert(0, str(REPO))
import pandas as pd  # noqa: E402
from src.pipeline import helpers as hp  # noqa: E402

ERR = []
N_OPS = 200
DONE = threading.Barrier(3)


def worker(seed: int):
    rnd = random.Random(seed)
    try:
        for i in range(N_OPS):
            key = ("f%d.xlsx" % rnd.randrange(6), "S", 0, False)
            sig = (rnd.randrange(1000), rnd.randrange(10_000))
            df = pd.DataFrame({"a": [rnd.randrange(100)] * rnd.randrange(1, 9)})
            hp._read_cache_put(key, sig, df)
            got = hp._read_cache_get(key, sig)
            if got is not None:
                got.iloc[0, 0] = -999          # mutate the returned copy
            hp.read_cache_stats()
            if rnd.random() < 0.1:
                hp.read_cache_invalidate(["f%d.xlsx" % rnd.randrange(6)])
            if rnd.random() < 0.05:
                hp.read_cache_invalidate(None)
            hp.read_cache_reset_counters()
    except Exception as e:  # noqa: BLE001
        ERR.append(repr(e))
    finally:
        DONE.wait(10)


t1 = threading.Thread(target=worker, args=(1,))
t2 = threading.Thread(target=worker, args=(2,))
t1.start(); t2.start()
DONE.wait(15)
t1.join(5); t2.join(5)

with hp._READ_CACHE_LOCK:
    cells_sum = sum(e.get("cells", 0) for e in hp._READ_CACHE.values())
    counter = hp._READ_CACHE_CELLS
    consistent = (cells_sum == counter)
    nonneg = counter >= 0

# poison check: put a known frame, get it, mutate the copy, get again
k = ("poison.xlsx", "S", 0, False)
sig = (1, 1)
hp._read_cache_put(k, sig, pd.DataFrame({"a": [42]}))
c1 = hp._read_cache_get(k, sig)
c1.iloc[0, 0] = -1
c2 = hp._read_cache_get(k, sig)
unpoisoned = c2.iloc[0, 0] == 42

out(f"errors during stress        : {ERR if ERR else 'none'}")
out(f"cells counter == sum(entries): {consistent} ({counter} vs {cells_sum})")
out(f"counter >= 0                 : {nonneg}")
out(f"get() returns private copy   : {unpoisoned}")
ok = (not ERR) and consistent and nonneg and unpoisoned
out("EXPECTED : no errors, accounting consistent, copies private")
out(f"ACTUAL   : errors={bool(ERR)}, consistent={consistent}, "
    f"nonneg={nonneg}, unpoisoned={unpoisoned}")
out("VERDICT  :", "NOT-BUG" if ok else "BUG")
sys.exit(0 if ok else 1)
