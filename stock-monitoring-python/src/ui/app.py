"""
app.py — Shell UI Stock Monitoring v3.9.22.

Struktur jendela (ala aplikasi Waste):
    ┌────────────────────────────────────────────────────┐
    │ ⬛ Toolbar gelap: 📊 judul + v3.9.22 + [💾 Export] │
    ├────────────────────────────────────────────────────┤
    │ Tab modern ber-ikon (10 tab, fungsi tidak berubah) │
    ├────────────────────────────────────────────────────┤
    │ Konten card-based per view (tabel lebar & besar)   │
    ├────────────────────────────────────────────────────┤
    │ StatusBar: ● status data + ringkasan baris          │
    └────────────────────────────────────────────────────┘

10 tab:
  1. ⚙️ Config          : RootPath + info config
  2. 🚀 Proses          : kontrol pipeline + KPI + konsol log gelap
  3. 📊 Pivot Table     : pivot matrix Excel-like (per resto default,
                          rentang tanggal default 26 BULAN LALU s/d 31
                          BULAN BERJALAN — v3.6)
  4. 📦 DEVIASI GR      : wide matrix + CEK anomaly (satuan GR) + ✓
                          (input TANGGAL H + Apply H — satu-satunya;
                          spinbox AMBANG ACR to BOM — v3.9.21) + kolom
                          Nominal (v3.9.34)
  5. 🧩 DEVIASI PCS     : wide matrix + CEK anomaly (non-GR) + ✓
                          (chip H read-only, ikut tab GR — v3.9;
                          spinbox ambang ACR sinkron — v3.9.21) + kolom
                          Nominal (v3.9.34)
  6. 📤 Rekap Selisih IN: SATU tabel IN (Accurate) vs Barang Masuk +
                          kolom SO + kolom Hasil Audit (logika macro VBA ×
                          data app — v3.6, tanpa sheet 29) + drill-down
  7. 📋 Laporan Deviasi : 3 MODE — ⚖ Komparasi File Deviasi (default,
                          v3.9.4; + kolom Nominal harga × GR Saat Ini —
                          v3.9.34) & 🚨 Anomali COM (v3.9.3) & 💰 Nominal
                          (H) (v3.9.32) + ✓
  8. 🧮 NOMINAL DEVIASI : Σ (Harga 41.09 × Qty Deviasi) per resto +
                          baris TOTAL + double-click resto → popup
                          rincian per barang (v3.9.34)
  9. ☑ Follow Up        : daftar baris tercentang + export (v3.2)
 10. 🛒 Rincian PO      : rekap PO + item (baris teal/putih, v3.9)

v3.9.34 ringkas (kolom Nominal di mana-mana + tab Σ per resto):
- Kolom Nominal (Harga 41.09 × Qty Deviasi) di tab 📦 Deviasi GR &
  🧩 Deviasi PCS (kolom Out_H/BK_H dihapus dari tampilan) dan di mode
  ⚖ Komparasi (harga × GR Saat Ini) — perhitungan = helper bersama
  src/ui/nominal_common.py (satu sumber kebenaran dgn mode 💰 Nominal
  (H)); app meneruskan harga_map/konversi_map audit_result ke view.
- TAB BARU 🧮 Nominal Deviasi: Σ nominal per resto + baris TOTAL +
  double-click resto → popup rincian per barang (user: "isinya total
  sum ... yang dapat dari harga × kuantitas deviasi, cuman ini disum
  per resto").

v3.7 "ENGINE TURBO" + DEEP AUDIT FIXES ringkasan:
- ENGINE 3,5-4× LEBIH CEPAT (output terverifikasi IDENTIK vs v3.6):
  * fn_running_stock_grouped vektor (global segmented cumsum):
    6,68s → 0,19s di real-data (36×); 6 edge-case sintetis ==
    implementasi lama (termasuk kasus baris bulan-lalu ber-net ≠ 0
    yang terlewat benchmark awal — tertangkap unit-test).
  * InformationGrouped vektor (pre-dedupe + agg C-level):
    6,7s → 0,05s (130×); 0/80.069 grup beda di real-data.
  * Reader rekap single-parse (jalur calamine): peek+full = 2× parse
    → 1× (peek nrows=8 di calamine mem-parse seluruh sheet juga).
  Pipeline real-data: 20,6s → 4,9s. Gunakan python-calamine (sudah di
  requirements.txt) supaya baca Excel pakai engine Rust.
- FIX 9 BUG fitur v3.6 (akar: setelah kolom disembunyikan, posisi
  display ≠ index logis values[] Treeview):
  * filter clone ⛶ membaca nilai kolom yang salah (kini: index logis)
  * auto-fit mengukur nilai kolom yang salah (kini: index logis)
  * filter '#0' clone pivot memakai text anak (metric) → semua baris
    hilang (kini: text parent = nama barang)
  * drill-down pivot ke resto/tanggal keliru setelah hide (kini:
    identify_to_column → nama kolom)
  * double-click copy Nomor/Nomor PO popup ambil kolom salah (2 popup)
  * toggle ✓ (Deviasi GR/PCS + Laporan + Follow Up) terpicu dari kolom
    lain setelah ✓ disembunyikan (kini: cocok nama kolom)
  * posisi popup filter melenceng (dulu ikut menghitung kolom
    tersembunyi + #0 phantom)
  * mirror hide/unhide clone↔sumber: state colmgr kini tersinkron
    (panel Kolom sumber tidak lagi menampilkan checkbox basi)

v3.6 ringkasan:
- BUG FIX KRITIS: tombol filter ⧩ di header TIDAK BISA DIKLIK dengan
  mouse (identify_column mengembalikan '#N' posisi-display sedangkan
  filter memakai nama kolom simbolik — tidak pernah match). Kini klik
  funnel membuka popup di SEMUA tabel, termasuk saat ada kolom
  tersembunyi. Clone ⛶ Perbesar juga kini punya filter + sort sendiri
  (sebelumnya ikon funnel tersalin tapi mati).
- HIDE/UNHIDE KOLOM: klik kanan judul kolom (Sembunyikan kolom ini /
  Tampilkan semua / auto-fit / filter) + tombol ◱ Kolom (panel
  checklist) — di semua tabel & window ⛶.
- AUDIT REKONSILASI DARI DATA APP: sheet '29 Rekap Barang Masuk' TIDAK
  dibaca. Tabel Rekap Selisih IN jadi SATU (segment dihapus) dengan
  kolom baru Hasil SO + Saldo + Hasil Audit + Catatan — semua bisa
  difilter ⧩. Catatan: kolom Barang Masuk terisi saat rekap memiliki
  input JENIS='BARANG MASUK'; selama belum diinput, baris ber-IN akan
  ditandai deviasi (sesuai logika).
- DEFAULT TANGGAL (v3.8): Pivot Table -31 s/d 31 = kolom tanggal
  lengkap tgl 25-31 BULAN LALU (label 25• s/d 31•, urut kronologis)
  lalu 1-31 bulan berjalan; Rekap Selisih IN 1 s/d 31 = bulan BERJALAN
  saja (tanpa bulan lalu).

Pipeline tetap dijalankan di thread terpisah; log stdout dipipakan lewat
queue thread-safe; Stop button mengirim stop_event yang dicek pipeline di
checkpoint major. Freeze-fix v2.1.1 (batch log + truncate) dipertahankan.
"""
import contextlib
import json
import os
import queue
import sys
import threading
import time
import warnings
from pathlib import Path

# Suppress openpyxl noise warnings (no default style, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

# Pastikan parent folder di sys.path agar `from src...` jalan
_BASE = Path(__file__).resolve().parent.parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from src.main import PipelineStopped, run_pipeline
from src.ui.deviasi_view import (
    DeviasiView,
    SharedACRThreshold,
    SharedPivotCache,
    SharedTanggalH,
    load_acr_threshold,
)
from src.ui.export_sheets import add_pivot_sheet
from src.ui.followup import FollowUpStore
from src.ui.followup_view import FollowUpView
from src.ui.in_selisih_view import InSelisihView
from src.ui.komparasi_deviasi_view import KomparasiDeviasiView
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.nominal_deviasi_view import NominalDeviasiView
from src.ui.nominal_resto_view import NominalRestoView
from src.ui.pivot_view import PivotTableView
from src.ui.rincian_po_view import RincianPoView, _resto_name
from src.ui.theme import (
    C_AMBER,
    C_BG,
    C_CARD,
    C_GREEN,
    C_HEADER,
    C_ORANGE,
    C_RED,
    C_TEXT_MUTED,
    apply_theme,
    font,
)
from src.ui.widgets import (
    AccentButton,
    DangerButton,
    GhostButton,
    KpiCard,
    KpiRow,
    LoadingOverlay,
    SegmentBar,
    Spinner,
    StatusBar,
    Toolbar,
    fmt_int_id,
    gc_shield_acquire,
    gc_shield_release,
    make_log_console,
    make_tree,
    run_async,
)

