"""
laporan_deviasi_view.py — v3.9.3: DAFTAR ANOMALI PEMAKAIAN (COM).

Permintaan user: "hapus isi data pada tab laporan deviasi dan sementara
ganti dengan list nama barang dan resto yang pemakaian (com) nya minus
atau lebih tinggi dari median pada pada kolom H".

Isi tab 📋 Laporan Deviasi DIGANTI (sementara — tabel Audit Harian versi
lama tersimpan di git history, commit e20141a / v3.9.2, siap dipulihkan
bila dibutuhkan):
- Baris = (Nama Barang × Nama Resto) yang nilai PEMAKAIAN (COM) pada
  kolom H MINUS (< 0) atau LEBIH TINGGI dari MEDIAN COM pasangan tsb.
  v3.9.7 (koreksi user): median dihitung ANTAR TANGGAL — median com(t)
  tgl 1..H milik pasangan itu sendiri (COM = pemakaian aktual harian di
  resto, BOM = pemakaian harian versi sistem → pembanding yang tepat =
  pola pemakaian harian pasangan tsb, BUKAN antar resto).
- COM dihitung dgn formula yang sama dgn baris "6.PEMAKAIAN (COM)" di
  tab 📊 Pivot (mode Tanggal, port dari M code):
      com(t) = SO(t-1) + IN(t) - BK(t) - SO(t)
  tanggal PERTAMA dalam rentang memakai SALDO AWAL sebagai SO(t-1).
- TANGGAL H = state bersama (SharedTanggalH, v3.9) — diatur di tab
  📦 Deviasi GR; tab ini menampilkan chip read-only + auto-refresh saat
  H berubah (tanpa double input).
- Kolom: ✓ follow-up · Nama Barang · Resto · Satuan · COM (heading
  dinamis "COM (H=25)") · Median (heading dinamis "Median (1..25)" —
  window antar tanggal) · Selisih vs Median · Status
  (MINUS / > MEDIAN / MINUS + > MEDIAN).
- Minus merah PER CELL (v3.9.2 — Tk 9 `tag cell`; fallback Tk 8 =
  tag per baris); sel Status diberi warna per-cell (merah / amber).
- Filter header ⧩ semua kolom, sort engine linear, ⛶ Layar Penuh,
  ⤢ Perbesar Tabel, ◱ Kolom, ↔ Auto-Fit, loading overlay + compute
  async (UI tidak membeku) — semua infrastruktur tabel dipertahankan.
"""

import contextlib
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import numpy as np
import pandas as pd

from .followup import CHECK_OFF, CHECK_ON, FollowUpStore, row_fingerprint
from .theme import (
    C_ACCENT,
    C_AMBER,
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
    fmt_int_id,
    identify_to_column,
    insert_tree_items,
    open_tree_maximized,
    run_async,
    sort_tree_by_column,
)


def _chrono(v):
    """Urutan kronologis kolom tanggal: -25 → -31 lalu 1 → 31
    (identik pivot_view._chrono — hari negatif = bulan lalu)."""
    try:
        iv = int(v)
        return (0, -iv) if iv < 0 else (1, iv)
    except (TypeError, ValueError):
        return (2, str(v))


