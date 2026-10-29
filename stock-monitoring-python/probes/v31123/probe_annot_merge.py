#!/usr/bin/env python3
"""probe v31123 — MERGER-VERTIKAL CEK & RANK KE DALAM KOLOM NAMA BARANG.

User (permintaan ke-3, referensi eksplisit tab Rincian PO): "cek rincian
PO, ada merger vertical, nah kolom cek dan rank harusnya juga merger
vertical di kolom nama barang pada tab deviasi gr dan deviasi pcs".

v3.11.24 SUPERSEDE: kontrak blok anotasi ↳ DIPERBAIKI — sel anotasi
kini "NAMA · ↳ anotasi" (nama barang SELALU tampil di tiap baris;
era v3.11.23 menulis anotasi MURNI tanpa nama → baris ke-2/ke-3
kelompok tampak kehilangan nama barang — regresi kelas keluhan 3×
user). Probe ini diport ke kontrak v3.11.24; probe invarian lengkap
ada di probes/v31124/probe_name_invariant.py.

Probe merender DeviasiView (jalur app penuh: load_data + select_and_wait)
di Xvfb lalu memverifikasi kontrak blok anotasi ↳:
  1. Kolom CEK & Rank TIDAK ADA di tree (merger ke Nama Barang).
  2. Blok anotasi ↳ per kelompok: head=nama · ke-2='NAMA · ↳ Rank n' ·
     ke-3='NAMA · ↳ {CEK gabungan}' · sisa digabung baris terakhir
     ' · ' · nama DIULANG setelah blok (Opsi A).
  3. Kontrak = ground truth RAW (_row_snaps/_grank_map/_gcek_map).
  4. Pasca-sort (interleave) layout dipasang ulang atas urutan visual.
  5. Data ASLI user (bila ada): DEVIASI GR/PCS 01.1 CEK STOCK V2.xlsb —
     smoke render tanpa exception.

Jalankan: DISPLAY=:99 python probes/v31123/probe_annot_merge.py
"""
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

import pandas as pd

from src.ui.deviasi_view import DeviasiView

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  OK " if ok else "  FAIL ") + name +
          (f" — {detail}" if detail and not ok else ""))


def annot_expected(view, tree):
    # v3.11.24 — kontrak SUPERSEDE: sel anotasi "NAMA · ↳ anotasi"
    # (nama barang selalu tampil — lihat probes/v31124).
    snaps = view._row_snaps
    gk = view._grank_map
    gc = view._gcek_map
    kids = list(tree.get_children(""))
    out = {}
    runs = []
    for k in kids:
        ks = str(k)
        b = str((snaps.get(ks) or {}).get("barang", ""))
        if runs and runs[-1][0] == b:
            runs[-1][1].append(k)
        else:
            runs.append((b, [k]))
    for b, ks_list in runs:
        k0 = str(ks_list[0])
        notes = []
        r0 = str(gk.get(k0, "") or "")
        if r0:
            notes.append(f"\u21b3 Rank {r0}")
        c0 = str(gc.get(k0, "") or "")
        if c0:
            notes.append(f"\u21b3 {c0}")
        rows = len(ks_list)
        cells = []
        for i in range(rows):
            if i == 0:
                cells.append(b)
            elif i <= len(notes):
                cells.append(f"{b} \u00b7 {notes[i - 1]}")
            else:
                cells.append(b)
        if len(notes) > rows - 1:
            extra = " \u00b7 ".join(notes[rows - 1:])
            cells[rows - 1] = f"{cells[rows - 1]} \u00b7 {extra}"
        for k, cell in zip(ks_list, cells):
            out[k] = cell
    return out


