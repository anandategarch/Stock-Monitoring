# AUDIT_PERFORMANCE_REPORT.md — CI Repair, Rilis EXE & Benchmark Performa

Tanggal: 2026-11-28 · Pekerjaan: master task P0 (CI) + P0 (release) + P1
(benchmark & optimasi) pada repo `anandategarch/Stock-Monitoring`.

---

## A. CI

### Kondisi sebelum
- Run terakhir saat audit: **46096669135** (commit `33438e6`, v3.17.1) —
  **FAILURE** pada tahap *Ruff — gerbang baseline*: **202 isu > baseline
  201**. Tahap berikutnya (py_compile, validasi config, suite UI, mock,
  smoke) tidak dijalankan.
- Riwayat: run 45980151062 (v3.17.0) juga FAILURE (ruff 202); run
  45291781533 (v3.16.1) SUCCESS (ruff 199). Lompatan 199→202 terjadi
  di v3.17.0.

### Diagnosis (ruff 0.17.1 — pin persis CI; diff temuan antar worktree v3.16.1/v3.17.0/v3.17.1)
Temuan NET baru = **3**, semua kosmetik, nol dampak logika bisnis:
1. `src/ui/pivot_view.py:50` **I001** — alignment komentar import `numpy`
   (10 spasi → 2 spasi).
2. `test_ui_redesign.py:24592` **I001** — blok import lokal §107: urutan
   (openpyxl third-party sebelum `src.*` first-party) + baris pemisah
   grup.
3. `test_ui_redesign.py:1018` **RUF100** — directive `# noqa: F401` pada
   import-probe `pareto_view` terbukti tidak pernah terpakai →
   directive dihapus (hanya komentar).

### Jumlah error Ruff sebelum/sesudah
- Sebelum: **202** (> 201 → CI gagal). Sesudah: **199** (paritas
  v3.16.1; ≤ 201). Basasline workflow **tidak dinaikkan**, tidak ada
  rule di-disable, tidak ada noqa baru, tidak ada kode dihapus.

### File yang diubah (commit `bd5dd03`)
| File | Perubahan |
|---|---|
| `src/ui/pivot_view.py` | 1 baris: alignment komentar import numpy |
| `test_ui_redesign.py` | 2 lokasi: urutan/separator import §107 + hapus 1 noqa tak terpakai |

### Hasil semua tes (lokal, paritas runner: Python 3.12.16 PBS + Tk 9.0.4 + Xvfb 1920x1080x24)
- ruff 0.17.1 = 199 ≤ 201 ✓
- py_compile seluruh file ✓
- Validasi config.json ✓
- `test_ui_redesign.py` = **1704 PASS / 0 FAIL** ✓
- `test_mock.py` = ALL PASS ✓
- Smoke 2 entry (`run_app.py`, `-m src.ui`) exit-124 hidup tanpa
  crash.log ✓

### Link workflow GitHub Actions
- CI repair hijau: run **46102794929** (commit `bd5dd03`)
  https://github.com/anandategarch/Stock-Monitoring/actions/runs/46102794929
- Benchmark framework hijau: run **46104311776** (commit `6021cf7`)
  https://github.com/anandategarch/Stock-Monitoring/actions/runs/46104311776
- Rilis v3.17.2 (tests + build Windows): run **46104911077**
  https://github.com/anandategarch/Stock-Monitoring/actions/runs/46104911077

---

## B. Release

| Item | Nilai |
|---|---|
| Versi sebelumnya (source saat audit) | v3.17.1 (v3.16.1 juga sudah di source sebelumnya) |
| Versi GitHub Release terakhir saat audit | **v3.15.0** (21 Nov) — source tertinggal 2 versi |
| Versi terbaru dirilis | **v3.17.2** (CI repair + sistem benchmark) |
| Commit SHA | `6021cf7` (dites penuh lokal + CI run 46104311776 hijau SEBELUM tag) |
| Tag yang dibuat | `v3.17.2` (annotated; tidak menimpa tag/release yang ada) |
| Status build | tests SUCCESS + build-windows SUCCESS (run 46104911077) |
| Link GitHub Release | https://github.com/anandategarch/Stock-Monitoring/releases/tag/v3.17.2 |
| Link ZIP EXE | https://github.com/anandategarch/Stock-Monitoring/releases/download/v3.17.2/StockMonitor-windows-x64.zip |
| Ukuran ZIP | 38.611.067 bytes (≈ 38,6 MB) |
| Versi source sesudah optimasi | v3.17.3 (commit optimasi — lihat §C/D) |

