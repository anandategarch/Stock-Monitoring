# Stock Monitoring — Python Edition

Porting **Power Query M code** untuk monitoring stok resto ke **Python**.
Pipeline ini membaca data export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu menghasilkan file Excel "Mutasi Barang.xlsx" yang **struktur pivot tables + slicers-nya sama persis** dengan template sample.

> Versi asli: Power Query M (1.009 baris, 30 query).
> Versi Python: 10 modul `fn_*` + `queries.py` + `append1.py` + `rincian_po.py` + `excel_output.py`.
> UI: Tkinter 3-tab (Config / Proses / Output).

---

## Cara Pakai (Cepat)

### 1. SETUP (sekali saja)
Klik dua kali **`SETUP.bat`** — akan menginstall dependency:
```
pandas, openpyxl, numpy
```

### 2. MULAI
Klik dua kali **`MULAI.bat`** — akan membuka UI Tkinter:
```
Stock Monitoring - Python Edition
```

### 3. Config (tab pertama)
- Pastikan **RootPath** sesuai lokasi folder data Anda.
- Klik **Simpan Config** untuk menyimpan ke `config.json`.

### 4. Proses (tab kedua)
- Klik **MULAI PROSES**.
- Lihat log real-time. Tunggu sampai muncul "SELESAI".

### 5. Output (tab ketiga)
- Klik **Buka File** untuk membuka Excel hasil, atau
- Klik **Buka Folder** untuk membuka folder output di Explorer.

> Alternatif CLI (tanpa UI):
> ```
> python -m src.main
> ```

---

## Struktur Folder

```
stock-monitoring-python/
├── MULAI.bat                     # Entry point UI (Windows)
├── SETUP.bat                     # Install dependencies (sekali)
├── requirements.txt              # pandas, openpyxl, numpy
├── README.md                     # Dokumen ini
├── config.json                   # Path & sheet name (EDIT di tab Config)
├── template/
│   └── Mutasi Barang - Template.xlsx   # Template Excel (pivot + slicers)
├── output/                       # Output default (dibuat otomatis)
│   └── Mutasi Barang.xlsx
└── src/
    ├── __init__.py
    ├── config.py                 # Loader config.json (mirror record Config di M)
    ├── main.py                   # Pipeline runner / orchestrator
    ├── pipeline/
    │   ├── __init__.py
    │   ├── helpers.py            # fn_combine_folder, text delimiters, type conv
    │   ├── queries.py            # OUT, IN, Full Rekap Mentah SO, individual queries
    │   ├── append1.py            # Pipeline utama → Append1 (long format)
    │   ├── rincian_po.py         # Rincian PO (filter KATEGORI = "DEVIASI")
    │   ├── fn_rekap_mentah.py    # fn #"Rekap Mentah" + "Full Rekap Mentah SO"
    │   ├── fn_2205.py            # fn #22.05 (Rincian Penjualan)
    │   ├── fn_3224.py            # fn #32.24 (Penerimaan Barang)
    │   ├── fn_4215.py            # fn #42.15 (Pemindahan Barang)
    │   ├── fn_4205.py            # fn #42.05 (Pemindahan Barang)
    │   ├── fn_4217.py            # fn #42.17 (Saldo Awal)
    │   ├── fn_pi.py              # fn #"Rincian PI"
    │   ├── fn_konversi_satuan.py # fn #"Konversi Satuan" (Dex)
    │   ├── fn_dbs_kategori.py    # fn #"DBS Kategori"
    │   └── fn_running_stock.py   # fn #"Running Stock" (List.Generate)
    ├── excel/
    │   ├── __init__.py
    │   └── excel_output.py       # Template-based output (replace pivot cache)
    └── ui/
        ├── __init__.py
        └── app.py                # Tkinter UI (3 tab)
```

---

## Config (`config.json`)

File konfigurasi utama. Struktur:

