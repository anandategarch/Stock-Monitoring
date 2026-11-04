# Changelog

Versi kanonik: `APP_VERSION` di `src/ui/app.py`.
Riwayat lengkap per-commit: `git log --oneline`.

## v3.11.41 — Opsi A: Nomor PO popup pivot prioritas dari file 3243 (Rincian Pesanan Pembelian)

**Analisa mendalam** (user: "Nomor PO dan keterangan dari file 3243 harusnya coba cek mendalam barangkali aku juga sala. cek juga file 3224"): ditemukan **DUA file berbeda** — v3.11.40 keliru pakai 3224:

| File | Nama sheet | Isi | Sumber Nomor PO |
|------|-----------|-----|-----------------|
| **3224** | `#32.24. Rincian Penerimaan Bara` | Penerimaan Barang (RI diterima) | `Nomor # PO` → `Nomor PO`. Hanya muncul bila penerimaan SUDAH terjadi DAN PO ditautkan ke RI. Bisa KOSONG bila terima tanpa PO / PO belum ditautkan saat terima. |
| **3243** | `#32.43. Rincian Pesanan Pembeli` | Pesanan Pembelian (PO itu sendiri) | `Nomor #` = Nomor PO. SELALU ada (semua PO yg pernah dibuat, termasuk yg belum diterima / "Menunggu diproses"). Punya juga `Keterangan PO` + `Status Pesanan Pembelian`. |

→ **3243 lebih lengkap & relevan** utk "Nomor PO" popup (Opsi A — user pilih "tampilkan SEMUA PO utk pasangan bulan ini").

**Implementasi Opsi A**:
- `po_keterangan.py`: + `po_nomor_map_3243(rincian_po_df)` → `{(Nama Barang, NAMA RESTO): "PO-001, PO-002, ..."}` — Nomor PO unik (di-dedup + urut) dari baris `rincian_po_df`. NAMA RESTO diturunkan dari kolom `Cabang PO` via `resto_from_cabang_po` (`"1370.MLGPAR"` → `"MLGPAR"` — logika bersama pipeline `fn_audit` PO Menunggu + UI `rincian_po_view`). TANPA filter tanggal (Opsi A — semua PO pasangan, tidak peduli Tanggal PO). `rincian_po_df` None/kosong/tak ber-Nomor # → `{}`. + `po_nomor_3243_for(...)` helper (lazy import `resto_from_cabang_po` utk hindari circular).
- `details_popup.py`: kolom `KETERANGAN PO` kini **prioritas NOMOR PO dari 3243** (semua PO pasangan); **fallback Nomor PO dari 3224** (per tanggal — `po_nomor_map`) bila 3243 tidak tersedia utk pasangan itu; **lalu label 'Potensi PO belum dibuat'** bila keduanya tidak ada. 3243 ada ⇒ PO sudah dibuat ⇒ label potensi TIDAK relevan (skip — hindari kontradiksi "PO belum dibuat" padahal Nomor PO tampil). Param baru `rincian_po_df` (None/pemanggil lama → jalur 3224/label potensi v3.11.40, backward compat).
- `pivot_view.py`: `load_data` terima param baru `rincian_po_df` (opsional); `_on_double_click` pass `rincian_po_df` ke `show_details_popup`.
- `app.py`: pass `rincian_po_df` (sudah tersedia `self.rincian_po_df` sejak v3.9.30) ke `pivot_view.load_data` — wiring Opsi A end-to-end.

**Verifikasi** (headless — no `$DISPLAY`): `py_compile` OK · `ruff` no-new-error (po_ket=0, details=13, pivot=4, app=17 — semua = baseline) · import OK · `po_nomor_map_3243` pandas e2e test PASS (dedup + sort + Cabang PO→resto + edge-cases None & missing-column). Known: verifikasi visual Tk (popup render, kolom KETERANGAN PO tampil) belum diuji headless — user perlu konfirmasi di Windows.

## v3.11.40 — 4 fitur: hide saldo awal pivot + resto khusus + toggle saldo sistem + popup keterangan PO 3224