# --- Konstanta UI -----------------------------------------------------------
APP_TITLE = "Stock Monitoring"
APP_VERSION = "3.9.34"  # v3.9.34 — kolom Nominal + tab 🧮 Nominal Deviasi
# v3.9.34 (user: kolom Nominal di Deviasi GR/PCS + Komparasi + tab Σ per
# resto):
# (1) kolom Nominal (Harga 41.09 × Qty Deviasi) di tab 📦 Deviasi GR &
#     🧩 Deviasi PCS — kolom Out_H/BK_H dihapus dari tampilan;
# (2) kolom Nominal di mode ⚖ Komparasi File Deviasi (harga × GR Saat
#     Ini);
# (3) TAB BARU 🧮 Nominal Deviasi — Σ (harga × qty deviasi) PER RESTO +
#     baris TOTAL + double-click resto → popup rincian per barang
#     (user: "ada tab nominal Deviasi, isinya total sum dari nama barang
#     kayak di laporan sampel kolom nominal deviasi, yang dapat dari
#     harga × kuantitas deviasi, cuman ini disum per resto");
# (4) helper bersama src/ui/nominal_common.py — SATU sumber kebenaran
#     perhitungan nominal (mode 💰 Nominal (H) + kolom GR/PCS +
#     Komparasi + tab 🧮);
# (5) app meneruskan harga_map/konversi_map (audit_result pipeline) ke
#     deviasi GR/PCS + komparasi + nominal + tab 🧮 Nominal Deviasi.
# v3.9.33 — AUDIT FIX WAVE (Task 48: deep audit 6 agent → 8 HIGH / 31 MED / ~54 LOW):
# (1) clone ⛶ basi ditutup saat re-render + gen-guard (toggle ✓ baris salah);
# (2) fn_9901 dedup baris duplikat lintas sheet/file + log per-sheet;
# (3) filter ⧩ Harga Nominal diperbaiki (mapping 'Harga Tampil');
# (4) font tema lazy-resolve (fallback tidak lagi terkunci sejak import);
# (5) _on_pipeline_done isolasi error per-view + pre-flight folder data;
# (6) H=1 kini resolve SO bulan lalu (key 0 → -1) + saldo-only H<=3;
# (7) Qty PO Menunggu campur satuan → jumlah terkonversi saja;
# (8) konversi_satuan first-match + in_selisih cache race + Nominal pending/busy/TOTAL pin;
# (9) Ctrl+C salin baris multi-select (semua tabel) + Salin Log + ☑ sync lintas tab;
# (10) kolom guard fn_3224/2205/4215 + key Sheets config dihubungkan + ffill kategori per-file;
# (11) README Cara Pakai rewrite + SETUP.bat cek errorlevel + MULAI.bat pythonw.
# v3.9.32 (user: 6 permintaan — "YA KERJAKAN SEMUA DAN PUSH TO GIT HUB"):
# (1) MULTI-SELECT SEMUA TABEL (user: "kenapa aku tidak bisa select ya
#     untuk semua data?"): semua tree selectmode browse → EXTENDED +
#     binding Ctrl+A pilih semua baris (rekursif utk tabel hierarki
#     pivot; Ctrl+Klik tambah/lepas, Shift+Klik rentang) — dulu semua
#     tabel hanya bisa seleksi BARIS TUNGGAL. Interaksi lama (double-click
#     detail, klik ✓, klik-kanan) tak berubah; clone Layar Penuh & popup
#     ikut (widgets.enable_multi_select).
# (2) POPUP DETAIL TAB PIVOT DIPERBESAR (user: "popup di tab pivot ada
#     deviasinya — terlalu kecil, besarkan lagi dan HAPUS tombol
#     perbesar popup pivot"): DetailsPopup kini ±90% layar adaptif
#     (sebelumnya 1100×540; clamp posisi ke layar; minsize tetap 800×320)
#     + tombol ⛶ Perbesar & item menu-nya DIHAPUS KHUSUS jalur pivot
#     (param show_maximize=False; jalur laporan/komparasi/follow-up tetap
#     punya tombol — popup mereka ikut membesar).
# (3) BARANG 42.17-ONLY TAMPIL DI DEVIASI GR/PCS (user: "BUMBU PASTA KUAH
#     hanya ada di 42.17, tidak muncul — apakah lookup cuma dari Deviasi
#     Weekly, tidak dua arah dari 42.17?"): akar = fn_4217 HARDCODE
#     Tanggal=1 → pasangan saldo-only (tanpa rekap SO/IN/out) tak pernah
#     masuk window analisa H±2 (H>3) + pivot_table membuang SATUAN NaN.
#     FIX: (a) baris ('2.SALDO AKHIR', t=1) pasangan TANPA baris window
#     selalu ikut mask + Sistem pasangan itu = saldo 42.17 (Deviasi =
#     0 − saldo — selisih nyata); (b) SATUAN pasangan tanpa rekap diisi
#     dari kolom 'Nama Satuan' file 42.17 (fallback; rekap tetap menang).
#     Pasangan ber-window TIDAK tersentuh (nilai tabel tak berubah).
# (4) FILTER KATEGORI 42.17 LEBIH AWAL (user: "filter data 42.17 pakai
#     kolom kategori barang [whitelist 5 kategori]"): fn_4217 membaca
#     kolom Kategori Barang sebagai kolom id SEBELUM melt (dulu kolom
#     kategori/satuan ter-melt jadi pseudo-baris resto → terbuang senyap)
#     + ffill header grup + whitelist config "KategoriBarang4217"
#     (default: 00.COST, 01.COST-PACKAGING V.2, 01. COST-PACKAGING-TIDAK
#     BOLEH, 10.FOOD [BUMBU|RM|WIP]-COM V.2 — 5 kategori produksi +
#     varian lama; prefix-match case/whitespace-insensitive; file tanpa
#     kolom → tanpa filter; hasil 0 baris → auto-bypass + peringatan).
#     Log '4217 kategori filter: N/M baris lolos'.
# (5) HARGA 41.09 (user: "harga dari file 4109 (41.09) folder 09.Harga
#     [alamat bisa diubah] — kolom harga = Nilai/Kuantitas Saldo Akhir"):
#     modul BARU fn_4109 (header 2 baris dideteksi per NAMA — bukan
#     posisi tetap; subtotal 'Total Nama Barang'/'Total Kategori Barang'
#     dibuang; kategori ffilled; Qty=0 → harga NaN guard; file contoh
#     user 4109.xlsx: AIR MINERAL 1.246,35/BOTOL, GULA 18,25/GR) →
#     audit_result['harga_map'] {barang: (harga, satuan)} GLOBAL +
#     audit_result['konversi_map'] (peta rasio v3.9.31).
# (6) MODE BARU '💰 Nominal (H)' tab 📋 Laporan Deviasi (user: "tab baru
#     Nominal = Harga × kuantitas deviasi, per barang + total"): baris
#     per pasangan (Nama Barang · Resto · Satuan · Harga · Qty Deviasi ·
#     Nominal; qty deviasi = 3.DEVIASI tanggal H — nilai kolom Deviasi
#     tab GR) + baris TOTAL (jumlah qty + nominal; style khusus) + chip
#     total di kartu Filter. HARGA DINORMALISASI ke satuan rekap via peta
#     rasio (harga41 × rasio(rekap)/rasio(41.09) — analisis data real:
#     176/187 match, 5 beda seperti MUTIARA BOBA KG-vs-GR; tanpa
#     harga/rasio → tampil berpenanda '*' & nominal '-', tak dihitung ke
#     total). H bersama (chip read-only + auto-refresh); urutan default
#     |Nominal| menurun; minus merah per-cell; sort parser Indonesia;
#     filter ⧩ + ⛶ + ⤢ + ◱ + ↔.
# v3.9.31 (user: "Kolom Kuantitas di Rincian PO atau file 3243 itu masih
# satuan besar bukan satuan kecil seperti di sheet barang masuk ... air
# mineral di rincian po pakai satuan karton dan sheet barang masuk botol
# ini jadi tidak match waktu cari deviasi murni karna PO belum update
# penerimaan sistem. Solusi: ambil konversi per satuan pada 2 file yaitu
# 32.24 di kolom Rasio Satuan dan Satuan ... dan file 4205 juga pakai
# kolom Rasio Satuan dan #Sat. Kirim" + konfirmasi "tampilkan nilai
# terkonversi" & fallback qty as-is berpenanda): PETA KONVERSI SATUAN
# {(barang, satuan): rasio} + {barang: satuan terkecil} dibangun DI
# MEMORI dari baris IN transaksi aktual (TANPA file master excel
# tambahan — selalu segar): fn_4205 + fn_3224 kini ikut membaca kolom
# 'Rasio Satuan' + '#Sat. Kirim'/'Satuan' + '#Sat. Terkecil' (resolusi
# defensive beda versi export) → dibakukan SATUAN DOK / RASIO SATUAN /
# SATUAN TERKECIL (kolom ekstra tak ikut pivot append1 — pola SOURCE IN
# v3.9.29) → append1 konversi_out (build_konversi_map; konflik rasio
# dihitung utk log) → KEDUA varian audit: qty PO Menunggu = Kuantitas ×
# rasio[(barang, Satuan PO)] → SATUAN TERKECIL — apple-to-apple dgn
# Selisih/Saldo (sisa -120 BOTOL vs PO 5 KARTON = match 120 BOTOL kini
# KELIHATAN; verifikasi data real 42.05: identitas Kuantiti Terima =
# #Qty Kirim × Rasio 4.591/4.591, 0 konflik rasio, rasio konsisten
# lintas resto → join key Nama Barang saja). Lookup gagal → qty PO
# as-is + penanda '*' di catatan (disetujui user); catatan berlabel
# satuan '(qty 120 BOTOL)'; aturan implisit (barang, satuan-PO ==
# satuan terkecil) → rasio 1 (70/152 barang real tanpa baris
# satuan==terkecil di 42.05); desc audit + hitungan 'tdk terkonversi'.
# Tab 🛒 Rincian PO TETAP tampilkan Kuantitas satuan PO asli (satuan
# dokumennya). Kompatibel: pemanggil tanpa peta → perilaku v3.9.30.
# v3.9.30 (user: "ya kerjakan semua dulu dan push to git hub" — konfirmasi
# atas analisis PO 'Menunggu diproses' 32.43: "PO sudah ada tapi penerimaan
# belum di-update di sistem → bisa jadi penyebab deviasi murni"): Rincian
# PO 32.43 kini dibaca SEKALIGUS TANPA filter KATEGORI (build_rincian_po
# semua_out — barang non-DEVIASI-master pun PO-nya ikut terbaca; query
# utama tab 🛒 tetap terfilter DEVIASI persis mirror M) → pasangan (resto
# dari Cabang PO '1370.MLGPAR'→'MLGPAR', barang) ber-Status Pesanan
# 'Menunggu diproses' (extract_po_pending, case-insensitive) diteruskan ke
# KEDUA varian audit (fn_audit._apply_po_menunggu — dipasang SETELAH engine
# VBA, pemanggil lama tanpa PO tak tersentuh): (1) kolom audit 'Qty PO
# Menunggu' (total qty PO menunggu pasangan — konstanta per pasangan);
# (2) catatan 'PO Menunggu: PO.xxx (qty 50) (+m)' di-append ke Detail &
# Catatan Audit HANYA baris DEVIASI MURNI pasangan itu (maks 2 nomor +
# hitungan sisa) — deviasi murni EXPLAINABLE (akan resolve saat PO
# diproses jadi RI) vs perlu audit fisik; (3) KPI 'dev_murni_po'. UI tab
# Rekap Selisih IN: KOLOM BARU 'PO Menunggu' (setelah Saldo; filterable/
# sortable) + KPI chip 'DEV MURNI · PO MENUNGGU' (amber) + opsi kolom
# export 'PO Menunggu' (numerik). PO menunggu = keadaan TERKINI (bukan
# transaksi bertanggal) → tidak difilter varian bulan.
# v3.9.29 (user: "nama barang + resto yang berasal dari 42.05 harusnya
# kategori internal. dari 32.24 eksternal dan 9901 juga eksternal ... aku
# mau ganti" + konfirmasi: campuran→'Campuran'; tanpa IN→kosong; MENGGANTI
# nilai source kiriman + "perbaiki animasi scroll seperti tidak smooth dan
# patah patah" + "hapus kolom kategori di tab deviasi gr dan pcs karna
# sudah ada filter di atasnya"): (1) SOURCE KIRIMAN kini DITURUNKAN per
# pasangan (Nama Barang × NAMA RESTO) dari SUMBER IN AKTUAL — query_in
# men-tag SEMUA baris IN dgn 'SOURCE IN' (dulu hanya detail); append1
# LANGKAH 5b _source_kiriman_per_pair: hanya 42.05/42.05-Lalu → 'Internal',
# hanya 32.24(-Lalu)/99.01 → 'Eksternal', campuran → 'Campuran', pasangan
# tanpa dokumen IN → kosong (None — mirror kolom Z 'Kiriman' sheet terhide
# 'Data Base Cek Deviasi' workbook referensi; verifikasi data referensi:
# IT.=Internal 3.682 baris / RI.=Eksternal 3.377 baris 100% konsisten, 985
# pasangan: 687 Internal / 273 Eksternal / 25 campuran). Merge di frame
# LEBAR → nilai konstan per pasangan terbawa ke format long; kolom master
# DBS Kategori 'SOURCE KIRIMAN' TIDAK diambil lagi (master tetap suplai
# KATEGORI + AKTIF/NON) → filter combobox pivot/popup/export kini
# Internal/Eksternal/Campuran. (2) SCROLL HALUS: enable_smooth_wheel BARU
# (dipasang enable_col_resize = semua tabel + clone ⛶ + popup) — 1 baris
# per notch (default Tk 3 baris = lompatan patah-patah) + akumulator delta
# pecahan utk trackpad/roda resolusi tinggi + 'break' mematikan binding
# kelas (tanpa dobel); CellColorOverlay (Tk 8.6) LABEL POOL (reuse label,
# bukan destroy/create = pop-in telat 1 frame) + reposisi SINKRON di
# _wrap_scroll saat frac berubah (label tidak 'melayang' di baris salah).
# v3.9.28 (user: "push to git hub dan perbaiki stock seharusnya dan hitung
# manual"): AKAR BUG BARU DITEMUKAN & DIFIKS — file .xlsb dibaca engine
# pyxlsb menghasilkan sel TANGGAL sebagai SERIAL MENTAH (46290 = 2026-09-25);
# pd.to_datetime lama membacanya sbg NANODETIK-EPOCH → SEMUA transaksi jatuh
# ke Tanggal=1 → In_H = 0 utk H>1 → "Stok Seharusnya" (W = SO(H-1)+IN_H−
# KIRIMAN_H−PENJUALAN_H) kelebihan potong IN & rasio |H−W|/|W| meledak →
# flag "Hitung Manual" PALSU (reproduksi: sheet '4  42 05' workbook user —
# 4.591 baris serial → 100% hari 1 pra-fix). FIX: helpers.to_datetime_robust
# (BARU) — nilai numeric dlm rentang serial Excel wajar (20000..80000) di-
# konversi via epoch 1899-12-30 (pecahan waktu ikut); date_to_day dibangun
# di atasnya (dipakai 42.05/32.24/22.05/42.15/9901); '#Tgl/Jam Pembuatan IT'
# (fn_4205 + queries 3224/3224-lalu) & kolom tanggal Rincian PO ikut robust.
# VERIFIKASI: pipeline mock 464.205 baris IDENTIK pra-fix (0 baris beda —
# file .xlsx dgn tanggal datetime tak tersentuh); .xlsb user via fn_buka_sheet
# → hari 1..26 tersebar benar (dulu 100% hari 1); fn_4205 dgn mock SERIAL →
# hari 25/30/27 + Tgl/Jam 24 Sep 18:00 benar; parity sheet DEVIASI GR H=25
# (mock + 32.24 eksternal): Hitung Manual program 3 = sheet 3 (overlap 3/3),
# Stok Seharusnya 794→12/1.405 (11 = dokumen ADA di raw 42.05 tapi TIDAK di
# pivot 'Barang Masuk' sheet — inkonsistensi internal workbook; 1 = rekap SO
# vs pivot 'SO BULAN INI' beda) — rumus program = rumus sheet (rekomputasi
# rantai LET dari nilai sheet sendiri: 0 mismatch).
# v3.9.27 (user: "pada rekap selisih in bisa mode hitung bulan lalu dan
# hanya hitung bulan ini. Tapi default hitung bulan ini aja" + "kondisi
# beda tanggal kok menghasilkan data kosong semua? cek file 01.1 CEK
# STOCK V2.xlsb bagian sheet Data Base Cek Deviasi KOLOM Y ... cek semua
# logika nya dan bandingkan dengan yang ada di program"):
# (1) MODE HITUNG tab 📤 Rekap Selisih IN — SegmentBar "MODE HITUNG":
#     "📅 Bulan Ini" (DEFAULT; audit varian bulan berjalan saja — baris
#     Tanggal negatif dibuang sebelum engine, mirror sheet
#     LAPORAN_DEVIASI tgl 1..31; rentang 1..31) | "📆 Lalu + Ini"
#     (audit varian penuh incl. bulan lalu; rentang -31..31). Kedua
#     varian dihitung pipeline SEKALI (audit_result + kunci
#     df_bulan_ini/kpi_bulan_ini/desc_bulan_ini); KPI chips + Saldo +
#     Hasil Audit ikut varian; ketik tanggal negatif → auto pindah
#     Lalu+Ini; Reset & data baru → default Bulan Ini.
# (2) CEK tab Deviasi GR/PCS DI-PORT ULANG PERSIS formula LET sheet
#     terhide 'Data Base Cek Deviasi' kolom Y (LET KondisiKosong/
#     Naikturun/HitungManual/TurunDrastis/KondisiACR; simulasi 2.120
#     baris = label sheet 128/129 eksak): kondisi 2 "Beda Tanggal"
#     J = KIRIMAN KELUAR (8.BARANG KELUAR; dari 9.ACR — bug port
#     pertama; bukti MLGPAR/ADONAN GORENG MEKAR sheet='Beda Tanggal',
#     app lama=''), aturan SO-stale v3.9.22 DIHAPUS (men-flag pasangan
#     ber-SO_H=0 — 'data kosong' — hingga mendominasi), kondisi 3
#     "Hitung Manual" stok = W sheet = SO(H-1)+IN−KIRIMAN−PENJUALAN
#     (dulu sistem+IN−ACR−BK → 266 flag palsu), Stok Seharusnya = W
#     sheet (dulu SO(H-1)−ACR; 794/1.405 baris beda). Gate sheet
#     IF(V="","",…) (Total ACR=0 → CEK kosong 47% baris + kaskade
#     #N/A tanggal di luar cakupan pivot → 'data kosong semua') TIDAK
#     direplikasi — app mengevaluasi kondisi apa adanya (gejala yang
#     user pertanyakan = mekanisme tsb; terdokumentasi docstring
#     deviasi_view).
# v3.9.26 (user: "potensi flip flop itu harusnya yang selisih nya
# dikit aja"): ARAH LABEL ANALISA 'Potensi Flip Flop' DIBALIK —
# audit 41-a (logika hanya di 2 titik komparasi_deviasi_view) +
# 41-b data real (87,9% pasangan flip = Parsial; aturan lama
# melabeli flip miring/noise [DEV 0,1 → GR −780] sbg 'Potensi Flip
# Flop' sedang cermin sejati [−9.525 → +9.551, selisih 26] cuma
# 'Berubah Arah'). DEFINISI BARU: pasangan flip (tanda DEV
# berlawanan) dgn SELISIH MAGNITUDO KECIL (disparitas <
# FFLOP_DISP_MAX 40% — Kategori Sempurna/Dominan; nilai bercermin ±,
# mis. −50 → +55: deviasi sama besarnya cuma pindah sisi → rawan
# bolak-balik) = 'Potensi Flip Flop'; disparitas ≥ 40% (Parsial —
# sisi dominan jauh lebih besar, mis. −100 → +10: deviasi nyaris
# hilang/membesar, arah benar-benar berganti) = 'Berubah Arah'.
# SATU konstanta FFLOP_DISP_MAX 0.40 utk TABEL TOP SELISIH
# (_top_aggregate) & PERUBAHAN ARAH (_render_flip + batas Kategori
# flip — FFLOP ⟺ Sempurna/Dominan, ARAH ⟺ Parsial; batas 0.40
# PERSIS mengikuti Kategori: strictly <). Prioritas np.select utuh
# (flip > Stabil); tanda sama tidak pernah FFLOP; label string,
# warna tag, filter, sort, export TIDAK berubah.
# v3.9.25 (user: "POP UP DI tab deviasi gr dan deviasi pcs perbesar
# lagi dan tambah kolom nomor po dan COM"): popup ringkas Deviasi GR/PCS
# (double-click baris) DIPERBESAR 880×480 → 1180×640 (minsize 820×340;
# judul wraplength 1020) + DUA kolom baru:
# (1) "Nomor PO" — nomor pesanan pembelian (PO......) baris 4.IN per
#     tanggal, split koma → dedup → urut → gabung (pola kolom Nomor
#     v3.9.22; IT. pemindahan biasanya tanpa PO → kosong);
# (2) "COM" — pemakaian harian per tanggal, formula PERSIS baris
#     6.PEMAKAIAN (COM) tab Pivot / 🚨 Anomali COM:
#         com(t) = so_prev(t) + IN(t) − BK(t) − SO(t)
#     _compute_com_series (deviasi_popup) = PORT laporan_deviasi_view.
#     _compute_com_matrix: kolom tanggal GLOBAL (union 4 JENIS — SALDO
#     AWAL/1.SO/4.IN/8.BARANG KELUAR — SEMUA pasangan di frame, persis
#     col_keys laporan; pasangan tanpa baris SO di kolom global t−1
#     dibaca 0); tanggal 1 → base SALDO AWAL pasangan bila ada (audit
#     fix v3.9.5, dibaca TANPA fill), fallback so_prev; parity 48/48
#     nilai vs matrix Anomali COM (diverifikasi test §35 langsung vs
#     matrix). Tanggal di luar kolom global (mis. hanya 2.SALDO AKHIR)
#     → COM kosong. Dihitung DALAM grup satuan yang diklik (FIX 35-b).
#     COM minus ikut merah PER CELL (Tk 9; fallback Tk 8 tag baris).
# v3.9.24 (user: "jika saat ini bulan oktober maka 1 periode nya mulai
# dari 26 september - 25 oktober nah untuk cek RI balancing berarti
# dengan NO. PO yang bukan bulan september dan oktober … AIR MINERAL
# punya resto TGRGEL transaksi tanggal 1 oktober ada RI RI.2026.10.10354
# dengan PO PO.2026.08.00571"):
# DEFINISI RI BALANCING DIPERBAIKI — dari "bulan Nomor RI ≠ bulan
# Nomor PO" (v3.9.19-23) menjadi PERIODE BISNIS 26→25: satu periode =
# tgl 26 bulan lalu s/d tgl 25 bulan ini (mencakup DUA bulan kalender).
# Dokumen RI tgl 1-25 → PO periodenya {bulan-1, bulan}; tgl 26-31 →
# {bulan, bulan+1} (wrap tahun Des↔Jan; tanggal bulan-lalu negatif
# dibaca absolut). Balancing = Nomor PO dari periode DI LUAR dua bulan
# itu — contoh user: RI 1 Okt ↔ PO Agu → balancing; RI 1 Okt ↔ PO Sep
# → BUKAN balancing (v3.9.19-23 SALAH FLAG kasus ini — PO bulan
# sebelumnya satu periode dgn RI-nya). Satu logika doc_codes._ri_
# balancing(nomor, po, tanggal) dipakai CEK kolom utama Deviasi +
# popup Rincian IN + Catatan Audit B1; tanpa tanggal valid (NaN/
# invalid) → fallback aturan lama bulan≠bulan (konservatif).
# v3.9.23 (user: "kerjakan poin 6 dan kerjakan semua poin B"):
# (1) POIN 6 — CEK "RI Balancing" DI KOLOM CEK UTAMA tab Deviasi GR & PCS:
#     pasangan barang×resto yang punya ≥1 dokumen IN dgn periode Nomor RI
#     ≠ periode Nomor PO (tanggal dokumen ≤ H) kini TERFLAG langsung di
#     tabel utama — dulu hanya terlihat di popup Rincian IN (harus buka
#     baris per baris). Prioritas: Promix 04 → RI Balancing → kondisi
#     pola numerik (Kosong/Tanggal/Manual/Drastis/ACR) — anomali
#     struktural dokumen (faktual) di atas heuristik pola; helper
#     diangkat ke modul bersama doc_codes.py (tidak diduplikasi).
# (2) SEMUA POIN B — CATATAN AUDIT OTOMATIS tab Rekap Selisih IN: kolom
#     Catatan Audit diperkaya catatan app per baris (di-append ke catatan
#     engine VBA, dipisah " | " — isi VBA tidak berubah): B1 RI
#     Balancing (nomor dokumen + bulan beda), B2 Nomor Dobel (input
#     ganda/sheet kembar), B3 Selisih IN ≠ 0 (arah & besar perbedaan),
#     B4 BM 0 padahal IN > 0 (input rekap belum diisi). Ikut ke 💾 Export.
# v3.9.22 — 7 permintaan user + deep audit semua perhitungan:
# (1) PER-CELL WARNA DI SEMUA VERSI Tk (user: "Saat ini disemua tab
#     warna masih tidak per cell tapi per row. coba cari alternatif
#     lain"): Tk 8.6 (Python standar Windows) tidak punya API tag cell
#     → ALTERNATIF overlay tk.Label per sel (CellColorOverlay,
#     widgets.py — virtual, event forwarding, double-click manual,
#     merge 2 tag; clone ⛶ & hierarki pivot didukung).
# (2) ANALISA KOMPARASI TUNGGAL (user: "hapus tab liga deviasi" +
#     "hapus arah minoritas" + "dead code nya juga hapus"): bagian
#     Minoritas & Liga dihapus penuh — tersisa Top & Flip.
# (3) CEK "Beda Tanggal" SO-STAEL (user: "Dikolom CEK analisa Beda
#     tanggal kok tidak ada ya"): pasangan dgn tanggal SO nonzero
#     terakhir < H terflag (belum SO tanggal analisa); prioritas
#     Promix 04 tetap pertama.
# (4) POPUP + KOLOM NOMOR (user: "Pop up di tab Deviasi GR dan PCS ada
#     Nomor nya juga Misal IT...... atau RI......"): nomor dokumen IN
#     per tanggal (dedup+urut+koma).
# (5) TANGGAL H DINAMIS (user: "Tanggal harusnya tanggal 26 bukan dari
#     tanggal 25"): H = tanggal SO nonzero terakhir saat data dimuat
#     (fallback 26; reset di ✕ Reset Filter; minggu komparasi 15..31 →
#     WEEK 4 — dulu 26..31 → "WEEK 5" tak pernah ada di file).
# (6) REKAP SELISIH IN default KATEGORI = Deviasi (user: "Rekap selisih
#     IN Default Kategori Deviasi") — di load & reset, tetap fleksibel.
# (7) DEEP AUDIT (user: "deep audit semua perhitungan apakah sudah
#     benar dan sesuai dan valid?"): BUG append1 pivot_table(dropna=
#     False) KOMBINASI KARTESIAN pasangan×tanggal (baris fantom) →
#     groupby+pivot (data real 768.000 → 527.528 baris); JENIS
#     case-drift dinormalisasi; export None → literal 'None' dibersihkan.
# v3.9.21 — 4 permintaan user:
# (1) AMBANG ACR to BOM (user: "di bagian ACR to BOM itu harusnya ada
#     threshold > 80% absolute dan aku bisa atur"): CEK kondisi ke-5 kini
#     |Deviasi| > (ambang/100) × Total ACR — dulu kaku > 100% × Total
#     ACR. Ambang default 80, spinbox "AMBANG ACR to BOM" di kartu Filter
#     KEDUA tab Deviasi GR & PCS (sinkron via SharedACRThreshold — pola
#     TANGGAL H); ubah ambang → pivot cache di-clear + recompute live;
#     nilai bertahan lintas sesi (settings.json, atomic write; file
#     hilang/korup → default 80 senyap).
# (2) PROMIX 04 PER-TANGGAL (user: "pada bagian CEK ada muncul nilai
#     Promix 04 di filter tapi kenapa data nya tidak ada?"): sumber SO
#     kini diresolve PER (pasangan × tanggal) atas baris rekap ber-NILAI
#     NON-NOL (append1 LANGKAH 9 merge per (pasangan, Tanggal); 'input
#     so harian' menang atas promix pada tanggal sama — hitungan manual;
#     baris template bernilai 0/NaN & sumber whitespace-only tidak
#     menentukan). deviasi_view membaca sumber baris 1.SO TANGGAL H —
#     label "Promix 04" muncul HANYA bila SO tanggal analisa BENAR
#     bersumber promix. Menggantikan resolusi pair-level "tanggal
#     tertinggi" yang rapuh: v3.9.19 bisa melabel SEMUA pasangan campuran
#     Promix (tie urutan baris — persis phantom yang user lihat);
#     v3.9.20 swing kebalikan (tak pernah Promix meski SO tanggal H
#     memang turunan promix — data real 01.1 CEK STOCK V2: 12 pasangan
#     promix di tgl 25 kini terlabel benar, 0 phantom).
# (3) TIDAK BERTABRAKAN dgn CEK lain (user: "Promix 04 bakal bertabrakan
#     gak logika nya dengan analisa CEK yang lain?"): prioritas tetap —
#     Promix 04 kondisi PERTAMA (SO sistem-turunan → pola naik/turun SO
#     tak bermakna); dgn resolusi per-tanggal label jadi AKURAT sehingga
#     pasangan so-harian dievaluasi CEK normal sepenuhnya.
# (4) MINUS PER-CELL LAPORAN DEVIASI (user: "nilai minus juga diberi
#     warna merah pada cell aja di tab laporan deviasi"): Anomali COM —
#     Median & Selisih vs Median kini ikut merah per-cell (dulu hanya
#     COM); Liga Deviasi — Rate minus ikut merah (⟺ DEV minus).
# v3.9.20 — DEEP AUDIT & FIX (5 agen audit + 5 agen fix): 1 BUG + 15 RISK diperbaiki + penuntasan "semua filter = data yang ada" (komparasi reset/popup · deviasi satuan/chrono/source · rincian NA/float/NaT/periode · pivot/FU/export · pipeline LANGKAH 9/sheet lalu/fn_4205)
# v3.9.20 — DEEP AUDIT & FIX (gelombang audit 34-a..34-e + fix 35-a..35-d,
# 25 perbaikan; 1 BUG + 15 RISK + 9 hardening/NIT):
# (1) KOMPARASI (35-a/audit 34-a): reset filter 4 tabel analisa (Top/Flip/
#     Minoritas/Liga) di SEMUA jalur reset tabel utama (load_data /
#     _load_paths / _close_file / ✕ Reset Filter — dulu filter basi
#     senyap → 0 baris di file baru); nilai popup filter tabel utama ⚖
#     + Arah Minoritas + Liga Deviasi kini BARIS YANG TAMPIL (param
#     fmt_fn di _filtered_analisa_series — penuntasan "berlaku untuk
#     semua filter"); 4 entri format kolom mati Risk/Bench dibersihkan.
# (2) DEVIASI + POPUP (35-b/audit 34-b): _hl_cells diinisialisasi di
#     __init__ (sort/reapply tag sebelum render pertama tidak lagi
#     AttributeError di Tk 9); popup ringkas memfilter SATUAN — angka
#     GR/PCS = BARIS YANG DIKLIK (dulu menjumlahkan lintas satuan);
#     _chrono_key float-safe (urutan 25•..31• benar utk Tanggal
#     float64); _so_source_lookup keep-LAST sort-Tanggal (preferensi
#     append1 LANGKAH 9 — baris berjalan menang); _compute_cek (kode
#     mati) dihapus penuh.
# (3) RINCIAN PO + RINCIAN IN (35-c1/audit 34-c+34-e): BUG clone ⛶
#     InSelisihView kini reapply tag neg per-cell (on_render_done —
#     dulu minus kehilangan warna di Layar Penuh); _resto_name pd.NA-
#     safe + float integral (1370.0 → "1370", dulu "0"); _fmt_date/
#     _fmt_datetime NaT-safe (dulu ValueError → tab mati); load_data
#     reset combo Cabang/Status (dulu filter basi → 0 baris senyap);
#     RI Balancing membandingkan PERIODE (tahun, bulan) dgn bulan
#     1-2 digit numerik — lintas-tahun-same-month kini terflag;
#     literal "None"/"nan"/"NaT" dibuang dari daftar nilai popup.
# (4) PIVOT + FOLLOWUP + EXPORT (35-c2/audit 34-e): popup Nama Barang
#     pivot = barang yang TAMPIL (RESTO mode Tanggal + SOURCE +
#     KATEGORI + rentang Tanggal + ☑ sembunyikan-baris-kosong; filter
#     sendiri dikecualikan); popup kolom FollowUp = baris tampil; F401
#     C_TEXT_MUTED dibersihkan; merah negatif pivot #CC0000 → #dc2626
#     (seragam 11 view); export sheet "Rincian PO" + kolom Nama Resto
#     (import _resto_name — tanpa duplikasi helper).
# (5) PIPELINE (35-d/audit 34-d): append1 LANGKAH 9 tie-break
#     DETERMINISTIK (mergesort + kunci sekunder bentuk-string SOURCE
#     DATA — tie → "input so harian" menang, konservatif utk CEK
#     Promix 04) + na_position="first" (NA-Tanggal tak pernah menang)
#     + SOURCE DATA di-strip (NA-safe); resolusi sheet folder bulan-
#     lalu: key dedikasi Sheets["Pemindahan4205Lalu"] + fallback
#     prefiks modul "#42.05"/"#32.24" (sheet lalu beda nama ≠ lagi 0
#     baris senyap — 32.24 & 42.05 konsisten); fn_4205 mode "lalu"
#     filter baris resto SEBELUM max_t (mirror persis fn_3224 — NA-
#     resto tak lagi menggeser jendela 5 hari).
# v3.9.19 — KOLOM ANALISA + HAPUS RISIKO/BENCHMARK + DEFAULT KATEGORI + NAMA RESTO PO + FILTER DATA-ADA + PROMIX 04 + 9.ACR + RI BALANCING
# v3.9.19 — 8 permintaan user:
# (1) KOLOM ANALISA (user: "tambah kolom baru untuk keterangan kenaikan
#     tertinggi, penurunan tertinggi, stabil, berubah arah, potensi
#     flip flop pada laporan deviasi tab TOP and FLIP. 1 kolom aja"):
#     bagian 📊 Top & Flip mode 📈 Analisa (tab 📋 Laporan Deviasi) —
#     tabel Top Selisih & Perubahan Arah kini berkolom ANALISA:
#     Kenaikan Tertinggi · Penurunan Tertinggi · Stabil · Berubah Arah
#     · Potensi Flip Flop (tanda berlawanan + disparitas ambang 40%
#     sama dgn Kategori flip; warna per-cell).
# (2) HAPUS BAGIAN (user: "hapus tab resiko flip dan bencmark"):
#     baris BAGIAN kini 3 bagian (Top & Flip · Arah Minoritas · Liga
#     Deviasi) — render/UI/metode ⚡ Risiko Flip & 💰 Benchmark
#     dihapus penuh.
# (3) DEFAULT KATEGORI (user: "secara default kategori terfilter ke
#     kategori Deviasi"): combobox KATEGORI tab Deviasi GR/PCS default
#     "Deviasi" (case-insensitive; fallback "Semua") saat load data &
#     ✕ Reset Filter.
# (4) NAMA RESTO DI RINCIAN PO (user: "tambahkan kolom nama resto di
#     rincian PO"): kolom baru di baris induk — dari Cabang PO
#     ("1370.MLGPAR" → "MLGPAR"), ikut filter header ⧩.
# (5) FILTER = DATA YANG ADA (user: "isi filter harus menampilkan data
#     yang ada aja bukan termasuk data yang tidak ada — berlaku untuk
#     semua filter"): daftar nilai filter header dihitung dari baris
#     yang TAMPIL (mode Satuan + KATEGORI + filter kolom lain — kolom
#     sendiri dikecualikan; perilaku AutoFilter Excel) di tab Deviasi
#     GR/PCS, Rincian PO, Rekap Selisih IN (juga rentang tanggal +
#     hanya-selisih), Anomali COM, dan tabel Top/Flip komparasi.
# (6) CEK "Promix 04" (user: "jika SO nya bersumber tanpa input so
#     harian maka tampilkan Promix 04"): SOURCE DATA REKAP MENTAH
#     JENIS SO ("input so harian" / "input promix 04 dine in" /
#     "take away") dibawa append1 per pasangan; CEK kondisi ke-0
#     (prioritas pertama — pola CEK lain tak bermakna utk SO turunan
#     sistem): bukan "input so harian" → "Promix 04".
# (7) ISTILAH 9.OUT → 9.ACR (user: "ganti istilah 9.OUT menjadi
#     9.ACR"): JENIS penjualan 22.05 kini "9.ACR" (rename_map append1,
#     METRICS pivot, deviasi/komparasi/tests) — data mentah tak berubah.
# (8) CEK "RI Balancing" (user: "jika bulan PO dan bulan RI tidak sama
#     ... kasih aja keterangannya RI Balancing"): popup Rincian IN
#     (tab 📤) berkolom CEK — dokumen RI.2026.10.10354 vs
#     PO.2026.08.00571 (struktur PREFIKS.TAHUN.BULAN.NOMOR): bulan
#     beda → "RI Balancing" (amber per-cell).
# v3.9.18 — FOKUS RESTO 1. DEVIASI WEEKLY + POPUP RINGKAS + KOLOM + HIGHLIGHT (tab Deviasi GR/PCS)
# v3.9.18 — 5 permintaan user utk tab 📦 Deviasi GR & 🧩 Deviasi PCS:
# (1) FOKUS RESTO (user: "resto yang dianalisa hanya berfokus pada
#     resto yang ada di folder 1. DEVIASI WEEKLY aja jangan semua"):
#     pivot hanya memuat pasangan (barang × resto) yang RESTOnya punya
#     data rekap berjalan — JENIS 1.SO / 5.BARANG MASUK dgn Tanggal
#     POSITIF (= sheet '1  DEVIASI WEEKLY' folder RekapBerjalan; rekap
#     bulan lalu bernomor NEGATIF & berasal dari folder lain — tidak
#     ikut menentukan scope). Resto yang hanya ada di sumber app
#     (32.24/42.05/9901/22.05/42.15) dikeluarkan — barisnya dulu
#     menampilkan Deviasi = 0 − Sistem = minus palsu.
# (2) LOOKUP BARANG DUA ARAH (user: "look up nama barang ini pakai dua
#     arah ... tidak hanya barang di folder deviasi weekly aja tapi
#     juga sebaliknya"): barang TIDAK difilter — utk resto rekap,
#     barang ber-SO rekap MAUPUN barang yang HANYA ada di data app
#     (IN/OUT/SALDO AKHIR saja, SO = 0) keduanya tampil.
# (3) POPUP RINGKAS (user: "pop up di deviasi GR ataupun PCS hanya
#     tampilkan: nama barang, nama resto, nilai saldo akhir, nilai SO,
#     nilai IN, nilai deviasi"): double-click kini membuka popup
#     ringkas BARU (src/ui/deviasi_popup.py — judul 'Nama Barang —
#     Nama Resto (satuan)', tabel per Tanggal hanya Tanggal · Saldo
#     Akhir · SO · IN · Deviasi; '25•' = bulan lalu; baris H latar
#     lembut; minus merah per-cell + fallback Tk 8). Popup source
#     rows lama (JENIS/Nomor/Nomor PO/Tgl-Jam/KATEGORI/SOURCE) TIDAK
#     lagi terbuka dari tab ini — tetap dipakai tab Pivot/Laporan.
# (4) KOLOM DIHAPUS (user: "tab deviasi GR dan PCS hapus kolom: max
#     dev, acr, total acr"): kolom Max Deviasi / ACR / Total ACR
#     dihapus dari TAMPILAN GR & PCS — hitungan internal TETAP persis
#     v3.9.6 (CEK kondisi ke-5 'ACR to BOM' · Dev to BOM% · Stok
#     Seharusnya · snapshot loss_bom Follow Up tetap benar).
# (5) HIGHLIGHT (user: "highlight kolom deviasi dan kolom SO H"):
#     latar lembut #fef3c7 di SEMUA sel kolom Deviasi & SO_H via tag
#     cell (Tk 9 — terukur pixel: bg cell-tag menang atas bg
#     evenrow/oddrow; fg minus merah tetap hidup di atasnya; dipasang
#     ulang setelah sort/filter/clone). Fallback Tk 8: tanpa tint
#     kolom. Legenda + chip 'kolom Deviasi/SO_H'.
# v3.9.17 — (1) SUMBER IN BARU (permintaan user: "tambahkan juga di
# alamat C:\KERJA\1. RESTO\9.NEW QUERY\4.1 4205 Bulan Lalu — ini
# sebagai penambah IN untuk periode 25-31 bulan lalu sama seperti 32.24
# bulanlalu"): folder baru config Pemindahan4205Lalu dibaca
# fn_4205(mode="lalu") — MIRROR PERSIS fn_3224 "lalu": 5 hari terakhir
# file bulan lalu (Tanggal >= maxT-4) + Tanggal dinegasikan (hari
# negatif = bulan lalu) → masuk query_in sebagai sumber IN tag
# "42.05 (Bulan Lalu)" + Qty SJ audit (Kiriman HO / export) + popup
# Rincian IN (grup tabel & chip teal). Folder kosong/tidak ada → 0 baris
# senyap (tidak wajib ada tiap bulan). (2) FOLLOW UP MINUS PER-CELL:
# tab ☑ Follow Up kini mewarnai HANYA sel bernilai minus (semua kolom
# numerik — Tk 9 `tag cell`; fallback Tk 8 tag baris, konsisten view
# lain sejak v3.9.2) — dulu tab ini TIDAK punya jalur per-cell: satu
# Deviasi minus mewarnai SELURUH baris + tag 'negative' (menang
# pertama) menimpa warna status resolved/pending; sort & clone ⛶
# memasang ulang tag (pola FIX B-03/B-12).
# v3.9.16 — TOP SELISIH: ABSOLUT + MEDIAN MULTI-FILE (permintaan user,
# khusus mode 📈 Analisa di tab 📋 Laporan Deviasi — tabel utama ⚖ &
# bagian analisa lain TIDAK berubah):
# (1) ABSOLUT: Selisih = |GR Saat Ini| − |DEV Lalu| (kedua nilai
#     diabsolutkan DULU — pembalikan tanda −50 → +30 tidak lagi
#     menggembungkan selisih: dulu 80 kini 20); kolom DEV Lalu / GR
#     Saat Ini tetap NILAI ASLI; Status MATCH/SELISIH (khusus tabel
#     Top Selisih) ikut toleransi Selisih absolut.
# (2) MEDIAN MULTI-FILE: file deviasi >1 → nilai Lalu per pasangan
#     (resto×bahan×minggu sama) = MEDIAN antar-file — SATU baris per
#     pasangan (bukan satu baris per file); yang ditampilkan nilai
#     median saja; Periode 'Median n file · Minggu' (≥2 file) /
#     'BULAN · Minggu' (1 file); kolom Periode kini kolom NYATA.
# v3.9.15 — GELOMBANG 1 (adopsi rumus repo Inventory-Control user; 4
# analisa baru sebagai BAGIAN di mode 📈 Analisa — baris "BAGIAN"
# SegmentBar: Top & Flip · Risiko Flip · Arah Minoritas · Liga Deviasi ·
# Benchmark; hanya bagian AKTIF yang dirender — pola malas v3.9.14,
# komputasi VEKTOR penuh):
# (1) ⚡ RISIKO FLIP PER BAHAN: skor = min(100, 30×Sempurna + 10×Flip),
#     Level TINGGI/SEDANG/RENDAH; klik-2× → popup resto kontributor.
# (2) 🧭 ARAH MINORITAS PER BAHAN: resto yang arah DEV-nya melawan
#     mayoritas (mayoritas ketat) — kandidat salah-input; klik-2× →
#     popup resto minoritas.
# (3) 🏆 LIGA DEVIASI-RATE PER BAHAN: rate = |DEV|/|BOM| per resto;
#     baseline median+MAD → robust-z = (rate−median)/(1,4826×MAD);
#     guard ≥5 resto ber-BOM & MAD>0; DEV 0 ikut populasi tak diranking.
# (4) 💰 BENCHMARK OPPORTUNITY: per resto (kelompok = 3 huruf awal kode
#     resto) loss = Σ|DEV<0|; opportunity = max(0, loss − median
#     kelompok) + total.
# Analisa per-periode (2/3/4) = BULAN TERBARU + SATU minggu snapshot
# (minggu yang memuat H — minggu file kumulatif: menjumlah lintas minggu
# = menghitung ganda).
# v3.9.14 (permintaan user: "tab analisa kenapa lemot sekali" deep audit
# performa + "week di tab analisa harusnya menyesuaikan kolom H — jika 7
# berarti week 1" + "ganti istilah app menjadi Saat ini dan File menjadi
# Lalu") — SEMUA di komparasi_deviasi_view.py:
# (1) PERF: analisa dirender MALAS (hanya saat mode 📈 aktif — dulu ikut
#     dirender walau tersembunyi: ±4,8 dtk freeze PER refresh di file
#     40rb baris); flip VEKTOR (sort+shift — dulu groupby+sort per grup
#     4,7 dtk → ±50ms, hasil identik); nilai app per baris via MERGE
#     vektor (dulu loop Series.get 2,9 dtk → ±60ms; terverifikasi
#     identik); Top Selisih tanpa iterrows.
# (2) MINGGU: Top Selisih & Perubahan Arah difilter minggu yang MEMUAT
#     H (H=7 → WEEK 1) — konsisten tabel utama.
# (3) ISTILAH: kolom *File → *Lalu, *App → *Saat Ini; status 'TIDAK ADA
#     DI DATA APP' → 'TIDAK ADA DI DATA SAAT INI'.
# v3.9.13 (6 permintaan user + adopsi rumus repo Inventory-Control user):
# (1) FILTER "HASIL SEARCH = PILIHAN": Enter di popup filter header
#     (semua tab) menjadikan HASIL PENCARIAN sebagai seleksi — 0 hasil =
#     0 baris (perilaku Excel) + operator teks (Mengandung/Diawali/
#     Diakhiri/Tidak mengandung) + tombol ↔ Balik (invert). State
#     seleksi EKSAK (nilai >3000 non-materialized ikut terhitung);
#     uncheck-semua kini 0 baris (dulu tampil semua).
# (2) FILTER KATEGORI di tab 📦 Deviasi GR & 🧩 Deviasi PCS: kolom
#     KATEGORI (data DBS sudah ada di pipeline) + combobox KATEGORI di
#     kartu Filter (post-pivot — SharedPivotCache tetap 1× GR+PCS).
# (3) PATH FILE DEVIASI tersimpan & BISA DIUBAH: entry editable
#     (multi-file dipisah ";") + 📂 multi-select + ↻; komparasi_last.json
#     {"paths": [...]} + AUTO-LOAD file terakhir saat tab terlihat.
#     FIX BUG v3.9.10: .with_suffix pada str → json TIDAK PERNAH tersimpan
#     sejak v3.9.10 (path file deviasi "tidak pernah teringat").
# (4) KOLOM LAPORAN DEVIASI (permintaan "hapus kolom H, minggu juga
#     hapus, Dev to bom harusnya persen"): kolom Minggu & H DIHAPUS dari
#     tabel (16→14; data internal tetap utk filter minggu/join/popup);
#     DEV App kini %TO BOM — App = DEV·App / |BOM·App| (persen — dulu
#     kuantitas; konsisten %TO BOM File & Dev to BOM% tab Deviasi).
# (5) MODE 📈 ANALISA (adopsi rumus repo Inventory-Control user):
#     Top Selisih (peringkat |GR App − DEV File| tertinggi, Top-N) +
#     PERUBAHAN ARAH ("flip": bulan berurutan MINGGU SAMA dengan tanda
#     DEV berlawanan — minus bulan lalu → surplus sekarang; Disparitas
#     = |P1+P2|/max(|P1|,|P2|): Sempurna <10% / Dominan 10–40% / Parsial
#     ≥40%; urut disparitas naik).
# (6) MULTI-FILE DEVIASI: 📂 askopenfilenames — semua file diparse di
#     worker & digabung; BULAN ikut dedup-key (baris bulan lain TIDAK
#     dibuang); default tabel = BULAN TERBARU (checkbox "Tampilkan semua
#     bulan"); label info per-file; file gagal dilewati (dilaporkan).
# v3.9.12 — TAB 🎯 PARETO DIHAPUS (user: "hapus tab pareto dan dead code nya")
# v3.9.11 (TUNTAS SISA TEMUAN AUDIT — "kerjakan semua & repo pribadi"):
# (0) P0 D-11 DIEKSEKUSI: repo GitHub anandategarch/Stock-Monitoring
#     kini PRIVATE (permintaan user "repo untuk pribadi aja") — workbook
#     produksi + objek 2205.xlsx di history tidak lagi dapat diakses
#     publik; BFG rewrite tidak diperlukan.
# (1) FIX B-21 sort kini BERINDIKATOR ARAH di heading (↓ menurun / ↑
#     menaik; panah lama kolom lain dibersihkan) — sebelumnya sort via
#     popup ↕ mengubah urutan tanpa jejak kolom mana yang terurut.
# (2) FIX B-14 toggle filter di clone ⛶ tidak lagi MENGEMBALIKAN urutan
#     sort (rebuild dulu dari cache urutan asli; sort terakhir kini
#     dijalankan ulang SEBELUM reapply tag per-cell).
# (3) FIX B-09 sort_tree_by_column untuk tree BERHIRARKI: jalur baru
#     tree.move (subtree + text #0 + state open terjaga; jalur lama
#     delete+reinsert MENGHAPUS anak) — latent utk caller saat ini
#     (semua datar), jalur flat O(n) tetap + kini pertahankan text/open.
# (4) FIX B-18 mirror kolom ⛶ DUA ARAH: hide/unhide kolom di tabel
#     UTAMA kini tercermin juga di window clone yang terbuka (dulu satu
#     arah clone→source saja).
# (5) FIX B-17 cursor "watch" LoadingOverlay BER-REFCOUNT per toplevel
#     — overlay pertama yang selesai tidak lagi me-reset cursor saat
#     overlay kedua masih loading; + klaim dilepas saat widget destroy.
# (6) FIX B-16 TableExpander.restore iterasi REVERSE — ≥2 target pack
#     berturut di akhir urutan tidak lagi terpasang TERBALIK.
# (7) FIX B-12 validated_tgl_entry + _on_tanggal_change Selisih IN:
#     pecahan ("7.9") DITOLAK warning+revert — dulu dilantai SENYAP
#     menjadi 7 oleh int(float()).
# (8) FIX B-11 EmptyState frame center ADAPTIF (clamp 520×260) — dulu
#     fixed 520×260: konten CTA terpotong di jendela sempit.
# v3.9.10 (DEEP AUDIT UI/UX ROUND 2 — 4 agent paralel, 37 temuan):
# (1) P1 RACE & ROBUSTNESS: FIX A-01 Stop→MULAI kini menghentikan
#     benar (guard worker masih hidup — dulu 2 pipeline bisa jalan
#     paralel & stop_event.clear() membatalkan Stop); FIX D-01 worker
#     capture data/H di awal compute (cache poisoning — data basi
#     senyap saat pipeline selesai di tengah refresh view); FIX C-02
#     rincian_po & details_popup kini punya on_error (view tidak lagi
#     mati permanen setelah 1 exception — kelas fix B-01 v3.9.1);
#     FIX B-01 sort Rekap Selisih IN pakai parser angka Indonesia;
#     FIX D-04 file Excel terkunci/hilang di-skip → KPI/status kini
#     memberi tahu (dulu "SELESAI" polos menutupi data parsial).
# (2) P2 TABEL: FIX B-02 tag minus/merah per-cell bertahan di clone ⛶
#     setelah filter (4 view + popup detail); FIX B-03 sort Selisih
#     IN tidak lagi menghapus tag minus; FIX B-04 bind add="+" —
#     auto-fit double-click tepi kolom hidup lagi di semua tabel;
#     FIX B-05 filter header >3000 nilai: nilai hasil pencarian di
#     luar cap kini DAPAT dicentang (checkbox lazy); FIX B-06 gc_shield
#     thread-safe (Lock); FIX B-07 filter clone saat copy awal (cancel
#     batch); FIX B-08 sort saat render batch → antre (3 view);
#     FIX D-03 followup render race (cancel insert lama).
# (3) P2 SHELL: FIX A-02 tombol Export disabled kini tampak DIM
#     (set_enabled — fix v3.9.1 akhirnya dipakai di semua call-site);
#     FIX A-03 DPI-awareness Windows 125%/150%; FIX A-04 Ctrl+Tab
#     navigasi tab (notebook.enable_traversal); FIX A-11 routing tab
#     berbasis widget (bukan index — tab disisipkan tak merusak).
# (4) P3 KONSISTENSI: FIX C-03 format angka Indonesia di Rincian PO &
#     popup detail (dulu EN "1,234.5"); FIX C-04 minus merah per-cell
#     di tabel Rekap Selisih IN; FIX C-06 sisa frasa instruksi dipangkas;
#     FIX C-10 footer "rows"→"baris" + fmt Indonesia; FIX C-07/C-08
#     deviasi unsubscribe-H + refresh saat tersembunyi cukup dirty;
#     FIX D-05/D-06 config & komparasi_last atomic write; FIX A-09
#     literal warna → token theme.
# v3.9.12 (TAB 🎯 PARETO DIHAPUS — user: "hapus tab pareto dan dead
# code nya"):
# (1) tab 🎯 Pareto (v3.9.9) DIHAPUS dari notebook — app kembali 9 tab;
#     index tab setelahnya bergeser -1 (routing berbasis widget A-11 —
#     tidak ada index angka ajaib yang perlu digeser).
# (2) DEAD CODE dihapus penuh: src/ui/pareto_view.py (ParetoDeviasiView
#     — subclass DeviasiView, 823 baris) + write_pareto_sheet() section
#     4 di export_sheets.py + integrasi app.py (frame tab, notebook.add,
#     _build_pareto_tab, entry _tab_views, load_data fan-out).
# (3) Fitur lain TIDAK tersentuh: Deviasi GR/PCS tetap memakai
#     SharedPivotCache + SharedTanggalH; ✓ Follow Up dari tab lain
#     tetap jalan; export sheet lain tetap utuh.

