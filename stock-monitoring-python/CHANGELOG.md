# Changelog

Versi kanonik: `APP_VERSION` di `src/ui/app.py`.
Riwayat lengkap per-commit: `git log --oneline`.

## v3.11.34 — 3 fix: PO Menunggu mismatch + popup chips dihapus + zebra diperkuat

- **(1) PO Menunggu tidak sesuai Nama Barang — FIX akar** (user: *"PO Menunggu kok tidak sesuai nama barangnya ya?"*). Akar: kunci pasangan PO Menunggu dinormalisasi **asimetris** — sisi audit (append1.py) UPPER+rapat-spasi+segmen-setelah-titik, tapi sisi PO (`fn_audit._po_menunggu_pairs`) cuma `.strip()` (case/whitespace mentah). Pasangan beda ejaan (`"Air Mineral  600ML"` vs `"AIR MINERAL 600ML"`, `"1370.mlgpar"` vs `"MLGPAR"`) tak cocok → `Qty PO Menunggu = 0` padahal PO ada. **Fix**: kedua sisi kini pakai helper kanonik `norm_nama_barang_key` (UPPER + rapat-spasi) + `norm_nama_resto_key` (UPPER + segmen setelah titik) dari `helpers.py` — paritas append1. Verifikasi end-to-end: PO source `"Air Mineral  600ML"` @ `"1370.mlgpar"` (lowercase + double-space) cocok dengan audit `"AIR MINERAL 600ML"` @ `"MLGPAR"` → qty 150 terpasang benar (sebelumnya 0).
- **(2) Popup Rekap Selisih IN — chip per-SOURCE IN dihapus** (user: *"Pop up rekap selisih in shapes shapes kaya 4205. (Bulan lalu), 3224 dan kawan kawan nya hapus aja"*). Popup double-click (`InDetailPopup`) dulu menampilkan 5 chip kotak ringkasan per-sumber: `42.05`, `42.05 (BULAN LALU)`, `32.24`, `32.24 (BULAN LALU)`, `99.01`. Chip itu **dihapus**. Tabel dokumen di bawah TETAP mengelompokkan baris per SOURCE IN (info grup tak hilang). Chip yang dipertahankan: `IN TOTAL` (jumlah semua sumber), `Barang Masuk`, `SO Kemarin`, `Selisih IN`, `COM`. Ini popup berbeda dari panel KPI utama yg sudah dihapus v3.11.30.
- **(3) Zebra Deviasi GR/PCS diperkuat** (user: *"Warna Zebra di tab deviasi gr dan pcs agak perkuat lagi warna nya dikit"*). `theme.ROW_ODD`: `#f8fafc` (slate-50, nyaris tak terlihat) → `#f1f5f9` (slate-100, lebih jelas). `ROW_EVEN` tetap `#ffffff`. Juga dirapikan: `in_selisih_view.py` InDetailPopup + main tree yang hardcoded `#f8fafc` kini pakai konstanta `ROW_EVEN`/`ROW_ODD` (paritas theme, sekali ubah — semua view ikut). Catatan: `setup_tree_tags` helper + base `Treeview` style juga baca konstanta ini → zebra di SEMUA tab (Pivot, Rekap Selisih IN, Rincian PO, dll.) ikut diperkuat seragam.
- **Verifikasi**: py_compile OK · ruff 8 (baseline 8 — net zero) · import app OK · test PO Menunggu end-to-end PASS (3 assertion: Air Mineral=150, Ayam=50, Gula Pasir=0).

## v3.11.33 — Fix format file 4217 baru (kolom satuan "Satuan #")

- **Masalah**: file `4217.xlsx` format baru (commit `212c8dc "PERUBAHAN FILE 4217"`) menamai kolom satuan **`Satuan #`** (dengan suffix ` #`), sedangkan engine `fn_4217._find_col` hanya cocok **exact** dengan kandidat `["Nama Satuan", "Satuan"]`. Hasilnya: `sat_col = None` → **kolom SATUAN kosong (`""`) untuk SEMUA 1.257 baris output**. Akibat downstream: pasangan GR/PCS tanpa rekap SO kehilangan satuan (fallback `append1.py` baris 1041 useless), baris bisa terbuang senyap oleh pivot Deviasi GR/PCS. Engine **tidak crash** — tapi data SATUAN hilang senyap.
- **Fix**: `_find_col` sekarang **exact-match dulu** (preserves perilaku file lama), **lalu fallback prefix-match** — kolom pertama ber-AWALAN nama kandidat. `"Satuan #".lower() == "satuan #"` exact-gagal, tapi `.startswith("satuan")` cocok → SATUAN terbaca benar. Future-proof untuk varian export lain (`Satuan (GR)`, `Satuan Utama`, dsb.).
- **Verifikasi end-to-end** (file `4217.xlsx` 590 baris): 1.257 baris output, 16 resto, 7 kategori. SATUAN kini berisi 8 varian: `GR (625) · PCS (388) · PACK (132) · UNIT (74) · ML (16) · BOTOL (16) · LEMBAR (5) · KG (1)` — sebelumnya semua `""`.
- Kolom `Kategori Barang` & `Nama Barang` (exact-match) tak berubah — fallback prefix tak terpicu untuk mereka (sudah cocok exact). Kolom `Total Nama Gudang` tetap dibuang oleh `_SUMMARY_COL_RE` (sudah benar sebelumnya). Kolom `Unnamed: 6/8/17` (empty) tetap terbuang oleh mask `NAMA RESTO != ""`.
- **Risiko rendah**: 1 file berubah (`fn_4217.py`), method `_find_col` cuma dipanggil 2× di file itu (kategori + satuan); exact-match diutamakan → file lama tak terdampak.