### Smoke test EXE (pemeriksaan artefak ZIP hasil download)
Yang dapat diverifikasi dari sandbox Linux terhadap artefak Windows:
- Struktur ZIP benar untuk distribusi onedir PyInstaller:
  `StockMonitor.exe` + `_internal/` + `config.json` di akar —
  aplikasi **bundled** (memuat `_tcl_data`/`_tk_data`, semua `.pyd`,
  DLL runtime; **tidak memerlukan Python terpisah** di mesin Windows).
- `config.json` tersedia & valid JSON (RootPath user, Folders, Sheets,
  KategoriBarang4217, DpiAware) — konfigurasi pengguna lama tidak
  tersentuh.
- **Version stamp EXE = "3.17.2"** terverifikasi di PE resource
  (UTF-16LE, FileVersion + ProductVersion) — judul aplikasi akan
  menampilkan versi benar (APP_VERSION ter-bundle).
- `followup.json`/`settings.json` dibuat runtime di sisi aplikasi
  (jalur sudah tercakup suite UI + smoke entry 2×exit-124 tanpa
  crash.log di CI ubuntu).

**Keterbatasan jujur**: EXE Windows tidak dapat **dijalankan** di
sandbox Linux — eksekusi runtime Windows (klik ikon, drag data nyata,
cek `logs/app.log` path Windows) tidak bisa diverifikasi di sini;
yang terverifikasi: build sukses di runner Windows asli (compile +
archive + upload), artefak lengkap, version stamp, struktur folder,
konfigurasi. Smoke runtime penuh direkomendasikan dilakukan user di
Windows (buka ZIP → jalankan `StockMonitor.exe`).

---

## C. Performance (P1)

### Spesifikasi komputer pengujian (sandbox)
- CPU 2 core · RAM 4.032 MB (tersedia ±2,8 GB) · disk lokal
- Python 3.12.16 (python-build-standalone) · Tk 9.0.4 · Xvfb
  1920x1080x24
- pandas 2.2.3 · numpy 2.1.3 · openpyxl · python-calamine (engine
  baca Excel utama) · psutil 7.2.2 (**tooling benchmark saja — BUKAN
  dependency runtime; requirements.txt tidak berubah**)
- ruff 0.17.1

### Sumber data — SINTETIS (dinyatakan jujur)
Dataset operasional user (RootPath `C:\KERJA\...`) **tidak tersedia**
di sandbox Linux → dataset **sintetis deterministik** dibuat dengan
`benchmarks/synth_data.py` meniru skema export Accurate lengkap
(16 folder: REKAP MENTAH per resto berjalan+lalu, 22.05, 32.24
berjalan+lalu, 42.15, 42.05 berjalan+lalu, 42.17 per resto, 41.09,
konversi, DBS kategori, PO 32.43, 9901 + config.json). Semua nama
generik (`BRG SYN 0001 (V.20)`, `RS01A`, `PM SYN BENCHMARK`) — tidak
ada nama restoran/barang bisnis nyata di repo/log. **Angka di bawah
adalah benchmark dataset SINTETIS, bukan klaim performa workbook
operasional.**

### Skala yang diuji (pipeline, dataset Excel sintetis)
| Skala target | Resto × Barang (pairs) | File Excel | Baris Append1 aktual |
|---|---|---|---|
| 100k | 16 × 20 = 320 | 59 | 97.728 |
| 300k | 28 × 35 = 980 | 95 | 299.124 |
| 600k | 36 × 52 = 1.872 | 119 | 571.248 |
| 900k | 44 × 65 = 2.860 | 143 | 872.652 |

