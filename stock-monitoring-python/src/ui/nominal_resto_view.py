"""
nominal_resto_view.py — v3.9.34 TAB BARU 🧮 Nominal Deviasi (user:
"ada tab nominal Deviasi itu isinya Total sum dari nama barang kayak
di laporan sampel kolom nominal deviasi yang dapat dari harga ×
kuantitas deviasi cuman ini disum per resto").

Baris = SATU RESTO — Σ Nominal Deviasi seluruh barang pasangannya
(Nominal = Harga 41.09 × Qty Deviasi tanggal H; pasangan tanpa harga
TIDAK ikut Σ — kolom 'Tanpa Harga' transparan). Sesuai laporan sampel
user ('20.AGUSTUS 2026.xlsx' — kolom NOMINAL DEVIASI per bahan per
resto), diagregasi per resto. Baris TOTAL di ujung. Double-click baris
resto → popup RINCIAN per barang resto itu. Urutan default |Σ Nominal|
MENURUN.

v3.9.36 (user: "di tab nominal deviasi bisa pop up per item dengan
kolom: Nama resto, nama barang, Kuantiti deviasi, Nominal deviasi
Sekarang, Nominal deviasi bulan lalu" + "tambah filter Kategori dengan
default pilihan Kategori = Deviasi ... Yang tanpa harga juga bisa pop
up untuk tampilkan tanpa harga item apa aja"):
  - POPUP RINCIAN 5 KOLOM: Nama Resto · Nama Barang · Kuantiti Deviasi
    · Nominal Deviasi Sekarang · Nominal Deviasi Bulan Lalu. 'Bulan
    Lalu' = FILE DEVIASI tab ⚖ Komparasi (parse_deviasi_file — bulan
    TERBARU di file + minggu TERAKHIR per pasangan; harga 41.09 × DEV
    Lalu; perhitungan = nominal_common.hitung_nominal_lalu_pairs).
    File berganti/ber-load → app memanggil on_lalu_file_changed()
    (pola listener SharedTanggalH); tanpa file → kolom '-' + footer
    petunjuk.
  - FILTER KATEGORI (pola deviasi_view v3.9.19): combobox 'Semua' =
    tanpa filter; DEFAULT 'Deviasi' (case-insensitive, fallback
    'Semua'); diterapkan pra-compute di _compute_resto.
  - DOUBLE-CLICK KOLOM 'Tanpa Harga' → popup daftar barang TANPA HARGA
    resto itu (TOTAL row = semua resto) + alasan (tak ada di 41.09 /
    satuan tak terkonversi).

Perhitungan = src/ui/nominal_common.py (satu sumber kebenaran dgn
mode 💰 Nominal (H) tab 📋 Laporan Deviasi, kolom Nominal tab 📦
Deviasi GR/🧩 PCS & mode ⚖ Komparasi — v3.9.34).

TANGGAL H = state bersama (SharedTanggalH — chip read-only + auto-
refresh dari tab 📦 Deviasi GR; pola mode Nominal). Minus merah
per-cell; format angka Indonesia; filter header ⧩ + sort (TOTAL dipin
di ujung) + ⛶ Layar Penuh + ⤢ Perbesar Tabel + ◱ Kolom + ↔ Auto-Fit
+ Ctrl+C salin baris terpilih (multi-select).
"""
import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

import pandas as pd

from .nominal_common import (
    _norm_name_lalu,
    _norm_resto_lalu,
    agregasi_nominal_per_resto,
    fmt_nominal_cell,
    hitung_nominal_lalu_pairs,
)
from .theme import (
    C_ACCENT,
    C_BG,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    font,
)
from .widgets import (
    CELL_TAGS_SUPPORTED,
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
    sort_tree_by_column,
)

# kolom popup rincian per resto (double-click) — v3.9.36 (user: "pop up
# per item dengan kolom: Nama resto, nama barang, Kuantiti deviasi,
# Nominal deviasi Sekarang, Nominal deviasi bulan lalu")
POPUP_COLUMNS = [
    ("Nama Resto", 90, "w"),
    ("Nama Barang", 210, "w"),
    ("Kuantiti Deviasi", 100, "e"),
    ("Nominal Deviasi Sekarang", 130, "e"),
    ("Nominal Deviasi Bulan Lalu", 130, "e"),
]

# kolom popup barang TANPA HARGA (double-click sel kolom 'Tanpa Harga')
NOHARGA_COLUMNS = [
    ("Nama Resto", 90, "w"),
    ("Nama Barang", 210, "w"),
    ("Satuan", 60, "w"),
    ("Kuantiti Deviasi", 100, "e"),
    ("Keterangan", 200, "w"),
]


