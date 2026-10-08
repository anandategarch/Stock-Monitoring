# Stock Monitoring — Python Edition

Porting **Power Query M code** untuk monitoring stok resto ke **Python**.
Pipeline membaca data export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu **menampilkan langsung di UI** (tanpa Excel output).

> Versi asli: Power Query M (1.009 baris, 30 query).
> Versi Python: 10 modul `fn_*` + `queries.py` + `append1.py` + `rincian_po.py` + UI Tkinter.
> **v3.0 — Total UI/UX redesign**: design language baru ala aplikasi *Waste* (slate + teal, card-based, dark toolbar, KPI cards, konsol log gelap). Pipeline & semua logika data **tidak berubah**.
> **v3.1 — UX upgrade**: filter Nama Barang menempel di header kolom (ala Excel AutoFilter, di SEMUA tab), tombol ⛶ **Perbesar tabel** (fullscreen), **copy Nomor/Nomor PO** di pop-up detail, **pivot per RESTO** (baris kosong disembunyikan, tanpa kolom Total), dan **animasi loading** di semua proses. Pipeline tetap 100% tidak berubah.
> **v3.2 — Follow Up + tabel besar + perf**: tab baru **☑ Follow Up** (ala aplikasi *Waste*: centang ✓ baris anomali di Deviasi GR/PCS & Laporan → shortlist investigasi, persist `followup.json`, export Excel + impor hasil tindak lanjut), **KPI row di atas tabel DIHAPUS** di semua tab data (tabel jadi lebar & besar; ringkasan pindah ke status footer), dan **aplikasi diperingatkan** (deviasi 16× lebih cepat via vektorisasi numpy; laporan 3.7×; lazy refresh per tab — hanya tab aktif yang dihitung).
> **v3.3 — Engine cepat + bug fix hasil deep audit**: **sort kolom kini LINEAR** (delete+reinsert — dulu `tree.move` O(n²) membekukan UI 45 detik di 50k baris, kini 0,7 detik), **fix bug follow-up salah baris setelah sort** (iid-based), **fix NameError path error pipeline**, double-click sel ✓ = toggle, cache pivot dibagi GR/PCS, tanpa modal "Selesai", dead code dibersihkan.
> **v3.3.1 — FIX "Saldo SO kosong semua"** (tab Deviasi GR/PCS & Laporan): dua akar masalah digarap tuntas — **(1) sumber SO gagal terbaca**: data kini berupa **workbook gabungan `.xlsb`** (mis. `01.1 CEK STOCK V2.xlsb`, sheet `1  DEVIASI WEEKLY`, semua resto dalam 1 sheet) padahal reader lama hanya mencari file per-resto `.xlsx` ber-sheet `REKAP MENTAH` → reader baru otomatis mendeteksi sheet ber-schema rekap mentah di file/format apa pun (`*.xlsb` kini ter-glob; NAMA RESTO diambil dari kolom; scan folder + RootPath; `pyxlsb` ditambahkan ke requirements), **(2) bug render vektorisasi v3.2**: kolom matrix `SO_H-2 … SO_H+2 / In / Out / BK` (Deviasi) dan `Saldo Awal / IN / OUT / BK / Saldo Kumulatif` (Laporan) tidak pernah diekstrak ke builder baris → selalu tampil `-` walau datanya ada → kini semua kolom terisi. Divalidasi terhadap sheet `DEVIASI GR` workbook user: 1404/1405 baris identik (2 sel beda = pivot cache Excel user yang stale, bukan app).
> **v3.6 — FIX tombol filter + hide/unhide kolom + audit dari data app + tanggal 26 lalu→31 berjalan**: **(1) BUG FIX KRITIS: tombol filter ⧩ di judul kolom TIDAK BISA DIKLIK dengan mouse** — `identify_column()` mengembalikan ID posisi-display (`#2`) sedangkan filter mencocokkan nama kolom simbolik (`Nama Barang`) → tidak pernah match (popup hanya terbuka via pemanggilan programatik; screenshot dev sebelumnya menipu). Kini klik funnel membuka popup di SEMUA tabel, tetap akurat saat ada kolom disembunyikan; window ⛶ Perbesar juga kini punya filter+sort sendiri (sebelumnya ikon funnel tersalin tapi MATI). **(2) HIDE/UNHIDE KOLOM** — klik kanan judul kolom (Sembunyikan/Auto-fit/Filter/Tampilkan semua) + tombol **◱ Kolom** (panel checklist) di semua tabel & window ⛶. **(3) AUDIT REKONSILIASI dari DATA APP** (permintaan user: tanpa sheet 29): tabel Rekap Selisih IN jadi SATU (segment dihapus) dengan kolom baru **Hasil SO · Saldo · Hasil Audit · Catatan Audit** — semua bisa difilter ⧩. **(4) Default tanggal -26 s/d 31 = tgl 26 BULAN LALU s/d 31 BULAN BERJALAN** + kolom hari bulan lalu berlabel `25•` + urutan kronologis diperbaiki.
> **v3.5 — Audit Rekonsiliasi (port macro VBA) + semua header ber-filter + LightMode dihapus**: mode **🔍 Audit Rekonsiliasi** di tab Rekap Selisih IN membaca sheet **`29 Rekap Barang Masuk`** langsung dan menjalankan algoritma macro VBA `BuatLaporanDeviasiSampel` (saldo kumulatif, VALID/CUT-OFF/DEVIASI MURNI, KPI chips, baris berwarna — tervalidasi 86.713/86.738 baris identik dgn output macro user; 86.738 baris render 3,4 detik). **LightMode DIHAPUS** (selalu FULL). **Matrix resto tanggal default 26–31**. **SEMUA judul kolom kini punya filter ⧩** (Excel AutoFilter) — filter RESTO/STATUS duplikat di card atas dihapus; kolom **KATEGORI** baru di Rekap Selisih IN.
> **v3.4 — Lebar kolom + SO bulan lalu + tab Rekap Selisih IN**: **(1)** lebar kolom kini **bisa di-adjust** — drag tepi kanan judul kolom untuk resize manual, double-click tepi = auto-fit 1 kolom, tombol **↔ Auto-Fit** di semua tabel (termasuk window ⛶ dan popup); **(2) FIX "SO bulan lalu gak ke record meskipun LightMode OFF"** — sheet `SO BULAN LALU` di workbook gabungan kini terbaca otomatis (header hari `Sum of N` + tanpa SATUAN didukung; scan RootPath untuk mode `lalu` dibatasi sheet ber-nama "LALU" agar bulan berjalan/lalu tidak tercampur) → tercatat sebagai Tanggal `-25 s/d -31`; **(3) tab BARU 📤 Rekap Selisih IN** — rekap per Resto × Tanggal × Barang × Satuan: **IN** (Accurate: 42.05+32.24+99.01) vs **Barang Masuk** (input rekap SO) + **Selisih IN**, double-click → **popup rincian IN per dokumen 42.05 / 32.24 / 99.01 BESERTA NOMORNYA** (subtotal per sumber + copy nomor); 9901 kini membawa kolom Nomor (PI) & Nomor PO; export Excel + sheet `Rincian IN`.

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

