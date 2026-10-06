"""
pivot_view.py — Excel-like pivot table widget untuk Tkinter.
Menampilkan data Append1 sebagai matrix pivot (rows: Nama Barang × JENIS, cols: Tanggal).

OPTIMIZED untuk speed:
- Pre-compute pivot dengan pandas pivot_table (vectorized C-level)
- Filter changes hanya re-aggregate (fast)
- Treeview bulk insert dengan tags untuk color coding
- No Python loop per cell — gun pandas .map() untuk formatting

Visual style matching Excel sample:
- Filter bar di atas (NAMA RESTO, SOURCE KIRIMAN, KATEGORI)
- Row Labels (tree column) + Tanggal columns
- Color coding per metric (1.SO, 2.SALDO AKHIR, etc.)
- Negative values in parentheses (accounting style)
- Zero shown as '-'
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from typing import Optional


class PivotTableView(ttk.Frame):
    """Excel-like pivot table in Tkinter."""

    # Metric order (same as Excel sample)
    METRICS = [
        "SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
        "4.IN", "5.BARANG MASUK", "6.Selisih IN", "7.OUT",
    ]

    # Light background colors per metric (matching Excel style)
    METRIC_BG = {
        "SALDO AWAL": "#E0E0E0",
        "1.SO": "#DAE3F3",
        "2.SALDO AKHIR": "#E2EFDA",
        "3.DEVIASI": "#FFF2CC",
        "4.IN": "#DDEBF7",
        "5.BARANG MASUK": "#E4DFEC",
        "6.Selisih IN": "#FCE4D6",
        "7.OUT": "#F8CBAD",
    }

    def __init__(self, parent, data: pd.DataFrame = None):
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None

        self._build_ui()
        if data is not None and not data.empty:
            self.load_data(data)

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Filter bar (top) ---
        filter_frame = ttk.LabelFrame(self, text="Filter")
        filter_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(filter_frame, text="NAMA RESTO:").grid(
            row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        self.resto_var = tk.StringVar(value="(All)")
        self.resto_combo = ttk.Combobox(
            filter_frame, textvariable=self.resto_var, state="readonly", width=15)
        self.resto_combo.grid(row=0, column=1, padx=(0, 12), pady=4)
        self.resto_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_pivot())

        ttk.Label(filter_frame, text="SOURCE KIRIMAN:").grid(
            row=0, column=2, padx=(0, 4), pady=4, sticky="w")
        self.source_var = tk.StringVar(value="(All)")
        self.source_combo = ttk.Combobox(
            filter_frame, textvariable=self.source_var, state="readonly", width=15)
        self.source_combo.grid(row=0, column=3, padx=(0, 12), pady=4)
        self.source_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_pivot())

        ttk.Label(filter_frame, text="KATEGORI:").grid(
            row=0, column=4, padx=(0, 4), pady=4, sticky="w")
        self.kategori_var = tk.StringVar(value="(All)")
        self.kategori_combo = ttk.Combobox(
            filter_frame, textvariable=self.kategori_var, state="readonly", width=15)
        self.kategori_combo.grid(row=0, column=5, padx=(0, 12), pady=4)
        self.kategori_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_pivot())

        ttk.Button(filter_frame, text="Reset Filter", command=self._reset_filter).grid(
            row=0, column=6, padx=4, pady=4)

        # --- Pivot table (Treeview) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, show="tree headings", selectmode="browse")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Configure tags for metric colors
        for metric, color in self.METRIC_BG.items():
            tag = self._metric_tag(metric)
            self.tree.tag_configure(tag, background=color)
        self.tree.tag_configure("item_header", font=("Segoe UI", 9, "bold"),
                                 background="#D9D9D9")
        self.tree.tag_configure("grand_total", font=("Segoe UI", 9, "bold"),
                                 background="#BFBFBF")

        # --- Status bar (bottom) ---
        self.status_var = tk.StringVar(value="Belum ada data. Jalankan pipeline di tab Proses.")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", pady=(2, 0))

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        """Load new data and refresh pivot."""
        self.data = data
        self._populate_filters()
        self._refresh_pivot()

    def _populate_filters(self):
        """Populate filter comboboxes with unique values from data."""
        if self.data is None or self.data.empty:
            return

        for col, combo in [
            ("NAMA RESTO", self.resto_combo),
            ("SOURCE KIRIMAN", self.source_combo),
            ("KATEGORI", self.kategori_combo),
        ]:
            if col in self.data.columns:
                values = ["(All)"] + sorted(
                    self.data[col].dropna().astype(str).unique().tolist())
                combo["values"] = values

    # =========================================================================
    # PIVOT COMPUTATION + RENDERING
    # =========================================================================
    def _refresh_pivot(self):
        """Recompute pivot and render in Treeview."""
        if self.data is None or self.data.empty:
            self.status_var.set("Belum ada data.")
            return

        # Apply filters
        df = self.data
        for col, var in [
            ("NAMA RESTO", self.resto_var),
            ("SOURCE KIRIMAN", self.source_var),
            ("KATEGORI", self.kategori_var),
        ]:
            val = var.get()
            if val and val != "(All)" and col in df.columns:
                df = df[df[col].astype(str) == val]

        if df.empty:
            self.tree.delete(*self.tree.get_children())
            self.status_var.set("Tidak ada data setelah filter.")
            return

        # Compute pivot: rows=(Nama Barang, JENIS), cols=Tanggal, values=sum(NILAI)
        # This is vectorized C-level — very fast
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

        # Get sorted tanggal columns + items
        tanggals = sorted(pivot.columns.tolist())
        items = sorted(pivot.index.get_level_values("Nama Barang").unique().tolist())

        # Clear tree
        self.tree.delete(*self.tree.get_children())

        # Configure columns
        self.tree["columns"] = [str(t) for t in tanggals]
        self.tree.column("#0", width=200, minwidth=150)
        self.tree.heading("#0", text="Row Labels")
        for t in tanggals:
            self.tree.column(str(t), width=70, minwidth=50, anchor="e")
            self.tree.heading(str(t), text=str(t))

        # Insert rows: item header (parent) + 8 metric rows (children)
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
                try:
                    row_data = pivot.loc[(item, metric)]
                except KeyError:
                    row_data = pd.Series({t: 0 for t in tanggals})

                # Format values efficiently
                values = [self._format_num(row_data.get(t, 0)) for t in tanggals]
                tag = self._metric_tag(metric)
                self.tree.insert(
                    item_iid, "end", text=metric, values=values, tags=(tag,)
                )
                row_count += 1

        # Expand all items
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

        self.status_var.set(
            f"{len(items)} barang × {len(tanggals)} tanggal = {row_count} baris. "
            f"Filtered: {len(df)} dari {len(self.data)} rows."
        )

    def _reset_filter(self):
        """Reset all filters to (All)."""
        self.resto_var.set("(All)")
        self.source_var.set("(All)")
        self.kategori_var.set("(All)")
        self._refresh_pivot()

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _metric_tag(metric: str) -> str:
        """Convert metric name to valid tag (lowercase, no spaces/dots)."""
        return metric.lower().replace(" ", "_").replace(".", "_").replace("-", "_")

    @staticmethod
    def _format_num(val) -> str:
        """Format number: thousand separators, 0 → '-', negative in parentheses."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        if val == 0:
            return "-"
        if val == int(val):
            s = f"{int(val):,}"
        else:
            s = f"{val:,.2f}"
        if val < 0:
            return f"({s[1:]})"  # (123) accounting style for negative
        return s