**Fitur 1 — filter "only select this" (NO-OP, sudah ada)**: konfirmasi bahwa filter search + klik-kanan "only select this" sudah ada di `widgets.py` (HeaderFilter popup sejak v3.11.30). User dapat: ketik di kotak pencarian untuk menyaring daftar checkbox → klik-kanan sebuah nilai → nilai itu menjadi SATU-SATUNYA seleksi (popup ditutup otomatis), tanpa uncek satu-satu. Hint tampil di popup: "Enter = pilih nilai terfilter · klik-kanan nilai = hanya itu saja · Esc = tutup". Tidak ada perubahan kode (verifikasi status implementasi).

**Fitur 2 — toggle 2 mode saldo sistem (Deviasi GR/PCS)** (user: "Di tab deviasi gr dan pcs aku bisa pakai 2 mode saldo sistem yaitu ambil dari saldo akhir pivot tabel atau dari folder 6. 42.17 ... Secara default pakai yang dari folder 4217 dulu terus ada opsi pakai yang dari pivot tabel"):
- Class baru `SharedSaldoSistemMode` (`deviasi_view.py`, pola `SharedComAmbang`) — state **dibagi GR & PCS** via listener + **persist** ke `settings.json` key `saldo_sistem_mode` (default `"4217"` — user: "saat ini sudah benar").
- Combobox `SALDO SISTEM` `[42.17 | Pivot]` di kartu Filter kedua tab (sinkron — ubah di salah satu, kedua tab ikut + recompute).
- Mode `"4217"` (default) = peta SALDO SISTEM file 42.17 folder `'6. 42.17'` (pipeline `append1 → query_4217_saldo_sistem`) **menimpa** running-stock (perilaku lama). Mode `"pivot"` = saldo akhir pivot tabel (`arr('2.SALDO AKHIR', H)` running-stock, **TANPA** override).
- Override hidup di pivot ter-cache → ganti mode = **invalidasi `SharedPivotCache` + refresh kedua tab** (angka tak basi).
- `app.py`: instantiate `self._shared_saldo_sistem` + teruskan ke `DeviasiView` GR & PCS via param `saldo_sistem_state`.

**Fitur 3 — hide baris 'SALDO AWAL' di pivot table** (user: "Saldo awal di pivot tabel hide aja"):
- `pivot_view.py _compute_payload`: filter `SALDO AWAL` dari daftar `metrics` tampilan (bukan dari konstanta `METRICS`). Baris tetap ADA di pivot DataFrame internal (dasar base COM tanggal 1 — `_compute_com get_series "SALDO AWAL"` tetap membacanya); hanya tidak ditampilkan sebagai baris metric di tree. Export Excel ikut (rows_data dibangun dari metrics terfilter). Reversible.

**Fitur 4 — popup keterangan PO dari file 3224** (user: "Pop up keterangan PO di pivot tabel kok gak muncul? itu ambil dari file 3224 keterangan PO kalau gak salah"):
- `po_keterangan.py`: + `po_nomor_map(in_detail)` → `{(barang, resto, tgl): "PO-001, PO-002, ..."}` (Nomor PO unik dedup+urut dari baris `in_detail` ber-`SOURCE IN` `'32.24'`, kolom `'Nomor PO'`); + `po_nomor_for(...)` helper. `in_detail` None/kosong/tak ber-Nomor PO → `{}`.
- `details_popup.py`: kolom `KETERANGAN PO` kini = **Nomor PO 3224** (+ ` · Potensi PO belum dibuat` bila label potensi menyala). Label potensi sebelumnya sering KOSONG (kondisi ketat: BM>0 + SO naik + 3224=0 + 9901=0 + tanggal terverifiable); Nomor PO 3224 SELALU tersedia bila ada penerimaan → kolom kini informatif. Saling eksklusif per tanggal (Nomor PO muncul ⇒ 3224>0 ⇒ potensi tak terpenuhi): popup tampilkan SALAH SATU.

**Fitur 5 — warna khusus resto MLGPAR & BDGSEK (Deviasi GR/PCS)** (user: "ada fitur kasih warna khusus untuk beberapa Nama resto yang aku mapping agar tau itu resto khusus. Saat ini hanya MLGPAR dan BDGSEK ... di tab deviasi gr dan deviasi pcs kolom Nama resto jika nilai nya MLGPAR DAN BDGSEK kasih warna khusus atau penanda"):
- Konstanta `RESTO_KHUSUS = frozenset({"MLGPAR", "BDGSEK"})` (`deviasi_view.py`) — mudah diperluas (tambah code resto lain).
- Tag cell `resto_khusus_cell` (bg amber lembut `#fef3c7` + fg amber-800 `#92400e` — Tk 9, **menang atas zebra evenrow/oddrow** untuk sel Resto itu saja; baris lain tak tersentuh). Match case-insensitive + strip (drift whitespace/case data tetap tertangkap). Dipasang dinamis per render + ulang pasca sort/clone (pola `_neg_cells`).

