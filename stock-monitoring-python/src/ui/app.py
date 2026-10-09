"""
app.py — Shell UI Stock Monitoring v3.9.11.

Struktur jendela (ala aplikasi Waste):
    ┌────────────────────────────────────────────────────┐
    │ ⬛ Toolbar gelap: 📊 judul + v3.9.11 + [💾 Export] │
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
                          (input TANGGAL H + Apply H — satu-satunya)
  5. 🧩 DEVIASI PCS     : wide matrix + CEK anomaly (non-GR) + ✓
                          (chip H read-only, ikut tab GR — v3.9)
  6. 🎯 PARETO          : 80/20 kontributor |Deviasi| terbesar — fokus
                          list ≤ cutoff % + grafik + KPI + export (v3.9.9)
  7. 📤 Rekap Selisih IN: SATU tabel IN (Accurate) vs Barang Masuk +
                          kolom SO + kolom Hasil Audit (logika macro VBA ×
                          data app — v3.6, tanpa sheet 29) + drill-down
  8. 📋 Laporan Deviasi : 2 MODE — ⚖ Komparasi File Deviasi (default,
                          v3.9.4) & 🚨 Anomali COM (v3.9.3) + ✓
  9. ☑ Follow Up        : daftar baris tercentang + export (v3.2)
 10. 🛒 Rincian PO      : rekap PO + item (baris teal/putih, v3.9)

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
from src.ui.deviasi_view import DeviasiView, SharedPivotCache, SharedTanggalH
from src.ui.export_sheets import add_pivot_sheet
from src.ui.followup import FollowUpStore
from src.ui.followup_view import FollowUpView
from src.ui.in_selisih_view import InSelisihView
from src.ui.komparasi_deviasi_view import KomparasiDeviasiView
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.pareto_view import ParetoDeviasiView
from src.ui.pivot_view import PivotTableView
from src.ui.rincian_po_view import RincianPoView
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
APP_VERSION = "3.9.11"  # v3.9.11 — TUNTAS: sisa temuan P3 audit 2-b (7 fix) + repo GitHub di-private
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
# v3.9.9 (TAB 🎯 PARETO — "mau coba pareto"):
# (1) tab BARU 🎯 Pareto (index 5, setelah Deviasi PCS): analisis 80/20
#     kontributor |Deviasi| — semua kombinasi (Barang × Resto × Satuan)
#     diurut |Deviasi| menurun + Kontribusi % + Kumulatif % + Fokus 🎯
#     (baris yang diperlukan mencapai CUTOFF %, default 80, input
#     1-100); (2) MODE GR/PCS via SegmentBar + TANGGAL H chip read-only
#     (state bersama); (3) KPI: KOMBINASI · TOTAL |DEVIASI| · FOKUS
#     ≤CUTOFF · TOP 20% → %; (4) GRAFIK canvas (top-30 batang teal +
#     garis kumulatif amber + garis cutoff merah + batas fokus); (5)
#     ✓ follow-up fingerprint IDENTIK tab Deviasi (dedup satu entri);
#     (6) export 💾 sheet PARETO (angka mentah + meta). Pivot dihitung
#     SEKALI lewat SharedPivotCache (ParetoDeviasiView = subclass
#     DeviasiView); index tab setelah Pareto bergeser +1 (Selisih IN 6,
#     Laporan 7, Rincian 9).

# v3.9.6 (3 permintaan user sekaligus):
# (1) "tambah kategori Deviasi pada tab Deviasi PCS dan GR" — 5 kolom
#     baru (mirror sheet DEVIASI GR/PCS workbook asli): Max Deviasi ·
#     ACR (rata-rata penjualan harian = Σ 9.OUT 1..H / H) · Total ACR
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
#     9.OUT, tgl 1..H — "2205 itu bom"), COM·App = Σ pemakaian com(t)
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
        self._shared_h = SharedTanggalH(25)

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
        self.tab_pareto = tk.Frame(self.notebook, bg=C_BG)
        self.tab_in_selisih = tk.Frame(self.notebook, bg=C_BG)
        self.tab_laporan = tk.Frame(self.notebook, bg=C_BG)
        self.tab_followup = tk.Frame(self.notebook, bg=C_BG)
        self.tab_rincian = tk.Frame(self.notebook, bg=C_BG)

        self.notebook.add(self.tab_config, text="⚙️ Config")
        self.notebook.add(self.tab_proses, text="🚀 Proses")
        self.notebook.add(self.tab_pivot, text="📊 Pivot Table")
        self.notebook.add(self.tab_deviasi_gr, text="📦 Deviasi GR")
        self.notebook.add(self.tab_deviasi_pcs, text="🧩 Deviasi PCS")
        self.notebook.add(self.tab_pareto, text="🎯 Pareto")
        self.notebook.add(self.tab_in_selisih, text="📤 Rekap Selisih IN")
        self.notebook.add(self.tab_laporan, text="📋 Laporan Deviasi")
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
        self._build_pareto_tab()
        self._build_in_selisih_tab()
        self._build_laporan_tab()
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
            view = (self.komparasi_view
                    if getattr(self, "laporan_segment", None) is not None
                    and self.laporan_segment.active == 0
                    else self.laporan_view)
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
            str(self.tab_pareto): self.pareto_view,
            str(self.tab_in_selisih): self.in_selisih_view,
            str(self.tab_laporan): self._laporan_tab_entry,
            str(self.tab_rincian): self.rincian_view,
        }

    def _update_followup_badge(self):
        """Badge jumlah baris di judul tab Follow Up."""
        try:
            n = len(self.followup_store)
            # FIX H-1 (audit 2-a hipotesis — TERKONFIRMASI): label tab
            # TANPA spasi ganda + padding ramping → 10 tab muat di lebar
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
            self.log_text.delete("1.0", "1001.0")
            self._log_line_count -= 1000

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
            self.root.after(0, lambda: self._on_pipeline_done(
                append1_df, rincian_po_df, in_detail_df, audit_result, None))
        except PipelineStopped as exc:
            err = (exc, None)
            self.root.after(0, lambda: self._on_pipeline_done(None, None, None, None, err))
        except Exception as exc:
            import traceback
            err = (exc, traceback.format_exc())
            self.root.after(0, lambda: self._on_pipeline_done(None, None, None, None, err))

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

        # Load data into views (v3.2: lazy — hanya tab aktif yang compute;
        # tab lain menunggu dipilih via <<NotebookTabChanged>>)
        self.pivot_view.load_data(append1_df)
        self.deviasi_gr_view.load_data(append1_df)
        self.deviasi_pcs_view.load_data(append1_df)
        self.pareto_view.load_data(append1_df)  # v3.9.9 — tab 🎯 Pareto
        self.in_selisih_view.load_data(append1_df, in_detail_df,
                                      audit_result=audit_result)
        self.laporan_view.load_data(append1_df)
        self.komparasi_view.load_data(append1_df)  # v3.9.4 — mode komparasi
        self.rincian_view.load_data(rincian_po_df)
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
            "📤 Rekap Selisih IN / 📋 Laporan / ☑ Follow Up / 🛒 Rincian PO.\n")

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
                    rincian_po_df.to_excel(writer, sheet_name="Rincian PO",
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
            h_state=self._shared_h, h_editable=True)
        self.deviasi_gr_view.pack(fill="both", expand=True)

    def _build_deviasi_pcs_tab(self):
        # v3.9: tab PCS TANPA input H — ikut H bersama dari tab GR
        # (chip read-only + auto-refresh saat H di-apply di tab GR)
        self.deviasi_pcs_view = DeviasiView(
            self.tab_deviasi_pcs, satuan_mode="PCS",
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            followup_store=self.followup_store,
            shared_cache=self._deviasi_pivot_cache,
            h_state=self._shared_h, h_editable=False)
        self.deviasi_pcs_view.pack(fill="both", expand=True)

    def _build_pareto_tab(self):
        """v3.9.9 — tab 🎯 Pareto: kontributor |Deviasi| terbesar 80/20.
        Subclass DeviasiView → pivot cache DIBAGI (tanpa recompute) +
        H bersama (chip read-only, ikut Apply H di tab GR)."""
        self.pareto_view = ParetoDeviasiView(
            self.tab_pareto,
            go_to_proses=lambda: self.notebook.select(self.tab_proses),
            followup_store=self.followup_store,
            shared_cache=self._deviasi_pivot_cache,
            h_state=self._shared_h)
        self.pareto_view.pack(fill="both", expand=True)

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
        self._laporan_container = tk.Frame(self.tab_laporan, bg=C_BG)
        self._laporan_container.pack(fill="both", expand=True)

        bar = tk.Frame(self._laporan_container, bg=C_BG)
        bar.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(bar, text="MODE", bg=C_BG, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left", padx=(0, 6))
        self.laporan_segment = SegmentBar(
            bar, ["⚖ Komparasi File Deviasi", "🚨 Anomali COM (H)"],
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
        # default: mode 0 (Komparasi) — Anomali COM tersembunyi
        self.komparasi_view.pack(fill="both", expand=True)
        self.laporan_view.pack_forget()

    def show_laporan_mode(self, idx: int):
        """v3.9.4 — ganti mode tab 📋 Laporan Deviasi (dipakai SegmentBar
        & test): 0 = ⚖ Komparasi File, 1 = 🚨 Anomali COM.
        v3.9.5 FIX (audit 19-c #7): sinkronkan SegmentBar (set_active_silent)
        — dulu pemanggilan programatik membuat segment.active basi →
        _on_tab_changed me-refresh pane yang SALAH & tombol mode tetap
        menyala di posisi lama."""
        if idx not in (0, 1):
            idx = 0
        self.laporan_segment.set_active_silent(idx)
        if idx == 0:
            self.laporan_view.pack_forget()
            self.komparasi_view.pack(fill="both", expand=True)
            self.komparasi_view.ensure_refreshed()
        else:
            self.komparasi_view.pack_forget()
            self.laporan_view.pack(fill="both", expand=True)
            self.laporan_view.ensure_refreshed()

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
