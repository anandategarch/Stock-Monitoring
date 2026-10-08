"""
komparasi_deviasi_view.py — v3.9.4: KOMPARASI FILE DEVIASI vs TAB DEVIASI GR.

Permintaan user: "Di file sampel kan ada Dev to bom ini kok gak ada ya?
Padahal data udah lengkap 2205 itu bom. Aku barusan upload file deviasi.
Nah aku mau compare file deviasi itu dengan yang deviasi di Tab deviasi GR
terus coba cek kolom status week 1 itu sama dengan 7 week 2 = 14 dan
week = 25. Itu buat kolom h."

KONSEP
------
File deviasi (contoh: "20.AGUSTUS 2026.xlsx" — "File Komparasi Deviasi
History Sampel") berisi laporan resmi per (RESTO × NAMA BAHAN × MINGGU):
    QTY BOM      = pemakaian teoretis dari penjualan  (minus)
    QTY COM      = pemakaian aktual                   (minus)
    QTY DEVIASI  = COM − BOM                          (±, plus = surplus)
    % QTY DEVIASI TO BOM = DEVIASI / |BOM|
Minggu = CUT-OFF KUMULATIF dari tanggal 1 (WEEK 2 ≈ 2× WEEK 1) — sama
dengan semantik TANGGAL H di aplikasi:
    STATUS BULAN  →  KOLOM H
    WEEK 1        →  7      (permintaan user)
    WEEK 2        →  14     (permintaan user)
    WEEK 3 / WEEK 4 → 25    (permintaan user "week = 25"; file sampel
                             memakai WEEK 4 — tidak ada WEEK 3)

SISI APP (dari data pipeline / append1, tanpa file tambahan — "data udah
lengkap, 2205 itu BOM"):
    BOM·App   = −Σ 9.OUT (penjualan 22.05) tanggal 1..H   — konvensi file
    COM·App   = −Σ pemakaian com(t) tanggal 1..H, dengan
                com(t) = SO(t-1) + IN(t) − BK(t) − SO(t)  (formula identik
                baris 6.PEMAKAIAN (COM) pivot & tab 📋 Anomali COM)
    DEV·App   = COM·App − BOM·App  ("Dev to BOM" versi app)
    GR·App    = SO_H − Sistem_H (2.SALDO AKHIR) — PERSIS kolom Deviasi di
                tab 📦 Deviasi GR pada H minggu tsb.
    Secara aljabar GR·App = ΣOUT − SA − ΣIN + ΣBK + SO_H = out_cum − com_cum
    = DEV·App — dua jalur hitung yang seharusnya sama; keduanya ditampilkan
    sehingga selisih internal juga terlihat.

VERDIK: Selisih = GR·App − DEV·File → Status MATCH (dalam toleransi) /
SELISIH / TIDAK ADA DI DATA APP / H TIDAK ADA DI DATA.

RESTO: file memakai kode bercabang ("1041.BDGUKU", "B.1001.MLGPAR") —
dinormalkan ke segmen setelah titik terakhir ("BDGUKU") lalu dicocokkan
ke NAMA RESTO data app (upper + strip).

INFRASTRUKTUR (dipertahankan dari view lain): ✓ follow-up, filter header
⧩ semua kolom, sort engine linear (parser angka Indonesia), ⛶ Layar Penuh,
⤢ Perbesar Tabel, ◱ Kolom, ↔ Auto-Fit, loading overlay + compute async +
on_error reset _busy (FIX B-01), minus merah PER CELL (v3.9.2 apply_cell_tag),
sel Status berwarna per-cell (MATCH hijau / SELISIH amber / lainnya merah).
"""

import json
import os
import re
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk

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
    add_tooltip,
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

# ---------------------------------------------------------------------------
# Konstanta pemetaan minggu → kolom H (permintaan user, lihat docstring)
# ---------------------------------------------------------------------------
WEEK_TO_H = {
    "WEEK 1": 7,
    "WEEK 2": 14,
    "WEEK 3": 25,   # user: "week = 25"
    "WEEK 4": 25,   # file sampel memakai WEEK 4 utk cut-off 25
}

# Toleransi MATCH: |selisih| <= TOL_ABS + TOL_REL * |nilai file|
TOL_ABS = 1.0
TOL_REL = 0.0001

# File kecil utk mengingat path file deviasi terakhir (initialdir dialog)
_LAST_FILE_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "komparasi_last.json")


def _chrono(v):
    """Urutan kronologis kolom tanggal: -25 → -31 lalu 1 → 31
    (identik pivot_view._chrono — hari negatif = bulan lalu)."""
    try:
        iv = int(v)
        return (0, -iv) if iv < 0 else (1, iv)
    except (TypeError, ValueError):
        return (2, str(v))


def _norm_resto(v) -> str:
    """'1041.BDGUKU' / 'B.1001.MLGPAR' / 'BDGUKU' → 'BDGUKU'
    (upper + strip + segmen setelah titik TERAKHIR)."""
    s = str(v).strip().upper()
    if "." in s:
        s = s.split(".")[-1].strip()
    return s


def _norm_name(v) -> str:
    """Normalisasi nama barang utk pencocokan: upper + rapat spasi ganda."""
    return re.sub(r"\s+", " ", str(v).strip().upper())


def _week_h(label) -> "int | None":
    """'WEEK 1' → 7. Label tak dikenal → heuristik 7×n (maks 31),
    tanpa angka → None."""
    s = str(label).strip().upper()
    if s in WEEK_TO_H:
        return WEEK_TO_H[s]
    m = re.search(r"(\d+)", s)
    if m:
        return min(7 * int(m.group(1)), 31)
    return None


