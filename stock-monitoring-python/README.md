# Stock Monitoring — Python Edition

Porting **Power Query M** (1.009 baris, 30 query) untuk monitoring stok resto ke Python.
Pipeline membaca export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu menampilkan langsung di UI Tkinter — tanpa output Excel.

> **Versi terkini: v3.11.30** — riwayat: [CHANGELOG.md](CHANGELOG.md)

## Persyaratan

- Windows + Python 3.12 (dengan Tcl/Tk) — jalankan `SETUP.bat` untuk install dependency:
  `pandas>=2,<3 · openpyxl · numpy · python-calamine · pyxlsb`
  (pandas sengaja dipin `<3` — semantik CoW pandas 3 belum terverifikasi)

## Cara Pakai

1. **SETUP** (sekali saja) — klik dua kali `SETUP.bat`.
2. **MULAI** — klik dua kali `MULAI.bat` (UI terbuka tanpa jendela console; log proses ada di tab Proses dalam aplikasi).
3. **Config** (tab Config) — set **RootPath** ke folder data bulanan Anda (mis. `C:\KERJA\1. RESTO\9.NEW QUERY\`). Sub-folder & nama sheet bisa diubah via key `Folders` / `Sheets` di `config.json`.
4. **Proses** (tab Proses) — klik **MULAI PROSES**. Pre-flight memeriksa semua folder data; log real-time tampil di konsol gelap. Tombol **Refresh Sumber** membaca ulang file terpilih saja.
5. **TANGGAL H** — input H + tombol *Apply H* hanya ada di tab **Deviasi GR**; semua tab lain memakai H yang sama (chip read-only, refresh otomatis).

### Tampilan HD & Zoom

- **DpiAware** (`config.json`, default `true`) — tajam di layar scaling 125%/150%.
- Tahan **Ctrl + Scroll** di mana saja = zoom UI 50%–200%.

## Tab Data

| Tab | Isi |
|---|---|
| 🧮 Pivot Table | Matrix per Resto/Tanggal (rentang default 25•–31• bulan lalu s/d 31 berjalan; kategori default "Deviasi") |
| 📦 Deviasi GR / 🧩 Deviasi PCS | Analisa deviasi per barang×resto — kolom **CEK** (analisa otomatis: Rank kelompok *hanya untuk grup ber-deviasi* & "Beda dari Resto Lain"), minus merah per-cell, popup detail per tanggal, kolom Nominal (Harga 41.09 × Qty Deviasi) |
| 📤 Rekap Selisih IN | IN (Accurate) vs Barang Masuk + kolom SO + Hasil Audit + PO Menunggu; mode hitung Bulan Ini / Lalu+Ini; export per resto |
| 📋 Laporan Deviasi | 3 mode — Komparasi File Deviasi · Anomali COM (H) · Nominal (H) |
| 💰 Nominal Deviasi | Σ Nominal Deviasi per resto + perbandingan bulan lalu + baris TOTAL |
| 🛒 Rincian PO | Daftar PO + item; keterangan & status tampil sebagai anotasi `↳` di kolom Pemasok/Nomor # |
| ⚖ Komparasi | Multi-file deviasi + analisa Top & Flip |
| ☑ Follow Up | Shortlist baris tercentang (persist `followup.json`) + export |

## Interaksi Tabel (semua tab)

- Klik judul kolom = sort · ikon ▼ = filter (daftar nilai = hanya data yang ada)
- **Multi-select**: Ctrl+Klik / Shift+Klik / Ctrl+A · **Ctrl+C** salin (tab-separated → paste ke Excel)
- Seleksi sel ala Excel: klik → jangkar, drag/Shift+klik → blok; Ctrl+C menyalin sel ter-highlight
- Klik-kanan judul = sembunyikan/auto-fit kolom; tombol Layar Penuh · Perbesar Tabel · Kolom · Auto-Fit
- Klik ✓ = masuk Follow Up · double-click baris = popup detail

## Struktur Kode

```
src/
├── main.py, config.py      # entry CLI + config loader
├── pipeline/               # porting Power Query (fn_2205 … fn_9901)
│   ├── queries.py          # orchestrator utama
│   ├── append1.py, rincian_po.py, konversi_satuan.py
│   └── fn_audit.py         # selisih IN, status audit, COM
└── ui/                     # shell + view per tab (Tkinter)
    ├── app.py, widgets.py, theme.py
    └── *_view.py, *_popup.py, export_sheets.py
```

## Testing & CI

```bash
bash run_tests.sh          # test_ui_redesign.py + test_mock.py (auto-Xvfb)
```

GitHub Actions (`.github/workflows/release-windows.yml`) menjalankan gerbang tes pada tiap push/PR: ruff (baseline ≤ 201) · py_compile · validasi config.json · suite UI penuh · pipeline mock · smoke 2 entry. Rilis EXE (tag `v*`) hanya dibuat bila gerbang hijau.

## Build EXE (Windows)

```bash
python build_exe.py         # PyInstaller → dist/
```