### Pipeline — ringkasan skenario (detik; peak RSS MB)
| Skala | Cold total | Warm total | Hemat | Peak RSS (cold/warm) | Cache hit/miss (cold / warm / refresh-one / refresh-all) |
|---|---|---|---|---|---|
| 100k | 1,94 | 1,36 | −30% | 148 / 185 | 1/58 · 58/0 · 57/1 · 1/58 |
| 300k | 4,39 | 3,54 | −19% | 332 / 362 | 1/94 · 94/0 · 93/1 · 1/94 |
| 600k | 7,84 | 6,82 | −13% | 492 / 526 | 1/118 · 118/0 · 117/1 · 1/118 |
| 900k | 11,57 | 10,23 | −12% | 705 / 741 | 1/142 · 142/0 · 141/1 · 1/142 |

- **Cache benar-benar digunakan**: setiap skenario menjalankan pipeline
  PENUH ulang (fungsi produksi sama); warm run membaca 142/142 file dari
  cache in-memory (0 miss), refresh_one membaca ulang TEPAT 1 file,
  refresh_all = semua miss. **Fingerprint hasil** (baris per JENIS +
  audit KPI + PO rows) **identik antar semua skenario** — cache tidak
  mengubah hasil analisis (terverifikasi otomatis di tiap run).
- Skala 900k (872.652 baris) ≈ beban nyata user (±892k) → pipeline
  headless ~11,6s di mesin 2-core sandbox.

### Pipeline — rincian tahap 900k (cold / warm, detik)
| Tahap | Cold | Warm |
|---|---|---|
| 2. build_append1 (baca Excel + pivot + running stock + kategori + unpivot) | 5,91 (51%) | 4,86 (47%) |
| 5. audit penuh | 2,21 (19%) | 2,22 (22%) |
| 6. audit bulan-ini | 1,97 (17%) | 1,98 (19%) |
| 7. harga 41.09 | 0,26 (2%) | 0,01 (0%) |
| 3. rincian PO / 4. maps | 0,10 / 0,12 | 0,03 / 0,12 |

- RAM bertahap (900k cold, MB): sebelum 82 → pasca append1 441 →
  pasca audit 465 → pasca harga 484 → **peak sampler 705** (transien
  pivot/unpivot) → setelah del+gc: RSS tidak langsung kembali (perilaku
  normal allocator — dilaporkan apa adanya: RSS akhir skenario
  ±485-752 MB per siklus).
- Memori DataFrame append1 (memory_usage deep): 45,6 MB (100k) →
  139,5 (300k) → 266,4 (600k) → **407,0 MB (900k)**.

### Views/UI (Xvfb; frame append1-like in-memory sintetis)
| Skala rows | Pivot compute resto/tanggal | Pivot render | Deviasi GR compute+render | Nominal compute | Sort kolom | Export pivot | Event-loop maxgap |
|---|---|---|---|---|---|---|---|
| 100.440 | 0,10 / 0,15 s | 0,72 s | 1,15 s (360 pair) | 0,06 s | 0,00 s | 0,10 s | 0,57 s |
| 273.420 | 0,25 / 0,32 s | 1,85 s | 1,77 s | 0,16 s | 0,00 s | 0,24 s | 1,67 s |
| 522.288 | 0,51 / 0,55 s | 3,43 s | 2,58 s | 0,30 s | 0,05 s | 0,51 s | 2,95 s |
| 898.380 | 0,83 / 0,93 s | 5,08 s | 3,85 s (3.220 pair) | 0,54 s | 0,10 s | 0,78 s | 4,23 s |

- Sort kolom tetap cepat (linear insert — hasil optimasi v3.3
  `sort_tree_by_column` 45s→1.1s masih efektif pada 3.220 baris).
- Event loop: `root.update()` maxgap tumbuh linier dengan skala render —
  UI **tidak membeku permanen**, ada jeda render awal beberapa detik di
  900k (sumber bottleneck → lihat optimasi di bawah).