## v3.11.32 — Zebra per-grup di tab Deviasi GR & PCS

- **Penanda visual batas grup Nama Barang**: tabel Deviasi GR & Deviasi PCS kini memakai **pita latar zebra per-grup** — baris dalam kelompok Nama Barang sama mendapat warna latar sama, dan paritas berganti (putih `#ffffff` ↔ slate-50 `#f8fafc`) tiap kali Nama Barang berubah di baris berikutnya. Batas antar-grup kelihatan instan. User: *"tampilan di tab deviasi gr dan deviasi pcs untuk tiap nama barang yang beda ada semacam penanda visual oh ini sudah grup barang lain."*
- **Implementasi**: method baru `_apply_group_zebra(tree)` walk `tree.get_children` di **urutan tampak saat ini**, lookup Nama Barang per iid via `self._row_snaps`, toggle paritas `evenrow`/`oddrow` pada group boundary. Dipasang dinamis (bukan dibakar di payload) lewat `_reapply_render_decorations` — jadi **ikut urutan sort aktif**: default sort (Nama Barang) → banding jelas; sort kolom lain (CEK/Nominal) → otomatis adaptif. Idempoten (strip zebra tag lama sebelum re-apply).
- **Berlaku juga untuk clone ⛶ Perbesar** (fullscreen popup) — `tree` dilewatkan sebagai param.
- **Tag per-cell (COM Tinggi/Rendah foreground, hl_cell bg, neg_cell) tak konflik**: `com_*_cell` hanya set `foreground` → bg zebra tembus; `hl_cell` set bg pada cell Deviasi/SO_H (perilaku lama tetap). Re-using tag `evenrow`/`oddrow` vestigial yang sudah di-configure sejak v3.9.x (pernah dipakai era merge-vertikal, dibuang v3.9.61, kini dihidupkan lagi dinamis).
- **Risiko rendah**: tidak ubah sort/filter/export/selection; hanya pasang tag row-level pasca-render/sort/clone-filter.

## v3.11.31 — Analisa Rekap Selisih IN diganti (tabel selisih) + dead code dibersihkan

- **Analisa mode 📈 (tab Rekap Selisih IN) diganti total**: 6-seksi reconciliation lama (1·Umur Gantung · 2·Leaderboard Resto · 3·Sistemik vs Lokal · 4·Resolve-Rate · 5·Anomali ΔSO · 6·COM Minus) **dihapus**; diganti tabel **SELISIH** sederhana: kolom `# · Resto · Tanggal · Nama Barang · Selisih IN · KATEGORI`, urut `|selisih| ↓` (baris selisih terbesar di atas), klik judul kolom = sort ulang (↕ toggle asc/desc), baris positif hijau `#15803d` · negatif merah `#b91c1c`. Sumber = frame TERFILTER rentang tanggal + ⧩ + filter Resto (PRA checkbox "Hanya Selisih ≠ 0" — analisa tetap melihat semua baris bermasalah). Header ringkasan: `N baris selisih (≠0) · Σ|selisih| = Y · X resto · Z barang · M baris total`. Cap render 2.000 baris (performa). User: *"di tab rekap selisih IN bagian analisa, aku pengen ditampilkan selisih resto dan nama barang dan tanggal. hapus aja analisa analisa sebelum nya ganti dengan yang baru."*
- **Dead code dibersihkan** (~600 baris): `_compute_analisa` (6-seksi payload) → `_compute_analisa_rows`; `_render_analisa` (6-seksi canvas+sections) → render `ttk.Treeview`; dihapus: `_analisa_helpers`, `_analisa_sec`, `_open_analisa_section` (popup ⤢ Perbesar), `_tgl_short`, `_as_umur`/`_as_resto`/`_as_sistemik`/`_as_resolve`/`_as_anomali`/`_as_comminus` (6 builder seksi), class attrs `_A_TREND_FG` & `_ANALISA_SEC_META`, import `AccentButton` level-modul (kini hanya dipakai via import lokal di popup InDetailPopup & dialog export), import `ClassVar`. Kolom aux `Delta SO`/`Qty BK` di `_compute_base` **dipertahankan** (masih dipakai saldo/COM ops, bukan milik analisa). Toggle SegmentBar `📋 Tabel / 📈 Analisa` & mekanik payload cache tak berubah. User: *"Hapus juga dead code nya."*

