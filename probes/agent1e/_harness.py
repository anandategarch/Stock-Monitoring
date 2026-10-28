"""Shared harness untuk probe agent 1-e (UX views & app shell).
Pola screenshot_ui.py: app NYATA di bawah Xvfb + mock data."""
import os
import sys
import time

PROJECT_ROOT = "/home/z/stock-audit/stock-monitoring-python"
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DISPLAY", ":99")

import tkinter as tk  # noqa: E402


def pump(root, seconds=0.4):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def make_app():
    """App nyata (stdout/stderr dipulihkan — StreamToQueue jangan
    menelan output probe)."""
    real = sys.stdout, sys.stderr
    from src.ui.app import StockMonitorApp
    root = tk.Tk()
    root.geometry("1440x900+0+0")
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real
    return root, app


def wait_view(root, view, timeout=15.0):
    t0 = time.time()
    while getattr(view, "_busy", False) and time.time() - t0 < timeout:
        root.update()
        time.sleep(0.01)
    t0 = time.time()
    while time.time() - t0 < 0.4:
        root.update()
        time.sleep(0.01)
    return not getattr(view, "_busy", False)


def select_and_wait(root, app, tab, view, timeout=15.0):
    app.notebook.select(tab)
    root.update()
    if hasattr(view, "ensure_refreshed"):
        view.ensure_refreshed()
    return wait_view(root, view, timeout)


class _Ev:
    """Dummy event double-click ala screenshot_ui.py."""

    def __init__(self, tree, iid, col=None):
        self.widget = tree
        bbox = tree.bbox(iid)
        self.x = (bbox[0] + 10) if bbox else 10
        self.y = (bbox[1] + bbox[3] // 2) if bbox else 10
        if col is not None:
            # posisi kolom display
            try:
                cid = tree.identify_column(self.x)
                # geser x ke kolom target kalau diketahui
                self.x = tree.bbox(iid, column=col)[0] + 4
            except Exception:
                pass


VERDICTS = []


def check(name, expected, actual, ok=None):
    ok = (expected == actual) if ok is None else ok
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"      EXPECTED: {expected!r}")
    print(f"      ACTUAL  : {actual!r}")
    VERDICTS.append((name, ok))
    return ok


def summary():
    n_bad = sum(1 for _, ok in VERDICTS if not ok)
    print(f"== {len(VERDICTS) - n_bad}/{len(VERDICTS)} cek PASS, "
          f"{n_bad} FAIL ==")
    return n_bad
