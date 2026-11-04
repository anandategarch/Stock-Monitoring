"""analisa_kronis_view.py — v3.11.47 — Anak tab "Analisa Kronis" di tab 🧮
Nominal Deviasi.

User: "tambahin analisa juga di saldo minus dengan nama barang yang sering
minus dan hanya barang itu aja yang minus di resto itu".

Interpretasi C (dipilih user via balasan ide): pasangan (Resto, Barang)
kronis minus (``Frek Minus`` >= ``threshold``) + flag eksklusif (barang
TIDAK minus di resto lain → investigasi fokus ke pasangan ini, bukan
masalah barang global).

Hitungan via ``hitung_saldo_minus_kronis`` (nominal_common) — re-use
``hitung_saldo_minus_pairs`` (sudah ber-Frek Minus, sudah ter-filter
Source Kiriman Eksternal/Campuran — konsisten dgn tab Saldo Sistem Minus).

Fitur (mirror saldo_minus_view):
- KPI card: total pasangan kronis · total eksklusif · resto kronis terbanyak
- Filter ⧩ + sort (klik header)
- Double-click baris → drill-down details_popup (pola saldo_minus_view)
- Highlight eksklusif (✅) vs global (✗)
- Export Excel (💾)
- Tooltip hover kolom Rekomendasi (narasi panjang) + kolom panjang lain
- Threshold control (Spinbox 1..H — frek minus minimum utk "kronis")
- Subscribe h_state + saldo_sistem_state (konsisten dgn SaldoMinusView)
- Zebra PER-GROUP Nama Barang (konsisten v3.11.47 saldo_minus_view)
"""
from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from .cell_tooltip import CellTooltip
from .nominal_common import (
    hitung_saldo_minus_kronis,
)
from .theme import (
    C_ACCENT,
    C_BG,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    ROW_EVEN,
    ROW_ODD,
    font,
    register_find_tags,
)
from .widgets import (
    CELL_TAGS_SUPPORTED,
    Card,
    EmptyState,
    GhostButton,
    HeaderFilterGroup,
    apply_cell_tag,
    auto_fit_columns,
    enable_col_resize,
    enable_multi_select,
    fmt_int_id,
    insert_tree_items,
    reset_autofit_once,
    run_async,
    sort_tree_by_column,
    zero_row_filter_message,
)

# v3.11.40 — RESTO KHUSUS (mirror saldo_minus_view.RESTO_KHUSUS — user:
# "kasih warna khusus untuk beberapa Nama resto yang aku mapping ...
# MLGPAR dan BDGSEK"). Frozenset — mudah diperluas.
RESTO_KHUSUS = frozenset({"MLGPAR", "BDGSEK"})


# Kolom tampilan anak tab "Analisa Kronis" (10 — user spec interpretasi C).
# Anchor: w=kiri (teks), e=kanan (angka), center= emojis.
KRONIS_COLUMNS = [
    ("Resto", 110, "w"),
    ("Nama Barang", 180, "w"),
    ("Satuan", 50, "w"),
    ("Frek Minus", 80, "e"),     # jumlah tgl minus (kronis = ≥ threshold)
    ("Total Durasi", 70, "e"),   # rentang sejak mulai minus
    ("Tipe", 90, "w"),
    ("Min Qty", 70, "e"),
    ("Max Qty", 70, "e"),
    ("Eksklusif", 70, "center"),  # ✅ / ✗
    ("Resto Lain", 70, "e"),     # 0 bila eksklusif
    ("Rekomendasi", 380, "w"),   # narasi panjang → tooltip
]

KRONIS_NUMERIC_COLS = (
    "Frek Minus", "Total Durasi", "Min Qty", "Max Qty", "Resto Lain",
)

# Default threshold frek minus utk "kronis". User: "threshold default 3
# tanggal? 5? configurable?" → jawab ide "default 3 tanggal".
_DEFAULT_THRESHOLD = 3


