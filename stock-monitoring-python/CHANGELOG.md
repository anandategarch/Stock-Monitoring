# Changelog

Versi kanonik: `APP_VERSION` di `src/ui/app.py`.
Riwayat lengkap per-commit: `git log --oneline`.

## v3.11.57 — FIX pra-pipeline: nilai KETIK tanpa Enter terbuang senyap

User: *"cek juga kenapa kolom H sebelum proses pipeline aku isi 5 misalnya
kok di tab deviasi gr dan pcs tetap 25 mendeteksi tanggal terdekat? harusnya
misal aku setting sebelum pipeline 5 itu juga ganti 5"*.

### Root cause (terbukti — repro app ASLI + Xvfb: uncheck Auto → ketik 5 → klik MULAI tanpa Enter → state tetap 25; kontrol "dengan Enter" → 5)
Spinbox kartu Pra-Pipeline (v3.11.56) hanya punya DUA jalur commit:
`command=` (HANYA klik panah ▲▼) dan `bind("<Return>")` (HANYA Enter).
Tidak ada `<FocusOut>` dan `_start_pipeline` tidak me-flush — alur natural
user **"ketik 5 → langsung klik 🚀 MULAI PROSES"** membuang nilai secara
SENYAP. Lebih parah: kartu tetap MENAMPILKAN "5" (StringVar berubah saat
mengetik) padahal state H masih 25 — UI menampilkan nilai yang TIDAK
dipakai. Akibat: H terkunci di nilai deteksi saat uncheck Auto (7/14/25)
→ `load_data` menjaga kunci → tab 📦 Deviasi GR & 🧩 Deviasi PCS menampilkan
snap tanggal terdekat (25), bukan 5 yang user minta. Bukti: kontrol
"dengan Enter" menghasilkan 5 — satu-satunya perbedaan = commit.

### Fix
- **`<FocusOut>` commit** di SEMUA 6 spin pra-pipeline (H, ACR, COM,
  Drastis, Manual, Kronis) via `_on_pre_focusout(which)` — commit SENYAP:
  teks tak valid/di luar rentang → balik ke nilai state tanpa dialog
  (FocusOut tidak boleh memicu messagebox modal — fokus berperebutan →
  FocusOut berantai). `_pre_float(..., silent=True)` untuk jalur ini.
- **`_flush_prepipeline_card()`** dipanggil di `_start_pipeline` SETELAH
  semua guard (jalur tombol 🚀, F5, ↻ Refresh Sumber) — jaring pengaman:
  nilai ketik DIJAMIN terpakai run INI walau fokus tidak pernah keluar
  dari spin. Kontrak kartu "set sekali → proses" kini penuh: apa yang
  tertulis di kartu saat MULAI ditekan = yang dipakai render pertama.
- **Guard mode Auto** di `_on_pre_h_change`: checkbox Auto tercentang →
  flush/FocusOut TIDAK mengunci preset dari teks sisa spin (mode Auto =
  tanpa preset, deteksi dinamis utuh).

### Repair test suite (pre-existing, ditemukan saat verifikasi fix)
Suite `test_ui_redesign.py` **CRASH total sejak v3.11.53** (AttributeError
`_dev_bulanan_mode` — API mode-auto dihapus v3.11.53 tapi cek §95-D tak
diupdate; kegagalan bawahnya tertutup crash) + 13 cek stale tertinggal
era v3.9.x–v3.11.8. Kini: **1630 PASS / 3 FAIL** (3 sisanya dependen
lingkungan sandbox Xvfb — clamp layar 1280×900 + metrik font "times";
identik gagalnya di HEAD pra-perubahan ini, hijau di mesin Windows asli).
- §95-D1–D4/D8: kontrak baru mode manual-only (tanpa
  `_dev_bulanan_mode`/`_auto_load_lalu`/SegmentBar; `DeviasiBulananMode`
  tak ditulis lagi).
- §94-E1/§95-D7/§96-D3/§96-D5: fixture file JULI → `19.JULI 2026.xlsx`
  (konvensi prefix 12+bulan v3.11.52).
- §60/§65-F1: `kategori_multi_values` kini 4 nilai rekap+stem (v3.11.45).
- §92-F4: `_kategori_values` nilai rekap kanonik di depan (v3.11.45).
- §63 E2E anak tab: 4 anak tab (+ Saldo Sistem Minus v3.11.42, Analisa
  Kronis v3.11.47).
- Cek versi: hard-pin "3.11.39" (stale 17 versi) → konsistensi
  APP_VERSION ↔ entri teratas CHANGELOG; headline README root+app
  disinkronkan ke v3.11.57.
- App: `_PIPELINE_WARN_RE` + `detect_data_period` (warning fallback
  periode v3.11.9 luput dari pola → tak terhitung `_schema_warnings` —
  kontrak §82b-1).

## v3.11.56 — Pra-Pipeline "set sekali" + deep-link lintas tab + UX (U2–U6)

User: *"kerjakan U2,U3,U4,U5,U6 dan sekarang aku bisa set kolom H atau key
sebelum pipeline biar gak nunggu loading 2x. Pokok nya semua aku bisa set di
awal dulu terus proses pipe line biar gak nunggu 2x"* (U1 — entry Follow-Up
di tab Kronis/Saldo Minus/Audit — TIDAK diminta, di-skip sesuai konfirmasi).

### 1. KARTU PRA-PIPELINE (tab 🚀 Proses) — fitur inti
- Kartu baru **"Pra-Pipeline — set sekali, render pertama langsung pakai"**
  berisi SEMUA parameter analisa yang dulu baru bisa diatur SETELAH pipeline:
  **Tanggal H** (spin + checkbox *"Auto (deteksi dari data)"*), **Ambang ACR
  to BOM**, **Ambang COM ±**, **Ambang Drastis ±**, **Ambang Manual ×**,
  **Saldo Sistem** (42.17/Pivot), **Kronis ≥** (threshold Frek Minus anak
  tab Analisa Kronis).
- **Mekanisme H preset**: `SharedTanggalH.lock_preset(h)` / `clear_preset()`
  (persist `settings.json` key `h_preset`) — `DeviasiView.load_data` TIDAK
  lagi men-snap H ke tanggal SO terakhir data selama preset terkunci →
  render pertama pipeline LANGSUNG memakai H pilihan user, tanpa
  "load pipeline → set H → reload" 2×. Checkbox Auto = perilaku lama utuh.
- Ambang/mode memakai shared state yang SAMA dengan spinbox kartu Filter
  tab 📦/🧩 (sinkron 2 arah — listener) + persist settings.json
  (`drastis_ambang_pct`, `manual_ambang_ratio`, `kronis_threshold`).

### 2. U6 — ambang Drastis & Hitung Manual configurable
- Dulu HARDCODED di compute CEK: Turun Drastis `< 50%`, Naik Drastis
  `> 150%`, Hitung Manual `|SO−W|/|W| > 1.3`. Kini
  `SharedDrastisAmbang` (5–95%) + `SharedManualAmbang` (1,05–5,0) — spinbox
  kartu Filter kedua tab Deviasi + kartu pra-pipeline; ganti = invalidasi
  `SharedPivotCache` + recompute kedua tab (pola ACR/COM v3.9.21/v3.11.12).
  Default 50/1.3 = perilaku lama PERSIS. Label **Beda Tanggal TIDAK ikut**
  (port formula VBA sheet user — kontrak tetap 150%).

### 3. U2 — deep-link navigasi lintas tab
- `DeviasiView.focus_pair(resto, barang)`: reset filter tabel → pasang
  filter kolom Resto/Nama Barang programatik
  (`HeaderFilterGroup.set_selected`) → render → pilih + gulir ke baris
  pasangan (`render_done` → `_consume_pending_focus`; pesan jujur bila
  pasangan tak ada di mode satuan GR).
- Context menu **klik-kanan → "🔎 Buka … di 📦 Deviasi GR"** di tab
  📤 Rekap Selisih IN + anak tab Saldo Sistem Minus & Analisa Kronis +
  tabel per-resto 💰 Nominal Deviasi (resto-saja).
- `app._go_to_deviasi` / `_open_kronis_subtab` (tab 💰 → anak tab Analisa
  Kronis) + `_go_to_tab` (generalisasi `go_to_proses` v3.9.59).
- `AnalisaKronisView.set_threshold()` + `initial_threshold` (pra-pipeline);
  ✕ Reset kembali ke nilai AWAL (bukan konstan 3).

### 4. U3 — Panel Ringkasan hasil pipeline (tab 🚀 Proses)
- Muncul setelah run sukses: stats data (baris/resto/barang + badge H
  preset/auto) · KPI audit (OK/CUT-OFF/DEVIASI MURNI/COM minus) · Follow Up
  aktif · distribusi label CEK (lazy — terisi saat pivot 📦 sudah dihitung,
  disegarkan tiap kembali ke tab Proses) · tombol deep-link ke 5 tab analisa.

