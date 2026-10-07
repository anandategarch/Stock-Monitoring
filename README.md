# Stock-Monitoring

Repository berisi:

1. **`Mutasi Barang - New - Copy.xlsx`** — File Excel asli dengan Power Query + Pivot Tables (monitoring stok resto berbasis Accurate Online export).

2. **`stock-monitoring-python/`** — Porting Python dari Power Query M code. Pipeline lengkap yang menghasilkan output Excel "sama persis" dengan sample, tanpa dependency Excel/Windows.

## Quick Start (Python Edition)

```bash
cd stock-monitoring-python
SETUP.bat   # Windows: install pandas, openpyxl, numpy
MULAI.bat   # Windows: buka Tkinter UI
```

Atau CLI:
```bash
python -m src.main
```

Lihat `stock-monitoring-python/README.md` untuk dokumentasi lengkap.

## Changelog

- **v3.3.1** — **FIX "Saldo SO kosong semua"** di tab Deviasi GR/PCS & Laporan. **Akar 1 — sumber SO**: data user kini satu **workbook gabungan `.xlsb`** (sheet `1  DEVIASI WEEKLY`, semua resto dalam 1 sheet, NAMA RESTO sebagai kolom) — reader lama hanya mencari file per-resto `.xlsx` ber-sheet `REKAP MENTAH` → SO tidak pernah terbaca. Reader baru: fallback otomatis scan semua file (termasuk `*.xlsb`) × sheet, deteksi schema rekap mentah (NAMA RESTO + JENIS + NAMA BARANG + SATUAN + kolom hari), NAMA RESTO dari kolom; format per-resto lama tetap didukung; `pyxlsb` masuk requirements. **Akar 2 — bug render v3.2**: vektorisasi lupa 8+5 kolom matrix (`SO_H-2…SO_H+2/In/Out/BK` + `Saldo Awal/IN/OUT/BK/Saldo Kumulatif`) → selalu `-` walau data benar. **Validasi vs sheet `DEVIASI GR` user: 1404/1405 baris identik**; mock + 117 UI test PASS.
- **v3.3.0** — Hasil **deep audit** (UI/UX + dead code + engine). **Engine sort LINEAR**: klik judul kolom memakai delete+reinsert O(n) — dulu `tree.move` O(n²) membekukan UI **45 detik** saat sort 50k baris di Laporan Deviasi (kini **0,7 detik**, 42-64×). **Bug fix follow-up** (kritis): klik ✓ / double-click kini iid-based — setelah sort tidak lagi mengeluarkan **baris yang salah**. **Bug fix pipeline error**: `except as e` + lambda tertunda → NameError (path error tidak pernah sampai UI). **Bug fix UX**: double-click sel ✓ = toggle follow-up (bukan popup). **Perf**: cache pivot Deviasi dibagi GR/PCS (compute 1× bukan 2×), cache Laporan tidak recompute saat ganti rentang tanggal, insert batch adaptif, popup detail tanpa full copy. **UX**: selesai pipeline → status bar + log (modal "Selesai" dihapus). **Dead code dibersihkan** (24 unused import, 9 konstanta warna, method mati, `test_large_scale.py`).
- **v3.2.0** — Tab **☑ Follow Up** (ala aplikasi *Waste*): centang ✓ baris anomali di Deviasi GR/PCS & Laporan → shortlist investigasi persisten (`followup.json`), export Excel + impor hasil tindak lanjut (PIC/KATEGORI/TINDAKAN). **KPI row di atas tabel dihapus** di semua tab data — tabel jadi lebar & besar (ringkasan pindah ke status footer). **Perf**: vektorisasi numpy (deviasi 16×, laporan 3.7× lebih cepat) + lazy refresh per tab (hanya tab aktif yang dihitung setelah pipeline).
- **v3.1.0** — Header filter (Excel AutoFilter) di semua tab, tombol ⛶ perbesar tabel, copy Nomor/Nomor PO di pop-up, pivot per resto (baris kosong disembunyikan, tanpa kolom Total), loading animation semua proses.
- **v3.0.0** — Total UI/UX redesign (design language Waste: slate + teal, card-based, dark toolbar).