**Verifikasi** (sandbox headless — no `$DISPLAY`, Tk test suite tak bisa run): `py_compile` OK semua file · `ruff` no-new-error (pivot_view 4=baseline · deviasi_view 5=baseline · details_popup 13=baseline · po_keterangan 0=baseline · app.py 17=baseline) · import OK (`deviasi_view`+`app` via `python -c`, tak butuh display) · `SharedSaldoSistemMode` logic test PASS (init/set/listener/no-op/invalid→default) · `RESTO_KHUSUS` matching test PASS (case-insensitive + strip) · `po_nomor_map` pandas e2e test PASS (dedup/sort/filter-32.24/edge-cases None & missing-column). Known: verifikasi visual Tk (combobox render, cell-tag warna) belum diuji headless — user perlu konfirmasi di Windows.

## v3.11.39 — Parity Waste (3/3): tombol toolbar ala Waste — idle menyatu, hover/pressed slate

**Restyle `widgets.py Toolbar.add_action`** (cermin `QToolBar QToolButton` Waste v2.15.0):
- **Tombol biasa (↻ Refresh Sumber)**: idle kini MENYATU dgn bar gelap (bg `C_HEADER` #0f172a — look 'transparan' Waste; dulu terisi #1e293b), hover `#1e293b`, pressed `#334155`, teks `#f1f5f9` 10pt normal (dulu #e2e8f0 9pt bold), padding (12,6) (dulu (12,5)).
- **Tombol accent (💾 Export Excel)**: tetap teal solid putih — padanan aksi utama (QSS `QPushButton#accent`); disabled `#94a3b8` (mirror `:disabled` Waste; dikunci test A-02/B-10).
- **Disabled tombol biasa**: bg tetap menyatu dgn bar + teks redup `#64748b` (cermin auto-dim Qt; pembeda state = warna teks).
- API `add_action(text, command, accent, danger)` + `set_enabled` tak berubah — call-site app.py (2 tombol) & test A-02/B-10/§69.B (tinggi bar 48/34) tetap hijau.

**Verifikasi**: FULL SUITE `DISPLAY=:61` HIJAU 1633 PASS / 0 FAIL + test_mock ALL PASSED + ruff + py_compile + **VLM QA screenshot** (28 skenario): toolbar non-accent tampak flat menyatu dgn bar gelap, badge versi & statusbar utuh, tab config pixel-identik (2 'glitch' terdeteksi VLM = pre-existing: tombol config terpotong identik pra/pasca — artefact jendela sempit 80% zoom; label 💾 Export blank = font emoji Xvfb, di Windows Segoe UI render normal).

## v3.11.38 — Parity Waste (2/3): KpiCard flat ala Waste — angka berwarna, tanpa bar aksen

**Restyle `widgets.py KpiCard`** (cermin `KpiCard` Waste v2.15.0):
- **Bar aksen kiri DIHAPUS** — kartu kini FLAT putih (QFrame#kpiframe Waste: border + radius via Card SM).
- **`accent` kini mewarnai TEKS ANGKA** (dulu bar kiri) — cermin Waste: TOTAL BARIS `#0f172a` · PRIORITAS `#dc2626` · POTENSI `#ea580c` · REVIEW `#b45309` · WASTE `#0f766e` · CABANG `#9333ea`. Default `accent` `C_ACCENT`→`C_HEADER` (kartu hitung ala TOTAL BARIS Waste).
- **Label 9pt normal** muted (dulu bold — cermin 'hint' 12px Waste) · **nilai 15pt bold** (≈20px Waste; dulu 16pt) · margin (12,8) spacing 2 (dulu (12,10)).
- **API tak berubah**: `KpiCard(parent, label, value, subtitle, accent)` + `set_value(value, subtitle, accent)` — 4 call-site app.py (kpi_status/elapsed/append/rincian) & test §69.C (lebar seragam KpiRow) tetap hijau tanpa perubahan. Status pipeline (SIAP hijau · ERROR merah · SELESAI PARSIAL oranye · DIHENTIKAN amber) kini terlihat di WARNANYA ANGKA — sama seperti KPI status di Waste.

**Verifikasi**: FULL SUITE `DISPLAY=:61` HIJAU 1633 PASS / 0 FAIL + ruff + py_compile bersih.

## v3.11.37 — Parity Waste (1/3): token tema — tab WCAG AA + STATUS_COLORS

**Analisa Waste**: repo Waste (PySide6, v2.15.0) sudah jadi rujukan design system Stock-Monitoring sejak v3.0 (slate+teal, card, toolbar gelap, konsol #0b1220). Audit GAP menemukan 3 token yang belum 100% paritas:

- **Tab non-aktif**: SM `#64748b` (slate-500) kontras 3,1:1 di latar `#e2e8f0` — **GAGAL WCAG AA**. Waste v2.13.15 (gel-6 C21) sudah fix ke `#475569` (slate-600, ±6,1:1). SM kini ikut: token baru `C_TAB_IDLE`.
- **STATUS_COLORS**: Waste punya peta status terstruktur (fg + bg tint per status). SM hanya konstanta tersebar. Kini ada sumber tunggal 1:1 dgn Waste (additive — view lama tak tersentuh).

**Skip jujur — heading padding**: Waste QSS `QHeaderView::section padding 6px 8px` sempat dicoba dipetakan ke `Treeview.Heading` (8,8)→(8,6). FULL SUITE GAGAL 1 test: `§41 LABEL POOL` (overlay) — header 4px lebih pendek membuat 1 baris tambahan tampak → jumlah label pool 12→13 melewati cap `max(12, before)` (before=12 after=13). Gain visual trivial vs risiko pergeseran geometri lintas 10 tabel + overlay → **(8,8) dipertahankan** (font SM 10pt > 13px Waste — (8,8) sudah proporsional).

**Verifikasi**: FULL SUITE `DISPLAY=:61` HIJAU 1633 PASS / 0 FAIL + test_mock ALL PASSED + ruff bersih + py_compile.

## v3.11.36 — Verifikasi jujur: test suite basi di-rewrite (pra-restyle UI Waste)

**Temuan baseline**: suite `test_ui_redesign.py` MERAH sebelum perubahan UI apa pun — 1559 ✓ / 6 ✗ + crash `_btn94.invoke()` yang mematikan ±1100 baris test akhir. Semua akar sama: **test tidak di-update saat v3.11.31 mengganti analisa 6-seksi dengan tabel selisih** (permintaan user), plus pin versi tertinggal di 3.11.30 dan headline README root tidak disinkronkan sejak v3.11.30.

**Fix (test-only, tanpa sentuhan kode produksi)**:
- **Pin versi** (§1): `APP_VERSION == "3.11.30"` → `3.11.36`.
- **§13b (3 test)**: payload `meta` 6-seksi (n_konteks/n_gantung/basis_v310/n_com_minus) → kontrak baru `_analisa_payload` (rows/n_total/n_selisih/sum_abs/n_resto/n_barang) + baris Resto·Tgl·Barang·Selisih (KOPI +100/−100, SUSU +80, urut |selisih|↓) + panel judul 'ANALISA SELISIH' + tree 3 baris ber-tag pos/neg.
- **§94-H (5 test H2..H6 → 3 test H2..H4)**: tombol '⤢ Perbesar'/popup seksi DIHAPUS (tidak ada lagi) → payload fixture aktual (n_total 2 · n_selisih 1 · rows R1/BRG/tgl5/+1) + tree 6 kolom + tag pos + sort klik judul toggle desc→asc.
- **§76l**: README root (`/README.md`) headline v3.11.30 → v3.11.36 (inner README ikut).
- Helper `_sec_btn_texts94`/`_find_btn94` (menyasar widget yang sudah tak ada) dibersihkan.

**Verifikasi**: FULL SUITE `DISPLAY=:61 python3 test_ui_redesign.py` HIJAU sampai akhir (bagian pasca-crash kini tereksekusi).

## v3.11.35 — Deep audit fix (5 agents): crash + dead feature + normalization consistency

**Audit**: 5 agents paralel scan 41 file / 41k LOC. Temuan: 2 P0 crash, 1 P1 dead feature, 5 P0/P1 normalization bug (pola sama dgn v3.11.34 PO Menunggu tapi belum ter-fix di join lain), 1 P3 v3.11.33 regression, + P3 cleanup.

**P0 crash**:
- **bench_views.py:104** — `NameError: t_lap` (v3.11.30 hapus Laporan benchmark tapi ranking tuple masih reference `t_lap`). Fix: hapus entry dari sorted list.
- **screenshot_ui.py:146-149** — `AttributeError: app.laporan_view` (v3.11.30 hapus tab tapi screenshot harness masih load). Fix: hapus 4-line Laporan block.

**P1 dead feature**:
- **in_selisih_view.py:2668,2671** — `"Button-1>"` (malformed bind, leading `<` hilang) → klik chip "SELISIH TERBANYAK BARANG×RESTO" dead (tidak toggle filter ⧩ Nama Barang). Fix: `"<Button-1>"`.

**P0/P1 normalization consistency** (pola asymmetric v3.11.34 — sisi audit canonical, sisi lain RAW):
- **konversi_satuan.py:116,150** — `build_konversi_map`/`lookup_rasio` kunci RAW `.strip()` vs caller (fn_audit v3.11.34) sudah `norm_nama_barang_key` → **rasio lookup miss → PO Menunggu tak terkonversi** (v3.11.34 incomplete). Fix: kedua sisi `norm_nama_barang_key`.
- **fn_audit.py:144-145** (`_attach_so_kemarin` saldo_awal_map) — audit RAW × map canonical → **SO Kemarin salah**. Fix: `.map(norm_nama_*_key)`.
- **fn_audit.py:869-870** (bk_map lookup) — audit RAW × map canonical → **Qty BK NaN → COM wrong**. Fix: sama.
- **append1.py:827-828** (DBS Kategori merge) — `.str.strip().str.upper()` (no whitespace-collapse) vs canonical → **KATEGORI None** on multi-space drift. Fix: `norm_nama_barang_key_series`.
- **append1.py:871,881** (Rekap Mentah KATEGORI) — same pattern. Fix: sama.
- **append1.py:365,373** (KATEGORI Manual config) — `str(k).strip().upper()` (no collapse). Fix: `norm_nama_barang_key`.
- **rincian_po.py:118-119** (DBS Kategori merge PO source) — same. Fix: `norm_nama_barang_key_series`.
- **app.py:3720-3725** (`_kat_norm`) — `str(s).strip().upper()`. Fix: `norm_nama_barang_key`.
- **main.py:256** (`_rekap_barangs`) — `str(b).strip().upper()`. Fix: `norm_nama_barang_key`.

**P3 v3.11.33 regression**:
- **fn_4217.py:174-192** (`_find_col` prefix-match) — bisa pick wrong column bila beberapa kolom ber-awalan sama (`Satuan Harga` vs `Satuan Default`). Fix: ambil **TERPENDEK** (paling spesifik) — mirror `fn_9901._find_column`.

**P3 cleanup**:
- 8 unused imports dihapus (`deviasi_view.py:127,129` restore_tree_view/snapshot_tree_view; `test_ui_redesign.py:489-495,3979` — residual v3.11.30 relokasi parser).
- **README.md** — versi `v3.11.30` → `v3.11.35`; hapus baris `📋 Laporan Deviasi` + `⚖ Komparasi` (tab dihapus v3.11.30); tambah info mode 📈 Analisa di Rekap Selisih IN.

**Verifikasi**: py_compile OK · ruff 66→57 (net improvement) · import app OK · 5 end-to-end test PASS (PO Menunggu konversi 2 KARTON→48 BOTOL dgn case/whitespace drift; saldo_awal_map; bk_map; konversi lookup; kategori multi-space drift).

**Yang TIDAK di-fix** (low impact / high risk — documented for future):
- `po_keterangan._build_map` CANONICAL×RAW in_detail (P1, lower frequency).
- `deviasi_popup._col_code_mask` + `details_popup:844` legacy RAW snaps (P1, legacy data only).
- `followup.py:467-489` legacy RAW snaps migration (P2, migration risk).
- `write_selisih_sheet` + `Laporan Deviasi (Audit)` sheet number_format (P2 cosmetic).
- `fn_4109._norm_barang_key` float-int barcode (P2 low probability).
- `fn_audit:904-918` desc text mixed satuan (P2 log-only).
- Orphan `LAPORAN-COM`/`KOMPARASI` snapshots in followup.json (P2 soft UX).

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