class NominalRestoView(tk.Frame):
    """Tab 🧮 Nominal Deviasi — Σ (Harga × Qty Deviasi) per resto."""

    COLUMNS = [
        ("Resto", 130, "w"),
        ("N Barang", 80, "e"),
        ("Tanpa Harga", 80, "e"),
        ("Nominal Deviasi", 130, "e"),   # heading dinamis "(H=n)"
    ]

    NUMERIC_COLS = ("N Barang", "Tanpa Harga", "Nominal Deviasi")

    def __init__(self, parent, go_to_proses: Callable | None = None,
                 h_state=None, lalu_provider: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: pd.DataFrame | None = None
        self.go_to_proses = go_to_proses
        self._h_state = h_state
        self.tanggal_h = int(h_state.h) if h_state is not None else 25
        self.harga_map: dict = {}
        self.konversi_map: dict | None = None
        # v3.9.36 — provider FILE DEVIASI (tab ⚖ Komparasi): () → df
        # parse_deviasi_file atau None. App memasang lambda pembaca
        # komparasi_view._file_df (referensi diganti — bukan dimutasi —
        # jadi pembacaan provider selalu segar); file berganti → app
        # memanggil on_lalu_file_changed().
        self._lalu_provider = lalu_provider
        self._lalu_df: pd.DataFrame | None = None   # snapshot popup lalu
        self._lalu_loaded = False      # provider pernah mengembalikan df
        # v3.9.36 — filter KATEGORI (pola deviasi_view v3.9.19):
        # None = 'Semua' = tanpa filter; default 'Deviasi'.
        self._kategori_sel: str | None = None
        self._busy = False
        self._pending = False
        self._dirty = False                # lazy refresh (pola v3.2)
        self._render_gen = 0
        self._insert_cancel = None
        self._pending_sort = None
        self._result_df = None
        self._pairs_df: pd.DataFrame | None = None   # rincian popup
        self._detail_wins: list = []       # popup rincian hidup
        self._col_sel: dict = {c: None for c in
                               [c[0] for c in self.COLUMNS]}
        # v3.9.2 minus merah PER CELL (fallback Tk 8 per baris)
        self._cell_tags = CELL_TAGS_SUPPORTED
        self._neg_cells: list = []
        self._total_cells: list = []       # sel baris TOTAL (style khusus)

        self._build_ui()
        self._setup_tags()
        self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        self.empty = EmptyState(
            self, icon="🧮",
            title="Belum ada data Nominal Deviasi per resto",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses
            else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card: chip H bersama (read-only) + TOTAL chip ---
        fcard = Card(self.content, title="Filter")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        self._fcard = fcard
        fbody = fcard.body()

        r1 = tk.Frame(fbody, bg=C_CARD)
        r1.pack(fill="x")
        # chip H read-only + petunjuk (pola mode Nominal v3.9.33)
        tk.Label(r1, text="TANGGAL H · atur di 📦 Deviasi GR", bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(8, "bold")).pack(side="left")
        self._h_chip_var = tk.StringVar(value=str(self.tanggal_h))
        chip = tk.Frame(r1, bg="#f1f5f9", highlightbackground="#e2e8f0",
                        highlightthickness=1)
        chip.pack(side="left", padx=(6, 18))
        tk.Label(chip, textvariable=self._h_chip_var, bg="#f1f5f9",
                 fg=C_ACCENT, font=font(11, "bold")).pack(
            padx=10, pady=(2, 3))
        self._total_var = tk.StringVar(value="")
        tk.Label(r1, textvariable=self._total_var, bg=C_CARD,
                 fg=C_HEADER, font=font(9, "bold")).pack(
            side="left", padx=(8, 0))
        GhostButton(r1, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left",
                                                     padx=(18, 0))
        tk.Label(r1, text="double-click resto → rincian per barang · "
                            "double-click sel Tanpa Harga → daftar tanpa "
                            "harga",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(
            side="right")

        # v3.9.36 — filter KATEGORI (user: "tambah filter Kategori dengan
        # default pilihan Kategori = Deviasi"; pola r0b deviasi_view):
        # 'Semua' = tanpa filter; DEFAULT 'Deviasi' (case-insensitive).
        r1b = tk.Frame(fbody, bg=C_CARD)
        r1b.pack(fill="x", pady=(6, 0))
        tk.Label(r1b, text="KATEGORI", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._kategori_var = tk.StringVar(value="Semua")
        self._kategori_combo = ttk.Combobox(
            r1b, textvariable=self._kategori_var, state="readonly",
            width=18, font=font(9))
        self._kategori_combo.pack(side="left", padx=(6, 0))
        self._kategori_combo.bind(
            "<<ComboboxSelected>>", lambda e: self._on_kategori_changed())
        tk.Label(r1b, text="default: Deviasi (pola tab 📦 Deviasi GR) · "
                            "kolom Bulan Lalu = file deviasi (⚖ Komparasi)",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(
            side="left", padx=(12, 0))

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._title_label = tk.Label(
            head, text="Nominal Deviasi per Resto — Σ (Harga 41.09 × "
                       "Qty Deviasi) — H shared",
            bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        self._title_label.pack(side="left")
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel",
                                 command=lambda: None)
        btn_expand.pack(side="right", padx=(0, 6))
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        btn_fit = GhostButton(head, text="↔ Auto-Fit",
                              command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="extended")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(tbody, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        enable_col_resize(self.tree)
        enable_multi_select(self.tree)
        self.tree.bind("<Double-1>", self._on_double_click)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew",
                  pady=(6, 0))
        self.status_var_label = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var_label, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold")).pack(side="right")

        self.overlay = LoadingOverlay(tbody, "Menghitung nominal per "
                                              "resto…")

        self.header_filters = HeaderFilterGroup(
            self.tree, col_ids,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))

        self._expander = TableExpander(btn_expand, [fcard,
                                                    self._title_label])

        # chip H bersama + auto-refresh saat H diubah di tab Deviasi GR
        if self._h_state is not None:
            self._h_state.subscribe(self._on_shared_h_changed)
            self.bind("<Destroy>", self._on_view_destroy, add="+")

    def _on_view_destroy(self, event):
        if event.widget is self and self._h_state is not None:
            with contextlib.suppress(Exception):
                self._h_state.unsubscribe(self._on_shared_h_changed)

    def _on_shared_h_changed(self, h):
        """Listener H bersama (pola mode Nominal v3.9.33): pane
        tersembunyi cukup ditandai dirty + chip diperbarui; refresh
        penuh saat tab terlihat (ensure_refreshed)."""
        self.tanggal_h = int(h)
        if hasattr(self, "_h_chip_var"):
            self._h_chip_var.set(str(self.tanggal_h))
        if self._dirty:
            return
        if not self.winfo_ismapped():
            self._dirty = True
            return
        if self.data is not None and not self.data.empty:
            self._refresh()

    # =========================================================================
    # FILTER / SORT
    # =========================================================================
    def _reset_filter(self):
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._reset_kategori()    # v3.9.36 — reset = default 'Deviasi'
        self._refresh()

    # v3.9.36 — combobox KATEGORI ("Semua" = tanpa filter; pola
    # deviasi_view v3.9.19; default 'Deviasi' — case-insensitive).
    def _on_kategori_changed(self):
        val = self._kategori_var.get()
        self._kategori_sel = None if (not val or val == "Semua") else val
        self._refresh()

    def _default_kategori_value(self) -> str:
        values = list(self._kategori_combo["values"] or [])
        for v in values:
            if str(v).strip().lower() == "deviasi":
                return str(v)
        return "Semua"

    def _reset_kategori(self):
        val = self._default_kategori_value()
        self._kategori_var.set(val)
        self._kategori_sel = None if val == "Semua" else val

    def _col_values(self, col: str) -> list:
        """Nilai unik TERFORMAT utk popup filter header (pola mode
        Nominal v3.9.33 — nilai identik dgn sel yang tampil)."""
        result = self._result_df
        if result is None or result.empty:
            return []
        f = result
        for c, sel in self._col_sel.items():
            if sel is None or c == col:
                continue
            if c in f.columns:
                fmt = self._format_col_series(c, f[c])
                f = f[fmt.isin(sel)]
        if f.empty or col not in f.columns:
            return []
        return self._format_col_series(col, f[col]).unique().tolist()

    def _format_col_series(self, col: str, series):
        if col == "Nominal Deviasi":
            return series.map(fmt_nominal_cell)
        return series.astype(str)

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
        self._refresh()

    def _result_cols(self) -> list:
        return [c[0] for c in self.COLUMNS]

    def _sort_by(self, col: str, reverse: bool = False):
        if col not in self._result_cols():
            return
        if self._busy:
            self._pending_sort = (col, reverse)
            return
        parse = self._parse_num_id if col in self.NUMERIC_COLS else None
        sort_tree_by_column(self.tree, col, reverse=reverse, parse=parse)
        self._pin_total_row(self.tree)
        self._reapply_cell_tags(self.tree)
        self._pending_sort = None

    def _pin_total_row(self, tree):
        """Baris TOTAL dipin di UJUNG setelah sort (pola mode Nominal
        v3.9.33 — sort menurun jangan melompatkan TOTAL ke atas)."""
        try:
            if "row_total" in tree.get_children(""):
                tree.move("row_total", "", "end")
        except tk.TclError:
            pass

    @staticmethod
    def _parse_num_id(s):
        """Parser sort format Indonesia (pola mode Nominal): '1.234' =
        1234, '(1.234)' = -1234, '-' = 0, '12,5' = 12.5."""
        s = str(s).replace("—", "").strip()
        parts = s.split()
        if parts:
            s = parts[0]
        if s in ("-", ""):
            return 0.0
        neg = s.startswith("(") and s.endswith(")")
        if neg:
            s = s[1:-1]
        s = s.replace(".", "").replace(",", ".")
        try:
            v = float(s)
        except ValueError:
            return 0.0
        return -v if neg else v

    def _show_empty(self):
        self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("neg_cell", foreground="#dc2626")
        tree.tag_configure("total", background="#e2e8f0",
                           foreground="#0f172a")
        tree.tag_configure("total_cell", background="#e2e8f0",
                           foreground="#0f172a")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame, harga_map: dict | None = None,
                  konversi_map: dict | None = None):
        self.data = data
        self.harga_map = harga_map or {}
        self.konversi_map = konversi_map
        self._render_gen += 1
        if self._insert_cancel is not None:
            self._insert_cancel()
            self._insert_cancel = None
        self._result_df = None
        self._pairs_df = None
        self._lalu_df = None          # v3.9.36 — snapshot basi dihapus
        self._lalu_loaded = False
        self._close_detail_wins()
        if getattr(self, "_expander", None) is not None:
            self._expander.reset()
        self._show_content()
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        # v3.9.36 — isi combobox KATEGORI dari kolom data (merge '21.
        # DBS Kategori' di append1 — pola deviasi_view) + reset seleksi
        # ke DEFAULT 'Deviasi' (case-insensitive, fallback 'Semua').
        if data is not None and "KATEGORI" in getattr(data, "columns", []):
            _kv = data["KATEGORI"].dropna().astype(str).str.strip()
            kategori_vals = sorted(v for v in _kv.unique() if v)
        else:
            kategori_vals = []
        self._kategori_combo["values"] = ["Semua"] + kategori_vals
        self._reset_kategori()
        # lazy refresh — compute hanya bila tab terlihat
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True
        # footer informatif jalur 0-baris (pola v3.9.33)
        if data is None or len(data) == 0:
            self.status_var_label.set(
                "Belum ada data — 0 baris terbaca dari pipeline "
                "(cek folder data / RootPath di tab ⚙ Pengaturan).")

    def ensure_refreshed(self):
        """Lazy refresh (v3.2): compute hanya saat tab ini terlihat."""
        if self._dirty and self.data is not None \
                and not self.data.empty:
            self._dirty = False
            self._refresh()

    def on_lalu_file_changed(self):
        """v3.9.36 — file deviasi (tab ⚖ Komparasi) berubah (load baru /
        ditutup) → snapshot Bulan Lalu basi: refresh bila tab terlihat,
        tandai dirty bila tersembunyi (pola listener SharedTanggalH)."""
        if self.data is None or self.data.empty:
            return
        if self._busy:
            self._pending = True
            return
        if not self.winfo_ismapped():
            self._dirty = True
            return
        self._refresh()

    # =========================================================================
    # COMPUTE
    # =========================================================================
    def _compute_resto(self, data: pd.DataFrame | None = None,
                       h: int | None = None) -> pd.DataFrame:
        """Frame per resto: [Resto, N Barang, Tanpa Harga, Nominal
        Deviasi] urut |Σ| menurun. self._pairs_df (rincian popup),
        self._lalu_df (pasangan file deviasi — v3.9.36) dan
        self._result_df (snapshot filter) ikut diisi."""
        df = self.data if data is None else data
        if df is None or df.empty:
            self._result_df = None
            self._pairs_df = None
            self._lalu_df = None
            self._lalu_loaded = False
            return pd.DataFrame()
        if h is None:
            h = self.tanggal_h
        # v3.9.36 — filter KATEGORI combobox PRA-COMPUTE (kategori
        # melekat per-baris hasil merge '21. DBS Kategori'; NaN → 'nan'
        # ≠ kategori → terbuang — konsisten deviasi_view).
        if self._kategori_sel and "KATEGORI" in df.columns:
            df = df[df["KATEGORI"].astype(str) == str(self._kategori_sel)]
            if df.empty:
                self._result_df = None
                self._pairs_df = None
                self._lalu_df = None
                self._lalu_loaded = False
                return pd.DataFrame()
        # v3.9.36 — snapshot pasangan Bulan Lalu dari FILE DEVIASI
        # (provider = pembaca komparasi_view._file_df; harga_map fresh
        # → dihitung ulang tiap compute).
        fdf = None
        if self._lalu_provider is not None:
            with contextlib.suppress(Exception):
                fdf = self._lalu_provider()
        self._lalu_loaded = fdf is not None
        self._lalu_df = hitung_nominal_lalu_pairs(
            fdf, self.harga_map, self.konversi_map)
        g, pairs = agregasi_nominal_per_resto(
            df, h, self.harga_map, self.konversi_map)
        if g.empty:
            self._result_df = None
            self._pairs_df = None
            return pd.DataFrame()
        self._pairs_df = pairs
        # snapshot utk filter header (SEBELUM filter diterapkan)
        self._result_df = g.copy()
        return g

    # =========================================================================
    # REFRESH + RENDER
    # =========================================================================
    def _refresh(self, sync: bool = False):
        if self.data is None or self.data.empty:
            self.status_var_label.set("Belum ada data.")
            return
        if self._busy:
            self._pending = True
            return
        self._busy = True
        self._dirty = False          # clear saat refresh berjalan (pola 48-e)
        data = self.data
        h = self.tanggal_h
        gen = self._render_gen

        def work():
            return self._compute_resto(data, h)

        def done(payload):
            if gen != self._render_gen:
                self._busy = False
                if self._pending:
                    self._pending = False
                    self._refresh()
                return
            self._render_rows(payload)

        def on_error(err):
            self._busy = False
            self._pending = False
            self.status_var_label.set(
                f"⚠ Gagal menghitung nominal per resto: {err}")

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung nominal per resto…",
                  on_error=on_error, sync=sync)

    def _render_rows(self, result: pd.DataFrame):
        if self._insert_cancel is not None:
            self._insert_cancel()
            self._insert_cancel = None
        self.tree.delete(*self.tree.get_children(""))
        self._close_detail_wins()    # data baru → popup rincian basi
        self._neg_cells = []
        self._total_cells = []

        # heading dinamis mengikuti TANGGAL H
        self.tree.heading(
            "Nominal Deviasi",
            text=f"Nominal Deviasi (H={self.tanggal_h})")
        if getattr(self, "header_filters", None) is not None:
            self.header_filters.refresh_icons()

        if result is None or result.empty:
            self.status_var_label.set(
                f"Tidak ada baris DEVIASI tanggal {self.tanggal_h}.")
            self._total_var.set("")

            def done_empty():
                self._busy = False
                if self._pending:
                    self._pending = False
                    self._refresh()

            done_empty()
            return

        # filter header ⧩ (nilai TERFORMAT — identik yang tampil)
        filtered = result
        for col, sel in self._col_sel.items():
            if sel is not None and col in filtered.columns:
                fmt = self._format_col_series(col, filtered[col])
                filtered = filtered[fmt.isin(sel)]
        if filtered.empty:
            self.status_var_label.set("Tidak ada baris setelah filter.")
            self._total_var.set("")
            self._render_done_guard()
            return

        col_ids = self._result_cols()
        n = len(filtered)
        total_nom = float(filtered["Nominal Deviasi"].dropna().sum()) \
            if "Nominal Deviasi" in filtered.columns else 0.0
        total_barang = int(filtered["N Barang"].sum()) \
            if "N Barang" in filtered.columns else 0
        total_noharga = int(filtered["Tanpa Harga"].sum()) \
            if "Tanpa Harga" in filtered.columns else 0
        n_neg = int((filtered["Nominal Deviasi"] < 0).sum())

        items = []
        for i in range(n):
            row = filtered.iloc[i]
            nom = row.get("Nominal Deviasi", 0)
            values = (
                str(row["Resto"]),
                fmt_int_id(int(row.get("N Barang", 0) or 0)),
                fmt_int_id(int(row.get("Tanpa Harga", 0) or 0)),
                fmt_nominal_cell(nom),
            )
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            nom_v = None
            try:
                if nom is not None and not pd.isna(nom):
                    nom_v = float(nom)
            except (TypeError, ValueError):
                nom_v = None
            if self._cell_tags:
                if nom_v is not None and nom_v < 0:
                    self._neg_cells.append((f"row_{i}",
                                            "Nominal Deviasi"))
            elif nom_v is not None and nom_v < 0:
                tags.append("negative")
            items.append(("", f"row_{i}",
                          {"values": values, "tags": tuple(tags)}))

        # baris TOTAL di ujung (jumlah semua resto tampil)
        values_total = (
            "TOTAL",
            fmt_int_id(total_barang),
            fmt_int_id(total_noharga),
            fmt_nominal_cell(total_nom),
        )
        items.append(("", "row_total",
                      {"values": values_total, "tags": ("total",)}))
        for col in col_ids:
            self._total_cells.append(("row_total", col))

        status = (f"{fmt_int_id(n)} resto · TANGGAL H = "
                  f"{self.tanggal_h}")
        if self._kategori_sel:
            status += f" · KATEGORI {self._kategori_sel}"
        if n_neg:
            status += f" · {fmt_int_id(n_neg)} resto minus"
        if total_noharga:
            status += f" · {fmt_int_id(total_noharga)} pasangan tanpa harga"
        self.status_var_label.set(status)
        self._total_var.set(
            f"TOTAL {fmt_nominal_cell(total_nom)}")

        self._insert_cancel = insert_tree_items(
            self.tree, items, batch=500, on_done=self._render_done)

    def _render_done_guard(self):
        """Jalur hasil-kosong tetap berakhir di render_done (reset
        _busy + proses pending — pola 48-e FIX 2/3 mode Nominal)."""
        self._reapply_cell_tags(self.tree)
        self._busy = False
        if self._pending:
            self._pending = False
            self._pending_sort = None
            self._refresh()
        elif self._pending_sort:
            col, rev = self._pending_sort
            self._pending_sort = None
            self._sort_by(col, reverse=rev)

    def _render_done(self):
        self._reapply_cell_tags(self.tree)
        self._busy = False
        if self._pending:
            self._pending = False
            self._pending_sort = None
            self._refresh()
        elif self._pending_sort:
            col, rev = self._pending_sort
            self._pending_sort = None
            self._sort_by(col, reverse=rev)

    def _reapply_cell_tags(self, tree):
        """Pasang ulang tag per-cell (sort/clone = delete+reinsert →
        tag ter-reset; pola mode Nominal)."""
        if not self._cell_tags:
            return
        if self._neg_cells:
            apply_cell_tag(tree, "neg_cell", self._neg_cells)
        if self._total_cells:
            apply_cell_tag(tree, "total_cell", self._total_cells)

    # =========================================================================
    # DOUBLE-CLICK → POPUP (rincian per resto / tanpa harga)
    # =========================================================================
    def _event_col_name(self, tree, event) -> "str | None":
        """v3.9.36 — nama kolom data pada posisi klik event (None bila
        event tanpa x / kolom tak teridentifikasi — pemanggil
        program lama tetap dapat popup rincian)."""
        try:
            cid = tree.identify_column(event.x)
        except (AttributeError, tk.TclError, TypeError):
            # event sintetis tanpa x / tree sudah di-destroy
            return None
        if not cid or cid == "#0":
            return None
        try:
            idx = int(str(cid).lstrip("#")) - 1
            cols = list(tree["columns"])
            return cols[idx] if 0 <= idx < len(cols) else None
        except (ValueError, IndexError, TypeError, tk.TclError):
            return None

    def _on_double_click(self, event):
        tree = event.widget
        try:
            sel = tree.selection()
            if not sel:
                return
            iid = sel[0]
            # v3.9.36 — kolom 'Tanpa Harga' + baris TOTAL → daftar
            # barang tanpa harga SEMUA resto (user: "yang tanpa harga
            # juga bisa pop up untuk tampilkan tanpa harga item apa aja")
            if iid == "row_total":
                if self._event_col_name(tree, event) == "Tanpa Harga":
                    self._show_noharga_popup(None)
                return
            resto = str(tree.set(iid, "Resto"))
            if self._event_col_name(tree, event) == "Tanpa Harga":
                self._show_noharga_popup(resto)
                return
        except tk.TclError:
            return
        self._show_resto_popup(resto)

    def _close_detail_wins(self):
        for w in self._detail_wins:
            with contextlib.suppress(tk.TclError):
                w.destroy()
        self._detail_wins = []

    def _lalu_map(self) -> dict:
        """v3.9.36 — peta (_resto_norm, _bahan_norm) → baris frame
        Bulan Lalu (snapshot self._lalu_df)."""
        lalu = self._lalu_df
        if lalu is None or lalu.empty:
            return {}
        m = {}
        for i in range(len(lalu)):
            r = lalu.iloc[i]
            m[(str(r["_resto_norm"]), str(r["_bahan_norm"]))] = r
        return m

    def _show_resto_popup(self, resto: str):
        """Popup RINCIAN PER ITEM utk satu resto (double-click baris) —
        v3.9.36 5 kolom (user: "Nama resto, nama barang, Kuantiti
        deviasi, Nominal deviasi Sekarang, Nominal deviasi bulan lalu").
        Data = self._pairs_df (sekarang) + self._lalu_df (bulan lalu —
        snapshot compute terakhir, read-only)."""
        pairs = self._pairs_df
        if pairs is None or pairs.empty:
            return
        sub = pairs[pairs["Resto"].astype(str) == str(resto)].copy()
        if sub.empty:
            return
        lalu_map = self._lalu_map()

        win = tk.Toplevel(self)
        win.title(f"Nominal Deviasi — {resto} (H={self.tanggal_h})")
        self._detail_wins.append(win)
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        with contextlib.suppress(tk.TclError):
            win.transient(self.winfo_toplevel())

        body = tk.Frame(win, bg=C_BG)
        body.pack(fill="both", expand=True)

        head = tk.Frame(body, bg=C_CARD)
        head.pack(fill="x")
        tk.Label(head, text=f"Rincian per barang — resto {resto} · "
                            f"TANGGAL H {self.tanggal_h}",
                 bg=C_CARD, fg=C_HEADER, font=font(10, "bold")).pack(
            side="left", padx=10, pady=8)
        tk.Label(head,
                 text="Sekarang = Harga 41.09 × Deviasi (H) · Bulan Lalu "
                      "= file deviasi (⚖ Komparasi, bulan terbaru)",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(
            side="right", padx=10)

        col_ids = [c[0] for c in POPUP_COLUMNS]
        tree = ttk.Treeview(body, columns=col_ids, show="headings",
                            selectmode="extended")
        for col_name, width, anchor in POPUP_COLUMNS:
            tree.column(col_name, width=width, minwidth=34,
                        anchor=anchor)
            tree.heading(col_name, text=col_name)
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("neg_cell", foreground="#dc2626")
        tree.tag_configure("total", background="#e2e8f0",
                           foreground="#0f172a")
        tree.tag_configure("total_cell", background="#e2e8f0",
                           foreground="#0f172a")

        neg_cells = []
        total_cells = []
        items = []
        sub = sub.reset_index(drop=True)
        _nolalu = 0
        for i in range(len(sub)):
            row = sub.iloc[i]
            nom = row.get("Nominal")
            # pasangan Bulan Lalu — kunci ternormalisasi (pola join
            # komparasi: '1030.BDGSET' ↔ 'BDGSET')
            lrow = lalu_map.get(
                (_norm_resto_lalu(resto),
                 _norm_name_lalu(row["Nama Barang"])))
            nom_lalu = lrow.get("Nominal Lalu") if lrow is not None else None
            if lrow is None:
                _nolalu += 1
            values = (
                str(resto), str(row["Nama Barang"]),
                fmt_nominal_cell(row.get("Qty Deviasi", 0)),
                fmt_nominal_cell(nom),
                fmt_nominal_cell(nom_lalu),
            )
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            nom_v = None
            try:
                if nom is not None and not pd.isna(nom):
                    nom_v = float(nom)
            except (TypeError, ValueError):
                nom_v = None
            noml_v = None
            try:
                if nom_lalu is not None and not pd.isna(nom_lalu):
                    noml_v = float(nom_lalu)
            except (TypeError, ValueError):
                noml_v = None
            if self._cell_tags:
                if nom_v is not None and nom_v < 0:
                    neg_cells.append(
                        (f"row_{i}", "Nominal Deviasi Sekarang"))
                if noml_v is not None and noml_v < 0:
                    neg_cells.append(
                        (f"row_{i}", "Nominal Deviasi Bulan Lalu"))
            else:
                if (nom_v is not None and nom_v < 0) \
                        or (noml_v is not None and noml_v < 0):
                    tags.append("negative")
            items.append(("", f"row_{i}",
                          {"values": values, "tags": tuple(tags)}))

        total_nom = float(sub["Nominal"].dropna().sum()) \
            if "Nominal" in sub.columns else 0.0
        # Σ Bulan Lalu hanya pasangan yang TAMPIL di popup ini (join
        # kiri dari pasangan sekarang — pasangan file-tak-match tak
        # ditarik; skipna seperti TOTAL sekarang).
        total_lalu = 0.0
        for i in range(len(sub)):
            lrow = lalu_map.get(
                (_norm_resto_lalu(resto),
                 _norm_name_lalu(sub.iloc[i]["Nama Barang"])))
            if lrow is not None:
                v = lrow.get("Nominal Lalu")
                try:
                    if v is not None and not pd.isna(v):
                        total_lalu += float(v)
                except (TypeError, ValueError):
                    pass
        items.append(("", "row_total", {
            "values": ("TOTAL", "", "",
                       fmt_nominal_cell(total_nom),
                       fmt_nominal_cell(total_lalu)),
            "tags": ("total",)}))
        for c in col_ids:
            total_cells.append(("row_total", c))

        vsb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        enable_multi_select(tree)   # Ctrl+A + Ctrl+C TSV

        insert_tree_items(tree, items, batch=500, on_done=lambda: (
            apply_cell_tag(tree, "neg_cell", neg_cells),
            apply_cell_tag(tree, "total_cell", total_cells)))

        foot = tk.Frame(body, bg=C_CARD)
        foot.pack(fill="x")
        n_no = int(sub["Nominal"].isna().sum()) \
            if "Nominal" in sub.columns else 0
        foot_txt = (f"{len(sub)} barang · {fmt_int_id(n_no)} tanpa harga · "
                    f"TOTAL SEKARANG {fmt_nominal_cell(total_nom)} · "
                    f"TOTAL BULAN LALU {fmt_nominal_cell(total_lalu)}")
        if not self._lalu_loaded:
            foot_txt += " · file deviasi belum dimuat (⚖ Komparasi)"
        elif _nolalu:
            foot_txt += (f" · {fmt_int_id(_nolalu)} barang tanpa "
                         "pasangan di file")
        tk.Label(foot, text=foot_txt,
                 bg=C_CARD, fg=C_HEADER, font=font(8, "bold")).pack(
            side="left", padx=10, pady=6)
        GhostButton(foot, text="Tutup", command=win.destroy).pack(
            side="right", padx=10, pady=4)

        # ukuran adaptif ±0.85 layar + clamp posisi (pola popup v3.9.32)
        try:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            w = min(1000, int(sw * 0.85))
            hgt = min(560, int(sh * 0.8))
            x = max(0, min(int(sw / 2 - w / 2), sw - w))
            y = max(0, min(int(sh / 2 - hgt / 2), sh - hgt))
            win.geometry(f"{w}x{hgt}+{x}+{y}")
        except tk.TclError:
            pass
        win.minsize(640, 320)

    # -------------------------------------------------------------------------
    # POPUP BARANG TANPA HARGA (v3.9.36)
    # -------------------------------------------------------------------------
    def _show_noharga_popup(self, resto: "str | None"):
        """Popup daftar barang TANPA HARGA (double-click sel kolom 'Tanpa
        Harga'; user: "yang tanpa harga juga bisa pop up untuk tampilkan
        tanpa harga item apa aja"). resto=None → SEMUA resto (baris
        TOTAL). Kolom Keterangan menjelaskan ALASAN (tak ada di 41.09 /
        satuan tak terkonversi — dari 'Harga Tampil' pairs)."""
        pairs = self._pairs_df
        if pairs is None or pairs.empty:
            return
        if "Nominal" not in pairs.columns:
            return
        sub = pairs[pairs["Nominal"].isna()].copy()
        if resto is not None:
            sub = sub[sub["Resto"].astype(str) == str(resto)].copy()
        title_resto = str(resto) if resto is not None else "SEMUA RESTO"

        win = tk.Toplevel(self)
        win.title(f"Barang Tanpa Harga — {title_resto} (H={self.tanggal_h})")
        self._detail_wins.append(win)
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        with contextlib.suppress(tk.TclError):
            win.transient(self.winfo_toplevel())

        body = tk.Frame(win, bg=C_BG)
        body.pack(fill="both", expand=True)

        head = tk.Frame(body, bg=C_CARD)
        head.pack(fill="x")
        tk.Label(head, text=f"Barang TANPA HARGA — {title_resto} · "
                            "tidak ikut Σ Nominal Deviasi",
                 bg=C_CARD, fg=C_HEADER, font=font(10, "bold")).pack(
            side="left", padx=10, pady=8)
        tk.Label(head,
                 text="harga = file 41.09 (folder 09.Harga)",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(
            side="right", padx=10)

        col_ids = [c[0] for c in NOHARGA_COLUMNS]
        tree = ttk.Treeview(body, columns=col_ids, show="headings",
                            selectmode="extended")
        for col_name, width, anchor in NOHARGA_COLUMNS:
            tree.column(col_name, width=width, minwidth=34,
                        anchor=anchor)
            tree.heading(col_name, text=col_name)
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")

        items = []
        sub = sub.reset_index(drop=True)
        for i in range(len(sub)):
            row = sub.iloc[i]
            ket = self._noharga_ket(row.get("Harga Tampil"))
            values = (
                str(row["Resto"]), str(row["Nama Barang"]),
                str(row.get("Satuan", "-")),
                fmt_nominal_cell(row.get("Qty Deviasi", 0)),
                ket,
            )
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            items.append(("", f"row_{i}",
                          {"values": values, "tags": tuple(tags)}))

        vsb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        enable_multi_select(tree)   # Ctrl+A + Ctrl+C TSV
        insert_tree_items(tree, items, batch=500)

        foot = tk.Frame(body, bg=C_CARD)
        foot.pack(fill="x")
        tk.Label(foot, text=f"{fmt_int_id(len(sub))} barang tanpa harga "
                            "· nominal '-' (transparan — tidak dihitung)",
                 bg=C_CARD, fg=C_HEADER, font=font(8, "bold")).pack(
            side="left", padx=10, pady=6)
        GhostButton(foot, text="Tutup", command=win.destroy).pack(
            side="right", padx=10, pady=4)

        # ukuran adaptif (pola popup rincian)
        try:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            w = min(820, int(sw * 0.7))
            hgt = min(500, int(sh * 0.7))
            x = max(0, min(int(sw / 2 - w / 2), sw - w))
            y = max(0, min(int(sh / 2 - hgt / 2), sh - hgt))
            win.geometry(f"{w}x{hgt}+{x}+{y}")
        except tk.TclError:
            pass
        win.minsize(560, 280)

    @staticmethod
    def _noharga_ket(harga_tampil) -> str:
        """Alasan pasangan tanpa harga — dari 'Harga Tampil' pairs:
        '-' = barang tak ada / harga None di 41.09; ber-'*' = satuan
        rekap tak ter-cover peta rasio (harga as-is ditampilkan)."""
        s = str(harga_tampil or "").strip()
        if not s or s == "-":
            return "barang tak ada di 41.09 (09.Harga)"
        if "*" in s:
            return f"satuan tak terkonversi — harga 41.09: {s}"
        return "harga 41.09 kosong"

    # =========================================================================
    # TOOLBAR TABEL
    # =========================================================================
    def _auto_fit(self):
        auto_fit_columns(self.tree)

    def _maximize(self):
        def filter_setup(new_tree):
            def _after_filter(t=new_tree):
                self._pin_total_row(t)
                self._reapply_cell_tags(t)

            attach_clone_filters(
                new_tree, self._result_cols(),
                get_values=lambda c: self._col_values(c),
                on_after_filter=_after_filter)

        return open_tree_maximized(
            self.tree, "Nominal Deviasi per Resto",
            setup_tags=lambda t: self._setup_tags(t),
            on_filter_setup=filter_setup,
            on_render_done=self._reapply_cell_tags)