```json
{
  "RootPath": "C:\\KERJA\\1. RESTO\\9.NEW QUERY\\",
  "Folders": {
    "RekapBerjalan":  "1. DEVIASI WEEKLY",
    "RekapLalu":      "1.12 Rekap Mentah Bulan Lalu",
    "Penjualan2205":  "2. 22.05",
    "Kirim4215":      "3.1 42.15 Kirim",
    "Terima4215":     "3. 42.15",
    "RI3224":         "13. 32.24 RI",
    "RI3224Lalu":     "13.2 3224 RI Bulan Lalu",
    "PI":             "26.Rincian PI",
    "SaldoAwal4217":  "6.1 42.17 Saldo Awal",
    "KonversiSatuan": "27.Konversi Satuan Dex",
    "DBSKategori":    "21. DBS Kategori",
    "Pemindahan4205": "4. 42.05",
    "RincianPO":      "25. Rincian PO"
  },
  "Sheets": {
    "RekapMentah":     "REKAP MENTAH",
    "Penjualan2205":   "#22.05. Rincian Penjualan per B",
    "Pemindahan4215":  "#42.15. Pemindahan Barang (KIRI",
    "Penerimaan3224":  "#32.24. Rincian Penerimaan Bara",
    "SaldoAwal4217":   "#42.17. Kuantitas Barang per Gu",
    "FakturPembelian": "#32.42. Rincian Faktur Pembelia",
    "KonversiSatuan":  "Sheet1",
    "DBSKategori":     "Sheet1",
    "Pemindahan4205":  "#42.05. Rincian Pemindahan Bara",
    "PesananPO":       "#32.43. Rincian Pesanan Pembeli"
  },
  "Output": {
    "TemplateFile": "template/Mutasi Barang - Template.xlsx",
    "DefaultOutput": "output/Mutasi Barang.xlsx"
  }
}
```

### Cara ubah RootPath
1. Buka aplikasi (MULAI.bat).
2. Tab **Config** → ubah field **RootPath** (atau klik **Browse...**).
3. Klik **Simpan Config**. Backup otomatis dibuat di `config.json.bak`.

> Folder name & sheet name HARUS sesuai dengan export Accurate Online. Jangan diubah kecuali Accurate mengubah format export.

---

## Pipeline — Penjelasan

Pipeline ada 2 stage utama, lalu di-write ke Excel.

### Stage 1: `build_append1(config)` — Pipeline Utama
Mirror persis query **`Append1`** di M code. Output: DataFrame long format 10 kolom:

| Kolom                  | Sumber                         |
|------------------------|--------------------------------|
| `Nama Barang`          | Dari semua source              |
| `NAMA RESTO`           | Dari semua source              |
| `Tanggal`              | Dari semua source              |
| `JENIS`                | OUT / IN / dll                 |
| `NILAI`                | Kuantitas (positif/negatif)    |
| `Nomor`                | Nomor transaksi                |
| `Nomor PO`             | Nomor PO (jika ada)            |
| `#Tgl/Jam Pembuatan IT`| Timestamp IT                   |
| `KATEGORI`             | Dari DBS Kategori (merge)      |
| `SOURCE KIRIMAN`       | Label source                   |

Alur internal `append1.py`:
1. **Source** — panggil 10 query (masing-masing pakai `fn_*` module).
2. **Information** — gabung + group by `Nama Barang` & `NAMA RESTO`, concat `Nomor`, `Nomor PO`, `#Tgl/Jam` dengan delimiter `", "` (filter null/`"0"`).
3. **Pivot** — pivot `JENIS` jadi kolom, sum `NILAI`.
4. **Running Stock** — implementasi `List.Generate` dari M: track `started` flag, akumulasi saldo per `Nama Barang` × `NAMA RESTO`.
5. **Deviasi** — hitung selisih vs saldo akhir.
6. **Merge KATEGORI** — left join dengan DBS Kategori.
7. **Unpivot** — kembalikan ke format long (10 kolom di atas).