## v3.11.30 — 6 permintaan user (rank, filter, tab, beda-sendiri, COM, KPI)

- **Rank DIHAPUS TOTAL dari kolom CEK** (tab Deviasi GR & PCS): era segmen "Rank N" (v3.11.27-29) ditutup — sel CEK kini murni label anomali + segmen analisa; `_grank_map` & seluruh jalur rank dibubarkan; sort kolom CEK kini teks label murni.
- **Filter ⧩ "only select this"**: KLIK-KANAN sebuah nilai di popup filter = nilai itu menjadi satu-satunya seleksi + popup tertutup (user: "misal aku mau filter 1 barang aja aku harus uncek semua"); hint di popup diperbarui; berlaku untuk semua kolom filter di semua tab.
- **Tab 📋 Laporan Deviasi DIHAPUS + dead code** (user: "Hapus tab laporan deviasi dan dead code nya"): 3 mode (⚖ Komparasi File Deviasi · 🚨 Anomali COM · 💰 Nominal (H)) dibongkar; modul `komparasi_deviasi_view.py` / `laporan_deviasi_view.py` / `nominal_deviasi_view.py` dihapus; parser pindah ke `deviasi_file.py`. **Yang tetap hidup**: file deviasi bulan lalu kini dimuat APP-LEVEL (⚡ Otomatis pasca-pipeline / tombol 📂 kartu DEV BULANAN ⚙️ Config) → kolom Dev. Bulan Lalu + analisa lalu-kini tab 📦/🧩 + popup Nominal Deviasi tetap berfungsi.
- **"Beda dari Resto Lain" kini DATA SAAT INI** (tanpa file bulan lalu — user: "kok seperti nya belum"): arah deviasi resto MINORITAS dalam grup Nama Barang (grup ≥3 baris; berlawanan ≥3× searah & ≥2; 0/netral dikecualikan); label "(Surplus · 18/20 resto lain Defisit)"; syarat dua-periode & gate file ⚖ dibuang.
- **Ambang COM**: default **90%** (dulu 50 — user: "Default 90% aja"); ganti ambang = langsung apply (sudah ada, dipertahankan); sel CEK baris ber-segmen COM kini **DIWARNAI** — COM Tinggi rose #be123c · COM Rendah teal #0f766e (tag cell Tk 9; fallback tag baris).
- **Kartu KPI Rekap Selisih IN DIHAPUS** (user: "shapes kotak seperti total baris. OK (matching) ini semau dan teman2 nya hapus aja"): panel TOTAL BARIS · OK (MATCHING) · VALID · CUT-OFF RESOLVED · DEVIASI MURNI · DEV MURNI·PO · SISA GANTUNG · COM MINUS tak lagi dibangun; kolom Hasil Audit di tabel tetap utuh.

## v3.11.29 — Rank unik per grup & kategori non-stok dibuang

- **Rank unik per grup**: seri antar grup berdeviasi DIKIKIS — tiap grup nama barang dapat nomor rank **berbeda** 1..N di kolom CEK (tab Deviasi GR & PCS). Sebelumnya grup dengan Σ|Deviasi| yang sama berbagi nomor sama (pola 13,13,13,16 — banyak grup kecil PCS tampak "rank sama semua"). Tie-break deterministik: nama barang alfabetis. Grup Σ|Deviasi| = 0 tetap tanpa prefiks Rank.
- **Identifikasi Kategori Manual**: barang ber-kategori 42.17 non-stok — **SUPPLIES [OTHERS], 00.COST, 21.COST.ASSET, 20.ASSET.ASSET- TIDAK BOLEH** — **dibuang di awal**: tidak pernah tampil di daftar (mode filter apa pun, termasuk "Semua"), keluar dari dropdown, tidak menulis baseline BARU; match versi-toleran (varian "…V.2" ikut terbuang); status bar menambah segmen "N non-stok dibuang". Murni tampilan — pipeline 42.17 tetap membaca saldo utuh (dipakai pasangan kolom Sistem di tab Deviasi).

## v3.11.28 — Fix rank & identifikasi manual