### 5. U4 — navigasi keyboard Ctrl+1..9
- Lompat LANGSUNG ke tab ke-n (9 tab). Melengkapi Ctrl+Tab traversal;
  Ctrl+0 tetap reset zoom — tanpa bentrok (Ctrl+F/R/± sudah terpakai).

### 6. U5 — slot hint StatusBar
- `StatusBar.set_hint(text)` (kiri badge versi, ikut dihitung potongan
  status kiri): petunjuk pintasan kontekstual per tab aktif
  (`_on_tab_changed` → `_update_status_hint`) — discoverability tanpa
  dokumentasi terpisah.

## v3.11.55 — FIX AttributeError `'StockMonitorApp' object has no attribute 'after'`

User: log `Exception in Tkinter callback` saat klik tombol 📂 "Pilih file deviasi bulan lalu" di tab Nominal Deviasi.

**Root cause:** `app.py:_load_lalu_paths` (line 6389) memanggil
`run_async(self, ...)` — `self` adalah instance `StockMonitorApp`, **plain
class wrapper** (bukan `tk.Misc`), tidak punya `.after()` / `.master` /
`.winfo_exists()`. Helper `run_async` → `_poll_host(widget)` di widgets.py
naik rantai `.master` utk cari Tk root; karena `StockMonitorApp` tidak punya
`.master`, `_poll_host` return controller itu sendiri → `host.after(70, poll)`
→ `AttributeError`.

**Mengapa baru muncul sekarang:** Bug sudah ada sejak `run_async` ditulis,
tapi jalur manual ini selalu early-return sebelum v3.11.52 (pattern file
hardcode `"20."` → file tidak ketemu → no-op senyap). v3.11.52 memperbaiki
pattern jadi `{12+month}.{BULAN} {TAHUN}` → file bisa ketemu; v3.11.53
menghapus auto-load (hanya tombol 📂 manual tersisa); v3.11.54 rapikan repo
→ user pertama kali benar-benar klik 📂 + pilih file valid → `paths` tidak
kosong → `run_async(self, ...)` pertama kalinya dipanggil end-to-end →
exception muncul.

**Fix:** 1-token perubahan — `run_async(self, ...)` → `run_async(self.root, ...)`.
Mirror precedent yang sudah benar di file yang sama (`app.py:6231` export
Excel). 12 caller `run_async` lainnya (view-view) adalah `tk.Frame` /
`tk.Toplevel` subclass — `_poll_host` berfungsi normal, tidak terkena
dampak.

## v3.11.54 — rapikan repo: hapus dead code + README profesional

User: "Rapikan repo, hapus dead code dan read me rapikan lebih professional dan sesuai kondisi aktual"

### Dead code dihapus
- **`app.py:_auto_load_lalu` method** (~80 baris) — dead code sejak v3.11.53 (call dihapus dari `_on_pipeline_done`, method tetap utk backward-compat). Sekarang dihapus sepenuhnya (gak ada caller lagi).
- **`app.py:_dev_bulanan_mode` method** — SELALU return "manual" sejak v3.11.53, gak dipanggil mana pun. Dihapus.
- **`app.py:_dev_bulanan_last_cfg` attribute** — defined `= None` di `_build_config_tab` tapi gak pernah dibaca. Dihapus.
- **`bench_views.py` script** — referensi `_compute_audit` (sudah dihapus v3.11.30 saat tab 📋 Laporan Deviasi dibongkar). Script broken, tidak dipakai CI/test. Dihapus.
- **Komentar basi** referensi `_auto_load_lalu`, `DeviasiBulananMode='auto'`, `20.{BULAN}` (pattern lama) — diupdate jadi kondisi aktual (`12+month.{BULAN}`, "diisi tombol 📂 di tab ⚙️ Config").

### README dirapikan profesional
- Struktur jelas: **Fitur Utama** · Persyaratan · Cara Pakai · Tab Data · Interaksi Tabel · Struktur Kode · Testing · Build EXE · Konfigurasi · Versi · Lisensi
- **Fitur Utama** ditambah — highlight 9 fitur kunci (pipeline, 9 tab, analisa CEK, saldo minus, analisa kronis, file bulan lalu manual, tooltip, persistensi, DPI-aware)
- **Tab Data** diupdate — 9 tab actual dgn emoji + deskripsi singkat per tab (termasuk sub-tab Saldo Sistem Minus + Analisa Kronis di Nominal Deviasi)
- **Cara Pakai File Deviasi Bulan Lalu** — section baru dgn 5 langkah (pattern `12+month.{BULAN}` dijelaskan)
- **Interaksi Tabel** — tambah tooltip hover cell panjang
- **Struktur Kode** — tree lengkap `src/` dgn deskripsi per file (20+ file ui/ + 12+ file pipeline/)
- **Konfigurasi** — tabel `config.json` + `settings.json` keys dgn deskripsi (RootPath, Folders, Sheets, KategoriBarang4217, DeviasiBulananFolder/Jumlah, DpiAware, acr_threshold, com_ambang_pct, saldo_sistem_mode, KategoriManual)
- Hilangkan referensi `tab 📋 Laporan Deviasi` (dihapus v3.11.30)
- Hilangkan mention "auto-load" (dihapus v3.11.53)

### Verifikasi
- compileall src/ OK · ruff: 18 errors = baseline (no regression)
- Semua import OK (`from src.ui.app import APP_VERSION` = 3.11.54)
- APP_VERSION → 3.11.54; README "Versi terkini: v3.11.54"

## v3.11.53 — HAPUS auto-load deviasi bulan lalu (user: "program jadi not responding waktu load deviasi. hapus auto file deviasi bulan lalu")

User: "program jadi not responding waktu load deviasi. kalau gitu aku pakai pilih file manual aja. hapus auto file deviasi bulan lalu"

**Root cause not responding:** `_auto_load_lalu` dipanggil di `_on_pipeline_done` (line 5566-5567) → parse file deviasi bulan lalu di worker thread → `_notify_lalu_consumers` di main thread → refresh 3 view (Deviasi GR + PCS + Nominal) sync. Tabel besar (892k baris append1) + refresh 3 view bersamaan bisa bekui UI.

**Fix — hapus auto-load sepenuhnya:**
- `app.py:_on_pipeline_done` — hapus `with contextlib.suppress(Exception): self._auto_load_lalu(audit_result)` (line 5566-5567 lama). Pipeline selesai TIDAK otomatis load file deviasi bulan lalu lagi. File deviasi bulan lalu HANYA dimuat via tombol 📂 "Muat Sekarang" di tab ⚙️ Config (manual, saat user butuh saja — gak ada background processing yg bisa bekui UI).
- `app.py:_build_config_tab` — hapus `SegmentBar` mode selector ("🫵 Manual (tombol)" / "⚡ Otomatis pasca-pipeline"). Sekarang HANYA ada tombol "📂 Muat Sekarang". Label ganti "Muat manual:".
- `app.py:_dev_bulanan_load_form` — hapus load `DeviasiBulananMode` dari config (force manual).
- `app.py:_dev_bulanan_save` — hapus simpan `data["DeviasiBulananMode"]` (gak ada mode lagi, key lama di config lama diabaikan).
- `app.py:_dev_bulanan_status_default` — status selalu "manual — muat via tombol (pipeline tidak otomatis memuat)".
- `app.py:_dev_bulanan_mode` — SELALU return "manual" (method tetap ada utk backward-compat kode lama).
- `app.py:_dev_bulanan_save` flash message + log: "mode manual (v3.11.53 — auto-load dihapus, hanya manual)".
- Hapus import `SegmentBar` dari `src.ui.widgets` (F401 unused setelah mode selector dihapus).
- `_auto_load_lalu` method tetap ada di kode (gak dihapus) tapi TIDAK dipanggil lagi dari mana pun — keep utk backward-compat bila kode lain/test masih referensi.

**Backward-compat:**
- `config.json` lama punya `DeviasiBulananMode: "auto"` → diabaikan, gak otomatis load.
- File `20.AGUSTUS` (pattern lama) tetap match (12+8=20).
- Tombol 📂 "Muat Sekarang" tetap berfungsi normal — user klik kapan butuh.

