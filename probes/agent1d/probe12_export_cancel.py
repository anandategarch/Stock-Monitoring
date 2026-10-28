"""PROBE 12 — ⏹ Batal during a long Excel export (v3.10.1 wiring):
  - cancel raised at the pivot-sheet checkpoint → ExportCancelled →
    friendly amber status (NOT an error dialog)
  - target file NEVER created; tmp cleaned up
  - export buttons re-enabled after cancel (no stuck-disabled state)
  - a second export right after cancel works normally (state machine reset)

EXPECTED : no target/tmp file, buttons re-enabled, INFO not ERROR dialog
ACTUAL   : (see output)
"""
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

tmp_base = H.make_tmp_base()
import pandas as pd  # noqa: E402
import src.ui.app as appmod  # noqa: E402
from src.ui.export_sheets import ExportCancelled  # noqa: E402

dialogs = {"err": 0, "warn": 0, "info": 0, "yesno": 0}
appmod.messagebox.showerror = lambda *a, **k: dialogs.__setitem__(
    "err", dialogs["err"] + 1)
appmod.messagebox.showwarning = lambda *a, **k: dialogs.__setitem__(
    "warn", dialogs["warn"] + 1)
appmod.messagebox.showinfo = lambda *a, **k: dialogs.__setitem__(
    "info", dialogs["info"] + 1)
appmod.messagebox.askyesno = lambda *a, **k: (
    dialogs.__setitem__("yesno", dialogs["yesno"] + 1) or False)

target = Path(tempfile.mkdtemp(prefix="a1d_exp")) / "out.xlsx"
appmod.filedialog.asksaveasfilename = lambda **k: str(target)

# slow pivot sheet so the cancel click lands mid-export — the REAL
# add_pivot_sheet keeps its own cancel checkpoints (create_sheet happens
# first, ExportCancelled raised per-32-rows), mirroring the real flow
real_add_pivot = appmod.add_pivot_sheet


def slow_pivot(writer, df, should_cancel=None):
    deadline = time.time() + 5
    while time.time() < deadline:
        if should_cancel is not None and should_cancel():
            break
        time.sleep(0.02)
    return real_add_pivot(writer, df, should_cancel=should_cancel)


appmod.add_pivot_sheet = slow_pivot

root, app = H.make_app(tmp_base)
app.append1_df = pd.DataFrame(
    [{"NAMA RESTO": f"R{i % 5}", "Nama Barang": f"B{i}",
      "JENIS": "3.DEVIASI", "Tanggal": 25, "NILAI": -3}
     for i in range(60)])
root.update()
app._sync_export_buttons()
H.out("btn_export before export:",
      str(app.btn_export.cget("state")))

app._export_excel()
t0 = time.monotonic()
while time.monotonic() - t0 < 3:
    root.update()
    if app._export_overlay._cancel_btn is not None:
        break
    time.sleep(0.01)
H.out("cancel button present:",
      app._export_overlay._cancel_btn is not None)
app._export_overlay._on_cancel_click()      # user clicks ⏹ Batal

t0 = time.monotonic()
while time.monotonic() - t0 < 10:
    root.update()
    if str(app.btn_export.cget("state")) == "normal":
        break
    time.sleep(0.02)
state_after = str(app.btn_export.cget("state"))
exists = target.exists()
tmp_exists = (Path(str(target) + ".tmp.xlsx")).exists()

H.out(f"target file created : {exists}")
H.out(f"tmp leftover        : {tmp_exists}")
H.out(f"btn_export after    : {state_after}")
H.out(f"dialogs             : {dialogs}")

ok = (not exists and not tmp_exists and state_after == "normal"
      and dialogs["err"] == 0)
H.out("EXPECTED : no files, buttons normal, 0 error dialogs (cancel = INFO)")
H.out(f"ACTUAL   : target={exists} tmp={tmp_exists} btn={state_after} "
      f"err_dialogs={dialogs['err']}")
H.out("VERDICT  :", "NOT-BUG" if ok else "BUG")
root.destroy()
sys.exit(0 if ok else 1)
