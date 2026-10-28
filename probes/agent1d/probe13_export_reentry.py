"""PROBE 13 — export re-entrancy: _on_pipeline_done → _sync_export_buttons
re-enables 💾 Export while a PREVIOUS export is still running (its run_async
job handle is DISCARDED by _export_excel — no is-exporting flag exists), so
the user can start a SECOND export. Both jobs write the SAME tmp file
(filepath + ".tmp.xlsx") when saving to the same path → two openpyxl writers
interleave on one file; the first os.replace consumes the tmp and the second
one fails (OSError → "Export Gagal" dialog) and/or the final file is
byte-interleaved garbage.

Real-world sequence mirrored:
  export#1 starts (big pivot sheet, slow) → user runs pipeline (F5/MULAI —
  NOT disabled during export) → pipeline finishes → _on_pipeline_done →
  _sync_export_buttons() → 💾 re-enabled mid-export → user exports again
  to the same path.

EXPECTED : export buttons stay disabled while an export is running; a
           second export cannot start
ACTUAL   : buttons re-enabled mid-export; second export starts; two
           writers on one tmp file → error dialog / corrupt output
"""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

tmp_base = H.make_tmp_base()
import pandas as pd  # noqa: E402
import src.ui.app as appmod  # noqa: E402

dialogs = {"err": [], "warn": 0, "info": 0, "yesno": 0}
appmod.messagebox.showerror = lambda title, msg, **k: (
    dialogs["err"].append((title, str(msg)[:120])))
appmod.messagebox.showwarning = lambda *a, **k: dialogs.__setitem__(
    "warn", dialogs["warn"] + 1)
appmod.messagebox.showinfo = lambda *a, **k: dialogs.__setitem__(
    "info", dialogs["info"] + 1)
appmod.messagebox.askyesno = lambda *a, **k: (
    dialogs.__setitem__("yesno", dialogs["yesno"] + 1) or False)

target = Path(tempfile.mkdtemp(prefix="a1d_exp2")) / "out.xlsx"
appmod.filedialog.asksaveasfilename = lambda **k: str(target)

real_add_pivot = appmod.add_pivot_sheet


def slow_pivot(writer, df, should_cancel=None):
    time.sleep(1.0)               # keep the export in-flight
    return real_add_pivot(writer, df, should_cancel=should_cancel)


appmod.add_pivot_sheet = slow_pivot

root, app = H.make_app(tmp_base)
app.append1_df = pd.DataFrame(
    [{"NAMA RESTO": f"R{i % 5}", "Nama Barang": f"B{i}",
      "JENIS": "3.DEVIASI", "Tanggal": 25, "NILAI": -3}
     for i in range(60)])
root.update()
app._sync_export_buttons()

# ---- export #1 ------------------------------------------------------------
app._export_excel()
H.out("export#1 started; btn_export =",
      str(app.btn_export.cget("state")))

# ---- pipeline finishes while export#1 still running ------------------------
time.sleep(0.3)
root.update()
app._sync_export_buttons()        # <- exact call _on_pipeline_done makes
mid_state = str(app.btn_export.cget("state"))
H.out(f"after simulated pipeline-done (export#1 STILL RUNNING): "
      f"btn_export = {mid_state}")

hole = (mid_state == "normal")

# ---- user clicks 💾 again (same path) --------------------------------------
if hole:
    app._export_excel()
    H.out("export#2 started -> two jobs, same tmp path "
          f"'{target}.tmp.xlsx'")

# ---- let both finish -------------------------------------------------------
t0 = time.monotonic()
while time.monotonic() - t0 < 15:
    root.update()
    time.sleep(0.02)

target_exists = target.exists()
tmp_left = Path(str(target) + ".tmp.xlsx").exists()
loadable = False
load_err = None
if target_exists:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(target)
        loadable = True
        wb.close()
    except Exception as e:  # noqa: BLE001
        load_err = repr(e)[:100]

H.out(f"target file exists : {target_exists} | loads cleanly: {loadable} "
      f"{('| ' + load_err) if load_err else ''}")
H.out(f"tmp leftover       : {tmp_left}")
H.out(f"error dialogs      : {len(dialogs['err'])} "
      f"{dialogs['err'][:1]}")

ok = not hole
H.out("EXPECTED : btn stays disabled during export (no re-entry possible)")
H.out(f"ACTUAL   : reentry_hole={hole}, err_dialogs={len(dialogs['err'])}, "
      f"target_loads={loadable}, tmp_left={tmp_left}")
H.out("VERDICT  :", "BUG" if hole else "NOT-BUG")
root.destroy()
sys.exit(0 if hole else 1)
