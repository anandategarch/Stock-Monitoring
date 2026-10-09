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
                com(1) = SALDO AWAL + IN(1) − BK(1) − SO(1)  (SA pair,
                          baris ber-Tanggal=1 — fn_4217; fallback
                          SO(t-1) bila SA tidak ada)
                com(t>1) = SO(t-1) + IN(t) − BK(t) − SO(t)  (formula
                          identik baris 6.PEMAKAIAN (COM) pivot & tab
                          🚨 Anomali COM)
    DEV·App   = COM·App − BOM·App  ("Dev to BOM" versi app)
    GR·App    = SO_H − Sistem_H (2.SALDO AKHIR) — PERSIS kolom Deviasi di
                tab 📦 Deviasi GR pada H minggu tsb.

    v3.9.5: karena Sistem (fn_running_stock) berbasis SALDO AWAL dan com(1)
    kini juga berbasis SA → GR·App == DEV·App secara ALJABAR PERSIS (dua
    jalur hitung saling cek internal; dulu menyimpang sebesar SO(−31)−SA
    saat data memuat tanggal negatif bulan lalu).

VERDIK: Selisih = GR·App − DEV·File → Status MATCH (dalam toleransi) /
SELISIH / TIDAK ADA DI DATA APP / H TIDAK ADA DI DATA.

