"""
probe_merge_group.py — probe audit v3.11.16 MERGE PER-KELOMPOK SEJAJAR
(user: "masih bug, belum merger vertikal antara kolom cek dan rank di
kolom nama barang. Justru ini kembali ke masalah lama yaitu nama barang
hilang untuk tiap grup nama barang. Deep audit dan fix").

Jalankan di bawah Xvfb:
  DISPLAY=:99 python3 probes/v31116/probe_merge_group.py

Kontrak (supersede probe v3.11.15 — run CEK/Rank diganti SPAN KELOMPOK):
  (1) SEJAJAR: TIGA kolom (Nama Barang · CEK · Rank) menampilkan nilai
      di baris HEAD kelompok yang SAMA — CEK = gabungan label unik
      (dedup per segmen ' · '), Rank = RANK KELOMPOK (peringkat
      Σ|Deviasi| barang, 1 = terbesar); baris lanjutan KOSONG di
      KETIGA kolom; RAW per-baris utuh (_rank_map/_cek_map — paritas
      sheet v3.9.65);
  (2) STICKY + POLLER: tengah kelompok (head di atas viewport) — baris
      pertama terlihat memuat nama+rank+cek BERSAMA; sweep 21 posisi
      scroll × 3 kolom patuh kontrak (jaring pengaman poller 150ms
      stateless aktif);
  (3) SORT Rank/CEK = nilai KELOMPOK: kelompok tetap KONTIGU utuh
      pasca sort (desc: grank besar teratas); sort analisa ▲ (label
      PER-BARIS RAW) tetap benar;
  (4) FILTER ⧩ Rank menyaring KELOMPOK utuh (konsisten popup = grank).

EXPECTED: 4 blok OK. Exit code 0 bila semua lulus.
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

import pandas as pd

from src.ui.deviasi_view import DeviasiView

FAILED = []
COLS = ("Nama Barang", "CEK", "Rank")


def ok(nama, kondisi, detail=""):
    print(("  OK " if kondisi else "  GAGAL ") + nama
          + (f" — {detail}" if detail else ""))
    if not kondisi:
        FAILED.append(nama)


def vis(tree, k):
    bb = tree.bbox(k)
    return bool(bb) and 0 <= bb[1] < tree.winfo_height()


def sticky_expected(view, tree, col):
    """{iid: teks} — head bila terlihat, else baris pertama kelompok
    yang terlihat; kelompok tanpa teks → ''."""
    snaps = view._row_snaps
    gk = view._grank_map
    gc = view._gcek_map
    out = {}
    run = []
    prev = None
    for k in tree.get_children(""):
        ks = str(k)
        b = str((snaps.get(ks) or {}).get("barang", ""))
        if b != prev:
            run = ([k], b)
            prev = b
        else:
            run[0].append(k)
        if col == "Nama Barang":
            text = b
        elif col == "Rank":
            text = str(gk.get(ks, ""))
        else:
            text = str(gc.get(ks, ""))
        if not text:
            out[k] = ""
            continue
        head = run[0][0]
        if vis(tree, head):
            disp = head
        else:
            v = [x for x in run[0] if vis(tree, x)]
            disp = v[0] if v else head
        out[k] = text if k == disp else ""
    return out


def build(nbar=6, nresto=30):
    src = []

    def add(b, r, so26, sa, in26):
        for t, sv in ((24, 20.0), (25, 20.0), (26, float(so26)), (27, 20.0)):
            for j, v in (("1.SO", sv), ("2.SALDO AKHIR", sa),
                         ("SALDO AWAL", 10.0), ("4.IN", in26)):
                src.append({"Nama Barang": b, "JENIS": j, "NAMA RESTO": r,
                            "Tanggal": t, "NILAI": v, "SATUAN": "GR",
                            "AKTIF/NON": "AKTIF",
                            "KATEGORI": "COM DEVIASI - RESTO",
                            "SOURCE KIRIMAN": "GUDANG"})
    for bi in range(1, nbar + 1):
        b = f"BARANG GRUP {bi:02d}"
        for ri in range(1, nresto + 1):
            dev = (bi * 7 + ri * 3) % 19          # unik → rank per-baris unik
            add(b, f"RESTO-{ri:03d}", 20, 20 - dev,
                2.0 if ri % 8 == 0 else 0)
    return src


def main():
    root = tk.Tk()
    root.geometry("1600x760+5+5")
    dv = DeviasiView(root, satuan_mode="GR")
    dv.pack(fill="both", expand=True)
    dv.data = pd.DataFrame(build())
    dv._show_content()
    dv._refresh(sync=True)
    for _ in range(400):
        root.update()
        if not dv._busy and len(dv.tree.get_children("")):
            break
        time.sleep(0.02)
    for _ in range(30):
        root.update()
        time.sleep(0.01)
    t = dv.tree
    kids = list(t.get_children(""))
    n = len(kids)
    print(f"== fixture: {n} baris 6 kelompok × 30 (H={dv.tanggal_h}) ==")

    # (1) SEJAJAR di head kelompok + RAW utuh
    print("== (1) merge per-kelompok SEJAJAR ==")
    heads = [k for k in kids if str(t.set(k, "Nama Barang")).strip()]
    ok("jumlah head = jumlah kelompok (6)",
       len(heads) == 6, f"heads={len(heads)}")
    ok("KETIGA kolom terisi di baris head yang SAMA (sejajar)",
       all(str(t.set(k, "Rank")).strip()
           and str(t.set(k, "CEK")).strip() for k in heads))
    ok("baris lanjutan kelompok KOSONG di KETIGA kolom",
       all(not any(str(t.set(k, c)).strip() for c in COLS)
           for k in kids if k not in heads))
    ok("RANK KELOMPOK = peringkat Σ|Deviasi| (1..6 unik — dev unik "
       "per grup → total beda)",
       sorted(str(t.set(k, "Rank")) for k in heads) ==
       [str(i) for i in range(1, 7)])
    # Σ|Deviasi| per kelompok dari RAW snapshot vs grank
    sums = {}
    for k in kids:
        sn = dv._row_snaps.get(str(k)) or {}
        sums[sn.get("barang", "")] = sums.get(sn.get("barang", ""), 0.0) \
            + abs(float(sn.get("deviasi", 0.0) or 0.0))
    order = sorted(sums, key=lambda b: -sums[b])
    ok("grank head konsisten Σ|Deviasi| terbesar→1 "
       f"(terbesar={order[0][:14]})",
       str(t.set(next(k for k in heads
                      if str((dv._row_snaps.get(str(k)) or {})
                             .get("barang", "")) == order[0]),
                 "Rank")) == "1")
    ok("RAW per-baris utuh (_rank_map/_cek_map lengkap — paritas sheet "
       "v3.9.65)",
       all(str(k) in dv._rank_map and str(k) in dv._cek_map
           for k in kids)
       and any(str(dv._rank_map.get(str(k), "")).strip() for k in kids))
    ok("CEK gabungan kelompok TANPA segmen duplikat (dedup per segmen)",
       all(len(set(str(t.set(k, "CEK")).split(" \u00b7 ")))
           == len(str(t.set(k, "CEK")).split(" \u00b7 "))
           for k in heads if str(t.set(k, "CEK")).strip()))

    # (2) sticky + poller
    print("== (2) sticky + poller (sweep 21 posisi) ==")
    ok("poller 150ms aktif di tree",
       getattr(t, "_vmerge_poll_on", False) is True)
    bad = []
    for i in range(21):
        t.yview_moveto(i / 20)
        for _ in range(8):
            root.update()
        time.sleep(0.005)
        vr = [k for k in t.get_children("") if vis(t, k)]
        if not vr:
            continue
        for c in COLS:
            exp = sticky_expected(dv, t, c)
            if any(str(t.set(k, c)) != exp[k] for k in vr):
                bad.append((i, c))
    ok("semua baris TERLIHAT patuh kontrak sticky (21 posisi × 3 kolom)",
       not bad, f"bad={bad[:3]}")
    t.yview_moveto(40 / n)
    for _ in range(40):
        root.update()
    vr = [k for k in t.get_children("") if vis(t, k)]
    ok("tengah kelompok: baris PERTAMA terlihat memuat nama+rank+CEK "
       "BERSAMA (sticky)",
       bool(vr) and all(str(t.set(vr[0], c)).strip() for c in COLS),
       f"first={(str(t.set(vr[0], 'Nama Barang'))[:14] if vr else None)}")

    # (3) sort Rank (kelompok) — kontigu utuh
    print("== (3) sort Rank = nilai kelompok ==")
    t.yview_moveto(0.0)
    for _ in range(30):
        root.update()
    dv._sort_by("Rank", reverse=True, tree=t)
    for _ in range(60):
        root.update()
        time.sleep(0.01)
    seq = [str((dv._row_snaps.get(str(k)) or {}).get("barang", ""))
           for k in t.get_children("")]
    # kelompok kontigu: tiap barang muncul dalam SATU blok
    blocks = []
    for b in seq:
        if not blocks or blocks[-1] != b:
            blocks.append(b)
    ok("pasca sort Rank: kelompok KONTIGU utuh (6 blok)",
       len(blocks) == 6 and len(set(blocks)) == 6, f"blocks={len(blocks)}")
    exp = sticky_expected(dv, t, "Rank")
    vr = [k for k in t.get_children("") if vis(t, k)]
    ok("layout Rank pasca sort = kontrak (baris terlihat)",
       bool(vr) and all(str(t.set(k, "Rank")) == exp[k] for k in vr))

    # (4) filter ⧩ Rank menyaring KELOMPOK utuh
    print("== (4) filter Rank = kelompok utuh ==")
    pl = dv._prepare_rows({"col_sel": {"Rank": {"1"}},
                           "tanggal_h": dv.tanggal_h,
                           "kategori": None, "aktif": None})
    rows = [(sn.get("barang"), sn.get("resto"))
            for sn in pl.get("row_snaps", {}).values()]
    ok("filter Rank={'1'} → kelompok grank-1 UTUH (30 baris, 1 barang)",
       len(pl["items"]) == 30 and len({r[0] for r in rows}) == 1,
       f"n={len(pl['items'])} barangs={len({r[0] for r in rows})}")
    cv = {str(x) for x in dv._col_values("Rank")}
    ok("popup ⧩ Rank = RANK KELOMPOK yang tampil ({'1'..'6'})",
       cv == {str(i) for i in range(1, 7)}, f"got {cv}")

    root.destroy()
    print()
    if FAILED:
        print(f"PROBE GAGAL: {FAILED}")
        sys.exit(1)
    print("PROBE v3.11.16 MERGE KELOMPOK: SEMUA OK")


if __name__ == "__main__":
    main()
