"""
pivot_view.py — Pivot table view (v3.0 redesign).

Menampilkan data Append1 sebagai matrix pivot (rows: Nama Barang × JENIS,
cols: Tanggal) — logika identik dengan versi lama, tampilan baru:
- Empty state dengan CTA "Jalankan Pipeline" saat belum ada data
- KPI strip: jumlah barang, jumlah tanggal, jumlah baris
- Filter card (RESTO / BARANG / SOURCE / KATEGORI / search) + tombol Reset
- Kartu tabel dengan footer status
- Conditional formatting dari sample Excel dipertahankan:
  * DEVIASI row → font merah
  * Selisih IN ≠ 0 → font merah + bg pink
  * Value = 0 → suppress (tampil "-", font abu-abu)
  * "4.IN" → cokelat + kuning muda
  * "5.BARANG MASUK" → hijau tua + hijau muda
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from typing import Optional, Callable

from .theme import (
    C_ACCENT, C_BG, C_CARD, C_HEADER, C_TEXT_MUTED, ROW_EVEN, ROW_ODD,
    font, setup_tree_tags,
)
from .widgets import (
    Card, EmptyState, GhostButton, KpiCard, KpiRow, LegendRow, add_tooltip,
    make_tree,
)


class PivotTableView(tk.Frame):
    """Pivot matrix view dengan tampilan card-based."""

    # Metric order — fixed (identik versi lama):
    METRICS = [
        "SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
        "4.IN", "5.BARANG MASUK", "6.PEMAKAIAN (COM)",
        "7.Selisih IN", "8.BARANG KELUAR", "9.OUT",
    ]

    # Soft pastel background per metric (identik versi lama)
    METRIC_BG = {
        "SALDO AWAL": "#F5F5F5",
        "1.SO": "#F0F4FA",
        "2.SALDO AKHIR": "#F2F8EE",
        "3.DEVIASI": "#FDF6E3",
        "4.IN": "#FFFBE6",
        "5.BARANG MASUK": "#EEF7EC",
        "6.PEMAKAIAN (COM)": "#E8E0F0",
        "7.Selisih IN": "#FCEEE8",
        "8.BARANG KELUAR": "#FFF0E0",
        "9.OUT": "#F8F0F0",
    }

    def __init__(self, parent, data: pd.DataFrame = None,
                 go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self.go_to_proses = go_to_proses

        self._build_ui()
        self._setup_tags()
        if data is not None and not data.empty:
            self.load_data(data)
        else:
            self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="📊", title="Belum ada data pivot",
            subtitle="Jalankan pipeline untuk memuat matrix pivot "
                     "(Nama Barang × Tanggal) ke tampilan ini.",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=self._cta_proses)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ( disembunyikan sampai ada data ) ---
        self.content = tk.Frame(self, bg=C_BG)

        # KPI row
        kpi = KpiRow(self.content)
        self.kpi_items = KpiCard(kpi, "Barang", "—", "nama barang unik")
        self.kpi_days = KpiCard(kpi, "Tanggal", "—", "kolom tanggal")
        self.kpi_rows = KpiCard(kpi, "Baris Matrix", "—", "barang × metric")
        for c in (self.kpi_items, self.kpi_days, self.kpi_rows):
            kpi.add(c)
        kpi.pack(fill="x", padx=12, pady=(12, 8))

        # --- Filter card ---
        fcard = Card(self.content, title="Filter",
                     subtitle="Semua filter live-apply. Search = substring, "
                              "kosongkan untuk lihat semua.")
        fcard.pack(fill="x", padx=12)
        fbody = fcard.body()

        # Row 0: NAMA RESTO, NAMA BARANG
        r0 = tk.Frame(fbody, bg=C_CARD)
        r0.pack(fill="x", pady=(0, 6))
        tk.Label(r0, text="RESTO", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.resto_var = tk.StringVar(value="(All)")
        self.resto_combo = ttk.Combobox(r0, textvariable=self.resto_var,
                                        state="readonly", width=16)
        self.resto_combo.pack(side="left", padx=(6, 18))
        self.resto_combo.bind("<<ComboboxSelected>>",
                              lambda e: self._refresh_pivot())
        add_tooltip(self.resto_combo, "Filter cabang resto")

        tk.Label(r0, text="NAMA BARANG", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.barang_var = tk.StringVar(value="(All)")
        self.barang_combo = ttk.Combobox(r0, textvariable=self.barang_var,
                                         state="readonly", width=26)
        self.barang_combo.pack(side="left", padx=(6, 0))
        self.barang_combo.bind("<<ComboboxSelected>>",
                               lambda e: self._refresh_pivot())
        add_tooltip(self.barang_combo, "Filter nama barang (exact match)")

        # Row 1: SOURCE KIRIMAN, KATEGORI
        r1 = tk.Frame(fbody, bg=C_CARD)
        r1.pack(fill="x", pady=(0, 6))
        tk.Label(r1, text="SOURCE KIRIMAN", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.source_var = tk.StringVar(value="(All)")
        self.source_combo = ttk.Combobox(r1, textvariable=self.source_var,
                                         state="readonly", width=16)
        self.source_combo.pack(side="left", padx=(6, 18))
        self.source_combo.bind("<<ComboboxSelected>>",
                               lambda e: self._refresh_pivot())

        tk.Label(r1, text="KATEGORI", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.kategori_var = tk.StringVar(value="(All)")
        self.kategori_combo = ttk.Combobox(r1, textvariable=self.kategori_var,
                                           state="readonly", width=16)
        self.kategori_combo.pack(side="left", padx=(6, 18))
        self.kategori_combo.bind("<<ComboboxSelected>>",
                                 lambda e: self._refresh_pivot())

        # Row 2: search + reset
        r2 = tk.Frame(fbody, bg=C_CARD)
        r2.pack(fill="x")
        tk.Label(r2, text="CARI", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.search_var = tk.StringVar(value="")
        search_entry = ttk.Entry(r2, textvariable=self.search_var, width=32)
        search_entry.pack(side="left", padx=(6, 12))
        search_entry.bind("<KeyRelease>", lambda e: self._refresh_pivot())
        add_tooltip(search_entry,
                    "Pencarian substring case-insensitive pada Nama Barang.\n"
                    "Mencocokkan baris parent (semua metric ikut tampil).")
        GhostButton(r2, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left", padx=(4, 0))

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(8, 0))
        tbody = tcard.body()

        self.tree = ttk.Treeview(tbody, show="tree headings", selectmode="browse")

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tbody.grid_rowconfigure(0, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        # Footer card: hint + status
        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Label(foot, text="🖱 Double-click cell/baris untuk detail source data",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(side="left")

        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(8, "bold")).pack(side="right")

        # Legend metric colors
        legend = LegendRow(
            self.content,
            [("IN", "#9C5700"), ("BARANG MASUK", "#006100"),
             ("DEVIASI", "#CC0000"), ("Selisih ≠ 0", "#FFC9C9")])
        legend.pack(fill="x", padx=12, pady=(6, 0))

        self.tree.bind("<Double-1>", self._on_double_click)

    def _cta_proses(self):
        if self.go_to_proses:
            self.go_to_proses()

    def _show_empty(self):
        self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    def _setup_tags(self):
        """Tag Treeview: warna metric + conditional formatting (identik lama)."""
        for metric, color in self.METRIC_BG.items():
            self.tree.tag_configure(self._metric_tag(metric), background=color)

        self.tree.tag_configure(
            "item_header", font=font(9, "bold"), background="#e2e8f0",
            foreground=C_HEADER)
        self.tree.tag_configure("deviasi_row", foreground="#CC0000")
        self.tree.tag_configure("selisih_anomaly", foreground="#CC0000",
                                background="#FFC9C9")
        self.tree.tag_configure("in_row", foreground="#9C5700",
                                background="#FFEB9C")
        self.tree.tag_configure("bm_row", foreground="#006100",
                                background="#C6EFCE")
        self.tree.tag_configure("negative", foreground="#CC0000")
        self.tree.tag_configure("zero_value", foreground="#999999")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        self._show_content()
        self._populate_filters()
        self._refresh_pivot()

    def _populate_filters(self):
        if self.data is None or self.data.empty:
            return
        for col, combo in [
            ("NAMA RESTO", self.resto_combo),
            ("Nama Barang", self.barang_combo),
            ("SOURCE KIRIMAN", self.source_combo),
            ("KATEGORI", self.kategori_combo),
        ]:
            if col in self.data.columns:
                values = ["(All)"] + sorted(
                    self.data[col].dropna().astype(str).unique().tolist())
                combo["values"] = values

    # =========================================================================
    # PIVOT COMPUTATION + RENDERING (logika identik versi lama)
    # =========================================================================
    def _refresh_pivot(self):
        if self.data is None or self.data.empty:
            self.status_var.set("Belum ada data.")
            return

        # Apply filters
        df = self.data
        for col, var in [
            ("NAMA RESTO", self.resto_var),
            ("Nama Barang", self.barang_var),
            ("SOURCE KIRIMAN", self.source_var),
            ("KATEGORI", self.kategori_var),
        ]:
            val = var.get()
            if val and val != "(All)" and col in df.columns:
                df = df[df[col].astype(str) == val]

        # substring search (case-insensitive) — parent rows only
        search_val = self.search_var.get().strip().lower()
        if search_val and "Nama Barang" in df.columns:
            df = df[df["Nama Barang"].astype(str).str.lower().str.contains(
                search_val, regex=False)]

        if df.empty:
            self.tree.delete(*self.tree.get_children())
            self.status_var.set("Tidak ada data setelah filter.")
            return

        # Compute pivot
        try:
            pivot = df.pivot_table(
                index=["Nama Barang", "JENIS"],
                columns="Tanggal",
                values="NILAI",
                aggfunc="sum",
                fill_value=0,
            )
        except Exception as e:
            self.status_var.set(f"Error: {e}")
            return

        if pivot.empty:
            self.tree.delete(*self.tree.get_children())
            self.status_var.set("Tidak ada data setelah pivot.")
            return

        tanggals = sorted(pivot.columns.tolist())
        items = sorted(pivot.index.get_level_values("Nama Barang").unique().tolist())

        # Clear tree
        self.tree.delete(*self.tree.get_children())

        # Configure columns
        self.tree["columns"] = [str(t) for t in tanggals]
        self.tree.column("#0", width=280, minwidth=180)
        self.tree.heading("#0", text="Nama Barang")
        for t in tanggals:
            self.tree.column(str(t), width=70, minwidth=50, anchor="e")
            self.tree.heading(str(t), text=str(t))

        # Insert rows: item header (parent) + metric rows (children)
        row_count = 0
        for item in items:
            item_iid = f"item_{row_count}"
            self.tree.insert(
                "", "end", iid=item_iid, text=item,
                values=["" for _ in tanggals],
                tags=("item_header",),
            )
            row_count += 1

            for metric in self.METRICS:
                if metric == "6.PEMAKAIAN (COM)":
                    row_data = self._compute_com(pivot, item, tanggals)
                else:
                    try:
                        row_data = pivot.loc[(item, metric)]
                    except KeyError:
                        row_data = pd.Series({t: 0 for t in tanggals})

                tags = self._compute_row_tags(metric, item, row_data, tanggals)

                values = []
                for t in tanggals:
                    v = row_data.get(t, 0)
                    values.append(self._format_num(v))

                self.tree.insert(
                    item_iid, "end", text=metric, values=values, tags=tags
                )
                row_count += 1

        # Expand all items
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

        # KPI + status
        self.kpi_items.set_value(f"{len(items):,}", "nama barang unik")
        self.kpi_days.set_value(f"{len(tanggals):,}", "kolom tanggal")
        self.kpi_rows.set_value(f"{row_count:,}", f"filter: {len(df):,} dari "
                                                   f"{len(self.data):,} rows")
        self.status_var.set(
            f"{len(items)} barang × {len(tanggals)} tanggal = {row_count} baris · "
            f"filtered {len(df):,}/{len(self.data):,} rows")

    def _compute_row_tags(self, metric: str, item: str, row_data: pd.Series,
                          tanggals: list) -> tuple:
        """Conditional formatting rules (identik versi lama)."""
        has_negative = any(
            (row_data.get(t, 0) or 0) < 0 for t in tanggals
        )

        if metric == "4.IN":
            return ("in_row",)
        if metric == "5.BARANG MASUK":
            return ("bm_row",)
        if metric == "7.Selisih IN":
            has_nonzero = any(row_data.get(t, 0) != 0 for t in tanggals)
            if has_nonzero:
                return ("selisih_anomaly",)
            return (self._metric_tag(metric),)
        if metric == "3.DEVIASI":
            return ("deviasi_row",)
        if has_negative:
            return ("negative", self._metric_tag(metric))
        return (self._metric_tag(metric),)

    def _reset_filter(self):
        self.resto_var.set("(All)")
        self.barang_var.set("(All)")
        self.source_var.set("(All)")
        self.kategori_var.set("(All)")
        self.search_var.set("")
        self._refresh_pivot()

    # =========================================================================
    # DOUBLE-CLICK → POPUP DETAILS (identik versi lama)
    # =========================================================================
    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return

        row_iid = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)

        if not row_iid:
            return

        parent_iid = self.tree.parent(row_iid)

        if parent_iid:
            nama_barang = self.tree.item(parent_iid, "text")
            jenis = self.tree.item(row_iid, "text")
        else:
            nama_barang = self.tree.item(row_iid, "text")
            jenis = None

        tanggal = None
        if col_id and col_id != "#0":
            try:
                col_idx = int(col_id.replace("#", "")) - 1
                tree_cols = list(self.tree["columns"])
                if 0 <= col_idx < len(tree_cols):
                    tanggal_str = tree_cols[col_idx]
                    tanggal = int(tanggal_str)
            except (ValueError, IndexError):
                pass

        active_filters = {}
        for col, var in [
            ("NAMA RESTO", self.resto_var),
            ("SOURCE KIRIMAN", self.source_var),
            ("KATEGORI", self.kategori_var),
        ]:
            val = var.get()
            if val and val != "(All)":
                active_filters[col] = val

        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()
        show_details_popup(
            root, self.data,
            nama_barang=nama_barang,
            jenis=jenis,
            tanggal=tanggal,
            filters=active_filters,
        )

    # =========================================================================
    # HELPERS (identik versi lama)
    # =========================================================================
    @staticmethod
    def _metric_tag(metric: str) -> str:
        return metric.lower().replace(" ", "_").replace(".", "_").replace("-", "_")

    @staticmethod
    def _format_num(val) -> str:
        """Format angka: 1 desimal, separator ribuan, negatif dalam kurung."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        if val == 0:
            return "-"
        if val == int(val):
            s = f"{val:,.0f}"
        else:
            s = f"{val:,.1f}"
        if val < 0:
            return f"({s[1:]})"
        return s

    @staticmethod
    def _compute_com(pivot, item, tanggals):
        """Hitung 6.PEMAKAIAN (COM) per tanggal (port dari M code)."""
        def get_series(jenis):
            try:
                return pivot.loc[(item, jenis)]
            except KeyError:
                return pd.Series({t: 0 for t in tanggals})

        so = get_series("1.SO")
        bm = get_series("4.IN")
        bk = get_series("8.BARANG KELUAR")
        sa = get_series("SALDO AWAL")

        com_values = {}
        for i, t in enumerate(tanggals):
            so_val = float(so.get(t, 0) or 0)
            bm_val = float(bm.get(t, 0) or 0)
            bk_val = float(bk.get(t, 0) or 0)
            sa_val = float(sa.get(t, 0) or 0)

            if i == 0:
                com_val = sa_val + bm_val - bk_val - so_val
            else:
                so_prev = float(so.get(tanggals[i - 1], 0) or 0)
                com_val = so_prev + bm_val - bk_val - so_val

            com_values[t] = com_val

        return pd.Series(com_values)
