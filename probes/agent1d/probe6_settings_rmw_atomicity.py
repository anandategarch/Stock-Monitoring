"""PROBE 6 — settings.json RMW/atomicity claims (app.py _save_window_state /
_save_filter_state / deviasi_view.save_acr_threshold):

  A. crash/exception mid-write (json.dump raises)  -> target file INTACT
  B. os.replace fails (OSError)                    -> target file INTACT
  C. process death between tmp write and replace   -> target file INTACT,
     loader degrades to defaults (no crash)
  D. RMW preserves unrelated keys across the THREE real writers
  E. corrupted settings.json (truncated JSON)      -> loaders return None
     gracefully, app-level defaults used

EXPECTED : target never left partial/corrupt; other keys preserved;
          corrupt file -> None (graceful)
ACTUAL   : (see output)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

tmp = H.make_tmp_base()
import src.ui.app as appmod  # noqa: E402
import src.ui.deviasi_view as dvmod  # noqa: E402

SETTINGS = tmp / "settings.json"
results = []


def seed():
    SETTINGS.write_text(json.dumps({
        "acr_threshold_pct": 80.0,
        "window_state": {"w": 1100, "h": 800, "maximized": False},
        "filter_state": {"pivot": {"kolom": "x"}},
    }), encoding="utf-8")


def intact(label, expect_keys):
    try:
        d = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        results.append((label, False, f"settings.json CORRUPT: {e!r}"))
        return
    missing = [k for k in expect_keys if k not in d]
    results.append((label, not missing,
                    f"missing={missing}" if missing else "intact"))


# ---------- A. json.dump raises mid-write ---------------------------------
seed()
_orig_dump = json.dump


def exploding_dump(obj, fp, *a, **k):
    fp.write('{"partial": tru')     # simulate torn write
    raise OSError(28, "No space left on device")


appmod.json.dump = exploding_dump
try:
    appmod._save_window_state(1220, 900, False, ui_zoom=1.0, x=10, y=20)
finally:
    appmod.json.dump = _orig_dump
intact("A: dump raises mid-write", ["acr_threshold_pct", "filter_state"])

# ---------- B. os.replace fails -------------------------------------------
seed()
_orig_replace = appmod.os.replace


def fail_replace(a, b):
    raise OSError(13, "Permission denied")


appmod.os.replace = fail_replace
try:
    appmod._save_window_state(1300, 950, True, ui_zoom=0.9)
finally:
    appmod.os.replace = _orig_replace
intact("B: os.replace OSError", ["acr_threshold_pct", "filter_state"])

# ---------- C. process dies between tmp write and replace -----------------
seed()
appmod.os.replace = lambda a, b: None          # silently "die before replace"
try:
    appmod._save_window_state(1400, 1000, False, ui_zoom=0.8)
finally:
    appmod.os.replace = _orig_replace
intact("C: death before replace", ["acr_threshold_pct", "filter_state"])
st = appmod._load_window_state()
results.append(("C2: loader after 'death'", st is None or st.get("w") in
                (1100, 1400), f"_load_window_state -> {st}"))

# ---------- D. RMW across the three real writers --------------------------
seed()
dvmod.save_acr_threshold(95.0)
appmod._save_window_state(1500, 1000, True, ui_zoom=1.2)
appmod._save_filter_state({"deviasi_gr": {"cek": "RI Balancing"}})
try:
    d = json.loads(SETTINGS.read_text(encoding="utf-8"))
    okd = (d.get("acr_threshold_pct") == 95.0
           and d.get("window_state", {}).get("w") == 1500
           and d.get("filter_state", {}).get("deviasi_gr") is not None)
    results.append(("D: 3 writers RMW", okd, json.dumps(d)[:160]))
except Exception as e:  # noqa: BLE001
    results.append(("D: 3 writers RMW", False, repr(e)))

# ---------- E. corrupted settings.json ------------------------------------
SETTINGS.write_text('{"window_state": {"w": 1020, "h": 7', encoding="utf-8")
st = appmod._load_window_state()
fs = appmod._load_filter_state()
acr = dvmod.load_acr_threshold()
okE = st is None and fs is None and acr == 80.0
results.append(("E: corrupt file graceful", okE,
                f"window={st} filter={fs} acr={acr}"))

all_ok = True
for label, ok, detail in results:
    all_ok &= ok
    H.out(f"[{'OK ' if ok else 'FAIL'}] {label:28s} {detail}")
H.out("EXPECTED : all checks OK (target never corrupt, keys preserved, "
      "graceful corrupt-handling)")
H.out(f"ACTUAL   : all_ok={all_ok}")
H.out("VERDICT  :", "NOT-BUG" if all_ok else "BUG")
sys.exit(0 if all_ok else 1)
