"""
rincian_po_view.py — Table view untuk Rincian PO data.
Simple Treeview dengan 13 columns + search filter.

OPTIMIZED: bulk insert, search via pandas .str.contains (vectorized).
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from typing import Optional


class RincianPoView(ttk.Frame):
    """Table view untuk Rincian PO data."""

    # Column definitions: (column_id, display_name, width)
    COLUMNS = [
        ("Nomor #", 120),
        ("Tanggal", 90),
        ("Cabang PO", 100),
        ("Pemasok", 200),
        ("Nama Barang", 150),
        ("Satuan", 60),
        ("Kuantitas", 80),
        ("@Harga", 90),
        ("Total Harga", 110),
        ("Keterangan PO", 90),
        ("Status Pesanan Pembelian", 130),
        ("Tgl/Jam Pembuatan", 130),
        ("DBS_Kategori.KATEGORI", 110),
    ]

    def __init__(self, parent, data: pd.DataFrame = None):
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None
        self._sort_col: str = None
        self._sort_asc: bool = True

        self._build_ui()
        if data is not None:
            self.load_data(data)

    def _build_ui(self):
        # --- Search bar (top) ---
        search_frame = ttk.LabelFrame(self, text="Cari")
        search_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(search_frame, text="Kata kunci:").grid(
            row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        self.search_var = tk.StringVar()
        # trace_add untuk Python 3.12+ (fallback trace untuk versi lama)
        if hasattr(self.search_var, "trace_add"):
            self.search_var.trace_add("write", self._on_search)
        else:
            self.search_var.trace("w", self._on_search)
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).grid(
            row=0, column=1, padx=(0, 8), pady=4, sticky="w")
        ttk.Button(search_frame, text="Reset", command=self._reset_search).grid(
            row=0, column=2, padx=4, pady=4)

        # --- Treeview (table) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings", selectmode="browse")

        # Configure columns + headings (clickable for sort)
        for col_name, width in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50)
            self.tree.heading(
                col_name, text=col_name,
                command=lambda c=col_name: self._sort_by(c))

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Alternate row colors
        self.tree.tag_configure("evenrow", background="#F5F5F5")
        self.tree.tag_configure("oddrow", background="#FFFFFF")

        # --- Status bar (bottom) ---
        self.status_var = tk.StringVar(value="Belum ada data. Jalankan pipeline di tab Proses.")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", pady=(2, 0))

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        """Load new data and render."""
        self.data = data
        self.search_var.set("")
        self._render(data)

    def _render(self, data: pd.DataFrame):
        """Render DataFrame to Treeview."""
        self.tree.delete(*self.tree.get_children())

        if data is None or data.empty:
            self.status_var.set("Tidak ada data.")
            return

        # Prepare column data as lists for fast iteration
        col_data = {}
        for col_name, _ in self.COLUMNS:
            if col_name in data.columns:
                col_data[col_name] = data[col_name].tolist()
            else:
                col_data[col_name] = [""] * len(data)

        # Build rows
        n = len(data)
        for i in range(n):
            values = []
            for col_name, _ in self.COLUMNS:
                val = col_data[col_name][i]
                values.append(self._format_cell(val))
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=values, tags=(tag,))

        self.status_var.set(f"{n} baris.")

    # =========================================================================
    # SEARCH + SORT
    # =========================================================================
    def _on_search(self, *args):
        """Filter data by search keyword (vectorized)."""
        if self.data is None or self.data.empty:
            return
        query = self.search_var.get().lower().strip()
        if not query:
            self._render(self.data)
            return

        # Vectorized search: check all columns
        mask = pd.Series([False] * len(self.data))
        for col in self.data.columns:
            col_str = self.data[col].astype(str).str.lower()
            mask = mask | col_str.str.contains(query, na=False)

        self._render(self.data[mask])

    def _reset_search(self):
        self.search_var.set("")
        if self.data is not None:
            self._render(self.data)

    def _sort_by(self, col: str):
        """Sort treeview by column (toggle ascending/descending)."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            items.sort(key=lambda x: float(x[0].replace(",", "").replace("(", "-").replace(")", "")),
                       reverse=not self._sort_asc)
        except (ValueError, AttributeError):
            items.sort(key=lambda x: x[0], reverse=not self._sort_asc)

        for i, (_, k) in enumerate(items):
            self.tree.move(k, "", i)

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _format_cell(val) -> str:
        """Format cell value for display."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        if hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(val, (int, np.integer)):
            return f"{val:,}"
        if isinstance(val, (float, np.floating)):
            if val == int(val):
                return f"{int(val):,}"
            return f"{val:,.2f}"
        return str(val)
