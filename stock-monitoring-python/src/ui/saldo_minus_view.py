"""
saldo_minus_view.py — v3.11.42 — Anak tab "Saldo Sistem Minus" di tab 🧮
Nominal Deviasi.

User: "tambah fitur baru lagi di tab nominal deviasi tambah 1 baru yaitu
Saldo Sistem Minus Dengan ambil data dari Pivot dan ditampilkan dalam
format: Nama Resto · Nama Barang (Khusus yang sumber nya dari Eksternal
aja) · Kuantiti · Keterangan. Jadi itu isinya rekapan saldo akhir atau
saldo sistem yang minus dan keterangan nya isi dengan mulai minus dari
tanggal berapa."

Opsi 2 (user pilih): SEMUA pasangan yg pernah minus di rentang 1..H (bukan
hanya snapshot H). Scan 2.SALDO AKHIR per (pasangan, tgl 1..H).

Mode saldo sistem (user pilih): 2 mode — pivot (running-stock) / 4217
(folder '6. 42.17' override tgl H). Konsisten dgn tab 📦/🧩 Deviasi GR/PCS
(SharedSaldoSistemMode).

Kolom (12 — user spec + ide tambahan A-K semua):
- Resto · Nama Barang · Satuan
- Qty Mulai Minus (user: "mulai minus aja" utk Kuantiti)
- Mulai Minus (tgl pertama saldo < 0)
- Durasi (H − mulai + 1) — ide A
- Min Qty · Max Qty (range 1..H) — ide B
- Tipe (Konsisten/Fluktuatif) — ide C
- Nomor PO (3243) — ide D
- Status PO (3243) — ide J
- Keterangan (narasi gabungan) — user spec + ide

Fitur pelengkap (ide E-K):
- KPI card: total pasangan minus · total qty minus · resto minus terbanyak
  (ide E)
- Filter ⧩ + sort (klik header) — ide F
- Double-click baris → drill-down details_popup (ide G)
- Highlight baris Konsisten (urgent) vs Fluktuatif — ide H
- Export Excel (💾) — ide I
- Tandai resto khusus MLGPAR/BDGSEK (warna cell) — ide K (konsisten
  v3.11.40 tab 📦/🧩)
"""
import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from .cell_tooltip import CellTooltip
from .nominal_common import (
    hitung_saldo_minus_pairs,
)
from .po_keterangan import po_nomor_map_3243, po_status_map_3243
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
    filter_disp_mask,  # v3.12.1 — FIX: seleksi ⧩ label-vs-mentah
    fmt_int_id,
    insert_tree_items,
    reset_autofit_once,
    run_async,
    sort_tree_by_column,
    zero_row_filter_message,
)

# v3.11.40 — RESTO KHUSUS (mirror deviasi_view.RESTO_KHUSUS — user: "kasih
# warna khusus untuk beberapa Nama resto yang aku mapping ... MLGPAR dan
# BDGSEK"). Frozenset — mudah diperluas.
RESTO_KHUSUS = frozenset({"MLGPAR", "BDGSEK"})


# Kolom tampilan anak tab "Saldo Sistem Minus" (12 — user spec + ide A-K).
# Anchor: w=kiri (teks), e=kanan (angka), center= checkboxes.
MINUS_COLUMNS = [
    ("Resto", 130, "w"),
    ("Nama Barang", 180, "w"),
    ("Satuan", 50, "w"),
    ("Qty Mulai Minus", 100, "e"),
    ("Mulai Minus", 80, "e"),
    ("Durasi", 60, "e"),
    ("Min Qty", 80, "e"),
    ("Max Qty", 80, "e"),
    ("Tipe", 90, "w"),
    ("Nomor PO", 150, "w"),
    ("Status PO", 110, "w"),
    ("Keterangan", 240, "w"),
]

# Kolom numerik (sort numerik; minus merah per-cell).
MINUS_NUMERIC_COLS = (
    "Qty Mulai Minus", "Mulai Minus", "Durasi", "Min Qty", "Max Qty",
)


