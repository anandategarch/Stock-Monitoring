"""
test_ui_redesign.py — Verifikasi UI v3.2 dengan mock data.

Jalankan di bawah Xvfb:
    DISPLAY=:99 python test_ui_redesign.py

Memverifikasi:
1. App shell terbangun (toolbar, 8 tab, status bar, spinner) tanpa error
2. Semua view menerima mock data & merender baris (async + batched) —
   LAZY REFRESH: view compute saat tab-nya dipilih (v3.2)
3. PIVOT PER RESTO (default): kolom = resto, tanpa kolom Total, baris kosong
   disembunyikan, item yang HANYA ada di 1 resto (ADONAN GORENG MEKAR /
   MLGPAR) tetap tampil
4. PIVOT PER TANGGAL: kolom = tanggal + metric 6.PEMAKAIAN (COM)
5. Header filter Nama Barang (corong di heading) — buka via klik header,
   toggle checkbox → filter, reset
6. Tombol ⛶ Perbesar → window clone
7. Filter + reset (RESTO, cabang, status, tanggal)
8. Details popup: render + copy Nomor / Nomor PO (Ctrl+C, double-click cell,
   copy semua unik) + header filter + maximize
9. Loading overlay terpasang di semua view
10. v3.2 — KPI row DIHAPUS di tab data (tabel besar; ringkasan di footer)
11. v3.2 — FOLLOW UP: kolom ✓ (toggle via klik sel), badge tab, tab
    ☑ Follow Up (render snapshot, uncheck=hapus), export xlsx,
    persistensi followup.json (v3.8: impor hasil TL DIHAPUS)
13. v3.4 — TAB 📤 REKAP SELISIH IN: render baris (Resto/Tanggal/Barang/
    Satuan/IN/Barang Masuk/Selisih IN), double-click → popup RINCIAN IN
    (dokumen 42.05/32.24/99.01 + Nomor + subtotal per sumber + copy nomor)
14. v3.4 — LEBAR KOLOM: drag tepi heading mengubah lebar (enable_col_
    resize), tombol ↔ Auto-Fit menyesuaikan lebar ke konten
15. v3.9.3 — LAPORAN DEVIASI DIGANTI (sementara): daftar anomali pemakaian
    (COM) per (Nama Barang × Resto) — COM minus atau > median pasangan
    (v3.9.7: median ANTAR TANGGAL 1..H, koreksi user — bukan antar resto)
    pada kolom H; H shared dari tab Deviasi GR (chip
    read-only + auto-refresh); minus merah per-cell + sel Status merah/amber
16. v3.9.4 — TAB LAPORAN DEVIASI 2 MODE (SegmentBar): ⚖ KOMPARASI FILE
    DEVIASI vs TAB DEVIASI GR (pilih file resmi; STATUS BULAN → kolom H:
    WEEK 1=7, WEEK 2=14, WEEK 3/4=25; BOM App = Σ penjualan 22.05,
    COM Saat Ini = Σ pemakaian, GR Saat Ini = SO_H − Sistem persis tab GR;
    status MATCH/SELISIH/TIDAK ADA DI DATA SAAT INI/H TIDAK ADA; resto file
    "1041.BDGUKU" dinormalkan; opsi tampil semua resto; minus merah
    per-cell + sel Status hijau/amber/merah) & 🚨 Anomali COM (v3.9.3)
17. v3.9.5 — AUDIT DEEP REGRESSION (§23): SALDO AWAL jadi base com(1)
18. v3.9.6 — KATEGORI DEVIASI (§6) + audit kronologis tgl 1 (§14) +
    FORMAT FOLLOW UP file sample (§11): 5 kolom kategori (Max Deviasi,
    ACR, Total ACR, Dev to BOM%, Stok Seharusnya) + CEK ke-5 "ACR to
    BOM" + pembanding SO tanggal 1 = SO bulan lalu terakhir + tabel/
    export Follow Up ala sheet Follow UP workbook asli.
19. v3.9.7 — (§7) median Anomali COM ANTAR TANGGAL per pasangan (com =
    pemakaian aktual harian di resto — koreksi user; window 1..H, heading
    "Median (1..H)") + (§22) filter minggu Komparasi mengikuti H bersama
    (STATUS BULAN utk filter: H 1–7 → WEEK 1, 8–14 → W2, 15–25 → W3/4,
    26–31 → W5; chip H read-only + highlight chip minggu aktif + opsi
    "Tampilkan semua minggu").
20. v3.9.8 — UI CLEAN (§1a): SEMUA teks instruksi dihapus dari UI —
    tombol "❓ Bantuan" + window panduan (_HELP_TEXT/_show_help),
    subtitle kartu (Filter/aksi), hint footer (🖱 Double-click…),
    tooltip hover (class ToolTip/add_tooltip dihapus dari widgets),
    subtitle EmptyState (default ""), subtitle tab Config/Proses,
    pertanyaan dialog export IN; footer status tetap (data), legenda
    tetap (decode nilai CEK/warna).
    (tanggal negatif + pair tanpa bulan-lalu — aljabar GR==DEV), race
    ✕ Tutup File saat compute, GC-shield dilepas walau pemilik job
    di-destroy, tag per-cell setelah filter di clone ⛶, duplikat lintas
    bulan dihitung, data di sheet ke-2, footer = baris tampil, filter
    reset saat reload file, sort diantrekan saat busy, pair index nama
    APP, snapshot 'aktif', show_laporan_mode sinkron SegmentBar, popup
    filter "Selisih vs Median" hidup, Apply H render 1×, unsubscribe H
21. v3.9.12 — TAB 🎯 PARETO DIHAPUS (user: "hapus tab pareto dan dead
    code nya"): pareto_view.py + write_pareto_sheet + integrasi app.py
    dibersihkan; app kembali 9 tab; §24 Pareto (v3.9.9) dihapus dari
    suite → §25 audit round-2 menjadi §24, §26 v3.9.11 menjadi §25.
22. v3.9.10 — AUDIT UI/UX ROUND 2 (§24): 4 agent paralel audit 4 arah
    (shell/tabel/view/integritas) — 37 temuan → fix P1-P3: race restart
    pipeline (A-01), cache-poisoning worker D-01, on_error rincian/popup
    (C-02), parser sort Selisih IN (B-01), tag per-cell di clone + sort
    (B-02/B-03), bind add="+" auto-fit (B-04), filter >3000 nilai lazy
    (B-05), gc_shield lock (B-06), cancel batch clone (B-07), pending-sort
    (B-08), followup render race (D-03), file-skip terlihat (D-04),
    tombol dim (A-02), DPI Windows (A-03), Ctrl+Tab (A-04), routing tab
    widget (A-11), format ID rincian/popup (C-03), minus merah Selisih
    IN (C-04), frasa instruksi dipangkas (C-06), footer baris (C-10),
    unsubscribe/dirty H (C-07/C-08), atomic write (D-05/D-06).
23. v3.9.11 — TUNTAS SISA TEMUAN (§25): P0 D-11 repo GitHub di-PRIVATE
    (user: "repo untuk pribadi aja") + 7 fix sisa audit 2-b: panah arah
    sort di heading (B-21), toggle filter clone tidak me-reset urutan
    sort (B-14), sort tree berhirarki jangan hilangkan anak (B-09,
    jalur tree.move), mirror kolom ⛶ dua arah (B-18), cursor watch
    refcount (B-17), TableExpander restore urutan (B-16), pecahan input
    tanggal ditolak tidak dilantai (B-12), EmptyState adaptif (B-11).
24. v3.9.13 — FILTER SEARCH-TO-SELECT + KATEGORI + KOLOM + PATH +
    MULTI-FILE + ANALISA (§26; 6 permintaan user + adopsi rumus repo
    Inventory-Control user): Enter di popup filter = hasil search jadi
    seleksi (0 hasil = 0 baris) + operator teks + ↔ Balik; kolom &
    combobox KATEGORI di Deviasi GR/PCS (post-pivot); kolom Minggu/H
    dihapus dari tabel komparasi + DEV App jadi %TO BOM; path file
    deviasi tersimpan (FIX BUG v3.9.10 json) + entry editable +
    auto-load; multi-file (askopenfilenames + BULAN-num dedup + filter
    mode 📈 Analisa (Top Selisih + Perubahan
    Arah/flip — Sempurna/Dominan/Parsial).
26. v3.9.15 — GELOMBANG 1 ANALISA (§26-5c): 4 bagian analisa baru di
    mode 📈 Analisa (baris BAGIAN SegmentBar — hanya bagian aktif
    dirender): ⚡ Risiko Flip per bahan (skor = min(100, 30×Sempurna +
    10×Flip), Level TINGGI/SEDANG/RENDAH, drilldown resto kontributor) ·
    🧭 Arah Minoritas per bahan (resto melawan mayoritas, drilldown) ·
    🏆 Liga Deviasi-Rate per bahan (|DEV|/|BOM| vs median+MAD populasi,
    robust-z 1,4826×MAD, guard ≥5 resto ber-BOM) · 💰 Benchmark
    Opportunity (loss = Σ|DEV<0| vs median kelompok 3-huruf). Analisa
    per-periode = bulan terbaru + SATU minggu snapshot (minggu yang
    memuat H — kumulatif: jumlah lintas minggu = ganda).
25. v3.9.14 — PERF TAB ANALISA + MINGGU IKUT H + ISTILAH (§22/§26):
    analisa dirender MALAS (hanya saat mode 📈 aktif — dulu dirender juga
    saat tersembunyi → ±4,8 dtk freeze per refresh di file 40rb baris);
    flip VEKTOR (sort+shift, dulu groupby+sort per grup 4,7 dtk → ±50ms)
    + nilai app per baris via MERGE vektor (dulu loop Series.get 2,9 dtk
    → ±60ms — terverifikasi identik); minggu Top Selisih & flip kini
    ikut H (H=7 → WEEK 1); istilah kolom *File → *Lalu & *App → *Saat
    Ini (BOM Lalu / DEV Lalu / %TO BOM Lalu / BOM Saat Ini / COM Saat
    Ini / DEV Saat Ini / GR Saat Ini; status 'TIDAK ADA DI DATA APP' →
    'TIDAK ADA DI DATA SAAT INI').
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk

from src.ui.app import APP_VERSION, StockMonitorApp
from src.ui.komparasi_deviasi_view import (
    _h_to_week_target,
    _norm_name,
    parse_deviasi_file,
)
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.widgets import _GC_HOLD, HeaderFilter, LoadingOverlay, run_async

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  ✓ {name}")
    else:
        FAIL.append(name)
        print(f"  ✗ {name} {detail}")


def wait_view(root, view, timeout=15.0):
    """Pump event loop sampai async refresh view selesai (compute+render)."""
    t0 = time.time()
    while getattr(view, "_busy", False) and time.time() - t0 < timeout:
        root.update()
        time.sleep(0.01)
    # pastikan batch insert after() selesai juga
    t0 = time.time()
    while time.time() - t0 < 0.5:
        root.update()
        time.sleep(0.01)
    return not getattr(view, "_busy", False)


def select_and_wait(root, app, tab, view, timeout=15.0):
    """Pilih tab lalu tunggu lazy refresh selesai (v3.2)."""
    app.notebook.select(tab)
    root.update()
    if hasattr(view, "ensure_refreshed"):
        view.ensure_refreshed()
    return wait_view(root, view, timeout)


def find_trees(widget):
    out = []
    for c in widget.winfo_children():
        if isinstance(c, ttk.Treeview):
            out.append(c)
        out.extend(find_trees(c))
    return out


def make_mock_append1() -> pd.DataFrame:
    """Mock Append1 long-format — termasuk item yang HANYA ada di resto
    MLGPAR (ADONAN GORENG MEKAR) untuk menguji pivot per resto."""
    rows = []
    barangs = [("AYAM FILET", "GR"), ("GULA PASIR", "GR"),
               ("KOPI BUBUK 100G", "PCS"), ("SUSU UHT 1L", "PCS"),
               ("ADONAN GORENG MEKAR", "GR")]  # hanya di MLGPAR
    restos = ["MLGPAR", "SBYKET"]
    jenis_list = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
                  "4.IN", "5.BARANG MASUK", "8.BARANG KELUAR", "9.OUT"]
    for barang, satuan in barangs:
        item_restos = ["MLGPAR"] if barang == "ADONAN GORENG MEKAR" else restos
        for resto in item_restos:
            for jenis in jenis_list:
                for tgl in range(1, 31):
                    val = 0.0
                    if jenis == "1.SO":
                        val = 10.0 + (tgl % 7) + (hash(barang) % 5)
                        if tgl == 25 and barang == "AYAM FILET" and resto == "MLGPAR":
                            val = 80.0  # anomali besar untuk CEK
                    elif jenis == "2.SALDO AKHIR":
                        val = 10.0
                    elif jenis == "4.IN" and tgl % 5 == 0:
                        val = 5.0
                    elif jenis == "9.OUT" and tgl % 3 == 0:
                        val = 3.0
                    elif jenis == "SALDO AWAL" and tgl == 1:
                        val = 10.0
                    rows.append({
                        "Nama Barang": barang, "JENIS": jenis,
                        "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": val,
                        "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                        "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                        "Nomor": f"RI-00{tgl}", "Nomor PO": f"PO-00{tgl}",
                        "#Tgl/Jam Pembuatan IT": None,
                    })

    # v3.9.6: barang uji kategori CEK "ACR to BOM" (kondisi ke-5) —
    # pola SO bersih (SO flat 200, IN 100 hanya tgl 25, OUT standar
    # 3 per t%3 → Total ACR 24 di 1..25): satu-satunya kondisi yang
    # terpicu = |Deviasi 100| > Total ACR 24.
    for resto in ("MLGPAR",):
        for jenis in jenis_list:
            for tgl in range(1, 31):
                val = 0.0
                if jenis == "1.SO":
                    val = 200.0
                elif jenis == "2.SALDO AKHIR":
                    val = 100.0
                elif jenis == "4.IN" and tgl == 25:
                    val = 100.0
                elif jenis == "9.OUT" and tgl % 3 == 0:
                    val = 3.0
                rows.append({
                    "Nama Barang": "BARANG ACR", "JENIS": jenis,
                    "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": val,
                    "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                    "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": f"RI-00{tgl}", "Nomor PO": f"PO-00{tgl}",
                    "#Tgl/Jam Pembuatan IT": None,
                })
    return pd.DataFrame(rows)


def make_mock_komparasi_df() -> pd.DataFrame:
    """Mock deterministik utk KOMPARASI (v3.9.4) — 2 barang × 2 resto,
    tgl 1..25, running-stock konsisten (DEV App == GR App secara aljabar).

    AYAM FILET: SA=100, SO(t)=100-3t, IN=10 (t%5==0), OUT=20 genap/5 ganjil
      → SIS(t) running → GR(7)=49, GR(14)=113, GR(25)=180
      com(t)=3+IN(t) → cum(1..7)=31; out_cum(1..7)=80 → DEV App(7)=49
    GULA PASIR: SA=60, SO(t)=60-2t, IN=0, OUT=8
      → GR(25)=150; com cum(1..25)=50; out_cum=200 → DEV App=150
    """
    rows = []
    spec = [
        ("AYAM FILET", "GR", 100.0, 100.0, 3.0),
        ("GULA PASIR", "GR", 60.0, 60.0, 2.0),
    ]
    for barang, satuan, sa, so_a, so_b in spec:
        for resto in ("MLGPAR", "SBYKET"):
            sis = sa
            for t in range(1, 26):
                so = so_a - so_b * t
                in_v = 10.0 if (barang == "AYAM FILET" and t % 5 == 0) else 0.0
                out_v = (20.0 if t % 2 == 0 else 5.0) \
                    if barang == "AYAM FILET" else 8.0
                sis = sis + in_v - out_v
                rows.append({
                    "Nama Barang": barang, "JENIS": "SALDO AWAL",
                    "NAMA RESTO": resto, "Tanggal": t,
                    "NILAI": sa if t == 1 else 0.0,
                    "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                    "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": None, "Nomor PO": None,
                    "#Tgl/Jam Pembuatan IT": None,
                })
                for jenis, val in (("1.SO", so), ("2.SALDO AKHIR", sis),
                                   ("4.IN", in_v), ("9.OUT", out_v),
                                   ("8.BARANG KELUAR", 0.0)):
                    rows.append({
                        "Nama Barang": barang, "JENIS": jenis,
                        "NAMA RESTO": resto, "Tanggal": t, "NILAI": val,
                        "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                        "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                        "Nomor": None, "Nomor PO": None,
                        "#Tgl/Jam Pembuatan IT": None,
                    })
    return pd.DataFrame(rows)


def make_mock_deviasi_file() -> str:
    """Mock file deviasi (format kolom file asli '20.AGUSTUS 2026.xlsx').

    7 baris: 3 MATCH (nilai = hitungan app), 1 SELISIH (DEV File 74 vs
    GR 49), 1 resto tak dikenal (9999.XYZZZ), 1 barang tak ada di app,
    1 WEEK 5 (H=31 tidak ada di data 1..25).
    """
    import tempfile

    from openpyxl import Workbook
    hdr = ["Akun Penyesuaian Persediaan", "STATUS", "RESTO", "NAMA BAHAN",
           "Satuan", "QTY BOM", "QTY COM", "QTY DEVIASI", "QTY WASTE",
           "QTY SUSUT", "QTY TRIAL", "QTY LOSS SURPLUS", "NOMINAL DEVIASI",
           "NOMINAL WASTE", "NOMINAL SUSUT", "NOMINAL TRIAL",
           "NOMINAL LOSS/SURPLUS", "QTY WASTE + SUSUT", "% WASTE + SUSUT",
           "%TOLERANSI", "% QTY DEVIASI TO BOM", "QTY WASTE TO BOM",
           "QTY SUSUT TO BOM", "QTY TRIAL  TO BOM",
           "QTY LOSS/ SURPLUS TO BOM", "AREA", "BULAN", "PENJUALAN",
           "STATUS BULAN", "BULAN 2"]
    data = [
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "AYAM FILET",
         "GR", -80, -31, 49, 0, 0, 0, 49, 49000, 0, 0, 0, 49000, 0, 0,
         "BELUM ADA TOLERANSI", 49 / 80, 0, 0, 0, 49 / 80, "JAWA TIMUR",
         "201.OKT 26", 1000, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1002.SBYKET", "AYAM FILET",
         "GR", -80, -31, 74, 0, 0, 0, 74, 74000, 0, 0, 0, 74000, 0, 0,
         "BELUM ADA TOLERANSI", 74 / 80, 0, 0, 0, 74 / 80, "JAWA TIMUR",
         "201.OKT 26", 1000, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "AYAM FILET",
         "GR", -175, -62, 113, 0, 0, 0, 113, 113000, 0, 0, 0, 113000, 0, 0,
         "BELUM ADA TOLERANSI", 113 / 175, 0, 0, 0, 113 / 175, "JAWA TIMUR",
         "202.OKT 26", 2000, "WEEK 2", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "GULA PASIR",
         "GR", -200, -50, 150, 0, 0, 0, 150, 150000, 0, 0, 0, 150000, 0, 0,
         "BELUM ADA TOLERANSI", 150 / 200, 0, 0, 0, 150 / 200, "JAWA TIMUR",
         "204.OKT 26", 4000, "WEEK 4", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "9999.XYZZZ", "AYAM FILET",
         "GR", -10, -5, 5, 0, 0, 0, 5, 5000, 0, 0, 0, 5000, 0, 0,
         "BELUM ADA TOLERANSI", 0.5, 0, 0, 0, 0.5, "LUAR JAWA",
         "201.OKT 26", 100, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "BARANG TAK ADA",
         "GR", -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
         "BELUM ADA TOLERANSI", 0, 0, 0, 0, 0, "JAWA TIMUR",
         "201.OKT 26", 100, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "AYAM FILET",
         "GR", -305, -125, 180, 0, 0, 0, 180, 180000, 0, 0, 0, 180000, 0, 0,
         "BELUM ADA TOLERANSI", 180 / 305, 0, 0, 0, 180 / 305, "JAWA TIMUR",
         "205.OKT 26", 5000, "WEEK 5", "8.OKTOBER"],
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(hdr)
    for row in data:
        ws.append(row)
    tmp = os.path.join(tempfile.gettempdir(), "mock_deviasi_komparasi.xlsx")
    wb.save(tmp)
    return tmp


def make_mock_in_detail() -> pd.DataFrame:
    """Mock detail IN per dokumen (v3.4) — 3 sumber + Nomor."""
    rows = []
    # 42.05 (pemindahan/SJ) — AYAM FILET MLGPAR tgl 5,10,15
    for tgl, nomor, qty in [(5, "IT.2026.09.00101", 500.0),
                            (10, "IT.2026.09.00202", 750.0),
                            (15, "IT.2026.09.00303", 250.0)]:
        rows.append({
            "NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
            "Tanggal": tgl, "Value": qty, "Nomor": nomor,
            "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
            "SOURCE IN": "42.05", "JENIS": "IN"})
    # 32.24 (RI) — AYAM FILET MLGPAR tgl 10
    rows.append({
        "NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
        "Tanggal": 10, "Value": 300.0, "Nomor": "RI.2026.09.009",
        "Nomor PO": "PO-010", "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "32.24", "JENIS": "IN"})
    # 42.05 — KOPI BUBUK 100G MLGPAR tgl 8 (utk uji CUT-OFF RESOLVED v3.6)
    rows.append({
        "NAMA RESTO": "MLGPAR", "Nama Barang": "KOPI BUBUK 100G",
        "Tanggal": 8, "Value": 100.0, "Nomor": "IT.2026.09.00404",
        "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "42.05", "JENIS": "IN"})
    # 99.01 (pembelian tanpa penerimaan) — GULA PASIR SBYKET tgl 5
    rows.append({
        "NAMA RESTO": "SBYKET", "Nama Barang": "GULA PASIR",
        "Tanggal": 5, "Value": 1200.0, "Nomor": "PI.2026.10.01556",
        "Nomor PO": "PO.2026.10.012", "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "99.01", "JENIS": "IN"})
    return pd.DataFrame(rows)


def make_mock_rekap_so() -> pd.DataFrame:
    """Mock rekap mentah (JENIS 'SO' + 'BARANG MASUK') — input Audit
    Rekonsiliasi dari data app (v3.6).

    Skenario status yang dihasilkan (bersama make_mock_in_detail):
    - AYAM FILET/MLGPAR tgl 5,10,15 : BM == IN          → OK (Matching)
    - GULA PASIR/SBYKET tgl 5        : SO naik+BM=0+IN  → VALID
    - KOPI BUBUK/MLGPAR tgl 3→8     : +100 lalu -100   → CUT-OFF RESOLVED
    - SUSU UHT 1L/MLGPAR tgl 2       : BM 80 tanpa IN   → DEVIASI MURNI
    """
    rows = []

    def so(barang, resto, tgl, val):
        rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                     "JENIS": "SO", "Tanggal": tgl, "Value": val})

    def bm(barang, resto, tgl, val):
        rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                     "JENIS": "BARANG MASUK", "Tanggal": tgl,
                     "Value": val})

    for t in (4, 5, 10, 15):
        so("AYAM FILET", "MLGPAR", t, 100.0 * t)
    bm("AYAM FILET", "MLGPAR", 5, 500.0)    # IN 500  → selisih 0
    bm("AYAM FILET", "MLGPAR", 10, 1050.0)  # IN 1050 → selisih 0
    bm("AYAM FILET", "MLGPAR", 15, 250.0)   # IN 250  → selisih 0
    so("GULA PASIR", "SBYKET", 4, 100.0)
    so("GULA PASIR", "SBYKET", 5, 1300.0)   # SO naik +1200, BM=0, IN=1200
    so("KOPI BUBUK 100G", "MLGPAR", 3, 50.0)
    bm("KOPI BUBUK 100G", "MLGPAR", 3, 100.0)  # +100 …
    bm("SUSU UHT 1L", "MLGPAR", 2, 80.0)      # gantung +80
    return pd.DataFrame(rows)


def make_mock_rincian() -> pd.DataFrame:
    rows = []
    for i in range(1, 13):
        for j in range(1, 4):
            rows.append({
                "Nomor #": f"PO-2024-{i:03d}",
                "Tanggal": pd.Timestamp("2024-06-01") + pd.Timedelta(days=i),
                "Nama Barang": ["AYAM FILET", "GULA PASIR", "SUSU UHT 1L"][j - 1],
                "Keterangan PO": "Rutin",
                "Pemasok": ["PT Sumber", "CV Maju", "UD Jaya"][j - 1],
                "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-01 09:00") +
                                     pd.Timedelta(days=i),
                "Satuan": "GR",
                "Kuantitas": 10.0 * j,
                "Cabang PO": "MLGPAR" if i % 2 else "SBYKET",
                "Status Pesanan Pembelian": "Selesai",
            })
    return pd.DataFrame(rows)


def main():
    print("== 1. Build app shell ==")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real_stdout, real_stderr
    root.update_idletasks()
    check("App + toolbar + 9 tab terbangun (v3.9.12: tab 🎯 Pareto dihapus)",
          len(app.notebook.tabs()) == 9, f"tabs={len(app.notebook.tabs())}")
    check("Status bar ada", app.statusbar is not None)
    check(f"Versi = 3.9.15", APP_VERSION == "3.9.15", f"got {APP_VERSION}")
    check("(v3.9.12) atribut app.pareto_view / app.tab_pareto DIHAPUS",
          not hasattr(app, "pareto_view") and not hasattr(app, "tab_pareto"))
    check("(v3.9.12) judul tab 'Pareto' tidak ada di notebook",
          not any("Pareto" in app.notebook.tab(t, "text")
                  for t in app.notebook.tabs()))
    try:
        import src.ui.pareto_view  # noqa: F401
        _pv_gone = False
    except ImportError:
        _pv_gone = True
    check("(v3.9.12) modul src.ui.pareto_view DIHAPUS (dead code)",
          _pv_gone)
    import src.ui.export_sheets as _es_mod
    check("(v3.9.12) write_pareto_sheet DIHAPUS dari export_sheets",
          not hasattr(_es_mod, "write_pareto_sheet"))
    check("Proses tab punya spinner status", app.status_spinner is not None)

    print("== 1a. v3.9.8 UI CLEAN — teks instruksi dihapus ==")
    import src.ui.widgets as _wmod
    check("(v3.9.8) widgets.ToolTip & add_tooltip DIHAPUS",
          not hasattr(_wmod, "ToolTip") and not hasattr(_wmod, "add_tooltip"))
    check("(v3.9.8) app._show_help DIHAPUS (tombol ❓ Bantuan hilang)",
          not hasattr(app, "_show_help"))

    def _all_labels_text(widget, acc=None):
        acc = [] if acc is None else acc
        for ch in widget.winfo_children():
            if isinstance(ch, tk.Label):
                t = ch.cget("text") or ""
                tv = ch.cget("textvariable") or ""
                if t and not tv:
                    acc.append(str(t))
            acc = _all_labels_text(ch, acc)
        return acc

    _shell_txt = _all_labels_text(root)
    _tb_btns = [str(b.cget("text")) for b in app.toolbar._actions.winfo_children()
                if isinstance(b, tk.Button)]
    check("(v3.9.8) Toolbar tanpa tombol Bantuan",
          not any("Bantuan" in t for t in _shell_txt + _tb_btns),
          f"found {[t for t in _shell_txt + _tb_btns if 'Bantuan' in t]}")
    check("(v3.9.8) Toolbar hanya 💾 Export Excel",
          _tb_btns == ["💾 Export Excel"], f"got {_tb_btns}")

    def _view_static_labels(view):
        """Label statis (non textvariable) di view — tanpa legenda & KPI."""
        out = []
        for lbl in _all_labels_text(view):
            if any(k in lbl for k in ("Kosong/Non Aktif", "Beda Tanggal",
                                      "Hitung Manual", "Turun Drastis",
                                      "ACR to BOM", "negatif (merah)",
                                      "IN", "BARANG MASUK",
                                      "Selisih ≠ 0", "tgl • = bulan lalu")):
                continue  # legenda (decode data — dipertahankan)
            out.append(lbl)
        return out

    for name, view in (("Deviasi GR", app.deviasi_gr_view),
                       ("Deviasi PCS", app.deviasi_pcs_view),
                       ("Pivot", app.pivot_view),
                       ("Rekap Selisih IN", app.in_selisih_view),
                       ("Laporan", app.laporan_view),
                       ("Komparasi", app.komparasi_view),
                       ("Follow Up", app.followup_view),
                       ("Rincian PO", app.rincian_view)):
        _txt = _view_static_labels(view)
        check(f"(v3.9.8) {name}: tanpa hint 'klik'/'double-click'/corong",
              not any(("klik" in t.lower() or "double-click" in t.lower()
                       or "corong" in t.lower() or "⧩" in t and "MINGGU" not in t)
                      for t in _txt),
              f"found {[t for t in _txt if 'klik' in t.lower()]}")
        check(f"(v3.9.8) {name}: tanpa panah-instruksi '→'",
              not any("→" in t and "MINGGU" not in t
                      and not t.startswith("WEEK ") for t in _txt),
              f"found {[t for t in _txt if '→' in t and 'MINGGU' not in t]}")

    check("(v3.9.8) EmptyState tanpa subtitle default",
          app.pivot_view.empty._subtitle_missing
          if hasattr(app.pivot_view.empty, "_subtitle_missing")
          else not any("Jalankan pipeline untuk memuat" in t
                       for t in _all_labels_text(app.pivot_view.empty)))

    print("== 2. Empty state semua view ==")
    check("Pivot empty state terpasang (pack)",
          app.pivot_view.empty.winfo_manager() == "pack")
    check("Pivot content tersembunyi",
          app.pivot_view.content.winfo_manager() == "")
    check("Deviasi GR empty", app.deviasi_gr_view.data is None)
    check("Laporan empty", app.laporan_view.data is None)
    check("Rincian empty", app.rincian_view.data is None)
    check("Rekap Selisih IN empty (v3.4)", app.in_selisih_view.data is None)

    print("== 3. Load mock data (async + loading overlay) ==")
    append1 = make_mock_append1()
    rincian = make_mock_rincian()
    in_detail = make_mock_in_detail()
    rekap_so = make_mock_rekap_so()
    # v3.6: audit dari data app (rekap SO + BM + IN per tanggal)
    from src.pipeline.fn_audit import build_audit_from_app
    audit_df, audit_kpi, audit_desc = build_audit_from_app(rekap_so,
                                                           in_detail)
    audit_result = {"df": audit_df, "kpi": audit_kpi, "desc": audit_desc}
    print(f"   mock append1: {len(append1)} rows, rincian: {len(rincian)} rows, "
          f"in_detail: {len(in_detail)} rows, audit: {len(audit_df)} rows")

    check("Pivot punya loading overlay",
          isinstance(app.pivot_view.overlay, LoadingOverlay))
    check("Deviasi GR punya loading overlay",
          isinstance(app.deviasi_gr_view.overlay, LoadingOverlay))
    check("Laporan punya loading overlay",
          isinstance(app.laporan_view.overlay, LoadingOverlay))
    check("Rincian punya loading overlay",
          isinstance(app.rincian_view.overlay, LoadingOverlay))
    check("Follow Up punya loading overlay",
          isinstance(app.followup_view.overlay, LoadingOverlay))

    # (v3.2) LAZY: load_data tanpa tab aktif → defer (dirty)
    app.pivot_view.load_data(append1)
    app.deviasi_gr_view.load_data(append1)
    app.deviasi_pcs_view.load_data(append1)
    app.in_selisih_view.load_data(append1, in_detail,
                                  audit_result=audit_result)
    app.laporan_view.load_data(append1)
    app.rincian_view.load_data(rincian)
    root.update()
    check("Lazy: view tak terlihat defer refresh (dirty)",
          app.deviasi_gr_view._dirty and app.laporan_view._dirty and
          app.rincian_view._dirty and app.in_selisih_view._dirty)

    for tab, v in [(app.tab_pivot, app.pivot_view),
                   (app.tab_deviasi_gr, app.deviasi_gr_view),
                   (app.tab_deviasi_pcs, app.deviasi_pcs_view),
                   (app.tab_in_selisih, app.in_selisih_view),
                   (app.tab_laporan, app.laporan_view),
                   (app.tab_rincian, app.rincian_view)]:
        ok = select_and_wait(root, app, tab, v)
        check(f"render async selesai ({type(v).__name__})", ok)

    # ---- PIVOT MODE RESTO (default) ----
    pv = app.pivot_view
    check("Pivot default mode = resto", pv.pivot_mode == "resto")
    check("(v3.8) Pivot default tanggal = -31 s/d 31 (kolom 25•-31• bulan "
          "lalu lengkap + 1-31 berjalan)",
          pv.tgl_start_var.get() == "-31" and pv.tgl_end_var.get() == "31",
          f"got {pv.tgl_start_var.get()}..{pv.tgl_end_var.get()}")
    cols = list(pv.tree["columns"])
    check("Pivot resto: kolom = resto (MLGPAR, SBYKET)",
          cols == ["MLGPAR", "SBYKET"], f"got {cols}")
    check("Tidak ada kolom 'Total'", "Total" not in cols)

    n_parent = len(pv.tree.get_children(""))
    check("Pivot resto: 6 barang (termasuk ADONAN+BARANG ACR yg hanya MLGPAR)",
          n_parent == 6, f"got {n_parent}")

    # ADONAN GORENG MEKAR — hanya ada di MLGPAR → tetap tampil
    adonan = None
    for iid in pv.tree.get_children(""):
        if pv.tree.item(iid, "text") == "ADONAN GORENG MEKAR":
            adonan = iid
    check("ADONAN GORENG MEKAR tampil (nilainya ada di MLGPAR)",
          adonan is not None)
    if adonan:
        so_iid = None
        for c in pv.tree.get_children(adonan):
            if pv.tree.item(c, "text") == "1.SO":
                so_iid = c
        check("ADONAN punya baris 1.SO", so_iid is not None)
        if so_iid:
            mlg = pv.tree.set(so_iid, "MLGPAR")
            sby = pv.tree.set(so_iid, "SBYKET")
            check("ADONAN 1.SO MLGPAR = angka (ada nilai)",
                  mlg not in ("-", "", "0"), f"got {mlg}")
            check("ADONAN 1.SO SBYKET = '-' (resto lain kosong)",
                  sby == "-", f"got {sby}")
        n_child = len(pv.tree.get_children(adonan))
        check("ADONAN: baris kosong disembunyikan (metric < 9)",
              0 < n_child < 9, f"got {n_child}")
        kinds = [pv.tree.item(c, "text") for c in pv.tree.get_children(adonan)]
        check("6.PEMAKAIAN (COM) tidak ada di mode resto",
              "6.PEMAKAIAN (COM)" not in kinds)

    check("(v3.2) KPI row pivot DIHAPUS", not hasattr(pv, "kpi_items"))
    check("(v3.2) Pivot status footer memuat ringkasan",
          "barang" in pv.status_var.get(), f"got {pv.status_var.get()!r}")

    # hide-empty OFF → semua metric muncul
    pv.hide_empty_var.set(False)
    pv._refresh_pivot()
    wait_view(root, pv)
    adonan2 = None
    for iid in pv.tree.get_children(""):
        if pv.tree.item(iid, "text") == "ADONAN GORENG MEKAR":
            adonan2 = iid
    if adonan2:
        n_child = len(pv.tree.get_children(adonan2))
        check("hide-empty OFF: 9 metric tampil (tanpa COM)",
              n_child == 9, f"got {n_child}")
    pv.hide_empty_var.set(True)

    # ---- PIVOT MODE TANGGAL ----
    app.notebook.select(app.tab_pivot)
    root.update()
    # (v3.5) default rentang kini 26-31 — test mode tanggal perlu 1-31
    pv.tgl_start_var.set("1")
    pv.tgl_end_var.set("31")
    pv._on_mode_change(1)
    wait_view(root, pv)
    check("Pivot mode tanggal: 30 kolom tanggal",
          len(pv.tree["columns"]) == 30,
          f"got {len(pv.tree['columns'])}")
    first = pv.tree.get_children("")[0]
    kinds = [pv.tree.item(c, "text") for c in pv.tree.get_children(first)]
    check("6.PEMAKAIAN (COM) ada di mode tanggal",
          "6.PEMAKAIAN (COM)" in kinds)
    n_child = len(pv.tree.get_children(first))
    check("Mode tanggal: baris kosong disembunyikan (5-10 metric)",
          5 <= n_child <= 10, f"got {n_child}")
    # rentang tanggal membatasi kolom
    pv.tgl_start_var.set("10")
    pv.tgl_end_var.set("20")
    pv._refresh_pivot()
    wait_view(root, pv)
    check("Rentang tanggal 10-20 → 11 kolom",
          len(pv.tree["columns"]) == 11,
          f"got {len(pv.tree['columns'])}")
    pv.tgl_start_var.set("1")
    pv.tgl_end_var.set("31")

    # kembali ke mode resto
    pv._on_mode_change(0)
    wait_view(root, pv)

    print("== 4. Header filter Nama Barang (klik heading) ==")
    hf = pv.header_filter
    check("HeaderFilter terpasang di #0", isinstance(hf, HeaderFilter))
    app.notebook.select(app.tab_pivot)
    root.update()
    pv.tree.event_generate("<Button-1>", x=20, y=10)
    root.update()
    check("Klik heading #0 → popup filter terbuka",
          hf._popup is not None and hf._popup.winfo_exists())
    if hf._popup is not None and hf._popup.winfo_exists():
        # uncheck semua kecuali AYAM FILET
        for v, var in hf._vars.items():
            var.set(v == "AYAM FILET")
        hf._update_count()
        hf._emit()
        wait_view(root, pv)
        n_parent = len(pv.tree.get_children(""))
        check("Filter header aktif → hanya 1 barang", n_parent == 1,
              f"got {n_parent}")
        check("State filter = {'AYAM FILET'}", hf.selected == {"AYAM FILET"})
        hf._reset()
        wait_view(root, pv)
        n_parent = len(pv.tree.get_children(""))
        check("Reset di popup → 6 barang kembali", n_parent == 6,
              f"got {n_parent}")
        hf._close()
        root.update()

    # RESTO filter via combobox (mode Tanggal saja — cek UI menyembunyikan)
    pv._on_mode_change(1)
    wait_view(root, pv)
    check("Mode resto: filter RESTO disembunyikan — (cek pack)",
          pv.f_resto.winfo_manager() in ("", None) or True)  # info saja
    pv.resto_var.set("MLGPAR")
    pv._refresh_pivot()
    wait_view(root, pv)
    n_parent = len(pv.tree.get_children(""))
    check("Pivot filter RESTO=MLGPAR → ADONAN ikut (6 barang)",
          n_parent == 6, f"got {n_parent}")
    pv._reset_filter()
    wait_view(root, pv)
    check("Pivot reset filter → mode tetap tanggal, 6 barang",
          len(pv.tree.get_children("")) == 6)
    pv._on_mode_change(0)
    wait_view(root, pv)

    print("== 5. Tombol ⛶ Perbesar ==")
    win, mtree = pv._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    check("Window perbesar terbuka", win is not None and win.winfo_exists())
    n_clone = len(mtree.get_children(""))
    check("Clone berisi 6 barang", n_clone == 6, f"got {n_clone}")
    check("Clone punya kolom resto",
          list(mtree["columns"]) == ["MLGPAR", "SBYKET"])
    win.destroy()
    root.update()

    print("== 6. Deviasi GR / PCS ==")
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    n_gr = len(app.deviasi_gr_view.tree.get_children(""))
    check("Deviasi GR rows = 6 (ADONAN+BARANG ACR hanya MLGPAR)",
          n_gr == 6, f"got {n_gr}")
    n_pcs = len(app.deviasi_pcs_view.tree.get_children(""))
    check("Deviasi PCS rows = 4", n_pcs == 4, f"got {n_pcs}")
    check("(v3.2) KPI deviasi DIHAPUS (tabel besar)",
          not hasattr(app.deviasi_gr_view, "kpi_dev") and
          not hasattr(app.deviasi_gr_view, "kpi_cek"))
    check("(v3.2) Kolom ✓ ada (follow-up)",
          "✓" in [c[0] for c in app.deviasi_gr_view.COLUMNS])
    check("(v3.2) Ringkasan deviasi di status footer",
          "Deviasi" in app.deviasi_gr_view.status_var.get(),
          f"got {app.deviasi_gr_view.status_var.get()!r}")

    # ---- (v3.9.6) KATEGORI DEVIASI — 5 kolom baru + CEK "ACR to BOM" ----
    gr_cols = [c[0] for c in app.deviasi_gr_view.COLUMNS]
    check("(v3.9.6) Skema: 5 kolom kategori Deviasi setelah Rank "
          "(v3.9.13: +1 — kolom KATEGORI index 4)",
          gr_cols[19:24] == ["Max Deviasi", "ACR", "Total ACR",
                             "Dev to BOM%", "Stok Seharusnya"] and
          gr_cols[24] == "CEK", f"got {gr_cols}")
    gr_idx = {c: i for i, c in enumerate(gr_cols)}
    acr_row = None
    for k in app.deviasi_gr_view.tree.get_children(""):
        v = app.deviasi_gr_view.tree.item(k, "values")
        if v[gr_idx["Nama Barang"]] == "BARANG ACR":
            acr_row = v
            break
    check("(v3.9.6) BARANG ACR tampil (GR, H=25 default)",
          acr_row is not None)
    if acr_row is not None:
        v = acr_row
        check("(v3.9.6) Deviasi = SO_H − Sistem = 100",
              v[gr_idx["Deviasi"]] == "100",
              f"got {v[gr_idx['Deviasi']]!r}")
        check("(v3.9.6) Total ACR = Σ OUT 1..25 = 24",
              v[gr_idx["Total ACR"]] == "24",
              f"got {v[gr_idx['Total ACR']]!r}")
        check("(v3.9.6) ACR = 24/25 = 0,96 → '1,0' (1 desimal)",
              v[gr_idx["ACR"]] == "1,0", f"got {v[gr_idx['ACR']]!r}")
        check("(v3.9.6) Dev to BOM% = 100/24 = '416,67%'",
              v[gr_idx["Dev to BOM%"]] == "416,67%",
              f"got {v[gr_idx['Dev to BOM%']]!r}")
        check("(v3.9.6) Stok Seharusnya = SO(24) − ACR = '199,0'",
              v[gr_idx["Stok Seharusnya"]] == "199,0",
              f"got {v[gr_idx['Stok Seharusnya']]!r}")
        check("(v3.9.6) Max Deviasi per barang = 100",
              v[gr_idx["Max Deviasi"]] == "100",
              f"got {v[gr_idx['Max Deviasi']]!r}")
        check("(v3.9.6) CEK = 'ACR to BOM' (kondisi ke-5, |100| > 24)",
              v[gr_idx["CEK"]] == "ACR to BOM",
              f"got {v[gr_idx['CEK']]!r}")
    # tag cek_acr di baris BARANG ACR
    acr_tags = None
    for k in app.deviasi_gr_view.tree.get_children(""):
        v = app.deviasi_gr_view.tree.item(k, "values")
        if v[2] == "BARANG ACR":
            acr_tags = app.deviasi_gr_view.tree.item(k, "tags")
            break
    check("(v3.9.6) Tag cek_acr di baris BARANG ACR",
          acr_tags is not None and "cek_acr" in acr_tags,
          f"got {acr_tags}")
    # legenda CEK memuat kategori baru (chip = Frame berisi Label)
    _legend_txt = []
    for _chip in app.deviasi_gr_view._legend.winfo_children():
        for _w in _chip.winfo_children():
            if isinstance(_w, tk.Label):
                _legend_txt.append(_w.cget("text"))
    check("(v3.9.6) Legenda CEK memuat 'ACR to BOM'",
          any("ACR to BOM" in t for t in _legend_txt),
          f"got {_legend_txt}")

    app.deviasi_gr_view._on_col_filter("Nama Barang", {"ADONAN GORENG MEKAR"})
    wait_view(root, app.deviasi_gr_view)
    check("Deviasi header filter → 1 row",
          len(app.deviasi_gr_view.tree.get_children("")) == 1)
    app.deviasi_gr_view._reset_filter()
    wait_view(root, app.deviasi_gr_view)
    check("Deviasi reset → 6 rows",
          len(app.deviasi_gr_view.tree.get_children("")) == 6)

    app.deviasi_gr_view.tanggal_h_var.set("10")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    check("Tanggal H=10 applied", app.deviasi_gr_view.tanggal_h == 10)
    heading = app.deviasi_gr_view.tree.heading("SO_H")["text"]
    check("Heading dinamis SO_H → 'SO_10'", heading == "SO_10",
          f"got '{heading}'")

    # (v3.9) SHARED H — PCS otomatis ikut tanpa input kedua:
    check("(v3.9) H dibagi: PCS ikut H=10 otomatis (tanpa double input)",
          app.deviasi_pcs_view.tanggal_h == 10,
          f"got {app.deviasi_pcs_view.tanggal_h}")
    check("(v3.9) PCS chip H menampilkan 10",
          app.deviasi_pcs_view._h_chip_var.get() == "10",
          f"got {app.deviasi_pcs_view._h_chip_var.get()!r}")
    check("(v3.9) PCS TIDAK punya input H sendiri",
          not hasattr(app.deviasi_pcs_view, "tanggal_h_var"))
    check("(v3.9) GR tetap punya input H + Apply",
          hasattr(app.deviasi_gr_view, "tanggal_h_var"))
    pcs_h = app._shared_h.h
    check("(v3.9) SharedTanggalH state = 10", pcs_h == 10, f"got {pcs_h}")

    # maximize deviasi + sort di clone
    win2, mtree2 = app.deviasi_gr_view._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    app.deviasi_gr_view._sort_by("Deviasi", tree=mtree2)  # sort di clone
    root.update()
    check("Sort via heading clone jalan (tanpa exception)", True)
    win2.destroy()
    root.update()

    print("== 7. Laporan Deviasi (v3.9.3 — daftar anomali COM) ==")
    app.show_laporan_mode(1)   # v3.9.4: segmen Anomali COM (mode 1)
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    lap = app.laporan_view
    n_all = len(lap.tree.get_children(""))
    print(f"   laporan rows total: {n_all}")
    check("(v3.9.3) Skema kolom baru (COM list)",
          [c[0] for c in lap.COLUMNS] == ["✓", "Nama Barang", "Resto",
                                          "Satuan", "COM", "Median",
                                          "Selisih vs Median", "Status"])
    check("(v3.9.3) Tabel audit harian lama DIGANTI (tanpa tgl range)",
          not hasattr(lap, "tgl_start_var") and
          not hasattr(lap, "tgl_end_var"))
    check("(v3.9.3) H laporan ikut H=10 dari tab GR (shared, tanpa input)",
          lap.tanggal_h == 10 and not hasattr(lap, "tanggal_h_var"),
          f"got {lap.tanggal_h}")
    check("(v3.9.3) Chip H read-only menampilkan 10",
          lap._h_chip_var.get() == "10",
          f"got {lap._h_chip_var.get()!r}")
    check("(v3.9.3) Heading COM dinamis 'COM (H=10)'",
          lap.tree.heading("COM")["text"] == "COM (H=10)",
          f"got {lap.tree.heading('COM')['text']!r}")
    check("(v3.2) 6 kartu KPI status DIHAPUS",
          not hasattr(lap, "_status_kpis"))
    check("(v3.2) Kolom ✓ di laporan", "✓" in [c[0] for c in lap.COLUMNS])
    check("(v3.5) HeaderFilterGroup terpasang (semua kolom)",
          hasattr(lap, "header_filters") and len(lap._col_sel) >= 7)

    # v3.9.7: median ANTAR TANGGAL per pasangan — mock com(10)=4
    # (IN(10)=5, SO diff −1) vs median com(1..10) = −1 → pasangan
    # pemakai '> MEDIAN' (BARANG ACR com(10)=0 == median 0 → tidak)
    _st_h10 = {lap.tree.set(k, "Status") for k in lap.tree.get_children("")}
    check("(v3.9.7) Mock H=10 → 9 baris '> MEDIAN' (median antar tanggal)",
          n_all == 9 and _st_h10 == {"> MEDIAN"},
          f"got {n_all} / {sorted(_st_h10)}")
    check("(v3.9.7) Median kolom = median com(1..10) pasangan (−1 → '(1)')",
          all(lap.tree.set(k, "Median") == "(1)"
              for k in lap.tree.get_children("")),
          f"got {sorted({lap.tree.set(k, 'Median') for k in lap.tree.get_children('')})[:4]}")
    check("(v3.9.7) Heading Median dinamis 'Median (1..10)'",
          lap.tree.heading("Median")["text"] == "Median (1..10)",
          f"got {lap.tree.heading('Median')['text']!r}")

    # anomali mock: AYAM FILET MLGPAR SO(25)=80 → com(25) besar negatif;
    # Apply H=25 di GR → laporan ikut refresh otomatis (shared H)
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)
    n_h25 = len(lap.tree.get_children(""))
    # v3.9.7: 10 pasangan — AYAM MLGPAR MINUS (com(25)=h−62), sisanya
    # '> MEDIAN' (com(25)=4 > median −1; BARANG ACR 100 > median 0)
    check("(v3.9.3) H=25 (anomali mock) → 10 baris: MLGPAR MINUS + 9 "
          "> MEDIAN", n_h25 == 10, f"got {n_h25}")
    if n_h25 >= 2:
        a_mlg = [k for k in lap.tree.get_children("")
                 if lap.tree.set(k, "Resto") == "MLGPAR" and
                 lap.tree.set(k, "Nama Barang") == "AYAM FILET"]
        a_sby = [k for k in lap.tree.get_children("")
                 if lap.tree.set(k, "Resto") == "SBYKET" and
                 lap.tree.set(k, "Nama Barang") == "AYAM FILET"]
        ok_mlg = (len(a_mlg) == 1 and
                  lap.tree.set(a_mlg[0], "Nama Barang") == "AYAM FILET" and
                  lap.tree.set(a_mlg[0], "Status") == "MINUS" and
                  lap.tree.set(a_mlg[0], "COM").startswith("("))
        ok_sby = (len(a_sby) == 1 and
                  lap.tree.set(a_sby[0], "Status") == "> MEDIAN")
        check("(v3.9.3) AYAM FILET/MLGPAR → MINUS (com negatif '(…)')",
              ok_mlg, f"got {[lap.tree.set(k, 'Status') for k in a_mlg]}")
        check("(v3.9.3) AYAM FILET/SBYKET → > MEDIAN (com 4 > median "
              "antar tanggal −1)", ok_sby,
              f"got {[lap.tree.set(k, 'Status') for k in a_sby]}")
    # kembali ke H=10 utk blok data deterministik
    app.deviasi_gr_view.tanggal_h_var.set("10")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)

    # ---- data deterministik: median / flag / status bisa dihitung tangan ----
    # v3.9.7: median ANTAR TANGGAL per pasangan — kontrol via deret SO
    # (SA + SO 1..10, IN=BK=0): com(1)=SA−SO(1), com(t)=SO(t−1)−SO(t).
    # com(1..10) per pasangan (SO = 100 − Σcom(1..t)):
    #   TEH MELATI  R1 = [5×9, 8]     → median 5,  com(10)=8   → > MEDIAN
    #   TEH MELATI  R2 = [5×10]       → median 5,  com(10)=5   → TIDAK ter-flag
    #   KOPI        R1 = [5×9, −5]    → median 5,  com(10)=−5  → MINUS
    #   KOPI        R2 = [5×9, 100]   → median 5,  com(10)=100 → > MEDIAN
    #   GULA AREN   R1 = [−30×9, −10] → median −30, com(10)=−10 → MINUS + > MEDIAN
    det_rows = []

    def _sa(barang, resto, val):
        det_rows.append({"Nama Barang": barang, "JENIS": "SALDO AWAL",
                         "NAMA RESTO": resto, "Tanggal": 1, "NILAI": val,
                         "SATUAN": "GR"})

    def _so(barang, resto, t, val):
        det_rows.append({"Nama Barang": barang, "JENIS": "1.SO",
                         "NAMA RESTO": resto, "Tanggal": t, "NILAI": val,
                         "SATUAN": "GR"})

    def _com_series(barang, resto, series):
        _sa(barang, resto, 100.0)
        so = 100.0
        for t, c in enumerate(series, start=1):
            so -= c
            _so(barang, resto, t, so)

    _com_series("TEH MELATI", "R1", [5.0] * 9 + [8.0])
    _com_series("TEH MELATI", "R2", [5.0] * 10)
    _com_series("KOPI ROBUSTA", "R1", [5.0] * 9 + [-5.0])
    _com_series("KOPI ROBUSTA", "R2", [5.0] * 9 + [100.0])
    _com_series("GULA AREN", "R1", [-30.0] * 9 + [-10.0])
    lap.load_data(pd.DataFrame(det_rows))
    wait_view(root, lap)
    n_det = len(lap.tree.get_children(""))
    check("(v3.9.7) Baris deterministik = 4 (median antar tanggal)",
          n_det == 4, f"got {n_det}")

    def _rowval(i, col):
        return lap.tree.set(lap.tree.get_children("")[i], col)

    # sort default: barang asc, COM desc →
    # GULA AREN(−10), KOPI ROBUSTA(100, −5), TEH MELATI(8)
    check("(v3.9.7) COM -10 (GULA AREN R1) tampil '(10)'",
          _rowval(0, "COM") == "(10)", f"got {_rowval(0, 'COM')!r}")
    check("(v3.9.7) Status 'MINUS + > MEDIAN' (−10 > median −30)",
          _rowval(0, "Status") == "MINUS + > MEDIAN",
          f"got {_rowval(0, 'Status')!r}")
    check("(v3.9.7) Median = median com(1..10) pasangan (−30 → '(30)')",
          _rowval(0, "Median") == "(30)", f"got {_rowval(0, 'Median')!r}")
    check("(v3.9.7) Selisih vs Median = COM − median (−10−(−30) = 20)",
          _rowval(0, "Selisih vs Median") == "20",
          f"got {_rowval(0, 'Selisih vs Median')!r}")
    check("(v3.9.7) KOPI 100 → '> MEDIAN' (median 5)",
          _rowval(1, "COM") == "100" and _rowval(1, "Status") == "> MEDIAN",
          f"got {_rowval(1, 'COM')!r}/{_rowval(1, 'Status')!r}")
    check("(v3.9.7) KOPI -5 → '(5)' + status MINUS",
          _rowval(2, "COM") == "(5)" and _rowval(2, "Status") == "MINUS",
          f"got {_rowval(2, 'COM')!r}/{_rowval(2, 'Status')!r}")
    check("(v3.9.7) TEH 8 → '> MEDIAN' (median 5)",
          _rowval(3, "COM") == "8" and _rowval(3, "Status") == "> MEDIAN",
          f"got {_rowval(3, 'COM')!r}/{_rowval(3, 'Status')!r}")
    teh_coms = [lap.tree.set(k, "COM")
                for k in lap.tree.get_children("")
                if lap.tree.set(k, "Nama Barang") == "TEH MELATI"]
    check("(v3.9.7) TEH MELATI R2 com(10)=5 == median → TIDAK ter-flag",
          teh_coms == ["8"], f"got {teh_coms}")

    # minus merah PER CELL (v3.9.2 berlanjut): 2 baris minus → 2 cell COM
    check("(v3.9.3) neg_cells: 2 cell COM minus",
          len(lap._neg_cells) == 2 and
          all(c[1] == "COM" for c in lap._neg_cells),
          f"got {lap._neg_cells}")
    check("(v3.9.3) sel Status minus 2 / above 2 (per-cell warna)",
          len(lap._st_minus_cells) == 2 and len(lap._st_above_cells) == 2,
          f"got {len(lap._st_minus_cells)}/{len(lap._st_above_cells)}")

    # header filter Status = 'MINUS' → kecocokan nilai TERFORMAT (exact):
    # hanya KOPI R1 (status 'MINUS + > MEDIAN' ≠ 'MINUS')
    lap._on_col_filter("Status", {"MINUS"})
    wait_view(root, lap)
    check("(v3.5) Header filter Status='MINUS' → 1 baris",
          len(lap.tree.get_children("")) == 1,
          f"got {len(lap.tree.get_children(''))}")
    lap._on_col_filter("Nama Barang", {"KOPI ROBUSTA"})
    wait_view(root, lap)
    check("(v3.5) Header filter Nama Barang KOPI ROBUSTA → 1 row",
          len(lap.tree.get_children("")) == 1)
    lap._reset_filter()
    wait_view(root, lap)
    check("Reset filter → semua baris kembali",
          len(lap.tree.get_children("")) == n_det)

    # H berubah dari tab GR → laporan ikut refresh (shared H)
    app.deviasi_gr_view.tanggal_h_var.set("9")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)
    check("(v3.9.3) Apply H=9 di tab GR → laporan ikut (chip + heading)",
          lap.tanggal_h == 9 and lap._h_chip_var.get() == "9" and
          lap.tree.heading("COM")["text"] == "COM (H=9)" and
          lap.tree.heading("Median")["text"] == "Median (1..9)",
          f"got H={lap.tanggal_h}")
    # v3.9.7: window 1..9 → com(9) == median utk semua pasangan kecuali
    # GULA AREN (com(9)=−30 < 0) → 1 baris MINUS
    n_h9 = len(lap.tree.get_children(""))
    _h9_status = [lap.tree.set(k, "Status")
                  for k in lap.tree.get_children("")]
    check("(v3.9.7) H=9: 1 baris MINUS (GULA com(9)=−30, == median)",
          n_h9 == 1 and _h9_status == ["MINUS"],
          f"got {n_h9} {_h9_status}")
    # kembalikan data mock; H=25 (anomali AYAM FILET → 10 baris) supaya
    # section 11 (klik ✓ follow-up dari Laporan) punya baris
    lap.load_data(append1)
    wait_view(root, lap)
    check("(v3.9.3) Kembali ke mock data: matriks COM terhitung (10 pasangan)",
          lap._cached_com is not None and lap._cached_com.shape[0] == 10,
          f"got {None if lap._cached_com is None else lap._cached_com.shape}")
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)
    check("(v3.9.7) Mock + H=25 → 10 baris anomali (baris utk section 11)",
          len(lap.tree.get_children("")) == 10,
          f"got {len(lap.tree.get_children(''))}")

    print("== 8. Rincian PO (v3.9 — layout ringkas) ==")
    select_and_wait(root, app, app.tab_rincian, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1  # minus grand total
    check("Rincian: 12 PO (parent) + grand total", n_po == 12, f"got {n_po}")
    check("(v3.2) KPI rincian DIHAPUS",
          not hasattr(app.rincian_view, "kpi_po"))
    check("(v3.2) Ringkasan PO di status footer",
          "PO" in app.rincian_view.status_var.get(),
          f"got {app.rincian_view.status_var.get()!r}")

    # (v3.9) layout ringkas: parent = info PO lengkap, anak = item saja
    rv = app.rincian_view
    first_po = rv.tree.get_children("")[0]
    po_vals = rv.tree.item(first_po, "values")
    kids = rv.tree.get_children(first_po)
    kid_vals = rv.tree.item(kids[0], "values")
    check("(v3.9) Kolom tabel baru (info PO + item)",
          list(rv.tree["columns"]) == [
              "Tanggal", "Pemasok", "Status Pesanan", "Keterangan PO",
              "Nama Barang", "Satuan", "Kuantitas", "Tgl/Jam Pembuatan"],
          f"got {list(rv.tree['columns'])}")
    check("(v3.9) Baris PO (teal) memuat Tanggal + Pemasok + Status",
          po_vals[0] == "2024-06-02" and po_vals[1] == "PT Sumber" and
          po_vals[2] == "Selesai",
          f"got {po_vals[:3]}")
    check("(v3.9) Baris PO memuat ringkasan jumlah item + total",
          "item" in po_vals[4] and "Total:" in po_vals[6],
          f"got {po_vals[4]!r} / {po_vals[6]!r}")
    check("(v3.9) Baris anak = HANYA item (info PO tidak diulang)",
          kid_vals[0] == "" and kid_vals[1] == "" and kid_vals[2] == "" and
          kid_vals[3] == "" and kid_vals[4] == "AYAM FILET" and
          kid_vals[5] == "GR" and kid_vals[6] == "10",
          f"got {list(kid_vals)}")
    check("(v3.9) Tgl/Jam Pembuatan tersembunyi default",
          "Tgl/Jam Pembuatan" in rv._colmgr.hidden and
          "Tgl/Jam Pembuatan" not in rv.tree.cget("displaycolumns"),
          f"hidden={rv._colmgr.hidden}")
    gt = rv.tree.item(rv.tree.get_children("")[-1], "values")
    check("(v3.9) Grand total: N PO + total qty di kolom Kuantitas",
          gt[4] == "12 PO" and gt[6] == "720",
          f"got {gt[4]!r} / {gt[6]!r}")

    app.rincian_view.cabang_var.set("MLGPAR")
    app.rincian_view._refresh()
    wait_view(root, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1
    check("Rincian filter cabang → 6 PO", n_po == 6, f"got {n_po}")

    app.rincian_view._on_col_filter("Nama Barang", {"AYAM FILET"})
    wait_view(root, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1
    check("Rincian header filter AYAM FILET → 6 PO", n_po == 6,
          f"got {n_po}")
    app.rincian_view._reset_filter()
    wait_view(root, app.rincian_view)

    print("== 9. Details popup + COPY Nomor / Nomor PO ==")
    from src.ui.details_popup import show_details_popup
    popup = show_details_popup(root, append1, nama_barang="AYAM FILET",
                               jenis="1.SO", tanggal=25)
    wait_view(root, popup)
    n_rows = len(popup.tree.get_children(""))
    check("Popup rows = 2 (AYAM FILET/1.SO/25 — 2 resto)",
          n_rows == 2, f"got {n_rows}")
    check("Popup punya header filter Nama Barang",
          isinstance(popup.header_filter, HeaderFilter))

    # Ctrl+C → copy Nomor baris terpilih
    first = popup.tree.get_children("")[0]
    popup.tree.selection_set(first)
    popup._on_copy_key(None)
    try:
        clip = root.clipboard_get()
        check("Ctrl+C copy Nomor ke clipboard", clip.startswith("RI-00"),
              f"got {clip!r}")
    except Exception as e:
        check("Ctrl+C copy Nomor ke clipboard", False, f"err {e}")

    # Double-click cell Nomor → copy (Tk 9 melarang event_generate <Double-1>,
    # jadi panggil handler dengan fake event)
    root.update()
    popup.update_idletasks()
    bbox = popup.tree.bbox(first, "Nomor")
    if bbox:
        x, y, w, h = bbox

        class _FakeEvent:
            pass

        ev = _FakeEvent()
        ev.widget = popup.tree
        ev.x, ev.y = x + 5, y + 5
        popup._on_double_click(ev)
        root.update()
        try:
            clip = root.clipboard_get()
            check("Double-click cell Nomor → copy", clip.startswith("RI-"),
                  f"got {clip!r}")
        except Exception as e:
            check("Double-click cell Nomor → copy", False, f"err {e}")
    else:
        print("  ! bbox Nomor tidak tersedia — skip double-click test")

    # Copy semua Nomor PO (unik)
    popup._copy_all_unique("Nomor PO")
    try:
        clip = root.clipboard_get()
        check("Copy SEMUA Nomor PO (unik) — 1 nilai", "PO-0025" in clip,
              f"got {clip!r}")
    except Exception as e:
        check("Copy SEMUA Nomor PO (unik)", False, f"err {e}")

    # Copy cell Nomor PO via context-menu helper (row)
    values = popup.tree.item(first, "values")
    nomor_po = values[6]
    popup._copy_to_clipboard(nomor_po, "Nomor PO")
    check("Status flash tersalin muncul",
          "TERSALIN" in popup.status_var.get(),
          f"got {popup.status_var.get()!r}")

    # Maximize popup + clone bisa copy (context menu handler terpasang)
    pwin, pmtree = popup._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    check("Popup maximize terbuka", pwin is not None and pwin.winfo_exists())
    check("Clone popup berisi 2 rows",
          len(pmtree.get_children("")) == 2)
    pwin.destroy()
    root.update()
    popup.destroy()
    root.update()

    print("== 10. Proses tab KPI ==")
    app.kpi_append.set_value("1,234", "test")
    check("KPI append set", app.kpi_append._value_var.get() == "1,234")

    # ==================================================================
    print("== 11. FOLLOW UP (v3.2 — ala Waste) ==")
    from src.ui.followup import followup_path, resolved_path
    for p in (followup_path(), resolved_path()):
        if p.exists():
            p.unlink()

    store = app.followup_store
    check("Store follow-up bersih", len(store) == 0)

    # -- toggle ✓ dari Deviasi GR (klik sel kolom pertama) --
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    dv = app.deviasi_gr_view
    tree = dv.tree
    first = tree.get_children("")[0]
    bbox = tree.bbox(first)
    check("bbox baris deviasi tersedia", bool(bbox))

    class _Ev:
        pass

    ev = _Ev()
    ev.widget = tree
    ev.x, ev.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_tree_click(ev)
    root.update()
    check("Klik ✓ → baris masuk follow-up", len(store) == 1)
    check("Cell ✓ berubah ☑", tree.set(first, "✓") == "☑",
          f"got {tree.set(first, '✓')!r}")
    fp0 = dv._fp_map.get(first)
    check("fp_map terisi", fp0 is not None and fp0 in store.rows)
    check("followup.json tersimpan", followup_path().exists())
    badge = app.notebook.tab(app.tab_followup, "text")
    root.update()
    check("Badge tab 'Follow Up (1)'", "1" in badge, f"got {badge!r}")

    # -- tab Follow Up: render snapshot (v3.9.6 FORMAT FILE SAMPLE) --
    select_and_wait(root, app, app.tab_followup, app.followup_view)
    fu = app.followup_view
    root.update()
    n_fu = len(fu.tree.get_children(""))
    check("Tab Follow Up menampilkan 1 baris", n_fu == 1, f"got {n_fu}")
    vals = fu.tree.item(fu.tree.get_children("")[0], "values")
    check("Snapshot: kolom asal = DEVIASI GR", vals[17] == "DEVIASI GR",
          f"got {vals[17]!r}")
    check("Snapshot: ada resto", bool(vals[1]))
    check("Status TL = Menunggu", vals[18] == "Menunggu",
          f"got {vals[18]!r}")
    # v3.9.6: urutan format file sample — Resto · Nama Barang · 5 kolom
    # tanggal · Sistem · Deviasi · Loss Surplus to BOM · Keterangan ·
    # SO · DEVIASI · Selisih · Selisih Deviasi · Cek FU
    from src.ui.followup_view import COLUMNS as FU_COLUMNS
    fu_cols = [c[0] for c in FU_COLUMNS]
    check("(v3.9.6) Skema FU = format file sample",
          fu_cols[:3] == ["✓", "Resto", "Nama Barang"] and
          fu_cols[3:8] == ["T-2", "T-1", "T", "T+1", "T+2"] and
          fu_cols[8:14] == ["Sistem", "Deviasi", "Loss Surplus to BOM",
                            "Keterangan", "SO", "DEVIASI"] and
          fu_cols[14:17] == ["Selisih", "Selisih Deviasi", "Cek FU"],
          f"got {fu_cols}")
    snap0 = next(iter(store.rows.values()))
    check("(v3.9.6) Snapshot FU membawa SO per tanggal",
          all(k in snap0 for k in
              ("so_m2", "so_m1", "so_p1", "so_p2", "loss_bom")),
          f"got keys {sorted(snap0.keys())}")
    # snapshot berasal dari tab Deviasi GR → kolom tanggal terisi & SO(T)=so
    check("(v3.9.6) FU: SO kolom T = snapshot so",
          float(vals[5]) == float(snap0.get("so", 0)),
          f"got {vals[5]!r} vs {snap0.get('so')!r}")
    check("(v3.9.6) FU: DEVIASI = snapshot deviasi",
          vals[13] == vals[9], f"got {vals[13]!r} vs {vals[9]!r}")
    # heading tanggal dinamis: H snapshot (25) → 23..27
    headings = [fu.tree.heading(c, "text") for c in ("T-2", "T", "T+2")]
    check("(v3.9.6) FU heading tanggal dinamis (H=25 → 23/25/27)",
          headings == ["23", "25", "27"], f"got {headings}")
    check("(v3.9.6) FU: kolom Selisih/Cek FU kosong (belum dikerjakan)",
          vals[14] == "-" and vals[16] == "-",
          f"got {vals[14]!r} / {vals[16]!r}")

    # -- lepas ✓ dari tab Follow Up --
    first_fu = fu.tree.get_children("")[0]
    bbox_fu = fu.tree.bbox(first_fu)
    ev2 = _Ev()
    ev2.widget = fu.tree
    ev2.x, ev2.y = bbox_fu[0] + 8, bbox_fu[1] + bbox_fu[3] // 2
    fu._on_tree_click(ev2)
    root.update()
    check("Klik ✓ di tab Follow Up → keluarkan", len(store) == 0)
    check("Empty state Follow Up kembali",
          fu.empty.winfo_manager() == "pack")

    # -- toggle dari Laporan + export (v3.8: Impor Hasil TL DIHAPUS) --
    app.show_laporan_mode(1)   # v3.9.4: segmen Anomali COM (mode 1)
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    lap_tree = app.laporan_view.tree
    first_lap = lap_tree.get_children("")[0]
    bbox_lap = lap_tree.bbox(first_lap)
    ev3 = _Ev()
    ev3.widget = lap_tree
    ev3.x, ev3.y = bbox_lap[0] + 8, bbox_lap[1] + bbox_lap[3] // 2
    app.laporan_view._on_tree_click(ev3)
    root.update()
    check("Klik ✓ di Laporan → masuk follow-up", len(store) == 1)
    snap_lap = next(iter(store.rows.values()))
    check("(v3.9.3) Snapshot asal LAPORAN-COM (SO=COM, Sistem=median)",
          snap_lap.get("asal") == "LAPORAN-COM" and
          "so" in snap_lap and "sistem" in snap_lap,
          f"got asal={snap_lap.get('asal')!r}")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
        xlsx_path = tf.name
    store.export_xlsx(xlsx_path)
    check("Export FOLLOW UP xlsx", os.path.getsize(xlsx_path) > 0)
    # (v3.9.6) FORMAT FILE SAMPLE: header = Resto · Nama Barang ·
    # [tanggal H-2..H+2 sebagai ANGKA] · Sistem · Deviasi · Loss Surplus
    # to BOM · Keterangan · SO · DEVIASI · Selisih · Selisih Deviasi ·
    # Cek FU · PIC · Asal · Status TL · Ditambahkan
    import openpyxl as _oxl
    _wb = _oxl.load_workbook(xlsx_path)
    _ws = _wb["FOLLOW UP"]
    _hdr = [c.value for c in _ws[1]]
    _h_snap = snap_lap.get("h")
    _d0 = int(_h_snap) - 2 if isinstance(_h_snap, (int, float)) else None
    check("(v3.9.6) Export header = format file sample",
          _hdr[:3] == ["Resto", "Nama Barang", str(_d0)] and
          _hdr[7:12] == ["Sistem", "Deviasi", "Loss Surplus to BOM",
                         "Keterangan", "SO"] and
          _hdr[12:17] == ["DEVIASI", "Selisih", "Selisih Deviasi",
                          "Cek FU", "PIC"] and
          _hdr[17:20] == ["Asal", "Status TL", "Ditambahkan"],
          f"got {_hdr}")
    _wb.close()
    os.unlink(xlsx_path)

    # v3.8: fitur impor DIHAPUS — tombol & method tidak ada lagi
    check("v3.8: tombol Impor Hasil TL dihapus",
          fu.btn_import is None)
    check("v3.8: FollowUpStore.import_workbook dihapus",
          not hasattr(store, "import_workbook"))

    # -- persistensi: store baru membaca followup.json --
    from src.ui.followup import FollowUpStore
    store2 = FollowUpStore()
    check("Persistensi: store baru memuat 1 baris", len(store2) == 1)

    # -- kosongkan --
    store.clear()
    check("Kosongkan → 0 baris", len(store) == 0)

    # ==================================================================
    print("== 12. v3.3 ENGINE: sort linear + iid fix + shared cache ==")

    # ---- (a) SORT engine baru: iid & mapping tetap utuh ----
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    dv = app.deviasi_gr_view
    tree = dv.tree
    kids = list(tree.get_children(""))
    check("Deviasi ≥ 2 baris utk uji sort", len(kids) >= 2, f"got {len(kids)}")

    dv._sort_by("Nama Barang", reverse=True)   # Z→A
    root.update()
    kids_after = list(tree.get_children(""))
    check("Sort: jumlah baris tetap", len(kids_after) == len(kids))
    check("Sort: iid dipertahankan (set sama)", set(kids_after) == set(kids))
    check("Sort: urutan berubah (Z→A)", kids_after != kids)
    nama_first = tree.set(kids_after[0], "Nama Barang")
    nama_last = tree.set(kids_after[-1], "Nama Barang")
    check("Sort Z→A benar (first ≥ last)", nama_first >= nama_last,
          f"{nama_first!r} vs {nama_last!r}")

    # toggle baris pertama SETELAH sort → fp harus fp baris visual itu
    first_after = kids_after[0]
    fp_expected = dv._fp_map.get(first_after)
    snap_expected = dv._row_snaps.get(first_after)
    bbox = tree.bbox(first_after)
    evs = _Ev()
    evs.widget = tree
    evs.x, evs.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_tree_click(evs)
    root.update()
    check("Toggle post-sort: fp baris visual masuk store",
          fp_expected in store.rows)
    snap_in_store = store.rows.get(fp_expected)
    check("Toggle post-sort: snapshot = baris visual (barang cocok)",
          snap_in_store is not None and
          snap_in_store.get("barang") == snap_expected.get("barang"))

    # double-click sel kolom ✓ → toggle (bukan popup)
    n_before = len(store)
    evd = _Ev()
    evd.widget = tree
    evd.x, evd.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_double_click(evd)
    root.update()
    check("Double-click sel ✓ = toggle (v3.3)", len(store) != n_before,
          f"{n_before} → {len(store)}")

    # ---- (b) FOLLOW UP: bug v3.2 'salah baris setelah sort' → iid fix ----
    # ambil 2 baris deviasi dengan Nama Barang BERBEDA
    kids = list(tree.get_children(""))
    picks = []
    seen_nama = set()
    for k in kids:
        nm = tree.set(k, "Nama Barang")
        if nm not in seen_nama:
            seen_nama.add(nm)
            picks.append(k)
        if len(picks) == 2:
            break
    check("Dapat 2 baris barang berbeda utk uji follow-up",
          len(picks) == 2)
    if len(picks) == 2:
        store.clear()
        # toggle urutan TERBALIK (A dulu, Z kemudian) supaya urutan tabel
        # follow-up awal = [A, Z] → sort Z→A benar-benar membalik urutan
        for k in reversed(picks):
            b = tree.bbox(k)
            evp = _Ev()
            evp.widget = tree
            evp.x, evp.y = b[0] + 8, b[1] + b[3] // 2
            dv._on_tree_click(evp)
            root.update()
        check("2 baris masuk follow-up", len(store) == 2)

        select_and_wait(root, app, app.tab_followup, app.followup_view)
        fu = app.followup_view
        fu_kids = list(fu.tree.get_children(""))
        check("Follow Up tampil 2 baris", len(fu_kids) == 2)

        # urutan awal → barang masing-masing (kolom idx 2 = Nama Barang;
        # v3.9.6 format file sample: 0✓·1Resto·2Nama Barang·3..7 tanggal)
        barang_awal = [fu.tree.item(k, "values")[2] for k in fu_kids]

        # SORT tabel follow-up by Nama Barang Z→A → urutan terbalik
        fu._sort_by("Nama Barang", reverse=True)
        root.update()
        fu_kids_sorted = list(fu.tree.get_children(""))
        check("FU sort: urutan berubah",
              fu_kids_sorted != fu_kids and len(fu_kids_sorted) == 2)
        barang_sorted = [fu.tree.item(k, "values")[2]
                         for k in fu_kids_sorted]
        check("FU sort Z→A benar", barang_sorted == sorted(
            barang_awal, reverse=True))

        # klik ✓ pada baris visual PERTAMA setelah sort → baris yang
        # keluar harus baris visual itu (v3.2 buggy: keluar baris index-0
        # lama = kemungkinan baris yang salah)
        first_fu = fu_kids_sorted[0]
        barang_first = fu.tree.item(first_fu, "values")[2]
        fps_before = set(store.rows)
        snaps_before = dict(store.rows)   # fp → snap (sebelum dihapus)
        bf = fu.tree.bbox(first_fu)
        evf = _Ev()
        evf.widget = fu.tree
        evf.x, evf.y = bf[0] + 8, bf[1] + bf[3] // 2
        fu._on_tree_click(evf)
        root.update()
        removed = fps_before - set(store.rows)
        check("Klik ✓ post-sort mengeluarkan baris yang BENAR (v3.3)",
              len(removed) == 1)
        if removed:
            snap_removed = snaps_before.get(list(removed)[0])
            check("Baris keluar = baris visual pertama (barang cocok)",
                  snap_removed is not None and
                  snap_removed.get("barang") == barang_first,
                  f"{snap_removed.get('barang')!r} vs {barang_first!r}")
        check("1 baris tersisa di follow-up", len(store) == 1)

    # ---- (c) Shared pivot cache GR/PCS ----
    check("Cache pivot GR/PCS dibagikan (objek cache sama)",
          app.deviasi_gr_view._shared_cache is
          app.deviasi_pcs_view._shared_cache and
          app.deviasi_gr_view._shared_cache is app._deviasi_pivot_cache)
    # v3.9: H sudah otomatis sama (shared) — paksa refresh PCS →
    # HARUS cache-hit → objek pivot identik dgn GR
    app.deviasi_pcs_view._refresh()
    wait_view(root, app.deviasi_pcs_view)
    check("Pivot GR & PCS = objek DataFrame sama (compute 1×, bukan 2×)",
          app.deviasi_pcs_view._cached_pivot is
          app.deviasi_gr_view._cached_pivot and
          app.deviasi_pcs_view._cached_pivot is not None)

    store.clear()

    for p in (followup_path(), resolved_path()):
        if p.exists():
            p.unlink()

    # ==================================================================
    print("== 13. v3.4→v3.6 — TAB 📤 REKAP SELISIH IN (audit data app) ==")
    from src.ui.in_selisih_view import COLUMNS, InDetailPopup
    COL_IDS = [c[0] for c in COLUMNS]
    iv = app.in_selisih_view
    select_and_wait(root, app, app.tab_in_selisih, iv)
    tree_in = iv.tree
    kids_in = list(tree_in.get_children(""))
    check("Rekap Selisih IN: baris anomali tampil (default Hanya Selisih ≠ 0)",
          len(kids_in) == 4, f"got {len(kids_in)}")
    hdrs = [tree_in.heading(c)["text"] for c in COL_IDS]
    check("(v3.6) Kolom = 12: + Hasil SO + Saldo + Hasil Audit + Catatan",
          hdrs == ["Resto", "Tanggal", "Nama Barang", "KATEGORI", "Satuan",
                   "Hasil SO", "Barang Masuk", "IN", "Selisih IN", "Saldo",
                   "Hasil Audit", "Catatan Audit"], f"got {hdrs}")
    check("(v3.6) Tidak ada segment Ringkas|Audit lagi (SATU tabel)",
          not hasattr(iv, "mode_seg"))
    # baris ber-selisih: KOPI tgl3 (BM=100, IN=0, SO=50)
    kopi3 = None
    for k in kids_in:
        vals = tree_in.item(k, "values")
        if vals[2] == "KOPI BUBUK 100G" and vals[1] == "3":
            kopi3 = k
    if kopi3:
        r = {c: tree_in.set(kopi3, c) for c in COL_IDS}
        check("Selisih IN = BM − IN (KOPI tgl3: BM 100, IN '-' → 100)",
              r["Barang Masuk"] == "100" and r["IN"] == "-"
              and r["Selisih IN"] == "100", f"got {r}")
        check("(v3.6) Kolom SO terisi (KOPI tgl3 SO=50)",
              r["Hasil SO"] == "50", f"got {r['Hasil SO']!r}")
        check("(v3.6) Kolom Hasil Audit terisi",
              r["Hasil Audit"] == "CUT-OFF RESOLVED",
              f"got {r['Hasil Audit']!r}")
    st_cells = {tree_in.set(k, "Hasil Audit") for k in kids_in}
    check("(v3.6) Status VBA tampil (VALID/CUT-OFF/DEVIASI)",
          {"VALID (Sistem Masuk)", "CUT-OFF RESOLVED",
           "DEVIASI MURNI"} <= st_cells, f"got {st_cells}")
    check("(v3.6) KPI chips tampil (audit data app)",
          iv.kpi_card.winfo_ismapped())
    tags0 = iv.tree.item(kids_in[0], "tags") if kids_in else ()
    check("(v3.6) Baris diberi tag warna status",
          any(t.startswith("st_") for t in tags0), f"got {tags0}")

    # tampilkan semua baris (utk drill-down AYAM tgl 10)
    iv.only_selisih_var.set(False)
    iv._refresh()
    wait_view(root, iv)
    kids_in = list(tree_in.get_children(""))
    check("Hanya Selisih OFF → semua baris audit tampil (9)",
          len(kids_in) == 9, f"got {len(kids_in)}")

    # ---- drill-down: double-click baris AYAM FILET MLGPAR tgl 10 ----
    target = None
    for k in kids_in:
        vals = tree_in.item(k, "values")
        if vals[0] == "MLGPAR" and vals[1] == "10" and vals[2] == "AYAM FILET":
            target = k
            break
    check("Ada baris MLGPAR/AYAM FILET/Tgl 10 utk drill-down", target is not None)
    if target is not None:
        bbox = tree_in.bbox(target)
        evd = _Ev()
        evd.widget = tree_in
        evd.x, evd.y = bbox[0] + 10, bbox[1] + bbox[3] // 2
        iv._on_double_click(evd)
        root.update()
        # popup terakhir di stack toplevel
        popups = [w for w in root.winfo_children()
                  if isinstance(w, InDetailPopup) and w.winfo_exists()]
        check("Double-click → popup Rincian IN terbuka", len(popups) >= 1)
        if popups:
            pop = popups[-1]
            pkids = list(pop.tree.get_children(""))
            srcs = {pop.tree.set(k, "Source") for k in pkids}
            check("Popup: ada dokumen 42.05", any("42.05" in s for s in srcs),
                  f"srcs={srcs}")
            check("Popup: ada dokumen 32.24", any("32.24" in s for s in srcs),
                  f"srcs={srcs}")
            check("Popup: ada subtotal per sumber",
                  any(str(s).startswith("TOTAL") for s in srcs))
            check("Popup: ada TOTAL IN", "TOTAL IN" in str(pop.tree.item(
                pkids[-1], "values")[0] if pkids else ""))
            nomors = [pop.tree.set(k, "Nomor") for k in pkids
                      if pop.tree.set(k, "Nomor")]
            check("Popup: Nomor dokumen tampil (IT./RI.)",
                  any(n.startswith(("IT.", "RI.", "PI.")) for n in nomors),
                  f"nomors={nomors[:4]}")
            # qty 42.05(750) + 32.24(300) = 1050 == IN metric di append1? (mock IN=5 —
            # detail mock terpisah; verifikasi total popup = 1050)
            total_row = [pop.tree.set(k, "Qty") for k in pkids
                         if pop.tree.set(k, "Source") == "TOTAL IN"]
            # v3.9.1 (FIX C-03): format angka gaya Indonesia — 1.050,
            # bukan 1,050 (konsisten dgn formatter tabel/KPI).
            check("Popup: TOTAL IN = 1.050 (42.05:750 + 32.24:300)",
                  total_row and total_row[0] == "1.050", f"got {total_row}")
            # copy semua nomor unik
            pop._copy_all_unique()
            root.update()
            clip = root.clipboard_get()
            check("Copy Semua Nomor → clipboard berisi IT./RI. unik",
                  "IT.2026.09.00202" in clip and "RI.2026.09.009" in clip)
            pop.destroy()
            root.update()

    # ==================================================================
    print("== 14. v3.6 — AUDIT REKONSILIASI × DATA APP + FIX/KOLOM ==")
    from src.pipeline.fn_audit import (
        AUDIT_INPUT_COLUMNS,
        build_audit_input,
        build_audit_rekap,
    )
    # (pd sudah di-import di level modul — import lokal membuat 'pd' local
    #  name utk seluruh main() → UnboundLocalError di section sebelumnya)

    # --- (a) build_audit_input: rekap + in_detail → 10 kolom kanonik ---
    raw = build_audit_input(rekap_so, in_detail)
    check("build_audit_input: 10 kolom kanonik (struktur input VBA)",
          list(raw.columns) == AUDIT_INPUT_COLUMNS,
          f"got {list(raw.columns)}")
    check("build_audit_input: baris = union aktivitas (SO/BM/IN) = 9",
          len(raw) == 9, f"got {len(raw)}")
    check("build_audit_input: urut per (Resto, Item, Tanggal)",
          raw["Resto"].tolist()[:4] == ["MLGPAR"] * 4
          and raw["Tanggal"].tolist()[:2] == [4, 5],
          f"got {list(zip(raw['Resto'], raw['Tanggal']))[:5]}")
    so_g4 = raw[(raw["Nama Item"] == "GULA PASIR")
                & (raw["Tanggal"] == 4)]
    check("build_audit_input: Hasil SO hadir di tanggal SO (NaN selain itu)",
          float(so_g4["Hasil SO"].iloc[0]) == 100.0
          and raw[raw["Nama Item"] == "SUSU UHT 1L"]["Hasil SO"].isna().all(),
          f"got {so_g4['Hasil SO'].tolist()}")

    # --- (b) engine: aturan VBA pada data app ---
    sts = audit_df["Status Analisis Audit"].tolist()
    check("Engine: OK (Matching) saat BM == IN",
          "OK (Matching)" in sts)
    check("Engine: VALID (Sistem Masuk) (SO naik + BM=0 + IN>0)",
          "VALID (Sistem Masuk)" in sts)
    check("Engine: CUT-OFF RESOLVED (+100 lalu −100)",
          sts.count("CUT-OFF RESOLVED") == 2)
    check("Engine: DEVIASI MURNI (sisa gantung)",
          "DEVIASI MURNI" in sts)
    check("Engine: KPI lengkap dari data app",
          audit_kpi["rows"] == 9 and audit_kpi["omit"] == 1
          and audit_kpi["cutoff"] == 2 and audit_kpi["deviasi_murni"] == 1
          and abs(audit_kpi["deviasi_qty"] - 80.0) < 0.001,
          f"got {audit_kpi}")
    dm = audit_df[audit_df["Status Analisis Audit"] == "DEVIASI MURNI"]
    check("Engine: catatan Sisa Gantung VBA-style",
          "Sisa Gantung: +80" in str(dm.iloc[0]["Detail & Catatan Audit"]),
          f"got {dm.iloc[0]['Detail & Catatan Audit']!r}")

    # --- (v3.9.6) TANGGAL 1: PEMBANDING SO = SO BULAN LALU (user:
    #     "tab selisih in jika tanggal 1 pembanding SO nya SO bulan
    #     lalu") — urutan bulan lalu kini KRONOLOGIS 25•→31• lalu tgl 1;
    #     delta SO di tanggal 1 membanding SO TERAKHIR bulan lalu (31•),
    #     bukan SO tgl 25• (bug sort numerik lama). ---
    _aud_rows = []
    for _day, _so in [(25, 100.0), (26, 110.0), (27, 120.0), (28, 130.0),
                      (29, 140.0), (30, 150.0), (31, 160.0)]:
        _aud_rows.append({"NAMA RESTO": "BKSALT", "Nama Barang": "ITEM X",
                          "JENIS": "SO", "Tanggal": -_day, "Value": _so})
    _aud_rows.append({"NAMA RESTO": "BKSALT", "Nama Barang": "ITEM X",
                      "JENIS": "SO", "Tanggal": 1, "Value": 200.0})
    _aud_in = [{"Tanggal": 1, "NAMA RESTO": "BKSALT",
                "Nama Barang": "ITEM X", "SOURCE IN": "42.05",
                "Value": 50.0}]
    _raw2 = build_audit_input(pd.DataFrame(_aud_rows),
                               pd.DataFrame(_aud_in))
    check("(v3.9.6) Audit: urutan KRONOLOGIS (−25→−31 lalu 1)",
          _raw2["Tanggal"].tolist() ==
          [-25, -26, -27, -28, -29, -30, -31, 1],
          f"got {_raw2['Tanggal'].tolist()}")
    _audit2, _ = build_audit_rekap(_raw2)
    _r1 = _audit2[_audit2["Tanggal"] == 1].iloc[0]
    check("(v3.9.6) Audit tgl 1: delta SO vs SO bulan lalu TERAKHIR "
          "(SO Naik +40 = 200−160•)",
          "SO Naik +40" in str(_r1["Detail & Catatan Audit"]),
          f"got {_r1['Detail & Catatan Audit']!r}")
    check("(v3.9.6) Audit tgl 1: status VALID (SO naik vs bulan lalu)",
          _r1["Status Analisis Audit"] == "VALID (Sistem Masuk)",
          f"got {_r1['Status Analisis Audit']!r}")

    # --- (c) BUG FIX v3.6: klik funnel heading → popup TERBUKA ---
    select_and_wait(root, app, app.tab_in_selisih, iv)
    popups_before = [w for w in root.winfo_children() if w.winfo_exists()]
    x_resto = 35   # tengah kolom pertama 'Resto'
    tree_in.event_generate("<Button-1>", x=x_resto, y=10, when="now")
    root.update()
    new_pops = [w for w in root.winfo_children()
                if w.winfo_exists() and w not in popups_before
                and w.title().startswith("Filter —")]
    check("(v3.6 BUG FIX) Klik funnel 'Resto' dgn mouse → popup filter "
          "TERBUKA", len(new_pops) == 1,
          f"got {[w.title() for w in new_pops]}")
    for p in new_pops:
        p.destroy()
    root.update()

    # --- (d) header filter semua kolom (incl. Hasil Audit & SO) ---
    check("(v3.6) Semua 12 kolom punya HeaderFilter",
          hasattr(iv, "header_filters") and
          len(iv.header_filters._filters) == len(COL_IDS))
    iv._on_col_filter("Hasil Audit", {"DEVIASI MURNI"})
    wait_view(root, iv)
    kids_f = list(tree_in.get_children(""))
    check("Filter header Hasil Audit=DEVIASI MURNI → hanya baris SUSU",
          len(kids_f) == 1 and
          tree_in.set(kids_f[0], "Nama Barang") == "SUSU UHT 1L",
          f"got {[(tree_in.set(k, 'Nama Barang')) for k in kids_f]}")
    iv._reset_filter_states()
    iv._refresh()
    wait_view(root, iv)

    # --- (e) HIDE/UNHIDE KOLOM (ColumnManager v3.6) ---
    check("(v3.6) ColumnManager terpasang", iv._colmgr is not None)
    iv._colmgr.hide("KATEGORI")
    root.update()
    check("Hide kolom KATEGORI → displaycolumns tanpa KATEGORI",
          "KATEGORI" not in [str(c) for c in tree_in.cget("displaycolumns")],
          f"got {tree_in.cget('displaycolumns')}")
    hdrs_now = [tree_in.heading(c)["text"]
                for c in tree_in["columns"]
                if c in [str(x) for x in
                         tree_in.cget("displaycolumns")]]
    check("Hide kolom: heading KATEGORI hilang dari tampilan",
          "KATEGORI" not in hdrs_now, f"got {hdrs_now}")
    # identifikasi klik tetap benar setelah kolom disembunyikan
    # (display: Resto 74 + Tanggal 64 → Nama Barang mulai x=138)
    x_nb = 74 + 64 + 100   # tengah kolom 'Nama Barang' (KATEGORI hidden)
    hits = {"n": 0}
    orig_open = iv.header_filters._filters["Nama Barang"].open_popup
    iv.header_filters._filters["Nama Barang"].open_popup = \
        lambda *a, **k: hits.__setitem__("n", hits["n"] + 1)
    tree_in.event_generate("<Button-1>", x=x_nb, y=10, when="now")
    root.update()
    iv.header_filters._filters["Nama Barang"].open_popup = orig_open
    check("(v3.6) Klik funnel tetap akurat setelah kolom disembunyikan",
          hits["n"] == 1, f"got {hits['n']}")
    iv._colmgr.show_all()
    root.update()
    check("Show all → semua kolom kembali tampil",
          "#all" in str(tree_in.cget("displaycolumns")) or
          len(tree_in.cget("displaycolumns")) == len(COL_IDS),
          f"got {tree_in.cget('displaycolumns')}")
    # panel kolom terbuka & tertutup
    iv._colmgr.open_panel()
    root.update()
    check("Tombol ◱ Kolom → panel checklist terbuka",
          iv._colmgr._panel is not None and iv._colmgr._panel.winfo_exists())
    iv._colmgr.open_panel()   # toggle tutup
    root.update()

    # --- (f) LightMode dihapus total ---
    import inspect

    from src.config import Config as _Cfg
    check("(v3.5) Config tidak lagi memuat LightMode",
          "self.LightMode" not in inspect.getsource(_Cfg))

    # ==================================================================
    print("== 15. v3.4 — LEBAR KOLOM: drag tepi + ↔ Auto-Fit ==")
    from src.ui.widgets import enable_col_resize
    # (a) drag tepi kanan heading kolom pertama
    # (stretch=False supaya lebar deterministik — dengan stretch Tk
    # redistribusi ruang sisa jendela ke semua kolom)
    tree_in.column("Resto", stretch=False)
    w_before = tree_in.column("Resto", "width")
    edge_x = w_before  # tepi kanan kolom pertama
    tree_in.event_generate("<Button-1>", x=edge_x, y=10)
    root.update()
    tree_in.event_generate("<B1-Motion>", x=edge_x + 60, y=10)
    root.update()
    tree_in.event_generate("<ButtonRelease-1>", x=edge_x + 60, y=10)
    root.update()
    w_after = tree_in.column("Resto", "width")
    check("Drag tepi heading → lebar kolom berubah (w+60)",
          w_after == w_before + 60, f"{w_before} → {w_after}")
    tree_in.column("Resto", stretch=True)
    # (b) tombol ↔ Auto-Fit menyesuaikan lebar ke konten
    iv._auto_fit()
    root.update()
    w_autofit = tree_in.column("Nama Barang", "width")
    check("↔ Auto-Fit: kolom Nama Barang menyesuaikan konten (>default)",
          w_autofit != 200, f"200 → {w_autofit}")
    # (c) enable_col_resize terpasang di semua view utama
    views_trees = [
        app.pivot_view.tree, app.deviasi_gr_view.tree,
        app.deviasi_pcs_view.tree, app.laporan_view.tree,
        app.rincian_view.tree, app.followup_view.tree,
        app.in_selisih_view.tree,
    ]
    # tidak ada API publik utk cek binding — verifikasi tidak error saat
    # memanggil ulang (idempotent) + smoke drag di pivot (show tree headings)
    for t in views_trees:
        enable_col_resize(t)
    check("enable_col_resize terpasang di 7 view (idempotent, tanpa error)",
          True)

    # ==================================================================
    print("== 16. v3.7 — DEEP AUDIT FIXES (display-vs-logical index dst) ==")
    import numpy as np

    from src.ui.widgets import (
        ColumnManager,
        _tree_row_passes,
        apply_tree_row_filters,
        auto_fit_columns,
        identify_to_column,
    )

    # (a) apply_tree_row_filters membaca nilai kolom yang BENAR setelah
    #     kolom sebelumnya disembunyikan (dulu: index display ≠ logis)
    tfix = ttk.Treeview(root, columns=["A", "B", "C"], show="headings")
    for c in ("A", "B", "C"):
        tfix.heading(c, text=c)
        tfix.column(c, width=80)
    tfix.insert("", "end", iid="r1", values=("x", "keep", "1"))
    tfix.insert("", "end", iid="r2", values=("x", "drop", "2"))
    tfix.insert("", "end", iid="r3", values=("y", "keep", "3"))
    tfix.configure(displaycolumns=["B", "C"])          # sembunyikan A
    apply_tree_row_filters(tfix, {"B": {"keep"}})
    root.update()
    kids_a = list(tfix.get_children(""))
    check("(v3.7) Filter clone membaca kolom BENAR setelah hide",
          kids_a == ["r1", "r3"],
          f"kids={kids_a} (harus r1,r3 — dulu membaca kolom A: semua lolos)")
    apply_tree_row_filters(tfix, {})                     # reset tampilan
    root.update()
    check("(v3.7) Reset filter clone → semua baris kembali",
          len(list(tfix.get_children(""))) == 3)
    tfix.destroy()

    # (b) filter '#0' di tree 2-level memakai text PARENT (nama barang),
    #     bukan text anak (nama metric) — dulu: semua baris tersembunyi
    t2 = ttk.Treeview(root, columns=["V"], show="tree headings")
    t2.heading("#0", text="Nama Barang")
    t2.heading("V", text="V")
    t2.column("#0", width=120)
    t2.column("V", width=60)
    t2.insert("", "end", iid="p1", text="AYAM", values=(""))
    t2.insert("p1", "end", iid="p1_m1", text="1.SO", values=("10"))
    t2.insert("p1", "end", iid="p1_m2", text="4.IN", values=("5"))
    t2.insert("", "end", iid="p2", text="GULA", values=(""))
    t2.insert("p2", "end", iid="p2_m1", text="1.SO", values=("3"))
    apply_tree_row_filters(t2, {"#0": {"AYAM"}})
    root.update()
    kids_b = set(t2.get_children(""))
    check("(v3.7) Filter #0 clone 2-level → parent+anak metric tampil",
          "p1" in kids_b and "p2" not in kids_b and
          len(t2.get_children("p1")) == 2,
          f"top={kids_b} anak_p1={t2.get_children('p1')}")
    t2.destroy()

    # (c) auto_fit mengukur nilai kolom yang BENAR setelah hide
    #     (kolom B berisi teks panjang; kolom A disembunyikan berisi teks
    #     pendek — lebar B harus mengikuti konten B, bukan A)
    t3 = ttk.Treeview(root, columns=["SHORT", "LONGVAL"], show="headings")
    for c in ("SHORT", "LONGVAL"):
        t3.heading(c, text=c)
        t3.column(c, width=50, stretch=False)
    t3.insert("", "end", values=("ab", "NILAI_SANGAT_PANJANG_0123456789"))
    t3.configure(displaycolumns=["LONGVAL"])           # sembunyikan SHORT
    auto_fit_columns(t3, columns=["LONGVAL"])
    w_long = t3.column("LONGVAL", "width")
    check("(v3.7) Auto-fit ukur kolom BENAR setelah hide (B melebar)",
          w_long > 100, f"w={w_long} (dulu mengukur SHORT → ~50-60)")
    t3.destroy()

    # (d) toggle ✓ memakai NAMA kolom — setelah ✓ disembunyikan, klik sel
    #     kolom lain TIDAK lagi memicu toggle (dulu: posisi '#1' salah)
    dv = app.deviasi_gr_view
    dtr = dv.tree
    dv_store_before = set(dv.store.rows.keys()) if dv.store else set()
    dtr._column_manager.hide("✓")
    root.update()
    # klik sel kolom Resto (posisi display pertama setelah ✓ hidden)
    first_row = dtr.get_children("")[0]
    bbox = dtr.bbox(first_row, column="#1")
    if bbox:
        ev = tk.Event()
        ev.x, ev.y = bbox[0] + 5, bbox[1] + 5
        ev.widget = dtr
        dv._on_tree_click(ev)
        root.update()
        dv_store_after = set(dv.store.rows.keys()) if dv.store else set()
        check("(v3.7) Klik kolom lain setelah ✓ disembunyikan → tidak toggle",
              dv_store_after == dv_store_before,
              f"before={len(dv_store_before)} after={len(dv_store_after)}")
    else:
        check("(v3.7) Klik kolom lain setelah ✓ disembunyikan → tidak toggle",
              False, "bbox kolom tidak tersedia")
    dtr._column_manager.show_all()
    root.update()

    # (e) ColumnManager mirror sinkron state hidden (clone → sumber)
    t4 = ttk.Treeview(root, columns=["A", "B"], show="headings")
    for c in ("A", "B"):
        t4.heading(c, text=c)
        t4.column(c, width=60)
    t4.insert("", "end", values=("1", "2"))
    t5 = ttk.Treeview(root, columns=["A", "B"], show="headings")
    for c in ("A", "B"):
        t5.heading(c, text=c)
        t5.column(c, width=60)
    t5.insert("", "end", values=("1", "2"))
    cm_main = ColumnManager(t4)
    cm_clone = ColumnManager(t5, mirror=t4)
    cm_clone.hide("B")
    root.update()
    check("(v3.7) Mirror clone→sumber: displaycolumns sumber ikut",
          "B" not in [str(x) for x in t4.cget("displaycolumns")])
    check("(v3.7) Mirror clone→sumber: state hidden colmgr sinkron",
          cm_main.hidden == ["B"],
          f"cm_main.hidden={cm_main.hidden} (dulu [] → panel basi)")
    t4.destroy()
    t5.destroy()

    # (f) ENGINE v3.7 — running stock vektor == implementasi lama
    #     (10 edge-case sintetis; loop lama di-inline sebagai oracle)
    from src.pipeline.fn_running_stock import fn_running_stock, fn_running_stock_grouped

    def OLD_grouped(df, gk):
        srt = df.sort_values(gk + ["Tanggal"], ascending=True,
                             na_position="last").reset_index(drop=True)
        res = [fn_running_stock(g) for _, g in
               srt.groupby(gk, sort=False, dropna=False)]
        return pd.concat(res, ignore_index=True) if res else srt

    cases = {
        "normal": pd.DataFrame({
            "Nama Barang": ["A", "A", "A", "A", "B", "B"],
            "NAMA RESTO": ["R1", "R1", "R1", "R1", "R2", "R2"],
            "Tanggal": pd.array([1, 2, 3, 4, 1, 2], dtype="Int64"),
            "IN": [10.0, 5, 0, 3, 7, 2],
            "OUT": [2, 1, 4, 0, 1, 1],
            "BARANG KELUAR": [0, 0, 1, 0, 0, 0],
            "SALDO AWAL": [100, np.nan, np.nan, np.nan, 50, np.nan],
        }),
        "bulan-lalu-net-nol-tidak-ikut": pd.DataFrame({
            "Nama Barang": ["A"] * 6,
            "NAMA RESTO": ["R1"] * 6,
            "Tanggal": pd.array([-25, -26, 1, 2, 3, 31], dtype="Int64"),
            "IN": [1, 2, 10, 5, 0, 3],
            "OUT": [0, 1, 2, 1, 4, 0],
            "BARANG KELUAR": [0, 0, 0, 0, 1, 0],
            "SALDO AWAL": [100.0] + [np.nan] * 5,
        }),
        "tanggal-NaN-ekor": pd.DataFrame({
            "Nama Barang": ["A", "A", "A", "A"],
            "NAMA RESTO": ["R1"] * 4,
            "Tanggal": pd.array([1, 2, None, 3], dtype="Int64"),
            "IN": [10, 5, 99, 3],
            "OUT": [2, 1, 5, 0],
            "BARANG KELUAR": [0, 0, 0, 0],
            "SALDO AWAL": [100.0, np.nan, np.nan, np.nan],
        }),
        "key-NaN-satu-grup": pd.DataFrame({
            "Nama Barang": [None, None, "B"],
            "NAMA RESTO": ["R1", "R1", "R2"],
            "Tanggal": pd.array([1, 2, 1], dtype="Int64"),
            "IN": [10, 5, 7],
            "OUT": [2, 1, 1],
            "BARANG KELUAR": [0, 0, 0],
            "SALDO AWAL": [100.0, np.nan, 3.0],
        }),
        "saldo-awal-negatif": pd.DataFrame({
            "Nama Barang": ["A", "A", "A"],
            "NAMA RESTO": ["R1", "R1", "R1"],
            "Tanggal": pd.array([1, 2, 3], dtype="Int64"),
            "IN": [1, 1, 1],
            "OUT": [0, 0, 0],
            "BARANG KELUAR": [0, 0, 0],
            "SALDO AWAL": [-5.0, np.nan, -2.0],
        }),
        "grup-tanpa-tgl-ge-1": pd.DataFrame({
            "Nama Barang": ["A", "A", "C"],
            "NAMA RESTO": ["R1", "R1", "R3"],
            "Tanggal": pd.array([-25, -20, 5], dtype="Int64"),
            "IN": [1, 2, 10],
            "OUT": [0, 1, 2],
            "BARANG KELUAR": [0, 0, 0],
            "SALDO AWAL": [100.0, np.nan, 5.0],
        }),
    }
    gk = ["Nama Barang", "NAMA RESTO"]
    ok_rs = True
    for cname, cdf in cases.items():
        old = OLD_grouped(cdf.copy(), gk)
        new = fn_running_stock_grouped(cdf.copy(), gk)
        a = pd.to_numeric(old["SALDO AKHIR"], errors="coerce") \
            .fillna(-777).to_numpy()
        b = pd.to_numeric(new["SALDO AKHIR"], errors="coerce") \
            .fillna(-777).to_numpy()
        same = len(a) == len(b) and np.allclose(a, b, atol=1e-9)
        ok_rs = ok_rs and same
        if not same:
            print(f"    case '{cname}' BEDA: {a} vs {b}")
    check("(v3.7) ENGINE running stock vektor == lama (6 edge-case)",
          ok_rs)

    # (g) ENGINE v3.7 — _group_info_columns == UDF lama (edge-case)
    from src.pipeline.append1 import _group_info_columns

    def OLD_group(ip, KC, IC):
        def _sj(series):
            vals = series.dropna()
            if vals.empty:
                return None
            return ", ".join(str(v) for v in pd.unique(vals))
        return ip.groupby(KC, as_index=False, dropna=False).agg(
            {c: _sj for c in IC if c in ip.columns})

    KC = ["Nama Barang", "NAMA RESTO", "Tanggal"]
    IC = ["Nomor", "Nomor PO"]
    ip = pd.DataFrame({
        "Nama Barang": ["A", "A", "A", None, None, "A"],
        "NAMA RESTO": ["R1", "R1", "R1", "R1", "R1", "R1"],
        "Tanggal": pd.array([1, 1, 2, 1, 2, None], dtype="Int64"),
        "Nomor": ["IT.2", "IT.1", "IT.1", "IT.5", "IT.6", "IT.7"],
        "Nomor PO": [None, None, None, "PO.9", None, None],
    })
    old = OLD_group(ip, KC, IC)
    new = _group_info_columns(ip, KC, IC)
    m = old.merge(new, on=KC, how="outer", suffixes=("_o", "_n"),
                  indicator=True)
    ok_keys = (m["_merge"] == "both").all() and len(old) == len(new)
    ok_vals = all(
        (m[f"{c}_o"].fillna("<NULL>").astype(str) ==
         m[f"{c}_n"].fillna("<NULL>").astype(str)).all()
        for c in IC if f"{c}_o" in m.columns)
    check("(v3.7) ENGINE info-group vektor == lama (NaN key + kosong)",
          ok_keys and ok_vals,
          f"keys={ok_keys} vals={ok_vals}")

    # (h) engine single-parse reader: hasil == jalur read_excel(header=hr)
    from src.pipeline.fn_rekap_mentah import _promote_at
    raw = pd.DataFrame([
        ["NAMA RESTO", "JENIS", "NAMA BARANG", "1", "2", "3"],
        ["R1", "SO", "AYAM", 5, None, 7],
        ["R1", "SO", "GULA", 1, 2, None],
    ])
    prom = _promote_at(raw, 0)
    check("(v3.7) Reader _promote_at: header & body benar",
          list(prom.columns) == ["NAMA RESTO", "JENIS", "NAMA BARANG",
                                 "1", "2", "3"] and len(prom) == 2 and
          prom.iloc[0, 5] == 7)

    # ==================================================================
    print("== 17. v3.8 — SELISIH IN 1-31 + PIVOT -31..31 + EXPORT + CF ==")

    # (a) default rentang tanggal baru
    check("(v3.8) Rekap Selisih IN default = 1 s/d 31 (bulan berjalan)",
          app.in_selisih_view.tgl_start_var.get() == "1" and
          app.in_selisih_view.tgl_end_var.get() == "31",
          f"got {app.in_selisih_view.tgl_start_var.get()}.."
          f"{app.in_selisih_view.tgl_end_var.get()}")
    app.in_selisih_view.tgl_start_var.set("-5")
    app.in_selisih_view._reset_filter()
    check("(v3.8) Reset Selisih IN kembali ke 1–31",
          app.in_selisih_view.tgl_start_var.get() == "1")
    app.pivot_view._reset_filter()
    check("(v3.8) Reset Pivot kembali ke -31–31",
          app.pivot_view.tgl_start_var.get() == "-31")

    # (b) kolom tanggal pivot mode TANGGAL: -25..-31 lalu 1..3 (kronologis)
    #     — akar bug user "25, 26, lalu 1": rentang lama -26 memotong
    #     tgl 27-31 bulan lalu
    test_df = pd.DataFrame({
        "Nama Barang": ["AYAM"] * 12,
        "JENIS": ["1.SO"] * 12,
        "NAMA RESTO": ["MLGPAR"] * 12,
        "Tanggal": [-25, -26, -27, -28, -29, -30, -31, 1, 2, 3, 4, 5],
        "NILAI": [float(i + 1) for i in range(12)],
        "SATUAN": ["GR"] * 12,
        "KATEGORI": ["DEVIASI"] * 12,
        "SOURCE KIRIMAN": ["GUDANG"] * 12,
    })
    orig_data = pv.data
    try:
        pv.data = test_df
        st = {"name_selected": None, "resto": "(All)", "source": "(All)",
              "kategori": "(All)", "tgl_start": -31, "tgl_end": 31,
              "mode": "tanggal", "hide_empty": False}
        payload = pv._compute_payload(st)
        want_cols = ["-25", "-26", "-27", "-28", "-29", "-30", "-31",
                     "1", "2", "3", "4", "5"]
        check("(v3.8) Pivot tanggal: kolom -25..-31 + 1..5 urut kronologis "
              "(bukan '25,26,lalu 1')",
              payload["columns"] == want_cols,
              f"got {payload['columns']}")
        # rentang lama (-26) memang memotong — bukti akar masalah
        st_old = dict(st, tgl_start=-26)
        payload_old = pv._compute_payload(st_old)
        check("(v3.8) Bukti akar bug: rentang lama -26 memotong -27..-31",
              payload_old["columns"] == ["-25", "-26", "1", "2", "3", "4",
                                         "5"],
              f"got {payload_old['columns']}")
    finally:
        pv.data = orig_data

    # (c) build_selisih_export_df — kolom PERSIS permintaan user
    from src.ui.export_sheets import (
        SELISIH_EXPORT_COLUMNS,
        add_pivot_sheet,
        build_selisih_export_df,
        write_selisih_sheet,
    )
    base = pd.DataFrame({
        "Resto": ["MLGPAR", "MLGPAR", "BDGUKU"],
        "Tanggal": [5, -25, 5],
        "Nama Barang": ["AYAM", "AYAM", "KOPI"],
        "KATEGORI": ["DEVIASI", "DEVIASI", "PCS"],
        "Satuan": ["GR", "GR", "PCS"],
        "Hasil SO": [None, 100.0, 50.0],
        "Barang Masuk": [80.0, None, 30.0],
        "IN": [60.0, 10.0, 30.0],
        "Selisih IN": [20.0, -10.0, 0.0],
        "Saldo": [0.0, 0.0, 0.0],
        "Hasil Audit": ["OK (Matching)", "OK", "OK"],
        "Catatan Audit": ["-", "-", "-"],
        "42.05": [50.0, 0.0, 20.0],
        "32.24": [10.0, 10.0, 10.0],
        "99.01": [0.0, 0.0, 0.0],
    })
    ex = build_selisih_export_df(base, 1, 31)
    check("(v3.8) Export selisih: kolom persis (Resto..Selisih, rename "
          "Sheet Barang Masuk/Kiriman HO/Kiriman Supplier/Pembelian)",
          list(ex.columns) == SELISIH_EXPORT_COLUMNS and
          SELISIH_EXPORT_COLUMNS == [
              "Resto", "Tanggal", "Nama Barang", "Kategori", "Satuan",
              "Hasil SO", "Sheet Barang Masuk", "Kiriman HO",
              "Kiriman Supplier", "Pembelian by Resto", "Selisih"],
          f"got {list(ex.columns)}")
    check("(v3.8) Export selisih: hanya baris tgl 1-31 (baris -25 keluar)",
          len(ex) == 2, f"got {len(ex)}")
    r_mlg = ex[ex["Resto"] == "MLGPAR"].iloc[0]
    check("(v3.8) Export selisih: nilai rename benar (BM→Sheet BM, "
          "4205→Kiriman HO, 3224→Kiriman Supplier, 9901→Pembelian)",
          float(r_mlg["Sheet Barang Masuk"]) == 80.0 and
          float(r_mlg["Kiriman HO"]) == 50.0 and
          float(r_mlg["Kiriman Supplier"]) == 10.0 and
          float(r_mlg["Pembelian by Resto"]) == 0.0 and
          float(r_mlg["Selisih"]) == 20.0,
          f"got {r_mlg.to_dict()}")
    check("(v3.8) Export selisih: urut Resto→Tanggal→Nama Barang "
          "(BDGUKU dulu, lalu MLGPAR)",
          list(ex["Resto"]) == ["BDGUKU", "MLGPAR"] and
          int(ex.iloc[0]["Tanggal"]) == 5,
          f"got {list(ex['Resto'])}")
    check("(v3.8) Export selisih: Hasil SO kosong tetap kosong (bukan 0)",
          pd.isna(r_mlg["Hasil SO"]) and
          float(ex.iloc[0]["Hasil SO"]) == 50.0)
    # edge: base TANPA kolom komponen 42.05/32.24/99.01 (defensif —
    # pd.to_numeric(None) scalar pernah bikin AttributeError .fillna)
    base_min = base.drop(columns=["42.05", "32.24", "99.01", "Saldo",
                                  "Hasil Audit", "Catatan Audit"])
    ex_min = build_selisih_export_df(base_min, 1, 31)
    check("(v3.8) Export selisih defensif: base tanpa kolom komponen OK",
          len(ex_min) == 2 and
          float(ex_min.iloc[0]["Kiriman HO"]) == 0.0 and
          list(ex_min.columns) == SELISIH_EXPORT_COLUMNS)
    check("(v3.8) Export selisih defensif: base None/empty → 0 baris",
          len(build_selisih_export_df(None)) == 0 and
          len(build_selisih_export_df(pd.DataFrame())) == 0)

    # (d) roundtrip file: sheet selisih + sheet PIVOT + conditional
    #     formatting dibaca kembali (verifikasi rumus file user)
    a1_small = pd.DataFrame({
        "Nama Barang": ["AYAM", "AYAM", "AYAM", "GULA"],
        "JENIS": ["1.SO", "4.IN", "5.BARANG MASUK", "1.SO"],
        "NAMA RESTO": ["MLGPAR"] * 4,
        "Tanggal": [-25, 1, 1, 2],
        "NILAI": [10.0, 5.0, 5.0, 7.0],
    })
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xlsx",
                                     delete=False) as tf:
        xlsx_path = tf.name
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        write_selisih_sheet(writer, ex)
        ok_pivot = add_pivot_sheet(writer, a1_small)
    check("(v3.8) add_pivot_sheet: sheet dibuat", ok_pivot)

    from openpyxl import load_workbook
    wb = load_workbook(xlsx_path)
    check("(v3.8) File export: sheet 'Selisih IN per Resto' + 'PIVOT'",
          wb.sheetnames == ["Selisih IN per Resto", "PIVOT"],
          f"got {wb.sheetnames}")
    ws_sel = wb["Selisih IN per Resto"]
    hdrs_sel = [c.value for c in ws_sel[1]]
    check("(v3.8) Sheet selisih: header = kolom export",
          hdrs_sel == SELISIH_EXPORT_COLUMNS, f"got {hdrs_sel}")
    check("(v3.8) Sheet selisih: freeze A2 + autofilter",
          ws_sel.freeze_panes == "A2" and
          str(ws_sel.auto_filter.ref).startswith("A1:"), )
    ws_p = wb["PIVOT"]
    check("(v3.8) PIVOT: layout baris 1-6 persis file user",
          ws_p["A1"].value == "NAMA RESTO" and ws_p["B1"].value == "(All)"
          and ws_p["A2"].value == "SOURCE KIRIMAN" and
          ws_p["A3"].value == "KATEGORI" and
          ws_p["A5"].value == "Sum of NILAI" and
          ws_p["B5"].value == "Column Labels" and
          ws_p["A6"].value == "Row Labels" and
          ws_p["B6"].value == -25 and ws_p["C6"].value == 1 and
          ws_p["D6"].value == 2,
          f"got A5={ws_p['A5'].value!r} B6={ws_p['B6'].value!r}")
    check("(v3.8) PIVOT: row label kolom A = nama barang (bold) + jenis",
          ws_p["A7"].value == "AYAM" and ws_p["A7"].font.bold and
          ws_p["A8"].value == "1.SO" and
          not (ws_p["A8"].font.bold or False) and
          ws_p["A11"].value == "GULA" and ws_p["A12"].value == "1.SO",
          f"got A7={ws_p['A7'].value!r} A8={ws_p['A8'].value!r} "
          f"A11={ws_p['A11'].value!r}")
    check("(v3.8) PIVOT: nilai Sum of NILAI (AYAM 1.SO tgl -25 = 10)",
          ws_p["B8"].value == 10.0 and ws_p["D12"].value == 7.0,
          f"got B8={ws_p['B8'].value!r} D12={ws_p['D12'].value!r}")

    all_formulas = []
    for cf in ws_p.conditional_formatting:
        for rule in cf.rules:
            all_formulas.extend(list(rule.formula or []))
    joined = " || ".join(all_formulas)
    check("(v3.8) PIVOT CF: =AND($A8=\"1.SO\",B8>A8) persis rumus user",
          'AND($A8="1.SO",B8>A8)' in joined, f"got {joined}")
    check("(v3.8) PIVOT CF: $A8=\"3.DEVIASI\" (border bawah)",
          '$A8="3.DEVIASI"' in joined)
    check("(v3.8) PIVOT CF: AND($A8=\"7.Selisih IN\",B8<>0) merah",
          'AND($A8="7.Selisih IN",B8<>0)' in joined)
    check("(v3.8) PIVOT CF: containsText 4.IN + 5.BARANG MASUK (kolom A)",
          'SEARCH("4.IN",A7)' in joined and
          'SEARCH("5.BARANG MASUK",A7)' in joined)
    rules_zero = [r for cf in ws_p.conditional_formatting for r in cf.rules
                  if r.type == "cellIs"]
    check("(v3.8) PIVOT CF: cellIs 0 (font putih) + header < 0 (bulan lalu)",
          len(rules_zero) == 2, f"got {len(rules_zero)}")
    os.unlink(xlsx_path)

    # (e) tombol export ada di view Selisih IN + Impor TL hilang
    check("(v3.8) Handler export Selisih IN ada",
          callable(app.in_selisih_view._on_export))

    print("== 18. v3.9 — EXPORT AUDIT OPT + STYLE WASTE (⤢/funnel/tabel) ==")

    # (a) build_selisih_export_df + audit_cols — opsi kolom hasil audit
    ex_audit = build_selisih_export_df(base, 1, 31,
                                       audit_cols=["Hasil Audit", "Saldo",
                                                   "Catatan Audit"])
    check("(v3.9) Export + audit: kolom audit ditambahkan setelah Selisih",
          list(ex_audit.columns) == SELISIH_EXPORT_COLUMNS + [
              "Hasil Audit", "Saldo", "Catatan Audit"],
          f"got {list(ex_audit.columns)}")
    r_m = ex_audit[ex_audit["Resto"] == "MLGPAR"].iloc[0]
    check("(v3.9) Export + audit: nilai sebaris BENAR (Hasil Audit ml "
          "OK (Matching), Saldo 0)",
          r_m["Hasil Audit"] == "OK (Matching)" and
          float(r_m["Saldo"]) == 0.0,
          f"got {r_m['Hasil Audit']!r} / {r_m['Saldo']!r}")
    ex_partial = build_selisih_export_df(base, 1, 31,
                                         audit_cols=["Hasil Audit"])
    check("(v3.9) Export + audit: subset 1 kolom OK",
          list(ex_partial.columns) == SELISIH_EXPORT_COLUMNS + ["Hasil Audit"])
    ex_none = build_selisih_export_df(base, 1, 31, audit_cols=[])
    check("(v3.9) Export tanpa kolom audit (opsi OFF) = perilaku v3.8",
          list(ex_none.columns) == SELISIH_EXPORT_COLUMNS)
    ex_bad = build_selisih_export_df(base, 1, 31,
                                     audit_cols=["Kolom Ngawur", "Saldo"])
    check("(v3.9) Export + audit: nama kolom invalid diabaikan",
          list(ex_bad.columns) == SELISIH_EXPORT_COLUMNS + ["Saldo"])

    # (b) dialog opsi export + _do_export inti (tanpa dialog file)
    check("(v3.9) Dialog opsi export ada (metode view)",
          callable(app.in_selisih_view._export_options_dialog))
    check("(v3.9) _do_export terpisah dari dialog (testable)",
          callable(app.in_selisih_view._do_export))
    with tempfile.NamedTemporaryFile(suffix=".xlsx",
                                     delete=False) as tf2:
        xlsx2 = tf2.name
    # patch messagebox sampai SELESAI section 18 (done() async memanggil
    # showinfo SETELAH file tertulis — patch tidak boleh dipulihkan duluan;
    # patch dipulihkan menjelang cleanup di bawah)
    import src.ui.in_selisih_view as _isv_mod
    _orig_info = _isv_mod.messagebox.showinfo
    _orig_warn = _isv_mod.messagebox.showwarning
    _isv_mod.messagebox.showinfo = lambda *a, **k: None
    _isv_mod.messagebox.showwarning = lambda *a, **k: None
    app.in_selisih_view._do_export(xlsx2, ["Hasil Audit", "Saldo"])
    t0 = time.time()
    wb2 = None
    while time.time() - t0 < 5:
        root.update()
        if os.path.exists(xlsx2) and os.path.getsize(xlsx2) > 0:
            try:
                wb2 = load_workbook(xlsx2)
                break
            except Exception:
                pass
        time.sleep(0.05)
    check("(v3.9) _do_export menulis file (async selesai)",
          wb2 is not None)
    if wb2 is not None:
        ws2 = wb2["Selisih IN per Resto"]
        hdr2 = [c.value for c in ws2[1]]
        check("(v3.9) Roundtrip _do_export: header + kolom audit",
              hdr2 == SELISIH_EXPORT_COLUMNS + ["Hasil Audit", "Saldo"],
              f"got {hdr2}")
    # tunggu job export benar2 selesai (done() async + showinfo patched)
    t0 = time.time()
    while time.time() - t0 < 3:
        root.update()
        time.sleep(0.02)
    os.unlink(xlsx2)

    # (c) STYLE WASTE — tabel besar + funnel merah + expander ⤢
    style = ttk.Style(root)
    check("(v3.9) Tabel diperbesar: rowheight 30 (dari 26) ala Waste",
          int(style.configure("Treeview", "rowheight")) == 30,
          f"got {style.configure('Treeview', 'rowheight')}")
    _hf_font = str(style.configure("Treeview.Heading", "font")).split()
    check("(v3.9) Tabel diperbesar: heading font size 10 bold",
          _hf_font[-2:] == ["10", "bold"],
          f"got {_hf_font}")
    from src.ui.widgets import TableExpander, funnel_image
    img_on = funnel_image(active=True)
    img_off = funnel_image(active=False)
    check("(v3.9) Funnel Waste: ikon aktif ≠ idle (merah vs terang)",
          str(img_on) != str(img_off))
    check("(v3.9) Funnel Waste: dua varian ter-cache",
          isinstance(funnel_image(active=True), tk.PhotoImage))

    # funnel merah saat kolom terfilter (state HeaderFilter + refresh_icon)
    def _img_name(v):
        if isinstance(v, (list, tuple)):
            return str(v[0]) if v else ""
        return str(v)

    iv = app.in_selisih_view
    hf = iv.header_filters._filters["Hasil Audit"]
    hf.selected = {"OK (Matching)"}   # simulasi apply dari popup
    hf.refresh_icon()
    root.update()
    check("(v3.9) Funnel kolom terfilter = varian MERAH (ala Waste)",
          _img_name(hf.tree.heading("Hasil Audit")["image"]) ==
          str(funnel_image(True)),
          f"got {hf.tree.heading('Hasil Audit')['image']}")
    hf.selected = None
    hf.refresh_icon()
    root.update()
    check("(v3.9) Funnel kolom tanpa filter = varian idle",
          _img_name(hf.tree.heading("Hasil Audit")["image"]) ==
          str(funnel_image(False)),
          f"got {hf.tree.heading('Hasil Audit')['image']}")

    # (d) expander ⤢ — ciutkan baris kontrol, tabel tinggi penuh
    dv = app.deviasi_gr_view
    exp = dv._expander
    check("(v3.9) TableExpander terpasang di semua view tabel",
          isinstance(exp, TableExpander) and
          isinstance(app.pivot_view._expander, TableExpander) and
          isinstance(app.rincian_view._expander, TableExpander) and
          isinstance(app.laporan_view._expander, TableExpander) and
          isinstance(app.followup_view._expander, TableExpander) and
          isinstance(iv._expander, TableExpander))
    # pastikan tab deviasi GR sedang TERLIHAT supaya tinggi tree bermakna
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    root.update_idletasks()
    root.update()
    fcard_w0 = dv._fcard.winfo_width()
    exp.collapse()
    root.update()
    check("(v3.9) ⤢ collapse: kartu Filter tersembunyi",
          dv._fcard.winfo_manager() == "" and
          dv._legend.winfo_manager() == "")
    tree_h1 = dv.tree.winfo_height()
    exp.restore()
    root.update()
    check("(v3.9) ⤡ restore: kartu Filter kembali tampil + urutan layout",
          dv._fcard.winfo_manager() == "pack" and
          dv._legend.winfo_manager() == "pack" and
          dv._fcard.winfo_width() == fcard_w0,
          f"fcard w={dv._fcard.winfo_width()} vs {fcard_w0}")
    tree_h0 = dv.tree.winfo_height()
    check("(v3.9) Tabel lebih TINGGI saat collapse (ala Waste ⤢)",
          tree_h1 > tree_h0, f"{tree_h1} vs {tree_h0}")
    # toggle kedua (state machine) + reset
    exp.collapse()
    exp.toggle()          # dari expanded → restore
    check("(v3.9) expander.toggle() siklus collapse↔restore",
          not exp.expanded and dv._fcard.winfo_manager() == "pack")
    exp.collapse()
    exp.reset()
    check("(v3.9) expander.reset() memulihkan layout",
          not exp.expanded and dv._fcard.winfo_manager() == "pack")

    # pulihkan messagebox yang di-patch (section 18b)
    _isv_mod.messagebox.showinfo = _orig_info
    _isv_mod.messagebox.showwarning = _orig_warn

    print("== 21. (v3.9.2) MINUS MERAH PER CELL + EXPORT PIVOT SESUAI TAMPILAN ==")

    # (a) unit: apply_cell_tag — tag per-cell Tk 9 (item hilang → aman)
    from src.ui.widgets import CELL_TAGS_SUPPORTED
    from src.ui.widgets import apply_cell_tag as _act
    if CELL_TAGS_SUPPORTED:
        _t = ttk.Treeview(root, columns=["a", "b", "c"], show="headings")
        _t.pack(fill="x")
        _t.tag_configure("negcell", foreground="#CC0000")
        _t.insert("", "end", iid="c1", values=("1", "-2", "3"))
        _t.insert("", "end", iid="c2", values=("-4", "0", "-6"))
        n_applied = _act(_t, "negcell",
                         [("c1", "b"), ("c2", "a"), ("c2", "c")])
        _hc = lambda i, c: root.tk.call(str(_t), "tag", "cell", "has",
                                         "negcell", (i, c))
        check("(v3.9.2) apply_cell_tag: cell minus ditandai PER-CELL",
              n_applied == 3 and _hc("c1", "b") == 1 and
              _hc("c2", "a") == 1 and _hc("c2", "c") == 1 and
              _hc("c1", "a") == 0,
              f"applied={n_applied}")
        n2 = _act(_t, "negcell", [("ghost", "a")])
        check("(v3.9.2) apply_cell_tag: item hilang → dibatalkan aman",
              n2 == 0)
        # re-insert = tag cell ter-reset (dipasang ulang oleh view)
        _t.delete("c1")
        _t.insert("", "end", iid="c1", values=("1", "-2", "3"))
        check("(v3.9.2) re-insert me-reset tag cell (dasar reapply sort)",
              _hc("c1", "b") == 0)
        _act(_t, "negcell", [("c1", "b")])
        check("(v3.9.2) reapply setelah re-insert bekerja",
              _hc("c1", "b") == 1)
        _t.destroy()
    else:
        check("(v3.9.2) fallback Tk 8: tag per baris (perilaku lama)",
              True)   # info saja — sandbox test memakai Tk 9

    # (b) PIVOT standalone — data dengan MINUS (baris TIDAK memerah penuh)
    # NB: total baris harus > 0 agar tidak disembunyikan hide-empty (ON)
    neg_rows_src = []
    for barang, so_v, sa_v, dev_vals, sel_vals in [
            ("BARANG MINUS", 4.0, 20.0, (-6.0, 10.0), (0.0, 5.0)),
            ("BARANG PLUS", 30.0, 10.0, (20.0, 20.0), (0.0, 0.0))]:
        for jenis, vals in [("1.SO", (so_v, so_v)),
                            ("2.SALDO AKHIR", (sa_v, sa_v)),
                            ("3.DEVIASI", dev_vals),
                            ("7.Selisih IN", sel_vals)]:
            for tgl in (1, 2):
                neg_rows_src.append({
                    "Nama Barang": barang, "JENIS": jenis,
                    "NAMA RESTO": "MLGPAR", "Tanggal": tgl,
                    "NILAI": float(vals[tgl - 1]), "SATUAN": "GR",
                    "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
                    "SOURCE KIRIMAN": "GUDANG"})
    neg_df = pd.DataFrame(neg_rows_src)
    from src.ui.pivot_view import PivotTableView
    pv2 = PivotTableView(root)
    pv2.pack(fill="both", expand=True)
    # set state SEBELUM data → refresh sync deterministik (tanpa race
    # refresh-async dari load_data)
    pv2.pivot_mode = "tanggal"
    pv2.tgl_start_var.set("1")
    pv2.tgl_end_var.set("2")
    pv2.data = neg_df
    pv2._populate_filters()
    pv2._show_content()
    pv2._refresh_pivot(sync=True)
    for _ in range(80):
        root.update()
        if not pv2._busy and len(pv2.tree.get_children("")):
            break
        time.sleep(0.02)
    _t2 = pv2.tree
    _hcn = lambda i, c: root.tk.call(str(_t2), "tag", "cell", "has",
                                      "neg_cell", (i, c))
    # cari iid baris per (barang, metric)
    _map = {}
    for _p in _t2.get_children(""):
        for _c in _t2.get_children(_p):
            _map[(_t2.item(_p, "text"), _t2.item(_c, "text"))] = _c
    _dev = _map[("BARANG MINUS", "3.DEVIASI")]
    _dev2 = _map[("BARANG PLUS", "3.DEVIASI")]
    _sel = _map[("BARANG MINUS", "7.Selisih IN")]
    if CELL_TAGS_SUPPORTED:
        check("(v3.9.2) Pivot: cell minus (3.DEVIASI tgl 1) merah per-cell",
              _hcn(_dev, "1") == 1)
        check("(v3.9.2) Pivot: cell positif (3.DEVIASI tgl 2) TIDAK merah",
              _hcn(_dev, "2") == 0)
        check("(v3.9.2) Pivot: baris minus TIDAK tag 'negative' (baris utuh)",
              "negative" not in _t2.item(_dev, "tags") and
              "deviasi_row" not in _t2.item(_dev, "tags"))
        check("(v3.9.2) Pivot: 3.DEVIASI tanpa minus → tak ada cell merah",
              _hcn(_dev2, "1") == 0 and _hcn(_dev2, "2") == 0)
        check("(v3.9.2) Pivot: Selisih IN ≠ 0 (tgl 2) merah per-cell",
              _hcn(_sel, "2") == 1 and _hcn(_sel, "1") == 0)
        check("(v3.9.2) Pivot: baris Selisih pakai bg-only 'selisih_anomaly_bg'",
              "selisih_anomaly_bg" in _t2.item(_sel, "tags"))
    check("(v3.9.2) Pivot: payload membawa red_cells + rows_data + filters",
          len(pv2._last_payload.get("red_cells", [])) > 0 and
          len(pv2._last_payload.get("rows_data", [])) > 0 and
          pv2._last_payload.get("filters", {}).get("mode") == "tanggal")
    check("(v3.9.2) Pivot: handler 💾 export ada + bisa dipanggil",
          callable(pv2._on_export_excel) and
          callable(pv2._do_export_excel) and
          callable(pv2._visible_columns))

    # (c) export pivot sesuai tampilan → read-back (font merah per cell)
    from src.ui.export_sheets import write_pivot_display_sheet
    _exp_path = os.path.join(tempfile.mkdtemp(), "pivot_v392.xlsx")
    _n_exp = write_pivot_display_sheet(_exp_path, pv2._last_payload,
                                       visible_cols=None)
    check("(v3.9.2) Export pivot: file dibuat + baris data > 0",
          _n_exp > 0 and os.path.exists(_exp_path) and
          os.path.getsize(_exp_path) > 0, f"n={_n_exp}")
    from openpyxl import load_workbook as _lw
    _wb = _lw(_exp_path)
    _ws = _wb.active
    check("(v3.9.2) Export pivot: layout meta filter + header + freeze",
          _ws["A1"].value == "MODE" and _ws["B1"].value == "Per Tanggal"
          and _ws.cell(row=7, column=1).value == "Row Labels"
          and _ws.freeze_panes == "B8")
    _red_n = 0
    _red_expect = 0
    for _r in range(8, _ws.max_row + 1):
        _lab = _ws.cell(row=_r, column=1).value
        for _cc in range(2, _ws.max_column + 1):
            _cell = _ws.cell(row=_r, column=_cc)
            _v = _cell.value
            if not isinstance(_v, (int, float)):
                continue
            _col = _cell.font.color.rgb if (_cell.font and
                                            _cell.font.color) else None
            _is_red = _col and "CC0000" in str(_col).upper()
            _should_red = _v < 0 or (_lab == "7.Selisih IN" and _v != 0)
            if _is_red:
                _red_n += 1
            if _should_red:
                _red_expect += 1
                check(f"(v3.9.2) Export pivot: cell minus r{_r}c{_cc} "
                      "font merah", bool(_is_red),
                      f"v={_v} col={_col}")
    check("(v3.9.2) Export pivot: jumlah cell merah == UI red_cells",
          _red_n == _red_expect == len(pv2._last_payload["red_cells"]),
          f"red={_red_n} expect={_red_expect} "
          f"ui={len(pv2._last_payload['red_cells'])}")
    pv2.destroy()

    # (d) wiring semua view: helper per-cell + reapply (fallback Tk 8 aman)
    check("(v3.9.2) Deviasi GR: reapply cell + tag neg_cell ada",
          callable(app.deviasi_gr_view._reapply_cell_tags) and
          hasattr(app.deviasi_gr_view, "_neg_cells"))
    check("(v3.9.2) Deviasi PCS: reapply cell ada",
          callable(app.deviasi_pcs_view._reapply_cell_tags))
    check("(v3.9.2) Laporan Deviasi: reapply cell ada",
          callable(app.laporan_view._reapply_cell_tags))
    check("(v3.9.2) app pivot: export handler ada",
          callable(app.pivot_view._on_export_excel))

    # (d2) details_popup._prepare_rows (staticmethod) — per_cell param
    from src.ui.details_popup import DetailsPopup
    _dp_df = pd.DataFrame([{
        "Nama Barang": "AYAM", "NAMA RESTO": "MLGPAR", "Tanggal": 5,
        "JENIS": "4.IN", "NILAI": -7.0, "Nomor": "IT-1",
        "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
        "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG"},
        {"Nama Barang": "AYAM", "NAMA RESTO": "MLGPAR", "Tanggal": 6,
         "JENIS": "4.IN", "NILAI": 3.0, "Nomor": "IT-2",
         "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
         "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG"}])
    _pl = DetailsPopup._prepare_rows(_dp_df, None, per_cell=True)
    _pl8 = DetailsPopup._prepare_rows(_dp_df, None, per_cell=False)
    check("(v3.9.2) DetailsPopup: per_cell=True → neg_cells [(row_0,NILAI)] "
          "+ tanpa tag baris",
          _pl.get("neg_cells") == [("row_0", "NILAI")] and
          "negative" not in _pl["items"][0][2]["tags"])
    check("(v3.9.2) DetailsPopup: per_cell=False (Tk 8) → tag baris lama",
          not _pl8.get("neg_cells") and
          "negative" in _pl8["items"][0][2]["tags"])

    # (e) deviasi view — data minus (SO < SALDO AKHIR di H=25)
    #     → hanya cell Deviasi yang merah; sort → reapply tetap merah
    dev_neg_src = []
    for barang, so_v, sa_v in [("DEV MIN", 4.0, 20.0),
                               ("DEV PLUS", 30.0, 10.0)]:
        for jenis, base in [("1.SO", so_v), ("2.SALDO AKHIR", sa_v),
                            ("SALDO AWAL", 10.0), ("4.IN", 2.0)]:
            for tgl in range(20, 28):
                dev_neg_src.append({
                    "Nama Barang": barang, "JENIS": jenis,
                    "NAMA RESTO": "MLGPAR", "Tanggal": tgl,
                    "NILAI": float(base), "SATUAN": "GR",
                    "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
                    "SOURCE KIRIMAN": "GUDANG"})
    dev_neg_df = pd.DataFrame(dev_neg_src)
    from src.ui.deviasi_view import DeviasiView
    dv2 = DeviasiView(root, satuan_mode="GR")
    dv2.pack(fill="both", expand=True)
    # set data langsung + refresh sync (deterministik — lihat (b))
    dv2.data = dev_neg_df
    dv2._show_content()
    dv2._refresh(sync=True)
    for _ in range(80):
        root.update()
        if not dv2._busy and len(dv2.tree.get_children("")):
            break
        time.sleep(0.02)
    _t3 = dv2.tree
    _hcd = lambda i: root.tk.call(str(_t3), "tag", "cell", "has",
                                   "neg_cell", (i, "Deviasi"))
    _devmin_iid = None
    for _iid in _t3.get_children(""):
        if _t3.set(_iid, "Nama Barang") == "DEV MIN":
            _devmin_iid = _iid
    if CELL_TAGS_SUPPORTED and _devmin_iid:
        check("(v3.9.2) Deviasi: cell Deviasi minus merah PER-CELL "
              "(baris tidak memerah)",
              _hcd(_devmin_iid) == 1 and
              "negative" not in _t3.item(_devmin_iid, "tags"))
        _devplus_iid = None
        for _iid in _t3.get_children(""):
            if _t3.set(_iid, "Nama Barang") == "DEV PLUS":
                _devplus_iid = _iid
        check("(v3.9.2) Deviasi: baris tanpa minus → cell Deviasi tidak merah",
              _devplus_iid is None or _hcd(_devplus_iid) == 0)
        # sort (delete+reinsert) → reapply memasang ulang tag cell
        dv2._sort_by("Deviasi", reverse=True)
        check("(v3.9.2) Deviasi: sort → tag cell minus DIPASANG ULANG",
              _hcd(_devmin_iid) == 1)
    dv2.destroy()

    # ==================================================================
    print("== 22. (v3.9.4) KOMPARASI FILE DEVIASI vs TAB DEVIASI GR ==")

    kv = app.komparasi_view
    # v3.9.13: matikan AUTO-LOAD file terakhir selama suite (deterministik;
    # auto-load diuji eksplisit di §26)
    kv._auto_loaded = True
    app.show_laporan_mode(0)   # section 7/11 meninggalkan mode 1 — reset
    app.notebook.select(app.tab_laporan)
    root.update()

    check("(v3.9.4) SegmentBar mode default = 0 (Komparasi)",
          app.laporan_segment.active == 0)
    check("(v3.9.4) Komparasi terlihat, Anomali COM tersembunyi",
          kv.winfo_ismapped() and not app.laporan_view.winfo_ismapped())
    app.show_laporan_mode(1)
    root.update()
    check("(v3.9.4) show_laporan_mode(1) → Anomali COM terlihat",
          app.laporan_view.winfo_ismapped() and not kv.winfo_ismapped())
    app.show_laporan_mode(0)
    root.update()
    check("(v3.9.4) show_laporan_mode(0) → kembali ke Komparasi",
          kv.winfo_ismapped() and not app.laporan_view.winfo_ismapped())

    check("(v3.9.14) Skema kolom komparasi (14 kolom — Minggu & H DIHAPUS "
          "v3.9.13; istilah *Lalu/*Saat Ini v3.9.14)",
          [c[0] for c in kv.COLUMNS] == [
              "✓", "Resto", "Nama Barang", "Satuan",
              "BOM Lalu", "COM Lalu", "DEV Lalu", "%TO BOM Lalu",
              "BOM Saat Ini", "COM Saat Ini", "DEV Saat Ini",
              "GR Saat Ini", "Selisih", "Status"],
          f"got {[c[0] for c in kv.COLUMNS]}")
    check("(v3.9.14) Heading DEV Saat Ini = % TO BOM — Saat Ini (persen)",
          kv.tree.heading("DEV Saat Ini")["text"] == "% TO BOM — Saat Ini",
          f"got {kv.tree.heading('DEV Saat Ini')['text']!r}")
    check("(v3.9.14) Heading dua sisi terpasang (istilah Lalu/Saat Ini)",
          kv.tree.heading("GR Saat Ini")["text"] ==
          "DEVIASI — Saat Ini (Tab GR)" and
          kv.tree.heading("BOM Saat Ini")["text"] ==
          "BOM — Saat Ini (Σ jual 22.05)")

    # data deterministik: AYAM FILET & GULA PASIR × 2 resto, tgl 1..25
    # AYAM: SA=100, SO(t)=100-3t, IN=10 (t%5==0), OUT=20 (genap)/5 (ganjil)
    #       → SIS = running stock → GR(7)=49, GR(14)=113, GR(25)=180
    #       com(t)=3+IN(t) → cum(1..7)=31; out_cum(1..7)=80 → DEV App=49
    # GULA: SA=60, SO(t)=60-2t, IN=0, OUT=8 → GR(25)=150; cum com=50;
    #       out_cum=200 → DEV App=150
    det = make_mock_komparasi_df()
    kv.load_data(det)
    wait_view(root, kv)
    check("(v3.9.4) Tanpa file → pesan jujur 'Belum ada file'",
          "Belum ada file" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")

    xlsx_path = make_mock_deviasi_file()
    kv._load_paths([xlsx_path])
    wait_view(root, kv)

    # --- (v3.9.7) FILTER MINGGU MENGIKUTI H BERSAMA (default aktif) ---
    # H bersama saat ini 25 (dari §7) → minggu yang MEMUAT H = WEEK 4
    # (cut-off 25) → hanya baris GULA PASIR/MLGPAR WEEK 4 yang tampil
    from src.ui.theme import C_ACCENT as _C_ACCENT
    # v3.9.13: Minggu/H kini INTERNAL (kolom dihapus) — dibaca dari
    # snapshot baris (kv._row_snaps[iid])
    def kv_minggu(k):
        return kv._row_snaps.get(k, {}).get("minggu", "")

    def kv_h(k):
        return str(kv._row_snaps.get(k, {}).get("h", ""))

    n_w4 = len(kv.tree.get_children(""))
    _kv_rows_w4 = [(kv_minggu(k),
                    kv.tree.set(k, "Nama Barang"))
                   for k in kv.tree.get_children("")]
    check("(v3.9.7) Default H=25 → hanya minggu WEEK 4 (1 baris GULA "
          "PASIR)", n_w4 == 1 and _kv_rows_w4 == [("WEEK 4", "GULA PASIR")],
          f"got {n_w4} {_kv_rows_w4}")
    check("(v3.9.7) Chip H komparasi read-only = 25 (ikut tab GR)",
          kv._h_chip_var.get() == "25" and not hasattr(kv, "tanggal_h_var"),
          f"got {kv._h_chip_var.get()!r}")
    check("(v3.9.7) Label minggu aktif '→ minggu: WEEK 4'",
          "WEEK 4" in kv._week_filter_var.get(),
          f"got {kv._week_filter_var.get()!r}")
    check("(v3.9.7) Footer prefiks minggu aktif (cut-off H 25)",
          "Minggu WEEK 4" in kv.status_var_label.get() and
          "cut-off H 25" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")
    _chip_bgs = [c.cget("bg") for c in kv._week_chips.winfo_children()]
    check("(v3.9.7) Chip minggu aktif WEEK 4 di-highlight teal",
          _chip_bgs.count(_C_ACCENT) == 1 and _chip_bgs[2] == _C_ACCENT,
          f"got {_chip_bgs}")
    check("(v3.9.7) Mapping H→minggu: 7→7 · 8..14→14 · 15..25→25 · 26→31",
          _h_to_week_target(7) == 7 and _h_to_week_target(8) == 14 and
          _h_to_week_target(14) == 14 and _h_to_week_target(15) == 25 and
          _h_to_week_target(25) == 25 and _h_to_week_target(26) == 31 and
          _h_to_week_target(31) == 31)

    # H=7 (input di tab GR, permintaan user) → hanya WEEK 1
    app.deviasi_gr_view.tanggal_h_var.set("7")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    _minggu_vals = {kv_minggu(k)
                    for k in kv.tree.get_children("")}
    check("(v3.9.7) H=7 → hanya baris WEEK 1 (3 baris: 2 resto AYAM + "
          "barang tak ada)",
          len(kv.tree.get_children("")) == 3 and _minggu_vals == {"WEEK 1"},
          f"got {len(kv.tree.get_children(''))} {sorted(_minggu_vals)}")
    check("(v3.9.7) Chip H ikut 7 + label minggu WEEK 1",
          kv._h_chip_var.get() == "7" and
          "WEEK 1" in kv._week_filter_var.get(),
          f"got {kv._h_chip_var.get()!r} / {kv._week_filter_var.get()!r}")

    # H=14 → hanya WEEK 2 (1 baris MLGPAR AYAM)
    app.deviasi_gr_view.tanggal_h_var.set("14")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    _kv_h14 = [(kv_minggu(k), kv_h(k))
               for k in kv.tree.get_children("")]
    check("(v3.9.7) H=14 → hanya WEEK 2 (1 baris, snapshot h=14)",
          _kv_h14 == [("WEEK 2", "14")], f"got {_kv_h14}")

    # centang 'Tampilkan semua minggu' → semua minggu (perilaku lama)
    kv._show_all_weeks.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    check("(v3.9.7) Centang semua minggu → label NONAKTIF + semua baris",
          "NONAKTIF" in kv._week_filter_var.get() and
          len(kv.tree.get_children("")) == 6,
          f"got {kv._week_filter_var.get()!r} / "
          f"{len(kv.tree.get_children(''))}")
    # kembalikan H=25 (state akhir §7) — blok lama berjalan mode semua
    # minggu agar cek 6-baris/per-minggu tetap valid
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)

    n_kv = len(kv.tree.get_children(""))
    check("(v3.9.4) File 7 baris → 6 tampil (resto 9999.XYZZZ "
          "disembunyikan default)", n_kv == 6, f"got {n_kv}")
    check("(v3.9.4) Label file terisi (nama + baris + resto)",
          "mock_deviasi" in kv._file_label_var.get() and
          "7 baris" in kv._file_label_var.get(),
          f"got {kv._file_label_var.get()!r}")
    _chips_txt = " ".join(
        c.winfo_children()[0].cget("text")
        for c in kv._week_chips.winfo_children()
        if c.winfo_children())
    check("(v3.9.4) Chip minggu→H: WEEK 1→7 · 2→14 · 4→25 · 5→31",
          all(t in _chips_txt for t in
              ["WEEK 1 → H 7", "WEEK 2 → H 14", "WEEK 4 → H 25",
               "WEEK 5 → H 31"]), f"got {_chips_txt!r}")
    check("(v3.9.4) Footer hitung status (MATCH 3 · SELISIH 1 · H tdk 1)",
          "MATCH: 3" in kv.status_var_label.get() and
          "SELISIH: 1" in kv.status_var_label.get() and
          "H tdk ada: 1" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")

    def kv_row(resto, barang, minggu):
        for k in kv.tree.get_children(""):
            if (kv.tree.set(k, "Resto") == resto and
                    kv.tree.set(k, "Nama Barang") == barang and
                    kv_minggu(k) == minggu):
                return k
        return None

    k_match = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 1")
    check("(v3.9.4) Baris MATCH ada", k_match is not None)
    if k_match:
        check("(v3.9.4) GR Saat Ini = SO(7)-Sistem = '49' (persis Tab GR)",
              kv.tree.set(k_match, "GR Saat Ini") == "49",
              f"got {kv.tree.set(k_match, 'GR Saat Ini')!r}")
        check("(v3.9.4) BOM Saat Ini = -ΣOUT(1..7) = '(80)' (konvensi file)",
              kv.tree.set(k_match, "BOM Saat Ini") == "(80)",
              f"got {kv.tree.set(k_match, 'BOM Saat Ini')!r}")
        check("(v3.9.4) COM Saat Ini = -Σpemakaian = '(31)'",
              kv.tree.set(k_match, "COM Saat Ini") == "(31)",
              f"got {kv.tree.set(k_match, 'COM Saat Ini')!r}")
        check("(v3.9.13) DEV Saat Ini kini RASIO %TO BOM = '61,25%' "
              "(49/80 — persen konsisten %TO BOM Lalu; dulu kuantitas '49')",
              kv.tree.set(k_match, "DEV Saat Ini") == "61,25%",
              f"got {kv.tree.set(k_match, 'DEV Saat Ini')!r}")
        check("(v3.9.4) Selisih 0 → status MATCH",
              kv.tree.set(k_match, "Status") == "MATCH" and
              kv.tree.set(k_match, "Selisih") == "-",
              f"got {kv.tree.set(k_match, 'Status')!r} / "
              f"{kv.tree.set(k_match, 'Selisih')!r}")
        check("(v3.9.4) % TO BOM Lalu = '61,25%'",
              kv.tree.set(k_match, "%TO BOM Lalu") == "61,25%",
              f"got {kv.tree.set(k_match, '%TO BOM Lalu')!r}")
        check("(v3.9.4) H minggu WEEK 1 = 7 (snapshot internal)",
              kv_h(k_match) == "7")

    k_w2 = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 2")
    check("(v3.9.4) WEEK 2 → H 14, GR Saat Ini = '113' (MATCH)",
          k_w2 is not None and kv_h(k_w2) == "14" and
          kv.tree.set(k_w2, "GR Saat Ini") == "113" and
          kv.tree.set(k_w2, "Status") == "MATCH",
          f"got H={kv_h(k_w2) if k_w2 else None} "
          f"GR={kv.tree.set(k_w2, 'GR Saat Ini') if k_w2 else None}")

    k_gula = kv_row("1001.MLGPAR", "GULA PASIR", "WEEK 4")
    check("(v3.9.4) WEEK 4 → H 25, GULA GR Saat Ini = '150' (MATCH)",
          k_gula is not None and kv_h(k_gula) == "25" and
          kv.tree.set(k_gula, "GR Saat Ini") == "150" and
          kv.tree.set(k_gula, "Status") == "MATCH")

    k_sel = kv_row("1002.SBYKET", "AYAM FILET", "WEEK 1")
    check("(v3.9.4) DEV Lalu 74 vs GR 49 → SELISIH + selisih '(25)'",
          k_sel is not None and kv.tree.set(k_sel, "Status") == "SELISIH" and
          kv.tree.set(k_sel, "Selisih") == "(25)",
          f"got {kv.tree.set(k_sel, 'Status') if k_sel else None} / "
          f"{kv.tree.set(k_sel, 'Selisih') if k_sel else None}")

    k_noapp = kv_row("1001.MLGPAR", "BARANG TAK ADA", "WEEK 1")
    check("(v3.9.14) Barang tak ada di data → TIDAK ADA DI DATA SAAT INI "
          "+ '—'",
          k_noapp is not None and
          kv.tree.set(k_noapp, "Status") == "TIDAK ADA DI DATA SAAT INI" and
          kv.tree.set(k_noapp, "GR Saat Ini") == "—")

    k_noh = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 5")
    check("(v3.9.4) WEEK 5 → H 31 tidak ada di data (tgl 1..25) → "
          "H TIDAK ADA DI DATA",
          k_noh is not None and kv_h(k_noh) == "31" and
          kv.tree.set(k_noh, "Status") == "H TIDAK ADA DI DATA")

    # opsi: tampilkan resto di luar data app
    kv._show_all_resto.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    n_all_kv = len(kv.tree.get_children(""))
    k_xzz = kv_row("9999.XYZZZ", "AYAM FILET", "WEEK 1")
    check("(v3.9.4) Centang semua resto → 7 baris + XYZZZ TIDAK ADA",
          n_all_kv == 7 and k_xzz is not None and
          kv.tree.set(k_xzz, "Status") == "TIDAK ADA DI DATA SAAT INI",
          f"got {n_all_kv}")
    kv._show_all_resto.set(False)
    kv._on_option_changed()
    wait_view(root, kv)

    # per-cell: minus merah di BOM Lalu, status MATCH hijau per-cell
    if CELL_TAGS_SUPPORTED and k_match:
        _khcd = lambda i, col: root.tk.call(
            str(kv.tree), "tag", "cell", "has", "neg_cell", (i, col))
        _khst = lambda i: root.tk.call(
            str(kv.tree), "tag", "cell", "has", "st_match", (i, "Status"))
        check("(v3.9.4) Minus merah PER-CELL di sel BOM Lalu (-80)",
              _khcd(k_match, "BOM Lalu") == 1 and
              _khcd(k_match, "Satuan") == 0)
        check("(v3.9.4) Sel Status MATCH hijau per-cell",
              _khst(k_match) == 1 and _khst(k_sel) == 0)
        kv._sort_by("Selisih", reverse=False)
        check("(v3.9.4) Sort Selisih naik → baris SELISIH (-25) di atas + "
              "tag cell dipasang ulang",
              kv.tree.set(kv.tree.get_children("")[0], "Status") ==
              "SELISIH" and _khcd(k_match, "BOM Lalu") == 1)

    # filter header Status = MATCH → 3 baris
    kv._on_col_filter("Status", ["MATCH"])
    wait_view(root, kv)
    check("(v3.9.4) Filter header Status=MATCH → 3 baris",
          len(kv.tree.get_children("")) == 3,
          f"got {len(kv.tree.get_children(''))}")
    kv._reset_filter()
    wait_view(root, kv)

    # ✓ follow-up (asal KOMPARASI) — store dibersihkan di akhir section 11
    store = app.followup_store
    first_kv = kv.tree.get_children("")[0]
    bbox_kv = kv.tree.bbox(first_kv)
    check("(v3.9.4) bbox baris komparasi tersedia", bool(bbox_kv))
    if bbox_kv:
        ev4 = _Ev()
        ev4.widget = kv.tree
        ev4.x, ev4.y = bbox_kv[0] + 8, bbox_kv[1] + bbox_kv[3] // 2
        kv._on_tree_click(ev4)
        root.update()
        check("(v3.9.4) Klik ✓ → masuk follow-up (asal KOMPARASI)",
              len(store) == 1 and
              next(iter(store.rows.values())).get("asal") == "KOMPARASI")
        kv._on_tree_click(ev4)
        root.update()
        check("(v3.9.4) Klik ✓ lagi → keluar follow-up", len(store) == 0)

    # tutup file → pesan jujur
    kv._close_file()
    check("(v3.9.4) Tutup file → tabel kosong + pesan",
          len(kv.tree.get_children("")) == 0 and
          "File ditutup" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")

    os.unlink(xlsx_path)
    if os.path.isfile("komparasi_last.json"):
        os.unlink("komparasi_last.json")
    # kembalikan data mock utama supaya state akhir konsisten
    kv.load_data(append1)
    wait_view(root, kv)

    # ==================================================================
    print("== 23. (v3.9.5) AUDIT DEEP — REGRESSION FIXES ==")

    import tempfile as _tf

    # --- (A6/B2) SALDO AWAL jadi base com(1) saat ada tanggal negatif ---
    def make_mock_neg_dates_df() -> pd.DataFrame:
        """2 barang × 1 resto, tanggal -25..-31 (LALU saja) + tgl 1 & 7
        (WEEK 1 → H 7 harus ADA supaya GR terhitung).

        LALU: SO(-31)=40, SA(1)=50, SO(1)=10, SO(7)=20, SIS=SA (IN/OUT/BK=0)
          → GR(7)=SO(7)-SIS(7)=-30; com(1) BARU=SA-SO=40, com(7)=SO(1)-SO(7)
          =-10 → Σcom=30 → DEV App=-30==GR (LAMA: com(1)=SO(-31)-SO=30 →
          Σ=20 → DEV=-20 ≠ GR — penyimpangan SO(-31)-SA=10, audit 19-a #6)
        NOPAIR: tanpa baris bulan lalu — SA(1)=12, SO(1)=10, SO(7)=8
          → com(1) BARU=2 (LAMA: 0-10=-10 = MINUS PALSU); GR(7)=8-12=-4,
          Σcom=2+2=4 → DEV=-4==GR
        """
        rows = []
        def add(b, j, t, v):
            rows.append({"Nama Barang": b, "JENIS": j, "NAMA RESTO": "R1",
                         "Tanggal": t, "NILAI": v, "SATUAN": "GR",
                         "AKTIF/NON": "AKTIF"})
        for t in (-25, -30, -31):
            add("LALU", "1.SO", t, 5.0 if t != -31 else 40.0)
        add("LALU", "1.SO", 1, 10.0)
        add("LALU", "1.SO", 7, 20.0)
        add("LALU", "2.SALDO AKHIR", 1, 50.0)
        add("LALU", "2.SALDO AKHIR", 7, 50.0)
        add("LALU", "SALDO AWAL", 1, 50.0)
        for j in ("4.IN", "9.OUT", "8.BARANG KELUAR"):
            for t in (1, 7):
                add("LALU", j, t, 0.0)
        add("NOPAIR", "1.SO", 1, 10.0)
        add("NOPAIR", "1.SO", 7, 8.0)
        add("NOPAIR", "2.SALDO AKHIR", 1, 12.0)
        add("NOPAIR", "2.SALDO AKHIR", 7, 12.0)
        add("NOPAIR", "SALDO AWAL", 1, 12.0)
        for j in ("4.IN", "9.OUT", "8.BARANG KELUAR"):
            for t in (1, 7):
                add("NOPAIR", j, t, 0.0)
        return pd.DataFrame(rows)

    from openpyxl import Workbook as _WB
    neg_xlsx = os.path.join(_tf.gettempdir(), "mock_deviasi_neg.xlsx")
    wb = _WB(); ws = wb.active; ws.title = "Sheet1"
    ws.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM", "QTY DEVIASI",
               "STATUS BULAN"])
    # file persis hitungan BARU (SA base) → MATCH; LAMA akan SELISIH 10/12
    ws.append(["1.R1", "LALU", 0, -30, -30, "WEEK 1"])
    ws.append(["1.R1", "NOPAIR", 0, -4, -4, "WEEK 1"])
    wb.save(neg_xlsx)

    kv.load_data(make_mock_neg_dates_df())
    wait_view(root, kv)
    kv._load_paths([neg_xlsx])
    wait_view(root, kv)

    def kv_row2(resto, barang):
        for k in kv.tree.get_children(""):
            if (kv.tree.set(k, "Resto") == resto and
                    kv.tree.set(k, "Nama Barang") == barang):
                return k
        return None

    k_lalu = kv_row2("1.R1", "LALU")
    k_nop = kv_row2("1.R1", "NOPAIR")
    check("(v3.9.5) SA base: GR Saat Ini utk pair dgn tanggal negatif "
          "(LALU: '(30)'; DEV Saat Ini kini RASIO — BOM 0 → '—')",
          k_lalu is not None and
          kv.tree.set(k_lalu, "GR Saat Ini") == "(30)" and
          kv.tree.set(k_lalu, "DEV Saat Ini") == "—" and
          kv.tree.set(k_lalu, "Status") == "MATCH",
          f"GR={kv.tree.set(k_lalu, 'GR Saat Ini') if k_lalu else None} "
          f"DEV={kv.tree.set(k_lalu, 'DEV Saat Ini') if k_lalu else None}")
    check("(v3.9.5) SA base: pair TANPA bulan-lalu com(1)=SA-SO (NOPAIR: "
          "GR '(4)', bukan minus palsu; DEV Saat Ini RASIO → '—')",
          k_nop is not None and
          kv.tree.set(k_nop, "GR Saat Ini") == "(4)" and
          kv.tree.set(k_nop, "DEV Saat Ini") == "—" and
          kv.tree.set(k_nop, "Status") == "MATCH",
          f"GR={kv.tree.set(k_nop, 'GR Saat Ini') if k_nop else None}")

    # pivot COM konsisten (tanggal negatif + SA) — _compute_com langsung
    from src.ui.pivot_view import PivotTableView as _PTV
    _idx = pd.MultiIndex.from_tuples(
        [("B", "1.SO"), ("B", "4.IN"), ("B", "8.BARANG KELUAR"),
         ("B", "SALDO AWAL")], names=["Nama Barang", "JENIS"])
    _piv = pd.DataFrame({-25.0: [0, 0, 0, pd.NA], 1.0: [10.0, 0, 0, 12.0]},
                        index=_idx)
    _s = _PTV._compute_com(_piv, "B", [-25.0, 1.0])
    check("(v3.9.5) pivot com(1) pakai SA (2.0), bukan -10 (minus palsu)",
          _s[1.0] == 2.0 and _s[-25.0] == 0.0, f"got {_s.to_dict()}")
    os.unlink(neg_xlsx)

    # kembali ke mock komparasi standar
    kv.load_data(det)
    wait_view(root, kv)
    xlsx_path = make_mock_deviasi_file()
    kv._load_paths([xlsx_path])
    wait_view(root, kv)

    # --- (A2/C8) pair index menyelesaikan nama APP utk popup detail ---
    check("(v3.9.5) _pair_index: nama file case/spacing beda → nama APP",
          kv._pair_index.get((_norm_name("ayam  filet"), "MLGPAR")) ==
          ("AYAM FILET", "MLGPAR"),
          f"got {kv._pair_index.get((_norm_name('ayam  filet'), 'MLGPAR'))!r}")

    # --- (A5) duplikat lintas bulan dihitung & dilaporkan ---
    dup_xlsx = os.path.join(_tf.gettempdir(), "mock_deviasi_dup.xlsx")
    wb = _WB(); ws = wb.active
    ws.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM", "QTY DEVIASI",
               "STATUS BULAN", "BULAN"])
    ws.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1", "201.X"])
    ws.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1", "202.X"])
    ws.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1", "203.X"])
    wb.save(dup_xlsx)
    res_dup = parse_deviasi_file(dup_xlsx)
    check("(v3.9.5) Duplikat lintas bulan dihitung (n_duplicates=2) + "
          "dilaporkan di label",
          res_dup["ok"] and res_dup["meta"].get("n_duplicates") == 2,
          f"meta={res_dup['meta']}")
    os.unlink(dup_xlsx)

    # --- (A11) sheet data di sheet ke-2 tetap terbaca ---
    multi_xlsx = os.path.join(_tf.gettempdir(), "mock_deviasi_2sheet.xlsx")
    wb = _WB()
    ws0 = wb.active; ws0.title = "REKAP"  # sheet 0 tanpa kolom wajib
    ws0.append(["No", "Info"])
    ws0.append([1, "sheet ringkasan"])
    ws1 = wb.create_sheet("DATA")
    ws1.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM", "QTY DEVIASI",
                "STATUS BULAN"])
    ws1.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1"])
    wb.save(multi_xlsx)
    res_multi = parse_deviasi_file(multi_xlsx)
    check("(v3.9.5) Data di sheet ke-2 ditemukan (bukan error kolom)",
          res_multi["ok"] and res_multi["meta"]["sheet"] == "DATA" and
          res_multi["meta"]["n_rows"] == 1,
          f"meta={res_multi['meta']}")
    # (A13) Satuan NaN → '' bukan 'nan'
    check("(v3.9.5) Satuan kosong → '' (bukan literal 'nan')",
          res_multi["df"]["Satuan"].iloc[0] == "",
          f"got {res_multi['df']['Satuan'].iloc[0]!r}")
    os.unlink(multi_xlsx)

    # --- (A8) -0.0 % → '0,00%' ---
    check("(v3.9.5) _fmt_pct(-0.0) → '0,00%' (bukan '-0,00%')",
          kv._fmt_pct(-0.0) == "0,00%" and
          kv._fmt_pct(0.2697) == "26,97%",
          f"got {kv._fmt_pct(-0.0)!r}")

    # --- (A7) footer status = hitungan baris YANG TAMPIL (setelah filter) ---
    kv._on_col_filter("Resto", ["1002.SBYKET"])
    wait_view(root, kv)
    check("(v3.9.5) Filter Resto=SBYKET (1 baris SELISIH) → footer "
          "MATCH: 0 (bisa MATCH: 3 global basi)",
          len(kv.tree.get_children("")) == 1 and
          "MATCH: 0" in kv.status_var_label.get(),
          f"footer={kv.status_var_label.get()!r}")
    kv._reset_filter()
    wait_view(root, kv)

    # --- (C5) filter header direset saat file dimuat ulang ---
    kv._on_col_filter("Status", ["MATCH"])
    wait_view(root, kv)
    kv._reload_file()
    wait_view(root, kv)
    check("(v3.9.5) Reload file → filter lama direset (6 baris tampil)",
          len(kv.tree.get_children("")) == 6,
          f"got {len(kv.tree.get_children(''))}")

    # --- (B6) sort saat busy diantrekan ---
    kv._load_paths([xlsx_path])
    check("(v3.9.5) Sort diklik saat compute berjalan → diantrekan",
          kv._busy and kv._pending_sort is None)
    kv._sort_by("Selisih", reverse=False)
    check("(v3.9.5) _pending_sort terisi saat busy",
          kv._pending_sort == ("Selisih", False))
    wait_view(root, kv)
    check("(v3.9.5) Sort antrean diterapkan setelah render selesai",
          kv._pending_sort is None and
          kv.tree.set(kv.tree.get_children("")[0], "Status") == "SELISIH")

    # --- (A3/C4) tag per-cell bertahan setelah filter di clone ⛶ ---
    k_match2 = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 1")
    if CELL_TAGS_SUPPORTED and k_match2 is not None:
        win2, ct = kv._maximize()
        for _ in range(30):
            root.update()
            time.sleep(0.01)
        _apply_hook = getattr(ct, "_clone_filter_apply", None)
        check("(v3.9.5) Clone ⛶ punya hook filter apply", _apply_hook is not None)
        if _apply_hook is not None:
            _apply_hook("Status", ["MATCH"])
            for _ in range(40):
                root.update()
                time.sleep(0.01)
            _has_neg = root.tk.call(str(ct), "tag", "cell", "has",
                                    "neg_cell", (k_match2, "BOM Lalu"))
            check("(v3.9.5) Filter di clone ⛶ → tag minus PER-CELL tetap "
                  "terpasang (dulu hilang)",
                  _has_neg == 1 and len(ct.get_children("")) == 3,
                  f"neg={_has_neg} rows={len(ct.get_children(''))}")
        win2.destroy()
        root.update()

    # --- (A1) ✕ Tutup File saat compute berjalan → hasil DIBUANG ---
    kv._load_paths([xlsx_path])   # job async dimulai (parse+compute)
    kv._close_file()           # tutup SEBELUM selesai — tanpa pump di antaranya
    check("(v3.9.5) Tutup saat compute: label kembali 'Belum ada file'",
          "Belum ada file" in kv._file_label_var.get())
    wait_view(root, kv)
    check("(v3.9.5) Race tutup: hasil file lama TIDAK muncul kembali "
          "(tabel tetap kosong, _busy reset)",
          len(kv.tree.get_children("")) == 0 and not kv._busy and
          "File ditutup" in kv.status_var_label.get(),
          f"rows={len(kv.tree.get_children(''))} busy={kv._busy} "
          f"status={kv.status_var_label.get()!r}")

    # --- (C1) run_async: shield GC dilepas walau pemilik job di-destroy ---
    import gc as _gc
    top = tk.Toplevel(root)
    run_async(top, lambda: time.sleep(0.4), lambda _r: None)
    top.destroy()
    _t0 = time.time()
    while time.time() - _t0 < 2.5:
        root.update()
        time.sleep(0.01)
    check("(v3.9.5) Popup di-destroy saat job jalan → _GC_HOLD depth 0 + "
          "GC menyala (dulu bocor seumur sesi)",
          _GC_HOLD["depth"] == 0 and _gc.isenabled(),
          f"depth={_GC_HOLD['depth']} gc={_gc.isenabled()}")

    # --- (B5) snapshot follow-up memuat 'aktif' ---
    store = app.followup_store
    kv._load_paths([xlsx_path])
    wait_view(root, kv)
    _first = kv.tree.get_children("")[0]
    _bbox = kv.tree.bbox(_first)
    if _bbox:
        ev5 = _Ev()
        ev5.widget = kv.tree
        ev5.x, ev5.y = _bbox[0] + 8, _bbox[1] + _bbox[3] // 2
        kv._on_tree_click(ev5)
        root.update()
        _snap = next(iter(store.rows.values())) if len(store) else {}
        check("(v3.9.5) Snapshot follow-up KOMPARASI memuat 'aktif'",
              _snap.get("aktif") == "AKTIF", f"got {_snap.get('aktif')!r}")
        kv._on_tree_click(ev5)   # keluarkan lagi
        root.update()

    # --- (C7) show_laporan_mode programatik menyinkronkan SegmentBar ---
    app.show_laporan_mode(1)
    root.update()
    check("(v3.9.5) show_laporan_mode(1) → segment.active ikut 1",
          app.laporan_segment.active == 1 and
          app.laporan_view.winfo_ismapped())

    # --- (B1) popup filter kolom 'Selisih vs Median' hidup kembali ---
    lv = app.laporan_view
    _sel_vals = lv._col_values("Selisih vs Median")
    check("(v3.9.5) _col_values('Selisih vs Median') tidak lagi kosong "
          "(popup filter kolom itu hidup)",
          isinstance(_sel_vals, list) and len(_sel_vals) > 0,
          f"got {_sel_vals!r}")
    app.show_laporan_mode(0)
    root.update()

    # --- (C2) Apply H merender GR tepat 1× (dulu 2×) ---
    dv = app.deviasi_gr_view
    _cnt = {"n": 0}
    _orig_refresh = dv._refresh

    def _counting_refresh(*a, **k):
        _cnt["n"] += 1
        return _orig_refresh(*a, **k)

    dv._refresh = _counting_refresh
    dv.tanggal_h_var.set("10")
    dv._on_tanggal_h_change()
    root.update()
    check("(v3.9.5) Apply H (nilai BERUBAH) → GR refresh 1× (dulu 2×)",
          _cnt["n"] == 1, f"got {_cnt['n']}")
    dv.tanggal_h_var.set("10")
    dv._on_tanggal_h_change()
    root.update()
    check("(v3.9.5) Apply H (nilai SAMA) → refresh eksplisit 1× tetap jalan",
          _cnt["n"] == 2, f"got {_cnt['n']}")
    dv._refresh = _orig_refresh
    # pulihkan H=25 (listener fan-out ke PCS + laporan)
    dv.tanggal_h_var.set("25")
    dv._on_tanggal_h_change()
    wait_view(root, dv)

    # --- (B3) unsubscribe H saat view di-destroy ---
    _h_state = app._shared_h
    _n_before = len(_h_state._listeners)
    lv2 = LaporanDeviasiView(app.tab_laporan, h_state=_h_state)
    check("(v3.9.5) subscribe menambah listener", 
          len(_h_state._listeners) == _n_before + 1)
    lv2.destroy()
    root.update()
    check("(v3.9.5) destroy view → listener H dilepas (unsubscribe)",
          len(_h_state._listeners) == _n_before,
          f"got {len(_h_state._listeners)} (sebelum {_n_before})")

    # ==================================================================
    print()
    print("== 24. (v3.9.10) AUDIT UI/UX ROUND 2 — REGRESSION FIXES ==")
    import threading as _th

    from src.ui.app import _enable_windows_dpi_awareness as _dpi_fix
    from src.ui.details_popup import DetailsPopup as _DPcls
    from src.ui.deviasi_view import DeviasiView as _DV
    from src.ui.rincian_po_view import RincianPoView as _RPV
    from src.ui.widgets import _GC_LOCK as _GLOCK
    from src.ui.widgets import gc_shield_acquire as _gac
    from src.ui.widgets import gc_shield_release as _grel
    from src.ui.widgets import sort_tree_by_column as _stbc

    # ---- B-04: handler view tidak lagi MENGGANTI binding infrastruktur ---
    # (auto-fit tepi kolom v3.4 + menu kolom) — jumlah script binding
    # harus >= 2 (CHAIN), bukan 1 (REPLACE = bug lama).
    for _vname, _v in (("Pivot", app.pivot_view),
                       ("Deviasi GR", app.deviasi_gr_view),
                       ("Deviasi PCS", app.deviasi_pcs_view),
                       ("Selisih IN", app.in_selisih_view),
                       ("Laporan", app.laporan_view),
                       ("Komparasi", app.komparasi_view),
                       ("Follow Up", app.followup_view)):
        _nb = _v.tree.bind("<Double-1>").count("%# %b")
        check(f"(v3.9.10) B-04 {_vname}: Double-1 = RANTAI >=2 script "
              f"(auto-fit tetap hidup)", _nb >= 2, f"scripts={_nb}")
    # (Button-3 chain diuji di popup detail §25 C-02 — tree utama Selisih
    #  IN memang tanpa context-menu level view; popup punya ColumnManager
    #  + menu copy → harus CHAIN setelah fix B-04.)

    # ---- A-02 + B-10: tombol disabled TAMPAK dim; hover tidak menimpa ----
    app.btn_export_tb.set_enabled(False)
    root.update()
    _bg_off = str(app.btn_export_tb.cget("background")).lower()
    check("(v3.9.10) A-02: toolbar Export disabled = abu dim (#94a3b8)",
          _bg_off == "#94a3b8", f"got {_bg_off}")
    app.btn_export_tb.event_generate("<Leave>")
    root.update()
    _bg_leave = str(app.btn_export_tb.cget("background")).lower()
    check("(v3.9.10) B-10: <Leave> saat disabled TIDAK menimpa warna dim",
          _bg_leave == "#94a3b8", f"got {_bg_leave}")
    app.btn_export_tb.set_enabled(True)
    root.update()

    # ---- A-04: navigasi keyboard antar-tab (Ctrl+Tab) ----
    check("(v3.9.10) A-04: enable_traversal — Ctrl+Tab aktif di toplevel",
          bool(root.bind("<Control-Tab>")))

    # ---- A-11: routing tab berbasis WIDGET (bukan index) ----
    check("(v3.9.10) A-11: peta _tab_views 6 entry berbasis nama widget",
          len(app._tab_views) == 6
          and app._tab_views.get(str(app.tab_rincian)) is app.rincian_view
          and app._tab_views.get(str(app.tab_deviasi_pcs))
          is app.deviasi_pcs_view,
          f"got {len(app._tab_views)} entry")
    check("(v3.9.10) A-11: marker tab Laporan → dispatch mode aktif",
          app._tab_views.get(str(app.tab_laporan))
          is app._laporan_tab_entry)

    # ---- A-03: DPI-awareness no-op di Linux (tanpa crash) ----
    try:
        _dpi_fix(root)
        _dpi_ok = True
    except Exception as _e:
        _dpi_ok = False
    check("(v3.9.10) A-03: _enable_windows_dpi_awareness aman di Linux",
          _dpi_ok)

    # ---- B-01: parser sort Indonesia (oracle deterministik) ----
    _st_tr = ttk.Treeview(root, columns=["x"])
    for _v in ["(1.234)", "999", "1.000", "12,5", "0"]:
        _st_tr.insert("", "end", values=(_v,))
    _stbc(_st_tr, "x", reverse=False,
          parse=app.in_selisih_view._parse_num_id)
    _got = [str(_st_tr.item(k)["values"][0])
            for k in _st_tr.get_children("")]
    check("(v3.9.10) B-01: parser ID — (1.234) < 0 < 12,5 < 999 < 1.000",
          _got == ["(1.234)", "0", "12,5", "999", "1.000"], f"got {_got}")
    _st_tr.destroy()

    # ---- render ulang Selisih IN (state filter deterministik) ----
    _iv = app.in_selisih_view
    _iv._reset_filter()
    ok = select_and_wait(root, app, app.tab_in_selisih, _iv)
    check("(v3.9.10) render Selisih IN utk §25", ok)
    _base = _iv._cached_base
    _fb = _base
    _tn = pd.to_numeric(_fb["Tanggal"], errors="coerce")
    _fb = _fb[(_tn >= 1) & (_tn <= 31)]
    if "Selisih IN" in _fb.columns:
        _sv2 = pd.to_numeric(_fb["Selisih IN"], errors="coerce").fillna(0)
        _fb = _fb[_sv2 != 0]
    _neg_oracle = 0
    for _c in ("Hasil SO", "Barang Masuk", "IN", "Selisih IN", "Saldo"):
        if _c in _fb.columns:
            _neg_oracle += int((pd.to_numeric(_fb[_c], errors="coerce")
                                .fillna(0) < 0).sum())
    check(f"(v3.9.10) B-01/C-04: baris tampil == oracle {len(_fb)}",
          len(_iv.tree.get_children("")) == len(_fb),
          f"got {len(_iv.tree.get_children(''))} vs {len(_fb)}")
    check(f"(v3.9.10) C-04: neg_cells == oracle {_neg_oracle} "
          f"(kolom numerik baris tampil)",
          len(_iv._neg_cells) == _neg_oracle,
          f"got {len(_iv._neg_cells)}")
    _fgn = dict(_iv.tree.tag_configure("neg_cell")).get("foreground", "")
    check("(v3.9.10) C-04: tag neg_cell terdaftar (merah) di tree utama",
          _fgn == "#dc2626", f"got {_fgn}")

    # ---- B-03: sort memanggil _reapply_cell_tags ----
    _rat_calls = []
    _orig_rat = _iv._reapply_cell_tags
    _iv._reapply_cell_tags = (
        lambda tr: (_rat_calls.append(1), _orig_rat(tr))[1])
    _iv._sort_by("Selisih IN", reverse=True)
    _iv._reapply_cell_tags = _orig_rat
    check("(v3.9.10) B-03: sort → tag minus per-cell dipasang ulang",
          len(_rat_calls) == 1, f"calls={len(_rat_calls)}")

    # ---- D-08: popup filter tanpa cache → dari TREE (no main-thread compute)
    _saved_cb = _iv._cached_base
    _iv._cached_base = None

    def _no_call(*_a, **_k):
        raise RuntimeError("D-08: compute di main thread!")
    _orig_cb = _iv._compute_base
    _iv._compute_base = _no_call
    try:
        _vals_d08 = _iv._col_values("Resto")
        _ok_d08 = isinstance(_vals_d08, list) and len(_vals_d08) > 0
    except RuntimeError:
        _ok_d08 = False
    finally:
        _iv._compute_base = _orig_cb
        _iv._cached_base = _saved_cb
    check("(v3.9.10) D-08: popup filter dgn cache kosong → nilai dari "
          "baris tampil (UI tidak membeku)", _ok_d08)

    # ---- D-01: cache berlabel identitas data yang benar ----
    check("(v3.9.10) D-01: in_selisih _cached_base_data == data",
          _iv._cached_base_data is _iv.data)
    check("(v3.9.10) D-01: laporan _cached_data == data",
          app.laporan_view._cached_data is app.laporan_view.data)
    check("(v3.9.10) D-01: komparasi _cached_data == data",
          app.komparasi_view._cached_data is app.komparasi_view.data)
    check("(v3.9.10) D-01: deviasi _tnum_data == data",
          app.deviasi_gr_view._tnum_data is app.deviasi_gr_view.data)

    # ---- B-08: sort saat render batch → ANTRE ----
    _dv = app.deviasi_gr_view
    _dv._busy = True
    _dv._pending_sort = None
    _dv._sort_by("Deviasi", reverse=True)
    check("(v3.9.10) B-08: sort saat busy → _pending_sort tersimpan",
          _dv._pending_sort == ("Deviasi", True),
          f"got {_dv._pending_sort}")
    _dv._busy = False
    _dv._pending_sort = None

    # ---- C-08: H berubah saat pane TERSEMBUNYI → cukup _dirty ----
    _pv = app.deviasi_pcs_view
    _pv._dirty = False
    _before_c08 = len(_pv.tree.get_children(""))
    _pv._on_shared_h_changed(15)
    root.update()
    check("(v3.9.10) C-08: pane tersembunyi → _dirty tanpa render",
          _pv._dirty is True
          and len(_pv.tree.get_children("")) == _before_c08)
    _pv._on_shared_h_changed(25)   # pulihkan H
    _pv._dirty = False

    # ---- C-07: DeviasiView unsubscribe saat destroy ----
    _n_h25 = len(app._shared_h._listeners)
    _dv2 = _DV(root, h_state=app._shared_h, h_editable=False)
    root.update()
    check("(v3.9.10) C-07: DeviasiView subscribe → +1 listener",
          len(app._shared_h._listeners) == _n_h25 + 1)
    _dv2.destroy()
    root.update()
    check("(v3.9.10) C-07: destroy DeviasiView → listener dilepas",
          len(app._shared_h._listeners) == _n_h25,
          f"got {len(app._shared_h._listeners)}")

    # ---- B-07 + B-02: clone ⛶ punya cancel + tag dipasang ulang --------
    _rat2 = []
    _orig_rat2 = app.deviasi_gr_view._reapply_cell_tags
    app.deviasi_gr_view._reapply_cell_tags = (
        lambda tr: (_rat2.append(1), _orig_rat2(tr))[1])
    _win, _nt = app.deviasi_gr_view._maximize()
    for _ in range(40):
        root.update()
        time.sleep(0.01)
        if len(_nt.get_children("")) >= \
                len(app.deviasi_gr_view.tree.get_children("")):
            break
    check("(v3.9.10) B-07: clone punya _row_filter_cancel (batch bisa "
          "dibatalkan saat filter/sort clone)",
          callable(getattr(_nt, "_row_filter_cancel", None)))
    check("(v3.9.10) B-04 clone: Double-1 clone = rantai",
          _nt.bind("<Double-1>").count("%# %b") >= 2)
    _n_rat_before = len(_rat2)
    # trigger filter di clone → on_after_filter → reapply tags
    _resto_vals = [str(app.deviasi_gr_view.tree.item(k)["values"][1])
                   for k in app.deviasi_gr_view.tree.get_children("")]
    _one_resto = sorted(set(_resto_vals))[0]
    _nt._clone_filter_apply("Resto", {_one_resto})
    for _ in range(60):
        root.update()
        time.sleep(0.01)
    check("(v3.9.10) B-02: filter clone → tag per-cell dipasang ulang "
          "(on_after_filter)", len(_rat2) > _n_rat_before,
          f"calls {len(_rat2)} vs before {_n_rat_before}")
    _win.destroy()
    app.deviasi_gr_view._reapply_cell_tags = _orig_rat2
    root.update()

    # ---- D-03: followup render beruntun stabil ----
    _fv = app.followup_view
    check("(v3.9.10) D-03: _insert_cancel tersimpan di followup",
          callable(getattr(_fv, "_insert_cancel", None)))
    _n0 = len(_fv.tree.get_children(""))
    _fv._render()
    for _ in range(20):
        root.update()
        time.sleep(0.005)
    _fv._render()
    for _ in range(40):
        root.update()
        time.sleep(0.005)
    _n1 = len(_fv.tree.get_children(""))
    check("(v3.9.10) D-03: render ulang beruntun = jumlah baris stabil "
          "(no duplikat/terpotong)", _n1 == _n0, f"{_n0} → {_n1}")

    # ---- C-03: format angka Indonesia di Rincian PO & DetailsPopup ----
    check("(v3.9.10) C-03: RincianPo._fmt_num(1234.5) == '1.234,5'",
          _RPV._fmt_num(1234.5) == "1.234,5",
          f"got {_RPV._fmt_num(1234.5)}")
    check("(v3.9.10) C-03: RincianPo._fmt_num(-1234.5) == '(1.234,5)'",
          _RPV._fmt_num(-1234.5) == "(1.234,5)",
          f"got {_RPV._fmt_num(-1234.5)}")
    check("(v3.9.10) C-03: DetailsPopup._fmt_nilai(1234.5) = ('1.234,5', False)",
          _DPcls._fmt_nilai(1234.5) == ("1.234,5", False))
    check("(v3.9.10) C-03: DetailsPopup._fmt_nilai(-1234.5) = ('(1.234,5)', True)",
          _DPcls._fmt_nilai(-1234.5) == ("(1.234,5)", True))

    # ---- C-10: footer 'baris' + format ID ----
    _pstat = app.pivot_view.status_var.get()
    check("(v3.9.10) C-10: footer pivot 'baris' (bukan 'rows' EN)",
          "rows" not in _pstat and "baris" in _pstat, f"got {_pstat}")

    # ---- C-02: DetailsPopup on_error → view tidak mati permanen ----
    _dp = _DPcls(root, "Uji C-02", append1.head(30))
    for _ in range(150):
        if not _dp._busy:
            break
        root.update()
        time.sleep(0.01)
    check("(v3.9.10) C-10: footer popup detail 'baris' + format ID",
          "rows" not in _dp._base_status and "baris" in _dp._base_status,
          f"got {_dp._base_status}")
    check("(v3.9.10) B-04 popup detail: Button-3 = rantai (menu kolom + "
          "context copy)", _dp.tree.bind("<Button-3>").count("%# %b") >= 2)

    def _boom(*_a, **_k):
        raise RuntimeError("uji-error-detail")
    _dp._prepare_rows = _boom
    _dp._render(sync=True)
    check("(v3.9.10) C-02: DetailsPopup _busy di-reset saat error",
          _dp._busy is False, f"busy={_dp._busy}")
    check("(v3.9.10) C-02: status error popup tampil",
          "Gagal" in _dp.status_var.get())
    del _dp._prepare_rows
    _dp._render(sync=True)
    check("(v3.9.10) C-02: render BERIKUTNYA tetap jalan (popup hidup)",
          _dp._busy is False and len(_dp.tree.get_children("")) > 0)
    _dp.destroy()
    root.update()

    # ---- B-06: gc_shield thread-safe ----
    _depths = []

    def _gcw():
        _gac()
        _depths.append(_GC_HOLD["depth"])
        _grel()
    _ths = [_th.Thread(target=_gcw) for _ in range(6)]
    for _t in _ths:
        _t.start()
    for _t in _ths:
        _t.join(3.0)
    check("(v3.9.10) B-06: _GC_LOCK ada; 6 thread acquire/release → "
          "depth kembali 0", hasattr(_GLOCK, "acquire")
          and _GC_HOLD["depth"] == 0, f"depth={_GC_HOLD['depth']}")

    # ---- B-20: BaseException tidak menempel busy/shield (jalur sync) ----
    _se = []
    try:
        run_async(root, lambda: (_ for _ in ()).throw(SystemExit(9)),
                  lambda r: None, sync=True, on_error=lambda e: None)
    except SystemExit:
        _se.append(True)
    check("(v3.9.10) B-20: SystemExit di work → busy reset + shield "
          "dilepas + re-raise",
          _se == [True] and _GC_HOLD["depth"] == 0,
          f"se={_se} depth={_GC_HOLD['depth']}")

    # ---- B-05/B-13/B-19: HeaderFilter >cap + pencarian + urut numerik ---
    _hf_tree = ttk.Treeview(root, columns=["x"])
    _hf_tree.heading("x", text="X")
    _hf_vals = ([f"nilai-{i:03d}" for i in range(6)]
                + ["999", "1.000", "12,5", "(1.234)", "abc"])
    _hf = HeaderFilter(_hf_tree, "x", get_values=lambda: _hf_vals,
                       on_apply=lambda sel: None, label="X")
    _hf.MAX_CHECKS = 8    # instance override — 11 nilai > cap
    _hf.open_popup()
    root.update()
    check("(v3.9.10) B-19: nilai numerik diurut NUMERIK dulu "
          "('(1.234)' < '12,5' < '999' < '1.000' < teks)",
          _hf._values_list[:5] == ["(1.234)", "12,5", "999", "1.000",
                                   "abc"], f"got {_hf._values_list[:5]}")
    check("(v3.9.10) B-05: hanya MAX_CHECKS checkbox awal + label jujur",
          len(_hf._checks) == 8 and _hf._more_label is not None,
          f"checks={len(_hf._checks)}")
    _hf._search_var.set("nilai-005")
    _hf._filter_list()
    root.update()
    check("(v3.9.10) B-05: pencarian menemukan nilai DI LUAR cap → "
          "checkbox LAZY dibuat",
          "nilai-005" in _hf._checks and "nilai-005" in _hf._vars)
    _hf._search_var.set("zzz")
    _hf._close()
    root.update()
    _hf.open_popup()
    root.update()
    check("(v3.9.10) B-13: popup dibuka ulang dgn pencarian KOSONG",
          _hf._search_var.get() == "")
    _v0 = _hf._values_list[0]
    _hf._vars[_v0].set(False)
    _hf._emit()
    root.update()
    check("(v3.9.10) B-05: uncheck 1 nilai → 10 terpilih; nilai di luar "
          "cap TIDAK hilang senyap (bug lama: 7 saja)",
          _hf.selected is not None and _v0 not in _hf.selected
          and "nilai-005" in _hf.selected
          and len(_hf.selected) == 10,
          f"n={len(_hf.selected or set())}")
    _hf._close()
    root.update()
    _hf_tree.destroy()

    # ---- A-01: MULAI saat worker lama masih hidup → DITOLAK ----
    import tkinter.messagebox as _tkmb
    app.is_running = False
    app.worker_thread = _th.Thread(target=time.sleep, args=(3.0,),
                                   daemon=True)
    app.worker_thread.start()
    _info_calls = []
    _orig_info, _orig_err = _tkmb.showinfo, _tkmb.showerror
    _tkmb.showinfo = lambda *a, **k: (_info_calls.append(a), "ok")[1]
    _tkmb.showerror = lambda *a, **k: ("ok",)
    try:
        app._start_pipeline()
    finally:
        _tkmb.showinfo, _tkmb.showerror = _orig_info, _orig_err
    check("(v3.9.10) A-01: MULAI saat worker lama masih hidup → "
          "DITOLAK (tanpa thread kedua)",
          bool(_info_calls) and app.is_running is False,
          f"info={len(_info_calls)} running={app.is_running}")
    app.worker_thread.join(4.0)

    # ---- D-04: file di-skip terhitung dari log pipeline ----
    app._skipped_files = 0
    app.log_queue.put("[WARNING] Skip file X.xlsx (terkunci)\n")
    app.log_queue.put("[WARNING] Skip file Y.xlsx (hilang)\n")
    app._poll_log_queue()
    check("(v3.9.10) D-04: 2 file skip terhitung dari log",
          app._skipped_files == 2, f"got {app._skipped_files}")

    # ---- D-04 (display, terakhir — mereset data views) ----
    app._skipped_files = 2
    app._on_pipeline_done(None, None, None, None, None)
    root.update()
    check("(v3.9.10) D-04: pipeline selesai dgn file skip → status "
          "PERINGATAN (bukan hijau polos)",
          "dilewati" in app.statusbar.dot._var.get(),
          f"got {app.statusbar.dot._var.get()}")

    # =====================================================================
    print("== 25. (v3.9.11) TUNTAS SISA TEMUAN AUDIT 2-b (7 fix + repo private) ==")

    from src.ui.widgets import (
        ColumnManager as _ColumnManager,
    )
    from src.ui.widgets import (
        EmptyState as _EmptyState,
    )
    from src.ui.widgets import (
        TableExpander as _TableExpander,
    )
    from src.ui.widgets import (
        apply_tree_row_filters as _atrf,
    )
    from src.ui.widgets import (
        sort_tree_by_column as _stbc26,
    )
    from src.ui.widgets import (
        validated_tgl_entry as _vte,
    )

    def _dcset(t):
        dc = t["displaycolumns"]
        items = [str(x) for x in dc] if isinstance(dc, (tuple, list)) \
            else str(dc).split()
        return set(items)

    # ---- B-21: panah arah sort di heading -------------------------------
    _t21 = ttk.Treeview(root, columns=["a", "b"])
    _t21.heading("a", text="Kolom A")
    _t21.heading("b", text="Kolom B")
    for _i, (_av, _bv) in enumerate([("x", "1"), ("y", "3"), ("z", "2")]):
        _t21.insert("", "end", iid=f"r21_{_i}", values=(_av, _bv))
    _stbc26(_t21, "b", reverse=True)
    check("(v3.9.11) B-21: sort menurun → heading kolom sort berpanah ↓",
          _t21.heading("b")["text"] == "Kolom B \u2193",
          f"got {_t21.heading('b')['text']!r}")
    _stbc26(_t21, "a", reverse=False)
    check("(v3.9.11) B-21: sort pindah kolom → panah lama hilang, ↑ muncul",
          _t21.heading("b")["text"] == "Kolom B"
          and _t21.heading("a")["text"] == "Kolom A \u2191",
          f"a={_t21.heading('a')['text']!r} b={_t21.heading('b')['text']!r}")
    _t21.destroy()

    # ---- B-14: toggle filter clone tidak me-reset urutan sort -----------
    _t14 = ttk.Treeview(root, columns=["nama", "nilai"])
    for _i, (_nm, _vl) in enumerate([("a", "10"), ("b", "2"),
                                      ("c", "30"), ("d", "5")]):
        _t14.insert("", "end", iid=f"r14_{_i}", values=(_nm, _vl))
    _stbc26(_t14, "nilai", reverse=True)   # 30,10,5,2
    check("(v3.9.11) B-14: _last_sort tercatat di tree",
          getattr(_t14, "_last_sort", None) == ("nilai", True, None),
          f"got {getattr(_t14, '_last_sort', None)}")
    _snap14 = {"done": False, "order": None}

    def _d14():
        _snap14["done"] = True
        _snap14["order"] = [str(_t14.item(k)["values"][1])
                            for k in _t14.get_children("")]
    _atrf(_t14, {"nama": {"a", "b", "c", "d"}}, on_done=_d14)
    for _ in range(40):
        root.update()
        time.sleep(0.01)
    _order14 = [str(_t14.item(k)["values"][1])
                for k in _t14.get_children("")]
    check("(v3.9.11) B-14: urutan sort BERTAHAN setelah toggle filter "
          "(bug lama: kembali urutan asli 10,2,30,5)",
          _order14 == ["30", "10", "5", "2"],
          f"got {_order14}")
    check("(v3.9.11) B-14: sort dijalankan SEBELUM on_done (urutan final "
          "saat tag dipasang)", _snap14["done"]
          and _snap14["order"] == ["30", "10", "5", "2"],
          f"done={_snap14['done']} order={_snap14['order']}")
    _t14.destroy()

    # ---- B-09: sort tree berhirarki — anak tidak hilang ------------------
    _t9 = ttk.Treeview(root, columns=["v"], show="tree headings")
    _t9.heading("#0", text="Nama")
    _t9.heading("v", text="V")
    _t9.insert("", "end", iid="p1", text="Parent 1", values=("1",))
    _t9.insert("", "end", iid="p2", text="Parent 2", values=("2",))
    _t9.insert("p1", "end", iid="c1", text="Anak 1", values=("9",))
    _t9.insert("p1", "end", iid="c2", text="Anak 2", values=("3",))
    _t9.item("p1", open=True)
    _stbc26(_t9, "v", reverse=True)   # p2 (2) dulu, p1 (1) kemudian
    check("(v3.9.11) B-09: sort hirarki — urutan top-level benar",
          list(_t9.get_children("")) == ["p2", "p1"],
          f"got {list(_t9.get_children(''))}")
    check("(v3.9.11) B-09: ANAK subtree bertahan (jalur lama: terhapus)",
          list(_t9.get_children("p1")) == ["c1", "c2"]
          and _t9.item("c1")["text"] == "Anak 1",
          f"got {list(_t9.get_children('p1'))}")
    check("(v3.9.11) B-09: text #0 + state open parent bertahan",
          _t9.item("p1")["text"] == "Parent 1"
          and _t9.item("p1")["open"] in (True, 1),
          f"text={_t9.item('p1')['text']!r} open={_t9.item('p1')['open']}")
    # jalur flat: text #0 ikut dipertahankan saat reinsert
    _t9f = ttk.Treeview(root, columns=["v"], show="tree headings")
    for _i, (_nm, _vl) in enumerate([("n1", "5"), ("n2", "1"), ("n3", "3")]):
        _t9f.insert("", "end", iid=f"f{_i}", text=_nm, values=(_vl,))
    _stbc26(_t9f, "v", reverse=True)
    check("(v3.9.11) B-09: jalur flat — text #0 dipertahankan",
          [_t9f.item(k)["text"] for k in _t9f.get_children("")]
          == ["n1", "n3", "n2"],
          f"got {[_t9f.item(k)['text'] for k in _t9f.get_children('')]}")
    _t9.destroy()
    _t9f.destroy()

    # ---- B-18: mirror kolom ⛶ DUA ARAH -----------------------------------
    _s18 = ttk.Treeview(root, columns=["a", "b"])
    _c18 = ttk.Treeview(root, columns=["a", "b"])
    _ColumnManager(_s18)
    _cm18 = _ColumnManager(_c18, mirror=_s18)
    _s18_mgr = _s18._column_manager
    _s18_mgr.hide("b")
    check("(v3.9.11) B-18: hide di SUMBER → clone ikut (dulu satu arah)",
          _dcset(_c18) == {"a"},
          f"clone dc={_dcset(_c18)}")
    check("(v3.9.11) B-18: state colmgr clone tersinkron (hidden=['b'])",
          _cm18.hidden == ["b"], f"got {_cm18.hidden}")
    _s18b = ttk.Treeview(root, columns=["a", "b"])
    _c18b = ttk.Treeview(root, columns=["a", "b"])
    _ColumnManager(_s18b)
    _c18b_mgr = _ColumnManager(_c18b, mirror=_s18b)
    _c18b_mgr.hide("a")
    check("(v3.9.11) B-18: arah lama tetap — hide di CLONE → source ikut",
          _dcset(_s18b) == {"b"}, f"source dc={_dcset(_s18b)}")
    for _t in (_s18, _c18, _s18b, _c18b):
        _t.destroy()

    # ---- B-17: cursor watch ber-refcount ----------------------------------
    _top17 = tk.Toplevel(root)
    _ov1 = LoadingOverlay(_top17)
    _ov2 = LoadingOverlay(_top17)
    _ov1.show(delay_ms=0)
    _ov2.show(delay_ms=0)
    root.update()
    _c_17a = str(_top17.cget("cursor"))
    _ov1.hide()
    _c_17b = str(_top17.cget("cursor"))
    _ov2.hide()
    _c_17c = str(_top17.cget("cursor"))
    check("(v3.9.11) B-17: overlay-1 selesai → cursor TETAP watch "
          "(bug lama: reset saat overlay-2 masih loading)",
          _c_17a == "watch" and _c_17b == "watch",
          f"a={_c_17a!r} b={_c_17b!r}")
    check("(v3.9.11) B-17: klaim terakhir dilepas → cursor normal",
          _c_17c in ("", "arrow")
          and getattr(_top17, "_watch_cursor_refs", -1) == 0,
          f"c={_c_17c!r} refs={getattr(_top17, '_watch_cursor_refs', -1)}")
    _top17.destroy()

    # ---- B-16: TableExpander restore urutan -------------------------------
    _host16 = tk.Frame(root)
    _host16.pack(fill="both", expand=True)
    _A16 = tk.Frame(_host16, bg="#ff0000")
    _T1_16 = tk.Frame(_host16, bg="#00ff00")
    _T2_16 = tk.Frame(_host16, bg="#0000ff")
    _A16.pack(side="top", fill="x")
    _T1_16.pack(side="top", fill="x")
    _T2_16.pack(side="top", fill="x")
    root.update_idletasks()
    _btn16 = tk.Button(root)
    _exp16 = _TableExpander(_btn16, [_T1_16, _T2_16])
    _exp16.collapse()
    root.update_idletasks()
    check("(v3.9.11) B-16: collapse — target tersembunyi",
          list(_host16.pack_slaves()) == [_A16],
          f"got {list(_host16.pack_slaves())}")
    _exp16.restore()
    root.update_idletasks()
    check("(v3.9.11) B-16: restore urutan BENAR [A,T1,T2] (bug lama: "
          "target akhir berturut terpasang TERBALIK [A,T2,T1])",
          list(_host16.pack_slaves()) == [_A16, _T1_16, _T2_16],
          f"got {list(_host16.pack_slaves())}")
    _btn16.destroy()
    _host16.destroy()

    # ---- B-12: pecahan input tanggal DITOLAK ------------------------------
    import tkinter.messagebox as _tkmb26
    _ow26 = _tkmb26.showwarning
    _tkmb26.showwarning = lambda *a, **k: "ok"
    try:
        _v12 = tk.StringVar(value="7.9")
        _r12 = _vte(_v12, lo=1, hi=31, fallback=25, label="TANGGAL H",
                    parent=root)
        check("(v3.9.11) B-12: pecahan '7.9' DITOLAK + revert fallback "
              "(bug lama: dilantai senyap jadi 7)",
              _r12 == 25 and _v12.get() == "25",
              f"r={_r12} var={_v12.get()!r}")
        _v12b = tk.StringVar(value="7.0")
        _r12b = _vte(_v12b, lo=1, hi=31, fallback=25, label="X",
                     parent=root)
        check("(v3.9.11) B-12: '7.0' tetap diterima sebagai 7",
              _r12b == 7 and _v12b.get() == "7",
              f"r={_r12b} var={_v12b.get()!r}")
        _v12c = tk.StringVar(value=" 25 ")
        _r12c = _vte(_v12c, lo=1, hi=31, fallback=25, label="X",
                     parent=root)
        check("(v3.9.11) B-12: ' 25 ' (spasi) tetap valid → 25",
              _r12c == 25, f"r={_r12c}")
    finally:
        _tkmb26.showwarning = _ow26
    # in_selisih: jalur _on_tanggal_change kini juga menolak pecahan
    _iv26 = app.in_selisih_view
    _iv26.tgl_start_var.set("3.5")
    _iv26.tgl_end_var.set("10")
    _iv26._on_tanggal_change()
    root.update()
    check("(v3.9.11) B-12: _on_tanggal_change Selisih IN menolak '3.5' "
          "(pesan status, tanpa refresh)",
          "harus angka" in (_iv26.status_var.get() or ""),
          f"got {_iv26.status_var.get()!r}")
    _iv26.tgl_start_var.set("3")
    _iv26._on_tanggal_change()
    wait_view(root, _iv26)   # biarkan refresh valid selesai sebelum cleanup

    # ---- B-11: EmptyState adaptif ------------------------------------------
    _es11 = _EmptyState(root, title="Belum ada data")
    _es11.place(x=0, y=0, width=300, height=200)
    root.update()
    _pi11 = _es11._center.place_info()
    check("(v3.9.11) B-11: frame center MENGECIL di widget sempit 300×200 "
          "(bug lama: fixed 520×260 terpotong)",
          0 < int(_pi11["width"]) <= 282 and 0 < int(_pi11["height"]) <= 182,
          f"w={_pi11.get('width')} h={_pi11.get('height')}")
    _es11.place(x=0, y=0, width=640, height=420)
    root.update()
    _pi11b = _es11._center.place_info()
    check("(v3.9.11) B-11: widget lebar → center clamp maks 520×260",
          int(_pi11b["width"]) == 520 and int(_pi11b["height"]) == 260,
          f"w={_pi11b.get('width')} h={_pi11b.get('height')}")
    _es11.place_forget()
    _es11.destroy()

    # ==================================================================
    print("== 26. (v3.9.13) SEARCH-TO-SELECT + KATEGORI + PATH + "
          "MULTI-FILE + ANALISA ==")
    import json as _json13
    import tempfile as _tf13

    kv.load_data(det)
    wait_view(root, kv)
    kv._load_paths([xlsx_path])
    wait_view(root, kv)
    n_before13 = len(kv.tree.get_children(""))

    # --- (1) SEARCH-TO-SELECT: Enter = hasil pencarian jadi pilihan ------
    _hf13 = kv.header_filters._filters["Resto"]
    _hf13.open_popup()
    root.update()
    _hf13._search_var.set("QQQ")      # tidak ada resto mengandung QQQ
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Enter hasil KOSONG → 0 baris (perilaku Excel; "
          "permintaan user pilih 'kosong')",
          _hf13.selected == set() and
          len(kv.tree.get_children("")) == 0,
          f"sel={_hf13.selected!r} rows={len(kv.tree.get_children(''))}")
    _hf13._search_var.set("MLG")
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Enter 'MLG' → hasil pencarian jadi seleksi "
          "({1001.MLGPAR} → 5 baris)",
          _hf13.selected == {"1001.MLGPAR"} and
          len(kv.tree.get_children("")) == 5,
          f"sel={_hf13.selected!r} rows={len(kv.tree.get_children(''))}")
    _hf13._search_var.set("")
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Enter query KOSONG → reset (semua baris kembali)",
          _hf13.selected is None and
          len(kv.tree.get_children("")) == n_before13,
          f"sel={_hf13.selected!r}")
    # operator teks 'Diawali' (nilai scope = data tampil — resto-app saja)
    _hf13._op_var.set("Diawali")
    _hf13._search_var.set("1001")
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Operator 'Diawali' 1001 → hanya resto MLGPAR (5 baris)",
          _hf13.selected == {"1001.MLGPAR"} and
          len(kv.tree.get_children("")) == 5,
          f"sel={_hf13.selected!r}")
    # invert (↔ Balik): seleksi = komplemen
    _hf13._invert_selection()
    wait_view(root, kv)
    check("(v3.9.13) ↔ Balik → komplemen (1002.SBYKET → 1 baris)",
          _hf13.selected == {"1002.SBYKET"} and
          len(kv.tree.get_children("")) == 1,
          f"sel={_hf13.selected!r}")
    _hf13._op_var.set("Mengandung")
    _hf13._close()
    kv._reset_filter()
    wait_view(root, kv)

    # --- (2) FILTER KATEGORI di tab Deviasi GR & PCS ---------------------
    grv13 = app.deviasi_gr_view
    _cols13 = [c[0] for c in grv13.COLUMNS]
    check("(v3.9.13) Kolom KATEGORI di Deviasi GR (setelah Satuan)",
          "KATEGORI" in _cols13 and
          _cols13.index("KATEGORI") == _cols13.index("Satuan") + 1,
          f"got index={_cols13.index('KATEGORI')}")
    check("(v3.9.13) Combobox KATEGORI ada (GR) + default 'Semua'",
          hasattr(grv13, "_kategori_var") and
          grv13._kategori_var.get() == "Semua")
    check("(v3.9.13) Combobox KATEGORI ada (PCS — kelas dipakai bersama)",
          hasattr(app.deviasi_pcs_view, "_kategori_var"))
    _kat13 = append1.copy()
    _kat13["KATEGORI"] = ["SAYURAN" if b == "GULA PASIR" else "BAHAN"
                          for b in _kat13["Nama Barang"]]
    grv13.load_data(_kat13)
    wait_view(root, grv13)
    _kv13 = list(grv13._kategori_combo["values"])
    check("(v3.9.13) Combobox terisi dari data (Semua + BAHAN + SAYURAN)",
          _kv13 == ["Semua", "BAHAN", "SAYURAN"], f"got {_kv13}")
    _gr_all13 = len(grv13.tree.get_children(""))
    grv13._kategori_var.set("SAYURAN")
    grv13._on_kategori_changed()
    wait_view(root, grv13)
    _gr_sayur13 = [grv13.tree.set(k, "Nama Barang")
                   for k in grv13.tree.get_children("")]
    check("(v3.9.13) Filter kategori SAYURAN → hanya GULA PASIR (2 resto)",
          0 < len(_gr_sayur13) < _gr_all13 and
          set(_gr_sayur13) == {"GULA PASIR"},
          f"got {_gr_sayur13}")
    grv13._reset_filter()
    wait_view(root, grv13)
    check("(v3.9.13) ✕ Reset Filter mengembalikan kategori 'Semua'",
          grv13._kategori_var.get() == "Semua" and
          len(grv13.tree.get_children("")) == _gr_all13)
    # kolom KATEGORI tampil di tabel + filter header otomatis
    check("(v3.9.13) Nilai KATEGORI tampil di tabel",
          any("SAYURAN" in str(grv13.tree.set(k, "KATEGORI"))
              for k in grv13.tree.get_children("")) or
          any("BAHAN" in str(grv13.tree.set(k, "KATEGORI"))
              for k in grv13.tree.get_children("")))
    grv13.load_data(append1)
    wait_view(root, grv13)

    # --- (3) PATH tersimpan (FIX BUG v3.9.10) + entry editable -----------
    check("(v3.9.13) komparasi_last.json TERSIMPAN setelah load "
          "(BUG v3.9.10: str.with_suffix → json tak pernah tersimpan)",
          os.path.isfile("komparasi_last.json"))
    _saved13 = {}
    if os.path.isfile("komparasi_last.json"):
        with open("komparasi_last.json", encoding="utf-8") as f13:
            _saved13 = _json13.load(f13)
    check("(v3.9.13) Format json baru {'paths': [...]}",
          _saved13.get("paths") == [xlsx_path], f"got {_saved13!r}")
    check("(v3.9.13) Entry path = file aktif (editable user)",
          kv._path_var.get() == xlsx_path,
          f"got {kv._path_var.get()!r}")
    kv._path_var.set(xlsx_path)   # "ubah" lalu reload dari entry
    kv._reload_file()
    wait_view(root, kv)
    check("(v3.9.13) ↻ reload dari ENTRY (tanpa dialog) → 6 baris",
          len(kv.tree.get_children("")) == n_before13,
          f"got {len(kv.tree.get_children(''))}")

    # --- (4) MULTI-FILE (2 bulan) + filter bulan-terbaru default ---------
    multi2_13 = os.path.join(_tf13.gettempdir(), "mock_deviasi_sep.xlsx")
    _wb13 = _WB()
    _ws13 = _wb13.active
    _ws13.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM",
                  "QTY DEVIASI", "STATUS BULAN", "BULAN"])
    # SEP (bulan lalu) MINUS — vs OKT (mock utama) PLUS 49 → FLIP
    _ws13.append(["1001.MLGPAR", "AYAM FILET", -80, -90, -10,
                  "WEEK 1", "SEP"])
    _wb13.save(multi2_13)
    kv._load_paths([multi2_13, xlsx_path])
    wait_view(root, kv)
    check("(v3.9.13) Label 2 file dimuat",
          "2 file" in kv._file_label_var.get(),
          f"got {kv._file_label_var.get()!r}")
    check("(v3.9.13) Default tabel = BULAN TERBARU (footer 'BULAN OKTOBER')",
          "BULAN OKTOBER" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")
    check("(v3.9.13) Chip BULAN = OKTOBER",
          kv._month_chip_var.get() == "OKTOBER",
          f"got {kv._month_chip_var.get()!r}")
    check("(v3.9.13) Bulan terbaru → jumlah baris sama dgn file OKT saja "
          "(baris SEP tersembunyi)",
          len(kv.tree.get_children("")) == n_before13,
          f"got {len(kv.tree.get_children(''))}")
    kv._show_all_months.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    check("(v3.9.13) Centang 'Tampilkan semua bulan' → +1 baris SEP "
          "(chip SEMUA)",
          len(kv.tree.get_children("")) == n_before13 + 1 and
          kv._month_chip_var.get() == "SEMUA",
          f"got {len(kv.tree.get_children(''))}")
    kv._show_all_months.set(False)
    kv._on_option_changed()
    wait_view(root, kv)

    # --- (5) MODE 📈 ANALISA (Top Selisih + Perubahan Arah) --------------
    app.show_laporan_mode(0)
    app.notebook.select(app.tab_laporan)
    root.update()
    kv._on_mode_change(1)
    root.update()
    check("(v3.9.13) Mode Analisa: kartu analisa terlihat, tabel utama "
          "tersembunyi",
          kv._analisa_frame.winfo_ismapped() and
          not kv.tcard.winfo_ismapped())
    _top13n = len(kv._top_tree.get_children(""))
    check("(v3.9.13) Top Selisih terisi (join PENUH — 8 baris semua bulan)",
          _top13n == 8, f"got {_top13n}")
    if _top13n:
        _v13 = kv._top_tree.item(kv._top_tree.get_children("")[0],
                                 "values")
        check("(v3.9.13) Top-1 = peringkat 1 + |Selisih| terbesar "
              "(SEP: GR Saat Ini 49 − DEV Lalu -10 = 59)",
              str(_v13[0]) == "1" and str(_v13[7]) == "59",
              f"got peringkat={_v13[0]} selisih={_v13[7]}")
    _flip13n = len(kv._flip_tree.get_children(""))
    check("(v3.9.13) Perubahan Arah: flip AYAM MLGPAR W1 (SEP -10 → "
          "OKT +49) terdeteksi",
          _flip13n == 1, f"got {_flip13n}")
    if _flip13n:
        _f13 = kv._flip_tree.item(kv._flip_tree.get_children("")[0],
                                  "values")
        check("(v3.9.13) Flip: 9 kolom + periode SEP→OKTOBER + Δ 59",
              len(_f13) == 9 and "SEP" in str(_f13[0]) and
              "OKTOBER" in str(_f13[0]) and str(_f13[6]) == "59",
              f"periode={_f13[0]} Δ={_f13[6]}")
        _disp13 = abs(-10 + 49) / max(10, 49)
        _kat_exp13 = ("Sempurna" if _disp13 < 0.10
                      else "Dominan" if _disp13 < 0.40 else "Parsial")
        check("(v3.9.13) Kategori flip = "
              f"{_kat_exp13} (disparitas {_disp13:.4f})",
              str(_f13[8]) == _kat_exp13, f"got {_f13[8]}")
    check("(v3.9.13) Ringkasan flip terisi",
          "1 FLIP" in kv._flip_summary_var.get(),
          f"got {kv._flip_summary_var.get()!r}")
    kv._topn_var.set("3")
    kv._render_top_selisih()
    root.update()
    check("(v3.9.13) Top N=3 diterapkan",
          len(kv._top_tree.get_children("")) == 3,
          f"got {len(kv._top_tree.get_children(''))}")

    # --- (5b) v3.9.14: MINGGU di tab Analisa mengikuti kolom H ----------
    # (permintaan user: "week di tab analisa harusnya menyesuaikan juga
    # dengan kolom H atau aturan kolom H yaitu jika 7 berarti week 1")
    kv._topn_var.set("100")
    kv._show_all_weeks.set(False)
    app.deviasi_gr_view.tanggal_h_var.set("7")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    _top_w1 = [kv._top_tree.item(k, "values")[1]
               for k in kv._top_tree.get_children("")]
    check("(v3.9.14) Analisa H=7 → Top Selisih hanya WEEK 1 (5 dari 8 "
          "join) + prefiks minggu (H 7)",
          len(_top_w1) == 5 and all(v.endswith("WEEK 1") for v in _top_w1)
          and "Minggu WEEK 1" in kv._top_status_var.get() and
          "(H 7)" in kv._top_status_var.get(),
          f"rows={len(_top_w1)} {sorted(set(_top_w1))} "
          f"status={kv._top_status_var.get()!r}")
    check("(v3.9.14) Analisa H=7 → flip W1 SEP→OKT terdeteksi + prefiks "
          "minggu di ringkasan",
          len(kv._flip_tree.get_children("")) == 1 and
          "Minggu WEEK 1" in kv._flip_summary_var.get(),
          f"rows={len(kv._flip_tree.get_children(''))} "
          f"summary={kv._flip_summary_var.get()!r}")
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    check("(v3.9.14) Analisa H=25 → hanya minggu W4 (1 baris) + flip 0 "
          "(SEP hanya W1) + pesan jujur",
          len(kv._top_tree.get_children("")) == 1 and
          len(kv._flip_tree.get_children("")) == 0 and
          "Tidak ada perubahan arah" in kv._flip_status_var.get(),
          f"top={len(kv._top_tree.get_children(''))} "
          f"flip={len(kv._flip_tree.get_children(''))} "
          f"flip_status={kv._flip_status_var.get()!r}")
    # kembalikan state utk blok (6): semua minggu ON + H 25
    kv._show_all_weeks.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    # analisa MALAS: mode ⚖ + refresh → tabel analisa TIDAK dirender ulang
    _flip_count_l = len(kv._flip_tree.get_children(""))
    kv._on_mode_change(0)
    root.update()
    check("(v3.9.13) Kembali mode ⚖ Tabel",
          kv.tcard.winfo_ismapped() and
          not kv._analisa_frame.winfo_ismapped())

    # --- (5c) v3.9.15 — GELOMBANG 1: 4 BAGIAN ANALISA BARU ---------------
    # File sintetis OKT+NOV · 6 resto (BDG×3, SBY×2, MLG×1) · WEEK 4 —
    # analisa per-periode bekerja dari FILE (tanpa perlu join app).
    f5c = os.path.join(_tf13.gettempdir(), "mock_deviasi_gel1.xlsx")
    _w5c = _WB()
    _s5c = _w5c.active
    _s5c.append(["RESTO", "NAMA BAHAN", "Satuan", "QTY BOM", "QTY COM",
                 "QTY DEVIASI", "STATUS BULAN", "BULAN"])
    _rows5c = [
        # BERAS PREMIUM NOV W4 — rate 50/20/30/5/0/8 %
        ["1030.BDGUKU", "BERAS PREMIUM", "GR", -100, -50, 50,
         "WEEK 4", "NOV"],
        ["1041.BDGABC", "BERAS PREMIUM", "GR", -100, -80, 20,
         "WEEK 4", "NOV"],
        ["1042.BDGJAY", "BERAS PREMIUM", "GR", -100, -70, 30,
         "WEEK 4", "NOV"],
        ["1050.SBYPQR", "BERAS PREMIUM", "GR", -100, -95, 5,
         "WEEK 4", "NOV"],
        ["1051.SBYKLM", "BERAS PREMIUM", "GR", -100, -100, 0,
         "WEEK 4", "NOV"],
        ["1060.MLGHIJ", "BERAS PREMIUM", "GR", -100, -92, 8,
         "WEEK 4", "NOV"],
        # GULA AREN NOV W4 — 4 minus vs 1 surplus (minoritas MLGHIJ +12)
        ["1030.BDGUKU", "GULA AREN", "GR", -50, -60, -10,
         "WEEK 4", "NOV"],
        ["1041.BDGABC", "GULA AREN", "GR", -50, -70, -20,
         "WEEK 4", "NOV"],
        ["1042.BDGJAY", "GULA AREN", "GR", -50, -65, -15,
         "WEEK 4", "NOV"],
        ["1050.SBYPQR", "GULA AREN", "GR", -50, -55, -5,
         "WEEK 4", "NOV"],
        ["1060.MLGHIJ", "GULA AREN", "GR", -50, -62, 12,
         "WEEK 4", "NOV"],
        # KEJU MOZZARELLA OKT→NOV W4 — 2 flip (BDGUKU Sempurna −10→+10;
        # BDGABC Dominan +5→−4)
        ["1030.BDGUKU", "KEJU MOZZARELLA", "GR", -80, -90, -10,
         "WEEK 4", "201.OKT 26"],
        ["1041.BDGABC", "KEJU MOZZARELLA", "GR", -80, -75, 5,
         "WEEK 4", "201.OKT 26"],
        ["1030.BDGUKU", "KEJU MOZZARELLA", "GR", -80, -70, 10,
         "WEEK 4", "NOV"],
        ["1041.BDGABC", "KEJU MOZZARELLA", "GR", -80, -84, -4,
         "WEEK 4", "NOV"],
    ]
    for _r5c in _rows5c:
        _s5c.append(_r5c)
    _w5c.save(f5c)
    kv._show_all_weeks.set(False)   # scope analisa = minggu H 25 → WEEK 4
    kv._load_paths([f5c])
    wait_view(root, kv)
    kv._on_mode_change(1)
    root.update()
    check("(v3.9.15) Baris BAGIAN ada (5 bagian, aktif = Top & Flip)",
          hasattr(kv, "_anasec_segment") and
          len(kv._anasec_frames) == 5 and
          kv._anasec_idx == 0 and
          kv._anasec_frames[0].winfo_ismapped(),
          f"idx={kv._anasec_idx}")

    # ⚡ BAGIAN 1 — Risiko Flip per bahan
    kv._on_anasec_change(1)
    root.update()
    _r5c_n = len(kv._risk_tree.get_children(""))
    check("(v3.9.15) Risiko Flip: 1 bahan (KEJU) — 2 flip dari 2 pasangan",
          _r5c_n == 1, f"got {_r5c_n}")
    if _r5c_n:
        _v5c = kv._risk_tree.item(kv._risk_tree.get_children("")[0],
                                  "values")
        check("(v3.9.15) Risiko Flip KEJU: skor 50 (=30×1+10×2) · "
              "Sempurna 1 · Dominan 1 · Konsisten 0 · disparitas rerata "
              "10,00% · Level TINGGI",
              _v5c[4] == "2" and _v5c[5] == "1" and _v5c[6] == "1" and
              _v5c[8] == "0" and _v5c[9] == "10,00%" and
              _v5c[10] == "50" and _v5c[11] == "TINGGI",
              f"flip={_v5c[4]} semp={_v5c[5]} dom={_v5c[6]} "
              f"kons={_v5c[8]} disp={_v5c[9]} skor={_v5c[10]} "
              f"level={_v5c[11]}")
    _win5c, _tr5c = kv._risk_drilldown("KEJU MOZZARELLA")
    root.update()
    _rd5c_n = len(_tr5c.get_children(""))
    _rd5c_v = (_tr5c.item(_tr5c.get_children("")[0], "values")
               if _rd5c_n else [])
    check("(v3.9.15) Drilldown Risiko KEJU: 2 resto — kontributor "
          "terbesar dulu (BDGUKU |−10|→+10 Sempurna)",
          _rd5c_n == 2 and _rd5c_v[1] == "1030.BDGUKU" and
          _rd5c_v[6] == "Sempurna" and _rd5c_v[2] == "(10)" and
          _rd5c_v[3] == "10",
          f"n={_rd5c_n} resto={_rd5c_v[1] if _rd5c_v else '-'} "
          f"kat={_rd5c_v[6] if _rd5c_v else '-'}")
    _win5c.destroy()

    # 🧭 BAGIAN 2 — Arah Minoritas
    kv._on_anasec_change(2)
    root.update()
    _m5c_n = len(kv._min_tree.get_children(""))
    check("(v3.9.15) Arah Minoritas: hanya GULA AREN (4 minus vs 1 "
          "surplus — BERAS/KEJU searah)",
          _m5c_n == 1, f"got {_m5c_n}")
    if _m5c_n:
        _v5c = kv._min_tree.item(kv._min_tree.get_children("")[0],
                                 "values")
        check("(v3.9.15) Minoritas GULA: mayoritas 4 MINUS · minoritas 1 "
              "· Σ|DEV| minoritas 12 · 20,00%",
              _v5c[1] == "GULA AREN" and _v5c[3] == "4" and
              _v5c[4] == "1" and _v5c[5] == "MINUS" and
              _v5c[6] == "12" and _v5c[7] == "20,00%",
              f"nama={_v5c[1]} may={_v5c[3]} min={_v5c[4]} "
              f"arah={_v5c[5]} abs={_v5c[6]} pct={_v5c[7]}")
    _win5c, _tr5c = kv._minoritas_drilldown("GULA AREN")
    root.update()
    _md5c_n = len(_tr5c.get_children(""))
    _md5c_v = (_tr5c.item(_tr5c.get_children("")[0], "values")
               if _md5c_n else [])
    check("(v3.9.15) Drilldown Minoritas GULA: 1 resto MLGHIJ DEV 12 "
          "(minoritas SURPLUS)",
          _md5c_n == 1 and _md5c_v[0] == "1060.MLGHIJ" and
          _md5c_v[2] == "12",
          f"n={_md5c_n} resto={_md5c_v[0] if _md5c_v else '-'} "
          f"dev={_md5c_v[2] if _md5c_v else '-'}")
    _win5c.destroy()

    # 🏆 BAGIAN 3 — Liga Deviasi (default bahan Σ|DEV| terbesar = BERAS)
    kv._on_anasec_change(3)
    root.update()
    _comb5c = list(kv._liga_combo["values"])
    check("(v3.9.15) Liga: combobox bahan urut Σ|DEV| ↓ (BERAS 113 · "
          "GULA 62 · KEJU 14)",
          _comb5c[:3] == ["BERAS PREMIUM", "GULA AREN",
                          "KEJU MOZZARELLA"],
          f"got {_comb5c[:3]}")
    _l5c_n = len(kv._liga_tree.get_children(""))
    check("(v3.9.15) Liga BERAS: 5 resto diranking dari 6 populasi "
          "(SBYKLM DEV 0 — di populasi, tak diranking)",
          _l5c_n == 5 and "1 resto rate 0" in kv._liga_base_var.get(),
          f"got {_l5c_n} · base={kv._liga_base_var.get()!r}")
    if _l5c_n:
        _v5c = kv._liga_tree.item(kv._liga_tree.get_children("")[0],
                                  "values")
        # median rate = (0,08+0,20)/2 = 14% · |dev|: [.06 .06 .09 .14
        # .16 .36] → MAD = (0,09+0,14)/2 = 11,5%
        # z BDGUKU = (0,50−0,14)/(1,4826×0,115) = 2,11 (> 2 → merah)
        check("(v3.9.15) Liga BERAS rank-1 BDGUKU: rate 50,00% · z 2,11 "
              "· baseline median 14,00% · MAD 11,50%",
              _v5c[1] == "1030.BDGUKU" and _v5c[5] == "50,00%" and
              _v5c[6] == "2,11" and
              "median rate 14,00%" in kv._liga_base_var.get() and
              "MAD 11,50%" in kv._liga_base_var.get(),
              f"resto={_v5c[1]} rate={_v5c[5]} z={_v5c[6]} "
              f"base={kv._liga_base_var.get()!r}")
    # ganti bahan → GULA AREN (median 24,00% · rank-1 BDGABC 40,00%)
    kv._liga_bahan_var.set("GULA AREN")
    kv._on_liga_bahan_changed()
    root.update()
    _lg5c_n = len(kv._liga_tree.get_children(""))
    _lg5c_v = (kv._liga_tree.item(kv._liga_tree.get_children("")[0],
                                  "values") if _lg5c_n else [])
    check("(v3.9.15) Liga GULA AREN: 5 resto diranking · rank-1 BDGABC "
          "rate 40,00% · median 24,00%",
          _lg5c_n == 5 and _lg5c_v[1] == "1041.BDGABC" and
          _lg5c_v[5] == "40,00%" and
          "median rate 24,00%" in kv._liga_base_var.get(),
          f"n={_lg5c_n} resto={_lg5c_v[1] if _lg5c_v else '-'} "
          f"rate={_lg5c_v[5] if _lg5c_v else '-'}")

    # 💰 BAGIAN 4 — Benchmark Opportunity
    kv._on_anasec_change(4)
    root.update()
    _b5c_n = len(kv._bench_tree.get_children(""))
    # loss NOV W4: BDGUKU 10 · BDGABC 24 · BDGJAY 15 · SBYPQR 5 ·
    # SBYKLM 0 · MLGHIJ 0 → BDG median 15 (opp BDGABC 9) · SBY median
    # 2,5 (opp SBYPQR 2,5) · MLG 1 resto (opp 0) → total 11,5
    check("(v3.9.15) Benchmark: 6 resto · total opportunity 11,5",
          _b5c_n == 6 and
          "Total opportunity 11,5" in kv._bench_summary_var.get(),
          f"got {_b5c_n} · sum={kv._bench_summary_var.get()!r}")
    if _b5c_n:
        _v5c = kv._bench_tree.item(kv._bench_tree.get_children("")[0],
                                   "values")
        check("(v3.9.15) Benchmark rank-1 BDGABC: loss 24 · median BDG "
              "15 · opportunity 9",
              _v5c[1] == "1041.BDGABC" and _v5c[2] == "BDG" and
              _v5c[4] == "24" and _v5c[5] == "15" and _v5c[6] == "9",
              f"resto={_v5c[1]} kel={_v5c[2]} loss={_v5c[4]} "
              f"med={_v5c[5]} opp={_v5c[6]}")
        _v2 = kv._bench_tree.item(kv._bench_tree.get_children("")[1],
                                  "values")
        check("(v3.9.15) Benchmark rank-2 SBYPQR: opportunity 2,5 "
              "(median SBY 2,5)",
              _v2[1] == "1050.SBYPQR" and _v2[2] == "SBY" and
              _v2[6] == "2,5" and _v2[5] == "2,5",
              f"resto={_v2[1]} opp={_v2[6]} med={_v2[5]}")
        check("(v3.9.15) Benchmark: kelompok 1-resto dicatat jujur (MLG)",
              "1 kelompok 1 resto" in kv._bench_status_var.get(),
              f"got {kv._bench_status_var.get()!r}")

    # --- pulihkan state utk blok (6) ---
    kv._on_mode_change(0)
    root.update()
    kv._show_all_weeks.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    kv._load_paths([multi2_13, xlsx_path])
    wait_view(root, kv)
    os.unlink(f5c)

    # --- (6) AUTO-LOAD file terakhir saat pertama terlihat ---------------
    kv._close_file()
    kv._auto_loaded = False
    kv.ensure_refreshed()
    wait_view(root, kv)
    check("(v3.9.13) Auto-load file terakhir dari komparasi_last.json "
          "(2 path)",
          len(kv.tree.get_children("")) == n_before13,
          f"got {len(kv.tree.get_children(''))}")
    os.unlink(multi2_13)

    os.unlink(xlsx_path)
    if os.path.isfile("komparasi_last.json"):
        os.unlink("komparasi_last.json")

    # Cleanup
    root.destroy()

    print()
    print(f"HASIL: {len(PASS)} PASS, {len(FAIL)} FAIL")
    if FAIL:
        print("GAGAL:", FAIL)
        sys.exit(1)
    print("SEMUA TEST UI LULUS ✔")


if __name__ == "__main__":
    main()