- **Fix rank "sama tiap grup"**: grup dengan Σ|Deviasi| = 0 tidak lagi diberi prefiks "Rank N" (dulu `method="min"` membuat semua grup nol berbagi nomor rank sama — konvensi sheet asli: deviasi 0 → rank kosong); rank dihitung 1..N hanya di antara grup berdeviasi; seri antar grup berdeviasi tetap dipertahankan.
- **Identifikasi Kategori Manual (tab Config)**: default filter = **Whitelist 42.17** (match versi-toleran seperti pipeline — kategori 42.17 kosong disembunyikan); kolom baru **"Di Deviasi Weekly"** (✓/✗ eksak dari nama barang yang terbaca folder rekap, bukan proksi kategori app); sort prioritas: **belum ada di deviasi weekly → tanpa kategori app → BARU → nama**; ✗ weekly ditandai merah; status bar menyebut jumlah belum-direkap.

## v3.11.x — Kolom CEK analisa & era merge-vertikal (ditutup)

- **v3.11.27** — Revert total merge-vertikal (dinilai jelek): tabel kembali datar per-baris; **kolom Rank dihapus, peringkatnya pindah ke kolom CEK** sebagai segmen analisa pertama (mis. "Rank 3 · Turun Drastis · …").
- **v3.11.22** — Segme CEK "Beda dari Resto Lain" dengan ambang rasio: resto lain berlawanan ≥ 3× searah (dan ≥ 2), label menyertakan rasio (mis. "18/20 resto lain Defisit").
- **v3.11.21–26** — Eksperimen merge-vertikal kolom CEK & Rank (statis ala Rincian PO, anotasi ↳, struktur induk-anak) — seluruhnya dibongkar di v3.11.27.
- **v3.11.19** — Nama barang diulang tiap baris (paritas file Excel user) — bug "nama barang hilang" tuntas permanen.
- **v3.11.13** — UI dibersihkan dari teks/emoji dekoratif berlebih.
- **v3.11.12** — Ambang COM tinggi/rendah dapat diatur (±%).
- **v3.11.10** — Audit 5-agen: 23 bug terverifikasi diperbaiki + fix crash live.
- **v3.11.5–8** — Rumus Selisih IN kembali BM − IN; identifikasi kategori manual bersumber 42.17; papan selisih terbanyak barang×resto.

## v3.10 — Basis selisih & analisa baru

- Basis selisih "SO kemarin", kolom COM, mode Analisa di Rekap Selisih IN.
- v3.10.1 — 17 bug audit ditutup.

## v3.9.x — Konsolidasi besar (highlight)

- **v3.9.68** — Gerbang tes CI: job `tests` (ruff + suite UI + mock + smoke) wajib hijau sebelum build EXE.
- **v3.9.66** — Filter persisten antar sesi (per tab + zoom).
- **v3.9.61–65** — Restrukturisasi tab Nominal Deviasi, Ctrl+F cari di tabel, zoom Ctrl+Scroll, fix rank per-baris.
- **v3.9.48** — Tampilan HD tajam (DpiAware) + zoom 50–200%.
- **v3.9.46–57** — Kategori rekap mentah, komparasi minggu ikut TANGGAL H, perbaikan filter kategori, sticky nama barang (era merge awal).
- **v3.9.34–45** — Kolom Nominal (Harga 41.09 × Qty), tab Nominal Deviasi per resto, Rincian PO ↳ keterangan/pemasok/status, seleksi sel ala Excel.
- **v3.9.27–33** — Mode hitung bulan, CEK RI Balancing, popup deviasi diperbesar + Nomor PO & COM, PO menunggu sebagai penjelas deviasi.
- **v3.9.19–26** — Kolom analisa, hapus risiko/benchmark, default kategori, nama resto PO, filter nilai-data-ada.
- **v3.9.5–18** — Deep audit bergelombang (P1–P3), mode Komparasi File Deviasi, median anomali COM antar-tanggal, kategori deviasi 5 kolom, fokus resto 1. DEVIASI WEEKLY, ikon & style dirapikan.
- **v3.9.1–4** — TANGGAL H shared 1×, export + audit, Rincian PO ringkas, style ala aplikasi Waste.

## v3.0 – v3.8 — Fondasi

- **v3.8** — Rekap Selisih IN 1–31, pivot 25•–31• lengkap, export PIVOT + per resto.
- **v3.7** — Engine 3,5–4× lebih cepat (output identik) + fix deep audit.
- **v3.6** — Hide/unhide kolom, audit rekonsiliasi dari data app, default tanggal 26 lalu → 31 berjalan.
- **v3.5** — Mode Audit Rekonsiliasi (port macro VBA).
- **v3.4** — Lebar kolom adjustable, SO bulan lalu, tab Rekap Selisih IN.
- **v3.2–3.3** — Tab ☑ Follow Up (persist + export), sort linear (0,7 dtk di 50k baris), fix follow-up setelah sort.
- **v3.1** — Filter menempel di header kolom (ala AutoFilter), perbesar tabel, pivot per resto.
- **v3.0** — Total UI/UX redesign (slate + teal, card-based, KPI cards, konsol log gelap).
