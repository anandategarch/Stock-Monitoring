"""
pivot_view.py — Excel-like pivot table widget untuk Tkinter.
Menampilkan data Append1 sebagai matrix pivot (rows: Nama Barang × JENIS, cols: Tanggal).

Visual style matching Excel sample:
- Filter bar di atas (NAMA RESTO, NAMA BARANG, SOURCE KIRIMAN, KATEGORI)
- Row Labels (tree column) + Tanggal columns
- Conditional formatting dari sample Excel:
  * DEVIASI row → font merah
  * Selisih IN ≠ 0 → font merah + bg pink (FFFFC9C9)
  * Value = 0 → suppress (tampilkan "-", font abu-abu)
  * "4.IN" label → brown font (FF9C5700) + light yellow bg (FFFFEB9C)
  * "5.BARANG MASUK" label → dark green font (FF006100) + light green bg (FFC6EFCE)
- Number format: #,##0.0 ;[Red]-#,##0.0(negative merah, 1 decimal)
- Warna background lembut (pastel) — tidak mencolok
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

    # Soft pastel background colors per metric (subtle, not jarring)
    # Based on sample Excel but with reduced intensity
    METRIC_BG = {
        "SALDO AWAL": "#F5F5F5",          # very light gray
        "1.SO": "#F0F4FA",                 # very light blue
        "2.SALDO AKHIR": "#F2F8EE",        # very light green
        "3.DEVIASI": "#FDF6E3",            # very light yellow
        "4.IN": "#FFFBE6",                 # light yellow (per sample conditional fmt)
        "5.BARANG MASUK": "#EEF7EC",       # light green (per sample conditional fmt)
        "6.Selisih IN": "#FCEEE8",         # light pink
        "7.OUT": "#F8F0F0",                # very light red
    }

    def __init__(self, parent, data: pd.DataFrame = None):
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None

        self._build_ui()
        self._setup_tags()
        if data is not None and not data.empty:
            self.load_data(data)

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Filter bar (top) — 2 rows for 4 filters + reset ---
        filter_frame = ttk.LabelFrame(self, text="Filter")
        filter_frame.pack(fill=tk.X, pady=(0, 4))

        # Row 0: NAMA RESTO, NAMA BARANG
        ttk.Label(filter_frame, text="NAMA RESTO:").grid(
            row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        self.resto_var = tk.StringVar(value="(All)")
        self.resto_combo = ttk.Combobox(
            filter_frame, textvariable=self.resto_var, state="readonly", width=15)
        self.resto_combo.grid(row=0, column=1, padx=(0, 12), pady=4)
        self.resto_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_pivot())

        ttk.Label(filter_frame, text="NAMA BARANG:").grid(
            row=0, column=2, padx=(0, 4), pady=4, sticky="w")
        self.barang_var = tk.StringVar(value="(All)")
        self.barang_combo = ttk.Combobox(
            filter_frame, textvariable=self.barang_var, state="readonly", width=25)
        self.barang_combo.grid(row=0, column=3, padx=(0, 12), pady=4)
        self.barang_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_pivot())

        # Row 1: SOURCE KIRIMAN, KATEGORI, Reset
        ttk.Label(filter_frame, text="SOURCE KIRIMAN:").grid(
            row=1, column=0, padx=(8, 4), pady=4, sticky="w")
        self.source_var = tk.StringVar(value="(All)")
        self.source_combo = ttk.Combobox(
            filter_frame, textvariable=self.source_var, state="readonly", width=15)
        self.source_combo.grid(row=1, column=1, padx=(0, 12), pady=4)
        self.source_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_pivot())

        ttk.Label(filter_frame, text="KATEGORI:").grid(
            row=1, column=2, padx=(0, 4), pady=4, sticky="w")
        self.kategori_var = tk.StringVar(value="(All)")
        self.kategori_combo = ttk.Combobox(
            filter_frame, textvariable=self.kategori_var, state="readonly", width=15)
        self.kategori_combo.grid(row=1, column=3, padx=(0, 12), pady=4)
        self.kategori_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_pivot())

        ttk.Button(filter_frame, text="Reset Filter", command=self._reset_filter).grid(
            row=1, column=4, padx=4, pady=4, sticky="w")

        # --- Pivot table (Treeview) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, show="tree headings", selectmode="browse")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # --- Status bar (bottom) ---
        self.status_var = tk.StringVar(value="Belum ada data. Jalankan pipeline di tab Proses.")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", pady=(2, 0))

        # --- Hint bar (above status) ---
        ttk.Label(
            self,
            text="💡 Double-click cell/baris untuk melihat detail source data",
            font=("Segoe UI", 9, "italic"),
            foreground="#888",
        ).pack(anchor="w", pady=(2, 0))

        # --- Bind double-click ---
        self.tree.bind("<Double-1>", self._on_double_click)

    def _setup_tags(self):
        """Configure Treeview tags for metric colors + conditional formatting."""
        # 1. Soft pastel background per metric
        for metric, color in self.METRIC_BG.items():
            tag = self._metric_tag(metric)
            self.tree.tag_configure(tag, background=color)

        # 2. Item header (Nama Barang) — bold, gray
        self.tree.tag_configure("item_header", font=("Segoe UI", 9, "bold"),
                                 background="#D9D9D9")

        # 3. Conditional formatting tags (from sample Excel dxfs):
        # dxf[13]: DEVIASI row → font red (FFFF0000)
        self.tree.tag_configure("deviasi_row", foreground="#CC0000")

        # dxf[12]: Selisih IN ≠ 0 → font red + bg pink (FFFFC9C9)
        self.tree.tag_configure("selisih_anomaly", foreground="#CC0000",
                                 background="#FFC9C9")

        # dxf[9]: "4.IN" label → brown font (FF9C5700) + light yellow bg (FFFFEB9C)
        self.tree.tag_configure("in_row", foreground="#9C5700",
                                 background="#FFEB9C")

        # dxf[10]: "5.BARANG MASUK" label → dark green font (FF006100) + light green bg (FFC6EFCE)
        self.tree.tag_configure("bm_row", foreground="#006100",
                                 background="#C6EFCE")

        # Negative value → font red (number format [Red])
        self.tree.tag_configure("negative", foreground="#CC0000")

        # Zero value → suppressed (gray, dimmed)
        self.tree.tag_configure("zero_value", foreground="#999999")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
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
    # PIVOT COMPUTATION + RENDERING
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

                # Determine tag(s) based on conditional formatting rules
                tags = self._compute_row_tags(metric, item, row_data, tanggals)

                # Format values
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

        self.status_var.set(
            f"{len(items)} barang × {len(tanggals)} tanggal = {row_count} baris. "
            f"Filtered: {len(df)} dari {len(self.data)} rows."
        )

    def _compute_row_tags(self, metric: str, item: str, row_data: pd.Series, tanggals: list) -> tuple:
        """Compute tags for a metric row based on conditional formatting rules.

        Rules from sample Excel (dxf mapping):
        - "4.IN" → in_row (brown font + yellow bg)
        - "5.BARANG MASUK" → bm_row (green font + green bg)
        - "3.DEVIASI" → deviasi_row (red font)
        - "6.Selisih IN" with any value ≠ 0 → selisih_anomaly (red font + pink bg)
        - Any row with negative value → negative (red font)
          * Priority: in_row / bm_row keep their colors (negatives in parentheses)
          * DEVIASI already red, Selisih anomaly already red
          * Others (SALDO AWAL, 1.SO, 2.SALDO AKHIR, 7.OUT) → red font if has negative

        Note: Treeview applies tags per-ROW, not per-cell. So "negative" red applies
        to the whole row text. This is a limitation — Excel does per-cell coloring.
        """
        # Check for negative values in this row
        has_negative = any(
            (row_data.get(t, 0) or 0) < 0 for t in tanggals
        )

        if metric == "4.IN":
            return ("in_row",)  # brown font + yellow bg (keep, negatives in parentheses)
        if metric == "5.BARANG MASUK":
            return ("bm_row",)  # green font + green bg (keep, negatives in parentheses)
        if metric == "6.Selisih IN":
            has_nonzero = any(row_data.get(t, 0) != 0 for t in tanggals)
            if has_nonzero:
                return ("selisih_anomaly",)  # red font + pink bg
            return (self._metric_tag(metric),)
        if metric == "3.DEVIASI":
            return ("deviasi_row",)  # red font (already red, negatives visible)
        # SALDO AWAL, 1.SO, 2.SALDO AKHIR, 7.OUT:
        # - If has negative → red font (negative tag overrides metric_bg)
        # - Else → metric background
        if has_negative:
            return ("negative", self._metric_tag(metric))
        return (self._metric_tag(metric),)

    def _reset_filter(self):
        self.resto_var.set("(All)")
        self.barang_var.set("(All)")
        self.source_var.set("(All)")
        self.kategori_var.set("(All)")
        self._refresh_pivot()

    # =========================================================================
    # DOUBLE-CLICK → POPUP DETAILS
    # =========================================================================
    def _on_double_click(self, event):
        """Handle double-click: identify cell + show source data popup."""
        if self.data is None or self.data.empty:
            return

        # Identify row + column from click position
        row_iid = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)

        if not row_iid:
            return  # clicked empty area

        # Determine: is this a parent (item header) or child (metric row)?
        parent_iid = self.tree.parent(row_iid)

        if parent_iid:
            # This is a child (metric row)
            # Nama Barang = parent's text
            # JENIS = this row's text
            nama_barang = self.tree.item(parent_iid, "text")
            jenis = self.tree.item(row_iid, "text")
        else:
            # This is a parent (item header)
            # Nama Barang = this row's text
            # JENIS = all
            nama_barang = self.tree.item(row_iid, "text")
            jenis = None

        # Determine Tanggal from column
        tanggal = None
        if col_id and col_id != "#0":
            # col_id format: "#1", "#2", ...
            try:
                col_idx = int(col_id.replace("#", "")) - 1  # 0-indexed
                # Treeview columns are tanggal strings
                tree_cols = list(self.tree["columns"])
                if 0 <= col_idx < len(tree_cols):
                    tanggal_str = tree_cols[col_idx]
                    tanggal = int(tanggal_str)
            except (ValueError, IndexError):
                pass

        # Get active filters (exclude Nama Barang since we filter by it explicitly)
        active_filters = {}
        for col, var in [
            ("NAMA RESTO", self.resto_var),
            ("SOURCE KIRIMAN", self.source_var),
            ("KATEGORI", self.kategori_var),
        ]:
            val = var.get()
            if val and val != "(All)":
                active_filters[col] = val

        # Show popup
        from src.ui.details_popup import show_details_popup
        # Find root Tk for popup parent
        root = self.winfo_toplevel()
        show_details_popup(
            root, self.data,
            nama_barang=nama_barang,
            jenis=jenis,
            tanggal=tanggal,
            filters=active_filters,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _metric_tag(metric: str) -> str:
        return metric.lower().replace(" ", "_").replace(".", "_").replace("-", "_")

    @staticmethod
    def _format_num(val) -> str:
        """Format number: 1 decimal, thousand separators, negative in parentheses (red via tag).
        Mirror Excel numFmt 165: #,##0.0_ ;[Red]-#,##0.0 (negative red)"""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            val = float(val)
        except (TypeError, ValueError):
            return str(val)
        if val == 0:
            return "-"
        # 1 decimal, thousand separators
        if val == int(val):
            s = f"{val:,.0f}"  # whole number, no decimal
        else:
            s = f"{val:,.1f}"  # 1 decimal
        if val < 0:
            return f"({s[1:]})"  # accounting style: (123.4)
        return s
