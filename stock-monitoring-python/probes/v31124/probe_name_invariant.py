#!/usr/bin/env python3
"""probe v31124 — AUDIT FIX "NAMA BARANG HILANG" DI SEL ANOTASI ↳.

User: "Deep audit dan fix". Akar yang ditemukan audit: era v3.11.23 menulis
anotasi ↳ MURNI ("↳ Rank n" / "↳ CEK…") di baris ke-2/ke-3 kelompok — nama
barang TIDAK terlihat di baris itu (VLM konfirmasi: 3 baris SBYKET tampak
hanya "Rank 1/2/3") — regresi kelas keluhan 3× user (v3.9.55-59 · v3.11.16
· v3.11.18 "nama barang hilang").

FIX yang diverifikasi probe ini:
  1. INVARIAN BARU: nama barang TIDAK PERNAH hilang — SETIAP baris kolom
     Nama Barang DIAWALI nama barang RAW snapshot.
  2. Kontrak blok anotasi ↳ v3.11.24: head = nama · baris ke-2 =
     "NAMA · ↳ Rank n" · baris ke-3 = "NAMA · ↳ CEK…" · sisa digabung
     baris TERAKHIR ' · ' · singleton = "NAMA · ↳ Rank n · ↳ CEK…".
  3. Pasca-sort interleave: layout dipasang ulang atas urutan visual
     (tiap run singleton = nama + blok lengkap — nama tetap ada).
  4. Kolom CEK & Rank tetap TIDAK ADA di tree.
  5. RAW maps utuh (per-baris _rank_map/_cek_map + kelompok _grank_map/
     _gcek_map).

Jalankan: DISPLAY=:61 python probes/v31124/probe_name_invariant.py
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
    """Kontrak v3.11.24 — sel anotasi = 'NAMA · ↳ anotasi' (nama selalu
    di depan)."""
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
            ("KOPI BUBUK", "MLGPAR", 10.0, 2.0),
            ("SUSU UHT", "MLGPAR", 1.0, 9.0),
            ("SUSU UHT", "SBYKET", 2.0, 8.0),
            ("SUSU UHT", "PWKTAM", 3.0, 7.0),
            ("SUSU UHT", "MLGKUL", 4.0, 6.0),
            ("SUSU UHT", "SMGBAN", 5.0, 5.0)]:
        for j, v in [("1.SO", so), ("2.SALDO AKHIR", saldo),
                     ("SALDO AWAL", 10.0), ("4.IN", 2.0)]:
            for t in range(20, 28):
                rows.append({
                    "Nama Barang": b, "JENIS": j, "NAMA RESTO": resto,
                    "Tanggal": t, "NILAI": float(v if j != "1.SO"
                                                 or t == 26 else 0.0),
                    "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                    "KATEGORI": "BAHAN",
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
    pump(root, 0.4)
    dv.load_data(df)
    t0 = time.time()
    while time.time() - t0 < 15:
        root.update()
        time.sleep(0.01)
        if not dv._busy and len(dv.tree.get_children("")):
            break
    t = dv.tree
    kids = list(t.get_children(""))
    cols = [str(c) for c in t["columns"]]

    # (1) kolom CEK & Rank tetap dihapus
    check("kolom CEK & Rank DIHAPUS dari tree (merger ↳ ke Nama Barang)",
          "CEK" not in cols and "Rank" not in cols, f"cols={cols}")

    # (2) INVARIAN BARU v3.11.24: nama barang TIDAK PERNAH hilang —
    #     SETIAP sel Nama Barang diawali nama barang RAW snapshot.
    bad = []
    for k in kids:
        ks = str(k)
        raw = str((dv._row_snaps.get(ks) or {}).get("barang", ""))
        cell = str(t.set(k, "Nama Barang"))
        if not cell.startswith(raw):
            bad.append((ks, raw, cell))
    check("INVARIAN v3.11.24: SEMUA sel Nama Barang diawali NAMA barang "
          "RAW (nama tidak pernah hilang — era v3.11.23 baris ke-2/ke-3 "
          "kelompok tampak hanya '↳ Rank n')",
          not bad, f"bad={bad[:4]}")

    # (3) kontrak blok anotasi ↳ v3.11.24 (nama · ↳ anotasi)
    exp = annot_expected(dv, t)
    bad2 = [(str(k), str(t.set(k, "Nama Barang")), exp.get(k)) for k in kids
            if str(t.set(k, "Nama Barang")) != exp.get(k)]
    check("blok anotasi ↳ == kontrak v3.11.24 SEMUA baris (head=nama · "
          "ke-2='NAMA · ↳ Rank n' · ke-3='NAMA · ↳ CEK…' · nama diulang "
          "setelah blok)",
          not bad2, f"bad={bad2[:4]}")

    # (4) struktur contoh: kelompok 3-baris GULA PASIR
    nb = {str(k): str(t.set(k, "Nama Barang")) for k in kids}
    gula = [k for k in kids if str((dv._row_snaps.get(str(k)) or {})
                                   .get("barang", "")) == "GULA PASIR"]
    check("GULA PASIR (3 baris): head=nama · ke-2='GULA PASIR · ↳ Rank n' "
          "(nama TETAP tampil — bukan '↳ Rank n' polos)",
          len(gula) == 3
          and nb[str(gula[0])] == "GULA PASIR"
          and nb[str(gula[1])].startswith("GULA PASIR \u00b7 \u21b3 Rank "),
          f"cells={[nb[str(k)] for k in gula]}")

    # (5) singleton KOPI BUBUK: nama + anotasi digabung ' · '
    kopi = [k for k in kids if str((dv._row_snaps.get(str(k)) or {})
                                  .get("barang", "")) == "KOPI BUBUK"]
    check("singleton KOPI BUBUK: 'KOPI BUBUK · ↳ Rank n · …' (sisa "
          "anotasi digabung baris terakhir — pola Rincian PO)",
          len(kopi) == 1
          and nb[str(kopi[0])].startswith("KOPI BUBUK \u00b7 \u21b3 Rank "),
          f"cell={nb[str(kopi[0])]!r}")

    # (6) sort interleave → layout dipasang ulang atas urutan visual
    #     + INVARIAN nama tetap berlaku
    dv._sort_by("Deviasi", reverse=True)
    t0 = time.time()
    while time.time() - t0 < 10:
        root.update()
        time.sleep(0.01)
        if not getattr(t, "_sort_insert_cancel", None):
            break
    exp2 = annot_expected(dv, t)
    bad3 = [(str(k), str(t.set(k, "Nama Barang")), exp2.get(k)) for k in
            t.get_children("")
            if str(t.set(k, "Nama Barang")) != exp2.get(k)]
    bad4 = []
    for k in t.get_children(""):
        ks = str(k)
        raw = str((dv._row_snaps.get(ks) or {}).get("barang", ""))
        cell = str(t.set(k, "Nama Barang"))
        if not cell.startswith(raw):
            bad4.append((ks, raw, cell))
    check("pasca-SORT interleave: blok anotasi dipasang ulang atas "
          "URUTAN VISUAL + INVARIAN nama tetap berlaku (tiap sel "
          "singleton = 'NAMA · ↳ Rank n · ↳ CEK…' — nama di depan)",
          not bad3 and not bad4, f"bad={bad3[:3]} bad_inv={bad4[:3]}")

    # (7) RAW maps utuh
    check("RAW maps utuh: _rank_map/_cek_map per-baris + _grank_map/"
          "_gcek_map kelompok (sort/filter/popup/follow-up)",
          len(dv._rank_map) == len(kids)
          and len(dv._cek_map) == len(kids)
          and len(dv._grank_map) == len(kids)
          and len(dv._gcek_map) == len(kids),
          f"n={len(kids)} rk={len(dv._rank_map)} ck={len(dv._cek_map)} "
          f"grk={len(dv._grank_map)} gck={len(dv._gcek_map)}")

    # (8) screenshot bukti visual (default view — urut ulang via sort by
    #     Nama Barang supaya kelompok kontigu lagi)
    dv._sort_by("Nama Barang", reverse=False)
    t0 = time.time()
    while time.time() - t0 < 10:
        root.update()
        time.sleep(0.01)
        if not getattr(t, "_sort_insert_cancel", None):
            break
    try:
        from PIL import ImageGrab
        top.lift()
        top.attributes("-topmost", True)
        pump(root, 0.4)
        img = ImageGrab.grab(
            xdisplay=os.environ.get("DISPLAY", ":61"))
        img.save(OUT / "probe_v31124_dev_gr.png")
        check("screenshot /tmp/shots/probe_v31124_dev_gr.png tersimpan",
              True)
    except Exception as e:  # noqa: BLE001 — opsional lintas lingkungan
        check("screenshot (opsional) dilewati", True, str(e))

    top.destroy()
    root.destroy()
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\nprobe v31124: {len(RESULTS) - n_fail}/{len(RESULTS)} OK")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
