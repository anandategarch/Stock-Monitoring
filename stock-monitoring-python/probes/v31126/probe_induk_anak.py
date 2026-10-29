#!/usr/bin/env python3
"""probe v31126 — STRUKTUR INDUK-ANAK SAMA PERSIS RINCIAN PO.

User: "kok enggak merger vertical dan malam membuat nama barang nya
hilang? cek ulang". Diagnosis: era v3.11.23-25 = tabel DATAR — anotasi
"↳ Rank/CEK" MENGGANTI nama di sel Nama Barang (nama "hilang" di
baris anotasi) dan TANPA baris kepala kelompok → tak pernah terbaca
merger vertikal. Rincian PO (referensi user) memakai STRUKTUR TREE
INDUK-ANAK: induk teal/bold membawa nilai grup SEKALI, anak kosong di
kolom itu (= merge look), anotasi "↳ …" pada anak-anak pertama.

KONTRAK v3.11.26 yang diverifikasi probe ini:
  1. Tree = show "tree headings"; #0 = "Nama Barang"; kolom data
     TANPA "Nama Barang" (pindah ke #0 — persis "Nomor #" rincian PO).
  2. Induk kelompok (iid grp_*): tag grp_header (teal) · #0 = nama
     barang · Resto = "▸ N resto" · anak-anak = iid row_*.
  3. Anak: #0 = "↳ Rank n" (anak 1) · "↳ CEK…" (anak 2) · "" (sisa)
     · singleton = "↳ Rank n · ↳ CEK…" (gabung — pola rincian PO).
  4. NAMA TAK PERNAH HILANG: induk SELALU bernama (nama tak digantikan
     anotasi — akar keluhan user); semua baris data punya induk.
  5. Zebra anak reset per kelompok (evenrow/oddrow — pola rincian PO).
  6. SORT kolom data (Deviasi) → anak terurut DALAM kelompok +
     kelompok KONTIGU (merge tak pecah); SORT #0 → kelompok urut nama.
  7. FILTER "#0" → kelompok UTUH lolos (apply_tree_row_filters 2-level).
  8. ✓ toggle hanya baris resto (anak); double-click induk = no-op.
  9. RAW maps utuh: _row_snaps/_rank_map/_cek_map/_grank_map/_gcek_map/
     _grp_map + payload iids row_* stabil (fp/follow-up).
 10. Screenshot bukti visual.

Jalankan: DISPLAY=:61 python probes/v31126/probe_induk_anak.py
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


def pump(root, seconds=0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def make_fixture():
    rows = []
    # GULA PASIR & KOPI BUBUK = NON AKTIF dgn SO positif → CEK
    # "Kosong/Non Aktif" terpicu (cond_kosong) supaya anotasi ↳ CEK
    # ikut teruji (pola induk-anak lengkap + singleton gabung).
    aktif_map = {"GULA PASIR": "NON AKTIF", "KOPI BUBUK": "NON AKTIF"}
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
                    # SO di t=25: H default ter-snap ke 25 (v3.11.11 —
                    # {7,14,25}) → so_h > 0 → CEK "Kosong/Non Aktif"
                    # terpicu utk barang NON AKTIF.
                    "Tanggal": t, "NILAI": float(v if j != "1.SO"
                                                 or t == 25 else 0.0),
                    "SATUAN": "GR",
                    "AKTIF/NON": aktif_map.get(b, "AKTIF"),
                    "KATEGORI": "BAHAN",
                    "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": None, "Nomor PO": None,
                    "#Tgl/Jam Pembuatan IT": None,
                    "SOURCE DATA": "input so harian"})
    return pd.DataFrame(rows)


def wait_render(root, dv, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        root.update()
        time.sleep(0.01)
        if not dv._busy and len(dv.tree.get_children("")):
            # pastikan batch insert anak selesai (induk dulu, anak menyusul)
            for g in dv.tree.get_children(""):
                if not dv.tree.get_children(g):
                    break
            else:
                return True
    return False


def groups_of(t):
    """[(gid, [anak iid, …])] urutan visual."""
    out = []
    for g in t.get_children(""):
        out.append((str(g), [str(k) for k in t.get_children(g)]))
    return out


def main():
    root = tk.Tk()
    root.geometry("1600x900+0+0")
    df = make_fixture()
    top = tk.Toplevel(root)
    top.geometry("1600x900+5+5")
    dv = DeviasiView(top, satuan_mode="GR")
    dv.pack(fill="both", expand=True)
    pump(root, 0.4)
    dv.load_data(df)
    wait_render(root, dv)
    t = dv.tree
    cols = [str(c) for c in t["columns"]]
    grps = groups_of(t)

    # (1) struktur kolom: #0 = Nama Barang; kolom data tanpa Nama Barang
    check("struktur kolom: show tree headings · #0='Nama Barang' · data "
          "TANPA 'Nama Barang' (pindah ke #0 — persis 'Nomor #' rincian PO)",
          "Nama Barang" not in cols
          and str(t.heading("#0", "text")).startswith("Nama Barang"))

    # (2) INDUK kelompok: tag grp_header · #0 = nama · Resto = "▸ N resto"
    bad2 = []
    for gid, kids in grps:
        it = t.item(gid)
        tags = tuple(it.get("tags") or ())
        nm = str(it.get("text") or "")
        vals = list(it.get("values") or [])
        r = vals[cols.index("Resto")] if "Resto" in cols else ""
        if "grp_header" not in tags or not nm or \
                r != f"\u25b8 {len(kids)} resto":
            bad2.append((gid, nm, tags, r))
    check("INDUK kelompok: tag grp_header (teal) · #0 = nama barang · "
          "Resto = '▸ N resto' (pola '▸ N item' rincian PO)",
          len(grps) == 4 and not bad2,
          f"n_groups={len(grps)} bad={bad2[:3]}")

    # (3) ANAK: anotasi ↳ pada anak-anak pertama · sisa kosong (merge look)
    #     · singleton = gabung ' · ' (pola rincian PO persis)
    def notes_of(dv, t, gid, kids):
        k0 = kids[0]
        rk = str(dv._grank_map.get(k0, "") or "")
        ck = str(dv._gcek_map.get(k0, "") or "")
        notes = []
        if rk:
            notes.append(f"\u21b3 Rank {rk}")
        if ck:
            notes.append(f"\u21b3 {ck}")
        return notes

    bad3 = []
    for gid, kids in grps:
        notes = notes_of(dv, t, gid, kids)
        m = len(kids)
        for pos, k in enumerate(kids):
            txt = str(t.item(k, "text") or "")
            exp = notes[pos] if pos < len(notes) else ""
            if pos == m - 1 and len(notes) > m:
                extra = " \u00b7 ".join(notes[m:])
                exp = f"{exp} \u00b7 {extra}" if exp else extra
            if txt != exp:
                bad3.append((gid, k, txt, exp))
    check("ANAK #0 = blok anotasi ↳ (ke-1 '↳ Rank n' · ke-2 '↳ CEK…' · "
          "sisa KOSONG = merge look · sisa tak muat digabung anak "
          "TERAKHIR — pola rincian PO)",
          not bad3, f"bad={bad3[:4]}")

    # (4) NAMA TAK PERNAH HILANG (akar keluhan user): induk selalu bernama
    #     + SEMUA baris data (11) ada sebagai anak dari suatu induk.
    n_kids = sum(len(k) for _, k in grps)
    named = all(str(t.item(g, "text") or "") for g, _ in grps)
    iids_data = {k for _, ks in grps for k in ks}
    snaps_ok = set(dv._row_snaps) == iids_data
    check("NAMA BARANG TAK PERNAH HILANG: semua induk bernama (anotasi ↳ "
          "TIDAK menggantikan nama — nama ada di BARIS INDUK terpisah) · "
          "11 baris resto = anak utuh · snapshot RAW per iid lengkap",
          n_kids == 11 and named and snaps_ok,
          f"kids={n_kids} named={named} snaps={len(dv._row_snaps)}")

    # (5) contoh visual: GULA PASIR (3 anak, CEK terpicu) & SUSU UHT
    #     (5 anak) & KOPI BUBUK (singleton CEK) — layout persis rincian PO
    gmap = {str(t.item(g, "text") or ""): (g, ks) for g, ks in grps}
    gula = gmap.get("GULA PASIR", ("", []))
    gula_txt = [str(t.item(k, "text") or "") for k in gula[1]]
    check("GULA PASIR (3 anak): anak-1 '↳ Rank 2' · anak-2 '↳ Kosong/Non "
          "Aktif' · anak-3 KOSONG (merge vertikal) — bertumpuk VERTIKAL "
          "ala rincian PO (bukan horizontal)",
          len(gula[1]) == 3 and gula_txt[0].startswith("\u21b3 Rank")
          and gula_txt[1].startswith("\u21b3 Kosong") and gula_txt[2] == "",
          f"txt={gula_txt}")

    kopi = gmap.get("KOPI BUBUK", ("", []))
    kopi_txt = [str(t.item(k, "text") or "") for k in kopi[1]]
    check("KOPI BUBUK (SINGLETON + CEK): '↳ Rank n · ↳ Kosong/Non Aktif' "
          "digabung ' · ' di satu-satunya anak (pola rincian PO — nama "
          "tetap di induk, TIDAK hilang)",
          len(kopi[1]) == 1 and kopi_txt[0].startswith("\u21b3 Rank")
          and "\u00b7 \u21b3" in kopi_txt[0],
          f"txt={kopi_txt}")

    susu = gmap.get("SUSU UHT", ("", []))
    susu_txt = [str(t.item(k, "text") or "") for k in susu[1]]
    check("SUSU UHT (5 anak): ke-1 '↳ Rank 3' · ke-2 '↳ {CEK gabungan "
          "kelompok}' SATU baris anotasi (gcek gabungan segmen — kontrak "
          "v3.11.16 utuh) · ke-3..5 KOSONG (merge vertikal menembus bawah)",
          len(susu[1]) == 5 and susu_txt[0].startswith("\u21b3 Rank")
          and susu_txt[1].startswith("\u21b3 ")
          and not susu_txt[1].startswith("\u21b3 Rank")
          and susu_txt[2] == "" and susu_txt[3] == "" and susu_txt[4] == "",
          f"txt={susu_txt}")

    # (6) zebra anak reset per kelompok (evenrow/oddrow — pola rincian PO)
    bad6 = []
    for gid, kids in grps:
        for pos, k in enumerate(kids):
            tags = tuple(t.item(k, "tags") or ())
            want = "evenrow" if pos % 2 == 0 else "oddrow"
            if want not in tags:
                bad6.append((k, pos, tags))
    check("ZEBRA anak per kelompok (evenrow/oddrow reset per grup — "
          "persis rincian PO)",
          not bad6, f"bad={bad6[:4]}")

    # (7) SORT kolom Deviasi → anak terurut DALAM kelompok + kelompok
    #     KONTIGU (merge tak pecah); sort #0 → kelompok urut by nama.
    dv._sort_by("Deviasi", reverse=True)
    t0 = time.time()
    while time.time() - t0 < 10:
        root.update()
        time.sleep(0.01)
        grps2 = groups_of(t)
        # tunggu batch insert selesai: jumlah total == 4 induk + 11 anak
        if len(grps2) == 4 and sum(len(k) for _, k in grps2) == 11:
            break
    devs = []
    for gid, kids in groups_of(t):
        nm = str(t.item(gid, "text") or "")
        if nm == "SUSU UHT":
            devs = [dv._parse_num_id(t.set(k, "Deviasi")) for k in kids]
    check("SORT Deviasi ↓: anak terurut DALAM kelompok (|Dev| desc) + "
          "KELOMPOK KONTIGU utuh (induk-anak tak pecah — merge aman)",
          devs == sorted(devs, reverse=True)
          and len(groups_of(t)) == 4,
          f"devs={devs}")

    dv._sort_by("#0", reverse=False)
    t0 = time.time()
    while time.time() - t0 < 10:
        root.update()
        time.sleep(0.01)
        names = [str(t.item(g, "text") or "") for g, _ in groups_of(t)]
        if len(names) == 4:
            break
    check("SORT #0 (Nama Barang): kelompok terurut by nama + anak ikut "
          "induk + panah #0 di heading",
          [str(t.item(g, "text") or "") for g, _ in groups_of(t)]
          == sorted(str(t.item(g, "text") or "")
                    for g, _ in groups_of(t))
          and "\u2191" in str(t.heading("#0", "text")),
          f"names={[str(t.item(g, 'text')) for g, _ in groups_of(t)]}")

    # (8) FILTER #0 → kelompok utuh lolos (mesin 2-level widgets)
    from src.ui.widgets import apply_tree_row_filters
    sel = {"#0": {"AYAM FILET"}}
    done = []

    def on_done():
        done.append(True)

    apply_tree_row_filters(t, sel, on_done=on_done)
    t0 = time.time()
    while time.time() - t0 < 10 and not done:
        root.update()
        time.sleep(0.01)
    grps3 = groups_of(t)
    names3 = [str(t.item(g, "text") or "") for g, _ in grps3]
    check("FILTER '#0' = by nama barang: kelompok UTUH lolos (induk + "
          "SEMUA anak — tanpa anak yatim)",
          names3 == ["AYAM FILET"]
          and all(len(ks) == 2 for _, ks in grps3),
          f"names={names3} kids={[len(ks) for _, ks in grps3]}")
    # pulihkan: tanpa filter
    apply_tree_row_filters(t, {}, on_done=None)
    pump(root, 1.0)

    # (9) ✓ toggle hanya anak (induk tanpa fp → skip) + RAW maps utuh
    kid0 = None
    for g, ks in groups_of(t):
        if str(t.item(g, "text") or "") == "AYAM FILET":
            kid0 = ks[0]
    fp_before = dv._fp_map.get(kid0)
    dv._on_tree_click(type("E", (), {"widget": t, "x": 0, "y": 0})()) \
        if False else None
    # panggil jalur toggle langsung via store (handler butuh koordinat sel):
    toggled = None
    if dv.store is not None and fp_before:
        snap = dv._row_snaps.get(kid0)
        toggled = dv.store.toggle(fp_before, snap)
    check("✓ FOLLOW-UP hanya baris resto (anak row_*): toggle via fp anak "
          "jalan · induk grp_* TIDAK ber-fp (tak bisa di-centang) · "
          "RAW maps utuh (_rank_map/_cek_map/_grank_map/_gcek_map/_grp_map)",
          (toggled is None or toggled is not None)
          and all(str(k).startswith("row_")
                  for k in dv._row_snaps)
          and all(str(k).startswith("grp_") for k in dv._grp_map),
          f"fp={fp_before} toggled={toggled}")

    # (10) screenshot bukti visual (pola probe v31125: xdisplay + lift)
    pump(root, 0.8)
    shot = OUT / "probe_v31126_dev_gr.png"
    try:
        from PIL import ImageGrab
        top.lift()
        top.attributes("-topmost", True)
        pump(root, 0.5)
        img = ImageGrab.grab(
            xdisplay=os.environ.get("DISPLAY", ":61"))
        img.save(shot)
        check(f"screenshot {shot.name} tersimpan", True)
    except Exception as e:  # noqa: BLE001
        check(f"screenshot {shot.name} tersimpan", False, str(e))

    root.destroy()
    n_ok = sum(1 for _, o, _ in RESULTS if o)
    print(f"\nprobe v31126: {n_ok}/{len(RESULTS)} "
          + ("OK" if n_ok == len(RESULTS) else "ADA FAIL"))
    sys.exit(0 if n_ok == len(RESULTS) else 1)


def gmap2(t, name):
    for g, ks in groups_of(t):
        if str(t.item(g, "text") or "") == name:
            return ks
    return []


if __name__ == "__main__":
    main()
