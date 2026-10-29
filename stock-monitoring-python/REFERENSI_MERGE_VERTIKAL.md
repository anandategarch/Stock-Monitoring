# Referensi & Diagnosis — Merge Vertikal (rowspan) ttk.Treeview

> Sesi riset v3.11.18 — laporan user: *"cek merger vertical, saat ini progam
> menjadi bug yaitu yang tampil hanya 1 nama barang per group atau section.
> Cari referensi sebanyak mungkin terkait ini entah di repo lain atau
> internet."*

---

## 1. Diagnosis (TERKONFIRMASI via probe + VLM + file Excel user)

### 1.1 Bukti reproduksi — `probe_vmerge_bug.py`

Data realistis (8 barang × 1–5 resto = 20 baris, 8 kelompok):

| Pengukuran | Hasil |
|---|---|
| Sel "Nama Barang" terisi | **8 dari 20** (1 per kelompok — baris HEAD saja) |
| Baris display KOSONG padahal RAW punya nama | **12 dari 20 (60%)** |
| Scroll tengah/bawah | tetap 8 terisi (sticky memindah nama ke baris pertama terlihat) |

Verifikasi visual VLM atas screenshot:

> *"It looks like **just blank cells, not a merged cell**. The horizontal
> grid lines remain continuous across the 'Nama Barang' column for the empty
> rows, indicating that each row is an individual cell that is simply empty,
> rather than a single tall merged cell spanning multiple rows."*

→ Baris lanjutan grup terbaca sebagai **sel kosong** — bukan sel gabungan.

### 1.2 Bukti file Excel asli user — `20.AGUSTUS 2026.xlsx` (40.740 baris)

| Pengukuran | Hasil |
|---|---|
| Merged cell ranges di seluruh file | **`set()` — NOL sel merged** |
| Kolom "NAMA BAHAN" | **nama diulang di SETIAP baris** |
| Barang unik | 110 |
| Barang muncul di >1 resto (grup multi-baris) | **77** |
| Distribusi resto-per-barang | 33 barang di 1 resto · 14 di 6 resto · **1 di 88 resto · 1 di 230 · 1 di 259 · 1 di 261 resto** |

→ Mental model user dari file kerjanya: **nama selalu ada per baris**,
dan grup terbesar = **261 baris** → dengan merge, user scroll menembus
ratusan baris "tanpa nama" (nama hanya di 1 baris per grup).

### 1.3 Bukti stress-test sticky — grup 100 resto (101 baris)

Sticky di Linux **berfungsi sesuai desain** (nama ikut baris pertama yang
terlihat: idx 0 → 30 → 51 → 74 saat scroll), TETAPI hanya **1 baris per
viewport per grup** yang menampilkan nama, dan nama "melompat" baris per
event scroll — perilaku ini BERBEDA dari Excel (teks merge diam di tengah
sel tinggi). Di jalur Windows/trackpad pernah dicurigai bocor (catatan
commit v3.11.16 AKAR-2).

### 1.4 Kesimpulan akar masalah

