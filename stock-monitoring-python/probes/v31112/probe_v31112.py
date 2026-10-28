"""PROBE v3.11.12 — TIGA PERMINTAAN USER (bukti fungsional runnable).

User: "Di tab deviasi Gr dan PCS kolom Cek kan ada analisa COM nah itu
bisa gak set 50% > atau < COM rendah atau COM tinggi nya?" +
"gimana cara tau misal sekarang bulan september apakah program otomatis
ambil yang agustus?" + "tampilan di config tidak bisa scroll aku harus
perkecil dulu unutk bisa lihat tombol proses bandingkan file manual".

Verifies (EXPECTED vs ACTUAL):
  A. com_gap_map min_pct  — ambang 50% dari |median|: gap 10 > 5 label ·
                            gap 5 TEPAT di ambang tak label (strict >) ·
                            gap 3 tertahan · median 0 → gap nonzero tetap
                            label walau ambang 500 · min_pct=0 = lama.
  B. DeviasiView          — default 50 menahan segmen COM gap kecil;
                            spinbox AMBANG COM → 0 → 'COM Tinggi (+3,0)'
                            muncul (recompute live).
  C. SharedComAmbang      — set + listener + clamp 0..500.
  D. bulan_mundur_list    — Sep-2026 mundur 2 → [Jul, Agu]; Jan mundur 3
                            wrap tahun → [Okt..Des 2025]; invalid → [].
                            + _auto_bulanan_paths parity (kronologis).
  E. SCROLL TAB ⚙️ CONFIG — konten 4 kartu di CANVAS ber-yscrollcommand;
                            tombol 📂 DALAM canvas (roda mouse menggulir);
                            yview_scroll menggulir saat meluap; scrollbar
                            auto-hide saat muat.
  F. STATUS TRANSPARANSI  — 'Periode data: SEPTEMBER 2026 → file dicari:
                            20.AGUSTUS 2026 ✓ · 20.JULI 2026 ✗' + tanpa
                            run → 'bulan komputer' diumumkan jujur.

Jalankan: DISPLAY=:99 python3 probes/v31112/probe_v31112.py
"""
import os
import sys
import tempfile
import time
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.ui.app import StockMonitorApp
from src.ui.com_analisa import (
    com_gap_map,
    com_rendah_map,
    com_tinggi_map,
)
from src.ui.deviasi_view import (
    DeviasiView,
    SharedComAmbang,
)
from src.ui.komparasi_deviasi_view import bulan_mundur_list

fails = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        fails.append(name)


def _row(barang, resto, jenis, tgl, nilai):
    return {"Nama Barang": barang, "JENIS": jenis,
            "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": nilai,
            "SATUAN": "GR", "AKTIF/NON": "AKTIF",
            "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
            "Nomor": None, "Nomor PO": None,
            "#Tgl/Jam Pembuatan IT": None, "SOURCE DATA": None}


# ---- fixture: median −10 (ACR 10 harian t1..t6); d(7) per pasangan --------
rows = []
for brg, acr7 in (("ATAS", 0.0), ("TEPAT", 5.0), ("BAWAH", 7.0),
                  ("RENDAH", 16.0)):
    for t in range(1, 8):
        rows.append(_row(f"BRG {brg}", "R", "1.SO", t, 100.0))
        rows.append(_row(f"BRG {brg}", "R", "9.ACR", t,
                         10.0 if t <= 6 else acr7))
        rows.append(_row(f"BRG {brg}", "R", "2.SALDO AKHIR", t, 100.0))
    rows.append(_row(f"BRG {brg}", "R", "SALDO AWAL", 1, 100.0))
for t in range(1, 8):   # MEDNOL: tanpa ACR (median 0) + IN 3 di t7
    rows.append(_row("BRG MEDNOL", "R", "1.SO", t, 100.0))
    rows.append(_row("BRG MEDNOL", "R", "2.SALDO AKHIR", t, 100.0))
rows.append(_row("BRG MEDNOL", "R", "SALDO AWAL", 1, 100.0))
rows.append(_row("BRG MEDNOL", "R", "4.IN", 7, 3.0))
df = pd.DataFrame(rows)

# ---- A. com_gap_map min_pct (modul pure) ----------------------------------
m50 = com_gap_map(df, 7, 50.0)
check("A1 ambang 50: gap 10 > 5 → ('tinggi', 10.0); rendah 6 > 5 → "
      "('rendah', 6.0)",
      m50.get(("BRG ATAS", "R")) == ("tinggi", 10.0)
      and m50.get(("BRG RENDAH", "R")) == ("rendah", 6.0),
      f"got {m50}")
check("A2 gap 5 TEPAT di ambang → strict > tak label; gap 3 tertahan",
      ("BRG TEPAT", "R") not in m50 and ("BRG BAWAH", "R") not in m50,
      f"got {m50}")
