#!/usr/bin/env python3
"""
probe_sticky_torture.py — TORTURE MERGE/STICKY v3.11.16+ (app PENUH).

Rekonstruksi permanen (v3.11.18-restored): versi asli v3.11.17 hilang
bersama sandbox. 28 cek dalam 5 blok, SEMUA di jalur app penuh
(StockMonitorApp + load_data + select_and_wait — BUKAN view standalone)
dengan render async batched (batch 500 via after()):

  A. kontrak dasar — jumlah baris · _vmerge aktif · head = kelompok ·
     TIGA kolom sejajar di head · RAW lengkap · kontrak viewport awal.
  B. jalur scroll — wheel Windows ±120 · micro-delta trackpad ·
     keyboard (Next/Prior/End/Home/Down/Up) · drag scrollbar ·
     moveto fraksional tengah kelompok ×12 · burst 40 tanpa idle.
  C. JALUR BUTA — semua hook dimatikan (_sticky_merge_cb=None ·
     yscrollcommand di-unwrap · poller off) → gejala user TERREPRODUKSI
     (nama barang blank) → poller dinyalakan → sembuh (display & kontrak
     penuh) → hook sinkron dipulihkan.
  D. siklus hidup — tab switch <Map> · clone ⤢ (semua baris + poller
     aktif + kontrak tengah kelompok + poller berhenti saat window
     ditutup) · sort Rank batched (invalidasi sinkron pra-sort +
     kelompok KONTIGU + kontrak pasca on_done) · sort Nama Barang.
  E. cleanup.

Skala via env: STICKY_NBAR (default 45 barang multi-resto) ·
STICKY_NRESTO (default 300 resto/barang) + 5 singleton → 50 kelompok.
Default = 13.505 baris; STICKY_NRESTO=620 → 27.905 (skala produksi).

Jalankan di bawah Xvfb (Xvfb + probe dalam SATU sesi shell — proses
background tak selamat antar sesi di sandbox):
  DISPLAY=:99 python3 probes/v31117/probe_sticky_torture.py
"""
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk

import pandas as pd

from src.ui.app import StockMonitorApp
from test_ui_redesign import select_and_wait

NBAR = int(os.environ.get("STICKY_NBAR", "45"))
NRESTO = int(os.environ.get("STICKY_NRESTO", "300"))
N_ACR = 5
MERGE_COLS = ("Nama Barang", "Rank", "CEK")
N_EXPECT = NBAR * NRESTO + N_ACR

FAILED = []
PASSED = 0


