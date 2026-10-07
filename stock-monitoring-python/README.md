# Stock Monitoring — Python Edition

Porting **Power Query M code** untuk monitoring stok resto ke **Python**.
Pipeline membaca data export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu **menampilkan langsung di UI** (tanpa Excel output).

> Versi asli: Power Query M (1.009 baris, 30 query).
> Versi Python: 10 modul `fn_*` + `queries.py` + `append1.py` + `rincian_po.py` + UI Tkinter.
> **v3.0 — Total UI/UX redesign**: design language baru ala aplikasi *Waste* (slate + teal, card-based, dark toolbar, KPI cards, konsol log gelap). Pipeline & semua logika data **tidak berubah**.
> **v3.1 — UX upgrade**: filter Nama Barang menempel di header kolom (ala Excel AutoFilter, di SEMUA tab), tombol ⛶ **Perbesar tabel** (fullscreen), **copy Nomor/Nomor PO** di pop-up detail, **pivot per RESTO** (baris kosong disembunyikan, tanpa kolom Total), dan **animasi loading** di semua proses. Pipeline tetap 100% tidak berubah.
> **v3.2 — Follow Up + tabel besar + perf**: tab baru **☑ Follow Up** (ala aplikasi *Waste*: centang ✓ baris anomali di Deviasi GR/PCS & Laporan → shortlist investigasi, persist `followup.json`, export Excel + impor hasil tindak lanjut), **KPI row di atas tabel DIHAPUS** di semua tab data (tabel jadi lebar & besar; ringkasan pindah ke status footer), dan **aplikasi diperingatkan** (deviasi 16× lebih cepat via vektorisasi numpy; laporan 3.7×; lazy refresh per tab — hanya tab aktif yang dihitung).

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
- **PIVOT PER** (segment di atas tabel):
  - **🏪 Resto** (default): kolom = resto, nilai = total per resto. Hanya baris dengan nilai total > 0 yang tampil (☑ "Sembunyikan baris kosong", ON) — item yang hanya ada di satu resto tetap muncul; **kolom Total sengaja tidak ditampilkan** (hanya dipakai internal untuk filter).
  - **📅 Tanggal**: kolom = tanggal + rentang tanggal (1–31) + metric 6.PEMAKAIAN (COM).
- Filter: RESTO (mode Tanggal), SOURCE KIRIMAN, KATEGORI + **filter Nama Barang via ikon corong di header kolom**.
- Color-coded per metric (1.SO, 2.SALDO AKHIR, 3.DEVIASI, dll).
- Negative values in parentheses, zero shown as '-'.
- Double-click cell → pop-up detail source (baris×resto / baris×tanggal).

### 6. Rincian PO (tab ketujuh)
- Tabel Rincian PO dengan filter Cabang PO & Status.
- Nomor # sebagai parent row (klik ▸ untuk expand).

---

## Fitur Baru v3.2

### ☑ Follow Up (ala aplikasi Waste)
- **Centang kolom ✓** di tabel Deviasi GR / Deviasi PCS / Laporan Deviasi → baris masuk ke tab **☑ Follow Up** (badge jumlah di judul tab).
- Daftar berbentuk **snapshot** (nilai apa adanya saat dicentang) — menetap, tidak ikut filter/Tanggal H.
- **Tersimpan otomatis** (`followup.json`, atomic write + backup file korup) — aman walau aplikasi ditutup.
- Klik ✓ lagi (di tab mana pun, termasuk window ⛶ Perbesar) = keluarkan baris.
- **💾 Export Excel**: snapshot + kolom serah-terima kosong **PIC / KATEGORI MASALAH / TINDAKAN** (diisi petugas, konvensi rekap mentah) — freeze header + autofilter.
- **📥 Impor Hasil TL**: baca kembali file terisi → baris cocok ber-status **Selesai** + PIC tampil (persist `followup_resolved.json`).
- ✕ **Kosongkan**: hapus seluruh daftar (dengan konfirmasi).
- Double-click baris → pop-up detail source data.

### 📐 Tabel lebar & besar (KPI row dihapus)
- Baris kartu KPI di atas tabel (Total |Deviasi|, Anomali CEK, 6 kartu status, dll.) **DIHAPUS** di semua tab data — tabel kini mengisi ruang vertikal penuh.
- Ringkasan yang hilang tetap tersedia di **status footer** bawah tabel (jumlah baris · total deviasi · anomali · distribusi status).
- Filter yang tadinya via klik kartu KPI status → pakai **combo STATUS** di kartu Filter.