class LaporanDeviasiView(tk.Frame):
    """Tab 📋 Laporan Deviasi — (v3.9.3, sementara) daftar anomali
    pemakaian (COM): barang × resto dengan COM minus / > median di
    kolom H."""

    COLUMNS = [
        ("✓", 34, "center"),
        ("Nama Barang", 200, "w"),
        ("Resto", 90, "w"),
        ("Satuan", 50, "w"),
        ("COM", 90, "e"),                # heading dinamis "COM (H=25)"
        ("Median", 90, "e"),
        ("Selisih vs Median", 100, "e"),
        ("Status", 130, "w"),
    ]

    NUMERIC_COLS = ("COM", "Median", "Selisih vs Median")

    def __init__(self, parent, go_to_proses: Callable | None = None,
                 followup_store: FollowUpStore | None = None,
                 h_state=None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self.go_to_proses = go_to_proses
        self.store = followup_store       # shared FollowUpStore (v3.2)
        # v3.9.3: TANGGAL H = state bersama (dari tab 📦 Deviasi GR) —
        # chip read-only + auto-refresh (pola tab 🧩 Deviasi PCS v3.9).
        self._h_state = h_state
        self.tanggal_h = int(h_state.h) if h_state is not None else 25
        self._fp_map: dict[str, str] = {}     # iid → fingerprint
        self._row_snaps: dict[str, dict] = {}  # iid → snapshot raw
        self._busy = False
        self._pending = False
        self._dirty = False                # lazy refresh (v3.2)
        # v3.9.5 (audit 19-a #1): guard job kedaluwarsa + pembatalan batch
        self._render_gen = 0
        self._insert_cancel = None
        self._pending_sort = None          # (col, reverse) antre saat busy
        # cache COM matrix — H-INDEPENDEN (ganti H tidak recompute pivot;
        # kolom H dipilih saat render) + lookup satuan
        self._cached_com = None
        self._cached_signature = None
        # v3.9.5 (audit 19-b #4): identitas df utk cache (id() bisa
        # dipakai ulang CPython setelah GC)
        self._cached_data = None
        self._aktif_lookup: dict = {}   # v3.9.5 (audit 19-b #5)
        self._satuan_lookup: dict = {}
        self._result_df = None  # hasil flagged di H
        # v3.9.2: minus merah PER CELL (fallback Tk 8: tag per baris)
        self._cell_tags = CELL_TAGS_SUPPORTED
        self._neg_cells: list = []     # [(iid, "COM")] — com < 0
        self._st_minus_cells: list = []  # [(iid, "Status")] — MINUS
        self._st_above_cells: list = []  # [(iid, "Status")] — > MEDIAN

        self._build_ui()
        self._setup_tags()
        self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="📋", title="Belum ada daftar Pemakaian (COM)",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card (v3.9.3: rentang tanggal DIGANTI chip H bersama) ---
        fcard = Card(self.content, title="Filter")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        self._fcard = fcard
        fbody = fcard.body()

        r1 = tk.Frame(fbody, bg=C_CARD)
        r1.pack(fill="x")
        tk.Label(r1, text="TANGGAL H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        # v3.9.3: chip read-only — H dibagikan dari tab 📦 Deviasi GR
        # (pola tab 🧩 Deviasi PCS; tanpa double input)
        self._h_chip_var = tk.StringVar(value=str(self.tanggal_h))
        chip = tk.Frame(r1, bg="#f1f5f9", highlightbackground="#e2e8f0",
                        highlightthickness=1)
        chip.pack(side="left", padx=(6, 18))
        tk.Label(chip, textvariable=self._h_chip_var, bg="#f1f5f9",
                 fg=C_ACCENT, font=font(11, "bold")).pack(
            padx=10, pady=(2, 3))

        GhostButton(r1, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left")

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        # Header tabel: judul + tombol perbesar
        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        title_label = tk.Label(
            head, text="Pemakaian (COM) — Minus / Di Atas Median (kolom H)",
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

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="browse")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34, anchor=anchor)
            # v3.5: SEMUA kolom pakai filter header ⧩ (sort via popup);
            # ✓ tetap toggle follow-up via klik sel
            self.tree.heading(col_name, text=col_name)

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

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.status_var_label = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var_label, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold")).pack(side="right")

        # Loading overlay (stacking di atas tree)
        self.overlay = LoadingOverlay(tbody, "Menghitung pemakaian (COM)…")

        # v3.5: filter header ⧩ di SEMUA kolom (kecuali ✓ = toggle)
        _filter_cols = [c[0] for c in self.COLUMNS if c[0] != "✓"]
        self._col_sel: dict = {c: None for c in _filter_cols}
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        # v3.6: hide/unhide kolom (klik kanan heading / tombol ◱ Kolom)
        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))

        # v3.9 (ala Waste): ⤢ Perbesar Tabel — ciutkan kartu Filter + judul
        self._expander = TableExpander(btn_expand, [fcard, title_label])

        # v3.9.3: berlangganan perubahan H bersama (chip + auto-refresh;
        # tab ini TIDAK punya input H sendiri — diterapkan di tab GR)
        if self._h_state is not None:
            self._h_state.subscribe(self._on_shared_h_changed)
            # v3.9.5 (audit 19-b #3): lepas listener saat view di-destroy —
            # SharedTanggalH kini punya unsubscribe() (anti listener zombie
            # bila view direbuild di masa depan)
            self.bind("<Destroy>", self._on_view_destroy, add="+")

        self.tree.bind("<Double-1>", self._on_double_click, add="+")  # FIX B-04
        # v3.2: klik sel kolom ✓ → toggle follow-up (tree-agnostic)
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

    def _on_view_destroy(self, event):
        """v3.9.5 (audit 19-b #3): lepas langganan H bersama saat view
        di-destroy (hanya event utk view ini sendiri, bukan anak)."""
        if event.widget is self and self._h_state is not None:
            with contextlib.suppress(Exception):
                self._h_state.unsubscribe(self._on_shared_h_changed)

    # =========================================================================
    # ✓ FOLLOW-UP (v3.2) — klik sel ✓ = daftarkan / keluarkan
    # =========================================================================
    def _on_tree_click(self, event):
        tree = event.widget
        try:
            if tree.identify_region(event.x, event.y) != "cell":
                return
            # v3.7 FIX: cocokkan NAMA kolom (bukan posisi display '#1') —
            # setelah kolom ✓ disembunyikan, posisi #1 jatuh ke kolom lain
            # → toggle follow-up terpicu dari kolom yang salah.
            col = identify_to_column(tree, tree.identify_column(event.x))
            if col != "✓":
                return
            row_iid = tree.identify_row(event.y)
        except Exception:
            return
        if not row_iid or self.store is None:
            return
        fp = self._fp_map.get(row_iid)
        snap = self._row_snaps.get(row_iid)
        if not fp or snap is None:
            return
        added = self.store.toggle(fp, snap)
        try:
            tree.set(row_iid, "✓", CHECK_ON if added else CHECK_OFF)
        except tk.TclError:
            pass
        n = len(self.store)
        self.status_var_label.set(
            f"{'Masuk' if added else 'Keluar'} daftar Follow Up — total "
            f"{n} baris" if n else "Dikeluarkan — daftar Follow Up kosong")

    def ensure_refreshed(self):
        """Lazy refresh (v3.2): compute hanya saat tab ini terlihat."""
        if self._dirty and self.data is not None and not self.data.empty:
            self._dirty = False
            self._refresh()

    def _col_values(self, col: str) -> list:
        """Nilai unik TERFORMAT utk popup filter header (v3.5 — semua kolom).

        v3.9.5 FIX (audit 19-b #1 — P2): kolom tampilan "Selisih vs Median"
        disimpan di _result_df dengan nama INTERNAL "Selisih" — dipetakan
        di sini juga. Dulu hanya jalur APPLY yang memetakan → daftar nilai
        kolom itu selalu KOSONG = popup filter tidak pernah bisa dibuka
        ("Tidak ada nilai yang bisa difilter")."""
        key = "Selisih" if col == "Selisih vs Median" else col
        result = self._result_df
        if result is None or result.empty or key not in result.columns:
            return []
        return self._format_col_series(col, result[key]).unique().tolist()

    def _format_col_series(self, col: str, series):
        """Format kolom → string tampilan (identik render tabel — dipakai
        filter header supaya nilai popup == nilai yang tampil)."""
        if col in self.NUMERIC_COLS:
            return series.map(self._fmt_num)
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
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        # fallback Tk 8 (tanpa tag cell): warna per BARIS
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("above_median", foreground=C_AMBER)
        # v3.9.2 — minus merah PER CELL (bukan satu baris penuh)
        tree.tag_configure("neg_cell", foreground="#dc2626")
        # v3.9.3 — sel Status diberi warna per-cell (semantik status)
        tree.tag_configure("st_minus", foreground="#dc2626")
        tree.tag_configure("st_above", foreground=C_AMBER)

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        # v3.9.5 (audit 19-a #12): data berganti → job lama dibuang
        self._render_gen += 1
        if self._insert_cancel is not None:
            self._insert_cancel()
            self._insert_cancel = None
        self._cached_com = None
        self._cached_signature = None
        self._cached_data = None
        self._satuan_lookup = {}
        self._aktif_lookup = {}
        self._result_df = None
        # v3.9: pulihkan layout bila sedang di-perbesar ⤢
        if getattr(self, "_expander", None) is not None:
            self._expander.reset()
        self._show_content()
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        # (v3.2) lazy refresh — compute hanya bila tab terlihat
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    # =========================================================================
    # COMPUTATION — matriks COM (H-independen, cache per data)
    # =========================================================================
    def _compute_com_matrix(self, data: pd.DataFrame | None = None) -> pd.DataFrame:
        """FIX D-01 (audit 2-d): data bisa di-pass eksplisit (identitas
        pra-capture worker) — default membaca self.data (kompatibel test)."""
        """Matriks PEMAKAIAN (COM) per (Nama Barang × Nama Resto) × tanggal.

        Formula identik dgn baris "6.PEMAKAIAN (COM)" tab 📊 Pivot mode
        Tanggal (port M code; lihat PivotTableView._compute_com):
            com(t=1)  = SALDO AWAL + IN(1) - BK(1) - SO(1)   (SA pair bila ada)
            com(t>1)  = SO(t-1) + IN(t) - BK(t) - SO(t)
        Kolom diurut kronologis (-25..-31 lalu 1..31). Matrix TIDAK
        bergantung H → dipakai lintas perubahan H (kolom H dipilih saat
        render). Juga mengisi self._satuan_lookup.

        v3.9.5 FIX (audit 19-b #2 — P2, bareng pivot & komparasi): SALDO
        AWAL dulu ditempel ke kolom kronologis PERTAMA GLOBAL — saat data
        memuat tanggal negatif (pipeline default FULL), kolom pertama =
        −25 padahal baris SA ber-Tanggal=1 (fn_4217) → SA tidak pernah
        terpakai: com(1) memakai SO(−31), dan pair TANPA data bulan lalu
        mendapat com(1) = IN−BK−SO ≈ −SO(1) = MINUS PALSU di H=1 (431 dari
        654 anomali H=1 pada data real). Kini base com(1) = SA milik pair
        (fallback SO(t-1), fallback 0).
        """
        df = self.data if data is None else data
        if df is None or df.empty:
            return pd.DataFrame()

        jenis_needed = ["SALDO AWAL", "1.SO", "4.IN", "8.BARANG KELUAR"]
        d = df[df["JENIS"].astype(str).isin(jenis_needed)].copy()
        if d.empty:
            self._build_satuan_lookup(df)
            return pd.DataFrame()
        d["_tgl"] = pd.to_numeric(d["Tanggal"], errors="coerce")
        d = d.dropna(subset=["_tgl"])
        d["NILAI"] = pd.to_numeric(d["NILAI"], errors="coerce")
        if d.empty:
            self._build_satuan_lookup(df)
            return pd.DataFrame()

        try:
            pivot = d.pivot_table(
                index=["Nama Barang", "NAMA RESTO", "JENIS"],
                columns="_tgl", values="NILAI",
                aggfunc="sum", fill_value=0,
            )
        except Exception:
            self._build_satuan_lookup(df)
            return pd.DataFrame()
        if pivot.empty:
            self._build_satuan_lookup(df)
            return pd.DataFrame()

        col_keys = sorted(pivot.columns.tolist(), key=_chrono)
        pairs = pivot.index.droplevel("JENIS").unique()

        def jenis_df(jenis: str, fill: bool = True) -> pd.DataFrame:
            try:
                sub = pivot.xs(jenis, level="JENIS")
            except KeyError:
                sub = pd.DataFrame()
            out = (sub.reindex(index=pairs, columns=col_keys)
                   .astype("float64"))
            return out.fillna(0.0) if fill else out

        so = jenis_df("1.SO")
        bm = jenis_df("4.IN")
        bk = jenis_df("8.BARANG KELUAR")

        # v3.9.5 (audit 19-b #2): so_prev[t_i] = SO[t_{i-1}]; base com di
        # TANGGAL 1 = SALDO AWAL milik pair (tanpa fillna — membedakan
        # 'SA ada, nilainya 0' dari 'SA tidak ada') bila ada, fallback
        # shift (SO tanggal negatif), kolom pertama tanpa data → 0.
        so_prev = so.shift(1, axis=1).fillna(0.0)
        if len(col_keys):
            so_prev.iloc[:, 0] = 0.0
        pos1 = [c for c in col_keys if int(float(c)) == 1]
        if pos1:
            sa_raw = jenis_df("SALDO AWAL", fill=False)
            key1 = pos1[0]
            so_prev[key1] = sa_raw[key1].fillna(so_prev[key1])

        com = so_prev + bm - bk - so
        com.columns = [int(c) if float(c).is_integer() else c
                       for c in col_keys]

        self._build_satuan_lookup(df)
        self._build_aktif_lookup(df)
        return com

    def _build_aktif_lookup(self, df: pd.DataFrame):
        """v3.9.5 (audit 19-b #5): lookup AKTIF/NON per barang — mengisi
        snapshot follow-up (kolom AKTIF/NON di tab ☑ Follow Up; sebelumnya
        kosong utk baris asal LAPORAN-COM)."""
        self._aktif_lookup = {}
        if "AKTIF/NON" in df.columns and "Nama Barang" in df.columns:
            adf = (df[["Nama Barang", "AKTIF/NON"]]
                   .dropna(subset=["AKTIF/NON"])
                   .drop_duplicates(subset=["Nama Barang"], keep="first"))
            self._aktif_lookup = dict(zip(
                adf["Nama Barang"].astype(str),
                adf["AKTIF/NON"].astype(str)))

    def _build_satuan_lookup(self, df: pd.DataFrame):
        """Lookup satuan per (Nama Barang, Nama Resto) — zip, bukan
        iterrows (pola v3.2)."""
        self._satuan_lookup = {}
        if "SATUAN" in df.columns and "Nama Barang" in df.columns \
                and "NAMA RESTO" in df.columns:
            sat = (df[["Nama Barang", "NAMA RESTO", "SATUAN"]]
                   .dropna(subset=["SATUAN"])
                   .drop_duplicates(subset=["Nama Barang", "NAMA RESTO"],
                                    keep="first"))
            self._satuan_lookup = {
                (nb, nr): s
                for nb, nr, s in zip(sat["Nama Barang"].astype(str),
                                     sat["NAMA RESTO"].astype(str),
                                     sat["SATUAN"].astype(str))
            }

    # =========================================================================
    # RENDER (async + batched)
    # =========================================================================
    def _refresh(self, sync: bool = False):
        if self.data is None or self.data.empty:
            # v3.9.5 (audit 19-b #8): bersihkan baris basi — dulu early-
            # return meninggalkan render lama tetap tampil di tree
            if self._insert_cancel is not None:
                self._insert_cancel()
                self._insert_cancel = None
            try:
                self.tree.delete(*self.tree.get_children())
            except tk.TclError:
                pass
            self.status_var_label.set(
                "Belum ada data. Jalankan pipeline di tab Proses.")
            return

        if self._busy:
            self._pending = True
            return
        self._busy = True
        # v3.9.7 FIX (bareng komparasi): _dirty di-CLEAR saat refresh
        # BERJALAN — dulu hanya ensure_refreshed yang me-clear →
        # load_data saat tab TERLIHAT me-render tabel tapi _dirty tetap
        # True → listener H berikutnya skip refresh (potensi tabel basi;
        # latent di view ini sejak v3.9.3, terpicu di komparasi §22).
        self._dirty = False
        # v3.9.5 (audit 19-a #1): gen naik tiap job — done() membuang job
        # kedaluwarsa (data berganti lewat load_data saat compute jalan)
        gen = self._render_gen = self._render_gen + 1

        # COM matrix H-independen → cache per data (identitas objek) saja;
        # pilihan kolom H + median difilter di _prepare_rows (murah).
        st = {
            "h": int(self.tanggal_h),
            "col_sel": {c: s for c, s in self._col_sel.items() if s},
        }

        def work():
            # FIX D-01 (audit 2-d): capture identitas SEKALU di awal job —
            # dulu _cached_data dibaca ULANG setelah compute; bila self.data
            # ditukar main thread (load_data pipeline selesai) di tengah
            # compute, cache berlabel data BARU berisi matrix data LAMA →
            # refresh berikutnya SKIP recompute (angka basi senyap; gen-guard
            # hanya membuang RENDER basi, bukan cache salah-label).
            data = self.data
            if (self._cached_com is None
                    or self._cached_data is not data):
                self._cached_com = self._compute_com_matrix(data)
                self._cached_data = data
                self._cached_signature = id(data)
            return self._prepare_rows(st, gen)

        def done(payload):
            if payload.get("gen") != self._render_gen:
                # v3.9.5 (audit 19-a #1): job kedaluwarsa — buang, lalu
                # jalankan refresh yang mengantre (data baru)
                self._busy = False
                if self._pending:
                    self._pending = False
                    self._refresh()
                return
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung pemakaian (COM)…", sync=sync,
                  on_error=self._on_error)

    def _on_error(self, err):
        """FIX B-01 (audit): _busy harus di-reset di jalur error — tanpa
        ini satu exception compute membuat view mati permanen (guard
        'if self._busy: return' menelan SEMUA refresh berikutnya)."""
        self._busy = False
        self._pending = False
        self.status_var_label.set(f"⚠ Gagal menghitung COM: {err}")

    def _prepare_rows(self, st: dict, gen: int = 0) -> dict:
        """Pure pandas: pilih kolom H, median per pasangan ANTAR TANGGAL
        (com(t) tgl 1..H), flag minus / > median, filter header → items
        tree (thread-safe).

        v3.9.7 (koreksi user): median tadinya antar resto per barang —
        kini antar tanggal per pasangan (barang × resto)."""
        com = self._cached_com
        if com is None or com.empty:
            self._result_df = None
            return {"gen": gen, "items": [], "status": "Tidak ada data."}

        h = st["h"]
        if h not in com.columns:
            avail = [int(c) for c in com.columns
                     if isinstance(c, (int, float))]
            lo = f"{avail[0]}" if avail else "-"
            hi = f"{avail[-1]}" if avail else "-"
            self._result_df = None
            return {"gen": gen, "items": [], "status":
                    f"Kolom H={h} tidak ada di data — tanggal tersedia "
                    f"{lo} s/d {hi}. Atur H di tab 📦 Deviasi GR."}

        # v3.9.7 (koreksi user): MEDIAN ANTAR TANGGAL per pasangan —
        # median com(t) utk t = 1..H (window bulan berjalan s/d cut-off;
        # nilai com berasal dari matrix yang sama dgn kolom COM).
        pos_cols = [c for c in com.columns
                    if isinstance(c, (int, float)) and 1 <= int(c) <= h]
        if pos_cols:
            med = com[pos_cols].median(axis=1)
        else:                       # tidak mungkin (h ada di kolom) — guard
            med = pd.Series(np.nan, index=com.index)

        df = (pd.DataFrame({"COM": com[h], "Median": med})
              .reset_index()
              .rename(columns={"NAMA RESTO": "Resto"}))
        # COM float + pasangan tanpa nilai → 0 (konvensi pivot fill_value)
        df["COM"] = pd.to_numeric(df["COM"], errors="coerce").fillna(0.0)
        df["Median"] = pd.to_numeric(df["Median"],
                                      errors="coerce").fillna(0.0)
        df["Selisih"] = df["COM"] - df["Median"]
        df["Satuan"] = [self._satuan_lookup.get((nb, rs), "")
                        for nb, rs in zip(df["Nama Barang"].astype(str),
                                          df["Resto"].astype(str))]

        minus = df["COM"] < 0
        above = df["COM"] > df["Median"]
        df["Status"] = np.select(
            [minus & above, minus, above],
            ["MINUS + > MEDIAN", "MINUS", "> MEDIAN"],
            default="",
        )
        flagged = df[minus | above].copy()

        if flagged.empty:
            # snapshot utk filter header & _col_values (SEBELUM filter header)
            self._result_df = flagged[
                ["Nama Barang", "Resto", "Satuan", "COM", "Median",
                 "Selisih", "Status"]].copy()
            return {"gen": gen, "items": [],
                    "status": f"0 baris — tidak ada COM minus / di atas "
                              f"median di kolom H={h}."}

        # snapshot utk filter header & _col_values (SEBELUM filter header)
        self._result_df = flagged[
            ["Nama Barang", "Resto", "Satuan", "COM", "Median",
             "Selisih", "Status"]].copy()

        # v3.5: filter header ⧩ — kecocokan nilai TERFORMAT (identik
        # dgn yang tampil di tabel)
        filtered = flagged
        for col, sel in st["col_sel"].items():
            out_col = "Selisih" if col == "Selisih vs Median" else col
            if out_col in filtered.columns and sel:
                fmt = self._format_col_series(col, filtered[out_col])
                filtered = filtered[fmt.isin(sel)]

        if filtered.empty:
            return {"gen": gen, "items": [],
                    "status": "Tidak ada baris COM minus / di atas median "
                              "setelah filter."}

        # sort default: Nama Barang lalu COM terbesar dulu
        filtered = filtered.sort_values(
            ["Nama Barang", "COM"], ascending=[True, False])

        n = len(filtered)
        n_minus = int((filtered["COM"] < 0).sum())
        n_above = int((filtered["COM"] > filtered["Median"]).sum())

        cols_np = {c: filtered[c].to_numpy() for c in
                   ("Nama Barang", "Resto", "Satuan", "COM", "Median",
                    "Selisih", "Status")}
        items = []
        fp_map = {}
        row_snaps = {}
        neg_cells = []       # v3.9.2 — minus merah PER CELL (kolom COM)
        st_minus_cells = []  # v3.9.3 — sel Status merah
        st_above_cells = []  # v3.9.3 — sel Status amber
        store = self.store
        for i in range(n):
            barang = str(cols_np["Nama Barang"][i])
            resto = str(cols_np["Resto"][i])
            com_val = float(cols_np["COM"][i])
            med_val = float(cols_np["Median"][i])
            sel_val = float(cols_np["Selisih"][i])
            status = str(cols_np["Status"][i])

            values = [
                "", barang, resto, str(cols_np["Satuan"][i]),
                self._fmt_num(com_val), self._fmt_num(med_val),
                self._fmt_num(sel_val), status,
            ]

            # v3.2: fingerprint + snapshot (raw, tanpa format tampilan) —
            # dipetakan ke kolom Follow Up: SO=nilai COM, Sistem=median
            # (pembanding), Deviasi=selisih, CEK=status
            snap = {
                "asal": "LAPORAN-COM",
                "resto": resto,
                "barang": barang,
                "satuan": str(cols_np["Satuan"][i]),
                # v3.9.5 (audit 19-b #5): AKTIF/NON utk kolom Follow Up
                "aktif": self._aktif_lookup.get(barang, ""),
                "h": h,
                "so": com_val,
                "sistem": med_val,
                "deviasi": sel_val,
                "cek": status,
            }
            fp = row_fingerprint(snap)
            checked = store is not None and store.has(fp)
            values[0] = CHECK_ON if checked else CHECK_OFF
            fp_map[f"row_{i}"] = fp
            row_snaps[f"row_{i}"] = snap

            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            if com_val < 0:
                if self._cell_tags:
                    neg_cells.append((f"row_{i}", "COM"))
                    st_minus_cells.append((f"row_{i}", "Status"))
                else:
                    tags.append("negative")
            elif com_val > med_val:
                if self._cell_tags:
                    st_above_cells.append((f"row_{i}", "Status"))
                else:
                    tags.append("above_median")

            items.append(("", f"row_{i}",
                          {"values": values, "tags": tuple(tags)}))

        status = (f"{n} baris · minus: {n_minus} · > median: {n_above} · "
                  f"H={h}")
        return {"gen": gen, "items": items, "status": status,
                "fp_map": fp_map, "row_snaps": row_snaps,
                "neg_cells": neg_cells, "st_minus_cells": st_minus_cells,
                "st_above_cells": st_above_cells}

    def _render_rows(self, payload: dict):
        try:
            self._render_rows_inner(payload)
        except tk.TclError:
            # v3.9.5: view di-destroy di tengah render — pastikan state
            # bersih supaya job berikutnya tidak terblokir.
            self._busy = False
            self._pending = False

    def _render_rows_inner(self, payload: dict):
        if self._insert_cancel is not None:
            # batch insert lama masih berjalan → stop dulu (race)
            self._insert_cancel()
            self._insert_cancel = None
        self.tree.delete(*self.tree.get_children())
        # _update_headings() sudah memanggil refresh_icons() — v3.9.5
        # (audit 19-b #10): hapus panggilan dobel di sini.
        self._update_headings()
        self._fp_map = payload.get("fp_map", {})
        self._row_snaps = payload.get("row_snaps", {})
        self._neg_cells = payload.get("neg_cells", [])       # v3.9.2
        self._st_minus_cells = payload.get("st_minus_cells", [])
        self._st_above_cells = payload.get("st_above_cells", [])
        self.status_var_label.set(payload["status"])

        def render_done():
            # v3.9.2: tag PER-CELL setelah semua item ter-insert
            self._reapply_cell_tags(self.tree)
            self._busy = False
            if self._pending:
                self._pending = False
                self._pending_sort = None
                self._refresh()
            elif self._pending_sort:
                # v3.9.5 (audit 19-b #6): sort yang diklik saat render
                # batch berjalan kini diantrekan (dulu dibuang diam-diam)
                col, rev = self._pending_sort
                self._pending_sort = None
                self._sort_by(col, reverse=rev)

        self._insert_cancel = insert_tree_items(
            self.tree, payload["items"], batch=500, on_done=render_done)

    def _update_headings(self):
        """Heading COM/Median dinamis mengikuti TANGGAL H
        (pola Deviasi SO_H; v3.9.7: Median menampilkan window 1..H)."""
        self.tree.heading("COM", text=f"COM (H={self.tanggal_h})")
        self.tree.heading("Median", text=f"Median (1..{self.tanggal_h})")
        if getattr(self, "header_filters", None) is not None:
            self.header_filters.refresh_icons()

    def _reapply_cell_tags(self, tree):
        """v3.9.2 — pasang ulang tag per-cell (sort = delete+reinsert →
        tag cell ter-reset; dipakai juga utk clone ⛶)."""
        if not self._cell_tags:
            return
        if self._neg_cells:
            apply_cell_tag(tree, "neg_cell", self._neg_cells)
        if self._st_minus_cells:
            apply_cell_tag(tree, "st_minus", self._st_minus_cells)
        if self._st_above_cells:
            apply_cell_tag(tree, "st_above", self._st_above_cells)

    def _reset_filter(self):
        """Reset filter header (H TIDAK di-reset — milik tab 📦 Deviasi GR,
        state bersama; mengubahnya dari sini akan mengejutkan tab lain)."""
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._refresh()

    # =========================================================================
    # TANGGAL H BERSAMA (v3.9) — chip read-only + auto-refresh
    # =========================================================================
    def _on_shared_h_changed(self, new_h: int):
        """Listener H bersama: H di-apply/reset di tab 📦 Deviasi GR →
        chip diperbarui + view refresh (bila tab belum pernah dilihat:
        tetap dirty, di-refresh saat tab dibuka — ensure_refreshed).

        v3.9.5 FIX (audit 19-c #3): pane tersembunyi (mode ⚖ Komparasi
        aktif / tab lain) TIDAK di-compute ulang — cukup tandai dirty +
        perbarui chip; refresh terjadi saat pane benar-benar terlihat.
        Dulu: 5× ganti H dgn mode 0 aktif = 5× render penuh yang tak
        terlihat (sort/selection ter-reset sia-sia)."""
        self.tanggal_h = int(new_h)
        if hasattr(self, "_h_chip_var"):
            self._h_chip_var.set(str(new_h))
        if self._dirty:
            return          # belum pernah dirender — refresh saat tab dibuka
        if not self.winfo_ismapped():
            self._dirty = True   # tersembunyi — refresh saat terlihat lagi
            return
        if self.data is not None and not self.data.empty:
            self._refresh()

    # =========================================================================
    # ⛶ PERBESAR (fullscreen)
    # =========================================================================
    def _maximize(self):
        def filter_setup(new_tree):
            # v3.6: funnel ⧩ + sort jalan juga di window besar
            attach_clone_filters(
                new_tree,
                [c[0] for c in self.COLUMNS if c[0] != "✓"],
                get_values=self._col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_by(c, reverse=d,
                                                               tree=t),
                # v3.9.5 FIX (audit 19-a #3 / 19-c #4): filter di clone ⛶
                # rebuild baris (delete+insert) → tag per-cell dipasang
                # ulang setelahnya — dulu hilang setelah memfilter di
                # window besar.
                on_after_filter=lambda t=new_tree: self._reapply_cell_tags(t))

        win, new_tree = open_tree_maximized(
            self.tree, "Pemakaian (COM) — Minus / Di Atas Median",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_filter_setup=filter_setup,
            on_render_done=self._reapply_cell_tags)  # v3.9.2 per-cell
        # v3.2: kolom ✓ aktif juga di window perbesar (iid identik)
        new_tree.bind("<Button-1>", self._on_tree_click, add="+")
        return win, new_tree

    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        """Sort kolom — engine LINEAR v3.3 (delete+reinsert).
        v3.9.2: delete+reinsert me-reset tag PER-CELL → dipasang ulang.
        v3.9.3: kolom numerik memakai parser format Indonesia (1.234,5 /
        kurung-negatif) — parser default menganggap "1.234" = 1.234.
        v3.9.5 (audit 19-b #6): klik sort saat render batch berjalan kini
        DIANTREKAN (dulu dibuang diam-diam — sort seolah tidak jalan)."""
        if self._busy and tree is None:
            self._pending_sort = (col, reverse)
            return
        tree = tree if tree is not None else self.tree
        parse = self._parse_num_id if col in self.NUMERIC_COLS else None
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_cell_tags(tree)

    def _auto_fit(self):
        """v3.4 — auto-fit lebar semua kolom ke konten."""
        auto_fit_columns(self.tree)

    # =========================================================================
    # DOUBLE-CLICK → POPUP (tree-agnostic via event.widget)
    # =========================================================================
    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return

        tree = event.widget
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return

        # v3.3: double-click di sel kolom ✓ = toggle follow-up
        # v3.7 FIX: cocokkan NAMA kolom (bukan posisi display '#1')
        try:
            if identify_to_column(tree, tree.identify_column(event.x)) == "✓":
                self._on_tree_click(event)
                return
        except Exception:
            pass

        values = tree.item(row_iid, "values")
        if not values:
            return

        col_ids = [c[0] for c in self.COLUMNS]
        row_data = dict(zip(col_ids, values))
        nama_barang = row_data.get("Nama Barang")
        nama_resto = row_data.get("Resto")
        if not nama_barang:
            return

        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()

        active_filters = {}
        if nama_resto and nama_resto != "(All)":
            active_filters["NAMA RESTO"] = nama_resto

        show_details_popup(
            root, self.data,
            nama_barang=nama_barang,
            jenis=None,
            tanggal=int(self.tanggal_h),
            filters=active_filters,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _fmt_num(val) -> str:
        """Format angka gaya Indonesia (FIX C-03): 1.234.567 / 1.234,5,
        negatif dalam kurung, 0 = '-' (identik pivot_view._format_num)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        if val == 0:
            return "-"
        if val == int(val):
            s = fmt_int_id(val)
        else:
            s = f"{val:,.1f}".replace(",", "\u00a0").replace(".", ",").replace(
                "\u00a0", ".")
        if val < 0:
            return f"({s[1:]})"
        return s

    @staticmethod
    def _parse_num_id(s):
        """Parser sort utk format Indonesia: "1.234" = 1234 (bukan 1.234),
        "(1.234)" = -1234, "-" = 0, "12,5" = 12.5."""
        s = str(s).replace("%", "").strip()
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
