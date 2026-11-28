# Stock Monitoring — Python Edition

Aplikasi desktop untuk monitoring stok resto berbasis **Python + Tkinter**. Porting pipeline Power Query M (1.009 baris, 30 query) ke Python — membaca export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu menampilkan langsung di UI tanpa output Excel perantara.

> **Versi terkini: v3.17.3** — riwayat lengkap: [CHANGELOG.md](CHANGELOG.md)

## Fitur Utama

- **Pipeline end-to-end** dari 14 sumber Excel (Rekap Mentah, 22.05, 42.15, 32.24, 42.05, 9901, 42.17 Saldo Awal & Sistem, 41.09 Harga, 32.43 Rincian PO, DBS Kategori) → 892k+ baris append1 terstruktur
- **9 tab analisa** dengan tabel interaktif (sort, filter ⧩, multi-select, copy Excel-style, auto-fit, layar penuh)
- **Analisa deviasi otomatis** — kolom CEK dengan 12 label anomali (Promix 04, RI Balancing, Kosong (AKTIF), Non Aktif (Masih Stok), Beda Tanggal, Hitung Manual, Hilang dari Pencatatan, Turun Drastis + varian SO Tidak Diinput, Naik Drastis, ACR to BOM, BOM 0) + segmen COM Tinggi/Rendah per satuan, Beda dari Resto Lain, Potensi PO belum dibuat, analisa lalu-kini berbasis Qty
- **Saldo sistem minus** — rekapan pasangan Eksternal/Campuran dengan saldo < 0 di rentang 1..H, dengan keterangan mulai minus dari tanggal berapa
- **% Growth Deviasi (pivot)** — baris `10.% Growth Deviasi` di tab Pivot (mode Tanggal): persen kenaikan/penurunan deviasi per tanggal dari baris `3.Deviasi` — **absolut penuh** `(|Dev(t)|−|Dev(t−1)|) ÷ |Dev(t−1)| × 100` (arah dari magnitudo) + **heatmap per-sel**: merah = deviasi naik / hijau = turun, intensitas <5%/<25%/<100%/≥100% (v3.17.0; rumus & heatmap v3.17.1)
- **File deviasi bulan lalu** — dimuat manual via tombol 📂 (parse async, gak bekui UI), pattern `{12+month}.{BULAN} {TAHUN}.xlsx`
- **Log persisten + crash trace** — `logs/app.log` (rotasi otomatis) merekam seluruh log run pipeline & exception runtime; `crash.log` append ber-timestamp per kejadian (v3.15)
- **Tooltip hover** untuk cell panjang (CEK narasi, Keterangan, Rekomendasi) — muncul dekat cursor
- **Persistensi** — filter, ukuran window, zoom, threshold ACR/COM tersimpan lintas sesi (settings.json)
- **DPI-aware** — tajam di layar scaling 125%/150%; zoom Ctrl+Scroll 50%–200%

## Persyaratan

- **Windows** + **Python 3.12** (dengan Tcl/Tk)
- Jalankan `SETUP.bat` sekali untuk install dependency:
  ```
  pandas>=2,<3 · openpyxl · numpy · python-calamine · pyxlsb
  ```
  (pandas dipin `<3` — semantik CoW pandas 3 belum terverifikasi)

## Cara Pakai