### ⚡ Performa (app diperingatkan)
- **Vektorisasi numpy**: Deviasi GR/PCS — `iterrows` per sel → operasi array + `np.select` CEK (**16× lebih cepat**: 1262 ms → 76 ms @ 200k rows); Laporan — `.apply(axis=1)` ganda (yang pertama dead-code) → `np.select` vektor (**3.7×**: 805 ms → 217 ms).
- **Lazy refresh per tab**: setelah pipeline selesai hanya tab aktif yang compute; tab lain menunggu dipilih (`<<NotebookTabChanged>>` → `ensure_refreshed()`) — dulu 5 view berhitung + render bersamaan.
- Cache `pd.to_numeric(Tanggal)` per data; ekstraksi pivot satu `.loc` per item (bukan item×metric); satuan-lookup via `zip` (bukan `iterrows`).
- Hasil komputasi **identik** (CEK & Status Audit diverifikasi identik vs formula lama).

## Fitur Baru v3.1

### ⧩ Filter Nama Barang menempel di header (semua tab)
Klik header kolom **Nama Barang** (ikon corong) → popup ala **Excel AutoFilter**:
- 🔍 pencarian nilai (menyaring daftar), daftar checkbox nilai unik, "Pilih semua"
- sort **A→Z / Z→A** langsung dari popup
- corong header berubah **teal** saat filter aktif; live-apply tiap toggle
- Search box lama & dropdown NAMA BARANG di kartu filter **dihapus** (digantikan fitur ini, berlaku di semua tab + pop-up detail)

### ⛶ Perbesar tabel (semua tab + pop-up)
- Tombol **⛶ Perbesar** di kartu tabel tiap tab (dan di header pop-up detail) membuka window besar berisi clone tabel lengkap.
- Sort, double-click detail, dan klik-kanan copy tetap berfungsi di window perbesar. **Esc** untuk menutup.

### 📋 Copy Nomor / Nomor PO (pop-up detail)
- **Klik kanan baris** → menu: Copy Nomor, Copy Nomor PO, Copy seluruh baris (tab-separated), Copy SEMUA Nomor / Nomor PO (unik), dan Perbesar.
- **Double-click cell** kolom Nomor / Nomor PO → langsung copy nilai cell.
- **Ctrl+C** → copy Nomor baris terpilih.
- Tombol cepat **📋 Semua Nomor / Semua Nomor PO** di footer pop-up.
- Status footer memberi konfirmasi "📋 … TERSALIN" setiap kali copy.

### ⏳ Loading animation di semua proses
- Chip loading melayang (spinner + teks) di tengah tabel saat: hitung pivot/deviasi/audit/rincian, render tabel besar (batched), buka pop-up detail, clone tabel perbesar, dan **Export Excel** (async — UI tidak membeku).
- Pipeline: progressbar + spinner status di tab Proses (dipertahankan).
- Compute berat berjalan di thread terpisah; render bertahap per-batch supaya UI tetap responsif.

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

Fitur UX per tab:
- **Proses** — 4 KPI live (status pipeline, waktu berjalan, rows Append1, rows Rincian PO) + progress bar + konsol log gelap
- **Deviasi GR/PCS** — kolom ✓ follow-up + legenda warna CEK; ringkasan (baris · total |Deviasi| · anomali CEK) di status footer *(v3.2: KPI row di atas tabel dihapus supaya tabel besar)*
- **Laporan Deviasi** — kolom ✓ follow-up + filter status via combo STATUS; distribusi status di status footer *(v3.2: 6 kartu KPI dihapus)*
- **Follow Up** *(v3.2)* — tabel snapshot baris tercentang + Export Excel / Impor Hasil TL / Kosongkan
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
├── test_ui_redesign.py         # test UI v3.2 (99 check — lazy/follow-up/KPI hapus + semua fitur v3.1)
├── bench_views.py              # benchmark compute per view (dev — ukur perf vektorisasi)
├── screenshot_ui.py            # dev tool: screenshot semua tab (butuh Xvfb)
└── src/
    ├── config.py               # loader config.json
    ├── main.py                 # run_pipeline() → (append1_df, rincian_po_df)
    ├── pipeline/               # porting fn_* dari M code (TIDAK berubah di v3)
    └── ui/                     # ← REDESIGN v3.0 (v3.2: +followup)
        ├── app.py              # shell: toolbar + 8 tab + status bar + kontrol pipeline + lazy tab refresh
        ├── theme.py            # design system (palet + font + ttk style)
        ├── widgets.py          # Card, tombol, tooltip, empty state, overlay, header filter, dll
        ├── followup.py         # (v3.2) FollowUpStore: fingerprint, snapshot, persist, export/import xlsx
        ├── followup_view.py    # (v3.2) tab ☑ Follow Up
        ├── pivot_view.py       # tab Pivot Table (per resto default)
        ├── deviasi_view.py     # tab Deviasi GR & PCS (vektorisasi numpy + kolom ✓)
        ├── laporan_deviasi_view.py  # tab Laporan Deviasi (np.select + kolom ✓)
        ├── rincian_po_view.py  # tab Rincian PO
        └── details_popup.py    # popup detail source rows (copy Nomor/PO)
```

---

## Testing

```
python test_mock.py          # pipeline end-to-end dgn mock data Accurate
python test_ui_redesign.py   # UI v3.2: 99 check (jalankan di bawah Xvfb di Linux)
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
