"""
rincian_po_view.py — Pivot table view untuk Rincian PO (v3.2 → v3.9).

v3.9.35 (user: "kolom status pesanan bisa gak ditaruh di bawah kolom
pemasok? seperti merge vertical gitu. Sama kaya kolom nama barang
yang ditampilkan secara vertical. Format tanggal pakai 01 Oktober 2026
aja format panjang"):
- KOLOM "Status Pesanan" DIHAPUS dari tabel — nilai status kini tampil
  di KOLOM PEMASOK pada baris anak PERTAMA tiap PO sebagai "↳ Status"
  (merge-vertical look: tepat di bawah nama pemasok, nilai sekali per
  PO, baris anak lain kosong — persis pola kolom Nama Barang yang
  nilai-nya berjalan vertikal). Teks status dibuat redup via tag
  per-cell (po_status_note) supaya terbaca sebagai anotasi PO, bukan
  data pemasok. Filter status tetap tersedia di kartu Filter (combo
  STATUS PESANAN).
- TANGGAL format panjang Indonesia: "02 Juni 2024" (kolom Tanggal) dan
  "02 Juni 2024 09:00" (Tgl/Jam Pembuatan) — nama bulan Indonesia.

v3.9.20 (deep audit 34-c/fix 35-c1): _resto_name pd.NA/float-safe
(1370.0 → '1370') + _fmt_date/_fmt_datetime NaT-safe (tab tidak mati) +
load_data reset combo Cabang/Status (filter basi) + literal
None/nan/NaT dibuang dari daftar nilai popup filter.

v3.9 — LAYOUT DISEDERHANAKAN (permintaan user: "tampilan rincian PO
apakah bisa lebih dipermudah lagi biar mudah dibaca?"):
- Baris INDUK (teal) kini memuat SEMUA info PO SEKALI: Nomor #, Tanggal,
  Pemasok, Status Pesanan, Keterangan PO, jumlah item & total kuantitas.
- Baris ANAK (putih) hanya berisi ITEM: Nama Barang, Satuan, Kuantitas —
  dulu setiap baris anak mengulang Tanggal/Pemasok/Tgl-Jam yang sama
  (tabel terasa penuh & sulit dipindai).
- Kolom "Tgl/Jam Pembuatan" (metadata PO, jarang dipakai) dipindah ke
  baris induk dan DISSEMBUNYIKAN default — tampilkan lewat tombol
  ◱ Kolom / klik kanan judul kolom.
- Tombol ⤢ Perbesar Tabel + ⛶ Layar Penuh (ala Waste).

Struktur mirror pivotTable di sample Excel (logika identik versi lama):
- Page filters: Cabang PO, Status Pesanan Pembelian
- Tree rows: Nomor# (parent) → detail children
- Value: Sum of Kuantitas per row + grand total row

v3.9.19 — KOLOM NAMA RESTO (permintaan user: "tambahkan kolom nama
resto di rincian PO"): diambil dari kolom Cabang PO ("1370.MLGPAR" →
"MLGPAR" — kode resto sesuai kolom Resto tab lain; tanpa titik →
nilai apa adanya). Diisi pada BARIS INDUK (info level-PO — konsisten
layout v3.9: anak hanya item); ikut filter header ⧩.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import pandas as pd

from .theme import C_BG, C_CARD, C_HEADER, C_TEXT_MUTED, font
from .widgets import (
    Card,
    ColumnManager,
    EmptyState,
    GhostButton,
    HeaderFilterGroup,
    LoadingOverlay,
    TableExpander,
    apply_cell_tag,
    attach_clone_filters,
    auto_fit_columns,
    enable_col_resize,
    enable_multi_select,
    fmt_int_id,
    insert_tree_items,
    open_tree_maximized,
    run_async,
)

# Kolom tabel v3.9.35 (urutan baru — info PO di kiri, item di kanan):
# baris induk mengisi kolom PO (Tanggal…Keterangan PO) + ringkasan;
# baris anak hanya mengisi Nama Barang / Satuan / Kuantitas + STATUS
# PESANAN (↳ di kolom Pemasok, anak pertama saja — merge vertical).
PO_COLUMNS = [
    "Tanggal", "Nama Resto", "Pemasok", "Keterangan PO",
    "Nama Barang", "Satuan", "Kuantitas", "Tgl/Jam Pembuatan",
]

# Pemetaan nama kolom tampilan → kolom DataFrame sumber
# v3.9.19: "Nama Resto" bersumber kolom Cabang PO (kode resto = bagian
# setelah titik terakhir, mis. "1370.MLGPAR" → "MLGPAR").
# v3.9.35: "Status Pesanan" tidak lagi kolom tampilan (merge ke bawah
# Pemasok) — sumbernya tetap dibaca utk nilai ↳ + combo filter.
COL_SRC = {
    "Nama Resto": "Cabang PO",
}

# v3.9.35 — nama bulan Indonesia utk format tanggal panjang
# ("01 Oktober 2026" — permintaan user).
_BULAN_ID = ("Januari", "Februari", "Maret", "April", "Mei", "Juni",
             "Juli", "Agustus", "September", "Oktober", "November",
             "Desember")


def _resto_name(val) -> str:
    """v3.9.19 — Cabang PO → nama resto: bagian setelah titik TERAKHIR
    ("1370.MLGPAR" → "MLGPAR"; tanpa titik → nilai apa adanya).
    v3.9.30 — logika diangkat ke pipeline helpers.resto_from_cabang_po
    (dipakai juga fn_audit PO Menunggu); wrapper ini tetap ada (app.py
    + test meng-import nama ini)."""
    from src.pipeline.helpers import resto_from_cabang_po
    return resto_from_cabang_po(val)


class RincianPoView(tk.Frame):
    """Pivot table view untuk Rincian PO data (tree-based)."""

    def __init__(self, parent, data: pd.DataFrame = None,
                 go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self.go_to_proses = go_to_proses
        self._busy = False
        self._pending = False
        self._dirty = False                # lazy refresh (v3.2)

        self._build_ui()
        self._setup_tags()
        if data is not None:
            self.load_data(data)
        else:
            self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="🛒", title="Belum ada data Rincian PO",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # (v3.2) KPI row DIHAPUS — tabel lebar & besar; ringkasan
        # (PO · item · total kuantitas) ada di status footer.

        # --- Filter card ---
        fcard = Card(self.content, title="Filter")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        fbody = fcard.body()

        r0 = tk.Frame(fbody, bg=C_CARD)
        r0.pack(fill="x")
        tk.Label(r0, text="CABANG PO", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.cabang_var = tk.StringVar(value="(All)")
        self.cabang_combo = ttk.Combobox(r0, textvariable=self.cabang_var,
                                         state="readonly", width=22)
        self.cabang_combo.pack(side="left", padx=(6, 18))
        self.cabang_combo.bind("<<ComboboxSelected>>",
                               lambda e: self._refresh())

        tk.Label(r0, text="STATUS PESANAN", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.status_pesanan_var = tk.StringVar(value="(All)")
        self.status_combo = ttk.Combobox(r0,
                                         textvariable=self.status_pesanan_var,
                                         state="readonly", width=22)
        self.status_combo.pack(side="left", padx=(6, 18))
        self.status_combo.bind("<<ComboboxSelected>>",
                               lambda e: self._refresh())

        GhostButton(r0, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left")

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        self._tcard = tcard
        tbody = tcard.body()

        # Header tabel: judul + tombol perbesar
        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        title_label = tk.Label(
            head, text="Rincian PO — per PO (teal) + item barang",
            bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        title_label.pack(side="left")
        # v3.9 (ala Waste): ⛶ = Layar Penuh (window terpisah)
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        # v3.9 (ala Waste): ⤢ = Perbesar Tabel (in-place)
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel")
        btn_expand.pack(side="right", padx=(0, 6))
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))

        # v3.9: expander ⤢ — ciutkan kartu filter + judul
        self._expander = TableExpander(btn_expand, [fcard, title_label])

        cols = PO_COLUMNS
        self.tree = ttk.Treeview(tbody, columns=cols, show="tree headings",
                                 selectmode="extended")

        self.tree.column("#0", width=130, minwidth=110)
        self.tree.heading("#0", text="Nomor #")
        col_widths = {
            "Tanggal": 132, "Nama Resto": 90, "Pemasok": 200,
            "Keterangan PO": 110,
            "Nama Barang": 200, "Satuan": 64, "Kuantitas": 90,
            "Tgl/Jam Pembuatan": 175,
        }
        for c in cols:
            self.tree.column(c, width=col_widths.get(c, 100), minwidth=50,
                             anchor="e" if c == "Kuantitas" else "w")
            self.tree.heading(c, text=c)

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        # v3.4: drag tepi heading = resize lebar kolom; double-click tepi =
        # auto-fit (dipasang SEBELUM HeaderFilter supaya "break" efektif)
        enable_col_resize(self.tree)
        enable_multi_select(self.tree)  # v3.9.32

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(8, "bold")).pack(side="right")

        # Loading overlay (stacking di atas tree)
        self.overlay = LoadingOverlay(tbody, "Menyiapkan pivot PO…")

        # v3.5: filter header ⧩ di SEMUA kolom (#0 = Nomor # + 7 kolom data)
        _filter_cols = ["#0"] + cols
        self._col_sel: dict = {c: None for c in _filter_cols}
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=None)

        # v3.6: hide/unhide kolom (klik kanan heading / tombol ◱ Kolom)
        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))
        # v3.9: "Tgl/Jam Pembuatan" disembunyikan default (metadata PO,
        # jarang dipakai — layout jadi ringkas; aktifkan via ◱ Kolom)
        self._colmgr.hide("Tgl/Jam Pembuatan")

    def _auto_fit(self):
        """v3.4 — auto-fit lebar semua kolom ke konten."""
        auto_fit_columns(self.tree)

    def _col_values(self, col: str) -> list:
        """Nilai unik TERFORMAT utk popup filter header (v3.5; v3.9 —
        mapping nama kolom tampilan → kolom df sumber).

        v3.9.19 — sumber nilai = baris yang TAMPIL SAAT INI (permintaan
        user: "isi filter harus menampilkan data yang ada aja"): filter
        CABANG PO + STATUS PESANAN + filter header kolom LAIN diterapkan
        dulu (kolom ini sendiri dikecualikan — perilaku AutoFilter Excel);
        dulu df mentah → nilai kategori/barang cabang lain ikut tampil
        meski barisnya sudah terfilter."""
        df = self._filtered_data(exclude_col=col)
        if df is None or df.empty:
            return []
        if col == "#0":
            if "Nomor #" in df.columns:
                vals = df["Nomor #"].dropna().astype(str).unique().tolist()
                return [v for v in vals if v not in ("None", "nan", "NaT")]
            return []
        src = COL_SRC.get(col, col)
        if src not in df.columns:
            return []
        # FIX 35-c1 (NIT C1): literal 'None'/'nan'/'NaT' (object cols dgn
        # None asli via safe_to_str) jangan bocor ke daftar nilai popup
        # filter — '' tetap dipertahankan (baris anak sah bernilai kosong).
        vals = self._format_col_series(col, df[src]).unique().tolist()
        return [v for v in vals if v not in ("None", "nan", "NaT")]

    def _filtered_data(self, exclude_col: str | None = None):
        """v3.9.19 — df setelah filter combobox + header kolom lain
        (vektor; dipanggil saat popup filter dibuka)."""
        df = self.data
        if df is None or df.empty:
            return df
        for c, val in [("Cabang PO", self.cabang_var.get()),
                       ("Status Pesanan Pembelian",
                        self.status_pesanan_var.get())]:
            if val and val != "(All)" and c in df.columns:
                df = df[df[c].astype(str) == val]
        for c, sel in self._col_sel.items():
            if sel is None or c == exclude_col:
                continue
            src_col = "Nomor #" if c == "#0" else COL_SRC.get(c, c)
            if src_col in df.columns:
                fmt = self._format_col_series(c, df[src_col])
                df = df[fmt.isin(sel)]
        return df

    def _format_col_series(self, col: str, series):
        """Format kolom → string tampilan (identik render tabel)."""
        if col == "Tanggal":
            return series.map(self._fmt_date)
        if col == "Tgl/Jam Pembuatan":
            return series.map(self._fmt_datetime)
        if col == "Kuantitas":
            return series.map(self._fmt_num)
        if col == "Nama Resto":   # v3.9.19 — Cabang PO → kode resto
            return series.map(_resto_name)
        return series.astype(str)

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
        self._refresh()

    def _show_empty(self):
        self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        # Nomor# parent row — teal tint + bold (v3.9: font 10 sej tabel)
        tree.tag_configure("po_header", font=font(10, "bold"),
                           background="#ccfbf1",
                           foreground="#134e4a")
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        # Grand total row — slate
        tree.tag_configure("grand_total", font=font(10, "bold"),
                           background="#e2e8f0",
                           foreground="#0f172a")
        # v3.9.35 — anotasi status PO (↳ di bawah Pemasok, anak pertama
        # tiap PO): teks REDUP via tag per-CELL (bukan tag baris — tidak
        # pernah dipasang ke item; mekanisme overlay sama dgn minus
        # merah view lain). Dipasang _apply_status_notes pasca-render.
        tree.tag_configure("po_status_note", foreground=C_TEXT_MUTED)

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        # v3.9: pulihkan layout bila sedang di-perbesar ⤢
        if getattr(self, "_expander", None) is not None:
            self._expander.reset()
        self._show_content()
        self._populate_filters()
        # FIX 35-c1 (RISK C5): combo CABANG/STATUS ikut di-reset saat data
        # berganti — dulu hanya _col_sel + header ⧩; var basi (mis. data baru
        # tanpa cabang itu) membuat tabel 0 baris SENYAP ("Tidak ada data
        # setelah filter.") & popup filter kolom mati.
        self.cabang_var.set("(All)")
        self.status_pesanan_var.set("(All)")
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        # (v3.2) lazy refresh — compute hanya bila tab terlihat
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True
        # v3.9.33 — AUDIT FIX (48-f P0#6 sebagian): pipeline 0 baris →
        # footer INFORMATIF (teks lama diperpanjang; kata kunci 'Belum
        # ada data' tetap ada supaya assertion lama tetap lolos).
        if data is None or len(data) == 0:
            self.status_var.set(
                "Belum ada data — 0 baris terbaca dari pipeline "
                "(cek folder data / RootPath di tab ⚙ Pengaturan).")

    def ensure_refreshed(self):
        """Lazy refresh (v3.2): compute hanya saat tab ini terlihat."""
        if self._dirty and self.data is not None and not self.data.empty:
            self._dirty = False
            self._refresh()

    def _populate_filters(self):
        if self.data is None or self.data.empty:
            return
        for col, combo in [("Cabang PO", self.cabang_combo),
                           ("Status Pesanan Pembelian", self.status_combo)]:
            if col in self.data.columns:
                values = ["(All)"] + sorted(
                    self.data[col].dropna().astype(str).unique().tolist())
                combo["values"] = values

    # =========================================================================
    # RENDER (async + batched — logika identik versi lama)
    # =========================================================================
    def _refresh(self, sync: bool = False):
        if self.data is None or self.data.empty:
            self.status_var.set("Belum ada data.")
            return
        if self._busy:
            self._pending = True
            return
        self._busy = True
        st = {
            "cabang": self.cabang_var.get(),
            "status_pesanan": self.status_pesanan_var.get(),
            # v3.9.13: seleksi kosong (set()) = filter AKTIF → 0 baris
            # (semantik Excel) — dulu truthiness `if s` menelannya.
            "col_sel": {c: s for c, s in self._col_sel.items()
                        if s is not None},
        }

        def work():
            return self._prepare_rows(st)

        def done(payload):
            self._render_rows(payload)

        # FIX C-02/D-02 (audit 2-c/2-d): on_error — kelas fix B-01 v3.9.1
        # yang terlewat di view ini: TANPA reset _busy, satu exception di
        # _prepare_rows membuat tab 🛒 Rincian PO MATI PERMANEN sesi
        # (guard `if self._busy` menelan semua refresh berikutnya).
        def on_error(err):
            self._busy = False
            self._pending = False
            self.status_var.set(f"⚠ Gagal menyiapkan pivot PO: {err}")

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menyiapkan pivot PO…", sync=sync,
                  on_error=on_error)

    def _prepare_rows(self, st: dict) -> dict:
        """Pure pandas: filter + group → items tree (thread-safe).

        v3.9 LAYOUT RINGKAS:
        - PARENT (teal, "po_header"): Nomor # + SEMUA info PO sekali
          (Tanggal, Pemasok, Status, Keterangan PO, Tgl/Jam Pembuatan
          [kolom tersembunyi default]) + ringkasan "N item" + total qty.
        - ANAK (putih, zebra): HANYA item — Nama Barang, Satuan, Kuantitas.
        """
        df = self.data
        for col, val in [("Cabang PO", st["cabang"]),
                         ("Status Pesanan Pembelian", st["status_pesanan"])]:
            if val and val != "(All)" and col in df.columns:
                df = df[df[col].astype(str) == val]

        # v3.5: filter header ⧩ — kecocokan nilai TERFORMAT (semua kolom;
        # v3.9: mapping nama kolom tampilan → kolom df sumber)
        for col, sel in st["col_sel"].items():
            src_col = "Nomor #" if col == "#0" else COL_SRC.get(col, col)
            if src_col in df.columns:
                fmt = self._format_col_series(col, df[src_col])
                df = df[fmt.isin(sel)]

        if df.empty:
            return {"items": [], "kpi": (0, 0, 0),
                    "status": "Tidak ada data setelah filter."}

        if "Nomor #" not in df.columns:
            return {"items": [], "kpi": (0, 0, 0),
                    "status": "Kolom 'Nomor #' tidak ditemukan."}

        sort_cols = [c for c in ["Nomor #", "Tanggal"] if c in df.columns]
        df_sorted = df.sort_values(sort_cols) if sort_cols else df

        total_qty = 0
        po_count = 0
        item_count = 0
        items = []

        def _first_str(series) -> str:
            """Nilai non-kosong pertama dari series (info level-PO)."""
            s = series.dropna().astype(str).str.strip()
            s = s[s != ""]
            return s.iloc[0] if len(s) else ""

        def _first_fmt(series, fmt) -> str:
            """v3.9.33 — AUDIT FIX (48-e FIX 13): nilai TERFORMAT non-kosong
            PERTAMA dari series (pola _first_str, utk kolom datetime) —
            'Tgl/Jam Pembuatan' dulu memakai .iloc[0]: baris PERTAMA
            NaT/kosong menampilkan kolom kosong padahal baris lain di PO
            yang sama punya nilai."""
            s = series.map(fmt).astype(str).str.strip()
            s = s[s != ""]
            return s.iloc[0] if len(s) else ""

        def _fmt_qty(v) -> str:
            """Kuantitas: bulat tanpa desimal, pecahan 1 desimal (v3.9).
            FIX C-03 (audit 2-c): format INDONESIA — dulu EN "1,234.5"
            (koma = ribuan) tidak konsisten dgn 6 view lain."""
            try:
                f = float(v)
            except (TypeError, ValueError):
                return str(v)
            if f == int(f):
                return fmt_int_id(f)
            return f"{f:,.1f}".replace(",", "X").replace(".", ",") \
                .replace("X", ".")

        # nilai per kolom PO: konsisten dalam satu PO → ambil nilai pertama
        for nomor, group in df_sorted.groupby("Nomor #", sort=False):
            po_count += 1
            n_items = len(group)
            po_qty = (group["Kuantitas"].sum()
                      if "Kuantitas" in group.columns else 0)
            total_qty += po_qty
            parent_iid = f"po_{po_count}"
            # v3.9.35 — STATUS PESANAN utk anotasi ↳ di kolom Pemasok
            # (baris anak PERTAMA — merge vertical; kolom tersendiri
            # DIHAPUS permintaan user).
            status_po = (_first_str(group["Status Pesanan Pembelian"])
                         if "Status Pesanan Pembelian" in group.columns
                         else "")
            # BARIS INDUK = info PO lengkap + ringkasan (v3.9)
            # v3.9.19: NAMA RESTO (dari Cabang PO — level-PO; anak baris
            # tetap hanya item, konsisten layout ringkas v3.9)
            items.append(("", parent_iid,
                          {"text": str(nomor),
                           "values": [
                               self._fmt_date(group["Tanggal"].iloc[0])
                               if "Tanggal" in group.columns else "",
                               _resto_name(_first_str(group["Cabang PO"]))
                               if "Cabang PO" in group.columns else "",
                               _first_str(group["Pemasok"])
                               if "Pemasok" in group.columns else "",
                               _first_str(group["Keterangan PO"])
                               if "Keterangan PO" in group.columns else "",
                               f"▸ {n_items} item",
                               "",
                               f"Total: {_fmt_qty(po_qty)}",
                               # v3.9.33 — AUDIT FIX (48-e FIX 13): nilai
                               # non-kosong PERTAMA (bukan .iloc[0]) —
                               # baris pertama NaT tak lagi menyembunyikan
                               # tgl/jam baris lain di PO yang sama.
                               _first_fmt(group["Tgl/Jam Pembuatan"],
                                          self._fmt_datetime)
                               if "Tgl/Jam Pembuatan" in group.columns
                               else "",
                           ],
                           "tags": ("po_header",), "open": True}))

            # BARIS ANAK = hanya item barang (v3.9 — tanpa mengulang info
            # PO). v3.9.35: anak PERTAMA membawa STATUS PO (↳ …) di kolom
            # PEMASOK — merge-vertical ala kolom Nama Barang; anak
            # berikutnya kosong (nilai status sekali per grup PO).
            for i, (_idx, row) in enumerate(group.iterrows()):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                item_count += 1
                items.append((
                    parent_iid, f"{parent_iid}_{item_count}",
                    {"text": "",
                     "values": [
                         "", "",
                         f"↳ {status_po}" if (i == 0 and status_po) else "",
                         "",
                         str(row.get("Nama Barang", "")),
                         str(row.get("Satuan", "")),
                         self._fmt_num(row.get("Kuantitas")),
                         "",
                     ],
                     "tags": (tag,), "open": False}))

        # 8 kolom nilai (grand total: N PO di kolom Nama Barang, total qty
        # sejajar kolom Kuantitas)
        items.append(("", "grand_total",
                      {"text": "GRAND TOTAL",
                       "values": ["", "", "", "",
                                   f"{po_count} PO", "",
                                   _fmt_qty(total_qty), ""],
                       "tags": ("grand_total",), "open": False}))

        status = (f"{po_count} PO · {item_count} item · "
                  f"Total Kuantitas: {_fmt_qty(total_qty)}")
        return {"items": items, "kpi": (po_count, item_count, total_qty),
                "status": status}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self.header_filters.refresh_icons()
        # ringkasan (PO · item · total qty) ada di status footer (v3.2)
        self.status_var.set(payload["status"])

        def render_done():
            self._busy = False
            # v3.9.35 — anotasi status ↳ (tag per-cell, teks redup)
            # dipasang SETELAH semua baris masuk (insert async batch).
            self._apply_status_notes()
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=500,
                          on_done=render_done)

    def _reset_filter(self):
        self.cabang_var.set("(All)")
        self.status_pesanan_var.set("(All)")
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._refresh()

    # =========================================================================
    # ⛶ PERBESAR (fullscreen)
    # =========================================================================
    def _maximize(self):
        def filter_setup(new_tree):
            # v3.6: funnel ⧩ jalan juga di window besar
            attach_clone_filters(
                new_tree, ["#0"] + [str(c) for c in new_tree["columns"]],
                get_values=self._col_values)

        return open_tree_maximized(
            self.tree, "Rincian PO — Pivot Nomor #",
            setup_tags=lambda t: self._setup_tags(t),
            on_filter_setup=filter_setup,
            # v3.9.35 — anotasi status ↳ ikut dipasang di clone ⛶
            on_render_done=lambda t: self._apply_status_notes(t))

    def _apply_status_notes(self, tree=None):
        """v3.9.35 — pasang tag per-cell `po_status_note` (teks redup) ke
        sel STATUS (↳ …) di kolom Pemasok baris anak pertama tiap PO.

        Dipanggil pasca-render (insert async) di tabel utama + clone ⛶.
        Tag per-cell ≠ tag baris — tidak pernah memengaruhi styling baris
        anak lain (mekanisme sama dgn minus merah per-cell view lain)."""
        tree = tree if tree is not None else self.tree
        cells = []
        try:
            for po in tree.get_children(""):
                if po == "grand_total":
                    continue
                kids = tree.get_children(po)
                if kids:
                    cells.append((kids[0], "Pemasok"))
        except tk.TclError:
            return
        apply_cell_tag(tree, "po_status_note", cells)

    # =========================================================================
    # HELPERS (identik versi lama)
    # =========================================================================
    @staticmethod
    def _fmt_num(val) -> str:
        """FIX C-03 (audit 2-c): format angka INDONESIA (1.234,5 · negatif
        kurung · 0 = '-') — dulu gaya EN "1,234.5"; nilai yang sama kini
        tampil konsisten dgn tabel sumber drill-down-nya."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val)
        if v == 0:
            return "-"
        if v == int(v):
            s = fmt_int_id(v)
        else:
            s = f"{v:,.1f}".replace(",", "X").replace(".", ",") \
                .replace("X", ".")
        if v < 0:
            return f"({s[1:]})"
        return s

    @staticmethod
    def _fmt_date(val) -> str:
        # v3.9.35 — FORMAT PANJANG Indonesia "01 Oktober 2026" (user:
        # "Format tanggal pakai 01 Oktober 2026 aja format panjang") —
        # nama bulan Indonesia manual (strftime %B = locale C → English).
        # FIX 35-c1 (RISK C6): NaT-safe tetap — NaT.strftime RAISES
        # ValueError di pandas 2.2.3 (to_datetime(errors="coerce") bisa
        # menghasilkan NaT) → satu baris NaT tidak mematikan tab.
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            if pd.isna(val):
                return ""
        except (TypeError, ValueError):
            pass
        d = val if hasattr(val, "strftime") else None
        if d is None:
            try:
                d = pd.to_datetime(val)
            except Exception:
                return str(val)
        try:
            return f"{d.day:02d} {_BULAN_ID[d.month - 1]} {d.year}"
        except (AttributeError, IndexError, TypeError, ValueError):
            return str(val)

    @staticmethod
    def _fmt_datetime(val) -> str:
        # v3.9.35 — format panjang + jam menit: "01 Oktober 2026 14:23"
        # (detik dibuang — kolom tersembunyi default, hemat lebar).
        # FIX 35-c1 (RISK C6): NaT-safe (lihat _fmt_date).
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            if pd.isna(val):
                return ""
        except (TypeError, ValueError):
            pass
        d = val if hasattr(val, "strftime") else None
        if d is None:
            try:
                d = pd.to_datetime(val)
            except Exception:
                return str(val)
        try:
            return (f"{d.day:02d} {_BULAN_ID[d.month - 1]} {d.year} "
                    f"{d.hour:02d}:{d.minute:02d}")
        except (AttributeError, IndexError, TypeError, ValueError):
            return str(val)
