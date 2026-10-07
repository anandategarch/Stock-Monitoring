# Stock Monitoring — Python Edition

Porting **Power Query M code** untuk monitoring stok resto ke **Python**.
Pipeline membaca data export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu **menampilkan langsung di UI** (tanpa Excel output).

> Versi asli: Power Query M (1.009 baris, 30 query).
> Versi Python: 10 modul `fn_*` + `queries.py` + `append1.py` + `rincian_po.py` + UI Tkinter.
> **v3.0 — Total UI/UX redesign**: design language baru ala aplikasi *Waste* (slate + teal, card-based, dark toolbar, KPI cards, konsol log gelap). Pipeline & semua logika data **tidak berubah**.

---

## Cara Pakai (Cepat)

### 1. SETUP (sekali saja)
Klik dua kali **`SETUP.bat`** — akan menginstall dependency:
```
pandas, openpyxl, numpy, python-calamine
```

### 2. MULAI
Klik dua kali **`MULAI.bat`** — akan membuka UI:
```
Stock Monitoring — Python Edition
```

### 3. Config (tab pertama)
- Pastikan **RootPath** sesuai lokasi folder data Anda.
- Centang **LightMode** untuk pipeline ringan (default: ON).
- Klik **Simpan Config** untuk menyimpan ke `config.json`.

### 4. Proses (tab kedua)
- Klik **MULAI PROSES**.
- Lihat log real-time di konsol gelap + KPI (status, waktu, rows).
- Tunggu sampai status bar menunjukkan **SELESAI**.

### 5. Pivot Table (tab ketiga)
- Pivot matrix ditampilkan langsung di UI (rows: Nama Barang × JENIS, cols: Tanggal).
- Filter: NAMA RESTO, NAMA BARANG, SOURCE KIRIMAN, KATEGORI + pencarian substring.
- Color-coded per metric (1.SO, 2.SALDO AKHIR, 3.DEVIASI, dll).
- Negative values in parentheses, zero shown as '-'.

### 6. Rincian PO (tab ketujuh)
- Tabel Rincian PO dengan filter Cabang PO & Status.
- Nomor # sebagai parent row (klik ▸ untuk expand).

---

## UI v3.0 — Design System

Shell aplikasi:
- **Toolbar gelap** (slate-900) — judul aplikasi, badge versi, aksi cepat `💾 Export Excel` & `❓ Bantuan`
- **7 tab ber-ikon**: ⚙️ Config · 🚀 Proses · 📊 Pivot Table · 📦 Deviasi GR · 🧩 Deviasi PCS · 📋 Laporan Deviasi · 🛒 Rincian PO
- **Status bar** global — indikator status pipeline (● SIAP / MENJALANKAN / SELESAI / ERROR) + ringkasan rows
- **Empty state** — setiap tab data menampilkan placeholder + tombol CTA "🚀 Jalankan Pipeline" saat belum ada data (auto berganti menjadi tabel saat data termuat)

Komponen inti (`src/ui/theme.py` + `src/ui/widgets.py`):
| Komponen | Fungsi |
|---|---|
| `Card` | kartu putih + border slate, judul & subtitle opsional |
| `KpiCard` / `KpiRow` | kartu metrik (label kecil, angka besar, aksen warna kiri) |
| `AccentButton` | tombol teal solid (aksi utama) — MULAI PROSES, Simpan Config |
| `DangerButton` | tombol putih teks merah — Stop |
| `EmptyState` | placeholder data kosong + CTA |
| `make_log_console` | konsol log gelap ala terminal (#0b1220 + monospace) |
| `ToolTip` | tooltip hover untuk kontrol penting |
| `StatusDot` | titik warna status di status bar |

Palet: `#f1f5f9` (bg) · `#ffffff` (kartu) · `#0f172a` (toolbar/teks judul) · `#0f766e` (aksen teal) · status: merah/oranye/amber/hijau. Font otomatis resolve: Segoe UI (Windows) → Noto Sans → DejaVu Sans.

Fitur UX baru per tab:
- **Proses** — 4 KPI live (status pipeline, waktu berjalan, rows Append1, rows Rincian PO) + progress bar + konsol log gelap
- **Deviasi GR/PCS** — KPI baris / total |Deviasi| / jumlah anomali CEK + legenda warna CEK
- **Laporan Deviasi** — **6 kartu Status Audit yang bisa diklik untuk memfilter** (klik lagi untuk melepas)
- **Semua tabel** — zebra rows, sort kolom (klik header), double-click baris → popup detail source data (header gelap, centered modal, Esc untuk tutup)
- Popup & jendela Bantuan otomatis **ter-center** di parent

---

## Struktur Folder

```
stock-monitoring-python/
├── MULAI.bat / SETUP.bat       # entry point Windows
├── config.json                 # RootPath + LightMode + Folders + Sheets
├── requirements.txt
├── test_mock.py                # test pipeline end-to-end (mock Accurate export)
├── test_large_scale.py         # benchmark 855K records (memory < 2GB)
├── test_ui_redesign.py         # test UI v3 (28 check — shell/KPI/filter/empty state)
├── screenshot_ui.py            # dev tool: screenshot semua tab (butuh Xvfb)
└── src/
    ├── config.py               # loader config.json
    ├── main.py                 # run_pipeline() → (append1_df, rincian_po_df)
    ├── pipeline/               # porting fn_* dari M code (TIDAK berubah di v3)
    └── ui/                     # ← REDESIGN v3.0
        ├── app.py              # shell: toolbar + tab + status bar + kontrol pipeline
        ├── theme.py            # design system (palet + font + ttk style)
        ├── widgets.py          # Card, KpiCard, tombol, tooltip, empty state, dll
        ├── pivot_view.py       # tab Pivot Table
        ├── deviasi_view.py     # tab Deviasi GR & PCS (dipakai 2×)
        ├── laporan_deviasi_view.py  # tab Laporan Deviasi (6-way Status Audit)
        ├── rincian_po_view.py  # tab Rincian PO
        └── details_popup.py    # popup detail source rows
```

---

## Testing

```
python test_mock.py          # pipeline end-to-end dgn mock data Accurate
python test_ui_redesign.py   # UI v3: 28 check (jalankan di bawah Xvfb di Linux)
python test_large_scale.py   # benchmark 855K rows
```

> UI test di Linux/headless: `xvfb-run` atau `Xvfb :99` + `DISPLAY=:99 python test_ui_redesign.py`.
> Di Windows langsung `python test_ui_redesign.py` (perlu display).

---

## Changelog

### v3.0.0 — Total UI/UX Redesign
- Design system baru (`theme.py` + `widgets.py`): slate/teal ala aplikasi Waste, card-based, dark toolbar, status bar global.
- Empty state + CTA di semua tab data; KPI cards di Proses/Deviasi/Laporan/Rincian.
- 6 kartu Status Audit klik-untuk-filter di tab Laporan.
- Konsol log gelap anti-freeze (batch + truncation tetap dari v2.1.1).
- Popup detail & Bantuan: header gelap, centered modal, Esc untuk tutup.
- Tooltip hover untuk kontrol penting; legenda warna CEK & metric.
- **Pipeline, logika pivot/deviasi/audit/CEK, dan semua perilaku data 100% dipertahankan** (hanya lapisan UI yang diganti).
- Fix pre-existing: `test_mock.py` kini konsisten dengan pipeline pasca-refactor hapus PI/Konversi + sumber IN 9901 (mock 9901 + folder `Data9901` ditambahkan).

### v2.1.1 — freeze fix + SettingWithCopyWarning fix
### v2.1.0 — LAPORAN DEVIASI tab + deep-audit fixes