**Verifikasi e2e (5/5 PASS):**
- T1 `_auto_load_lalu` call removed from `_on_pipeline_done` ✓ (grep = 0)
- T2 SegmentBar mode selector removed ✓ (grep = 0)
- T3 `data["DeviasiBulananMode"]` not saved anymore ✓ (grep = 0)
- T4 `_dev_bulanan_mode()` always returns "manual" ✓
- T5 Tombol "📂 Muat Sekarang" tetap ada (manual load still works) ✓
- compileall OK · ruff: 17 errors = baseline (no regression — SegmentBar unused import removed, no new findings).
- APP_VERSION → 3.11.53; README "Versi terkini: v3.11.53".

**Cara pakai sekarang:**
1. Tab ⚙️ Config → kartu "DEV BULANAN" → isi folder + jumlah bulan mundur
2. Klik 💾 Simpan (optional — tombol 📂 baca form saat itu, gak perlu simpan dulu)
3. Run pipeline (Proses) → selesai tanpa auto-load
4. Klik tombol 📂 "Muat Sekarang" SAAT butuh file deviasi bulan lalu → parse async di worker thread → refresh 3 view
5. Kalau gak butuh file bulan lalu, biarkan kosong — pipeline tetap jalan normal

## v3.11.52 — FIX pattern nama file deviasi bulan lalu: prefix 12+month (Jan=13, Okt=22, Agu=20)

User: "ternyata di nama file nya. Januari start dengan angka 13. Jadi 13.JANUARI 2026 dan Oktober menjadi 22.OKTOBER 2026. Perbaiki issue ini"

**Root cause:** `auto_bulanan_paths` (deviasi_file.py) hardcode pattern `"20.{BULAN} {TAHUN}"` — padahal pola asli user pakai prefix nomor urut = `12 + month_number`. Kebetulan untuk Agustus (12+8=20) match dgn "20.", tapi untuk bulan lain (Januari=13, Oktober=22, dll) gak match → file gak ketemu → log "[DEV BULANAN] Auto: belum ada file cocok..." padahal file ada.

**Pattern baru:**
| Bulan | m | prefix = 12+m | Contoh nama file |
|---|---|---|---|
| JANUARI | 1 | 13 | `13.JANUARI 2026.xlsx` |
| FEBRUARI | 2 | 14 | `14.FEBRUARI 2026.xlsx` |
| MARET | 3 | 15 | `15.MARET 2026.xlsx` |
| APRIL | 4 | 16 | `16.APRIL 2026.xlsx` |
| MEI | 5 | 17 | `17.MEI 2026.xlsx` |
| JUNI | 6 | 18 | `18.JUNI 2026.xlsx` |
| JULI | 7 | 19 | `19.JULI 2026.xlsx` |
| AGUSTUS | 8 | 20 | `20.AGUSTUS 2026.xlsx` ← backward-compat match "20." |
| SEPTEMBER | 9 | 21 | `21.SEPTEMBER 2026.xlsx` |
| OKTOBER | 10 | 22 | `22.OKTOBER 2026.xlsx` |
| NOVEMBER | 11 | 23 | `23.NOVEMBER 2026.xlsx` |
| DESEMBER | 12 | 24 | `24.DESEMBER 2026.xlsx` |

**Fix:**
- `deviasi_file.py:auto_bulanan_paths` line 417-418 — ganti `f"20.{_BULAN_NAME[m]} {y}"` → `f"{12+m}.{_BULAN_NAME[m]} {y}"`. Backward-compat: Agustus (12+8=20) tetap match file lama `20.AGUSTUS` tanpa rename. File lama bulan lain (mis. `20.JANUARI`) gak match lagi — user harus rename ke `13.JANUARI` (pola yg benar).

