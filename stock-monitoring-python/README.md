# Stock Monitoring — Python Edition

Porting **Power Query M code** untuk monitoring stok resto ke **Python**.
Pipeline membaca data export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu **menampilkan langsung di UI** (tanpa Excel output).

> Versi asli: Power Query M (1.009 baris, 30 query).
> Versi Python: 10 modul `fn_*` + `queries.py` + `append1.py` + `rincian_po.py` + UI Tkinter.
> UI: Tkinter 4-tab (Config / Proses / Pivot Table / Rincian PO).

---

## Cara Pakai (Cepat)

### 1. SETUP (sekali saja)
Klik dua kali **`SETUP.bat`** — akan menginstall dependency:
```
pandas, openpyxl, numpy, python-calamine
```

### 2. MULAI
Klik dua kali **`MULAI.bat`** — akan membuka UI Tkinter:
```
Stock Monitoring - Python Edition
```

### 3. Config (tab pertama)
- Pastikan **RootPath** sesuai lokasi folder data Anda.
- Centang **LightMode** untuk pipeline ringan (default: ON).
- Klik **Simpan Config** untuk menyimpan ke `config.json`.

### 4. Proses (tab kedua)
- Klik **MULAI PROSES**.
- Lihat log real-time. Tunggu sampai muncul "SELESAI".

### 5. Pivot Table (tab ketiga)
- Pivot matrix ditampilkan langsung di UI (rows: Nama Barang × JENIS, cols: Tanggal).
- Filter: NAMA RESTO, SOURCE KIRIMAN, KATEGORI (dropdown).
- Color-coded per metric (1.SO, 2.SALDO AKHIR, 3.DEVIASI, dll).
- Negative values in parentheses, zero shown as '-'.

### 6. Rincian PO (tab keempat)
- Tabel Rincian PO dengan search + sort.
- Klik header kolom untuk sort.

---

## Struktur Folder

```
stock-monitoring-python/
├── MULAI.bat                     # Entry point UI (Windows)
├── SETUP.bat                     # Install dependencies (sekali)
├── requirements.txt              # pandas, openpyxl, numpy, python-calamine
├── README.md                     # Dokumen ini
├── config.json                   # Path & sheet name + LightMode (EDIT di tab Config)
└── src/
    ├── __init__.py
    ├── config.py                 # Loader config.json
    ├── main.py                   # Pipeline runner (return DataFrames)
    ├── pipeline/
    │   ├── __init__.py
    │   ├── helpers.py            # fn_combine_folder + calamine engine + vectorized text
    │   ├── fn_rekap_mentah.py    # SO + BARANG MASUK (NAMA RESTO dari file name)
    │   ├── fn_2205.py            # Penjualan (OUT)
    │   ├── fn_3224.py            # Penerimaan (IN)
    │   ├── fn_4215.py            # Pemindahan kirim (OUT)
    │   ├── fn_4205.py            # Pemindahan barang (IN)
    │   ├── fn_4217.py            # Saldo awal
    │   ├── fn_pi.py              # Faktur pembelian (IN + konversi satuan)
    │   ├── fn_konversi_satuan.py # Master konversi
    │   ├── fn_dbs_kategori.py    # Master kategori
    │   ├── fn_running_stock.py   # Algoritma running balance (vectorized cumsum)
    │   ├── queries.py            # OUT, IN, Full Rekap SO (LightMode: skip bulan lalu)
    │   ├── append1.py            # Pipeline utama (LightMode: pre-filter DEVIASI)
    │   └── rincian_po.py         # Query Rincian PO
    └── ui/
        ├── __init__.py
        ├── app.py                # Tkinter 4-tab UI
        ├── pivot_view.py         # Excel-like pivot table widget
        └── rincian_po_view.py    # Rincian PO table widget
```

---

## LightMode (config.json)

```json
{
  "LightMode": true,
  "RootPath": "C:\\KERJA\\1. RESTO\\9.NEW QUERY\\",
  ...
}
```

**LightMode=true (default, ringan):**
- Skip bulan lalu (RekapLalu + 3224_Bulan Lalu) — hemat ~40% source
- Skip InfoColumns (Nomor, Nomor PO, #Tgl/Jam) — hemat grouping time
- Pre-filter KATEGORI=DEVIASI — hemat ~60% barang
- Hasil: ~50-80k rows (vs 1.2M Full mode)

**LightMode=false (penuh):**
- Semua data, semua kolom, semua barang
- Lebih lengkap tapi lebih lambat

---

## Performance

| Metric | LightMode | Full Mode |
|---|---|---|
| Source data | ~80-120k rows | ~429k rows |
| Output data | ~50-80k rows | ~1.2M rows |
| Pipeline time | ~10-20s | ~60-120s |
| Pivot render | ~0.15s | ~0.5s |
| Filter change | ~0.12s | ~0.3s |
| Memory | ~100-200 MB | ~500 MB |

Benchmark (100 items × 5 restos × 31 days × 8 metrics = 124k rows):
- Load + render: 0.15s
- Filter change: 0.12s
- No lag

---

## Dependencies

- **pandas** — DataFrame operations
- **openpyxl** — Excel reader (fallback)
- **numpy** — numerical operations
- **python-calamine** — Rust-based Excel reader (10-20x faster than openpyxl)

Install: `SETUP.bat` atau `pip install -r requirements.txt`

---

## Troubleshooting

**Q: Pipeline lambat**
A: Pastikan LightMode=true di config.json. Pastikan python-calamine terinstall (cekc via `pip show python-calamine`).

**Q: Pivot table kosong**
A: Jalankan pipeline di tab Proses dulu. Pastikan data source ada di RootPath.

**Q: Filter tidak berfungsi**
A: Klik dropdown, pilih nilai, pivot auto-refresh.

**Q: Error "No module named 'src'"**
A: Jalankan via `MULAI.bat` atau `python -m src.ui.app` dari root folder.