# v3.9.6 (3 permintaan user sekaligus):
# (1) "tambah kategori Deviasi pada tab Deviasi PCS dan GR" — 5 kolom
#     baru (mirror sheet DEVIASI GR/PCS workbook asli): Max Deviasi ·
#     ACR (rata-rata penjualan harian = Σ 9.ACR 1..H / H) · Total ACR
#     (BOM per barang×resto = Σ penjualan 1..H) · Dev to BOM% (= Deviasi
#     / Total ACR — "Loss Surplus to BOM") · Stok Seharusnya (= SO(H−1) −
#     ACR) + CEK kondisi ke-5 "ACR to BOM" (|Deviasi| > Total ACR —
#     melengkapi port formula LET yang dulu 4/5 kondisi) + parser sort
#     Indonesia utk semua kolom numerik.
# (2) "Tab selisih in jika tanggal 1 pembanding SO nya SO bulan lalu" —
#     urutan baris audit kini KRONOLOGIS (bulan lalu 25•→31• lalu 1..31);
#     dulu sort numerik membalik urutan bulan lalu sehingga delta SO di
#     tanggal 1 membanding SO tgl 25• (BUKAN SO terakhir bulan lalu).
# (3) "Format Follow UP Seperti File Sample" — tabel + export tab ☑
#     Follow Up kini persis sheet Follow UP file asli: Resto · Nama
#     Barang · SO per tanggal (H-2..H+2, heading angka tanggal) ·
#     Sistem · Deviasi · Loss Surplus to BOM · Keterangan · SO · DEVIASI
#     · Selisih · Selisih Deviasi · Cek FU · PIC (+ pelacakan app).
# v3.9.4 (permintaan user: "Di file sampel kan ada Dev to bom ini kok gak
# ada ya? Padahal data udah lengkap 2205 itu bom. Aku barusan upload file
# deviasi. Nah aku mau compare file deviasi itu dengan yang deviasi di
# Tab deviasi GR terus coba cek kolom status week 1 itu sama dengan 7
# week 2 = 14 dan week = 25. Itu buat kolom h."):
# (1) TAB 📋 LAPORAN DEVIASI kini punya 2 MODE (SegmentBar):
#     ⚖ Komparasi File Deviasi (BARU — default) dan 🚨 Anomali COM (v3.9.3
#     dipertahankan, tinggal ganti segmen).
# (2) MODE KOMPARASI: pilih file deviasi resmi (mis. "20.AGUSTUS 2026.xlsx"
#     — RESTO/NAMA BAHAN/STATUS BULAN/QTY BOM/QTY COM/QTY DEVIASI/% TO
#     BOM). Tiap baris file dibandingkan sisi-app pada KOLOM H menurut
#     STATUS BULAN: WEEK 1→H 7 · WEEK 2→H 14 · WEEK 3/4→H 25 (permintaan
#     user; file sampel memakai WEEK 4, minggu = CUT-OFF KUMULATIF dari
#     tgl 1 — WEEK 2 ≈ 2× WEEK 1, konsisten semantik H).
# (3) "DEV TO BOM" kini ADA di app: BOM·App = Σ penjualan 22.05 (JENIS
#     9.ACR, tgl 1..H — "2205 itu bom"), COM·App = Σ pemakaian com(t)
#     tgl 1..H (com(t) = SO(t-1)+IN(t)−BK(t)−SO(t), formula identik
#     pivot 6.PEMAKAIAN & tab Anomali COM), DEV·App = COM−BOM (formula
#     identik file), GR·App = SO_H − Sistem_H (PERSIS kolom Deviasi di
#     tab 📦 Deviasi GR pada H minggu tsb — aljabar: GR·App = ΣOUT−SA−
#     ΣIN+ΣBK+SO_H = out_cum − com_cum = DEV·App, dua jalur hitung).
# (4) KOLOM: ✓ · Resto · Nama Barang · Satuan · Minggu · H · BOM/COM/DEV/
#     %TO BOM File · BOM/COM/DEV App · GR App · Selisih (GR App − DEV
#     File) · Status (MATCH / SELISIH / TIDAK ADA DI DATA APP / H TIDAK
#     ADA DI DATA). Resto file "1041.BDGUKU"/"B.1001.MLGPAR" dinormalkan
#     ke kode app (BDGUKU/MLGPAR). Default hanya resto yang ada di data
#     app (20 resto cek stock) — centang utk semua 340 cabang.
# (5) Infrastruktur utuh: ✓ follow-up (asal KOMPARASI), filter header ⧩,
#     sort parser Indonesia, ⛶ Layar Penuh, ⤢ Perbesar, ◱ Kolom, ↔
#     Auto-Fit, minus merah per-cell, sel Status hijau/amber/merah,
#     compute async + FIX B-01, path file terakhir diingat
#     (komparasi_last.json) → initialdir dialog.
# v3.9.3 — TAB LAPORAN DEVIASI → DAFTAR ANOMALI PEMAKAIAN (COM)
# v3.9.3 (permintaan user: "hapus isi data pada tab laporan deviasi dan
# sementara ganti dengan list nama barang dan resto yang pemakaian (com)
# nya minus atau lebih tinggi dari median pada pada kolom H"):
# (1) Isi tab 📋 LAPORAN DEVIASI DIGANTI (sementara; tabel Audit Harian
#     lama tersimpan di git history — commit e20141a): kini berisi DAFTAR
#     (Nama Barang × Resto) dengan nilai PEMAKAIAN (COM) pada kolom H yang
#     MINUS (< 0) atau LEBIH TINGGI dari MEDIAN pasangan tsb — v3.9.7
#     (koreksi user): median dihitung ANTAR TANGGAL (com(t) tgl 1..H
#     milik pasangan barang×resto; COM = pemakaian aktual harian di
#     resto, BOM = pemakaian harian versi sistem), BUKAN antar resto.
# (2) COM dihitung dgn formula identik baris 6.PEMAKAIAN (COM) di pivot
#     mode Tanggal: com(t) = SO(t-1) + IN(t) - BK(t) - SO(t), tanggal
#     pertama memakai SALDO AWAL. Matriks COM di-cache per data
#     (H-independen) — ganti H cukup pilih kolom, tanpa recompute pivot.
# (3) TANGGAL H = state bersama (SharedTanggalH v3.9): tab ini menampilkan
#     chip read-only + auto-refresh saat H di-apply di tab 📦 Deviasi GR.
# (4) Kolom: ✓ · Nama Barang · Resto · Satuan · COM (heading dinamis
#     "COM (H=25)") · Median · Selisih vs Median · Status (MINUS /
#     > MEDIAN / MINUS + > MEDIAN). Minus merah PER CELL (v3.9.2) + sel
#     Status merah/amber per-cell; parser sort numerik format Indonesia.
# (5) Follow-up ✓ tetap jalan (asal snapshot = LAPORAN-COM: SO=nilai COM,
#     Sistem=median, Deviasi=selisih, CEK=status).
# v3.9.2 — MINUS MERAH PER CELL + EXPORT PIVOT SESUAI TAMPILAN
# v3.9.2 (permintaan user: "minus harusnya cuman merah per cell bukan per
# baris dan pivot tabel nya bisa export excel"):
# (1) MINUS MERAH PER CELL (bukan per baris) di SEMUA tabel: Pivot matrix,
#     Deviasi GR/PCS, Laporan Deviasi, popup Rincian IN & popup Detail —
#     Tk 9 API `treeview tag cell add` (helper apply_cell_tag); hanya cell
#     bernilai negatif yang merah — label baris & cell lain tetap normal.
#     Baris 3.DEVIASI pivot tidak lagi selalu merah; 7.Selisih ≠ 0 tetap
#     fill merah muda per baris, font merah per-cell pada nilai ≠ 0.
#     Tag cell dipasang ulang otomatis setelah sort (delete+reinsert) &
#     clone ⛶ (hook on_render_done). Fallback Tk 8.6: perilaku lama.
# (2) Tombol 💾 Export Excel di tab 📊 PIVOT: matrix pivot SESUAI
#     TAMPILAN (filter RESTO/SOURCE/KATEGORI + rentang Tanggal + mode
#     🏪/📅 + sembunyikan-baris-kosong + kolom tampil ◱) → .xlsx:
#     minus = font merah PER CELL (mirror UI), 0 = font putih, metric bg,
#     header 25• bulan lalu biru, freeze B8 (write_pivot_display_sheet).
# v3.9.1 — DEEP AUDIT UI/UX → 15 FIX PORT KE v3.9
# v3.9.1 (hasil audit 39 temuan, 3 high — semua fix ditandai "# FIX <ID>"
# di kode, bisa di-grep):
# (1) B-01 (HIGH): _busy di-reset saat compute GAGAL — sebelumnya 1x error
#     membuat view mati permanen (Apply H/filter/reset berikutnya ditelan
#     guard `if self._busy`). on_error dipasang di 3 view (Deviasi/Pivot/
#     Rekap Selisih IN).
# (2) B-02 (HIGH): validasi input TANGGAL konsisten di semua view lewat
#     helper validated_tgl_entry (warning + revert, pola tab Deviasi) —
#     sebelumnya 3 perilaku beda: pivot fallback senyap, selisih int(float)
#     senyap, deviasi modal+revert. Jalur export selisih ikut tervalidasi.
# (3) B-03: popup funnel 600→3000 nilai + label jujur "menampilkan X dari Y".
# (4) B-07: ✕ Reset Filter kini juga reset TANGGAL H ke 25 (v3.9: lewat
#     SharedTanggalH — GR & PCS sync; tab GR ikut berlangganan listener).
# (5) C-03: format angka gaya INDONESIA konsisten (1.234.567 / 1.234,5 /
#     negatif kurung) di 3 view + KPI chips + log audit + popup TOTAL IN.
# (6) C-05: menu ⧩ Filter kolom non-#0 di Pivot tidak mati senyap — kini
#     diarahkan ke filter Nama + status bar menjelaskan.
# (7) A-01/A-02: tombol toolbar disabled kini terlihat DIM (teal→abu)
#     lewat Toolbar.add_action.set_enabled; konvensi konsisten.
# (8) A-04: (dihapus v3.9.8 — window Bantuan dihapus, UI clean).
# (9) A-08: teks fungsional font(8)→font(9): label KPI, legend, counter
#     filter, counter panel kolom, hint window clone (metadata tetap 8).
# Riwayat v3.9.0 — SHARED H + EXPORT AUDIT + RINCIAN PO RINGKAS + STYLE WASTE:
# (1) TANGGAL H dibagi 2 tab: input + "Apply H" hanya di tab 📦 Deviasi
#     GR, otomatis berlaku juga di tab 🧩 Deviasi PCS (chip read-only +
#     refresh otomatis — tidak ada double input; permintaan user);
#     SharedPivotCache thread-safe dgn lock (GR+PCS refresh bersamaan).
# (2) Export Rekap Selisih IN: dialog opsi kolom hasil audit (Hasil Audit /
#     Saldo / Catatan Audit — bisa ditambahkan atau tidak, permintaan user).
# (3) Rincian PO disederhanakan: baris TEAL = info PO lengkap sekali, baris
#     putih = item saja; kolom Tgl/Jam Pembuatan tersembunyi default.
# (4) STYLE WASTE: funnel header MERAH saat terfilter; tabel diperbesar
#     (font 10, rowheight 30); ⤢ Perbesar Tabel + ⛶ Layar Penuh semua tab.
# (5) CRASH FIX laten CPython 3.12 + Tk: GC shield saat thread worker hidup.
# Riwayat: v3.8.0 — selisih IN 1-31; pivot -31..31 (kolom 25•-31• lengkap);
# sheet PIVOT + CF; export selisih per resto; impor TL dihapus. v3.7.0 —
# ENGINE TURBO (output identik, 4× lebih cepat) + fix 9 bug index display.
# v3.6.0 — fix tombol filter; hide/unhide kolom; audit dari data app.
# v3.5.0 — LightMode dihapus; header filter semua kolom; KATEGORI.
# v3.4.0 — lebar kolom adjustable; SO bulan lalu; tab Rekap Selisih IN.
WINDOW_SIZE = "1280x760"
# FIX (audit 2-a QA visual): tinggi minimum 640 → 700 — di bawah ~695
# h-scrollbar tabel tertabrak tepi bawah (tidak bisa scroll horizontal).
WINDOW_MIN = (1020, 700)

