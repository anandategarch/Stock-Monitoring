"""
rincian_po_view.py — Pivot table view untuk Rincian PO data.
Menampilkan sebagai pivot table dengan row hierarchy (seperti sample Excel):
- Page filters: Cabang PO, Status Pesanan Pembelian
- Tree rows: Nomor# (parent) → detail children (Tanggal, Nama Barang, Pemasok, Kuantitas)
- Value: Sum of Kuantitas per row

Struktur mirror pivotTable1 di sample Excel:
  rowFields: Nomor#, Tanggal, Nama Barang, Keterangan PO, Pemasok, Tgl/Jam, Satuan
  dataField: Sum of Kuantitas
  pageFields: Cabang PO, Status Pesanan Pembelian
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from typing import Optional


class RincianPoView(ttk.Frame):
    """Pivot table view untuk Rincian PO data (tree-based, like Excel sample)."""

    def __init__(self, parent, data: pd.DataFrame = None):
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None

        self._build_ui()
        self._setup_tags()
        if data is not None:
            self.load_data(data)

    def _build_ui(self):
        # --- Filter bar (top) — Cabang PO + Status Pesanan ---
        filter_frame = ttk.LabelFrame(self, text="Filter")
        filter_frame.pack(fill=tk.X, pady=(0, 4))

        ttk.Label(filter_frame, text="Cabang PO:").grid(
            row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        self.cabang_var = tk.StringVar(value="(All)")
        self.cabang_combo = ttk.Combobox(
            filter_frame, textvariable=self.cabang_var, state="readonly", width=20)
        self.cabang_combo.grid(row=0, column=1, padx=(0, 16), pady=4)
        self.cabang_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        ttk.Label(filter_frame, text="Status:").grid(
            row=0, column=2, padx=(0, 4), pady=4, sticky="w")
        self.status_pesanan_var = tk.StringVar(value="(All)")
        self.status_combo = ttk.Combobox(
            filter_frame, textvariable=self.status_pesanan_var, state="readonly", width=20)
        self.status_combo.grid(row=0, column=3, padx=(0, 16), pady=4)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        ttk.Button(filter_frame, text="Reset Filter", command=self._reset_filter).grid(
            row=0, column=4, padx=4, pady=4, sticky="w")

        # --- Treeview (pivot table) ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        # Columns: Tanggal | Nama Barang | Keterangan PO | Pemasok | Tgl/Jam | Satuan | Kuantitas
        cols = ["Tanggal", "Nama Barang", "Keterangan PO", "Pemasok",
                "Tgl/Jam Pembuatan", "Satuan", "Kuantitas"]
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="tree headings", selectmode="browse")

        # Configure columns
        self.tree.column("#0", width=160, minwidth=120)  # Nomor# (tree column)
        self.tree.heading("#0", text="Nomor #")
        col_widths = {
            "Tanggal": 90, "Nama Barang": 180, "Keterangan PO": 90,
            "Pemasok": 220, "Tgl/Jam Pembuatan": 130, "Satuan": 60, "Kuantitas": 80,
        }
        for c in cols:
            self.tree.column(c, width=col_widths.get(c, 100), minwidth=50,
                              anchor="e" if c == "Kuantitas" else "w")
            self.tree.heading(c, text=c)

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

    def _setup_tags(self):
        """Configure tags for row styling."""
        # Nomor# parent row — bold, light blue-gray
        self.tree.tag_configure("po_header", font=("Segoe UI", 9, "bold"),
                                 background="#D9E1F2")
        # Detail rows — alternating
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        # Grand total row
        self.tree.tag_configure("grand_total", font=("Segoe UI", 9, "bold"),
                                 background="#BFBFBF")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        self._populate_filters()
        self._refresh()

    def _populate_filters(self):
        if self.data is None or self.data.empty:
            return
        for col, combo in [("Cabang PO", self.cabang_combo),
                           ("Status Pesanan Pembelian", self.status_combo)]:
            if col in self.data.columns:
                values = ["(All)"] + sorted(
                    self.data[col].dropna().astype(str).unique().tolist())
                combo["values"] = values

    # =========================================================================
    # RENDER
    # =========================================================================
    def _refresh(self):
        if self.data is None or self.data.empty:
            self.status_var.set("Belum ada data.")
            return

        df = self.data
        for col, var in [("Cabang PO", self.cabang_var),
                         ("Status Pesanan Pembelian", self.status_pesanan_var)]:
            val = var.get()
            if val and val != "(All)" and col in df.columns:
                df = df[df[col].astype(str) == val]

        self.tree.delete(*self.tree.get_children())

        if df.empty:
            self.status_var.set("Tidak ada data setelah filter.")
            return

        # Group by Nomor# (parent), each child = detail row
        if "Nomor #" not in df.columns:
            self.status_var.set("Kolom 'Nomor #' tidak ditemukan.")
            return

        # Sort by Nomor# then Tanggal
        sort_cols = [c for c in ["Nomor #", "Tanggal"] if c in df.columns]
        df_sorted = df.sort_values(sort_cols) if sort_cols else df

        total_qty = 0
        po_count = 0
        row_idx = 0

        for nomor, group in df_sorted.groupby("Nomor #", sort=False):
            po_count += 1
            # Parent row: Nomor# + summary
            po_qty = group["Kuantitas"].sum() if "Kuantitas" in group.columns else 0
            total_qty += po_qty
            parent_iid = f"po_{po_count}"
            self.tree.insert(
                "", "end", iid=parent_iid, text=str(nomor),
                values=["", "", "", "", "", f"Total:", f"{po_qty:,}"],
                tags=("po_header",),
            )

            # Children: detail rows
            for _, row in group.iterrows():
                tag = "evenrow" if row_idx % 2 == 0 else "oddrow"
                row_idx += 1
                self.tree.insert(
                    parent_iid, "end",
                    text="",  # empty for child (Nomor# shown in parent)
                    values=[
                        self._fmt_date(row.get("Tanggal")),
                        str(row.get("Nama Barang", "")),
                        str(row.get("Keterangan PO", "")),
                        str(row.get("Pemasok", "")),
                        self._fmt_datetime(row.get("Tgl/Jam Pembuatan")),
                        str(row.get("Satuan", "")),
                        self._fmt_num(row.get("Kuantitas")),
                    ],
                    tags=(tag,),
                )

            # Expand parent
            self.tree.item(parent_iid, open=True)

        # Grand total row
        self.tree.insert(
            "", "end", iid="grand_total",
            text="GRAND TOTAL",
            values=["", "", "", "", "", "", f"{total_qty:,}"],
            tags=("grand_total",),
        )

        self.status_var.set(
            f"{po_count} PO × {len(df)} items = {len(df)} baris. "
            f"Total Kuantitas: {total_qty:,}"
        )

    def _reset_filter(self):
        self.cabang_var.set("(All)")
        self.status_pesanan_var.set("(All)")
        self._refresh()

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _fmt_num(val) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            v = float(val)
            if v == int(v):
                return f"{int(v):,}"
            return f"{v:,.1f}"
        except (TypeError, ValueError):
            return str(val)

    @staticmethod
    def _fmt_date(val) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        if hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%d")
        try:
            return pd.to_datetime(val).strftime("%Y-%m-%d")
        except Exception:
            return str(val)

    @staticmethod
    def _fmt_datetime(val) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        if hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%d %H:%M:%S")
        try:
            return pd.to_datetime(val).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(val)