check("A3 min_pct=0 default = perilaku lama (semua selisih)",
      com_gap_map(df, 7).get(("BRG TEPAT", "R")) == ("tinggi", 5.0)
      and com_gap_map(df, 7) == com_gap_map(df, 7, 0.0),
      "back-compat gagal")
check("A4 median 0: cut 0 → gap 3 label walau ambang 500",
      com_gap_map(df, 7, 500.0).get(("BRG MEDNOL", "R")) == ("tinggi", 3.0),
      f"got {com_gap_map(df, 7, 500.0).get(('BRG MEDNOL', 'R'))!r}")
check("A5 turunan meneruskan min_pct (MEDNOL ikut tinggi — median 0 "
      "melampaui ambang apa pun)",
      com_tinggi_map(df, 7, 50.0)
      == {("BRG ATAS", "R"): 10.0, ("BRG MEDNOL", "R"): 3.0}
      and com_rendah_map(df, 7, 50.0) == {("BRG RENDAH", "R"): 6.0},
      f"tinggi={com_tinggi_map(df, 7, 50.0)} "
      f"rendah={com_rendah_map(df, 7, 50.0)}")

# ---- B. DeviasiView — spinbox AMBANG COM ----------------------------------
# CATATAN: root TANPA withdraw — StockMonitorApp (seksi E) butuh root
# TER-MAP supaya halaman notebook (tab ⚙️ Config) ikut ter-map; root
# yang di-withdraw membuat page tetap unmapped → scrollbar tak pernah
# tampil (pelajaran debug probe ini).
root = tk.Tk()
top = tk.Toplevel(root)
top.geometry("1250x700+15+15")
dv = DeviasiView(top, satuan_mode="GR")
dv.pack(fill="both", expand=True)
root.update()
root.update_idletasks()
root.update()
dv.load_data(df, None)


def _wait(view, timeout=15.0):
    """Pump event loop sampai async refresh selesai (pola wait_view
    test_ui_redesign — worker butuh wall-time, bukan cuma update())."""
    t0 = time.time()
    while getattr(view, "_busy", False) and time.time() - t0 < timeout:
        root.update()
        time.sleep(0.01)
    t0 = time.time()
    while time.time() - t0 < 0.5:
        root.update()
        time.sleep(0.01)


_wait(dv)


def cek(barang):
    for k in dv.tree.get_children(""):
        if dv.tree.set(k, "Nama Barang") == barang:
            return dv.tree.set(k, "CEK")
    return "<missing>"


check("B1 default 50: segmen COM gap 3 TERTAHAN (CEK kosong)",
      cek("BRG BAWAH") == "", f"cek={cek('BRG BAWAH')!r}")
dv._com_var.set("0")
dv._on_com_ambang_change()
_wait(dv)
check("B2 spinbox → 0: 'COM Tinggi (+3,0)' muncul (recompute live)",
      cek("BRG BAWAH") == "COM Tinggi (+3,0)" and dv.com_ambang == 0.0,
      f"cek={cek('BRG BAWAH')!r} amb={dv.com_ambang}")
top.destroy()
root.update()

# ---- C. SharedComAmbang ----------------------------------------------------
st = SharedComAmbang(50.0)
rec = []
st.subscribe(rec.append)
check("C1 set 25 → pct 25 + listener; clamp: -1/600 ditolak",
      st.set(25.0) and st.pct == 25.0 and rec == [25.0]
      and not st.set(-1.0) and not st.set(600.0) and st.pct == 25.0,
      f"pct={st.pct} rec={rec}")

# ---- D. bulan_mundur_list + _auto_bulanan_paths parity --------------------
check("D1 Sep-2026 mundur 2 → [(2026,7),(2026,8)] kronologis; Jan-2026 "
      "mundur 3 → wrap tahun [(2025,10)..(2025,12)]",
      bulan_mundur_list((2026, 9), 2) == [(2026, 7), (2026, 8)]
      and bulan_mundur_list((2026, 1), 3)
      == [(2025, 10), (2025, 11), (2025, 12)],
      f"got {bulan_mundur_list((2026, 9), 2)}")
check("D2 invalid → []", bulan_mundur_list((2026, 13), 1) == []
      and bulan_mundur_list(None, 1) == []
      and bulan_mundur_list((2026, 9), 0) == [], "tak kosong")
_fld = tempfile.mkdtemp(prefix="p31112_files_")
for nm in ("20.AGUSTUS 2026.xlsx", "20.JULI 2026.xlsx"):
    with open(os.path.join(_fld, nm), "w", encoding="utf-8") as f:
        f.write("x")
# F1 butuh folder dgn SATU file saja (utk tanda ✓ vs ✗)
_fld_f = tempfile.mkdtemp(prefix="p31112_f1_")
with open(os.path.join(_fld_f, "20.AGUSTUS 2026.xlsx"), "w",
          encoding="utf-8") as f:
    f.write("x")