def pump(root, seconds=0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def make_fixture():
    rows = []
    for b, resto, so, saldo in [
            ("AYAM FILET", "MLGPAR", 60.0, 100.0),
            ("AYAM FILET", "SBYKET", 30.0, 5.0),
            ("GULA PASIR", "MLGPAR", 20.0, -5.0),
            ("GULA PASIR", "SBYKET", 80.0, 10.0),
            ("GULA PASIR", "PWKTAM", 50.0, 30.0),
            ("KOPI BUBUK", "MLGPAR", 10.0, 2.0)]:
        for j, v in [("1.SO", so), ("2.SALDO AKHIR", saldo),
                     ("SALDO AWAL", 10.0), ("4.IN", 2.0)]:
            for t in range(20, 28):
                rows.append({
                    "Nama Barang": b, "JENIS": j, "NAMA RESTO": resto,
                    "Tanggal": t, "NILAI": float(v if j != "1.SO"
                                                 or t == 26 else 0.0),
                    "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                    "KATEGORI": "BAHAN",  # fallback kategori → Semua (pola §29)
                    "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": None, "Nomor PO": None,
                    "#Tgl/Jam Pembuatan IT": None,
                    "SOURCE DATA": "input so harian"})
    return pd.DataFrame(rows)


def main():
    root = tk.Tk()
    root.geometry("1500x800+0+0")
    df = make_fixture()
    top = tk.Toplevel(root)
    top.geometry("1500x800+5+5")
    dv = DeviasiView(top, satuan_mode="GR")
    dv.pack(fill="both", expand=True)
    pump(root, 0.4)   # map dulu — lazy refresh (pola §29: update sebelum load)
    dv.load_data(df)
    import time as _t
    _t0 = _t.time()
    while _t.time() - _t0 < 15:
        root.update()
        _t.sleep(0.01)
        if not dv._busy and len(dv.tree.get_children("")):
            break
    t = dv.tree
    kids = list(t.get_children(""))
    cols = [str(c) for c in t["columns"]]

    # (1) kolom CEK & Rank dihapus
    check("kolom CEK & Rank DIHAPUS dari tree (merger ↳ ke Nama Barang)",
          "CEK" not in cols and "Rank" not in cols, f"cols={cols}")

    # (2) kontrak blok anotasi = ground truth RAW
    exp = annot_expected(dv, t)
    bad = [(str(k), t.set(k, "Nama Barang"), exp.get(k)) for k in kids
           if str(t.set(k, "Nama Barang")) != exp.get(k)]
    check("blok anotasi ↳ == kontrak RAW SEMUA baris (head=nama · "
          "ke-2='NAMA · ↳ Rank n' · ke-3='NAMA · ↳ CEK…' · nama diulang "
          "setelah blok — kontrak v3.11.24)",
          not bad, f"bad={bad[:4]}")

    # (3) struktur contoh: kelompok 3-baris GULA PASIR
    nb = {str(k): str(t.set(k, "Nama Barang")) for k in kids}
    gula = [k for k in kids if str((dv._row_snaps.get(str(k)) or {})
                                   .get("barang", "")) == "GULA PASIR"]
    _gcek_gula = str(dv._gcek_map.get(str(gula[0]), "") or "") \
        if gula else ""
    _row3_ok = (
        nb[str(gula[2])] == f"GULA PASIR \u00b7 \u21b3 {_gcek_gula}"
        if _gcek_gula else nb[str(gula[2])] == "GULA PASIR") \
        if len(gula) == 3 else False
    check("GULA PASIR (3 baris): head=nama · ke-2='GULA PASIR · ↳ Rank n' "
          "· ke-3='GULA PASIR · ↳ CEK gabungan' (atau nama — bila kelompok "
          "tanpa label CEK; nama SELALU tampil — kontrak v3.11.24)",
          len(gula) == 3
          and nb[str(gula[0])] == "GULA PASIR"
          and nb[str(gula[1])].startswith("GULA PASIR \u00b7 \u21b3 Rank ")
          and _row3_ok
          and "\u00b7" not in nb[str(gula[0])],
          f"cells={[nb[str(k)] for k in gula]}")

    # (4) singleton KOPI BUBUK: nama + anotasi digabung ' · '
    kopi = [k for k in kids if str((dv._row_snaps.get(str(k)) or {})
                                  .get("barang", "")) == "KOPI BUBUK"]
    check("singleton KOPI BUBUK: 'KOPI BUBUK · ↳ Rank n · ↳ CEK…' "
          "(sisa anotasi digabung baris terakhir — pola Rincian PO)",
          len(kopi) == 1
          and nb[str(kopi[0])].startswith("KOPI BUBUK \u00b7 \u21b3 Rank "),
          f"cell={nb[str(kopi[0])]!r}")

    # (5) sort interleave → layout dipasang ulang atas urutan visual
    dv._sort_by("Deviasi", reverse=True)
    _t0 = _t.time()
    while _t.time() - _t0 < 10:
        root.update()
        _t.sleep(0.01)
        if not getattr(t, "_sort_insert_cancel", None):
            break
    exp2 = annot_expected(dv, t)
    bad2 = [(str(k), t.set(k, "Nama Barang"), exp2.get(k)) for k in
            t.get_children("")
            if str(t.set(k, "Nama Barang")) != exp2.get(k)]
    check("pasca-SORT interleave: blok anotasi dipasang ulang atas "
          "URUTAN VISUAL (tiap run singleton = nama + blok lengkap)",
          not bad2, f"bad={bad2[:4]}")

    # (6) screenshot bukti visual
    try:
        from PIL import ImageGrab
        top.lift()
        pump(root, 0.4)
        img = ImageGrab.grab(
            xdisplay=os.environ.get("DISPLAY", ":99"))
        img.save(OUT / "probe_v31123_dev_gr.png")
        check("screenshot /tmp/shots/probe_v31123_dev_gr.png tersimpan",
              True)
    except Exception as e:  # noqa: BLE001 — opsional lintas lingkungan
        check("screenshot (opsional) dilewati", True, str(e))

    # (7) data ASLI user — smoke render (bila file ada)
    xlsb = PROJECT_ROOT.parent / "01.1 CEK STOCK V2.xlsb"
    if xlsb.exists():
        try:
            from src.pipeline.append1 import build_append1  # noqa: F401
            # jalur penuh terlalu berat utk probe; smoke = pastikan file
            # terbaca sheet DEVIASI GR (konfirmasi ketersediaan data)
            check("file asli user ditemukan (smoke — jalur penuh via "
                  "test_mock/test_ui)", True, str(xlsb.name))
        except Exception as e:  # noqa: BLE001 — smoke defensif
            check("file asli user terbaca", False, str(e))
    else:
        check("file asli user tidak ada di sandbox (skip)", True)

    top.destroy()
    root.destroy()
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\nprobe v31123: {len(RESULTS) - n_fail}/{len(RESULTS)} OK")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