v3.9.7 — FILTER MINGGU MENGIKUTI H BERSAMA (permintaan user:
"STATUS BULAN itu berguna buat filter. misal H aku input 7 maka
hanya tampilkan week 1 aja"): view kini berlangganan SharedTanggalH
(chip read-only, pola tab Anomali COM). Rentang minggu yang MEMUAT H:
    H 1–7 → WEEK 1 (cut-off 7)      H 8–14  → WEEK 2 (cut-off 14)
    H 15–25 → WEEK 3/4 (cut-off 25) H 26–31 → WEEK 5 (cut-off 31)
Default: hanya baris minggu tsb yang tampil (chip minggu aktif
di-highlight). Centang "Tampilkan semua minggu" utk perilaku lama.
File tanpa minggu tsb → 0 baris + pesan jujur (minggu di file
didaftar).

RESTO: file memakai kode bercabang ("1041.BDGUKU", "B.1001.MLGPAR") —
dinormalkan ke segmen setelah titik terakhir ("BDGUKU") lalu dicocokkan
ke NAMA RESTO data app (upper + strip).

INFRASTRUKTUR (dipertahankan dari view lain): ✓ follow-up, filter header
⧩ semua kolom, sort engine linear (parser angka Indonesia), ⛶ Layar Penuh,
⤢ Perbesar Tabel, ◱ Kolom, ↔ Auto-Fit, loading overlay + compute async +
on_error reset _busy (FIX B-01), minus merah PER CELL (v3.9.2 apply_cell_tag),
sel Status berwarna per-cell (MATCH hijau / SELISIH amber / lainnya merah).
"""

import contextlib
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


def _h_to_week_target(h: int) -> int:
    """v3.9.7: H input → CUT-OFF minggu yang MEMUAT tanggal H
    (minggu file = rentang kumulatif dari tanggal 1):
        H 1–7 → 7 (WEEK 1) · H 8–14 → 14 (WEEK 2) ·
        H 15–25 → 25 (WEEK 3/4) · H 26–31 → 31 (WEEK 5)
    Total: semua H 1..31 terpetakan (H=7 → WEEK 1 persis permintaan
    user "H aku input 7 maka hanya tampilkan week 1")."""
    h = int(h)
    if h <= 7:
        return 7
    if h <= 14:
        return 14
    if h <= 25:
        return 25
    return 31

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


def _norm_col_map(df: pd.DataFrame) -> dict:
    """Peta kolom ternormalisasi (case/spasi diabaikan) → kolom asli."""
    cols = {}
    for c in df.columns:
        cols[str(c).strip().upper().replace(" ", "")] = c
    return cols


def _find_col(cols: dict, *cands):
    for cand in cands:
        key = cand.upper().replace(" ", "")
        if key in cols:
            return cols[key]
    return None


def _missing_required_columns(df: pd.DataFrame) -> list:
    """Label kolom wajib yang hilang dari df ([] = lengkap)."""
    cols = _norm_col_map(df)
    got = {
        "RESTO": _find_col(cols, "RESTO", "NAMARESTO", "CABANG"),
        "NAMA BAHAN": _find_col(cols, "NAMABAHAN", "NAMABARANG", "BARANG",
                                "ITEM"),
        "STATUS BULAN": _find_col(cols, "STATUSBULAN", "STATUSMINGGU",
                                  "WEEK", "MINGGU", "STATUS"),
        "QTY BOM": _find_col(cols, "QTYBOM", "BOM"),
        "QTY COM": _find_col(cols, "QTYCOM", "COM"),
        "QTY DEVIASI": _find_col(cols, "QTYDEVIASI", "DEVIASI"),
    }
    return [label for label, c in got.items() if c is None]


def parse_deviasi_file(path: str) -> dict:
    """Baca & validasi file deviasi (pure — tanpa Tk; mudah diuji).

    Return dict:
        ok: bool
        error: str (bila not ok)
        df: DataFrame ternormalisasi (kolom _resto_norm, _bahan_norm,
            _week, _h) atau None
        meta: {weeks, n_rows, n_resto, bulan, file_name, sheet,
               n_unknown_week, n_duplicates}

    v3.9.5 (audit 19-a #5/#11): duplikat lintas bulan DIHITUNG & dilaporkan
    via meta.n_duplicates (dulu dibuang diam-diam — file "History"
    multi-bulan); sheet dicoba satu per satu sampai ketemu sheet dengan
    kolom wajib (dulu hanya sheet pertama — data di sheet lain → error
    kolom yang menyesatkan).
    """
    meta = {"file_name": os.path.basename(path), "sheet": None,
            "weeks": [], "n_rows": 0, "n_resto": 0, "bulan": []}
    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        return {"ok": False, "error": f"Gagal membaca file: {e}",
                "df": None, "meta": meta}

    # v3.9.5 (audit 19-a #11): pilih sheet PERTAMA yang punya kolom wajib
    # & berisi baris; bila tidak ada → pakai sheet pertama utk pesan error.
    df = None
    sheet = None
    for sh in xl.sheet_names:
        cand = None
        with contextlib.suppress(Exception):
            cand = xl.parse(sh)
        if cand is None or cand.empty:
            if df is None:
                df, sheet = cand, sh
            continue
        if not _missing_required_columns(cand):
            df, sheet = cand, sh
            break
        if df is None or df.empty:
            df, sheet = cand, sh
    if df is None:
        return {"ok": False, "error": "File kosong (tidak ada baris).",
                "df": None, "meta": meta}
    meta["sheet"] = sheet

    if df.empty:
        return {"ok": False, "error": "File kosong (tidak ada baris).",
                "df": None, "meta": meta}

    missing = _missing_required_columns(df)
    if missing:
        return {"ok": False,
                "error": "Kolom wajib tidak ditemukan: "
                         + ", ".join(missing)
                         + ". Kolom file (sheet " + str(sheet) + "): "
                         + ", ".join(str(c) for c in df.columns[:12]),
                "df": None, "meta": meta}

    # --- deteksi kolom (nama fleksibel, case/space-insensitive) ---
    cols = _norm_col_map(df)
    col_resto = _find_col(cols, "RESTO", "NAMARESTO", "CABANG")
    col_bahan = _find_col(cols, "NAMABAHAN", "NAMABARANG", "BARANG", "ITEM")
    col_week = _find_col(cols, "STATUSBULAN", "STATUSMINGGU", "WEEK",
                         "MINGGU", "STATUS")
    col_bom = _find_col(cols, "QTYBOM", "BOM")
    col_com = _find_col(cols, "QTYCOM", "COM")
    col_dev = _find_col(cols, "QTYDEVIASI", "DEVIASI")
    col_sat = _find_col(cols, "SATUAN", "UOM", "UNIT")
    col_pct = None
    for k, orig in cols.items():
        if k.startswith("%") and "DEVIASI" in k and "BOM" in k:
            col_pct = orig
            break
    col_bulan = _find_col(cols, "BULAN", "MONTH")

    out = pd.DataFrame({
        "Resto": df[col_resto].astype(str),
        "Nama Barang": df[col_bahan].astype(str),
        # v3.9.5 (audit 19-a #13): NaN → '' (astype(str) menghasilkan
        # literal 'nan')
        "Satuan": (df[col_sat].fillna("").astype(str)
                   if col_sat is not None else ""),
        "Minggu": df[col_week].astype(str).str.strip().str.upper(),
        "BOM File": pd.to_numeric(df[col_bom], errors="coerce"),
        "COM File": pd.to_numeric(df[col_com], errors="coerce"),
        "DEV File": pd.to_numeric(df[col_dev], errors="coerce"),
    })
    out["%TO BOM File"] = (pd.to_numeric(df[col_pct], errors="coerce")
                           if col_pct is not None else np.nan)
    out["BULAN"] = (df[col_bulan].fillna("").astype(str).str.strip()
                    if col_bulan is not None else "")

    out["_resto_norm"] = out["Resto"].map(_norm_resto)
    out["_bahan_norm"] = out["Nama Barang"].map(_norm_name)
    out["_h"] = out["Minggu"].map(_week_h)

    # minggu tak dikenal → baris dibuang (dilaporkan via meta)
    bad_week = out["_h"].isna()
    n_bad = int(bad_week.sum())
    out = out[~bad_week].copy()

    # duplikat (minggu, resto, bahan) → keep first (file sampel unik);
    # v3.9.5 (audit 19-a #5): jumlah duplikat DIHITUNG (umumnya baris
    # bulan lain — file "History" multi-bulan) & dilaporkan via meta —
    # dulu dibuang diam-diam.
    before_dedup = len(out)
    out = out.drop_duplicates(
        subset=["Minggu", "_resto_norm", "_bahan_norm"], keep="first")
    n_dup = before_dedup - len(out)

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
    meta["n_duplicates"] = n_dup
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
                 initial_dir: str = "", h_state=None):
        super().__init__(parent, bg=C_BG)
        self.data: pd.DataFrame | None = None
        self.go_to_proses = go_to_proses
        self.store = followup_store
        self._initial_dir = initial_dir
        # v3.9.7: TANGGAL H = state bersama (dari tab 📦 Deviasi GR) —
        # dipakai FILTER MINGGU file (H=7 → hanya WEEK 1; pola chip
        # read-only tab Anomali COM). Komparasi TIDAK punya input H.
        self._h_state = h_state
        self.tanggal_h = int(h_state.h) if h_state is not None else 25
        self._fp_map: dict[str, str] = {}
        self._row_snaps: dict[str, dict] = {}
        self._busy = False
        self._pending = False
        self._dirty = False                 # lazy refresh
        # v3.9.5 (audit 19-a #1): generation counter — job async yang
        # sudah kedaluwarsa (file ditutup/diganti, data baru) dibuang di
        # done() supaya hasil file lama tidak muncul kembali.
        self._render_gen = 0
        self._insert_cancel = None         # batch insert yang berjalan
        self._pending_path: str | None = None   # file yang antre saat busy
        self._pending_sort = None          # (col, reverse) antre saat busy
        # file deviasi yang sedang dibandingkan
        self._file_df: pd.DataFrame | None = None
        self._file_meta: dict = {}
        self._file_path: str = ""
        # cache matriks app — per objek data + file
        self._cached_mats = None
        self._cached_signature = None
        # v3.9.5 (audit 19-b #4): identitas df utk cache (id() bisa
        # dipakai ulang CPython setelah GC; identitas objek lebih aman)
        self._cached_data = None
        self._satuan_lookup: dict = {}
        self._aktif_lookup: dict = {}   # v3.9.5 (audit 19-b #5): AKTIF/NON
        self._result_df = None
        # v3.9.5 (audit 19-a #2): (bahan_norm, resto_norm) → nama barang &
        # resto versi APP — dipakai popup detail (nama file RAW tidak
        # selalu cocok exact dgn nama app).
        self._pair_index: dict = {}
        # opsi tampilan
        self._show_all_resto = tk.BooleanVar(value=False)
        # v3.9.7: filter minggu mengikuti H bersama (default AKTIF);
        # checkbox "Tampilkan semua minggu" = perilaku lama (semua minggu)
        self._show_all_weeks = tk.BooleanVar(value=False)
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
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card: pemilih file + opsi ---
        fcard = Card(self.content,
                     title="⚖ Komparasi File Deviasi vs Tab Deviasi GR")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        self._fcard = fcard
        fbody = fcard.body()

        r1 = tk.Frame(fbody, bg=C_CARD)
        r1.pack(fill="x")
        btn_pick = GhostButton(r1, text="📂 Pilih File Deviasi…",
                               command=self._pick_file)
        btn_pick.pack(side="left")
        self._file_label_var = tk.StringVar(
            value="Belum ada file dipilih.")
        self._file_label = tk.Label(
            r1, textvariable=self._file_label_var, bg=C_CARD,
            fg=C_TEXT_MUTED, font=font(9), anchor="w", justify="left")
        self._file_label.pack(side="left", padx=(10, 8), fill="x",
                              expand=True)
        self._btn_close = GhostButton(r1, text="✕ Tutup File",
                                      command=self._close_file)
        self._btn_close.pack(side="right")
        self._btn_close.configure(state="disabled")

        # baris ke-2: TANGGAL H (read-only, bersama) + filter minggu +
        # opsi resto
        r2 = tk.Frame(fbody, bg=C_CARD)
        r2.pack(fill="x", pady=(6, 0))
        tk.Label(r2, text="TANGGAL H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        # v3.9.7: chip read-only — H dibagikan dari tab 📦 Deviasi GR
        # (pola tab Anomali COM; komparasi tanpa input H sendiri)
        self._h_chip_var = tk.StringVar(value=str(self.tanggal_h))
        hchip = tk.Frame(r2, bg="#f1f5f9", highlightbackground="#e2e8f0",
                         highlightthickness=1)
        hchip.pack(side="left", padx=(6, 8))
        tk.Label(hchip, textvariable=self._h_chip_var, bg="#f1f5f9",
                 fg=C_ACCENT, font=font(11, "bold")).pack(
            padx=10, pady=(2, 3))
        # label minggu aktif (dinamis — file & H)
        self._week_filter_var = tk.StringVar(
            value="belum ada file")
        self._week_filter_label = tk.Label(
            r2, textvariable=self._week_filter_var, bg=C_CARD,
            fg=C_TEXT_MUTED, font=font(9), anchor="w")
        self._week_filter_label.pack(side="left", padx=(2, 12))
        self._chk_all_weeks = tk.Checkbutton(
            r2, text="Tampilkan semua minggu", variable=self._show_all_weeks,
            bg=C_CARD, fg=C_HEADER, font=font(9), selectcolor="#ffffff",
            activebackground=C_CARD, activeforeground=C_HEADER,
            command=self._on_option_changed)
        self._chk_all_weeks.pack(side="left")
        self._chk_all = tk.Checkbutton(
            r2, text="Tampilkan resto di luar data app",
            variable=self._show_all_resto, bg=C_CARD, fg=C_HEADER,
            font=font(9), selectcolor="#ffffff", activebackground=C_CARD,
            activeforeground=C_HEADER, command=self._on_option_changed)
        self._chk_all.pack(side="left", padx=(16, 0))

        GhostButton(r2, text="↻ Muat Ulang File",
                    command=self._reload_file).pack(side="right")
        GhostButton(r2, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="right",
                                                     padx=(0, 6))

        # baris ke-3: chip pemetaan minggu→H (minggu aktif di-highlight)
        r3 = tk.Frame(fbody, bg=C_CARD)
        r3.pack(fill="x", pady=(6, 0))
        tk.Label(r3, text="MINGGU → H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._week_chips = tk.Frame(r3, bg=C_CARD)
        self._week_chips.pack(side="left", padx=(6, 16))
        self._render_week_chips()

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

        self.tree.bind("<Double-1>", self._on_double_click, add="+")  # FIX B-04
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

        # v3.9.7: berlangganan perubahan H bersama (filter minggu file
        # mengikuti H — "H aku input 7 maka hanya tampilkan week 1")
        if self._h_state is not None:
            self._h_state.subscribe(self._on_shared_h_changed)
            # pola laporan_deviasi_view (audit 19-b #3): lepas listener
            # saat view di-destroy (anti listener zombie)
            self.bind("<Destroy>", self._on_view_destroy, add="+")

    def _on_view_destroy(self, event):
        """v3.9.7: lepas langganan H bersama saat view di-destroy
        (hanya event utk view ini sendiri, bukan anak)."""
        if event.widget is self and self._h_state is not None:
            with contextlib.suppress(Exception):
                self._h_state.unsubscribe(self._on_shared_h_changed)

    # =========================================================================
    # TANGGAL H BERSAMA (v3.9.7) — filter minggu file
    # =========================================================================
    def _on_shared_h_changed(self, new_h: int):
        """Listener H bersama: H di-apply di tab 📦 Deviasi GR → chip H +
        label minggu + highlight chip diperbarui, tabel di-refresh dgn
        filter minggu baru (H=7 → WEEK 1 saja). Pane tersembunyi →
        cukup dirty (pola audit 19-c #3 — tidak compute yang tak terlihat)."""
        self.tanggal_h = int(new_h)
        self._update_h_chip()
        if self._dirty:
            return          # belum pernah dirender — refresh saat terlihat
        if not self.winfo_ismapped():
            self._dirty = True   # tersembunyi — refresh saat terlihat lagi
            return
        if (self.data is not None and not self.data.empty
                and self._file_df is not None):
            self._refresh()

    def _update_h_chip(self):
        """Chip H + label minggu aktif + highlight chip minggu."""
        if hasattr(self, "_h_chip_var"):
            self._h_chip_var.set(str(self.tanggal_h))
        self._update_week_filter_label()
        self._render_week_chips()

    def _update_week_filter_label(self):
        """Label '→ minggu: WEEK X' di kartu filter (dinamis: file + H)."""
        if not hasattr(self, "_week_filter_var"):
            return
        if self._file_df is None:
            self._week_filter_var.set("belum ada file")
        elif self._show_all_weeks.get():
            self._week_filter_var.set(
                "filter minggu NONAKTIF — semua minggu tampil")
        else:
            wt = _h_to_week_target(self.tanggal_h)
            weeks = [w for w in (self._file_meta.get("weeks") or [])
                     if _week_h(w) == wt]
            if weeks:
                self._week_filter_var.set(
                    f"→ minggu: {', '.join(weeks)}")
            else:
                self._week_filter_var.set(
                    f"→ minggu cut-off H {wt} TIDAK ADA di file")

    def _render_week_chips(self):
        """Chip 'WEEK 1→H 7' sesuai minggu yang ada di file (atau default).
        v3.9.7: minggu yang MEMUAT H aktif di-highlight teal (bila filter
        minggu aktif)."""
        for c in self._week_chips.winfo_children():
            c.destroy()
        weeks = (self._file_meta.get("weeks")
                 or ["WEEK 1", "WEEK 2", "WEEK 4"])
        wt = (None if self._show_all_weeks.get()
              else _h_to_week_target(self.tanggal_h))
        for w in weeks:
            h = _week_h(w)
            active = wt is not None and h is not None and int(h) == wt
            bg = C_ACCENT if active else "#f1f5f9"
            fg = "#ffffff" if active else C_ACCENT
            chip = tk.Frame(self._week_chips, bg=bg,
                            highlightbackground=(C_ACCENT if active
                                                 else "#e2e8f0"),
                            highlightthickness=1)
            chip.pack(side="left", padx=(0, 6))
            tk.Label(chip, text=f"{w} → H {h if h is not None else '?'}",
                     bg=bg, fg=fg, font=font(9, "bold")).pack(
                padx=8, pady=(2, 3))

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
        # v3.9.7: label minggu + highlight chip ikut opsi semua-minggu
        self._update_week_filter_label()
        self._render_week_chips()
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
        # v3.9.5 (audit 19-a #1): data berganti → job lama dibuang
        self._render_gen += 1
        if self._insert_cancel is not None:
            self._insert_cancel()
            self._insert_cancel = None
        self._cached_mats = None
        self._cached_signature = None
        self._cached_data = None
        self._satuan_lookup = {}
        self._aktif_lookup = {}
        self._result_df = None
        self._pair_index = {}
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
            filetypes=[("Excel", "*.xlsx *.xlsm *.xls *.xlsb"),
                       ("Semua file", "*.*")])
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str):
        """v3.9.5 (audit 19-a #4): PARSE FILE DIJALANKAN DI THREAD WORKER —
        file nyata 9,4MB butuh ±8 detik; parse di main thread membekukan
        UI tanpa overlay. Seluruh parse+compute+join kini satu job async.
        Filter header file LAMA direset DI SINI (sebelum job) — payload
        memakai snapshot state saat job mulai (audit 19-c #5: sisa filter
        menyembunyikan baris file baru secara diam-diam).
        """
        if self.data is None or self.data.empty:
            messagebox.showinfo(
                "Belum ada data app",
                "Jalankan pipeline dulu (tab 🚀 Proses) supaya ada data "
                "app untuk dibandingkan dengan file deviasi.",
                parent=self.winfo_toplevel())
            return
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._refresh(parse_path=path)

    def _apply_file_state(self, new_file: dict, path: str | None):
        """Simpan state file yang baru selesai diparse (main thread)."""
        self._file_df = new_file["df"]
        self._file_meta = new_file["meta"]
        if path:
            self._file_path = path
            # simpan path terakhir (initialdir dialog berikutnya)
            # FIX D-06 (audit 2-d): tulis ATOMIK (tmp + os.replace) — crash
            # di tengah write tidak meninggalkan json korup (pembacaan sudah
            # guarded fallback, tapi file korup tetap mengganggu).
            try:
                tmp = _LAST_FILE_JSON.with_suffix(".json.tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({"path": path}, f)
                os.replace(tmp, _LAST_FILE_JSON)
            except Exception:
                pass
        self._btn_close.configure(state="normal")
        self._render_week_chips()
        # v3.9.7: label minggu aktif mengikuti file yang baru dimuat
        self._update_week_filter_label()
        meta = self._file_meta
        info = (f"{meta['file_name']} · {meta['n_rows']} baris · "
                f"{meta['n_resto']} resto · {', '.join(meta['weeks'])}")
        if meta.get("bulan"):
            info += f" · BULAN: {', '.join(meta['bulan'])}"
        if meta.get("n_unknown_week"):
            info += (f" · {meta['n_unknown_week']} baris minggu tak "
                     f"dikenal dibuang")
        if meta.get("n_duplicates"):
            info += (f" · {meta['n_duplicates']} baris duplikat "
                     f"(minggu+resto+bahan sama) dibuang")
        self._file_label_var.set(info)
        self._file_label.configure(fg=C_HEADER)

    def _close_file(self):
        # v3.9.5 FIX (audit 19-a #1 — P1): ✕ Tutup saat job komparasi masih
        # berjalan → job lama harus dibuang. Tanpa ini, hasil compute file
        # yang barusan ditutup tetap di-render kembali oleh done() (3.418
        # baris + footer file lama muncul lagi padahal label "Belum ada
        # file"). Generation counter + pembatalan batch insert.
        self._render_gen += 1
        self._pending = False
        self._pending_path = None
        self._pending_sort = None
        if self._insert_cancel is not None:
            self._insert_cancel()
            self._insert_cancel = None
        self._file_df = None
        self._file_meta = {}
        self._file_path = ""
        self._pair_index = {}
        self._btn_close.configure(state="disabled")
        self._file_label_var.set("Belum ada file dipilih.")
        self._file_label.configure(fg=C_TEXT_MUTED)
        self._render_week_chips()
        # v3.9.7: label minggu kembali 'belum ada file'
        self._update_week_filter_label()
        self.tree.delete(*self.tree.get_children())
        self._result_df = None
        self._neg_cells = []
        self._st_match_cells = []
        self._st_diff_cells = []
        self._st_missing_cells = []
        # v3.9.5 (audit 19-c #5): reset filter header saat file ditutup
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self.status_var_label.set("File ditutup.")

    def _reload_file(self):
        if self._file_path and os.path.isfile(self._file_path):
            self._load_file(self._file_path)
        else:
            self._pick_file()

    # =========================================================================
    # COMPUTATION — matriks app (H-independen, cache per data)
    # =========================================================================
    def _compute_matrices(self, data: pd.DataFrame | None = None) -> "dict | None":
        """FIX D-01 (audit 2-d): data bisa di-pass eksplisit (identitas
        pra-capture worker) — default membaca self.data (kompatibel test)."""
        """Pivot data app per (Nama Barang × NAMA RESTO) × tanggal untuk
        JENIS yang dipakai komparasi. Formula com identik
        laporan_deviasi_view._compute_com_matrix / pivot 6.PEMAKAIAN (COM):
            com(t=1)  = SALDO AWAL + IN(1) − BK(1) − SO(1)   (bila SA ada)
            com(t>1)  = SO(t-1) + IN(t) − BK(t) − SO(t)
        Ditambah matriks so / sis (2.SALDO AKHIR) / out (9.OUT).

        v3.9.5 FIX (audit 19-a #6 / 19-b #2): base com di TANGGAL 1 kini
        SALDO AWAL milik pair (baris SA ber-Tanggal=1, fn_4217) bila ada;
        fallback SO(t-1) via shift (tanggal negatif bulan lalu), fallback 0.
        SEMANTIK LAMA: SA ditempel ke kolom kronologis PERTAMA GLOBAL —
        saat data memuat tanggal negatif (pipeline FULL), kolom pertama =
        −25 (SA=0 di situ) → SA tidak pernah terpakai, com(1) memakai
        SO(−31), dan pair TANPA data bulan lalu mendapat com(1) =
        IN−BK−SO ≈ −SO(1) = MINUS PALSU (431/654 anomali H=1 di data
        real). Dengan SA sebagai base: GR·App == DEV·App secara aljabar
        (Sistem fn_running_stock juga berbasis SA). Fix diterapkan ke 3
        tempat sekaligus (pivot, laporan, komparasi) supaya formula COM
        tetap identik antar view.
        """
        df = self.data if data is None else data
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

        def jenis_df(jenis: str, fill: bool = True) -> pd.DataFrame:
            try:
                sub = pivot.xs(jenis, level="JENIS")
            except KeyError:
                sub = pd.DataFrame()
            out = (sub.reindex(index=pairs, columns=col_keys)
                   .astype("float64"))
            return out.fillna(0.0) if fill else out

        so = jenis_df("1.SO")
        sis = jenis_df("2.SALDO AKHIR")
        bm = jenis_df("4.IN")
        bk = jenis_df("8.BARANG KELUAR")
        out = jenis_df("9.OUT")

        so_prev = so.shift(1, axis=1).fillna(0.0)
        # v3.9.5 (audit 19-a #6 / 19-b #2): base com tanggal 1 = SALDO
        # AWAL pair (tanpa fillna — membedakan 'SA ada, nilainya 0' dari
        # 'SA tidak ada') bila ada; fallback SO(t-1) shift; kolom pertama
        # tanpa SA → 0 (tidak ada data sebelumnya).
        if len(col_keys):
            so_prev.iloc[:, 0] = 0.0
        pos1 = [c for c in col_keys if int(float(c)) == 1]
        if pos1:
            sa_raw = jenis_df("SALDO AWAL", fill=False)
            key1 = pos1[0]
            so_prev[key1] = sa_raw[key1].fillna(so_prev[key1])
        com = so_prev + bm - bk - so

        self._build_satuan_lookup(df)
        self._build_aktif_lookup(df)
        return {"pairs": pairs, "col_keys": col_keys, "com": com,
                "out": out, "so": so, "sis": sis}

    def _build_aktif_lookup(self, df: pd.DataFrame):
        """v3.9.5 (audit 19-b #5): lookup AKTIF/NON per barang — mengisi
        snapshot follow-up (kolom AKTIF/NON di tab ☑ Follow Up; sebelumnya
        kosong utk baris asal KOMPARASI)."""
        self._aktif_lookup = {}
        if "AKTIF/NON" in df.columns and "Nama Barang" in df.columns:
            adf = (df[["Nama Barang", "AKTIF/NON"]]
                   .dropna(subset=["AKTIF/NON"])
                   .drop_duplicates(subset=["Nama Barang"], keep="first"))
            self._aktif_lookup = dict(zip(
                adf["Nama Barang"].astype(str),
                adf["AKTIF/NON"].astype(str)))

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
    def _refresh(self, sync: bool = False, parse_path: str | None = None):
        if self.data is None or self.data.empty:
            # v3.9.5 (audit 19-a #12): bersihkan baris basi — dulu early-
            # return meninggalkan baris render lama tetap tampil
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
        if parse_path is None and self._file_df is None:
            if self._insert_cancel is not None:
                self._insert_cancel()
                self._insert_cancel = None
            try:
                self.tree.delete(*self.tree.get_children())
            except tk.TclError:
                pass
            self._result_df = None
            self.status_var_label.set("Belum ada file deviasi.")
            return

        if self._busy:
            self._pending = True
            if parse_path is not None:
                self._pending_path = parse_path
            return
        self._busy = True
        # v3.9.7 FIX (ditemukan test §22): _dirty di-CLEAR saat refresh
        # BERJALAN — dulu hanya ensure_refreshed yang me-clear →
        # load_data saat PANE TERLIHAT me-render tabel tapi _dirty tetap
        # True → listener H berikutnya salah menganggap 'belum pernah
        # dirender' & SKIP refresh (tabel basi menampilkan minggu lama).
        self._dirty = False
        # v3.9.5 (audit 19-a #1): gen naik tiap job — done() membuang job
        # yang kedaluwarsa (file ditutup/diganti/data baru).
        gen = self._render_gen = self._render_gen + 1

        st = {
            "col_sel": {c: s for c, s in self._col_sel.items() if s},
            "show_all": bool(self._show_all_resto.get()),
            # v3.9.7: filter minggu sesuai H bersama (None = semua minggu)
            "week_target": (None if self._show_all_weeks.get()
                            else _h_to_week_target(int(self.tanggal_h))),
            "h_label": int(self.tanggal_h),
        }
        path = parse_path

        def work():
            # v3.9.5 (audit 19-a #4): parse file ikut di thread worker —
            # file 9,4MB tadinya membekukan UI ±8 detik (tanpa overlay).
            new_file = None
            if path is not None:
                res = parse_deviasi_file(path)
                if not res["ok"]:
                    return {"gen": gen, "parse_error": res["error"]}
                new_file = res
            # FIX D-01 (audit 2-d): capture identitas SEKALU di awal job —
            # dulu _cached_data dibaca ULANG setelah compute; bila self.data
            # ditukar main thread (load_data pipeline selesai) di tengah
            # compute, cache berlabel data BARU berisi matrix data LAMA →
            # refresh berikutnya SKIP recompute (angka basi senyap;
            # gen-guard hanya membuang RENDER basi, bukan cache salah-label).
            data = self.data
            if (self._cached_mats is None
                    or self._cached_data is not data):
                self._cached_mats = self._compute_matrices(data)
                self._cached_data = data
                self._cached_signature = id(data)
            return self._prepare_rows(st, new_file, gen)

        def done(payload):
            if payload.get("gen") != self._render_gen:
                # v3.9.5 (audit 19-a #1): job kedaluwarsa — buang hasil;
                # jalankan yang mengantre (file baru / refresh data baru)
                # supaya state tidak macet.
                self._busy = False
                p = self._pending_path
                self._pending_path = None
                if p:
                    self._load_file(p)
                elif self._pending:
                    self._pending = False
                    self._refresh()
                return
            if payload.get("parse_error"):
                self._busy = False
                self._pending = False
                self._pending_path = None
                messagebox.showerror("File deviasi tidak valid",
                                     payload["parse_error"],
                                     parent=self.winfo_toplevel())
                self.status_var_label.set(f"⚠ {payload['parse_error']}")
                return
            if payload.get("new_file"):
                self._apply_file_state(payload["new_file"], path)
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Memuat & membandingkan deviasi…", sync=sync,
                  on_error=self._on_error)

    def _on_error(self, err):
        """FIX B-01: _busy di-reset di jalur error supaya view tidak
        mati permanen setelah 1x gagal compute."""
        self._busy = False
        self._pending = False
        self._pending_path = None
        self.status_var_label.set(f"⚠ Gagal membandingkan: {err}")

    def _prepare_rows(self, st: dict, new_file: dict | None = None,
                      gen: int = 0) -> dict:
        """Pure pandas: gabung file × matriks app → baris komparasi
        (delegasi ke implementasi vektor — thread-safe).

        v3.9.5: fdf/new_file diteruskan EKSPLISIT (bukan membaca
        self._file_df dari thread — mutasi UI thread di tengah compute
        = sumber race ✕ Tutup File).
        v3.9.7: FILTER MINGGU sesuai H bersama diterapkan di sini
        (st['week_target'] — None bila 'Tampilkan semua minggu').
        """
        fdf = new_file["df"] if new_file else self._file_df
        mats = self._cached_mats
        if fdf is None:
            return {"gen": gen, "items": [],
                    "status": "Belum ada file."}
        if mats is None:
            self._result_df = None
            return {"gen": gen, "items": [], "status":
                    "Data app tidak punya JENIS yang dibutuhkan "
                    "(SO / SALDO AKHIR / IN / OUT). Jalankan ulang pipeline."}

        # v3.9.7 (permintaan user "misal H aku input 7 maka hanya
        # tampilkan week 1 aja" — STATUS BULAN dipakai utk filter):
        # hanya baris minggu yang MEMUAT H yang diproses/ditampilkan.
        wt = st.get("week_target")
        if wt is not None:
            weeks_in_file = sorted(fdf["Minggu"].unique().tolist())
            fdf = fdf[fdf["_h"] == wt]
            if fdf.empty:
                self._result_df = None
                return {"gen": gen, "new_file": new_file, "items": [],
                        "status": (
                            f"0 baris — file tidak punya minggu cut-off "
                            f"H {wt} (minggu di file: "
                            f"{', '.join(weeks_in_file)}). Input H di "
                            f"tab 📦 Deviasi GR (H sekarang "
                            f"{st.get('h_label', wt)} → minggu cut-off "
                            f"{wt}) atau centang 'Tampilkan semua "
                            f"minggu'.")}

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
                                      st, avail_max, gen, new_file)

    def _prepare_rows_vec(self, fdf, per_h, pair_index, resto_set,
                          st, avail_max, gen=0, new_file=None) -> dict:
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
            # v3.9.5 (audit 19-c #9): istilah "| Status == H TIDAK ADA"
            # dihapus — status itu hanya diberi SETELAH pasangan ditemukan
            # (resto sudah pasti in_app), jadi tidak pernah menambah baris.
            keep = in_app_resto
            df = df[keep].reset_index(drop=True)
            n_hidden = int((~keep).sum())
        else:
            n_hidden = 0

        # snapshot utk filter header (SEBELUM filter header)
        self._result_df = df.copy()

        # filter header ⧩ — kecocokan nilai TERFORMAT
        filtered = df
        for col, sel in st["col_sel"].items():
            if col in filtered.columns and sel:
                fmt = self._format_col_series(col, filtered[col])
                filtered = filtered[fmt.isin(sel)]
        if filtered.empty:
            return {"gen": gen, "new_file": new_file,
                    "items": [], "status":
                    "Tidak ada baris setelah filter."}

        # v3.9.5 (audit 19-a #7): hitungan status diambil SETELAH filter
        # header — footer "174 baris · MATCH: 7" padahal MATCH=0 di baris
        # yang tampil itu menyesatkan.
        m = len(filtered)
        n_match = int((filtered["Status"] == "MATCH").sum())
        n_sel = int((filtered["Status"] == "SELISIH").sum())
        n_noapp = int((filtered["Status"] == "TIDAK ADA DI DATA APP").sum())
        n_noh = int((filtered["Status"] == "H TIDAK ADA DI DATA").sum())

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
                # v3.9.5 (audit 19-b #5): AKTIF/NON utk kolom Follow Up
                "aktif": self._aktif_lookup.get(barang, ""),
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
        # v3.9.7: prefiks minggu aktif (filter minggu sesuai H)
        if st.get("week_target") is not None:
            wlabels = sorted({str(v) for v in filtered["Minggu"]})
            if wlabels:
                status = (f"Minggu {', '.join(wlabels)} (cut-off H "
                          f"{st['week_target']}) · {status}")
        if n_hidden:
            # FIX C-06 (audit 2-c): "(centang utk lihat)" = instruksi
            # cara-pakai → cukup data (opsi ada di kartu Filter).
            status += f" · {n_hidden} resto file disembunyikan"
        if avail_max:
            status += f" · tanggal app s/d {avail_max}"
        return {"gen": gen, "new_file": new_file, "items": items,
                "status": status, "fp_map": fp_map,
                "row_snaps": row_snaps, "pair_index": pair_index,
                "neg_cells": neg_cells,
                "st_match_cells": st_match_cells,
                "st_diff_cells": st_diff_cells,
                "st_missing_cells": st_missing_cells}

    def _render_rows(self, payload: dict):
        try:
            self._render_rows_inner(payload)
        except tk.TclError:
            # v3.9.5: view di-destroy di tengah render (popup/job async
            # menembak setelah widget mati) — pastikan state bersusih.
            self._busy = False
            self._pending = False

    def _render_rows_inner(self, payload: dict):
        if self._insert_cancel is not None:
            # batch insert lama masih berjalan (race) → stop dulu
            self._insert_cancel()
            self._insert_cancel = None
        self.tree.delete(*self.tree.get_children())
        self._update_headings()
        self._fp_map = payload.get("fp_map", {})
        self._row_snaps = payload.get("row_snaps", {})
        # v3.9.5 (audit 19-a #2): simpan pair index utk popup detail
        self._pair_index = payload.get("pair_index", {})
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
                p = self._pending_path
                self._pending_path = None
                self._pending_sort = None
                if p:
                    self._load_file(p)   # file yang antre saat busy
                else:
                    self._refresh()
            elif self._pending_sort:
                # v3.9.5 (audit 19-b #6): sort yang diklik saat render
                # batch berjalan kini diantrekan (dulu dibuang diam-diam)
                col, rev = self._pending_sort
                self._pending_sort = None
                self._sort_by(col, reverse=rev)

        self._insert_cancel = insert_tree_items(
            self.tree, payload["items"], batch=500, on_done=render_done)

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
                                                               tree=t),
                # v3.9.5 FIX (audit 19-a #3): filter di clone ⛶ rebuild
                # baris (delete+insert) → tag per-cell harus dipasang
                # ulang setelahnya — dulu minus-merah & warna Status
                # hilang setelah memfilter di window besar.
                on_after_filter=lambda t=new_tree: self._reapply_cell_tags(t))

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
            # v3.9.5 (audit 19-b #6): antre sort saat render batch masih
            # berjalan (dulu dibuang diam-diam tanpa umpan balik)
            self._pending_sort = (col, reverse)
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

        # v3.9.5 FIX (audit 19-a #2 / 19-c #8): pakai nama barang & resto
        # versi APP — popup memfilter Nama Barang secara EXACT; nama file
        # (kapital/spasi beda) cocok di tabel via normalisasi tapi popup
        # kosong bila nama RAW dipakai.
        resto_raw = row_data.get("Resto")
        pair = self._pair_index.get(
            (_norm_name(nama_barang), _norm_resto(resto_raw)))
        nb_app, nr_app = (pair if pair is not None
                          else (nama_barang, _norm_resto(resto_raw)))

        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()
        active_filters = {}
        if nr_app:
            active_filters["NAMA RESTO"] = nr_app
        show_details_popup(
            root, self.data,
            nama_barang=nb_app,
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
        """Ratio (0.2697) → '26,97%'; NaN → '—'.

        v3.9.5 (audit 19-a #8): -0.0 → '0,00%' (dulu '-0,00%' — tanda
        nol negatif bocor karena '-0.0 < 0' adalah False di Python)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        if val == 0:
            return "0,00%"
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
