"""PROBE 9 — window-state / zoom persistence edge cases (settings.json):
  1. off-screen saved position (x=-2000)      -> NOT restored (anti lost
     window), window stays visible on the current screen
  2. small-negative multi-monitor pos (x=-50) -> restored as saved
  3. oversized saved size (w=5000 > screen)   -> clamped to screen
  4. undersized h (< WINDOW_MIN)              -> state rejected -> defaults
  5. out-of-range / wrong-type ui_zoom        -> falls back to default 0.8
  6. pending zoom burst state at close        -> PENDING target persisted
     (self.ui_zoom is state-authoritative per §68 contract)

EXPECTED : window always recoverable/visible; zoom defaults sane; pending
           zoom persisted
ACTUAL   : (see output)
"""
import sys

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

import src.ui.app as appmod  # noqa: E402
from src.ui.app import UI_ZOOM_DEFAULT  # noqa: E402


def fresh(settings_dict):
    tmp = H.make_tmp_base()
    if settings_dict is not None:
        import json
        (tmp / "settings.json").write_text(
            json.dumps(settings_dict), encoding="utf-8")
    root, app = H.make_app(tmp)
    root.update()
    return tmp, root, app


def close_and_reload(root, app):
    """Simulate the close-path save then a fresh load."""
    import src.ui.app as am
    mx = False
    try:
        mx = app._is_root_maximized()
    except Exception:
        pass
    am._save_window_state(root.winfo_width(), root.winfo_height(), mx,
                          ui_zoom=getattr(app, "ui_zoom", None),
                          x=None if mx else root.winfo_x(),
                          y=None if mx else root.winfo_y())
    root.destroy()
    return H.read_json(am._SETTINGS_PATH).get("window_state", {})


results = []

# --- 1. off-screen position ---
tmp, root, app = fresh({"window_state": {"w": 1200, "h": 800,
                                         "maximized": False,
                                         "x": -2000, "y": 300}})
root.update()
x, sw = root.winfo_x(), root.winfo_screenwidth()
ok = -120 <= x <= sw - 100
results.append((f"1: off-screen x=-2000 not restored (got x={x})", ok))
root.destroy()

# --- 2. small-negative position restored? (v3.9.72 FIX 9 claims position
#        persistence: _save_window_state WRITES x/y; __init__ restore reads
#        _saved_win.get("x") — but _load_window_state() builds its return
#        dict WITHOUT x/y → validation always fails → position NEVER
#        restored. Dead wiring of the whole feature.) ---
tmp, root, app = fresh({"window_state": {"w": 1200, "h": 800,
                                         "maximized": False,
                                         "x": -50, "y": 40}})
root.update()
x, y = root.winfo_x(), root.winfo_y()
ok = (x == -50 and y == 40)
results.append((f"2: saved pos (-50,40) restored (got {x},{y}) — "
                f"_load_window_state returns {appmod._load_window_state()}",
                ok))
root.destroy()

# --- 3. oversized size clamped ---
tmp, root, app = fresh({"window_state": {"w": 5000, "h": 4000,
                                         "maximized": False}})
root.update()
w, h, sw, sh = (root.winfo_width(), root.winfo_height(),
                root.winfo_screenwidth(), root.winfo_screenheight())
ok = w <= sw and h <= sh
results.append((f"3: oversized clamped (got {w}x{h} vs screen {sw}x{sh})", ok))
root.destroy()

# --- 4. undersized height rejected -> defaults (maximize path) ---
tmp, root, app = fresh({"window_state": {"w": 1200, "h": 300,
                                         "maximized": False}})
root.update()
h = root.winfo_height()
ok = h >= 600      # rejected -> maximize/default geometry, not 300
results.append((f"4: undersized rejected (got h={h})", ok))
root.destroy()

# --- 5. bad ui_zoom variants ---
for label, z in (("out-of-range 99", 99), ("string '1.5'", "1.5"),
                 ("bool True", True)):
    tmp, root, app = fresh({"window_state": {"w": 1200, "h": 800,
                                             "maximized": False,
                                             "ui_zoom": z}})
    ok = abs(app.ui_zoom - UI_ZOOM_DEFAULT) < 1e-9
    results.append((f"5: ui_zoom {label} -> default {UI_ZOOM_DEFAULT} "
                    f"(got {app.ui_zoom})", ok))
    root.destroy()

# --- 6. pending zoom burst persisted at close ---
tmp, root, app = fresh({"window_state": {"w": 1200, "h": 800,
                                         "maximized": False}})
app._zoom_step(3)          # burst: state now 0.8+0.3=1.1, effects deferred
pending_target = app.ui_zoom
ws = close_and_reload(root, app)
ok = abs(float(ws.get("ui_zoom", -1)) - pending_target) < 1e-9
results.append((f"6: pending zoom burst persisted (target={pending_target}, "
                f"saved={ws.get('ui_zoom')})", ok))

all_ok = True
for label, ok in results:
    all_ok &= ok
    H.out(f"[{'OK ' if ok else 'FAIL'}] {label}")
H.out("EXPECTED : all window/zoom persistence edge cases handled")
H.out(f"ACTUAL   : all_ok={all_ok}")
H.out("VERDICT  :", "NOT-BUG" if all_ok else "BUG")
sys.exit(0 if all_ok else 1)
