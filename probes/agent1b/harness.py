"""Shared harness for agent1b UI/UX probes.

Boots the real StockMonitorApp under Xvfb :99 with mock pipeline data
(reuses test_ui_redesign fixtures — the same approach screenshot_ui.py
uses). Import PROJ first, then fixtures.
"""
import os
import sys
import time

PROJ = "/home/z/stock-audit/stock-monitoring-python"
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)

os.environ.setdefault("DISPLAY", ":99")

VERDICTS = []


def verdict(name, expected, actual, is_bug, severity="", where=""):
    tag = "BUG" if is_bug else "NOT-BUG"
    if is_bug and severity:
        tag = f"BUG ({severity})"
    VERDICTS.append((name, tag))
    print(f"[{tag}] {name}")
    print(f"   EXPECTED: {expected}")
    print(f"   ACTUAL  : {actual}")
    if where:
        print(f"   where   : {where}")
    print()


def pump(root, seconds=0.4):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def boot_app():
    """Boot real app; returns (root, app). Caller must destroy."""
    import tkinter as tk
    from src.ui.app import StockMonitorApp
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    root.geometry("1500x950+0+0")
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real_stdout, real_stderr
    app._filter_restore_state = None  # determinism (same as test suite)
    pump(root, 0.3)
    return root, app


def summary():
    print("=" * 64)
    bugs = [v for v in VERDICTS if v[1].startswith("BUG")]
    ok = [v for v in VERDICTS if not v[1].startswith("BUG")]
    print(f"TOTAL probes: {len(VERDICTS)}  BUG: {len(bugs)}  NOT-BUG: {len(ok)}")
    for n, t in VERDICTS:
        print(f"  {t:12s} {n}")