### Stage 2: `build_rincian_po(config)` — Rincian PO
Mirror query **`Rincian PO`**:
- Source: folder `RincianPO` + sheet `PesananPO` (modul 32.43).
- Filter: `DBS_Kategori.KATEGORI = "DEVIASI"`.
- Output: 13 kolom (Nomor #, Tanggal, Cabang PO, Pemasok, Nama Barang, Satuan, Kuantitas, @Harga, Total Harga, Keterangan PO, Status, Tgl/Jam, KATEGORI).

### Stage 3: `generate_output(...)` — Excel Output
Template-based approach (bukan tulis Excel dari nol):
1. Copy `template/Mutasi Barang - Template.xlsx` → output.
2. Unzip ke temp dir.
3. Replace `pivotCacheRecords1.xml` + `pivotCacheDefinition1.xml` (data Append1).
4. Replace `pivotCacheRecords2.xml` + `pivotCacheDefinition2.xml` (data Rincian PO).
5. Modify `pivotTable*.xml`: hapus `<items>` (biar Excel rebuild saat dibuka).
6. Modify `slicerCache*.xml`: hapus `<items>`.
7. Hapus `connections.xml` & query table Power Query (tidak dipakai).
8. Re-zip → output `.xlsx`.

Hasil: **pivot tables + slicers aktif** dan tampil sama persis dengan template sample.

---

## Output

File: `output/Mutasi Barang.xlsx` (default, bisa diubah).

Isi:
- **Sheet dengan PivotTable** dari Append1 (10 kolom long format).
- **Sheet dengan PivotTable** dari Rincian PO (KATEGORI = DEVIASI).
- **Slicers** yang ter-link ke pivot.
- **Styling** (warna, format angka) mengikuti template.

> Saat pertama kali dibuka di Excel, pivot akan refresh otomatis untuk rebuild `<items>`. Klik kanan pivot → **Refresh** jika perlu.

---

## Dependencies

Diinstall otomatis oleh `SETUP.bat`:

| Package    | Versi    | Untuk                                 |
|------------|----------|---------------------------------------|
| `pandas`   | ≥ 2.0.0  | DataFrame, groupby, pivot             |
| `openpyxl` | ≥ 3.1.0  | Baca sheet Excel dari Accurate export |
| `numpy`    | ≥ 1.24.0 | Numeric operations, NaN handling      |

Tidak butuh `selenium` / `playwright` — data sumber adalah file lokal.

---

## Menjalankan tanpa UI (CLI)

```bash
# Pakai config.json default
python -m src.main

# Custom config & output
python -m src.main --config path/to/config.json --output path/to/output.xlsx
```

---

## Troubleshooting

### 1. `python: command not found` / `python is not recognized`
Python belum terinstall. Install dari https://python.org (versi 3.10+). Saat install, **centang "Add Python to PATH"**.

### 2. `ModuleNotFoundError: No module named 'pandas'`
`SETUP.bat` belum dijalankan. Jalankan sekali, atau manual:
```
pip install pandas openpyxl numpy
```

### 3. UI tidak muncul / langsung tutup
Jalankan lewat Command Prompt untuk lihat error:
```
cd C:\path\ke\stock-monitoring-python
python -m src.ui.app
```
Pastikan `SETUP.bat` sudah dijalankan minimal sekali.

### 4. `FileNotFoundError: config.json`
File config hilang. Salin dari backup `config.json.bak`, atau buat ulang (lihat contoh di atas).

### 5. `FileNotFoundError` untuk folder source
Cek di tab **Config**:
- RootPath benar?
- Folder di dalam RootPath ada? (cek nama persis: `1. DEVIASI WEEKLY`, dll.)
- File Excel di tiap folder bisa dibuka?

### 6. Output rusak / tidak bisa dibuka Excel
- Pastikan `template/Mutasi Barang - Template.xlsx` tidak dihapus/dimodifikasi.
- Coba hapus `output/Mutasi Barang.xlsx` lalu jalankan ulang.
- Excel kadang butuh **Refresh** manual pada pivot: klik kanan → Refresh.

### 7. Pipeline lambat
- Dataset besar (>100MB total) wajar 30-60 detik.
- Lihat progress di log UI.
- Jangan klik tombol MULAI berkali-kali sebelum selesai.

### 8. Slicer/Pivot tidak refresh otomatis
Buka file di Excel, klik kanan pivot → **Refresh**. Atau **Data → Refresh All**.

---

## Catatan Pengembangan

- Kode pipeline di-fork dari Power Query M (1.009 baris) — semua 30 query M dipetakan ke Python.
- `fn_running_stock` mengimplementasi `List.Generate` M secara presis (flag `started`, akumulasi saldo).
- Excel output pakai template-based approach (replace pivot cache) supaya pivot tables & slicers tetap utuh dan ter-link.
- UI thread-safe: pipeline dijalankan di worker thread, log dikirim via queue ke main thread.
- Backup `config.json.bak` dibuat otomatis setiap kali Simpan Config.

---

## Lisensi

Internal use — Resto Operations.