## Fitur Baru v3.7 — "ENGINE TURBO" + Deep Audit Fixes

### ⚡ Engine 3,5–4× lebih cepat (output terverifikasi IDENTIK)
Deep audit engine (cProfile + wall-time per stage, data asli) menemukan 2 hotspot Python-loop per-grup yang makan ~75% waktu komputasi:
- **`fn_running_stock_grouped` vektor** — global segmented cumsum (satu sort + `np.cumsum` + offset grup + posisi start per grup): **6,68s → 0,19s (36×)** di real-data 561 rb baris / 14.388 grup. 6 edge-case sintetis == implementasi lama (bulan lalu · tanggal NaN · key NaN · saldo awal negatif/all-NaN · grup tanpa tgl ≥ 1). **Bug benchmark awal tertangkap unit-test**: akumulasi harus mulai dari baris PERTAMA tanggal ≥ 1, bukan awal grup — real-data lama lolos benchmark hanya karena baris bulan-lalunya ber-net 0 (di mesin dengan RI 32.24 Bulan Lalu, versi benchmark awal akan SALAH).
- **InformationGrouped vektor** (`_group_info_columns` di `append1.py`) — per kolom: dropna → `astype(str)` → `drop_duplicates(key+nilai)` → `groupby().agg(', '.join)` level C: **6,67s → 0,05s (130×)**; paritas 100% dengan UDF `_smart_join` lama (0/80.069 grup beda real-data + 8 edge-case sintetis termasuk key NaN yang membuat groupby menghasilkan kolom float64 → normalisasi dtype sebelum merge).
- **Reader rekap single-parse** (jalur calamine): `_read_combined_file` membaca sheet SEKALI (header=None penuh), deteksi header dari 6 baris pertama frame yang sudah terbaca, promote di memori (`_promote_at`) — peek `nrows=8` di calamine mem-parse seluruh sheet juga (0,17s vs full 0,25s), jadi peek+full = 2× parse sia-sia. Jalur openpyxl tetap peek-dulu (murah di read-only).
- **Verifikasi A/B real-data**: append1 **2.792.790 baris** + in_detail 86.057 + audit 80.068 + KPI — **SEMUA IDENTIK** (numeric `np.allclose` maxdiff 8e-08; non-numerik exact). Pipeline real-data: **20,6s → 4,9s (4,2×)**. `python-calamine` (engine Rust) sudah dideklarasikan di `requirements.txt` — pastikan terpasang (`pip install -r requirements.txt`) supaya I/O Excel 2,6–3× lebih cepat dari openpyxl.

