"""
probe_merge_vertikal.py — probe audit v3.11.15 MERGE-VERTIKAL kolom
CEK + Rank + Nama Barang (user: "kolom Cek bisa gak merger vertical
dengan nama barang? di tab deviasi gr dan deviasi pcs? Rank juga
merger vertical").

Jalankan di bawah Xvfb:  DISPLAY=:99 python3 probes/v31115/probe_merge_vertikal.py

Memverifikasi KONTRAK DISPLAY secara programatik (lebih autoritatif
dari VLM — posisi piksel kolom kanan mudah salah-baca). Kontrak =
mesin stateless sticky (§98 test_ui_redesign):
  (1) payload head-run: nilai hanya di head tiap run kontigu
      bernilai-sama; RAW (_row_snaps/_rank_map/_cek_map) lengkap
      per-baris (KEY ADA — teks boleh kosong: rank dev-0/NaN → ''
      kontrak v3.9.65; cek baris bersih → '');
  (2) sticky madya-grup: di SEMUA posisi scroll (sweep 21 langkah),
      SEMUA baris terlihat patuh kontrak sticky — nilai run SELALU
      tampak (head bila terlihat, selain itu baris pertama run yang
      terlihat); tengah kelompok 30-baris, baris PERTAMA terlihat
      memuat nama kelompok (ala merged-cell Excel);
  (3) pasca-sort Deviasi: sweep penuh → tiap run ber-teks MINIMAL
      SATU sel berisi (nilai tak pernah hilang) + tak ada sel bernama
      SALAH + baris terlihat patuh kontrak (sub-blok barang+dev
      kontigu tetap merge);
  (4) interleave via sort Resto (stabil → beberapa pasangan barang
      sama bersebelahan di batas blok resto = run 2-baris SAH):
      tiap baris menampilkan nama yang BENAR (atau kosong = baris
      lanjutan run) + run pendek mayoritas singleton;
  (5) mode PCS: engine merge sama aktif (kolom Rank/Nama Barang
      head-run — satuan tak mengubah struktur).

EXPECTED: 5 blok "OK". Exit code 0 bila semua lulus.
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
MERGE_COLS = ("Nama Barang", "CEK", "Rank")


def ok(nama, kondisi, detail=""):
    print(("  OK " if kondisi else "  GAGAL ") + nama + (f" — {detail}" if detail else ""))
    if not kondisi:
        FAILED.append(nama)


def vis(tree, k):
    bb = tree.bbox(k)
    return bool(bb) and 0 <= bb[1] < tree.winfo_height()


def raw_runs(view, tree, col):
    """[(iids, teks), ...] run kontigu bernilai-sama, dari RAW maps."""
    snaps = view._row_snaps
    rk = view._rank_map
    ck = view._cek_map
    runs = []
    prev_key = None
    for k in tree.get_children(""):
        ks = str(k)
        b = str((snaps.get(ks) or {}).get("barang", ""))
        if col == "Nama Barang":
            key, text = b, b
        elif col == "Rank":
            t = str(rk.get(ks, ""))
            key, text = (b, t), t
        else:
            t = str(ck.get(ks, ""))
            key, text = (b, t), t
        if key != prev_key:
            runs.append(([k], text))
            prev_key = key
        else:
            runs[-1][0].append(k)
    return runs


def sticky_expected(view, tree, col):
    """{iid: teks} — head bila terlihat, selain itu baris pertama run
    yang terlihat; run tanpa teks → ''."""
    out = {}
    for iids, text in raw_runs(view, tree, col):
        if not text:
            for k in iids:
                out[k] = ""
            continue
        head = iids[0]
        if vis(tree, head):
            disp = head
        else:
            v = [k for k in iids if vis(tree, k)]
            disp = v[0] if v else head
        for k in iids:
            out[k] = text if k == disp else ""
    return out


def sweep(root, tree, steps=21):
    """Scroll 0.0→1.0 — tiap baris pernah masuk viewport (self-heal
    stateless menulis diff di tiap event scroll)."""
    for i in range(steps):
        tree.yview_moveto(i / (steps - 1))
        for _ in range(8):
            root.update()
        time.sleep(0.005)


def build_fixture():
    src = []

    def add(b, r, so26, sa):
        for t, sv in ((24, 20.0), (25, 20.0), (26, float(so26)), (27, 20.0)):
            for j, v in (("1.SO", sv), ("2.SALDO AKHIR", sa),
                         ("SALDO AWAL", 10.0),
                         ("4.IN", 2.0 if so26 == 20 else 0)):
                src.append({"Nama Barang": b, "JENIS": j, "NAMA RESTO": r,
                            "Tanggal": t, "NILAI": v, "SATUAN": "GR",
                            "AKTIF/NON": "AKTIF",
                            "KATEGORI": "COM DEVIASI - RESTO",
                            "SOURCE KIRIMAN": "GUDANG"})

    # 3 grup × 30 resto; dev = i%5 / i%3 / i%4 (ikat rank method="min")
    for i in range(1, 31):
        add("AYAM GORENG SPESIAL", f"R{i:02d}", 20, 20 - (i % 5))
        add("BUMBU RENDANG PADANG", f"R{i:02d}", 20, 20 - (i % 3))
        add("CABE MERAH KERING", f"R{i:02d}", 20, 20 - (i % 4))
    return src


def make_view(root, src, satuan="GR"):
    dv = DeviasiView(root, satuan_mode=satuan)
    dv.pack(fill="both", expand=True)
    dv.data = pd.DataFrame(src)
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
    return dv


def main():
    root = tk.Tk()
    root.geometry("1600x700+5+5")
    dv = make_view(root, build_fixture())
    t = dv.tree
    kids = list(t.get_children(""))
    n = len(kids)
    print(f"== fixture: {n} baris 3 kelompok × 30 (H={dv.tanggal_h}) ==")

    # (1) payload head-run + RAW lengkap (key-presence)
    print("== (1) payload head-run + RAW per-baris (key ada) ==")
    for col in MERGE_COLS:
        runs = raw_runs(dv, t, col)
        exp = {}
        for iids, text in runs:
            for k in iids:
                exp[k] = text if k == iids[0] else ""
        ok(f"layout head-run kolom {col}",
           all(str(t.set(k, col)) == exp[k] for k in kids))
    ok("RAW snapshot/_rank_map/_cek_map lengkap 90/90 (key ada — teks "
       "rank dev-0 kosong = kontrak v3.9.65)",
       all(str(k) in dv._row_snaps
           and str((dv._row_snaps.get(str(k)) or {}).get("barang", ""))
           and str(k) in dv._rank_map
           and str(k) in dv._cek_map
           for k in kids))

    # (2) sticky: sweep penuh — tiap posisi, baris terlihat patuh kontrak
    print("== (2) sticky stateless (sweep 21 posisi scroll) ==")
    bad_pos = []
    for i in range(21):
        t.yview_moveto(i / 20)
        for _ in range(8):
            root.update()
        vr = [k for k in kids if vis(t, k)]
        if not vr:
            continue
        for col in MERGE_COLS:
            exp = sticky_expected(dv, t, col)
            if any(str(t.set(k, col)) != exp[k] for k in vr):
                bad_pos.append((i, col))
    ok("semua baris TERLIHAT patuh kontrak sticky di 21 posisi × 3 kolom",
       not bad_pos, f"bad={bad_pos[:3]}")
    t.yview_moveto(38 / n)
    for _ in range(40):
        root.update()
    vr = [k for k in kids if vis(t, k)]
    snap0 = dv._row_snaps.get(str(vr[0]), {}) if vr else {}
    ok("tengah kelompok 30-baris: baris PERTAMA terlihat memuat NAMA "
       "KELOMPOK (sticky — nilai run selalu tampak)",
       bool(vr) and str(t.set(vr[0], "Nama Barang")) == snap0.get("barang"),
       f"first={t.set(vr[0], 'Nama Barang')!r}")

    # (3) pasca-sort Deviasi: sweep → nilai tak hilang & tak ada salah
    print("== (3) pasca-sort Deviasi (sub-blok kontigu tetap merge) ==")
    t.yview_moveto(0.0)
    for _ in range(40):
        root.update()
    dv._sort_by("Deviasi", reverse=True)
    for _ in range(60):
        root.update()
        time.sleep(0.01)
    sweep(root, t)
    lost = []      # run ber-teks tanpa satu pun sel berisi
    wrong = []     # sel menampilkan nama ≠ barang baris itu
    for col in MERGE_COLS:
        for iids, text in raw_runs(dv, t, col):
            if text and not any(str(t.set(k, col)).strip() for k in iids):
                lost.append((col, text[:20]))
    for k in t.get_children(""):
        d = str(t.set(k, "Nama Barang"))
        b = str((dv._row_snaps.get(str(k)) or {}).get("barang", ""))
        if d and d != b:
            wrong.append((d[:15], b[:15]))
    ok("tiap run ber-teks ≥1 sel berisi (nilai tak hilang) + TAK ADA "
       "sel bernama salah",
       not lost and not wrong,
       f"lost={lost[:3]} wrong={wrong[:3]}")
    vr = [k for k in t.get_children("") if vis(t, k)]
    exps = {c: sticky_expected(dv, t, c) for c in MERGE_COLS}
    ok("baris terlihat pasca-sort patuh kontrak sticky",
       bool(vr) and all(str(t.set(k, c)) == exps[c][k]
                        for k in vr for c in MERGE_COLS))

    # (4) interleave via sort Resto (stabil → beberapa run 2-baris SAH
    #     di batas blok resto — baris lanjutan run memang kosong)
    print("== (4) interleave (sort Resto — run 2-baris batas blok sah) ==")
    dv._sort_by("Resto", reverse=False)
    for _ in range(60):
        root.update()
        time.sleep(0.01)
    sweep(root, t)
    wrong4 = []
    lost4 = []
    for k in t.get_children(""):
        d = str(t.set(k, "Nama Barang"))
        b = str((dv._row_snaps.get(str(k)) or {}).get("barang", ""))
        if d and d != b:
            wrong4.append((d[:15], b[:15]))
    for iids, text in raw_runs(dv, t, "Nama Barang"):
        if text and not any(str(t.set(k, "Nama Barang")).strip()
                            for k in iids):
            lost4.append(text[:15])
    ok("tiap baris menampilkan nama yang BENAR (atau kosong = baris "
       "lanjutan run sah) + tiap run ≥1 sel",
       not wrong4 and not lost4,
       f"wrong={wrong4[:3]} lost={lost4[:3]}")
    named = sum(1 for k in t.get_children("")
                if str(t.set(k, "Nama Barang")).strip())
    runs4 = len(raw_runs(dv, t, "Nama Barang"))
    ok("interleave menghasilkan run pendek (mayoritas singleton — "
       "bukan 3 kelompok panjang lagi)",
       runs4 > 40 and named >= runs4,
       f"runs={runs4} named={named}")
    dv.destroy()

    # (5) mode PCS — engine merge sama aktif
    print("== (5) mode PCS (engine sama, satuan beda) ==")
    src = build_fixture()
    for row in src:
        row["SATUAN"] = "PCS"
    dv2 = make_view(root, src, satuan="PCS")
    t2 = dv2.tree
    ok("PCS: layout head-run Nama Barang + Rank aktif",
       all(not str(t2.set(k, "Nama Barang")).strip()
           or str(t2.set(k, "Nama Barang"))
           == str((dv2._row_snaps.get(str(k)) or {}).get("barang", ""))
           for k in list(t2.get_children(""))[1:])
       and any(not str(t2.set(k, "Rank")).strip()
               for k in list(t2.get_children(""))[1:]))
    runs2 = raw_runs(dv2, t2, "Nama Barang")
    heads2 = sum(1 for k in t2.get_children("")
                 if str(t2.set(k, "Nama Barang")).strip())
    ok("PCS: jumlah sel berisi = jumlah run kelompok",
       heads2 == len(runs2), f"heads={heads2} runs={len(runs2)}")
    dv2.destroy()

    root.destroy()
    print()
    if FAILED:
        print(f"PROBE GAGAL: {FAILED}")
        sys.exit(1)
    print("PROBE v3.11.15 MERGE-VERTIKAL: SEMUA OK")


if __name__ == "__main__":
    main()