# Path config.json di root project
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"

# --- Freeze-fix konstanta (dipertahankan dari v2.1.1) -----------------------
MAX_CHUNKS_PER_POLL = 200       # max chunks diproses per poll cycle
MAX_CHARS_PER_POLL = 50000      # max karakter di-append per poll (cap buffer)
MAX_LOG_LINES = 3000            # max baris di Text widget (truncate ke 2000)
LOG_POLL_INTERVAL_MS = 100      # interval poll

# Warna status pipeline
_ST_SIAP = ("SIAP — menunggu perintah", C_GREEN)
_ST_RUN = ("Pipeline berjalan…", C_ORANGE)
_ST_DONE = ("SELESAI", C_GREEN)
_ST_STOP = ("DIHENTIKAN oleh user", C_AMBER)
_ST_ERR = ("ERROR — lihat log", C_RED)


# --- Helper: redirect stdout ke Text widget via queue -----------------------
class StreamToQueue:
    """Object file-like yang menulis ke queue (thread-safe)."""

    def __init__(self, q: queue.Queue):
        self.q = q

    def write(self, s: str):
        if s:
            self.q.put(s)

    def flush(self):
        pass


# --- Aplikasi utama ---------------------------------------------------------
class StockMonitorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_TITLE} — Python Edition")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*WINDOW_MIN)
        self.root.configure(bg=C_BG)

        # State
        self.log_queue: queue.Queue = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.is_running = False
        # stop_event benar-benar memotong pipeline di checkpoint (dipertahankan)
        self.stop_event = threading.Event()
        self.append1_df = None
        self.rincian_po_df = None
        self.in_detail_df = None
        self.audit_result = None      # v3.5: {"df", "kpi", "desc"} audit rekonsiliasi
        self._log_line_count = 0
        self._run_start_time: float | None = None
        self._elapsed_after_id = None
        # FIX D-04: penghitung file Excel yang di-skip reader (terkunci/
        # hilang/rusak) — dihitung dari log pipeline, ditampilkan saat
        # pipeline selesai supaya data parsial tidak disembunyikan.
        self._skipped_files = 0

        # v3.2: store follow-up bersama (persist followup.json)
        self.followup_store = FollowUpStore()
        # v3.3: cache pivot Deviasi dibagi GR & PCS (compute 1×, bukan 2×)
        self._deviasi_pivot_cache = SharedPivotCache()
        # v3.9: TANGGAL H dibagi GR & PCS — input 1× (di tab GR), berlaku
        # di kedua tab (permintaan user: tidak double input)
        # v3.9.22: fallback awal 26 (user: "Tanggal harusnya tanggal 26
        # bukan dari tanggal 25"); setelah data dimuat DeviasiView mengatur
        # H DINAMIS ke tanggal SO nonzero terakhir (data user sampai 26).
        self._shared_h = SharedTanggalH(26)
        # v3.9.21: AMBANG ACR to BOM dibagi GR & PCS (user: "threshold
        # > 80% absolute dan aku bisa atur") — spinbox kedua tab sinkron;
        # nilai bertahan lintas sesi (settings.json), default 80.
        self._shared_acr = SharedACRThreshold(load_acr_threshold())

        # Style ttk (design system global)
        apply_theme(self.root)

        # Build UI
        self._build_toolbar()
        self._build_statusbar()
        self._build_notebook()

        # Redirect stdout/stderr ke queue
        sys.stdout = StreamToQueue(self.log_queue)
        sys.stderr = StreamToQueue(self.log_queue)

        # Poll queue untuk update log (batched + throttled — freeze fix)
        self._poll_log_queue()

        # Load config awal ke tab Config
        self._load_config_to_form()

        # v3.9.33 — AUDIT FIX (48-c LOW): tombol X / WM_DELETE_WINDOW — dulu
        # TANPA handler (48-f: tidak ada WM_DELETE_WINDOW) → pipeline hidup
        # saat window ditutup → after() TclError ganda di thread daemon.
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)

    # =====================================================================
    # SHELL: TOOLBAR + STATUSBAR + NOTEBOOK
    # =====================================================================
    def _build_toolbar(self):
        self.toolbar = Toolbar(self.root, f"📊 {APP_TITLE}", APP_VERSION)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_export_tb = self.toolbar.add_action(
            "💾 Export Excel", command=self._export_excel, accent=True)
        # FIX A-02 (audit 2-a): set_enabled → tombol disabled TAMPAK dim
        # (abu) — bukan configure(state) yang meninggalkan warna teal.
        self.btn_export_tb.set_enabled(False)

    def _build_statusbar(self):
        self.statusbar = StatusBar(self.root)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbar.set_right(f"v{APP_VERSION} · Python Edition")

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=(2, 6))

        self.tab_config = tk.Frame(self.notebook, bg=C_BG)
        self.tab_proses = tk.Frame(self.notebook, bg=C_BG)
        self.tab_pivot = tk.Frame(self.notebook, bg=C_BG)
        self.tab_deviasi_gr = tk.Frame(self.notebook, bg=C_BG)
        self.tab_deviasi_pcs = tk.Frame(self.notebook, bg=C_BG)
        self.tab_in_selisih = tk.Frame(self.notebook, bg=C_BG)
        self.tab_laporan = tk.Frame(self.notebook, bg=C_BG)
        # v3.9.34 — tab 🧮 Nominal Deviasi (Σ nominal per resto)
        self.tab_nominal_resto = tk.Frame(self.notebook, bg=C_BG)
        self.tab_followup = tk.Frame(self.notebook, bg=C_BG)
        self.tab_rincian = tk.Frame(self.notebook, bg=C_BG)

        self.notebook.add(self.tab_config, text="⚙️ Config")
        self.notebook.add(self.tab_proses, text="🚀 Proses")
        self.notebook.add(self.tab_pivot, text="📊 Pivot Table")
        self.notebook.add(self.tab_deviasi_gr, text="📦 Deviasi GR")
        self.notebook.add(self.tab_deviasi_pcs, text="🧩 Deviasi PCS")
        self.notebook.add(self.tab_in_selisih, text="📤 Rekap Selisih IN")
        self.notebook.add(self.tab_laporan, text="📋 Laporan Deviasi")
        # v3.9.34 — tab 🧮 Nominal Deviasi: Σ harga×qty deviasi per resto
        self.notebook.add(self.tab_nominal_resto,
                          text="🧮 Nominal Deviasi")
        self.notebook.add(self.tab_followup, text="☑ Follow Up")
        self.notebook.add(self.tab_rincian, text="🛒 Rincian PO")
        # v3.2: lazy refresh — tab data hanya compute saat TERLIHAT
        # (setelah pipeline selesai hanya tab aktif yang refresh; tab lain
        # menunggu dipilih → app terasa jauh lebih ringan)
        self.notebook.bind("<<NotebookTabChanged>>",
                           self._on_tab_changed)
        # FIX A-04 (audit 2-a): aktifkan navigasi keyboard antar-tab
        # (Ctrl+Tab / Ctrl+Shift+Tab) — ttk notebook punya mekanisme ini
        # tapi harus di-enable eksplisit dari aplikasi.
        self.notebook.enable_traversal()
        self._update_followup_badge()

        self._build_config_tab()
        self._build_proses_tab()
        self._build_pivot_tab()
        self._build_deviasi_gr_tab()
        self._build_deviasi_pcs_tab()
        self._build_in_selisih_tab()
        self._build_laporan_tab()
        self._build_nominal_resto_tab()   # v3.9.34 — tab 🧮
        self._build_followup_tab()
        self._build_rincian_tab()
        self._build_tab_views()  # FIX A-11: routing tab berbasis widget

    def _on_tab_changed(self, _event=None):
        """Tab baru dipilih → pastikan view-nya sudah di-refresh.

        FIX A-11 (audit 2-a): routing berbasis WIDGET FRAME (bukan index
        angka) — v3.9.9 terpaksa reindex manual saat Pareto disisipkan;
        mapping kini dibangun sekali di _build_tab_views() sehingga tab
        baru cukup menambah satu entry, tidak menggeser angka ajaib.
        """
        try:
            sel = self.notebook.select()  # string nama widget Tk
        except Exception:
            return
        views = getattr(self, "_tab_views", None)
        if not views:
            return
        view = views.get(sel)
        if view is self._laporan_tab_entry:
            # v3.9.4: refresh pane SESUAI MODE aktif di tab Laporan
            # v3.9.32: mode 2 = 💰 Nominal (H)
            _active = (getattr(self, "laporan_segment", None).active
                       if getattr(self, "laporan_segment", None) is not None
                       else 0)
            view = (self.komparasi_view if _active == 0
                    else (self.nominal_view if _active == 2
                          else self.laporan_view))
        if view is not None and hasattr(view, "ensure_refreshed"):
            view.ensure_refreshed()

    def _build_tab_views(self):
        """FIX A-11: peta nama-widget tab → view yang di-lazy-refresh.
        Follow Up sengaja tanpa entry (reaktif via store listener).
        """
        self._laporan_tab_entry = object()  # marker dispatch khusus
        self._tab_views = {
            str(self.tab_pivot): self.pivot_view,
            str(self.tab_deviasi_gr): self.deviasi_gr_view,
            str(self.tab_deviasi_pcs): self.deviasi_pcs_view,
            str(self.tab_in_selisih): self.in_selisih_view,
            str(self.tab_laporan): self._laporan_tab_entry,
            # v3.9.34 — dispatch _on_tab_changed → ensure_refreshed
            str(self.tab_nominal_resto): self.nominal_resto_view,
            str(self.tab_rincian): self.rincian_view,
        }

    def _update_followup_badge(self):
        """Badge jumlah baris di judul tab Follow Up."""
        try:
            n = len(self.followup_store)
            # FIX H-1 (audit 2-a hipotesis — TERKONFIRMASI): label tab
            # TANPA spasi ganda + padding ramping → semua tab muat di lebar
            # minimum 1020px (dulu ±1280px — tab paling kanan terpotong /
            # tak terjangkau; kritis juga di Windows 125% scaling).
            self.notebook.tab(
                self.tab_followup,
                text=f"☑ Follow Up{' (' + str(n) + ')' if n else ''}")
        except Exception:
            pass

    # =====================================================================
    # TAB: CONFIG
    # =====================================================================
    def _build_config_tab(self):
        tab = self.tab_config
        wrap = tk.Frame(tab, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Card: Lokasi Data ---
        card = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                        highlightthickness=1)
        card.pack(fill="x")
        inner = tk.Frame(card, bg=C_CARD)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(inner, text="Lokasi Data (RootPath)", bg=C_CARD,
                 fg=C_HEADER, font=font(12, "bold")).pack(anchor="w")

        form = tk.Frame(inner, bg=C_CARD)
        form.pack(fill="x")
        tk.Label(form, text="RootPath", bg=C_CARD, fg=C_HEADER,
                 font=font(9, "bold")).grid(row=0, column=0, sticky="nw", pady=6)
        self.rootpath_var = tk.StringVar()
        self.entry_rootpath = ttk.Entry(form, textvariable=self.rootpath_var)
        self.entry_rootpath.grid(row=0, column=1, sticky="ew", padx=(10, 8), pady=6)
        btn_browse = GhostButton(form, text="📂 Browse…", command=self._browse_folder)
        btn_browse.grid(row=0, column=2, pady=6)
        form.columnconfigure(1, weight=1)

        btn_row = tk.Frame(inner, bg=C_CARD)
        btn_row.pack(fill="x")
        AccentButton(btn_row, text="💾 Simpan Config",
                     command=self._save_config).pack(side="left")
        GhostButton(btn_row, text="↻ Reload Config",
                    command=self._load_config_to_form).pack(
            side="left", padx=(8, 0))

        # --- Card: Info Config (read-only) ---
        info_card = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                             highlightthickness=1)
        info_card.pack(fill="both", expand=True, pady=(12, 0))
        info_inner = tk.Frame(info_card, bg=C_CARD)
        info_inner.pack(fill="both", expand=True, padx=16, pady=(14, 16))

        tk.Label(info_inner, text="Info Config (read-only)", bg=C_CARD,
                 fg=C_HEADER, font=font(12, "bold")).pack(anchor="w")

        self.info_tree = make_tree(info_inner, ["item", "value"], show="headings")
        self.info_tree.column("item", width=260, minwidth=160, anchor="w")
        self.info_tree.heading("item", text="Item")
        self.info_tree.column("value", width=420, minwidth=200, anchor="w")
        self.info_tree.heading("value", text="Nilai")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Pilih RootPath")
        if folder:
            if not folder.endswith(os.sep):
                folder += os.sep
            self.rootpath_var.set(folder)

    def _load_config_to_form(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self._set_info_error(
                f"config.json tidak ditemukan di:\n{CONFIG_PATH}")
            self.rootpath_var.set("")
            return
        except json.JSONDecodeError as e:
            self._set_info_error(f"config.json rusak (JSON invalid):\n{e}")
            self.rootpath_var.set("")
            return

        self.rootpath_var.set(data.get("RootPath", ""))
        self._render_info_tree(data)
        # v3.9.5 FIX (audit 19-c #6): RootPath dibaca SAAT notebook dibangun
        # (SEBELUM config dimuat) → initialdir dialog 📂 Pilih File Deviasi
        # selalu "" saat app baru dibuka. Sinkronkan setiap RootPath berubah.
        self._sync_komparasi_initial_dir()

    def _sync_komparasi_initial_dir(self):
        """v3.9.5 (audit 19-c #6): initial dialog komparasi mengikuti
        RootPath terkini (config dimuat SETELAH notebook dibangun)."""
        rp = (self.rootpath_var.get().strip()
              if getattr(self, "rootpath_var", None) is not None else "")
        if rp and getattr(self, "komparasi_view", None) is not None:
            self.komparasi_view._initial_dir = rp

    def _render_info_tree(self, data: dict):
        self.info_tree.delete(*self.info_tree.get_children())
        for section, key in [("FOLDERS", "Folders"), ("SHEETS", "Sheets")]:
            sec_id = self.info_tree.insert(
                "", "end", values=(f"== {section} ==", ""))
            self.info_tree.item(sec_id, open=True)
            for k, v in (data.get(key, {}) or {}).items():
                self.info_tree.insert(sec_id, "end", values=(k, v))
        self.info_tree.tag_configure("bold", font=font(9, "bold"))

    def _set_info_error(self, msg: str):
        self.info_tree.delete(*self.info_tree.get_children())
        self.info_tree.insert("", "end", values=("ERROR", msg), tags=("err",))
        self.info_tree.tag_configure("err", foreground=C_RED)

    def _save_config(self):
        new_root = self.rootpath_var.get().strip()
        if not new_root:
            messagebox.showwarning("Validasi", "RootPath tidak boleh kosong.",
                                   parent=self.root)
            return

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError as e:
            messagebox.showerror(
                "Config Rusak",
                f"config.json tidak bisa dibaca (JSON invalid):\n{e}",
                parent=self.root)
            return

        data["RootPath"] = new_root
        # v3.5: LightMode dihapus — key lama (bila ada) dibuang saat save
        data.pop("LightMode", None)

        # FIX D-05 (audit 2-d): tulis ATOMIK (tmp + os.replace) — crash
        # di tengah write tidak lagi meninggalkan config.json korup
        # (pola sama followup.py; .bak tetap dibuat sebagai cadangan).
        backup_path = CONFIG_PATH.with_suffix(".json.bak")
        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, CONFIG_PATH)
        except Exception as e:
            with contextlib.suppress(Exception):
                tmp_path.unlink(missing_ok=True)
            messagebox.showerror(
                "Gagal Simpan", f"Tidak bisa menulis config.json:\n{e}",
                parent=self.root)
            return

        messagebox.showinfo(
            "Berhasil",
            f"Config disimpan.\n\nRootPath: {new_root}",
            parent=self.root)
        self._load_config_to_form()

    # =====================================================================
    # TAB: PROSES
    # =====================================================================
    def _build_proses_tab(self):
        tab = self.tab_proses
        wrap = tk.Frame(tab, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Card: Kontrol Pipeline ---
        ctrl = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                        highlightthickness=1)
        ctrl.pack(fill="x")
        ctrl_inner = tk.Frame(ctrl, bg=C_CARD)
        ctrl_inner.pack(fill="x", padx=16, pady=14)

        tk.Label(ctrl_inner, text="Kontrol Pipeline", bg=C_CARD, fg=C_HEADER,
                 font=font(12, "bold")).pack(anchor="w")

        btns = tk.Frame(ctrl_inner, bg=C_CARD)
        btns.pack(fill="x", pady=(0, 10))
        self.btn_mulai = AccentButton(btns, text="🚀 MULAI PROSES",
                                      command=self._start_pipeline)
        self.btn_mulai.pack(side="left")

        self.btn_stop = DangerButton(btns, text="⏹ Stop", state="disabled",
                                     command=self._stop_pipeline)
        self.btn_stop.pack(side="left", padx=(8, 0))
        # FIX A-02: state disabled dari constructor tidak memakai styling
        # dim → panggil set_enabled sekali supaya konsisten visual.
        self.btn_stop.set_enabled(False)

        self.btn_bersih = GhostButton(btns, text="🧹 Bersihkan Log",
                                      command=self._clear_log)
        self.btn_bersih.pack(side="left", padx=(8, 0))

        # v3.9.33 — AUDIT FIX (48-f MEDIUM): log konsol (state disabled) tidak
        # bisa di-copy — tombol salin SELURUH isi log ke clipboard.
        self.btn_salin_log = GhostButton(btns, text="📋 Salin Log",
                                         command=self._copy_log)
        self.btn_salin_log.pack(side="left", padx=(8, 0))

        self.btn_export = GhostButton(btns, text="💾 Export ke Excel",
                                      state="disabled",
                                      command=self._export_excel)
        self.btn_export.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Status: siap.")
        status_row = tk.Frame(ctrl_inner, bg=C_CARD)
        status_row.pack(fill="x")
        self.status_spinner = Spinner(status_row, size=18, bg=C_CARD)
        self.status_spinner.pack(side="left", padx=(0, 8))
        self.status_spinner.stop()
        tk.Label(status_row, textvariable=self.status_var, bg=C_CARD,
                 fg=C_HEADER, font=font(10, "bold")).pack(anchor="w")
        self.progress = ttk.Progressbar(ctrl_inner, mode="indeterminate",
                                        orient="horizontal")
        self.progress.pack(fill="x", pady=(6, 2))

        # --- KPI row ---
        kpi_row = KpiRow(wrap)
        self.kpi_status = KpiCard(kpi_row, "Status Pipeline", "SIAP",
                                  "menunggu perintah", C_GREEN)
        self.kpi_elapsed = KpiCard(kpi_row, "Waktu Berjalan", "0.0 dtk",
                                   "sejak MULAI PROSES", C_HEADER)
        self.kpi_append = KpiCard(kpi_row, "Rows Append1", "—",
                                  "pipeline belum jalan")
        self.kpi_rincian = KpiCard(kpi_row, "Rows Rincian PO", "—",
                                   "pipeline belum jalan")
        for c in (self.kpi_status, self.kpi_elapsed, self.kpi_append,
                  self.kpi_rincian):
            kpi_row.add(c)
        kpi_row.pack(fill="x", pady=12)

        # --- Konsol log gelap ---
        log_card = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                            highlightthickness=1)
        log_card.pack(fill="both", expand=True)
        log_head = tk.Frame(log_card, bg=C_CARD)
        log_head.pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(log_head, text="Log Proses", bg=C_CARD, fg=C_HEADER,
                 font=font(12, "bold")).pack(anchor="w")

        log_wrap = tk.Frame(log_card, bg=C_CARD)
        log_wrap.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        self.log_text, _ = make_log_console(log_wrap)

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._log_line_count = 0

    def _copy_log(self):
        """v3.9.33 — AUDIT FIX (48-f MEDIUM): salin SELURUH isi konsol log ke
        clipboard (traceback pipeline jadi bisa dibagikan) + feedback singkat
        di baris status kartu Kontrol Pipeline."""
        try:
            content = self.log_text.get("1.0", "end-1c")
        except tk.TclError:
            return
        if not content.strip():
            messagebox.showinfo("Salin Log", "Log masih kosong.",
                                parent=self.root)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        n_baris = len(content.splitlines())
        prev = self.status_var.get()
        self.status_var.set(
            f"📋 Log TERSALIN ke clipboard ({fmt_int_id(n_baris)} baris).")
        if getattr(self, "_log_flash_after", None):
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._log_flash_after)

        def _restore():
            if self.root.winfo_exists():
                self.status_var.set(prev)

        self._log_flash_after = self.root.after(2500, _restore)

    # =====================================================================
    # LOG QUEUE (freeze fix dipertahankan)
    # =====================================================================
    def _append_log_batched(self, text: str):
        """Append batch text ke konsol log dengan truncation otomatis."""
        if not text:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text)

        new_lines = text.count("\n")
        self._log_line_count += new_lines

        if self._log_line_count > MAX_LOG_LINES:
            # v3.9.33 — AUDIT FIX (48-f LOW): baris awal dibuang TANPA jejak —
            # user tidak tahu lognya terpangkas. Sisipkan SATU baris marker
            # di puncak supaya jelas (+1 ke hitungan baris).
            self.log_text.delete("1.0", "1001.0")
            self._log_line_count -= 1000
            self.log_text.insert("1.0",
                                 f"(log dipangkas — {fmt_int_id(1000)} "
                                 "baris awal dibuang)\n")
            self._log_line_count += 1

        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _poll_log_queue(self):
        """Batch log writes — ambil semua chunks dari queue (dengan cap)."""
        chunks = []
        total_chars = 0
        chunk_count = 0
        try:
            while chunk_count < MAX_CHUNKS_PER_POLL and total_chars < MAX_CHARS_PER_POLL:
                chunk = self.log_queue.get_nowait()
                chunks.append(chunk)
                total_chars += len(chunk)
                chunk_count += 1
        except queue.Empty:
            pass

        if chunks:
            text = "".join(chunks)
            # FIX D-04: reader me-log "[WARNING] Skip file ..." ke stdout
            # (helpers.py) — dihitung di sini (jalur log = satu-satunya
            # tempat lewat) TANPA mengubah kontrak pipeline.
            n = text.count("[WARNING] Skip file")
            if n:
                self._skipped_files += n
            self._append_log_batched(text)

        self.root.after(LOG_POLL_INTERVAL_MS, self._poll_log_queue)

    # =====================================================================
    # PIPELINE CONTROL
    # =====================================================================
    def _start_pipeline(self):
        if self.is_running:
            messagebox.showinfo(
                "Sedang Berjalan",
                "Pipeline sedang berjalan. Tunggu hingga selesai atau klik Stop.",
                parent=self.root)
            return

        if not CONFIG_PATH.exists():
            messagebox.showerror(
                "Config Tidak Ada",
                f"config.json tidak ditemukan:\n{CONFIG_PATH}", parent=self.root)
            return

        # FIX A-01 (audit 2-a): guard kedua — bila worker LAMA masih hidup
        # (baru di-Stop, belum sampai checkpoint), JANGAN jalankan thread
        # kedua: stop_event.clear() akan membatalkan Stop-nya & dua
        # pipeline berjalan paralel (log tercampur, data last-writer-wins).
        worker = getattr(self, "worker_thread", None)
        if worker is not None and worker.is_alive():
            messagebox.showinfo(
                "Masih Menghentikan",
                "Pipeline sebelumnya masih berhenti di checkpoint.\n"
                "Tunggu sampai status berubah, lalu Mulai lagi.",
                parent=self.root)
            return

        # FIX D-04: reset penghitung file yang di-skip reader
        self._skipped_files = 0

        # v3.9.33 — AUDIT FIX (48-f HIGH-#6): PRE-FLIGHT folder data SEBELUM
        # pipeline — dulu folder hilang / RootPath salah → pipeline berjalan
        # dan berakhir "SELESAI" HIJAU + tabel kosong SENYAP tanpa pesan aksi.
        # Kini kegagalan di-surface AWAL (log + dialog + status amber) lalu
        # run tetap lanjut (perilaku degrade yang sama, kini terlihat).
        # Kontrak: src/pipeline/helpers.preflight_folders(cfg) —
        # missing [(key, full_path)] folder Folders yang tidak ada;
        # counts [(key, n_file_excel)] per folder (folder hilang → 0).
        pre_missing: list = []
        try:
            from src.config import Config
            from src.pipeline.helpers import preflight_folders
            pre_missing, pre_counts = preflight_folders(Config(str(CONFIG_PATH)))
            for key, n in pre_counts:
                self._append_log_batched(f"  Pre-flight {key}: "
                                         f"{fmt_int_id(n)} file excel\n")
        except ImportError:
            # helper belum tersedia saat runtime → skip pre-flight graceful
            pre_missing = []
        except Exception as exc:  # defensive: config rusak dll — jangan blokir run
            pre_missing = []
            self._append_log_batched(
                f"\n[PERINGATAN] Pre-flight folder dilewati: {exc}\n")

        if pre_missing:
            daftar = "\n".join(f"  • {key} → {path}"
                               for key, path in pre_missing)
            self._append_log_batched(
                "\n[PERINGATAN] Folder data TIDAK DITEMUKAN —\n"
                + daftar +
                "\n  Pipeline tetap dijalankan (data jadi parsial/kosong).\n")
            messagebox.showwarning(
                "Folder data tidak ditemukan",
                "Folder data berikut TIDAK DITEMUKAN:\n\n" + daftar +
                "\n\nPipeline tetap dijalankan (data bisa parsial/kosong).\n"
                "Perbaiki RootPath / Folders di tab ⚙ Pengaturan.",
                parent=self.root)

        self.notebook.select(self.tab_proses)
        self.is_running = True
        self.stop_event.clear()
        self.btn_mulai.set_enabled(False)
        self.btn_stop.set_enabled(True)
        # FIX A-02: set_enabled (visual dim) — bukan configure(state) polos
        self.btn_export.set_enabled(False)
        self.btn_export_tb.set_enabled(False)
        self.status_var.set("Status: menjalankan pipeline…")
        self.status_spinner.start()
        self.statusbar.set_status(*_ST_RUN)
        if pre_missing:
            # v3.9.33 — status AMBER sebelum run: folder data bermasalah jangan
            # tertutup status "berjalan" polos (48-f: kegagalan senyap).
            self.statusbar.set_status(
                "Pipeline berjalan… ⚠ folder data tidak ditemukan — lihat log",
                C_AMBER)
        self.kpi_status.set_value("MENJALANKAN", "pipeline sedang diproses…",
                                  C_ORANGE)
        self.progress.start(12)
        self._run_start_time = time.time()
        self._tick_elapsed()

        self._append_log_batched("\n" + "=" * 60 + "\n  Memulai pipeline…\n")

        self.worker_thread = threading.Thread(
            target=self._run_pipeline_worker, daemon=True)
        self.worker_thread.start()

    def _tick_elapsed(self):
        """Update KPI waktu berjalan tiap detik selama pipeline aktif."""
        if self._run_start_time is None:
            return
        elapsed = time.time() - self._run_start_time
        if elapsed < 60:
            txt = f"{elapsed:.0f} dtk"
        else:
            txt = f"{int(elapsed // 60)} mnt {elapsed % 60:.0f} dtk"
        self.kpi_elapsed.set_value(txt)
        self._elapsed_after_id = self.root.after(1000, self._tick_elapsed)

    def _stop_elapsed(self):
        if self._elapsed_after_id:
            try:
                self.root.after_cancel(self._elapsed_after_id)
            except Exception:
                pass
            self._elapsed_after_id = None

    def _schedule_to_main(self, fn):
        """v3.9.33 — AUDIT FIX (48-c LOW): root.after() dari thread worker
        saat window sudah DITUTUP melempar TclError; jalur except lama
        memanggil after() LAGI → TclError tak tertangkap di thread daemon.
        Kini: root sudah mati → menyerah senyap (proses ikut mati bersama
        main thread — worker memang daemon)."""
        try:
            self.root.after(0, fn)
        except tk.TclError:
            pass

    def _run_pipeline_worker(self):
        """Worker thread: jalankan run_pipeline, tangkap error.

        v3.3 BUG FIX: dulu `except X as e:` + lambda tertunda → Python
        menghapus binding `e` di akhir blok except → NameError saat
        callback berjalan (error pipeline tidak pernah sampai ke UI).
        Kini error ditangkap ke tuple lokal dulu, lambda bebas closure.

        v3.9 CRASH FIX: GC dimatikan selama thread pipeline hidup — GC di
        thread worker bisa mem-finalisasi tk.Variable sisa popup yang
        sudah ditutup (destructor memanggil Tcl dari thread bukan-main →
        segfault CPython 3.12+Tk). Dilepas di _on_pipeline_done (main
        thread) setelah thread dipastikan mati.
        """
        gc_shield_acquire()
        try:
            append1_df, rincian_po_df, in_detail_df, audit_result = run_pipeline(
                verbose=True, stop_event=self.stop_event)
            self._schedule_to_main(lambda: self._on_pipeline_done(
                append1_df, rincian_po_df, in_detail_df, audit_result, None))
        except PipelineStopped as exc:
            err = (exc, None)
            self._schedule_to_main(lambda: self._on_pipeline_done(
                None, None, None, None, err))
        except Exception as exc:
            import traceback
            err = (exc, traceback.format_exc())
            self._schedule_to_main(lambda: self._on_pipeline_done(
                None, None, None, None, err))

    def _on_pipeline_done(self, append1_df, rincian_po_df, in_detail_df,
                          audit_result, error):
        """Dijadwalkan ke main thread via after()."""
        # v3.9: lepas GC shield SEBELUM UI work berat — bila thread pipeline
        # belum benar-benar mati, retry 15ms sampai mati (lihat widgets.py)
        gc_shield_release(self.worker_thread, retry_widget=self.root)
        self.progress.stop()
        self.status_spinner.stop()
        self._stop_elapsed()
        self.is_running = False
        self.btn_mulai.set_enabled(True)
        self.btn_stop.set_enabled(False)

        # Final elapsed
        if self._run_start_time is not None:
            elapsed = time.time() - self._run_start_time
            self.kpi_elapsed.set_value(f"{elapsed:.1f} dtk", "total waktu proses")
            self._run_start_time = None

        if error is not None:
            exc, tb = error
            if isinstance(exc, PipelineStopped):
                self.status_var.set("Status: DIHENTIKAN oleh user.")
                self.statusbar.set_status(*_ST_STOP)
                self.kpi_status.set_value("DIHENTIKAN", "oleh user", C_AMBER)
                self._append_log_batched(f"\n[STOP] {exc}\n")
                return
            self.status_var.set("Status: ERROR.")
            self.statusbar.set_status(*_ST_ERR)
            self.kpi_status.set_value("ERROR", "lihat log untuk detail", C_RED)
            self._append_log_batched("\n[ERROR] Pipeline gagal:\n")
            self._append_log_batched(str(exc) + "\n")
            if tb:
                self._append_log_batched("\n" + tb + "\n")
            messagebox.showerror(
                "Pipeline Gagal",
                f"Terjadi error:\n{exc}\n\nLihat log di tab Proses untuk detail.",
                parent=self.root)
            return

        # Sukses — simpan + muat data ke semua view
        # (defensive: caller test boleh pass None — anggap kosong)
        if append1_df is None:
            append1_df = pd.DataFrame()
        if rincian_po_df is None:
            rincian_po_df = pd.DataFrame()
        if in_detail_df is None:
            in_detail_df = pd.DataFrame()
        self.append1_df = append1_df
        self.rincian_po_df = rincian_po_df
        self.in_detail_df = in_detail_df
        self.audit_result = audit_result
        audit_df = audit_result.get("df") if audit_result else None
        audit_kpi = audit_result.get("kpi") if audit_result else None
        audit_n = len(audit_df) if audit_df is not None else 0
        self.status_var.set("Status: SELESAI.")
        self.statusbar.set_status(
            f"SELESAI — Append1: {len(append1_df):,} rows · "
            f"Rincian PO: {len(rincian_po_df):,} rows · "
            f"IN detail: {len(in_detail_df):,} rows · "
            f"Audit: {audit_n:,} rows", C_GREEN)
        self.kpi_status.set_value("SELESAI", "data siap dianalisis", C_GREEN)
        self.kpi_append.set_value(f"{len(append1_df):,}",
                                  "baris pivot siap di tab 📊")
        self.kpi_rincian.set_value(f"{len(rincian_po_df):,}",
                                   "baris PO siap di tab 🛒")
        self._append_log_batched(f"\n  Append1: {len(append1_df)} rows\n")
        self._append_log_batched(f"  Rincian PO: {len(rincian_po_df)} rows\n")
        if audit_df is not None and audit_n:
            # FIX C-03: log audit ikut format Indonesia (1.234.567) —
            # konsisten dgn formatter tabel & KPI chips.
            self._append_log_batched(
                f"  Audit Rekonsiliasi: {fmt_int_id(audit_n)} rows · "
                f"OK {fmt_int_id(audit_kpi['ok'])} · "
                f"Cut-off {fmt_int_id(audit_kpi['cutoff'])} · "
                f"Valid {fmt_int_id(audit_kpi['omit'])} · "
                f"Deviasi Murni {fmt_int_id(audit_kpi['deviasi_murni'])} · "
                f"Sisa Gantung {fmt_int_id(audit_kpi['deviasi_qty'])}\n")
            # v3.9.30 — deviasi murni ber-PO 'Menunggu diproses'
            # (explainable — akan resolve saat PO diproses jadi RI)
            _n_po = audit_kpi.get("dev_murni_po", 0)
            if _n_po:
                self._append_log_batched(
                    f"  Deviasi Murni ber-PO Menunggu: "
                    f"{fmt_int_id(_n_po)} baris — explainable, sisanya "
                    f"perlu audit fisik\n")
        # v3.9.32 — harga 41.09 (mode Nominal siap?)
        _n_harga = len(audit_result.get("harga_map") or {}) \
            if audit_result else 0
        if _n_harga:
            self._append_log_batched(
                f"  Harga 41.09: {fmt_int_id(_n_harga)} barang — mode "
                f"💰 Nominal (H) tab 📋 Laporan Deviasi siap\n")
        # v3.9.34 — peta harga 41.09 + peta rasio konversi (dari
        # audit_result pipeline) diteruskan ke SEMUA view nominal:
        # kolom Nominal Deviasi GR/PCS, kolom Nominal mode Komparasi,
        # mode 💰 Nominal (H), tab 🧮 Nominal Deviasi (Σ per resto).
        _hm = (audit_result.get("harga_map") if audit_result else None)
        _kv = (audit_result.get("konversi_map") if audit_result else None)

        # Load data into views (v3.2: lazy — hanya tab aktif yang compute;
        # tab lain menunggu dipilih via <<NotebookTabChanged>>)
        # v3.9.33 — AUDIT FIX (48-c HIGH-2): ISOLASI ERROR PER-VIEW — dulu
        # 8 load_data berurutan TANPA try/except: satu view exception →
        # view sisanya data BASI + tombol Export tetap mati + log
        # "[SELESAI]" tak pernah tercetak (padahal status bar sudah hijau).
        # Kini tiap view punya try/except sendiri → error DIBISINGKAN ke
        # log dan sisanya tetap dimuat; jalur error pipeline (on_error)
        # tetap terpisah — tidak tertelan di sini.
        def _load_view(nama: str, fn) -> None:
            try:
                fn()
            except Exception as exc:  # view gagal ≠ pipeline gagal — lanjut
                self._append_log_batched(
                    f"\n[ERROR] Gagal memuat view {nama}: {exc}\n")

        _load_view("📊 Pivot Table",
                   lambda: self.pivot_view.load_data(append1_df))
        # v3.9.23 (poin 6): detail dokumen IN ikut diteruskan ke tab
        # Deviasi GR & PCS — sumber CEK "RI Balancing" kolom utama
        # (bulan Nomor RI ≠ bulan Nomor PO, tanggal dok ≤ H).
        _load_view("📦 Deviasi GR",
                   lambda: self.deviasi_gr_view.load_data(
                       append1_df, in_detail_df,
                       harga_map=_hm, konversi_map=_kv))
        _load_view("🧩 Deviasi PCS",
                   lambda: self.deviasi_pcs_view.load_data(
                       append1_df, in_detail_df,
                       harga_map=_hm, konversi_map=_kv))
        _load_view("📤 Rekap Selisih IN",
                   lambda: self.in_selisih_view.load_data(
                       append1_df, in_detail_df, audit_result=audit_result))
        _load_view("🚨 Anomali COM",
                   lambda: self.laporan_view.load_data(append1_df))
        _load_view("⚖ Komparasi File Deviasi",
                   lambda: self.komparasi_view.load_data(
                       append1_df, harga_map=_hm, konversi_map=_kv))
        # v3.9.32 — mode 💰 Nominal: append1 + peta harga 41.09 + peta
        # rasio konversi (dari audit_result — pipeline v3.9.32;
        # v3.9.34: sumber lokal _hm/_kv bersama semua view nominal)
        _load_view("💰 Nominal (H)",
                   lambda: self.nominal_view.load_data(
                       append1_df, harga_map=_hm, konversi_map=_kv))
        # v3.9.34 — tab 🧮 Nominal Deviasi: Σ nominal per resto
        _load_view("🧮 Nominal Deviasi",
                   lambda: self.nominal_resto_view.load_data(
                       append1_df, harga_map=_hm, konversi_map=_kv))
        _load_view("🛒 Rincian PO",
                   lambda: self.rincian_view.load_data(rincian_po_df))
        self.btn_export.set_enabled(True)
        self.btn_export_tb.set_enabled(True)

        # FIX D-04 (audit 2-d): file Excel di-skip reader (terkunci/
        # hilang/rusak) tidak lagi disembunyikan di balik status hijau
        # "SELESAI" — user berhak tahu datanya parsial.
        if self._skipped_files:
            warn = (f"{fmt_int_id(self._skipped_files)} file Excel "
                    "dilewati (terkunci/hilang/rusak) — lihat log")
            self.statusbar.set_status(f"SELESAI — ⚠ {warn}", C_AMBER)
            self.kpi_status.set_value("SELESAI ⚠", warn, C_AMBER)
            self._append_log_batched(f"\n[PERINGATAN] {warn}\n")

        # Switch to Pivot Table tab (default view) — refresh pivot lewat
        # event tab-changed (lazy loading)
        self.notebook.select(self.tab_pivot)
        self.pivot_view.ensure_refreshed()

        # v3.3: selesai = status bar (hijau) + log — TANPA dialog modal
        # (dulu messagebox "Selesai" mem-blok alur tiap kali pipeline usai)
        self._append_log_batched(
            "\n[SELESAI] Pipeline selesai — data siap dianalisis.\n"
            "Lanjut ke tab 📊 Pivot / 📦 Deviasi GR / 🧩 Deviasi PCS /\n"
            "📤 Rekap Selisih IN / 📋 Laporan / 🧮 Nominal Deviasi /\n"
            "☑ Follow Up / 🛒 Rincian PO.\n")

    def _on_close_window(self):
        """v3.9.33 — AUDIT FIX (48-c LOW): handler tombol X.

        Pipeline masih berjalan → konfirmasi dulu (worker daemon mati
        bersama proses bila user tetap keluar; tidak ada cleanup khusus
        lain di close path — state persist antara-sesi disimpan oleh
        mekanisme masing-masing saat berubah). Idle → langsung tutup."""
        worker = getattr(self, "worker_thread", None)
        pipeline_hIDup = (self.is_running
                          or (worker is not None and worker.is_alive()))
        if pipeline_hIDup and not messagebox.askyesno(
                "Pipeline Masih Berjalan",
                "Pipeline masih berjalan.\n\nTetap keluar? (proses akan "
                "dihentikan paksa)",
                parent=self.root):
            return
        self.root.destroy()

    def _stop_pipeline(self):
        """Stop graceful — set stop_event, pipeline memeriksa di checkpoint."""
        if not self.is_running:
            return
        self.stop_event.set()
        self.is_running = False
        self.btn_stop.set_enabled(False)
        self.status_var.set("Status: menghentikan pipeline…")
        self.statusbar.set_status("menghentikan pipeline…", C_AMBER)
        self.kpi_status.set_value("MENGHENTIKAN…", "menunggu checkpoint", C_AMBER)
        self._append_log_batched(
            "\n[STOP] Permintaan stop dikirim. Pipeline akan berhenti "
            "di checkpoint berikutnya.\n")

    def _export_excel(self):
        """Export data (Append1 + Rincian PO + Rincian IN) ke Excel — async + loading."""
        if self.append1_df is None and self.rincian_po_df is None:
            messagebox.showwarning(
                "Export", "Belum ada data. Jalankan pipeline dulu.",
                parent=self.root)
            return
        filepath = filedialog.asksaveasfilename(
            title="Simpan sebagai Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="stock_monitoring_export.xlsx",
        )
        if not filepath:
            return

        append1_df = self.append1_df
        rincian_po_df = self.rincian_po_df
        in_detail_df = self.in_detail_df
        audit_df = self.audit_result.get("df") if self.audit_result else None

        # loading overlay di tengah jendela utama (dibuat lazily)
        if not hasattr(self, "_export_overlay"):
            self._export_overlay = LoadingOverlay(self.root,
                                                  "Mengekspor ke Excel…")
        self._export_overlay.show("Mengekspor ke Excel…", delay_ms=0)
        self.btn_export.set_enabled(False)
        self.btn_export_tb.set_enabled(False)

        def work():
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                # v3.8: sheet PIVOT ditulis DULU → jadi tab pertama
                # (matrix mutasi barang + conditional formatting ala
                # tab pivot "Mutasi Barang - New" user)
                add_pivot_sheet(writer, append1_df)
                if append1_df is not None and not append1_df.empty:
                    append1_df.to_excel(writer, sheet_name="Append1",
                                        index=False)
                if rincian_po_df is not None and not rincian_po_df.empty:
                    # v3.9.19 (paritas UI): kolom "Nama Resto" — derivasi
                    # sama dgn rincian_po_view (Cabang PO → kode resto,
                    # rsplit titik terakhir; tanpa Cabang PO → "") —
                    # disisipkan tepat setelah Tanggal. Baris tanpa kode
                    # Cabang PO (parent tak terisi / NA) → "".
                    po_export = rincian_po_df.copy()
                    nama_resto = (po_export["Cabang PO"].map(_resto_name)
                                  if "Cabang PO" in po_export.columns
                                  else "")
                    po_cols = list(po_export.columns)
                    pos = (po_cols.index("Tanggal") + 1
                           if "Tanggal" in po_cols else 0)
                    po_export.insert(pos, "Nama Resto", nama_resto)
                    po_export.to_excel(writer, sheet_name="Rincian PO",
                                       index=False)
                # v3.4: detail IN per dokumen (42.05 / 32.24 / 99.01 + nomor)
                if in_detail_df is not None and not in_detail_df.empty:
                    in_detail_df.to_excel(writer, sheet_name="Rincian IN",
                                          index=False)
                # v3.5: hasil Audit Rekonsiliasi (port macro VBA)
                if audit_df is not None and not audit_df.empty:
                    audit_df.to_excel(writer,
                                      sheet_name="Laporan Deviasi (Audit)",
                                      index=False)
            return filepath

        def done(path):
            if self.append1_df is not None:
                self.btn_export.set_enabled(True)
                self.btn_export_tb.set_enabled(True)
            messagebox.showinfo(
                "Export Berhasil", f"Data di-export ke:\n{path}",
                parent=self.root)

        def on_error(e):
            if self.append1_df is not None:
                self.btn_export.set_enabled(True)
                self.btn_export_tb.set_enabled(True)
            messagebox.showerror(
                "Export Gagal", f"Tidak bisa export:\n{e}", parent=self.root)

        run_async(self.root, work, done, overlay=self._export_overlay,
                  loading_text="Mengekspor ke Excel…", on_error=on_error)

    # =====================================================================
    # TAB LAIN (view)
    # =====================================================================
    def _build_pivot_tab(self):
        self.pivot_view = PivotTableView(
            self.tab_pivot, go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.pivot_view.pack(fill="both", expand=True)

    def _build_deviasi_gr_tab(self):
        # v3.9: tab GR = satu-satunya pemegang input H + Apply H
        self.deviasi_gr_view = DeviasiView(
            self.tab_deviasi_gr, satuan_mode="GR",
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            followup_store=self.followup_store,
            shared_cache=self._deviasi_pivot_cache,
            h_state=self._shared_h, h_editable=True,
            acr_state=self._shared_acr)   # v3.9.21 — ambang ACR bersama
        self.deviasi_gr_view.pack(fill="both", expand=True)

    def _build_deviasi_pcs_tab(self):
        # v3.9: tab PCS TANPA input H — ikut H bersama dari tab GR
        # (chip read-only + auto-refresh saat H di-apply di tab GR)
        self.deviasi_pcs_view = DeviasiView(
            self.tab_deviasi_pcs, satuan_mode="PCS",
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            followup_store=self.followup_store,
            shared_cache=self._deviasi_pivot_cache,
            h_state=self._shared_h, h_editable=False,
            acr_state=self._shared_acr)   # v3.9.21 — ambang ACR bersama
        self.deviasi_pcs_view.pack(fill="both", expand=True)

    def _build_in_selisih_tab(self):
        """v3.4 — tab 📤 Rekap Selisih IN (drill-down rincian dokumen IN)."""
        self.in_selisih_view = InSelisihView(
            self.tab_in_selisih,
            go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.in_selisih_view.pack(fill="both", expand=True)

    def _build_laporan_tab(self):
        # v3.9.4: tab 📋 Laporan Deviasi = 2 MODE via SegmentBar:
        # ⚖ Komparasi File Deviasi (default — v3.9.4) & 🚨 Anomali COM
        # (v3.9.3, H bersama chip read-only + auto-refresh dari tab GR).
        # v3.9.32: mode ke-3 💰 Nominal (H) — Harga 41.09 × Qty Deviasi
        # per pasangan + baris TOTAL (user: "tab baru Nominal = Harga ×
        # kuantitas deviasi, per barang + total").
        self._laporan_container = tk.Frame(self.tab_laporan, bg=C_BG)
        self._laporan_container.pack(fill="both", expand=True)

        bar = tk.Frame(self._laporan_container, bg=C_BG)
        bar.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(bar, text="MODE", bg=C_BG, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left", padx=(0, 6))
        self.laporan_segment = SegmentBar(
            bar, ["⚖ Komparasi File Deviasi", "🚨 Anomali COM (H)",
                  "💰 Nominal (H)"],
            command=lambda idx: self.show_laporan_mode(idx))
        self.laporan_segment.pack(side="left")

        self.komparasi_view = KomparasiDeviasiView(
            self._laporan_container,
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            followup_store=self.followup_store,
            initial_dir=(self.rootpath_var.get().strip()
                         if getattr(self, "rootpath_var", None) is not None
                         else ""),
            h_state=self._shared_h)   # v3.9.7: filter minggu file
        self.laporan_view = LaporanDeviasiView(
            self._laporan_container,
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            followup_store=self.followup_store,
            h_state=self._shared_h)
        # v3.9.32 — mode Nominal: Harga × Qty Deviasi (+ baris TOTAL)
        self.nominal_view = NominalDeviasiView(
            self._laporan_container,
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            h_state=self._shared_h)
        # default: mode 0 (Komparasi) — COM & Nominal tersembunyi
        self.komparasi_view.pack(fill="both", expand=True)
        self.laporan_view.pack_forget()
        self.nominal_view.pack_forget()

    def show_laporan_mode(self, idx: int):
        """v3.9.4 — ganti mode tab 📋 Laporan Deviasi (dipakai SegmentBar
        & test): 0 = ⚖ Komparasi File, 1 = 🚨 Anomali COM,
        2 = 💰 Nominal (v3.9.32).
        v3.9.5 FIX (audit 19-c #7): sinkronkan SegmentBar (set_active_silent)
        — dulu pemanggilan programatik membuat segment.active basi →
        _on_tab_changed me-refresh pane yang SALAH & tombol mode tetap
        menyala di posisi lama."""
        if idx not in (0, 1, 2):
            idx = 0
        self.laporan_segment.set_active_silent(idx)
        # lepas semua pane lalu pack pane aktif (urutan pack konsisten)
        self.laporan_view.pack_forget()
        self.nominal_view.pack_forget()
        self.komparasi_view.pack_forget()
        if idx == 0:
            self.komparasi_view.pack(fill="both", expand=True)
            self.komparasi_view.ensure_refreshed()
        elif idx == 2:
            self.nominal_view.pack(fill="both", expand=True)
            self.nominal_view.ensure_refreshed()
        else:
            self.laporan_view.pack(fill="both", expand=True)
            self.laporan_view.ensure_refreshed()

    def _build_nominal_resto_tab(self):
        """v3.9.34 — tab 🧮 Nominal Deviasi: Σ (Harga 41.09 × Qty
        Deviasi) per resto + TOTAL + double-click resto → rincian per
        barang (user: "ada tab nominal Deviasi, isinya total sum dari
        nama barang kayak di laporan sampel kolom nominal deviasi, yang
        dapat dari harga × kuantitas deviasi, cuman ini disum per
        resto")."""
        self.nominal_resto_view = NominalRestoView(
            self.tab_nominal_resto,
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            h_state=self._shared_h)
        self.nominal_resto_view.pack(fill="both", expand=True)

    def _build_followup_tab(self):
        self.followup_view = FollowUpView(
            self.tab_followup, self.followup_store,
            get_data=lambda: self.append1_df,
            go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.followup_view.pack(fill="both", expand=True)
        # badge tab ikut berubah saat daftar berubah
        self.followup_store.add_listener(
            lambda _s: self.root.after(0, self._update_followup_badge))

    def _build_rincian_tab(self):
        self.rincian_view = RincianPoView(
            self.tab_rincian,
            go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.rincian_view.pack(fill="both", expand=True)


# --- Entry point ------------------------------------------------------------
def _enable_windows_dpi_awareness(root: tk.Tk) -> None:
    """FIX A-03 (audit 2-a): Windows DPI-aware (125%/150%) supaya teks &
    tabel tidak di-bitmap-scale (blur) oleh OS.

    No-op di Linux/macOS. SetProcessDpiAwareness(PER_MONITOR) → ukuran
    font Tk mengikuti DPI monitor aktual (tk scaling = dpi/72).
    Catatan: butuh verifikasi visual di mesin Windows asli.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            # 1 = PER_MONITOR_DPI_AWARE (tajam di semua monitor campuran)
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            # fallback Windows versi lama (< 8.1)
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        return
    try:
        dpi = root.winfo_fpixels("1i")  # piksel per inci fisik
        if dpi > 0:
            root.tk.call("tk", "scaling", dpi / 72.0)
    except Exception:
        pass


def main():
    root = tk.Tk()
    _enable_windows_dpi_awareness(root)
    StockMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