### 🐛 FIX 9 bug fitur v3.6 (deep audit)
Akar sistemik: setelah kolom disembunyikan, **posisi-display ≠ index logis** `values[]` Treeview — beberapa handler masih memetakan `identify_column()` (display) ke daftar kolom logis:
1. **Filter clone ⛶** (`apply_tree_row_filters`) membaca nilai kolom yang SALAH setelah hide (kini: index logis `tree["columns"]`).
2. **Auto-fit** mengukur nilai kolom yang salah setelah hide (kini: index logis).
3. **Filter '#0' clone pivot** mencocokkan text ANAK (nama metric) → pilih nama barang = semua baris hilang (kini: text PARENT — sesuai dokumentasi aslinya).
4. **Drill-down pivot** double-click → resto/tanggal KELIRU setelah hide (kini: `identify_to_column` → nama kolom).
5. **Double-click copy Nomor/Nomor PO** di popup Rincian IN & popup detail (clone) mengambil kolom salah (kini: nama kolom).
6. **Toggle ✓** (Deviasi GR/PCS + Laporan Deviasi + Follow Up) terpicu dari kolom lain setelah ✓ disembunyikan — klik & double-click (kini: cocok NAMA kolom "✓").
7. **Posisi popup filter** melenceng setelah hide (dulu ikut menjumlahkan lebar kolom tersembunyi + lebar #0 phantom saat show="headings").
8. **Mirror hide/unhide clone↔sumber** tidak sinkron state — panel Kolom tabel sumber menampilkan checkbox basi & apply() berikutnya menimpa state mirror (kini: colmgr terdaftar di tree, state `hidden` tersinkron).
9. **in_selisih `_apply_columns`** kini re-apply state kolom tersembunyi setelah reconfigure (defensive).

### ✅ Test
174/174 UI test (164 lama + **10 regresi baru**: filter-clone-benar-setelah-hide, reset-clone, #0-2-level, auto-fit-benar, klik-bukan-✓-tidak-toggle, mirror-sync×2, running-stock==lama 6 case, info-group==lama, `_promote_at`) + mock + E2E real-data (pipeline 4,9s, render 2,6s, funnel 0,05s, filter 0,2s) PASS.

---

## Fitur Baru v3.6

### 🐛 BUG FIX KRITIS — tombol filter ⧩ tidak bisa diklik
`ttk.Treeview.identify_column()` mengembalikan **ID posisi-tampilan** (`#2`), sedangkan `HeaderFilter` mencocokkan **nama kolom simbolik** (`"Nama Barang"`) → klik funnel dengan mouse **tidak pernah membuka popup** (sejak v3.1!). Popup hanya terbuka via pemanggilan programatik — itulah kenapa screenshot dev terlihat normal. Fix: resolver `identify_to_column()` (posisi-display → nama kolom aktual, termasuk saat kolom disembunyikan/di-reindex). Window **⛶ Perbesar** juga kini memasang **filter+sort sendiri** di clone-nya (sebelumnya heading tersalin lengkap dengan ikon funnel-nya tapi **tanpa binding apa pun** — funnel mati).

### ◱ Hide / Unhide kolom (semua tabel)
- **Klik kanan judul kolom** → menu: ⧩ Filter kolom ini · ↔ Auto-fit kolom ini · ◱ Sembunyikan kolom ini · ▦ Tampilkan Semua · ◫ Panel Kolom · ↔ Auto-fit Semua.
- **Tombol ◱ Kolom** di setiap tabel + window ⛶ → panel checklist semua kolom (centang = tampil, scrollable, Esc tutup).
- State per-tabel in-memory; di window ⛶ perubahan **mirror** ke tabel utama (tetap konsisten setelah window ditutup); minimal 1 kolom selalu tampil; funnel/auto-fit/resize tetap benar terhadap kolom yang tampil (`displaycolumns`-aware).

### 🔍 Audit Rekonsiliasi dari DATA APP (tanpa sheet 29)
Permintaan user: *"audit rekonsiliasi tidak perlu ambil dari sheet 29 — aplikasikan logika nya dengan tambah kolom SO dan kolom hasil audit nya, bisa difilter"*. Tabel 📤 Rekap Selisih IN kini **SATU** (segment Ringkas|Audit dihapus) per (Resto × Tanggal × Barang):
- **Sumber input = data app** (`src/pipeline/fn_audit.py` — reader sheet 29 DIHAPUS): **Hasil SO** ← rekap `JENIS='SO'` (hari 1..31 + -25..-31 lalu; hadir hanya di tanggal yang SO direkam); **Qty SO Harian** ← rekap `JENIS='BARANG MASUK'`; **Qty SJ/RI/Pembelian** ← in_detail per tanggal (42.05 / 32.24+32.24 lalu / 99.01); baris = union tanggal beraktivitas; urut (Resto, Item, Tanggal).
- **Kolom baru**: Hasil SO (kolom SO) · Saldo · **Hasil Audit** · Catatan Audit — **semua bisa difilter ⧩** (mis. tampilkan hanya DEVIASI MURNI).
- **Engine tetap port 1:1 macro VBA** (divalidasi 99,97% identik vs LAPORAN_DEVIASI pada input yang sama): VALID (Sistem Masuk) / OK (Matching) / CUT-OFF RESOLVED / OK (Dalam Cut-off) / DEVIASI MURNI + KPI chips + baris berwarna. Filter tetap display-only.
- Catatan data: kolom **Barang Masuk** terisi saat rekap berisi input `JENIS='BARANG MASUK'`; selama belum diinput, baris ber-IN akan ditandai DEVIASI MURNI (selisih = −penerimaan) — sesuai logika rekonsiliasi.

### 📅 Default tanggal 26 BULAN LALU s/d 31 BULAN BERJALAN
- Pivot + Rekap Selisih IN: default **`-26` s/d `31`** (tgl 26 bulan lalu → 31 bulan berjalan = periode resto penuh); Reset Filter kembali ke sana; angka negatif = bulan lalu.
- Mode Tanggal pivot: kolom bulan lalu berlabel **`25•`** + legend `tgl • = bulan lalu`; **urutan kronologis diperbaiki** (dulu ascending naif meletakkan -31 sebelum -25 = terbalik; juga membuat 6.PEMAKAIAN (COM) salah ambil SO hari-sebelumnya di perbatasan bulan).

---

## Fitur Baru v3.5

### 🔍 Mode "Audit Rekonsiliasi" — port macro VBA BuatLaporanDeviasiSampel
Tab 📤 Rekap Selisih IN kini punya 2 mode (segment di atas tabel): **📋 Ringkas** (perilaku v3.4) dan **🔍 Audit Rekonsiliasi** (default bila tersedia).
- **Input = sheet `29 Rekap Barang Masuk`** dibaca LANGSUNG dari workbook user (auto-scan RootPath + folder config; nama sheet dinormalisasi — harus mengandung `REKAP` + `BARANG MASUK`, jadi sheet pivot `Barang Masuk` tidak salah terbaca). 10 kolom persis input macro: Resto/Nama Item/UoM/Tanggal/Hasil SO/Qty Masuk SO Harian/Qty SJ 42.05/Qty RI 32.24/Qty Pembelian 99.01/Selisih Qty.
- **Algoritma port 1:1** (`src/pipeline/fn_rekap29.py`): Penerimaan Sistem = SJ+RI+Pembelian; Selisih Harian = Qty SO Harian − Penerimaan; grup kontigu (Resto × Item, urut sheet — identik macro); aturan **VALID (Sistem Masuk)** (deltaSO > 0 + SO Harian = 0 + Penerimaan > 0 → omit input harian); **OK (Matching)**; saldo kumulatif; **CUT-OFF RESOLVED** saat saldo kembali ±0,0001 (catatan "Beda X Hari (Periode Tgl A–B)"); sisa gantung akhir bulan → **DEVIASI MURNI** ("Sisa Gantung: ±N (Sejak Tgl X)"); format angka locale Indonesia (titik ribuan) persis output macro.
- **Tabel 12 kolom**: Resto | Tanggal | Nama Barang | KATEGORI | Satuan | Hasil SO | Qty SO Harian | Penerimaan Sistem | Selisih Harian | Saldo Kumulatif | Status Analisis Audit | Detail & Catatan Audit.
- **KPI chips** di atas tabel (mirror "EXECUTIVE RECONCILIATION SUMMARY"): Total Baris · OK (Matching) · Valid (Sistem Masuk) · Cut-off Resolved · Deviasi Murni · Sisa Gantung (Net) — dihitung dari sheet penuh, tidak terpengaruh filter tampilan.
- **Baris berwarna** (mirror conditional formatting VBA): hijau OK, biru VALID, kuning CUT-OFF, merah DEVIASI MURNI.
- **Filter = display-only**: rentang tanggal / RESTO / KATEGORI / status / nilai kolom hanya menyembunyikan baris — status & saldo kumulatif tetap dihitung dari sheet penuh (dipotong = rekonsiliasi salah).
- Default "Hanya Selisih ≠ 0" ON di mode audit (langsung fokus baris bermasalah; matikan untuk lihat semua 86k+ baris — render 3,4 detik).
- **Validasi**: 86.713/86.738 baris **100% identik** dgn sheet `LAPORAN_DEVIASI` (output macro user) — status, saldo kumulatif, selisih, penerimaan, sampai string detail catatan. 25 baris sisanya = 1 grup (SBRTUP SURAI NAGA) yang datanya berubah setelah macro terakhir dijalankan (terbukti: layout LAPORAN lama = header baris 1, macro yang dipaste = header baris 11).
- Pipeline: `run_pipeline` kini return **4 hasil** (append1, rincian_po, in_detail, audit_result); export Excel + sheet **`Laporan Deviasi (Audit)`**.
- Double-click baris (kedua mode) tetap membuka popup **Rincian IN 42.05/32.24/99.01 + nomor**.

### ⧩ SEMUA header kolom punya filter (Excel AutoFilter) — duplikat di atas dihapus
- Klik judul kolom **mana pun** → popup filter: search + checkbox nilai unik + pilih semua + **↕ Sort A→Z / Z→A** + reset (nilai terformat identik dgn yang tampil di tabel).
- Berlaku di: Rekap Selisih IN (kedua mode), Laporan Deviasi, Deviasi GR/PCS, Rincian PO (termasuk kolom Nomor #), Follow Up. Kolom ✓ tetap toggle follow-up.
- **Filter duplikat di card atas DIHAPUS**: RESTO (Deviasi GR/PCS, Laporan, Rekap Selisih IN) dan STATUS (Laporan) — digantikan filter header kolomnya. Card atas kini berisi TANGGAL/opsi yang tidak terduplikasi saja.
- Widget baru `HeaderFilterGroup` (+ `SegmentBar.set_active_silent`, `HeaderFilter.detach` anti binding ganda saat kolom dikonfigurasi ulang).

### 🧹 Lainnya
- **LightMode DIHAPUS TOTAL** — pipeline selalu FULL (checkbox di tab Config hilang; key `LightMode` lama di config.json diabaikan/dibuang saat save; 3224 bulan lalu & RekapLalu selalu dibaca).
- **Matrix resto (Pivot): TANGGAL default 26–31** — total per resto dihitung hanya dari tanggal dalam rentang; Reset mengembalikan 26–31.
- Kolom **KATEGORI** baru di Rekap Selisih IN (map via DBS Kategori).
- `config.json`: `_comment` diperbarui (tanpa LightMode).

## Fitur Baru v3.4

### 📏 Lebar kolom bisa di-adjust + ↔ Auto-Fit (semua tabel)
- **Drag** tepi kanan judul kolom → resize manual (zona tepi 7px, jauh lebih mudah daripada separator bawaan Tk yang nyaris tak terlihat).
- **Double-click tepi kolom** → auto-fit kolom itu ke lebar konten (ala Excel).
- Tombol **↔ Auto-Fit** di atas setiap tabel (juga di window ⛶ Perbesar dan semua popup) → auto-fit SEMUA kolom (judul + sampel ≤400 baris diukur via `Font.measure`, dibatasi 44–340px).
- Mengapa sebelumnya "tidak bisa": popup filter header membuka `grab_set()` saat Button-1 di heading → pointer ter-curiah sehingga drag mati; kini binding resize dipasang **pertama** dan mengembalikan `"break"` saat drag → sort/filter tidak terpicu.

### 🐛 FIX — "SO bulan lalu gak ke record meskipun LightMode OFF"
- Data bulan lalu user ada di sheet **`SO BULAN LALU`** (workbook gabungan di RootPath; schema: NAMA RESTO + NAMA BARANG + JENIS + kolom hari `Sum of 1`..`Sum of 31`, tanpa SATUAN). Sebelumnya: mode `lalu` tidak pernah scan RootPath + sheet itu gagal deteksi → `1.12 Rekap Mentah Bulan Lalu` kosong → SO bulan lalu tidak pernah terbaca.
- Fix: deteksi schema menerima header hari `Sum of N` dan SATUAN opsional (wajib: NAMA RESTO + JENIS + NAMA BARANG + ≥3 kolom hari); mode `lalu` ikut scan RootPath **tetapi hanya sheet ber-nama "LALU"**; mode `berjalan` kini SKIP sheet ber-nama "LALU" (defensive — `1  DEVIASI WEEKLY` tetap sumber bulan berjalan).
- Hasil (data asli user): **11970 baris SO bulan lalu terbaca** (Tanggal `-25 s/d -31`, total 534.232.690 — identik dgn penjumlahan mentah sheet), append1 bertambah 105.735 baris `1.SO` negatif-tanggal; nilai Deviasi GR/PCS **tidak berubah** (SO_23/24/25 = 145.408/110.289/202.000 — identik v3.3.1).

### 📤 Tab BARU — "Rekap Selisih IN" (drill-down rincian dokumen)
- Kolom: **Resto | Tanggal | Nama Barang | Satuan | IN | Barang Masuk | Selisih IN** (1 baris per Resto × Tanggal × Barang; hanya baris dengan aktivitas IN≠0 / BM≠0).
  - `IN` = metric `4.IN` (Accurate: 42.05 + 32.24 + 99.01 + 32.24 bulan lalu).
  - `Barang Masuk` = metric `5.BARANG MASUK` (input rekap SO harian).
  - `Selisih IN` = `7.Selisih IN` = Barang Masuk − IN.
- **Double-click baris → popup RINCIAN IN**: daftar dokumen pendukung per sumber **42.05 / 32.24 / 32.24 (Bulan Lalu) / 99.01 BESERTA NOMORNYA** + Nomor PO + Qty + subtotal per sumber + TOTAL IN + chip ringkasan; copy Nomor (klik kanan / double-click cell / 📋 Semua Nomor unik); ⛶ Perbesar + ↔ Auto-Fit + sort.
- Filter: RESTO, rentang TANGGAL (1–31; `-25..-31` = bulan lalu), checkbox **Hanya Selisih ≠ 0**, header-filter Nama Barang.
- Pipeline: `query_in(detail_out=…)` menandai tiap baris IN dengan `SOURCE IN`; `run_pipeline` kini return **3 DataFrame** (append1, rincian_po, in_detail); export Excel menambah sheet **`Rincian IN`**; konsistensi dijamin — total rincian popup == kolom IN (max diff 0.0 di 573.990 grup data asli).
- `fn_9901` kini membawa kolom **Nomor** (`Nomor #` = nomor faktur pembelian `PI.2026…`) dan **Nomor PO**.

## Fitur Baru v3.3.1

### 🐛 FIX KRITIS — "Saldo SO kosong semua" (tab Deviasi GR / PCS / Laporan)
Dua akar masalah, keduanya digarap:

**1. Sumber SO tidak terbaca (pipeline `fn_rekap_mentah`)**
- Data SO user kini berupa **satu workbook gabungan `.xlsb`** (`01.1 CEK STOCK V2.xlsb`, sheet `1  DEVIASI WEEKLY`: 20 resto × 150 barang × hari 1-31, JENIS = `SO`, NAMA RESTO sebagai KOLOM) — padahal reader lama (mirror M) hanya mencari **file per-resto `.xlsx/.xls/.xlsm` ber-sheet `REKAP MENTAH`** dengan NAMA RESTO dari nama file. Akibat: glob tidak match → SO = 0 semua → kolom SO `-`.
- Reader baru: bila folder tidak punya file per-resto, **scan otomatis** semua file (termasuk `*.xlsb`) × sheet → deteksi baris header ber-schema rekap mentah (NAMA RESTO + JENIS + NAMA BARANG + SATUAN + ≥3 kolom hari 1-31) → baca dengan NAMA RESTO dari kolom. Scan folder itu + folder induk/RootPath (mode berjalan saja, agar bulan lalu tidak tercampur).
- Format per-resto lama **tetap didukung** (dipakai duluan bila ada — tidak ada double-count).
- `*.xlsb` kini terbaca di seluruh pipeline (`helpers._list_excel_files` + engine `pyxlsb`/`calamine` di `fn_buka_sheet`); `pyxlsb>=0.7.0` ditambahkan ke `requirements.txt`.
- Nilai teks di-strip (`SATUAN "GR "` → `"GR"` — 57 nilai trailing-space di data user; tanpa strip baris GR bocor ke tab PCS).

**2. Bug render vektorisasi v3.2 (UI)**
- `_prepare_rows` (Deviasi GR/PCS & Laporan) membangun `cols_np` yang **lupa 8 kolom matrix**: `SO_H-2, SO_H-1, In_H-1, In_H, Out_H, BK_H, SO_H+1, In_H+1, SO_H+2` + (Laporan) `Saldo Awal, IN, OUT, BK, Saldo Kumulatif` → kolom tersebut jatuh ke `else 0` → **selalu `-` walau data pivot benar**. Kini semua kolom diekstrak numerik.

**Validasi (data asli user):** `BDGUKU · ADONAN PANGSIT (V.20) · tgl 25 = 336.480` identik dgn sheet mentah; perbandingan penuh vs sheet `DEVIASI GR` workbook user: **1404/1405 baris SO_23/24/25 identik** (2 sel beda = pivot cache Excel user yang stale — data mentahnya sendiri sudah direvisi setelah refresh terakhir). `test_mock.py` (format per-resto) + `test_ui_redesign.py` 117/117 PASS.

## Fitur Baru v3.3

### ⚡ Engine sort LINEAR (akar "aplikasi tambah berat")
- Dulu: klik judul kolom → `tree.move` per baris → **O(n²)** internal Tk — sort 50k baris (Laporan Deviasi) **membekukan UI 45 detik**.
- Kini: snapshot `tree.item()` → `delete` semua → insert ulang di posisi `end` (append cepat) → **O(n)** — 50k baris ter-sort **0,7 detik** (42-64× lebih cepat); 20k: 1,9 s → 0,29 s.
- **iid dipertahankan** → pemetaan ✓ follow-up & double-click tetap mengenai baris yang benar setelah sort; seleksi baris dipulihkan.
- Sort saat render batch berjalan ditunda otomatis (mencegah urutan campur).

### 🐛 Bug fix hasil deep audit
- **Follow-up salah baris setelah sort** (kritis): klik ✓ / double-click di tab Follow Up memakai `tree.index()` + urutan lama → SETELAH SORT mengenai/keluarkan **baris yang salah**. Kini **iid-based** (`iid → fingerprint`) — selalu baris yang benar, juga di window ⛶ Perbesar.
- **Path error pipeline tidak pernah sampai UI**: `except … as e:` + lambda tertunda → Python menghapus binding `e` di akhir blok → **NameError** di callback. Kini error ditangkap ke tuple lokal dulu.
- **Double-click sel kolom ✓** = toggle follow-up (dulu tetap membuka popup — kurang intuitif), di Deviasi/Laporan/Follow Up.

### 🧹 Perf & bersih-bersih
- **Cache pivot Deviasi dibagi GR/PCS** — `_compute_pivot()` tidak bergantung satuan, dulu GR & PCS menghitung pivot identik **2×** (waktu + memori ganda).
- **Cache Laporan tanpa recompute** saat ganti rentang tanggal (signature lama memasukkan rentang padahal compute tidak bergantung rentang → 230 ms sia-sia per ganti).
- Insert batch **delay adaptif** (>20k baris: 1 ms/batch, tidak lagi +1 detik ekstra di 50k).
- Pop-up detail **tanpa `data.copy()` penuh** sebelum filter.
- Selesai pipeline → **status bar + log** (modal `messagebox "Selesai"` yang mem-blok alur dihapus).
- **Dead code dibersihkan**: 24 unused import (ruff F401), 9 konstanta warna theme tak terpakai, method mati (`SegmentBar.set_active`, `FollowUpStore.pending_count`/`prune_for_new_data`, `Card._title/_subtitle`), dead lines di `vec_text_before_delimiter`, `test_large_scale.py` dihapus. `ruff check --select F401,F811,F841` kini **bersih**.
- `.gitignore` ditambahkan (`followup*.json`, `__pycache__/`, `*.bad`) — file runtime lokal tidak masuk repo.

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
- **Rekap Selisih IN** *(v3.4)* — rekap IN (Accurate) vs Barang Masuk + drill-down rincian dokumen 42.05/32.24/99.01 + nomor
- **Semua tabel** — zebra rows, sort kolom (klik header), double-click baris → popup detail source data (header gelap, centered modal, Esc untuk tutup), **lebar kolom bisa di-adjust** *(v3.4: drag tepi judul / double-click tepi = auto-fit / tombol ↔ Auto-Fit)*
- Popup & jendela Bantuan otomatis **ter-center** di parent

---

## Struktur Folder

```
stock-monitoring-python/
├── MULAI.bat / SETUP.bat       # entry point Windows
├── config.json                 # RootPath + LightMode + Folders + Sheets
├── requirements.txt
├── test_mock.py                # test pipeline end-to-end (mock Accurate export)
├── test_ui_redesign.py         # test UI v3.7 (174 check — + engine turbo & fix display-vs-logical index)
├── bench_views.py              # benchmark compute per view (dev — ukur perf vektorisasi)
├── screenshot_ui.py            # dev tool: screenshot semua tab (butuh Xvfb)
└── src/
    ├── config.py               # loader config.json
    ├── main.py                 # run_pipeline() → (append1_df, rincian_po_df, in_detail_df, audit_result)
    ├── pipeline/               # porting fn_* dari M code + (v3.6) fn_audit.py (Audit data app)
    │   ├── fn_audit.py         # (v3.6) input audit dari data app + engine rekonsiliasi (port macro VBA)
    │   └── …                   # fn_rekap_mentah, fn_2205…fn_9901, queries, append1, rincian_po
    └── ui/                     # ← REDESIGN v3.0 (v3.2: +followup, v3.4: +rekap selisih IN, v3.6: +audit data app)
        ├── app.py              # shell: toolbar + 9 tab + status bar + kontrol pipeline + lazy tab refresh
        ├── theme.py            # design system (palet + font + ttk style)
        ├── widgets.py          # Card, tombol, tooltip, empty state, overlay, HeaderFilter(+Group), ColumnManager (v3.6), resize, auto-fit, dll
        ├── followup.py         # (v3.2) FollowUpStore: fingerprint, snapshot, persist, export/import xlsx
        ├── followup_view.py    # (v3.2) tab ☑ Follow Up
        ├── pivot_view.py       # tab Pivot Table (per resto default; default -26..31)
        ├── deviasi_view.py     # tab Deviasi GR & PCS (vektorisasi numpy + kolom ✓)
        ├── laporan_deviasi_view.py  # tab Laporan Deviasi (np.select + kolom ✓)
        ├── in_selisih_view.py  # (v3.4→v3.6) tab 📤 Rekap Selisih IN + audit data app + popup Rincian IN
        ├── rincian_po_view.py  # tab Rincian PO
        └── details_popup.py    # popup detail source rows (copy Nomor/PO)
```

---

## Testing

```
python test_mock.py          # pipeline end-to-end dgn mock data Accurate
python test_ui_redesign.py   # UI v3.7: 174 check (jalankan di bawah Xvfb di Linux)
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