def ok(nama, kondisi, detail=""):
    global PASSED
    if kondisi:
        PASSED += 1
        print(f"  OK {nama}" + (f" — {f'{detail}'}" if detail else ""))
    else:
        FAILED.append(nama)
        print(f"  GAGAL {nama}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------- fixture
def make_fixture() -> pd.DataFrame:
    rows = []
    for i in range(1, NBAR + 1):
        barang = f"BARANG GRUP {i:02d}"
        for j in range(NRESTO):
            resto = f"RESTO {j:03d}"
            so = 10.0 + ((i * 7 + j * 13) % 23)
            rows.append({"Nama Barang": barang, "JENIS": "SALDO AWAL",
                         "NAMA RESTO": resto, "Tanggal": 1, "NILAI": 10.0,
                         "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                         "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                         "Nomor": "RI-001", "Nomor PO": "PO-001",
                         "#Tgl/Jam Pembuatan IT": None})
            rows.append({"Nama Barang": barang, "JENIS": "1.SO",
                         "NAMA RESTO": resto, "Tanggal": 25, "NILAI": so,
                         "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                         "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                         "Nomor": "RI-025", "Nomor PO": "PO-025",
                         "#Tgl/Jam Pembuatan IT": None})
            rows.append({"Nama Barang": barang, "JENIS": "2.SALDO AKHIR",
                         "NAMA RESTO": resto, "Tanggal": 25, "NILAI": 10.0,
                         "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                         "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                         "Nomor": "RI-025", "Nomor PO": "PO-025",
                         "#Tgl/Jam Pembuatan IT": None})
    for i in range(1, N_ACR + 1):
        barang = f"BARANG ACR {i}"
        for jenis, tgl, val in (("SALDO AWAL", 1, 10.0),
                                ("1.SO", 25, 80.0 + i),
                                ("2.SALDO AKHIR", 25, 10.0)):
            rows.append({"Nama Barang": barang, "JENIS": jenis,
                         "NAMA RESTO": "RESTO 000", "Tanggal": tgl,
                         "NILAI": val, "SATUAN": "GR",
                         "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
                         "SOURCE KIRIMAN": "GUDANG", "Nomor": "RI-025",
                         "Nomor PO": "PO-025",
                         "#Tgl/Jam Pembuatan IT": None})
    return pd.DataFrame(rows)


# ------------------------------------------------------------- kontrak
def vis_rows(tree, kids, vh):
    out = []
    for k in kids:
        try:
            bb = tree.bbox(k)
        except tk.TclError:
            continue
        if bb and 0 <= bb[1] < vh:
            out.append(k)
    return out


def fast_violations(view, tree):
    """(bad_cols, n_vis) — tiap kelompok TERLIHAT punya TEPAT SATU baris
    non-empty per kolom merge, dan baris non-empty KETIGA kolom SAMA
    (sejajar ala kontrak kelompok)."""
    kids = list(tree.get_children(""))
    try:
        vh = tree.winfo_height()
    except tk.TclError:
        return list(MERGE_COLS), 0
    if vh <= 1:
        return list(MERGE_COLS), 0
    vis = vis_rows(tree, kids, vh)
    snaps = view._row_snaps
    bad = set()
    i = 0
    while i < len(vis):
        b = str((snaps.get(str(vis[i])) or {}).get("barang", ""))
        grp = [vis[i]]
        j = i + 1
        while j < len(vis) and str((snaps.get(str(vis[j])) or {})
                                   .get("barang", "")) == b and b:
            grp.append(vis[j])
            j += 1
        for col in MERGE_COLS:
            nz = [k for k in grp if str(tree.set(k, col)).strip()]
            if len(nz) != 1:
                bad.add(col)
        # sejajar: baris non-empty identik lintas kolom
        rows_nz = {tuple(k for k in grp if str(tree.set(k, col)).strip())
                   for col in MERGE_COLS}
        if len(rows_nz) != 1:
            bad.update(MERGE_COLS)
        i = j
    return sorted(bad), len(vis)


def contract_full(view, tree):
    """Kontrak PENUH: baris display = head bila terlihat, selain itu
    baris PERTAMA run yang terlihat."""
    bad, n_vis = fast_violations(view, tree)
    if bad or not n_vis:
        return False, n_vis
    kids = list(tree.get_children(""))
    snaps = view._row_snaps
    vh = tree.winfo_height()
    vis = vis_rows(tree, kids, vh)
    vset = set(map(str, vis))
    i = 0
    while i < len(vis):
        b = str((snaps.get(str(vis[i])) or {}).get("barang", ""))
        if not b:
            i += 1
            continue
        grp, j = [vis[i]], i + 1
        while j < len(vis) and str((snaps.get(str(vis[j])) or {})
                                   .get("barang", "")) == b:
            grp.append(vis[j])
            j += 1
        # head run penuh (kelompok kontigu di tree — cari via kids)
        full = []
        for k in kids:
            if str((snaps.get(str(k)) or {}).get("barang", "")) == b:
                full.append(k)
        head = full[0] if full else grp[0]
        want = head if str(head) in vset else grp[0]
        for col in MERGE_COLS:
            if not str(tree.set(want, col)).strip():
                return False, n_vis
            for k in grp:
                if k != want and str(tree.set(k, col)).strip():
                    return False, n_vis
        i = j
    return True, n_vis


def wait_clean(root, view, tree, fn, timeout=3.0):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        root.update()
        good, _ = fn(view, tree) if fn is contract_full else (*fn(view, tree), )
        if fn is fast_violations:
            good = not good[0]
        if good:
            return time.perf_counter() - t0
        time.sleep(0.02)
    return None


def pump(root, n=6, dt=0.03):
    for _ in range(n):
        root.update()
        time.sleep(dt)


def find_vsb(widget):
    out = []
    for c in widget.winfo_children():
        if isinstance(c, ttk.Scrollbar) and str(c.cget("orient")) == "vertical":
            out.append(c)
        out.extend(find_vsb(c))
    return out


def head_layout_ok(view, tree):
    """Layout PENUH (semua baris, bukan hanya viewport): nilai hanya di
    head kelompok — pakai RAW kelompok (_grank_map/_gcek_map)."""
    snaps, grk, gck = view._row_snaps, view._grank_map, view._gcek_map
    prev, n_heads = None, 0
    for k in tree.get_children(""):
        ks = str(k)
        b = str((snaps.get(ks) or {}).get("barang", ""))
        if b != prev:
            n_heads += 1
            want = {"Nama Barang": b, "Rank": str(grk.get(ks, "")),
                    "CEK": str(gck.get(ks, ""))}
            for col, t in want.items():
                if str(tree.set(k, col)) != t:
                    return False, 0
        else:
            for col in MERGE_COLS:
                if str(tree.set(k, col)).strip():
                    return False, 0
        prev = b
    return True, n_heads


def main():
    append1 = make_fixture()
    real = sys.stdout, sys.stderr
    root = tk.Tk()
    root.geometry("1440x900+0+0")
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real
    view = app.deviasi_gr_view
    tree = view.tree

    t0 = time.perf_counter()
    view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_gr, view)
    # tunggu batch insert selesai
    while len(tree.get_children("")) != N_EXPECT \
            and time.perf_counter() - t0 < 60:
        root.update()
        time.sleep(0.02)
    pump(root, 10, 0.03)
    t_load = time.perf_counter() - t0
    n = len(tree.get_children(""))
    print(f"== fixture: {n} baris · {NBAR + N_ACR} kelompok "
          f"(load+render {t_load:.1f}s) ==")

    # ================= A. kontrak dasar =================
    print("== A. kontrak dasar (app penuh, async batched) ==")
    ok("A1 jumlah baris sesuai fixture", n == N_EXPECT, f"n={n}")
    vm = getattr(tree, "_vmerge", None)
    ok("A2 _vmerge aktif (n cocok, 3 kolom run)",
       isinstance(vm, dict) and vm.get("n") == N_EXPECT
       and set(vm.get("runs", {})) == set(MERGE_COLS))
    lay, n_heads = head_layout_ok(view, tree)
    ok("A3 jumlah head = jumlah kelompok",
       lay and n_heads == NBAR + N_ACR, f"heads={n_heads}")
    ok("A4 KETIGA kolom sejajar di baris head (layout penuh)", lay)
    snaps_ok = all(
        str(k) in view._row_snaps
        and str((view._row_snaps.get(str(k)) or {}).get("barang", ""))
        and str(k) in view._rank_map and str(k) in view._cek_map
        for k in tree.get_children(""))
    ok("A5 RAW maps lengkap per-baris (paritas sheet v3.9.65)", snaps_ok)
    bad, n_vis = fast_violations(view, tree)
    ok("A6 kontrak sticky posisi awal (viewport)",
       not bad and n_vis > 0, f"bad_cols={bad} n_vis={n_vis}")

    # ================= B. jalur scroll =================
    print("== B. jalur scroll (wheel Windows · trackpad · keyboard · "
          "scrollbar · moveto · burst) ==")

    def scroll_wheel(delta, times):
        for _ in range(times):
            tree.event_generate("<MouseWheel>", delta=delta, when="now")
            root.update()

    scroll_wheel(-120, 25)
    pump(root)
    bad, n_vis = fast_violations(view, tree)
    ok("B1 wheel Windows delta=-120 ×25", not bad,
       f"bad_cols={bad} n_vis={n_vis}")
    scroll_wheel(120, 25)
    pump(root)
    bad, n_vis = fast_violations(view, tree)
    ok("B2 wheel Windows delta=+120 ×25", not bad,
       f"bad_cols={bad} n_vis={n_vis}")

    tree.yview_moveto(0.0)
    pump(root, 2)
    for _ in range(60):
        tree.event_generate("<MouseWheel>", delta=-3, when="now")
        root.update()
    pump(root)
    bad, n_vis = fast_violations(view, tree)
    ok("B3 trackpad micro-delta ×60", not bad,
       f"bad_cols={bad} n_vis={n_vis}")

    tree.focus_set()
    for key in ("<Next>", "<Prior>", "<End>", "<Home>", "<Down>", "<Up>"):
        tree.event_generate(key, when="now")
        pump(root, 2)
    bad, n_vis = fast_violations(view, tree)
    ok("B4 keyboard Next/Prior/End/Home/Down/Up", not bad,
       f"bad_cols={bad} n_vis={n_vis}")

    vsbs = [sb for sb in find_vsb(tree.master)]
    ok("B5a scrollbar vertikal ditemukan", bool(vsbs))
    if vsbs:
        sb = vsbs[0]
        sb.event_generate("<ButtonPress-1>", x=4, y=120, when="now")
        for dy in range(10):
            sb.event_generate("<B1-Motion>", x=4, y=120 + dy * 18,
                              when="now")
            root.update()
        sb.event_generate("<ButtonRelease-1>", when="now")
        pump(root)
        bad, n_vis = fast_violations(view, tree)
        ok("B5 scrollbar drag (press+motion)", not bad,
           f"bad_cols={bad} n_vis={n_vis}")
        sb.event_generate("<ButtonPress-1>", x=4, y=10, when="now")
        for dy in range(8):
            sb.event_generate("<B1-Motion>", x=4,
                              y=max(4, 10 - dy * 12), when="now")
            root.update()
        sb.event_generate("<ButtonRelease-1>", when="now")
        pump(root)
        bad, n_vis = fast_violations(view, tree)
        ok("B5b scrollbar drag kembali ke atas", not bad,
           f"bad_cols={bad} n_vis={n_vis}")

    # kelompok panjang + moveto ×12 posisi tengah kelompok
    snaps = view._row_snaps
    kids = list(tree.get_children(""))
    spans = {}
    for k in kids:
        b = str((snaps.get(str(k)) or {}).get("barang", ""))
        spans[b] = spans.get(b, 0) + 1
    longest = max(spans, key=spans.get)
    ok("B6a kelompok panjang tersedia utk uji tengah-grup",
       spans.get(longest, 0) >= 50,
       f"{longest} span={spans.get(longest)}")
    bad_pos = []
    for i in range(1, 13):
        tree.yview_moveto(i / 13)
        root.update()
        bad, _ = fast_violations(view, tree)
        if bad:
            bad_pos.append((i, bad))
    pump(root)
    ok("B6 moveto tengah kelompok ×12 posisi — nama+CEK+Rank tetap "
       "tampak (gejala 'hilang per grup' tak terjadi)", not bad_pos,
       f"bad_pos={bad_pos}")

    tree.yview_moveto(0.0)
    pump(root, 2)
    calls = {"n": 0}
    orig_sticky = view._vmerge_sticky

    def counting_sticky(t, _o=orig_sticky, _c=calls):
        _c["n"] += 1
        return _o(t)

    view._vmerge_sticky = counting_sticky
    for _ in range(40):
        tree.event_generate("<MouseWheel>", delta=-120, when="now")
    root.update()
    pump(root, 3)
    view._vmerge_sticky = orig_sticky
    bad, n_vis = fast_violations(view, tree)
    ok("B7 burst 40 scroll tanpa idle → kontrak tetap pulih", not bad,
       f"flush={calls['n']} bad_cols={bad} n_vis={n_vis}")

    # ================= C. jalur buta =================
    print("== C. jalur buta (semua hook dimatikan — poller hanya-nya) ==")
    tree.yview_moveto(0.0)
    pump(root, 3)
    cb_backup = getattr(tree, "_sticky_merge_cb", None)
    tree._sticky_merge_cb = None
    try:
        tree.configure(yscrollcommand="")
    except tk.TclError:
        pass
    tree._vmerge_poll_on = False

    tree.yview_moveto(0.55)
    pump(root, 3)
    vh = tree.winfo_height()
    kids = list(tree.get_children(""))
    vis = vis_rows(tree, kids, vh)
    blank = sum(
        1 for k in vis
        if not str(tree.set(k, "Nama Barang")).strip())
    ok("C2 jalur buta TANPA pertahanan: nama barang BLANK terjadi "
       "(reproduksi gejala user)", blank > len(vis) // 2,
       f"blank={blank}/{len(vis)}")

    tree._vmerge_poll_on = True
    tree.after(1, lambda: view._vmerge_poller(tree))
    t0 = time.perf_counter()
    dt_display = None
    while time.perf_counter() - t0 < 3.0:
        root.update()
        bad, _ = fast_violations(view, tree)
        if not bad:
            dt_display = (time.perf_counter() - t0) * 1000
            break
        time.sleep(0.02)
    ok("C3 poller menyembuhkan jalur buta (display ≤ ~2 tik 150ms)",
       dt_display is not None, f"display_heal={dt_display:.0f}ms")

    t0 = time.perf_counter()
    dt_contract = None
    while time.perf_counter() - t0 < 3.0:
        root.update()
        good, _ = contract_full(view, tree)
        if good:
            dt_contract = (time.perf_counter() - t0) * 1000
            break
        time.sleep(0.02)
    ok("C3b kontrak penuh pulih via poller", dt_contract is not None,
       f"contract_heal={dt_contract:.0f}ms")

    tree._sticky_merge_cb = cb_backup
    # v3.11.18-restored: pasang ULANG wrap yscrollcommand (jalur buta
    # melepasnya — C4 memulihkan KEDUA hook: cb sinkron utk wheel + wrap
    # utk moveto/see programatik; wrap = mirror _vmerge_bind: orig vsb.set).
    vsbs_c = [sb for sb in find_vsb(tree.master)]
    if vsbs_c and cb_backup:
        import contextlib as _cl
        _sb = vsbs_c[0]

        def _rewrap(*args, _sb=_sb, _cb=cb_backup):
            with _cl.suppress(tk.TclError):
                _sb.set(*args)
            _cb()
        with _cl.suppress(tk.TclError):
            tree.configure(yscrollcommand=_rewrap)
    tree.event_generate("<MouseWheel>", delta=-120, when="now")
    pump(root)
    bad, n_vis = fast_violations(view, tree)
    ok("C4 hook sinkron dipulihkan — wheel benar", not bad,
       f"bad_cols={bad} n_vis={n_vis}")

    # ================= D. siklus hidup =================
    print("== D. siklus hidup (tab switch · clone ⤢ · sort batched) ==")
    tree.yview_moveto(0.42)
    pump(root, 3)
    app.notebook.select(app.tab_proses)
    pump(root, 4)
    app.notebook.select(app.tab_deviasi_gr)
    t0 = time.perf_counter()
    dt_d = dt_dc = None
    while time.perf_counter() - t0 < 2.0:
        root.update()
        bad, _ = fast_violations(view, tree)
        if not bad and dt_d is None:
            dt_d = (time.perf_counter() - t0) * 1000
        good, _ = contract_full(view, tree)
        if good and dt_dc is None:
            dt_dc = (time.perf_counter() - t0) * 1000
        if dt_d is not None and dt_dc is not None:
            break
        time.sleep(0.02)
    ok("D1 tab switch → kembali (Map): kontrak pulih",
       dt_d is not None and dt_dc is not None,
       f"display={dt_d and f'{dt_d:.0f}ms'} "
       f"contract={dt_dc and f'{dt_dc:.0f}ms'}")

    tops_before = set(root.winfo_children())
    view._maximize()
    pump(root, 8, 0.05)
    tops = [w for w in root.winfo_children()
            if isinstance(w, tk.Toplevel) and w not in tops_before]
    ok("D2a clone window + tree ditemukan", bool(tops))
    if tops:
        win = tops[0]
        # tunggu tree clone UTAMA muncul & terisi PENUH (fase collect:
        # snapshot chunked — tree baru 0 baris; filter >100 baris di sini
        # = bug probe run-1: loop keluar instan → sort D3 menghapus baris
        # SUMBER saat snapshot masih jalan → 'Item row_N not found').
        # Tree utama = yang ber-kolom 'Rank' (frozen pane hanya #0).
        trees2 = []
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < 90:
            root.update()
            time.sleep(0.02)
            trees2 = [t for t in find_trees(win)
                      if "Rank" in (t.cget("columns") or ())
                      and len(t.get_children("")) >= N_EXPECT]
            if trees2:
                break
        ok("D2b clone memuat semua baris",
           bool(trees2) and len(trees2[0].get_children("")) == N_EXPECT,
           f"{len(trees2[0].get_children('')) if trees2 else 0}/{N_EXPECT}")
        if trees2:
            t2 = trees2[0]
            ok("D2c poller clone aktif",
               getattr(t2, "_vmerge_bound", False)
               and getattr(t2, "_vmerge_poll_on", False))
            t2.yview_moveto(0.55)
            root.update()
            t0 = time.perf_counter()
            dt2 = None
            while time.perf_counter() - t0 < 2.5:
                root.update()
                good, _ = contract_full(view, t2)
                if good:
                    dt2 = (time.perf_counter() - t0) * 1000
                    break
                time.sleep(0.02)
            ok("D2d clone: kontrak sticky + poller (tengah kelompok)",
               dt2 is not None, f"display={dt2 and f'{dt2:.0f}ms'}")
            win.destroy()
            err = None
            try:
                pump(root, 12, 0.04)
            except Exception as exc:  # noqa: BLE001
                err = exc
            alive = root.winfo_exists()
            ok("D2e poller clone BERHENTI setelah window ditutup "
               "(tree mati — loop berhenti sendiri)",
               err is None and alive, f"err={err}")

    # ---- sort batched ----
    view._sort_by("Rank", reverse=True)
    ok("D3a sort skala penuh: _vmerge dilumpuhkan sinkron pra-sort",
       getattr(tree, "_vmerge", None) is None)
    t0 = time.perf_counter()
    while (getattr(tree, "_vmerge", None) is None
           or len(tree.get_children("")) != N_EXPECT) \
            and time.perf_counter() - t0 < 60:
        root.update()
        time.sleep(0.02)
    pump(root, 5)
    snaps = view._row_snaps
    kids = list(tree.get_children(""))
    blocks, prev, heads = 0, None, []
    for k in kids:
        b = str((snaps.get(str(k)) or {}).get("barang", ""))
        if b != prev:
            blocks += 1
            heads.append(b)
        prev = b
    ok("D3b pasca sort Rank: kelompok KONTIGU (blok = kelompok)",
       blocks == NBAR + N_ACR, f"blocks={blocks} groups={NBAR + N_ACR}")
    tree.yview_moveto(1 / 3)
    pump(root, 3)
    bad, n_vis = fast_violations(view, tree)
    ok("D3c kontrak pasca sort batched (1/3)", not bad,
       f"bad_cols={bad} n_vis={n_vis}")
    tree.yview_moveto(2 / 3)
    pump(root, 3)
    bad, n_vis = fast_violations(view, tree)
    ok("D3d kontrak pasca sort batched (2/3)", not bad,
       f"bad_cols={bad} n_vis={n_vis}")

    view._sort_by("Nama Barang", reverse=False)
    t0 = time.perf_counter()
    while (getattr(tree, "_vmerge", None) is None
           or len(tree.get_children("")) != N_EXPECT) \
            and time.perf_counter() - t0 < 60:
        root.update()
        time.sleep(0.02)
    pump(root, 5)
    snaps = view._row_snaps
    kids = list(tree.get_children(""))
    blocks, prev, heads = 0, None, []
    for k in kids:
        b = str((snaps.get(str(k)) or {}).get("barang", ""))
        if b != prev:
            blocks += 1
            heads.append(b)
        prev = b
    ok("D4 pasca sort Nama Barang: kontigu + urut",
       blocks == NBAR + N_ACR and heads == sorted(heads))
    tree.yview_moveto(0.55)
    pump(root, 3)
    bad, n_vis = fast_violations(view, tree)
    ok("D4b kontrak pasca sort nama (0.55)", not bad,
       f"bad_cols={bad} n_vis={n_vis}")

    # ================= E. cleanup =================
    print("== E. cleanup ==")
    root.destroy()
    print()
    if FAILED:
        print(f"PROBE STICKY-TORTURE GAGAL: {len(FAILED)} — {FAILED}")
        sys.exit(1)
    print(f"PROBE STICKY-TORTURE: SEMUA OK — {PASSED} cek · {n} baris · "
          f"{NBAR + N_ACR} kelompok · jalur buta terbukti sembuh via "
          f"poller")


def find_trees(widget):
    out = []
    for c in widget.winfo_children():
        if isinstance(c, ttk.Treeview):
            out.append(c)
        out.extend(find_trees(c))
    return out


if __name__ == "__main__":
    main()