from src.ui.komparasi_deviasi_view import (
    KomparasiDeviasiView,
)

kv = KomparasiDeviasiView(tk.Toplevel(root))
_paths = kv._auto_bulanan_paths((_fld, (2026, 9), 2))
check("D3 _auto_bulanan_paths via bulan_mundur_list: Sep-2026 mundur 2 "
      "→ [JULI, AGUSTUS] kronologis (perilaku v3.11.9 utuh)",
      [os.path.basename(p) for p in _paths]
      == ["20.JULI 2026.xlsx", "20.AGUSTUS 2026.xlsx"],
      f"got {[os.path.basename(p) for p in _paths]}")

# ---- E/F. app: scroll tab ⚙️ Config + status transparansi ------------------
# CATATAN: StockMonitorApp me-REDIRECT sys.stdout/stderr ke konsol log
# internal (make_log_console) — simpan & pulihkan seperti test_ui_redesign
# (§1) supaya output PASS/FAIL tetap ke terminal.
_real_out, _real_err = sys.stdout, sys.stderr
app = StockMonitorApp(root)
sys.stdout, sys.stderr = _real_out, _real_err
root.update()
root.update_idletasks()
root.update()

check("E1 struktur scroll: canvas ber-yscrollcommand + sb seinduk + "
      "yscrollincrement 40",
      isinstance(app._cfg_canvas, tk.Canvas)
      and str(app._cfg_canvas.cget("yscrollcommand"))
      and app._cfg_sb.master is app._cfg_canvas.master
      and int(app._cfg_canvas.cget("yscrollincrement")) == 40,
      f"cv={type(app._cfg_canvas).__name__}")
_anc = app.dev_bulanan_folder_entry.master
_in_wrap = False
while _anc is not None:
    if _anc is app._cfg_wrap:
        _in_wrap = True
        break
    _anc = getattr(_anc, "master", None)
check("E2 tombol 📂 'Muat ke ⚖ Komparasi Sekarang' DALAM canvas — roda "
      "mouse di mana pun tab config menggulir halaman",
      _in_wrap, "entry di luar wrap")
app.notebook.select(app.tab_config)
root.update()
app._cfg_scroll_fit()
root.update()
_over = (app._cfg_wrap.winfo_reqheight() > app._cfg_canvas.winfo_height() + 2)
_y0 = app._cfg_canvas.yview()[0]
app._cfg_canvas.yview_scroll(3, "units")
root.update()
check("E3 fungsional: scrollbar tampil ⟺ meluap + yview_scroll menggulir "
      "saat meluap (tombol 📂 terjangkau tanpa mengecilkan window)",
      app._cfg_sb.winfo_ismapped() == _over
      and ((app._cfg_canvas.yview()[0] > _y0) if _over
           else app._cfg_canvas.yview()[0] == _y0),
      f"over={_over} mapped={app._cfg_sb.winfo_ismapped()} "
      f"y0={_y0} y1={app._cfg_canvas.yview()[0]} "
      f"req={app._cfg_wrap.winfo_reqheight()} "
      f"cv={app._cfg_canvas.winfo_height()}")

app.dev_bulanan_folder_var.set(_fld_f)
app.dev_bulanan_jumlah_var.set("2")
_ar = app.audit_result
try:
    app.audit_result = {"period": [2026, 9]}
    app._dev_bulanan_status_default()
    _st = app.dev_bulanan_status_var.get()
    check("F1 status transparansi: 'Periode data: SEPTEMBER 2026 (data "
          "run terakhir) → file dicari: 20.AGUSTUS 2026 ✓ · "
          "20.JULI 2026 ✗'",
          "Periode data: SEPTEMBER 2026" in _st
          and "20.AGUSTUS 2026 ✓" in _st
          and "20.JULI 2026 ✗" in _st,
          f"got {_st!r}")
    app.audit_result = None
    app._dev_bulanan_status_default()
    _st2 = app.dev_bulanan_status_var.get()
    check("F2 tanpa run → fallback 'bulan komputer' DIUMUMKAN jujur",
          "bulan komputer" in _st2 and "Periode data:" in _st2,
          f"got {_st2!r}")
finally:
    app.audit_result = _ar
    app.dev_bulanan_folder_var.set("")
    app.dev_bulanan_jumlah_var.set("1")
    app._dev_bulanan_load_form()
    import shutil
    shutil.rmtree(_fld, ignore_errors=True)
    shutil.rmtree(_fld_f, ignore_errors=True)

root.destroy()

print()
if fails:
    print(f"FAIL: {len(fails)} — {fails}")
    sys.exit(1)
print("PROBE v3.11.12 SEMUA PASS ✔")