def parse_deviasi_file(path: str) -> dict:
    """Baca & validasi file deviasi (pure — tanpa Tk; mudah diuji).

    Return dict:
        ok: bool
        error: str (bila not ok)
        df: DataFrame ternormalisasi (kolom _resto_norm, _bahan_norm,
            _week, _h) atau None
        meta: {weeks, n_rows, n_resto, bulan, file_name, sheet}
    """
    meta = {"file_name": os.path.basename(path), "sheet": None,
            "weeks": [], "n_rows": 0, "n_resto": 0, "bulan": []}
    try:
        xl = pd.ExcelFile(path)
        sheet = xl.sheet_names[0]
        meta["sheet"] = sheet
        df = xl.parse(sheet)
    except Exception as e:
        return {"ok": False, "error": f"Gagal membaca file: {e}",
                "df": None, "meta": meta}

    if df is None or df.empty:
        return {"ok": False, "error": "File kosong (tidak ada baris).",
                "df": None, "meta": meta}

    # --- deteksi kolom (nama fleksibel, case/space-insensitive) ---
    cols = {}
    for c in df.columns:
        cols[str(c).strip().upper().replace(" ", "")] = c

    def find(*cands):
        for cand in cands:
            if cand.upper().replace(" ", "") in cols:
                return cols[cand.upper().replace(" ", "")]
        return None

    col_resto = find("RESTO", "NAMARESTO", "CABANG")
    col_bahan = find("NAMABAHAN", "NAMABARANG", "BARANG", "ITEM")
    col_week = find("STATUSBULAN", "STATUSMINGGU", "WEEK", "MINGGU",
                    "STATUS")
    col_bom = find("QTYBOM", "BOM")
    col_com = find("QTYCOM", "COM")
    col_dev = find("QTYDEVIASI", "DEVIASI")
    col_sat = find("SATUAN", "UOM", "UNIT")
    col_pct = None
    for k, orig in cols.items():
        if k.startswith("%") and "DEVIASI" in k and "BOM" in k:
            col_pct = orig
            break
    col_bulan = find("BULAN", "MONTH")

    missing = []
    for label, c in [("RESTO", col_resto), ("NAMA BAHAN", col_bahan),
                     ("STATUS BULAN", col_week), ("QTY BOM", col_bom),
                     ("QTY COM", col_com), ("QTY DEVIASI", col_dev)]:
        if c is None:
            missing.append(label)
    if missing:
        return {"ok": False,
                "error": "Kolom wajib tidak ditemukan: "
                         + ", ".join(missing)
                         + ". Kolom file: "
                         + ", ".join(str(c) for c in df.columns[:12]),
                "df": None, "meta": meta}

    out = pd.DataFrame({
        "Resto": df[col_resto].astype(str),
        "Nama Barang": df[col_bahan].astype(str),
        "Satuan": (df[col_sat].astype(str) if col_sat is not None
                   else ""),
        "Minggu": df[col_week].astype(str).str.strip().str.upper(),
        "BOM File": pd.to_numeric(df[col_bom], errors="coerce"),
        "COM File": pd.to_numeric(df[col_com], errors="coerce"),
        "DEV File": pd.to_numeric(df[col_dev], errors="coerce"),
    })
    out["%TO BOM File"] = (pd.to_numeric(df[col_pct], errors="coerce")
                           if col_pct is not None else np.nan)
    out["BULAN"] = (df[col_bulan].astype(str).str.strip()
                    if col_bulan is not None else "")

    out["_resto_norm"] = out["Resto"].map(_norm_resto)
    out["_bahan_norm"] = out["Nama Barang"].map(_norm_name)
    out["_h"] = out["Minggu"].map(_week_h)

    # minggu tak dikenal → baris dibuang (dilaporkan via meta)
    bad_week = out["_h"].isna()
    n_bad = int(bad_week.sum())
    out = out[~bad_week].copy()

    # duplikat (minggu, resto, bahan) → keep first (file sampel unik)
    out = out.drop_duplicates(
        subset=["Minggu", "_resto_norm", "_bahan_norm"], keep="first")

    # rapatkan index setelah filter
    out = out.reset_index(drop=True)

    weeks = sorted(out["Minggu"].unique().tolist())
    meta["weeks"] = weeks
    meta["n_rows"] = len(out)
    meta["n_resto"] = int(out["_resto_norm"].nunique())
    if "BULAN" in out.columns:
        bulan = [b for b in out["BULAN"].unique().tolist()
                 if b and b.lower() != "nan"]
        meta["bulan"] = sorted(bulan)[:6]
    meta["n_unknown_week"] = n_bad
    return {"ok": True, "error": None, "df": out, "meta": meta}