def _fmt_num(v) -> str:
    """Format angka gaya Indonesia: 1 desimal, separator ribuan '.',
    desimal ','. Negatif dalam kurung. 0 → '-'. NaN/None → '-'."""
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
        s = fmt_int_id(int(f))
    else:
        s = (f"{f:,.1f}".replace(",", "\u00a0")
             .replace(".", ",").replace("\u00a0", "."))
    return f"({s[1:]})" if f < 0 else s


def _build_keterangan(row) -> str:
    """Narasi gabungan Keterangan: 'Mulai minus tgl 3 · durasi 3 hari ·
    Konsisten · PO: PO-001, PO-002 (Menunggu diproses, Diproses)'."""
    parts = [f"Mulai minus tgl {int(row.get('Tgl Mulai Minus', 0))}",
             f"durasi {int(row.get('Durasi', 0))} hari",
             str(row.get("Tipe", ""))]
    nomor = str(row.get("Nomor PO", "") or "").strip()
    status = str(row.get("Status PO", "") or "").strip()
    if nomor:
        po_part = f"PO: {nomor}"
        if status:
            po_part += f" ({status})"
        parts.append(po_part)
    elif status:
        parts.append(f"Status PO: {status}")
    return " · ".join(p for p in parts if p)


class SaldoMinusView(tk.Frame):
    """v3.11.42 — Anak tab "Saldo Sistem Minus" (frame self-contained,
    di-embed ke nominal_resto_view sebagai anak tab Notebook).

    Pasangan dgn SALDO SISTEM minus di 1..H (Opsi 2 — SEMUA pasangan yg
    pernah minus). Hanya SOURCE KIRIMAN Eksternal/Campuran. 12 kolom +
    KPI card + filter ⧩ + sort + drill-down + export + resto khusus.
    """

    def __init__(self, parent,
                 h_state=None,
                 saldo_sistem_state=None,
                 go_to_proses: Callable | None = None,
                 go_to_deviasi: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: pd.DataFrame | None = None
        self._h_state = h_state
        self.tanggal_h = (int(h_state.h) if h_state is not None else 25)
        # v3.11.42 — mode saldo sistem (pivot/4217) dibagi dgn tab 📦/🧩.
        self._saldo_sistem_state = saldo_sistem_state
        self.saldo_sistem_mode = (saldo_sistem_state.mode
                                  if saldo_sistem_state is not None
                                  else "4217")
        self.saldo_sistem_map: dict = {}
        self.rincian_po_df: pd.DataFrame | None = None
        self.go_to_proses = go_to_proses
        # v3.11.56 — U2: deep-link ke tab 📦 Deviasi GR (context menu
        # klik-kanan pasangan — diteruskan nominal_resto_view dari app).
        self.go_to_deviasi = go_to_deviasi
        self._busy = False
        self._pending = False
        self._dirty = False
        # cache hasil compute (frame minus + PO info merged)
        self._minus_df: pd.DataFrame | None = None
        self._minus_data_id = None  # identitas data terakhir compute
        self._minus_h = None
        self._minus_mode = None
        self._minus_stats: dict | None = None  # v3.11.45 — breakdown scan
        # render state
        self._neg_cells: list = []
        self._resto_khusus_cells: list = []
        self._konsisten_cells: list = []  # baris Konsisten (highlight bg)
        self._fluktuatif_cells: list = []  # baris Fluktuatif (fg amber)
        self._col_sel: dict = {c[0]: None for c in MINUS_COLUMNS}
        self._cell_tags = CELL_TAGS_SUPPORTED

        self._build_ui()
        self._setup_tags()
        # subscribe state bersama (pola deviasi_view)
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
        # Empty state
        self.empty = EmptyState(
            self, title="Belum ada data — Saldo Sistem Minus",
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
        # mode saldo sistem (read-only chip — diatur di tab 📦 Deviasi GR)
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
        tk.Label(r, text="· atur mode di 📦 Deviasi GR", bg="#f1f5f9",
                 fg=C_TEXT_MUTED, font=font(8)).pack(
            side="left", padx=(4, 14), pady=(2, 3))
        GhostButton(r, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left")
        tk.Label(r, text="Saldo sistem minus (1..H) · hanya Eksternal/"
                         "Campuran · mode saldo sistem ikut tab 📦",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(
            side="right")

        # --- KPI card (ide E) ---
        kcard = Card(self.content)
        kcard.pack(fill="x", padx=12, pady=(10, 0))
        kbody = kcard.body()
        self._kpi_var = tk.StringVar(
            value="Total pasangan minus: - · Total qty minus: - · "
                  "Resto minus terbanyak: -")
        tk.Label(kbody, textvariable=self._kpi_var, bg=C_CARD,
                 fg=C_HEADER, font=font(9, "bold")).pack(anchor="w")

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()
        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        tk.Label(head, text="Saldo Sistem Minus — pasangan Eksternal/"
                            "Campuran dgn saldo < 0 di 1..H",
                bg=C_CARD, fg=C_HEADER, font=font(10, "bold")).pack(
            side="left")
        GhostButton(head, text="💾 Export Excel",
                    command=self._export_excel).pack(side="right")
        GhostButton(head, text="↔ Auto-Fit",
                    command=lambda: auto_fit_columns(self.tree)).pack(
            side="right", padx=(0, 6))

        col_ids = [c[0] for c in MINUS_COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="extended")
        for col_name, width, anchor in MINUS_COLUMNS:
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
        # v3.11.56 — U2: context menu deep-link (klik-kanan pasangan →
        # filter pasangan itu di tab 📦 Deviasi GR).
        self.tree.bind("<Button-3>", self._on_context_menu, add="+")
        # v3.11.47 — Fitur 2: tooltip hover untuk kolom panjang yang
        # sering terpotong (Keterangan narasi gabungan, Nomor PO,
        # Status PO). Provider mengambil nilai dari tree.set(iid, col)
        # dan tip muncul hanya bila teks cukup panjang (≥ 30 char —
        # cell pendek sudah terbaca penuh di tabel, anti-noise).
        # Kolom lain (Resto, Nama Barang, Tipe, satuan) biasanya pendek
        # → tip tidak muncul (truncate_provider min_len=30).
        _LONG_COLS = ("Keterangan", "Nomor PO", "Status PO", "Resto",
                      "Nama Barang")

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
            self.tree,
            provider=_tip_provider,
            delay_ms=500,
            max_width=460)

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
        # minus merah per-cell (kolom Qty/Min/Max)
        tree.tag_configure("neg_cell", foreground="#dc2626")
        # v3.11.40 — RESTO KHUSUS MLGPAR/BDGSEK (mirror deviasi_view)
        tree.tag_configure("resto_khusus_cell", background="#fef3c7",
                           foreground="#92400e")
        # ide H — highlight Tipe
        tree.tag_configure("konsisten_row", foreground="#991b1b")  # red-800
        tree.tag_configure("fluktuatif_row", foreground="#b45309")  # amber-700

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
        # invalidate cache compute (data berubah)
        self._minus_df = None
        self._minus_data_id = None
        self._minus_stats = None  # v3.11.45 — breakdown ikut di-reset
        if data is None or getattr(data, "empty", True):
            self._show_empty()
            self.status_var.set("Belum ada data — jalankan Pipeline.")
            self._kpi_var.set(
                "Total pasangan minus: - · Total qty minus: - · "
                "Resto minus terbanyak: -")
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
              "col_sel": self._col_sel}
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
                  loading_text="Menghitung saldo sistem minus…",
                  on_error=on_error, sync=sync)

    def _compute(self, st: dict) -> dict:
        """Pure pandas: compute minus pairs + merge PO info + filter + sort.
        Cache per (data_id, h, mode) — recompute hanya bila berubah."""
        data = self.data
        if data is None or getattr(data, "empty", True):
            return {"items": [], "status": "Belum ada data.",
                    "kpi": "", "neg_cells": [],
                    "resto_khusus_cells": [],
                    "konsisten_cells": [], "fluktuatif_cells": []}
        h = st["tanggal_h"]
        mode_4217 = (st["saldo_sistem_mode"] == "4217")
        # cache check (identitas data + h + mode)
        data_id = id(data)
        if (self._minus_df is not None
                and self._minus_data_id == data_id
                and self._minus_h == h
                and self._minus_mode == st["saldo_sistem_mode"]):
            minus_df = self._minus_df
            stats = getattr(self, "_minus_stats", None) or {}
        else:
            # v3.11.45 — stats_out: transparansi KENAPA kosong (user:
            # "tab saldominus juga kosong dengan mode pivot atau mode
            # 42.17") — breakdown scan di status + log 1 baris.
            stats = {}
            minus_df = hitung_saldo_minus_pairs(
                data, h, self.saldo_sistem_map, mode_4217=mode_4217,
                stats_out=stats)
            # log 1 baris (stdout app di-redirect → tab 🚀 Proses)
            _mode_lbl = "42.17" if mode_4217 else "pivot"
            print(f"[SALDO MINUS] mode={_mode_lbl} · H={h} · "
                  f"{stats.get('saldo_rows', 0):,} baris saldo · "
                  f"{stats.get('saldo_pairs', 0):,} pasangan ber-saldo · "
                  f"{stats.get('minus_pairs', 0):,} pernah minus · "
                  f"{stats.get('excluded_src', 0):,} dibuang sumber "
                  f"(Internal) · {stats.get('shown', 0):,} tampil")
            self._minus_stats = stats
            # merge PO info (3243)
            if not minus_df.empty and self.rincian_po_df is not None:
                _nomor_m = po_nomor_map_3243(self.rincian_po_df)
                _status_m = po_status_map_3243(self.rincian_po_df)
                minus_df = minus_df.assign(
                    **{"Nomor PO": minus_df.apply(
                        lambda r: _nomor_m.get(
                            (r["Nama Barang"], r["NAMA RESTO"]), ""),
                        axis=1),
                       "Status PO": minus_df.apply(
                        lambda r: _status_m.get(
                            (r["Nama Barang"], r["NAMA RESTO"]), ""),
                        axis=1)})
            elif not minus_df.empty:
                minus_df = minus_df.assign(
                    **{"Nomor PO": "", "Status PO": ""})
            self._minus_df = minus_df
            self._minus_data_id = data_id
            self._minus_h = h
            self._minus_mode = st["saldo_sistem_mode"]

        if minus_df is None or minus_df.empty:
            # v3.11.45 — pesan KOSONG yang JUJUR (pola v3.9.46): bilang
            # KENAPA kosong dari stats breakdown — bukan generik 'Tidak
            # ada pasangan minus.' (user tak bisa membedakan bug vs data).
            _sp = int(stats.get("saldo_pairs", 0) or 0)
            _mp = int(stats.get("minus_pairs", 0) or 0)
            _ex = int(stats.get("excluded_src", 0) or 0)
            _mode_lbl45 = "42.17" if mode_4217 else "pivot"
            if _sp == 0:
                _why = (f"0 pasangan ber-saldo (2.SALDO AKHIR) di 1..{h} — "
                        "data kosong atau pipeline belum dijalankan")
            elif _mp == 0:
                _why = (f"{_sp:,} pasangan ber-saldo dipindai 1..{h} — "
                        f"TIDAK ADA yang pernah minus (mode {_mode_lbl45})")
            elif _ex and _mp == _ex:
                _why = (f"{_mp:,} pasangan minus ditemukan tapi SEMUA "
                        f"ber-sumber Internal — filter tab ini hanya "
                        "Eksternal/Campuran (permintaan awal fitur)")
            else:
                _why = (f"{_mp:,} pasangan minus · {_ex:,} dibuang sumber "
                        f"· 0 lolos (mode {_mode_lbl45})")
            return {"items": [],
                    "status": f"Tidak ada pasangan minus — {_why}.",
                    "kpi": "Total pasangan minus: 0 · Total qty minus: - · "
                           "Resto minus terbanyak: -",
                    "neg_cells": [], "resto_khusus_cells": [],
                    "konsisten_cells": [], "fluktuatif_cells": []}

        # filter ⧩ (kecocokan nilai TERFORMAT — pola nominal_resto)
        # v3.11.48 — FIX audit #6+#10: filter loop pakai _col_to_df utk
        # resolve display col → df col (sebelumnya "Mulai Minus" display
        # tidak match "Tgl Mulai Minus" df → filter silent skip; "Resto"
        # display tidak match "NAMA RESTO" df → popup empty).
        filtered = minus_df
        for col, sel in st["col_sel"].items():
            df_col = self._col_to_df(col)
            if not df_col:
                # non-numeric display cols (Resto/Keterangan/Nama Barang/
                # Satuan/Tipe/Nomor PO/Status PO) — map manual khusus.
                df_col = ("NAMA RESTO" if col == "Resto"
                          else col if col in filtered.columns else None)
            if not df_col or df_col not in filtered.columns or not sel:
                continue
            fmt = self._format_col_series(col, filtered[df_col])
            # v3.12.1 — FIX filter tidak berfungsi (anak tab Saldo Minus):
            # seleksi popup ber-LABEL tampilan ('␣'/'(Kosong)') — cocokkan
            # nilai mentah ATAU label (pola nominal_resto v3.12.1).
            filtered = filtered[filter_disp_mask(fmt, sel)]
        if filtered.empty:
            _hint = zero_row_filter_message(st["col_sel"])
            return {"items": [],
                    "status": _hint or "Tidak ada baris setelah filter.",
                    "kpi": "Total pasangan minus: 0 (terfilter) · "
                           "Total qty minus: - · Resto minus terbanyak: -",
                    "neg_cells": [], "resto_khusus_cells": [],
                    "konsisten_cells": [], "fluktuatif_cells": []}

        filtered = filtered.reset_index(drop=True)
        n = len(filtered)
        col_ids = [c[0] for c in MINUS_COLUMNS]
        items = []
        neg_cells = []
        resto_khusus_cells = []
        konsisten_cells = []
        fluktuatif_cells = []
        # v3.11.47 — Fitur 1: zebra PER-GROUP Nama Barang (bukan per index).
        # Warna berganti SAAT nilai Nama Barang berubah → efek "blok" per
        # barang; semua baris dgn barang sama → warna sama → mata gampang
        # kelompokin. Sort default hitung_saldo_minus_pairs: Nama Barang
        # ASC → |qty| DESC (baris barang sama berdekatan).
        prev_barang_grp = None
        group_parity = 0   # 0 = evenrow, 1 = oddrow; grup pertama = 0
        for i in range(n):
            row = filtered.iloc[i]
            values = []
            for col_id in col_ids:
                if col_id == "Keterangan":
                    values.append(_build_keterangan(row))
                elif col_id == "Resto":
                    values.append(str(row.get("NAMA RESTO", "")))
                elif col_id == "Nama Barang":
                    values.append(str(row.get("Nama Barang", "")))
                elif col_id == "Satuan":
                    sat = str(row.get("Satuan", "") or "")
                    values.append(sat if sat and sat != "-" else "-")
                elif col_id == "Tipe":
                    values.append(str(row.get("Tipe", "")))
                elif col_id == "Nomor PO":
                    values.append(str(row.get("Nomor PO", "") or "") or "-")
                elif col_id == "Status PO":
                    values.append(str(row.get("Status PO", "") or "") or "-")
                elif col_id in MINUS_NUMERIC_COLS:
                    v = row.get(col_id.replace("Qty Mulai Minus",
                               "Qty Mulai Minus"), 0)
                    # map nama kolom tampilan → nama df
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
                pass  # grup pertama, biarkan parity 0 (evenrow)
            elif barang_i != prev_barang_grp:
                group_parity ^= 1   # toggle 0↔1
            prev_barang_grp = barang_i
            tags = ["evenrow" if group_parity == 0 else "oddrow"]
            resto = str(row.get("NAMA RESTO", "")).strip().upper()
            if resto in RESTO_KHUSUS:
                resto_khusus_cells.append((f"row_{i}", "Resto"))
            tipe = str(row.get("Tipe", ""))
            if tipe == "Konsisten":
                konsisten_cells.append(f"row_{i}")
                tags.append("konsisten_row")
            elif tipe == "Fluktuatif":
                fluktuatif_cells.append(f"row_{i}")
                tags.append("fluktuatif_row")
            items.append(("", f"row_{i}",
                         {"values": values, "tags": tuple(tags)}))

        # KPI
        total_qty = float(filtered["Qty Mulai Minus"].abs().sum())
        resto_counts = (filtered["NAMA RESTO"].astype(str)
                        .value_counts())
        if not resto_counts.empty:
            top_resto = str(resto_counts.index[0])
            top_n = int(resto_counts.iloc[0])
            resto_kpi = f"{top_resto} ({top_n})"
        else:
            resto_kpi = "-"
        kpi = (f"Total pasangan minus: {fmt_int_id(n)} · "
               f"Total |qty mulai minus|: {fmt_int_id(int(total_qty))} · "
               f"Resto minus terbanyak: {resto_kpi}")
        # mode + H di status (v3.11.45 — + jumlah dibuang sumber bila ada:
        # transparansi pasangan Internal minus yang tak tampil by-design)
        mode_label = "42.17 (folder)" if mode_4217 else "Pivot (running-stock)"
        _ex45 = int(stats.get("excluded_src", 0) or 0)
        _ex_txt = (f" · {_ex45:,} lain dibuang (Internal)" if _ex45 else "")
        status = (f"{n} pasangan minus · H={h} · mode: {mode_label} · "
                  f"scan 1..{h} · hanya Eksternal/Campuran{_ex_txt}")
        return {"items": items, "status": status, "kpi": kpi,
                "neg_cells": neg_cells,
                "resto_khusus_cells": resto_khusus_cells,
                "konsisten_cells": konsisten_cells,
                "fluktuatif_cells": fluktuatif_cells}

    @staticmethod
    def _col_to_df(col_id: str) -> str:
        """Map nama kolom tampilan → nama kolom DataFrame hitung_saldo_minus_pairs."""
        m = {"Qty Mulai Minus": "Qty Mulai Minus",
             "Mulai Minus": "Tgl Mulai Minus",
             "Durasi": "Durasi",
             "Min Qty": "Min Qty",
             "Max Qty": "Max Qty",
             # v3.11.48 — FIX audit #10: + Resto mapping (display "Resto" →
             # df "NAMA RESTO") supaya filter ⧩ popup tidak empty.
             "Resto": "NAMA RESTO"}
        return m.get(col_id, "")

    def _format_col_series(self, col: str, series: pd.Series) -> pd.Series:
        """Format nilai kolom utk filter ⧩ (identik dgn tampilan)."""
        if col == "Keterangan":
            # gabungan narasi — tidak ada di df asli (built per-row)
            # utk filter, pakai Tipe + Nomor PO sebagai proxy
            return series.astype(str)
        if col in MINUS_NUMERIC_COLS:
            return series.map(_fmt_num)
        return series.astype(str)

    def _col_values(self, col: str) -> list:
        """Nilai unik TERFORMAT utk popup ⧩ (sorted)."""
        if self._minus_df is None or self._minus_df.empty:
            return []
        if col == "Keterangan":
            # tidak terfilter (built per-row) — return empty (no popup)
            return []
        # v3.11.48 — FIX audit #10: resolve display col → df col via
        # _col_to_df (sebelumnya "Resto" tdk match "NAMA RESTO" → popup
        # empty; "Mulai Minus" tdk match "Tgl Mulai Minus" → popup empty).
        df_col = self._col_to_df(col)
        if not df_col or df_col not in self._minus_df.columns:
            # fallback: col display == df col (e.g. "Nama Barang", "Tipe")
            df_col = col if col in self._minus_df.columns else None
        if not df_col:
            return []
        if col in MINUS_NUMERIC_COLS:
            return sorted({_fmt_num(v) for v in self._minus_df[df_col]})
        return sorted({str(v) for v in self._minus_df[df_col]
                       if str(v).strip()})

    def _render(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self._neg_cells = payload.get("neg_cells", [])
        self._resto_khusus_cells = payload.get("resto_khusus_cells", [])
        self._konsisten_cells = payload.get("konsisten_cells", [])
        self._fluktuatif_cells = payload.get("fluktuatif_cells", [])
        self.status_var.set(payload["status"])
        self._kpi_var.set(payload["kpi"])
        self._filters.refresh_icons()

        def render_done():
            if self._cell_tags:
                apply_cell_tag(self.tree, "neg_cell", self._neg_cells)
                apply_cell_tag(self.tree, "resto_khusus_cell",
                               self._resto_khusus_cells)
            # v3.11.48 — FIX audit #5+#11: re-apply zebra per-group +
            # cell tags SETELAH render (sort manual user dipreserve via
            # tree._last_sort — pola deviasi_view._reapply_render_decorations).
            self._reapply_zebra_per_group()
            # v3.11.48 — FIX audit #5: re-apply user's last manual sort
            # bila ada (sebelumnya sort lost on every _refresh).
            last_sort = getattr(self.tree, "_last_sort", None)
            if last_sort:
                col, rev, parse, vg = last_sort
                sort_tree_by_column(
                    self.tree, col, reverse=rev, parse=parse,
                    value_get=vg, on_done=self._reapply_zebra_per_group)
            self._busy = False
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=400,
                          on_done=render_done)

    def _reapply_zebra_per_group(self) -> None:
        """v3.11.48 — FIX audit #1+#4: re-apply zebra PER-GROUP Nama Barang
        berdasarkan urutan VISUAL tree (post-sort / post-filter clone rebuild).

        Sebelumnya zebra tags dibangun di _compute (default sort order).
        Saat user klik header sort, sort_tree_by_column reorder iid TAPI
        tags follow iid → zebra jadi random. Method ini walk tree.get_
        children("") dalam urutan visible, lookup Nama Barang per iid,
        toggle parity saat barang berubah → re-apply tags.

        Juga re-apply cell tags (neg_cell, resto_khusus_cell) yang hilang
        setelah sort (sort_tree_by_column delete+insert ulang, cell tag
        mapping tidak di-preserve).
        """
        tree = self.tree
        try:
            children = list(tree.get_children(""))
        except tk.TclError:
            return
        prev_barang = None
        parity = 0
        for iid in children:
            try:
                vals = tree.item(iid, "values")
            except tk.TclError:
                continue
            # Nama Barang = kolom index 1 (Resto=0, Nama Barang=1)
            barang = str(vals[1]) if len(vals) > 1 else ""
            if prev_barang is not None and barang != prev_barang:
                parity ^= 1
            prev_barang = barang
            existing = list(tree.item(iid, "tags") or ())
            # bersihkan tag evenrow/oddrow LAMA, pertahankan tag lain
            # (konsisten_row/fluktuatif_row/resto_khusus — cell tag terpisah).
            cleaned = [t for t in existing
                       if t not in ("evenrow", "oddrow")]
            cleaned.append("evenrow" if parity == 0 else "oddrow")
            try:
                tree.item(iid, tags=tuple(cleaned))
            except tk.TclError:
                pass
        # re-apply cell tags (hilang setelah sort)
        if self._cell_tags:
            apply_cell_tag(tree, "neg_cell", self._neg_cells)
            apply_cell_tag(tree, "resto_khusus_cell",
                           self._resto_khusus_cells)

    # =========================================================================
    # FILTER ⧩ + SORT
    # =========================================================================
    def _on_col_filter(self, col_sel: dict):
        self._col_sel = dict(col_sel)
        self._refresh()

    def _sort_by(self, col: str, reverse: bool = True):
        # v3.11.48 — FIX audit #1+#4+#5: pass on_done supaya zebra per-group
        # + cell tags re-applied setelah sort (sebelumnya zebra jadi random
        # + cell tag neg/resto_khusus hilang krn sort delete+insert ulang).
        sort_tree_by_column(
            self.tree, col, reverse=reverse,
            on_done=self._reapply_zebra_per_group)

    def _reset_filter(self):
        self._col_sel = {c[0]: None for c in MINUS_COLUMNS}
        self._filters.clear()
        self._refresh()

    # =========================================================================
    # v3.11.56 — U2: CONTEXT MENU DEEP-LINK (klik-kanan pasangan → tab 📦)
    # =========================================================================
    def _on_context_menu(self, event):
        """v3.11.56 — U2: klik-kanan baris pasangan → menu "Buka di 📦
        Deviasi GR" (app._go_to_deviasi → DeviasiView.focus_pair memasang
        filter Resto+Nama Barang + memilih barisnya). Tanpa callback
        (standalone/test) → no-op senyap."""
        if self.go_to_deviasi is None:
            return
        tree = event.widget
        iid = tree.identify_row(event.y)
        if not iid:
            return
        try:
            if iid not in tree.selection():
                tree.selection_set(iid)
            vals = tree.item(iid, "values")
        except tk.TclError:
            return
        if not vals:
            return
        # Resto = kolom 0, Nama Barang = kolom 1 (urutan MINUS_COLUMNS —
        # mirror _on_double_click)
        resto = str(vals[0]).strip() if len(vals) > 0 else ""
        barang = str(vals[1]).strip() if len(vals) > 1 else ""
        if not resto and not barang:
            return
        menu = tk.Menu(tree, tearoff=0)
        menu.add_command(
            label=f"🔎 Buka {(barang or resto)[:40]} di 📦 Deviasi GR",
            command=lambda: self.go_to_deviasi(resto or None,
                                               barang or None))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # =========================================================================
    # DOUBLE-CLICK → DRILL-DOWN (ide G)
    # =========================================================================
    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return
        tree = event.widget
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return
        # baca nilai baris
        try:
            vals = tree.item(row_iid, "values")
        except tk.TclError:
            return
        if not vals:
            return
        # nama barang = kolom index 1 (Resto=0, Nama Barang=1)
        nama_barang = str(vals[1]) if len(vals) > 1 else None
        if not nama_barang:
            return
        # mulai minus tgl = kolom index 4 (Mulai Minus)
        tgl_mulai = None
        try:
            tgl_mulai = int(float(str(vals[4]).replace(".", "")
                                 .replace(",", ".").strip("()")))
        except (ValueError, IndexError):
            pass
        # drill-down details_popup
        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()
        with contextlib.suppress(Exception):
            show_details_popup(
                root, self.data,
                nama_barang=nama_barang,
                jenis="2.SALDO AKHIR",
                tanggal=tgl_mulai,
                show_maximize=False,
                in_detail=None,
                rincian_po_df=self.rincian_po_df)

    # =========================================================================
    # EXPORT EXCEL (ide I)
    # =========================================================================
    def _export_excel(self):
        if self._minus_df is None or self._minus_df.empty:
            messagebox.showinfo("Export Excel",
                                "Tidak ada data untuk diexport.",
                                parent=self.winfo_toplevel())
            return
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Export Saldo Sistem Minus",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")])
        if not path:
            return
        try:
            df = self._minus_df.copy()
            # bangun Keterangan per baris
            if "Keterangan" not in df.columns:
                df["Keterangan"] = df.apply(_build_keterangan, axis=1)
            # rename kolom df → tampilan
            df = df.rename(columns={
                "NAMA RESTO": "Resto",
                "Tgl Mulai Minus": "Mulai Minus",
            })
            # urut kolom sesuai MINUS_COLUMNS
            col_order = [c[0] for c in MINUS_COLUMNS
                         if c[0] in df.columns]
            df = df[col_order]
            df.to_excel(path, index=False, sheet_name="Saldo Minus")
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
        self._minus_df = None  # invalidate cache
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def _on_shared_saldo_sistem_changed(self, new_mode):
        self.saldo_sistem_mode = str(new_mode)
        if hasattr(self, "_mode_var"):
            self._mode_var.set(
                "42.17" if self.saldo_sistem_mode == "4217" else "Pivot")
        self._minus_df = None  # invalidate cache
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