1. **Model DATA sudah benar** (nilai di head, lanjutan kosong, RAW per-baris
   utuh di `_row_snaps`/`_rank_map`/`_cek_map`) — identik model
   Excel/Handsontable (lihat referensi #6).
2. **RENDERING-nya yang mustahil pada ttk.Treeview**: widget ini TIDAK punya
   API cell-span — garis grid tetap menembus, teks tidak bisa digambar
   vertikal-tengah memenuhi area grup. Simulasi "blank continuation +
   sticky" terbaca user sebagai **"nama barang hilang"**.
3. **Ini keluhan ke-3 KALI** dengan akar yang sama:
   - era v3.9.55–59: "nama barang tidak muncul" → v3.9.60 merge DIBONGKAR;
   - v3.11.16: "kembali ke masalah lama yaitu nama barang hilang untuk tiap
     grup nama barang";
   - v3.11.18 (ini): "yang tampil hanya 1 nama barang per group atau
     section".

Lokasi kode terkait (`src/ui/deviasi_view.py`):
- `_show_b[i] = brg[i] != brg[i-1]` — baris 3404–3406 (batas kelompok);
- `values[j] = barang if _show_b[i] else ""` — 3433–3437 (blank continuation);
- `_vmerge_setup` 3749 · `_vmerge_sticky` 3893 · `_vmerge_poller` 3848.

---

## 2. Referensi eksternal (11 sumber — Tk/Python, desktop, web, standar)

### A. Dunia Tk/Python — konfirmasi keterbatasan Treeview

**#1 — Tcler's Wiki: ttk::treeview** ·
<https://wiki.tcl-lang.org/page/ttk%3A%3Atreeview> dan
<https://wiki.tcl-lang.org/page/treeview>
Halaman resmi komunitas Tcl/Tk tentang treeview — **tidak ada satupun
kemampuan span/merge sel**. Alternatif yang direkomendasikan wiki:
tablelist, TkTreeCtrl.

**#2 — Tablelist 7.12 (Csaba Nemethi)** ·
<https://www.nemethi.de/tablelist/tablelist.html>
Widget tabel Tk paling matang. Programmer's Guide-nya TIDAK memuat fitur
merge cell — satu-satunya "rowspan" yang ada adalah opsi `grid` geometry
manager (layout widget, bukan sel). → Konfirmasi: **widget tabel Tk
mainstream TIDAK support merge**.

**#3 — tksheet v7 (ragardner)** ·
<https://ragardner.github.io/tksheet/DOCUMENTATION.html> ·
<https://github.com/ragardner/tksheet>
Satu-satunya widget tabel tkinter dengan **span asli**: `sheet.span(0, 0,
2, 2)` = sel gabungan 2×2; span adalah objek first-class (format data,
highlight, read-only, alignment, checkbox bisa ditempel per-span).
**Kunci**: tksheet merender via **Canvas** — itulah kenapa bisa menggambar
sel gabungan sejati (garis grid tidak menembus span, satu blok teks).
Catatan: pengembangan telah berhenti (bug-fix saja).

### B. Desktop toolkit lain — rowspan sebagai API kelas satu

**#4 — Qt 6 `QTableView::setSpan`** ·
<https://doc.qt.io/qt-6/qtableview.html#setSpan>
`setSpan(row, column, rowSpanCount, columnSpanCount)` — rowspan/colspan
native di view tabel Qt (model/view).

**#5 — wxPython `wx.grid.Grid.SetCellSize`** ·
<https://docs.wxpython.org/wx.grid.Grid.html>
`SetCellSize(row, col, num_rows, num_cols)`; `GetCellSize` mengembalikan
`CellSpan_Main` untuk sel utama dan **offset NEGATIF** untuk sel yang
ditutupi span — model "main cell + covered cells" klasik.

### C. Web data-grid — semantik "merge nilai berurutan yang sama"

**#6 — Handsontable Merge Cells** ·
<https://handsontable.com/docs/javascript-data-grid/merge-cells/>
> *"Handsontable merges cells **in the same way as Microsoft Excel**: keeps
> only the **upper-left value** of the selected range and **clears other
> values**."*

→ Model data app kita (head berisi, lanjutan kosong) = **standar industri**
— yang membedakan adalah RENDERING-nya (Handsontable menggambar sel
gabungan sejati; Treeview tidak bisa). Docs ini juga membahas perilaku
merge saat reorder/freeze viewport — berguna sebagai spesifikasi acuan.

**#7 — AG Grid v36 Row Spanning** ·
<https://ag-grid.com/javascript-data-grid/row-spanning/>
> *"A single cell can be used to represent **multiple contiguous leaf rows
> with equal values**."*

`enableCellSpan: true` + `colDef.spanRows: true`; kustomisasi callback:
`spanRows: ({valueA, valueB}) => valueA === valueB` — **persis semantik
`_show_b` kita** (merge baris berurutan bernilai sama). Catatan menarik:
AG Grid baru menambahkan ini di v36 — bertahun-tahun jadi feature request
(sebelumnya tidak didukung).

**#8 — Ant Design Table (React)** ·
<https://ant.design/components/table>
> *"Table cell supports colSpan and rowSpan that set in **onCell** return
> object. When each of them is set to **0, the cell will not be
> rendered**."*

Pola HTML klasik: sel spanner membawa `rowSpan=N`, sel di bawahnya
`rowSpan=0` (tidak dirender) — atribut `<td rowspan>` yang melakukan
penggabungan visual.

**#9 — Element Plus Table `span-method` (Vue)** ·
<https://element-plus.org/en-US/component/table.html>
`span-method({row, column, rowIndex, columnIndex})` → `[rowspan, colspan]`.
Demo resminya menampilkan kolom "Name" ("Tom") di-merge vertikal —
perilaku yang ditiru app, tapi dirender DOM sejati.

**#10 — MDN `<td>` atribut `rowspan`** ·
<https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/td>
Standar HTML: *"non-negative integer … for how many rows the data cell
spans or extends"* — dasar semua implementasi web di atas.

**#11 — Tabulator 6.x Group Rows** ·
<https://tabulator.info/docs/6.2/group>
**Pola ALTERNATIF** (tanpa merge): baris HEADER GRUP tersendiri per nilai
("male (5 items)") yang bisa di-collapse — pendekatan berbeda untuk masalah
yang sama.

### D. Ekosistem Excel (model file — relevan utk export_sheets.py)

**#12 — openpyxl `Worksheet.merge_cells`** ·
<https://openpyxl.readthedocs.io/en/stable/api/openpyxl.worksheet.worksheet.html>
`ws.merge_cells("A1:E1")` — jika kelak user ingin OUTPUT Excel dengan merge
asli, jalur resminya ini (bukan simulasi display).

---

## 3. Sintesis — mengapa app kita "terasa bug" padahal logikanya benar

| Komponen | App saat ini | Excel/tksheet/AG Grid |
|---|---|---|
| Model data | nilai di head, lanjutan kosong ✅ | sama ✅ |
| Garis grid dalam grup | **menembus** (sel terpisah) ❌ | tidak ada (satu sel) ✅ |
| Posisi teks | menempel baris head / baris sticky | **vertikal tengah** sel tinggi ✅ |
| Nilai saat scroll | "melompat" baris per event | diam di tengah sel ✅ |
| Ekspektasi user (file asli) | — | **nama diulang tiap baris, 0 merged cell** ✅ |

ttk.Treeview tidak menyediakan cell-span (referensi #1–#2); satu-satunya
jalur render sejati di atas Treeview = **overlay canvas** (prinsip yang
dipakai tksheet #3), atau ganti widget.

---

## 4. Opsi perbaikan + rekomendasi

### Opsi A — PARITAS EXCEL USER (direkomendasikan) ⭐
**Nama Barang diulang di SETIAP baris**; CEK (gabungan kelompok) & Rank
(kelompok) TETAP merge head-only + sticky.
- ✅ 100% paritas dengan file kerja user (nama selalu terlihat — membunuh
  keluhan yang berulang 3× secara permanen).
- ✅ Tanpa hack render; robust lintas OS (kelas bug sticky/poller Windows
  hilang total utk kolom nama).
- ✅ Kolom CEK/Rank tidak ada di Excel user → merge di sana justru
  menyampaikan informasi "nilai milik kelompok" tanpa melanggar paritas.
- ➕ Opsional: garis pemisah tipis antar kelompok (afordansi visual grup).
- Biaya: kecil (hapus `else ""` utk Nama Barang di _prepare_rows +
  penyesuaian kontrak §98 + sort/auto-fit value_get).

### Opsi B — TRUE MERGED-CELL via overlay canvas (tampilan Excel asli)
Gambar kotak gabungan per kelompok (tanpa garis grid internal, teks
vertikal-tengah) di atas Treeview — kelas tksheet.
- ✅ Visual persis "merger vertical" Excel.
- ❌ Butuh infrastruktur overlay baru meliputi scroll/sort/filter/clone ⛶/
  zoom/kolom-hide — riwayat era v3.9.55–59 menunjukkan kelas bug ini rapuh;
  biaya & risiko besar (grup 261 baris, 28.548 baris produksi).

### Opsi C — Migrasi widget ke tksheet v7
Span asli, tapi pengembangan berhenti + migrasi total ekosistem
(sort/filter/tags/popup/follow-up/auto-fit/frozen-pane) — **tidak
disarankan**.

### Opsi D — Group header rows (pola Tabulator #11)
Baris header grup collapsible — mengubah semantik baris data
(sort/filter/popup/follow-up ikut berubah) — **tidak disarankan**.

---

## 5. Artefak sesi ini

- `probe_vmerge_bug.py` — probe reproduksi (8 grup/20 baris + dump kolom +
  screenshot 3 tahap scroll) → bukti §1.1.
- `/tmp/probe_big_group.py` — stress sticky grup 100 resto → bukti §1.3.
- Screenshot bukti: `/tmp/shots/probe_vm_{1,2,3}_*.png`.