class KomparasiDeviasiView(tk.Frame):
    """Pane ⚖ Komparasi File Deviasi — pembanding file deviasi resmi
    vs hitungan app (Tab 📦 Deviasi GR) per (Resto × Barang × Minggu)."""

    COLUMNS = [
        ("✓", 34, "center"),
        ("Resto", 100, "w"),
        ("Nama Barang", 190, "w"),
        ("Satuan", 50, "w"),
        ("Minggu", 70, "w"),
        ("H", 36, "e"),
        ("BOM File", 95, "e"),
        ("COM File", 95, "e"),
        ("DEV File", 100, "e"),
        ("%TO BOM File", 85, "e"),
        ("BOM App", 95, "e"),
        ("COM App", 95, "e"),
        ("DEV App", 100, "e"),
        ("GR App", 100, "e"),
        ("Selisih", 100, "e"),
        ("Status", 120, "w"),
    ]

    NUMERIC_COLS = ("BOM File", "COM File", "DEV File", "%TO BOM File",
                    "BOM App", "COM App", "DEV App", "GR App", "Selisih")

    def __init__(self, parent, go_to_proses: Callable | None = None,
                 followup_store: FollowUpStore | None = None,
                 initial_dir: str = ""):
        super().__init__(parent, bg=C_BG)
        self.data: pd.DataFrame | None = None
        self.go_to_proses = go_to_proses
        self.store = followup_store
        self._initial_dir = initial_dir
        self._fp_map: dict[str, str] = {}
        self._row_snaps: dict[str, dict] = {}
        self._busy = False
        self._pending = False
        self._dirty = False                 # lazy refresh
        # file deviasi yang sedang dibandingkan
        self._file_df: pd.DataFrame | None = None
        self._file_meta: dict = {}
        self._file_path: str = ""
        # cache matriks app — per objek data (id) + file
        self._cached_mats = None
        self._cached_signature = None
        self._satuan_lookup: dict = {}
        self._result_df = None
        # opsi tampilan
        self._show_all_resto = tk.BooleanVar(value=False)
        # v3.9.2: minus merah PER CELL
        self._cell_tags = CELL_TAGS_SUPPORTED
        self._neg_cells: list = []      # [(iid, col)] nilai < 0
        self._st_match_cells: list = []
        self._st_diff_cells: list = []
        self._st_missing_cells: list = []

        self._build_ui()
        self._setup_tags()
        self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="⚖", title="Belum ada data komparasi",
            subtitle="Jalankan pipeline untuk memuat data app, lalu pilih "
                     "file deviasi (mis. \"20.AGUSTUS 2026.xlsx\") untuk "
                     "dibandingkan dengan Tab 📦 Deviasi GR.",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card: pemilih file + opsi ---
        fcard = Card(
            self.content, title="⚖ Komparasi File Deviasi vs Tab Deviasi GR",
            subtitle="Pilih file deviasi (laporan resmi per minggu: QTY "
                     "BOM / QTY COM / QTY DEVIASI / % TO BOM). Tiap minggu "
                     "dibandingkan pada KOLOM H: WEEK 1→7 · WEEK 2→14 · "
                     "WEEK 3/4→25. Sisi app: GR = SO_H − Sistem (persis "
                     "tab 📦 Deviasi GR), BOM = Σ penjualan 22.05 (1..H), "
                     "COM = Σ pemakaian (1..H) — semua dari data pipeline, "
                     "tanpa file tambahan.")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        self._fcard = fcard
        fbody = fcard.body()

        r1 = tk.Frame(fbody, bg=C_CARD)
        r1.pack(fill="x")
        btn_pick = GhostButton(r1, text="📂 Pilih File Deviasi…",
                               command=self._pick_file)
        btn_pick.pack(side="left")
        add_tooltip(btn_pick,
                    "Pilih file Excel laporan deviasi (kolom: STATUS BULAN, "
                    "RESTO, NAMA BAHAN, QTY BOM, QTY COM, QTY DEVIASI).\n"
                    "Minggu dipetakan ke kolom H: WEEK 1→7, WEEK 2→14, "
                    "WEEK 3/4→25.")
        self._file_label_var = tk.StringVar(
            value="Belum ada file dipilih.")
        self._file_label = tk.Label(
            r1, textvariable=self._file_label_var, bg=C_CARD,
            fg=C_TEXT_MUTED, font=font(9), anchor="w", justify="left")
        self._file_label.pack(side="left", padx=(10, 8), fill="x",
                              expand=True)
        add_tooltip(self._file_label,
                    "File deviasi aktif + ringkasan isi (baris, minggu, "
                    "resto, bulan).")
        self._btn_close = GhostButton(r1, text="✕ Tutup File",
                                      command=self._close_file)
        self._btn_close.pack(side="right")
        add_tooltip(self._btn_close, "Buang file deviasi dari perbandingan.")
        self._btn_close.configure(state="disabled")

        # baris ke-2: chip pemetaan minggu→H + opsi resto
        r2 = tk.Frame(fbody, bg=C_CARD)
        r2.pack(fill="x", pady=(6, 0))
        tk.Label(r2, text="MINGGU → H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._week_chips = tk.Frame(r2, bg=C_CARD)
        self._week_chips.pack(side="left", padx=(6, 16))
        self._render_week_chips()
        self._chk_all = tk.Checkbutton(
            r2, text="Tampilkan resto di luar data app",
            variable=self._show_all_resto, bg=C_CARD, fg=C_HEADER,
            font=font(9), selectcolor="#ffffff", activebackground=C_CARD,
            activeforeground=C_HEADER, command=self._on_option_changed)
        self._chk_all.pack(side="left")
        add_tooltip(self._chk_all,
                    "Default: hanya resto yang ADA di data app (mis. 20 "
                    "resto cek stock) yang ditampilkan.\nCentang untuk "
                    "menampilkan SEMUA resto di file (340 cabang) — baris "
                    "tanpa data app diberi status TIDAK ADA DI DATA APP.")

        GhostButton(r2, text="↻ Muat Ulang File",
                    command=self._reload_file).pack(side="right")
        GhostButton(r2, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="right",
                                                     padx=(0, 6))

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._title_label = tk.Label(
            head, text="Komparasi Deviasi — File vs Tab 📦 Deviasi GR",
            bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        self._title_label.pack(side="left")
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        add_tooltip(btn_max, "Buka tabel ini dalam window besar\n"
                             "(filter & sort juga jalan di window besar;\n"
                             "Esc untuk menutup)")
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel")
        btn_expand.pack(side="right", padx=(0, 6))
        add_tooltip(btn_expand,
                    "Sembunyikan kartu Filter & judul supaya tabel "
                    "memakai seluruh tinggi tampilan.\nKlik lagi (⤡ "
                    "Tampilkan Filter & KPI) untuk mengembalikan.")
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        add_tooltip(btn_cols, "Sembunyikan / tampilkan kolom\n"
                              "(juga bisa: klik kanan judul kolom)")
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))
        add_tooltip(btn_fit, "Sesuaikan lebar semua kolom ke konten\n"
                             "(double-click tepi kolom = auto-fit 1 kolom;\n"
                             "drag tepi kolom = atur lebar manual)")

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="browse")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name)
        # heading penjelas tiap sisi
        self._update_headings()

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        enable_col_resize(self.tree)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Label(foot, text="🖱 Double-click baris → detail · ✓ = Follow Up "
                            "· klik judul kolom ⧩ = filter + sort · "
                            "Selisih = GR App − DEV File",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(side="left")
        self.status_var_label = tk.StringVar(value="Belum ada file.")
        tk.Label(foot, textvariable=self.status_var_label, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold")).pack(side="right")

        self.overlay = LoadingOverlay(tbody, "Membandingkan deviasi…")

        _filter_cols = [c[0] for c in self.COLUMNS if c[0] != "✓"]
        self._col_sel: dict = {c: None for c in _filter_cols}
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))

        self._expander = TableExpander(btn_expand,
                                       [fcard, self._title_label])

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

    def _render_week_chips(self):
        """Chip 'WEEK 1→H 7' sesuai minggu yang ada di file (atau default)."""
        for c in self._week_chips.winfo_children():
            c.destroy()
        weeks = (self._file_meta.get("weeks")
                 or ["WEEK 1", "WEEK 2", "WEEK 4"])
        for w in weeks:
            h = _week_h(w)
            chip = tk.Frame(self._week_chips, bg="#f1f5f9",
                            highlightbackground="#e2e8f0",
                            highlightthickness=1)
            chip.pack(side="left", padx=(0, 6))
            tk.Label(chip, text=f"{w} → H {h if h is not None else '?'}",
                     bg="#f1f5f9", fg=C_ACCENT,
                     font=font(9, "bold")).pack(padx=8, pady=(2, 3))

    def _update_headings(self):
        """Heading dua sisi (File vs App) — jelas dari mana angka berasal."""
        heads = {
            "BOM File": "BOM — File",
            "COM File": "COM — File",
            "DEV File": "DEVIASI — File",
            "%TO BOM File": "% TO BOM — File",
            "BOM App": "BOM — App (Σ jual 22.05)",
            "COM App": "COM — App (Σ pakai)",
            "DEV App": "DEV TO BOM — App",
            "GR App": "DEVIASI — App (Tab GR)",
            "Selisih": "Selisih (GR App − DEV File)",
        }
        for col, text in heads.items():
            self.tree.heading(col, text=text)
        if getattr(self, "header_filters", None) is not None:
            self.header_filters.refresh_icons()

    # =========================================================================
    # ✓ FOLLOW-UP (klik sel ✓) — pola identik view lain
    # =========================================================================
    def _on_tree_click(self, event):
        tree = event.widget
        try:
            if tree.identify_region(event.x, event.y) != "cell":
                return
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
        """Lazy refresh: compute hanya saat pane terlihat."""
        if self._dirty and self.data is not None and not self.data.empty:
            self._dirty = False
            self._refresh()

    def _col_values(self, col: str) -> list:
        result = self._result_df
        if result is None or result.empty or col not in result.columns:
            return []
        return self._format_col_series(col, result[col]).unique().tolist()

    def _format_col_series(self, col: str, series):
        if col in self.NUMERIC_COLS:
            if col == "%TO BOM File":
                return series.map(self._fmt_pct)
            return series.map(self._fmt_num)
        return series.astype(str)

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
        self._refresh()

    def _on_option_changed(self):
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
        tree.tag_configure("match_row", foreground="#15803d")
        # per-cell
        tree.tag_configure("neg_cell", foreground="#dc2626")
        tree.tag_configure("st_match", foreground="#15803d")
        tree.tag_configure("st_diff", foreground=C_AMBER)
        tree.tag_configure("st_missing", foreground="#dc2626")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        self._cached_mats = None
        self._cached_signature = None
        self._satuan_lookup = {}
        self._result_df = None
        if getattr(self, "_expander", None) is not None:
            self._expander.reset()
        self._show_content()
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        # lazy refresh — compute hanya bila pane terlihat
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    # =========================================================================
    # FILE DEVIASI
    # =========================================================================
    def _pick_file(self):
        if self.data is None or self.data.empty:
            messagebox.showinfo(
                "Belum ada data app",
                "Jalankan pipeline dulu (tab 🚀 Proses) supaya ada data "
                "app untuk dibandingkan dengan file deviasi.",
                parent=self.winfo_toplevel())
            return
        initialdir = self._initial_dir or None
        # ingat folder terakhir bila ada
        if os.path.isfile(_LAST_FILE_JSON):
            try:
                with open(_LAST_FILE_JSON, "r", encoding="utf-8") as f:
                    last = json.load(f).get("path", "")
                if last and os.path.isdir(os.path.dirname(last)):
                    initialdir = os.path.dirname(last)
            except Exception:
                pass
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(), title="Pilih File Deviasi",
            initialdir=initialdir,
            filetypes=[("Excel", "*.xlsx *.xlsm *.xls"),
                       ("Semua file", "*.*")])
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str):
        res = parse_deviasi_file(path)
        if not res["ok"]:
            messagebox.showerror("File deviasi tidak valid", res["error"],
                                 parent=self.winfo_toplevel())
            self.status_var_label.set(f"⚠ {res['error']}")
            return
        self._file_df = res["df"]
        self._file_meta = res["meta"]
        self._file_path = path
        # simpan path terakhir (initialdir dialog berikutnya)
        try:
            with open(_LAST_FILE_JSON, "w", encoding="utf-8") as f:
                json.dump({"path": path}, f)
        except Exception:
            pass
        self._btn_close.configure(state="normal")
        self._render_week_chips()
        meta = self._file_meta
        info = (f"{meta['file_name']} · {meta['n_rows']} baris · "
                f"{meta['n_resto']} resto · {', '.join(meta['weeks'])}")
        if meta.get("bulan"):
            info += f" · BULAN: {', '.join(meta['bulan'])}"
        if meta.get("n_unknown_week"):
            info += (f" · {meta['n_unknown_week']} baris minggu tak "
                     f"dikenal dibuang")
        self._file_label_var.set(info)
        self._file_label.configure(fg=C_HEADER)
        self._refresh()

    def _close_file(self):
        self._file_df = None
        self._file_meta = {}
        self._file_path = ""
        self._btn_close.configure(state="disabled")
        self._file_label_var.set("Belum ada file dipilih.")
        self._file_label.configure(fg=C_TEXT_MUTED)
        self._render_week_chips()
        self.tree.delete(*self.tree.get_children())
        self._result_df = None
        self.status_var_label.set(
            "File ditutup — klik 📂 Pilih File Deviasi… untuk memuat.")

    def _reload_file(self):
        if self._file_path and os.path.isfile(self._file_path):
            self._load_file(self._file_path)
        else:
            self._pick_file()

    # =========================================================================
    # COMPUTATION — matriks app (H-independen, cache per data)
    # =========================================================================
    def _compute_matrices(self) -> "dict | None":
        """Pivot data app per (Nama Barang × NAMA RESTO) × tanggal untuk
        JENIS yang dipakai komparasi. Formula com identik
        laporan_deviasi_view._compute_com_matrix / pivot 6.PEMAKAIAN (COM):
            com(t0)  = SALDO AWAL + IN(t0) − BK(t0) − SO(t0)
            com(t>0) = SO(t-1) + IN(t) − BK(t) − SO(t)
        Ditambah matriks so / sis (2.SALDO AKHIR) / out (9.OUT).
        """
        df = self.data
        if df is None or df.empty:
            return None

        jenis_needed = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "4.IN",
                        "8.BARANG KELUAR", "9.OUT"]
        d = df[df["JENIS"].astype(str).isin(jenis_needed)].copy()
        if d.empty:
            self._build_satuan_lookup(df)
            return None
        d["_tgl"] = pd.to_numeric(d["Tanggal"], errors="coerce")
        d = d.dropna(subset=["_tgl"])
        d["NILAI"] = pd.to_numeric(d["NILAI"], errors="coerce")
        if d.empty:
            self._build_satuan_lookup(df)
            return None

        try:
            pivot = d.pivot_table(
                index=["Nama Barang", "NAMA RESTO", "JENIS"],
                columns="_tgl", values="NILAI",
                aggfunc="sum", fill_value=0,
            )
        except Exception:
            self._build_satuan_lookup(df)
            return None
        if pivot.empty:
            self._build_satuan_lookup(df)
            return None

        col_keys = sorted(pivot.columns.tolist(), key=_chrono)
        pairs = pivot.index.droplevel("JENIS").unique()

        def jenis_df(jenis: str) -> pd.DataFrame:
            try:
                sub = pivot.xs(jenis, level="JENIS")
            except KeyError:
                sub = pd.DataFrame()
            return (sub.reindex(index=pairs, columns=col_keys)
                    .astype("float64").fillna(0.0))

        so = jenis_df("1.SO")
        sa = jenis_df("SALDO AWAL")
        sis = jenis_df("2.SALDO AKHIR")
        bm = jenis_df("4.IN")
        bk = jenis_df("8.BARANG KELUAR")
        out = jenis_df("9.OUT")

        so_prev = so.shift(1, axis=1).fillna(0.0)
        if len(col_keys):
            so_prev.iloc[:, 0] = sa.iloc[:, 0]
        com = so_prev + bm - bk - so

        self._build_satuan_lookup(df)
        return {"pairs": pairs, "col_keys": col_keys, "com": com,
                "out": out, "so": so, "sis": sis}

    def _build_satuan_lookup(self, df: pd.DataFrame):
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

    def _per_h_values(self, mats: dict, h_list: list) -> dict:
        """Nilai app per H: gr (SO_H − Sistem_H), bom_app, com_app, dev_app.

        bom_app / com_app memakai KONVENSI FILE (pemakaian = minus)
        supaya kolom berdampingan langsung bisa dibandingkan:
            bom_app = −Σ out[t], com_app = −Σ com[t], t = 1..H
            dev_app = com_app − bom_app (formula identik file)
            gr      = so[H] − sis[H]  (persis tab 📦 Deviasi GR)
        """
        out = {}
        col_keys = mats["col_keys"]
        com, outm, so, sis = (mats["com"], mats["out"],
                              mats["so"], mats["sis"])
        for h in h_list:
            h = int(h)
            pos = [t for t in col_keys if 1 <= float(t) <= h]
            has_h = any(int(float(t)) == h for t in col_keys)
            entry = {"has_h": has_h, "h": h}
            if has_h:
                key_h = next(t for t in col_keys if int(float(t)) == h)
                entry["gr"] = (so[key_h] - sis[key_h]).astype("float64")
                entry["so_h"] = so[key_h]
                entry["sis_h"] = sis[key_h]
            else:
                entry["gr"] = None
            if pos:
                com_app = -com[pos].sum(axis=1).astype("float64")
                bom_app = -outm[pos].sum(axis=1).astype("float64")
            else:
                com_app = pd.Series(0.0, index=com.index)
                bom_app = pd.Series(0.0, index=com.index)
            entry["com_app"] = com_app
            entry["bom_app"] = bom_app
            entry["dev_app"] = com_app - bom_app
            out[h] = entry
        return out

    # =========================================================================
    # RENDER (async + batched)
    # =========================================================================
    def _refresh(self, sync: bool = False):
        if self.data is None or self.data.empty:
            self.status_var_label.set(
                "Belum ada data. Jalankan pipeline di tab Proses.")
            return
        if self._file_df is None:
            self.tree.delete(*self.tree.get_children())
            self.status_var_label.set(
                "Belum ada file — klik '📂 Pilih File Deviasi…' untuk "
                "memuat file perbandingan.")
            return

        if self._busy:
            self._pending = True
            return
        self._busy = True

        sig = (id(self.data), id(self._file_df),
               bool(self._show_all_resto.get()))
        st = {
            "col_sel": {c: s for c, s in self._col_sel.items() if s},
            "show_all": bool(self._show_all_resto.get()),
        }

        def work():
            if self._cached_mats is None or self._cached_signature != sig[0]:
                self._cached_mats = self._compute_matrices()
                self._cached_signature = sig[0]
            return self._prepare_rows(st)

        def done(payload):
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Membandingkan deviasi…", sync=sync,
                  on_error=self._on_error)

    def _on_error(self, err):
        """FIX B-01: _busy di-reset di jalur error supaya view tidak
        mati permanen setelah 1x gagal compute."""
        self._busy = False
        self._pending = False
        self.status_var_label.set(f"⚠ Gagal membandingkan: {err}")

    def _prepare_rows(self, st: dict) -> dict:
        """Pure pandas: gabung file × matriks app → baris komparasi
        (delegasi ke implementasi vektor — thread-safe)."""
        fdf = self._file_df
        mats = self._cached_mats
        if fdf is None:
            return {"items": [], "status": "Belum ada file."}
        if mats is None:
            self._result_df = None
            return {"items": [], "status":
                    "Data app tidak punya JENIS yang dibutuhkan "
                    "(SO / SALDO AKHIR / IN / OUT). Jalankan ulang pipeline."}

        col_keys = mats["col_keys"]
        avail_pos = sorted(int(float(t)) for t in col_keys
                           if float(t) >= 1)
        avail_max = avail_pos[-1] if avail_pos else 0

        h_list = sorted({int(v) for v in fdf["_h"]})
        per_h = self._per_h_values(mats, h_list)

        # lookup app: (bahan_norm, resto_norm) → pasangan (barang, resto)
        pair_index = {}
        for (nb, nr) in mats["pairs"]:
            pair_index[(_norm_name(nb), _norm_resto(nr))] = (nb, nr)
        resto_set = {_norm_resto(nr) for (_, nr) in mats["pairs"]}

        return self._prepare_rows_vec(fdf, per_h, pair_index, resto_set,
                                      st, avail_max)

    def _prepare_rows_vec(self, fdf, per_h, pair_index, resto_set,
                          st, avail_max) -> dict:
        """Implementasi vektor _prepare_rows — akses kolom berspasi aman
        via DataFrame pandas (tanpa itertuples)."""
        n = len(fdf)
        df = pd.DataFrame({
            "Resto": fdf["Resto"].astype(str).values,
            "Nama Barang": fdf["Nama Barang"].astype(str).values,
            "Satuan": fdf["Satuan"].astype(str).values,
            "Minggu": fdf["Minggu"].astype(str).values,
            "H": fdf["_h"].astype(int).values,
            "BOM File": pd.to_numeric(fdf["BOM File"],
                                      errors="coerce").fillna(0.0).values,
            "COM File": pd.to_numeric(fdf["COM File"],
                                      errors="coerce").fillna(0.0).values,
            "DEV File": pd.to_numeric(fdf["DEV File"],
                                      errors="coerce").fillna(0.0).values,
            "%TO BOM File": pd.to_numeric(fdf["%TO BOM File"],
                                          errors="coerce").values,
        })

        # nilai app per baris (lookup per grup H)
        bom_app = np.full(n, np.nan)
        com_app = np.full(n, np.nan)
        dev_app = np.full(n, np.nan)
        gr_app = np.full(n, np.nan)
        status = np.empty(n, dtype=object)
        status[:] = ""

        keys = list(zip(fdf["_bahan_norm"].astype(str).values,
                        fdf["_resto_norm"].astype(str).values))
        hvals = df["H"].values

        for h, ph in per_h.items():
            mask = hvals == h
            if not mask.any():
                continue
            idxs = np.where(mask)[0]
            for i in idxs:
                key = keys[i]
                pair = pair_index.get(key)
                if pair is None:
                    status[i] = "TIDAK ADA DI DATA APP"
                    continue
                if not ph["has_h"]:
                    status[i] = "H TIDAK ADA DI DATA"
                    continue
                bom_app[i] = float(ph["bom_app"].get(pair, np.nan))
                com_app[i] = float(ph["com_app"].get(pair, np.nan))
                dev_app[i] = float(ph["dev_app"].get(pair, np.nan))
                gr_app[i] = float(ph["gr"].get(pair, np.nan))
                selisih = gr_app[i] - float(df["DEV File"].values[i])
                if np.isnan(gr_app[i]):
                    status[i] = "H TIDAK ADA DI DATA"
                elif abs(selisih) <= TOL_ABS + TOL_REL * abs(
                        float(df["DEV File"].values[i])):
                    status[i] = "MATCH"
                else:
                    status[i] = "SELISIH"

        df["BOM App"] = bom_app
        df["COM App"] = com_app
        df["DEV App"] = dev_app
        df["GR App"] = gr_app
        # NaN otomatis menjalar dari gr_app (baris tanpa nilai app)
        df["Selisih"] = gr_app - df["DEV File"].values
        df["Status"] = status

        # default: sembunyikan resto di luar data app
        in_app_resto = np.array([r in resto_set for r in
                                 fdf["_resto_norm"].astype(str).values])
        if not st["show_all"]:
            keep = in_app_resto | (df["Status"].values == "H TIDAK ADA DI DATA")
            df = df[keep].reset_index(drop=True)
            n_hidden = int((~keep).sum())
        else:
            n_hidden = 0

        n_all = len(df)  # noqa: F841 — dipakai di docstring/status di bawah
        n_match = int((df["Status"] == "MATCH").sum())
        n_sel = int((df["Status"] == "SELISIH").sum())
        n_noapp = int((df["Status"] == "TIDAK ADA DI DATA APP").sum())
        n_noh = int((df["Status"] == "H TIDAK ADA DI DATA").sum())

        # snapshot utk filter header (SEBELUM filter header)
        self._result_df = df.copy()

        # filter header ⧩ — kecocokan nilai TERFORMAT
        filtered = df
        for col, sel in st["col_sel"].items():
            if col in filtered.columns and sel:
                fmt = self._format_col_series(col, filtered[col])
                filtered = filtered[fmt.isin(sel)]
        if filtered.empty:
            return {"items": [], "status":
                    "Tidak ada baris setelah filter. Klik '✕ Reset Filter' "
                    "atau ubah filter."}

        # sort default: Resto, Nama Barang, H
        filtered = filtered.sort_values(
            ["Resto", "Nama Barang", "H"],
            ascending=[True, True, True], kind="stable")

        cols_np = {c: filtered[c].to_numpy() for c in
                   ("Resto", "Nama Barang", "Satuan", "Minggu", "H",
                    "BOM File", "COM File", "DEV File", "%TO BOM File",
                    "BOM App", "COM App", "DEV App", "GR App", "Selisih",
                    "Status")}
        items = []
        fp_map = {}
        row_snaps = {}
        neg_cells = []
        st_match_cells = []
        st_diff_cells = []
        st_missing_cells = []
        store = self.store
        m = len(filtered)
        for i in range(m):
            resto = str(cols_np["Resto"][i])
            barang = str(cols_np["Nama Barang"][i])
            h = int(cols_np["H"][i])
            status = str(cols_np["Status"][i])
            fmt_vals = {
                "BOM File": self._fmt_num(cols_np["BOM File"][i]),
                "COM File": self._fmt_num(cols_np["COM File"][i]),
                "DEV File": self._fmt_num(cols_np["DEV File"][i]),
                "%TO BOM File": self._fmt_pct(cols_np["%TO BOM File"][i]),
                "BOM App": self._fmt_num(cols_np["BOM App"][i]),
                "COM App": self._fmt_num(cols_np["COM App"][i]),
                "DEV App": self._fmt_num(cols_np["DEV App"][i]),
                "GR App": self._fmt_num(cols_np["GR App"][i]),
                "Selisih": self._fmt_num(cols_np["Selisih"][i]),
            }
            values = ["", resto, barang, str(cols_np["Satuan"][i]),
                      str(cols_np["Minggu"][i]), str(h),
                      fmt_vals["BOM File"], fmt_vals["COM File"],
                      fmt_vals["DEV File"], fmt_vals["%TO BOM File"],
                      fmt_vals["BOM App"], fmt_vals["COM App"],
                      fmt_vals["DEV App"], fmt_vals["GR App"],
                      fmt_vals["Selisih"], status]

            snap = {
                "asal": "KOMPARASI",
                "resto": _norm_resto(resto),
                "barang": barang,
                "satuan": str(cols_np["Satuan"][i]),
                "h": h,
                "so": (None if np.isnan(cols_np["GR App"][i])
                       else float(cols_np["GR App"][i])),
                "sistem": float(cols_np["DEV File"][i]),
                "deviasi": (None if np.isnan(cols_np["Selisih"][i])
                            else float(cols_np["Selisih"][i])),
                "cek": status,
                "minggu": str(cols_np["Minggu"][i]),
            }
            fp = row_fingerprint(snap)
            checked = store is not None and store.has(fp)
            values[0] = CHECK_ON if checked else CHECK_OFF
            fp_map[f"row_{i}"] = fp
            row_snaps[f"row_{i}"] = snap

            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            # sel status per-cell
            if status == "MATCH":
                st_match_cells.append((f"row_{i}", "Status"))
            elif status == "SELISIH":
                st_diff_cells.append((f"row_{i}", "Status"))
            elif status:
                st_missing_cells.append((f"row_{i}", "Status"))
            # nilai minus per-cell di kolom numerik
            if self._cell_tags:
                for col in self.NUMERIC_COLS:
                    v = cols_np[col][i]
                    if v is not None and not (isinstance(v, float)
                                              and np.isnan(v)) and v < 0:
                        neg_cells.append((f"row_{i}", col))
            else:
                raw_vals = [cols_np[c][i] for c in self.NUMERIC_COLS]
                if any((v is not None and not (isinstance(v, float)
                        and np.isnan(v)) and v < 0) for v in raw_vals):
                    tags.append("negative")

            items.append(("", f"row_{i}",
                          {"values": values, "tags": tuple(tags)}))

        status = (f"{m} baris · MATCH: {n_match} · SELISIH: {n_sel} · "
                  f"H tdk ada: {n_noh} · di luar data app: {n_noapp}")
        if n_hidden:
            status += (f" · {n_hidden} resto file disembunyikan "
                       f"(centang utk lihat)")
        if avail_max:
            status += f" · tanggal app s/d {avail_max}"
        return {"items": items, "status": status,
                "fp_map": fp_map, "row_snaps": row_snaps,
                "neg_cells": neg_cells,
                "st_match_cells": st_match_cells,
                "st_diff_cells": st_diff_cells,
                "st_missing_cells": st_missing_cells}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self._update_headings()
        self.header_filters.refresh_icons()
        self._fp_map = payload.get("fp_map", {})
        self._row_snaps = payload.get("row_snaps", {})
        self._neg_cells = payload.get("neg_cells", [])
        self._st_match_cells = payload.get("st_match_cells", [])
        self._st_diff_cells = payload.get("st_diff_cells", [])
        self._st_missing_cells = payload.get("st_missing_cells", [])
        self.status_var_label.set(payload["status"])

        def render_done():
            self._reapply_cell_tags(self.tree)
            self._busy = False
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=500,
                          on_done=render_done)

    def _reapply_cell_tags(self, tree):
        """v3.9.2 — pasang ulang tag per-cell (sort = delete+reinsert)."""
        if not self._cell_tags:
            return
        if self._neg_cells:
            apply_cell_tag(tree, "neg_cell", self._neg_cells)
        if self._st_match_cells:
            apply_cell_tag(tree, "st_match", self._st_match_cells)
        if self._st_diff_cells:
            apply_cell_tag(tree, "st_diff", self._st_diff_cells)
        if self._st_missing_cells:
            apply_cell_tag(tree, "st_missing", self._st_missing_cells)

    def _reset_filter(self):
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._refresh()

    # =========================================================================
    # ⛶ PERBESAR (fullscreen)
    # =========================================================================
    def _maximize(self):
        def filter_setup(new_tree):
            attach_clone_filters(
                new_tree,
                [c[0] for c in self.COLUMNS if c[0] != "✓"],
                get_values=self._col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_by(c, reverse=d,
                                                               tree=t))

        win, new_tree = open_tree_maximized(
            self.tree, "Komparasi Deviasi — File vs Tab Deviasi GR",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_filter_setup=filter_setup,
            on_render_done=self._reapply_cell_tags)
        new_tree.bind("<Button-1>", self._on_tree_click, add="+")
        return win, new_tree

    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        if self._busy and tree is None:
            return
        tree = tree if tree is not None else self.tree
        parse = self._parse_num_id if col in self.NUMERIC_COLS else None
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_cell_tags(tree)

    def _auto_fit(self):
        auto_fit_columns(self.tree)

    # =========================================================================
    # DOUBLE-CLICK → POPUP DETAIL (difilter barang + resto + tanggal H)
    # =========================================================================
    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return
        tree = event.widget
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return
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
        if not nama_barang:
            return
        try:
            h = int(row_data.get("H") or 0)
        except (TypeError, ValueError):
            h = 0

        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()
        active_filters = {}
        resto_norm = _norm_resto(row_data.get("Resto"))
        if resto_norm:
            active_filters["NAMA RESTO"] = resto_norm
        show_details_popup(
            root, self.data,
            nama_barang=nama_barang,
            jenis=None,
            tanggal=h,
            filters=active_filters,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _fmt_num(val) -> str:
        """Format angka gaya Indonesia: 1.234.567 / 1.234,5, negatif
        kurung, 0/NaN → '-' (identik view lain)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
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
    def _fmt_pct(val) -> str:
        """Ratio (0.2697) → '26,97%'; NaN → '—'."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        s = f"{val * 100:,.2f}".replace(",", "\u00a0").replace(
            ".", ",").replace("\u00a0", ".")
        if val < 0:
            return f"({s[1:]})%"
        return f"{s}%"

    @staticmethod
    def _parse_num_id(s):
        """Parser sort utk format Indonesia: '1.234' = 1234,
        '(1.234)' = -1234, '-' = 0, '12,5' = 12.5, '26,97%' = 26.97."""
        s = str(s).replace("%", "").replace("—", "").strip()
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