**Verifikasi e2e (5/5 PASS):**
- T1 period Feb 2026 → 1 month back → match `13.JANUARI 2026.xlsx` ✓
- T2 period Nov 2026 → 1 month back → match `22.OKTOBER 2026.xlsx` ✓
- T3 period Sept 2026 → 1 month back → match `20.AGUSTUS 2026.xlsx` ✓ (backward-compat, 12+8=20)
- T4 period Nov 2026 → 2 months back → match `21.SEPTEMBER 2026.xlsx` + `22.OKTOBER 2026.xlsx` (kronologis lama→baru) ✓
- T5 whitespace variant `22. OKTOBER 2026.xlsx` (spasi setelah titik) → match ✓ (FIX v3.11.50 #17 masih kerja)
- compileall OK · ruff: baseline (no regression).
- APP_VERSION → 3.11.52; README "Versi terkini: v3.11.52".

## v3.11.51 — FIX false-positive warning settings.json FileNotFoundError di first run

User log v3.11.50: baris pertama log tab 🚀 Proses berbunyi `[PERINGATAN] Filter persist: gagal membaca settings.json (FileNotFoundError(2, 'No such file or directory')) — kombinasi filter tersimpan TIDAK dipulihkan sesi ini.`

**Root cause:** `_load_filter_state` (app.py:1926) catch `OSError` (yg includes `FileNotFoundError`) dan treat sebagai ERROR — padahal `FileNotFoundError` di first run (file belum dibuat) adalah **expected behavior**. User install baru / pindah folder → selalu lihat warning ini meski tidak ada masalah. Save_filter_state akan create file saat close app pertama kali.

**Fix:**
- `app.py:_load_filter_state` — split `except FileNotFoundError` (silent return None, expected) dari `except (OSError, ValueError, TypeError)` (warning tetap muncul utk PermissionError / JSON korup / dll). Komentar jelas: "file belum ada = first run / install baru / pindah folder. EXPECTED — save_filter_state akan create file saat close app."

**Verifikasi e2e (3/3 PASS):**
- **T1** `FileNotFoundError` → return None, `_FILTER_LOAD_WARNINGS` tetap kosong (no warning) ✓
- **T2** JSON korup → return None, warning muncul `[PERINGATAN] Filter persist: gagal membaca settings.json (JSONDecodeError(...))` ✓ (preserve behavior)
- **T3** Valid settings.json → return dict `{'deviasi_gr': {'kategori': 'Deviasi'}}`, no warnings ✓ (preserve behavior)
- compileall OK · ruff: 22 errors = baseline (no regression).
- APP_VERSION → 3.11.51; README "Versi terkini: v3.11.51".

## v3.11.50 — fix Deviasi Bulan Lalu (13 findings dari audit deep cek)

User: "auto file deviasi bulan lalu ini apakah ada bug? sehingga tidak muncul di tab mana pun? Deep cek dulu" → "fix semua".

Deep audit 2 agent paralel audit end-to-end pipeline Deviasi Bulan Lalu → 17 findings. 13 paling impact-ful di-fix; 4 LOW/defensive skip (comment wording, dead param, race window, AGS typo redundan dgn singkatan lain). **Root cause utama "tidak muncul di tab mana pun": default `DeviasiBulananMode='manual'` + folder hilang → silent no-op tanpa log.**

### CRITICAL fix
- **#1 default mode `manual` silent no-op** (`app.py:_auto_load_lalu`): sebelumnya `if self._dev_bulanan_mode() != "auto": return` TANPA log → user gak tau kenapa kolom 'Dev. Bulan Lalu' kosong. FIX: log jelas "[DEV BULANAN] Mode Manual — auto-load dilewati. Klik 📂 'Muat Sekarang' di tab ⚙️ Config, atau set DeviasiBulananMode='auto' di config.json".
- **#2 `_dev_bulanan_cfg` return None silent** (`app.py:_auto_load_lalu`): folder hilang / config invalid / period invalid → silent return. FIX: log jelas KENAPA cfg None — "folder deviasi bulanan TIDAK ADA / belum dikonfigurasi — '{folder}'" atau "folder '{folder}' ada tapi periode data tidak valid".
- **#3 period fallback pakai jam sistem** (`main.py:detect_data_period`): bila timestamp & Nomor regex gagal, fallback `datetime.now()` → mismatch bila user proses data lama di bulan berbeda → auto_bulanan_paths cari file bulan SALAH. FIX: log WARNING jelas "[WARNING] detect_data_period gagal — fallback periode jam sistem: YYYY-MM. Bila data lama, auto-load file deviasi bulan lalu mungkin miss".
- **#4 STALE `_lalu_file_df` lintas run** (`app.py:_auto_load_lalu` + `_load_lalu_paths`): Run 1 sukses load, Run 2 gagal → `_lalu_file_df` LAMA tetap dipakai consumer (data basi, kolom tetap nunjukkin data bulan lalu yg salah tanpa warning). FIX: clear `self._lalu_file_df = None` + `_notify_lalu_consumers()` di AWAL `_auto_load_lalu` (mode auto) + di `_load_lalu_paths.done` bila semua file gagal parse.

### HIGH fix
- **#5 label tombol "Muat ke Komparasi Sekarang"** (`app.py`): tab Komparasi sudah dihapus v3.11.30! User bingung. FIX: ganti ke "📂 Muat Sekarang".
- **#6 footer popup "(Komparasi)"** (`nominal_resto_view.py:1801, 2275`): referensi tab yg sudah dihapus. FIX: ganti ke "(klik 📂 di tab ⚙️ Config)".
- **#7 `_lalu_loaded = fdf is not None`** (`nominal_resto_view.py:1451`): empty df dianggap "loaded" → popup footer misleading "tanpa pasangan" padahal file kosong total. FIX: `fdf is not None and not getattr(fdf, "empty", True)`.
- **#8 `parse_deviasi_file` empty df after bad_week** (`deviasi_file.py:306-308`): kalau SEMUA baris punya Minggu tak dikenal ("PERIODE 1", "AKHIR") → return `ok=True, df=<empty>` → log "1 file dimuat (0 baris)" menyesatkan. FIX: cek `if out.empty` setelah bad_week filter → return `ok=False` dgn error jelas.
- **#9 `_BULAN_NUM` missing "AGS"** (`deviasi_file.py:43-51`): singkatan umum Agustus "AGS" tidak ada → semua baris August dgn label "AGS" jadi bulan_num=0 → parse rusak. FIX: tambah `"AGS": 8`.

### MEDIUM fix
- **#10 `_notify_lalu_consumers` contextlib.suppress** (`app.py:6322, 6327`): consumer exception senyap, debugging impossible. FIX: ganti ke try/except dgn `print("[WARNING] ...")`.
- **#12 `_lalu_provider()` exception senyap** (`nominal_resto_view.py:1448-1451`): contextlib.suppress(Exception). FIX: try/except dgn log WARNING.

### LOW fix
- **#17 filename whitespace strict** (`deviasi_file.py:auto_bulanan_paths`): "20. AGUSTUS 2026.xlsx" (spasi setelah titik) gak match "20.AGUSTUS 2026" target. FIX: normalisasi `re.sub(r"\s+", " ", base)` + `re.sub(r"\.\s+", ".", base)` di by_base keys + want target — case-insensitive + whitespace-tolerant.

### LOW yang TIDAK di-fix (deferred)
- #11 async race window (table render ~7s sebelum auto-load selesai) — perlu loading chip UI, defer.
- #13 default folder Windows path absolut — by-design (user set sendiri di ⚙️ Config).
- #15 sub-tab "Nominal Deviasi Bulan Lalu" TIDAK ADA — itu KOLOM di tab "Per Resto" + popup drill-down (double-click baris), bukan sub-tab terpisah — by-design.
- #16 dead `anchor` param di loop — false alarm, valid unpacked tuple usage.

### Verifikasi — Xvfb GUI test + e2e pandas (4/4 PASS)
- **T1** `_lalu_loaded = False` ketika provider returns None (sebelumnya True) — FIX #7 ✓
- **T2** `_lalu_loaded = False` ketika provider returns empty DataFrame (sebelumnya True) — FIX #7 ✓
- **T3** label "Muat ke Komparasi Sekarang" sudah dihapus dari app.py (grep = 0) — FIX #5 ✓
- **T4** footer "belum dimuat (Komparasi)" sudah dihapus dari nominal_resto_view.py (grep = 0) — FIX #6 ✓
- Plus e2e pandas: `_BULAN_NUM.get("AGS") == 8` ✓ (FIX #9) · `auto_bulanan_paths` whitespace normalization — 3 variants filename (`20.AGUSTUS 2026.xlsx`, `20. AGUSTUS 2026.xlsx`, `20.  AGUSTUS 2026.xlsx`) all match same target → 1 path returned ✓ (FIX #17).
- compileall src/ OK · ruff: 22 errors = baseline (no regression).
- APP_VERSION → 3.11.50; README "Versi terkini: v3.11.50".

### Catatan ke user (penyebab utama "tidak muncul")
1. **Mode default = `manual`** — kamu harus klik tombol 📂 "Muat Sekarang" di tab ⚙️ Config, ATAU set `DeviasiBulananMode: "auto"` di `config.json`.
2. **Folder config salah / belum di-set** — default `C:\KERJA\1. RESTO\99.TOOLS\DATA BASE DEVIASI\DEVIASI_BULANAN` mungkin gak ada di komputer kamu.
3. **File `20.{BULAN} {TAHUN}.xlsx` harus ada di folder yg dikonfigurasi** — nama PERSIS (sekarang whitespace-tolerant: "20. AGUSTUS 2026.xlsx" juga match).
4. **Kalau file pakai singkatan "AGS" utk Agustus** — sekarang sudah didukung (FIX #9).
5. **Sekarang setiap exit path auto-load kelog jelas** — kamu bisa self-diagnose di tab 🚀 Proses.

## v3.11.49 — FIX regression v3.11.48: tooltip muncul di pojok kiri atas (wm_transient konflik overrideredirect)

User: "tooltip berada di pojok kirii atas?" — regression dari v3.11.48 audit fix #5 (cell_tooltip.py _render_tip).

**Root cause:** v3.11.48 menambahkan `wm_transient(tree.winfo_toplevel())` untuk reliability Linux X11 (audit #5 concern: tip bisa tertutup Toplevel lain). TAPI `wm_transient` pada `wm_overrideredirect(True)` Toplevel **konflik di Windows Tk** — `wm_transient` trigger WM interaction yang reset posisi window ke default (0, 0) → tip muncul di **pojok kiri atas layar**, bukan dekat cursor.

**Fix:**
- `cell_tooltip.py:_render_tip` — HAPUS `wm_transient(tree.winfo_toplevel())` sepenuhnya. Audit #5 concern (tip obscured by other Toplevels in X11) sudah diatasi oleh `self._tip.lift()` saja (line bawah, ditambah v3.11.48) — tidak butuh `wm_transient`.
- Bonus: `wm_geometry(f"+{x}+{y}")` (position-only) → `wm_geometry(f"{w}x{h}+{x}+{y}")` (full geometry format) untuk reliability cross-platform — beberapa Tk version tidak stick dengan position-only format.

**Verifikasi — Xvfb test SUNGGUHAN:**
- Hover cell CEK row_0 di Xvfb :99 → pointer warped ke (500, 129) → tip muncul di **(514, 147)** = pointer + offset (14, 18) — TEPAT dekat cursor, BUKAN (0, 0) pojok kiri atas.
- `assert tip_x > 50` PASS (514 > 50) · `assert tip_y > 50` PASS (147 > 50) · `assert abs(tip_x - expected_x) < 200` PASS (0 < 200).
- compileall OK · ruff: cell_tooltip All checks passed.
- APP_VERSION → 3.11.49; README "Versi terkini: v3.11.49".

**Catatan:** audit #5 v3.11.48 (tip obscured Toplevel lain in X11) adalah concern minor — `lift()` saja cukup. `wm_transient` over-engineering yang malah jadi regression. Pelajaran: jangan tambah `wm_transient` pada `overrideredirect(True)` window — keduanya konflik (overrideredirect = bypass WM; transient = minta WM manage).

## v3.11.48 — deep audit fix (5 agent paralel → 22 findings, 14 fixed)

User: "Deep audit sebar agent dan fix" — 5 agent di-launch paralel audit v3.11.47 (cell_tooltip.py · saldo_minus_view + analisa_kronis_view · nominal_common · nominal_resto_view wiring · deviasi_view tooltip integration). 22 findings terkumpul (2 CRITICAL, 7 HIGH, 5 MEDIUM, 8 LOW). 14 paling impact-ful di-fix; sisanya LOW/dead-code/defensive — didokumentasikan di CHANGELOG.

### CRITICAL fix
- **#7 deviasi_view provider dead code** (`deviasi_view.py:1046-1060`): tuple `"NAMA BARANG", "KATEGORI", "NOMOR PO", "#KET PO"` TIDAK match column id tree (`"Nama Barang"` title-case; KATEGORI dihapus v3.9.29; NOMOR PO/#KET PO tidak pernah ada). Ganti ke `col == "Nama Barang"` saja — tip sekarang JALAN di kolom Nama Barang panjang (sebelumnya dead code, tip cuma muncul di CEK).
- **#8 CellTooltip NOT bound to clone ⛶ maximize tree** (`deviasi_view.py:_maximize` +3779-3813): user klik ⛶ Perbesar → clone `new_tree` dibuat TANPA CellTooltip → tip tidak muncul di window maximize (padahal scenario utama user "cek CEK panjang" sering di maximize). FIX: instantiate `CellTooltip(new_tree, provider=_clone_tip_provider, ...)` di `_maximize`; simpan `win._cell_tip` + cleanup hook `_cell_tip_cleanup` (dipanggil `_close_stale_clones`).

### HIGH fix
- **#1 cell_tooltip.py destroy() wipe ALL bindings** (`cell_tooltip.py`): `unbind(seq, None)` calls `tk.call('bind', w, seq, '')` → CLEARS ALL bindings for that sequence (incl deviasi_view `_on_tree_motion` cursor hand2, `enable_multi_select` Button-1, `CellColorOverlay._on_destroy`, dll). FIX: capture funcid tiap `bind(..., add="+")` (motion/leave/button1/destroy), pass ke `unbind(seq, fid)` → hanya lepas binding CellTooltip sendiri.
- **#2 CellColorOverlay blocks Motion** (`widgets.py:_FORWARD_SEQS`): overlay Labels (child of tree, untuk cell-tag warna di Tk 8.x) menelan Motion event → CellTooltip._on_motion TIDAK fires di cell ber-tag (CEK com_tinggi_cell/com_rendah_cell/resto_khusus_cell — paling penting!). FIX: tambah `"<Motion>", "<Leave>"` ke `_FORWARD_SEQS` → label forward event ke tree.
- **#3 Tree `<Leave>` fires spuriously** (`cell_tooltip.py:_on_leave`): pointer masuk overlay Label (child tree) → tree `<Leave>` fires → tip flicker off. FIX: `_on_leave` cek `winfo_containing(x_root, y_root)`, bila pointer MASIH di tree atau descendant → skip cancel (pola winfo_parent walk).
- **#4 zebra per-group BREAKS after manual sort** (`saldo_minus_view.py` + `analisa_kronis_view.py`): tags follow iid, sort reorders rows → zebra random. FIX: `_reapply_zebra_per_group()` method — walk `tree.get_children("")` in visible order, toggle parity saat Nama Barang berubah, re-apply tags via `tree.item(iid, tags=...)`. Pass sebagai `on_done` ke `sort_tree_by_column` + di `render_done` post-insert.
- **#5 cell tags (neg_cell, resto_khusus_cell) LOST after sort** (sama): sort_tree_by_column delete+insert ulang, cell tag mapping tidak di-preserve. FIX: `_reapply_zebra_per_group()` juga re-apply `apply_cell_tag(tree, "neg_cell", ...)` + `"resto_khusus_cell"`.
- **#6 filter ⧩ "Mulai Minus" silent skip** (`saldo_minus_view.py:_compute`): display col "Mulai Minus" ≠ df col "Tgl Mulai Minus" → filter guard `if col in filtered.columns` False → filter silently skipped. FIX: filter loop pakai `_col_to_df(col)` resolve display→df.
- **#9 `_on_view_destroy` no explicit CellTooltip destroy** (`deviasi_view.py:_on_view_destroy`): relied on Tk destroy cascade (not deterministic). FIX: explicit `self._cell_tip.destroy()` + `self._close_stale_clones()` di awal `_on_view_destroy`.
- **#10 filter ⧩ popup "Resto" EMPTY** (`saldo_minus_view._col_values` + `analisa_kronis_view._col_values`): display "Resto" ≠ df "NAMA RESTO". FIX: tambah `"Resto": "NAMA RESTO"` ke `_col_to_df` map; `_col_values` resolve via `_col_to_df`.

### MEDIUM fix
- **#11 manual sort lost on every `_refresh()`** (`saldo_minus_view` + `analisa_kronis_view`): _render rebuild dari df order (default sort), bukan user's last sort. FIX: di `render_done`, cek `getattr(tree, "_last_sort", None)` + re-apply via `sort_tree_by_column(..., on_done=self._reapply_zebra_per_group)`.
- **#12 old tip lingers on cell change** (`cell_tooltip.py:_on_motion`): user move cell A→B → tip A tetap visible 500ms. FIX: `_hide_now()` di else-branch sebelum schedule tip baru.
- **#13 `-topmost` unreliable on Linux X11** (`cell_tooltip.py:_render_tip`): FIX: `wm_transient(tree.winfo_toplevel())` + `self._tip.lift()` setelah `wm_geometry` — tip selalu di atas parent.
- **#14 tip overflow when taller than screen** (`cell_tooltip.py:_render_tip`): tip 30+ baris di screen 768px → clipped. FIX: bila `h > sh - 8`, reduce `wraplength` proporsional → tip muat.

### LOW fix
- **#15 threshold Spinbox allows > H** (`analisa_kronis_view:_on_threshold_changed`): `min(31, v)` bisa > H → kronis always empty. FIX: `min(self.tanggal_h, v)`.
- **#17 docstring column count mismatch** (`analisa_kronis_view.py:75`): comment "(10 — user spec)" tapi list 11 items. FIX: update ke "(11 — user spec)".
- **#19 dead rename "Tgl Mulai Minus" → "Mulai Minus"** (`nominal_common.hitung_saldo_minus_kronis`): column produced tapi NEVER displayed/exported di KRONIS_COLUMNS. FIX: hapus rename; "Tgl Mulai Minus" tetap di df (tidak digunakan view, konsisten dgn minus_df asli).
- **#20 stats_out["threshold"] set before clamp** (`nominal_common.hitung_saldo_minus_kronis`): init pakai pre-clamp value. FIX: move `threshold = max(1, int(threshold))` SEBELUM `stats_out.update(...)`, update `stats_out["threshold"]` konsisten.

### LOW yang TIDAK di-fix (deferred — dead code / defensive / cosmetic)
- `cell_tooltip.truncate_provider` + `set_provider` — dead code, tidak ada caller (tidak mengganggu).
- `nominal_common.hitung_saldo_minus_pairs iterrows()` performance — pre-existing, acceptable.
- CEK tip threshold `>= 20` arbitrary — would need `tkfont.Font().measure()` (over-engineering).
- Absolute import `from src.ui.details_popup` — style inconsistency, tidak break.

### Verifikasi — GUI test Xvfb SUNGGUHAN (7/7 PASS)
- **T1** SaldoMinus `_col_values('Resto')` = `['BDGSEK', 'MLGPAR', 'TGRBIN']` (3 resto) — popup NOT empty (sebelumnya empty).
- **T2** SaldoMinus `_col_values('Mulai Minus')` = `['3', '4', '5']` — popup NOT empty (sebelumnya empty).
- **T3** Zebra per-group SETELAH sort: parity sequence `[0, 1, 0]` — alternating benar (sebelumnya random).
- **T4** `smv._neg_cells` populated (6 cells) — `_reapply_zebra_per_group` called, neg_cell re-applied.
- **T5** Threshold set 31 → clamped ke 7 (= H) — `assert kv.threshold == 7` PASS.
- **T6** CellTooltip funcids properly captured: `motion=...140150004095936_on_m, leave=...140149982915584_on_l` (sebelumnya None).
- **T7** CellTooltip.destroy() TIDAK wipe dummy Motion handler — `bound` contains `dummy_motion` (sebelumnya wiped).
- Plus e2e pandas sintetis (3 pasangan, 1 eksklusif + 1 global): `hitung_saldo_minus_kronis` threshold=3 → 2 kronis, eksklusif_pairs=1, dead rename removed (`'Mulai Minus' not in k.columns`), stats threshold konsisten.
- **compileall src/ OK** · ruff: cell_tooltip + analisa_kronis + saldo_minus = All checks passed; deviasi_view + nominal_common + nominal_resto_view = baseline (tidak ada temuan baru).
- APP_VERSION → 3.11.48; README "Versi terkini: v3.11.48".

## v3.11.47 — zebra per-group Nama Barang (tab Saldo Minus) + tooltip hover cell CEK (Deviasi GR/PCS) + anak tab "Analisa Kronis" (pasangan kronis minus + eksklusif)

User: "zebra grup di tab minus perbaiiki sehingga jadi per group nama barang. dan bisa gak untuk kolom cek di tab deviasi gr dan deviasi pcs kan kadang terlalu panjang ke kanan misal aku klik cell itu terus muncul pop up tampilan lengkap nya bisa gak? jagan buat kode dulu buat ide. tambahin analisa juga di saldo minus dengan nama barang yang sering minus dan hanya barang itu aja yang minus di resto itu."

Konfirmasi user via balasan ide: Fitur 1 = opsi 1A (sort Nama Barang asc → |qty| desc + zebra per-group); Fitur 2 = opsi 2A (tooltip hover saja); Fitur 3 = interpretasi C (pasangan kronis + eksklusif resto-spesifik) + threshold default 3 tanggal + sub-tab baru (3-i) + KPI.

### Fitur 1 — Zebra per-group Nama Barang (tab Saldo Sistem Minus)
**Sebelum:** zebra by index baris (`i % 2`) → 1 barang muncul di 5 resto → 5 baris warna acak, susah dilihat sebagai 1 grup.
**Sekarang:**
- `hitung_saldo_minus_pairs` LANGKAH 8 — sort default diubah: `Nama Barang ASC → |Qty Mulai Minus| DESC` (dulu `|qty| desc` saja) — baris dgn barang SAMA berdekatan (grup visual), dalam grup paling minus di atas;
- `saldo_minus_view._compute` — zebra parity berganti SAAT nilai Nama Barang berubah (bukan tiap baris) → efek "blok" per barang; grup pertama = evenrow (putih), grup kedua = oddrow (abu), dst;
- Sort klik header tetap bekerja (sort_tree_by_column) — zebra saat user sort manual akan ikut grup barang (selama sort default dipertahankan atau user sort by Nama Barang).

### Fitur 2 — Tooltip hover cell CEK yang kepotong (Deviasi GR/PCS + Saldo Minus + Analisa Kronis)
**Sebelum:** kolom CEK tampil teks `"Rank 3 · Turun Drastis · Beda dari Resto Lain (BBG TGR 5,2 kg · BJMHAS 3,1 kg) · ACR to BOM 12%"` (108+ char) → terpotong `…`, tidak ada cara lihat full-nya.
**Sekarang:**
- `cell_tooltip.py` (BARU, ~240 baris) — `CellTooltip` reusable: bind `<Motion>` `add="+"` (tidak mengganggu handler cursor hand2 deviasi_view), hover 500ms di cell target → Toplevel tip kecil dekat cursor (clamp ke layar, topmost, wrap 460-540px), mouse leave / klik / cell berubah → cancel + hide;
- `deviasi_view` — tip untuk kolom **CEK** (dari `_cek_map` RAW, min 20 char) + kolom NAMA BARANG/KATEGORI/NOMOR PO/#KET PO (≥ 30 char anti-noise);
- `saldo_minus_view` — tip untuk kolom Keterangan / Nomor PO / Status PO / Resto / Nama Barang (≥ 30 char);
- `analisa_kronis_view` — tip untuk kolom Rekomendasi (narasi panjang 170+ char) + Resto + Nama Barang;
- Tidak konflik dgn single-click ✓ (follow-up) atau double-click drill-down (tooltip cuma Toplevel pasif, no grab).

### Fitur 3 — Anak tab "Analisa Kronis" (sub-tab ke-3 di 🧮 Nominal Deviasi)
**User:** "tambahin analisa juga di saldo minus dengan nama barang yang sering minus dan hanya barang itu aja yang minus di resto itu" → interpretasi C: pasangan (Resto, Barang) kronis + eksklusif.

**Baru:**
- `nominal_common.hitung_saldo_minus_kronis(data, h, saldo_sistem_map, mode_4217, threshold=3, stats_out)` — re-use `hitung_saldo_minus_pairs` (minus_df dgn kolom baru `Frek Minus`), filter `frek >= threshold`, hitung "resto lain yg juga minus" per barang (groupby Nama Barang → nunique NAMA RESTO di SEMUA pasangan minus, bukan hanya kronis — supaya non-kronis di resto lain tetap dihitung sbg "resto lain juga minus"), flag Eksklusif ✅/✗, narasi Rekomendasi (resto-spesifik vs barang global);
- `hitung_saldo_minus_pairs` extend: tambah kolom `Frek Minus` (jumlah tanggal minus di 1..H) — kolom BARU, tidak mengubah kontrak view existing (saldo_minus_view tidak menampilkannya);
- `analisa_kronis_view.py` (BARU, ~700 baris) — `AnalisaKronisView(tk.Frame)` mirror SaldoMinusView: 11 kolom (Resto · Nama Barang · Satuan · Frek Minus · Total Durasi · Tipe · Min Qty · Max Qty · Eksklusif · Resto Lain · Rekomendasi); KPI (pasangan kronis · eksklusif · resto kronis terbanyak); filter ⧩ + sort; double-click drill-down details_popup; export Excel; tag eksklusif_row (hijau) / global_row (ungu); tooltip Rekomendasi; **Spinbox threshold 1..31** (default 3 — user bisa naikkan/turunkan "kronis" definition); zebra per-group Nama Barang (konsisten Fitur 1); subscribe h_state + saldo_sistem_state (konsisten dgn SaldoMinusView);
- `nominal_resto_view._sub_nb` — sub-tab ke-4 "Analisa Kronis"; wiring `load_data` + `ensure_refreshed` + `_on_sub_tab_changed` propagate ke `_kronis_view` (pola v3.11.44 saldo minus);
- Status kosong jujur (pola v3.9.46/v3.11.45): "0 pasangan minus (2.SALDO AKHIR) di 1..H — pipeline belum dijalankan" vs "N pasangan minus dipindai tapi TIDAK ADA yg Frek Minus ≥ threshold — coba turunkan threshold";
- Log 1 baris `[ANALISA KRONIS] mode=… · H=… · thr=… · N total · N kronis · N eksklusif · N tampil` tiap compute (stdout → tab 🚀 Proses).

### Verifikasi — GUI test Xvfb SUNGGUHAN (bukan cuma logic)
- **CellTooltip standalone 5/5 PASS**: provider CEK panjang muncul (len 108) · provider cell pendek (< 30 char) return None (anti-noise) · Motion event ke cell CEK → tip Toplevel visible setelah delay · Leave → tip hidden;
- **AnalisaKronisView + SaldoMinusView e2e 7/7 PASS**: T1 SaldoMinusView 3 baris (3 pasangan minus) · T2 AnalisaKronisView 2 baris (2 kronis, threshold 3) · T3 zebra per-group parity beda (BPG=evenrow, GULA=oddrow) · T4 Eksklusif ✅ untuk BPG (frek 5) + GULA (frek 3) · T5 CellTooltip attached ke kedua view · T6 threshold=5 → cache invalidate + recompute → 1 baris (BPG only) · T7 tooltip provider Rekomendasi return teks 172 char;
- **E2E pandas sintetis** (3 pasangan, 1 eksklusif + 1 global): hitung_saldo_minus_kronis threshold=3 → 2 kronis, eksklusif_pairs=1, Resto Lain benar (BPG=1 krn BDGSEK juga minus, GULA=0 krn eksklusif);
- **compileall src/ OK** · ruff: cell_tooltip + analisa_kronis_view + saldo_minus_view = All checks passed; deviasi_view baseline (4 errors pre-existing, I001 fixed via --fix); nominal_common + nominal_resto_view = baseline (1 error pre-existing each);
- APP_VERSION → 3.11.47; README "Versi terkini: v3.11.47".

## v3.11.46 — versi build di baris pertama log pipeline (log yang di-copy langsung teridentifikasi)

User: "build nya masih 3.11.43. padahal sudah download dari git hub terbaru" — verifikasi langsung `git ls-remote origin`: **GitHub main sudah v3.11.45** (semua fix kategori manual + saldo minus TER-upload; README GitHub pun sudah bilang "Versi terkini: v3.11.45"). Jadi app yang dijalankan user masih kode lama — download-nya tidak benar-benar mengambil yang terbaru (zip GitHub kena cache browser / menjalankan exe lama / extract ke folder lama). Dua putaran debug "tetap sama aja" (v3.11.44/45) berpotensi akibat ambigu versi; judul window + statusbar (v3.11.45) ternyata **kurang terlihat saat user melapor pakai log**.

**Fix — versi tampil DI LOG (media yang user copy-paste saat lapor):**
- `app.py` `_run_pipeline`: baris `BUILD v{APP_VERSION}` tepat setelah separator `====` di awal **tiap run** (run baru maupun Refresh Sumber) — baris pertama log selalu menyebut versi;
- `main.py` `run_pipeline` banner: `Build: v{APP_VERSION}` di bawah "STOCK MONITORING - PIPELINE RUNNER" — import `src.ui.app` **lazy saat call** (app.py hanya lazy-import modul ini di dalam fungsi; import balik di top-level akan membuat cycle saat module load; CLI/standalone tanpa UI → baris dilewati via try/except);
- `APP_VERSION` → 3.11.46.

**Verifikasi**: py_compile `app.py` + `main.py` OK · ruff kedua file = baseline (tanpa kategori temuan baru) · urutan log: `====` → `BUILD v3.11.46` → `Memulai pipeline…/REFRESH FILE SUMBER` → Pre-flight → banner RUNNER `Build: v3.11.46`.

**Catatan untuk user (download yang benar):** zip GitHub (`main.zip`) sering disajikan browser dari **cache lama** — unduh lewat jendela incognito/private (atau Ctrl+F5 halaman repo dulu), extract ke **folder BARU**, lalu **copy `config.json` dari folder lama** (agar RootPath + mapping `KategoriManual` ikut) dan jalankan `MULAI.bat` dari folder baru. Bila selama ini memakai `.exe` hasil build: download source TIDAK mengubah exe — jalankan dari source atau rebuild exe (`build_exe.py`). Cek versi: judul window / statusbar kanan bawah / baris pertama log.

## v3.11.45 — fix AKAR "kategori manual tetap gak masuk" (stem 'COM DEVIASI' vs filter default) + status saldo minus JUJUR + versi di judul window

User: "tetap gak masuk untuk mapping manual. nam item nya BAWANG PUTIH GORENG itu gak masuk ke tab devias gr padahal aku udah set jadi COM DEVIASI. tab saldominus juga kosong dengan mode pivot atau mode 42.17"

**Bug #1 — ROOT CAUSE SEBENARNYA (kenapa v3.11.43 & v3.11.44 'tetap sama aja'): TAXONOMI NILAI, bukan mekanisme apply.**
Reproduksi terkontrol (data realistis + Xvfb GUI test) membuktikan rantai lengkapnya:
- mapping manual user disimpan dgn nilai **"COM DEVIASI"** (bentuk pendek — dipilih/diketik di dialog; instant-apply v3.11.44 & LANGKAH 5d BEKERJA — nilai KATEGORI baris barang benar-benar jadi "COM DEVIASI" — GUI test T4: barang MUNCUL saat seleksi eksplisit 'COM DEVIASI');
- TAPI seleksi DEFAULT semua tab ber-filter kategori = entri gabungan **"Deviasi (COM + Packaging)"** yang hanya mencocokkan 2 nilai rekap ber-suffix: `"COM DEVIASI - RESTO"` & `"Biaya Packaging - RESTO"` (`kategori_multi_values` → `kategori_filter_mask`);
- `"COM DEVIASI"` ≠ `"COM DEVIASI - RESTO"` → barang TER-APPLY tapi TERSEMBUNYI oleh filter default di Deviasi GR/PCS · Nominal · Pivot · Rekap Selisih IN → terlihat "gak masuk"/"tetap sama aja" di SEMUA versi sejak fitur mapping lahir (v3.11.7). GUI test T3 (pra-fix): BAWANG PUTIH GORENG TIDAK tampil dgn filter default.

**Fix (satu titik — semua tab): `pipeline/helpers.py`**
- `KATEGORI_REKAP_STEMS = ("COM DEVIASI", "Biaya Packaging")` + `KATEGORI_GABUNGAN_VALUES = KATEGORI_REKAP_VALUES + KATEGORI_REKAP_STEMS`;
- `kategori_multi_values()` kini mengembalikan tuple extended → seleksi gabungan default **mencocokkan stem bentuk pendek juga** (case-insensitive — `kategori_filter_mask` sudah upper());
- `kategori_has_default_values()` ikut extended → data yang hanya ber-nilai stem pun mendapat entry default yang cocok;
- `in_selisih_view._default_kategori_value` scan `KATEGORI_GABUNGAN_VALUES` (default header ⧩ KATEGORI Rekap Selisih IN ikut menangkap stem);
- `KATEGORI_REKAP_VALUES` asli TIDAK berubah (chips rekap in_selisih_view dkk. tetap nilai penuh);
- `app._kategori_values()` (dialog Identifikasi/Edit): nilai rekap kanonik DI DEPAN daftar — arahkan mapping baru ke nilai penuh (lebih rapi), walau stem kini pun cocok.

**Bug #2 — saldo minus: wiring v3.11.44 TERVERIFIKASI LAGI bekerja (GUI Xvfb: klik sub-tab → 2 baris; ganti mode pivot → 2 baris). Untuk kasus user yang masih kosong, kini app BILANG KENAPA:**
- `hitung_saldo_minus_pairs(..., stats_out=...)` — breakdown in-place: `saldo_rows`/`saldo_pairs`/`minus_pairs`/`excluded_src`/`shown`/`schema_ok` (semua exit point terisi);
- status kosong JUJUR (pola v3.9.46): "0 pasangan ber-saldo … pipeline belum dijalankan" vs "N pasangan dipindai — TIDAK ADA yang pernah minus (mode …)" vs "N pasangan minus tapi SEMUA ber-sumber Internal — filter tab ini hanya Eksternal/Campuran" (kemungkinan besar inilah jawaban kasus user: minus-nya Internal, atau build/exe belum v3.11.44+);
- status non-kosong + " · N lain dibuang (Internal)" bila ada;
- **log 1 baris `[SALDO MINUS] mode=… · H=… · … tampil`** tiap compute (cache rebuild) — stdout ter-redirect ke tab 🚀 Proses → laporan user berikutnya langsung menunjukkan angka scan.

**Bonus — versi di judul window**: `APP_TITLE — Python Edition · v{APP_VERSION}` — menutup ambigu "user jalankan build lama?" (dua laporan 'tetap sama aja' berpotensi exe belum di-update; kini versi terlihat di title bar + screenshot).

**Verifikasi**: repro pure-pandas (filter mask: 'COM DEVIASI' kini match — pra-fix False) + GUI Xvfb alur user penuh: T1 wiring sub-tab 2 baris PASS · T2 mode pivot 2 baris PASS · **T3 BAWANG PUTIH GORENG tampil dgn filter default PASS (pra-fix FAIL)** · T4 seleksi eksplisit 'COM DEVIASI' PASS · py_compile semua file OK · ruff = baseline per file.

## v3.11.44 — FIX WIRING saldo minus (root cause "tidak terjadi apa apa") + kategori manual INSTANT-APPLY

User: "kok sama aja? tidak terjadi apa apa" — analisa mendalam menemukan **ROOT CAUSE sebenarnya** (v3.11.43 salah diagnosis arah):

**Bug #2 — saldo minus kosong: ROOT CAUSE = WIRING, bukan filter SOURCE KIRIMAN.**
`SaldoMinusView` punya siklus lazy refresh SENDIRI: `load_data` saat tab tersembunyi (pipeline run — user di tab Proses) hanya menandai `_dirty = True` (tabel tidak dirender). Sementara:
- app `<<NotebookTabChanged>>` hanya memanggil `nominal_resto_view.ensure_refreshed()` — yang hanya refresh tabel UTAMA 'Per Resto', TIDAK pernah propagate ke `_saldo_minus_view`;
- sub-notebook `_sub_nb` TIDAK punya binding `<<NotebookTabChanged>>` sama sekali.
Akibatnya `_dirty` TIDAK PERNAH di-clear → tabel 'Saldo Sistem Minus' menampilkan "Belum ada data." SELAMANYA walau data ada — itulah "tidak terjadi apa apa". (Fix v3.11.43 filter SOURCE KIRIMAN benar tapi tidak mengubah gejala — wiring-nya yang putus.)

**Fix (2 jalur)**:
1. `nominal_resto_view.ensure_refreshed()` → **propagate** ke `_saldo_minus_view.ensure_refreshed()` (saat main tab dibuka).
2. `nominal_resto_view._build_ui`: **bind** `_sub_nb <<NotebookTabChanged>>` → `_on_sub_tab_changed` → saat anak tab 'Saldo Sistem Minus' dipilih → `ensure_refreshed` (klik sub-tab belakangan).

**Bug #1 — kategori manual: INSTANT-APPLY (tanpa re-run pipeline).**
Root cause perilaku lama: kategori manual hanya di-apply `append1 LANGKAH 5d` saat pipeline RUN (log lama: "diterapkan mulai run pipeline berikutnya" — user tak sadar harus re-run → terasa "gak masuk"/"sama aja").

**Fix**:
- `app.py`: `_apply_kategori_manual_live()` — setelah `_kategori_manual_save` sukses (Identifikasi/Edit): terapkan mapping ke `self.append1_df` **in-place** (mirror `apply_kategori_manual` LANGKAH 5d — kunci kanonik `norm_nama_barang_key`) + refresh view ber-kategori. Hapus mapping tidak instant (nilai otomatis pra-manual tak tersimpan di memori — kembali setelah run pipeline berikutnya; log jujur).
- `deviasi_view.py`: blok populasi combo kategori di-extract ke `_repopulate_kategori_combo()` + `on_kategori_manual_changed()` (invalidasi pivot cache + repopulate + refresh — GR & PCS keduanya).
- `pivot_view.py`: `on_kategori_manual_changed()` (`_populate_filters` + refresh).
- `nominal_resto_view.py`: blok populasi di-extract ke `_repopulate_kategori_values()` + `on_kategori_manual_changed()` (repopulate + refresh; klasifikasi COM/Packaging hidup di compute dari KATEGORI).

**Bug #3 — runtime (ditemukan GUI test)**: `saldo_minus_view._render` panggil `HeaderFilterGroup.refresh_icon()` — method itu tidak ada (yang benar `refresh_icons`, plural). AttributeError saat render pertama → tabel kosong + traceback. py_compile/ruff/import tak mendeteksi (runtime attribute). FIXED.

**Verifikasi — GUI TEST Xvfb SUNGGUHAN** (bukan cuma logic): `NominalRestoView` + `DeviasiView` di-instantiate di Tk + Xvfb :61, simulasi alur nyata (load_data saat tersembunyi → buka tab → ensure_refreshed → klik sub-tab): **9/9 PASS** — T1a dirty set saat tersembunyi · T1b tabel kosong saat tersembunyi · T1c dirty cleared · **T1d tabel TERISI 2 baris (dulu 0 selamanya)** · T1e sub-tab klik aman · T1f sort |qty| desc benar · T1g Keterangan benar · T2a kategori belum ada · **T2b 'BEBAN GAS' muncul instant di combo**. Plus `py_compile` OK + `ruff` semua = baseline (nominal_resto=1, deviasi=5, pivot=4, app=17, saldo_minus=0).

## v3.11.43 — Fix bug saldo minus kosong (SOURCE KIRIMAN None tetap tampil) + remove silent suppress

**Bug #2 — saldo minus kosong** (user: "hasil dari fitur baru saldo minus juga kok gak ada isi nya? cek juga deept"):

**Analisa mendalam**: `hitung_saldo_minus_pairs` (v3.11.42) memfilter `SOURCE KIRIMAN ∈ {Eksternal, Campuran}`. Tapi pasangan 42.17-only (saldo sistem tanpa dokumen IN) punya `SOURCE KIRIMAN = None/kosong` (by-design append1 LANGKAH 5b line 247-249: "pasangan TANPA dokumen IN → tidak mengeluarkan baris (merge left → None = kosong)"). Filter `isin({Eksternal, Campuran})` membuang semua pasangan dgn SOURCE KIRIMAN kosong → hasil kosong.

**Fix**: pasangan dgn SOURCE KIRIMAN kosong (None/NA/empty) **TETAP ditampilkan** (bukan dibuang) — saldo sistem minus pada barang tanpa kiriman kemungkinan besar adalah barang eksternal (saldo 42.17 = snapshot supplier). Filter ⧩ kolom Source Kiriman tetap bisa menyaring spesifik Eksternal/Campuran bila user mau. Internal tetap di-skip (bukan eksternal).

**Fix #2**: `nominal_resto_view.load_data` delegation ke `SaldoMinusView` dulu pakai `contextlib.suppress(Exception)` — menelan error senyap (user kesulitan debug "saldo minus kosong"). Kini `try/except` dgn `print("[WARNING] SaldoMinusView load_data gagal: {exc}")` — error terlihat di log.

**Bug #1 — kategori manual tidak masuk list filter deviasi** (user: "mapping kategori manual di config misal aku udah mapping kok gak masuk di list deviasi gr dan deviasi pcs ya?"):

**Analisa mendalam**: cek config.json sandbox — key `KategoriManual` **TIDAK ADA** (0 entries). `apply_kategori_manual` (append1 LANGKAH 5d) test PASS — logic apply benar. `_kategori_manual_save` (app.py) test PASS — persist ke config.json benar. Flow: UI tombol 🎯 Identifikasi → `_kategori_dialog` → `_kategori_manual_save` → config.json → pipeline run → `apply_kategori_manual` → append1_df KATEGORI → filter deviasi.

**Root cause**: BUKAN code bug. User kemungkinan: (a) belum re-run pipeline setelah mapping (kategori manual hanya di-apply saat pipeline run — log line 4571: "diterapkan mulai run pipeline berikutnya"), ATAU (b) config.json di Windows user berbeda lokasi (mode frozen PyInstaller → config.json di folder .exe). Tidak ada perubahan code (logic benar) — user perlu konfirmasi: (1) re-run pipeline setelah mapping, (2) cek config.json di folder .exe punya key `KategoriManual`.

**Verifikasi**: `py_compile` OK · `ruff` no-new-error (nominal_common=1, nominal_resto_view=1 — baseline) · e2e test `hitung_saldo_minus_pairs` PASS (SOURCE KIRIMAN None tetap tampil, Internal skip, Eksternal/Campuran tampil).

## v3.11.42 — Anak tab "Saldo Sistem Minus" di Nominal Deviasi (Opsi 2, mode pivot/4217, 12 kolom, ide A-K semua)

**Fitur baru** (user: "tambah fitur baru lagi di tab nominal deviasi tambah 1 baru yaitu Saldo Sistem Minus Dengan ambil data dari Pivot ... isinya rekapan saldo akhir atau saldo sistem yang minus dan keterangan nya isi dengan mulai minus dari tanggal berapa"). Klarifikasi user: (1) sumber 2 mode pivot/4217, (2) Opsi 2 SEMUA pasangan pernah minus 1..H, (3) Kuantiti = qty mulai minus, (4) Eksternal termasuk Campuran, (5) semua ide tambahan A-K.

**Implementasi**:
- **`nominal_common.py`**: + `hitung_saldo_minus_pairs(data, h, saldo_sistem_map, mode_4217)` → DataFrame per pasangan minus. Scan `2.SALDO AKHIR` per (pasangan, tgl 1..H); override tgl H dgn saldo_sistem_map (file 42.17) bila mode `4217`. Filter `SOURCE KIRIMAN` ∈ {Eksternal, Campuran}. Output: Nama Barang · NAMA RESTO · Satuan · Source Kiriman · Tgl Mulai Minus · Qty Mulai Minus · Min Qty · Max Qty · Tipe (Konsisten=beruntun minus dari mulai sampai H / Fluktuatif) · Durasi (H−mulai+1).
- **`po_keterangan.py`**: + `po_status_map_3243(rincian_po_df)` → Status Pesanan Pembelian per pasangan (ide J — konteks "minus karena PO belum diterima / Menunggu").
- **`saldo_minus_view.py`** (file baru): class `SaldoMinusView(tk.Frame)` — self-contained anak tab. 12 kolom (Resto · Nama Barang · Satuan · Qty Mulai Minus · Mulai Minus · Durasi · Min Qty · Max Qty · Tipe · Nomor PO 3243 · Status PO 3243 · Keterangan narasi gabungan). KPI card (total pasangan minus · total |qty| · resto minus terbanyak — ide E). Filter ⧩ + sort (ide F). Double-click → drill-down `details_popup` (ide G). Highlight baris Konsisten (red-800) vs Fluktuatif (amber-700 — ide H). Export Excel 💾 (ide I). Resto khusus MLGPAR/BDGSEK warna cell amber (ide K — konsisten v3.11.40). Subscribe `SharedTanggalH` + `SharedSaldoSistemMode` (auto-refresh H/mode berubah — konsisten dgn tab 📦/🧩).
- **`nominal_resto_view.py`**: + anak tab "Saldo Sistem Minus" (sub-notebook ke-3, sejajar "Per Resto" & "Tanpa Harga"). `__init__` terima `saldo_sistem_state` + `rincian_po_df`; `load_data` delegate ke `SaldoMinusView`.
- **`app.py`**: pass `saldo_sistem_state=self._shared_saldo_sistem` + `rincian_po_df=rincian_po_df` ke `NominalRestoView` (instantiate + load_data) — wiring end-to-end.

**Mode saldo sistem**: konsisten dgn tab 📦/🧩 Deviasi GR/PCS (`SharedSaldoSistemMode` v3.11.40). Mode `4217` (default) = peta file 42.17 folder '6. 42.17' override tgl H. Mode `pivot` = running-stock saldo akhir pivot (TANPA override). Combobox diatur di tab 📦 Deviasi GR; SaldoMinusView subscribe → auto-refresh.

**Kolom Keterangan** (narasi gabungan): `"Mulai minus tgl 3 · durasi 3 hari · Konsisten · PO: PO-001, PO-003 (Diproses, Menunggu diproses)"` — menggabung mulai minus + durasi + tipe + PO info (3243) dlm 1 string utk copy ringkas.

**Verifikasi** (headless — no `$DISPLAY`): `py_compile` OK semua file · `ruff` no-new-error (nominal_common=1, po_keterangan=0, saldo_minus_view=0 [new, clean], nominal_resto_view=1, app.py=17 — semua = baseline) · import OK (semua modul + signature benar) · `hitung_saldo_minus_pairs` pandas e2e test PASS (mode pivot + mode 4217 override + filter Internal skip + Tipe Konsisten/Fluktuatif + sort |qty| desc + edge-cases None/empty) · `po_status_map_3243` test PASS · Keterangan builder test PASS · full e2e (compute + PO merge 3243 + Keterangan) PASS. Known: verifikasi visual Tk (anak tab render, KPI, cell-tag warna, drill-down popup) belum diuji headless — user perlu konfirmasi di Windows.

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
