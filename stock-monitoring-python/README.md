# Stock Monitoring — Python Edition

Porting **Power Query M code** untuk monitoring stok resto ke **Python**.
Pipeline membaca data export Accurate Online, menggabungkan, memutar (pivot), menghitung running stock & deviasi, lalu **menampilkan langsung di UI** (tanpa Excel output).

> Versi asli: Power Query M (1.009 baris, 30 query).
> Versi Python: 10 modul `fn_*` + `queries.py` + `append1.py` + `rincian_po.py` + UI Tkinter.
> **v3.9.12 — TAB 🎯 PARETO DIHAPUS** (user: *"hapus tab pareto dan dead code nya"*): tab 🎯 Pareto (v3.9.9) dihapus — app kembali **9 tab**; `pareto_view.py` (ParetoDeviasiView, 823 baris) + `write_pareto_sheet()` di export_sheets.py + seluruh integrasi app.py dibersihkan; fitur lain tidak tersentuh.
> **v3.9.11 — TUNTAS SISA TEMUAN AUDIT + REPO PRIVATE** (user: "kerjakan semua dan repo untuk pribadi aja"): **P0 D-11 — repo GitHub kini PRIVATE** (data produksi + objek 2205.xlsx di history tidak lagi publik; BFG tidak perlu). 7 fix sisa audit 2-b: **B-21 panah arah sort di heading** (↓/↑ — kolom terurut kini terlihat), **B-14 toggle filter clone tidak me-reset urutan sort** (sort terakhir dijalankan ulang sebelum reapply tag), **B-09 sort tree berhirarki aman** (jalur tree.move — anak subtree/text/open terjaga; flat O(n) tetap), **B-18 mirror kolom ⛶ dua arah** (hide kolom di tabel utama tercermin di clone terbuka + backref bersih saat tutup), **B-17 cursor watch ber-refcount** (2 overlay tidak saling me-reset), **B-16 TableExpander restore urutan benar**, **B-12 pecahan tanggal ditolak** ("7.9" tidak lagi dilantai senyap jadi 7), **B-11 EmptyState adaptif** (clamp 520×260). + FIX laten: import contextlib di app.py (F821). **514/514 UI test × 2 run (22 baru §26 satu-per-bug) + mock ALL PASS + ruff 223 < 224.**
>
> **v3.9.10 — DEEP AUDIT UI/UX ROUND 2**: audit ulang 4-arah (shell/tabel/view/integritas — 37 temuan) + fix P1-P3 TANPA menyentuh formula bisnis: race restart pipeline (Stop→MULAI tidak lagi dobel thread), cache-poisoning worker (data basi senyap saat pipeline selesai di tengah refresh — capture identitas di awal compute), on_error Rincian PO & popup detail (view tidak mati permanen), sort Rekap Selisih IN parser Indonesia, file Excel di-skip kini TERLIHAT ("SELESAI ⚠ N file dilewati"), tag minus per-cell bertahan di clone ⛶ setelah filter (4 view + popup), auto-fit double-click tepi kolom hidup lagi (bind add="+"), filter header >3000 nilai bisa dicentang via pencarian (lazy), gc_shield thread-safe (Lock), sort-saat-render di-antre, race render Follow Up, tombol disabled tampak dim, DPI-awareness Windows, Ctrl+Tab navigasi tab, routing tab berbasis widget, **tab strip muat di 1020px** (dulu tab kanan terpotong) + WINDOW_MIN 700 (h-scrollbar selalu terlihat), format angka Indonesia di Rincian PO & popup, minus merah per-cell Selisih IN, frasa instruksi dipangkas, footer "baris", tulis atomik config/komparasi_last. **492/492 UI test (55 baru — satu per bug) + mock + ruff 224 < baseline 261 + VLM visual 2 batch + probe piksel/H-1.**
>
> **v3.9.9 — TAB 🎯 PARETO (80/20 KONTRIBUTOR DEVIASI TERBESAR)**: tab BARU 🎯 Pareto (setelah Deviasi PCS — app kini 10 tab): semua kombinasi (Barang × Resto × Satuan) **diurut |Deviasi| menurun** + **Kontribusi %** + **Kumulatif %** + **Fokus 🎯** (baris yang diperlukan mencapai CUTOFF % — default 80, input 1–100) → fokus list audit "20% kombinasi menyumbang 80% deviasi". MODE GR/PCS (SegmentBar) · TANGGAL H chip read-only (state bersama, ikut Apply H) · KPI strip (KOMBINASI · TOTAL |DEVIASI| · FOKUS ≤ CUTOFF · TOP 20%) · GRAFIK canvas (top-30 batang teal/amber kumulatif/garis cutoff merah/batas fokus) · ✓ follow-up fingerprint identik tab Deviasi (dedup 1 entri) · export 💾 sheet PARETO. Pivot dihitung 1× (subclass DeviasiView + SharedPivotCache). 438/438 UI test × 2 + smoke real-data 3,5jt baris (oracle 25/25 × 3 konfigurasi; fokus/total == oracle) + VLM visual PASS.
> **v3.9.8 — UI CLEAN**: **SEMUA teks instruksi/petunjuk DIHAPUS dari UI** (permintaan user: "kata kata atau kalimat diseluruh aplikasi python hapus semua biar clean tanpa teks teks gak penting") — tombol "❓ Bantuan" + window panduan (±200 baris), subtitle semua kartu (mis. "Filter Nama Barang → klik header kolom (ikon corong ⧩)"), hint footer (🖱 Double-click → …) di semua tabel + window ⛶, **tooltip hover** (class `ToolTip`/`add_tooltip` dihapus dari widgets), subtitle EmptyState, subtitle tab Config/Proses, pertanyaan dialog export IN. Yang tetap: label input, tombol, chip nilai, footer status berisi DATA (n baris · MATCH/SELISIH · Minggu WEEK X), legenda CEK/warna, KPI, pesan error, log proses. 390/390 UI test × 2 + mock + ruff 0 baru + VLM visual PASS.
> **v3.9.7 — MEDIAN ANOMALI COM ANTAR TANGGAL + FILTER MINGGU KOMPARASI MENGIKUTI H**: **(1) KOREKSI user ("harusnya antar tanggal — com itu pemakaian aktual harian di resto, bom pemakaian harian di sistem")**: median pembanding tab 🚨 Anomali COM kini = **median com(t) tgl 1..H per pasangan (barang × resto)** — pemakaian hari H vs pola harian pasangan itu sendiri, BUKAN antar resto; heading dinamis "Median (1..H)". **(2)** ⚖ Komparasi kini **filter minggu mengikuti H bersama** ("misal H aku input 7 maka hanya tampilkan week 1 aja" — STATUS BULAN dipakai utk filter): H 1–7 → WEEK 1 · 8–14 → WEEK 2 · 15–25 → WEEK 3/4 · 26–31 → WEEK 5; chip H read-only + chip minggu aktif highlight + opsi "Tampilkan semua minggu". FIX ikutan: _dirty basi (tabel komparasi tak refresh saat H diubah setelah load_data saat terlihat). 369/369 UI test × 2 + smoke real-data (oracle 25/25 median per-pasangan; H=7/14/25 → 1.356/1.365/1.367 baris == ekspektasi) + VLM visual PASS.
> **v3.9.6 — KATEGORI DEVIASI + PEMBANDING SO TGL 1 = SO BULAN LALU + FORMAT FOLLOW UP FILE SAMPLE**: **(1)** tab 📦 Deviasi GR & 🧩 Deviasi PCS kini punya **5 KOLOM KATEGORI DEVIASI** (mirror sheet DEVIASI GR/PCS workbook asli): **Max Deviasi** · **ACR** (rata-rata penjualan harian) · **Total ACR** (BOM = Σ penjualan 1..H) · **Dev to BOM%** (= Deviasi/Total ACR — "Loss Surplus to BOM") · **Stok Seharusnya** (= SO(H−1) − ACR) + **CEK kondisi ke-5 "ACR to BOM"** (|Deviasi| > Total ACR → pasti salah; melengkapi port formula LET 5 kondisi) + parser sort angka Indonesia; **(2)** audit Rekap Selisih IN diurut **kronologis** — di **tanggal 1**, pembanding SO (delta "SO Naik") kini = **SO TERAKHIR bulan lalu** (sort lama terbalik → membanding SO tgl 25•); **(3)** tab ☑ Follow Up + export kini **format sheet Follow UP file asli**: SO per tanggal (H-2..H+2, heading angka tanggal) · Sistem · Deviasi · Loss Surplus to BOM · Keterangan · SO · DEVIASI · Selisih · Selisih Deviasi · Cek FU · PIC. 358/358 UI test × 2 + smoke real-data (810 baris GR, 97 "ACR to BOM", audit 35.436 baris, komparasi 40.739 baris).
> **v3.9.5 — DEEP AUDIT BUG (4 agent paralel) → semua P1/P2/P3 diperbaiki**: **(P1) race ✕ Tutup File** saat komparasi menghitung → hasil file lama tak muncul lagi (generation counter); **(P1) kebocoran GC seumur sesi** (popup ditutup di tengah render → gc.disable menempel — poll kini di root app); **(P2) parse file 9,4MB di thread worker** (UI tak membeku 8 detik); **(P2) SALDO AWAL jadi base com(1)** di 3 view sekaligus (pivot/laporan/komparasi — pair tanpa data bulan-lalu tak lagi dapat MINUS PALSU di H=1; GR·App == DEV·App aljabar persis); **(P2) popup detail** pakai nama barang versi APP; **(P2) tag per-cell bertahan setelah filter di clone ⛶**; **(P2) popup filter "Selisih vs Median" hidup**; **(P2) Apply H render 1× (dulu 2×)**; plus duplikat multi-bulan dihitung, scan sheet ke-2, footer = hitungan baris tampil, filter reset saat ganti file, sort diantrekan saat busy, initialdir ikut RootPath, unsubscribe H, dst. **337/337 UI test × 2 run + smoke real-data 342rb baris + VLM visual PASS.**
> **v3.9.4 — KOMPARASI FILE DEVIASI vs TAB DEVIASI GR + "DEV TO BOM" DI APP**: tab 📋 Laporan Deviasi kini **2 MODE** (SegmentBar): **⚖ Komparasi File Deviasi (BARU — default)** — pilih file deviasi resmi (mis. `20.AGUSTUS 2026.xlsx`), tiap baris dibandingkan sisi-app pada **kolom H menurut minggunya (WEEK 1→7 · WEEK 2→14 · WEEK 3/4→25** — permintaan user; minggu file = cut-off kumulatif dari tgl 1); **BOM App = Σ penjualan 22.05** ("2205 itu BOM"), COM App = Σ pemakaian, **GR App = SO_H − Sistem persis tab 📦 Deviasi GR**, DEV App = COM−BOM (formula file); kolom Selisih + Status **MATCH / SELISIH / TIDAK ADA DI DATA APP / H TIDAK ADA**; resto file "1041.BDGUKU" dinormalkan otomatis; minus merah per-cell + sel Status hijau/amber/merah — dan **🚨 Anomali COM (v3.9.3, tetap ada tinggal ganti segmen)**.
> **v3.9.3 — LAPORAN DEVIASI → DAFTAR ANOMALI PEMAKAIAN (COM) (SEMENTARA)**: isi tab 📋 Laporan Deviasi DIGANTI — kini **daftar (Nama Barang × Resto) dengan pemakaian (COM) di kolom H yang MINUS atau LEBIH TINGGI dari MEDIAN barang tsb** (median antar resto, per barang, di kolom H). Formula COM identik baris 6.PEMAKAIAN (COM) pivot (com = SO(t-1) + IN − BK − SO; tanggal pertama = SALDO AWAL — diverifikasi oracle 286 nilai vs pivot, 0 mismatch); matriks COM di-cache (ganti H tanpa recompute); TANGGAL H bersama dari tab 📦 Deviasi GR (chip read-only + auto-refresh); minus merah **per cell** + sel Status merah/amber; tabel Audit Harian lama tersimpan di git history (commit e20141a).
> **v3.9 — SHARED H + EXPORT AUDIT + RINCIAN PO RINGKAS + STYLE WASTE**: **(1) TANGGAL H cukup input 1×** — input + tombol *Apply H* hanya ada di tab 📦 Deviasi GR, otomatis berlaku juga di tab 🧩 Deviasi PCS (chip nilai H read-only + refresh otomatis; pivot dihitung 1× via cache bersama + lock — tidak ada double input lagi). **(2) Export Rekap Selisih IN + opsi kolom hasil audit** — sebelum simpan file muncul dialog opsi: ☑ Hasil Audit · ☑ Saldo · ☑ Catatan Audit (bisa ditambahkan atau tidak, sesuai kebutuhan). **(3) Rincian PO DISEDERHANAKAN** — baris TEAL = info PO lengkap SEKALI (Nomor #, Tanggal, Pemasok, Status, Keterangan, N item, Total), baris putih di bawahnya = item saja (Nama Barang · Satuan · Kuantitas); kolom Tgl/Jam Pembuatan pindah ke baris induk + tersembunyi default (tampilkan via ◱ Kolom). **(4) STYLE ala repo Waste** — corong filter header **MERAH saat kolom terfilter** (idle = isi terang + outline gelap), **tabel diperbesar** (font 9→10, rowheight 26→30, heading 10 bold), tombol **⤢ Perbesar Tabel** (ciutkan baris kontrol → tabel tinggi penuh, in-place) + **⛶ Layar Penuh** (window terpisah) di semua tab, padding tombol/tab lebih lapang. **(5) CRASH FIX laten CPython 3.12+Tk** — finalisasi `tk.Variable` dari thread worker (pemicu segfault; kini mustahil via GC shield seumur thread) + cache pivot GR/PCS kini thread-safe (lock).
> **v3.0 — Total UI/UX redesign**: design language baru ala aplikasi *Waste* (slate + teal, card-based, dark toolbar, KPI cards, konsol log gelap). Pipeline & semua logika data **tidak berubah**.
> **v3.1 — UX upgrade**: filter Nama Barang menempel di header kolom (ala Excel AutoFilter, di SEMUA tab), tombol ⛶ **Perbesar tabel** (fullscreen), **copy Nomor/Nomor PO** di pop-up detail, **pivot per RESTO** (baris kosong disembunyikan, tanpa kolom Total), dan **animasi loading** di semua proses. Pipeline tetap 100% tidak berubah.
> **v3.2 — Follow Up + tabel besar + perf**: tab baru **☑ Follow Up** (ala aplikasi *Waste*: centang ✓ baris anomali di Deviasi GR/PCS & Laporan → shortlist investigasi, persist `followup.json`, export Excel + impor hasil tindak lanjut), **KPI row di atas tabel DIHAPUS** di semua tab data (tabel jadi lebar & besar; ringkasan pindah ke status footer), dan **aplikasi diperingatkan** (deviasi 16× lebih cepat via vektorisasi numpy; laporan 3.7×; lazy refresh per tab — hanya tab aktif yang dihitung).
> **v3.3 — Engine cepat + bug fix hasil deep audit**: **sort kolom kini LINEAR** (delete+reinsert — dulu `tree.move` O(n²) membekukan UI 45 detik di 50k baris, kini 0,7 detik), **fix bug follow-up salah baris setelah sort** (iid-based), **fix NameError path error pipeline**, double-click sel ✓ = toggle, cache pivot dibagi GR/PCS, tanpa modal "Selesai", dead code dibersihkan.
> **v3.3.1 — FIX "Saldo SO kosong semua"** (tab Deviasi GR/PCS & Laporan): dua akar masalah digarap tuntas — **(1) sumber SO gagal terbaca**: data kini berupa **workbook gabungan `.xlsb`** (mis. `01.1 CEK STOCK V2.xlsb`, sheet `1  DEVIASI WEEKLY`, semua resto dalam 1 sheet) padahal reader lama hanya mencari file per-resto `.xlsx` ber-sheet `REKAP MENTAH` → reader baru otomatis mendeteksi sheet ber-schema rekap mentah di file/format apa pun (`*.xlsb` kini ter-glob; NAMA RESTO diambil dari kolom; scan folder + RootPath; `pyxlsb` ditambahkan ke requirements), **(2) bug render vektorisasi v3.2**: kolom matrix `SO_H-2 … SO_H+2 / In / Out / BK` (Deviasi) dan `Saldo Awal / IN / OUT / BK / Saldo Kumulatif` (Laporan) tidak pernah diekstrak ke builder baris → selalu tampil `-` walau datanya ada → kini semua kolom terisi. Divalidasi terhadap sheet `DEVIASI GR` workbook user: 1404/1405 baris identik (2 sel beda = pivot cache Excel user yang stale, bukan app).
> **v3.8 — Rekap Selisih IN 1–31 + pivot lengkap 25•–31• + export PIVOT/SELISIH + impor TL dihapus**: **(1)** tab 📤 Rekap Selisih IN kini default periode **1–31 bulan BERJALAN saja** (tanpa bulan lalu); **(2) FIX kolom tanggal pivot "25, 26, lalu 1"** — data bulan lalu = tgl 25–31 (−25…−31) tetapi rentang lama `−26…31` memotong tgl 27–31 → kini default `−31…31`, kolom lengkap kronologis **25•, 26•, 27•, 28•, 29•, 30•, 31•, lalu 1, 2, 3…**; **(3)** Export Excel kini menyertakan sheet **PIVOT** (tab pertama) — mirror tab pivot "Mutasi Barang - New" user: row label kolom A = nama barang (bold) + jenis, kolom tanggal −25…−31 lalu 1…31, conditional formatting persis file user (`=AND($A8="1.SO",B8>A8)` bold hijau, `$A8="3.DEVIASI"` border bawah, `AND($A8="7.Selisih IN",B8<>0)` merah, nol = font putih, containsText `4.IN`/`5.BARANG MASUK` di kolom A, header tanggal < 0 biru muda); **(4)** tombol **💾 Export** di tab Rekap Selisih IN — rekap **per resto** dgn kolom Resto · Tanggal · Nama Barang · Kategori · Satuan · Hasil SO · **Sheet Barang Masuk** · **Kiriman HO** (42.05) · **Kiriman Supplier** (32.24) · **Pembelian by Resto** (99.01) · Selisih; **(5)** fitur **📥 Impor Hasil TL DIHAPUS** (user: tidak terlalu perlu).
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

### 6. Laporan Deviasi (v3.9.4 — 2 MODE via SegmentBar MODE)
- **⚖ Komparasi File Deviasi (default — BARU)**: klik **📂 Pilih File Deviasi…** → bandingkan file deviasi resmi (mis. `20.AGUSTUS 2026.xlsx`) dengan hitungan app per (Resto × Barang × Minggu) pada **kolom H minggunya: WEEK 1→7 · WEEK 2→14 · WEEK 3/4→25**. Kolom: ✓ · Resto · Nama Barang · Satuan · Minggu · H · **BOM/COM/DEVIASI/%TO BOM — File** · **BOM/COM/DEV TO BOM — App** (BOM App = Σ penjualan 22.05 tgl 1..H; COM App = Σ pemakaian) · **DEVIASI — App (Tab GR)** = SO_H − Sistem · **Selisih** (GR App − DEV File) · **Status** (MATCH / SELISIH / TIDAK ADA DI DATA APP / H TIDAK ADA DI DATA). Default hanya resto yang ada di data app — centang *"Tampilkan resto di luar data app"* untuk semua cabang (file sampel 340 resto). Double-click → popup detail di tanggal H minggu tsb. **(v3.9.7) FILTER MINGGU MENGIKUTI H**: hanya minggu yang MEMUAT H yang tampil (H 1–7 → WEEK 1 · 8–14 → WEEK 2 · 15–25 → WEEK 3/4 · 26–31 → WEEK 5 — STATUS BULAN dipakai utk filter; permintaan user "H aku input 7 maka hanya tampilkan week 1 aja"); chip H read-only + chip minggu aktif di-highlight; centang *"Tampilkan semua minggu"* utk semua minggu.
- **🚨 Anomali COM (v3.9.3 → v3.9.7 median ANTAR TANGGAL, ganti segmen)**: daftar **(Nama Barang × Resto)** dengan **pemakaian (COM) di kolom H** yang **minus** atau **lebih tinggi dari median com harian pasangan tsb** — v3.9.7 (koreksi user): median = **median com(t) tanggal 1..H milik pasangan itu sendiri** (pemakaian aktual harian di resto vs pola hariannya; BOM = pemakaian harian versi sistem), bukan antar resto. Kolom: ✓ · Nama Barang · Resto · Satuan · COM (H) · Median (1..H) · Selisih vs Median · Status (MINUS / > MEDIAN / MINUS + > MEDIAN). **Tanggal H diatur di tab 📦 Deviasi GR** (chip read-only — tabel ikut refresh otomatis saat H berubah).
- ✓ = masuk Follow Up (Komparasi: asal KOMPARASI; Anomali: asal LAPORAN-COM) · double-click → detail · klik judul kolom ⧩ = filter + sort.

### 7. Rincian PO (tab ketujuh)
- Tabel Rincian PO dengan filter Cabang PO & Status.
- Nomor # sebagai parent row (klik ▸ untuk expand).

---

## Perbaikan Bug v3.9.5 — Deep Audit (4 Agent Paralel)

Audit menyeluruh fitur terbaru (v3.9.3 Anomali COM + v3.9.4 Komparasi Deviasi) memakai 4 agent paralel (view komparasi / view laporan / integrasi app+widgets / runtime) dengan oracle numerik + GUI harness di Xvfb. Temuan: 0 P0, 2 P1, 7 P2, ~15 P3 — **semua diperbaiki**:

1. **RACE ✕ TUTUT FILE (P1)** — menutup file deviasi saat komparasi masih menghitung membuat hasil file lama di-render ulang. Fix: generation counter (`_render_gen`) + pembatalan batch insert + reset `_busy` di `done()`; job kedaluwarsa menjalankan refresh/file yang mengantre.
2. **KEBOCORAN GC (P1)** — `run_async` menjadwalkan poll pada widget pemilik; popup detail yang ditutup di tengah job → `gc.disable()` menempel seumur sesi. Fix: poll dijadwalkan pada root aplikasi (`_poll_host` naik rantai master).
3. **PARSE FILE DI THREAD (P2)** — file 9,4MB membekukan UI ±8 detik; kini parse+compute+join = satu job async dengan overlay.
4. **SALDO AWAL BASE com(1) (P2, 3 file bareng)** — pivot `_compute_com`, laporan `_compute_com_matrix`, komparasi `_compute_matrices`: base com di tanggal 1 = SA milik pair (baris SA ber-Tanggal=1), fallback SO(t-1), fallback 0. Pair tanpa data bulan lalu tak lagi dapat com(1) ≈ −SO(1) (minus palsu); GR·App == DEV·App aljabar persis.
5. **POPUP DETAIL (P2)** — nama barang file → resolve nama versi APP via `_pair_index` (popup memfilter exact).
6. **TAG PER-CELL + FILTER DI CLONE ⛶ (P2)** — `attach_clone_filters(on_after_filter=…)`; `apply_tree_row_filters(on_done=…)`; `apply_cell_tag` fallback per-iid yang masih ada (satu iid hilang dulu membatalkan seluruh chunk).
7. **FILTER "Selisih vs Median" (P2)** — mapping nama tampilan→kolom internal di `_col_values`.
8. **APPLY H RENDER DOBEL (P2)** — refresh eksplisit hanya bila H tidak berubah / view dirty.
9. **Lainnya (P3)**: duplikat lintas bulan dihitung+dilaporkan; scan sheet ke-2+; footer status = baris tampil (bukan global); filter reset saat file berganti; sort diantrekan saat busy; pane tersembunyi tak di-compute saat H berubah; initialdir komparasi ikut RootPath; `show_laporan_mode` sinkron SegmentBar; snapshot follow-up + kolom AKTIF/NON; `SharedTanggalH.unsubscribe()`; `-0,00%`→`0,00%`; Satuan NaN→`''`; dialog + `*.xlsb`; baris basi dibersihkan saat data kosong.

**Verifikasi**: 337/337 UI test × 2 run (25 check baru §23) + `test_mock` ALL PASS + ruff 0 error baru + oracle SA 3 view + smoke real-data 342.222 baris (tgl −31..31, parse async 8,2s dgn 740 pump = UI hidup, anomali 2.135 baris 0,4s, race & cache-invalidation bersih) + 3 screenshot VLM PASS.

## Fitur Baru v3.9.11 — Tuntas Sisa Temuan Audit + Repo Private

Eksekusi instruksi user **"kerjakan semua dan repo untuk pribadi aja"**: P0 D-11 (katalog risiko git dari audit v3.9.10) dieksekusi + semua sisa temuan P3 audit 2-b yang ditunda + 1 fix laten v3.9.10. Tidak ada formula bisnis / fingerprint / pipeline / kontrak export yang disentuh.

**P0 — keamanan data (D-11)**
- Repo GitHub `anandategarch/Stock-Monitoring` dijadikan **PRIVATE** via API (verifikasi ulang: `private: true`). Workbook produksi + objek `2205.xlsx` di git history tidak lagi dapat diakses publik; **BFG/rewrite history tidak diperlukan** (destruktif — mengubah semua hash commit). Workbook tetap ter-track sesuai kegunaan repo pribadi.

**Fix sisa audit 2-b**
| Fix | Masalah (v3.9.10) | Perilaku baru |
|---|---|---|
| B-21 | Sort via popup ↕ mengubah urutan tabel tanpa jejak kolom mana yang terurut | Heading kolom sort berpanah **↓ menurun / ↑ menaik**; panah kolom lama dibersihkan; ikon funnel (opsi `image`) tidak tersentuh |
| B-14 | Toggle filter di clone ⛶ mengembalikan urutan asli (rebuild dari cache urutan asli) | Sort terakhir (`tree._last_sort`) dijalankan ulang **sebelum** reapply tag per-cell — tag dipasang pada urutan final |
| B-09 | `sort_tree_by_column` reinsert hanya values+tags — tree berhirarki kehilangan anak (latent) | Jalur `tree.move` utk tree berhirarki (subtree + text #0 + open terjaga); jalur flat O(n) tetap + mempertahankan text #0/open |
| B-18 | Mirror kolom clone→source satu arah — hide kolom di tabel utama tidak tercermin di clone terbuka | **Dua arah**: colmgr clone terdaftar di source (`_mirror_backrefs`); apply() sumber mendorong ke semua clone; backref dilepas saat window clone ditutup |
| B-17 | Overlay pertama yang selesai me-reset cursor saat overlay kedua masih loading | Cursor "watch" **ber-refcount per toplevel** + klaim dilepas saat widget destroy |
| B-16 | `TableExpander.restore` iterasi maju — ≥2 target pack berturut di akhir terpasang TERBALIK | Iterasi **reverse** (benar utk semua kombinasi anchor after/before) |
| B-12 | `int(float("7.9"))` melantai pecahan senyap jadi 7 | Pecahan **ditolak** warning+revert (validated_tgl_entry semua view + `_on_tanggal_change` Selisih IN); "7.0" tetap diterima |
| B-11 | EmptyState frame center fixed 520×260 — konten terpotong di jendela sempit | Center **adaptif** (clamp maks 520×260, ikut event `<Configure>`) |

**+ Fix laten v3.9.10**: `import contextlib` di app.py — F821 (jalur gagal simpan config memakai `contextlib.suppress` tanpa import → NameError menggantikan dialog error).

**Verifikasi**: 514/514 UI test × 2 run stabil (492 v3.9.10 + **22 baru §26 — satu test per bug**) + test_mock ALL PASS × 2 + ruff **223 < baseline 224** (F821 hilang, 0 kelas error baru — S110/BLE001 baru dikonversi `contextlib.suppress` sesuai konvensi v3.9.10) + probe visual Xvfb (panah sort terlihat di heading, EmptyState mengecil di jendela 1020×640).

## Fitur Baru v3.9.10 — Deep Audit UI/UX Round 2 (37 Temuan → Fix)

Audit ulang menyeluruh kondisi v3.9.9 oleh 4 agen paralel (shell & navigasi / infrastruktur tabel / konsistensi 10 view / integritas data & race). Semua temuan terverifikasi dari kode diperbaiki **tanpa mengubah formula bisnis, fingerprint Follow Up, pipeline, atau kontrak export**.

**P1 — race & robustness**
| Fix | Masalah (v3.9.9) | Perilaku baru |
|---|---|---|
| A-01 | Stop → MULAI menjalankan 2 pipeline paralel & membatalkan Stop (`stop_event.clear` sebelum worker mati) | MULAI saat worker lama masih hidup → ditolak dengan pesan |
| D-01 | Cache worker berlabel identitas data BARU berisi hasil compute data LAMA (data basi senyap) | Identitas data/H di-capture sekali di awal compute (5 view) |
| C-02/D-02 | Rincian PO & popup detail tanpa `on_error` → view mati permanen setelah 1 exception | `_busy` di-reset + status error → refresh berikutnya tetap jalan |
| B-01 | Sort Rekap Selisih IN: parser default salah untuk format Indonesia | Parser `_parse_num_id` (pola deviasi/komparasi) |
| D-04 | File Excel terkunci/hilang di-skip senyap — status "SELESAI" polos | "SELESAI ⚠ N file Excel dilewati — lihat log" (amber) |

**P2 — tabel & shell**
- **B-02/B-03**: tag minus-merah per-cell dipasang ulang setelah filter/sort di clone ⛶ (Deviasi/Pareto/Selisih IN/Pivot + popup detail).
- **B-04**: `bind add="+"` — auto-fit double-click tepi kolom & menu kolom hidup lagi (semua tabel + clone).
- **B-05/B-13/B-19**: popup filter >3000 nilai — pencarian membuat checkbox LAZY; uncheck tidak lagi menyembunyikan nilai di luar cap; nilai numerik urut numerik; pencarian reset saat popup dibuka ulang.
- **B-06/B-07/B-08/B-20**: gc_shield pakai Lock; filter/sort clone membatalkan batch copy awal; sort saat render batch di-antre (3 view); BaseException tidak menempel busy/shield.
- **D-03**: render Follow Up beruntun (toggle ✓ cepat) membatalkan batch lama — dulu baris bisa duplikat/terpotong senyap.
- **A-02/B-10**: tombol disabled tampak DIM (abu) + hover tidak menimpa warna dim.
- **A-03**: DPI-awareness Windows 125%/150% (`SetProcessDpiAwareness` — no-op di Linux).
- **A-04**: Ctrl+Tab / Ctrl+Shift+Tab navigasi antar-tab.
- **A-11**: routing tab-change berbasis widget (bukan index angka).
- **H-1 (terkonfirmasi)**: tab strip ±1280px meluap di jendela 1020px → label tanpa spasi ganda + padding 12 → **10/10 tab terjangkau** (probe Xvfb); `WINDOW_MIN` 640→700 (h-scrollbar selalu terlihat).

**P3 — konsistensi**
C-03 format Indonesia di Rincian PO & popup ("1.234,5") · C-04 minus merah per-cell Selisih IN · C-06 sisa frasa instruksi dipangkas · C-10 footer "baris" + fmt Indonesia · C-07/C-08 DeviasiView unsubscribe-H + pane tersembunyi cukup `_dirty` · D-05/D-06 tulis atomik config.json & komparasi_last.json · A-06 KPI Pareto font 9 · A-07/A-09 docstring & token warna.

**Verifikasi**: 492/492 UI test (437 lama + **55 baru §25 — satu test per bug**, termasuk oracle filter-lazy, oracle neg-cells, guard-restart dengan thread dummy, piksel-dim, rantai-binding) + test_mock ALL PASS + ruff 224 < baseline 261 + VLM visual 2 batch + probe programatik.

## Fitur Baru v3.9.8 — UI Clean (Hapus Semua Teks Instruksi)

Permintaan user: *"tulisan tulisan seperti: Filter nama barang -> klik header kolom nama
barang (Ikon corong) di tabel … dan kata kata atau kalimat diseluruh aplikasi
python hapus semua biar clean tanpa teks teks gak penting".*

UI kini bersih — hanya konten fungsional + data. Yang dihapus:

| Bagian | Dihapus |
|---|---|
| Toolbar | tombol **❓ Bantuan** + seluruh window panduan (`_HELP_TEXT`/`_show_help`) |
| Kartu Filter/aksi | semua **subtitle penjelas** (mis. "Filter Nama Barang → klik header kolom (ikon corong ⧩) di tabel") di 7 view |
| Footer tabel | hint **"🖱 Double-click baris → detail · ✓ = Follow Up · klik judul kolom ⧩ = filter + sort"** dst. (termasuk window ⛶ Layar Penuh) |
| Hover | **tooltip** — class `ToolTip` + `add_tooltip` dihapus dari `widgets.py` (±45 panggilan di 10 file) |
| Empty state | subtitle "Jalankan pipeline untuk memuat…" (judul + CTA tetap) |
| Tab Config/Proses | subtitle "Ubah RootPath sesuai…", "Pipeline mode: FULL…", "Baca seluruh export → …", "stdout pipeline real-time…" |
| Dialog export IN | pertanyaan "Tambahkan kolom hasil audit…?" (checkbox + tombol tetap) |

**Yang tetap ada** (bukan teks instruksi — data/fungsional): label input
(TANGGAL H / RESTO / CABANG PO / STATUS), tombol, chip nilai (H, minggu),
**footer status berisi hitungan data** (n baris · minus · > median ·
Minggu WEEK X cut-off H N · MATCH/SELISIH), **legenda CEK & warna**, KPI
pipeline, pesan error/pesan jujur, log proses.

## Fitur Baru v3.9.7 — Median Antar Tanggal · Filter Minggu Komparasi

### 1. Tab 🚨 Anomali COM — median pembanding ANTAR TANGGAL (koreksi user)
Koreksi user: *"harusnya antar tanggal. com itu pemakaian aktual harian di resto sementara bom itu pemakaian harian di sistem."*
- **Median kini = median com(t) tanggal 1..H milik pasangan (Nama Barang × Resto) itu sendiri** — pemakaian COM di tanggal H dibandingkan dengan pola pemakaian harian typikal pasangan tsb (bukan lagi median antar resto per barang).
- Heading kolom Median dinamis **"Median (1..H)"**; footer menjelaskan "median antar tanggal (1..H)".
- Konsekuensi alami: barang yang sama di resto berbeda kini punya **median berbeda** (masing-masing mengikuti pola hariannya) — terbukti di real-data: 23/23 barang multi-resto median-nya beda.
- Baris tetap: COM di kolom H minus (< 0) atau lebih tinggi dari median pasangannya → Status MINUS / > MEDIAN / MINUS + > MEDIAN; snapshot follow-up tetap (SO=COM, Sistem=median, Deviasi=selisih).

### 2. Tab ⚖ Komparasi — filter minggu mengikuti TANGGAL H (STATUS BULAN untuk filter)
Permintaan user: *"itu berguna buat filter. misal H aku input 7 maka hanya tampilkan week 1 aja."*
- Komparasi kini **berlangganan TANGGAL H bersama** (chip read-only — diatur di tab 📦 Deviasi GR): hanya baris **minggu yang MEMUAT H** yang ditampilkan:
  | H input | Minggu tampil | Cut-off |
  |---|---|---|
  | 1–7 | WEEK 1 | 7 |
  | 8–14 | WEEK 2 | 14 |
  | 15–25 | WEEK 3 / WEEK 4 | 25 |
  | 26–31 | WEEK 5 | 31 |
- **Chip minggu aktif di-highlight teal**, label "→ minggu: WEEK X" di kartu filter, footer berprefiks "Minggu WEEK X (cut-off H N)".
- File tanpa minggu tsb → **0 baris + pesan jujur** (daftar minggu yang ada di file + petunjuk).
- Centang **"Tampilkan semua minggu"** untuk melihat semua minggu (perilaku v3.9.4–v3.9.6).
- H berubah di tab 📦 Deviasi GR → tabel komparasi difilter ulang otomatis (pane tersembunyi → ditandai dirty, di-refresh saat dibuka).

### 3. FIX ikutan — flag _dirty basi (tabel basi)
`load_data` saat pane **terlihat** me-render tabel tapi flag `_dirty` tetap True → listener H berikutnya menganggap "belum pernah dirender" & **skip refresh** (tabel komparasi masih menampilkan minggu lama). Kini `_dirty` di-clear saat refresh berjalan (komparasi + laporan).

## Fitur Baru v3.9.6 — Kategori Deviasi · Pembanding SO Tgl 1 · Format Follow Up

### 1. Kategori Deviasi di tab 📦 Deviasi GR & 🧩 Deviasi PCS

5 kolom baru setelah **Rank** (nama & rumus mirror sheet `DEVIASI GR`/`DEVIASI PCS`
workbook asli `01.1 CEK STOCK V2.xlsb` — formula diverifikasi nilai-per-nilai
dari sheet tsb):

| Kolom | Rumus | Keterangan |
|---|---|---|
| **Max Deviasi** | max \|Deviasi\| per barang (antar resto) | pembanding cepat: seberapa ekstrem resto ini vs resto lain |
| **ACR** | Σ penjualan 9.OUT (22.05) tgl 1..H ÷ H | *average consumption rate* — rata-rata pemakaian harian |
| **Total ACR** | Σ penjualan 9.OUT tgl 1..H | BOM per barang×resto (pemakaian teoretis) |
| **Dev to BOM%** | Deviasi ÷ Total ACR | = "Loss Surplus to BOM" sheet Follow UP — > 100% = rugi melebihi pemakaian teoretis |
| **Stok Seharusnya** | SO(H−1) − ACR | perkiraan stok hari H bila pemakaian normal |

Plus **kategori CEK ke-5 "ACR to BOM"**: `|Deviasi| > Total ACR > 0` → selisih
stok melebihi seluruh pemakaian teoretis sebulan → pasti salah (tag ungu;
melengkapi port formula LET Excel yang sejak v3.2 baru 4 dari 5 kondisi —
"ACR butuh BOM, TODO"). Sort kolom numerik kini memakai parser angka
Indonesia (`1.234.567` / `(5,00)%` terurut benar).

### 2. Tab 📤 Rekap Selisih IN — pembanding SO tanggal 1 = SO bulan lalu

Baris audit per grup kini diurut **kronologis**: bulan lalu (Tanggal −25..−31)
urut hari naik 25•→31•, lalu bulan berjalan 1..31. Sort numerik lama
membalik urutan bulan lalu (−31 tampil pertama) sehingga baris tepat sebelum
tanggal 1 = Tanggal −25 — delta SO aturan **"SO Naik" (VALID Sistem Masuk)**
di tanggal 1 membanding SO tgl 25• bulan lalu, **bukan SO terakhir bulan
lalu (31•)**. Kini pembanding tanggal 1 = **SO bulan lalu terakhir** —
sesuai permintaan "jika tanggal 1 pembanding SO nya SO bulan lalu".

### 3. Tab ☑ Follow Up — format file sample

Tabel & export kini mengikuti sheet **Follow UP** workbook asli:

```
✓ · Resto · Nama Barang · [SO tgl H-2 · H-1 · H · H+1 · H+2 — heading ANGKA
TANGGAL (H=25 → 23..27)] · Sistem · Deviasi · Loss Surplus to BOM ·
Keterangan · SO · DEVIASI · Selisih · Selisih Deviasi · Cek FU · PIC ·
Asal · Status TL · Ditambahkan
```

- Kolom tanggal SO = snapshot saat baris dicentang (baris dari Laporan/
  Komparasi yang tak punya nilai per tanggal tampil "-").
- Kolom kerja **Selisih · Selisih Deviasi · Cek FU** = diisi petugas
  (dibawa resolved store bila sudah ada).
- Snapshot lama (v3.9.5 dan sebelumnya) tetap dimuat; fingerprint tidak
  berubah → `followup.json` lama kompatibel.

## Fitur Baru v3.9.4 — Komparasi File Deviasi vs Tab Deviasi GR

Permintaan user: *"Di file sampel kan ada Dev to bom ini kok gak ada ya? Padahal data udah lengkap 2205 itu bom. Aku barusan upload file deviasi. Nah aku mau compare file deviasi itu dengan yang deviasi di Tab deviasi GR terus coba cek kolom status week 1 itu sama dengan 7 week 2 = 14 dan week = 25. Itu buat kolom h."*

Tab 📋 **Laporan Deviasi** kini punya **2 MODE** (SegmentBar `MODE` di atas tab):
**⚖ Komparasi File Deviasi** (BARU — default) dan **🚨 Anomali COM (H)** (v3.9.3 —
tetap ada, tinggal ganti segmen; v3.9.1 ada tombol bantu ganti mode
`app.show_laporan_mode(idx)` untuk otomasi).

### ⚖ Mode Komparasi File Deviasi
1. **Pilih file** — tombol 📂 *Pilih File Deviasi…* (path terakhir diingat di
   `komparasi_last.json` → dialog terbuka di folder yang sama; tombol ↻ *Muat
   Ulang File* membaca ulang). Kolom file yang dibaca (nama fleksibel —
   kapital/spasi diabaikan): **STATUS BULAN · RESTO · NAMA BAHAN · QTY BOM ·
   QTY COM · QTY DEVIASI · % QTY DEVIASI TO BOM** (opsional: Satuan, BULAN).
   Kolom wajib hilang → pesan error jelas beserta daftar kolom file.
2. **Minggu → Kolom H** (permintaan user): **WEEK 1 → H 7 · WEEK 2 → H 14 ·
   WEEK 3/WEEK 4 → H 25**; minggu lain → 7×n (maks 31). Chip pemetaan tampil
   di kartu Filter sesuai minggu yang ada di file. Terverifikasi dari file
   sampel `20.AGUSTUS 2026.xlsx` (40.739 baris, 340 resto, WEEK 1/2/4):
   minggu file = **cut-off KUMULATIF dari tanggal 1** (WEEK 2 ≈ 2× WEEK 1) —
   konsisten dgn semantik Tanggal H.
3. **Sisi app (tanpa file tambahan — "data udah lengkap, 2205 itu BOM")**:
   - **BOM — App** = Σ penjualan 22.05 (JENIS `9.OUT`) tgl 1..H — konvensi
     file (minus = pemakaian) supaya kolom berdampingan langsung banding.
   - **COM — App** = Σ pemakaian `com(t)` tgl 1..H; `com(t) = SO(t-1) +
     IN(t) − BK(t) − SO(t)`, tanggal pertama memakai SALDO AWAL (formula
     identik baris 6.PEMAKAIAN (COM) pivot & tab 🚨 Anomali COM).
   - **DEV TO BOM — App** = COM App − BOM App (formula identik file).
   - **DEVIASI — App (Tab GR)** = `SO_H − Sistem_H` — PERSIS kolom *Deviasi*
     tab 📦 Deviasi GR pada H minggu tsb. Secara aljabar
     `GR App = ΣOUT − SA − ΣIN + ΣBK + SO_H = out_cum − com_cum = DEV App`
     — dua jalur hitung yang seharusnya sama (selisih internal langsung
     terlihat bila data tidak konsisten).
4. **Verdict** — **Selisih** = GR App − DEV File; **Status**: `MATCH` (|selisih|
   ≤ 1 + 0,01%·|DEV File|) / `SELISIH` / `TIDAK ADA DI DATA APP` (pasangan
   barang-resto tidak ada di data) / `H TIDAK ADA DI DATA` (tanggal H di luar
   rentang data app — mis. WEEK 5→31 saat data s/d 25). Footer menghitung
   semuanya + label BULAN file (reminder: pastikan bulan file = bulan data
   app).
5. **Resto otomatis dicocokkan** — file memakai kode cabang (`1041.BDGUKU`,
   `B.1001.MLGPAR`) → segmen setelah titik terakhir (`BDGUKU`, `MLGPAR`) →
   nama barang upper+strip. Default hanya **resto yang ada di data app**
   (mis. 20 resto cek stock) — centang *Tampilkan resto di luar data app*
   untuk semua cabang (file sampel: 340 resto; 37.321 baris disembunyikan).
6. **Infrastruktur tabel utuh** — ✓ follow-up (asal **KOMPARASI**: SO = GR
   App, Sistem = DEV File, Deviasi = selisih, CEK = status, + minggu),
   filter header ⧩ semua kolom, sort parser angka Indonesia, ⛶ Layar Penuh,
   ⤢ Perbesar Tabel, ◱ Kolom, ↔ Auto-Fit, minus **merah PER CELL** di semua
   kolom angka, **sel Status hijau (MATCH) / amber (SELISIH) / merah**,
   compute async + FIX B-01 (view tidak mati setelah error), double-click →
   popup detail difilter barang + resto (kode app) + tanggal H minggu.

### ✅ Test
337/337 UI test (279 v3.9.3 + 33 v3.9.4 + **25 v3.9.5 audit-fix** — mode switcher, parsing file format
asli, pemetaan minggu→H, GR App = SO_H−Sistem eksak (49/113/150 dari mock
deterministik), BOM/COM/DEV App konvensi file, MATCH/SELISIH/TIDAK ADA DI
DATA APP/H TIDAK ADA, opsi semua resto, minus per-cell + sel Status berwarna
+ dipasang ulang setelah sort, filter header Status, ✓ follow-up KOMPARASI,
tutup file) × 2 run stabil + mock pipeline PASS; ruff 0 error baru (app.py
13 = 13 baseline, test 23 = 23 baseline); smoke real-data: file
`20.AGUSTUS 2026.xlsx` (40.739 baris × 340 resto) vs matriks app dari sheet
SO BULAN INI/Barang Masuk/Barang Keluar (101.697 baris) → 3.418 baris
komparasi (3 MATCH + 3.383 SELISIH — beda bulan Sept vs Agust sesuai
harapan) dalam 8,7 detik.

---

## Fitur Baru v3.9.3 — Laporan Deviasi: Daftar Anomali Pemakaian (COM)

Permintaan user: *"hapus isi data pada tab laporan deviasi dan sementara ganti dengan list nama barang dan resto yang pemakaian (com) nya minus atau lebih tinggi dari median pada pada kolom H"*.

Isi tab 📋 **Laporan Deviasi** DIGANTI (sementara — tabel *Audit Harian 6 Status* lama tersimpan di git history, commit `e20141a`, siap dipulihkan bila dibutuhkan). Yang tampil sekarang:

- **Baris = (Nama Barang × Nama Resto)** dengan nilai **PEMAKAIAN (COM) pada kolom H** yang **MINUS (< 0)** atau **LEBIH TINGGI dari MEDIAN barang tersebut** — median dihitung **antar resto untuk barang yang sama, pada kolom H** (identifikasi resto pemakai-abnormal per barang).
- **Kolom**: ✓ follow-up · Nama Barang · Resto · Satuan · **COM** (heading dinamis `COM (H=25)`) · **Median** · **Selisih vs Median** · **Status** (`MINUS` / `> MEDIAN` / `MINUS + > MEDIAN` — dua kondisi bisa sekaligus, mis. com −10 vs median −20).
- **Formula COM** sama persis dgn baris `6.PEMAKAIAN (COM)` tab 📊 Pivot mode Tanggal (port M code): `com(t) = SO(t-1) + IN(t) − BK(t) − SO(t)`, tanggal PERTAMA memakai SALDO AWAL. Diverifikasi oracle: 286 nilai dibandingkan vs `PivotTableView._compute_com` — **0 mismatch** (termasuk tanggal negatif bulan lalu & barang 1-resto).
- **TANGGAL H bersama** (SharedTanggalH v3.9): chip read-only + **auto-refresh saat H di-apply/reset di tab 📦 Deviasi GR** — tanpa double input. Bila H tidak ada di data: pesan jelas "Kolom H=99 tidak ada di data — tanggal tersedia …".
- **Matriks COM di-cache & vektorisasi**: pivot (Barang×Resto×JENIS) × tanggal dibangun SEKALI per data (H-independen — ganti H hanya memilih kolom + median); real-data 215.950 baris → 791 anomali di H=25 dalam hitungan detik.
- **Minus merah PER CELL** (lanjutan v3.9.2 — hanya sel COM bernilai negatif) + **sel Status** diberi warna per-cell (MINUS = merah, > MEDIAN = amber); angka format Indonesia (1.234.567, negatif kurung); **parser sort numerik Indonesia** (`_parse_num_id` — "1.234" = 1234, "(1.234)" = −1234).
- **Infrastruktur tabel utuh**: filter header ⧩ semua kolom, sort linear, ⛶ Layar Penuh (tag per-cell dipasang ulang di clone), ⤢ Perbesar Tabel, ◱ Kolom, ↔ Auto-Fit, loading overlay + compute async.
- **✓ follow-up tetap jalan** — snapshot memakai asal **LAPORAN-COM** dengan pemetaan kolom Follow Up: **SO = nilai COM**, **Sistem = median** (pembanding), **Deviasi = selisih**, **CEK = status**.

### ✅ Test
279/279 UI test (256 v3.9.2 + **23 baru**: skema kolom baru, data deterministik median/flag/status 3-barang × 2/3-resto termasuk kasus MINUS + > MEDIAN, minus per-cell + sel status, H-shared chip/heading/auto-refresh dari tab GR, filter header Status/Nama Barang, snapshot follow-up LAPORAN-COM) + mock pipeline PASS; ruff 0 error baru (8 = 8 baseline file); 4 screenshot dicek visual (VLM) memakai data real 01.1 CEK STOCK V2.xlsb (20 resto × ±320 barang).

---

## Fitur Baru v3.9 — Shared H · Export + Audit · Rincian PO Ringkas · Style Waste

### 1. TANGGAL H dibagi 2 tab — cukup input 1× (tidak double input)
Permintaan user: *"kolom apply H atau input H cukup 1 tab aja dan berlaku di 2 tab yang berkaitan yaitu Deviasi Gr dan Deviasi PCS sehingga tidak double input"*.
- Tab 📦 **Deviasi GR** = satu-satunya pemegang input **TANGGAL H** + tombol **Apply H** (dulu tiap tab punya input sendiri — harus input 2× dan nilainya bisa beda).
- Tab 🧩 **Deviasi PCS** menampilkan **chip nilai H read-only** (ikut berubah saat H di-apply di tab GR) + tabelnya **di-refresh otomatis** — pivot tetap dihitung 1× via `SharedPivotCache` yang kini **thread-safe (lock)**: saat Apply H kedua view refresh bersamaan, hanya 1 thread yang menghitung pivot, keduanya menerima objek yang sama.
- Subtitle tiap tab menjelaskan arah sinkronisasi (PCS: "Tanggal H diatur di tab 📦 Deviasi GR").

### 2. Export Rekap Selisih IN + opsi kolom hasil audit
Permintaan user: *"waktu ekspor tambahin hasil auditnya aja tapi ada opsi buat tambahin kolom tersebut atau tidak"*.
- Klik **💾 Export** di tab 📤 Rekap Selisih IN → muncul **dialog opsi**: ☑ Hasil Audit · ☑ Saldo · ☑ Catatan Audit (semua default tercentang; centang/batal sesuai kebutuhan — tombol **Tanpa Kolom Audit** untuk export murni rekap v3.8).
- Kolom audit ditambahkan **setelah kolom Selisih**; nilai audit diambil dari data penuh (konsisten dgn kolom di tabel UI, tidak terpotong rentang tampilan).
- `build_selisih_export_df(base, tgl_start, tgl_end, audit_cols=None)` — `audit_cols` divalidasi (nama tak dikenal diabaikan); roundtrip file + sebaris nilai dicek test.

### 3. Rincian PO disederhanakan (mudah dibaca)
Permintaan user: *"tampilan rincian PO apakah bisa lebih dipermudah lagi biar mudah dibaca?"*.
- **Baris TEAL (induk PO)** memuat SEMUA info PO **SEKALI**: Nomor # · Tanggal · Pemasok · Status Pesanan · Keterangan PO · "▸ N item" · "Total: X".
- **Baris putih (anak)** hanya item: Nama Barang · Satuan · Kuantitas — dulu setiap baris anak MENGULANG Tanggal/Pemasok/Tgl-Jam yang sama (tabel penuh & sulit dipindai).
- Kolom **Tgl/Jam Pembuatan** (metadata PO) pindah ke baris induk dan **tersembunyi default** — tampilkan lewat tombol ◱ Kolom / klik kanan judul kolom. Baris GRAND TOTAL menyimpan N PO + total kuantitas.

### 4. Style ala repo Waste (tombol filter, perbesar tabel, dll)
Permintaan user: *"semua style aplikasi ini bisa gak tiru style repo Waste mulai dari tombol filternya, perbesar tabelnya dan lain lain"* (palet warna sudah identik sejak v3.0 — yang disamakan kini detail komponennya):
- **Corong filter header ala Waste**: terisi **MERAH** (#dc2626) saat kolom terfilter; idle = isi terang #cbd5e1 + outline #64748b (bukan lagi teal kecil); ikon 11×8 → 13×11 px (2 varian di-cache).
- **Tabel diperbesar** (theme.py): font Treeview 9 → **10**, rowheight 26 → **30**, heading font **10 bold** + padding (8,8) + latar #f8fafc — baris terasa lapang seperti tabel Waste (13px + padding 3/8).
- **Tombol ⤢ Perbesar Tabel** (class `TableExpander`) di semua tab tabel — menyembunyikan kartu Filter/KPI/judul/legenda secara IN-PLACE supaya tabel memakai seluruh tinggi tab (klik lagi ⤡ *Tampilkan Filter & KPI* untuk mengembalikan; urutan layout asli dipulihkan via anchor pack/grid_remove).
- **⛶ Layar Penuh** (dulu "⛶ Perbesar") = window besar terpisah — penamaan sama dengan Waste.
- Padding tombol ghost (14,7) + tab notebook (18,9) — lebih lapang ala QSS Waste.

### 5. Crash fix laten (CPython 3.12 + Tk) + cache pivot thread-safe
- **GC shield** (`gc_shield_acquire`/`gc_shield_release`): GC otomatis kini dimatikan **selama thread worker hidup** (bukan hanya saat `work()`) — fase *thread-exit* (`threading._delete`) adalah jendela crash: GC di situ bisa mem-finalisasi `tk.Variable` sisa popup/clone window yang sudah ditutup (destructor memanggil Tcl dari thread bukan-main → segfault heap, terbukti empiris saat 2 view di-refresh bersamaan oleh Apply H). GC dinyalakan kembali dari MAIN thread setelah thread benar-benar mati (cek `is_alive` + retry 15ms). Pipeline thread ikut dilindungi.
- **`SharedPivotCache` + lock**: tanpa lock, GR & PCS yang refresh bersamaan sama-sama cache-miss → pivot dihitung 2× dan entry tertimpa objek berbeda; kini get+compute+put dalam satu lock → 1 komputasi, objek sama.

### ✅ Test
230/230 UI test (198 v3.8 + **32 baru**: shared-H 6 check, rincian ringkas 7, export audit 9, style/expander 10) + mock pipeline PASS; ruff 0 error baru; 10 screenshot fitur baru diperiksa visual (VLM).

---

## Fitur Baru v3.8 — Rekap Selisih IN 1–31 · Pivot 25•–31• · Export PIVOT + Selisih per Resto

### 1. Rekap Selisih IN — periode default 1–31 (bulan berjalan saja)
Permintaan user: *"untuk rekap selisih in hanya periode 1-31 aja gak perlu bulan lalu"*.
Default rentang TANGGAL di tab 📤 Rekap Selisih IN kini `1` s/d `31` (dulu `-26` s/d `31`); Reset Filter ikut kembali ke 1–31; angka negatif tetap bisa diketik bila suatu saat perlu. Filter hanya menyembunyikan baris — saldo kumulatif & status audit tetap dihitung dari data penuh.

### 2. FIX kolom tanggal pivot "25, 26, lalu 1" → 25•–31• lengkap
Permintaan user: *"Tanggal di tab pivot tabel matrix tanggal kenapa dari 25,26 terus 1 ya? harusnya 25,26,27,28,29,30,31 baru kemudian 1,2,3…"*. **Akar masalah**: data bulan lalu mencakup tgl **25–31** (sheet `SO BULAN LALU` → Tanggal −25 s/d −31), tetapi rentang default lama `-26…31` **memotong tgl 27–31** — kolom bulan lalu yang lolos hanya 25• dan 26•, lalu loncat ke 1. Kini default `−31…31` (pivot + Reset): kolom tanggal lengkap urut kronologis **25•, 26•, 27•, 28•, 29•, 30•, 31•, lalu 1, 2, 3…** (dengan data asli: 38 kolom tanggal, 176 barang — kolom tetap data-driven, tanggal tanpa data tidak dibuat).

### 3. Export Excel + sheet PIVOT (mirror tab pivot "Mutasi Barang - New")
Tombol 💾 Export Excel kini menulis sheet **PIVOT sebagai tab pertama**, meniru tab pivot di file "Mutasi Barang - New" milik user (struktur + conditional formatting dibaca langsung dari XML file tsb):
- **Layout identik**: baris 1–3 filter `NAMA RESTO / SOURCE KIRIMAN / KATEGORI = (All)` · baris 5 `Sum of NILAI | Column Labels` · baris 6 `Row Labels` + kolom tanggal **−25…−31 lalu 1…31** (numerik, urut kronologis) · baris 7+ kolom A = row label **nama barang (bold) + jenis**, nilai = Sum of NILAI (semua resto = (All)).
- **Conditional formatting persis file user**: `=AND($A8="1.SO",B8>A8)` → font bold hijau 00B050 · `$A8="3.DEVIASI"` → border bawah tipis · `=AND($A8="7.Selisih IN",B8<>0)` → bold merah + fill FFC9C9 · `cellIs = 0` → font putih (nol "tak terlihat", trik file user) · kolom A containsText `4.IN` → 9C5700/FFEB9C dan `5.BARANG MASUK` → 006100/C6EFCE · header tanggal `< 0` → bold + fill biru muda (bulan lalu). Catatan: file lama memakai `6.Selisih IN` (penomoran pra-v3.4); rumus disesuaikan ke `7.Selisih IN` — 5 rumus lain identik karakter-per-karakter, warna dxf diambil dari file user.
- Modul baru `src/ui/export_sheets.py` (pure pandas + openpyxl, thread-safe).

### 4. Tombol 💾 Export di tab Rekap Selisih IN — rekap PER RESTO
Permintaan user: *"export bagian tab selisih IN per resto"* dengan kolom: **Resto · Tanggal · Nama Barang · Kategori · Satuan · Hasil SO · Sheet Barang Masuk · Kiriman HO · Kiriman Supplier · Pembelian by Resto · Selisih** (rename dari user: Barang masuk → *Sheet Barang Masuk*; 4205 → *Kiriman HO*; 3224 → *Kiriman Supplier*; 9901 → *Pembelian by Resto*). Semua baris dalam rentang tanggal aktif (default 1–31), urut Resto → Tanggal → Nama Barang; Hasil SO kosong tetap kosong (bukan 0); sheet `Selisih IN per Resto` (header bold + freeze + autofilter). Tervalidasi real-data 68.098 baris: Kiriman HO/Supplier/Pembelian == rincian dokumen in_detail asli (401 sampel acak) dan == kolom IN.

### 5. 📥 Impor Hasil TL DIHAPUS
Permintaan user: *"hapus import hasil TL gak terlalu perlu"* — tombol + `FollowUpStore.import_workbook()` dihapus dari tab ☑ Follow Up. Export TL (kolom PIC/KATEGORI MASALAH/TINDAKAN) tetap; status Selesai/PIC yang sudah tersimpan sebelumnya tetap tampil.

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
- **Toolbar gelap** (slate-900) — judul aplikasi, badge versi, aksi cepat `💾 Export Excel`
- **7 tab ber-ikon**: ⚙️ Config · 🚀 Proses · 📊 Pivot Table · 📦 Deviasi GR · 🧩 Deviasi PCS · 📋 Laporan Deviasi · 🛒 Rincian PO
- **Status bar** global — indikator status pipeline (● SIAP / MENJALANKAN / SELESAI / ERROR) + ringkasan rows
- **Empty state** — setiap tab data menampilkan placeholder + tombol CTA "🚀 Jalankan Pipeline" saat belum ada data (auto berganti menjadi tabel saat data termuat)

Komponen inti (`src/ui/theme.py` + `src/ui/widgets.py`):
| Komponen | Fungsi |
|---|---|
| `Card` | kartu putih + border slate, judul opsional |
| `KpiCard` / `KpiRow` | kartu metrik (label kecil, angka besar, aksen warna kiri) |
| `AccentButton` | tombol teal solid (aksi utama) — MULAI PROSES, Simpan Config |
| `DangerButton` | tombol putih teks merah — Stop |
| `EmptyState` | placeholder data kosong + CTA |
| `make_log_console` | konsol log gelap ala terminal (#0b1220 + monospace) |
| `StatusDot` | titik warna status di status bar |

Palet: `#f1f5f9` (bg) · `#ffffff` (kartu) · `#0f172a` (toolbar/teks judul) · `#0f766e` (aksen teal) · status: merah/oranye/amber/hijau. Font otomatis resolve: Segoe UI (Windows) → Noto Sans → DejaVu Sans.

Fitur UX per tab:
- **Proses** — 4 KPI live (status pipeline, waktu berjalan, rows Append1, rows Rincian PO) + progress bar + konsol log gelap
- **Deviasi GR/PCS** — kolom ✓ follow-up + legenda warna CEK; ringkasan (baris · total |Deviasi| · anomali CEK) di status footer *(v3.2: KPI row di atas tabel dihapus supaya tabel besar)*
- **Laporan Deviasi** — kolom ✓ follow-up + filter status via combo STATUS; distribusi status di status footer *(v3.2: 6 kartu KPI dihapus)*
- **Follow Up** *(v3.2)* — tabel snapshot baris tercentang + Export Excel / Impor Hasil TL / Kosongkan
- **Rekap Selisih IN** *(v3.4)* — rekap IN (Accurate) vs Barang Masuk + drill-down rincian dokumen 42.05/32.24/99.01 + nomor
- **Semua tabel** — zebra rows, sort kolom (klik header), double-click baris → popup detail source data (header gelap, centered modal, Esc untuk tutup), **lebar kolom bisa di-adjust** *(v3.4: drag tepi judul / double-click tepi = auto-fit / tombol ↔ Auto-Fit)*
- Popup otomatis **ter-center** di parent

---

## Struktur Folder

```
stock-monitoring-python/
├── MULAI.bat / SETUP.bat       # entry point Windows
├── config.json                 # RootPath + Folders + Sheets
├── requirements.txt
├── test_mock.py                # test pipeline end-to-end (mock Accurate export)
├── test_ui_redesign.py         # test UI v3.9.3 (279 check — + daftar anomali COM di Laporan Deviasi)
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
        ├── pivot_view.py       # tab Pivot Table (per resto default; default -31..31)
        ├── deviasi_view.py     # tab Deviasi GR & PCS (vektorisasi numpy + kolom ✓)
        ├── laporan_deviasi_view.py  # tab Laporan Deviasi (np.select + kolom ✓)
        ├── in_selisih_view.py  # (v3.4→v3.8) tab 📤 Rekap Selisih IN + audit + 💾 Export per resto (default 1-31)
        ├── rincian_po_view.py  # tab Rincian PO
        ├── export_sheets.py    # (v3.8) sheet PIVOT (CF ala file user) + sheet Selisih IN per resto
        └── details_popup.py    # popup detail source rows (copy Nomor/PO)
```

---

## Testing

```
python test_mock.py          # pipeline end-to-end dgn mock data Accurate
python test_ui_redesign.py   # UI v3.9.3: 279 check (jalankan di bawah Xvfb di Linux)
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
- Popup detail: header gelap, centered modal, Esc untuk tutup.
- Tooltip hover untuk kontrol penting; legenda warna CEK & metric.
- **Pipeline, logika pivot/deviasi/audit/CEK, dan semua perilaku data 100% dipertahankan** (hanya lapisan UI yang diganti).
- Fix pre-existing: `test_mock.py` kini konsisten dengan pipeline pasca-refactor hapus PI/Konversi + sumber IN 9901 (mock 9901 + folder `Data9901` ditambahkan).

### v2.1.1 — freeze fix + SettingWithCopyWarning fix
### v2.1.0 — LAPORAN DEVIASI tab + deep-audit fixes
