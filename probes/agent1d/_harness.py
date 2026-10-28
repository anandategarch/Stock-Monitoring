"""Shared harness for agent1d probes — isolates persistence paths to a temp
dir and provides an app factory with a fully controllable (fake) pipeline.

Run each probe with:  DISPLAY=:99 python3 probeN_*.py
"""
import json
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

REPO = Path("/home/z/stock-audit/stock-monitoring-python")
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

# Keep a handle on the REAL stdout — the app redirects sys.stdout/stderr to
# its internal log queue once instantiated.
REAL_OUT = sys.stdout


def out(*a):
    print(*a, file=REAL_OUT, flush=True)


def make_tmp_base() -> Path:
    """Temp dir with an isolated copy of config.json; patches ALL runtime
    persistence paths (settings.json / followup*.json / kategori_seen.json /
    config.json) away from the repo."""
    tmp = Path(tempfile.mkdtemp(prefix="a1d_"))
    shutil.copy(REPO / "config.json", tmp / "config.json")
    import src.ui.app as appmod
    import src.ui.followup as fumod
    import src.ui.deviasi_view as dvmod
    appmod._SETTINGS_PATH = tmp / "settings.json"
    appmod.CONFIG_PATH = tmp / "config.json"
    fumod._BASE = tmp
    dvmod._SETTINGS_BASE = tmp
    # followup_path()/resolved_path() are module funcs reading _BASE at call
    # time — already covered. komparasi_last.json lives next to config too.
    return tmp


def make_app(tmp: Path):
    """Instantiate the REAL StockMonitorApp under Xvfb with isolated paths.
    Returns (root, app)."""
    import tkinter as tk
    import src.ui.app as appmod
    root = tk.Tk()
    app = appmod.StockMonitorApp(root)
    return root, app


class FakePipeline:
    """Installs a controllable run_pipeline into src.ui.app BEFORE the first
    worker binds the real one (_ensure_pipeline_symbols only binds when the
    module global is still None — see app.py:215)."""

    def __init__(self):
        self.mode = "block"          # block -> wait stop_event / run2 -> wait evt
        self.release_run2 = threading.Event()
        self.calls = 0
        self._lock = threading.Lock()
        import src.ui.app as appmod
        import src.main as mainmod
        self._mainmod = mainmod
        appmod.run_pipeline = self._run

    def _empty_result(self):
        return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                {"df": pd.DataFrame(), "kpi": {}, "desc": "",
                 "period": [2026, 1], "month_len": 31, "lalu_month_len": 31})

    def _run(self, config_path=None, verbose=True, stop_event=None):
        with self._lock:
            self.calls += 1
            n = self.calls
        if n == 1:
            # run 1: behave like a real run that gets stopped by the user —
            # sleep until stop_event fires (or 10s safety), then raise.
            if stop_event is None or not stop_event.wait(10):
                return self._empty_result()
            raise self._mainmod.PipelineStopped("simulated stop")
        # run >= 2: block until the probe releases it
        self.release_run2.wait(10)
        return self._empty_result()


def drain(root, cond, timeout=15.0, poll=0.01):
    """Pump the Tk event loop until cond() is truthy (bounded)."""
    import time
    t0 = time.monotonic()
    while not cond():
        if time.monotonic() - t0 > timeout:
            return False
        root.update()
        time.sleep(poll)
    return True


def read_json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"__error__": repr(e)}
