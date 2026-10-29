#!/usr/bin/env python3
"""v3.11.17/v3.11.18 (restored) — PULIHKAN IKON TERKURASI + BERSIHKAN SLOP.

Rekonstruksi sesi v3.11.18: repo sandbox lokal hilang saat reset (commit
v3.11.17+v3.11.18 tidak pernah ter-push — GitHub masih v3.11.16). Script ini
memulihkan pekerjaan itu di atas v3.11.16 dengan pasangan (file, old, new,
count) tervalidasi: tiap pasangan HARUS cocok persis `count` kali —
mismatch = ABORT (tidak ada edit parsial diam-diam).

Kurasi (pengganti kosakata v3.11.12 yang hilang bersama sandbox):
- Tab: ⚙️ Config · 🚀 Proses · 🧮 Pivot Table · 📦 Deviasi GR · 🧩 Deviasi PCS
  · 📤 Rekap Selisih IN · 📋 Laporan Deviasi · 💰 Nominal Deviasi · ☑ Follow
  Up · 🛒 Rincian PO (🧮/💰 dikurasi ulang — v3.11.12 memakai 📊/🧮).
- "📂 Muat ke Komparasi Sekarang" TANPA ⚖ di tengah (kutipan baca v3.11.17).
- TETAP POLOS (slop, sesuai v3.11.17): EmptyState (judul/subjudul/CTA),
  pesan status/log/toast/dialog, header seksi analisa (1 · UMUR GANTUNG dst
  · SKOR RESTO · SELISIH TERBANYAK · ANALISA REKONSILIASI), legenda chip,
  judul popup (🔍 Detail… · ⚖ Komparasi Deviasi — · 🧮 Nominal Deviasi —),
  bar mode pivot [Resto | Tanggal], tombol [📅 Bulan Ini | 📆 Lalu + Ini].
- v3.11.18: label "MUAT FILE:" → "Mode muat:" · 🫵 U+1FAF5 (bukan 🫅).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # stock-monitoring-python/

# (path, old, new, expected_count)
PAIRS = [
    # ---------------- app.py: 3 daftar label tab + badge ----------------
    ("src/ui/app.py", '"Config": "Config",', '"⚙️ Config": "Config",', 1),
    ("src/ui/app.py", '"Proses": "Proses",', '"🚀 Proses": "Proses",', 1),
    ("src/ui/app.py", '"Pivot Table": "Pivot",', '"🧮 Pivot Table": "Pivot",', 1),
    ("src/ui/app.py", '"Deviasi GR": "Deviasi GR",', '"📦 Deviasi GR": "Deviasi GR",', 1),
    ("src/ui/app.py", '"Deviasi PCS": "Deviasi PCS",', '"🧩 Deviasi PCS": "Deviasi PCS",', 1),
    ("src/ui/app.py", '"Rekap Selisih IN": "Selisih IN",', '"📤 Rekap Selisih IN": "Selisih IN",', 1),
    ("src/ui/app.py", '"Laporan Deviasi": "Laporan",', '"📋 Laporan Deviasi": "Laporan",', 1),
    ("src/ui/app.py", '"Nominal Deviasi": "Nominal",', '"💰 Nominal Deviasi": "Nominal",', 1),
    ("src/ui/app.py", '"Rincian PO": "Rincian PO",', '"🛒 Rincian PO": "Rincian PO",', 1),
    ("src/ui/app.py", 'str(self.tab_config): "Config",', 'str(self.tab_config): "⚙️ Config",', 1),
    ("src/ui/app.py", 'str(self.tab_proses): "Proses",', 'str(self.tab_proses): "🚀 Proses",', 1),
    ("src/ui/app.py", 'str(self.tab_pivot): "Pivot Table",', 'str(self.tab_pivot): "🧮 Pivot Table",', 1),
    ("src/ui/app.py", 'str(self.tab_deviasi_gr): "Deviasi GR",', 'str(self.tab_deviasi_gr): "📦 Deviasi GR",', 1),
    ("src/ui/app.py", 'str(self.tab_deviasi_pcs): "Deviasi PCS",', 'str(self.tab_deviasi_pcs): "🧩 Deviasi PCS",', 1),
    ("src/ui/app.py", 'str(self.tab_in_selisih): "Rekap Selisih IN",', 'str(self.tab_in_selisih): "📤 Rekap Selisih IN",', 1),
    ("src/ui/app.py", 'str(self.tab_laporan): "Laporan Deviasi",', 'str(self.tab_laporan): "📋 Laporan Deviasi",', 1),
    ("src/ui/app.py", 'str(self.tab_nominal_resto): "Nominal Deviasi",', 'str(self.tab_nominal_resto): "💰 Nominal Deviasi",', 1),
    ("src/ui/app.py", 'str(self.tab_followup): "Follow Up",', 'str(self.tab_followup): "☑ Follow Up",', 1),
    ("src/ui/app.py", 'str(self.tab_rincian): "Rincian PO",', 'str(self.tab_rincian): "🛒 Rincian PO",', 1),
    ("src/ui/app.py", 'text="Config")', 'text="⚙️ Config")', 1),
    ("src/ui/app.py", 'text="Proses")', 'text="🚀 Proses")', 1),
    ("src/ui/app.py", 'text="Pivot Table")', 'text="🧮 Pivot Table")', 1),
    ("src/ui/app.py", 'text="Deviasi GR")', 'text="📦 Deviasi GR")', 1),
    ("src/ui/app.py", 'text="Deviasi PCS")', 'text="🧩 Deviasi PCS")', 1),
    ("src/ui/app.py", 'text="Rekap Selisih IN")', 'text="📤 Rekap Selisih IN")', 1),
    ("src/ui/app.py", 'text="Laporan Deviasi")', 'text="📋 Laporan Deviasi")', 1),
    ("src/ui/app.py", 'text="Nominal Deviasi")', 'text="💰 Nominal Deviasi")', 1),
    ("src/ui/app.py", 'text="Follow Up")', 'text="☑ Follow Up")', 1),
    ("src/ui/app.py", 'text="Rincian PO")', 'text="🛒 Rincian PO")', 1),
    ("src/ui/app.py", 'f"Follow Up{\' (\' + str(n) + \')\' if n else \'\'}"',
     'f"☑ Follow Up{\' (\' + str(n) + \')\' if n else \'\'}"', 1),
    # ---------------- app.py: toolbar + kartu Config ----------------
    ("src/ui/app.py", '"Refresh Sumber", command=self._open_refresh_dialog)',
     '"↻ Refresh Sumber", command=self._open_refresh_dialog)', 1),
    ("src/ui/app.py", '"Export Excel", command=self._export_excel, accent=True)',
     '"💾 Export Excel", command=self._export_excel, accent=True)', 1),
    ("src/ui/app.py", 'text="Browse…"', 'text="📂 Browse…"', 1),
    ("src/ui/app.py", 'text="Simpan Config"', 'text="💾 Simpan Config"', 1),
    ("src/ui/app.py", 'text="Reload Config"', 'text="↻ Reload Config"', 1),
    ("src/ui/app.py", 'text="Identifikasi…"', 'text="🎯 Identifikasi…"', 1),
    ("src/ui/app.py", 'text="Edit…"', 'text="✏️ Edit…"', 1),
    ("src/ui/app.py", 'text="Hapus"', 'text="🗑 Hapus"', 1),
    # ---------------- app.py: kartu Proses ----------------
    ("src/ui/app.py", 'text="MULAI PROSES"', 'text="🚀 MULAI PROSES"', 1),
    ("src/ui/app.py", 'text="Stop"', 'text="⏹ Stop"', 1),
    ("src/ui/app.py", 'text="Bersihkan Log"', 'text="🧹 Bersihkan Log"', 1),
    ("src/ui/app.py", 'text="Salin Log"', 'text="📋 Salin Log"', 1),
    ("src/ui/app.py", 'text="Refresh Sumber"', 'text="↻ Refresh Sumber"', 1),
    ("src/ui/app.py", 'text="Export Excel"', 'text="💾 Export Excel"', 1),
    # ---------------- app.py: mode bar Laporan + dbul ------------------
    ("src/ui/app.py", '["Komparasi File Deviasi", "Anomali COM (H)",',
     '["⚖ Komparasi File Deviasi", "🚨 Anomali COM (H)",', 1),
    ("src/ui/app.py", 'text="MUAT FILE:"', 'text="Mode muat:"', 1),
    ("src/ui/app.py", '["Manual (tombol)",', '["🫵 Manual (tombol)",', 1),
    ("src/ui/app.py", '"Otomatis pasca-pipeline"]', '"⚡ Otomatis pasca-pipeline"]', 1),
    ("src/ui/app.py", 'text="Muat ke Komparasi Sekarang"',
     'text="📂 Muat ke Komparasi Sekarang"', 1),
    # ---------------- deviasi_view.py ----------------
    ("src/ui/deviasi_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 1),
    ("src/ui/deviasi_view.py", 'text="Perbesar"', 'text="⤢ Perbesar"', 1),
    ("src/ui/deviasi_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/deviasi_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/deviasi_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 1),
    ("src/ui/deviasi_view.py", 'text="· atur di Deviasi GR"', 'text="· atur di 📦 Deviasi GR"', 1),
    # ---------------- followup_view.py ----------------
    ("src/ui/followup_view.py", 'text="Export Excel"', 'text="💾 Export Excel"', 1),
    ("src/ui/followup_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 1),
    ("src/ui/followup_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/followup_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/followup_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    # ---------------- in_selisih_view.py ----------------
    ("src/ui/in_selisih_view.py", '["Tabel", "Analisa"]', '["📋 Tabel", "📈 Analisa"]', 1),
    ("src/ui/in_selisih_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 2),
    ("src/ui/in_selisih_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 2),
    ("src/ui/in_selisih_view.py", 'text="Semua Nomor"', 'text="📋 Semua Nomor"', 1),
    ("src/ui/in_selisih_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/in_selisih_view.py", 'text="Export Excel"', 'text="💾 Export Excel"', 2),
    ("src/ui/in_selisih_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/in_selisih_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 1),
    ("src/ui/in_selisih_view.py", 'text="Perbesar"', 'text="⤢ Perbesar"', 1),
    ("src/ui/in_selisih_view.py", 'text="Export Rekap Selisih IN per Resto"',
     'text="💾 Export Rekap Selisih IN per Resto"', 1),
    ("src/ui/in_selisih_view.py", 'label="Copy baris (tab-separated)"',
     'label="📋 Copy baris (tab-separated)"', 1),
    # ---------------- komparasi_deviasi_view.py ----------------
    ("src/ui/komparasi_deviasi_view.py", '["Tabel", "Analisa"]', '["📋 Tabel", "📈 Analisa"]', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Pilih File Deviasi…"', 'text="📂 Pilih File Deviasi…"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Muat Ulang File"', 'text="↻ Muat Ulang File"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Export Excel"', 'text="💾 Export Excel"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 3),
    ("src/ui/komparasi_deviasi_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Terapkan"', 'text="↻ Terapkan"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="Tutup File"', 'text="✕ Tutup File"', 1),
    ("src/ui/komparasi_deviasi_view.py", 'text="· atur di Deviasi GR"', 'text="· atur di 📦 Deviasi GR"', 1),
    # ---------------- laporan_deviasi_view.py ----------------
    ("src/ui/laporan_deviasi_view.py", 'text="Export Excel"', 'text="💾 Export Excel"', 1),
    ("src/ui/laporan_deviasi_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 1),
    ("src/ui/laporan_deviasi_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/laporan_deviasi_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/laporan_deviasi_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/laporan_deviasi_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 1),
    ("src/ui/laporan_deviasi_view.py", 'text="TANGGAL H · atur di Deviasi GR"',
     'text="TANGGAL H · atur di 📦 Deviasi GR"', 1),
    # ---------------- nominal_deviasi_view.py ----------------
    ("src/ui/nominal_deviasi_view.py", 'text="Export Excel"', 'text="💾 Export Excel"', 1),
    ("src/ui/nominal_deviasi_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 1),
    ("src/ui/nominal_deviasi_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/nominal_deviasi_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/nominal_deviasi_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/nominal_deviasi_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 1),
    ("src/ui/nominal_deviasi_view.py", 'text="TANGGAL H · atur di Deviasi GR"',
     'text="TANGGAL H · atur di 📦 Deviasi GR"', 1),
    # ---------------- nominal_resto_view.py ----------------
    ("src/ui/nominal_resto_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 2),
    ("src/ui/nominal_resto_view.py", 'text="Muat Lebar"', 'text="↺ Muat Lebar"', 1),
    ("src/ui/nominal_resto_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/nominal_resto_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/nominal_resto_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 2),
    ("src/ui/nominal_resto_view.py", 'text="Export Excel"', 'text="💾 Export Excel"', 1),
    ("src/ui/nominal_resto_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 2),
    ("src/ui/nominal_resto_view.py", 'text="TANGGAL H · atur di Deviasi GR"',
     'text="TANGGAL H · atur di 📦 Deviasi GR"', 1),
    # ---------------- pivot_view.py (mode [Resto|Tanggal] TETAP polos) --
    ("src/ui/pivot_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 1),
    ("src/ui/pivot_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/pivot_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/pivot_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/pivot_view.py", 'text="Export Excel"', 'text="💾 Export Excel"', 1),
    ("src/ui/pivot_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 1),
    # ---------------- refresh_sources.py (judul popup tetap polos) ----
    ("src/ui/refresh_sources.py", 'text="Refresh Semua"', 'text="↻ Refresh Semua"', 1),
    ("src/ui/refresh_sources.py", 'text="Refresh Terpilih (0)"', 'text="↻ Refresh Terpilih (0)"', 1),
    ("src/ui/refresh_sources.py", 'text=f"Refresh Terpilih ({k})"',
     'text=f"↻ Refresh Terpilih ({k})"', 1),
    # ---------------- rincian_po_view.py ----------------
    ("src/ui/rincian_po_view.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 1),
    ("src/ui/rincian_po_view.py", 'text="Perbesar Tabel"', 'text="⤢ Perbesar Tabel"', 1),
    ("src/ui/rincian_po_view.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/rincian_po_view.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/rincian_po_view.py", 'text="Reset Filter"', 'text="✕ Reset Filter"', 1),
    # ---------------- details_popup.py (judul popup tetap polos) ------
    ("src/ui/details_popup.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/details_popup.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
    ("src/ui/details_popup.py", 'text="Layar Penuh"', 'text="⛶ Layar Penuh"', 1),
    ("src/ui/details_popup.py", 'text="Semua Nomor"', 'text="📋 Semua Nomor"', 1),
    ("src/ui/details_popup.py", 'text="Semua Nomor PO"', 'text="📋 Semua Nomor PO"', 1),
    ("src/ui/details_popup.py", 'label="Copy seluruh baris (tab-separated)"',
     'label="📋 Copy seluruh baris (tab-separated)"', 1),
    ("src/ui/details_popup.py", 'label="Copy SEMUA Nomor (unik)"',
     'label="📋 Copy SEMUA Nomor (unik)"', 1),
    ("src/ui/details_popup.py", 'label="Copy SEMUA Nomor PO (unik)"',
     'label="📋 Copy SEMUA Nomor PO (unik)"', 1),
    ("src/ui/details_popup.py", 'label="Layar Penuh"', 'label="⛶ Layar Penuh"', 1),
    # ---------------- deviasi_popup.py (judul popup tetap polos) ------
    ("src/ui/deviasi_popup.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/deviasi_popup.py", 'text="Semua Nomor"', 'text="📋 Semua Nomor"', 1),
    ("src/ui/deviasi_popup.py", 'text="Semua Nomor PO"', 'text="📋 Semua Nomor PO"', 1),
    ("src/ui/deviasi_popup.py", 'label="Copy seluruh baris (tab-separated)"',
     'label="📋 Copy seluruh baris (tab-separated)"', 1),
    ("src/ui/deviasi_popup.py", 'label="Copy SEMUA Nomor (unik)"',
     'label="📋 Copy SEMUA Nomor (unik)"', 1),
    ("src/ui/deviasi_popup.py", 'label="Copy SEMUA Nomor PO (unik)"',
     'label="📋 Copy SEMUA Nomor PO (unik)"', 1),
    # ---------------- widgets.py ----------------
    ("src/ui/widgets.py", 'text_expand="Perbesar Tabel"',
     'text_expand="⤢ Perbesar Tabel"', 1),
    ("src/ui/widgets.py", 'text_restore="Tampilkan Filter & KPI"',
     'text_restore="⤡ Tampilkan Filter & KPI"', 1),
    ("src/ui/widgets.py", 'text="Reset"', 'text="↺ Reset"', 1),
    ("src/ui/widgets.py", 'text="Balik"', 'text="↔ Balik"', 1),
    ("src/ui/widgets.py", 'text="Sort A→Z"', 'text="↕ Sort A→Z"', 1),
    ("src/ui/widgets.py", 'text="Sort Z→A"', 'text="↕ Sort Z→A"', 1),
    ("src/ui/widgets.py", 'label="Auto-fit kolom ini"', 'label="↔ Auto-fit kolom ini"', 1),
    ("src/ui/widgets.py", 'label="Tampilkan Semua Kolom"', 'label="▦ Tampilkan Semua Kolom"', 1),
    ("src/ui/widgets.py", 'label="Panel Kolom…"', 'label="◫ Panel Kolom…"', 1),
    ("src/ui/widgets.py", 'label="Auto-fit Semua Kolom"', 'label="↔ Auto-fit Semua Kolom"', 1),
    ("src/ui/widgets.py", 'text="Tampilkan Semua"', 'text="▦ Tampilkan Semua"', 1),
    ("src/ui/widgets.py", 'text="Kolom yang ditampilkan"', 'text="◫ Kolom yang ditampilkan"', 1),
    ("src/ui/widgets.py", 'text="Auto-Fit"', 'text="↔ Auto-Fit"', 1),
    ("src/ui/widgets.py", 'text="Kolom"', 'text="◱ Kolom"', 1),
]

# SLOP: paragraf kategori manual (v3.11.16, 405 char) → versi padat
P_SLOP_KAT = '''                 text="Daftar barang bersaldo dari file 42.17 yang "
                      "ditarik saat analisa (hanya yang ada saldo) — "
                      "kategori 42.17 = kolom 'Kategori Barang' file; "
                      "kategori app = pipeline (rekap/master) + mapping "
                      "manual. Barang tanpa kategori app (amber) diberi "
                      "kategori manual — tersimpan di config.json (key "
                      "KategoriManual, prioritas tertinggi) dan diterapkan "
                      "mulai run pipeline BERIKUTNYA (F5). Barang yang "
                      "pertama kali muncul di 42.17 ditandai BARU. Mapping "
                      "bisa diedit / dihapus kapan saja (barang kembali ke "
                      "kategori otomatis).",'''
P_CLEAN_KAT = '''                 text="Daftar barang bersaldo dari file 42.17 — "
                      "kategori 42.17 dari kolom file, kategori app dari "
                      "pipeline + mapping manual. Baris amber belum punya "
                      "kategori app: klik 🎯 Identifikasi… untuk mengisi "
                      "(prioritas tertinggi, diterapkan mulai run pipeline "
                      "berikutnya). Barang yang baru muncul ditandai BARU; "
                      "mapping bisa diedit / dihapus kapan saja.",'''

# SLOP: hint Auto File Deviasi Bulan Lalu (430→215 char, teks v3.11.17)
P_CLEAN_DBUL = '''                 text="Folder file deviasi bulan lalu (nama file mis. "
                      "20.AGUSTUS 2026). Jumlah File = berapa bulan mundur "
                      "dari bulan data (1–12). Manual (default): muat "
                      "sendiri via tombol. Otomatis: dimuat setelah "
                      "pipeline selesai.",'''

# SLOP: judul kartu kategori — folder cukup di subheader
P_SLOP_TITLE = '''        tk.Label(kat_inner, text="Identifikasi Kategori Manual "
                 "(sumber: 42.17 — folder '6. 42.17')", bg=C_CARD,'''
P_CLEAN_TITLE = '''        tk.Label(kat_inner, text="Identifikasi Kategori Manual", bg=C_CARD,'''


def _find_dbul_block(src: str):
    """Blok hint dbul lama: mulai baris text="Folder file deviasi ... sampai
    baris berakhir `",` setelah frasa 'Otomatis = dimuat ...'."""
    i = src.find('text="Folder file deviasi bulan lalu (format nama file "')
    if i < 0:
        return None, None
    # cari akhir literal: baris yang menutup paragraf dengan `",`
    probe = src.find('Otomatis = dimuat')
    if probe < 0:
        return None, None
    end = src.find('",', probe)
    if end < 0:
        return None, None
    end_line = src.find('\n', end)
    return i, end_line + 1 if end_line > 0 else len(src)


def main():
    apply = "--apply" in sys.argv
    texts = {rel: (ROOT / rel).read_text(encoding="utf-8")
             for rel in sorted({p[0] for p in PAIRS})}

    app = "src/ui/app.py"
    src = texts[app]
    i, j = _find_dbul_block(src)
    if i is None:
        print("ABORT: blok slop dbul tidak ketemu"); return 2
    old_dbul = src[i:j]
    if "MUAT FILE Manual" not in old_dbul:
        print("ABORT: blok dbul tak berisi teks slop yang diharapkan")
        return 2
    texts[app] = src[:i] + P_CLEAN_DBUL + "\n" + src[j:]

    fails = []
    for rel, old, new, want in PAIRS:
        n = texts[rel].count(old)
        if n != want:
            fails.append((rel, old, n, want)); continue
        texts[rel] = texts[rel].replace(old, new)

    src = texts[app]
    for old, new in ((P_SLOP_KAT, P_CLEAN_KAT), (P_SLOP_TITLE, P_CLEAN_TITLE)):
        if src.count(old) != 1:
            fails.append((app, old[:60], src.count(old), 1)); continue
        src = src.replace(old, new)
    texts[app] = src

    if fails:
        print("== MISMATCH (edit DIBATALKAN — tak ada file tertulis) ==")
        for rel, old, n, want in fails:
            print(f"  {rel}: {old[:70]!r} -> ketemu {n}, want {want}")
        return 1

    if apply:
        for rel, txt in texts.items():
            (ROOT / rel).write_text(txt, encoding="utf-8")
        print(f"OK — {len(PAIRS)} pasangan + 3 blok slop diterapkan "
              f"di {len(texts)} file.")
    else:
        print(f"DRY-RUN OK — {len(PAIRS)} pasangan + 3 blok slop cocok "
              f"({len(texts)} file). Jalankan dengan --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