1. **SETUP** (sekali) — klik dua kali `SETUP.bat`
2. **MULAI** — klik dua kali `MULAI.bat` (UI terbuka tanpa jendela console; log ada di tab 🚀 Proses)
3. **Config** (tab ⚙️ Config) — set **RootPath** ke folder data bulanan (mis. `C:\KERJA\1. RESTO\9.NEW QUERY\`). Sub-folder & nama sheet bisa diubah via key `Folders` / `Sheets` di `config.json`
4. **Proses** (tab 🚀 Proses) — klik **MULAI PROSES**. Pre-flight memeriksa semua folder data; log real-time tampil di konsol gelap. Tombol **Refresh Sumber** membaca ulang file terpilih saja
5. **TANGGAL H** — input H + tombol Apply H hanya ada di tab **Deviasi GR**; semua tab lain memakai H yang sama (chip read-only, refresh otomatis)

### File Deviasi Bulan Lalu (manual)

1. Tab ⚙️ Config → kartu **DEV BULANAN** → isi folder + jumlah bulan mundur
2. Klik 💾 Simpan (optional — tombol 📂 baca form saat itu)
3. Run pipeline (Proses) → selesai tanpa auto-load
4. Klik tombol 📂 **Muat Sekarang** saat butuh file deviasi bulan lalu → parse async → kolom **Dev. Bulan Lalu** terisi di tab Deviasi GR/PCS + popup Nominal Deviasi
5. Pattern nama file: `{12+month}.{BULAN} {TAHUN}.xlsx` — mis. `13.JANUARI 2026.xlsx`, `22.OKTOBER 2026.xlsx`, `20.AGUSTUS 2026.xlsx` (Agustus backward-compat dgn pattern lama "20.")

## Tab Data

| Tab | Isi |
|---|---|
| ⚙️ Config | RootPath, Folders, Sheets, KategoriBarang4217, kartu DEV BULANAN, ambang COM, DPI |
| 🚀 Proses | Kontrol pipeline (MULAI/Stop/Refresh Sumber), KPI real-time, log konsol gelap, tombol Export Excel |
| 🧮 Pivot Table | Matrix per Resto/Tanggal (rentang default 25•–31• bulan lalu s/d 31 berjalan; kategori default "Deviasi") + baris **10.% Growth Deviasi** dari 3.Deviasi per tanggal (mode Tanggal saja) |
| 📦 Deviasi GR / 🧩 Deviasi PCS | Analisa deviasi per barang×resto — kolom **CEK** (12 label anomali: Turun Drastis dibedakan vs SO Tidak Diinput, Kosong (AKTIF) vs Non Aktif (Masih Stok), Beda Tanggal, Hitung Manual, Hilang dari Pencatatan, Naik Drastis, ACR to BOM, BOM 0, Promix 04, RI Balancing + segmen COM Tinggi/Rendah per satuan, Beda dari Resto Lain, Potensi PO, Peningkatan/Penurunan Qty ±p%), minus merah per-cell, popup detail per tanggal (footer: median d & gap), kolom Nominal (Harga 41.09 × Qty Deviasi), kolom **Dev. Bulan Lalu**, tooltip hover cell CEK |
| 📤 Rekap Selisih IN | IN (Accurate) vs Barang Masuk + kolom SO + Hasil Audit + PO Menunggu; mode hitung Bulan Ini / Lalu+Ini; mode 📈 Analisa = tabel selisih (Resto·Tgl·Barang) urut \|selisih\|↓; export per resto |
| 💰 Nominal Deviasi | Σ Nominal Deviasi per resto + perbandingan bulan lalu + baris TOTAL. Sub-tab: **Per Resto** · **Tanpa Harga** (global) · **Saldo Sistem Minus** (pasangan Eksternal/Campuran minus) · *(v3.17.0 — sub-tab **Analisa Kronis** dihapus)* |
| ☑ Follow Up | Shortlist baris tercentang (persist `followup.json`) + export |
| 🛒 Rincian PO | Daftar PO + item; keterangan & status tampil sebagai anotasi `↳` di kolom Pemasok/Nomor # |

## Interaksi Tabel (semua tab)

- **Klik judul kolom** = sort · **ikon ⧩** = filter (daftar nilai = hanya data yang ada)
- **Multi-select**: Ctrl+Klik / Shift+Klik / Ctrl+A · **Ctrl+C** salin (tab-separated → paste ke Excel)
- **Seleksi sel ala Excel**: klik → jangkar, drag/Shift+klik → blok; Ctrl+C menyalin sel ter-highlight
- **Klik-kanan judul** = sembunyikan/auto-fit kolom; tombol Layar Penuh · Perbesar Tabel · Kolom · Auto-Fit
- **Klik ✓** = masuk Follow Up · **double-click baris** = popup detail
- **Hover cell panjang** (CEK, Keterangan, Rekomendasi) = tooltip muncul 0,5 detik dekat cursor

## Struktur Kode

```
src/
├── main.py, config.py         # entry CLI + config loader
├── pipeline/                  # porting Power Query (fn_2205 … fn_9901)
│   ├── queries.py             # orchestrator utama
│   ├── append1.py             # pipeline utama (892k baris)
│   ├── rincian_po.py          # Rincian PO 32.43
│   ├── konversi_satuan.py     # peta rasio satuan
│   ├── fn_audit.py            # selisih IN, status audit, COM, detect_data_period
│   ├── fn_4217.py             # Saldo Awal & Sistem 42.17
│   ├── fn_rekap_mentah.py     # Rekap Mentah SO
│   └── fn_2205 … fn_9901     # readers per sumber Excel
└── ui/                        # shell + view per tab (Tkinter)
    ├── app.py                 # StockMonitorApp (7.500+ baris)
    ├── widgets.py             # komponen reusable (Treeview, HeaderFilter, dll)
    ├── theme.py               # design system (colors, fonts)
    ├── deviasi_view.py        # tab 📦/🧩 (5.200+ baris)
    ├── nominal_resto_view.py  # tab 💰 + 3 sub-tab (2.700+ baris)
    ├── saldo_minus_view.py    # sub-tab Saldo Sistem Minus
    ├── cell_tooltip.py        # reusable hover tooltip
    ├── diagnostics.py         # log file rotasi + excepthook global + crash.log (v3.15)
    ├── deviasi_file.py        # parse file deviasi bulan lalu
    ├── nominal_common.py      # hitung saldo minus, nominal lalu
    ├── po_keterangan.py       # peta PO 3243
    ├── details_popup.py       # popup drill-down
    ├── deviasi_popup.py       # popup ringkas per tanggal
    ├── in_selisih_view.py     # tab 📤
    ├── pivot_view.py          # tab 🧮
    ├── rincian_po_view.py     # tab 🛒
    ├── followup_view.py       # tab ☑
    ├── followup.py            # FollowUpStore (persist JSON)
    ├── refresh_sources.py     # dialog Refresh Sumber
    ├── export_sheets.py       # Export Excel multi-sheet
    ├── com_analisa.py         # segmen CEK COM
    ├── doc_codes.py           # kode dokumen
    └── __main__.py            # entry `python -m src.ui`
```

## Testing & CI

```bash
bash run_tests.sh          # test_ui_redesign.py + test_mock.py (auto-Xvfb)
```

GitHub Actions (`.github/workflows/release-windows.yml`) menjalankan gerbang tes pada tiap push/PR: ruff (baseline ≤ 201) · py_compile · validasi config.json · suite UI penuh · pipeline mock · smoke 2 entry. Rilis EXE (tag `v*`) hanya dibuat bila gerbang hijau.

Benchmark performa (P1, v3.17.2) — `benchmarks/` (dataset sintetis, tanpa data bisnis):

```bash
python benchmarks/synth_data.py --out /tmp/bench --restos 16 --barang 20   # buat dataset
python benchmarks/benchmark_pipeline.py --data-dir /tmp/bench --config /tmp/bench/config.json --tag 100k
python benchmarks/benchmark_views.py --restos 18 --barang 20 --tag 100k      # butuh Xvfb
python benchmarks/benchmark_report.py                                        # rapikan hasil → markdown
```

Mengukur: pipeline per-tahap (cold/warm/refresh cache), peak RAM (psutil), pivot/deviasi/nominal compute + render + sort + filter + export. `psutil` hanya tooling benchmark — bukan dependency runtime.

## Build EXE (Windows)

```bash
python build_exe.py         # PyInstaller → dist/
```

## Konfigurasi

`config.json` (auto-generated saat simpan dari tab ⚙️ Config):

| Key | Deskripsi |
|---|---|
| `RootPath` | Folder data bulanan (export Accurate Online) |
| `Folders` | Sub-folder per sumber (RekapBerjalan, Penjualan2205, dll) |
| `Sheets` | Nama sheet Excel per sumber |
| `KategoriBarang4217` | Whitelist kategori saldo 42.17 (8 kategori default) |
| `DeviasiBulananFolder` | Folder file deviasi bulan lalu |
| `DeviasiBulananJumlah` | Jumlah bulan mundur (1–12) |
| `DpiAware` | Aktifkan DPI-awareness (default `true`) |
| `acr_threshold` | Ambang ACR to BOM (%) |
| `com_ambang_pct` | Ambang COM Tinggi/Rendah (median ± %) |
| `saldo_sistem_mode` | Mode saldo sistem (`4217` / `pivot`) |
| `KategoriManual` | Mapping kategori manual per barang |

`settings.json` (auto-generated saat close app):

| Key | Deskripsi |
|---|---|
| `window_state` | Ukuran, posisi, maximised, zoom UI |
| `filter_state` | Kombinasi filter per tab (pulih lintas sesi) |
| `acr_threshold`, `com_ambang_pct`, `saldo_sistem_mode` | State shared lintas tab |

## Versi & Changelog

Versi kanonik: `APP_VERSION` di `src/ui/app.py`. Riwayat lengkap per-commit: `git log --oneline` atau [CHANGELOG.md](CHANGELOG.md).

## Lisensi

Internal — porting pipeline Power Query M untuk monitoring stok resto.
