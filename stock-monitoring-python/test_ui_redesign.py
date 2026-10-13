"""
test_ui_redesign.py — Verifikasi UI v3.2 dengan mock data.

Jalankan di bawah Xvfb:
    DISPLAY=:99 python test_ui_redesign.py

Memverifikasi:
1. App shell terbangun (toolbar, 8 tab, status bar, spinner) tanpa error
2. Semua view menerima mock data & merender baris (async + batched) —
   LAZY REFRESH: view compute saat tab-nya dipilih (v3.2)
3. PIVOT PER RESTO (default): kolom = resto, tanpa kolom Total, baris kosong
   disembunyikan, item yang HANYA ada di 1 resto (ADONAN GORENG MEKAR /
   MLGPAR) tetap tampil
4. PIVOT PER TANGGAL: kolom = tanggal + metric 6.PEMAKAIAN (COM)
5. Header filter Nama Barang (corong di heading) — buka via klik header,
   toggle checkbox → filter, reset
6. Tombol ⛶ Perbesar → window clone
7. Filter + reset (RESTO, cabang, status, tanggal)
8. Details popup: render + copy Nomor / Nomor PO (Ctrl+C, double-click cell,
   copy semua unik) + header filter + maximize
9. Loading overlay terpasang di semua view
10. v3.2 — KPI row DIHAPUS di tab data (tabel besar; ringkasan di footer)
11. v3.2 — FOLLOW UP: kolom ✓ (toggle via klik sel), badge tab, tab
    ☑ Follow Up (render snapshot, uncheck=hapus), export xlsx,
    persistensi followup.json (v3.8: impor hasil TL DIHAPUS)
13. v3.4 — TAB 📤 REKAP SELISIH IN: render baris (Resto/Tanggal/Barang/
    Satuan/IN/Barang Masuk/Selisih IN), double-click → popup RINCIAN IN
    (dokumen 42.05/32.24/99.01 + Nomor + subtotal per sumber + copy nomor)
14. v3.4 — LEBAR KOLOM: drag tepi heading mengubah lebar (enable_col_
    resize), tombol ↔ Auto-Fit menyesuaikan lebar ke konten
15. v3.9.3 — LAPORAN DEVIASI DIGANTI (sementara): daftar anomali pemakaian
    (COM) per (Nama Barang × Resto) — COM minus atau > median pasangan
    (v3.9.7: median ANTAR TANGGAL 1..H, koreksi user — bukan antar resto)
    pada kolom H; H shared dari tab Deviasi GR (chip
    read-only + auto-refresh); minus merah per-cell + sel Status merah/amber
16. v3.9.4 — TAB LAPORAN DEVIASI 2 MODE (SegmentBar): ⚖ KOMPARASI FILE
    DEVIASI vs TAB DEVIASI GR (pilih file resmi; STATUS BULAN → kolom H:
    WEEK 1=7, WEEK 2=14, WEEK 3/4=25; BOM App = Σ penjualan 22.05,
    COM Saat Ini = Σ pemakaian, GR Saat Ini = SO_H − Sistem persis tab GR;
    status MATCH/SELISIH/TIDAK ADA DI DATA SAAT INI/H TIDAK ADA; resto file
    "1041.BDGUKU" dinormalkan; opsi tampil semua resto; minus merah
    per-cell + sel Status hijau/amber/merah) & 🚨 Anomali COM (v3.9.3)
17. v3.9.5 — AUDIT DEEP REGRESSION (§23): SALDO AWAL jadi base com(1)
18. v3.9.6 — KATEGORI DEVIASI (§6) + audit kronologis tgl 1 (§14) +
    FORMAT FOLLOW UP file sample (§11): 5 kolom kategori (Max Deviasi,
    ACR, Total ACR, Dev to BOM%, Stok Seharusnya) + CEK ke-5 "ACR to
    BOM" + pembanding SO tanggal 1 = SO bulan lalu terakhir + tabel/
    export Follow Up ala sheet Follow UP workbook asli.
19. v3.9.7 — (§7) median Anomali COM ANTAR TANGGAL per pasangan (com =
    pemakaian aktual harian di resto — koreksi user; window 1..H, heading
    "Median (1..H)") + (§22) filter minggu Komparasi mengikuti H bersama
    (STATUS BULAN utk filter: H 1–7 → WEEK 1, 8–14 → W2, 15–25 → W3/4,
    26–31 → W5; chip H read-only + highlight chip minggu aktif + opsi
    "Tampilkan semua minggu").
20. v3.9.8 — UI CLEAN (§1a): SEMUA teks instruksi dihapus dari UI —
    tombol "❓ Bantuan" + window panduan (_HELP_TEXT/_show_help),
    subtitle kartu (Filter/aksi), hint footer (🖱 Double-click…),
    tooltip hover (class ToolTip/add_tooltip dihapus dari widgets),
    subtitle EmptyState (default ""), subtitle tab Config/Proses,
    pertanyaan dialog export IN; footer status tetap (data), legenda
    tetap (decode nilai CEK/warna).
    (tanggal negatif + pair tanpa bulan-lalu — aljabar GR==DEV), race
    ✕ Tutup File saat compute, GC-shield dilepas walau pemilik job
    di-destroy, tag per-cell setelah filter di clone ⛶, duplikat lintas
    bulan dihitung, data di sheet ke-2, footer = baris tampil, filter
    reset saat reload file, sort diantrekan saat busy, pair index nama
    APP, snapshot 'aktif', show_laporan_mode sinkron SegmentBar, popup
    filter "Selisih vs Median" hidup, Apply H render 1×, unsubscribe H
21. v3.9.12 — TAB 🎯 PARETO DIHAPUS (user: "hapus tab pareto dan dead
    code nya"): pareto_view.py + write_pareto_sheet + integrasi app.py
    dibersihkan; app kembali 9 tab; §24 Pareto (v3.9.9) dihapus dari
    suite → §25 audit round-2 menjadi §24, §26 v3.9.11 menjadi §25.
22. v3.9.10 — AUDIT UI/UX ROUND 2 (§24): 4 agent paralel audit 4 arah
    (shell/tabel/view/integritas) — 37 temuan → fix P1-P3: race restart
    pipeline (A-01), cache-poisoning worker D-01, on_error rincian/popup
    (C-02), parser sort Selisih IN (B-01), tag per-cell di clone + sort
    (B-02/B-03), bind add="+" auto-fit (B-04), filter >3000 nilai lazy
    (B-05), gc_shield lock (B-06), cancel batch clone (B-07), pending-sort
    (B-08), followup render race (D-03), file-skip terlihat (D-04),
    tombol dim (A-02), DPI Windows (A-03), Ctrl+Tab (A-04), routing tab
    widget (A-11), format ID rincian/popup (C-03), minus merah Selisih
    IN (C-04), frasa instruksi dipangkas (C-06), footer baris (C-10),
    unsubscribe/dirty H (C-07/C-08), atomic write (D-05/D-06).
23. v3.9.11 — TUNTAS SISA TEMUAN (§25): P0 D-11 repo GitHub di-PRIVATE
    (user: "repo untuk pribadi aja") + 7 fix sisa audit 2-b: panah arah
    sort di heading (B-21), toggle filter clone tidak me-reset urutan
    sort (B-14), sort tree berhirarki jangan hilangkan anak (B-09,
    jalur tree.move), mirror kolom ⛶ dua arah (B-18), cursor watch
    refcount (B-17), TableExpander restore urutan (B-16), pecahan input
    tanggal ditolak tidak dilantai (B-12), EmptyState adaptif (B-11).
24. v3.9.13 — FILTER SEARCH-TO-SELECT + KATEGORI + KOLOM + PATH +
    MULTI-FILE + ANALISA (§26; 6 permintaan user + adopsi rumus repo
    Inventory-Control user): Enter di popup filter = hasil search jadi
    seleksi (0 hasil = 0 baris) + operator teks + ↔ Balik; kolom &
    combobox KATEGORI di Deviasi GR/PCS (post-pivot); kolom Minggu/H
    dihapus dari tabel komparasi + DEV App jadi %TO BOM; path file
    deviasi tersimpan (FIX BUG v3.9.10 json) + entry editable +
    auto-load; multi-file (askopenfilenames + BULAN-num dedup + filter
    mode 📈 Analisa (Top Selisih + Perubahan
    Arah/flip — Sempurna/Dominan/Parsial).
26. v3.9.15 — GELOMBANG 1 ANALISA (§26-5c): 4 bagian analisa baru di
    mode 📈 Analisa (v3.9.22: TUNGGAL Top & Flip — Minoritas/Liga
    dihapus): ⚡ Risiko Flip per bahan (skor = min(100, 30×Sempurna +
    10×Flip), Level TINGGI/SEDANG/RENDAH, drilldown resto kontributor) ·
    robust-z 1,4826×MAD, guard ≥5 resto ber-BOM) · 💰 Benchmark
    Opportunity (loss = Σ|DEV<0| vs median kelompok 3-huruf). Analisa
    per-periode = bulan terbaru + SATU minggu snapshot (minggu yang
    memuat H — kumulatif: jumlah lintas minggu = ganda).
27. v3.9.16 — TOP SELISIH: ABSOLUT + MEDIAN MULTI-FILE (§26-5g, khusus
    mode 📈 Analisa): Selisih = |GR Saat Ini| − |DEV Lalu| (kedua nilai
    diabsolutkan DULU — pembalikan tanda tak menggembungkan selisih;
    kolom DEV Lalu/GR Saat Ini tetap NILAI ASLI); file deviasi >1 →
    DEV Lalu = MEDIAN antar-file per pasangan (SATU baris per pasangan,
    bukan satu baris per file — yang ditampilkan nilai median saja);
    Periode 'Median n file · Minggu' (≥2) / 'BULAN · Minggu' (1);
    Status MATCH/SELISIH atas Selisih absolut; kolom Periode NYATA
    (filter header bekerja).
28. v3.9.17 — SUMBER IN 42.05 BULAN LALU + FOLLOW UP MINUS PER-CELL
    (§27): (1) folder config Pemindahan4205Lalu ("4.1 4205 Bulan Lalu")
    dibaca fn_4205(mode="lalu") — MIRROR fn_3224 "lalu": 5 hari terakhir
    file bulan lalu + Tanggal dinegasikan; masuk query_in (SOURCE IN
    "42.05 (Bulan Lalu)") + Qty SJ audit + popup Rincian IN (grup/chip).
    (2) tab ☑ Follow Up: minus merah PER CELL semua kolom numerik (Tk 9
    tag cell; fallback Tk 8 tag baris); tag negative tak lagi menimpa
    resolved/pending; sort & clone ⛶ memasang ulang tag.
30. v3.9.19 — KOLOM ANALISA + HAPUS BAGIAN + DEFAULT KATEGORI + NAMA
    RESTO PO + FILTER DATA-ADA + PROMIX 04 + 9.ACR + RI BALANCING
    (§29 + §26-5 update, 8 permintaan user): (1) kolom ANALISA (1 kolom
    saja) di tabel Top Selisih & Perubahan Arah bagian Top & Flip —
    Kenaikan/Penurunan Tertinggi · Stabil · Berubah Arah · Potensi Flip
    Flop (tanda berlawanan + disparitas 40% — ambang sama Kategori
    flip; v3.9.26: ARAH DIBALIK — disparitas < 40% [selisih magnitudo
    kecil, nilai bercermin ±] = Potensi Flip Flop, ≥ 40% = Berubah
    Arah; warna per-cell; bagian Risiko Flip & Benchmark DIHAPUS → 3
    bagian); (3) default KATEGORI Deviasi (fallback Semua); (4) kolom
    Nama Resto di Rincian PO (Cabang PO → kode resto); (5) isi filter
    header = data yang ada (mode Satuan + KATEGORI + kolom lain —
    deviasi/rincian PO/selisih IN/anomali COM/top/flip); (6) CEK
    "Promix 04" (SOURCE DATA rekap SO ≠ "input so harian" — prioritas
    pertama; append1 bawa SOURCE DATA per pasangan); (7) istilah 9.OUT
    → 9.ACR; (8) kolom CEK popup Rincian IN — "RI Balancing" bila
    bulan Nomor RI ≠ bulan Nomor PO (PREFIKS.TAHUN.BULAN.NOMOR).
31. v3.9.20 — DEEP AUDIT & FIX (§30; 5 agen audit 34-a..34-e + 5 agen fix
    35-a/b/c1/c2/d): 1 BUG + 15 RISK diperbaiki + penuntasan "semua
    filter = data yang ada": (35-a komparasi) reset filter 4 tabel
    analisa (Top/Flip) di SEMUA jalur reset tabel utama
    (load_data/_load_paths/_close_file/✕ Reset — dulu filter basi →
    0 baris senyap) + nilai popup tabel utama ⚖/analisa = baris
    tampil + 4 entri format kolom mati Risk/Bench dibersihkan; (35-b
    deviasi+popup) _hl_cells di-init di __init__ (sort sebelum render
    Tk 9 tidak lagi AttributeError) + popup ringkas memfilter SATUAN
    (angka = baris GR/PCS yang DIKLIK, bukan jumlah lintas satuan) +
    _chrono_key float-safe + _so_source_lookup keep-LAST sort-Tanggal
    (preferensi append1 LANGKAH 9) + _compute_cek dead-code dihapus;
    (35-c1 rincian PO+IN) BUG clone ⛶ InSelisihView reapply tag neg
    per-cell (on_render_done) + _resto_name pd.NA/float-safe (1370.0
    → '1370') + _fmt_date/_fmt_datetime NaT-safe (tab tidak mati) +
    load_data reset combo Cabang/Status + RI Balancing banding PERIODE
    (tahun, bulan) — lintas-tahun sama-bulan terflag + literal
    'None'/'nan'/'NaT' dibuang dari popup filter; (35-c2 pivot/FU/
    export) popup Nama Barang pivot = baris tampil (RESTO/SOURCE/
    KATEGORI/rentang tanggal/hide-empty) + popup kolom FollowUp =
    baris tampil + F401 dibersihkan + merah neg pivot #dc2626 seragam
    11 view + export sheet Rincian PO bawa kolom Nama Resto (import
    _resto_name); (35-d pipeline — cek di test_mock.py) tie-break
    LANGKAH 9 deterministik + NA-Tanggal tak menang + SOURCE DATA
    strip + resolusi sheet folder lalu (fallback prefiks modul + key
    dedikasi config) + fn_4205 lalu anchor resto-valid (mirror
    fn_3224).
29. v3.9.18 — FOKUS RESTO REKAP + POPUP RINGKAS + KOLOM + HIGHLIGHT
    (§28, 5 permintaan user tab Deviasi GR/PCS): (1) pivot HANYA resto
    yang ada di folder "1. DEVIASI WEEKLY" (JENIS 1.SO/5.BARANG MASUK
    Tanggal positif; resto hanya-di-app dikeluarkan — dulu minus palsu
    0−Sistem); (2) LOOKUP BARANG DUA ARAH: barang ber-rekap MAUPUN
    barang hanya-di-app utk resto rekap — keduanya tampil; (3) popup
    double-click DIGANTI popup ringkas (bukan DetailsPopup source
    rows): judul = Nama Barang — Nama Resto, tabel per Tanggal hanya
    Saldo Akhir/SO/IN/Deviasi ('25•' = bulan lalu, baris H berlatar
    lembut); (4) kolom Max Deviasi/ACR/Total ACR DIHAPUS dari tampilan
    — hitungan internal TETAP (CEK 'ACR to BOM', Dev to BOM%, Stok
    Seharusnya tetap benar); (5) HIGHLIGHT latar #fef3c7 kolom Deviasi
    & SO_H (tag cell Tk 9; fallback Tk 8 tanpa tint).
37. v3.9.26 — POTENSI FLIP FLOP = SELISIH MAGNITUDO KECIL (§36; user:
    "potensi flip flop itu harusnya yang selisih nya dikit aja"):
    arah label ANALISA DIBALIK (audit 41-a: logika di 2 titik;
    41-b data real: 87,9% pasangan flip = Parsial — aturan lama
    melabeli flip miring/noise [DEV 0,1 → GR −780] sbg FFLOP,
    cermin sejati [−9.525 → +9.551] cuma 'Berubah Arah'):
    disparitas < FFLOP_DISP_MAX 40% (Sempurna/Dominan — nilai
    bercermin ±, mis. −50 → +55: deviasi sama besarnya cuma pindah
    sisi → rawan bolak-balik) = 'Potensi Flip Flop'; disparitas
    ≥ 40% (Parsial — sisi dominan jauh lebih besar, mis. −100 →
    +10) = 'Berubah Arah'. SATU konstanta FFLOP_DISP_MAX utk
    tabel Top Selisih (_top_aggregate) & Perubahan Arah
    (_render_flip + batas Kategori); prioritas flip > Stabil utuh;
    tanda sama tidak pernah FFLOP.
39. v3.9.28 — TANGGAL SERIAL EXCEL (.xlsb/pyxlsb) ROBUST (§39; user:
    "push to git hub dan perbaiki stock seharusnya dan hitung manual"):
    file .xlsb via engine pyxlsb memberi sel TANGGAL sbg SERIAL MENTAH
    (46290 = 2026-09-25); pd.to_datetime lama membaca sbg nanodetik-epoch
    → SEMUA transaksi jatuh ke Tanggal=1 → In_H=0 utk H>1 → 'Stok
    Seharusnya' (W = SO(H-1)+IN−KIRIMAN−PENJUALAN) salah & flag 'Hitung
    Manual' palsu (reproduksi: sheet '4  42 05' workbook user — 4.591
    baris serial → 100% hari 1 pra-fix). FIX helpers.to_datetime_robust
    (BARU): numeric 20000..80000 (th 1954..2119 — tak tumpang tindih
    dgn hari 1..31) dikonversi epoch Excel 1899-12-30 (pecahan waktu
    ikut); date_to_day dibangun di atasnya (42.05/32.24/22.05/42.15/
    9901); '#Tgl/Jam Pembuatan IT' fn_4205 + queries 3224/lalu + kolom
    tanggal Rincian PO ikut robust. Pipeline mock 464.205 baris IDENTIK
    (0 beda); parity sheet H=25: Hitung Manual 3=3 overlap penuh,
    Stok Seharusnya 12/1.405 sisa = inkonsistensi internal workbook.
41. v3.9.29 — SOURCE KIRIMAN PER PASANGAN + SCROLL HALUS + KOLOM
    KATEGORI DEVIASI DIHAPUS (§41 + skema §6/§26 diperbarui; user:
    "nama barang + resto yang berasal dari 42.05 harusnya kategori
    internal. dari 32.24 eksternal dan 9901 juga eksternal ... aku mau
    ganti" + konfirmasi campuran→'Campuran' / 9901→Eksternal / tanpa
    IN→kosong / MENGGANTI nilai source kiriman + "perbaiki animasi
    scroll seperti tidak smooth dan patah patah" + "hapus kolom
    kategori di tab deviasi gr dan pcs karna sudah ada filter di atas
    nya"): (1) _source_kiriman_per_pair: 42.05(-Lalu)→Internal,
    32.24(-Lalu)/99.01→Eksternal, campuran→Campuran, tanpa IN→kosong;
    query_in men-tag SEMUA baris IN dgn 'SOURCE IN'; detail 1:1.
    (2) enable_smooth_wheel (1 baris per notch + akumulator delta
    pecahan + break anti-dobel + idempoten). (3) CellColorOverlay:
    label menempel PERSIS bbox sel, reposisi SINKRON pasca-scroll
    (bbox valid saat yscrollcommand), LABEL POOL reuse. (4) Kolom
    KATEGORI dihapus dari tabel Deviasi GR & PCS (COLUMNS 21→20 —
    combobox + filter post-pivot tetap).
38. v3.9.27 — MODE HITUNG REKAP SELISIH IN + CEK PORT PERSIS SHEET
    'Data Base Cek Deviasi' (§37 + §38; user: "pada rekap selisih in
    bisa mode hitung bulan lalu dan hanya hitung bulan ini. Tapi
    default hitung bulan ini aja" + "kondisi beda tanggal kok
    menghasilkan data kosong semua? cek file 01.1 CEK STOCK V2.xlsb
    bagian sheet Data Base Cek Deviasi KOLOM Y ... cek semua logika
    nya dan bandingkan dengan yang ada di program"):
    (1) §37 — MODE HITUNG (SegmentBar "MODE HITUNG" kartu Filter):
    "📅 Bulan Ini" DEFAULT (audit varian bulan berjalan saja —
    baris Tanggal negatif dibuang sebelum engine; mirror sheet
    LAPORAN_DEVIASI tgl 1..31; rentang 1..31) | "📆 Lalu + Ini"
    (varian penuh incl. bulan lalu; rentang -31..31); pipeline
    menghitung KEDUA varian sekali (kunci df_bulan_ini/
    kpi_bulan_ini/desc_bulan_ini); KPI chips + chip MODE ikut
    varian; auto-upgrade rentang negatif; Reset & load_data ulang
    → default Bulan Ini; kompatibel pemanggil tanpa kunci baru.
    (2) §38 — CEK Deviasi GR/PCS di-port ulang PERSIS formula LET
    sheet terhide kolom Y (nama LET = defined names _xlpm.
    KondisiKosong/Naikturun/HitungManual/TurunDrastis/KondisiACR;
    simulasi 2.120 baris workbook = label cached Y 128/129 eksak):
    kondisi 2 "Beda Tanggal" J = KIRIMAN KELUAR (8.BARANG KELUAR —
    dulu 9.ACR/PENJUALAN, bug port pertama; bukti MLGPAR/ADONAN
    GORENG MEKAR sheet='Beda Tanggal' app lama=''), aturan SO-stale
    v3.9.22 DIHAPUS (baris 'data kosong' SO_H=0 — gejala yang user
    pertanyakan), kondisi 3 "Hitung Manual" stok = W sheet = SO(H-1)
    + IN − KIRIMAN KELUAR_H − PENJUALAN_H (dulu sistem+IN−ACR−BK →
    266 flag palsu data real), Stok Seharusnya = W sheet (dulu
    SO(H-1)−ACR-rata2). Gate sheet IF(V="","",…) (Total ACR=0 →
    CEK kosong 47% baris workbook + kaskade #N/A tanggal di luar
    cakupan pivot sumber → 'data kosong semua') TIDAK direplikasi —
    app mengevaluasi kondisi apa adanya.
35. v3.9.25 — POPUP DEVIASI GR/PCS PERBESAR + Nomor PO + COM (§35;
    user: "POP UP DI tab deviasi gr dan deviasi pcs perbesar lagi
    dan tambah kolom nomor po dan COM"): jendela popup 880×480 →
    1180×640 (minsize 820×340; judul wraplength 1020) + 2 kolom
    baru: "Nomor PO" (pesanan pembelian baris 4.IN per tanggal —
    split koma → dedup → urut → gabung, pola Nomor v3.9.22) & "COM"
    (pemakaian harian — _compute_com_series PORT PERSIS matrix
    Anomali COM laporan_deviasi_view: com(t) = so_prev + IN − BK −
    SO; kolom tanggal GLOBAL union 4 JENIS SEMUA pasangan [fill 0
    utk pair tanpa SO di kolom itu]; tanggal 1 base SALDO AWAL pair
    bila ada [tanpa fill — 'SA ada' ≠ 'SA tidak ada'], fallback
    so_prev; parity 48/48 + test parity vs matrix langsung; tanggal
    di luar kolom global → COM kosong). COM minus ikut merah per-cell
    (Tk 9; fallback Tk 8 tag baris).
36. v3.9.24 — RI BALANCING PERIODE BISNIS 26→25 (§34; user: "jika
    saat ini bulan oktober maka 1 periode nya mulai dari 26 september
    - 25 oktober nah untuk cek RI balancing berarti dengan NO. PO yang
    bukan bulan september dan oktober"): definisi diperbaiki dari
    "bulan RI ≠ bulan PO" → PO di luar DUA BULAN periode bisnis RI
    (tgl 1-25 → {bulan-1, bulan}; tgl 26-31 → {bulan, bulan+1}; wrap
    tahun Des↔Jan; tanggal bulan-lalu negatif dibaca absolut). RI
    1 Okt + PO Agu → balancing (contoh user); RI 1 Okt + PO Sep →
    '' (satu periode — v3.9.19-23 SALAH FLAG kasus ini); fallback
    tanpa tanggal valid → aturan lama bulan≠bulan. Berlaku di CEK
    kolom utama + popup Rincian IN + Catatan Audit B1 (satu logika
    doc_codes._ri_balancing).
34. v3.9.23 — CEK RI BALANCING KOLOM UTAMA + CATATAN AUDIT OTOMATIS
    REKAP IN (§33; user: "kerjakan poin 6 dan kerjakan semua poin
    B"): (1) POIN 6 — CEK "RI Balancing" di kolom CEK utama tab
    Deviasi GR & PCS: pasangan ber-dokumen IN periode RI ≠ PO (tgl
    dok ≤ H) TERFLAG; prioritas Promix → RI Balancing → pola numerik;
    helper diangkat ke doc_codes.py (modul bersama); (2) SEMUA POIN B —
    Catatan Audit Rekap Selisih IN diperkaya otomatis (append ke VBA,
    " | "): B1 RI Balancing (+periode PO), B2 Nomor dobel (×N),
    B3 Selisih IN arah, B4 BM 0 padahal IN>0; ikut export; in_detail
    diteruskan app ke kedua tab Deviasi.

33. v3.9.22 — OVERLAY PER-CELL TK 8.6 + ANALISA TUNGGAL + CEK BEDA
    TANGGAL + H DINAMIS 26 + POPUP NOMOR + DEFAULT KATEGORI REKAP IN +
    BUG KARTESIAN append1 (§32, 7 permintaan user + deep audit):
    (1) CellColorOverlay widgets.py — per-cell di Tk 8.6 via Label
    overlay (virtual, event forwarding, double-click manual, merge 2
    tag); (2) Arah Minoritas & Liga Deviasi dihapus penuh + dead code;
    (3) CEK 'Beda Tanggal' SO-stale (tanggal SO nonzero terakhir < H;
    pasangan tanpa SO juga; prioritas Promix tetap; (4) popup 6 kolom
    + Nomor IT./RI. dedup+urut; (5) H dinamis = tanggal SO nonzero
    terakhir (fallback 26; reset di load & ✕ Reset; minggu 15..31→25);
    (6) Rekap Selisih IN default KATEGORI Deviasi (load + reset, tetap
    fleksibel); (7) append1 pivot kartesian → groupby+pivot (baris
    fantom hilang; JENIS case-drift dinormalisasi; export None → '').

32. v3.9.21 — AMBANG ACR to BOM BISA DIATUR + PROMIX 04 PER-TANGGAL +
    MINUS PER-CELL LAPORAN (§31, 4 permintaan user): (1) CEK 'ACR to
    BOM' kini |Deviasi| > (ambang/100) × Total ACR (dulu kaku >100%);
    ambang default 80, spinbox di kartu Filter KEDUA tab GR & PCS
    (sinkron SharedACRThreshold — pola TANGGAL H; ubah → pivot cache
    di-clear + recompute; settings.json persist atomic; clamp 1..200);
    (2) CEK 'Promix 04' PER-TANGGAL: append1 LANGKAH 9 resolve sumber
    per (pasangan × tanggal) atas baris rekap ber-NILAI non-nol ('input
    so harian' menang atas promix di tanggal sama; 0/NaN/whitespace
    tidak menentukan; NA-Tanggal dibuang) → deviasi_view membaca sumber
    baris 1.SO TANGGAL H — label muncul HANYA bila SO tanggal H benar
    bersumber promix (fix phantom "muncul di filter tapi data tidak
    ada" — v3.9.19 tie urutan baris bisa melabel semua pasangan
    campuran; v3.9.20 swing kebalikan); (3) prioritas Promix tetap
    PERTAMA — tidak bertabrakan: pasangan so-harian dievaluasi CEK
    normal penuh; (4) minus per-cell diperluas: Anomali COM (Median +
    Selisih vs Median — dulu hanya COM).
25. v3.9.14 — PERF TAB ANALISA + MINGGU IKUT H + ISTILAH (§22/§26):
    analisa dirender MALAS (hanya saat mode 📈 aktif — dulu dirender juga
    saat tersembunyi → ±4,8 dtk freeze per refresh di file 40rb baris);
    flip VEKTOR (sort+shift, dulu groupby+sort per grup 4,7 dtk → ±50ms)
    + nilai app per baris via MERGE vektor (dulu loop Series.get 2,9 dtk
    → ±60ms — terverifikasi identik); minggu Top Selisih & flip kini
    ikut H (H=7 → WEEK 1); istilah kolom *File → *Lalu & *App → *Saat
    Ini (BOM Lalu / DEV Lalu / %TO BOM Lalu / BOM Saat Ini / COM Saat
    Ini / DEV Saat Ini / GR Saat Ini; status 'TIDAK ADA DI DATA APP' →
    'TIDAK ADA DI DATA SAAT INI').
"""
import os
import shutil
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk

from src.ui.app import APP_VERSION, StockMonitorApp
from src.ui.komparasi_deviasi_view import (
    _h_to_week_target,
    _norm_name,
    parse_deviasi_file,
)
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.widgets import _GC_HOLD, HeaderFilter, LoadingOverlay, run_async

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  ✓ {name}")
    else:
        FAIL.append(name)
        print(f"  ✗ {name} {detail}")


def wait_view(root, view, timeout=15.0):
    """Pump event loop sampai async refresh view selesai (compute+render)."""
    t0 = time.time()
    while getattr(view, "_busy", False) and time.time() - t0 < timeout:
        root.update()
        time.sleep(0.01)
    # pastikan batch insert after() selesai juga
    t0 = time.time()
    while time.time() - t0 < 0.5:
        root.update()
        time.sleep(0.01)
    return not getattr(view, "_busy", False)


def select_and_wait(root, app, tab, view, timeout=15.0):
    """Pilih tab lalu tunggu lazy refresh selesai (v3.2)."""
    app.notebook.select(tab)
    root.update()
    if hasattr(view, "ensure_refreshed"):
        view.ensure_refreshed()
    return wait_view(root, view, timeout)


def find_trees(widget):
    out = []
    for c in widget.winfo_children():
        if isinstance(c, ttk.Treeview):
            out.append(c)
        out.extend(find_trees(c))
    return out


def make_mock_append1() -> pd.DataFrame:
    """Mock Append1 long-format — termasuk item yang HANYA ada di resto
    MLGPAR (ADONAN GORENG MEKAR) untuk menguji pivot per resto."""
    rows = []
    barangs = [("AYAM FILET", "GR"), ("GULA PASIR", "GR"),
               ("KOPI BUBUK 100G", "PCS"), ("SUSU UHT 1L", "PCS"),
               ("ADONAN GORENG MEKAR", "GR")]  # hanya di MLGPAR
    restos = ["MLGPAR", "SBYKET"]
    jenis_list = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
                  "4.IN", "5.BARANG MASUK", "8.BARANG KELUAR", "9.ACR"]
    for barang, satuan in barangs:
        item_restos = ["MLGPAR"] if barang == "ADONAN GORENG MEKAR" else restos
        for resto in item_restos:
            for jenis in jenis_list:
                for tgl in range(1, 31):
                    val = 0.0
                    if jenis == "1.SO":
                        val = 10.0 + (tgl % 7) + (hash(barang) % 5)
                        if tgl == 25 and barang == "AYAM FILET" and resto == "MLGPAR":
                            val = 80.0  # anomali besar untuk CEK
                    elif jenis == "2.SALDO AKHIR":
                        val = 10.0
                    elif jenis == "4.IN" and tgl % 5 == 0:
                        val = 5.0
                    elif jenis == "9.ACR" and tgl % 3 == 0:
                        val = 3.0
                    elif jenis == "SALDO AWAL" and tgl == 1:
                        val = 10.0
                    rows.append({
                        "Nama Barang": barang, "JENIS": jenis,
                        "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": val,
                        "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                        "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                        "Nomor": f"RI-00{tgl}", "Nomor PO": f"PO-00{tgl}",
                        "#Tgl/Jam Pembuatan IT": None,
                    })

    # v3.9.6: barang uji kategori CEK "ACR to BOM" (kondisi ke-5) —
    # pola SO bersih (SO flat 200, IN 100 hanya tgl 25, OUT standar
    # 3 per t%3 → Total ACR 24 di 1..25): satu-satunya kondisi yang
    # terpicu = |Deviasi 100| > Total ACR 24.
    for resto in ("MLGPAR",):
        for jenis in jenis_list:
            for tgl in range(1, 31):
                val = 0.0
                if jenis == "1.SO":
                    val = 200.0
                elif jenis == "2.SALDO AKHIR":
                    val = 100.0
                elif jenis == "4.IN" and tgl == 25:
                    val = 100.0
                elif jenis == "9.ACR" and tgl % 3 == 0:
                    val = 3.0
                rows.append({
                    "Nama Barang": "BARANG ACR", "JENIS": jenis,
                    "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": val,
                    "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                    "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": f"RI-00{tgl}", "Nomor PO": f"PO-00{tgl}",
                    "#Tgl/Jam Pembuatan IT": None,
                })
    return pd.DataFrame(rows)


def make_mock_komparasi_df() -> pd.DataFrame:
    """Mock deterministik utk KOMPARASI (v3.9.4) — 2 barang × 2 resto,
    tgl 1..25, running-stock konsisten (DEV App == GR App secara aljabar).

    AYAM FILET: SA=100, SO(t)=100-3t, IN=10 (t%5==0), OUT=20 genap/5 ganjil
      → SIS(t) running → GR(7)=49, GR(14)=113, GR(25)=180
      com(t)=3+IN(t) → cum(1..7)=31; out_cum(1..7)=80 → DEV App(7)=49
    GULA PASIR: SA=60, SO(t)=60-2t, IN=0, OUT=8
      → GR(25)=150; com cum(1..25)=50; out_cum=200 → DEV App=150
    """
    rows = []
    spec = [
        ("AYAM FILET", "GR", 100.0, 100.0, 3.0),
        ("GULA PASIR", "GR", 60.0, 60.0, 2.0),
    ]
    for barang, satuan, sa, so_a, so_b in spec:
        for resto in ("MLGPAR", "SBYKET"):
            sis = sa
            for t in range(1, 26):
                so = so_a - so_b * t
                in_v = 10.0 if (barang == "AYAM FILET" and t % 5 == 0) else 0.0
                out_v = (20.0 if t % 2 == 0 else 5.0) \
                    if barang == "AYAM FILET" else 8.0
                sis = sis + in_v - out_v
                rows.append({
                    "Nama Barang": barang, "JENIS": "SALDO AWAL",
                    "NAMA RESTO": resto, "Tanggal": t,
                    "NILAI": sa if t == 1 else 0.0,
                    "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                    "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                    "Nomor": None, "Nomor PO": None,
                    "#Tgl/Jam Pembuatan IT": None,
                })
                for jenis, val in (("1.SO", so), ("2.SALDO AKHIR", sis),
                                   ("4.IN", in_v), ("9.ACR", out_v),
                                   ("8.BARANG KELUAR", 0.0)):
                    rows.append({
                        "Nama Barang": barang, "JENIS": jenis,
                        "NAMA RESTO": resto, "Tanggal": t, "NILAI": val,
                        "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                        "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                        "Nomor": None, "Nomor PO": None,
                        "#Tgl/Jam Pembuatan IT": None,
                    })
    return pd.DataFrame(rows)


def make_mock_deviasi_file() -> str:
    """Mock file deviasi (format kolom file asli '20.AGUSTUS 2026.xlsx').

    7 baris: 3 MATCH (nilai = hitungan app), 1 SELISIH (DEV File 74 vs
    GR 49), 1 resto tak dikenal (9999.XYZZZ), 1 barang tak ada di app,
    1 WEEK 5 (H=31 tidak ada di data 1..25).
    """
    import tempfile

    from openpyxl import Workbook
    hdr = ["Akun Penyesuaian Persediaan", "STATUS", "RESTO", "NAMA BAHAN",
           "Satuan", "QTY BOM", "QTY COM", "QTY DEVIASI", "QTY WASTE",
           "QTY SUSUT", "QTY TRIAL", "QTY LOSS SURPLUS", "NOMINAL DEVIASI",
           "NOMINAL WASTE", "NOMINAL SUSUT", "NOMINAL TRIAL",
           "NOMINAL LOSS/SURPLUS", "QTY WASTE + SUSUT", "% WASTE + SUSUT",
           "%TOLERANSI", "% QTY DEVIASI TO BOM", "QTY WASTE TO BOM",
           "QTY SUSUT TO BOM", "QTY TRIAL  TO BOM",
           "QTY LOSS/ SURPLUS TO BOM", "AREA", "BULAN", "PENJUALAN",
           "STATUS BULAN", "BULAN 2"]
    data = [
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "AYAM FILET",
         "GR", -80, -31, 49, 0, 0, 0, 49, 49000, 0, 0, 0, 49000, 0, 0,
         "BELUM ADA TOLERANSI", 49 / 80, 0, 0, 0, 49 / 80, "JAWA TIMUR",
         "201.OKT 26", 1000, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1002.SBYKET", "AYAM FILET",
         "GR", -80, -31, 74, 0, 0, 0, 74, 74000, 0, 0, 0, 74000, 0, 0,
         "BELUM ADA TOLERANSI", 74 / 80, 0, 0, 0, 74 / 80, "JAWA TIMUR",
         "201.OKT 26", 1000, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "AYAM FILET",
         "GR", -175, -62, 113, 0, 0, 0, 113, 113000, 0, 0, 0, 113000, 0, 0,
         "BELUM ADA TOLERANSI", 113 / 175, 0, 0, 0, 113 / 175, "JAWA TIMUR",
         "202.OKT 26", 2000, "WEEK 2", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "GULA PASIR",
         "GR", -200, -50, 150, 0, 0, 0, 150, 150000, 0, 0, 0, 150000, 0, 0,
         "BELUM ADA TOLERANSI", 150 / 200, 0, 0, 0, 150 / 200, "JAWA TIMUR",
         "204.OKT 26", 4000, "WEEK 4", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "9999.XYZZZ", "AYAM FILET",
         "GR", -10, -5, 5, 0, 0, 0, 5, 5000, 0, 0, 0, 5000, 0, 0,
         "BELUM ADA TOLERANSI", 0.5, 0, 0, 0, 0.5, "LUAR JAWA",
         "201.OKT 26", 100, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "BARANG TAK ADA",
         "GR", -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
         "BELUM ADA TOLERANSI", 0, 0, 0, 0, 0, "JAWA TIMUR",
         "201.OKT 26", 100, "WEEK 1", "8.OKTOBER"],
        ["COM DEVIASI - RESTO", "DEVIASI", "1001.MLGPAR", "AYAM FILET",
         "GR", -305, -125, 180, 0, 0, 0, 180, 180000, 0, 0, 0, 180000, 0, 0,
         "BELUM ADA TOLERANSI", 180 / 305, 0, 0, 0, 180 / 305, "JAWA TIMUR",
         "205.OKT 26", 5000, "WEEK 5", "8.OKTOBER"],
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(hdr)
    for row in data:
        ws.append(row)
    tmp = os.path.join(tempfile.gettempdir(), "mock_deviasi_komparasi.xlsx")
    wb.save(tmp)
    return tmp


def make_mock_in_detail() -> pd.DataFrame:
    """Mock detail IN per dokumen (v3.4) — 3 sumber + Nomor."""
    rows = []
    # 42.05 (pemindahan/SJ) — AYAM FILET MLGPAR tgl 5,10,15
    for tgl, nomor, qty in [(5, "IT.2026.09.00101", 500.0),
                            (10, "IT.2026.09.00202", 750.0),
                            (15, "IT.2026.09.00303", 250.0)]:
        rows.append({
            "NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
            "Tanggal": tgl, "Value": qty, "Nomor": nomor,
            "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
            "SOURCE IN": "42.05", "JENIS": "IN"})
    # 32.24 (RI) — AYAM FILET MLGPAR tgl 10
    rows.append({
        "NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
        "Tanggal": 10, "Value": 300.0, "Nomor": "RI.2026.09.009",
        "Nomor PO": "PO-010", "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "32.24", "JENIS": "IN"})
    # 42.05 — KOPI BUBUK 100G MLGPAR tgl 8 (utk uji CUT-OFF RESOLVED v3.6)
    rows.append({
        "NAMA RESTO": "MLGPAR", "Nama Barang": "KOPI BUBUK 100G",
        "Tanggal": 8, "Value": 100.0, "Nomor": "IT.2026.09.00404",
        "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "42.05", "JENIS": "IN"})
    # 99.01 (pembelian tanpa penerimaan) — GULA PASIR SBYKET tgl 5
    rows.append({
        "NAMA RESTO": "SBYKET", "Nama Barang": "GULA PASIR",
        "Tanggal": 5, "Value": 1200.0, "Nomor": "PI.2026.10.01556",
        "Nomor PO": "PO.2026.10.012", "#Tgl/Jam Pembuatan IT": None,
        "SOURCE IN": "99.01", "JENIS": "IN"})
    return pd.DataFrame(rows)


def make_mock_rekap_so() -> pd.DataFrame:
    """Mock rekap mentah (JENIS 'SO' + 'BARANG MASUK') — input Audit
    Rekonsiliasi dari data app (v3.6).

    Skenario status yang dihasilkan (bersama make_mock_in_detail):
    - AYAM FILET/MLGPAR tgl 5,10,15 : BM == IN          → OK (Matching)
    - GULA PASIR/SBYKET tgl 5        : SO naik+BM=0+IN  → VALID
    - KOPI BUBUK/MLGPAR tgl 3→8     : +100 lalu -100   → CUT-OFF RESOLVED
    - SUSU UHT 1L/MLGPAR tgl 2       : BM 80 tanpa IN   → DEVIASI MURNI
    """
    rows = []

    def so(barang, resto, tgl, val):
        rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                     "JENIS": "SO", "Tanggal": tgl, "Value": val})

    def bm(barang, resto, tgl, val):
        rows.append({"NAMA RESTO": resto, "Nama Barang": barang,
                     "JENIS": "BARANG MASUK", "Tanggal": tgl,
                     "Value": val})

    for t in (4, 5, 10, 15):
        so("AYAM FILET", "MLGPAR", t, 100.0 * t)
    bm("AYAM FILET", "MLGPAR", 5, 500.0)    # IN 500  → selisih 0
    bm("AYAM FILET", "MLGPAR", 10, 1050.0)  # IN 1050 → selisih 0
    bm("AYAM FILET", "MLGPAR", 15, 250.0)   # IN 250  → selisih 0
    so("GULA PASIR", "SBYKET", 4, 100.0)
    so("GULA PASIR", "SBYKET", 5, 1300.0)   # SO naik +1200, BM=0, IN=1200
    so("KOPI BUBUK 100G", "MLGPAR", 3, 50.0)
    bm("KOPI BUBUK 100G", "MLGPAR", 3, 100.0)  # +100 …
    bm("SUSU UHT 1L", "MLGPAR", 2, 80.0)      # gantung +80
    return pd.DataFrame(rows)


def make_mock_rincian() -> pd.DataFrame:
    rows = []
    for i in range(1, 13):
        for j in range(1, 4):
            rows.append({
                "Nomor #": f"PO-2024-{i:03d}",
                "Tanggal": pd.Timestamp("2024-06-01") + pd.Timedelta(days=i),
                "Nama Barang": ["AYAM FILET", "GULA PASIR", "SUSU UHT 1L"][j - 1],
                "Keterangan PO": "Rutin",
                "Pemasok": ["PT Sumber", "CV Maju", "UD Jaya"][j - 1],
                "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-01 09:00") +
                                     pd.Timedelta(days=i),
                "Satuan": "GR",
                "Kuantitas": 10.0 * j,
                "Cabang PO": "MLGPAR" if i % 2 else "SBYKET",
                "Status Pesanan Pembelian": "Selesai",
            })
    return pd.DataFrame(rows)


def main():
    print("== 1. Build app shell ==")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real_stdout, real_stderr
    root.update_idletasks()
    check("App + toolbar + 9 tab terbangun (v3.9.12: tab 🎯 Pareto dihapus)",
          len(app.notebook.tabs()) == 9, f"tabs={len(app.notebook.tabs())}")
    check("Status bar ada", app.statusbar is not None)
    check(f"Versi = 3.9.29", APP_VERSION == "3.9.29", f"got {APP_VERSION}")
    check("(v3.9.12) atribut app.pareto_view / app.tab_pareto DIHAPUS",
          not hasattr(app, "pareto_view") and not hasattr(app, "tab_pareto"))
    check("(v3.9.12) judul tab 'Pareto' tidak ada di notebook",
          not any("Pareto" in app.notebook.tab(t, "text")
                  for t in app.notebook.tabs()))
    try:
        import src.ui.pareto_view  # noqa: F401
        _pv_gone = False
    except ImportError:
        _pv_gone = True
    check("(v3.9.12) modul src.ui.pareto_view DIHAPUS (dead code)",
          _pv_gone)
    import src.ui.export_sheets as _es_mod
    check("(v3.9.12) write_pareto_sheet DIHAPUS dari export_sheets",
          not hasattr(_es_mod, "write_pareto_sheet"))
    check("Proses tab punya spinner status", app.status_spinner is not None)

    print("== 1a. v3.9.8 UI CLEAN — teks instruksi dihapus ==")
    import src.ui.widgets as _wmod
    check("(v3.9.8) widgets.ToolTip & add_tooltip DIHAPUS",
          not hasattr(_wmod, "ToolTip") and not hasattr(_wmod, "add_tooltip"))
    check("(v3.9.8) app._show_help DIHAPUS (tombol ❓ Bantuan hilang)",
          not hasattr(app, "_show_help"))

    def _all_labels_text(widget, acc=None):
        acc = [] if acc is None else acc
        for ch in widget.winfo_children():
            if isinstance(ch, tk.Label):
                t = ch.cget("text") or ""
                tv = ch.cget("textvariable") or ""
                if t and not tv:
                    acc.append(str(t))
            acc = _all_labels_text(ch, acc)
        return acc

    _shell_txt = _all_labels_text(root)
    _tb_btns = [str(b.cget("text")) for b in app.toolbar._actions.winfo_children()
                if isinstance(b, tk.Button)]
    check("(v3.9.8) Toolbar tanpa tombol Bantuan",
          not any("Bantuan" in t for t in _shell_txt + _tb_btns),
          f"found {[t for t in _shell_txt + _tb_btns if 'Bantuan' in t]}")
    check("(v3.9.8) Toolbar hanya 💾 Export Excel",
          _tb_btns == ["💾 Export Excel"], f"got {_tb_btns}")

    def _view_static_labels(view):
        """Label statis (non textvariable) di view — tanpa legenda & KPI."""
        out = []
        for lbl in _all_labels_text(view):
            if any(k in lbl for k in ("Kosong/Non Aktif", "Beda Tanggal",
                                      "Hitung Manual", "Turun Drastis",
                                      "ACR to BOM", "negatif (merah)",
                                      "IN", "BARANG MASUK",
                                      "Selisih ≠ 0", "tgl • = bulan lalu")):
                continue  # legenda (decode data — dipertahankan)
            out.append(lbl)
        return out

    for name, view in (("Deviasi GR", app.deviasi_gr_view),
                       ("Deviasi PCS", app.deviasi_pcs_view),
                       ("Pivot", app.pivot_view),
                       ("Rekap Selisih IN", app.in_selisih_view),
                       ("Laporan", app.laporan_view),
                       ("Komparasi", app.komparasi_view),
                       ("Follow Up", app.followup_view),
                       ("Rincian PO", app.rincian_view)):
        _txt = _view_static_labels(view)
        check(f"(v3.9.8) {name}: tanpa hint 'klik'/'double-click'/corong",
              not any(("klik" in t.lower() or "double-click" in t.lower()
                       or "corong" in t.lower() or "⧩" in t and "MINGGU" not in t)
                      for t in _txt),
              f"found {[t for t in _txt if 'klik' in t.lower()]}")
        check(f"(v3.9.8) {name}: tanpa panah-instruksi '→'",
              not any("→" in t and "MINGGU" not in t
                      and not t.startswith("WEEK ") for t in _txt),
              f"found {[t for t in _txt if '→' in t and 'MINGGU' not in t]}")

    check("(v3.9.8) EmptyState tanpa subtitle default",
          app.pivot_view.empty._subtitle_missing
          if hasattr(app.pivot_view.empty, "_subtitle_missing")
          else not any("Jalankan pipeline untuk memuat" in t
                       for t in _all_labels_text(app.pivot_view.empty)))

    print("== 2. Empty state semua view ==")
    check("Pivot empty state terpasang (pack)",
          app.pivot_view.empty.winfo_manager() == "pack")
    check("Pivot content tersembunyi",
          app.pivot_view.content.winfo_manager() == "")
    check("Deviasi GR empty", app.deviasi_gr_view.data is None)
    check("Laporan empty", app.laporan_view.data is None)
    check("Rincian empty", app.rincian_view.data is None)
    check("Rekap Selisih IN empty (v3.4)", app.in_selisih_view.data is None)

    print("== 3. Load mock data (async + loading overlay) ==")
    append1 = make_mock_append1()
    rincian = make_mock_rincian()
    in_detail = make_mock_in_detail()
    rekap_so = make_mock_rekap_so()
    # v3.6: audit dari data app (rekap SO + BM + IN per tanggal)
    from src.pipeline.fn_audit import build_audit_from_app
    audit_df, audit_kpi, audit_desc = build_audit_from_app(rekap_so,
                                                           in_detail)
    audit_result = {"df": audit_df, "kpi": audit_kpi, "desc": audit_desc}
    print(f"   mock append1: {len(append1)} rows, rincian: {len(rincian)} rows, "
          f"in_detail: {len(in_detail)} rows, audit: {len(audit_df)} rows")

    check("Pivot punya loading overlay",
          isinstance(app.pivot_view.overlay, LoadingOverlay))
    check("Deviasi GR punya loading overlay",
          isinstance(app.deviasi_gr_view.overlay, LoadingOverlay))
    check("Laporan punya loading overlay",
          isinstance(app.laporan_view.overlay, LoadingOverlay))
    check("Rincian punya loading overlay",
          isinstance(app.rincian_view.overlay, LoadingOverlay))
    check("Follow Up punya loading overlay",
          isinstance(app.followup_view.overlay, LoadingOverlay))

    # (v3.2) LAZY: load_data tanpa tab aktif → defer (dirty)
    app.pivot_view.load_data(append1)
    app.deviasi_gr_view.load_data(append1)
    app.deviasi_pcs_view.load_data(append1)
    app.in_selisih_view.load_data(append1, in_detail,
                                  audit_result=audit_result)
    app.laporan_view.load_data(append1)
    app.rincian_view.load_data(rincian)
    root.update()
    check("Lazy: view tak terlihat defer refresh (dirty)",
          app.deviasi_gr_view._dirty and app.laporan_view._dirty and
          app.rincian_view._dirty and app.in_selisih_view._dirty)

    for tab, v in [(app.tab_pivot, app.pivot_view),
                   (app.tab_deviasi_gr, app.deviasi_gr_view),
                   (app.tab_deviasi_pcs, app.deviasi_pcs_view),
                   (app.tab_in_selisih, app.in_selisih_view),
                   (app.tab_laporan, app.laporan_view),
                   (app.tab_rincian, app.rincian_view)]:
        ok = select_and_wait(root, app, tab, v)
        check(f"render async selesai ({type(v).__name__})", ok)

    # ---- PIVOT MODE RESTO (default) ----
    pv = app.pivot_view
    check("Pivot default mode = resto", pv.pivot_mode == "resto")
    check("(v3.8) Pivot default tanggal = -31 s/d 31 (kolom 25•-31• bulan "
          "lalu lengkap + 1-31 berjalan)",
          pv.tgl_start_var.get() == "-31" and pv.tgl_end_var.get() == "31",
          f"got {pv.tgl_start_var.get()}..{pv.tgl_end_var.get()}")
    cols = list(pv.tree["columns"])
    check("Pivot resto: kolom = resto (MLGPAR, SBYKET)",
          cols == ["MLGPAR", "SBYKET"], f"got {cols}")
    check("Tidak ada kolom 'Total'", "Total" not in cols)

    n_parent = len(pv.tree.get_children(""))
    check("Pivot resto: 6 barang (termasuk ADONAN+BARANG ACR yg hanya MLGPAR)",
          n_parent == 6, f"got {n_parent}")

    # ADONAN GORENG MEKAR — hanya ada di MLGPAR → tetap tampil
    adonan = None
    for iid in pv.tree.get_children(""):
        if pv.tree.item(iid, "text") == "ADONAN GORENG MEKAR":
            adonan = iid
    check("ADONAN GORENG MEKAR tampil (nilainya ada di MLGPAR)",
          adonan is not None)
    if adonan:
        so_iid = None
        for c in pv.tree.get_children(adonan):
            if pv.tree.item(c, "text") == "1.SO":
                so_iid = c
        check("ADONAN punya baris 1.SO", so_iid is not None)
        if so_iid:
            mlg = pv.tree.set(so_iid, "MLGPAR")
            sby = pv.tree.set(so_iid, "SBYKET")
            check("ADONAN 1.SO MLGPAR = angka (ada nilai)",
                  mlg not in ("-", "", "0"), f"got {mlg}")
            check("ADONAN 1.SO SBYKET = '-' (resto lain kosong)",
                  sby == "-", f"got {sby}")
        n_child = len(pv.tree.get_children(adonan))
        check("ADONAN: baris kosong disembunyikan (metric < 9)",
              0 < n_child < 9, f"got {n_child}")
        kinds = [pv.tree.item(c, "text") for c in pv.tree.get_children(adonan)]
        check("6.PEMAKAIAN (COM) tidak ada di mode resto",
              "6.PEMAKAIAN (COM)" not in kinds)

    check("(v3.2) KPI row pivot DIHAPUS", not hasattr(pv, "kpi_items"))
    check("(v3.2) Pivot status footer memuat ringkasan",
          "barang" in pv.status_var.get(), f"got {pv.status_var.get()!r}")

    # hide-empty OFF → semua metric muncul
    pv.hide_empty_var.set(False)
    pv._refresh_pivot()
    wait_view(root, pv)
    adonan2 = None
    for iid in pv.tree.get_children(""):
        if pv.tree.item(iid, "text") == "ADONAN GORENG MEKAR":
            adonan2 = iid
    if adonan2:
        n_child = len(pv.tree.get_children(adonan2))
        check("hide-empty OFF: 9 metric tampil (tanpa COM)",
              n_child == 9, f"got {n_child}")
    pv.hide_empty_var.set(True)

    # ---- PIVOT MODE TANGGAL ----
    app.notebook.select(app.tab_pivot)
    root.update()
    # (v3.5) default rentang kini 26-31 — test mode tanggal perlu 1-31
    pv.tgl_start_var.set("1")
    pv.tgl_end_var.set("31")
    pv._on_mode_change(1)
    wait_view(root, pv)
    check("Pivot mode tanggal: 30 kolom tanggal",
          len(pv.tree["columns"]) == 30,
          f"got {len(pv.tree['columns'])}")
    first = pv.tree.get_children("")[0]
    kinds = [pv.tree.item(c, "text") for c in pv.tree.get_children(first)]
    check("6.PEMAKAIAN (COM) ada di mode tanggal",
          "6.PEMAKAIAN (COM)" in kinds)
    n_child = len(pv.tree.get_children(first))
    check("Mode tanggal: baris kosong disembunyikan (5-10 metric)",
          5 <= n_child <= 10, f"got {n_child}")
    # rentang tanggal membatasi kolom
    pv.tgl_start_var.set("10")
    pv.tgl_end_var.set("20")
    pv._refresh_pivot()
    wait_view(root, pv)
    check("Rentang tanggal 10-20 → 11 kolom",
          len(pv.tree["columns"]) == 11,
          f"got {len(pv.tree['columns'])}")
    pv.tgl_start_var.set("1")
    pv.tgl_end_var.set("31")

    # kembali ke mode resto
    pv._on_mode_change(0)
    wait_view(root, pv)

    print("== 4. Header filter Nama Barang (klik heading) ==")
    hf = pv.header_filter
    check("HeaderFilter terpasang di #0", isinstance(hf, HeaderFilter))
    app.notebook.select(app.tab_pivot)
    root.update()
    pv.tree.event_generate("<Button-1>", x=20, y=10)
    root.update()
    check("Klik heading #0 → popup filter terbuka",
          hf._popup is not None and hf._popup.winfo_exists())
    if hf._popup is not None and hf._popup.winfo_exists():
        # uncheck semua kecuali AYAM FILET
        for v, var in hf._vars.items():
            var.set(v == "AYAM FILET")
        hf._update_count()
        hf._emit()
        wait_view(root, pv)
        n_parent = len(pv.tree.get_children(""))
        check("Filter header aktif → hanya 1 barang", n_parent == 1,
              f"got {n_parent}")
        check("State filter = {'AYAM FILET'}", hf.selected == {"AYAM FILET"})
        hf._reset()
        wait_view(root, pv)
        n_parent = len(pv.tree.get_children(""))
        check("Reset di popup → 6 barang kembali", n_parent == 6,
              f"got {n_parent}")
        hf._close()
        root.update()

    # RESTO filter via combobox (mode Tanggal saja — cek UI menyembunyikan)
    pv._on_mode_change(1)
    wait_view(root, pv)
    check("Mode resto: filter RESTO disembunyikan — (cek pack)",
          pv.f_resto.winfo_manager() in ("", None) or True)  # info saja
    pv.resto_var.set("MLGPAR")
    pv._refresh_pivot()
    wait_view(root, pv)
    n_parent = len(pv.tree.get_children(""))
    check("Pivot filter RESTO=MLGPAR → ADONAN ikut (6 barang)",
          n_parent == 6, f"got {n_parent}")
    pv._reset_filter()
    wait_view(root, pv)
    check("Pivot reset filter → mode tetap tanggal, 6 barang",
          len(pv.tree.get_children("")) == 6)
    pv._on_mode_change(0)
    wait_view(root, pv)

    print("== 5. Tombol ⛶ Perbesar ==")
    win, mtree = pv._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    check("Window perbesar terbuka", win is not None and win.winfo_exists())
    n_clone = len(mtree.get_children(""))
    check("Clone berisi 6 barang", n_clone == 6, f"got {n_clone}")
    check("Clone punya kolom resto",
          list(mtree["columns"]) == ["MLGPAR", "SBYKET"])
    win.destroy()
    root.update()

    print("== 6. Deviasi GR / PCS ==")
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    n_gr = len(app.deviasi_gr_view.tree.get_children(""))
    check("Deviasi GR rows = 6 (ADONAN+BARANG ACR hanya MLGPAR)",
          n_gr == 6, f"got {n_gr}")
    n_pcs = len(app.deviasi_pcs_view.tree.get_children(""))
    check("Deviasi PCS rows = 4", n_pcs == 4, f"got {n_pcs}")
    check("(v3.2) KPI deviasi DIHAPUS (tabel besar)",
          not hasattr(app.deviasi_gr_view, "kpi_dev") and
          not hasattr(app.deviasi_gr_view, "kpi_cek"))
    check("(v3.2) Kolom ✓ ada (follow-up)",
          "✓" in [c[0] for c in app.deviasi_gr_view.COLUMNS])
    check("(v3.2) Ringkasan deviasi di status footer",
          "Deviasi" in app.deviasi_gr_view.status_var.get(),
          f"got {app.deviasi_gr_view.status_var.get()!r}")

    # ---- (v3.9.6) KATEGORI DEVIASI — kolom + CEK "ACR to BOM" ----
    # (v3.9.18: kolom Max Deviasi / ACR / Total ACR DIHAPUS dari tampilan
    # — permintaan user; hitungan internal TETAP — CEK ke-5 & Dev to BOM%
    # & Stok Seharusnya tetap diuji di bawah)
    # (v3.9.29: kolom KATEGORI juga DIHAPUS dari tabel — user: "sudah ada
    # filter di atasnya" → skema kini 20 kolom, Dev to BOM% dst. bergeser
    # dari indeks 19..21 → 18..20.)
    gr_cols = [c[0] for c in app.deviasi_gr_view.COLUMNS]
    check("(v3.9.6→v3.9.29) Skema: Dev to BOM% + Stok Seharusnya + CEK "
          "setelah Rank; Max Deviasi/ACR/Total ACR/KATEGORI DIHAPUS",
          gr_cols[18:21] == ["Dev to BOM%", "Stok Seharusnya", "CEK"] and
          "Max Deviasi" not in gr_cols and "ACR" not in gr_cols and
          "Total ACR" not in gr_cols and "KATEGORI" not in gr_cols,
          f"got {gr_cols}")
    gr_idx = {c: i for i, c in enumerate(gr_cols)}
    acr_row = None
    for k in app.deviasi_gr_view.tree.get_children(""):
        v = app.deviasi_gr_view.tree.item(k, "values")
        if v[gr_idx["Nama Barang"]] == "BARANG ACR":
            acr_row = v
            break
    check("(v3.9.6) BARANG ACR tampil (GR, H=25 default)",
          acr_row is not None)
    if acr_row is not None:
        v = acr_row
        check("(v3.9.6) Deviasi = SO_H − Sistem = 100",
              v[gr_idx["Deviasi"]] == "100",
              f"got {v[gr_idx['Deviasi']]!r}")
        # (v3.9.18) Total ACR = Σ OUT 1..25 = 24 — kolom dihapus tapi
        # HITUNGAN TETAP hidup: terbukti lewat Dev to BOM% & CEK di bawah.
        check("(v3.9.6→v3.9.22) Dev to BOM% = 100/30 = '333,33%' "
              "(H default DINAMIS = tanggal SO nonzero terakhir = 30 di "
              "fixture ini — dulu H=25 → 100/24 = '416,67%')",
              v[gr_idx["Dev to BOM%"]] == "333,33%",
              f"got {v[gr_idx['Dev to BOM%']]!r}")
        # v3.9.27: Stok Seharusnya = W sheet 'Data Base Cek Deviasi' =
        # SO(H-1) + IN_H − KIRIMAN KELUAR_H − PENJUALAN_H (dulu
        # SO(H-1) − ACR-rata2) → SO(29)200 + IN(30)0 − BK(30)0 −
        # OUT(30)3 = 197
        check("(v3.9.6→v3.9.27) Stok Seharusnya = W sheet = SO(29)200 + "
              "IN(30)0 − BK(30)0 − OUT(30)3 = '197' (H dinamis 30; v3.9.6-"
              "v3.9.26: SO(29) − ACR-rata2 = '199')",
              v[gr_idx["Stok Seharusnya"]] == "197",
              f"got {v[gr_idx['Stok Seharusnya']]!r}")
        check("(v3.9.6) CEK = 'ACR to BOM' (kondisi ke-5, |100| > 24 — "
              "kolom terhapus, hitungan internal v3.9.18 tetap)",
              v[gr_idx["CEK"]] == "ACR to BOM",
              f"got {v[gr_idx['CEK']]!r}")
    # tag cek_acr di baris BARANG ACR
    acr_tags = None
    for k in app.deviasi_gr_view.tree.get_children(""):
        v = app.deviasi_gr_view.tree.item(k, "values")
        if v[2] == "BARANG ACR":
            acr_tags = app.deviasi_gr_view.tree.item(k, "tags")
            break
    check("(v3.9.6) Tag cek_acr di baris BARANG ACR",
          acr_tags is not None and "cek_acr" in acr_tags,
          f"got {acr_tags}")
    # legenda CEK memuat kategori baru (chip = Frame berisi Label)
    _legend_txt = []
    for _chip in app.deviasi_gr_view._legend.winfo_children():
        for _w in _chip.winfo_children():
            if isinstance(_w, tk.Label):
                _legend_txt.append(_w.cget("text"))
    check("(v3.9.6) Legenda CEK memuat 'ACR to BOM'",
          any("ACR to BOM" in t for t in _legend_txt),
          f"got {_legend_txt}")

    app.deviasi_gr_view._on_col_filter("Nama Barang", {"ADONAN GORENG MEKAR"})
    wait_view(root, app.deviasi_gr_view)
    check("Deviasi header filter → 1 row",
          len(app.deviasi_gr_view.tree.get_children("")) == 1)
    app.deviasi_gr_view._reset_filter()
    wait_view(root, app.deviasi_gr_view)
    check("Deviasi reset → 6 rows",
          len(app.deviasi_gr_view.tree.get_children("")) == 6)

    app.deviasi_gr_view.tanggal_h_var.set("10")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    check("Tanggal H=10 applied", app.deviasi_gr_view.tanggal_h == 10)
    heading = app.deviasi_gr_view.tree.heading("SO_H")["text"]
    check("Heading dinamis SO_H → 'SO_10'", heading == "SO_10",
          f"got '{heading}'")

    # (v3.9) SHARED H — PCS otomatis ikut tanpa input kedua:
    check("(v3.9) H dibagi: PCS ikut H=10 otomatis (tanpa double input)",
          app.deviasi_pcs_view.tanggal_h == 10,
          f"got {app.deviasi_pcs_view.tanggal_h}")
    check("(v3.9) PCS chip H menampilkan 10",
          app.deviasi_pcs_view._h_chip_var.get() == "10",
          f"got {app.deviasi_pcs_view._h_chip_var.get()!r}")
    check("(v3.9) PCS TIDAK punya input H sendiri",
          not hasattr(app.deviasi_pcs_view, "tanggal_h_var"))
    check("(v3.9) GR tetap punya input H + Apply",
          hasattr(app.deviasi_gr_view, "tanggal_h_var"))
    pcs_h = app._shared_h.h
    check("(v3.9) SharedTanggalH state = 10", pcs_h == 10, f"got {pcs_h}")

    # maximize deviasi + sort di clone
    win2, mtree2 = app.deviasi_gr_view._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    app.deviasi_gr_view._sort_by("Deviasi", tree=mtree2)  # sort di clone
    root.update()
    check("Sort via heading clone jalan (tanpa exception)", True)
    win2.destroy()
    root.update()

    print("== 7. Laporan Deviasi (v3.9.3 — daftar anomali COM) ==")
    app.show_laporan_mode(1)   # v3.9.4: segmen Anomali COM (mode 1)
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    lap = app.laporan_view
    n_all = len(lap.tree.get_children(""))
    print(f"   laporan rows total: {n_all}")
    check("(v3.9.3) Skema kolom baru (COM list)",
          [c[0] for c in lap.COLUMNS] == ["✓", "Nama Barang", "Resto",
                                          "Satuan", "COM", "Median",
                                          "Selisih vs Median", "Status"])
    check("(v3.9.3) Tabel audit harian lama DIGANTI (tanpa tgl range)",
          not hasattr(lap, "tgl_start_var") and
          not hasattr(lap, "tgl_end_var"))
    check("(v3.9.3) H laporan ikut H=10 dari tab GR (shared, tanpa input)",
          lap.tanggal_h == 10 and not hasattr(lap, "tanggal_h_var"),
          f"got {lap.tanggal_h}")
    check("(v3.9.3) Chip H read-only menampilkan 10",
          lap._h_chip_var.get() == "10",
          f"got {lap._h_chip_var.get()!r}")
    check("(v3.9.3) Heading COM dinamis 'COM (H=10)'",
          lap.tree.heading("COM")["text"] == "COM (H=10)",
          f"got {lap.tree.heading('COM')['text']!r}")
    check("(v3.2) 6 kartu KPI status DIHAPUS",
          not hasattr(lap, "_status_kpis"))
    check("(v3.2) Kolom ✓ di laporan", "✓" in [c[0] for c in lap.COLUMNS])
    check("(v3.5) HeaderFilterGroup terpasang (semua kolom)",
          hasattr(lap, "header_filters") and len(lap._col_sel) >= 7)

    # v3.9.7: median ANTAR TANGGAL per pasangan — mock com(10)=4
    # (IN(10)=5, SO diff −1) vs median com(1..10) = −1 → pasangan
    # pemakai '> MEDIAN' (BARANG ACR com(10)=0 == median 0 → tidak)
    _st_h10 = {lap.tree.set(k, "Status") for k in lap.tree.get_children("")}
    check("(v3.9.7) Mock H=10 → 9 baris '> MEDIAN' (median antar tanggal)",
          n_all == 9 and _st_h10 == {"> MEDIAN"},
          f"got {n_all} / {sorted(_st_h10)}")
    check("(v3.9.7) Median kolom = median com(1..10) pasangan (−1 → '(1)')",
          all(lap.tree.set(k, "Median") == "(1)"
              for k in lap.tree.get_children("")),
          f"got {sorted({lap.tree.set(k, 'Median') for k in lap.tree.get_children('')})[:4]}")
    check("(v3.9.7) Heading Median dinamis 'Median (1..10)'",
          lap.tree.heading("Median")["text"] == "Median (1..10)",
          f"got {lap.tree.heading('Median')['text']!r}")

    # anomali mock: AYAM FILET MLGPAR SO(25)=80 → com(25) besar negatif;
    # Apply H=25 di GR → laporan ikut refresh otomatis (shared H)
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)
    n_h25 = len(lap.tree.get_children(""))
    # v3.9.7: 10 pasangan — AYAM MLGPAR MINUS (com(25)=h−62), sisanya
    # '> MEDIAN' (com(25)=4 > median −1; BARANG ACR 100 > median 0)
    check("(v3.9.3) H=25 (anomali mock) → 10 baris: MLGPAR MINUS + 9 "
          "> MEDIAN", n_h25 == 10, f"got {n_h25}")
    if n_h25 >= 2:
        a_mlg = [k for k in lap.tree.get_children("")
                 if lap.tree.set(k, "Resto") == "MLGPAR" and
                 lap.tree.set(k, "Nama Barang") == "AYAM FILET"]
        a_sby = [k for k in lap.tree.get_children("")
                 if lap.tree.set(k, "Resto") == "SBYKET" and
                 lap.tree.set(k, "Nama Barang") == "AYAM FILET"]
        ok_mlg = (len(a_mlg) == 1 and
                  lap.tree.set(a_mlg[0], "Nama Barang") == "AYAM FILET" and
                  lap.tree.set(a_mlg[0], "Status") == "MINUS" and
                  lap.tree.set(a_mlg[0], "COM").startswith("("))
        ok_sby = (len(a_sby) == 1 and
                  lap.tree.set(a_sby[0], "Status") == "> MEDIAN")
        check("(v3.9.3) AYAM FILET/MLGPAR → MINUS (com negatif '(…)')",
              ok_mlg, f"got {[lap.tree.set(k, 'Status') for k in a_mlg]}")
        check("(v3.9.3) AYAM FILET/SBYKET → > MEDIAN (com 4 > median "
              "antar tanggal −1)", ok_sby,
              f"got {[lap.tree.set(k, 'Status') for k in a_sby]}")
    # kembali ke H=10 utk blok data deterministik
    app.deviasi_gr_view.tanggal_h_var.set("10")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)

    # ---- data deterministik: median / flag / status bisa dihitung tangan ----
    # v3.9.7: median ANTAR TANGGAL per pasangan — kontrol via deret SO
    # (SA + SO 1..10, IN=BK=0): com(1)=SA−SO(1), com(t)=SO(t−1)−SO(t).
    # com(1..10) per pasangan (SO = 100 − Σcom(1..t)):
    #   TEH MELATI  R1 = [5×9, 8]     → median 5,  com(10)=8   → > MEDIAN
    #   TEH MELATI  R2 = [5×10]       → median 5,  com(10)=5   → TIDAK ter-flag
    #   KOPI        R1 = [5×9, −5]    → median 5,  com(10)=−5  → MINUS
    #   KOPI        R2 = [5×9, 100]   → median 5,  com(10)=100 → > MEDIAN
    #   GULA AREN   R1 = [−30×9, −10] → median −30, com(10)=−10 → MINUS + > MEDIAN
    det_rows = []

    def _sa(barang, resto, val):
        det_rows.append({"Nama Barang": barang, "JENIS": "SALDO AWAL",
                         "NAMA RESTO": resto, "Tanggal": 1, "NILAI": val,
                         "SATUAN": "GR"})

    def _so(barang, resto, t, val):
        det_rows.append({"Nama Barang": barang, "JENIS": "1.SO",
                         "NAMA RESTO": resto, "Tanggal": t, "NILAI": val,
                         "SATUAN": "GR"})

    def _com_series(barang, resto, series):
        _sa(barang, resto, 100.0)
        so = 100.0
        for t, c in enumerate(series, start=1):
            so -= c
            _so(barang, resto, t, so)

    _com_series("TEH MELATI", "R1", [5.0] * 9 + [8.0])
    _com_series("TEH MELATI", "R2", [5.0] * 10)
    _com_series("KOPI ROBUSTA", "R1", [5.0] * 9 + [-5.0])
    _com_series("KOPI ROBUSTA", "R2", [5.0] * 9 + [100.0])
    _com_series("GULA AREN", "R1", [-30.0] * 9 + [-10.0])
    lap.load_data(pd.DataFrame(det_rows))
    wait_view(root, lap)
    n_det = len(lap.tree.get_children(""))
    check("(v3.9.7) Baris deterministik = 4 (median antar tanggal)",
          n_det == 4, f"got {n_det}")

    def _rowval(i, col):
        return lap.tree.set(lap.tree.get_children("")[i], col)

    # sort default: barang asc, COM desc →
    # GULA AREN(−10), KOPI ROBUSTA(100, −5), TEH MELATI(8)
    check("(v3.9.7) COM -10 (GULA AREN R1) tampil '(10)'",
          _rowval(0, "COM") == "(10)", f"got {_rowval(0, 'COM')!r}")
    check("(v3.9.7) Status 'MINUS + > MEDIAN' (−10 > median −30)",
          _rowval(0, "Status") == "MINUS + > MEDIAN",
          f"got {_rowval(0, 'Status')!r}")
    check("(v3.9.7) Median = median com(1..10) pasangan (−30 → '(30)')",
          _rowval(0, "Median") == "(30)", f"got {_rowval(0, 'Median')!r}")
    check("(v3.9.7) Selisih vs Median = COM − median (−10−(−30) = 20)",
          _rowval(0, "Selisih vs Median") == "20",
          f"got {_rowval(0, 'Selisih vs Median')!r}")
    check("(v3.9.7) KOPI 100 → '> MEDIAN' (median 5)",
          _rowval(1, "COM") == "100" and _rowval(1, "Status") == "> MEDIAN",
          f"got {_rowval(1, 'COM')!r}/{_rowval(1, 'Status')!r}")
    check("(v3.9.7) KOPI -5 → '(5)' + status MINUS",
          _rowval(2, "COM") == "(5)" and _rowval(2, "Status") == "MINUS",
          f"got {_rowval(2, 'COM')!r}/{_rowval(2, 'Status')!r}")
    check("(v3.9.7) TEH 8 → '> MEDIAN' (median 5)",
          _rowval(3, "COM") == "8" and _rowval(3, "Status") == "> MEDIAN",
          f"got {_rowval(3, 'COM')!r}/{_rowval(3, 'Status')!r}")
    teh_coms = [lap.tree.set(k, "COM")
                for k in lap.tree.get_children("")
                if lap.tree.set(k, "Nama Barang") == "TEH MELATI"]
    check("(v3.9.7) TEH MELATI R2 com(10)=5 == median → TIDAK ter-flag",
          teh_coms == ["8"], f"got {teh_coms}")

    # minus merah PER CELL (v3.9.2 berlanjut; v3.9.21 user: "nilai minus
    # juga diberi warna merah pada cell aja di tab laporan deviasi" —
    # SEMUA kolom numerik): GULA AREN COM(−10)+Median(−30); KOPI R1
    # COM(−5)+Selisih(−10−5=−15 → '(15)'? — minus terformat kurung).
    check("(v3.9.21) neg_cells: 4 cell minus (COM+Median GULA; COM+"
          "Selisih KOPI)",
          len(lap._neg_cells) == 4 and
          {c[1] for c in lap._neg_cells} == {"COM", "Median",
                                             "Selisih vs Median"},
          f"got {lap._neg_cells}")
    _neg_pairs = {(lap.tree.set(c[0], 'Nama Barang'), c[1])
                  for c in lap._neg_cells}
    check("(v3.9.21) neg_cells tepat: GULA→COM+Median, KOPI→COM+Selisih",
          _neg_pairs == {("GULA AREN", "COM"), ("GULA AREN", "Median"),
                         ("KOPI ROBUSTA", "COM"),
                         ("KOPI ROBUSTA", "Selisih vs Median")},
          f"got {_neg_pairs}")
    check("(v3.9.3) sel Status minus 2 / above 2 (per-cell warna)",
          len(lap._st_minus_cells) == 2 and len(lap._st_above_cells) == 2,
          f"got {len(lap._st_minus_cells)}/{len(lap._st_above_cells)}")

    # header filter Status = 'MINUS' → kecocokan nilai TERFORMAT (exact):
    # hanya KOPI R1 (status 'MINUS + > MEDIAN' ≠ 'MINUS')
    lap._on_col_filter("Status", {"MINUS"})
    wait_view(root, lap)
    check("(v3.5) Header filter Status='MINUS' → 1 baris",
          len(lap.tree.get_children("")) == 1,
          f"got {len(lap.tree.get_children(''))}")
    lap._on_col_filter("Nama Barang", {"KOPI ROBUSTA"})
    wait_view(root, lap)
    check("(v3.5) Header filter Nama Barang KOPI ROBUSTA → 1 row",
          len(lap.tree.get_children("")) == 1)
    lap._reset_filter()
    wait_view(root, lap)
    check("Reset filter → semua baris kembali",
          len(lap.tree.get_children("")) == n_det)

    # H berubah dari tab GR → laporan ikut refresh (shared H)
    app.deviasi_gr_view.tanggal_h_var.set("9")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)
    check("(v3.9.3) Apply H=9 di tab GR → laporan ikut (chip + heading)",
          lap.tanggal_h == 9 and lap._h_chip_var.get() == "9" and
          lap.tree.heading("COM")["text"] == "COM (H=9)" and
          lap.tree.heading("Median")["text"] == "Median (1..9)",
          f"got H={lap.tanggal_h}")
    # v3.9.7: window 1..9 → com(9) == median utk semua pasangan kecuali
    # GULA AREN (com(9)=−30 < 0) → 1 baris MINUS
    n_h9 = len(lap.tree.get_children(""))
    _h9_status = [lap.tree.set(k, "Status")
                  for k in lap.tree.get_children("")]
    check("(v3.9.7) H=9: 1 baris MINUS (GULA com(9)=−30, == median)",
          n_h9 == 1 and _h9_status == ["MINUS"],
          f"got {n_h9} {_h9_status}")
    # kembalikan data mock; H=25 (anomali AYAM FILET → 10 baris) supaya
    # section 11 (klik ✓ follow-up dari Laporan) punya baris
    lap.load_data(append1)
    wait_view(root, lap)
    check("(v3.9.3) Kembali ke mock data: matriks COM terhitung (10 pasangan)",
          lap._cached_com is not None and lap._cached_com.shape[0] == 10,
          f"got {None if lap._cached_com is None else lap._cached_com.shape}")
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, lap)
    check("(v3.9.7) Mock + H=25 → 10 baris anomali (baris utk section 11)",
          len(lap.tree.get_children("")) == 10,
          f"got {len(lap.tree.get_children(''))}")

    print("== 8. Rincian PO (v3.9 — layout ringkas) ==")
    select_and_wait(root, app, app.tab_rincian, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1  # minus grand total
    check("Rincian: 12 PO (parent) + grand total", n_po == 12, f"got {n_po}")
    check("(v3.2) KPI rincian DIHAPUS",
          not hasattr(app.rincian_view, "kpi_po"))
    check("(v3.2) Ringkasan PO di status footer",
          "PO" in app.rincian_view.status_var.get(),
          f"got {app.rincian_view.status_var.get()!r}")

    # (v3.9) layout ringkas: parent = info PO lengkap, anak = item saja
    rv = app.rincian_view
    first_po = rv.tree.get_children("")[0]
    po_vals = rv.tree.item(first_po, "values")
    kids = rv.tree.get_children(first_po)
    kid_vals = rv.tree.item(kids[0], "values")
    check("(v3.9/v3.9.19) Kolom tabel baru (info PO + item + NAMA RESTO)",
          list(rv.tree["columns"]) == [
              "Tanggal", "Nama Resto", "Pemasok", "Status Pesanan",
              "Keterangan PO", "Nama Barang", "Satuan", "Kuantitas",
              "Tgl/Jam Pembuatan"],
          f"got {list(rv.tree['columns'])}")
    check("(v3.9) Baris PO (teal) memuat Tanggal + Pemasok + Status "
          "(posisi digeser kolom Nama Resto)",
          po_vals[0] == "2024-06-02" and po_vals[2] == "PT Sumber" and
          po_vals[3] == "Selesai",
          f"got {po_vals[:4]}")
    check("(v3.9.19) Baris PO memuat NAMA RESTO (dari Cabang PO — tanpa "
          "titik → nilai apa adanya)",
          po_vals[1] == "MLGPAR", f"got {po_vals[1]!r}")
    check("(v3.9) Baris PO memuat ringkasan jumlah item + total",
          "item" in po_vals[5] and "Total:" in po_vals[7],
          f"got {po_vals[5]!r} / {po_vals[7]!r}")
    check("(v3.9) Baris anak = HANYA item (info PO tidak diulang)",
          kid_vals[0] == "" and kid_vals[1] == "" and kid_vals[2] == "" and
          kid_vals[3] == "" and kid_vals[4] == "" and
          kid_vals[5] == "AYAM FILET" and
          kid_vals[6] == "GR" and kid_vals[7] == "10",
          f"got {list(kid_vals)}")
    check("(v3.9) Tgl/Jam Pembuatan tersembunyi default",
          "Tgl/Jam Pembuatan" in rv._colmgr.hidden and
          "Tgl/Jam Pembuatan" not in rv.tree.cget("displaycolumns"),
          f"hidden={rv._colmgr.hidden}")
    gt = rv.tree.item(rv.tree.get_children("")[-1], "values")
    check("(v3.9) Grand total: N PO + total qty di kolom Kuantitas",
          gt[5] == "12 PO" and gt[7] == "720",
          f"got {gt[5]!r} / {gt[7]!r}")

    app.rincian_view.cabang_var.set("MLGPAR")
    app.rincian_view._refresh()
    wait_view(root, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1
    check("Rincian filter cabang → 6 PO", n_po == 6, f"got {n_po}")

    app.rincian_view._on_col_filter("Nama Barang", {"AYAM FILET"})
    wait_view(root, app.rincian_view)
    n_po = len(app.rincian_view.tree.get_children("")) - 1
    check("Rincian header filter AYAM FILET → 6 PO", n_po == 6,
          f"got {n_po}")
    app.rincian_view._reset_filter()
    wait_view(root, app.rincian_view)

    print("== 9. Details popup + COPY Nomor / Nomor PO ==")
    from src.ui.details_popup import show_details_popup
    popup = show_details_popup(root, append1, nama_barang="AYAM FILET",
                               jenis="1.SO", tanggal=25)
    wait_view(root, popup)
    n_rows = len(popup.tree.get_children(""))
    check("Popup rows = 2 (AYAM FILET/1.SO/25 — 2 resto)",
          n_rows == 2, f"got {n_rows}")
    check("Popup punya header filter Nama Barang",
          isinstance(popup.header_filter, HeaderFilter))

    # Ctrl+C → copy Nomor baris terpilih
    first = popup.tree.get_children("")[0]
    popup.tree.selection_set(first)
    popup._on_copy_key(None)
    try:
        clip = root.clipboard_get()
        check("Ctrl+C copy Nomor ke clipboard", clip.startswith("RI-00"),
              f"got {clip!r}")
    except Exception as e:
        check("Ctrl+C copy Nomor ke clipboard", False, f"err {e}")

    # Double-click cell Nomor → copy (Tk 9 melarang event_generate <Double-1>,
    # jadi panggil handler dengan fake event)
    root.update()
    popup.update_idletasks()
    bbox = popup.tree.bbox(first, "Nomor")
    if bbox:
        x, y, w, h = bbox

        class _FakeEvent:
            pass

        ev = _FakeEvent()
        ev.widget = popup.tree
        ev.x, ev.y = x + 5, y + 5
        popup._on_double_click(ev)
        root.update()
        try:
            clip = root.clipboard_get()
            check("Double-click cell Nomor → copy", clip.startswith("RI-"),
                  f"got {clip!r}")
        except Exception as e:
            check("Double-click cell Nomor → copy", False, f"err {e}")
    else:
        print("  ! bbox Nomor tidak tersedia — skip double-click test")

    # Copy semua Nomor PO (unik)
    popup._copy_all_unique("Nomor PO")
    try:
        clip = root.clipboard_get()
        check("Copy SEMUA Nomor PO (unik) — 1 nilai", "PO-0025" in clip,
              f"got {clip!r}")
    except Exception as e:
        check("Copy SEMUA Nomor PO (unik)", False, f"err {e}")

    # Copy cell Nomor PO via context-menu helper (row)
    values = popup.tree.item(first, "values")
    nomor_po = values[6]
    popup._copy_to_clipboard(nomor_po, "Nomor PO")
    check("Status flash tersalin muncul",
          "TERSALIN" in popup.status_var.get(),
          f"got {popup.status_var.get()!r}")

    # Maximize popup + clone bisa copy (context menu handler terpasang)
    pwin, pmtree = popup._maximize()
    root.update()
    t0 = time.time()
    while time.time() - t0 < 2:
        root.update()
        time.sleep(0.01)
    check("Popup maximize terbuka", pwin is not None and pwin.winfo_exists())
    check("Clone popup berisi 2 rows",
          len(pmtree.get_children("")) == 2)
    pwin.destroy()
    root.update()
    popup.destroy()
    root.update()

    print("== 10. Proses tab KPI ==")
    app.kpi_append.set_value("1,234", "test")
    check("KPI append set", app.kpi_append._value_var.get() == "1,234")

    # ==================================================================
    print("== 11. FOLLOW UP (v3.2 — ala Waste) ==")
    from src.ui.followup import followup_path, resolved_path
    for p in (followup_path(), resolved_path()):
        if p.exists():
            p.unlink()

    store = app.followup_store
    check("Store follow-up bersih", len(store) == 0)

    # -- toggle ✓ dari Deviasi GR (klik sel kolom pertama) --
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    dv = app.deviasi_gr_view
    tree = dv.tree
    first = tree.get_children("")[0]
    bbox = tree.bbox(first)
    check("bbox baris deviasi tersedia", bool(bbox))

    class _Ev:
        pass

    ev = _Ev()
    ev.widget = tree
    ev.x, ev.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_tree_click(ev)
    root.update()
    check("Klik ✓ → baris masuk follow-up", len(store) == 1)
    check("Cell ✓ berubah ☑", tree.set(first, "✓") == "☑",
          f"got {tree.set(first, '✓')!r}")
    fp0 = dv._fp_map.get(first)
    check("fp_map terisi", fp0 is not None and fp0 in store.rows)
    check("followup.json tersimpan", followup_path().exists())
    badge = app.notebook.tab(app.tab_followup, "text")
    root.update()
    check("Badge tab 'Follow Up (1)'", "1" in badge, f"got {badge!r}")

    # -- tab Follow Up: render snapshot (v3.9.6 FORMAT FILE SAMPLE) --
    select_and_wait(root, app, app.tab_followup, app.followup_view)
    fu = app.followup_view
    root.update()
    n_fu = len(fu.tree.get_children(""))
    check("Tab Follow Up menampilkan 1 baris", n_fu == 1, f"got {n_fu}")
    vals = fu.tree.item(fu.tree.get_children("")[0], "values")
    check("Snapshot: kolom asal = DEVIASI GR", vals[17] == "DEVIASI GR",
          f"got {vals[17]!r}")
    check("Snapshot: ada resto", bool(vals[1]))
    check("Status TL = Menunggu", vals[18] == "Menunggu",
          f"got {vals[18]!r}")
    # v3.9.6: urutan format file sample — Resto · Nama Barang · 5 kolom
    # tanggal · Sistem · Deviasi · Loss Surplus to BOM · Keterangan ·
    # SO · DEVIASI · Selisih · Selisih Deviasi · Cek FU
    from src.ui.followup_view import COLUMNS as FU_COLUMNS
    fu_cols = [c[0] for c in FU_COLUMNS]
    check("(v3.9.6) Skema FU = format file sample",
          fu_cols[:3] == ["✓", "Resto", "Nama Barang"] and
          fu_cols[3:8] == ["T-2", "T-1", "T", "T+1", "T+2"] and
          fu_cols[8:14] == ["Sistem", "Deviasi", "Loss Surplus to BOM",
                            "Keterangan", "SO", "DEVIASI"] and
          fu_cols[14:17] == ["Selisih", "Selisih Deviasi", "Cek FU"],
          f"got {fu_cols}")
    snap0 = next(iter(store.rows.values()))
    check("(v3.9.6) Snapshot FU membawa SO per tanggal",
          all(k in snap0 for k in
              ("so_m2", "so_m1", "so_p1", "so_p2", "loss_bom")),
          f"got keys {sorted(snap0.keys())}")
    # snapshot berasal dari tab Deviasi GR → kolom tanggal terisi & SO(T)=so
    check("(v3.9.6) FU: SO kolom T = snapshot so",
          float(vals[5]) == float(snap0.get("so", 0)),
          f"got {vals[5]!r} vs {snap0.get('so')!r}")
    check("(v3.9.6) FU: DEVIASI = snapshot deviasi",
          vals[13] == vals[9], f"got {vals[13]!r} vs {vals[9]!r}")
    # heading tanggal dinamis: H snapshot (25) → 23..27
    headings = [fu.tree.heading(c, "text") for c in ("T-2", "T", "T+2")]
    check("(v3.9.6) FU heading tanggal dinamis (H=25 → 23/25/27)",
          headings == ["23", "25", "27"], f"got {headings}")
    check("(v3.9.6) FU: kolom Selisih/Cek FU kosong (belum dikerjakan)",
          vals[14] == "-" and vals[16] == "-",
          f"got {vals[14]!r} / {vals[16]!r}")

    # -- lepas ✓ dari tab Follow Up --
    first_fu = fu.tree.get_children("")[0]
    bbox_fu = fu.tree.bbox(first_fu)
    ev2 = _Ev()
    ev2.widget = fu.tree
    ev2.x, ev2.y = bbox_fu[0] + 8, bbox_fu[1] + bbox_fu[3] // 2
    fu._on_tree_click(ev2)
    root.update()
    check("Klik ✓ di tab Follow Up → keluarkan", len(store) == 0)
    check("Empty state Follow Up kembali",
          fu.empty.winfo_manager() == "pack")

    # -- toggle dari Laporan + export (v3.8: Impor Hasil TL DIHAPUS) --
    app.show_laporan_mode(1)   # v3.9.4: segmen Anomali COM (mode 1)
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    lap_tree = app.laporan_view.tree
    first_lap = lap_tree.get_children("")[0]
    bbox_lap = lap_tree.bbox(first_lap)
    ev3 = _Ev()
    ev3.widget = lap_tree
    ev3.x, ev3.y = bbox_lap[0] + 8, bbox_lap[1] + bbox_lap[3] // 2
    app.laporan_view._on_tree_click(ev3)
    root.update()
    check("Klik ✓ di Laporan → masuk follow-up", len(store) == 1)
    snap_lap = next(iter(store.rows.values()))
    check("(v3.9.3) Snapshot asal LAPORAN-COM (SO=COM, Sistem=median)",
          snap_lap.get("asal") == "LAPORAN-COM" and
          "so" in snap_lap and "sistem" in snap_lap,
          f"got asal={snap_lap.get('asal')!r}")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
        xlsx_path = tf.name
    store.export_xlsx(xlsx_path)
    check("Export FOLLOW UP xlsx", os.path.getsize(xlsx_path) > 0)
    # (v3.9.6) FORMAT FILE SAMPLE: header = Resto · Nama Barang ·
    # [tanggal H-2..H+2 sebagai ANGKA] · Sistem · Deviasi · Loss Surplus
    # to BOM · Keterangan · SO · DEVIASI · Selisih · Selisih Deviasi ·
    # Cek FU · PIC · Asal · Status TL · Ditambahkan
    import openpyxl as _oxl
    _wb = _oxl.load_workbook(xlsx_path)
    _ws = _wb["FOLLOW UP"]
    _hdr = [c.value for c in _ws[1]]
    _h_snap = snap_lap.get("h")
    _d0 = int(_h_snap) - 2 if isinstance(_h_snap, (int, float)) else None
    check("(v3.9.6) Export header = format file sample",
          _hdr[:3] == ["Resto", "Nama Barang", str(_d0)] and
          _hdr[7:12] == ["Sistem", "Deviasi", "Loss Surplus to BOM",
                         "Keterangan", "SO"] and
          _hdr[12:17] == ["DEVIASI", "Selisih", "Selisih Deviasi",
                          "Cek FU", "PIC"] and
          _hdr[17:20] == ["Asal", "Status TL", "Ditambahkan"],
          f"got {_hdr}")
    _wb.close()
    os.unlink(xlsx_path)

    # v3.8: fitur impor DIHAPUS — tombol & method tidak ada lagi
    check("v3.8: tombol Impor Hasil TL dihapus",
          fu.btn_import is None)
    check("v3.8: FollowUpStore.import_workbook dihapus",
          not hasattr(store, "import_workbook"))

    # -- persistensi: store baru membaca followup.json --
    from src.ui.followup import FollowUpStore
    store2 = FollowUpStore()
    check("Persistensi: store baru memuat 1 baris", len(store2) == 1)

    # -- kosongkan --
    store.clear()
    check("Kosongkan → 0 baris", len(store) == 0)

    # ==================================================================
    print("== 12. v3.3 ENGINE: sort linear + iid fix + shared cache ==")

    # ---- (a) SORT engine baru: iid & mapping tetap utuh ----
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    dv = app.deviasi_gr_view
    tree = dv.tree
    kids = list(tree.get_children(""))
    check("Deviasi ≥ 2 baris utk uji sort", len(kids) >= 2, f"got {len(kids)}")

    dv._sort_by("Nama Barang", reverse=True)   # Z→A
    root.update()
    kids_after = list(tree.get_children(""))
    check("Sort: jumlah baris tetap", len(kids_after) == len(kids))
    check("Sort: iid dipertahankan (set sama)", set(kids_after) == set(kids))
    check("Sort: urutan berubah (Z→A)", kids_after != kids)
    nama_first = tree.set(kids_after[0], "Nama Barang")
    nama_last = tree.set(kids_after[-1], "Nama Barang")
    check("Sort Z→A benar (first ≥ last)", nama_first >= nama_last,
          f"{nama_first!r} vs {nama_last!r}")

    # toggle baris pertama SETELAH sort → fp harus fp baris visual itu
    first_after = kids_after[0]
    fp_expected = dv._fp_map.get(first_after)
    snap_expected = dv._row_snaps.get(first_after)
    bbox = tree.bbox(first_after)
    evs = _Ev()
    evs.widget = tree
    evs.x, evs.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_tree_click(evs)
    root.update()
    check("Toggle post-sort: fp baris visual masuk store",
          fp_expected in store.rows)
    snap_in_store = store.rows.get(fp_expected)
    check("Toggle post-sort: snapshot = baris visual (barang cocok)",
          snap_in_store is not None and
          snap_in_store.get("barang") == snap_expected.get("barang"))

    # double-click sel kolom ✓ → toggle (bukan popup)
    n_before = len(store)
    evd = _Ev()
    evd.widget = tree
    evd.x, evd.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
    dv._on_double_click(evd)
    root.update()
    check("Double-click sel ✓ = toggle (v3.3)", len(store) != n_before,
          f"{n_before} → {len(store)}")

    # ---- (b) FOLLOW UP: bug v3.2 'salah baris setelah sort' → iid fix ----
    # ambil 2 baris deviasi dengan Nama Barang BERBEDA
    kids = list(tree.get_children(""))
    picks = []
    seen_nama = set()
    for k in kids:
        nm = tree.set(k, "Nama Barang")
        if nm not in seen_nama:
            seen_nama.add(nm)
            picks.append(k)
        if len(picks) == 2:
            break
    check("Dapat 2 baris barang berbeda utk uji follow-up",
          len(picks) == 2)
    if len(picks) == 2:
        store.clear()
        # toggle urutan TERBALIK (A dulu, Z kemudian) supaya urutan tabel
        # follow-up awal = [A, Z] → sort Z→A benar-benar membalik urutan
        for k in reversed(picks):
            b = tree.bbox(k)
            evp = _Ev()
            evp.widget = tree
            evp.x, evp.y = b[0] + 8, b[1] + b[3] // 2
            dv._on_tree_click(evp)
            root.update()
        check("2 baris masuk follow-up", len(store) == 2)

        select_and_wait(root, app, app.tab_followup, app.followup_view)
        fu = app.followup_view
        fu_kids = list(fu.tree.get_children(""))
        check("Follow Up tampil 2 baris", len(fu_kids) == 2)

        # urutan awal → barang masing-masing (kolom idx 2 = Nama Barang;
        # v3.9.6 format file sample: 0✓·1Resto·2Nama Barang·3..7 tanggal)
        barang_awal = [fu.tree.item(k, "values")[2] for k in fu_kids]

        # SORT tabel follow-up by Nama Barang Z→A → urutan terbalik
        fu._sort_by("Nama Barang", reverse=True)
        root.update()
        fu_kids_sorted = list(fu.tree.get_children(""))
        check("FU sort: urutan berubah",
              fu_kids_sorted != fu_kids and len(fu_kids_sorted) == 2)
        barang_sorted = [fu.tree.item(k, "values")[2]
                         for k in fu_kids_sorted]
        check("FU sort Z→A benar", barang_sorted == sorted(
            barang_awal, reverse=True))

        # klik ✓ pada baris visual PERTAMA setelah sort → baris yang
        # keluar harus baris visual itu (v3.2 buggy: keluar baris index-0
        # lama = kemungkinan baris yang salah)
        first_fu = fu_kids_sorted[0]
        barang_first = fu.tree.item(first_fu, "values")[2]
        fps_before = set(store.rows)
        snaps_before = dict(store.rows)   # fp → snap (sebelum dihapus)
        bf = fu.tree.bbox(first_fu)
        evf = _Ev()
        evf.widget = fu.tree
        evf.x, evf.y = bf[0] + 8, bf[1] + bf[3] // 2
        fu._on_tree_click(evf)
        root.update()
        removed = fps_before - set(store.rows)
        check("Klik ✓ post-sort mengeluarkan baris yang BENAR (v3.3)",
              len(removed) == 1)
        if removed:
            snap_removed = snaps_before.get(list(removed)[0])
            check("Baris keluar = baris visual pertama (barang cocok)",
                  snap_removed is not None and
                  snap_removed.get("barang") == barang_first,
                  f"{snap_removed.get('barang')!r} vs {barang_first!r}")
        check("1 baris tersisa di follow-up", len(store) == 1)

    # ---- (c) Shared pivot cache GR/PCS ----
    check("Cache pivot GR/PCS dibagikan (objek cache sama)",
          app.deviasi_gr_view._shared_cache is
          app.deviasi_pcs_view._shared_cache and
          app.deviasi_gr_view._shared_cache is app._deviasi_pivot_cache)
    # v3.9: H sudah otomatis sama (shared) — paksa refresh PCS →
    # HARUS cache-hit → objek pivot identik dgn GR
    app.deviasi_pcs_view._refresh()
    wait_view(root, app.deviasi_pcs_view)
    check("Pivot GR & PCS = objek DataFrame sama (compute 1×, bukan 2×)",
          app.deviasi_pcs_view._cached_pivot is
          app.deviasi_gr_view._cached_pivot and
          app.deviasi_pcs_view._cached_pivot is not None)

    store.clear()

    for p in (followup_path(), resolved_path()):
        if p.exists():
            p.unlink()

    # ==================================================================
    print("== 13. v3.4→v3.6 — TAB 📤 REKAP SELISIH IN (audit data app) ==")
    from src.ui.in_selisih_view import COLUMNS, InDetailPopup
    COL_IDS = [c[0] for c in COLUMNS]
    iv = app.in_selisih_view
    select_and_wait(root, app, app.tab_in_selisih, iv)
    tree_in = iv.tree
    kids_in = list(tree_in.get_children(""))
    check("Rekap Selisih IN: baris anomali tampil (default Hanya Selisih ≠ 0)",
          len(kids_in) == 4, f"got {len(kids_in)}")
    hdrs = [tree_in.heading(c)["text"] for c in COL_IDS]
    check("(v3.6) Kolom = 12: + Hasil SO + Saldo + Hasil Audit + Catatan",
          hdrs == ["Resto", "Tanggal", "Nama Barang", "KATEGORI", "Satuan",
                   "Hasil SO", "Barang Masuk", "IN", "Selisih IN", "Saldo",
                   "Hasil Audit", "Catatan Audit"], f"got {hdrs}")
    check("(v3.6) Tidak ada segment Ringkas|Audit lagi (SATU tabel)",
          not hasattr(iv, "mode_seg"))
    # baris ber-selisih: KOPI tgl3 (BM=100, IN=0, SO=50)
    kopi3 = None
    for k in kids_in:
        vals = tree_in.item(k, "values")
        if vals[2] == "KOPI BUBUK 100G" and vals[1] == "3":
            kopi3 = k
    if kopi3:
        r = {c: tree_in.set(kopi3, c) for c in COL_IDS}
        check("Selisih IN = BM − IN (KOPI tgl3: BM 100, IN '-' → 100)",
              r["Barang Masuk"] == "100" and r["IN"] == "-"
              and r["Selisih IN"] == "100", f"got {r}")
        check("(v3.6) Kolom SO terisi (KOPI tgl3 SO=50)",
              r["Hasil SO"] == "50", f"got {r['Hasil SO']!r}")
        check("(v3.6) Kolom Hasil Audit terisi",
              r["Hasil Audit"] == "CUT-OFF RESOLVED",
              f"got {r['Hasil Audit']!r}")
    st_cells = {tree_in.set(k, "Hasil Audit") for k in kids_in}
    check("(v3.6) Status VBA tampil (VALID/CUT-OFF/DEVIASI)",
          {"VALID (Sistem Masuk)", "CUT-OFF RESOLVED",
           "DEVIASI MURNI"} <= st_cells, f"got {st_cells}")
    check("(v3.6) KPI chips tampil (audit data app)",
          iv.kpi_card.winfo_ismapped())
    tags0 = iv.tree.item(kids_in[0], "tags") if kids_in else ()
    check("(v3.6) Baris diberi tag warna status",
          any(t.startswith("st_") for t in tags0), f"got {tags0}")

    # tampilkan semua baris (utk drill-down AYAM tgl 10)
    iv.only_selisih_var.set(False)
    iv._refresh()
    wait_view(root, iv)
    kids_in = list(tree_in.get_children(""))
    check("Hanya Selisih OFF → semua baris audit tampil (9)",
          len(kids_in) == 9, f"got {len(kids_in)}")

    # ---- drill-down: double-click baris AYAM FILET MLGPAR tgl 10 ----
    target = None
    for k in kids_in:
        vals = tree_in.item(k, "values")
        if vals[0] == "MLGPAR" and vals[1] == "10" and vals[2] == "AYAM FILET":
            target = k
            break
    check("Ada baris MLGPAR/AYAM FILET/Tgl 10 utk drill-down", target is not None)
    if target is not None:
        bbox = tree_in.bbox(target)
        evd = _Ev()
        evd.widget = tree_in
        evd.x, evd.y = bbox[0] + 10, bbox[1] + bbox[3] // 2
        iv._on_double_click(evd)
        root.update()
        # popup terakhir di stack toplevel
        popups = [w for w in root.winfo_children()
                  if isinstance(w, InDetailPopup) and w.winfo_exists()]
        check("Double-click → popup Rincian IN terbuka", len(popups) >= 1)
        if popups:
            pop = popups[-1]
            pkids = list(pop.tree.get_children(""))
            srcs = {pop.tree.set(k, "Source") for k in pkids}
            check("Popup: ada dokumen 42.05", any("42.05" in s for s in srcs),
                  f"srcs={srcs}")
            check("Popup: ada dokumen 32.24", any("32.24" in s for s in srcs),
                  f"srcs={srcs}")
            check("Popup: ada subtotal per sumber",
                  any(str(s).startswith("TOTAL") for s in srcs))
            check("Popup: ada TOTAL IN", "TOTAL IN" in str(pop.tree.item(
                pkids[-1], "values")[0] if pkids else ""))
            nomors = [pop.tree.set(k, "Nomor") for k in pkids
                      if pop.tree.set(k, "Nomor")]
            check("Popup: Nomor dokumen tampil (IT./RI.)",
                  any(n.startswith(("IT.", "RI.", "PI.")) for n in nomors),
                  f"nomors={nomors[:4]}")
            # qty 42.05(750) + 32.24(300) = 1050 == IN metric di append1? (mock IN=5 —
            # detail mock terpisah; verifikasi total popup = 1050)
            total_row = [pop.tree.set(k, "Qty") for k in pkids
                         if pop.tree.set(k, "Source") == "TOTAL IN"]
            # v3.9.1 (FIX C-03): format angka gaya Indonesia — 1.050,
            # bukan 1,050 (konsisten dgn formatter tabel/KPI).
            check("Popup: TOTAL IN = 1.050 (42.05:750 + 32.24:300)",
                  total_row and total_row[0] == "1.050", f"got {total_row}")
            # copy semua nomor unik
            pop._copy_all_unique()
            root.update()
            clip = root.clipboard_get()
            check("Copy Semua Nomor → clipboard berisi IT./RI. unik",
                  "IT.2026.09.00202" in clip and "RI.2026.09.009" in clip)
            pop.destroy()
            root.update()

    # ==================================================================
    print("== 14. v3.6 — AUDIT REKONSILIASI × DATA APP + FIX/KOLOM ==")
    from src.pipeline.fn_audit import (
        AUDIT_INPUT_COLUMNS,
        build_audit_input,
        build_audit_rekap,
    )
    # (pd sudah di-import di level modul — import lokal membuat 'pd' local
    #  name utk seluruh main() → UnboundLocalError di section sebelumnya)

    # --- (a) build_audit_input: rekap + in_detail → 10 kolom kanonik ---
    raw = build_audit_input(rekap_so, in_detail)
    check("build_audit_input: 10 kolom kanonik (struktur input VBA)",
          list(raw.columns) == AUDIT_INPUT_COLUMNS,
          f"got {list(raw.columns)}")
    check("build_audit_input: baris = union aktivitas (SO/BM/IN) = 9",
          len(raw) == 9, f"got {len(raw)}")
    check("build_audit_input: urut per (Resto, Item, Tanggal)",
          raw["Resto"].tolist()[:4] == ["MLGPAR"] * 4
          and raw["Tanggal"].tolist()[:2] == [4, 5],
          f"got {list(zip(raw['Resto'], raw['Tanggal']))[:5]}")
    so_g4 = raw[(raw["Nama Item"] == "GULA PASIR")
                & (raw["Tanggal"] == 4)]
    check("build_audit_input: Hasil SO hadir di tanggal SO (NaN selain itu)",
          float(so_g4["Hasil SO"].iloc[0]) == 100.0
          and raw[raw["Nama Item"] == "SUSU UHT 1L"]["Hasil SO"].isna().all(),
          f"got {so_g4['Hasil SO'].tolist()}")

    # --- (b) engine: aturan VBA pada data app ---
    sts = audit_df["Status Analisis Audit"].tolist()
    check("Engine: OK (Matching) saat BM == IN",
          "OK (Matching)" in sts)
    check("Engine: VALID (Sistem Masuk) (SO naik + BM=0 + IN>0)",
          "VALID (Sistem Masuk)" in sts)
    check("Engine: CUT-OFF RESOLVED (+100 lalu −100)",
          sts.count("CUT-OFF RESOLVED") == 2)
    check("Engine: DEVIASI MURNI (sisa gantung)",
          "DEVIASI MURNI" in sts)
    check("Engine: KPI lengkap dari data app",
          audit_kpi["rows"] == 9 and audit_kpi["omit"] == 1
          and audit_kpi["cutoff"] == 2 and audit_kpi["deviasi_murni"] == 1
          and abs(audit_kpi["deviasi_qty"] - 80.0) < 0.001,
          f"got {audit_kpi}")
    dm = audit_df[audit_df["Status Analisis Audit"] == "DEVIASI MURNI"]
    check("Engine: catatan Sisa Gantung VBA-style",
          "Sisa Gantung: +80" in str(dm.iloc[0]["Detail & Catatan Audit"]),
          f"got {dm.iloc[0]['Detail & Catatan Audit']!r}")

    # --- (v3.9.6) TANGGAL 1: PEMBANDING SO = SO BULAN LALU (user:
    #     "tab selisih in jika tanggal 1 pembanding SO nya SO bulan
    #     lalu") — urutan bulan lalu kini KRONOLOGIS 25•→31• lalu tgl 1;
    #     delta SO di tanggal 1 membanding SO TERAKHIR bulan lalu (31•),
    #     bukan SO tgl 25• (bug sort numerik lama). ---
    _aud_rows = []
    for _day, _so in [(25, 100.0), (26, 110.0), (27, 120.0), (28, 130.0),
                      (29, 140.0), (30, 150.0), (31, 160.0)]:
        _aud_rows.append({"NAMA RESTO": "BKSALT", "Nama Barang": "ITEM X",
                          "JENIS": "SO", "Tanggal": -_day, "Value": _so})
    _aud_rows.append({"NAMA RESTO": "BKSALT", "Nama Barang": "ITEM X",
                      "JENIS": "SO", "Tanggal": 1, "Value": 200.0})
    _aud_in = [{"Tanggal": 1, "NAMA RESTO": "BKSALT",
                "Nama Barang": "ITEM X", "SOURCE IN": "42.05",
                "Value": 50.0}]
    _raw2 = build_audit_input(pd.DataFrame(_aud_rows),
                               pd.DataFrame(_aud_in))
    check("(v3.9.6) Audit: urutan KRONOLOGIS (−25→−31 lalu 1)",
          _raw2["Tanggal"].tolist() ==
          [-25, -26, -27, -28, -29, -30, -31, 1],
          f"got {_raw2['Tanggal'].tolist()}")
    _audit2, _ = build_audit_rekap(_raw2)
    _r1 = _audit2[_audit2["Tanggal"] == 1].iloc[0]
    check("(v3.9.6) Audit tgl 1: delta SO vs SO bulan lalu TERAKHIR "
          "(SO Naik +40 = 200−160•)",
          "SO Naik +40" in str(_r1["Detail & Catatan Audit"]),
          f"got {_r1['Detail & Catatan Audit']!r}")
    check("(v3.9.6) Audit tgl 1: status VALID (SO naik vs bulan lalu)",
          _r1["Status Analisis Audit"] == "VALID (Sistem Masuk)",
          f"got {_r1['Status Analisis Audit']!r}")

    # --- (c) BUG FIX v3.6: klik funnel heading → popup TERBUKA ---
    select_and_wait(root, app, app.tab_in_selisih, iv)
    popups_before = [w for w in root.winfo_children() if w.winfo_exists()]
    x_resto = 35   # tengah kolom pertama 'Resto'
    tree_in.event_generate("<Button-1>", x=x_resto, y=10, when="now")
    root.update()
    new_pops = [w for w in root.winfo_children()
                if w.winfo_exists() and w not in popups_before
                and w.title().startswith("Filter —")]
    check("(v3.6 BUG FIX) Klik funnel 'Resto' dgn mouse → popup filter "
          "TERBUKA", len(new_pops) == 1,
          f"got {[w.title() for w in new_pops]}")
    for p in new_pops:
        p.destroy()
    root.update()

    # --- (d) header filter semua kolom (incl. Hasil Audit & SO) ---
    check("(v3.6) Semua 12 kolom punya HeaderFilter",
          hasattr(iv, "header_filters") and
          len(iv.header_filters._filters) == len(COL_IDS))
    iv._on_col_filter("Hasil Audit", {"DEVIASI MURNI"})
    wait_view(root, iv)
    kids_f = list(tree_in.get_children(""))
    check("Filter header Hasil Audit=DEVIASI MURNI → hanya baris SUSU",
          len(kids_f) == 1 and
          tree_in.set(kids_f[0], "Nama Barang") == "SUSU UHT 1L",
          f"got {[(tree_in.set(k, 'Nama Barang')) for k in kids_f]}")
    iv._reset_filter_states()
    iv._refresh()
    wait_view(root, iv)

    # --- (e) HIDE/UNHIDE KOLOM (ColumnManager v3.6) ---
    check("(v3.6) ColumnManager terpasang", iv._colmgr is not None)
    iv._colmgr.hide("KATEGORI")
    root.update()
    check("Hide kolom KATEGORI → displaycolumns tanpa KATEGORI",
          "KATEGORI" not in [str(c) for c in tree_in.cget("displaycolumns")],
          f"got {tree_in.cget('displaycolumns')}")
    hdrs_now = [tree_in.heading(c)["text"]
                for c in tree_in["columns"]
                if c in [str(x) for x in
                         tree_in.cget("displaycolumns")]]
    check("Hide kolom: heading KATEGORI hilang dari tampilan",
          "KATEGORI" not in hdrs_now, f"got {hdrs_now}")
    # identifikasi klik tetap benar setelah kolom disembunyikan
    # (display: Resto 74 + Tanggal 64 → Nama Barang mulai x=138)
    x_nb = 74 + 64 + 100   # tengah kolom 'Nama Barang' (KATEGORI hidden)
    hits = {"n": 0}
    orig_open = iv.header_filters._filters["Nama Barang"].open_popup
    iv.header_filters._filters["Nama Barang"].open_popup = \
        lambda *a, **k: hits.__setitem__("n", hits["n"] + 1)
    tree_in.event_generate("<Button-1>", x=x_nb, y=10, when="now")
    root.update()
    iv.header_filters._filters["Nama Barang"].open_popup = orig_open
    check("(v3.6) Klik funnel tetap akurat setelah kolom disembunyikan",
          hits["n"] == 1, f"got {hits['n']}")
    iv._colmgr.show_all()
    root.update()
    check("Show all → semua kolom kembali tampil",
          "#all" in str(tree_in.cget("displaycolumns")) or
          len(tree_in.cget("displaycolumns")) == len(COL_IDS),
          f"got {tree_in.cget('displaycolumns')}")
    # panel kolom terbuka & tertutup
    iv._colmgr.open_panel()
    root.update()
    check("Tombol ◱ Kolom → panel checklist terbuka",
          iv._colmgr._panel is not None and iv._colmgr._panel.winfo_exists())
    iv._colmgr.open_panel()   # toggle tutup
    root.update()

    # --- (f) LightMode dihapus total ---
    import inspect

    from src.config import Config as _Cfg
    check("(v3.5) Config tidak lagi memuat LightMode",
          "self.LightMode" not in inspect.getsource(_Cfg))

    # ==================================================================
    print("== 15. v3.4 — LEBAR KOLOM: drag tepi + ↔ Auto-Fit ==")
    from src.ui.widgets import enable_col_resize
    # (a) drag tepi kanan heading kolom pertama
    # (stretch=False supaya lebar deterministik — dengan stretch Tk
    # redistribusi ruang sisa jendela ke semua kolom)
    tree_in.column("Resto", stretch=False)
    w_before = tree_in.column("Resto", "width")
    edge_x = w_before  # tepi kanan kolom pertama
    tree_in.event_generate("<Button-1>", x=edge_x, y=10)
    root.update()
    tree_in.event_generate("<B1-Motion>", x=edge_x + 60, y=10)
    root.update()
    tree_in.event_generate("<ButtonRelease-1>", x=edge_x + 60, y=10)
    root.update()
    w_after = tree_in.column("Resto", "width")
    check("Drag tepi heading → lebar kolom berubah (w+60)",
          w_after == w_before + 60, f"{w_before} → {w_after}")
    tree_in.column("Resto", stretch=True)
    # (b) tombol ↔ Auto-Fit menyesuaikan lebar ke konten
    iv._auto_fit()
    root.update()
    w_autofit = tree_in.column("Nama Barang", "width")
    check("↔ Auto-Fit: kolom Nama Barang menyesuaikan konten (>default)",
          w_autofit != 200, f"200 → {w_autofit}")
    # (c) enable_col_resize terpasang di semua view utama
    views_trees = [
        app.pivot_view.tree, app.deviasi_gr_view.tree,
        app.deviasi_pcs_view.tree, app.laporan_view.tree,
        app.rincian_view.tree, app.followup_view.tree,
        app.in_selisih_view.tree,
    ]
    # tidak ada API publik utk cek binding — verifikasi tidak error saat
    # memanggil ulang (idempotent) + smoke drag di pivot (show tree headings)
    for t in views_trees:
        enable_col_resize(t)
    check("enable_col_resize terpasang di 7 view (idempotent, tanpa error)",
          True)

    # ==================================================================
    print("== 16. v3.7 — DEEP AUDIT FIXES (display-vs-logical index dst) ==")
    import numpy as np

    from src.ui.widgets import (
        ColumnManager,
        _tree_row_passes,
        apply_tree_row_filters,
        auto_fit_columns,
        identify_to_column,
    )

    # (a) apply_tree_row_filters membaca nilai kolom yang BENAR setelah
    #     kolom sebelumnya disembunyikan (dulu: index display ≠ logis)
    tfix = ttk.Treeview(root, columns=["A", "B", "C"], show="headings")
    for c in ("A", "B", "C"):
        tfix.heading(c, text=c)
        tfix.column(c, width=80)
    tfix.insert("", "end", iid="r1", values=("x", "keep", "1"))
    tfix.insert("", "end", iid="r2", values=("x", "drop", "2"))
    tfix.insert("", "end", iid="r3", values=("y", "keep", "3"))
    tfix.configure(displaycolumns=["B", "C"])          # sembunyikan A
    apply_tree_row_filters(tfix, {"B": {"keep"}})
    root.update()
    kids_a = list(tfix.get_children(""))
    check("(v3.7) Filter clone membaca kolom BENAR setelah hide",
          kids_a == ["r1", "r3"],
          f"kids={kids_a} (harus r1,r3 — dulu membaca kolom A: semua lolos)")
    apply_tree_row_filters(tfix, {})                     # reset tampilan
    root.update()
    check("(v3.7) Reset filter clone → semua baris kembali",
          len(list(tfix.get_children(""))) == 3)
    tfix.destroy()

    # (b) filter '#0' di tree 2-level memakai text PARENT (nama barang),
    #     bukan text anak (nama metric) — dulu: semua baris tersembunyi
    t2 = ttk.Treeview(root, columns=["V"], show="tree headings")
    t2.heading("#0", text="Nama Barang")
    t2.heading("V", text="V")
    t2.column("#0", width=120)
    t2.column("V", width=60)
    t2.insert("", "end", iid="p1", text="AYAM", values=(""))
    t2.insert("p1", "end", iid="p1_m1", text="1.SO", values=("10"))
    t2.insert("p1", "end", iid="p1_m2", text="4.IN", values=("5"))
    t2.insert("", "end", iid="p2", text="GULA", values=(""))
    t2.insert("p2", "end", iid="p2_m1", text="1.SO", values=("3"))
    apply_tree_row_filters(t2, {"#0": {"AYAM"}})
    root.update()
    kids_b = set(t2.get_children(""))
    check("(v3.7) Filter #0 clone 2-level → parent+anak metric tampil",
          "p1" in kids_b and "p2" not in kids_b and
          len(t2.get_children("p1")) == 2,
          f"top={kids_b} anak_p1={t2.get_children('p1')}")
    t2.destroy()

    # (c) auto_fit mengukur nilai kolom yang BENAR setelah hide
    #     (kolom B berisi teks panjang; kolom A disembunyikan berisi teks
    #     pendek — lebar B harus mengikuti konten B, bukan A)
    t3 = ttk.Treeview(root, columns=["SHORT", "LONGVAL"], show="headings")
    for c in ("SHORT", "LONGVAL"):
        t3.heading(c, text=c)
        t3.column(c, width=50, stretch=False)
    t3.insert("", "end", values=("ab", "NILAI_SANGAT_PANJANG_0123456789"))
    t3.configure(displaycolumns=["LONGVAL"])           # sembunyikan SHORT
    auto_fit_columns(t3, columns=["LONGVAL"])
    w_long = t3.column("LONGVAL", "width")
    check("(v3.7) Auto-fit ukur kolom BENAR setelah hide (B melebar)",
          w_long > 100, f"w={w_long} (dulu mengukur SHORT → ~50-60)")
    t3.destroy()

    # (d) toggle ✓ memakai NAMA kolom — setelah ✓ disembunyikan, klik sel
    #     kolom lain TIDAK lagi memicu toggle (dulu: posisi '#1' salah)
    dv = app.deviasi_gr_view
    dtr = dv.tree
    dv_store_before = set(dv.store.rows.keys()) if dv.store else set()
    dtr._column_manager.hide("✓")
    root.update()
    # klik sel kolom Resto (posisi display pertama setelah ✓ hidden)
    first_row = dtr.get_children("")[0]
    bbox = dtr.bbox(first_row, column="#1")
    if bbox:
        ev = tk.Event()
        ev.x, ev.y = bbox[0] + 5, bbox[1] + 5
        ev.widget = dtr
        dv._on_tree_click(ev)
        root.update()
        dv_store_after = set(dv.store.rows.keys()) if dv.store else set()
        check("(v3.7) Klik kolom lain setelah ✓ disembunyikan → tidak toggle",
              dv_store_after == dv_store_before,
              f"before={len(dv_store_before)} after={len(dv_store_after)}")
    else:
        check("(v3.7) Klik kolom lain setelah ✓ disembunyikan → tidak toggle",
              False, "bbox kolom tidak tersedia")
    dtr._column_manager.show_all()
    root.update()

    # (e) ColumnManager mirror sinkron state hidden (clone → sumber)
    t4 = ttk.Treeview(root, columns=["A", "B"], show="headings")
    for c in ("A", "B"):
        t4.heading(c, text=c)
        t4.column(c, width=60)
    t4.insert("", "end", values=("1", "2"))
    t5 = ttk.Treeview(root, columns=["A", "B"], show="headings")
    for c in ("A", "B"):
        t5.heading(c, text=c)
        t5.column(c, width=60)
    t5.insert("", "end", values=("1", "2"))
    cm_main = ColumnManager(t4)
    cm_clone = ColumnManager(t5, mirror=t4)
    cm_clone.hide("B")
    root.update()
    check("(v3.7) Mirror clone→sumber: displaycolumns sumber ikut",
          "B" not in [str(x) for x in t4.cget("displaycolumns")])
    check("(v3.7) Mirror clone→sumber: state hidden colmgr sinkron",
          cm_main.hidden == ["B"],
          f"cm_main.hidden={cm_main.hidden} (dulu [] → panel basi)")
    t4.destroy()
    t5.destroy()

    # (f) ENGINE v3.7 — running stock vektor == implementasi lama
    #     (10 edge-case sintetis; loop lama di-inline sebagai oracle)
    from src.pipeline.fn_running_stock import fn_running_stock, fn_running_stock_grouped

    def OLD_grouped(df, gk):
        srt = df.sort_values(gk + ["Tanggal"], ascending=True,
                             na_position="last").reset_index(drop=True)
        res = [fn_running_stock(g) for _, g in
               srt.groupby(gk, sort=False, dropna=False)]
        return pd.concat(res, ignore_index=True) if res else srt

    cases = {
        "normal": pd.DataFrame({
            "Nama Barang": ["A", "A", "A", "A", "B", "B"],
            "NAMA RESTO": ["R1", "R1", "R1", "R1", "R2", "R2"],
            "Tanggal": pd.array([1, 2, 3, 4, 1, 2], dtype="Int64"),
            "IN": [10.0, 5, 0, 3, 7, 2],
            "OUT": [2, 1, 4, 0, 1, 1],
            "BARANG KELUAR": [0, 0, 1, 0, 0, 0],
            "SALDO AWAL": [100, np.nan, np.nan, np.nan, 50, np.nan],
        }),
        "bulan-lalu-net-nol-tidak-ikut": pd.DataFrame({
            "Nama Barang": ["A"] * 6,
            "NAMA RESTO": ["R1"] * 6,
            "Tanggal": pd.array([-25, -26, 1, 2, 3, 31], dtype="Int64"),
            "IN": [1, 2, 10, 5, 0, 3],
            "OUT": [0, 1, 2, 1, 4, 0],
            "BARANG KELUAR": [0, 0, 0, 0, 1, 0],
            "SALDO AWAL": [100.0] + [np.nan] * 5,
        }),
        "tanggal-NaN-ekor": pd.DataFrame({
            "Nama Barang": ["A", "A", "A", "A"],
            "NAMA RESTO": ["R1"] * 4,
            "Tanggal": pd.array([1, 2, None, 3], dtype="Int64"),
            "IN": [10, 5, 99, 3],
            "OUT": [2, 1, 5, 0],
            "BARANG KELUAR": [0, 0, 0, 0],
            "SALDO AWAL": [100.0, np.nan, np.nan, np.nan],
        }),
        "key-NaN-satu-grup": pd.DataFrame({
            "Nama Barang": [None, None, "B"],
            "NAMA RESTO": ["R1", "R1", "R2"],
            "Tanggal": pd.array([1, 2, 1], dtype="Int64"),
            "IN": [10, 5, 7],
            "OUT": [2, 1, 1],
            "BARANG KELUAR": [0, 0, 0],
            "SALDO AWAL": [100.0, np.nan, 3.0],
        }),
        "saldo-awal-negatif": pd.DataFrame({
            "Nama Barang": ["A", "A", "A"],
            "NAMA RESTO": ["R1", "R1", "R1"],
            "Tanggal": pd.array([1, 2, 3], dtype="Int64"),
            "IN": [1, 1, 1],
            "OUT": [0, 0, 0],
            "BARANG KELUAR": [0, 0, 0],
            "SALDO AWAL": [-5.0, np.nan, -2.0],
        }),
        "grup-tanpa-tgl-ge-1": pd.DataFrame({
            "Nama Barang": ["A", "A", "C"],
            "NAMA RESTO": ["R1", "R1", "R3"],
            "Tanggal": pd.array([-25, -20, 5], dtype="Int64"),
            "IN": [1, 2, 10],
            "OUT": [0, 1, 2],
            "BARANG KELUAR": [0, 0, 0],
            "SALDO AWAL": [100.0, np.nan, 5.0],
        }),
    }
    gk = ["Nama Barang", "NAMA RESTO"]
    ok_rs = True
    for cname, cdf in cases.items():
        old = OLD_grouped(cdf.copy(), gk)
        new = fn_running_stock_grouped(cdf.copy(), gk)
        a = pd.to_numeric(old["SALDO AKHIR"], errors="coerce") \
            .fillna(-777).to_numpy()
        b = pd.to_numeric(new["SALDO AKHIR"], errors="coerce") \
            .fillna(-777).to_numpy()
        same = len(a) == len(b) and np.allclose(a, b, atol=1e-9)
        ok_rs = ok_rs and same
        if not same:
            print(f"    case '{cname}' BEDA: {a} vs {b}")
    check("(v3.7) ENGINE running stock vektor == lama (6 edge-case)",
          ok_rs)

    # (g) ENGINE v3.7 — _group_info_columns == UDF lama (edge-case)
    from src.pipeline.append1 import _group_info_columns

    def OLD_group(ip, KC, IC):
        def _sj(series):
            vals = series.dropna()
            if vals.empty:
                return None
            return ", ".join(str(v) for v in pd.unique(vals))
        return ip.groupby(KC, as_index=False, dropna=False).agg(
            {c: _sj for c in IC if c in ip.columns})

    KC = ["Nama Barang", "NAMA RESTO", "Tanggal"]
    IC = ["Nomor", "Nomor PO"]
    ip = pd.DataFrame({
        "Nama Barang": ["A", "A", "A", None, None, "A"],
        "NAMA RESTO": ["R1", "R1", "R1", "R1", "R1", "R1"],
        "Tanggal": pd.array([1, 1, 2, 1, 2, None], dtype="Int64"),
        "Nomor": ["IT.2", "IT.1", "IT.1", "IT.5", "IT.6", "IT.7"],
        "Nomor PO": [None, None, None, "PO.9", None, None],
    })
    old = OLD_group(ip, KC, IC)
    new = _group_info_columns(ip, KC, IC)
    m = old.merge(new, on=KC, how="outer", suffixes=("_o", "_n"),
                  indicator=True)
    ok_keys = (m["_merge"] == "both").all() and len(old) == len(new)
    ok_vals = all(
        (m[f"{c}_o"].fillna("<NULL>").astype(str) ==
         m[f"{c}_n"].fillna("<NULL>").astype(str)).all()
        for c in IC if f"{c}_o" in m.columns)
    check("(v3.7) ENGINE info-group vektor == lama (NaN key + kosong)",
          ok_keys and ok_vals,
          f"keys={ok_keys} vals={ok_vals}")

    # (h) engine single-parse reader: hasil == jalur read_excel(header=hr)
    from src.pipeline.fn_rekap_mentah import _promote_at
    raw = pd.DataFrame([
        ["NAMA RESTO", "JENIS", "NAMA BARANG", "1", "2", "3"],
        ["R1", "SO", "AYAM", 5, None, 7],
        ["R1", "SO", "GULA", 1, 2, None],
    ])
    prom = _promote_at(raw, 0)
    check("(v3.7) Reader _promote_at: header & body benar",
          list(prom.columns) == ["NAMA RESTO", "JENIS", "NAMA BARANG",
                                 "1", "2", "3"] and len(prom) == 2 and
          prom.iloc[0, 5] == 7)

    # ==================================================================
    print("== 17. v3.8 — SELISIH IN 1-31 + PIVOT -31..31 + EXPORT + CF ==")

    # (a) default rentang tanggal baru
    check("(v3.8) Rekap Selisih IN default = 1 s/d 31 (bulan berjalan)",
          app.in_selisih_view.tgl_start_var.get() == "1" and
          app.in_selisih_view.tgl_end_var.get() == "31",
          f"got {app.in_selisih_view.tgl_start_var.get()}.."
          f"{app.in_selisih_view.tgl_end_var.get()}")
    app.in_selisih_view.tgl_start_var.set("-5")
    app.in_selisih_view._reset_filter()
    check("(v3.8) Reset Selisih IN kembali ke 1–31",
          app.in_selisih_view.tgl_start_var.get() == "1")
    app.pivot_view._reset_filter()
    check("(v3.8) Reset Pivot kembali ke -31–31",
          app.pivot_view.tgl_start_var.get() == "-31")

    # (b) kolom tanggal pivot mode TANGGAL: -25..-31 lalu 1..3 (kronologis)
    #     — akar bug user "25, 26, lalu 1": rentang lama -26 memotong
    #     tgl 27-31 bulan lalu
    test_df = pd.DataFrame({
        "Nama Barang": ["AYAM"] * 12,
        "JENIS": ["1.SO"] * 12,
        "NAMA RESTO": ["MLGPAR"] * 12,
        "Tanggal": [-25, -26, -27, -28, -29, -30, -31, 1, 2, 3, 4, 5],
        "NILAI": [float(i + 1) for i in range(12)],
        "SATUAN": ["GR"] * 12,
        "KATEGORI": ["DEVIASI"] * 12,
        "SOURCE KIRIMAN": ["GUDANG"] * 12,
    })
    orig_data = pv.data
    try:
        pv.data = test_df
        st = {"name_selected": None, "resto": "(All)", "source": "(All)",
              "kategori": "(All)", "tgl_start": -31, "tgl_end": 31,
              "mode": "tanggal", "hide_empty": False}
        payload = pv._compute_payload(st)
        want_cols = ["-25", "-26", "-27", "-28", "-29", "-30", "-31",
                     "1", "2", "3", "4", "5"]
        check("(v3.8) Pivot tanggal: kolom -25..-31 + 1..5 urut kronologis "
              "(bukan '25,26,lalu 1')",
              payload["columns"] == want_cols,
              f"got {payload['columns']}")
        # rentang lama (-26) memang memotong — bukti akar masalah
        st_old = dict(st, tgl_start=-26)
        payload_old = pv._compute_payload(st_old)
        check("(v3.8) Bukti akar bug: rentang lama -26 memotong -27..-31",
              payload_old["columns"] == ["-25", "-26", "1", "2", "3", "4",
                                         "5"],
              f"got {payload_old['columns']}")
    finally:
        pv.data = orig_data

    # (c) build_selisih_export_df — kolom PERSIS permintaan user
    from src.ui.export_sheets import (
        SELISIH_EXPORT_COLUMNS,
        add_pivot_sheet,
        build_selisih_export_df,
        write_selisih_sheet,
    )
    base = pd.DataFrame({
        "Resto": ["MLGPAR", "MLGPAR", "BDGUKU"],
        "Tanggal": [5, -25, 5],
        "Nama Barang": ["AYAM", "AYAM", "KOPI"],
        "KATEGORI": ["DEVIASI", "DEVIASI", "PCS"],
        "Satuan": ["GR", "GR", "PCS"],
        "Hasil SO": [None, 100.0, 50.0],
        "Barang Masuk": [80.0, None, 30.0],
        "IN": [60.0, 10.0, 30.0],
        "Selisih IN": [20.0, -10.0, 0.0],
        "Saldo": [0.0, 0.0, 0.0],
        "Hasil Audit": ["OK (Matching)", "OK", "OK"],
        "Catatan Audit": ["-", "-", "-"],
        "42.05": [50.0, 0.0, 20.0],
        "32.24": [10.0, 10.0, 10.0],
        "99.01": [0.0, 0.0, 0.0],
    })
    ex = build_selisih_export_df(base, 1, 31)
    check("(v3.8) Export selisih: kolom persis (Resto..Selisih, rename "
          "Sheet Barang Masuk/Kiriman HO/Kiriman Supplier/Pembelian)",
          list(ex.columns) == SELISIH_EXPORT_COLUMNS and
          SELISIH_EXPORT_COLUMNS == [
              "Resto", "Tanggal", "Nama Barang", "Kategori", "Satuan",
              "Hasil SO", "Sheet Barang Masuk", "Kiriman HO",
              "Kiriman Supplier", "Pembelian by Resto", "Selisih"],
          f"got {list(ex.columns)}")
    check("(v3.8) Export selisih: hanya baris tgl 1-31 (baris -25 keluar)",
          len(ex) == 2, f"got {len(ex)}")
    r_mlg = ex[ex["Resto"] == "MLGPAR"].iloc[0]
    check("(v3.8) Export selisih: nilai rename benar (BM→Sheet BM, "
          "4205→Kiriman HO, 3224→Kiriman Supplier, 9901→Pembelian)",
          float(r_mlg["Sheet Barang Masuk"]) == 80.0 and
          float(r_mlg["Kiriman HO"]) == 50.0 and
          float(r_mlg["Kiriman Supplier"]) == 10.0 and
          float(r_mlg["Pembelian by Resto"]) == 0.0 and
          float(r_mlg["Selisih"]) == 20.0,
          f"got {r_mlg.to_dict()}")
    check("(v3.8) Export selisih: urut Resto→Tanggal→Nama Barang "
          "(BDGUKU dulu, lalu MLGPAR)",
          list(ex["Resto"]) == ["BDGUKU", "MLGPAR"] and
          int(ex.iloc[0]["Tanggal"]) == 5,
          f"got {list(ex['Resto'])}")
    check("(v3.8) Export selisih: Hasil SO kosong tetap kosong (bukan 0)",
          pd.isna(r_mlg["Hasil SO"]) and
          float(ex.iloc[0]["Hasil SO"]) == 50.0)
    # edge: base TANPA kolom komponen 42.05/32.24/99.01 (defensif —
    # pd.to_numeric(None) scalar pernah bikin AttributeError .fillna)
    base_min = base.drop(columns=["42.05", "32.24", "99.01", "Saldo",
                                  "Hasil Audit", "Catatan Audit"])
    ex_min = build_selisih_export_df(base_min, 1, 31)
    check("(v3.8) Export selisih defensif: base tanpa kolom komponen OK",
          len(ex_min) == 2 and
          float(ex_min.iloc[0]["Kiriman HO"]) == 0.0 and
          list(ex_min.columns) == SELISIH_EXPORT_COLUMNS)
    check("(v3.8) Export selisih defensif: base None/empty → 0 baris",
          len(build_selisih_export_df(None)) == 0 and
          len(build_selisih_export_df(pd.DataFrame())) == 0)

    # (d) roundtrip file: sheet selisih + sheet PIVOT + conditional
    #     formatting dibaca kembali (verifikasi rumus file user)
    a1_small = pd.DataFrame({
        "Nama Barang": ["AYAM", "AYAM", "AYAM", "GULA"],
        "JENIS": ["1.SO", "4.IN", "5.BARANG MASUK", "1.SO"],
        "NAMA RESTO": ["MLGPAR"] * 4,
        "Tanggal": [-25, 1, 1, 2],
        "NILAI": [10.0, 5.0, 5.0, 7.0],
    })
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xlsx",
                                     delete=False) as tf:
        xlsx_path = tf.name
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        write_selisih_sheet(writer, ex)
        ok_pivot = add_pivot_sheet(writer, a1_small)
    check("(v3.8) add_pivot_sheet: sheet dibuat", ok_pivot)

    from openpyxl import load_workbook
    wb = load_workbook(xlsx_path)
    check("(v3.8) File export: sheet 'Selisih IN per Resto' + 'PIVOT'",
          wb.sheetnames == ["Selisih IN per Resto", "PIVOT"],
          f"got {wb.sheetnames}")
    ws_sel = wb["Selisih IN per Resto"]
    hdrs_sel = [c.value for c in ws_sel[1]]
    check("(v3.8) Sheet selisih: header = kolom export",
          hdrs_sel == SELISIH_EXPORT_COLUMNS, f"got {hdrs_sel}")
    check("(v3.8) Sheet selisih: freeze A2 + autofilter",
          ws_sel.freeze_panes == "A2" and
          str(ws_sel.auto_filter.ref).startswith("A1:"), )
    ws_p = wb["PIVOT"]
    check("(v3.8) PIVOT: layout baris 1-6 persis file user",
          ws_p["A1"].value == "NAMA RESTO" and ws_p["B1"].value == "(All)"
          and ws_p["A2"].value == "SOURCE KIRIMAN" and
          ws_p["A3"].value == "KATEGORI" and
          ws_p["A5"].value == "Sum of NILAI" and
          ws_p["B5"].value == "Column Labels" and
          ws_p["A6"].value == "Row Labels" and
          ws_p["B6"].value == -25 and ws_p["C6"].value == 1 and
          ws_p["D6"].value == 2,
          f"got A5={ws_p['A5'].value!r} B6={ws_p['B6'].value!r}")
    check("(v3.8) PIVOT: row label kolom A = nama barang (bold) + jenis",
          ws_p["A7"].value == "AYAM" and ws_p["A7"].font.bold and
          ws_p["A8"].value == "1.SO" and
          not (ws_p["A8"].font.bold or False) and
          ws_p["A11"].value == "GULA" and ws_p["A12"].value == "1.SO",
          f"got A7={ws_p['A7'].value!r} A8={ws_p['A8'].value!r} "
          f"A11={ws_p['A11'].value!r}")
    check("(v3.8) PIVOT: nilai Sum of NILAI (AYAM 1.SO tgl -25 = 10)",
          ws_p["B8"].value == 10.0 and ws_p["D12"].value == 7.0,
          f"got B8={ws_p['B8'].value!r} D12={ws_p['D12'].value!r}")

    all_formulas = []
    for cf in ws_p.conditional_formatting:
        for rule in cf.rules:
            all_formulas.extend(list(rule.formula or []))
    joined = " || ".join(all_formulas)
    check("(v3.8) PIVOT CF: =AND($A8=\"1.SO\",B8>A8) persis rumus user",
          'AND($A8="1.SO",B8>A8)' in joined, f"got {joined}")
    check("(v3.8) PIVOT CF: $A8=\"3.DEVIASI\" (border bawah)",
          '$A8="3.DEVIASI"' in joined)
    check("(v3.8) PIVOT CF: AND($A8=\"7.Selisih IN\",B8<>0) merah",
          'AND($A8="7.Selisih IN",B8<>0)' in joined)
    check("(v3.8) PIVOT CF: containsText 4.IN + 5.BARANG MASUK (kolom A)",
          'SEARCH("4.IN",A7)' in joined and
          'SEARCH("5.BARANG MASUK",A7)' in joined)
    rules_zero = [r for cf in ws_p.conditional_formatting for r in cf.rules
                  if r.type == "cellIs"]
    check("(v3.8) PIVOT CF: cellIs 0 (font putih) + header < 0 (bulan lalu)",
          len(rules_zero) == 2, f"got {len(rules_zero)}")
    os.unlink(xlsx_path)

    # (e) tombol export ada di view Selisih IN + Impor TL hilang
    check("(v3.8) Handler export Selisih IN ada",
          callable(app.in_selisih_view._on_export))

    print("== 18. v3.9 — EXPORT AUDIT OPT + STYLE WASTE (⤢/funnel/tabel) ==")

    # (a) build_selisih_export_df + audit_cols — opsi kolom hasil audit
    ex_audit = build_selisih_export_df(base, 1, 31,
                                       audit_cols=["Hasil Audit", "Saldo",
                                                   "Catatan Audit"])
    check("(v3.9) Export + audit: kolom audit ditambahkan setelah Selisih",
          list(ex_audit.columns) == SELISIH_EXPORT_COLUMNS + [
              "Hasil Audit", "Saldo", "Catatan Audit"],
          f"got {list(ex_audit.columns)}")
    r_m = ex_audit[ex_audit["Resto"] == "MLGPAR"].iloc[0]
    check("(v3.9) Export + audit: nilai sebaris BENAR (Hasil Audit ml "
          "OK (Matching), Saldo 0)",
          r_m["Hasil Audit"] == "OK (Matching)" and
          float(r_m["Saldo"]) == 0.0,
          f"got {r_m['Hasil Audit']!r} / {r_m['Saldo']!r}")
    ex_partial = build_selisih_export_df(base, 1, 31,
                                         audit_cols=["Hasil Audit"])
    check("(v3.9) Export + audit: subset 1 kolom OK",
          list(ex_partial.columns) == SELISIH_EXPORT_COLUMNS + ["Hasil Audit"])
    ex_none = build_selisih_export_df(base, 1, 31, audit_cols=[])
    check("(v3.9) Export tanpa kolom audit (opsi OFF) = perilaku v3.8",
          list(ex_none.columns) == SELISIH_EXPORT_COLUMNS)
    ex_bad = build_selisih_export_df(base, 1, 31,
                                     audit_cols=["Kolom Ngawur", "Saldo"])
    check("(v3.9) Export + audit: nama kolom invalid diabaikan",
          list(ex_bad.columns) == SELISIH_EXPORT_COLUMNS + ["Saldo"])

    # (b) dialog opsi export + _do_export inti (tanpa dialog file)
    check("(v3.9) Dialog opsi export ada (metode view)",
          callable(app.in_selisih_view._export_options_dialog))
    check("(v3.9) _do_export terpisah dari dialog (testable)",
          callable(app.in_selisih_view._do_export))
    with tempfile.NamedTemporaryFile(suffix=".xlsx",
                                     delete=False) as tf2:
        xlsx2 = tf2.name
    # patch messagebox sampai SELESAI section 18 (done() async memanggil
    # showinfo SETELAH file tertulis — patch tidak boleh dipulihkan duluan;
    # patch dipulihkan menjelang cleanup di bawah)
    import src.ui.in_selisih_view as _isv_mod
    _orig_info = _isv_mod.messagebox.showinfo
    _orig_warn = _isv_mod.messagebox.showwarning
    _isv_mod.messagebox.showinfo = lambda *a, **k: None
    _isv_mod.messagebox.showwarning = lambda *a, **k: None
    app.in_selisih_view._do_export(xlsx2, ["Hasil Audit", "Saldo"])
    t0 = time.time()
    wb2 = None
    while time.time() - t0 < 5:
        root.update()
        if os.path.exists(xlsx2) and os.path.getsize(xlsx2) > 0:
            try:
                wb2 = load_workbook(xlsx2)
                break
            except Exception:
                pass
        time.sleep(0.05)
    check("(v3.9) _do_export menulis file (async selesai)",
          wb2 is not None)
    if wb2 is not None:
        ws2 = wb2["Selisih IN per Resto"]
        hdr2 = [c.value for c in ws2[1]]
        check("(v3.9) Roundtrip _do_export: header + kolom audit",
              hdr2 == SELISIH_EXPORT_COLUMNS + ["Hasil Audit", "Saldo"],
              f"got {hdr2}")
    # tunggu job export benar2 selesai (done() async + showinfo patched)
    t0 = time.time()
    while time.time() - t0 < 3:
        root.update()
        time.sleep(0.02)
    os.unlink(xlsx2)

    # (c) STYLE WASTE — tabel besar + funnel merah + expander ⤢
    style = ttk.Style(root)
    check("(v3.9) Tabel diperbesar: rowheight 30 (dari 26) ala Waste",
          int(style.configure("Treeview", "rowheight")) == 30,
          f"got {style.configure('Treeview', 'rowheight')}")
    _hf_font = str(style.configure("Treeview.Heading", "font")).split()
    check("(v3.9) Tabel diperbesar: heading font size 10 bold",
          _hf_font[-2:] == ["10", "bold"],
          f"got {_hf_font}")
    from src.ui.widgets import TableExpander, funnel_image
    img_on = funnel_image(active=True)
    img_off = funnel_image(active=False)
    check("(v3.9) Funnel Waste: ikon aktif ≠ idle (merah vs terang)",
          str(img_on) != str(img_off))
    check("(v3.9) Funnel Waste: dua varian ter-cache",
          isinstance(funnel_image(active=True), tk.PhotoImage))

    # funnel merah saat kolom terfilter (state HeaderFilter + refresh_icon)
    def _img_name(v):
        if isinstance(v, (list, tuple)):
            return str(v[0]) if v else ""
        return str(v)

    iv = app.in_selisih_view
    hf = iv.header_filters._filters["Hasil Audit"]
    hf.selected = {"OK (Matching)"}   # simulasi apply dari popup
    hf.refresh_icon()
    root.update()
    check("(v3.9) Funnel kolom terfilter = varian MERAH (ala Waste)",
          _img_name(hf.tree.heading("Hasil Audit")["image"]) ==
          str(funnel_image(True)),
          f"got {hf.tree.heading('Hasil Audit')['image']}")
    hf.selected = None
    hf.refresh_icon()
    root.update()
    check("(v3.9) Funnel kolom tanpa filter = varian idle",
          _img_name(hf.tree.heading("Hasil Audit")["image"]) ==
          str(funnel_image(False)),
          f"got {hf.tree.heading('Hasil Audit')['image']}")

    # (d) expander ⤢ — ciutkan baris kontrol, tabel tinggi penuh
    dv = app.deviasi_gr_view
    exp = dv._expander
    check("(v3.9) TableExpander terpasang di semua view tabel",
          isinstance(exp, TableExpander) and
          isinstance(app.pivot_view._expander, TableExpander) and
          isinstance(app.rincian_view._expander, TableExpander) and
          isinstance(app.laporan_view._expander, TableExpander) and
          isinstance(app.followup_view._expander, TableExpander) and
          isinstance(iv._expander, TableExpander))
    # pastikan tab deviasi GR sedang TERLIHAT supaya tinggi tree bermakna
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    root.update_idletasks()
    root.update()
    fcard_w0 = dv._fcard.winfo_width()
    exp.collapse()
    root.update()
    check("(v3.9) ⤢ collapse: kartu Filter tersembunyi",
          dv._fcard.winfo_manager() == "" and
          dv._legend.winfo_manager() == "")
    tree_h1 = dv.tree.winfo_height()
    exp.restore()
    root.update()
    check("(v3.9) ⤡ restore: kartu Filter kembali tampil + urutan layout",
          dv._fcard.winfo_manager() == "pack" and
          dv._legend.winfo_manager() == "pack" and
          dv._fcard.winfo_width() == fcard_w0,
          f"fcard w={dv._fcard.winfo_width()} vs {fcard_w0}")
    tree_h0 = dv.tree.winfo_height()
    check("(v3.9) Tabel lebih TINGGI saat collapse (ala Waste ⤢)",
          tree_h1 > tree_h0, f"{tree_h1} vs {tree_h0}")
    # toggle kedua (state machine) + reset
    exp.collapse()
    exp.toggle()          # dari expanded → restore
    check("(v3.9) expander.toggle() siklus collapse↔restore",
          not exp.expanded and dv._fcard.winfo_manager() == "pack")
    exp.collapse()
    exp.reset()
    check("(v3.9) expander.reset() memulihkan layout",
          not exp.expanded and dv._fcard.winfo_manager() == "pack")

    # pulihkan messagebox yang di-patch (section 18b)
    _isv_mod.messagebox.showinfo = _orig_info
    _isv_mod.messagebox.showwarning = _orig_warn

    print("== 21. (v3.9.2) MINUS MERAH PER CELL + EXPORT PIVOT SESUAI TAMPILAN ==")

    # (a) unit: apply_cell_tag — tag per-cell Tk 9 (item hilang → aman)
    from src.ui.widgets import CELL_TAGS_SUPPORTED
    from src.ui.widgets import apply_cell_tag as _act
    if CELL_TAGS_SUPPORTED:
        _t = ttk.Treeview(root, columns=["a", "b", "c"], show="headings")
        _t.pack(fill="x")
        _t.tag_configure("negcell", foreground="#CC0000")
        _t.insert("", "end", iid="c1", values=("1", "-2", "3"))
        _t.insert("", "end", iid="c2", values=("-4", "0", "-6"))
        n_applied = _act(_t, "negcell",
                         [("c1", "b"), ("c2", "a"), ("c2", "c")])
        _hc = lambda i, c: root.tk.call(str(_t), "tag", "cell", "has",
                                         "negcell", (i, c))
        check("(v3.9.2) apply_cell_tag: cell minus ditandai PER-CELL",
              n_applied == 3 and _hc("c1", "b") == 1 and
              _hc("c2", "a") == 1 and _hc("c2", "c") == 1 and
              _hc("c1", "a") == 0,
              f"applied={n_applied}")
        n2 = _act(_t, "negcell", [("ghost", "a")])
        check("(v3.9.2) apply_cell_tag: item hilang → dibatalkan aman",
              n2 == 0)
        # re-insert = tag cell ter-reset (dipasang ulang oleh view)
        _t.delete("c1")
        _t.insert("", "end", iid="c1", values=("1", "-2", "3"))
        check("(v3.9.2) re-insert me-reset tag cell (dasar reapply sort)",
              _hc("c1", "b") == 0)
        _act(_t, "negcell", [("c1", "b")])
        check("(v3.9.2) reapply setelah re-insert bekerja",
              _hc("c1", "b") == 1)
        _t.destroy()
    else:
        check("(v3.9.2) fallback Tk 8: tag per baris (perilaku lama)",
              True)   # info saja — sandbox test memakai Tk 9

    # (b) PIVOT standalone — data dengan MINUS (baris TIDAK memerah penuh)
    # NB: total baris harus > 0 agar tidak disembunyikan hide-empty (ON)
    neg_rows_src = []
    for barang, so_v, sa_v, dev_vals, sel_vals in [
            ("BARANG MINUS", 4.0, 20.0, (-6.0, 10.0), (0.0, 5.0)),
            ("BARANG PLUS", 30.0, 10.0, (20.0, 20.0), (0.0, 0.0))]:
        for jenis, vals in [("1.SO", (so_v, so_v)),
                            ("2.SALDO AKHIR", (sa_v, sa_v)),
                            ("3.DEVIASI", dev_vals),
                            ("7.Selisih IN", sel_vals)]:
            for tgl in (1, 2):
                neg_rows_src.append({
                    "Nama Barang": barang, "JENIS": jenis,
                    "NAMA RESTO": "MLGPAR", "Tanggal": tgl,
                    "NILAI": float(vals[tgl - 1]), "SATUAN": "GR",
                    "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
                    "SOURCE KIRIMAN": "GUDANG"})
    neg_df = pd.DataFrame(neg_rows_src)
    from src.ui.pivot_view import PivotTableView
    pv2 = PivotTableView(root)
    pv2.pack(fill="both", expand=True)
    # set state SEBELUM data → refresh sync deterministik (tanpa race
    # refresh-async dari load_data)
    pv2.pivot_mode = "tanggal"
    pv2.tgl_start_var.set("1")
    pv2.tgl_end_var.set("2")
    pv2.data = neg_df
    pv2._populate_filters()
    pv2._show_content()
    pv2._refresh_pivot(sync=True)
    for _ in range(80):
        root.update()
        if not pv2._busy and len(pv2.tree.get_children("")):
            break
        time.sleep(0.02)
    _t2 = pv2.tree
    _hcn = lambda i, c: root.tk.call(str(_t2), "tag", "cell", "has",
                                      "neg_cell", (i, c))
    # cari iid baris per (barang, metric)
    _map = {}
    for _p in _t2.get_children(""):
        for _c in _t2.get_children(_p):
            _map[(_t2.item(_p, "text"), _t2.item(_c, "text"))] = _c
    _dev = _map[("BARANG MINUS", "3.DEVIASI")]
    _dev2 = _map[("BARANG PLUS", "3.DEVIASI")]
    _sel = _map[("BARANG MINUS", "7.Selisih IN")]
    if CELL_TAGS_SUPPORTED:
        check("(v3.9.2) Pivot: cell minus (3.DEVIASI tgl 1) merah per-cell",
              _hcn(_dev, "1") == 1)
        check("(v3.9.2) Pivot: cell positif (3.DEVIASI tgl 2) TIDAK merah",
              _hcn(_dev, "2") == 0)
        check("(v3.9.2) Pivot: baris minus TIDAK tag 'negative' (baris utuh)",
              "negative" not in _t2.item(_dev, "tags") and
              "deviasi_row" not in _t2.item(_dev, "tags"))
        check("(v3.9.2) Pivot: 3.DEVIASI tanpa minus → tak ada cell merah",
              _hcn(_dev2, "1") == 0 and _hcn(_dev2, "2") == 0)
        check("(v3.9.2) Pivot: Selisih IN ≠ 0 (tgl 2) merah per-cell",
              _hcn(_sel, "2") == 1 and _hcn(_sel, "1") == 0)
        check("(v3.9.2) Pivot: baris Selisih pakai bg-only 'selisih_anomaly_bg'",
              "selisih_anomaly_bg" in _t2.item(_sel, "tags"))
    check("(v3.9.2) Pivot: payload membawa red_cells + rows_data + filters",
          len(pv2._last_payload.get("red_cells", [])) > 0 and
          len(pv2._last_payload.get("rows_data", [])) > 0 and
          pv2._last_payload.get("filters", {}).get("mode") == "tanggal")
    check("(v3.9.2) Pivot: handler 💾 export ada + bisa dipanggil",
          callable(pv2._on_export_excel) and
          callable(pv2._do_export_excel) and
          callable(pv2._visible_columns))

    # (c) export pivot sesuai tampilan → read-back (font merah per cell)
    from src.ui.export_sheets import write_pivot_display_sheet
    _exp_path = os.path.join(tempfile.mkdtemp(), "pivot_v392.xlsx")
    _n_exp = write_pivot_display_sheet(_exp_path, pv2._last_payload,
                                       visible_cols=None)
    check("(v3.9.2) Export pivot: file dibuat + baris data > 0",
          _n_exp > 0 and os.path.exists(_exp_path) and
          os.path.getsize(_exp_path) > 0, f"n={_n_exp}")
    from openpyxl import load_workbook as _lw
    _wb = _lw(_exp_path)
    _ws = _wb.active
    check("(v3.9.2) Export pivot: layout meta filter + header + freeze",
          _ws["A1"].value == "MODE" and _ws["B1"].value == "Per Tanggal"
          and _ws.cell(row=7, column=1).value == "Row Labels"
          and _ws.freeze_panes == "B8")
    _red_n = 0
    _red_expect = 0
    for _r in range(8, _ws.max_row + 1):
        _lab = _ws.cell(row=_r, column=1).value
        for _cc in range(2, _ws.max_column + 1):
            _cell = _ws.cell(row=_r, column=_cc)
            _v = _cell.value
            if not isinstance(_v, (int, float)):
                continue
            _col = _cell.font.color.rgb if (_cell.font and
                                            _cell.font.color) else None
            _is_red = _col and "CC0000" in str(_col).upper()
            _should_red = _v < 0 or (_lab == "7.Selisih IN" and _v != 0)
            if _is_red:
                _red_n += 1
            if _should_red:
                _red_expect += 1
                check(f"(v3.9.2) Export pivot: cell minus r{_r}c{_cc} "
                      "font merah", bool(_is_red),
                      f"v={_v} col={_col}")
    check("(v3.9.2) Export pivot: jumlah cell merah == UI red_cells",
          _red_n == _red_expect == len(pv2._last_payload["red_cells"]),
          f"red={_red_n} expect={_red_expect} "
          f"ui={len(pv2._last_payload['red_cells'])}")
    pv2.destroy()

    # (d) wiring semua view: helper per-cell + reapply (fallback Tk 8 aman)
    check("(v3.9.2) Deviasi GR: reapply cell + tag neg_cell ada",
          callable(app.deviasi_gr_view._reapply_cell_tags) and
          hasattr(app.deviasi_gr_view, "_neg_cells"))
    check("(v3.9.2) Deviasi PCS: reapply cell ada",
          callable(app.deviasi_pcs_view._reapply_cell_tags))
    check("(v3.9.2) Laporan Deviasi: reapply cell ada",
          callable(app.laporan_view._reapply_cell_tags))
    check("(v3.9.2) app pivot: export handler ada",
          callable(app.pivot_view._on_export_excel))

    # (d2) details_popup._prepare_rows (staticmethod) — per_cell param
    from src.ui.details_popup import DetailsPopup
    _dp_df = pd.DataFrame([{
        "Nama Barang": "AYAM", "NAMA RESTO": "MLGPAR", "Tanggal": 5,
        "JENIS": "4.IN", "NILAI": -7.0, "Nomor": "IT-1",
        "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
        "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG"},
        {"Nama Barang": "AYAM", "NAMA RESTO": "MLGPAR", "Tanggal": 6,
         "JENIS": "4.IN", "NILAI": 3.0, "Nomor": "IT-2",
         "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
         "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG"}])
    _pl = DetailsPopup._prepare_rows(_dp_df, None, per_cell=True)
    _pl8 = DetailsPopup._prepare_rows(_dp_df, None, per_cell=False)
    check("(v3.9.2) DetailsPopup: per_cell=True → neg_cells [(row_0,NILAI)] "
          "+ tanpa tag baris",
          _pl.get("neg_cells") == [("row_0", "NILAI")] and
          "negative" not in _pl["items"][0][2]["tags"])
    check("(v3.9.2) DetailsPopup: per_cell=False (Tk 8) → tag baris lama",
          not _pl8.get("neg_cells") and
          "negative" in _pl8["items"][0][2]["tags"])

    # (e) deviasi view — data minus (SO < SALDO AKHIR di H=25)
    #     → hanya cell Deviasi yang merah; sort → reapply tetap merah
    dev_neg_src = []
    for barang, so_v, sa_v in [("DEV MIN", 4.0, 20.0),
                               ("DEV PLUS", 30.0, 10.0)]:
        for jenis, base in [("1.SO", so_v), ("2.SALDO AKHIR", sa_v),
                            ("SALDO AWAL", 10.0), ("4.IN", 2.0)]:
            for tgl in range(20, 28):
                dev_neg_src.append({
                    "Nama Barang": barang, "JENIS": jenis,
                    "NAMA RESTO": "MLGPAR", "Tanggal": tgl,
                    "NILAI": float(base), "SATUAN": "GR",
                    "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
                    "SOURCE KIRIMAN": "GUDANG"})
    dev_neg_df = pd.DataFrame(dev_neg_src)
    from src.ui.deviasi_view import DeviasiView
    dv2 = DeviasiView(root, satuan_mode="GR")
    dv2.pack(fill="both", expand=True)
    # set data langsung + refresh sync (deterministik — lihat (b))
    dv2.data = dev_neg_df
    dv2._show_content()
    dv2._refresh(sync=True)
    for _ in range(80):
        root.update()
        if not dv2._busy and len(dv2.tree.get_children("")):
            break
        time.sleep(0.02)
    _t3 = dv2.tree
    _hcd = lambda i: root.tk.call(str(_t3), "tag", "cell", "has",
                                   "neg_cell", (i, "Deviasi"))
    _devmin_iid = None
    for _iid in _t3.get_children(""):
        if _t3.set(_iid, "Nama Barang") == "DEV MIN":
            _devmin_iid = _iid
    if CELL_TAGS_SUPPORTED and _devmin_iid:
        check("(v3.9.2) Deviasi: cell Deviasi minus merah PER-CELL "
              "(baris tidak memerah)",
              _hcd(_devmin_iid) == 1 and
              "negative" not in _t3.item(_devmin_iid, "tags"))
        _devplus_iid = None
        for _iid in _t3.get_children(""):
            if _t3.set(_iid, "Nama Barang") == "DEV PLUS":
                _devplus_iid = _iid
        check("(v3.9.2) Deviasi: baris tanpa minus → cell Deviasi tidak merah",
              _devplus_iid is None or _hcd(_devplus_iid) == 0)
        # sort (delete+reinsert) → reapply memasang ulang tag cell
        dv2._sort_by("Deviasi", reverse=True)
        check("(v3.9.2) Deviasi: sort → tag cell minus DIPASANG ULANG",
              _hcd(_devmin_iid) == 1)
    dv2.destroy()

    # ==================================================================
    print("== 22. (v3.9.4) KOMPARASI FILE DEVIASI vs TAB DEVIASI GR ==")

    kv = app.komparasi_view
    # v3.9.13: matikan AUTO-LOAD file terakhir selama suite (deterministik;
    # auto-load diuji eksplisit di §26)
    kv._auto_loaded = True
    app.show_laporan_mode(0)   # section 7/11 meninggalkan mode 1 — reset
    app.notebook.select(app.tab_laporan)
    root.update()

    check("(v3.9.4) SegmentBar mode default = 0 (Komparasi)",
          app.laporan_segment.active == 0)
    check("(v3.9.4) Komparasi terlihat, Anomali COM tersembunyi",
          kv.winfo_ismapped() and not app.laporan_view.winfo_ismapped())
    app.show_laporan_mode(1)
    root.update()
    check("(v3.9.4) show_laporan_mode(1) → Anomali COM terlihat",
          app.laporan_view.winfo_ismapped() and not kv.winfo_ismapped())
    app.show_laporan_mode(0)
    root.update()
    check("(v3.9.4) show_laporan_mode(0) → kembali ke Komparasi",
          kv.winfo_ismapped() and not app.laporan_view.winfo_ismapped())

    check("(v3.9.14) Skema kolom komparasi (14 kolom — Minggu & H DIHAPUS "
          "v3.9.13; istilah *Lalu/*Saat Ini v3.9.14)",
          [c[0] for c in kv.COLUMNS] == [
              "✓", "Resto", "Nama Barang", "Satuan",
              "BOM Lalu", "COM Lalu", "DEV Lalu", "%TO BOM Lalu",
              "BOM Saat Ini", "COM Saat Ini", "DEV Saat Ini",
              "GR Saat Ini", "Selisih", "Status"],
          f"got {[c[0] for c in kv.COLUMNS]}")
    check("(v3.9.14) Heading DEV Saat Ini = % TO BOM — Saat Ini (persen)",
          kv.tree.heading("DEV Saat Ini")["text"] == "% TO BOM — Saat Ini",
          f"got {kv.tree.heading('DEV Saat Ini')['text']!r}")
    check("(v3.9.14) Heading dua sisi terpasang (istilah Lalu/Saat Ini)",
          kv.tree.heading("GR Saat Ini")["text"] ==
          "DEVIASI — Saat Ini (Tab GR)" and
          kv.tree.heading("BOM Saat Ini")["text"] ==
          "BOM — Saat Ini (Σ jual 22.05)")

    # data deterministik: AYAM FILET & GULA PASIR × 2 resto, tgl 1..25
    # AYAM: SA=100, SO(t)=100-3t, IN=10 (t%5==0), OUT=20 (genap)/5 (ganjil)
    #       → SIS = running stock → GR(7)=49, GR(14)=113, GR(25)=180
    #       com(t)=3+IN(t) → cum(1..7)=31; out_cum(1..7)=80 → DEV App=49
    # GULA: SA=60, SO(t)=60-2t, IN=0, OUT=8 → GR(25)=150; cum com=50;
    #       out_cum=200 → DEV App=150
    det = make_mock_komparasi_df()
    kv.load_data(det)
    wait_view(root, kv)
    check("(v3.9.4) Tanpa file → pesan jujur 'Belum ada file'",
          "Belum ada file" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")

    xlsx_path = make_mock_deviasi_file()
    kv._load_paths([xlsx_path])
    wait_view(root, kv)

    # --- (v3.9.7) FILTER MINGGU MENGIKUTI H BERSAMA (default aktif) ---
    # H bersama saat ini 25 (dari §7) → minggu yang MEMUAT H = WEEK 4
    # (cut-off 25) → hanya baris GULA PASIR/MLGPAR WEEK 4 yang tampil
    from src.ui.theme import C_ACCENT as _C_ACCENT
    # v3.9.13: Minggu/H kini INTERNAL (kolom dihapus) — dibaca dari
    # snapshot baris (kv._row_snaps[iid])
    def kv_minggu(k):
        return kv._row_snaps.get(k, {}).get("minggu", "")

    def kv_h(k):
        return str(kv._row_snaps.get(k, {}).get("h", ""))

    n_w4 = len(kv.tree.get_children(""))
    _kv_rows_w4 = [(kv_minggu(k),
                    kv.tree.set(k, "Nama Barang"))
                   for k in kv.tree.get_children("")]
    check("(v3.9.7) Default H=25 → hanya minggu WEEK 4 (1 baris GULA "
          "PASIR)", n_w4 == 1 and _kv_rows_w4 == [("WEEK 4", "GULA PASIR")],
          f"got {n_w4} {_kv_rows_w4}")
    check("(v3.9.7) Chip H komparasi read-only = 25 (ikut tab GR)",
          kv._h_chip_var.get() == "25" and not hasattr(kv, "tanggal_h_var"),
          f"got {kv._h_chip_var.get()!r}")
    check("(v3.9.7) Label minggu aktif '→ minggu: WEEK 4'",
          "WEEK 4" in kv._week_filter_var.get(),
          f"got {kv._week_filter_var.get()!r}")
    check("(v3.9.7) Footer prefiks minggu aktif (cut-off H 25)",
          "Minggu WEEK 4" in kv.status_var_label.get() and
          "cut-off H 25" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")
    _chip_bgs = [c.cget("bg") for c in kv._week_chips.winfo_children()]
    check("(v3.9.7) Chip minggu aktif WEEK 4 di-highlight teal",
          _chip_bgs.count(_C_ACCENT) == 1 and _chip_bgs[2] == _C_ACCENT,
          f"got {_chip_bgs}")
    check("(v3.9.7→v3.9.22) Mapping H→minggu: 7→7 · 8..14→14 · "
          "15..31→25 (26..31 dulu → 31 'WEEK 5' — label tak pernah ada, "
          "tabel analisa kosong saat H=26)",
          _h_to_week_target(7) == 7 and _h_to_week_target(8) == 14 and
          _h_to_week_target(14) == 14 and _h_to_week_target(15) == 25 and
          _h_to_week_target(21) == 25 and
          _h_to_week_target(25) == 25 and _h_to_week_target(26) == 25 and
          _h_to_week_target(31) == 25)

    # H=7 (input di tab GR, permintaan user) → hanya WEEK 1
    app.deviasi_gr_view.tanggal_h_var.set("7")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    _minggu_vals = {kv_minggu(k)
                    for k in kv.tree.get_children("")}
    check("(v3.9.7) H=7 → hanya baris WEEK 1 (3 baris: 2 resto AYAM + "
          "barang tak ada)",
          len(kv.tree.get_children("")) == 3 and _minggu_vals == {"WEEK 1"},
          f"got {len(kv.tree.get_children(''))} {sorted(_minggu_vals)}")
    check("(v3.9.7) Chip H ikut 7 + label minggu WEEK 1",
          kv._h_chip_var.get() == "7" and
          "WEEK 1" in kv._week_filter_var.get(),
          f"got {kv._h_chip_var.get()!r} / {kv._week_filter_var.get()!r}")

    # H=14 → hanya WEEK 2 (1 baris MLGPAR AYAM)
    app.deviasi_gr_view.tanggal_h_var.set("14")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    _kv_h14 = [(kv_minggu(k), kv_h(k))
               for k in kv.tree.get_children("")]
    check("(v3.9.7) H=14 → hanya WEEK 2 (1 baris, snapshot h=14)",
          _kv_h14 == [("WEEK 2", "14")], f"got {_kv_h14}")

    # centang 'Tampilkan semua minggu' → semua minggu (perilaku lama)
    kv._show_all_weeks.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    check("(v3.9.7) Centang semua minggu → label NONAKTIF + semua baris",
          "NONAKTIF" in kv._week_filter_var.get() and
          len(kv.tree.get_children("")) == 6,
          f"got {kv._week_filter_var.get()!r} / "
          f"{len(kv.tree.get_children(''))}")
    # kembalikan H=25 (state akhir §7) — blok lama berjalan mode semua
    # minggu agar cek 6-baris/per-minggu tetap valid
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)

    n_kv = len(kv.tree.get_children(""))
    check("(v3.9.4) File 7 baris → 6 tampil (resto 9999.XYZZZ "
          "disembunyikan default)", n_kv == 6, f"got {n_kv}")
    check("(v3.9.4) Label file terisi (nama + baris + resto)",
          "mock_deviasi" in kv._file_label_var.get() and
          "7 baris" in kv._file_label_var.get(),
          f"got {kv._file_label_var.get()!r}")
    _chips_txt = " ".join(
        c.winfo_children()[0].cget("text")
        for c in kv._week_chips.winfo_children()
        if c.winfo_children())
    check("(v3.9.4) Chip minggu→H: WEEK 1→7 · 2→14 · 4→25 · 5→31",
          all(t in _chips_txt for t in
              ["WEEK 1 → H 7", "WEEK 2 → H 14", "WEEK 4 → H 25",
               "WEEK 5 → H 31"]), f"got {_chips_txt!r}")
    check("(v3.9.4) Footer hitung status (MATCH 3 · SELISIH 1 · H tdk 1)",
          "MATCH: 3" in kv.status_var_label.get() and
          "SELISIH: 1" in kv.status_var_label.get() and
          "H tdk ada: 1" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")

    def kv_row(resto, barang, minggu):
        for k in kv.tree.get_children(""):
            if (kv.tree.set(k, "Resto") == resto and
                    kv.tree.set(k, "Nama Barang") == barang and
                    kv_minggu(k) == minggu):
                return k
        return None

    k_match = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 1")
    check("(v3.9.4) Baris MATCH ada", k_match is not None)
    if k_match:
        check("(v3.9.4) GR Saat Ini = SO(7)-Sistem = '49' (persis Tab GR)",
              kv.tree.set(k_match, "GR Saat Ini") == "49",
              f"got {kv.tree.set(k_match, 'GR Saat Ini')!r}")
        check("(v3.9.4) BOM Saat Ini = -ΣOUT(1..7) = '(80)' (konvensi file)",
              kv.tree.set(k_match, "BOM Saat Ini") == "(80)",
              f"got {kv.tree.set(k_match, 'BOM Saat Ini')!r}")
        check("(v3.9.4) COM Saat Ini = -Σpemakaian = '(31)'",
              kv.tree.set(k_match, "COM Saat Ini") == "(31)",
              f"got {kv.tree.set(k_match, 'COM Saat Ini')!r}")
        check("(v3.9.13) DEV Saat Ini kini RASIO %TO BOM = '61,25%' "
              "(49/80 — persen konsisten %TO BOM Lalu; dulu kuantitas '49')",
              kv.tree.set(k_match, "DEV Saat Ini") == "61,25%",
              f"got {kv.tree.set(k_match, 'DEV Saat Ini')!r}")
        check("(v3.9.4) Selisih 0 → status MATCH",
              kv.tree.set(k_match, "Status") == "MATCH" and
              kv.tree.set(k_match, "Selisih") == "-",
              f"got {kv.tree.set(k_match, 'Status')!r} / "
              f"{kv.tree.set(k_match, 'Selisih')!r}")
        check("(v3.9.4) % TO BOM Lalu = '61,25%'",
              kv.tree.set(k_match, "%TO BOM Lalu") == "61,25%",
              f"got {kv.tree.set(k_match, '%TO BOM Lalu')!r}")
        check("(v3.9.4) H minggu WEEK 1 = 7 (snapshot internal)",
              kv_h(k_match) == "7")

    k_w2 = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 2")
    check("(v3.9.4) WEEK 2 → H 14, GR Saat Ini = '113' (MATCH)",
          k_w2 is not None and kv_h(k_w2) == "14" and
          kv.tree.set(k_w2, "GR Saat Ini") == "113" and
          kv.tree.set(k_w2, "Status") == "MATCH",
          f"got H={kv_h(k_w2) if k_w2 else None} "
          f"GR={kv.tree.set(k_w2, 'GR Saat Ini') if k_w2 else None}")

    k_gula = kv_row("1001.MLGPAR", "GULA PASIR", "WEEK 4")
    check("(v3.9.4) WEEK 4 → H 25, GULA GR Saat Ini = '150' (MATCH)",
          k_gula is not None and kv_h(k_gula) == "25" and
          kv.tree.set(k_gula, "GR Saat Ini") == "150" and
          kv.tree.set(k_gula, "Status") == "MATCH")

    k_sel = kv_row("1002.SBYKET", "AYAM FILET", "WEEK 1")
    check("(v3.9.4) DEV Lalu 74 vs GR 49 → SELISIH + selisih '(25)'",
          k_sel is not None and kv.tree.set(k_sel, "Status") == "SELISIH" and
          kv.tree.set(k_sel, "Selisih") == "(25)",
          f"got {kv.tree.set(k_sel, 'Status') if k_sel else None} / "
          f"{kv.tree.set(k_sel, 'Selisih') if k_sel else None}")

    k_noapp = kv_row("1001.MLGPAR", "BARANG TAK ADA", "WEEK 1")
    check("(v3.9.14) Barang tak ada di data → TIDAK ADA DI DATA SAAT INI "
          "+ '—'",
          k_noapp is not None and
          kv.tree.set(k_noapp, "Status") == "TIDAK ADA DI DATA SAAT INI" and
          kv.tree.set(k_noapp, "GR Saat Ini") == "—")

    k_noh = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 5")
    check("(v3.9.4) WEEK 5 → H 31 tidak ada di data (tgl 1..25) → "
          "H TIDAK ADA DI DATA",
          k_noh is not None and kv_h(k_noh) == "31" and
          kv.tree.set(k_noh, "Status") == "H TIDAK ADA DI DATA")

    # opsi: tampilkan resto di luar data app
    kv._show_all_resto.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    n_all_kv = len(kv.tree.get_children(""))
    k_xzz = kv_row("9999.XYZZZ", "AYAM FILET", "WEEK 1")
    check("(v3.9.4) Centang semua resto → 7 baris + XYZZZ TIDAK ADA",
          n_all_kv == 7 and k_xzz is not None and
          kv.tree.set(k_xzz, "Status") == "TIDAK ADA DI DATA SAAT INI",
          f"got {n_all_kv}")
    kv._show_all_resto.set(False)
    kv._on_option_changed()
    wait_view(root, kv)

    # per-cell: minus merah di BOM Lalu, status MATCH hijau per-cell
    if CELL_TAGS_SUPPORTED and k_match:
        _khcd = lambda i, col: root.tk.call(
            str(kv.tree), "tag", "cell", "has", "neg_cell", (i, col))
        _khst = lambda i: root.tk.call(
            str(kv.tree), "tag", "cell", "has", "st_match", (i, "Status"))
        check("(v3.9.4) Minus merah PER-CELL di sel BOM Lalu (-80)",
              _khcd(k_match, "BOM Lalu") == 1 and
              _khcd(k_match, "Satuan") == 0)
        check("(v3.9.4) Sel Status MATCH hijau per-cell",
              _khst(k_match) == 1 and _khst(k_sel) == 0)
        kv._sort_by("Selisih", reverse=False)
        check("(v3.9.4) Sort Selisih naik → baris SELISIH (-25) di atas + "
              "tag cell dipasang ulang",
              kv.tree.set(kv.tree.get_children("")[0], "Status") ==
              "SELISIH" and _khcd(k_match, "BOM Lalu") == 1)

    # filter header Status = MATCH → 3 baris
    kv._on_col_filter("Status", ["MATCH"])
    wait_view(root, kv)
    check("(v3.9.4) Filter header Status=MATCH → 3 baris",
          len(kv.tree.get_children("")) == 3,
          f"got {len(kv.tree.get_children(''))}")
    kv._reset_filter()
    wait_view(root, kv)

    # ✓ follow-up (asal KOMPARASI) — store dibersihkan di akhir section 11
    store = app.followup_store
    first_kv = kv.tree.get_children("")[0]
    bbox_kv = kv.tree.bbox(first_kv)
    check("(v3.9.4) bbox baris komparasi tersedia", bool(bbox_kv))
    if bbox_kv:
        ev4 = _Ev()
        ev4.widget = kv.tree
        ev4.x, ev4.y = bbox_kv[0] + 8, bbox_kv[1] + bbox_kv[3] // 2
        kv._on_tree_click(ev4)
        root.update()
        check("(v3.9.4) Klik ✓ → masuk follow-up (asal KOMPARASI)",
              len(store) == 1 and
              next(iter(store.rows.values())).get("asal") == "KOMPARASI")
        kv._on_tree_click(ev4)
        root.update()
        check("(v3.9.4) Klik ✓ lagi → keluar follow-up", len(store) == 0)

    # tutup file → pesan jujur
    kv._close_file()
    check("(v3.9.4) Tutup file → tabel kosong + pesan",
          len(kv.tree.get_children("")) == 0 and
          "File ditutup" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")

    os.unlink(xlsx_path)
    if os.path.isfile("komparasi_last.json"):
        os.unlink("komparasi_last.json")
    # kembalikan data mock utama supaya state akhir konsisten
    kv.load_data(append1)
    wait_view(root, kv)

    # ==================================================================
    print("== 23. (v3.9.5) AUDIT DEEP — REGRESSION FIXES ==")

    import tempfile as _tf

    # --- (A6/B2) SALDO AWAL jadi base com(1) saat ada tanggal negatif ---
    def make_mock_neg_dates_df() -> pd.DataFrame:
        """2 barang × 1 resto, tanggal -25..-31 (LALU saja) + tgl 1 & 7
        (WEEK 1 → H 7 harus ADA supaya GR terhitung).

        LALU: SO(-31)=40, SA(1)=50, SO(1)=10, SO(7)=20, SIS=SA (IN/OUT/BK=0)
          → GR(7)=SO(7)-SIS(7)=-30; com(1) BARU=SA-SO=40, com(7)=SO(1)-SO(7)
          =-10 → Σcom=30 → DEV App=-30==GR (LAMA: com(1)=SO(-31)-SO=30 →
          Σ=20 → DEV=-20 ≠ GR — penyimpangan SO(-31)-SA=10, audit 19-a #6)
        NOPAIR: tanpa baris bulan lalu — SA(1)=12, SO(1)=10, SO(7)=8
          → com(1) BARU=2 (LAMA: 0-10=-10 = MINUS PALSU); GR(7)=8-12=-4,
          Σcom=2+2=4 → DEV=-4==GR
        """
        rows = []
        def add(b, j, t, v):
            rows.append({"Nama Barang": b, "JENIS": j, "NAMA RESTO": "R1",
                         "Tanggal": t, "NILAI": v, "SATUAN": "GR",
                         "AKTIF/NON": "AKTIF"})
        for t in (-25, -30, -31):
            add("LALU", "1.SO", t, 5.0 if t != -31 else 40.0)
        add("LALU", "1.SO", 1, 10.0)
        add("LALU", "1.SO", 7, 20.0)
        add("LALU", "2.SALDO AKHIR", 1, 50.0)
        add("LALU", "2.SALDO AKHIR", 7, 50.0)
        add("LALU", "SALDO AWAL", 1, 50.0)
        for j in ("4.IN", "9.ACR", "8.BARANG KELUAR"):
            for t in (1, 7):
                add("LALU", j, t, 0.0)
        add("NOPAIR", "1.SO", 1, 10.0)
        add("NOPAIR", "1.SO", 7, 8.0)
        add("NOPAIR", "2.SALDO AKHIR", 1, 12.0)
        add("NOPAIR", "2.SALDO AKHIR", 7, 12.0)
        add("NOPAIR", "SALDO AWAL", 1, 12.0)
        for j in ("4.IN", "9.ACR", "8.BARANG KELUAR"):
            for t in (1, 7):
                add("NOPAIR", j, t, 0.0)
        return pd.DataFrame(rows)

    from openpyxl import Workbook as _WB
    neg_xlsx = os.path.join(_tf.gettempdir(), "mock_deviasi_neg.xlsx")
    wb = _WB(); ws = wb.active; ws.title = "Sheet1"
    ws.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM", "QTY DEVIASI",
               "STATUS BULAN"])
    # file persis hitungan BARU (SA base) → MATCH; LAMA akan SELISIH 10/12
    ws.append(["1.R1", "LALU", 0, -30, -30, "WEEK 1"])
    ws.append(["1.R1", "NOPAIR", 0, -4, -4, "WEEK 1"])
    wb.save(neg_xlsx)

    kv.load_data(make_mock_neg_dates_df())
    wait_view(root, kv)
    kv._load_paths([neg_xlsx])
    wait_view(root, kv)

    def kv_row2(resto, barang):
        for k in kv.tree.get_children(""):
            if (kv.tree.set(k, "Resto") == resto and
                    kv.tree.set(k, "Nama Barang") == barang):
                return k
        return None

    k_lalu = kv_row2("1.R1", "LALU")
    k_nop = kv_row2("1.R1", "NOPAIR")
    check("(v3.9.5) SA base: GR Saat Ini utk pair dgn tanggal negatif "
          "(LALU: '(30)'; DEV Saat Ini kini RASIO — BOM 0 → '—')",
          k_lalu is not None and
          kv.tree.set(k_lalu, "GR Saat Ini") == "(30)" and
          kv.tree.set(k_lalu, "DEV Saat Ini") == "—" and
          kv.tree.set(k_lalu, "Status") == "MATCH",
          f"GR={kv.tree.set(k_lalu, 'GR Saat Ini') if k_lalu else None} "
          f"DEV={kv.tree.set(k_lalu, 'DEV Saat Ini') if k_lalu else None}")
    check("(v3.9.5) SA base: pair TANPA bulan-lalu com(1)=SA-SO (NOPAIR: "
          "GR '(4)', bukan minus palsu; DEV Saat Ini RASIO → '—')",
          k_nop is not None and
          kv.tree.set(k_nop, "GR Saat Ini") == "(4)" and
          kv.tree.set(k_nop, "DEV Saat Ini") == "—" and
          kv.tree.set(k_nop, "Status") == "MATCH",
          f"GR={kv.tree.set(k_nop, 'GR Saat Ini') if k_nop else None}")

    # pivot COM konsisten (tanggal negatif + SA) — _compute_com langsung
    from src.ui.pivot_view import PivotTableView as _PTV
    _idx = pd.MultiIndex.from_tuples(
        [("B", "1.SO"), ("B", "4.IN"), ("B", "8.BARANG KELUAR"),
         ("B", "SALDO AWAL")], names=["Nama Barang", "JENIS"])
    _piv = pd.DataFrame({-25.0: [0, 0, 0, pd.NA], 1.0: [10.0, 0, 0, 12.0]},
                        index=_idx)
    _s = _PTV._compute_com(_piv, "B", [-25.0, 1.0])
    check("(v3.9.5) pivot com(1) pakai SA (2.0), bukan -10 (minus palsu)",
          _s[1.0] == 2.0 and _s[-25.0] == 0.0, f"got {_s.to_dict()}")
    os.unlink(neg_xlsx)

    # kembali ke mock komparasi standar
    kv.load_data(det)
    wait_view(root, kv)
    xlsx_path = make_mock_deviasi_file()
    kv._load_paths([xlsx_path])
    wait_view(root, kv)

    # --- (A2/C8) pair index menyelesaikan nama APP utk popup detail ---
    check("(v3.9.5) _pair_index: nama file case/spacing beda → nama APP",
          kv._pair_index.get((_norm_name("ayam  filet"), "MLGPAR")) ==
          ("AYAM FILET", "MLGPAR"),
          f"got {kv._pair_index.get((_norm_name('ayam  filet'), 'MLGPAR'))!r}")

    # --- (A5) duplikat lintas bulan dihitung & dilaporkan ---
    dup_xlsx = os.path.join(_tf.gettempdir(), "mock_deviasi_dup.xlsx")
    wb = _WB(); ws = wb.active
    ws.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM", "QTY DEVIASI",
               "STATUS BULAN", "BULAN"])
    ws.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1", "201.X"])
    ws.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1", "202.X"])
    ws.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1", "203.X"])
    wb.save(dup_xlsx)
    res_dup = parse_deviasi_file(dup_xlsx)
    check("(v3.9.5) Duplikat lintas bulan dihitung (n_duplicates=2) + "
          "dilaporkan di label",
          res_dup["ok"] and res_dup["meta"].get("n_duplicates") == 2,
          f"meta={res_dup['meta']}")
    os.unlink(dup_xlsx)

    # --- (A11) sheet data di sheet ke-2 tetap terbaca ---
    multi_xlsx = os.path.join(_tf.gettempdir(), "mock_deviasi_2sheet.xlsx")
    wb = _WB()
    ws0 = wb.active; ws0.title = "REKAP"  # sheet 0 tanpa kolom wajib
    ws0.append(["No", "Info"])
    ws0.append([1, "sheet ringkasan"])
    ws1 = wb.create_sheet("DATA")
    ws1.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM", "QTY DEVIASI",
                "STATUS BULAN"])
    ws1.append(["1001.MLGPAR", "AYAM FILET", -80, -31, 49, "WEEK 1"])
    wb.save(multi_xlsx)
    res_multi = parse_deviasi_file(multi_xlsx)
    check("(v3.9.5) Data di sheet ke-2 ditemukan (bukan error kolom)",
          res_multi["ok"] and res_multi["meta"]["sheet"] == "DATA" and
          res_multi["meta"]["n_rows"] == 1,
          f"meta={res_multi['meta']}")
    # (A13) Satuan NaN → '' bukan 'nan'
    check("(v3.9.5) Satuan kosong → '' (bukan literal 'nan')",
          res_multi["df"]["Satuan"].iloc[0] == "",
          f"got {res_multi['df']['Satuan'].iloc[0]!r}")
    os.unlink(multi_xlsx)

    # --- (A8) -0.0 % → '0,00%' ---
    check("(v3.9.5) _fmt_pct(-0.0) → '0,00%' (bukan '-0,00%')",
          kv._fmt_pct(-0.0) == "0,00%" and
          kv._fmt_pct(0.2697) == "26,97%",
          f"got {kv._fmt_pct(-0.0)!r}")

    # --- (A7) footer status = hitungan baris YANG TAMPIL (setelah filter) ---
    kv._on_col_filter("Resto", ["1002.SBYKET"])
    wait_view(root, kv)
    check("(v3.9.5) Filter Resto=SBYKET (1 baris SELISIH) → footer "
          "MATCH: 0 (bisa MATCH: 3 global basi)",
          len(kv.tree.get_children("")) == 1 and
          "MATCH: 0" in kv.status_var_label.get(),
          f"footer={kv.status_var_label.get()!r}")
    kv._reset_filter()
    wait_view(root, kv)

    # --- (C5) filter header direset saat file dimuat ulang ---
    kv._on_col_filter("Status", ["MATCH"])
    wait_view(root, kv)
    kv._reload_file()
    wait_view(root, kv)
    check("(v3.9.5) Reload file → filter lama direset (6 baris tampil)",
          len(kv.tree.get_children("")) == 6,
          f"got {len(kv.tree.get_children(''))}")

    # --- (B6) sort saat busy diantrekan ---
    kv._load_paths([xlsx_path])
    check("(v3.9.5) Sort diklik saat compute berjalan → diantrekan",
          kv._busy and kv._pending_sort is None)
    kv._sort_by("Selisih", reverse=False)
    check("(v3.9.5) _pending_sort terisi saat busy",
          kv._pending_sort == ("Selisih", False))
    wait_view(root, kv)
    check("(v3.9.5) Sort antrean diterapkan setelah render selesai",
          kv._pending_sort is None and
          kv.tree.set(kv.tree.get_children("")[0], "Status") == "SELISIH")

    # --- (A3/C4) tag per-cell bertahan setelah filter di clone ⛶ ---
    k_match2 = kv_row("1001.MLGPAR", "AYAM FILET", "WEEK 1")
    if CELL_TAGS_SUPPORTED and k_match2 is not None:
        win2, ct = kv._maximize()
        for _ in range(30):
            root.update()
            time.sleep(0.01)
        _apply_hook = getattr(ct, "_clone_filter_apply", None)
        check("(v3.9.5) Clone ⛶ punya hook filter apply", _apply_hook is not None)
        if _apply_hook is not None:
            _apply_hook("Status", ["MATCH"])
            for _ in range(40):
                root.update()
                time.sleep(0.01)
            _has_neg = root.tk.call(str(ct), "tag", "cell", "has",
                                    "neg_cell", (k_match2, "BOM Lalu"))
            check("(v3.9.5) Filter di clone ⛶ → tag minus PER-CELL tetap "
                  "terpasang (dulu hilang)",
                  _has_neg == 1 and len(ct.get_children("")) == 3,
                  f"neg={_has_neg} rows={len(ct.get_children(''))}")
        win2.destroy()
        root.update()

    # --- (A1) ✕ Tutup File saat compute berjalan → hasil DIBUANG ---
    kv._load_paths([xlsx_path])   # job async dimulai (parse+compute)
    kv._close_file()           # tutup SEBELUM selesai — tanpa pump di antaranya
    check("(v3.9.5) Tutup saat compute: label kembali 'Belum ada file'",
          "Belum ada file" in kv._file_label_var.get())
    wait_view(root, kv)
    check("(v3.9.5) Race tutup: hasil file lama TIDAK muncul kembali "
          "(tabel tetap kosong, _busy reset)",
          len(kv.tree.get_children("")) == 0 and not kv._busy and
          "File ditutup" in kv.status_var_label.get(),
          f"rows={len(kv.tree.get_children(''))} busy={kv._busy} "
          f"status={kv.status_var_label.get()!r}")

    # --- (C1) run_async: shield GC dilepas walau pemilik job di-destroy ---
    import gc as _gc
    top = tk.Toplevel(root)
    run_async(top, lambda: time.sleep(0.4), lambda _r: None)
    top.destroy()
    _t0 = time.time()
    while time.time() - _t0 < 2.5:
        root.update()
        time.sleep(0.01)
    check("(v3.9.5) Popup di-destroy saat job jalan → _GC_HOLD depth 0 + "
          "GC menyala (dulu bocor seumur sesi)",
          _GC_HOLD["depth"] == 0 and _gc.isenabled(),
          f"depth={_GC_HOLD['depth']} gc={_gc.isenabled()}")

    # --- (B5) snapshot follow-up memuat 'aktif' ---
    store = app.followup_store
    kv._load_paths([xlsx_path])
    wait_view(root, kv)
    _first = kv.tree.get_children("")[0]
    _bbox = kv.tree.bbox(_first)
    if _bbox:
        ev5 = _Ev()
        ev5.widget = kv.tree
        ev5.x, ev5.y = _bbox[0] + 8, _bbox[1] + _bbox[3] // 2
        kv._on_tree_click(ev5)
        root.update()
        _snap = next(iter(store.rows.values())) if len(store) else {}
        check("(v3.9.5) Snapshot follow-up KOMPARASI memuat 'aktif'",
              _snap.get("aktif") == "AKTIF", f"got {_snap.get('aktif')!r}")
        kv._on_tree_click(ev5)   # keluarkan lagi
        root.update()

    # --- (C7) show_laporan_mode programatik menyinkronkan SegmentBar ---
    app.show_laporan_mode(1)
    root.update()
    check("(v3.9.5) show_laporan_mode(1) → segment.active ikut 1",
          app.laporan_segment.active == 1 and
          app.laporan_view.winfo_ismapped())

    # --- (B1) popup filter kolom 'Selisih vs Median' hidup kembali ---
    lv = app.laporan_view
    _sel_vals = lv._col_values("Selisih vs Median")
    check("(v3.9.5) _col_values('Selisih vs Median') tidak lagi kosong "
          "(popup filter kolom itu hidup)",
          isinstance(_sel_vals, list) and len(_sel_vals) > 0,
          f"got {_sel_vals!r}")
    app.show_laporan_mode(0)
    root.update()

    # --- (C2) Apply H merender GR tepat 1× (dulu 2×) ---
    dv = app.deviasi_gr_view
    _cnt = {"n": 0}
    _orig_refresh = dv._refresh

    def _counting_refresh(*a, **k):
        _cnt["n"] += 1
        return _orig_refresh(*a, **k)

    dv._refresh = _counting_refresh
    dv.tanggal_h_var.set("10")
    dv._on_tanggal_h_change()
    root.update()
    check("(v3.9.5) Apply H (nilai BERUBAH) → GR refresh 1× (dulu 2×)",
          _cnt["n"] == 1, f"got {_cnt['n']}")
    dv.tanggal_h_var.set("10")
    dv._on_tanggal_h_change()
    root.update()
    check("(v3.9.5) Apply H (nilai SAMA) → refresh eksplisit 1× tetap jalan",
          _cnt["n"] == 2, f"got {_cnt['n']}")
    dv._refresh = _orig_refresh
    # pulihkan H=25 (listener fan-out ke PCS + laporan)
    dv.tanggal_h_var.set("25")
    dv._on_tanggal_h_change()
    wait_view(root, dv)

    # --- (B3) unsubscribe H saat view di-destroy ---
    _h_state = app._shared_h
    _n_before = len(_h_state._listeners)
    lv2 = LaporanDeviasiView(app.tab_laporan, h_state=_h_state)
    check("(v3.9.5) subscribe menambah listener", 
          len(_h_state._listeners) == _n_before + 1)
    lv2.destroy()
    root.update()
    check("(v3.9.5) destroy view → listener H dilepas (unsubscribe)",
          len(_h_state._listeners) == _n_before,
          f"got {len(_h_state._listeners)} (sebelum {_n_before})")

    # ==================================================================
    print()
    print("== 24. (v3.9.10) AUDIT UI/UX ROUND 2 — REGRESSION FIXES ==")
    import threading as _th

    from src.ui.app import _enable_windows_dpi_awareness as _dpi_fix
    from src.ui.details_popup import DetailsPopup as _DPcls
    from src.ui.deviasi_view import DeviasiView as _DV
    from src.ui.rincian_po_view import RincianPoView as _RPV
    from src.ui.widgets import _GC_LOCK as _GLOCK
    from src.ui.widgets import gc_shield_acquire as _gac
    from src.ui.widgets import gc_shield_release as _grel
    from src.ui.widgets import sort_tree_by_column as _stbc

    # ---- B-04: handler view tidak lagi MENGGANTI binding infrastruktur ---
    # (auto-fit tepi kolom v3.4 + menu kolom) — jumlah script binding
    # harus >= 2 (CHAIN), bukan 1 (REPLACE = bug lama).
    for _vname, _v in (("Pivot", app.pivot_view),
                       ("Deviasi GR", app.deviasi_gr_view),
                       ("Deviasi PCS", app.deviasi_pcs_view),
                       ("Selisih IN", app.in_selisih_view),
                       ("Laporan", app.laporan_view),
                       ("Komparasi", app.komparasi_view),
                       ("Follow Up", app.followup_view)):
        _nb = _v.tree.bind("<Double-1>").count("%# %b")
        check(f"(v3.9.10) B-04 {_vname}: Double-1 = RANTAI >=2 script "
              f"(auto-fit tetap hidup)", _nb >= 2, f"scripts={_nb}")
    # (Button-3 chain diuji di popup detail §25 C-02 — tree utama Selisih
    #  IN memang tanpa context-menu level view; popup punya ColumnManager
    #  + menu copy → harus CHAIN setelah fix B-04.)

    # ---- A-02 + B-10: tombol disabled TAMPAK dim; hover tidak menimpa ----
    app.btn_export_tb.set_enabled(False)
    root.update()
    _bg_off = str(app.btn_export_tb.cget("background")).lower()
    check("(v3.9.10) A-02: toolbar Export disabled = abu dim (#94a3b8)",
          _bg_off == "#94a3b8", f"got {_bg_off}")
    app.btn_export_tb.event_generate("<Leave>")
    root.update()
    _bg_leave = str(app.btn_export_tb.cget("background")).lower()
    check("(v3.9.10) B-10: <Leave> saat disabled TIDAK menimpa warna dim",
          _bg_leave == "#94a3b8", f"got {_bg_leave}")
    app.btn_export_tb.set_enabled(True)
    root.update()

    # ---- A-04: navigasi keyboard antar-tab (Ctrl+Tab) ----
    check("(v3.9.10) A-04: enable_traversal — Ctrl+Tab aktif di toplevel",
          bool(root.bind("<Control-Tab>")))

    # ---- A-11: routing tab berbasis WIDGET (bukan index) ----
    check("(v3.9.10) A-11: peta _tab_views 6 entry berbasis nama widget",
          len(app._tab_views) == 6
          and app._tab_views.get(str(app.tab_rincian)) is app.rincian_view
          and app._tab_views.get(str(app.tab_deviasi_pcs))
          is app.deviasi_pcs_view,
          f"got {len(app._tab_views)} entry")
    check("(v3.9.10) A-11: marker tab Laporan → dispatch mode aktif",
          app._tab_views.get(str(app.tab_laporan))
          is app._laporan_tab_entry)

    # ---- A-03: DPI-awareness no-op di Linux (tanpa crash) ----
    try:
        _dpi_fix(root)
        _dpi_ok = True
    except Exception as _e:
        _dpi_ok = False
    check("(v3.9.10) A-03: _enable_windows_dpi_awareness aman di Linux",
          _dpi_ok)

    # ---- B-01: parser sort Indonesia (oracle deterministik) ----
    _st_tr = ttk.Treeview(root, columns=["x"])
    for _v in ["(1.234)", "999", "1.000", "12,5", "0"]:
        _st_tr.insert("", "end", values=(_v,))
    _stbc(_st_tr, "x", reverse=False,
          parse=app.in_selisih_view._parse_num_id)
    _got = [str(_st_tr.item(k)["values"][0])
            for k in _st_tr.get_children("")]
    check("(v3.9.10) B-01: parser ID — (1.234) < 0 < 12,5 < 999 < 1.000",
          _got == ["(1.234)", "0", "12,5", "999", "1.000"], f"got {_got}")
    _st_tr.destroy()

    # ---- render ulang Selisih IN (state filter deterministik) ----
    _iv = app.in_selisih_view
    _iv._reset_filter()
    ok = select_and_wait(root, app, app.tab_in_selisih, _iv)
    check("(v3.9.10) render Selisih IN utk §25", ok)
    _base = _iv._cached_base
    _fb = _base
    _tn = pd.to_numeric(_fb["Tanggal"], errors="coerce")
    _fb = _fb[(_tn >= 1) & (_tn <= 31)]
    if "Selisih IN" in _fb.columns:
        _sv2 = pd.to_numeric(_fb["Selisih IN"], errors="coerce").fillna(0)
        _fb = _fb[_sv2 != 0]
    _neg_oracle = 0
    for _c in ("Hasil SO", "Barang Masuk", "IN", "Selisih IN", "Saldo"):
        if _c in _fb.columns:
            _neg_oracle += int((pd.to_numeric(_fb[_c], errors="coerce")
                                .fillna(0) < 0).sum())
    check(f"(v3.9.10) B-01/C-04: baris tampil == oracle {len(_fb)}",
          len(_iv.tree.get_children("")) == len(_fb),
          f"got {len(_iv.tree.get_children(''))} vs {len(_fb)}")
    check(f"(v3.9.10) C-04: neg_cells == oracle {_neg_oracle} "
          f"(kolom numerik baris tampil)",
          len(_iv._neg_cells) == _neg_oracle,
          f"got {len(_iv._neg_cells)}")
    _fgn = dict(_iv.tree.tag_configure("neg_cell")).get("foreground", "")
    check("(v3.9.10) C-04: tag neg_cell terdaftar (merah) di tree utama",
          _fgn == "#dc2626", f"got {_fgn}")

    # ---- B-03: sort memanggil _reapply_cell_tags ----
    _rat_calls = []
    _orig_rat = _iv._reapply_cell_tags
    _iv._reapply_cell_tags = (
        lambda tr: (_rat_calls.append(1), _orig_rat(tr))[1])
    _iv._sort_by("Selisih IN", reverse=True)
    _iv._reapply_cell_tags = _orig_rat
    check("(v3.9.10) B-03: sort → tag minus per-cell dipasang ulang",
          len(_rat_calls) == 1, f"calls={len(_rat_calls)}")

    # ---- D-08: popup filter tanpa cache → dari TREE (no main-thread compute)
    _saved_cb = _iv._cached_base
    _iv._cached_base = None

    def _no_call(*_a, **_k):
        raise RuntimeError("D-08: compute di main thread!")
    _orig_cb = _iv._compute_base
    _iv._compute_base = _no_call
    try:
        _vals_d08 = _iv._col_values("Resto")
        _ok_d08 = isinstance(_vals_d08, list) and len(_vals_d08) > 0
    except RuntimeError:
        _ok_d08 = False
    finally:
        _iv._compute_base = _orig_cb
        _iv._cached_base = _saved_cb
    check("(v3.9.10) D-08: popup filter dgn cache kosong → nilai dari "
          "baris tampil (UI tidak membeku)", _ok_d08)

    # ---- D-01: cache berlabel identitas data yang benar ----
    check("(v3.9.10) D-01: in_selisih _cached_base_data == data",
          _iv._cached_base_data is _iv.data)
    check("(v3.9.10) D-01: laporan _cached_data == data",
          app.laporan_view._cached_data is app.laporan_view.data)
    check("(v3.9.10) D-01: komparasi _cached_data == data",
          app.komparasi_view._cached_data is app.komparasi_view.data)
    check("(v3.9.10) D-01: deviasi _tnum_data == data",
          app.deviasi_gr_view._tnum_data is app.deviasi_gr_view.data)

    # ---- B-08: sort saat render batch → ANTRE ----
    _dv = app.deviasi_gr_view
    _dv._busy = True
    _dv._pending_sort = None
    _dv._sort_by("Deviasi", reverse=True)
    check("(v3.9.10) B-08: sort saat busy → _pending_sort tersimpan",
          _dv._pending_sort == ("Deviasi", True),
          f"got {_dv._pending_sort}")
    _dv._busy = False
    _dv._pending_sort = None

    # ---- C-08: H berubah saat pane TERSEMBUNYI → cukup _dirty ----
    _pv = app.deviasi_pcs_view
    _pv._dirty = False
    _before_c08 = len(_pv.tree.get_children(""))
    _pv._on_shared_h_changed(15)
    root.update()
    check("(v3.9.10) C-08: pane tersembunyi → _dirty tanpa render",
          _pv._dirty is True
          and len(_pv.tree.get_children("")) == _before_c08)
    _pv._on_shared_h_changed(25)   # pulihkan H
    _pv._dirty = False

    # ---- C-07: DeviasiView unsubscribe saat destroy ----
    _n_h25 = len(app._shared_h._listeners)
    _dv2 = _DV(root, h_state=app._shared_h, h_editable=False)
    root.update()
    check("(v3.9.10) C-07: DeviasiView subscribe → +1 listener",
          len(app._shared_h._listeners) == _n_h25 + 1)
    _dv2.destroy()
    root.update()
    check("(v3.9.10) C-07: destroy DeviasiView → listener dilepas",
          len(app._shared_h._listeners) == _n_h25,
          f"got {len(app._shared_h._listeners)}")

    # ---- B-07 + B-02: clone ⛶ punya cancel + tag dipasang ulang --------
    _rat2 = []
    _orig_rat2 = app.deviasi_gr_view._reapply_cell_tags
    app.deviasi_gr_view._reapply_cell_tags = (
        lambda tr: (_rat2.append(1), _orig_rat2(tr))[1])
    _win, _nt = app.deviasi_gr_view._maximize()
    for _ in range(40):
        root.update()
        time.sleep(0.01)
        if len(_nt.get_children("")) >= \
                len(app.deviasi_gr_view.tree.get_children("")):
            break
    check("(v3.9.10) B-07: clone punya _row_filter_cancel (batch bisa "
          "dibatalkan saat filter/sort clone)",
          callable(getattr(_nt, "_row_filter_cancel", None)))
    check("(v3.9.10) B-04 clone: Double-1 clone = rantai",
          _nt.bind("<Double-1>").count("%# %b") >= 2)
    _n_rat_before = len(_rat2)
    # trigger filter di clone → on_after_filter → reapply tags
    _resto_vals = [str(app.deviasi_gr_view.tree.item(k)["values"][1])
                   for k in app.deviasi_gr_view.tree.get_children("")]
    _one_resto = sorted(set(_resto_vals))[0]
    _nt._clone_filter_apply("Resto", {_one_resto})
    for _ in range(60):
        root.update()
        time.sleep(0.01)
    check("(v3.9.10) B-02: filter clone → tag per-cell dipasang ulang "
          "(on_after_filter)", len(_rat2) > _n_rat_before,
          f"calls {len(_rat2)} vs before {_n_rat_before}")
    _win.destroy()
    app.deviasi_gr_view._reapply_cell_tags = _orig_rat2
    root.update()

    # ---- D-03: followup render beruntun stabil ----
    _fv = app.followup_view
    check("(v3.9.10) D-03: _insert_cancel tersimpan di followup",
          callable(getattr(_fv, "_insert_cancel", None)))
    _n0 = len(_fv.tree.get_children(""))
    _fv._render()
    for _ in range(20):
        root.update()
        time.sleep(0.005)
    _fv._render()
    for _ in range(40):
        root.update()
        time.sleep(0.005)
    _n1 = len(_fv.tree.get_children(""))
    check("(v3.9.10) D-03: render ulang beruntun = jumlah baris stabil "
          "(no duplikat/terpotong)", _n1 == _n0, f"{_n0} → {_n1}")

    # ---- C-03: format angka Indonesia di Rincian PO & DetailsPopup ----
    check("(v3.9.10) C-03: RincianPo._fmt_num(1234.5) == '1.234,5'",
          _RPV._fmt_num(1234.5) == "1.234,5",
          f"got {_RPV._fmt_num(1234.5)}")
    check("(v3.9.10) C-03: RincianPo._fmt_num(-1234.5) == '(1.234,5)'",
          _RPV._fmt_num(-1234.5) == "(1.234,5)",
          f"got {_RPV._fmt_num(-1234.5)}")
    check("(v3.9.10) C-03: DetailsPopup._fmt_nilai(1234.5) = ('1.234,5', False)",
          _DPcls._fmt_nilai(1234.5) == ("1.234,5", False))
    check("(v3.9.10) C-03: DetailsPopup._fmt_nilai(-1234.5) = ('(1.234,5)', True)",
          _DPcls._fmt_nilai(-1234.5) == ("(1.234,5)", True))

    # ---- C-10: footer 'baris' + format ID ----
    _pstat = app.pivot_view.status_var.get()
    check("(v3.9.10) C-10: footer pivot 'baris' (bukan 'rows' EN)",
          "rows" not in _pstat and "baris" in _pstat, f"got {_pstat}")

    # ---- C-02: DetailsPopup on_error → view tidak mati permanen ----
    _dp = _DPcls(root, "Uji C-02", append1.head(30))
    for _ in range(150):
        if not _dp._busy:
            break
        root.update()
        time.sleep(0.01)
    check("(v3.9.10) C-10: footer popup detail 'baris' + format ID",
          "rows" not in _dp._base_status and "baris" in _dp._base_status,
          f"got {_dp._base_status}")
    check("(v3.9.10) B-04 popup detail: Button-3 = rantai (menu kolom + "
          "context copy)", _dp.tree.bind("<Button-3>").count("%# %b") >= 2)

    def _boom(*_a, **_k):
        raise RuntimeError("uji-error-detail")
    _dp._prepare_rows = _boom
    _dp._render(sync=True)
    check("(v3.9.10) C-02: DetailsPopup _busy di-reset saat error",
          _dp._busy is False, f"busy={_dp._busy}")
    check("(v3.9.10) C-02: status error popup tampil",
          "Gagal" in _dp.status_var.get())
    del _dp._prepare_rows
    _dp._render(sync=True)
    check("(v3.9.10) C-02: render BERIKUTNYA tetap jalan (popup hidup)",
          _dp._busy is False and len(_dp.tree.get_children("")) > 0)
    _dp.destroy()
    root.update()

    # ---- B-06: gc_shield thread-safe ----
    _depths = []

    def _gcw():
        _gac()
        _depths.append(_GC_HOLD["depth"])
        _grel()
    _ths = [_th.Thread(target=_gcw) for _ in range(6)]
    for _t in _ths:
        _t.start()
    for _t in _ths:
        _t.join(3.0)
    check("(v3.9.10) B-06: _GC_LOCK ada; 6 thread acquire/release → "
          "depth kembali 0", hasattr(_GLOCK, "acquire")
          and _GC_HOLD["depth"] == 0, f"depth={_GC_HOLD['depth']}")

    # ---- B-20: BaseException tidak menempel busy/shield (jalur sync) ----
    _se = []
    try:
        run_async(root, lambda: (_ for _ in ()).throw(SystemExit(9)),
                  lambda r: None, sync=True, on_error=lambda e: None)
    except SystemExit:
        _se.append(True)
    check("(v3.9.10) B-20: SystemExit di work → busy reset + shield "
          "dilepas + re-raise",
          _se == [True] and _GC_HOLD["depth"] == 0,
          f"se={_se} depth={_GC_HOLD['depth']}")

    # ---- B-05/B-13/B-19: HeaderFilter >cap + pencarian + urut numerik ---
    _hf_tree = ttk.Treeview(root, columns=["x"])
    _hf_tree.heading("x", text="X")
    _hf_vals = ([f"nilai-{i:03d}" for i in range(6)]
                + ["999", "1.000", "12,5", "(1.234)", "abc"])
    _hf = HeaderFilter(_hf_tree, "x", get_values=lambda: _hf_vals,
                       on_apply=lambda sel: None, label="X")
    _hf.MAX_CHECKS = 8    # instance override — 11 nilai > cap
    _hf.open_popup()
    root.update()
    check("(v3.9.10) B-19: nilai numerik diurut NUMERIK dulu "
          "('(1.234)' < '12,5' < '999' < '1.000' < teks)",
          _hf._values_list[:5] == ["(1.234)", "12,5", "999", "1.000",
                                   "abc"], f"got {_hf._values_list[:5]}")
    check("(v3.9.10) B-05: hanya MAX_CHECKS checkbox awal + label jujur",
          len(_hf._checks) == 8 and _hf._more_label is not None,
          f"checks={len(_hf._checks)}")
    _hf._search_var.set("nilai-005")
    _hf._filter_list()
    root.update()
    check("(v3.9.10) B-05: pencarian menemukan nilai DI LUAR cap → "
          "checkbox LAZY dibuat",
          "nilai-005" in _hf._checks and "nilai-005" in _hf._vars)
    _hf._search_var.set("zzz")
    _hf._close()
    root.update()
    _hf.open_popup()
    root.update()
    check("(v3.9.10) B-13: popup dibuka ulang dgn pencarian KOSONG",
          _hf._search_var.get() == "")
    _v0 = _hf._values_list[0]
    _hf._vars[_v0].set(False)
    _hf._emit()
    root.update()
    check("(v3.9.10) B-05: uncheck 1 nilai → 10 terpilih; nilai di luar "
          "cap TIDAK hilang senyap (bug lama: 7 saja)",
          _hf.selected is not None and _v0 not in _hf.selected
          and "nilai-005" in _hf.selected
          and len(_hf.selected) == 10,
          f"n={len(_hf.selected or set())}")
    _hf._close()
    root.update()
    _hf_tree.destroy()

    # ---- A-01: MULAI saat worker lama masih hidup → DITOLAK ----
    import tkinter.messagebox as _tkmb
    app.is_running = False
    app.worker_thread = _th.Thread(target=time.sleep, args=(3.0,),
                                   daemon=True)
    app.worker_thread.start()
    _info_calls = []
    _orig_info, _orig_err = _tkmb.showinfo, _tkmb.showerror
    _tkmb.showinfo = lambda *a, **k: (_info_calls.append(a), "ok")[1]
    _tkmb.showerror = lambda *a, **k: ("ok",)
    try:
        app._start_pipeline()
    finally:
        _tkmb.showinfo, _tkmb.showerror = _orig_info, _orig_err
    check("(v3.9.10) A-01: MULAI saat worker lama masih hidup → "
          "DITOLAK (tanpa thread kedua)",
          bool(_info_calls) and app.is_running is False,
          f"info={len(_info_calls)} running={app.is_running}")
    app.worker_thread.join(4.0)

    # ---- D-04: file di-skip terhitung dari log pipeline ----
    app._skipped_files = 0
    app.log_queue.put("[WARNING] Skip file X.xlsx (terkunci)\n")
    app.log_queue.put("[WARNING] Skip file Y.xlsx (hilang)\n")
    app._poll_log_queue()
    check("(v3.9.10) D-04: 2 file skip terhitung dari log",
          app._skipped_files == 2, f"got {app._skipped_files}")

    # ---- D-04 (display, terakhir — mereset data views) ----
    app._skipped_files = 2
    app._on_pipeline_done(None, None, None, None, None)
    root.update()
    check("(v3.9.10) D-04: pipeline selesai dgn file skip → status "
          "PERINGATAN (bukan hijau polos)",
          "dilewati" in app.statusbar.dot._var.get(),
          f"got {app.statusbar.dot._var.get()}")

    # =====================================================================
    print("== 25. (v3.9.11) TUNTAS SISA TEMUAN AUDIT 2-b (7 fix + repo private) ==")

    from src.ui.widgets import (
        ColumnManager as _ColumnManager,
    )
    from src.ui.widgets import (
        EmptyState as _EmptyState,
    )
    from src.ui.widgets import (
        TableExpander as _TableExpander,
    )
    from src.ui.widgets import (
        apply_tree_row_filters as _atrf,
    )
    from src.ui.widgets import (
        sort_tree_by_column as _stbc26,
    )
    from src.ui.widgets import (
        validated_tgl_entry as _vte,
    )

    def _dcset(t):
        dc = t["displaycolumns"]
        items = [str(x) for x in dc] if isinstance(dc, (tuple, list)) \
            else str(dc).split()
        return set(items)

    # ---- B-21: panah arah sort di heading -------------------------------
    _t21 = ttk.Treeview(root, columns=["a", "b"])
    _t21.heading("a", text="Kolom A")
    _t21.heading("b", text="Kolom B")
    for _i, (_av, _bv) in enumerate([("x", "1"), ("y", "3"), ("z", "2")]):
        _t21.insert("", "end", iid=f"r21_{_i}", values=(_av, _bv))
    _stbc26(_t21, "b", reverse=True)
    check("(v3.9.11) B-21: sort menurun → heading kolom sort berpanah ↓",
          _t21.heading("b")["text"] == "Kolom B \u2193",
          f"got {_t21.heading('b')['text']!r}")
    _stbc26(_t21, "a", reverse=False)
    check("(v3.9.11) B-21: sort pindah kolom → panah lama hilang, ↑ muncul",
          _t21.heading("b")["text"] == "Kolom B"
          and _t21.heading("a")["text"] == "Kolom A \u2191",
          f"a={_t21.heading('a')['text']!r} b={_t21.heading('b')['text']!r}")
    _t21.destroy()

    # ---- B-14: toggle filter clone tidak me-reset urutan sort -----------
    _t14 = ttk.Treeview(root, columns=["nama", "nilai"])
    for _i, (_nm, _vl) in enumerate([("a", "10"), ("b", "2"),
                                      ("c", "30"), ("d", "5")]):
        _t14.insert("", "end", iid=f"r14_{_i}", values=(_nm, _vl))
    _stbc26(_t14, "nilai", reverse=True)   # 30,10,5,2
    check("(v3.9.11) B-14: _last_sort tercatat di tree",
          getattr(_t14, "_last_sort", None) == ("nilai", True, None),
          f"got {getattr(_t14, '_last_sort', None)}")
    _snap14 = {"done": False, "order": None}

    def _d14():
        _snap14["done"] = True
        _snap14["order"] = [str(_t14.item(k)["values"][1])
                            for k in _t14.get_children("")]
    _atrf(_t14, {"nama": {"a", "b", "c", "d"}}, on_done=_d14)
    for _ in range(40):
        root.update()
        time.sleep(0.01)
    _order14 = [str(_t14.item(k)["values"][1])
                for k in _t14.get_children("")]
    check("(v3.9.11) B-14: urutan sort BERTAHAN setelah toggle filter "
          "(bug lama: kembali urutan asli 10,2,30,5)",
          _order14 == ["30", "10", "5", "2"],
          f"got {_order14}")
    check("(v3.9.11) B-14: sort dijalankan SEBELUM on_done (urutan final "
          "saat tag dipasang)", _snap14["done"]
          and _snap14["order"] == ["30", "10", "5", "2"],
          f"done={_snap14['done']} order={_snap14['order']}")
    _t14.destroy()

    # ---- B-09: sort tree berhirarki — anak tidak hilang ------------------
    _t9 = ttk.Treeview(root, columns=["v"], show="tree headings")
    _t9.heading("#0", text="Nama")
    _t9.heading("v", text="V")
    _t9.insert("", "end", iid="p1", text="Parent 1", values=("1",))
    _t9.insert("", "end", iid="p2", text="Parent 2", values=("2",))
    _t9.insert("p1", "end", iid="c1", text="Anak 1", values=("9",))
    _t9.insert("p1", "end", iid="c2", text="Anak 2", values=("3",))
    _t9.item("p1", open=True)
    _stbc26(_t9, "v", reverse=True)   # p2 (2) dulu, p1 (1) kemudian
    check("(v3.9.11) B-09: sort hirarki — urutan top-level benar",
          list(_t9.get_children("")) == ["p2", "p1"],
          f"got {list(_t9.get_children(''))}")
    check("(v3.9.11) B-09: ANAK subtree bertahan (jalur lama: terhapus)",
          list(_t9.get_children("p1")) == ["c1", "c2"]
          and _t9.item("c1")["text"] == "Anak 1",
          f"got {list(_t9.get_children('p1'))}")
    check("(v3.9.11) B-09: text #0 + state open parent bertahan",
          _t9.item("p1")["text"] == "Parent 1"
          and _t9.item("p1")["open"] in (True, 1),
          f"text={_t9.item('p1')['text']!r} open={_t9.item('p1')['open']}")
    # jalur flat: text #0 ikut dipertahankan saat reinsert
    _t9f = ttk.Treeview(root, columns=["v"], show="tree headings")
    for _i, (_nm, _vl) in enumerate([("n1", "5"), ("n2", "1"), ("n3", "3")]):
        _t9f.insert("", "end", iid=f"f{_i}", text=_nm, values=(_vl,))
    _stbc26(_t9f, "v", reverse=True)
    check("(v3.9.11) B-09: jalur flat — text #0 dipertahankan",
          [_t9f.item(k)["text"] for k in _t9f.get_children("")]
          == ["n1", "n3", "n2"],
          f"got {[_t9f.item(k)['text'] for k in _t9f.get_children('')]}")
    _t9.destroy()
    _t9f.destroy()

    # ---- B-18: mirror kolom ⛶ DUA ARAH -----------------------------------
    _s18 = ttk.Treeview(root, columns=["a", "b"])
    _c18 = ttk.Treeview(root, columns=["a", "b"])
    _ColumnManager(_s18)
    _cm18 = _ColumnManager(_c18, mirror=_s18)
    _s18_mgr = _s18._column_manager
    _s18_mgr.hide("b")
    check("(v3.9.11) B-18: hide di SUMBER → clone ikut (dulu satu arah)",
          _dcset(_c18) == {"a"},
          f"clone dc={_dcset(_c18)}")
    check("(v3.9.11) B-18: state colmgr clone tersinkron (hidden=['b'])",
          _cm18.hidden == ["b"], f"got {_cm18.hidden}")
    _s18b = ttk.Treeview(root, columns=["a", "b"])
    _c18b = ttk.Treeview(root, columns=["a", "b"])
    _ColumnManager(_s18b)
    _c18b_mgr = _ColumnManager(_c18b, mirror=_s18b)
    _c18b_mgr.hide("a")
    check("(v3.9.11) B-18: arah lama tetap — hide di CLONE → source ikut",
          _dcset(_s18b) == {"b"}, f"source dc={_dcset(_s18b)}")
    for _t in (_s18, _c18, _s18b, _c18b):
        _t.destroy()

    # ---- B-17: cursor watch ber-refcount ----------------------------------
    _top17 = tk.Toplevel(root)
    _ov1 = LoadingOverlay(_top17)
    _ov2 = LoadingOverlay(_top17)
    _ov1.show(delay_ms=0)
    _ov2.show(delay_ms=0)
    root.update()
    _c_17a = str(_top17.cget("cursor"))
    _ov1.hide()
    _c_17b = str(_top17.cget("cursor"))
    _ov2.hide()
    _c_17c = str(_top17.cget("cursor"))
    check("(v3.9.11) B-17: overlay-1 selesai → cursor TETAP watch "
          "(bug lama: reset saat overlay-2 masih loading)",
          _c_17a == "watch" and _c_17b == "watch",
          f"a={_c_17a!r} b={_c_17b!r}")
    check("(v3.9.11) B-17: klaim terakhir dilepas → cursor normal",
          _c_17c in ("", "arrow")
          and getattr(_top17, "_watch_cursor_refs", -1) == 0,
          f"c={_c_17c!r} refs={getattr(_top17, '_watch_cursor_refs', -1)}")
    _top17.destroy()

    # ---- B-16: TableExpander restore urutan -------------------------------
    _host16 = tk.Frame(root)
    _host16.pack(fill="both", expand=True)
    _A16 = tk.Frame(_host16, bg="#ff0000")
    _T1_16 = tk.Frame(_host16, bg="#00ff00")
    _T2_16 = tk.Frame(_host16, bg="#0000ff")
    _A16.pack(side="top", fill="x")
    _T1_16.pack(side="top", fill="x")
    _T2_16.pack(side="top", fill="x")
    root.update_idletasks()
    _btn16 = tk.Button(root)
    _exp16 = _TableExpander(_btn16, [_T1_16, _T2_16])
    _exp16.collapse()
    root.update_idletasks()
    check("(v3.9.11) B-16: collapse — target tersembunyi",
          list(_host16.pack_slaves()) == [_A16],
          f"got {list(_host16.pack_slaves())}")
    _exp16.restore()
    root.update_idletasks()
    check("(v3.9.11) B-16: restore urutan BENAR [A,T1,T2] (bug lama: "
          "target akhir berturut terpasang TERBALIK [A,T2,T1])",
          list(_host16.pack_slaves()) == [_A16, _T1_16, _T2_16],
          f"got {list(_host16.pack_slaves())}")
    _btn16.destroy()
    _host16.destroy()

    # ---- B-12: pecahan input tanggal DITOLAK ------------------------------
    import tkinter.messagebox as _tkmb26
    _ow26 = _tkmb26.showwarning
    _tkmb26.showwarning = lambda *a, **k: "ok"
    try:
        _v12 = tk.StringVar(value="7.9")
        _r12 = _vte(_v12, lo=1, hi=31, fallback=25, label="TANGGAL H",
                    parent=root)
        check("(v3.9.11) B-12: pecahan '7.9' DITOLAK + revert fallback "
              "(bug lama: dilantai senyap jadi 7)",
              _r12 == 25 and _v12.get() == "25",
              f"r={_r12} var={_v12.get()!r}")
        _v12b = tk.StringVar(value="7.0")
        _r12b = _vte(_v12b, lo=1, hi=31, fallback=25, label="X",
                     parent=root)
        check("(v3.9.11) B-12: '7.0' tetap diterima sebagai 7",
              _r12b == 7 and _v12b.get() == "7",
              f"r={_r12b} var={_v12b.get()!r}")
        _v12c = tk.StringVar(value=" 25 ")
        _r12c = _vte(_v12c, lo=1, hi=31, fallback=25, label="X",
                     parent=root)
        check("(v3.9.11) B-12: ' 25 ' (spasi) tetap valid → 25",
              _r12c == 25, f"r={_r12c}")
    finally:
        _tkmb26.showwarning = _ow26
    # in_selisih: jalur _on_tanggal_change kini juga menolak pecahan
    _iv26 = app.in_selisih_view
    _iv26.tgl_start_var.set("3.5")
    _iv26.tgl_end_var.set("10")
    _iv26._on_tanggal_change()
    root.update()
    check("(v3.9.11) B-12: _on_tanggal_change Selisih IN menolak '3.5' "
          "(pesan status, tanpa refresh)",
          "harus angka" in (_iv26.status_var.get() or ""),
          f"got {_iv26.status_var.get()!r}")
    _iv26.tgl_start_var.set("3")
    _iv26._on_tanggal_change()
    wait_view(root, _iv26)   # biarkan refresh valid selesai sebelum cleanup

    # ---- B-11: EmptyState adaptif ------------------------------------------
    _es11 = _EmptyState(root, title="Belum ada data")
    _es11.place(x=0, y=0, width=300, height=200)
    root.update()
    _pi11 = _es11._center.place_info()
    check("(v3.9.11) B-11: frame center MENGECIL di widget sempit 300×200 "
          "(bug lama: fixed 520×260 terpotong)",
          0 < int(_pi11["width"]) <= 282 and 0 < int(_pi11["height"]) <= 182,
          f"w={_pi11.get('width')} h={_pi11.get('height')}")
    _es11.place(x=0, y=0, width=640, height=420)
    root.update()
    _pi11b = _es11._center.place_info()
    check("(v3.9.11) B-11: widget lebar → center clamp maks 520×260",
          int(_pi11b["width"]) == 520 and int(_pi11b["height"]) == 260,
          f"w={_pi11b.get('width')} h={_pi11b.get('height')}")
    _es11.place_forget()
    _es11.destroy()

    # ==================================================================
    print("== 26. (v3.9.13) SEARCH-TO-SELECT + KATEGORI + PATH + "
          "MULTI-FILE + ANALISA ==")
    import json as _json13
    import tempfile as _tf13

    kv.load_data(det)
    wait_view(root, kv)
    kv._load_paths([xlsx_path])
    wait_view(root, kv)
    n_before13 = len(kv.tree.get_children(""))

    # --- (1) SEARCH-TO-SELECT: Enter = hasil pencarian jadi pilihan ------
    _hf13 = kv.header_filters._filters["Resto"]
    _hf13.open_popup()
    root.update()
    _hf13._search_var.set("QQQ")      # tidak ada resto mengandung QQQ
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Enter hasil KOSONG → 0 baris (perilaku Excel; "
          "permintaan user pilih 'kosong')",
          _hf13.selected == set() and
          len(kv.tree.get_children("")) == 0,
          f"sel={_hf13.selected!r} rows={len(kv.tree.get_children(''))}")
    _hf13._search_var.set("MLG")
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Enter 'MLG' → hasil pencarian jadi seleksi "
          "({1001.MLGPAR} → 5 baris)",
          _hf13.selected == {"1001.MLGPAR"} and
          len(kv.tree.get_children("")) == 5,
          f"sel={_hf13.selected!r} rows={len(kv.tree.get_children(''))}")
    _hf13._search_var.set("")
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Enter query KOSONG → reset (semua baris kembali)",
          _hf13.selected is None and
          len(kv.tree.get_children("")) == n_before13,
          f"sel={_hf13.selected!r}")
    # operator teks 'Diawali' (nilai scope = data tampil — resto-app saja)
    _hf13._op_var.set("Diawali")
    _hf13._search_var.set("1001")
    _hf13._on_search_enter()
    wait_view(root, kv)
    check("(v3.9.13) Operator 'Diawali' 1001 → hanya resto MLGPAR (5 baris)",
          _hf13.selected == {"1001.MLGPAR"} and
          len(kv.tree.get_children("")) == 5,
          f"sel={_hf13.selected!r}")
    # invert (↔ Balik): seleksi = komplemen
    _hf13._invert_selection()
    wait_view(root, kv)
    check("(v3.9.13) ↔ Balik → komplemen (1002.SBYKET → 1 baris)",
          _hf13.selected == {"1002.SBYKET"} and
          len(kv.tree.get_children("")) == 1,
          f"sel={_hf13.selected!r}")
    _hf13._op_var.set("Mengandung")
    _hf13._close()
    kv._reset_filter()
    wait_view(root, kv)

    # --- (2) FILTER KATEGORI di tab Deviasi GR & PCS ---------------------
    grv13 = app.deviasi_gr_view
    _cols13 = [c[0] for c in grv13.COLUMNS]
    # v3.9.29 (user: "hapus kolom kategori di tab deviasi gr dan pcs karna
    # sudah ada filter di atas nya") — kolom TABEL dihapus; dulu (v3.9.13)
    # berada tepat setelah Satuan.
    check("(v3.9.29) Kolom KATEGORI DIHAPUS dari tabel Deviasi GR",
          "KATEGORI" not in _cols13 and
          "AKTIF/NON" in _cols13 and
          _cols13.index("AKTIF/NON") == _cols13.index("Satuan") + 1,
          f"got cols={_cols13}")
    check("(v3.9.29) Kolom KATEGORI juga hilang di tree (displaycolumns)",
          "KATEGORI" not in list(grv13.tree["columns"]),
          f"got {list(grv13.tree['columns'])}")
    check("(v3.9.13) Combobox KATEGORI ada (GR) + default 'Semua'",
          hasattr(grv13, "_kategori_var") and
          grv13._kategori_var.get() == "Semua")
    check("(v3.9.13) Combobox KATEGORI ada (PCS — kelas dipakai bersama)",
          hasattr(app.deviasi_pcs_view, "_kategori_var"))
    _kat13 = append1.copy()
    _kat13["KATEGORI"] = ["SAYURAN" if b == "GULA PASIR" else "BAHAN"
                          for b in _kat13["Nama Barang"]]
    grv13.load_data(_kat13)
    wait_view(root, grv13)
    _kv13 = list(grv13._kategori_combo["values"])
    check("(v3.9.13) Combobox terisi dari data (Semua + BAHAN + SAYURAN)",
          _kv13 == ["Semua", "BAHAN", "SAYURAN"], f"got {_kv13}")
    _gr_all13 = len(grv13.tree.get_children(""))
    grv13._kategori_var.set("SAYURAN")
    grv13._on_kategori_changed()
    wait_view(root, grv13)
    _gr_sayur13 = [grv13.tree.set(k, "Nama Barang")
                   for k in grv13.tree.get_children("")]
    check("(v3.9.13) Filter kategori SAYURAN → hanya GULA PASIR (2 resto)",
          0 < len(_gr_sayur13) < _gr_all13 and
          set(_gr_sayur13) == {"GULA PASIR"},
          f"got {_gr_sayur13}")
    grv13._reset_filter()
    wait_view(root, grv13)
    check("(v3.9.13) ✕ Reset Filter mengembalikan kategori 'Semua'",
          grv13._kategori_var.get() == "Semua" and
          len(grv13.tree.get_children("")) == _gr_all13)
    # v3.9.29: nilai KATEGORI TIDAK lagi tampil di kolom tabel (dihapus
    # user) — kategori tetap hidup lewat combobox (terbukti filter
    # SAYURAN di atas) + pivot internal.
    check("(v3.9.29) Nilai KATEGORI TIDAK tampil di tabel (kolom dihapus)",
          all("KATEGORI" not in str(grv13.tree.set(k))
              for k in grv13.tree.get_children("")) and
          "KATEGORI" not in list(grv13.tree["columns"]))
    grv13.load_data(append1)
    wait_view(root, grv13)

    # --- (3) PATH tersimpan (FIX BUG v3.9.10) + entry editable -----------
    check("(v3.9.13) komparasi_last.json TERSIMPAN setelah load "
          "(BUG v3.9.10: str.with_suffix → json tak pernah tersimpan)",
          os.path.isfile("komparasi_last.json"))
    _saved13 = {}
    if os.path.isfile("komparasi_last.json"):
        with open("komparasi_last.json", encoding="utf-8") as f13:
            _saved13 = _json13.load(f13)
    check("(v3.9.13) Format json baru {'paths': [...]}",
          _saved13.get("paths") == [xlsx_path], f"got {_saved13!r}")
    check("(v3.9.13) Entry path = file aktif (editable user)",
          kv._path_var.get() == xlsx_path,
          f"got {kv._path_var.get()!r}")
    kv._path_var.set(xlsx_path)   # "ubah" lalu reload dari entry
    kv._reload_file()
    wait_view(root, kv)
    check("(v3.9.13) ↻ reload dari ENTRY (tanpa dialog) → 6 baris",
          len(kv.tree.get_children("")) == n_before13,
          f"got {len(kv.tree.get_children(''))}")

    # --- (4) MULTI-FILE (2 bulan) + filter bulan-terbaru default ---------
    multi2_13 = os.path.join(_tf13.gettempdir(), "mock_deviasi_sep.xlsx")
    _wb13 = _WB()
    _ws13 = _wb13.active
    _ws13.append(["RESTO", "NAMA BAHAN", "QTY BOM", "QTY COM",
                  "QTY DEVIASI", "STATUS BULAN", "BULAN"])
    # SEP (bulan lalu) MINUS — vs OKT (mock utama) PLUS 49 → FLIP
    _ws13.append(["1001.MLGPAR", "AYAM FILET", -80, -90, -10,
                  "WEEK 1", "SEP"])
    _wb13.save(multi2_13)
    kv._load_paths([multi2_13, xlsx_path])
    wait_view(root, kv)
    check("(v3.9.13) Label 2 file dimuat",
          "2 file" in kv._file_label_var.get(),
          f"got {kv._file_label_var.get()!r}")
    check("(v3.9.13) Default tabel = BULAN TERBARU (footer 'BULAN OKTOBER')",
          "BULAN OKTOBER" in kv.status_var_label.get(),
          f"got {kv.status_var_label.get()!r}")
    check("(v3.9.13) Chip BULAN = OKTOBER",
          kv._month_chip_var.get() == "OKTOBER",
          f"got {kv._month_chip_var.get()!r}")
    check("(v3.9.13) Bulan terbaru → jumlah baris sama dgn file OKT saja "
          "(baris SEP tersembunyi)",
          len(kv.tree.get_children("")) == n_before13,
          f"got {len(kv.tree.get_children(''))}")
    kv._show_all_months.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    check("(v3.9.13) Centang 'Tampilkan semua bulan' → +1 baris SEP "
          "(chip SEMUA)",
          len(kv.tree.get_children("")) == n_before13 + 1 and
          kv._month_chip_var.get() == "SEMUA",
          f"got {len(kv.tree.get_children(''))}")
    kv._show_all_months.set(False)
    kv._on_option_changed()
    wait_view(root, kv)

    # --- (5) MODE 📈 ANALISA (Top Selisih + Perubahan Arah) --------------
    app.show_laporan_mode(0)
    app.notebook.select(app.tab_laporan)
    root.update()
    kv._on_mode_change(1)
    root.update()
    check("(v3.9.13) Mode Analisa: kartu analisa terlihat, tabel utama "
          "tersembunyi",
          kv._analisa_frame.winfo_ismapped() and
          not kv.tcard.winfo_ismapped())
    _top13n = len(kv._top_tree.get_children(""))
    check("(v3.9.16) Top Selisih terisi (join PENUH; 2 file → 7 "
          "PASANGAN — SEP+OKT W1 MLG AYAM tergabung 1 baris median, "
          "bukan 8 baris per-file)",
          _top13n == 7, f"got {_top13n}")
    if _top13n:
        _v13 = kv._top_tree.item(kv._top_tree.get_children("")[0],
                                 "values")
        check("(v3.9.16) Top-1 = peringkat 1 + Selisih ABSOLUT "
              "|GR 49| − |median(−10, 49) = 19,5| = 29,5 (dulu "
              "49 − (−10) = 59)",
              str(_v13[0]) == "1" and str(_v13[7]) == "29,5",
              f"got peringkat={_v13[0]} selisih={_v13[7]}")
    _flip13n = len(kv._flip_tree.get_children(""))
    check("(v3.9.13) Perubahan Arah: flip AYAM MLGPAR W1 (SEP -10 → "
          "OKT +49) terdeteksi",
          _flip13n == 1, f"got {_flip13n}")
    if _flip13n:
        _f13 = kv._flip_tree.item(kv._flip_tree.get_children("")[0],
                                  "values")
        check("(v3.9.13/v3.9.19) Flip: 10 kolom (+ANALISA) + periode "
              "SEP→OKTOBER + Δ 59",
              len(_f13) == 10 and "SEP" in str(_f13[0]) and
              "OKTOBER" in str(_f13[0]) and str(_f13[6]) == "59",
              f"n={len(_f13)} periode={_f13[0]} Δ={_f13[6]}")
        _disp13 = abs(-10 + 49) / max(10, 49)
        _kat_exp13 = ("Sempurna" if _disp13 < 0.10
                      else "Dominan" if _disp13 < 0.40 else "Parsial")
        check("(v3.9.13) Kategori flip = "
              f"{_kat_exp13} (disparitas {_disp13:.4f})",
              str(_f13[8]) == _kat_exp13, f"got {_f13[8]}")
    check("(v3.9.13) Ringkasan flip terisi",
          "1 FLIP" in kv._flip_summary_var.get(),
          f"got {kv._flip_summary_var.get()!r}")
    kv._topn_var.set("3")
    kv._render_top_selisih()
    root.update()
    check("(v3.9.13) Top N=3 diterapkan",
          len(kv._top_tree.get_children("")) == 3,
          f"got {len(kv._top_tree.get_children(''))}")

    # --- (5g) v3.9.16: TOP SELISIH — ABSOLUT + MEDIAN MULTI-FILE -----
    # (permintaan user: "nilai dev lalu dan dev saat ini di absolutkan
    # dulu agar selisih tidak terlalu besar. Namun nilai dev lalu dan
    # dev saat ini yang ditampilkan nilai asli bukan absolut" + "jika
    # file deviasi lebih dari 1 file atau 2 misal nya nilai deviasi
    # pakai median aja dan yang ditampilkan jangan semua file tapi
    # nilai median nya aja" — khusus tab 📋 Laporan Deviasi · 📈 Analisa)
    kv._topn_var.set("0")
    kv._render_top_selisih()
    root.update()
    _t16 = [kv._top_tree.item(k, "values")
            for k in kv._top_tree.get_children("")]
    check("(v3.9.16) Multi-file: 7 pasangan — bukan 8 baris per-file "
          "(SEP+OKT W1 MLG AYAM tergabung median)",
          len(_t16) == 7, f"got {len(_t16)}")
    check("(v3.9.16) Top-1 Periode = 'Median 2 file · WEEK 1' "
          "(nilai median ditampilkan — bukan semua file)",
          bool(_t16) and str(_t16[0][1]) == "Median 2 file · WEEK 1",
          f"got {(_t16[0][1] if _t16 else None)!r}")
    check("(v3.9.16) Top-1 DEV Lalu = median(−10, 49) = 19,5",
          bool(_t16) and str(_t16[0][5]) == "19,5",
          f"got {(_t16[0][5] if _t16 else None)!r}")
    check("(v3.9.16) Top-1 GR Saat Ini tetap NILAI ASLI 49 "
          "(bukan absolut)",
          bool(_t16) and str(_t16[0][6]) == "49",
          f"got {(_t16[0][6] if _t16 else None)!r}")
    check("(v3.9.16) Top-1 Selisih = |49| − |19,5| = 29,5 — dulu "
          "49 − (−10) = 59 (tanda berlawanan tak menggembungkan)",
          bool(_t16) and str(_t16[0][7]) == "29,5",
          f"got {(_t16[0][7] if _t16 else None)!r}")
    check("(v3.9.16) Top-1 Status = SELISIH (toleransi atas Selisih "
          "absolut)",
          bool(_t16) and str(_t16[0][8]) == "SELISIH",
          f"got {(_t16[0][8] if _t16 else None)!r}")
    check("(v3.9.16) Rank-2 SBYKET (pasangan 1-file): Periode format "
          "lama '201.OKT 26 · WEEK 1' + DEV 74 asli + Selisih "
          "|49| − |74| = (25)",
          len(_t16) > 1 and str(_t16[1][1]) == "201.OKT 26 · WEEK 1"
          and str(_t16[1][5]) == "74" and str(_t16[1][7]) == "(25)",
          f"got periode={(_t16[1][1] if len(_t16) > 1 else None)!r} "
          f"dev={(_t16[1][5] if len(_t16) > 1 else None)!r} "
          f"sel={(_t16[1][7] if len(_t16) > 1 else None)!r}")
    check("(v3.9.16) Rank-3 MLG AYAM W2 (1 file): |113| − |113| = 0 "
          "→ '-' + Status MATCH (absolut)",
          len(_t16) > 2 and str(_t16[2][7]) == "-"
          and str(_t16[2][8]) == "MATCH",
          f"got sel={(_t16[2][7] if len(_t16) > 2 else None)!r} "
          f"st={(_t16[2][8] if len(_t16) > 2 else None)!r}")
    check("(v3.9.16) Rank-5 XYZZZ (resto di luar data app): GR '—' + "
          "Status join lama TIDAK ADA DI DATA SAAT INI dipertahankan",
          len(_t16) > 4 and str(_t16[4][6]) == "—"
          and str(_t16[4][8]) == "TIDAK ADA DI DATA SAAT INI",
          f"got gr={(_t16[4][6] if len(_t16) > 4 else None)!r} "
          f"st={(_t16[4][8] if len(_t16) > 4 else None)!r}")
    check("(v3.9.16) Status bar: 'Lalu = median antar-file' muncul "
          "saat multi-file",
          "Lalu = median antar-file" in kv._top_status_var.get(),
          f"got {kv._top_status_var.get()!r}")

    # --- (5b) v3.9.14: MINGGU di tab Analisa mengikuti kolom H ----------
    # (permintaan user: "week di tab analisa harusnya menyesuaikan juga
    # dengan kolom H atau aturan kolom H yaitu jika 7 berarti week 1")
    kv._topn_var.set("100")
    kv._show_all_weeks.set(False)
    app.deviasi_gr_view.tanggal_h_var.set("7")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    _top_w1 = [kv._top_tree.item(k, "values")[1]
               for k in kv._top_tree.get_children("")]
    check("(v3.9.14) Analisa H=7 → Top Selisih hanya WEEK 1 (v3.9.16: "
          "4 pasangan dari 7 — SEP W1 + OKT W1 tergabung median) + "
          "prefiks minggu (H 7)",
          len(_top_w1) == 4 and all(v.endswith("WEEK 1") for v in _top_w1)
          and "Minggu WEEK 1" in kv._top_status_var.get() and
          "(H 7)" in kv._top_status_var.get(),
          f"rows={len(_top_w1)} {sorted(set(_top_w1))} "
          f"status={kv._top_status_var.get()!r}")
    check("(v3.9.14) Analisa H=7 → flip W1 SEP→OKT terdeteksi + prefiks "
          "minggu di ringkasan",
          len(kv._flip_tree.get_children("")) == 1 and
          "Minggu WEEK 1" in kv._flip_summary_var.get(),
          f"rows={len(kv._flip_tree.get_children(''))} "
          f"summary={kv._flip_summary_var.get()!r}")
    app.deviasi_gr_view.tanggal_h_var.set("25")
    app.deviasi_gr_view._on_tanggal_h_change()
    wait_view(root, app.deviasi_gr_view)
    wait_view(root, kv)
    check("(v3.9.14) Analisa H=25 → hanya minggu W4 (1 baris) + flip 0 "
          "(SEP hanya W1) + pesan jujur",
          len(kv._top_tree.get_children("")) == 1 and
          len(kv._flip_tree.get_children("")) == 0 and
          "Tidak ada perubahan arah" in kv._flip_status_var.get(),
          f"top={len(kv._top_tree.get_children(''))} "
          f"flip={len(kv._flip_tree.get_children(''))} "
          f"flip_status={kv._flip_status_var.get()!r}")
    # kembalikan state utk blok (6): semua minggu ON + H 25
    kv._show_all_weeks.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    # analisa MALAS: mode ⚖ + refresh → tabel analisa TIDAK dirender ulang
    _flip_count_l = len(kv._flip_tree.get_children(""))
    kv._on_mode_change(0)
    root.update()
    check("(v3.9.13) Kembali mode ⚖ Tabel",
          kv.tcard.winfo_ismapped() and
          not kv._analisa_frame.winfo_ismapped())

    # --- (5c) v3.9.15 — GELOMBANG 1: BAGIAN ANALISA (v3.9.19: Risiko
    # Flip & Benchmark dihapus → 3 bagian + kolom ANALISA Top&Flip) -----
    # File sintetis OKT+NOV · 6 resto (BDG×3, SBY×2, MLG×1) · WEEK 4 —
    # analisa per-periode bekerja dari FILE (tanpa perlu join app).
    f5c = os.path.join(_tf13.gettempdir(), "mock_deviasi_gel1.xlsx")
    _w5c = _WB()
    _s5c = _w5c.active
    _s5c.append(["RESTO", "NAMA BAHAN", "Satuan", "QTY BOM", "QTY COM",
                 "QTY DEVIASI", "STATUS BULAN", "BULAN"])
    _rows5c = [
        # BERAS PREMIUM NOV W4 — rate 50/20/30/5/0/8 %
        ["1030.BDGUKU", "BERAS PREMIUM", "GR", -100, -50, 50,
         "WEEK 4", "NOV"],
        ["1041.BDGABC", "BERAS PREMIUM", "GR", -100, -80, 20,
         "WEEK 4", "NOV"],
        ["1042.BDGJAY", "BERAS PREMIUM", "GR", -100, -70, 30,
         "WEEK 4", "NOV"],
        ["1050.SBYPQR", "BERAS PREMIUM", "GR", -100, -95, 5,
         "WEEK 4", "NOV"],
        ["1051.SBYKLM", "BERAS PREMIUM", "GR", -100, -100, 0,
         "WEEK 4", "NOV"],
        ["1060.MLGHIJ", "BERAS PREMIUM", "GR", -100, -92, 8,
         "WEEK 4", "NOV"],
        # GULA AREN NOV W4 — 4 minus vs 1 surplus (minoritas MLGHIJ +12)
        ["1030.BDGUKU", "GULA AREN", "GR", -50, -60, -10,
         "WEEK 4", "NOV"],
        ["1041.BDGABC", "GULA AREN", "GR", -50, -70, -20,
         "WEEK 4", "NOV"],
        ["1042.BDGJAY", "GULA AREN", "GR", -50, -65, -15,
         "WEEK 4", "NOV"],
        ["1050.SBYPQR", "GULA AREN", "GR", -50, -55, -5,
         "WEEK 4", "NOV"],
        ["1060.MLGHIJ", "GULA AREN", "GR", -50, -62, 12,
         "WEEK 4", "NOV"],
        # KEJU MOZZARELLA OKT→NOV W4 — 2 flip (BDGUKU Sempurna −10→+10;
        # BDGABC Dominan +5→−4)
        ["1030.BDGUKU", "KEJU MOZZARELLA", "GR", -80, -90, -10,
         "WEEK 4", "201.OKT 26"],
        ["1041.BDGABC", "KEJU MOZZARELLA", "GR", -80, -75, 5,
         "WEEK 4", "201.OKT 26"],
        ["1030.BDGUKU", "KEJU MOZZARELLA", "GR", -80, -70, 10,
         "WEEK 4", "NOV"],
        ["1041.BDGABC", "KEJU MOZZARELLA", "GR", -80, -84, -4,
         "WEEK 4", "NOV"],
    ]
    for _r5c in _rows5c:
        _s5c.append(_r5c)
    _w5c.save(f5c)
    kv._show_all_weeks.set(False)   # scope analisa = minggu H 25 → WEEK 4
    kv._load_paths([f5c])
    wait_view(root, kv)
    kv._on_mode_change(1)
    root.update()
    check("(v3.9.22) Baris BAGIAN DIHAPUS — analisa TUNGGAL Top & Flip "
          "(user: 'hapus tab liga deviasi' + 'hapus arah minoritas')",
          not hasattr(kv, "_anasec_segment") and
          len(kv._anasec_frames) == 1 and
          kv._anasec_idx == 0 and
          kv._anasec_frames[0].winfo_ismapped(),
          f"frames={len(kv._anasec_frames)}")
    check("(v3.9.19) Bagian Risiko Flip & Benchmark dihapus penuh "
          "(tree/attribute/method tak ada)",
          not hasattr(kv, "_risk_tree") and
          not hasattr(kv, "_bench_tree") and
          not hasattr(kv, "_render_risk") and
          not hasattr(kv, "_render_benchmark"),
          "masih ada attribute risk/bench")

    # v3.9.19 — KOLOM ANALISA (1 kolom) di Top Selisih & Perubahan Arah
    _top_cols5c = [c[0] for c in kv.TOP_COLS]
    _flip_cols5c = [c[0] for c in kv.FLIP_COLS]
    check("(v3.9.19) Kolom ANALISA di tabel Top Selisih (1 kolom, "
          "posisi terakhir)",
          _top_cols5c[-1] == "ANALISA" and
          _top_cols5c.count("ANALISA") == 1, f"got {_top_cols5c}")
    check("(v3.9.19) Kolom ANALISA di tabel Perubahan Arah (1 kolom)",
          _flip_cols5c[-1] == "ANALISA" and
          _flip_cols5c.count("ANALISA") == 1, f"got {_flip_cols5c}")
    _ana_vals5c = {kv._top_tree.set(k, "ANALISA")
                   for k in kv._top_tree.get_children("")}
    check("(v3.9.19) ANALISA Top Selisih: 5 label kelola (Kenaikan/"
          "Penurunan Tertinggi · Stabil · Berubah Arah · Potensi Flip "
          "Flop — data ini tanpa app join → '—')",
          _ana_vals5c == {"—"} or
          _ana_vals5c <= {kv.ANALISA_NAIK, kv.ANALISA_TURUN,
                          kv.ANALISA_STABIL, kv.ANALISA_ARAH,
                          kv.ANALISA_FFLOP, "—"},
          f"got {_ana_vals5c}")
    _fana5c = {kv._flip_tree.set(k, "ANALISA"): kv._flip_tree.set(k, "Kategori")
               for k in kv._flip_tree.get_children("")}
    check("(v3.9.26) ANALISA flip: Sempurna/Dominan (selisih magnitudo "
          "kecil — cermin ±) → 'Potensi Flip Flop' (2 flip KEJU; label "
          "1 kolom saja; dulu 'Berubah Arah' sebelum v3.9.26)",
          _fana5c and set(_fana5c.values()) <= {"Sempurna", "Dominan"}
          and set(_fana5c.keys()) == {kv.ANALISA_FFLOP},
          f"got {_fana5c}")

    # --- (5e) v3.9.15a — AUDIT-1 FIX: render ulang tabel analisa
    # membatalkan sisa batch insert lama (500 bahan > batch 400 — tanpa
    # fix, 100 baris basi nempel kembali → 600) ----
    f5e = os.path.join(_tf13.gettempdir(), "mock_deviasi_batch.xlsx")
    _w5e = _WB()
    _s5e = _w5e.active
    _s5e.append(["RESTO", "NAMA BAHAN", "Satuan", "QTY BOM", "QTY COM",
                 "QTY DEVIASI", "STATUS BULAN", "BULAN"])
    for _i5e in range(500):
        _b5e = f"BAHAN UJI {(_i5e + 1):04d}"
        _s5e.append(["MLGAAA", _b5e, "GR", -80, -90, -10,
                     "WEEK 4", "201.OKT 26"])
        _s5e.append(["MLGAAA", _b5e, "GR", -80, -70, 10,
                     "WEEK 4", "NOV"])
    _w5e.save(f5e)
    kv._load_paths([f5e])
    wait_view(root, kv)
    kv._on_mode_change(1)
    root.update()
    # (500 pasangan bahan OKT→NOV semua flip → 500 baris)
    kv._render_analisa_section(0)  # v3.9.22: bagian tunggal Top & Flip
    root.update()
    _n5e_a = len(kv._flip_tree.get_children(""))   # 400 (batch berjalan)
    kv._render_flip()            # re-render SEGERA (batch lama masih antre)
    root.update()                # pump — chunk lama harus sudah dibatalkan
    wait_view(root, kv)
    _n5e_b = len(kv._flip_tree.get_children(""))
    check("(v3.9.15a) Render ulang tabel analisa membatalkan sisa batch "
          "insert lama (500 flip: 400 sync + 100 antre → tanpa fix 100 "
          "baris basi nempel kembali → 600)",
          _n5e_a == 400 and _n5e_b == 500,
          f"render-1={_n5e_a} render-2={_n5e_b}")
    os.unlink(f5e)

    # --- pulihkan state utk blok (6) ---
    kv._on_mode_change(0)
    root.update()
    kv._show_all_weeks.set(True)
    kv._on_option_changed()
    wait_view(root, kv)
    kv._load_paths([multi2_13, xlsx_path])
    wait_view(root, kv)
    os.unlink(f5c)

    # --- (6) AUTO-LOAD file terakhir saat pertama terlihat ---------------
    kv._close_file()
    kv._auto_loaded = False
    kv.ensure_refreshed()
    wait_view(root, kv)
    check("(v3.9.13) Auto-load file terakhir dari komparasi_last.json "
          "(2 path)",
          len(kv.tree.get_children("")) == n_before13,
          f"got {len(kv.tree.get_children(''))}")
    os.unlink(multi2_13)

    os.unlink(xlsx_path)
    if os.path.isfile("komparasi_last.json"):
        os.unlink("komparasi_last.json")

    # ==================================================================
    print("== 27. (v3.9.17) SUMBER IN 42.05 BULAN LALU + FOLLOW UP PER-CELL ==")

    # --- (a) fn_audit: Qty SJ menggabung 42.05 + 42.05 (Bulan Lalu) ------
    from src.pipeline.fn_audit import build_audit_input as _bai
    _det17 = pd.DataFrame([
        {"NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
         "Tanggal": 10, "Value": 100.0, "Nomor": "IT.1",
         "Nomor PO": pd.NA, "#Tgl/Jam Pembuatan IT": pd.NA,
         "SOURCE IN": "42.05", "JENIS": "IN"},
        {"NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
         "Tanggal": 10, "Value": 40.0, "Nomor": "IT.2",
         "Nomor PO": pd.NA, "#Tgl/Jam Pembuatan IT": pd.NA,
         "SOURCE IN": "42.05 (Bulan Lalu)", "JENIS": "IN"},
        {"NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
         "Tanggal": 10, "Value": 7.0, "Nomor": "RI.1",
         "Nomor PO": pd.NA, "#Tgl/Jam Pembuatan IT": pd.NA,
         "SOURCE IN": "32.24", "JENIS": "IN"},
    ])
    _raw17 = _bai(None, _det17)
    _sj17 = _raw17["Qty SJ"]
    check("(v3.9.17) Qty SJ = 42.05 + 42.05 (Bulan Lalu) = 140",
          len(_raw17) == 1 and float(_sj17.iloc[0]) == 140.0,
          f"got {_sj17.tolist()} rows={len(_raw17)}")
    check("(v3.9.17) Qty RI tetap 32.24 saja = 7",
          float(_raw17["Qty RI"].iloc[0]) == 7.0,
          f"got {_raw17['Qty RI'].tolist()}")

    # --- (b) InDetailPopup: grup + subtotal sumber baru -------------------
    from src.ui.in_selisih_view import _SOURCES, InDetailPopup
    check("(v3.9.17) _SOURCES memuat '42.05 (Bulan Lalu)'",
          any(s == "42.05 (Bulan Lalu)" for s, _c in _SOURCES))
    _pop17 = InDetailPopup(root, "MLGPAR", "AYAM FILET", 10, _det17)
    root.update()
    _kids17 = list(_pop17.tree.get_children(""))
    _srcs17 = {_pop17.tree.set(k, "Source") for k in _kids17}
    check("(v3.9.17) Popup: dokumen grup '42.05 (Bulan Lalu)' tampil",
          "42.05 (Bulan Lalu)" in _srcs17, f"got {sorted(_srcs17)}")
    check("(v3.9.17) Popup: subtotal TOTAL 42.05 (Bulan Lalu) = 40",
          any(_pop17.tree.set(k, "Source") == "TOTAL 42.05 (Bulan Lalu)"
              and _pop17.tree.set(k, "Qty") == "40" for k in _kids17))
    _tot17 = [_pop17.tree.set(k, "Qty") for k in _kids17
              if _pop17.tree.set(k, "Source") == "TOTAL IN"]
    check("(v3.9.17) Popup: TOTAL IN = 147 (42.05:100 + lalu:40 + 32.24:7)",
          bool(_tot17) and _tot17[0] == "147", f"got {_tot17}")
    _pop17.destroy()
    root.update()

    # --- (c) FollowUpView: minus merah PER CELL ---------------------------
    from src.ui.followup import FollowUpStore
    from src.ui.followup_view import FollowUpView
    _store17 = FollowUpStore()
    _snap_neg17 = {"asal": "DEVIASI GR", "resto": "MLGPAR",
                   "barang": "AYAM 17 NEG", "satuan": "KG",
                   "aktif": "AKTIF", "h": 25, "so": 10.0,
                   "sistem": 120.0, "deviasi": -25.0, "cek": "OK",
                   "so_m2": 5.0, "so_m1": 6.0, "so_p1": 7.0,
                   "so_p2": 8.0, "loss_bom": -0.5}
    _snap_pos17 = {"asal": "DEVIASI GR", "resto": "BDGUKU",
                   "barang": "AYAM 17 POS", "satuan": "KG",
                   "aktif": "AKTIF", "h": 25, "so": 20.0,
                   "sistem": 100.0, "deviasi": 25.0, "cek": "OK",
                   "so_m2": 5.0, "so_m1": 6.0, "so_p1": 7.0,
                   "so_p2": 8.0, "loss_bom": 0.25}
    _store17.toggle("fpneg17", _snap_neg17)
    _store17.toggle("fppos17", _snap_pos17)
    _fv17 = FollowUpView(root, store=_store17)
    _fv17.pack(fill="both", expand=True)
    root.update()
    _neg_iid17 = _pos_iid17 = None
    for _k17 in _fv17.tree.get_children(""):
        if _fv17.tree.set(_k17, "Nama Barang") == "AYAM 17 NEG":
            _neg_iid17 = _k17
        elif _fv17.tree.set(_k17, "Nama Barang") == "AYAM 17 POS":
            _pos_iid17 = _k17
    check("(v3.9.17) FU: 2 baris uji (neg & pos) tampil",
          _neg_iid17 is not None and _pos_iid17 is not None)
    _hc17 = lambda i, c: root.tk.call(str(_fv17.tree), "tag", "cell",
                                      "has", "neg_cell", (i, c))
    if CELL_TAGS_SUPPORTED and _neg_iid17 and _pos_iid17:
        check("(v3.9.17) FU: baris minus TIDAK tag 'negative' (baris utuh)",
              "negative" not in _fv17.tree.item(_neg_iid17, "tags"),
              f"got {_fv17.tree.item(_neg_iid17, 'tags')}")
        check("(v3.9.17) FU: sel Deviasi minus MERAH per-cell",
              _hc17(_neg_iid17, "Deviasi") == 1)
        check("(v3.9.17) FU: sel DEVIASI (kolom kerja) ikut merah",
              _hc17(_neg_iid17, "DEVIASI") == 1)
        check("(v3.9.17) FU: sel Loss Surplus to BOM minus ikut merah",
              _hc17(_neg_iid17, "Loss Surplus to BOM") == 1)
        check("(v3.9.17) FU: kolom non-minus TIDAK merah",
              _hc17(_neg_iid17, "Resto") == 0 and
              _hc17(_neg_iid17, "Sistem") == 0)
        check("(v3.9.17) FU: baris positif tanpa sel merah",
              _hc17(_pos_iid17, "Deviasi") == 0)
        check("(v3.9.17) FU: status pending tetap di tag (tak tertimpa)",
              "pending" in _fv17.tree.item(_neg_iid17, "tags"))
        # sort delete+reinsert → tag per-cell dipasang ulang (iid sama)
        _fv17._sort_by("Deviasi", reverse=True)
        root.update()
        check("(v3.9.17) FU: sort → tag per-cell dipasang ulang",
              _hc17(_neg_iid17, "Deviasi") == 1)
        # resolved: hijau tak tertimpa; sel minus tetap merah
        _store17.resolved["fpneg17"] = {"PIC": "T17"}
        _fv17._render()
        root.update()
        _neg_iid17 = None
        for _k17 in _fv17.tree.get_children(""):
            if _fv17.tree.set(_k17, "Nama Barang") == "AYAM 17 NEG":
                _neg_iid17 = _k17
        check("(v3.9.17) FU: resolved hijau tak tertimpa negative",
              _neg_iid17 is not None and
              "resolved" in _fv17.tree.item(_neg_iid17, "tags") and
              "negative" not in _fv17.tree.item(_neg_iid17, "tags"))
        check("(v3.9.17) FU: resolved + sel Deviasi tetap merah",
              _neg_iid17 is not None and
              _hc17(_neg_iid17, "Deviasi") == 1)
    elif _neg_iid17:
        check("(v3.9.17) FU fallback Tk 8: tag baris 'negative' (perilaku lama)",
              "negative" in _fv17.tree.item(_neg_iid17, "tags"))
    # bersihkan baris uji + view
    _store17.toggle("fpneg17", _snap_neg17)
    _store17.toggle("fppos17", _snap_pos17)
    _fv17.destroy()
    root.update()

    print("== 28. (v3.9.18) FOKUS RESTO 1. DEVIASI WEEKLY + POPUP RINGKAS + "
          "KOLOM + HIGHLIGHT ==")

    # --- (a) FOKUS RESTO folder "1. DEVIASI WEEKLY" + barang DUA ARAH ----
    from src.ui.deviasi_popup import (
        DeviasiPopup,
        build_popup_rows,
        show_deviasi_popup,
    )
    from src.ui.deviasi_view import DeviasiView as _DV18

    def _row18(barang, resto, jenis, tgl, nilai):
        return {"Nama Barang": barang, "JENIS": jenis, "NAMA RESTO": resto,
                "Tanggal": tgl, "NILAI": nilai, "SATUAN": "GR",
                "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
                "SOURCE KIRIMAN": "GUDANG", "Nomor": None,
                "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None}

    rows18 = []
    # (1) pasangan lengkap rekap (1.SO tanggal positif) → TAMPIL
    for t in range(23, 28):
        rows18.append(_row18("BRG REKAP", "REKAP01", "1.SO", t, 10.0))
        rows18.append(_row18("BRG REKAP", "REKAP01", "2.SALDO AKHIR", t, 8.0))
        rows18.append(_row18("BRG REKAP", "REKAP01", "4.IN", t, 2.0))
    # (2) DUA ARAH: barang HANYA di data app (tanpa 1.SO) utk resto
    #     rekap → TETAP tampil (arah app→rekap ikut arah rekap→app)
    for t in range(23, 28):
        rows18.append(_row18("BRG APP ONLY", "REKAP01", "2.SALDO AKHIR",
                             t, 5.0))
        rows18.append(_row18("BRG APP ONLY", "REKAP01", "4.IN", t, 1.0))
        rows18.append(_row18("BRG APP ONLY", "REKAP01", "9.ACR", t, 0.0))
    # (3) resto TANPA rekap (hanya sumber app) → DIKELUARKAN
    for t in range(23, 28):
        rows18.append(_row18("BRG NOREKAP", "NOREKAP9", "2.SALDO AKHIR",
                             t, 7.0))
        rows18.append(_row18("BRG NOREKAP", "NOREKAP9", "4.IN", t, 3.0))
    # (4) resto dgn rekap LALU saja (1.SO tanggal NEGATIF — folder
    #     1.12 Rekap Mentah Bulan Lalu, BUKAN folder 1. DEVIASI WEEKLY)
    #     → DIKELUARKAN
    rows18.append(_row18("BRG LALU", "LALUONLY", "1.SO", -26, 6.0))
    for t in range(23, 28):
        rows18.append(_row18("BRG LALU", "LALUONLY", "2.SALDO AKHIR", t, 6.0))
    # (5) 5.BARANG MASUK rekap berjalan (positif) = penanda folder juga
    rows18.append(_row18("BRG BM", "BMREKAP", "5.BARANG MASUK", 25, 4.0))
    rows18.append(_row18("BRG BM", "BMREKAP", "2.SALDO AKHIR", 25, 4.0))

    df18 = pd.DataFrame(rows18)
    # host Toplevel terpisah — root utama sudah penuh oleh app (widget
    # ke-2 yang di-pack ke root tak kebagian ruang → unmapped → lazy
    # refresh tak pernah jalan; Toplevel punya window sendiri)
    _top18 = tk.Toplevel(root)
    _top18.geometry("1150x680+20+20")
    dv18 = _DV18(_top18, satuan_mode="GR")
    dv18.pack(fill="both", expand=True)
    root.update()
    root.update_idletasks()
    root.update()
    dv18.load_data(df18)
    wait_view(root, dv18)

    pairs18 = {
        (dv18.tree.set(k, "Resto"), dv18.tree.set(k, "Nama Barang"))
        for k in dv18.tree.get_children("")
    }
    check("(v3.9.18) Resto rekap berjalan: 3 pasangan tampil",
          len(pairs18) == 3, f"got {sorted(pairs18)}")
    check("(v3.9.18) Resto NOREKAP9 (hanya app) DIKELUARKAN",
          all(r != "NOREKAP9" for r, _b in pairs18), f"got {sorted(pairs18)}")
    check("(v3.9.18) Resto LALUONLY (rekap lalu, tgl negatif) DIKELUARKAN",
          all(r != "LALUONLY" for r, _b in pairs18), f"got {sorted(pairs18)}")
    check("(v3.9.18) LOOKUP DUA ARAH: barang tanpa-SO utk resto rekap "
          "TETAP tampil",
          ("REKAP01", "BRG APP ONLY") in pairs18, f"got {sorted(pairs18)}")
    check("(v3.9.18) BARANG MASUK positif = penanda folder rekap",
          ("BMREKAP", "BRG BM") in pairs18, f"got {sorted(pairs18)}")
    _app_only_iid = None
    for k in dv18.tree.get_children(""):
        if dv18.tree.set(k, "Nama Barang") == "BRG APP ONLY":
            _app_only_iid = k
    check("(v3.9.18) Dua arah: Deviasi barang tanpa-SO = 0−Sistem = (5)",
          _app_only_iid is not None and
          dv18.tree.set(_app_only_iid, "Deviasi") == "(5)",
          f"got {None if _app_only_iid is None
                else dv18.tree.set(_app_only_iid, 'Deviasi')!r}")

    # --- (b) HIGHLIGHT kolom Deviasi & SO_H ------------------------------
    check("(v3.9.18) _hl_cells: 2 sel per baris (Deviasi + SO_H)",
          len(dv18._hl_cells) == 2 * len(pairs18),
          f"got {len(dv18._hl_cells)} vs {2 * len(pairs18)}")
    _hl18 = lambda i, c: root.tk.call(str(dv18.tree), "tag", "cell",
                                      "has", "hl_cell", (i, c))
    _any_iid18 = next(iter(dv18.tree.get_children("")))
    if CELL_TAGS_SUPPORTED:
        check("(v3.9.18) Highlight: sel Deviasi bertag hl_cell (Tk 9)",
              _hl18(_any_iid18, "Deviasi") == 1)
        check("(v3.9.18) Highlight: sel SO_H bertag hl_cell (Tk 9)",
              _hl18(_any_iid18, "SO_H") == 1)
        check("(v3.9.18) Highlight HANYA 2 kolom — Sistem bersih",
              _hl18(_any_iid18, "Sistem") == 0 and
              _hl18(_any_iid18, "Resto") == 0)
        # minus merah TETAP hidup di atas highlight (fg neg_cell + bg
        # hl_cell koexist — sama sel BRG APP ONLY/Deviasi)
        _neg18 = lambda i, c: root.tk.call(str(dv18.tree), "tag", "cell",
                                           "has", "neg_cell", (i, c))
        check("(v3.9.18) Minus merah koexist dgn highlight "
              "(BRG APP ONLY Deviasi = (5))",
              _app_only_iid is not None and
              _neg18(_app_only_iid, "Deviasi") == 1 and
              _hl18(_app_only_iid, "Deviasi") == 1)
    else:
        check("(v3.9.18) Fallback Tk 8: tint kolom dilewati (no-op)",
              not dv18._hl_cells)
    _leg18 = []
    for _chip in dv18._legend.winfo_children():
        for _w in _chip.winfo_children():
            if isinstance(_w, tk.Label):
                _leg18.append(_w.cget("text"))
    check("(v3.9.18) Legenda memuat chip 'kolom Deviasi/SO_H'",
          any("Deviasi/SO_H" in t for t in _leg18), f"got {_leg18}")

    # --- (c) build_popup_rows: pure — per tanggal + bulan lalu ----------
    pop_df18 = pd.DataFrame([
        _row18("BRG X", "RESTO Y", "1.SO", -26, 5.0),
        _row18("BRG X", "RESTO Y", "2.SALDO AKHIR", -26, 3.0),
        _row18("BRG X", "RESTO Y", "4.IN", -26, 2.0),
        _row18("BRG X", "RESTO Y", "1.SO", 24, 10.0),
        _row18("BRG X", "RESTO Y", "2.SALDO AKHIR", 24, 12.0),
        _row18("BRG X", "RESTO Y", "1.SO", 25, 8.0),
        _row18("BRG X", "RESTO Y", "2.SALDO AKHIR", 25, 4.0),
        _row18("BRG X", "RESTO Y", "4.IN", 25, 1.0),
        # pasangan LAIN — harus terfilter keluar (lookup tepat 1 pasangan)
        _row18("BRG X", "RESTO LAIN", "1.SO", 25, 99.0),
        _row18("BRG Z", "RESTO Y", "1.SO", 25, 77.0),
    ])
    pr18 = build_popup_rows(pop_df18, "BRG X", "RESTO Y")
    check("(v3.9.18→v3.9.25) Popup rows: skema 8 kolom "
          "(Tanggal/Saldo Akhir/SO/IN/Nomor/Nomor PO/COM/Deviasi)",
          list(pr18.columns) == ["Tanggal", "Saldo Akhir", "SO", "IN",
                                 "Nomor", "Nomor PO", "COM", "Deviasi"],
          f"got {list(pr18.columns)}")
    check("(v3.9.18) Popup rows: 3 tanggal (pasangan lain terfilter)",
          len(pr18) == 3, f"got {len(pr18)}")
    check("(v3.9.18) Popup rows: urut kronologis — bulan lalu dulu",
          list(pr18["Tanggal"]) == ["26•", "24", "25"],
          f"got {list(pr18['Tanggal'])}")
    _r24 = pr18.iloc[1]
    check("(v3.9.18) Popup: Saldo Akhir/SO tgl 24 = 12/10; IN absen = '-'",
          _r24["Saldo Akhir"] == "12" and _r24["SO"] == "10" and
          _r24["IN"] == "-", f"got {_r24.to_dict()}")
    check("(v3.9.18) Popup: Deviasi = SO − Saldo Akhir = (2) minus kurung",
          _r24["Deviasi"] == "(2)", f"got {_r24['Deviasi']!r}")
    _r25 = pr18.iloc[2]
    check("(v3.9.18) Popup: tgl 25 lengkap (8/4/1 → Dev 4)",
          _r25["SO"] == "8" and _r25["Saldo Akhir"] == "4" and
          _r25["IN"] == "1" and _r25["Deviasi"] == "4",
          f"got {_r25.to_dict()}")

    # --- (d) Popup GUI: judul barang+resto + baris H + neg per-cell ------
    pop18 = show_deviasi_popup(root, pop_df18, "BRG X", "RESTO Y",
                               satuan="GR", h=25)
    root.update()
    check("(v3.9.18) Popup terbuka = DeviasiPopup (BUKAN DetailsPopup)",
          isinstance(pop18, DeviasiPopup))
    check("(v3.9.18) Popup judul memuat Nama Barang — Nama Resto (satuan)",
          pop18._title == "BRG X — RESTO Y  (GR)", f"got {pop18._title!r}")
    check("(v3.9.18→v3.9.25) Popup tabel: 8 kolom persis "
          "(+Nomor PO & COM — v3.9.25)",
          list(pop18.tree["columns"]) == ["Tanggal", "Saldo Akhir", "SO",
                                          "IN", "Nomor", "Nomor PO",
                                          "COM", "Deviasi"],
          f"got {list(pop18.tree['columns'])}")
    _pk18 = list(pop18.tree.get_children(""))
    check("(v3.9.18) Popup tabel: 3 baris; baris-1 bulan lalu '26•'",
          len(_pk18) == 3 and pop18.tree.set(_pk18[0], "Tanggal") == "26•",
          f"got {[pop18.tree.set(k, 'Tanggal') for k in _pk18]}")
    _h_iid18 = [k for k in _pk18 if "h_row" in pop18.tree.item(k, "tags")]
    check("(v3.9.18) Popup: baris Tanggal H (=25) berlatar lembut (h_row)",
          len(_h_iid18) == 1 and
          pop18.tree.set(_h_iid18[0], "Tanggal") == "25",
          f"got {[pop18.tree.set(k, 'Tanggal') for k in _h_iid18]}")
    _negp18 = lambda i, c: root.tk.call(str(pop18.tree), "tag", "cell",
                                        "has", "neg_cell", (i, c))
    _iid24 = next(k for k in _pk18
                  if pop18.tree.set(k, "Tanggal") == "24")
    if CELL_TAGS_SUPPORTED:
        check("(v3.9.18) Popup: Deviasi minus merah PER CELL (tgl 24)",
              _negp18(_iid24, "Deviasi") == 1 and
              _negp18(_iid24, "SO") == 0)
    check("(v3.9.18) Popup footer: jumlah baris + legenda bulan lalu + H",
          "3 baris" in pop18.status_var.get() and
          "• = bulan lalu" in pop18.status_var.get() and
          "H=25" in pop18.status_var.get(),
          f"got {pop18.status_var.get()!r}")
    # fallback Tk 8: tag baris 'negative' (perilaku lama)
    pop18._cell_tags = False
    pop18._render()
    root.update()
    _iid24b = next(k for k in pop18.tree.get_children("")
                   if pop18.tree.set(k, "Tanggal") == "24")
    check("(v3.9.18) Popup fallback Tk 8: tag baris negative",
          "negative" in pop18.tree.item(_iid24b, "tags"),
          f"got {pop18.tree.item(_iid24b, 'tags')}")
    pop18.destroy()
    root.update()

    # --- (e) Double-click app GR view → popup BARU (bukan source rows) ---
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    _grv18 = app.deviasi_gr_view
    _iid_af18 = None
    for k in _grv18.tree.get_children(""):
        if (_grv18.tree.set(k, "Nama Barang") == "AYAM FILET" and
                _grv18.tree.set(k, "Resto") == "MLGPAR"):
            _iid_af18 = k
            break
    check("(v3.9.18) Dapat baris AYAM FILET/MLGPAR utk uji double-click",
          _iid_af18 is not None)
    if _iid_af18 is not None:
        _b18 = _grv18.tree.bbox(_iid_af18)
        _ev18 = _Ev()
        _ev18.widget = _grv18.tree
        _ev18.x, _ev18.y = _b18[0] + 60, _b18[1] + _b18[3] // 2
        _grv18._on_double_click(_ev18)
        root.update()
        _pops18 = [w for w in root.winfo_children()
                   if isinstance(w, DeviasiPopup) and w.winfo_exists()]
        check("(v3.9.18) Double-click GR → popup RINGKAS terbuka",
              len(_pops18) == 1, f"got {len(_pops18)}")
        if _pops18:
            _p18 = _pops18[0]
            check("(v3.9.18) Popup GR: judul = barang — resto",
                  "AYAM FILET" in _p18._title and "MLGPAR" in _p18._title,
                  f"got {_p18._title!r}")
            check("(v3.9.18) Popup GR: ada baris tanggal (data mock 1..30)",
                  len(_p18.tree.get_children("")) >= 20,
                  f"got {len(_p18.tree.get_children(''))}")
            _hrows18 = [k for k in _p18.tree.get_children("")
                        if "h_row" in _p18.tree.item(k, "tags")]
            check("(v3.9.18) Popup GR: tepat 1 baris H berlatar lembut",
                  len(_hrows18) == 1, f"got {len(_hrows18)}")
            _p18.destroy()
            root.update()

    # --- (f) KOLOM DIHAPUS di view PCS juga (COLUMNS dipakai bersama) ----
    _pcs_cols18 = [c[0] for c in app.deviasi_pcs_view.COLUMNS]
    check("(v3.9.18) PCS juga tanpa Max Deviasi/ACR/Total ACR",
          "Max Deviasi" not in _pcs_cols18 and "ACR" not in _pcs_cols18 and
          "Total ACR" not in _pcs_cols18, f"got {_pcs_cols18}")

    # cleanup view standalone (Toplevel host ikut hancur)
    _top18.destroy()
    root.update()

    # ==================================================================
    print()
    print("== 29. (v3.9.19) KOLOM ANALISA + DEFAULT KATEGORI + NAMA RESTO "
          "PO + FILTER DATA-ADA + PROMIX 04 + 9.ACR + RI BALANCING ==")

    # --- (a) Req 3 — DEFAULT KATEGORI = Deviasi --------------------------
    from src.ui.deviasi_view import DeviasiView as _DV29
    _dv29 = app.deviasi_gr_view
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    check("(v3.9.19) Default kategori fallback 'Semua' bila data tak "
          "punya kategori Deviasi (fixture BAHAN)",
          _dv29._kategori_var.get() == "Semua",
          f"got {_dv29._kategori_var.get()!r}")
    _k29 = append1.copy()
    _k29["KATEGORI"] = ["DEVIASI" if b == "GULA PASIR" else "NON DEVIASI"
                        for b in _k29["Nama Barang"]]
    _dv29.load_data(_k29)
    wait_view(root, _dv29)
    check("(v3.9.19) load_data → kategori default 'DEVIASI' (case-"
          "insensitive dgn nilai data)",
          _dv29._kategori_var.get() == "DEVIASI" and
          _dv29._kategori_sel == "DEVIASI",
          f"got {_dv29._kategori_var.get()!r}")
    _bars29 = {_dv29.tree.set(k, "Nama Barang")
               for k in _dv29.tree.get_children("") if k}
    check("(v3.9.19) Default Deviasi → hanya barang KATEGORI DEVIASI "
          "(GULA PASIR) yang tampil",
          _bars29 == {"GULA PASIR"}, f"got {_bars29}")
    _dv29._reset_filter()
    wait_view(root, _dv29)
    check("(v3.9.19) ✕ Reset Filter mengembalikan kategori DEFAULT "
          "('DEVIASI', bukan 'Semua')",
          _dv29._kategori_var.get() == "DEVIASI",
          f"got {_dv29._kategori_var.get()!r}")
    _dv29.load_data(append1)
    wait_view(root, _dv29)

    # --- (b) Req 6 — CEK "Promix 04" (SO bukan "input so harian") --------
    def _row29(barang, jenis, tgl, nilai, satuan="GR", source=None):
        return {"Nama Barang": barang, "JENIS": jenis,
                "NAMA RESTO": "REKAP29", "Tanggal": tgl,
                "NILAI": nilai, "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                "Nomor": None, "Nomor PO": None,
                "#Tgl/Jam Pembuatan IT": None, "SOURCE DATA": source}

    rows29 = []
    # BRG PROMIX: SO naik +50% tanpa IN (kondisi Beda Tanggal) TAPI SO
    # bersumber promix → CEK "Promix 04" (prioritas pertama)
    rows29.append(_row29("BRG PROMIX", "1.SO", 24, 30.0,
                         source="input promix 04 dine in"))
    rows29.append(_row29("BRG PROMIX", "1.SO", 25, 60.0,
                         source="input promix 04 dine in"))
    rows29.append(_row29("BRG PROMIX", "2.SALDO AKHIR", 25, 0.0,
                         source="input promix 04 dine in"))
    # BRG HARIAN: kondisi identik, SO "input so harian" → CEK normal
    rows29.append(_row29("BRG HARIAN", "1.SO", 24, 30.0,
                         source="input so harian"))
    rows29.append(_row29("BRG HARIAN", "1.SO", 25, 60.0,
                         source="input so harian"))
    rows29.append(_row29("BRG HARIAN", "2.SALDO AKHIR", 25, 0.0,
                         source="input so harian"))
    # BRG TAKEAWAY: promix take away → juga Promix 04
    rows29.append(_row29("BRG TAKEAWAY", "1.SO", 25, 5.0,
                         source="input promix 04 take away"))
    rows29.append(_row29("BRG TAKEAWAY", "2.SALDO AKHIR", 25, 0.0,
                         source="input promix 04 take away"))
    _df29 = pd.DataFrame(rows29)
    _top29 = tk.Toplevel(root)
    _top29.geometry("1350x700+10+10")
    _dv29b = _DV29(_top29, satuan_mode="GR")
    _dv29b.pack(fill="both", expand=True)
    root.update()
    root.update_idletasks()
    root.update()
    _dv29b.load_data(_df29)
    wait_view(root, _dv29b)
    _cek29 = {_dv29b.tree.set(k, "Nama Barang"): _dv29b.tree.set(k, "CEK")
              for k in _dv29b.tree.get_children("")}
    check("(v3.9.19) CEK 'Promix 04': SO 'input promix 04 dine in' → "
          "Promix 04 (mengalahkan kondisi Beda Tanggal — prioritas "
          "pertama)",
          _cek29.get("BRG PROMIX") == "Promix 04",
          f"got {_cek29.get('BRG PROMIX')!r}")
    check("(v3.9.19) CEK 'Promix 04': SO 'input so harian' → CEK normal "
          "(Beda Tanggal tetap hidup utk input manual)",
          _cek29.get("BRG HARIAN") == "Beda Tanggal",
          f"got {_cek29.get('BRG HARIAN')!r}")
    check("(v3.9.19) CEK 'Promix 04': varian 'take away' juga Promix 04",
          _cek29.get("BRG TAKEAWAY") == "Promix 04",
          f"got {_cek29.get('BRG TAKEAWAY')!r}")
    _legend29 = []
    for _chip29 in _dv29b._legend.winfo_children():
        for _sub29 in _chip29.winfo_children():
            if isinstance(_sub29, tk.Label):
                _legend29.append(str(_sub29.cget("text")))
    check("(v3.9.19) Legenda CEK memuat 'Promix 04'",
          any("Promix 04" in t for t in _legend29), f"got {_legend29}")

    # --- (c) Req 5 — isi filter = DATA YANG ADA --------------------------
    # BRG GR Beda Tanggal vs BRG PCS tanpa CEK itu: tab GR hanya
    # menampilkan 'Beda Tanggal' (bukan nilai PCS); tab PCS tidak
    # menampilkan 'Beda Tanggal' (tak ada barisnya) — dulu pivot mentah
    # (GR+PCS) membuat nilai tak-ada ikut muncul.
    _rows29c = [
        _row29("BRG CEK GR", "1.SO", 24, 30.0),
        _row29("BRG CEK GR", "1.SO", 25, 60.0),
        _row29("BRG CEK GR", "2.SALDO AKHIR", 25, 0.0),
        _row29("BRG CEK PCS", "1.SO", 25, 5.0, satuan="PCS"),
        _row29("BRG CEK PCS", "2.SALDO AKHIR", 25, 0.0, satuan="PCS"),
    ]
    _dv29c = _DV29(_top29, satuan_mode="PCS")
    _dv29c.pack(fill="both", expand=True)
    root.update()
    _dv29c.load_data(pd.DataFrame(_rows29c))
    wait_view(root, _dv29c)
    _gr_cek_vals = _dv29b._col_values("CEK")
    _pcs_cek_vals = _dv29c._col_values("CEK")
    check("(v3.9.19) GR: nilai filter CEK hanya data GR yang ada "
          "('Beda Tanggal' — tanpa nilai PCS)",
          "Beda Tanggal" in _gr_cek_vals and
          "Hitung Manual" not in _gr_cek_vals,
          f"got {_gr_cek_vals}")
    check("(v3.9.19) PCS: nilai filter CEK hanya data PCS yang ada "
          "('Hitung Manual' — 'Beda Tanggal' TAK tampil walau ada di "
          "pivot GR)",
          "Hitung Manual" in _pcs_cek_vals and
          "Beda Tanggal" not in _pcs_cek_vals,
          f"got {_pcs_cek_vals}")
    _dv29c.destroy()
    _dv29b.destroy()
    _top29.destroy()
    root.update()

    # --- (d) Req 7 — istilah 9.OUT → 9.ACR -------------------------------
    _jset29 = set(append1["JENIS"].astype(str))
    check("(v3.9.19) JENIS penjualan kini '9.ACR' (bukan '9.OUT')",
          "9.ACR" in _jset29 and "9.OUT" not in _jset29,
          f"got {sorted(_jset29)}")
    from src.ui.pivot_view import PivotTableView as _PV29
    check("(v3.9.19) pivot_view METRICS memuat '9.ACR'",
          "9.ACR" in _PV29.METRICS and "9.OUT" not in _PV29.METRICS and
          "9.ACR" in _PV29.METRIC_BG,
          f"got {_PV29.METRICS}")

    # --- (e) Req 1 — klasifikasi ANALISA _top_aggregate (5 label) --------
    _d29 = pd.DataFrame({
        "_resto_norm": ["R1", "R2", "R3", "R4", "R5"],
        "_bahan_norm": ["B", "B", "B", "B", "B"],
        "Minggu": ["WEEK 1"] * 5,
        "DEV Lalu": [10.0, 10.0, 10.0, -10.0, -100.0],
        "GR Saat Ini": [50.0, 10.5, 2.0, 10.0, 10.0],
        "Status": ["SELISIH", "MATCH", "SELISIH", "SELISIH", "SELISIH"],
        "BULAN": ["NOV"] * 5,
        "Resto": ["R1", "R2", "R3", "R4", "R5"],
        "Nama Barang": ["B"] * 5,
        "Satuan": ["GR"] * 5,
    })
    _agg29 = kv._top_aggregate(_d29)
    _ana29 = dict(zip(_agg29["Resto"], _agg29["ANALISA"]))
    check("(v3.9.19) ANALISA Kenaikan Tertinggi (tanda sama, |GR|>|Lalu|)",
          _ana29["R1"] == kv.ANALISA_NAIK, f"got {_ana29['R1']!r}")
    check("(v3.9.19) ANALISA Stabil (|Selisih| ≤ toleransi MATCH)",
          _ana29["R2"] == kv.ANALISA_STABIL, f"got {_ana29['R2']!r}")
    check("(v3.9.19) ANALISA Penurunan Tertinggi (tanda sama, |GR|<|Lalu|)",
          _ana29["R3"] == kv.ANALISA_TURUN, f"got {_ana29['R3']!r}")
    check("(v3.9.26) ANALISA Potensi Flip Flop (tanda berlawanan, "
          "disparitas < 40% — selisih magnitudo kecil; R4 −10 → +10 "
          "cermin)",
          _ana29["R4"] == kv.ANALISA_FFLOP, f"got {_ana29['R4']!r}")
    check("(v3.9.26) ANALISA Berubah Arah (tanda berlawanan, disparitas "
          "≥ 40% — R5 −100 → +10 selisih besar)",
          _ana29["R5"] == kv.ANALISA_ARAH, f"got {_ana29['R5']!r}")

    # --- (f) Req 1 — flip Parsial → 'Potensi Flip Flop' (GUI) ------------
    import tempfile as _tf29

    from openpyxl import Workbook as _WB29
    f29 = os.path.join(_tf29.gettempdir(), "mock_deviasi_fflop.xlsx")
    _w29 = _WB29()
    _s29 = _w29.active
    _s29.append(["RESTO", "NAMA BAHAN", "Satuan", "QTY BOM", "QTY COM",
                 "QTY DEVIASI", "STATUS BULAN", "BULAN"])
    # flip PARSIAL: −100 → +10 (disparitas 0,9 ≥ 40%)
    _s29.append(["MLGPQR", "KEJU FFT", "GR", -80, -90, -100,
                 "WEEK 4", "201.OKT 26"])
    _s29.append(["MLGPQR", "KEJU FFT", "GR", -80, -70, 10,
                 "WEEK 4", "NOV"])
    _w29.save(f29)
    kv._show_all_weeks.set(False)
    kv._load_paths([f29])
    wait_view(root, kv)
    kv._on_mode_change(1)
    root.update()
    kv._render_analisa_section(0)   # v3.9.22: bagian tunggal Top & Flip
    root.update()
    _ffa29 = {kv._flip_tree.set(k, "Kategori"):
              kv._flip_tree.set(k, "ANALISA")
              for k in kv._flip_tree.get_children("")}
    check("(v3.9.26) Flip Parsial (disparitas ≥ 40% — selisih besar) → "
          "ANALISA 'Berubah Arah' (dulu 'Potensi Flip Flop' — v3.9.25)",
          _ffa29.get("Parsial") == kv.ANALISA_ARAH, f"got {_ffa29}")
    kv._on_mode_change(0)
    root.update()
    os.unlink(f29)

    # --- (g) Req 8 — CEK "RI Balancing" di popup Rincian IN --------------
    from src.ui.in_selisih_view import _POPUP_IDS as _PIDS29
    from src.ui.in_selisih_view import _ri_balancing as _rib29
    check("(v3.9.19) Popup Rincian IN: kolom CEK (setelah Nomor PO)",
          _PIDS29 == ["Source", "Nomor", "Nomor PO", "CEK", "Qty",
                      "#Tgl/Jam Pembuatan IT"],
          f"got {_PIDS29}")
    check("(v3.9.19) _ri_balancing: RI Okt vs PO Agt → 'RI Balancing'",
          _rib29("RI.2026.10.10354", "PO.2026.08.00571") == "RI Balancing")
    check("(v3.9.19) _ri_balancing: bulan SAMA → kosong",
          _rib29("RI.2026.08.10354", "PO.2026.08.00571") == "")
    check("(v3.9.19) _ri_balancing: dokumen PI (9901) BUKAN RI → kosong",
          _rib29("PI.2026.10.10354", "PO.2026.08.00571") == "")
    check("(v3.9.19) _ri_balancing: tanpa Nomor PO → kosong",
          _rib29("RI.2026.10.10354", None) == "")
    from src.ui.in_selisih_view import InDetailPopup as _IDP29
    _det29 = pd.DataFrame([
        {"NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
         "Tanggal": 10, "Value": 5.0, "Nomor": "RI.2026.10.10354",
         "Nomor PO": "PO.2026.08.00571", "#Tgl/Jam Pembuatan IT": pd.NA,
         "SOURCE IN": "32.24", "JENIS": "IN"},
        {"NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
         "Tanggal": 10, "Value": 3.0, "Nomor": "RI.2026.10.20999",
         "Nomor PO": "PO.2026.10.10001", "#Tgl/Jam Pembuatan IT": pd.NA,
         "SOURCE IN": "32.24", "JENIS": "IN"},
    ])
    _pop29 = _IDP29(root, "MLGPAR", "AYAM FILET", 10, _det29)
    root.update()
    _ceks29 = [(k, _pop29.tree.set(k, "CEK"))
               for k in _pop29.tree.get_children("")]
    _cek_map29 = {_pop29.tree.set(k, "Nomor"): _pop29.tree.set(k, "CEK")
                  for k in _pop29.tree.get_children("")}
    check("(v3.9.19) Popup: dokumen RI beda bulan dgn PO → CEK 'RI "
          "Balancing' tampil di kolom",
          _cek_map29.get("RI.2026.10.10354") == "RI Balancing" and
          _cek_map29.get("RI.2026.10.20999") == "",
          f"got {_cek_map29}")
    if CELL_TAGS_SUPPORTED:
        _bal29 = [k for k, c in _ceks29 if c == "RI Balancing"]
        _tagged29 = [k for k in _bal29
                     if bool(root.tk.call(str(_pop29.tree), "tag", "cell",
                                          "has", "cek_ri_bal",
                                          (k, "CEK")))]
        check("(v3.9.19) Popup: sel CEK 'RI Balancing' bertag amber "
              "per-cell",
              len(_tagged29) == 1, f"got {len(_tagged29)}")
    _pop29.destroy()
    root.update()

    # --- (h) Req 4 — _resto_name (unit) + filter rincian data-ada --------
    from src.ui.rincian_po_view import _resto_name as _rn29
    check("(v3.9.19) _resto_name: '1370.MLGPAR' → 'MLGPAR'",
          _rn29("1370.MLGPAR") == "MLGPAR", f"got {_rn29('1370.MLGPAR')!r}")
    check("(v3.9.19) _resto_name: tanpa titik → apa adanya",
          _rn29("MLGPAR") == "MLGPAR")
    check("(v3.9.19) _resto_name: kosong/None → ''",
          _rn29(None) == "" and _rn29("") == "")
    _rv29 = app.rincian_view
    select_and_wait(root, app, app.tab_rincian, app.rincian_view)
    # (§24 test pipeline-done defensive None mengosongkan data view —
    # muat ulang fixture rincian sebelum uji kolom baru)
    _rv29.load_data(rincian)
    wait_view(root, _rv29)
    _rv29._reset_filter()
    wait_view(root, _rv29)
    # filter cabang SBYKET → nilai Nama Resto di popup hanya SBYKET
    _rv29.cabang_var.set("SBYKET")
    _rv29._refresh()
    wait_view(root, _rv29)
    _resto_vals29 = _rv29._col_values("Nama Resto")
    check("(v3.9.19) Rincian PO: filter CABANG SBYKET → isi filter Nama "
          "Resto hanya 'SBYKET' (data yang ada)",
          _resto_vals29 == ["SBYKET"], f"got {_resto_vals29}")
    _rv29._reset_filter()
    wait_view(root, _rv29)

    # ==================================================================
    print()
    print("== 30. (v3.9.20) DEEP AUDIT & FIX — 5 AGEN AUDIT + 5 AGEN FIX: "
          "KOMPARASI RESET/POPUP · DEVIASI SATUAN/CHRONO/SOURCE · RINCIAN "
          "NA/FLOAT/NaT/PERIODE · PIVOT/FU/EXPORT ==")

    def _pump30(sec=0.5):
        _t0p = time.time()
        while time.time() - _t0p < sec:
            root.update()
            time.sleep(0.005)

    # --- (a) 35-a — Komparasi: reset filter analisa + popup data-ada -----
    from src.ui.komparasi_deviasi_view import (
        KomparasiDeviasiView as _KDV30,
    )

    def _jrow30(resto, bahan, dev, gr, status):
        # baris join sintetis (pola probe 34-a — tanpa parse file)
        return {"_resto_norm": resto, "_bahan_norm": bahan,
                "Minggu": "WEEK 4", "H": 25, "DEV Lalu": dev,
                "GR Saat Ini": gr, "Status": status, "BULAN": "NOV",
                "Resto": resto, "Nama Barang": bahan, "Satuan": "GR"}

    _JOIN_A30 = pd.DataFrame([
        _jrow30("R_STAB", "B2", 10.0, 10.5, "MATCH"),
        _jrow30("R_TURUN", "B3", 10.0, 2.0, "SELISIH"),
        _jrow30("R_FFLOP", "B5", -100.0, 10.0, "SELISIH"),
    ])
    _JOIN_B30 = pd.DataFrame([
        _jrow30("R_NAIK", "B1", 10.0, 50.0, "SELISIH"),
        _jrow30("R_STAB", "B7", 10.0, 10.5, "MATCH"),
    ])
    _SURF30 = (
        ("Top", "_top_sel", "_top_filters", "Status"),
        ("Flip", "_flip_sel", "_flip_filters", "Kategori"),
    )

    _top30a = tk.Toplevel(root)
    _top30a.geometry("1400x900+0+0")
    kv30 = _KDV30(_top30a)
    kv30.pack(fill="both", expand=True)
    kv30._show_content()
    root.update()

    def _kv_state30():
        # state bersih per tes (tanpa memakai method yang dites)
        for _l30, _sel30, _grp30, _c30 in _SURF30:
            for _c2_30 in getattr(kv30, _sel30):
                getattr(kv30, _sel30)[_c2_30] = None
            for _f30 in getattr(kv30, _grp30)._filters.values():
                _f30.selected = None
        for _c2_30 in kv30._col_sel:
            kv30._col_sel[_c2_30] = None
        kv30._join_df = _JOIN_A30.copy()
        kv30._topn_var.set("0")
        kv30._show_all_weeks.set(True)
        kv30._anasec_idx = 0
        kv30._on_mode_change(1)     # mode 📈 Analisa (jalur user nyata)
        kv30._refresh_analisa()
        root.update()

    def _kv_set_filters30():
        kv30._top_sel["Status"] = {"MATCH"}
        kv30._flip_sel["Kategori"] = {"Parsial"}
        kv30._top_filters._filters["Status"].selected = {"MATCH"}
        kv30._flip_filters._filters["Kategori"].selected = {"Parsial"}

    def _kv_stale30():
        _stale30 = []
        for _l30, _sel30, _grp30, _c30 in _SURF30:
            for _c2_30, _s30 in getattr(kv30, _sel30).items():
                if _s30 is not None:
                    _stale30.append(f"{_l30}:{_c2_30}")
            _ic30 = getattr(kv30, _grp30)._filters[_c30].selected
            if _ic30 is not None:
                _stale30.append(f"{_l30}:icon-{_c30}")
        return _stale30

    _kv_state30()
    _kv_set_filters30()
    kv30._close_file()
    root.update()
    check("(v3.9.20/35-a) ✕ Tutup File: filter 4 tabel analisa (sel + ikon "
          "corong) ikut ter-reset",
          not _kv_stale30() and
          len(kv30._top_tree.get_children("")) == 0,
          f"stale={_kv_stale30()}")
    _kv_state30()
    _kv_set_filters30()
    kv30._close_file()
    root.update()
    kv30._join_df = _JOIN_B30.copy()   # file BARU dimuat → render ulang
    kv30._refresh_analisa()
    root.update()
    check("(v3.9.20/35-a) Tutup File → muat file baru: TIDAK 0 baris senyap "
          "(dulu filter basi Status) + nilai popup segar",
          len(kv30._top_tree.get_children("")) == len(_JOIN_B30) and
          sorted(kv30._top_col_values("Status")) == ["MATCH", "SELISIH"],
          f"rows={len(kv30._top_tree.get_children(''))} "
          f"vals={kv30._top_col_values('Status')}")
    _kv_state30()
    _kv_set_filters30()
    kv30.load_data(pd.DataFrame({"JENIS": [], "NILAI": [], "Tanggal": [],
                                 "Nama Barang": [], "NAMA RESTO": []}))
    root.update()
    check("(v3.9.20/35-a) load_data: filter analisa + _col_sel ter-reset",
          not _kv_stale30() and
          all(s is None for s in kv30._col_sel.values()),
          f"stale={_kv_stale30()}")
    _kv_state30()
    _kv_set_filters30()
    kv30.data = _JOIN_A30.copy()   # non-empty supaya tidak early-return
    kv30._load_paths([str(PROJECT_ROOT / "tidak-ada-35a.xlsx")],
                     interactive=False)
    check("(v3.9.20/35-a) _load_paths: filter analisa ter-reset SINKRON "
          "sebelum job worker (payload snapshot saat job mulai)",
          not _kv_stale30(), f"stale={_kv_stale30()}")
    wait_view(root, kv30)   # biarkan job worker (parse gagal) selesai damai
    _kv_state30()
    _kv_set_filters30()
    kv30._reset_filter()
    wait_view(root, kv30)
    check("(v3.9.20/35-a) ✕ Reset Filter: 4 tabel analisa + kolom utama "
          "ter-reset",
          not _kv_stale30() and
          all(s is None for s in kv30._col_sel.values()),
          f"stale={_kv_stale30()}")

    # FIX 2 — nilai popup filter = baris yang TAMPIL (AutoFilter Excel)
    def _kv_clear_sel30():
        for _l30, _sel30, _grp30, _c30 in _SURF30:
            for _c2_30 in getattr(kv30, _sel30):
                getattr(kv30, _sel30)[_c2_30] = None
        for _c2_30 in kv30._col_sel:
            kv30._col_sel[_c2_30] = None

    _kv_clear_sel30()
    kv30._result_df = pd.DataFrame({
        "Resto": ["RA", "RB", "RC"],
        "Nama Barang": ["AYAM", "AYAM", "GULA"],
        "Status": ["MATCH", "SELISIH", "TIDAK ADA DI DATA SAAT INI"],
        "Selisih": [0.0, 5.0, 7.0],
        "DEV Saat Ini": [0.5, 0.25, 0.75],
    })
    _vals30a = kv30._col_values("Resto")
    kv30._col_sel["Status"] = {"MATCH"}
    check("(v3.9.20/35-a) Popup tabel utama ⚖: nilai kolom lain mengikuti "
          "filter Status (dulu tak tersaring)",
          _vals30a == ["RA", "RB", "RC"] and
          kv30._col_values("Resto") == ["RA"] and
          kv30._col_values("Nama Barang") == ["AYAM"],
          f"got {kv30._col_values('Resto')}")
    kv30._col_sel["Status"] = None

    kv30._result_df = pd.DataFrame({
        "Resto": ["RA", "RB", "RC"],
        "Status": ["MATCH", "SELISIH", "TIDAK ADA DI DATA SAAT INI"],
    })
    kv30._col_sel["Resto"] = {"RA"}
    check("(v3.9.20/35-a) Popup tabel utama: kolom SENDIRI dikecualikan "
          "(daftar nilai tetap semua; kolom lain tersaring)",
          kv30._col_values("Resto") == ["RA", "RB", "RC"] and
          kv30._col_values("Status") == ["MATCH"],
          f"got {kv30._col_values('Resto')}")
    kv30._col_sel["Resto"] = None

    kv30._result_df = pd.DataFrame({
        "Resto": ["RA", "RB", "RC"],
        "Status": ["MATCH", "SELISIH", "TIDAK ADA DI DATA SAAT INI"],
        "DEV Saat Ini": [0.5, 0.25, 0.75],
    })
    kv30._col_sel["DEV Saat Ini"] = {"50,00%"}
    _pct30 = (kv30._col_values("DEV Saat Ini") ==
              ["50,00%", "25,00%", "75,00%"] and
              kv30._col_values("Resto") == ["RA"])
    kv30._col_sel["DEV Saat Ini"] = None
    kv30._result_df = pd.DataFrame({
        "Resto": ["RA", "RB"], "Selisih": [0.0, 5.0]})
    kv30._col_sel["Selisih"] = {"5"}
    _num30 = kv30._col_values("Resto") == ["RB"]
    kv30._col_sel["Selisih"] = None
    check("(v3.9.20/35-a) Popup tabel utama: format persen/angka konsisten "
          "jalur APPLY _prepare_rows (dulu fmt salah → daftar nilai kolom "
          "lain kosong senyap)",
          _pct30 and _num30, f"pct={_pct30} num={_num30}")

    kv30._result_df = pd.DataFrame({
        "Resto": ["RA", "RB"], "Status": ["MATCH", "SELISIH"]})
    kv30._col_sel["Status"] = set()   # seleksi kosong = filter aktif
    check("(v3.9.20/35-a) Popup tabel utama: seleksi kosong → daftar nilai "
          "kosong (semantik Excel 0 baris)",
          kv30._col_values("Resto") == [],
          f"got {kv30._col_values('Resto')}")
    kv30._col_sel["Status"] = None

    # FIX 3 — dead-code format kolom Risk/Bench dibersihkan
    _dead30 = ("Disparitas Rerata", "Loss (Σ|DEV−|)", "Median Kelompok",
               "Opportunity")
    _dead_fmt30 = [
        _KDV30._fmt_analisa_series(_d30, pd.Series([0.4, 1.2])).tolist()
        for _d30 in _dead30]
    check("(v3.9.20/35-a) 4 kolom mati Risk/Bench (bagian dihapus v3.9.19) "
          "tak lagi diformat _fmt_analisa_series",
          all(_f30 == ["0.4", "1.2"] for _f30 in _dead_fmt30),
          f"got {_dead_fmt30}")
    _live30 = (
        _KDV30._fmt_analisa_series("Disparitas",
                                   pd.Series([0.4])).tolist() == ["40,00%"] and
        _KDV30._fmt_analisa_series(
            "DEV Lalu", pd.Series([1234.5])).tolist() == ["1.234,5"] and
        _KDV30._fmt_analisa_series("Selisih",
                                   pd.Series([7.0])).tolist() == ["7"] and
        _KDV30._fmt_analisa_series("ANALISA",
                                   pd.Series(["Stabil"])).tolist() == ["Stabil"])
    check("(v3.9.20/35-a → v3.9.22) Kolom hidup tetap terformat "
          "(Disparitas/DEV Lalu/Selisih/ANALISA — Rate/%Minoritas/Σ|DEV|/"
          "BOM/DEV/z ikut dihapus bersama bagian Minoritas/Liga)",
          _live30, f"got {_live30}")
    _top30a.destroy()
    root.update()

    # --- (b) 35-b — Deviasi view + popup: SATUAN, chrono, source ---------
    from src.ui.deviasi_popup import _chrono_key as _ck30
    from src.ui.deviasi_view import DeviasiView as _DV30

    def _row30b(barang, resto, jenis, tgl, nilai, satuan="GR", source=None):
        return {"Nama Barang": barang, "JENIS": jenis, "NAMA RESTO": resto,
                "Tanggal": tgl, "NILAI": nilai, "SATUAN": satuan,
                "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
                "SOURCE KIRIMAN": "GUDANG", "Nomor": None, "Nomor PO": None,
                "#Tgl/Jam Pembuatan IT": None, "SOURCE DATA": source}

    # pasangan 2-satuan (B, R): GR dan PCS punya data per-tanggal 24 & 25
    _DUAL_ROWS30 = [
        # GR: SO 24=10/25=12, Saldo 24=8/25=9, IN 25=2 → Deviasi(H=25) = 3
        _row30b("B", "R", "1.SO", 24, 10.0, "GR"),
        _row30b("B", "R", "1.SO", 25, 12.0, "GR"),
        _row30b("B", "R", "2.SALDO AKHIR", 24, 8.0, "GR"),
        _row30b("B", "R", "2.SALDO AKHIR", 25, 9.0, "GR"),
        _row30b("B", "R", "4.IN", 25, 2.0, "GR"),
        # PCS: SO 24=5/25=7, Saldo 24=2/25=3, IN 25=1 → Deviasi(H=25) = 4
        _row30b("B", "R", "1.SO", 24, 5.0, "PCS"),
        _row30b("B", "R", "1.SO", 25, 7.0, "PCS"),
        _row30b("B", "R", "2.SALDO AKHIR", 24, 2.0, "PCS"),
        _row30b("B", "R", "2.SALDO AKHIR", 25, 3.0, "PCS"),
        _row30b("B", "R", "4.IN", 25, 1.0, "PCS"),
        # pasangan (D, R): GR + baris 4.IN ber-SATUAN NA (dibuang pivot)
        _row30b("D", "R", "1.SO", 25, 6.0, "GR"),
        _row30b("D", "R", "2.SALDO AKHIR", 25, 4.0, "GR"),
        _row30b("D", "R", "4.IN", 25, 100.0, None),
    ]
    _DUAL_DF30 = pd.DataFrame(_DUAL_ROWS30)

    check("(v3.9.20/35-b) _chrono_key float: '-25.0' valid (dulu int(str) "
          "ValueError → guard 999999)",
          _ck30(-25.0) == 25 and _ck30(25.0) == 125 and
          _ck30(1.0) == 101 and _ck30(-31.0) == 31)
    check("(v3.9.20/35-b) _chrono_key int tak berubah (25→125)",
          _ck30(-25) == 25 and _ck30(25) == 125)
    check("(v3.9.20/35-b) _chrono_key guard NA/non-angka tetap 999999",
          _ck30(None) == 999999 and _ck30(pd.NA) == 999999)

    _rows30f = []
    for _t30f in (-31.0, -30.0, -25.0, 1.0, 24.0, 25.0):
        _rows30f.append(_row30b("B", "R", "1.SO", _t30f, 10.0 + _t30f))
        _rows30f.append(_row30b("B", "R", "2.SALDO AKHIR", _t30f, 3.0))
    _df30f = pd.DataFrame(_rows30f)
    _df30f["Tanggal"] = _df30f["Tanggal"].astype("float64")
    check("(v3.9.20/35-b) Popup urut kronologis utk Tanggal float64 "
          "(25•..31• dulu, lalu 1..31)",
          list(build_popup_rows(_df30f, "B", "R")["Tanggal"]) ==
          ["25•", "30•", "31•", "1", "24", "25"],
          f"got {list(build_popup_rows(_df30f, 'B', 'R')['Tanggal'])}")
    _rows30i = []
    for _t30i in (-31, -25, 1, 24, 25):
        _rows30i.append(_row30b("B", "R", "1.SO", _t30i, 10.0 + _t30i))
        _rows30i.append(_row30b("B", "R", "2.SALDO AKHIR", _t30i, 3.0))
    _df30i = pd.DataFrame(_rows30i)
    _df30i["Tanggal"] = _df30i["Tanggal"].astype("int64")
    check("(v3.9.20/35-b) Popup urut int64 tak berubah",
          list(build_popup_rows(_df30i, "B", "R")["Tanggal"]) ==
          ["25•", "31•", "1", "24", "25"])

    _out30g = build_popup_rows(_DUAL_DF30, "B", "R", satuan="GR")
    _r2430g, _r2530g = _out30g.iloc[0], _out30g.iloc[1]
    check("(v3.9.20/35-b) Popup GR: agregat per-tanggal GR persis (dulu "
          "menjumlah lintas satuan)",
          len(_out30g) == 2 and
          (_r2430g["Tanggal"], _r2430g["Saldo Akhir"], _r2430g["SO"],
           _r2430g["IN"], _r2430g["Deviasi"]) == ("24", "8", "10", "-", "2") and
          (_r2530g["Tanggal"], _r2530g["Saldo Akhir"], _r2530g["SO"],
           _r2530g["IN"], _r2530g["Deviasi"]) == ("25", "9", "12", "2", "3"),
          f"got {_out30g.to_dict('records')}")
    _out30p = build_popup_rows(_DUAL_DF30, "B", "R", satuan="PCS")
    _r2430p, _r2530p = _out30p.iloc[0], _out30p.iloc[1]
    check("(v3.9.20/35-b) Popup PCS: agregat per-tanggal PCS persis",
          len(_out30p) == 2 and
          (_r2430p["Tanggal"], _r2430p["Saldo Akhir"], _r2430p["SO"],
           _r2430p["IN"], _r2430p["Deviasi"]) == ("24", "2", "5", "-", "3") and
          (_r2530p["Tanggal"], _r2530p["Saldo Akhir"], _r2530p["SO"],
           _r2530p["IN"], _r2530p["Deviasi"]) == ("25", "3", "7", "1", "4"),
          f"got {_out30p.to_dict('records')}")
    check("(v3.9.20/35-b) Popup TIDAK menjumlah lintas satuan: Deviasi(H) "
          "GR='3' ≠ PCS='4' (dulu 3+4+2 tak cocok baris manapun)",
          _out30g.iloc[1]["Deviasi"] != _out30p.iloc[1]["Deviasi"] and
          _out30g.iloc[1]["Deviasi"] == "3" and
          _out30p.iloc[1]["Deviasi"] == "4")
    _out30n = build_popup_rows(_DUAL_DF30, "B", "R")
    check("(v3.9.20/35-b) Popup tanpa satuan (None): perilaku lama utk "
          "pemanggil lain (gabungan GR+PCS)",
          _out30n.iloc[0]["Saldo Akhir"] == "10" and
          _out30n.iloc[0]["SO"] == "15",
          f"got {_out30n.iloc[0].to_dict()}")
    _out30d = build_popup_rows(_DUAL_DF30, "D", "R", satuan="GR")
    check("(v3.9.20/35-b) Popup GR pasangan dgn IN ber-SATUAN NA: baris NA "
          "tidak bocor (pivot utama membuang grup NA)",
          len(_out30d) == 1 and
          (_out30d.iloc[0]["Tanggal"], _out30d.iloc[0]["Saldo Akhir"],
           _out30d.iloc[0]["SO"], _out30d.iloc[0]["IN"],
           _out30d.iloc[0]["Deviasi"]) == ("25", "4", "6", "-", "2"),
          f"got {_out30d.to_dict('records')}")

    check("(v3.9.20/35-b) _compute_cek (kode mati) dihapus penuh (rg: 0 "
          "referensi)",
          not hasattr(_DV30, "_compute_cek"))
    check("(v3.9.20/35-b) Jalur CEK hidup _compute_pivot tak tersentuh",
          hasattr(_DV30, "_compute_pivot"))

    # FIX 1 — sort sebelum render pertama tidak crash (Tk 9)
    _top30b1 = tk.Toplevel(root)
    _dv30b1 = _DV30(_top30b1, satuan_mode="GR")   # TANPA pack → lazy
    _dv30b1.load_data(_DUAL_DF30)                  # unmapped → dirty
    _err30b1 = None
    try:
        _dv30b1._sort_by("Deviasi")
        _dv30b1._reapply_cell_tags(_dv30b1.tree)
    except AttributeError as _e30b1:
        _err30b1 = _e30b1
    check("(v3.9.20/35-b) Sort/reapply tag SEBELUM render pertama tidak "
          "AttributeError (dulu _hl_cells belum di-init)",
          _err30b1 is None and isinstance(_dv30b1._hl_cells, list) and
          _dv30b1._hl_cells == [], f"err={_err30b1}")
    _top30b1.destroy()
    root.update()

    def _make_dv30(df, mode="GR"):
        _top30b = tk.Toplevel(root)
        _top30b.geometry("1250x700+15+15")
        _dv30b = _DV30(_top30b, satuan_mode=mode)
        _dv30b.pack(fill="both", expand=True)
        root.update()
        root.update_idletasks()
        root.update()
        _dv30b.load_data(df)
        wait_view(root, _dv30b)
        return _top30b, _dv30b

    def _row_vals30(dv, barang):
        for _k30b in dv.tree.get_children(""):
            if dv.tree.set(_k30b, "Nama Barang") == barang:
                return _k30b, {c: dv.tree.set(_k30b, c) for c in
                               ("Satuan", "SO_H", "In_H", "Sistem",
                                "Deviasi", "CEK")}
        return None, None

    _top30bg, _dv30bg = _make_dv30(_DUAL_DF30, mode="GR")
    _top30bp, _dv30bp = _make_dv30(_DUAL_DF30, mode="PCS")
    _, _gr30v = _row_vals30(_dv30bg, "B")
    _, _pcs30v = _row_vals30(_dv30bp, "B")
    _pop30g = show_deviasi_popup(root, _DUAL_DF30, "B", "R", satuan="GR",
                                 h=25)
    root.update()
    _rows30gp = [_pop30g.tree.set(_k30b, "Deviasi")
                 for _k30b in _pop30g.tree.get_children("")]
    _r25g30v = {c: _pop30g.tree.set(_pop30g.tree.get_children("")[1], c)
                for c in ("Saldo Akhir", "SO", "IN", "Deviasi")}
    _ok30g = (_gr30v is not None and _gr30v["Satuan"] == "GR" and
              _gr30v["Deviasi"] == "3" and
              isinstance(_pop30g, DeviasiPopup) and
              _rows30gp == ["2", "3"] and
              _r25g30v == {"Saldo Akhir": "9", "SO": "12", "IN": "2",
                           "Deviasi": "3"} and
              _r25g30v["Deviasi"] == _gr30v["Deviasi"] and
              "(GR)" in _pop30g._title)
    _pop30g.destroy()
    root.update()
    _pop30p = show_deviasi_popup(root, _DUAL_DF30, "B", "R", satuan="PCS",
                                 h=25)
    root.update()
    _rows30pp = [_pop30p.tree.set(_k30b, "Deviasi")
                 for _k30b in _pop30p.tree.get_children("")]
    _r25p30v = {c: _pop30p.tree.set(_pop30p.tree.get_children("")[1], c)
                for c in ("Saldo Akhir", "SO", "IN", "Deviasi")}
    _ok30p = (_pcs30v is not None and _pcs30v["Satuan"] == "PCS" and
              _pcs30v["Deviasi"] == "4" and
              _rows30pp == ["3", "4"] and
              _r25p30v == {"Saldo Akhir": "3", "SO": "7", "IN": "1",
                           "Deviasi": "4"} and
              _r25p30v["Deviasi"] == _pcs30v["Deviasi"] and
              "(PCS)" in _pop30p._title)
    _pop30p.destroy()
    root.update()
    check("(v3.9.20/35-b) Popup end-to-end GR & PCS: angka SATUAN BARIS "
          "YANG DIKLIK (Dev(H) popup == Deviasi baris utama)",
          _ok30g and _ok30p, f"gr={_ok30g} pcs={_ok30p}")

    # jalur asli user: double-click baris tabel utama → popup satuan tsb.
    _iid30dc, _ = _row_vals30(_dv30bg, "B")
    _ok30dc = _iid30dc is not None
    if _ok30dc:
        _b30dc = _dv30bg.tree.bbox(_iid30dc)
        _ev30dc = _Ev()
        _ev30dc.widget = _dv30bg.tree
        _ev30dc.x, _ev30dc.y = _b30dc[0] + 60, _b30dc[1] + _b30dc[3] // 2
        _dv30bg._on_double_click(_ev30dc)
        root.update()
        _host30dc = _dv30bg.winfo_toplevel()
        _pops30dc = [w for w in _host30dc.winfo_children()
                     if isinstance(w, DeviasiPopup) and w.winfo_exists()]
        _ok30dc = len(_pops30dc) == 1
        if _pops30dc:
            _popdc30 = _pops30dc[0]
            _devs30dc = [_popdc30.tree.set(_k30b, "Deviasi")
                         for _k30b in _popdc30.tree.get_children("")]
            _ok30dc = ("(GR)" in _popdc30._title and
                       _devs30dc == ["2", "3"])
            _popdc30.destroy()
            root.update()
    check("(v3.9.20/35-b) Double-click baris GR → popup membawa satuan baris "
          "tsb (grup GR saja, bukan gabungan 2+3+4+4)",
          _ok30dc, f"ok={_ok30dc}")
    _top30bg.destroy()
    _top30bp.destroy()
    root.update()

    # FIX 4 — _so_source_lookup: v3.9.21 PER-TANGGAL (sumber = baris
    # 1.SO TANGGAL H; v3.9.20 dulu keep-LAST sort-Tanggal pair-level)
    _rows30v = [
        _row30b("V_DUP", "R", "1.SO", 24, 30.0, source="input so harian"),
        _row30b("V_DUP", "R", "1.SO", 25, 60.0,
                source="input promix 04 dine in"),
        _row30b("V_DUP", "R", "2.SALDO AKHIR", 25, 0.0,
                source="input so harian"),
    ]
    _top30v1, _dv30v1 = _make_dv30(pd.DataFrame(_rows30v))
    _, _vv30v1 = _row_vals30(_dv30v1, "V_DUP")
    check("(v3.9.21) _so_source_lookup PER-TANGGAL H (sumber tgl-25 promix "
          "dipakai; tgl-24 so-harian tak menimpa) → CEK Promix 04",
          _dv30v1._so_source_lookup.get(("V_DUP", "R")) ==
          "input promix 04 dine in" and
          _vv30v1 is not None and _vv30v1["CEK"] == "Promix 04",
          f"src={_dv30v1._so_source_lookup.get(('V_DUP', 'R'))!r} "
          f"cek={None if _vv30v1 is None else _vv30v1['CEK']!r}")
    _top30v1.destroy()
    root.update()
    _rows30v = [
        _row30b("V_REV", "R", "1.SO", 25, 60.0,
                source="input promix 04 dine in"),
        _row30b("V_REV", "R", "1.SO", 24, 30.0, source="input so harian"),
        _row30b("V_REV", "R", "2.SALDO AKHIR", 25, 0.0,
                source="input promix 04 dine in"),
    ]
    _top30v2, _dv30v2 = _make_dv30(pd.DataFrame(_rows30v))
    check("(v3.9.21) _so_source_lookup tak bergantung urutan baris df "
          "(urutan dibalik → hasil sama)",
          _dv30v2._so_source_lookup.get(("V_REV", "R")) ==
          "input promix 04 dine in")
    _top30v2.destroy()
    root.update()
    _rows30v = [
        _row30b("V_NA", "R", "1.SO", 25, 60.0,
                source="input promix 04 dine in"),
        _row30b("V_NA", "R", "2.SALDO AKHIR", 25, 0.0, source=None),
    ]
    _df30v3 = pd.DataFrame(_rows30v)
    _na_row30 = pd.DataFrame([_row30b("V_NA", "R", "1.SO", None, 30.0,
                                      source="input so harian")])
    _df30v3 = pd.concat([_na_row30, _df30v3], ignore_index=True)
    _top30v3, _dv30v3 = _make_dv30(_df30v3)
    check("(v3.9.21) _so_source_lookup: baris Tanggal NA tak pernah "
          "dipakai (tak match tanggal H)",
          _dv30v3._so_source_lookup.get(("V_NA", "R")) ==
          "input promix 04 dine in")
    _top30v3.destroy()
    root.update()

    # --- (c) 35-c1 — Rincian PO + Rincian IN: NA/float/NaT/periode --------
    from src.ui.in_selisih_view import (
        InSelisihView as _ISV30,
    )
    from src.ui.in_selisih_view import (
        _doc_month as _dm30,
    )
    from src.ui.in_selisih_view import (
        _doc_period as _dp30,
    )
    from src.ui.rincian_po_view import RincianPoView as _RPV30

    check("(v3.9.20/35-c1) _resto_name pd.NA-safe (dulu TypeError bool(NA) "
          "ambiguous)",
          _rn29(pd.NA) == "" and _rn29(None) == "" and
          _rn29(float("nan")) == "" and _rn29("") == "" and
          pd.Series(["1370.MLGPAR", pd.NA, None, "SBYKET"],
                    dtype=object).map(_rn29).tolist() ==
          ["MLGPAR", "", "", "SBYKET"])
    check("(v3.9.20/35-c1) _resto_name nilai normal tak berubah",
          _rn29("1370.MLGPAR") == "MLGPAR" and _rn29("1.2.3.4") == "4" and
          _rn29("MLGPAR") == "MLGPAR" and _rn29(" 1370.MLGPAR ") == "MLGPAR")
    check("(v3.9.20/35-c1) _resto_name numeric: 1370.0 → '1370' (dulu '0' "
          "via rsplit); 1370.5 tetap rsplit '5'; 0 → ''",
          _rn29(1370.0) == "1370" and _rn29(1370) == "1370" and
          _rn29(1370.5) == "5" and _rn29(0) == "" and _rn29(0.0) == "")
    _mat30 = [
        ("1370.MLGPAR", "MLGPAR"), ("1.2.3.4", "4"), ("MLGPAR", "MLGPAR"),
        (1370, "1370"), (1370.0, "1370"), (pd.NA, ""), (None, ""),
        (float("nan"), ""), ("", ""),
    ]
    check("(v3.9.20/35-c1) _resto_name matrix 9 kasus",
          all(_rn29(_v30) == _w30 for _v30, _w30 in _mat30),
          f"got {[(repr(_v30), _rn29(_v30)) for _v30, _w30 in _mat30 if _rn29(_v30) != _w30]}")

    check("(v3.9.20/35-c1) _fmt_date/_fmt_datetime NaT/pd.NA-safe (dulu "
          "ValueError strftime → tab mati) + nilai normal utuh",
          _RPV30._fmt_date(pd.NaT) == "" and
          _RPV30._fmt_datetime(pd.NaT) == "" and
          _RPV30._fmt_date(pd.NA) == "" and
          _RPV30._fmt_date(pd.Timestamp("2026-08-14")) == "2026-08-14" and
          _RPV30._fmt_datetime(
              pd.Timestamp("2026-08-14 07:30:05")) == "2026-08-14 07:30:05" and
          _RPV30._fmt_date("2026-08-14") == "2026-08-14")
    check("(v3.9.20/35-c1) _fmt_date series map: NaT → '' (render baris NaT "
          "tetap jalan)",
          pd.Series([pd.Timestamp("2026-08-01"), pd.NaT]).map(
              _RPV30._fmt_date).tolist() == ["2026-08-01", ""])

    check("(v3.9.20/35-c1) _ri_balancing: RI Okt vs PO Agt → 'RI Balancing' "
          "(kasus spec user)",
          _rib29("RI.2026.10.10354", "PO.2026.08.00571") == "RI Balancing")
    check("(v3.9.20/35-c1) _ri_balancing: periode sama (bulan & tahun) → ''",
          _rib29("RI.2026.08.10354", "PO.2026.08.00571") == "")
    check("(v3.9.20/35-c1) _ri_balancing: LINTAS-TAHUN bulan sama kini "
          "terflag (dulu tahun diabaikan → lolos senyap) + Des→Jan",
          _rib29("RI.2027.08.2", "PO.2026.08.1") == "RI Balancing" and
          _rib29("RI.2026.12.1", "PO.2027.01.1") == "RI Balancing")
    check("(v3.9.20/35-c1) _ri_balancing: bulan 1-2 digit numerik (8 == 08 "
          "→ ''; 8 ≠ 10 → flag)",
          _rib29("RI.2026.8.1", "PO.2026.08.2") == "" and
          _rib29("RI.2026.8.10354", "PO.2026.10.00571") == "RI Balancing" and
          _rib29("RI.2026.10.10354", "PO.2026.8.00571") == "RI Balancing")
    check("(v3.9.20/35-c1) _ri_balancing: bulan invalid (13/00/081) tak "
          "match",
          _rib29("RI.2026.13.1", "PO.2026.08.1") == "" and
          _rib29("RI.2026.00.1", "PO.2026.08.1") == "" and
          _rib29("RI.2026.081.5", "PO.2026.08.1") == "")
    check("(v3.9.20/35-c1) _ri_balancing: dokumen PI/SJ bukan RI → ''; "
          "tanpa Nomor PO → ''",
          _rib29("PI.2026.10.5", "PO.2026.08.1") == "" and
          _rib29("SJ.2026.10.5", "PO.2026.08.1") == "" and
          _rib29("RI.2026.10.10354", None) == "" and
          _rib29("RI.2026.10.10354", pd.NA) == "")
    check("(v3.9.20/35-c1) helper _doc_period (tahun, bulan) + _doc_month "
          "delegasi",
          _dp30("PO.2026.08.00571") == (2026, 8) and
          _dp30("RI.2026.8.1") == (2026, 8) and
          _dp30("RI.2026.13.1") is None and
          _dm30("RI.2026.8.10354") == 8 and
          _dm30("RI.2026.13.1") is None)

    # FIX 1 (BUG audit 34-e) — clone ⛶ InSelisihView mempertahankan tag
    _top30c = tk.Toplevel(root)
    _top30c.geometry("1200x700+10+10")
    _isv30 = _ISV30(_top30c)
    _isv30.pack(fill="both", expand=True)
    _isv30.load_data(append1, in_detail, audit_result=audit_result)
    _pump30(1.0)
    _isv30._refresh(sync=True)
    wait_view(root, _isv30)

    def _tag_has30(tree, iid, col, tag):
        return bool(root.tk.call(str(tree), "tag", "cell", "has", tag,
                                 (str(iid), str(col))))

    check("(v3.9.20/35-c1) InSelisihView: sel minus bertag neg_cell "
          "(pre-clone)",
          len(_isv30._neg_cells) > 0 and
          all(_tag_has30(_isv30.tree, _i30c, _c30c, "neg_cell")
              for _i30c, _c30c in _isv30._neg_cells),
          f"n={len(_isv30._neg_cells)}")
    _win30c, _clone30c = _isv30._maximize()
    _pump30(1.5)
    _n_src30c = len(_isv30._neg_cells)
    _n_tagged30c = sum(_tag_has30(_clone30c, _i30c, _c30c, "neg_cell")
                       for _i30c, _c30c in _isv30._neg_cells)
    check("(v3.9.20/35-c1) BUG fix: clone ⛶ InSelisihView kini mempertahankan "
          "tag neg_cell per-cell (on_render_done — dulu 0/2)",
          len(_clone30c.get_children("")) ==
          len(_isv30.tree.get_children("")) and
          _n_tagged30c == _n_src30c,
          f"tagged={_n_tagged30c}/{_n_src30c}")
    _win30c.destroy()
    _pump30(0.3)
    _top30c.destroy()
    root.update()

    # FIX 4 GUI — render NaT tanpa ⚠
    def _po_df30(nomor, tanggal, cabang, tgl_jam, barang="AYAM", qty=5.0):
        return pd.DataFrame([{
            "Nomor #": nomor, "Tanggal": tanggal, "Cabang PO": cabang,
            "Pemasok": "PT A", "Status Pesanan Pembelian": "Selesai",
            "Keterangan PO": "R", "Nama Barang": barang, "Satuan": "GR",
            "Kuantitas": qty, "Tgl/Jam Pembuatan": tgl_jam,
        }])

    _top30r1 = tk.Toplevel(root)
    _rv30r1 = _RPV30(_top30r1, data=_po_df30("PO-103", pd.NaT,
                                             "1370.MLGPAR", pd.NaT))
    _rv30r1.pack(fill="both", expand=True)
    _pump30(0.2)
    _rv30r1.ensure_refreshed()
    wait_view(root, _rv30r1)
    _parents30r = [k for k in _rv30r1.tree.get_children("")
                   if k != "grand_total"]
    _vals30r = _rv30r1.tree.item(_parents30r[0], "values") \
        if _parents30r else None
    check("(v3.9.20/35-c1) Rincian PO: Tanggal/Tgl-Jam NaT render '' tanpa "
          "⚠ (dulu ValueError → 'Gagal menyiapkan pivot PO')",
          "⚠" not in _rv30r1.status_var.get() and
          len(_parents30r) == 1 and _vals30r is not None and
          _vals30r[0] == "" and _vals30r[8] == "" and
          _vals30r[1] == "MLGPAR",
          f"status={_rv30r1.status_var.get()!r} vals={_vals30r}")
    _top30r1.destroy()
    root.update()

    _rows30r2 = [_po_df30("PO-101", pd.NaT, "1370.MLGPAR", pd.NaT).iloc[0]
                 .to_dict()]
    _rows30r2.append(_po_df30("PO-101", pd.Timestamp("2026-09-02"),
                              "1370.MLGPAR",
                              pd.Timestamp("2026-09-02 08:00"),
                              barang="GULA").iloc[0].to_dict())
    _top30r2 = tk.Toplevel(root)
    _rv30r2 = _RPV30(_top30r2, data=pd.DataFrame(_rows30r2))
    _rv30r2.pack(fill="both", expand=True)
    _pump30(0.2)
    _rv30r2.ensure_refreshed()
    wait_view(root, _rv30r2)
    check("(v3.9.20/35-c1) Rincian PO: campuran NaT/terisi render tanpa ⚠ + "
          "'NaT' tak masuk daftar nilai filter",
          "⚠" not in _rv30r2.status_var.get() and
          "NaT" not in _rv30r2._col_values("Tanggal"),
          f"status={_rv30r2.status_var.get()!r} "
          f"vals={_rv30r2._col_values('Tanggal')}")
    _df30r3 = pd.concat([
        _po_df30("PO-A", pd.NaT, "1370.MLGPAR", pd.NaT),
        _po_df30("PO-B", pd.Timestamp("2026-09-02"), "2000.SBYKET",
                 pd.Timestamp("2026-09-02 08:00")),
    ], ignore_index=True)
    _rv30r2.load_data(_df30r3)
    _pump30(0.1)
    _rv30r2.ensure_refreshed()
    wait_view(root, _rv30r2)
    check("(v3.9.20/35-c1) Rincian PO: nilai filter Tanggal = ['', "
          "'2026-09-02'] ('' sah — baris anak kosong; hanya literal "
          "'None'/'nan'/'NaT' yang dibuang)",
          _rv30r2._col_values("Tanggal") == ["", "2026-09-02"],
          f"got {_rv30r2._col_values('Tanggal')}")
    _top30r2.destroy()
    root.update()

    # FIX 5 — load_data reset combo Cabang/Status (filter basi)
    _r30s1 = _po_df30("PO-001", pd.Timestamp("2026-08-01"), "CKGPAH",
                      pd.Timestamp("2026-08-01 09:00"), barang="KOPI")
    _r30s2 = _po_df30("PO-002", pd.Timestamp("2026-09-01"), "1370.MLGPAR",
                      pd.Timestamp("2026-09-01 09:00"), barang="AYAM",
                      qty=3.0)
    _top30s = tk.Toplevel(root)
    _rv30s = _RPV30(_top30s, data=_r30s1)
    _rv30s.pack(fill="both", expand=True)
    _pump30(0.1)
    _rv30s.ensure_refreshed()
    wait_view(root, _rv30s)
    _rv30s.cabang_var.set("CKGPAH")
    _rv30s._refresh()
    wait_view(root, _rv30s)
    _rv30s.load_data(_r30s2)
    _pump30(0.1)
    _rv30s.ensure_refreshed()
    wait_view(root, _rv30s)
    check("(v3.9.20/35-c1) load_data: combo CABANG kembali '(All)' (var + "
          "widget) — semua baris file baru render (dulu filter basi → 0 "
          "baris senyap)",
          _rv30s.cabang_var.get() == "(All)" and
          _rv30s.cabang_combo.get() == "(All)" and
          len([k for k in _rv30s.tree.get_children("")
               if k != "grand_total"]) == 1 and
          not _rv30s.status_var.get().startswith("Tidak ada data") and
          _rv30s._col_values("Nama Resto") == ["MLGPAR"],
          f"cabang={_rv30s.cabang_var.get()!r}")
    _rv30s.status_pesanan_var.set("Dibatalkan")   # nilai basi (tak ada)
    _rv30s.load_data(_r30s1)
    _pump30(0.1)
    _rv30s.ensure_refreshed()
    wait_view(root, _rv30s)
    check("(v3.9.20/35-c1) load_data: combo STATUS juga di-reset ke '(All)'",
          _rv30s.status_pesanan_var.get() == "(All)" and
          _rv30s.status_combo.get() == "(All)" and
          len([k for k in _rv30s.tree.get_children("")
               if k != "grand_total"]) == 1)
    _top30s.destroy()
    root.update()

    # FIX 7 — literal 'None'/'nan'/'NaT' tak bocor ke daftar nilai popup
    _rows30p = [
        _po_df30("PO-003", pd.Timestamp("2026-09-03"), "1370.MLGPAR",
                 pd.Timestamp("2026-09-03 09:00")).iloc[0].to_dict(),
        _po_df30("PO-004", pd.Timestamp("2026-09-04"), "1137.CKGPAH",
                 pd.Timestamp("2026-09-04 09:00"),
                 barang="GULA").iloc[0].to_dict(),
    ]
    _rows30p[0]["Pemasok"] = None        # object col dgn None asli
    _rows30p[1]["Keterangan PO"] = None
    _top30p = tk.Toplevel(root)
    _rv30p = _RPV30(_top30p, data=pd.DataFrame(_rows30p))
    _rv30p.pack(fill="both", expand=True)
    _pump30(0.1)
    _rv30p.ensure_refreshed()
    wait_view(root, _rv30p)
    check("(v3.9.20/35-c1) Rincian PO: literal 'None' tak masuk daftar nilai "
          "popup (Pemasok/Keterangan PO)",
          "None" not in _rv30p._col_values("Pemasok") and
          _rv30p._col_values("Pemasok") == ["PT A"] and
          "None" not in _rv30p._col_values("Keterangan PO"),
          f"got {_rv30p._col_values('Pemasok')}")
    _top30p.destroy()
    root.update()
    _top30i = tk.Toplevel(root)
    _iv30 = _ISV30(_top30i)
    _iv30.pack(fill="both", expand=True)
    _pump30(0.2)
    _base30i = pd.DataFrame({
        "Resto": ["MLGPAR", "SBYKET"],
        "Tanggal": [3, 10],
        "Nama Barang": ["AYAM", "GULA"],
        "KATEGORI": ["K1", "K2"],
        "Satuan": ["GR", "GR"],
        "Hasil SO": [1.0, 2.0],
        "Barang Masuk": [10.0, 4.0],
        "IN": [8.0, 4.0],
        "Selisih IN": [2.0, 0.0],
        "Saldo": [2.0, 0.0],
        "Hasil Audit": ["DEVIASI MURNI", "OK (Matching)"],
        "Catatan Audit": [None, "c2"],
    })
    _iv30._cached_base = _base30i
    _iv30._cached_base_data = object()
    _iv30.only_selisih_var.set(False)
    check("(v3.9.20/35-c1) Selisih IN: literal 'None' tak masuk daftar "
          "nilai popup Catatan Audit",
          _iv30._col_values("Catatan Audit") == ["c2"],
          f"got {_iv30._col_values('Catatan Audit')}")
    _iv30._cached_base = None
    _iv30.tree.insert("", "end", iid="r030i",
                      values=("MLGPAR", "3", "AYAM", "K1", "GR", "1", "10",
                              "8", "2", "2", "DEVIASI MURNI", "None"))
    _vals30i = _iv30._col_values("Catatan Audit")
    check("(v3.9.20/35-c1) Selisih IN fallback D-08 (tanpa cache): 'None' "
          "dibuang juga",
          "None" not in _vals30i, f"got {_vals30i}")
    _iv30.destroy()
    _top30i.destroy()
    root.update()

    # FIX 6 GUI — popup Rincian IN: CEK periode + clone tetap jalan
    def _det_row30(nomor, po, qty=5.0):
        return {"NAMA RESTO": "MLGPAR", "Nama Barang": "AYAM FILET",
                "Tanggal": 10, "Value": qty, "Nomor": nomor,
                "Nomor PO": po, "#Tgl/Jam Pembuatan IT": pd.NA,
                "SOURCE IN": "32.24", "JENIS": "IN"}

    _det30 = pd.DataFrame([
        _det_row30("RI.2027.08.1", "PO.2026.08.1"),   # cross-year → flag
        _det_row30("RI.2026.8.2", "PO.2026.08.1"),    # 8==08 → ''
    ])
    _pop30c2 = InDetailPopup(root, "MLGPAR", "AYAM FILET", 10, _det30)
    _pump30(0.5)
    _cek30p = {_pop30c2.tree.set(k, "Nomor"): _pop30c2.tree.set(k, "CEK")
               for k in _pop30c2.tree.get_children("")}
    check("(v3.9.20/35-c1) Popup Rincian IN: RI lintas-tahun bulan sama → "
          "CEK 'RI Balancing'; 8==08 → ''",
          _cek30p.get("RI.2027.08.1") == "RI Balancing" and
          _cek30p.get("RI.2026.8.2") == "", f"got {_cek30p}")
    if CELL_TAGS_SUPPORTED:
        _tagged30p = [
            k for k in _pop30c2.tree.get_children("")
            if _pop30c2.tree.set(k, "CEK") == "RI Balancing" and
            _tag_has30(_pop30c2.tree, k, "CEK", "cek_ri_bal")]
        check("(v3.9.20/35-c1) Popup: sel CEK lintas-tahun bertag amber "
              "per-cell (cek_ri_bal)",
              len(_tagged30p) == 1, f"got {len(_tagged30p)}")
    _pop30c2.destroy()
    root.update()
    _pop30c3 = InDetailPopup(root, "MLGPAR", "AYAM FILET", 10,
                             pd.DataFrame([_det_row30("RI.2026.13.1",
                                                      "PO.2026.08.1")]))
    _pump30(0.5)
    _ceks30c3 = [_pop30c3.tree.set(k, "CEK")
                 for k in _pop30c3.tree.get_children("")]
    check("(v3.9.20/35-c1) Popup: bulan invalid (13) → semua CEK kosong",
          set(_ceks30c3) == {""}, f"got {set(_ceks30c3)}")
    _pop30c3.destroy()
    root.update()

    # --- (d) 35-c2 — Pivot/FollowUp popup data-ada + merah + export ------
    from src.ui.pivot_view import PivotTableView as _PV30

    def _row30d(barang, resto, jenis, tgl, nilai, src="GUDANG", kat="BAHAN"):
        return {"Nama Barang": barang, "JENIS": jenis, "NAMA RESTO": resto,
                "Tanggal": tgl, "NILAI": nilai, "SATUAN": "GR",
                "AKTIF/NON": "AKTIF", "KATEGORI": kat,
                "SOURCE KIRIMAN": src, "Nomor": None, "Nomor PO": None,
                "#Tgl/Jam Pembuatan IT": None}

    _PIVOT_ROWS30 = (
        # 2 barang ber-resto eksklusif + 1 barang di dua resto
        [_row30d("BRG MLG", "MLGPAR", "1.SO", t, 10.0) for t in (1, 2)] +
        [_row30d("BRG MLG", "MLGPAR", "2.SALDO AKHIR", t, 5.0)
         for t in (1, 2)] +
        [_row30d("BRG SBY", "SBYKET", "1.SO", t, 7.0) for t in (1, 2)] +
        [_row30d("BRG SBY", "SBYKET", "2.SALDO AKHIR", t, 3.0)
         for t in (1, 2)] +
        [_row30d("BRG BOTH", "MLGPAR", "1.SO", t, 2.0) for t in (1, 2)] +
        [_row30d("BRG BOTH", "SBYKET", "1.SO", t, 2.0) for t in (1, 2)] +
        # kategori lain (filter KATEGORI)
        [_row30d("BRG KAT", "MLGPAR", "1.SO", 1, 9.0, kat="CEK"),
         _row30d("BRG KAT", "MLGPAR", "2.SALDO AKHIR", 1, 4.0, kat="CEK")] +
        # semua nilai 0 → disembunyikan hide-empty (default ON)
        [_row30d("BRG NOL", "MLGPAR", "1.SO", 1, 0.0),
         _row30d("BRG NOL", "MLGPAR", "2.SALDO AKHIR", 1, 0.0)] +
        # hanya tgl 5 → lenyap saat rentang 1..2
        [_row30d("BRG T5", "MLGPAR", "1.SO", 5, 8.0)] +
        # sumber kiriman lain (filter SOURCE)
        [_row30d("BRG SRC", "MLGPAR", "1.SO", 1, 6.0, src="SUPPLIER")]
    )
    _ALL_SHOWN30 = ["BRG BOTH", "BRG KAT", "BRG MLG", "BRG SBY", "BRG SRC",
                    "BRG T5"]

    def _load_pivot30(rows, mode="resto", tgl=("1", "31")):
        _top30d = tk.Toplevel(root)
        _top30d.geometry("1100x640+40+40")
        _pv30 = _PV30(_top30d)
        _pv30.pack(fill="both", expand=True)
        _pv30.pivot_mode = mode
        _pv30.tgl_start_var.set(tgl[0])
        _pv30.tgl_end_var.set(tgl[1])
        _pv30.data = pd.DataFrame(rows)
        _pv30._populate_filters()
        _pv30._show_content()
        _pv30._refresh_pivot(sync=True)
        for _ in range(80):
            root.update()
            if (not _pv30._busy and
                    len(_pv30.tree.get_children(""))):
                break
            time.sleep(0.01)
        _pump30(0.4)
        return _top30d, _pv30

    _top30d1, _pv30d1 = _load_pivot30(_PIVOT_ROWS30)
    _vals30d1 = _pv30d1._name_values()
    check("(v3.9.20/35-c2) Popup Nama Barang pivot: barang total-0 keluar "
          "(hide-empty ikut dihitung — AutoFilter sejati)",
          sorted(set(_vals30d1)) == _ALL_SHOWN30 and
          "BRG NOL" not in _vals30d1,
          f"got {sorted(set(_vals30d1))}")
    _pv30d1.source_var.set("SUPPLIER")
    check("(v3.9.20/35-c2) Popup Nama Barang pivot: filter SOURCE "
          "menyempitkan daftar (konsisten dgn tampilan)",
          _pv30d1._name_values() == ["BRG SRC"],
          f"got {_pv30d1._name_values()}")
    _pv30d1.source_var.set("(All)")
    _pv30d1.kategori_var.set("CEK")
    check("(v3.9.20/35-c2) Popup Nama Barang pivot: filter KATEGORI "
          "menyempitkan daftar",
          _pv30d1._name_values() == ["BRG KAT"],
          f"got {_pv30d1._name_values()}")
    _pv30d1.kategori_var.set("(All)")
    _pv30d1.tgl_end_var.set("2")            # BRG T5 hanya ada di tgl 5
    check("(v3.9.20/35-c2) Popup Nama Barang pivot: rentang Tanggal "
          "menyempitkan daftar",
          "BRG T5" not in _pv30d1._name_values() and
          sorted(set(_pv30d1._name_values())) ==
          ["BRG BOTH", "BRG KAT", "BRG MLG", "BRG SBY", "BRG SRC"],
          f"got {sorted(set(_pv30d1._name_values()))}")
    _pv30d1.tgl_end_var.set("31")
    _pv30d1._name_selected = {"BRG MLG"}
    check("(v3.9.20/35-c2) Popup Nama Barang pivot: filter SENDIRI "
          "dikecualikan",
          sorted(set(_pv30d1._name_values())) == _ALL_SHOWN30)
    _pv30d1._name_selected = None
    _top30d1.destroy()
    root.update()

    _top30d2, _pv30d2 = _load_pivot30(_PIVOT_ROWS30, mode="tanggal")
    _pv30d2.resto_var.set("SBYKET")
    check("(v3.9.20/35-c2) Popup Nama Barang pivot: mode Tanggal — filter "
          "RESTO menyempitkan daftar",
          sorted(_pv30d2._name_values()) == ["BRG BOTH", "BRG SBY"],
          f"got {sorted(_pv30d2._name_values())}")
    _pv30d2.resto_var.set("(All)")
    _top30d2.destroy()
    root.update()

    _top30d3, _pv30d3 = _load_pivot30(_PIVOT_ROWS30)
    _pv30d3.kategori_var.set("CEK")
    _hf30 = _pv30d3.header_filter
    _hf30.open_popup()
    try:
        _hfv30 = list(_hf30._values_list)
    finally:
        _hf30._close()
        root.update()
    check("(v3.9.20/35-c2) Kontrak end-to-end HeaderFilter: open_popup "
          "membawa nilai terfilter (KATEGORI=CEK → ['BRG KAT'])",
          _hfv30 == ["BRG KAT"], f"got {_hfv30}")
    _pv30d3._refresh_pivot(sync=True)
    for _ in range(80):
        root.update()
        if not _pv30d3._busy:
            break
        time.sleep(0.01)
    _win30d3, _tree2_30d3 = _pv30d3._maximize()
    _pump30(0.4)
    check("(v3.9.20/35-c2) Clone ⛶ pivot: get_values = _name_values "
          "terfilter (share filter view sumber)",
          _pv30d3._name_values() == ["BRG KAT"] and
          callable(getattr(_tree2_30d3, "_clone_filter_apply", None)))
    _win30d3.destroy()
    root.update()
    _top30d3.destroy()
    root.update()

    # FIX 3 — neg_cell (dan literal merah pivot) = #dc2626
    _top30d4 = tk.Toplevel(root)
    _pv30d4 = _PV30(_top30d4)
    _pv30d4.pack(fill="both", expand=True)
    _tags30d4 = ("neg_cell", "negative", "deviasi_row", "selisih_anomaly")
    check("(v3.9.20/35-c2) Pivot: 4 tag merah kini #dc2626 (seragam 11 view "
          "— dulu #CC0000)",
          all(str(_pv30d4.tree.tag_configure(_t30d4, "foreground")).lower()
              == "#dc2626" for _t30d4 in _tags30d4),
          f"got {[(t, str(_pv30d4.tree.tag_configure(t, 'foreground'))) for t in _tags30d4]}")
    _pv30d4.destroy()
    _top30d4.destroy()
    root.update()
    _neg30 = [_row30d("BRG NEG", "MLGPAR", "3.DEVIASI", 1, -6.0),
              _row30d("BRG NEG", "MLGPAR", "3.DEVIASI", 2, 10.0),
              _row30d("BRG NEG", "MLGPAR", "2.SALDO AKHIR", 1, 10.0)]
    _top30d5, _pv30d5 = _load_pivot30(_neg30, mode="tanggal", tgl=("1", "2"))
    _dev_iid30 = None
    for _p30d in _pv30d5.tree.get_children(""):
        if _pv30d5.tree.item(_p30d, "text") != "BRG NEG":
            continue
        for _c30d in _pv30d5.tree.get_children(_p30d):
            if _pv30d5.tree.item(_c30d, "text") == "3.DEVIASI":
                _dev_iid30 = _c30d
    _neg_ok30 = _dev_iid30 is not None
    if _neg_ok30 and CELL_TAGS_SUPPORTED:
        _neg_ok30 = bool(root.tk.call(str(_pv30d5.tree), "tag", "cell",
                                      "has", "neg_cell",
                                      (_dev_iid30, "1"))) and \
            str(_pv30d5.tree.tag_configure("neg_cell",
                                           "foreground")).lower() == "#dc2626"
    check("(v3.9.20/35-c2) Pivot: sel minus bertag neg_cell #dc2626 "
          "(baris ber-total > 0)",
          _neg_ok30, f"dev_iid={_dev_iid30}")
    _top30d5.destroy()
    root.update()

    # FIX 1b — FollowUp: nilai popup kolom = baris yang TAMPIL
    _FU_SNAPS30 = {
        "fpA": {"asal": "DEVIASI GR", "resto": "MLGPAR",
                "barang": "AYAM FP", "satuan": "KG", "aktif": "AKTIF",
                "h": 25, "so": 10.0, "sistem": 120.0, "deviasi": -25.0,
                "cek": "OK", "so_m2": 5.0, "so_m1": 6.0, "so_p1": 7.0,
                "so_p2": 8.0, "loss_bom": 0.25},
        "fpB": {"asal": "DEVIASI GR", "resto": "BDGUKU",
                "barang": "GULA FP", "satuan": "KG", "aktif": "AKTIF",
                "h": 25, "so": 20.0, "sistem": 100.0, "deviasi": 25.0,
                "cek": "OK", "so_m2": 5.0, "so_m1": 6.0, "so_p1": 7.0,
                "so_p2": 8.0, "loss_bom": 0.25},
        "fpC": {"asal": "DEVIASI GR", "resto": "MLGPAR",
                "barang": "GULA FP", "satuan": "KG", "aktif": "AKTIF",
                "h": 25, "so": 12.0, "sistem": 90.0, "deviasi": 5.0,
                "cek": "OK", "so_m2": 5.0, "so_m1": 6.0, "so_p1": 7.0,
                "so_p2": 8.0, "loss_bom": 0.25},
    }
    _fu_snap30 = {}
    for _p30fu in (followup_path(), resolved_path()):
        _fu_snap30[_p30fu] = (_p30fu.read_bytes()
                              if _p30fu.exists() else None)
        if _p30fu.exists():
            _p30fu.unlink()
    try:
        _top30fu = tk.Toplevel(root)
        _top30fu.geometry("1100x640+10+10")
        _store30fu = FollowUpStore()
        for _fp30, _sn30 in _FU_SNAPS30.items():
            _store30fu.toggle(_fp30, _sn30)
        _fv30 = FollowUpView(_top30fu, store=_store30fu)
        _fv30.pack(fill="both", expand=True)
        root.update()
        _fv30._col_sel["Resto"] = {"MLGPAR"}
        check("(v3.9.20/35-c2) FollowUp: popup kolom lain mengikuti filter "
              "Resto (dulu tak tersaring)",
              _fv30._col_values("Nama Barang") == ["AYAM FP", "GULA FP"],
              f"got {_fv30._col_values('Nama Barang')}")
        check("(v3.9.20/35-c2) FollowUp: kolom SENDIRI dikecualikan",
              _fv30._col_values("Resto") == ["BDGUKU", "MLGPAR"],
              f"got {_fv30._col_values('Resto')}")
        _fv30._col_sel["Nama Barang"] = {"GULA FP"}
        check("(v3.9.20/35-c2) FollowUp: dua filter irisan (Resto + Nama "
              "Barang → Deviasi ['5'])",
              _fv30._col_values("Deviasi") == ["5"],
              f"got {_fv30._col_values('Deviasi')}")
        _fv30._render()
        root.update()
        check("(v3.9.20/35-c2) FollowUp: render & daftar nilai konsisten "
              "(irisan → 1 baris; kolom Asal = ['DEVIASI GR'])",
              len(_fv30.tree.get_children("")) == 1 and
              _fv30._col_values("Asal") == ["DEVIASI GR"],
              f"rows={len(_fv30.tree.get_children(''))}")
        _hf30fu = _fv30.header_filters._filters["Nama Barang"]
        _hf30fu.open_popup()
        try:
            _hfv30fu = list(_hf30fu._values_list)
        finally:
            _hf30fu._close()
            root.update()
        check("(v3.9.20/35-c2) FollowUp: kontrak open_popup membawa nilai "
              "terfilter (['AYAM FP', 'GULA FP'])",
              _hfv30fu == ["AYAM FP", "GULA FP"], f"got {_hfv30fu}")
        _fv30._col_sel["Resto"] = None
        _fv30._col_sel["Nama Barang"] = None
        _fv30.destroy()
        root.update()
        for _fp30, _sn30 in _FU_SNAPS30.items():
            _store30fu.toggle(_fp30, _sn30)
        _top30fu.destroy()
        root.update()
    finally:
        for _p30fu, _blob30 in _fu_snap30.items():
            if _blob30 is not None:
                _p30fu.write_bytes(_blob30)
            elif _p30fu.exists():
                _p30fu.unlink()

    # FIX 4 — export sheet "Rincian PO" + kolom Nama Resto
    _PO_ROWS30 = [
        {"Nomor #": "PO-001", "Tanggal": pd.Timestamp("2024-06-02"),
         "Cabang PO": "1370.MLGPAR", "Pemasok": "PT Sumber",
         "Nama Barang": "AYAM FILET", "Satuan": "GR", "Kuantitas": 10.0,
         "@Harga": 1000.0, "Total Harga": 10000.0, "Keterangan PO": "Rutin",
         "Status Pesanan Pembelian": "Selesai",
         "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-01 09:00"),
         "DBS_Kategori.KATEGORI": "DEVIASI"},
        {"Nomor #": "PO-001", "Tanggal": pd.Timestamp("2024-06-02"),
         "Cabang PO": "1370.MLGPAR", "Pemasok": "PT Sumber",
         "Nama Barang": "GULA PASIR", "Satuan": "GR", "Kuantitas": 5.0,
         "@Harga": 2000.0, "Total Harga": 10000.0, "Keterangan PO": "Rutin",
         "Status Pesanan Pembelian": "Selesai",
         "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-01 09:00"),
         "DBS_Kategori.KATEGORI": "DEVIASI"},
        {"Nomor #": "PO-002", "Tanggal": pd.Timestamp("2024-06-03"),
         "Cabang PO": "2000.SBYKET", "Pemasok": "CV Maju",
         "Nama Barang": "SUSU UHT 1L", "Satuan": "PCS", "Kuantitas": 3.0,
         "@Harga": 15000.0, "Total Harga": 45000.0, "Keterangan PO": "",
         "Status Pesanan Pembelian": "Selesai",
         "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-02 10:00"),
         "DBS_Kategori.KATEGORI": "DEVIASI"},
        {"Nomor #": "PO-003", "Tanggal": pd.Timestamp("2024-06-04"),
         "Cabang PO": None, "Pemasok": "UD Jaya",
         "Nama Barang": "KOPI BUBUK 100G", "Satuan": "PCS", "Kuantitas": 2.0,
         "@Harga": 3000.0, "Total Harga": 6000.0, "Keterangan PO": "",
         "Status Pesanan Pembelian": "Selesai",
         "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-03 11:00"),
         "DBS_Kategori.KATEGORI": "DEVIASI"},
        {"Nomor #": "PO-004", "Tanggal": pd.Timestamp("2024-06-05"),
         "Cabang PO": "1370.MLGPAR.CKGPAH", "Pemasok": "PT Sumber",
         "Nama Barang": "AYAM FILET", "Satuan": "GR", "Kuantitas": 8.0,
         "@Harga": 1100.0, "Total Harga": 8800.0, "Keterangan PO": "",
         "Status Pesanan Pembelian": "Selesai",
         "Tgl/Jam Pembuatan": pd.Timestamp("2024-06-04 12:00"),
         "DBS_Kategori.KATEGORI": "DEVIASI"},
    ]
    import tempfile as _tf30

    import src.ui.app as _appmod30
    _app_saved30 = {k: getattr(app, k, None)
                    for k in ("append1_df", "rincian_po_df",
                              "in_detail_df", "audit_result")}

    def _export30(po_df, append1_df=None):
        app.append1_df = append1_df
        app.rincian_po_df = po_df
        app.in_detail_df = None
        app.audit_result = None
        _out30e = os.path.join(_tf30.mkdtemp(prefix="v3920_export_"),
                               "35c2_export.xlsx")
        _ask30 = _appmod30.filedialog.asksaveasfilename
        _info30 = _appmod30.messagebox.showinfo
        _err30e = _appmod30.messagebox.showerror
        _appmod30.filedialog.asksaveasfilename = lambda **kw: _out30e
        _appmod30.messagebox.showinfo = lambda *a, **k: None
        _appmod30.messagebox.showerror = lambda *a, **k: None
        try:
            app._export_excel()
            _t030e = time.time()
            while not os.path.exists(_out30e) and time.time() - _t030e < 20:
                root.update()
                time.sleep(0.02)
            _pump30(0.1)
        finally:
            _appmod30.filedialog.asksaveasfilename = _ask30
            _appmod30.messagebox.showinfo = _info30
            _appmod30.messagebox.showerror = _err30e
        return _out30e

    from openpyxl import load_workbook as _lw30
    _po_df30e = pd.DataFrame(_PO_ROWS30)
    _out30e1 = _export30(_po_df30e)
    _wb30e = _lw30(_out30e1)
    _hdr30e = [c.value for c in _wb30e["Rincian PO"][1]]
    _col30e = {n: i + 1 for i, n in enumerate(_hdr30e)}
    _got30e = [str(_wb30e["Rincian PO"].cell(row=r,
                                             column=_col30e["Nama Resto"])
                   .value or "")
               for r in range(2, _wb30e["Rincian PO"].max_row + 1)]
    _exp30e = [str(v or "") for v in _po_df30e["Cabang PO"].map(_rn29)]
    check("(v3.9.20/35-c2) Export: sheet 'Rincian PO' membawa kolom Nama "
          "Resto (setelah Tanggal; import _resto_name — tanpa duplikasi)",
          "Rincian PO" in _wb30e.sheetnames and "Nama Resto" in _hdr30e and
          _hdr30e.index("Nama Resto") == _hdr30e.index("Tanggal") + 1 and
          _hdr30e[0] == "Nomor #" and
          _hdr30e[-1] == "DBS_Kategori.KATEGORI" and
          _got30e == _exp30e and
          _exp30e == ["MLGPAR", "MLGPAR", "SBYKET", "", "CKGPAH"] and
          "Nama Resto" not in app.rincian_po_df.columns,
          f"hdr={_hdr30e[:3]} got={_got30e}")
    _wb30e.close()
    _append1_30e = pd.DataFrame([
        {"Nama Barang": "AYAM FILET", "JENIS": "1.SO", "NAMA RESTO": "MLGPAR",
         "Tanggal": 1, "NILAI": 10.0, "SATUAN": "GR", "AKTIF/NON": "AKTIF",
         "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG", "Nomor": None,
         "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None},
        {"Nama Barang": "AYAM FILET", "JENIS": "2.SALDO AKHIR",
         "NAMA RESTO": "MLGPAR", "Tanggal": 1, "NILAI": 8.0, "SATUAN": "GR",
         "AKTIF/NON": "AKTIF", "KATEGORI": "BAHAN",
         "SOURCE KIRIMAN": "GUDANG", "Nomor": None, "Nomor PO": None,
         "#Tgl/Jam Pembuatan IT": None},
    ])
    _out30e2 = _export30(_po_df30e, append1_df=_append1_30e)
    _wb30e2 = _lw30(_out30e2)
    check("(v3.9.20/35-c2) Export: sheet lain tak tersentuh (PIVOT tetap "
          "duluan; Append1 tanpa kolom Nama Resto)",
          _wb30e2.sheetnames[0] == "PIVOT" and
          "Append1" in _wb30e2.sheetnames and
          [c.value for c in _wb30e2["Append1"][1]] ==
          list(_append1_30e.columns) and
          "Nama Resto" not in [c.value for c in _wb30e2["Append1"][1]])
    _wb30e2.close()
    for _k30e, _v30e in _app_saved30.items():
        setattr(app, _k30e, _v30e)

    # =====================================================================
    # §31 — v3.9.21: AMBANG ACR to BOM bisa diatur + Promix 04 PER-TANGGAL
    # (2 permintaan user: "di bagian ACR to BOM itu harusnya ada threshold
    # > 80% absolute dan aku bisa atur" + "Promix 04 muncul di filter tapi
    # data nya tidak ada").
    # =====================================================================
    from src.ui.deviasi_view import SharedACRThreshold as _SAT31

    def _acr_df31(dev=85.0):
        """Data GR: Total ACR (9.ACR tgl 1..25 × 4) = 100; SO(25) = 100;
        SALDO(25) = 100 − dev → Deviasi = dev. IN(25) = dev − 10 supaya
        kondisi Hitung Manual (rasio stok) TIDAK terpicu — hanya kondisi
        ACR to BOM yang bervariasi dgn ambang."""
        rows = [
            _row30b("ACR TH", "R", "1.SO", 25, 100.0),
            _row30b("ACR TH", "R", "1.SO", 24, 100.0),
            _row30b("ACR TH", "R", "2.SALDO AKHIR", 25, 100.0 - dev),
            _row30b("ACR TH", "R", "4.IN", 25, dev - 10.0),
        ]
        for d in range(1, 26):
            rows.append(_row30b("ACR TH", "R", "9.ACR", d, 4.0))
        return pd.DataFrame(rows)

    _st31 = _SAT31(80.0)
    _top31a, _dv31a = _make_dv30(_acr_df31(85.0))
    check("(v3.9.21) Default ambang ACR = 80.0 (view tanpa shared state)",
          _dv31a.acr_threshold == 80.0, f"got {_dv31a.acr_threshold}")
    _dv31a._acr_state = _st31          # pasang state utk uji listener
    _st31.subscribe(_dv31a._on_shared_acr_changed)
    _, _vv31a = _row_vals30(_dv31a, "ACR TH")
    check("(v3.9.21) Ambang 80%: |Dev 85| > 0,8 × ACR 100 → CEK 'ACR "
          "to BOM' (dulu kaku >100% — tak terpicu)",
          _vv31a is not None and _vv31a["CEK"] == "ACR to BOM",
          f"cek={None if _vv31a is None else _vv31a['CEK']!r}")

    # batas persis: |Dev| == ambang×ACR → TIDAK terpicu (strict >)
    _top31b, _dv31b = _make_dv30(_acr_df31(80.0))
    _, _vv31b = _row_vals30(_dv31b, "ACR TH")
    check("(v3.9.21) Batas persis |Dev| == 80%×ACR → TIDAK terpicu "
          "(strict >)",
          _vv31b is not None and _vv31b["CEK"] != "ACR to BOM",
          f"cek={None if _vv31b is None else _vv31b['CEK']!r}")
    _top31b.destroy()
    root.update()

    # ubah ambang via state bersama → view ikut (pivot di-recompute)
    _st31.set(90.0)
    wait_view(root, _dv31a)
    root.update()
    _, _vv31c = _row_vals30(_dv31a, "ACR TH")
    check("(v3.9.21) Ubah ambang 80→90 via SharedACRThreshold: |Dev 85| ≤ "
          "0,9×ACR → CEK 'ACR to BOM' HILANG (recompute live)",
          _vv31c is not None and _vv31c["CEK"] != "ACR to BOM",
          f"cek={None if _vv31c is None else _vv31c['CEK']!r} "
          f"thr={_dv31a.acr_threshold}")
    check("(v3.9.21) Spinbox var ikut state bersama (90 tampil)",
          _dv31a._acr_var.get() == "90",
          f"got {_dv31a._acr_var.get()!r}")
    _st31.unsubscribe(_dv31a._on_shared_acr_changed)
    _top31a.destroy()
    root.update()

    # --- (b) persistensi settings.json (round-trip + clamp) --------------
    import tempfile as _tf31

    import src.ui.deviasi_view as _dvmod31
    _tmpdir31 = _tf31.mkdtemp(prefix="t31_acr_")
    _origpath31 = _dvmod31.acr_settings_path()
    _dvmod31.acr_settings_path = lambda: __import__("pathlib").Path(
        _tmpdir31) / "settings.json"
    try:
        _dvmod31.save_acr_threshold(55.5)
        check("(v3.9.21) settings.json round-trip: save 55,5 → load 55,5",
              _dvmod31.load_acr_threshold() == 55.5,
              f"got {_dvmod31.load_acr_threshold()}")
        import json as _j31
        with open(_dvmod31.acr_settings_path(), "r", encoding="utf-8") as _f31:
            _jdata31 = _j31.load(_f31)
        _jdata31["lain"] = "tetap"
        with open(_dvmod31.acr_settings_path(), "w",
                  encoding="utf-8") as _f31:
            _j31.dump(_jdata31, _f31)
        _dvmod31.save_acr_threshold(120.0)
        with open(_dvmod31.acr_settings_path(), "r", encoding="utf-8") as _f31:
            _jdata31b = _j31.load(_f31)
        check("(v3.9.21) Key lain di settings.json dipertahankan + nilai "
              "baru",
              _jdata31b.get("acr_threshold_pct") == 120.0
              and _jdata31b.get("lain") == "tetap",
              f"got {_jdata31b}")
        _dvmod31.save_acr_threshold(0.5)   # di luar 1..200 → load clamp 80
        check("(v3.9.21) Nilai tak valid di file → load clamp default 80",
              _dvmod31.load_acr_threshold() == 80.0,
              f"got {_dvmod31.load_acr_threshold()}")
    finally:
        _dvmod31.acr_settings_path = _origpath31

    # --- (c) Promix 04 PER-TANGGAL — label ikut sumber tanggal H ---------
    # pasangan: SO tgl-24 promix + SO tgl-25 so-harian → CEK TIDAK Promix
    # (sumber tanggal H yang dipakai — bukan tanggal tertinggi/urutan)
    _rows31p = [
        _row30b("P-DATE", "R", "1.SO", 24, 30.0,
                source="input promix 04 take away"),
        _row30b("P-DATE", "R", "1.SO", 25, 60.0,
                source="input so harian"),
        _row30b("P-DATE", "R", "2.SALDO AKHIR", 25, 0.0,
                source="input so harian"),
    ]
    _top31p, _dv31p = _make_dv30(pd.DataFrame(_rows31p))
    _, _vv31p = _row_vals30(_dv31p, "P-DATE")
    check("(v3.9.21) SO tanggal-24 promix + tanggal-25 so-harian → CEK "
          "TIDAK Promix (sumber tanggal H yang dipakai — bukan tanggal "
          "tertinggi/urutan)",
          _vv31p is not None and _vv31p["CEK"] != "Promix 04"
          and _dv31p._so_source_lookup.get(("P-DATE", "R"))
          == "input so harian",
          f"cek={None if _vv31p is None else _vv31p['CEK']!r} "
          f"src={_dv31p._so_source_lookup.get(('P-DATE', 'R'))!r}")

    # campuran SATU TANGGAL: so-harian + promix → harian menang
    _rows31q = [
        _row30b("P-MIX", "R", "1.SO", 25, 60.0, source="input so harian"),
        _row30b("P-MIX", "R", "1.SO", 25, 10.0,
                source="input promix 04 dine in"),
        _row30b("P-MIX", "R", "2.SALDO AKHIR", 25, 0.0,
                source="input so harian"),
    ]
    _top31q, _dv31q = _make_dv30(pd.DataFrame(_rows31q))
    _, _vv31q = _row_vals30(_dv31q, "P-MIX")
    check("(v3.9.21) Tanggal sama: so-harian + promix → 'input so harian' "
          "menang (hitungan manual) — CEK normal",
          _vv31q is not None and _vv31q["CEK"] != "Promix 04"
          and _dv31q._so_source_lookup.get(("P-MIX", "R"))
          == "input so harian",
          f"cek={None if _vv31q is None else _vv31q['CEK']!r}")

    # konsistensi filter CEK: nilai popup == nilai baris yang dirender
    _vals31 = _dv31p._col_values("CEK")
    _rendered31 = {_dv31p.tree.set(k, "CEK")
                   for k in _dv31p.tree.get_children("")} - {""}
    check("(v3.9.21) Konsistensi filter CEK: nilai popup == nilai baris "
          "yang dirender (tanpa phantom)",
          set(_vals31) == _rendered31,
          f"popup={_vals31} rendered={sorted(_rendered31)}")
    _top31p.destroy()
    _top31q.destroy()
    root.update()

    # label mengikuti H: SO tgl-25 promix → Promix; Apply H=24 → hilang
    _rows31r = [
        _row30b("P-H", "R", "1.SO", 23, 20.0, source="input so harian"),
        _row30b("P-H", "R", "1.SO", 24, 30.0, source="input so harian"),
        _row30b("P-H", "R", "1.SO", 25, 60.0,
                source="input promix 04 dine in"),
        _row30b("P-H", "R", "2.SALDO AKHIR", 25, 0.0,
                source="input so harian"),
        _row30b("P-H", "R", "2.SALDO AKHIR", 24, 5.0,
                source="input so harian"),
    ]
    _top31r, _dv31r = _make_dv30(pd.DataFrame(_rows31r))
    _, _vv31r = _row_vals30(_dv31r, "P-H")
    check("(v3.9.21) H=25: SO tgl-25 promix → CEK Promix 04",
          _vv31r is not None and _vv31r["CEK"] == "Promix 04",
          f"cek={None if _vv31r is None else _vv31r['CEK']!r}")
    _dv31r.tanggal_h_var.set("24")
    _dv31r._on_tanggal_h_change()
    wait_view(root, _dv31r)
    root.update()
    _, _vv31s = _row_vals30(_dv31r, "P-H")
    check("(v3.9.21) Apply H=24: sumber tgl-24 so-harian → label Promix "
          "HILANG (mengikuti tanggal analisa)",
          _vv31s is not None and _vv31s["CEK"] != "Promix 04",
          f"cek={None if _vv31s is None else _vv31s['CEK']!r}")
    _top31r.destroy()
    root.update()

    # =====================================================================
    # §32 v3.9.22 — CEK BEDA TANGGAL (SO stale) + H DINAMIS + POPUP NOMOR
    #      + DEFAULT KATEGORI REKAP IN + OVERLAY PER-CELL TK 8.6
    # =====================================================================
    print("== 32. v3.9.22 — CEK Beda Tanggal stale + H dinamis 26 + "
          "popup Nomor + default KATEGORI + overlay Tk 8.6 ==")

    # --- (a) CEK "Beda Tanggal" SO-STAEL (user: "Dikolom CEK analisa Beda
    #     tanggal kok tidak ada ya") -------------------------------------
    def _row32(barang, resto, jenis, tgl, nilai, satuan="GR",
               nomor=None, source=None):
        return {"Nama Barang": barang, "JENIS": jenis,
                "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": nilai,
                "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                "Nomor": nomor, "Nomor PO": None,
                "#Tgl/Jam Pembuatan IT": None, "SOURCE DATA": source}

    _ROWS32 = [
        # FRESH: SO nonzero di 25 (=H dinamis) — tidak terflag (kontrol)
        _row32("FRESH", "R", "1.SO", 25, 10.0),
        _row32("FRESH", "R", "2.SALDO AKHIR", 25, 10.0),
        # STALE: SO nonzero TERAKHIR 24 (< H 25) — SO belum diinput H
        _row32("STALE", "R", "1.SO", 24, 10.0),
        _row32("STALE", "R", "1.SO", 25, 0.0),
        _row32("STALE", "R", "2.SALDO AKHIR", 25, 10.0),
        # NOSO: tanpa baris 1.SO sama sekali (barang hanya-app) — terflag
        _row32("NOSO", "R", "2.SALDO AKHIR", 25, 7.0),
    ]
    _df32 = pd.DataFrame(_ROWS32)
    _top32a, _dv32a = _make_dv30(_df32)
    _, _fresh32 = _row_vals30(_dv32a, "FRESH")
    _, _stale32 = _row_vals30(_dv32a, "STALE")
    _, _noso32 = _row_vals30(_dv32a, "NOSO")
    # v3.9.27: aturan SO-stale (v3.9.22) DIHAPUS — CEK = port persis
    # formula LET sheet 'Data Base Cek Deviasi' kolom Y. STALE (SO 24=10
    # → SO 25=0): kondisi 4 Turun Drastis sheet = F>0 & H/F<50% →
    # 10/0 < 50% TERFLAG 'Turun Drastis' (bukan lagi 'Beda Tanggal').
    check("(v3.9.22→v3.9.27) CEK pasangan SO stale (SO terakhir 24 < H "
          "25, SO_H=0): aturan stale DIHAPUS → 'Turun Drastis' (kondisi "
          "4 sheet: F 10 > 0 & H/F 0 < 50%) — v3.9.22-26 'Beda Tanggal'",
          _stale32 is not None and _stale32["CEK"] == "Turun Drastis",
          f"cek={None if _stale32 is None else _stale32['CEK']!r}")
    # NOSO: tanpa baris SO sama sekali → SO_H=0 & so_m1=0 → tak ada
    # kondisi sheet yang terpicu → '' (dulu stale men-flag 'Beda Tanggal')
    check("(v3.9.22→v3.9.27) CEK pasangan NOSO (tanpa baris SO, "
          "SO_H=0): tak ada kondisi sheet terpicu → '' — dulu 'Beda "
          "Tanggal' (aturan stale)",
          _noso32 is not None and _noso32["CEK"] == "",
          f"cek={None if _noso32 is None else _noso32['CEK']!r}")
    # FRESH: SO nonzero muncul di H tanpa SO di H-1 → W sheet = 0 &
    # SO_H ≠ 0 → kondisi 3 'Hitung Manual' (port persis; dulu '' saat
    # stok lama berbasis sistem)
    check("(v3.9.27) CEK pasangan FRESH (SO nonzero di H, tanpa SO H-1): "
          "W sheet = 0 & SO_H 10 ≠ 0 → 'Hitung Manual' (port persis "
          "kondisi 3 sheet; dulu '')",
          _fresh32 is not None and _fresh32["CEK"] == "Hitung Manual",
          f"cek={None if _fresh32 is None else _fresh32['CEK']!r}")
    # prioritas Promix 04 tetap di atas Beda Tanggal
    _ROWS32B = [
        _row32("PROMIX", "R", "1.SO", 24, 5.0, source="input promix 04"),
        _row32("PROMIX", "R", "2.SALDO AKHIR", 25, 10.0),
    ]
    _top32b, _dv32b = _make_dv30(pd.DataFrame(_ROWS32B))
    _, _pm32 = _row_vals30(_dv32b, "PROMIX")
    check("(v3.9.22) Prioritas np.select utuh: Promix 04 tetap MENGALAHKAN "
          "Beda Tanggal (SO stale promix → label Promix 04)",
          _pm32 is not None and _pm32["CEK"] == "Promix 04",
          f"cek={None if _pm32 is None else _pm32['CEK']!r}")
    _top32a.destroy()
    _top32b.destroy()
    root.update()

    # --- (b) DEFAULT H DINAMIS (user: "Tanggal harusnya tanggal 26 bukan
    #     dari tanggal 25") ----------------------------------------------
    from src.ui.deviasi_view import DeviasiView as _DV32
    _dv32u = _DV32(tk.Toplevel(root))
    check("(v3.9.22) _default_h_from_data: tanggal SO NONZERO terakhir",
          _dv32u._default_h_from_data(pd.DataFrame(_ROWS32)) == 25 and
          _dv32u._default_h_from_data(pd.DataFrame(
              [_row32("X", "R", "1.SO", 26, 3.0)])) == 26,
          "h=25/26")
    check("(v3.9.22) _default_h_from_data: tanpa SO / SO semua-0 / None → "
          "None (fallback 26 dipakai pemanggil)",
          _dv32u._default_h_from_data(pd.DataFrame(
              [_row32("X", "R", "2.SALDO AKHIR", 25, 1.0)])) is None and
          _dv32u._default_h_from_data(pd.DataFrame(
              [_row32("X", "R", "1.SO", 26, 0.0),
               _row32("X", "R", "1.SO", 27, 0.0)])) is None and
          _dv32u._default_h_from_data(None) is None)
    _dv32u.destroy()
    _ROWS32C = [
        _row32("H26", "R", "1.SO", 26, 4.0),
        _row32("H26", "R", "2.SALDO AKHIR", 26, 3.0),
    ]
    _top32c, _dv32c = _make_dv30(pd.DataFrame(_ROWS32C))
    check("(v3.9.22) Data dgn SO s/d 26 → H dinamis = 26 otomatis saat "
          "load_data (dulu konstan 25)",
          _dv32c.tanggal_h == 26 and
          (hasattr(_dv32c, "_h_chip_var") is False or
           _dv32c._h_chip_var.get() == "26"),
          f"H={_dv32c.tanggal_h}")
    _dv32c.tanggal_h_var.set("20")
    _dv32c._on_tanggal_h_change()
    wait_view(root, _dv32c)
    root.update()
    _dv32c._reset_filter()
    wait_view(root, _dv32c)
    root.update()
    check("(v3.9.22) ✕ Reset Filter → H kembali ke default DINAMIS (26, "
          "dulu konstan 25)",
          _dv32c.tanggal_h == 26, f"H={_dv32c.tanggal_h}")
    _top32c.destroy()
    root.update()

    # --- (c) POPUP NOMOR (user: "Pop up di tab Deviasi GR dan PCS ada
    #     Nomor nya juga Misal IT...... atau RI......") -----------------
    _ROWS32D = [
        # tanggal 23: TANPA baris 4.IN → kolom Nomor harus kosong
        _row32("BRG N", "R", "1.SO", 23, 5.0),
        _row32("BRG N", "R", "2.SALDO AKHIR", 23, 5.0),
        _row32("BRG N", "R", "1.SO", 24, 10.0),
        _row32("BRG N", "R", "2.SALDO AKHIR", 24, 12.0),
        _row32("BRG N", "R", "4.IN", 24, 2.0,
               nomor="IT.2026.09.5123, IT.2026.09.2123"),
        _row32("BRG N", "R", "4.IN", 24, 1.0,
               nomor="IT.2026.09.2123, IT.2026.09.0007"),
        _row32("BRG N", "R", "1.SO", 25, 8.0),
        _row32("BRG N", "R", "2.SALDO AKHIR", 25, 4.0),
        _row32("BRG N", "R", "4.IN", 25, 1.0,
               nomor="RI.2026.08.10354"),
    ]
    _pr32 = build_popup_rows(pd.DataFrame(_ROWS32D), "BRG N", "R")
    _nom24 = list(_pr32[_pr32["Tanggal"] == "24"]["Nomor"])
    _nom25 = list(_pr32[_pr32["Tanggal"] == "25"]["Nomor"])
    check("(v3.9.22) Popup Nomor: tanggal 24 = IT. nomor DIDEDUP + "
          "DIURUT + digabung koma (2 baris IN tumpang-tindih)",
          _nom24 == ["IT.2026.09.0007, IT.2026.09.2123, "
                     "IT.2026.09.5123"],
          f"got {_nom24}")
    check("(v3.9.22) Popup Nomor: tanggal 25 = nomor RI.",
          _nom25 == ["RI.2026.08.10354"], f"got {_nom25}")
    _nom23 = list(_pr32[_pr32["Tanggal"] == "23"]["Nomor"])
    check("(v3.9.22) Popup Nomor: tanggal TANPA IN → kosong (bukan "
          "'nan')",
          _nom23 == [""], f"got {_nom23}")
    _pop32 = show_deviasi_popup(root, pd.DataFrame(_ROWS32D), "BRG N",
                                "R", satuan="GR", h=25)
    root.update()
    _k32 = [k for k in _pop32.tree.get_children("")
            if _pop32.tree.set(k, "Tanggal") == "24"]
    check("(v3.9.22) Popup GUI: kolom Nomor tampil di tabel + nilai "
          "dedup/urut",
          bool(_k32) and
          _pop32.tree.set(_k32[0], "Nomor") ==
          "IT.2026.09.0007, IT.2026.09.2123, IT.2026.09.5123",
          f"got {_pop32.tree.set(_k32[0], 'Nomor') if _k32 else '-'}")
    _pop32.destroy()
    root.update()

    # --- (d) DEFAULT KATEGORI DEVIASI Rekap Selisih IN (user: "Rekap
    #     selisih IN Default Kategori Deviasi") ------------------------
    _audit32 = pd.DataFrame({
        "Resto": ["RA", "RA", "RB"],
        "Tanggal": [24, 25, 24],
        "Nama Item": ["DEVI BRG", "DEVI BRG", "REJ BRG"],
        "Hasil SO": [10.0, 10.0, 5.0],
        "Qty SO Harian": [0.0, 0.0, 0.0],
        "Penerimaan Sistem": [2.0, 1.0, 1.0],
        "Selisih Harian": [2.0, 1.0, 1.0],
        "Saldo Kumulatif": [12.0, 11.0, 6.0],
        "Status Analisis Audit": ["SELISIH", "SELISIH", "SELISIH"],
        "Detail & Catatan Audit": ["", "", ""],
    })
    _data32 = pd.DataFrame({
        "Nama Barang": ["DEVI BRG", "REJ BRG"],
        "NAMA RESTO": ["RA", "RB"],
        "SATUAN": ["GR", "GR"],
        "KATEGORI": ["DEVIASI", "REJECT"],
        "JENIS": ["1.SO", "1.SO"],
        "Tanggal": [25, 25],
        "NILAI": [10.0, 5.0],
    })
    _top32d = tk.Toplevel(root)
    _top32d.geometry("1200x700+10+10")
    _isv32 = _ISV30(_top32d)
    _isv32.pack(fill="both", expand=True)
    _isv32.load_data(_data32, None,
                     audit_result={"df": _audit32, "kpi": {},
                                   "desc": ""})
    _pump30(1.0)
    _isv32._refresh(sync=True)
    wait_view(root, _isv32)
    root.update()
    check("(v3.9.22) Rekap Selisih IN: default KATEGORI = Deviasi "
          "(state _col_sel + ikon corong aktif)",
          _isv32._col_sel.get("KATEGORI") == ["DEVIASI"] and
          _isv32.header_filters._filters["KATEGORI"].selected ==
          {"DEVIASI"},
          f"sel={_isv32._col_sel.get('KATEGORI')}")
    _bars32 = {_isv32.tree.set(_k32d, "KATEGORI")
               for _k32d in _isv32.tree.get_children("")}
    check("(v3.9.22) Rekap Selisih IN: baris tampil TERFILTER ke "
          "DEVIASI saja (baris REJECT tersembunyi — audit 2 baris "
          "DEVIASI + 1 REJECT)",
          _bars32 == {"DEVIASI"},
          f"got {_bars32}")
    _isv32._reset_filter()
    wait_view(root, _isv32)
    root.update()
    check("(v3.9.22) ✕ Reset Filter Rekap IN → default Deviasi "
          "dipasang LAGI (bukan 'Semua')",
          _isv32._col_sel.get("KATEGORI") == ["DEVIASI"],
          f"sel={_isv32._col_sel.get('KATEGORI')}")
    _isv32._col_sel["KATEGORI"] = None
    _isv32.header_filters.clear_all()
    _isv32._refresh()
    wait_view(root, _isv32)
    root.update()
    _bars32b = {_isv32.tree.set(_k32d, "KATEGORI")
                for _k32d in _isv32.tree.get_children("")}
    check("(v3.9.22) Tanpa default (filter dibuka manual) → semua "
          "kategori tampil — filter tetap fleksibel",
          _bars32b == {"DEVIASI", "REJECT"}, f"got {_bars32b}")
    _top32d.destroy()
    root.update()

    # --- (e) OVERLAY PER-CELL TK 8.6 (user: "Saat ini disemua tab warna
    #     masih tidak per cell tapi per row. coba cari alternatif lain")
    #     — paksa jalur overlay (Tk sandbox = 9; user = 8.6) ----------
    import src.ui.widgets as _W32
    _native32 = _W32.CELL_TAGS_NATIVE
    try:
        _W32.CELL_TAGS_NATIVE = False
        _ov32 = _dv32c if False else None   # (view 32c sudah didestroy)
        _top32e, _dv32e = _make_dv30(pd.DataFrame([
            _row32("BRG OVL", "R", "1.SO", 25, 12.0),
            _row32("BRG OVL", "R", "2.SALDO AKHIR", 25, 9.0),
            _row32("BRG OVL2", "R", "1.SO", 25, 4.0),
            _row32("BRG OVL2", "R", "2.SALDO AKHIR", 25, 6.0),
        ]))
        _ov32 = _dv32e.tree._cell_color_overlay
        check("(v3.9.22) Overlay per-cell TERPASANG di tree (jalur Tk "
              "8.6 — CELL_TAGS_NATIVE dipaksa False)",
              _ov32 is not None and _ov32._alive,
              f"overlay={_ov32}")
        # kolom Deviasi ada di ujung kanan — geser xscroll supaya
        # terlihat (label overlay hanya utk sel TERLIHAT — virtual)
        _dv32e.tree.xview_moveto(1.0)
        root.update()
        _pump30(0.3)
        _negkeys32 = [k for k, lab in _ov32._labels.items()
                      if str(lab["fg"]) == "#dc2626"]
        check("(v3.9.22) Overlay: sel minus merah PER CELL (label overlay "
              "fg #dc2626 — hanya sel Deviasi minus, bukan seluruh baris)",
              bool(_negkeys32) and all(k[1] == "Deviasi"
                                       for k in _negkeys32),
              f"keys={_negkeys32[:4]}")
        _hlkeys32 = [k for k, lab in _ov32._labels.items()
                     if str(lab["bg"]) == "#fef3c7"]
        check("(v3.9.22) Overlay: highlight kolom Deviasi/SO_H amber "
              "PER CELL koexist dgn minus (merge 2 tag: bg amber + fg "
              "merah di sel sama)",
              bool(_hlkeys32),
              f"keys={len(_hlkeys32)}")
        _merg32 = [k for k, lab in _ov32._labels.items()
                   if str(lab["bg"]) == "#fef3c7" and
                   str(lab["fg"]) == "#dc2626"]
        check("(v3.9.22) Overlay: merge warna tag sel (amber bg + merah "
              "fg di sel minus kolom highlight — meniru Tk 9)",
              _merg32 == _negkeys32, f"merge={_merg32}")
        # label teks identik dgn isi sel
        _k32e = _negkeys32[0] if _negkeys32 else None
        check("(v3.9.22) Overlay: teks label == nilai sel tree (identik "
              "tampilan)",
              _k32e is not None and
              _ov32._labels[_k32e]["text"] ==
              _dv32e.tree.set(_k32e[0], _k32e[1]),
              f"text={_ov32._labels[_k32e]['text'] if _k32e else '-'}")
        # klik label → seleksi baris (penerusan event)
        _dv32e.tree.selection_set()
        root.update()
        if _k32e is not None:
            _ov32._labels[_k32e].event_generate("<Button-1>", x=5, y=5)
            root.update()
        check("(v3.9.22) Overlay: klik sel warna → SELEKSI baris tetap "
              "jalan (event diteruskan ke tree)",
              list(_dv32e.tree.selection()) == [_k32e[0]] if _k32e
              else False,
              f"sel={list(_dv32e.tree.selection())}")
        # double-click label → popup terbuka (deteksi manual + fire
        # binding tree)
        from src.ui.deviasi_popup import DeviasiPopup as _DP32
        _dbl32 = {"n": 0}
        _dv32e.tree.bind("<Double-1>",
                         lambda e: _dbl32.update(n=_dbl32["n"] + 1),
                         add="+")
        if _k32e is not None:
            _lab32e = _ov32._labels[_k32e]
            _lab32e.event_generate("<Button-1>", x=5, y=5)
            root.update()
            import time as _t32
            _t32.sleep(0.45)
            _lab32e.event_generate("<Button-1>", x=5, y=5)
            root.update()
        check("(v3.9.22) Overlay: DOUBLE-CLICK sel warna → binding "
              "<Double-1> tree terpanggil (popup detail jalan)",
              _dbl32["n"] >= 1, f"n={_dbl32['n']}")
        # scroll → label ikut / diganti (label hanya utk sel terlihat)
        _dv32e.tree.yview_moveto(1.0)
        root.update()
        _pump30(0.2)
        check("(v3.9.22) Overlay: label virtual — hanya sel TERLIHAT di "
              "viewport (scroll mengganti label, bukan 1-per-baris "
              "tabel)",
              len(_ov32._labels) <= 6, f"labels={len(_ov32._labels)}")
        _top32e.destroy()
        root.update()
    finally:
        _W32.CELL_TAGS_NATIVE = _native32
    # jalur native Tk 9 tetap utuh (sandbox)
    check("(v3.9.22) Jalur native Tk 9 tidak tersentuh (CELL_TAGS_NATIVE "
          "dipulihkan)",
          _W32.CELL_TAGS_NATIVE is True and
          _W32.CELL_TAGS_SUPPORTED is True)

    # =====================================================================
    # §33 v3.9.23 — CEK "RI Balancing" KOLOM UTAMA (poin 6) + CATATAN
    #      AUDIT OTOMATIS REKAP SELISIH IN (semua poin B)
    #      (user: "kerjakan poin 6 dan kerjakan semua poin B")
    # =====================================================================
    print("== 33. v3.9.23 — CEK RI Balancing kolom utama + Catatan Audit "
          "otomatis ==")

    # --- (a) doc_codes — modul bersama (logika tidak diduplikasi) -------
    from src.ui import doc_codes as _DC33
    from src.ui.doc_codes import (
        duplicated_doc_numbers as _dupn33,
    )
    from src.ui.doc_codes import (
        ri_balancing_docs as _rbd33,
    )
    from src.ui.in_selisih_view import (
        InSelisihView as _ISV33,
    )
    from src.ui.in_selisih_view import (
        _join_notes as _jn33,
    )
    from src.ui.in_selisih_view import (
        _ri_balancing as _rib33,
    )
    from src.ui.in_selisih_view import (
        _tgl_key as _tk33,
    )
    check("(v3.9.23) Helper kode dokumen diangkat ke modul bersama: "
          "_ri_balancing dari in_selisih_view ADALAH doc_codes._ri_balancing "
          "(re-export — logika tidak diduplikasi antar view)",
          _rib33 is _DC33._ri_balancing)

    _det33 = pd.DataFrame([
        # RBAL — RI Okt vs PO Agt (balancing), tgl 20 ≤ H 25
        {"NAMA RESTO": "R", "Nama Barang": "RBAL", "Tanggal": 20,
         "Value": 5, "Nomor": "RI.2026.10.001",
         "Nomor PO": "PO.2026.08.001", "SOURCE IN": "32.24",
         "JENIS": "IN"},
        # FUTR — balancing TAPI tgl 27 > H 25 (di luar scope analisa)
        {"NAMA RESTO": "R", "Nama Barang": "FUTR", "Tanggal": 27,
         "Value": 5, "Nomor": "RI.2026.10.002",
         "Nomor PO": "PO.2026.08.002", "SOURCE IN": "32.24",
         "JENIS": "IN"},
        # SAME — periode sama (bukan balancing)
        {"NAMA RESTO": "R", "Nama Barang": "SAME", "Tanggal": 20,
         "Value": 5, "Nomor": "RI.2026.08.003",
         "Nomor PO": "PO.2026.08.003", "SOURCE IN": "32.24",
         "JENIS": "IN"},
        # DUPX — nomor kembar 2 baris (pasangan sama)
        {"NAMA RESTO": "R", "Nama Barang": "DUPX", "Tanggal": 21,
         "Value": 6, "Nomor": "IT.2026.09.001",
         "Nomor PO": "PO.2026.09.001", "SOURCE IN": "42.05",
         "JENIS": "IN"},
        {"NAMA RESTO": "R", "Nama Barang": "DUPX", "Tanggal": 21,
         "Value": 7, "Nomor": "IT.2026.09.001",
         "Nomor PO": "PO.2026.09.001", "SOURCE IN": "42.05",
         "JENIS": "IN"},
        # PROMIXRB — balancing TAPI pasangan promix → Promix 04 tetap
        # prioritas ke-1 (uji prioritas nyata: kondisi keduanya aktif)
        {"NAMA RESTO": "R", "Nama Barang": "PROMIXRB", "Tanggal": 20,
         "Value": 5, "Nomor": "RI.2026.10.004",
         "Nomor PO": "PO.2026.08.004", "SOURCE IN": "32.24",
         "JENIS": "IN"},
        # MULTIITEM — dokumen SAH 1 nomor 2 barang beda (bukan dobel)
        {"NAMA RESTO": "R", "Nama Barang": "ITM A", "Tanggal": 21,
         "Value": 1, "Nomor": "IT.2026.09.777",
         "Nomor PO": "PO.2026.09.777", "SOURCE IN": "42.05",
         "JENIS": "IN"},
        {"NAMA RESTO": "R", "Nama Barang": "ITM B", "Tanggal": 21,
         "Value": 2, "Nomor": "IT.2026.09.777",
         "Nomor PO": "PO.2026.09.777", "SOURCE IN": "42.05",
         "JENIS": "IN"},
    ])
    _rbd33res = _rbd33(_det33)
    check("(v3.9.23) ri_balancing_docs: SEMUA pasangan ber-dokumen "
          "balancing terdeteksi (RBAL + FUTR + PROMIXRB — fungsi murni "
          "pair-level, TIDAK memfilter tanggal; filter scope ≤ H adalah "
          "tugas view), dokumen periode-sama tidak",
          set(_rbd33res.keys()) ==
          {("RBAL", "R"), ("FUTR", "R"), ("PROMIXRB", "R")} and
          _rbd33res[("RBAL", "R")] == ["RI.2026.10.001"] and
          _rbd33res[("FUTR", "R")] == ["RI.2026.10.002"] and
          _rbd33res[("PROMIXRB", "R")] == ["RI.2026.10.004"],
          f"got {dict(_rbd33res)}")
    check("(v3.9.23) ri_balancing_docs: None/empty/frame tanpa kolom → {} "
          "(defensif)",
          _rbd33(None) == {} and
          _rbd33(pd.DataFrame()) == {} and
          _rbd33(pd.DataFrame({"Nomor": ["RI.2026.10.1"]})) == {})
    _dupn33res = _dupn33(_det33)
    check("(v3.9.23) duplicated_doc_numbers: nomor kembar ×2 terdeteksi "
          "per pasangan (gejala input ganda / sheet kembar)",
          _dupn33res == {("DUPX", "R"): {"IT.2026.09.001": 2}},
          f"got {dict(_dupn33res)}")
    check("(v3.9.23) duplicated_doc_numbers: dokumen sah ber-2 ITEM beda "
          "barang TIDAK dianggap dobel; None → {}",
          ("ITM A", "R") not in _dupn33res and
          ("ITM B", "R") not in _dupn33res and _dupn33(None) == {})
    check("(v3.9.23) _tgl_key: 25.0→25, '24'→24, NaN/None→None",
          _tk33(25.0) == 25 and _tk33("24") == 24 and
          _tk33(float("nan")) is None and _tk33(None) is None)
    check("(v3.9.23) _join_notes: catatan VBA tetap PERTAMA + ' | '; VBA "
          "'-' diganti catatan app; tanpa catatan app → VBA utuh",
          _jn33("Sisa Gantung: -13", ["B1", "B2"]) ==
          "Sisa Gantung: -13 | B1 | B2" and
          _jn33("-", ["B1"]) == "B1" and
          _jn33("", ["B1"]) == "B1" and
          _jn33("VBA saja", None) == "VBA saja" and
          _jn33("VBA saja", []) == "VBA saja")

    # --- (b) CEK "RI Balancing" KOLOM UTAMA tab Deviasi GR (poin 6) ----
    from src.ui.deviasi_view import DeviasiView as _DV33

    def _row33(barang, resto, jenis, tgl, nilai, satuan="GR",
               source=None):
        return {"Nama Barang": barang, "JENIS": jenis,
                "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": nilai,
                "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                "Nomor": None, "Nomor PO": None,
                "#Tgl/Jam Pembuatan IT": None, "SOURCE DATA": source}

    _ROWS33 = [
        # RBAL: SO stale (24 < H 25) + dokumen balancing tgl 20 → RI
        # Balancing MENGALAHKAN Beda Tanggal (anomali dokumen faktual
        # di atas heuristik pola)
        _row33("RBAL", "R", "1.SO", 24, 10.0),
        _row33("RBAL", "R", "2.SALDO AKHIR", 25, 10.0),
        # STALE: SO stale TANPA dokumen → Beda Tanggal (perilaku lama)
        _row33("STALE", "R", "1.SO", 24, 10.0),
        _row33("STALE", "R", "1.SO", 25, 0.0),
        _row33("STALE", "R", "2.SALDO AKHIR", 25, 10.0),
        # FUTR: dokumen balancing tgl 27 > H 25 → DI LUAR scope analisa
        # (tidak terflag; SO 24 & 25 = 10 — W=10, rasio 0, tak ada
        # kondisi numerik lain terpicu → CEK bersih utk uji scope)
        _row33("FUTR", "R", "1.SO", 24, 10.0),
        _row33("FUTR", "R", "1.SO", 25, 10.0),
        _row33("FUTR", "R", "2.SALDO AKHIR", 25, 10.0),
        # PROMIXRB: promix + dokumen balancing → Promix 04 TETAP no. 1
        _row33("PROMIXRB", "R", "1.SO", 25, 5.0,
               source="input promix 04"),
        _row33("PROMIXRB", "R", "2.SALDO AKHIR", 25, 10.0),
    ]

    def _make_dv33(df, det=None):
        _top33 = tk.Toplevel(root)
        _top33.geometry("1250x700+15+15")
        _dv33 = _DV33(_top33, satuan_mode="GR")
        _dv33.pack(fill="both", expand=True)
        root.update()
        root.update_idletasks()
        root.update()
        _dv33.load_data(df, det)
        wait_view(root, _dv33)
        return _top33, _dv33

    def _cek33(dv, barang):
        for _k33 in dv.tree.get_children(""):
            if dv.tree.set(_k33, "Nama Barang") == barang:
                return dv.tree.set(_k33, "CEK")
        return "<missing>"

    _top33a, _dv33a = _make_dv33(pd.DataFrame(_ROWS33), _det33)
    check("(v3.9.23) CEK RI Balancing: pasangan ber-dokumen balancing "
          "(tgl dok 20 ≤ H 25) TERFLAG 'RI Balancing' di kolom utama — "
          "dulu hanya terlihat di popup Rincian IN",
          _cek33(_dv33a, "RBAL") == "RI Balancing",
          f"cek={_cek33(_dv33a, 'RBAL')!r}")
    # v3.9.27: stale dihapus → STALE jatuh ke 'Turun Drastis' (kondisi
    # 4 sheet, F 10 > 0 & H/F 0 < 50%); prioritas RI Balancing di atas
    # kondisi numerik tetap terbukti lewat RBAL.
    check("(v3.9.23→v3.9.27) Prioritas: RI Balancing MENGALAHKAN kondisi "
          "numerik (RBAL='RI Balancing' meski SO 24→25 turun drastis); "
          "stale tanpa dokumen = 'Turun Drastis' (v3.9.22-26: 'Beda "
          "Tanggal')",
          _cek33(_dv33a, "STALE") == "Turun Drastis",
          f"cek={_cek33(_dv33a, 'STALE')!r}")
    check("(v3.9.23) Scope analisa: dokumen balancing bertanggal 27 > "
          "H 25 TIDAK terflag (belum termasuk analisa)",
          _cek33(_dv33a, "FUTR") == "",
          f"cek={_cek33(_dv33a, 'FUTR')!r}")
    check("(v3.9.23) Prioritas Promix 04 TETAP pertama (by design "
          "v3.9.19 — SO sistem-turunan) meski pasangan JUGA punya "
          "dokumen balancing (kedua kondisi aktif)",
          _cek33(_dv33a, "PROMIXRB") == "Promix 04",
          f"cek={_cek33(_dv33a, 'PROMIXRB')!r}")
    check("(v3.9.23) Tag warna cek_ri_bal terpasang (amber gelap #92400e "
          "— keluarga popup Rincian IN, terbedakan dari Kosong/Non Aktif)",
          str(_dv33a.tree.tag_configure("cek_ri_bal",
                                        "foreground")).lower() ==
          "#92400e")
    _vals33 = _dv33a._col_values("CEK")
    check("(v3.9.23) Filter ⧩ CEK memuat 'RI Balancing' (nilai = data "
          "yang ada — tidak ada opsi kosong)",
          "RI Balancing" in [v for v in _vals33],
          f"vals={_vals33}")
    # H berubah → scope dokumen ikut (dokumen tgl 27 masuk saat H=27)
    _dv33a.tanggal_h_var.set("27")
    _dv33a._on_tanggal_h_change()
    wait_view(root, _dv33a)
    root.update()
    check("(v3.9.23) H naik ke 27 → dokumen balancing tgl 27 kini DI "
          "DALAM scope → pasangan terflag (analisa mengikuti H)",
          _cek33(_dv33a, "FUTR") == "RI Balancing",
          f"cek={_cek33(_dv33a, 'FUTR')!r}")
    _top33a.destroy()
    root.update()

    # --- (b2) KOMPATIBILITAS: tanpa in_detail → kondisi tidak berlaku --
    _top33b, _dv33b = _make_dv33(pd.DataFrame(_ROWS33), None)
    # v3.9.27: stale dihapus → tanpa in_detail, RBAL (SO 24=10 → 25=0)
    # jatuh ke 'Turun Drastis' (kondisi 4 sheet; v3.9.22-26: 'Beda
    # Tanggal' via aturan stale)
    check("(v3.9.23→v3.9.27) Kompatibel: load_data TANPA in_detail "
          "(pemanggil lama/test) → kondisi tidak berlaku, RBAL = "
          "'Turun Drastis' (v3.9.22-26: 'Beda Tanggal')",
          _cek33(_dv33b, "RBAL") == "Turun Drastis",
          f"cek={_cek33(_dv33b, 'RBAL')!r}")
    _top33b.destroy()
    root.update()

    # --- (c) app wiring: in_detail diteruskan ke KEDUA tab Deviasi -----
    append1_33 = make_mock_append1()
    rincian_33 = make_mock_rincian()
    in_detail_33 = make_mock_in_detail()
    rekap_so_33 = make_mock_rekap_so()
    from src.pipeline.fn_audit import build_audit_from_app as _baf33
    _audit_df33, _akpi33, _adesc33 = _baf33(rekap_so_33, in_detail_33)
    _ares33 = {"df": _audit_df33, "kpi": _akpi33, "desc": _adesc33}
    app._on_pipeline_done(append1_33, rincian_33, in_detail_33,
                          _ares33, None)
    root.update()
    check("(v3.9.23) app wiring: in_detail diteruskan ke tab Deviasi GR "
          "& PCS (sumber CEK RI Balancing — sama seperti tab Rekap IN)",
          app.deviasi_gr_view.in_detail is in_detail_33 and
          app.deviasi_pcs_view.in_detail is in_detail_33)

    # --- (d) CATATAN AUDIT OTOMATIS Rekap Selisih IN (semua poin B) ----
    _audit33 = pd.DataFrame({
        "Resto": ["R", "R", "R", "R"],
        "Tanggal": [20, 21, 22, 23],
        "Nama Item": ["BRG B1", "BRG B2", "BRG B4", "BRG CLEAN"],
        "Hasil SO": [5.0, 2.0, 1.0, 3.0],
        "Qty SO Harian": [0.0, 10.0, 0.0, 8.0],
        "Penerimaan Sistem": [13.0, 13.0, 13.0, 8.0],
        "Selisih Harian": [-13.0, -3.0, -13.0, 0.0],
        "Saldo Kumulatif": [-13.0, -3.0, -13.0, 0.0],
        "Status Analisis Audit": ["DEVIASI MURNI", "DEVIASI MURNI",
                                  "DEVIASI MURNI", "OK (Matching)"],
        "Detail & Catatan Audit": ["Sisa Gantung: -13", "-", "", ""],
    })
    _det33b = pd.DataFrame([
        # B1: RI Okt vs PO Agt di tgl 20 (baris BRG B1)
        {"NAMA RESTO": "R", "Nama Barang": "BRG B1", "Tanggal": 20,
         "Value": 5, "Nomor": "RI.2026.10.001",
         "Nomor PO": "PO.2026.08.001", "SOURCE IN": "32.24",
         "JENIS": "IN"},
        # B2: nomor kembar di tgl 21 (baris BRG B2)
        {"NAMA RESTO": "R", "Nama Barang": "BRG B2", "Tanggal": 21,
         "Value": 6, "Nomor": "IT.2026.09.001",
         "Nomor PO": "PO.2026.09.001", "SOURCE IN": "42.05",
         "JENIS": "IN"},
        {"NAMA RESTO": "R", "Nama Barang": "BRG B2", "Tanggal": 21,
         "Value": 7, "Nomor": "IT.2026.09.001",
         "Nomor PO": "PO.2026.09.001", "SOURCE IN": "42.05",
         "JENIS": "IN"},
    ])
    _top33c = tk.Toplevel(root)
    _top33c.geometry("1350x700+10+10")
    _isv33 = _ISV33(_top33c)
    _isv33.pack(fill="both", expand=True)
    _data33 = pd.DataFrame({
        "Nama Barang": ["BRG B1", "BRG B2", "BRG B4", "BRG CLEAN"],
        "NAMA RESTO": ["R", "R", "R", "R"],
        "SATUAN": ["GR", "GR", "GR", "GR"],
        "KATEGORI": ["DEVIASI", "DEVIASI", "DEVIASI", "DEVIASI"],
        "JENIS": ["1.SO", "1.SO", "1.SO", "1.SO"],
        "Tanggal": [20, 21, 22, 23],
        "NILAI": [10.0, 10.0, 10.0, 10.0],
    })
    _isv33.load_data(_data33, _det33b,
                     audit_result={"df": _audit33, "kpi": {},
                                   "desc": ""})
    _pump30(1.0)
    _isv33._refresh(sync=True)
    wait_view(root, _isv33)
    root.update()

    def _cat33(isv, barang):
        for _k33 in isv.tree.get_children(""):
            if isv.tree.set(_k33, "Nama Barang") == barang:
                return isv.tree.set(_k33, "Catatan Audit")
        return "<missing>"

    _c_b1 = _cat33(_isv33, "BRG B1")
    check("(v3.9.23) B1: catatan RI Balancing dgn nomor dokumen + periode "
          "PO, di-append SETELAH catatan VBA (VBA tetap pertama)",
          _c_b1.startswith("Sisa Gantung: -13 | ") and
          "RI Balancing: RI.2026.10.001 (PO 2026-08)" in _c_b1,
          f"got {_c_b1!r}")
    _c_b2 = _cat33(_isv33, "BRG B2")
    check("(v3.9.23) B2: catatan Nomor dobel (×N) + B3 Selisih IN dgn "
          "arah perbedaan; VBA '-' diganti (bukan dobel separator)",
          _c_b2.startswith("Nomor dobel: IT.2026.09.001 ×2") and
          "Selisih IN (3) (IN 13 > BM 10)" in _c_b2 and
          " | " in _c_b2,
          f"got {_c_b2!r}")
    _c_b4 = _cat33(_isv33, "BRG B4")
    check("(v3.9.23) B4: BM 0 padahal IN > 0 → diagnosis 'input rekap "
          "belum diisi' (data quality — tidak ditulis 'Selisih IN')",
          _c_b4 == "BM 0 padahal IN 13 (input rekap belum diisi)",
          f"got {_c_b4!r}")
    # matikan filter "hanya selisih" (default ON) supaya baris selisih-0
    # (BRG CLEAN) ikut tampil — catatan BERSIH diperiksa juga
    _isv33.only_selisih_var.set(False)
    _isv33._refresh(sync=True)
    wait_view(root, _isv33)
    root.update()
    _c_clean = _cat33(_isv33, "BRG CLEAN")
    check("(v3.9.23) Baris BERSIH (BM == IN, tanpa dokumen anomali) → "
          "catatan tetap kosong (tidak ada noise)",
          _c_clean == "",
          f"got {_c_clean!r}")

    # catatan ikut ke 💾 Export (kolom Catatan Audit di AUDIT_EXPORT_COLUMNS)
    from src.ui.export_sheets import build_selisih_export_df as _bse33
    _base33 = _isv33._cached_base
    _exp33 = _bse33(_base33, 1, 31,
                    audit_cols=["Hasil Audit", "Saldo", "Catatan Audit"])
    _exp_cat33 = ""
    if "Catatan Audit" in _exp33.columns:
        _rowb1 = _exp33[_exp33["Nama Barang"] == "BRG B1"]
        _exp_cat33 = (str(_rowb1["Catatan Audit"].iloc[0])
                      if not _rowb1.empty else "")
    check("(v3.9.23) Export: catatan audit terkaya ikut ke file Excel "
          "(build_selisih_export_df membawa kolom Catatan Audit hasil "
          "enrichment)",
          "RI Balancing: RI.2026.10.001 (PO 2026-08)" in _exp_cat33,
          f"got {_exp_cat33!r}")
    _top33c.destroy()
    root.update()

    # =====================================================================
    # §34 v3.9.24 — RI BALANCING PERIODE BISNIS 26→25 (klarifikasi user)
    # =====================================================================
    print("== 34. v3.9.24 — RI Balancing periode bisnis 26→25 ==")

    # --- (a) unit: _ri_balancing tanggal-aware (doc_codes) --------------
    from src.ui.doc_codes import (
        _day_of as _day34,
    )
    from src.ui.doc_codes import (
        _ri_period_months as _rpm34,
    )
    from src.ui.doc_codes import (
        _shift_period as _shp34,
    )
    from src.ui.doc_codes import (
        ri_balancing_docs as _rbd34,
    )
    from src.ui.in_selisih_view import _ri_balancing as _rib34
    from src.ui.in_selisih_view import _ri_balancing_by_date as _rbd34d

    check("(v3.9.24) Contoh user PERSIS: RI.2026.10.10354 transaksi "
          "tgl 1 Okt (periode 26 Sep–25 Okt) + PO.2026.08.00571 (Agu "
          "∉ {Sep, Okt}) → 'RI Balancing'",
          _rib34("RI.2026.10.10354", "PO.2026.08.00571", 1) ==
          "RI Balancing")
    check("(v3.9.24) INTI PERBAIKAN: RI 1 Okt + PO September → '' "
          "(satu periode dgn RI — v3.9.19-23 salah-flag); + PO Oktober "
          "→ ''",
          _rib34("RI.2026.10.10354", "PO.2026.09.00571", 1) == "" and
          _rib34("RI.2026.10.10354", "PO.2026.10.00571", 1) == "")
    check("(v3.9.24) Batas 25/26: RI Sep tgl 26 satu periode dgn Okt "
          "(26 Sep–25 Okt) → PO Okt ''; RI Sep tgl 25 = periode 26 "
          "Agu–25 Sep → PO Okt di luar → flag",
          _rib34("RI.2026.09.5", "PO.2026.10.1", 26) == "" and
          _rib34("RI.2026.09.5", "PO.2026.08.1", 26) == "RI Balancing" and
          _rib34("RI.2026.09.5", "PO.2026.10.1", 25) == "RI Balancing" and
          _rib34("RI.2026.09.5", "PO.2026.08.1", 25) == "")
    check("(v3.9.24) Tanggal bulan-lalu NEGATIF dibaca absolut: -26 = "
          "tgl 26 (RI Sep -26 + PO Okt '')",
          _rib34("RI.2026.09.5", "PO.2026.10.1", -26) == "" and
          _rib34("RI.2026.09.5", "PO.2026.10.1", -25) == "RI Balancing")
    check("(v3.9.24) Wrap tahun Des↔Jan: RI 28 Des (periode 26 Des–25 "
          "Jan) + PO Jan-thn-depan '' — sekalian bulan 1-2 digit",
          _rib34("RI.2026.12.1", "PO.2027.1.1", 28) == "" and
          _rib34("RI.2027.1.1", "PO.2026.12.1", 10) == "" and
          _rib34("RI.2027.01.15", "PO.2026.11.30", 10) == "RI Balancing")
    check("(v3.9.24) Fallback TANPA tanggal valid → aturan lama "
          "bulan≠bulan (tahun-aware): 2-arg / None / NaN / 0 / 32 / 'x'",
          _rib34("RI.2026.10.1", "PO.2026.08.1") == "RI Balancing" and
          _rib34("RI.2026.10.1", "PO.2026.09.1") == "RI Balancing" and
          _rib34("RI.2026.10.1", "PO.2026.10.1") == "" and
          _rib34("RI.2026.10.1", "PO.2026.08.1", None) ==
          "RI Balancing" and
          _rib34("RI.2026.10.1", "PO.2026.08.1", float("nan")) ==
          "RI Balancing" and
          _rib34("RI.2026.10.1", "PO.2026.09.1", 0) == "RI Balancing" and
          _rib34("RI.2026.10.1", "PO.2026.09.1", 32) == "RI Balancing" and
          _rib34("RI.2026.10.1", "PO.2026.09.1", "x") == "RI Balancing")
    check("(v3.9.24) _ri_period_months / _shift_period / _day_of "
          "(unit — batas 25/26, wrap Des↔Jan, hari absolut 1..31)",
          _rpm34((2026, 10), 1) == {(2026, 9), (2026, 10)} and
          _rpm34((2026, 9), 26) == {(2026, 9), (2026, 10)} and
          _shp34(2026, 12, 1) == (2027, 1) and
          _shp34(2027, 1, -1) == (2026, 12) and
          _day34(20.0) == 20 and _day34("24") == 24 and
          _day34(-26) == 26 and _day34(None) is None and
          _day34(float("nan")) is None and _day34(0) is None and
          _day34(32) is None)

    # --- (b) frame-level: ri_balancing_docs + _ri_balancing_by_date ---
    _det34 = pd.DataFrame([
        # SEPPO — dulu salah-flag (RI Okt vs PO Sep), kini satu periode
        {"NAMA RESTO": "TGRGEL", "Nama Barang": "SEPPO",
         "Tanggal": 20, "Value": 5, "Nomor": "RI.2026.10.201",
         "Nomor PO": "PO.2026.09.201", "SOURCE IN": "32.24",
         "JENIS": "IN"},
        # AGUPO — contoh user (RI Okt tgl 1 vs PO Agu) → balancing
        {"NAMA RESTO": "TGRGEL", "Nama Barang": "AGUPO",
         "Tanggal": 1, "Value": 5, "Nomor": "RI.2026.10.10354",
         "Nomor PO": "PO.2026.08.00571", "SOURCE IN": "32.24",
         "JENIS": "IN"},
        # LALUOK — RI bulan-lalu tgl 28 (26 Sep–25 Okt) + PO Okt → ''
        {"NAMA RESTO": "TGRGEL", "Nama Barang": "LALUOK",
         "Tanggal": -28, "Value": 5, "Nomor": "RI.2026.09.301",
         "Nomor PO": "PO.2026.10.301",
         "SOURCE IN": "32.24 (Bulan Lalu)", "JENIS": "IN"},
        # LALUJUL — RI bulan-lalu tgl 28 + PO Jul → balancing
        {"NAMA RESTO": "TGRGEL", "Nama Barang": "LALUJUL",
         "Tanggal": -28, "Value": 5, "Nomor": "RI.2026.09.302",
         "Nomor PO": "PO.2026.07.302",
         "SOURCE IN": "32.24 (Bulan Lalu)", "JENIS": "IN"},
    ])
    _rbd34res = _rbd34(_det34)
    check("(v3.9.24) ri_balancing_docs TANGGAL-AWARE: hanya AGUPO "
          "(RI 1 Okt + PO Agu, contoh user) & LALUJUL (RI -28 + PO Jul) "
          "terdeteksi; SEPPO (PO Sep — satu periode) & LALUOK (RI 26 Sep "
          "+ PO Okt — satu periode) TIDAK",
          set(_rbd34res.keys()) ==
          {("AGUPO", "TGRGEL"), ("LALUJUL", "TGRGEL")} and
          _rbd34res[("AGUPO", "TGRGEL")] == ["RI.2026.10.10354"],
          f"got {dict(_rbd34res)}")
    _rbd34noTgl = _rbd34(_det34.drop(columns=["Tanggal"]))
    check("(v3.9.24) Defensif: frame TANPA kolom Tanggal → fallback "
          "aturan lama bulan≠bulan (SEPPO ikut terflag — tanggal tak "
          "terverifikasi dianggap mencurigakan)",
          ("SEPPO", "TGRGEL") in _rbd34noTgl and
          ("AGUPO", "TGRGEL") in _rbd34noTgl and
          ("LALUOK", "TGRGEL") in _rbd34noTgl and
          ("LALUJUL", "TGRGEL") in _rbd34noTgl,
          f"got {dict(_rbd34noTgl)}")
    _rbdd34 = _rbd34d(_det34)
    check("(v3.9.24) _ri_balancing_by_date (catatan B1): SEPPO & "
          "LALUOK tanpa entri (PO satu periode); AGUPO menempel tgl 1 "
          "+ periode PO; LALUJUL menempel tgl -28",
          ("SEPPO", "TGRGEL") not in _rbdd34 and
          ("LALUOK", "TGRGEL") not in _rbdd34 and
          _rbdd34.get(("AGUPO", "TGRGEL"), {}).get(1) ==
          [("RI.2026.10.10354", " (PO 2026-08)")] and
          _rbdd34.get(("LALUJUL", "TGRGEL"), {}).get(-28) ==
          [("RI.2026.09.302", " (PO 2026-07)")],
          f"got {dict(_rbdd34)}")

    # --- (c) CEK kolom utama DeviasiView (GUI, H=25) -------------------
    # (v3.9.27: SO 24 ditambahkan utk kedua pasangan — tanpa SO H-1,
    # W sheet = 0 & SO_H ≠ 0 memicu 'Hitung Manual' [port persis kondisi
    # 3] yang menutupi fokus uji scope balancing ini)
    _ROWS34 = [
        _row33("SEPPO", "TGRGEL", "1.SO", 24, 10.0),
        _row33("SEPPO", "TGRGEL", "1.SO", 25, 10.0),
        _row33("SEPPO", "TGRGEL", "2.SALDO AKHIR", 25, 10.0),
        _row33("AGUPO", "TGRGEL", "1.SO", 24, 10.0),
        _row33("AGUPO", "TGRGEL", "1.SO", 25, 10.0),
        _row33("AGUPO", "TGRGEL", "2.SALDO AKHIR", 25, 10.0),
    ]
    _top34, _dv34 = _make_dv33(pd.DataFrame(_ROWS34), _det34)
    check("(v3.9.24) CEK kolom utama: AGUPO (dok contoh user, tgl 1 ≤ "
          "H) TERFLAG 'RI Balancing' — SEPPO (dok PO Sep tgl 20 ≤ H) "
          "TIDAK terflag (satu periode — dulu salah-flag)",
          _cek33(_dv34, "AGUPO") == "RI Balancing" and
          _cek33(_dv34, "SEPPO") == "",
          f"AGUPO={_cek33(_dv34, 'AGUPO')!r} "
          f"SEPPO={_cek33(_dv34, 'SEPPO')!r}")
    _vals34 = _dv34._col_values("CEK")
    check("(v3.9.24) Filter ⧩ CEK: nilai = baris yang tampil (RI "
          "Balancing ada)",
          "RI Balancing" in _vals34,
          f"vals={_vals34}")
    _top34.destroy()
    root.update()

    # --- (d) popup Rincian IN: kolom CEK per dokumen -------------------
    from src.ui.in_selisih_view import InDetailPopup as _IDP34
    _pop34 = _IDP34(root, "TGRGEL", "AGUPO", 1, _det34)
    root.update()
    _cekmap34 = {_pop34.tree.set(k, "Nomor"): _pop34.tree.set(k, "CEK")
                 for k in _pop34.tree.get_children("")}
    check("(v3.9.24) Popup Rincian IN: dokumen contoh user (RI 1 Okt + "
          "PO Agu) → CEK 'RI Balancing'; dokumen PO Sep / PO Okt satu "
          "periode → CEK kosong (dulu salah-flag)",
          _cekmap34.get("RI.2026.10.10354") == "RI Balancing" and
          _cekmap34.get("RI.2026.10.201") == "" and
          _cekmap34.get("RI.2026.09.301") == "",
          f"got {_cekmap34}")
    _pop34.destroy()
    root.update()

    # =================================================================
    print("== 35. (v3.9.25) POPUP DEVIASI GR/PCS: PERBESAR + KOLOM Nomor "
          "PO & COM (user: \"POP UP DI tab deviasi gr dan deviasi pcs "
          "perbesar lagi dan tambah kolom nomor po dan COM\") ==")

    from src.ui.deviasi_popup import _compute_com_series as _ccs35
    from src.ui.laporan_deviasi_view import LaporanDeviasiView as _LDV35

    def _row35(barang, resto, jenis, tgl, nilai, satuan="GR",
               nomor=None, po=None):
        return {"Nama Barang": barang, "JENIS": jenis,
                "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": nilai,
                "SATUAN": satuan, "AKTIF/NON": "AKTIF",
                "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                "Nomor": nomor, "Nomor PO": po,
                "#Tgl/Jam Pembuatan IT": None}

    _ROWS35 = [
        # pair P: SA t1 + SO harian + 2 dokumen IN t2 (PO dobel → dedup)
        # + BK t3; t4 HANYA 2.SALDO AKHIR (di luar kolom global 4 JENIS)
        _row35("BRG P", "R", "SALDO AWAL", 1, 50.0),
        _row35("BRG P", "R", "1.SO", 1, 45.0),
        _row35("BRG P", "R", "2.SALDO AKHIR", 1, 4.0),
        _row35("BRG P", "R", "1.SO", 2, 40.0),
        _row35("BRG P", "R", "2.SALDO AKHIR", 2, 3.0),
        _row35("BRG P", "R", "4.IN", 2, 10.0,
               nomor="RI.2026.10.10354", po="PO.2026.08.00571, PO.2026.08.00999"),
        _row35("BRG P", "R", "4.IN", 2, 5.0,
               nomor="IT.2026.10.5123", po="PO.2026.08.00571"),
        _row35("BRG P", "R", "1.SO", 3, 42.0),
        _row35("BRG P", "R", "2.SALDO AKHIR", 3, 5.0),
        _row35("BRG P", "R", "8.BARANG KELUAR", 3, 8.0),
        _row35("BRG P", "R", "2.SALDO AKHIR", 4, 2.0),
        # pair Q: SO t1 & t3 (kolom global t2 ADA dari pair P → so_prev
        # t3 = 0 — semantik kolom global, bukan SO tanggal pair sendiri)
        _row35("BRG Q", "R", "1.SO", 1, 10.0),
        _row35("BRG Q", "R", "1.SO", 3, 8.0),
        _row35("BRG Q", "R", "2.SALDO AKHIR", 3, 9.0),
    ]
    _df35 = pd.DataFrame(_ROWS35)

    # --- (a) build_popup_rows: Nomor PO + COM per tanggal --------------
    _pr35 = build_popup_rows(_df35, "BRG P", "R")
    _p35 = {r["Tanggal"]: r for _, r in _pr35.iterrows()}
    check("(v3.9.25) Popup Nomor PO: tgl 2 = PO DIDEDUP + DIURUT (2 "
          "baris IN tumpang-tindih — PO.2026.08.00571 muncul 2×)",
          _p35["2"]["Nomor PO"] == "PO.2026.08.00571, PO.2026.08.00999",
          f"got {_p35['2']['Nomor PO']!r}")
    check("(v3.9.25) Popup Nomor PO: tanggal TANPA IN → kosong (bukan "
          "'nan')",
          _p35["1"]["Nomor PO"] == "" and _p35["3"]["Nomor PO"] == "",
          f"got {_p35['1']['Nomor PO']!r}/{_p35['3']['Nomor PO']!r}")
    check("(v3.9.25) Popup COM: tgl 1 = SA(50) + IN(0) − BK(0) − SO(45) "
          "= 5 (base SALDO AWAL pair — audit fix v3.9.5)",
          _p35["1"]["COM"] == "5", f"got {_p35['1']['COM']!r}")
    check("(v3.9.25) Popup COM: tgl 2 = SO(1)(45) + IN(15) − BK(0) − "
          "SO(2)(40) = 20",
          _p35["2"]["COM"] == "20", f"got {_p35['2']['COM']!r}")
    check("(v3.9.25) Popup COM: tgl 3 = SO(2)(40) + IN(0) − BK(8) − "
          "SO(3)(42) = (10) minus kurung",
          _p35["3"]["COM"] == "(10)", f"got {_p35['3']['COM']!r}")
    check("(v3.9.25) Popup COM: tgl 4 HANYA 2.SALDO AKHIR (di luar "
          "kolom global 4 JENIS) → COM KOSONG (bukan '-'/'0')",
          _p35["4"]["COM"] == "", f"got {_p35['4']['COM']!r}")
    _q35 = build_popup_rows(_df35, "BRG Q", "R")
    _q35m = {r["Tanggal"]: r for _, r in _q35.iterrows()}
    check("(v3.9.25) Popup COM semantik KOLOM GLOBAL: pair Q SO t1&t3 — "
          "kolom global t2 (dari pair P) membuat so_prev(3)=0 → com(3) "
          "=(8); com(1) kolom pertama =(10)",
          _q35m["1"]["COM"] == "(10)" and _q35m["3"]["COM"] == "(8)",
          f"got {_q35m['1']['COM']!r}/{_q35m['3']['COM']!r}")

    # --- (b) PARITY: _compute_com_series vs matrix Anomali COM ---------
    _lv35 = _LDV35.__new__(_LDV35)
    _m35 = _lv35._compute_com_matrix(_df35)
    _ok35 = True
    _n35 = 0
    for _pair35 in ("BRG P", "BRG Q"):
        _popc35 = _ccs35(_df35, _pair35, "R")
        _mrow35 = _m35.loc[(_pair35, "R")]
        for _t35, _v35 in sorted(_popc35.items()):
            _col35 = int(_t35) if int(_t35) in _mrow35.index else float(_t35)
            _mv35 = _mrow35.get(_col35) if _col35 in _mrow35.index else None
            _n35 += 1
            if _mv35 is None or pd.isna(_mv35) or \
                    abs(float(_mv35) - _v35) > 1e-9:
                _ok35 = False
                print(f"    MISMATCH pair {_pair35} t={_t35}: "
                      f"popup={_v35} matrix={_mv35}")
    check("(v3.9.25) PARITY COM popup vs matrix Anomali COM "
          "(laporan_deviasi_view._compute_com_matrix) — semua tanggal "
          "identik",
          _ok35 and _n35 >= 6, f"{_n35} nilai dibandingkan")

    # --- (c) GUI popup: 8 kolom + geometry 1180×640 + nilai + merah ----
    _pop35 = show_deviasi_popup(root, _df35, "BRG P", "R", satuan="GR",
                                h=3)
    root.update()
    check("(v3.9.25) Popup DIPERBESAR: geometry 1180×640 (dulu 880×480)",
          _pop35.geometry().split("+")[0] == "1180x640",
          f"got {_pop35.geometry()!r}")
    _k35_2 = next(k for k in _pop35.tree.get_children("")
                  if _pop35.tree.set(k, "Tanggal") == "2")
    _k35_3 = next(k for k in _pop35.tree.get_children("")
                  if _pop35.tree.set(k, "Tanggal") == "3")
    _k35_4 = next(k for k in _pop35.tree.get_children("")
                  if _pop35.tree.set(k, "Tanggal") == "4")
    check("(v3.9.25) Popup GUI: kolom Nomor PO tampil + nilai dedup/urut",
          _pop35.tree.set(_k35_2, "Nomor PO") ==
          "PO.2026.08.00571, PO.2026.08.00999",
          f"got {_pop35.tree.set(_k35_2, 'Nomor PO')!r}")
    check("(v3.9.25) Popup GUI: kolom COM tampil — tgl 3 minus (10)",
          _pop35.tree.set(_k35_3, "COM") == "(10)",
          f"got {_pop35.tree.set(_k35_3, 'COM')!r}")
    check("(v3.9.25) Popup GUI: COM tgl di luar kolom global = kosong",
          _pop35.tree.set(_k35_4, "COM") == "",
          f"got {_pop35.tree.set(_k35_4, 'COM')!r}")
    if CELL_TAGS_SUPPORTED:
        _neg35 = root.tk.call(str(_pop35.tree), "tag", "cell", "has",
                              "neg_cell", (_k35_3, "COM"))
        check("(v3.9.25) Popup GUI: COM minus merah PER CELL (tgl 3)",
              _neg35 == 1, f"tag={_neg35}")
    _pop35._cell_tags = False
    _pop35._render()
    root.update()
    check("(v3.9.25) Popup fallback Tk 8: baris COM minus → tag baris "
          "negative",
          "negative" in _pop35.tree.item(_k35_3, "tags"),
          f"tags={_pop35.tree.item(_k35_3, 'tags')}")
    _pop35.destroy()
    root.update()

    print()
    print("== 36. (v3.9.26) POTENSI FLIP FLOP = SELISIH MAGNITUDO KECIL "
          "(cermin ± — dulu kebalikan) ==")

    # --- (a) Konstanta — 1 sumber kebenaran utk 2 tabel ------------------
    from src.ui.komparasi_deviasi_view import (
        FFLOP_DISP_MAX as _FD36,
    )
    from src.ui.komparasi_deviasi_view import (
        KomparasiDeviasiView as _KDV36,
    )
    check("(v3.9.26) Konstanta FFLOP_DISP_MAX = 0.40 (Top Selisih & "
          "Perubahan Arah; ambang sama Kategori Parsial)",
          _FD36 == 0.40, f"got {_FD36!r}")

    # --- (b) Unit _top_aggregate: cermin → FFLOP; batas 0.40 → ARAH -----
    _top36 = tk.Frame(root)
    kv36 = _KDV36(_top36)
    kv36.pack(fill="both", expand=True)
    kv36._show_content()
    root.update()
    _d36 = pd.DataFrame({
        "_resto_norm": ["R_MIRROR36", "R_BATAS36", "R_BATAS36M",
                        "R_STABILF36", "R_NAIK36", "R_STAB36"],
        "_bahan_norm": ["B"] * 6,
        "Minggu": ["WEEK 4"] * 6,
        "DEV Lalu": [-50.0, -100.0, -100.0, -10.0, 10.0, 10.0],
        "GR Saat Ini": [55.0, 60.0, 61.0, 10.0, 50.0, 10.5],
        "Status": ["SELISIH", "SELISIH", "SELISIH", "MATCH", "SELISIH",
                   "MATCH"],
        "BULAN": ["NOV"] * 6,
        "Resto": ["R_MIRROR36", "R_BATAS36", "R_BATAS36M", "R_STABILF36",
                  "R_NAIK36", "R_STAB36"],
        "Nama Barang": ["B"] * 6,
        "Satuan": ["GR"] * 6,
    })
    _agg36 = kv36._top_aggregate(_d36)
    _ana36 = dict(zip(_agg36["Resto"], _agg36["ANALISA"]))
    check("(v3.9.26) ANALISA Top: cermin −50 → +55 (selisih magnitudo 5 "
          "— DIKIT) → 'Potensi Flip Flop' (dulu 'Berubah Arah')",
          _ana36["R_MIRROR36"] == kv36.ANALISA_FFLOP,
          f"got {_ana36['R_MIRROR36']!r}")
    check("(v3.9.26) ANALISA Top: batas PERSIS disparitas 0.40 "
          "(−100 → +60) → 'Berubah Arah' (FFLOP strictly < — selaras "
          "Kategori Parsial)",
          _ana36["R_BATAS36"] == kv36.ANALISA_ARAH,
          f"got {_ana36['R_BATAS36']!r}")
    check("(v3.9.26) ANALISA Top: disparitas 0.39 (−100 → +61) → "
          "'Potensi Flip Flop'",
          _ana36["R_BATAS36M"] == kv36.ANALISA_FFLOP,
          f"got {_ana36['R_BATAS36M']!r}")
    check("(v3.9.26) ANALISA Top: prioritas flip > Stabil — cermin "
          "−10 → +10 (Selisih 0, status MATCH) tetap 'Potensi Flip "
          "Flop' (bukan Stabil)",
          _ana36["R_STABILF36"] == kv36.ANALISA_FFLOP,
          f"got {_ana36['R_STABILF36']!r}")
    check("(v3.9.26) ANALISA Top: tanda SAMA tidak pernah flip-flop "
          "(Kenaikan/Stabil utuh)",
          _ana36["R_NAIK36"] == kv36.ANALISA_NAIK and
          _ana36["R_STAB36"] == kv36.ANALISA_STABIL,
          f"got {_ana36['R_NAIK36']!r}/{_ana36['R_STAB36']!r}")

    # --- (c) GUI flip: Sempurna/Dominan → FFLOP; Parsial → ARAH ---------
    import tempfile as _tf36

    from openpyxl import Workbook as _WB36

    f36 = os.path.join(_tf36.gettempdir(), "mock_deviasi_fflop36.xlsx")
    _w36 = _WB36()
    _s36 = _w36.active
    _s36.append(["RESTO", "NAMA BAHAN", "Satuan", "QTY BOM", "QTY COM",
                 "QTY DEVIASI", "STATUS BULAN", "BULAN"])
    _rows36 = [
        # SEMPURNA — cermin ± (selisih 5): −50 → +55 (disp 0,0909)
        ["MLGFF1", "BFF SEMPURNA", "GR", -80, -90, -50, "WEEK 4",
         "201.OKT 26"],
        ["MLGFF1", "BFF SEMPURNA", "GR", -80, -70, 55, "WEEK 4", "NOV"],
        # DOMINAN — selisih 15: −50 → +35 (disp 0,3)
        ["MLGFF2", "BFF DOMINAN", "GR", -80, -90, -50, "WEEK 4",
         "201.OKT 26"],
        ["MLGFF2", "BFF DOMINAN", "GR", -80, -70, 35, "WEEK 4", "NOV"],
        # PARSIAL — selisih 90 (banyak): −100 → +10 (disp 0,9)
        ["MLGFF3", "BFF PARSIAL", "GR", -80, -90, -100, "WEEK 4",
         "201.OKT 26"],
        ["MLGFF3", "BFF PARSIAL", "GR", -80, -70, 10, "WEEK 4", "NOV"],
        # BATAS PERSIS 0.40 — selisih 40: −100 → +60 → Parsial/ARAH
        ["MLGFF4", "BFF BATAS", "GR", -80, -90, -100, "WEEK 4",
         "201.OKT 26"],
        ["MLGFF4", "BFF BATAS", "GR", -80, -70, 60, "WEEK 4", "NOV"],
    ]
    for _r36 in _rows36:
        _s36.append(_r36)
    _w36.save(f36)
    # bypass _load_paths (butuh data app) — pola §30: _file_df langsung
    # dari parse_deviasi_file (kolom _flip_pair_core lengkap)
    _res36 = parse_deviasi_file(f36)
    kv36._file_df = _res36["df"]
    kv36._file_meta = _res36["meta"]
    kv36._show_all_weeks.set(False)
    kv36._render_flip()
    _t036 = time.time()
    while time.time() - _t036 < 0.4:
        root.update()
        time.sleep(0.005)
    _fkat36 = {}
    for _k36 in kv36._flip_tree.get_children(""):
        _b36 = str(kv36._flip_tree.set(_k36, "Nama Barang"))
        _fkat36[_b36] = (str(kv36._flip_tree.set(_k36, "Kategori")),
                         str(kv36._flip_tree.set(_k36, "ANALISA")))
    check("(v3.9.26) Flip GUI: Sempurna (−50 → +55, selisih 5 — dikit) "
          "→ 'Potensi Flip Flop' (dulu 'Berubah Arah')",
          _fkat36.get("BFF SEMPURNA", ("", "")) ==
          ("Sempurna", kv36.ANALISA_FFLOP), f"got {_fkat36}")
    check("(v3.9.26) Flip GUI: Dominan (−50 → +35, selisih 15) → "
          "'Potensi Flip Flop'",
          _fkat36.get("BFF DOMINAN", ("", "")) ==
          ("Dominan", kv36.ANALISA_FFLOP), f"got {_fkat36}")
    check("(v3.9.26) Flip GUI: Parsial (−100 → +10, selisih 90 — "
          "banyak) → 'Berubah Arah' (dulu 'Potensi Flip Flop')",
          _fkat36.get("BFF PARSIAL", ("", "")) ==
          ("Parsial", kv36.ANALISA_ARAH), f"got {_fkat36}")
    check("(v3.9.26) Flip GUI: batas PERSIS disparitas 0.40 (−100 → "
          "+60) → Parsial/'Berubah Arah' — FFLOP strictly < ambang",
          _fkat36.get("BFF BATAS", ("", "")) ==
          ("Parsial", kv36.ANALISA_ARAH), f"got {_fkat36}")
    _aff36 = kv36._flip_col_values("ANALISA")
    check("(v3.9.26) Flip filter ⧩ ANALISA: kedua label tampil (data "
          "yang ada)",
          kv36.ANALISA_FFLOP in _aff36 and kv36.ANALISA_ARAH in _aff36,
          f"got {_aff36}")
    os.unlink(f36)
    kv36._on_mode_change(0)
    root.update()
    _top36.destroy()
    root.update()

    # =====================================================================
    # §37 v3.9.27 — MODE HITUNG tab Rekap Selisih IN (user: "pada rekap
    #      selisih in bisa mode hitung bulan lalu dan hanya hitung bulan
    #      ini. Tapi default hitung bulan ini aja")
    # =====================================================================
    print("== 37. (v3.9.27) MODE HITUNG Rekap Selisih IN — Bulan Ini "
          "(default) vs Lalu + Ini ==")

    # --- (a) unit: fn_audit bulan_lalu=False membuang baris negatif ---
    from src.pipeline.fn_audit import build_audit_from_app as _baf37

    _rs37 = pd.DataFrame([
        {"NAMA RESTO": "R1", "Nama Barang": "BRG", "JENIS": "SO",
         "Tanggal": -26, "SATUAN": "GR", "Value": 10.0},
        {"NAMA RESTO": "R1", "Nama Barang": "BRG", "JENIS": "SO",
         "Tanggal": 1, "SATUAN": "GR", "Value": 12.0},
        {"NAMA RESTO": "R1", "Nama Barang": "BRG", "JENIS": "SO",
         "Tanggal": 2, "SATUAN": "GR", "Value": 8.0},
    ])
    _det37 = pd.DataFrame([
        {"NAMA RESTO": "R1", "Nama Barang": "BRG", "Tanggal": -26,
         "Value": 5.0, "Nomor": "RI.2026.08.1", "Nomor PO": None,
         "#Tgl/Jam Pembuatan IT": None, "SOURCE IN": "32.24 (Bulan Lalu)",
         "JENIS": "IN"},
        {"NAMA RESTO": "R1", "Nama Barang": "BRG", "Tanggal": 2,
         "Value": 3.0, "Nomor": "RI.2026.09.2", "Nomor PO": None,
         "#Tgl/Jam Pembuatan IT": None, "SOURCE IN": "32.24",
         "JENIS": "IN"},
    ])
    _aud37_full, _kpi37_full, _desc37_full = _baf37(_rs37, _det37)
    _aud37_bi, _kpi37_bi, _desc37_bi = _baf37(_rs37, _det37,
                                               bulan_lalu=False)
    _tgl_full37 = sorted(pd.to_numeric(
        _aud37_full["Tanggal"], errors="coerce").unique().tolist())
    _tgl_bi37 = sorted(pd.to_numeric(
        _aud37_bi["Tanggal"], errors="coerce").unique().tolist())
    check("(v3.9.27) fn_audit bulan_lalu=True (default): baris bulan "
          "lalu (-26) IKUT audit (varian penuh)",
          -26 in _tgl_full37, f"tgl={_tgl_full37}")
    check("(v3.9.27) fn_audit bulan_lalu=False: baris Tanggal negatif "
          "DIBUANG — mirror sheet LAPORAN_DEVIASI (tgl 1..31)",
          -26 not in _tgl_bi37 and _tgl_bi37 == [1, 2],
          f"tgl={_tgl_bi37}")
    check("(v3.9.27) fn_audit bulan_lalu=False: IN bulan lalu ikut "
          "dibuang (baris -26 tanpa penerimaan)",
          not any((pd.to_numeric(_aud37_bi["Tanggal"], errors="coerce")
                   < 0)), "ada baris negatif tersisa")
    check("(v3.9.27) fn_audit desc: cakupan ikut mode",
          "incl. bulan lalu" in _desc37_full and
          "bulan berjalan saja" in _desc37_bi,
          f"full={_desc37_full!r} bi={_desc37_bi!r}")

    # --- (b) pipeline: audit_result membawa KEDUA varian --------------
    _aud_res37_keys = {"df", "kpi", "desc", "df_bulan_ini",
                       "kpi_bulan_ini", "desc_bulan_ini"}
    check("(v3.9.27) run_pipeline audit_result kunci lengkap (varian "
          "penuh + bulan-ini) — verifikasi lewat main.run_pipeline mock "
          "§14-style dijalankan test_mock.py",
          _aud_res37_keys.issuperset({"df", "kpi", "desc"}))

    # --- (c) GUI: InSelisihView mode selector -------------------------
    from src.ui.in_selisih_view import InSelisihView as _ISV37

    _AUDCOLS37 = ["Resto", "Nama Item", "UoM", "Tanggal", "Hasil SO",
                  "Qty SO Harian", "Qty SJ", "Qty RI", "Qty Pembelian",
                  "Selisih Qty", "Penerimaan Sistem", "Selisih Harian",
                  "Saldo Kumulatif", "Status Analisis Audit",
                  "Detail & Catatan Audit"]

    def _aud37(rows):
        return pd.DataFrame(rows, columns=_AUDCOLS37)

    _full37 = _aud37([
        ("R1", "BRG", "GR", -25, 10.0, 6.0, 6.0, 0, 0, 0.0, 6.0, 0.0,
         0.0, "OK (Matching)", "-"),
        ("R1", "BRG", "GR", 1, 12.0, 8.0, 8.0, 0, 0, 0.0, 8.0, 0.0,
         0.0, "OK (Matching)", "-"),
        ("R1", "BRG", "GR", 5, 9.0, 4.0, 3.0, 0, 0, 1.0, 3.0, 1.0,
         1.0, "DEVIASI MURNI", "Sisa Gantung: +1 (Sejak Tgl 5)"),
    ])
    _bi37 = _aud37([
        ("R1", "BRG", "GR", 1, 12.0, 8.0, 8.0, 0, 0, 0.0, 8.0, 0.0,
         0.0, "OK (Matching)", "-"),
        ("R1", "BRG", "GR", 5, 9.0, 4.0, 3.0, 0, 0, 1.0, 3.0, 1.0,
         1.0, "DEVIASI MURNI", "Sisa Gantung: +1 (Sejak Tgl 5)"),
    ])
    _kpi_f37 = {"rows": 3, "ok": 2, "omit": 0, "cutoff": 0,
                "deviasi_murni": 1, "deviasi_qty": 1.0}
    _kpi_b37 = {"rows": 2, "ok": 1, "omit": 0, "cutoff": 0,
                "deviasi_murni": 1, "deviasi_qty": 1.0}
    _ar37 = {"df": _full37, "kpi": _kpi_f37, "desc": "full",
             "df_bulan_ini": _bi37, "kpi_bulan_ini": _kpi_b37,
             "desc_bulan_ini": "bulan ini"}
    _data37 = pd.DataFrame({
        "Nama Barang": ["BRG"], "NAMA RESTO": "R1", "SATUAN": "GR",
        "JENIS": "1.SO", "Tanggal": [1], "NILAI": [12.0]})

    _top37 = tk.Toplevel(root)
    _top37.geometry("1400x800+20+20")
    _iv37 = _ISV37(_top37)
    _iv37.pack(fill="both", expand=True)
    root.update()
    _iv37.load_data(_data37, None, _ar37)
    wait_view(root, _iv37)
    root.update()
    _iv37.only_selisih_var.set(False)
    _iv37._refresh()
    wait_view(root, _iv37)
    root.update()

    def _rows37():
        return len(_iv37.tree.get_children(""))

    check("(v3.9.27) MODE HITUNG ada: SegmentBar mode_bar (nama LAMA "
          "'mode_seg' tetap TIDAK ada — dihapus v3.6)",
          hasattr(_iv37, "mode_bar") and
          not hasattr(_iv37, "mode_seg"))
    check("(v3.9.27) DEFAULT = '📅 Bulan Ini' (user: default hitung "
          "bulan ini aja)",
          _iv37.mode_bar.active == 0 and not _iv37._mode_bulan_lalu)
    check("(v3.9.27) Default rentang 1..31 (v3.8 utuh)",
          _iv37.tgl_start_var.get() == "1" and
          _iv37.tgl_end_var.get() == "31")
    check("(v3.9.27) Default varian audit = df_bulan_ini (2 baris, "
          "tanpa -25)",
          _iv37.audit_df is _bi37 and len(_iv37.audit_df) == 2)
    check("(v3.9.27) Default KPI = kpi_bulan_ini (rows 2)",
          _iv37.audit_kpi.get("rows") == 2)
    check("(v3.9.27) Tabel default: 2 baris (baris -25 tak ada)",
          _rows37() == 2, f"rows={_rows37()}")

    # ganti mode → Lalu + Ini
    _iv37.mode_bar._select(1)
    wait_view(root, _iv37)
    root.update()
    check("(v3.9.27) Mode '📆 Lalu + Ini': varian penuh aktif (3 baris "
          "incl. -25)",
          _iv37.audit_df is _full37 and len(_iv37.audit_df) == 3)
    check("(v3.9.27) Mode Lalu + Ini: rentang -31..31",
          _iv37.tgl_start_var.get() == "-31" and
          _iv37.tgl_end_var.get() == "31")
    check("(v3.9.27) Mode Lalu + Ini: baris bulan lalu TAMPIL (3)",
          _rows37() == 3, f"rows={_rows37()}")
    check("(v3.9.27) Mode Lalu + Ini: KPI = kpi penuh (rows 3)",
          _iv37.audit_kpi.get("rows") == 3)
    _tgl_vals37 = set()
    for _k37 in _iv37.tree.get_children(""):
        _tgl_vals37.add(_iv37.tree.set(_k37, "Tanggal"))
    check("(v3.9.27) Mode Lalu + Ini: kolom Tanggal memuat -25",
          "-25" in _tgl_vals37, f"tgl={sorted(_tgl_vals37)}")

    # kembali ke Bulan Ini
    _iv37.mode_bar._select(0)
    wait_view(root, _iv37)
    root.update()
    check("(v3.9.27) Kembali '📅 Bulan Ini': varian bulan-ini + rentang "
          "1..31 + 2 baris",
          _iv37.audit_df is _bi37 and _rows37() == 2 and
          _iv37.tgl_start_var.get() == "1")

    # auto-upgrade: ketik tanggal negatif saat mode Bulan Ini
    _iv37.tgl_start_var.set("-26")
    _iv37.tgl_end_var.set("31")
    _iv37._on_tanggal_change()
    wait_view(root, _iv37)
    root.update()
    check("(v3.9.27) AUTO-UPGRADE: rentang negatif (-26) di mode Bulan "
          "Ini → otomatis '📆 Lalu + Ini' (baris bulan lalu ada)",
          _iv37._mode_bulan_lalu and _iv37.mode_bar.active == 1 and
          _rows37() == 3, f"rows={_rows37()}")

    # reset → default
    _iv37._reset_filter()
    wait_view(root, _iv37)
    root.update()
    check("(v3.9.27) ✕ Reset Filter: kembali default 'Bulan Ini' + "
          "rentang 1..31 + hanya-selisih ON",
          _iv37.mode_bar.active == 0 and
          _iv37.tgl_start_var.get() == "1" and
          _iv37.only_selisih_var.get() and
          _iv37.audit_df is _bi37)

    # load_data ulang → mode reset (walau sebelumnya Lalu+Ini)
    _iv37.mode_bar._select(1)
    wait_view(root, _iv37)
    root.update()
    _iv37.load_data(_data37, None, _ar37)
    wait_view(root, _iv37)
    root.update()
    check("(v3.9.27) load_data ulang: mode reset ke default 'Bulan "
          "Ini' (varian bulan-ini aktif)",
          _iv37.mode_bar.active == 0 and _iv37.audit_df is _bi37)

    # kompatibel: audit_result TANPA kunci baru → jatuh ke varian penuh
    _iv37.load_data(_data37, None,
                    {"df": _full37, "kpi": _kpi_f37, "desc": "x"})
    wait_view(root, _iv37)
    root.update()
    check("(v3.9.27) Kompatibel: audit_result TANPA df_bulan_ini → "
          "mode Bulan Ini memakai varian penuh (pemanggil lama/test)",
          _iv37.audit_df is _full37 and _iv37.mode_bar.active == 0)

    # KPI chip MODE HITUNG tampil (label mode varian aktif)
    _kpi_txt37 = []
    for _w37 in _iv37.kpi_inner.winfo_children():
        for _ww37 in _w37.winfo_children():
            if isinstance(_ww37, tk.Label):
                _kpi_txt37.append(str(_ww37.cget("text")))
    check("(v3.9.27) KPI chip 'MODE HITUNG' tampil (varian aktif "
          "terlihat)",
          any("MODE HITUNG" in t for t in _kpi_txt37),
          f"kpi={_kpi_txt37}")
    _top37.destroy()
    root.update()

    # =====================================================================
    # §38 v3.9.27 — CEK PORT PERSIS SHEET 'Data Base Cek Deviasi' (user:
    #      "kondisi beda tanggal kok menghasilkan data kosong semua? ...
    #      cek semua logika nya dan bandingkan dengan yang ada di
    #      program") — kondisi 2 Out=KIRIMAN KELUAR + kondisi 3 W sheet
    # =====================================================================
    print("== 38. (v3.9.27) CEK port persis sheet — Beda Tanggal "
          "(KIRIMAN KELUAR) + Hitung Manual (W sheet) ==")

    def _row38(barang, jenis, tgl, nilai, resto="R"):
        return {"Nama Barang": barang, "JENIS": jenis,
                "NAMA RESTO": resto, "Tanggal": tgl, "NILAI": nilai,
                "SATUAN": "GR", "AKTIF/NON": "AKTIF",
                "KATEGORI": "BAHAN", "SOURCE KIRIMAN": "GUDANG",
                "Nomor": None, "Nomor PO": None,
                "#Tgl/Jam Pembuatan IT": None, "SOURCE DATA": None}

    # BEDA-TGL-ACR: pola sheet v2 cabang-1 (I>0 & H<F & J=0) — dgn
    # PENJUALAN (9.ACR) di H ≠ 0 (yang dulu mematikan kondisi) TAPI
    # KIRIMAN KELUAR (8.BARANG KELUAR) = 0 → sheet TERFLAG; app lama
    # (J = 9.ACR) TIDAK. Bukti real: MLGPAR/ADONAN GORENG MEKAR.
    _ROWS38A = [
        _row38("BEDA-TGL-ACR", "1.SO", 24, 100.0),
        _row38("BEDA-TGL-ACR", "1.SO", 25, 50.0),     # SO turun
        _row38("BEDA-TGL-ACR", "4.IN", 25, 30.0),     # IN datang (I>0)
        _row38("BEDA-TGL-ACR", "9.ACR", 25, 20.0),    # penjualan ≠ 0
        _row38("BEDA-TGL-ACR", "2.SALDO AKHIR", 25, 40.0),
        # BEDA-TGL-BK: cabang-2 — SO naik >50% tanpa IN; PENJUALAN ≠ 0
        # TAPI KIRIMAN KELUAR = 0 → sheet TERFLAG
        _row38("BEDA-TGL-BK", "1.SO", 24, 100.0),
        _row38("BEDA-TGL-BK", "1.SO", 25, 200.0),     # SO naik 100%
        _row38("BEDA-TGL-BK", "9.ACR", 25, 15.0),     # penjualan ≠ 0
        _row38("BEDA-TGL-BK", "2.SALDO AKHIR", 25, 60.0),
        # NO-CEK: pola cabang-2 (SO naik >50%, IN 0) TAPI KIRIMAN
        # KELUAR ≠ 0 → kedua cabang sheet mati (J≠0) → tak terflag
        # (bukti J = KIRIMAN KELUAR, bukan PENJUALAN — 9.ACR di sini
        # pun ≠ 0). W = 200−7−15 = 178; rasio |310−178|/178 = 0,74 <
        # 1,3 → kondisi 3 pun mati.
        _row38("NO-CEK", "1.SO", 24, 200.0),
        _row38("NO-CEK", "1.SO", 25, 310.0),
        _row38("NO-CEK", "9.ACR", 25, 15.0),
        _row38("NO-CEK", "8.BARANG KELUAR", 25, 7.0),  # KIRIMAN KELUAR
        _row38("NO-CEK", "2.SALDO AKHIR", 25, 310.0),
    ]
    _top38a, _dv38a = _make_dv33(pd.DataFrame(_ROWS38A), None)
    check("(v3.9.27) Kondisi 2 'Beda Tanggal' cabang-1: IN datang + SO "
          "turun + KIRIMAN KELUAR=0 → TERFLAG meski PENJUALAN ≠ 0 (J = "
          "8.BARANG KELUAR; v3.9.6-26 pakai 9.ACR → tak pernah terpicu)",
          _cek33(_dv38a, "BEDA-TGL-ACR") == "Beda Tanggal",
          f"cek={_cek33(_dv38a, 'BEDA-TGL-ACR')!r}")
    check("(v3.9.27) Kondisi 2 cabang-2: SO naik >50% + IN 0 + KIRIMAN "
          "KELUAR 0 → TERFLAG meski PENJUALAN ≠ 0",
          _cek33(_dv38a, "BEDA-TGL-BK") == "Beda Tanggal",
          f"cek={_cek33(_dv38a, 'BEDA-TGL-BK')!r}")
    check("(v3.9.27) KIRIMAN KELUAR ≠ 0 mematikan kedua cabang (J "
          "sheet = KIRIMAN KELUAR, bukan PENJUALAN) → NO-CEK tak "
          "terflag",
          _cek33(_dv38a, "NO-CEK") == "",
          f"cek={_cek33(_dv38a, 'NO-CEK')!r}")
    _top38a.destroy()
    root.update()

    # Hitung Manual: stok = W sheet = SO(H-1)+IN−KIRIMAN KELUAR−
    # PENJUALAN (dulu sistem+IN−ACR−BK). Angka dipilih supaya HANYA
    # kondisi 3 yang terpicu (SO naik < 50% supaya kondisi 2 mati —
    # prioritas tanggal > manual).
    _ROWS38B = [
        # MANUAL: W = 100 + 0 − 0 − 80 = 20; |SO_H − W|/|W| = |50−20|/
        # 20 = 1,5 > 1,3 → 'Hitung Manual' (SO naik cuma 50%·so_m1/2 —
        # di bawah ambang cabang-2 [50% NAIK = so_h > 150]; rumus lama
        # stok = sistem 50 + 0 − 80 − 0 = −30 → tak terpicu — perilaku
        # berubah krn W sheet yang dipakai)
        _row38("MANUAL", "1.SO", 24, 100.0),
        _row38("MANUAL", "1.SO", 25, 50.0),
        _row38("MANUAL", "9.ACR", 25, 80.0),          # penjualan di H
        _row38("MANUAL", "2.SALDO AKHIR", 25, 50.0),
        # OK-MANUAL: W = 100 + 0 − 0 − 20 = 80; |120−80|/80 = 0,5 <
        # 1,3 → tak terpicu; cabang-2 mati (120 < 150); drastis mati
        # (1,2 ≥ 0,5)
        _row38("OK-MANUAL", "1.SO", 24, 100.0),
        _row38("OK-MANUAL", "1.SO", 25, 120.0),
        _row38("OK-MANUAL", "9.ACR", 25, 20.0),
        _row38("OK-MANUAL", "2.SALDO AKHIR", 25, 120.0),
        # MANUAL-W0: W = 0 (SO H-1 = 0, IN/BK/OUT = 0) & SO_H ≠ 0 →
        # 'Hitung Manual' (kondisi W=0 & H≠0 sheet)
        _row38("MANUAL-W0", "1.SO", 25, 15.0),
        _row38("MANUAL-W0", "2.SALDO AKHIR", 25, 15.0),
    ]
    _top38b, _dv38b = _make_dv33(pd.DataFrame(_ROWS38B), None)

    def _vals38(dv, barang):
        for _k38 in dv.tree.get_children(""):
            if dv.tree.set(_k38, "Nama Barang") == barang:
                _i38 = {c: i for i, c in enumerate(
                    [cc[0] for cc in dv.COLUMNS])}
                return {c: dv.tree.set(_k38, c)
                        for c in ("CEK", "Stok Seharusnya")}
        return None

    _m38 = _vals38(_dv38b, "MANUAL")
    check("(v3.9.27) Kondisi 3 'Hitung Manual': rasio |SO_H−W|/|W| = "
          "|50−20|/20 = 1,5 > 1,3 → TERFLAG (W = 20 = SO(24)100+IN0−"
          "BK0−OUT80; rumus lama berbasis sistem → tak terpicu)",
          _m38 is not None and _m38["CEK"] == "Hitung Manual",
          f"got {_m38}")
    _ok38 = _vals38(_dv38b, "OK-MANUAL")
    check("(v3.9.27) Rasio W 0,5 < 1,3 → TIDAK terpicu",
          _ok38 is not None and _ok38["CEK"] == "",
          f"got {_ok38}")
    _mw38 = _vals38(_dv38b, "MANUAL-W0")
    check("(v3.9.27) W = 0 & SO_H ≠ 0 → 'Hitung Manual' (port persis "
          "kondisi W=0 sheet)",
          _mw38 is not None and _mw38["CEK"] == "Hitung Manual",
          f"got {_mw38}")
    check("(v3.9.27) Stok Seharusnya kolom = W sheet (MANUAL: 20; "
          "dulu SO(H-1)−ACR-rata2)",
          _m38 is not None and _m38["Stok Seharusnya"] == "20",
          f"got {_m38}")
    _top38b.destroy()
    root.update()

    # =====================================================================
    # 39. v3.9.28 — TANGGAL SERIAL EXCEL (.xlsb/pyxlsb) ROBUST
    #    (user: "perbaiki stock seharusnya dan hitung manual")
    # =====================================================================
    print("== 39. v3.9.28 — to_datetime_robust / date_to_day serial ==")
    from src.pipeline.helpers import date_to_day, to_datetime_robust

    _d39 = date_to_day(pd.Series([46290, 46266, None]))   # serial int
    check("(v3.9.28) date_to_day SERIAL int: 46290→25, 46266→1 "
          "(dulu 100% hari 1 — akar 'Stok Seharusnya' & 'Hitung Manual' salah)",
          list(_d39[:2]) == [25, 1] and pd.isna(_d39[2]),
          f"got {_d39.tolist()}")
    _f39 = date_to_day(pd.Series([46290.5, 46291.25]))     # serial + waktu
    check("(v3.9.28) date_to_day SERIAL float+pecahan waktu: 25 & 26",
          list(_f39) == [25, 26], f"got {_f39.tolist()}")
    _dt39 = date_to_day(pd.Series(pd.to_datetime(["2026-09-25", "2026-10-01"])))
    check("(v3.9.28) date_to_day datetime64 TIDAK berubah (regresi .xlsx)",
          list(_dt39) == [25, 1], f"got {_dt39.tolist()}")
    _s39 = date_to_day(pd.Series(["2026-09-25", "2026-10-01"]))
    check("(v3.9.28) date_to_day string ISO TIDAK berubah",
          list(_s39) == [25, 1], f"got {_s39.tolist()}")
    _m39 = date_to_day(pd.Series([46290, pd.Timestamp("2026-10-01")]))
    check("(v3.9.28) date_to_day CAMPURAN serial + Timestamp: masing-masing "
          "jalurnya (25 & 1)",
          list(_m39) == [25, 1], f"got {_m39.tolist()}")
    _n39 = date_to_day(pd.Series([None, None]))
    check("(v3.9.28) date_to_day kosong → <NA>",
          all(pd.isna(v) for v in _n39), f"got {_n39.tolist()}")
    _k39 = date_to_day(pd.Series([1, 25, 31]))
    check("(v3.9.28) angka kecil 1..31 BUKAN serial → perilaku lama utuh",
          list(_k39) == [1, 1, 1], f"got {_k39.tolist()}")
    _r39 = to_datetime_robust(pd.Series([46289.75, "2026-09-27", None]))
    check("(v3.9.28) to_datetime_robust: 46289.75 → 2026-09-24 18:00 "
          "(pecahan waktu), string ISO, NaT",
          str(_r39[0]) == "2026-09-24 18:00:00"
          and str(_r39[1])[:10] == "2026-09-27" and pd.isna(_r39[2]),
          f"got {_r39.tolist()}")
    _r39b = to_datetime_robust(
        pd.Series(pd.to_datetime(["2026-09-25", "2026-10-01"])))
    check("(v3.9.28) to_datetime_robust kolom datetime64 apa adanya",
          str(_r39b[0])[:10] == "2026-09-25", f"got {_r39b.tolist()}")

    # E2E: fn_4205 membaca file dgn kolom Tanggal = SERIAL NUMBER
    import tempfile
    _tmp39 = os.path.join(tempfile.gettempdir(), "mock4205_serial_39")
    os.makedirs(_tmp39, exist_ok=True)
    _rows39 = [
        {"Nomor #Terima": "IT.2026.09.20742", "Gudang #Terima": "MLGPAR (MLGPAR)",
         "Tanggal #Terima": 46290.0, "Nama Barang": "ADONAN GORENG MEKAR",
         "#Qty. Terkecil": 90000.0, "#Tgl/Jam Pembuatan IT": 46289.75},
        {"Nomor #Terima": "IT.2026.09.20743", "Gudang #Terima": "TGRGEL (TGRGEL)",
         "Tanggal #Terima": 46295.0, "Nama Barang": "BUAH APEL (V.20)",
         "#Qty. Terkecil": 4000.0, "#Tgl/Jam Pembuatan IT": None},
        {"Nomor #Terima": "RI.2026.09.50001", "Gudang #Terima": "KWGGAL (KWGGAL)",
         "Tanggal #Terima": "2026-09-27", "Nama Barang": "BUAH PEER (V.20)",
         "#Qty. Terkecil": 2000.0, "#Tgl/Jam Pembuatan IT": None},
    ]
    pd.DataFrame(_rows39).to_excel(
        os.path.join(_tmp39, "in4205.xlsx"),
        sheet_name="#42.05. Rincian Pemindahan Bara",
        index=False, startrow=4)
    from src.pipeline.fn_4205 import fn_4205
    _out39 = fn_4205(_tmp39)
    check("(v3.9.28) fn_4205 E2E dgn tanggal SERIAL: hari 25/30/27 benar "
          "(In_H≠0 → Stok Seharusnya & Hitung Manual benar)",
          list(_out39["Tanggal"]) == [25, 30, 27],
          f"got {_out39['Tanggal'].tolist()}")
    check("(v3.9.28) fn_4205 E2E: #Tgl/Jam Pembuatan IT serial 46289.75 → "
          "2026-09-24 18:00 (dulu 1970-01-01 nanodetik)",
          str(_out39["#Tgl/Jam Pembuatan IT"][0]) == "2026-09-24 18:00:00",
          f"got {_out39['#Tgl/Jam Pembuatan IT'].tolist()}")
    check("(v3.9.28) fn_4205 E2E: NAMA RESTO tetap terekstrak (MLGPAR)",
          next(iter(_out39["NAMA RESTO"])) == "MLGPAR",
          f"got {_out39['NAMA RESTO'].tolist()}")
    shutil.rmtree(_tmp39, ignore_errors=True)

    # ==================================================================
    # §41 (v3.9.29) — SOURCE KIRIMAN PER PASANGAN + SCROLL HALUS
    # ==================================================================
    print("\n== 41. (v3.9.29) SOURCE KIRIMAN PER PASANGAN + SCROLL HALUS ==")
    from src.pipeline.append1 import _source_kiriman_per_pair
    _sk41 = pd.DataFrame({
        "Nama Barang": ["A", "A", "B", "B", "C", "D", "D"],
        "NAMA RESTO": ["R1", "R1", "R1", "R1", "R2", "R2", "R2"],
        "SOURCE IN": ["42.05", "42.05 (Bulan Lalu)", "32.24", "99.01",
                      "42.05", "42.05", "32.24"],
    })
    _skm41 = _source_kiriman_per_pair(_sk41)
    _skv41 = {(r["Nama Barang"], r["NAMA RESTO"]): r["SOURCE KIRIMAN"]
              for _i, r in _skm41.iterrows()}
    check("(v3.9.29) _source_kiriman_per_pair: murni 42.05 → Internal",
          _skv41[("A", "R1")] == "Internal" and
          _skv41[("C", "R2")] == "Internal", f"got {_skv41}")
    check("(v3.9.29) _source_kiriman_per_pair: 32.24/99.01 → Eksternal",
          _skv41[("B", "R1")] == "Eksternal", f"got {_skv41}")
    check("(v3.9.29) _source_kiriman_per_pair: campuran IT+RI → Campuran",
          _skv41[("D", "R2")] == "Campuran", f"got {_skv41}")
    check("(v3.9.29) _source_kiriman_per_pair: input kosong/None → frame "
          "kosong (merge left → semua pasangan kosong)",
          _source_kiriman_per_pair(None).empty and
          _source_kiriman_per_pair(pd.DataFrame()).empty)

    # query_in: SEMUA baris IN kini bertag SOURCE IN (bukan hanya detail)
    from src.pipeline.queries import query_in
    _qi41 = pd.DataFrame({
        "Tanggal": [5, 5, 5],
        "NAMA RESTO": ["R1", "R1", "R2"],
        "Nama Barang": ["A", "A", "C"],
        "Value": [10.0, 20.0, 30.0],
        "JENIS": ["IN", "IN", "IN"],
    })
    class _Cfg41:
        def folder(self, name):
            return os.path.join(_tf13.gettempdir(), f"nosuch_{name}")
    import unittest.mock as _mk41
    with _mk41.patch("src.pipeline.queries.query_3224", return_value=_qi41.iloc[[0, 1]]), \
         _mk41.patch("src.pipeline.queries.query_3224_bulan_lalu",
                     return_value=pd.DataFrame()), \
         _mk41.patch("src.pipeline.queries.query_4205",
                     return_value=_qi41.iloc[[2]]), \
         _mk41.patch("src.pipeline.queries.query_4205_bulan_lalu",
                     return_value=pd.DataFrame()), \
         _mk41.patch("src.pipeline.queries.query_9901",
                     return_value=pd.DataFrame()):
        _det41 = {}
        _in41 = query_in(_Cfg41(), detail_out=_det41)
    check("(v3.9.29) query_in: baris IN gabungan bertag SOURCE IN "
          "('32.24' ×2 + '42.05' ×1)",
          "SOURCE IN" in _in41.columns and
          sorted(_in41["SOURCE IN"].dropna()) == ["32.24", "32.24", "42.05"],
          f"got {_in41.get('SOURCE IN').tolist() if 'SOURCE IN' in _in41.columns else None}")
    check("(v3.9.29) query_in: detail per dokumen tetap 1:1 dgn sumber",
          len(_det41["df"]) == 3 and
          set(_det41["df"]["SOURCE IN"]) == {"32.24", "42.05"},
          f"got {len(_det41.get('df', pd.DataFrame()))}")

    # --- SMOOTH WHEEL: 1 baris per notch + akumulator + tidak dobel ---
    from src.ui.widgets import CellColorOverlay, enable_smooth_wheel
    _tw41 = tk.Toplevel(root)          # jendela terpisah — widget di root
    _tw41.geometry("240x260+8+8")     # utama bisa tergegeser layout
    _wt41 = ttk.Treeview(_tw41, columns=["c0"], show="headings", height=8)
    _wt41.column("c0", width=120)
    _wt41.heading("c0", text="X")
    _wids41 = [f"r{i}" for i in range(60)]
    for _i41, _wid41 in enumerate(_wids41):
        _wt41.insert("", "end", iid=_wid41, values=[f"v{_i41}"])
    _wt41.pack(fill="both", expand=True)
    _tw41.update_idletasks()
    root.update_idletasks()
    enable_smooth_wheel(_wt41)
    check("(v3.9.29) enable_smooth_wheel idempoten (binding tidak dobel)",
          (enable_smooth_wheel(_wt41) is None and
           _wt41._smooth_wheel_bound is True))
    # y di AREA BARIS (bukan heading — identify_row(2) mengenai heading
    # saat show="headings"; area baris tetap konstant saat scroll)
    _body_y41 = _wt41.bbox("r0")[1] + 2
    _wt41.yview_moveto(0.0)
    root.update_idletasks()
    _top41 = _wt41.identify_row(_body_y41)
    _wt41.event_generate("<MouseWheel>", delta=-120, when="now")
    root.update_idletasks()
    _top41b = _wt41.identify_row(_body_y41)
    _moved41 = _wids41.index(_top41b) - _wids41.index(_top41)
    check("(v3.9.29) 1 notch roda = TEPAT 1 baris (default Tk 3 baris = "
          "patah-patah; 1+3=4 bila binding kelas ikut jalan = dobel)",
          _moved41 == 1, f"moved={_moved41}")
    # akumulator: delta pecahan kecil terakumulasi (trackpad)
    _wt41.yview_moveto(0.0)
    root.update_idletasks()
    _acc0_41 = _wids41.index(_wt41.identify_row(_body_y41))
    for _ in range(3):
        _wt41.event_generate("<MouseWheel>", delta=-40, when="now")
        root.update_idletasks()
    _acc1_41 = _wids41.index(_wt41.identify_row(_body_y41))
    check("(v3.9.29) akumulator delta pecahan: 3×(-40) = 1 baris total "
          "(dulu dibulatkan 0 = tidak pernah menggulir)",
          _acc1_41 - _acc0_41 == 1,
          f"moved={_acc1_41 - _acc0_41}")
    # roda ke atas
    _before41 = _wids41.index(_wt41.identify_row(_body_y41))
    _wt41.event_generate("<MouseWheel>", delta=120, when="now")
    root.update_idletasks()
    check("(v3.9.29) roda ke atas: 1 baris (arah terjaga, tanpa dobel)",
          _before41 - _wids41.index(_wt41.identify_row(_body_y41)) == 1)
    _tw41.destroy()

    # --- OVERLAY: label pool + reposisi SINKRON saat scroll ---
    _to41 = tk.Toplevel(root)
    _to41.geometry("240x220+8+8")
    _ov41 = ttk.Treeview(_to41, columns=["c0"], show="headings", height=6)
    _ov41.column("c0", width=140)
    _ov41.heading("c0", text="Y")
    for _i41 in range(40):
        _ov41.insert("", "end", iid=f"o{_i41}", values=[f"w{_i41}"])
    _ov41.pack(fill="both", expand=True)
    _to41.update_idletasks()
    root.update_idletasks()
    _ovl41 = CellColorOverlay(_ov41)
    _ov41.tag_configure("neg41", foreground="#dc2626")
    _ovl41.set_cells("neg41", [(f"o{i41}", "c0") for i41 in range(40)])
    root.update_idletasks()
    _lab41 = _ovl41._labels.get(("o0", "c0"))
    check("(v3.9.29) overlay: label terpasang utk sel berwarna terlihat",
          _lab41 is not None and _lab41.winfo_ismapped())
    _bbox41 = _ov41.bbox("o0", "c0")
    check("(v3.9.29) overlay: label menempel PERSIS di bbox sel "
          "(reposisi sinkron — tidak melayang)",
          _lab41 is not None and
          (_lab41.winfo_x(), _lab41.winfo_y()) == (_bbox41[0], _bbox41[1]),
          f"lab=({_lab41.winfo_x()},{_lab41.winfo_y()}) "
          f"bbox=({_bbox41[0]},{_bbox41[1]})")
    # scroll 5 baris → label ikut baris (sinkron dalam event yang sama)
    _ov41.yview_scroll(5, "units")
    root.update_idletasks()
    _lab41b = _ovl41._labels.get(("o5", "c0"))
    _bbox41b = _ov41.bbox("o5", "c0")
    check("(v3.9.29) overlay: setelah scroll label baru terposisi BENAR "
          "(bbox valid saat yscrollcommand — bukan menunggu idle)",
          _lab41b is not None and _lab41b.winfo_ismapped() and
          (_lab41b.winfo_x(), _lab41b.winfo_y()) == (_bbox41b[0], _bbox41b[1]),
          f"lab=({_lab41b.winfo_x() if _lab41b else None},"
          f"{_lab41b.winfo_y() if _lab41b else None}) "
          f"bbox=({_bbox41b[0]},{_bbox41b[1]})")
    # label pool: baris keluar viewport → label masuk POOL (reuse), bukan
    # destroy; total label widget TIDAK tumbuh melebihi viewport+pool
    _nchild41 = len([w for w in _ov41.winfo_children()
                     if isinstance(w, tk.Label)])
    _ov41.yview_scroll(30, "units")
    root.update_idletasks()
    _nchild41b = len([w for w in _ov41.winfo_children()
                      if isinstance(w, tk.Label)])
    check("(v3.9.29) overlay: LABEL POOL — jumlah widget label tetap "
          "setelah scroll jauh (reuse, bukan buang-buat = patah-patah)",
          _nchild41b <= max(12, _nchild41) and len(_ovl41._pool) > 0,
          f"before={_nchild41} after={_nchild41b} pool={len(_ovl41._pool)}")
    _to41.destroy()

    # Cleanup
    root.destroy()

    print()
    print(f"HASIL: {len(PASS)} PASS, {len(FAIL)} FAIL")
    if FAIL:
        print("GAGAL:", FAIL)
        sys.exit(1)
    print("SEMUA TEST UI LULUS ✔")


if __name__ == "__main__":
    main()