### Optimasi berbasis bukti (v3.17.3) — kondisi sebelum → sesudah
**Bukti (cProfile render pivot 900k, 7,5s total)**:
`_repopulate_filter_combos` = **3,7s (~50%)** — `_combo_offered_values`
menghitung ulang normalisasi string (2,7jt lambda) + groupby 900k baris
**tiap render ulang dengan state filter sama**, di main thread.

**Perubahan minimal** (memoization; jalur komputasi asli tidak diubah
satu baris pun): cache hasil `_combo_offered_values` per
`(dim, seluruh-state-filter)` — key mencakup semua input fungsi +
identitas objek data (strong-ref per entry; `load_data` data baru →
reset). Batas 32 entri.

| Ukuran (900k) | Sebelum | Sesudah | Δ |
|---|---|---|---|
| Render ulang state filter sama | 5,10 s | **0,94 s** | **−82%** |
| Pulang-pergi mode resto→tanggal→resto (render #3) | 5,10 s (hitung ulang penuh) | **0,98 s** | −81% |
| Render pertama state baru | 5,10 s | 5,10 s | 0 (miss natural) |

**Verifikasi kesetaraan**: output `_combo_offered_values` IDENTIK vs
implementasi lama pada 8 kasus (mode tanggal×resto × dim resto/source ×
filter barang × hide-off; baseline disnapshot pre-edit). **Regresi
penuh**: suite UI 1704/0 · mock ALL PASS · ruff 199 · py_compile OK.

### Kandidat optimasi yang SENGAJA tidak diambil (dengan alasan)
- Menyatukan audit penuh & audit bulan-ini (2,2s + 2,0s @900k):
  varian bulan-ini membuang baris Tanggal negatif SEBELUM engine →
  basis "SO kemarin" di tanggal 1 memakai data bulan lalu — hasilnya
  TIDAK ekuivalen dengan filter varian penuh; penggabungan berisiko
  mengubah hasil audit (dilarang aturan global).
- `astype(str)` groupby keys → factorize: mengubah penggabungan kunci
  numerik-vs-string (kelas bug E-1 v3.16.0) — risiko hasil berubah.
- Memindah `_repopulate_filter_combos` ke worker thread: perubahan
  struktural threading berisiko race; cache mencapai tujuan yang sama
  tanpa sentuh threading.

---

## D. Daftar perubahan

### File yang dimodifikasi
| File | Perubahan | Alasan | Dampak |
|---|---|---|---|
| `src/ui/pivot_view.py` | (1) alignment komentar import numpy (I001); (2) v3.17.3 cache `_combo_offered_values` + reset di `load_data` | CI repair; optimasi P1 terverifikasi | render ulang state sama −82%; hasil identik |
| `test_ui_redesign.py` | urutan/separator import §107 (I001); hapus 1 noqa F401 tak terpakai (RUF100) | CI repair | nol (cosmetic) |
| `src/ui/app.py` | APP_VERSION 3.17.1 → 3.17.2 → 3.17.3 (+komentar) | sinkron versi rilis | judul/statusbar/EXE stamp versi baru |
| `CHANGELOG.md` | entri v3.17.2 + v3.17.3 | dokumentasi | — |
| `README.md` (python) | headline versi ×2 + bagian benchmark | dokumentasi | — |
| `README.md` (root) | headline versi ×2 + baris tabel Isi Repository | dokumentasi | — |
| `stock-monitoring-python/.gitignore` | + `benchmarks/results/` | artefak regenerabel | — |

### File yang ditambahkan (commit `6021cf7`)
| File | Isi |
|---|---|
| `benchmarks/synth_data.py` | generator dataset sintetis deterministik (16-folder tree + config + make_big_append1) |
| `benchmarks/benchmark_pipeline.py` | pipeline per-tahap + skenario cache + psutil peak RSS + fingerprint |
| `benchmarks/benchmark_views.py` | pivot/deviasi/nominal/sort/filter/export + event-loop maxgap |
| `benchmarks/benchmark_report.py` | JSON → tabel markdown |
| `stock-monitoring-python/AUDIT_PERFORMANCE_REPORT.md` | laporan ini |

### File yang dihapus
**Tidak ada.**

### Kode/fitur yang dihilangkan
**Tidak ada.** (Hanya 1 directive komentar `# noqa: F401` yang
terbukti tak pernah aktif.)

### Dependency ditambahkan/dihapus
**Tidak ada** perubahan `requirements.txt`. `psutil` di-install di
environment tooling benchmark saja. (CI lintas-runs: ruff dipin
0.17.1 & Pillow — sudah ada sebelumnya, tidak diubah.)

---

## E. Temuan tersisa & keterbatasan

### Bug belum diperbaiki
- Tidak ditemukan bug fungsional baru selama pekerjaan ini (suite UI
  1704/0 lintas semua commit; smoke & mock hijau).

### Keterbatasan benchmark
1. **Dataset sintetis**, bukan workbook operasional (RootPath user di
   `C:\` tak terakses dari sandbox Linux). Karakteristik (nama panjang
   variatif, format tanggal nyata, jumlah baris per sumber real)
   mempengaruhi waktu baca Excel — angka nyata bisa berbeda. Dataset &
   harness tersedia agar benchmark bisa dijalankan ulang user pada
   RootPath asli (satu perintah; hasil JSON otomatis).
2. **Popup detail & jendela fullscreen tabel tidak diukur** — butuh
   interaksi seleksi baris lintas modul; diklaim apa adanya sebagai
   keterbatasan (bukan disembunyikan).
3. **EXE Windows tidak dapat dieksekusi** di sandbox Linux — smoke
   runtime penuh (buka app, drag data, lihat logs path) direkomendasikan
   dijalankan user di Windows.
4. Sandbox 2 CPU / 4GB — mesin user (Windows, biasanya lebih besar)
   akan lebih cepat; perbandingan RELATIF antar skenario tetap valid.
5. Benchmark pipeline headless TIDAK men-disable GC (jalur CLI natural);
   jalur UI produksi memakai `gc_shield` — RAM puncak UI nyata bisa
   sedikit lebih tinggi.

### Area belum teruji
- Kombinasi Tk 8.6 path overlay-label heatmap di Windows EXE secara
  visual (dilindungi suite §21/§35/§76 pada Tk 9 + fallback code-path
  sudah ada, namun visual Windows tidak bisa dilihat dari sandbox).
- `logs/app.log` rotasi & crash.log path di Windows distribusi
  (dibangun jalur CI ubuntu smoke; tidak dapat dijalankan Windows dari
  sini).

### Risiko yang masih ada
- Ruff baseline 199/201 hanya menyisakan margin 2 isu — commit berikut
  yang menambah 3+ isu baru akan menggagalkan CI lagi (disiplin:
  jalankan ruff lokal sebelum push).
- `branches: ain]` di YAML workflow ternyata **ilusi tampilan ANSI**
  (file asli `[main]` — run v3.17.2 ter-trigger normal; bukan bug).

### Rekomendasi perbaikan berikutnya
1. Jalankan `benchmarks/benchmark_pipeline.py` pada RootPath asli di
   mesin user (cold vs warm) — angka nyata akan menggantikan sintetis.
2. Kandidat optimasi lanjutan (butuh bukti profil dulu): pembacaan
   Excel `fn_combine_folder` saat cold (≈1,3s dari 5,9s append1 di
   900k) dan unpivot pivot-table — dua sisa kontributor terbesar.
3. Pertimbangkan mengukur `test_ui_redesign.py` runtime CI (menit) bila
   ingin feedback loop lebih cepat — saat ini ±7 menit per push di
   runner.
4. Baseline ruff 199 → turunkan bertahap per rilis (mis. −5 isu per
   rilis) hingga 0 supaya margin tidak terus tipis.

---

### Rekap tautan verifikasi
- CI repair: https://github.com/anandategarch/Stock-Monitoring/actions/runs/46102794929
- Benchmark commit: https://github.com/anandategarch/Stock-Monitoring/actions/runs/46104311776
- Rilis v3.17.2 (tests + build): https://github.com/anandategarch/Stock-Monitoring/actions/runs/46104911077
- Release & ZIP: https://github.com/anandategarch/Stock-Monitoring/releases/tag/v3.17.2