def _fmt_num(v) -> str:
    """Format angka gaya Indonesia (mirror saldo_minus_view._fmt_num)."""
    if v is None:
        return "-"
    try:
        if pd.isna(v):
            return "-"
    except (TypeError, ValueError):
        pass
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if f == 0:
        return "-"
    if f == int(f):
        return fmt_int_id(int(f))
    s = (f"{f:,.1f}".replace(",", "\u00a0")
         .replace(".", ",").replace("\u00a0", "."))
    return f"({s[1:]})" if f < 0 else s


class AnalisaKronisView(tk.Frame):
    """Anak tab "Analisa Kronis" — pasangan kronis minus + eksklusif.

    Mirror SaldoMinusView struktur (cache per data_id+h+mode+threshold,
    lazy refresh, subscribe h_state + saldo_sistem_state, filter ⧩, sort,
    export Excel, double-click drill-down).
    """

    def __init__(self, parent,
                 h_state=None,
                 saldo_sistem_state=None,
                 go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: pd.DataFrame | None = None
        self._h_state = h_state
        self.tanggal_h = (int(h_state.h) if h_state is not None else 25)
        # mode saldo sistem (pivot/4217) dibagi dgn tab 📦/🧩 + Saldo Minus.
        self._saldo_sistem_state = saldo_sistem_state
        self.saldo_sistem_mode = (saldo_sistem_state.mode
                                  if saldo_sistem_state is not None
                                  else "4217")
        self.saldo_sistem_map: dict = {}
        self.rincian_po_df: pd.DataFrame | None = None
        self.go_to_proses = go_to_proses
        self._busy = False
        self._pending = False
        self._dirty = False
        # threshold "kronis" — frek minus minimum (default 3).
        self.threshold = _DEFAULT_THRESHOLD
        # cache hasil compute
        self._kronis_df: pd.DataFrame | None = None
        self._cache_key: tuple | None = None  # (data_id, h, mode, threshold)
        self._kronis_stats: dict | None = None
        # render state
        self._neg_cells: list = []
        self._resto_khusus_cells: list = []
        self._eksklusif_cells: list = []
        self._global_cells: list = []
        self._col_sel: dict = {c[0]: None for c in KRONIS_COLUMNS}
        self._cell_tags = CELL_TAGS_SUPPORTED

        self._build_ui()
        self._setup_tags()
        if self._h_state is not None:
            self._h_state.subscribe(self._on_shared_h_changed)
        if self._saldo_sistem_state is not None:
            self._saldo_sistem_state.subscribe(
                self._on_shared_saldo_sistem_changed)
        if (self._h_state is not None
                or self._saldo_sistem_state is not None):
            self.bind("<Destroy>", self._on_view_destroy, add="+")

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        self.empty = EmptyState(
            self, title="Belum ada data — Analisa Kronis",
            cta_text="Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses
                            else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card ---
        fcard = Card(self.content, title="Filter")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        fbody = fcard.body()
        r = tk.Frame(fbody, bg=C_CARD)
        r.pack(fill="x")
        self._h_var = tk.StringVar(value=str(self.tanggal_h))
        tk.Label(r, text="TANGGAL H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        _h_chip = tk.Frame(r, bg="#f1f5f9",
                           highlightbackground="#e2e8f0",
                           highlightthickness=1)
        _h_chip.pack(side="left", padx=(6, 14))
        tk.Label(_h_chip, textvariable=self._h_var, bg="#f1f5f9",
                fg=C_ACCENT, font=font(11, "bold")).pack(
            padx=10, pady=(2, 3))
        # mode saldo sistem (read-only chip)
        tk.Label(r, text="SALDO SISTEM", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._mode_var = tk.StringVar(
            value=("42.17" if self.saldo_sistem_mode == "4217"
                   else "Pivot"))
        _mode_chip = tk.Frame(r, bg="#f1f5f9",
                              highlightbackground="#e2e8f0",
                              highlightthickness=1)
        _mode_chip.pack(side="left", padx=(6, 14))
        tk.Label(_mode_chip, textvariable=self._mode_var, bg="#f1f5f9",
                fg=C_ACCENT, font=font(9, "bold")).pack(
            padx=8, pady=(2, 3))
        # threshold "kronis" — Spinbox (1..H)
        tk.Label(r, text="FREK MINUS MIN", bg=C_CARD, fg=C_TEXT_MUTED,
                font=font(8, "bold")).pack(side="left")
        self._thr_var = tk.IntVar(value=self.threshold)
        _thr = tk.Spinbox(
            r, from_=1, to=31, width=4, textvariable=self._thr_var,
            font=font(9, "bold"), justify="center",
            command=self._on_threshold_changed)
        _thr.pack(side="left", padx=(6, 14))
        # Enter key pada spinbox juga trigger
        _thr.bind("<Return>", lambda e: self._on_threshold_changed())
        _thr.bind("<FocusOut>", lambda e: self._on_threshold_changed())
        GhostButton(r, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left")
        tk.Label(r, text="Pasangan kronis (Frek Minus ≥ threshold) · "
                         "eksklusif = barang hanya minus di 1 resto · "
                         "mode saldo sistem ikut tab 📦",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(
            side="right")

        # --- KPI card ---
        kcard = Card(self.content)
        kcard.pack(fill="x", padx=12, pady=(10, 0))
        kbody = kcard.body()
        self._kpi_var = tk.StringVar(
            value="Pasangan kronis: - · Eksklusif: - · "
                  "Resto kronis terbanyak: -")
        tk.Label(kbody, textvariable=self._kpi_var, bg=C_CARD,
                 fg=C_HEADER, font=font(9, "bold")).pack(anchor="w")

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()
        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        tk.Label(head, text="Analisa Kronis — pasangan kronis minus + "
                            "flag eksklusif (barang hanya minus di 1 resto)",
                bg=C_CARD, fg=C_HEADER, font=font(10, "bold")).pack(
            side="left")
        GhostButton(head, text="💾 Export Excel",
                    command=self._export_excel).pack(side="right")
        GhostButton(head, text="↔ Auto-Fit",
                    command=lambda: auto_fit_columns(self.tree)).pack(
            side="right", padx=(0, 6))

        col_ids = [c[0] for c in KRONIS_COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="extended")
        for col_name, width, anchor in KRONIS_COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name, anchor=anchor)

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
        self.tree.bind("<Double-1>", self._on_double_click, add="+")
        # v3.11.47 — Fitur 2: tooltip hover kolom Rekomendasi (narasi
        # panjang) + kolom panjang lain.
        _LONG_COLS = ("Rekomendasi", "Nama Barang", "Resto")

        def _tip_provider(iid: str, col: str) -> str | None:
            if col not in _LONG_COLS:
                return None
            try:
                txt = self.tree.set(iid, col)
            except tk.TclError:
                return None
            if not txt or txt == "-":
                return None
            if len(txt) < 30:
                return None
            return txt

        self._cell_tip = CellTooltip(
            self.tree, provider=_tip_provider,
            delay_ms=500, max_width=540)

        # Footer status
        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold")).pack(side="right")

        # filter header ⧩ + sort
        self._filters = HeaderFilterGroup(
            self.tree, col_ids,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

    def _setup_tags(self):
        tree = self.tree
        register_find_tags(tree)
        tree.tag_configure("evenrow", background=ROW_EVEN)
        tree.tag_configure("oddrow", background=ROW_ODD)
        # minus merah per-cell (kolom Min Qty / Max Qty)
        tree.tag_configure("neg_cell", foreground="#dc2626")
        # RESTO KHUSUS MLGPAR/BDGSEK (mirror saldo_minus_view)
        tree.tag_configure("resto_khusus_cell", background="#fef3c7",
                           foreground="#92400e")
        # eksklusif = hijau (fokus investigasi resto-spesifik)
        tree.tag_configure("eksklusif_row", foreground="#047857")
        # global = ungu (barang global — bukan fokus resto-spesifik)
        tree.tag_configure("global_row", foreground="#6d28d9")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame,
                  saldo_sistem_map: dict | None = None,
                  rincian_po_df: pd.DataFrame | None = None):
        self.data = data
        self.saldo_sistem_map = saldo_sistem_map or {}
        self.rincian_po_df = rincian_po_df
        reset_autofit_once(self)
        # invalidate cache
        self._kronis_df = None
        self._cache_key = None
        self._kronis_stats = None
        if data is None or getattr(data, "empty", True):
            self._show_empty()
            self.status_var.set("Belum ada data — jalankan Pipeline.")
            self._kpi_var.set(
                "Pasangan kronis: - · Eksklusif: - · "
                "Resto kronis terbanyak: -")
            return
        self._show_content()
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def ensure_refreshed(self):
        if self._dirty and self.data is not None:
            self._dirty = False
            self._refresh()

    def _show_empty(self):
        with contextlib.suppress(tk.TclError):
            self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        with contextlib.suppress(tk.TclError):
            self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    # =========================================================================
    # REFRESH (async + render batched)
    # =========================================================================
    def _refresh(self, sync: bool = False):
        if self.data is None or getattr(self.data, "empty", True):
            self.status_var.set("Belum ada data.")
            return
        if self._busy:
            self._pending = True
            return
        st = {"tanggal_h": self.tanggal_h,
              "saldo_sistem_mode": self.saldo_sistem_mode,
              "col_sel": self._col_sel,
              "threshold": self.threshold}
        self._busy = True

        def work():
            return self._compute(st)

        def done(payload):
            self._render(payload)

        def on_error(err):
            self._busy = False
            self._pending = False
            self.status_var.set(f"⚠ Gagal menghitung: {err}")

        run_async(self, work, done, overlay=None,
                  loading_text="Menghitung analisa kronis…",
                  on_error=on_error, sync=sync)

    def _compute(self, st: dict) -> dict:
        data = self.data
        if data is None or getattr(data, "empty", True):
            return self._empty_payload("Belum ada data.")
        h = st["tanggal_h"]
        mode_4217 = (st["saldo_sistem_mode"] == "4217")
        threshold = int(st["threshold"])
        # cache check (identitas data + h + mode + threshold)
        data_id = id(data)
        cache_key = (data_id, h, st["saldo_sistem_mode"], threshold)
        if (self._kronis_df is not None
                and self._cache_key == cache_key):
            kronis_df = self._kronis_df
            stats = getattr(self, "_kronis_stats", None) or {}
        else:
            stats = {}
            kronis_df = hitung_saldo_minus_kronis(
                data, h, self.saldo_sistem_map, mode_4217=mode_4217,
                threshold=threshold, stats_out=stats)
            _mode_lbl = "42.17" if mode_4217 else "pivot"
            print(f"[ANALISA KRONIS] mode={_mode_lbl} · H={h} · "
                  f"thr={threshold} · "
                  f"{stats.get('total_minus_pairs', 0):,} pasangan minus "
                  f"total · {stats.get('kronis_pairs', 0):,} kronis · "
                  f"{stats.get('eksklusif_pairs', 0):,} eksklusif · "
                  f"{stats.get('shown', 0):,} tampil")
            self._kronis_df = kronis_df
            self._cache_key = cache_key
            self._kronis_stats = stats

        if kronis_df is None or kronis_df.empty:
            # pesan KOSONG jujur (pola v3.9.46 / v3.11.45 saldo_minus_view)
            _tmp = int(stats.get("total_minus_pairs", 0) or 0)
            _mode_lbl = "42.17" if mode_4217 else "pivot"
            if _tmp == 0:
                _why = (f"0 pasangan minus (2.SALDO AKHIR) di 1..{h} — "
                        "data kosong atau pipeline belum dijalankan "
                        f"(mode {_mode_lbl})")
            else:
                _why = (f"{_tmp:,} pasangan minus dipindai 1..{h} tapi "
                        f"TIDAK ADA yg Frek Minus ≥ {threshold} (mode "
                        f"{_mode_lbl}) — coba turunkan threshold")
            return self._empty_payload(
                f"Tidak ada pasangan kronis — {_why}.")

        # filter ⧩ (kecocokan nilai TERFORMAT — pola saldo_minus_view)
        filtered = kronis_df
        for col, sel in st["col_sel"].items():
            if col in filtered.columns and sel:
                fmt = self._format_col_series(col, filtered[col])
                filtered = filtered[fmt.isin(sel)]
        if filtered.empty:
            _hint = zero_row_filter_message(st["col_sel"])
            return self._empty_payload(
                _hint or "Tidak ada baris setelah filter.")

        filtered = filtered.reset_index(drop=True)
        n = len(filtered)
        col_ids = [c[0] for c in KRONIS_COLUMNS]
        items = []
        neg_cells = []
        resto_khusus_cells = []
        eksklusif_cells = []
        global_cells = []
        # zebra PER-GROUP Nama Barang (konsisten v3.11.47 saldo_minus_view)
        prev_barang_grp = None
        group_parity = 0
        for i in range(n):
            row = filtered.iloc[i]
            values = []
            for col_id in col_ids:
                if col_id == "Resto":
                    values.append(str(row.get("NAMA RESTO", "")))
                elif col_id == "Nama Barang":
                    values.append(str(row.get("Nama Barang", "")))
                elif col_id == "Satuan":
                    sat = str(row.get("Satuan", "") or "")
                    values.append(sat if sat and sat != "-" else "-")
                elif col_id == "Tipe":
                    values.append(str(row.get("Tipe", "")))
                elif col_id == "Eksklusif":
                    values.append(str(row.get("Eksklusif", "")))
                elif col_id == "Rekomendasi":
                    values.append(str(row.get("Rekomendasi", "")))
                elif col_id in KRONIS_NUMERIC_COLS:
                    df_col = self._col_to_df(col_id)
                    v = row.get(df_col, 0) if df_col else 0
                    values.append(_fmt_num(v))
                    try:
                        fv = float(v)
                        if fv < 0:
                            neg_cells.append((f"row_{i}", col_id))
                    except (TypeError, ValueError):
                        pass
                else:
                    values.append(str(row.get(col_id, "") or ""))
            # zebra per-group Nama Barang
            barang_i = str(row.get("Nama Barang", ""))
            if prev_barang_grp is None:
                pass
            elif barang_i != prev_barang_grp:
                group_parity ^= 1
            prev_barang_grp = barang_i
            tags = ["evenrow" if group_parity == 0 else "oddrow"]
            resto = str(row.get("NAMA RESTO", "")).strip().upper()
            if resto in RESTO_KHUSUS:
                resto_khusus_cells.append((f"row_{i}", "Resto"))
            eks = str(row.get("Eksklusif", ""))
            if eks == "✅":
                eksklusif_cells.append(f"row_{i}")
                tags.append("eksklusif_row")
            elif eks == "✗":
                global_cells.append(f"row_{i}")
                tags.append("global_row")
            items.append(("", f"row_{i}",
                         {"values": values, "tags": tuple(tags)}))

        # KPI
        n_eks = int((filtered["Eksklusif"] == "✅").sum())
        resto_counts = (filtered["NAMA RESTO"].astype(str)
                        .value_counts())
        if not resto_counts.empty:
            top_resto = str(resto_counts.index[0])
            top_n = int(resto_counts.iloc[0])
            resto_kpi = f"{top_resto} ({top_n})"
        else:
            resto_kpi = "-"
        kpi = (f"Pasangan kronis: {fmt_int_id(n)} · "
               f"Eksklusif: {fmt_int_id(n_eks)} · "
               f"Resto kronis terbanyak: {resto_kpi}")
        mode_label = "42.17 (folder)" if mode_4217 else "Pivot (running-stock)"
        status = (f"{n} pasangan kronis · Frek ≥ {threshold} · H={h} · "
                   f"mode: {mode_label} · {n_eks} eksklusif · "
                   f"{n - n_eks} barang global")
        return {"items": items, "status": status, "kpi": kpi,
                "neg_cells": neg_cells,
                "resto_khusus_cells": resto_khusus_cells,
                "eksklusif_cells": eksklusif_cells,
                "global_cells": global_cells}

    @staticmethod
    def _empty_payload(status: str) -> dict:
        return {"items": [], "status": status,
                "kpi": "Pasangan kronis: 0 · Eksklusif: - · "
                       "Resto kronis terbanyak: -",
                "neg_cells": [], "resto_khusus_cells": [],
                "eksklusif_cells": [], "global_cells": []}

    @staticmethod
    def _col_to_df(col_id: str) -> str:
        """Map nama kolom tampilan → nama kolom DataFrame kronis."""
        m = {"Frek Minus": "Frek Minus",
             "Total Durasi": "Total Durasi",
             "Min Qty": "Min Qty",
             "Max Qty": "Max Qty",
             "Resto Lain": "Resto Lain"}
        return m.get(col_id, "")

    def _format_col_series(self, col: str, series: pd.Series) -> pd.Series:
        """Format nilai kolom utk filter ⧩ (identik dgn tampilan)."""
        if col == "Rekomendasi":
            return series.astype(str)
        if col in KRONIS_NUMERIC_COLS:
            return series.map(_fmt_num)
        return series.astype(str)

    def _col_values(self, col: str) -> list:
        """Nilai unik TERFORMAT utk popup ⧩ (sorted)."""
        if self._kronis_df is None or self._kronis_df.empty:
            return []
        if col == "Rekomendasi":
            # narasi panjang — tidak difilter (built per-row) → no popup
            return []
        if col in KRONIS_NUMERIC_COLS:
            df_col = self._col_to_df(col)
            if df_col and df_col in self._kronis_df.columns:
                return sorted({_fmt_num(v) for v in
                               self._kronis_df[df_col]})
            return []
        if col in self._kronis_df.columns:
            return sorted({str(v) for v in self._kronis_df[col]
                           if str(v).strip()})
        return []

    def _render(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self._neg_cells = payload.get("neg_cells", [])
        self._resto_khusus_cells = payload.get("resto_khusus_cells", [])
        self._eksklusif_cells = payload.get("eksklusif_cells", [])
        self._global_cells = payload.get("global_cells", [])
        self.status_var.set(payload["status"])
        self._kpi_var.set(payload["kpi"])
        self._filters.refresh_icons()

        def render_done():
            if self._cell_tags:
                apply_cell_tag(self.tree, "neg_cell", self._neg_cells)
                apply_cell_tag(self.tree, "resto_khusus_cell",
                               self._resto_khusus_cells)
            self._busy = False
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=400,
                          on_done=render_done)

    # =========================================================================
    # FILTER ⧩ + SORT + THRESHOLD
    # =========================================================================
    def _on_col_filter(self, col_sel: dict):
        self._col_sel = dict(col_sel)
        self._refresh()

    def _sort_by(self, col: str, reverse: bool = True):
        sort_tree_by_column(self.tree, col, reverse=reverse)

    def _reset_filter(self):
        self._col_sel = {c[0]: None for c in KRONIS_COLUMNS}
        self._filters.clear()
        # reset threshold juga
        self.threshold = _DEFAULT_THRESHOLD
        self._thr_var.set(self.threshold)
        self._kronis_df = None  # invalidate cache (threshold berubah)
        self._refresh()

    def _on_threshold_changed(self):
        try:
            v = int(self._thr_var.get())
        except (tk.TclError, ValueError):
            self._thr_var.set(self.threshold)
            return
        v = max(1, min(31, v))  # clamp 1..31 (max H realistis)
        if v == self.threshold:
            return
        self.threshold = v
        self._thr_var.set(v)
        self._kronis_df = None  # invalidate cache (threshold berubah)
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    # =========================================================================
    # DOUBLE-CLICK → DRILL-DOWN (mirror saldo_minus_view)
    # =========================================================================
    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return
        tree = event.widget
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return
        try:
            vals = tree.item(row_iid, "values")
        except tk.TclError:
            return
        if not vals:
            return
        # nama barang = kolom index 1 (Resto=0, Nama Barang=1)
        col_ids = [c[0] for c in KRONIS_COLUMNS]
        try:
            nb_idx = col_ids.index("Nama Barang")
        except ValueError:
            return
        nama_barang = str(vals[nb_idx]) if len(vals) > nb_idx else None
        if not nama_barang:
            return
        # drill-down details_popup (jenis 2.SALDO AKHIR, tanggal H — biar
        # user lihat kronologi saldo akhir pasangan ini)
        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()
        with contextlib.suppress(Exception):
            show_details_popup(
                root, self.data,
                nama_barang=nama_barang,
                jenis="2.SALDO AKHIR",
                tanggal=self.tanggal_h,
                show_maximize=False,
                in_detail=None,
                rincian_po_df=self.rincian_po_df)

    # =========================================================================
    # EXPORT EXCEL
    # =========================================================================
    def _export_excel(self):
        if self._kronis_df is None or self._kronis_df.empty:
            messagebox.showinfo("Export Excel",
                                "Tidak ada data untuk diexport.",
                                parent=self.winfo_toplevel())
            return
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Export Analisa Kronis",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")])
        if not path:
            return
        try:
            df = self._kronis_df.copy()
            # rename kolom df → tampilan (mirror saldo_minus_view)
            df = df.rename(columns={
                "NAMA RESTO": "Resto",
            })
            col_order = [c[0] for c in KRONIS_COLUMNS
                         if c[0] in df.columns]
            df = df[col_order]
            df.to_excel(path, index=False, sheet_name="Analisa Kronis")
            self.status_var.set(f"💾 Export: {path}")
        except Exception as exc:  # noqa: BLE001 — export I/O
            messagebox.showerror("Export Gagal", str(exc),
                                 parent=self.winfo_toplevel())

    # =========================================================================
    # STATE LISTENER (h_state + saldo_sistem_state)
    # =========================================================================
    def _on_shared_h_changed(self, new_h):
        self.tanggal_h = int(new_h)
        if hasattr(self, "_h_var"):
            self._h_var.set(str(self.tanggal_h))
        # clamp threshold ke H (jangan > H)
        if self.threshold > self.tanggal_h:
            self.threshold = self.tanggal_h
            if hasattr(self, "_thr_var"):
                self._thr_var.set(self.threshold)
        self._kronis_df = None
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def _on_shared_saldo_sistem_changed(self, new_mode):
        self.saldo_sistem_mode = str(new_mode)
        if hasattr(self, "_mode_var"):
            self._mode_var.set(
                "42.17" if self.saldo_sistem_mode == "4217" else "Pivot")
        self._kronis_df = None
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def _on_view_destroy(self, event):
        if event.widget is not self:
            return
        if self._h_state is not None:
            self._h_state.unsubscribe(self._on_shared_h_changed)
        if self._saldo_sistem_state is not None:
            self._saldo_sistem_state.unsubscribe(
                self._on_shared_saldo_sistem_changed)
