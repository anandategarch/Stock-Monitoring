"""probe_cek_rank.py — v3.11.27 VISUAL & PROGRAMATIK: revert total
merge-vertikal + Rank masuk kolom CEK (user: "ternyata jadi jelek
ketika merger vertical, sekarang gak perlu merger vertical kembali
menjadi awal aja. tapi kolom rank dihapus dan dipindah ke kolom CEK
sebagai analisa Rank 1 misal nya").

Fixture mirror §61 test_ui_redesign (BUMBU/CABE/PENTOL — 5 baris,
label analisa lalu-kini + BOM 0 + Hitung Manual bervariasi per baris).
CHECK:
 1. Kolom Rank TIDAK ADA di tree (COLUMNS/tree/col_sel).
 2. Tabel DATAR: CEK terisi di SEMUA baris (tanpa sel kosong head-only).
 3. CEK = "Rank N · <label>" — Rank konstan per kelompok
    (BUMBU Σ|Dev|=1→'3' · CABE 65→'2' · PENTOL 95→'1').
 4. Nama Barang PER-BARIS (OPSI A tetap).
 5. Sort CEK = rank numerik (parser prefiks) — desc: PENTOL(1) teratas.
 6. Screenshot bukti visual: /tmp/shots/probe_v31127_*.png.

Jalankan: DISPLAY=:99 python probes/v31127/probe_cek_rank.py
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

from src.ui.deviasi_view import DeviasiView

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)

ROWS = []


def _row(jenis, tgl, nilai, barang, resto):
    return {"Nama Barang": barang, "JENIS": jenis,
            "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": float(nilai),
            "SATUAN": "GR", "AKTIF/NON": "AKTIF",
            "KATEGORI": "COM DEVIASI - RESTO",
            "SOURCE KIRIMAN": "GUDANG"}


def build_fixture():
    rows = [r for jenis, tgl, nilai in (
        ("3.DEVIASI", 13, 0.0), ("3.DEVIASI", 14, -25.0),
        ("3.DEVIASI", 15, 0.0), ("3.DEVIASI", 16, 7777.0))
        for r in [_row(jenis, tgl, nilai, "PENTOL", "PWKTAM")]]
    for barang, resto, so, sis in (
            ("CABE", "MLGPAR", 60.0, 100.0),
            ("CABE", "PWKTAM", 30.0, 5.0),
            ("PENTOL", "MLGPAR", 20.0, -5.0),
            ("PENTOL", "PWKTAM", 80.0, 10.0),
            ("BUMBU", "MLGPAR", 50.0, 30.0)):
        for t in (12, 13, 14, 15, 16):
            rows.append(_row("1.SO", t, so if t == 14 else 0.0,
                             barang, resto))
        rows.append(_row("2.SALDO AKHIR", 14, sis, barang, resto))
        for t in (13, 14, 15):
            rows.append(_row("4.IN", t, 30.0, barang, resto))
    return rows


def shot(name, delay=0.4):
    time.sleep(delay)
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(xdisplay=os.environ.get("DISPLAY", ":99"))
        img.save(OUT / f"{name}.png")
        print(f"    📸 {OUT / (name + '.png')}")
    except Exception as exc:                    # noqa: BLE001
        print(f"    ! screenshot gagal: {exc}")


def main():
    root = tk.Tk()
    root.geometry("1500x700+5+5")
    dv = DeviasiView(root, satuan_mode="GR")
    dv.pack(fill="both", expand=True)
    root.update()
    dv.load_data(pd.DataFrame(build_fixture()))

    deadline = time.time() + 15
    while time.time() < deadline:
        root.update()
        if not dv._busy and len(dv.tree.get_children("")):
            break
        time.sleep(0.05)
    for _ in range(20):
        root.update()
        time.sleep(0.02)

    ok = []

    kids = list(dv.tree.get_children(""))
    # 1 — kolom Rank dihapus
    ok.append(("kolom Rank DIHAPUS dari COLUMNS & tree & col_sel",
               "Rank" not in [c[0] for c in dv.COLUMNS]
               and "Rank" not in [str(c) for c in dv.tree["columns"]]
               and "Rank" not in dv._col_sel))
    # 2 — datar: SEMUA baris ber-CEK
    ok.append(("tabel DATAR — CEK terisi SEMUA baris (no head-only)",
               all(str(dv.tree.set(k, "CEK")).strip() for k in kids)))
    # 3 — prefiks Rank konstan per kelompok
    exp_rk = {"BUMBU": "3", "CABE": "2", "PENTOL": "1"}
    ok.append(("CEK = 'Rank N · <label>' konstan per kelompok",
               all(dv.tree.set(k, "CEK").startswith(
                   f"Rank {exp_rk[str((dv._row_snaps.get(str(k)) or {})
                                    .get('barang', ''))]}")
                   for k in kids)))
    # 4 — nama barang per-baris
    ok.append(("Nama Barang PER-BARIS (OPSI A)",
               all(str(dv.tree.set(k, "Nama Barang")).strip() for k in kids)
               and not any(hasattr(dv, a) for a in
                           ("_static_merge_layout", "MERGE_COLS",
                            "_rank_map", "_gcek_map"))))
    # 5 — sort CEK = rank numerik asc (rank 1 = peringkat teratas dulu)
    dv._sort_by("CEK", reverse=False)
    for _ in range(30):
        root.update()
        time.sleep(0.02)
    rk_seq = [int(dv._grank_map.get(str(k), "0"))
              for k in dv.tree.get_children("")]
    ok.append(("sort CEK = rank NUMERIK asc (PENTOL '1' teratas — "
               "'Rank 2' < 'Rank 10' numerik, bukan leksikografis)",
               rk_seq == sorted(rk_seq)
               and rk_seq[0] == 1))

    shot("probe_v31127_cek_rank_sort")

    # balik urutan default utk screenshot kedua
    dv._sort_by("Nama Barang", reverse=False)
    for _ in range(30):
        root.update()
        time.sleep(0.02)
    shot("probe_v31127_cek_rank_default")

    print("\n== probe v31127: CEK ber-Rank + tabel datar ==")
    n_ok = 0
    for label, passed in ok:
        print(f"    {'OK' if passed else 'GAGAL'} — {label}")
        n_ok += bool(passed)
    print(f"HASIL: {n_ok}/{len(ok)} OK")
    dv.destroy()
    root.destroy()
    return 0 if n_ok == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
