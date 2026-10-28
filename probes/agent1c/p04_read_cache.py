"""P04 — read-cache accounting re-verification (v3.9.69/v3.9.70 fixed twice).

Aggressive probe against helpers._READ_CACHE*:
 (a) counter == sum(cells of entries in dict) after EVERY operation
 (b) same-key replacement (old entry popped, counted ONCE)
 (c) oversize frame rejected WITHOUT evicting others (v3.9.70 claim)
 (d) FIFO eviction order honors dict insertion order
 (e) read_cache_invalidate(paths) partial drop accounting
 (f) full invalidate resets counter to 0
 (g) mutation isolation: caller mutating the returned copy never taints the
     cached frame (cache hit path returns .copy())
 (h) sig mismatch => miss (file changed -> re-read path)
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT

sys.path.insert(0, PROJECT)
from src.pipeline import helpers as H  # noqa: E402


def reset(cells_max=100):
    H._READ_CACHE.clear()
    H._READ_CACHE_CELLS = 0
    H._READ_CACHE_MAX_CELLS = cells_max
    H._READ_CACHE_HIT_FILES.clear()
    H._READ_CACHE_MISS_FILES.clear()


def invariant(tag):
    total = sum(e["cells"] for e in H._READ_CACHE.values())
    ok = total == H._READ_CACHE_CELLS and total <= H._READ_CACHE_MAX_CELLS
    print(f"  [{tag}] counter={H._READ_CACHE_CELLS} dictsum={total} "
          f"entries={list(H._READ_CACHE)} -> "
          f"{'OK' if ok else 'VIOLATION'}")
    return ok


def df_of(rows, cols):
    return pd.DataFrame([[f"v{r}{c}" for c in range(cols)] for r in range(rows)],
                        dtype=object)


def main():
    print("=== (a)+(b) same-key replacement, counter counted once ===")
    reset(100)
    kA = ("a.xlsx", "S", 0, False)
    sig = (1, 10)
    H._read_cache_put(kA, sig, df_of(5, 4))          # 20 cells
    ok_a = invariant("put A=20")
    H._read_cache_put(kA, sig, df_of(10, 5))         # replace A -> 50
    ok_a &= invariant("replace A=50")
    # v3.9.69 bug was: counter 70 (old not subtracted). v3.9.70 pops first.
    ok_b = H._READ_CACHE_CELLS == 50
    print(f"  replace counted once (50, not 70/100): "
          f"{'OK' if ok_b else 'VIOLATION'}")

    print("=== (c) oversize rejected BEFORE eviction ===")
    reset(100)
    kB = ("b.xlsx", "S", 0, False)
    H._read_cache_put(kB, sig, df_of(10, 5))          # 50
    H._read_cache_put(("huge.xlsx", "S", 0, False), sig, df_of(20, 10))  # 200
    ok_c = invariant("after oversize try")
    ok_c &= ("huge.xlsx", "S", 0, False) not in H._READ_CACHE \
        and kB in H._READ_CACHE
    print(f"  oversize rejected & small entry survived: "
          f"{'OK' if ok_c else 'VIOLATION'}")

    print("=== (d) FIFO eviction order (dict insertion order) ===")
    reset(100)
    for name, cells in (("A", 30), ("B", 40)):
        H._read_cache_put((name, "S", 0, False), sig, df_of(*divmod_dim(cells)))
    H._read_cache_put(("C", "S", 0, False), sig, df_of(10, 5))  # 50 -> evict A
    ok_d = invariant("after put C")
    ok_d &= ("A", "S", 0, False) not in H._READ_CACHE \
        and ("B", "S", 0, False) in H._READ_CACHE \
        and ("C", "S", 0, False) in H._READ_CACHE
    print(f"  FIFO evicted A first, B+C kept: {'OK' if ok_d else 'VIOLATION'}")

    print("=== (e) partial invalidate accounting ===")
    reset(100)
    kpath = os.path.join(os.sep, "x", "B.xlsx")
    kB = (os.path.normcase(os.path.normpath(kpath)), "S", 0, False)
    H._read_cache_put(kB, sig, df_of(10, 5))          # 50
    H._read_cache_put(("C", "S", 0, False), sig, df_of(4, 10))  # 40
    H.read_cache_invalidate([kpath])
    ok_e = invariant("after invalidate B")
    ok_e &= kB not in H._READ_CACHE and ("C", "S", 0, False) in H._READ_CACHE
    print(f"  B dropped by path: {'OK' if ok_e else 'VIOLATION'}")

    print("=== (f) full invalidate resets ===")
    n = H.read_cache_invalidate(None)
    ok_f = H._READ_CACHE_CELLS == 0 and not H._READ_CACHE and n >= 1
    print(f"  cleared {n} entries, counter={H._READ_CACHE_CELLS}: "
          f"{'OK' if ok_f else 'VIOLATION'}")

    print("=== (g) mutation isolation on cache hit ===")
    reset(10_000_000)
    kx = ("x.xlsx", "S", 4, True)
    H._read_cache_put(kx, sig, df_of(3, 3))
    got = H._read_cache_get(kx, sig)
    got.iloc[0, 0] = "MUTATED"
    got.insert(1, "NewCol", "z")
    got2 = H._read_cache_get(kx, sig)
    clean = (got2.iloc[0, 0] == "v00" and "NewCol" not in got2.columns)
    print(f"  cached frame untainted after caller mutation: "
          f"{'OK' if clean else 'VIOLATION'}")

    print("=== (h) sig mismatch => miss ===")
    got3 = H._read_cache_get(kx, (999, 1))
    miss = got3 is None
    print(f"  changed file signature => cache MISS: "
          f"{'OK' if miss else 'VIOLATION'}")

    all_ok = all([ok_a, ok_b, ok_c, ok_d, ok_e, ok_f, clean, miss])
    print("\nEXPECTED: all invariants hold (accounting correct post-v3.9.70)")
    print("VERDICT:", "NOT-BUG (accounting re-verified clean)" if all_ok
          else "BUG — cache accounting broken")


def divmod_dim(cells):
    # pick rows x cols exactly `cells`
    import math
    r = int(math.sqrt(cells))
    while cells % r:
        r -= 1
    return r, cells // r


if __name__ == "__main__":
    main()
