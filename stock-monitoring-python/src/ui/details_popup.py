"""
details_popup.py — Popup window untuk menampilkan source rows Append1.
Muncul saat user double-click cell di PivotTableView.

Menampilkan 10 kolom:
  Nama Barang, NAMA RESTO, Tanggal, JENIS, NILAI,
  Nomor, Nomor PO, #Tgl/Jam Pembuatan IT, KATEGORI, SOURCE KIRIMAN
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Optional


# Column definitions: (column_id, display_name, width, anchor)
COLUMNS = [
    ("Nama Barang", 140, "w"),
    ("NAMA RESTO", 80, "w"),
    ("Tanggal", 60, "e"),
    ("JENIS", 100, "w"),
    ("NILAI", 90, "e"),
    ("Nomor", 130, "w"),
    ("Nomor PO", 130, "w"),
    ("#Tgl/Jam Pembuatan IT", 140, "w"),
    ("KATEGORI", 80, "w"),
    ("SOURCE KIRIMAN", 100, "w"),
]


class DetailsPopup(tk.Toplevel):
    """Popup window menampilkan source rows untuk kombinasi cell pivot."""

    def __init__(self, parent, title: str, df: pd.DataFrame, filter_info: str = ""):
        """
        Args:
            parent: parent widget (root Tk)
            title: judul popup (e.g., "GULA (V.20) / 1.SO / Tgl 5")
            df: DataFrame source rows (sudah filtered)
            filter_info: string deskripsi filter aktif (e.g., "NAMA RESTO=MLGPAR")
        """
        super().__init__(parent)
        self.title(f"Details: {title}")
        self.geometry("1100x500")
        self.minsize(800, 300)

        # Modal — block parent sampai ditutup
        self.transient(parent)
        self.grab_set()

        # State
        self.df = df

        # Build UI
        self._build_ui(title, filter_info)

        # Render data
        self._render()

        # Focus + close on Escape
        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self, title: str, filter_info: str):
        # --- Header frame ---
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=8, pady=(8, 4))

        ttk.Label(
            header,
            text=f"Details: {title}",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        if filter_info:
            ttk.Label(
                header,
                text=f"Filter aktif: {filter_info}",
                font=("Segoe UI", 9),
                # FIX: contrast #666 → #555 (still acceptable, slightly darker)
                foreground="#555",
            ).pack(anchor="w", pady=(2, 0))

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=8, pady=4)

        # --- Treeview ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

        col_ids = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings", selectmode="browse")

        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50, anchor=anchor)
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Alternating row colors
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        # Negative NILAI → red font
        self.tree.tag_configure("negative", foreground="#CC0000")

        # --- Status bar ---
        self.status_var = tk.StringVar()
        ttk.Label(
            self,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            # FIX: contrast #666 → #555
            foreground="#555",
        ).pack(anchor="w", padx=8, pady=(4, 2))

        # --- Button frame ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=(2, 8))
        ttk.Button(btn_frame, text="Tutup", command=self.destroy).pack(side=tk.RIGHT)

    def _render(self):
        """Render DataFrame ke Treeview."""
        self.tree.delete(*self.tree.get_children())

        if self.df is None or self.df.empty:
            self.status_var.set("Tidak ada source data untuk kombinasi ini.")
            return

        # Prepare column data as lists for fast iteration
        col_data = {}
        for col_name, _, _ in COLUMNS:
            if col_name in self.df.columns:
                col_data[col_name] = self.df[col_name].tolist()
            else:
                col_data[col_name] = [""] * len(self.df)

        n = len(self.df)
        total_nilai = 0
        for i in range(n):
            values = []
            has_negative = False
            for col_name, _, _ in COLUMNS:
                val = col_data[col_name][i]
                if col_name == "NILAI":
                    formatted, is_neg = self._fmt_nilai(val)
                    values.append(formatted)
                    if is_neg:
                        has_negative = True
                    try:
                        total_nilai += float(val) if val is not None and not pd.isna(val) else 0
                    except (TypeError, ValueError):
                        pass
                else:
                    values.append(self._fmt_cell(val, col_name))
            # Tags: negative + alternating
            tags = []
            if has_negative:
                tags.append("negative")
            tags.append("evenrow" if i % 2 == 0 else "oddrow")
            self.tree.insert("", "end", values=values, tags=tuple(tags))

        # Status
        if total_nilai == int(total_nilai):
            total_str = f"{int(total_nilai):,}"
        else:
            total_str = f"{total_nilai:,.1f}"
        self.status_var.set(f"{n} rows. Total NILAI: {total_str}")

    @staticmethod
    def _fmt_nilai(val):
        """Format NILAI: thousand separators, negative in parentheses, 1 decimal.
        Returns (formatted_string, is_negative)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "", False
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val), False
        is_neg = v < 0
        if v == 0:
            return "-", False
        if v == int(v):
            s = f"{v:,.0f}"
        else:
            s = f"{v:,.1f}"
        if is_neg:
            return f"({s[1:]})", True
        return s, False

    @staticmethod
    def _fmt_cell(val, col_name: str) -> str:
        """Format cell value for display."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        # Datetime columns
        if col_name in ("#Tgl/Jam Pembuatan IT",):
            if hasattr(val, "strftime"):
                return val.strftime("%d/%m/%Y %H:%M:%S")
            try:
                return pd.to_datetime(val).strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                return str(val)
        # Tanggal (int)
        if col_name == "Tanggal":
            try:
                return str(int(val))
            except (TypeError, ValueError):
                return str(val)
        return str(val)


def show_details_popup(parent, data: pd.DataFrame, nama_barang: str = None,
                        jenis: str = None, tanggal=None,
                        filters: dict = None):
    """Filter data + show popup.

    Args:
        parent: parent widget
        data: full Append1 DataFrame
        nama_barang: filter Nama Barang (None = all)
        jenis: filter JENIS (None = all)
        tanggal: filter Tanggal (None = all)
        filters: dict of {column: value} for additional filters (e.g., NAMA RESTO)
    """
    if data is None or data.empty:
        # Show empty popup
        popup = DetailsPopup(parent, "Tidak ada data", pd.DataFrame())
        return popup

    df = data.copy()

    # Build title parts
    title_parts = []
    if nama_barang:
        df = df[df["Nama Barang"].astype(str) == str(nama_barang)]
        title_parts.append(nama_barang)
    if jenis:
        df = df[df["JENIS"].astype(str) == str(jenis)]
        title_parts.append(jenis)
    if tanggal is not None:
        try:
            tgl_int = int(tanggal)
            df = df[pd.to_numeric(df["Tanggal"], errors="coerce") == tgl_int]
            title_parts.append(f"Tgl {tgl_int}")
        except (TypeError, ValueError):
            pass

    # Apply additional filters (from active pivot filters)
    filter_info_parts = []
    if filters:
        for col, val in filters.items():
            if val and val != "(All)" and col in df.columns:
                df = df[df[col].astype(str) == str(val)]
                filter_info_parts.append(f"{col}={val}")

    title = " / ".join(title_parts) if title_parts else "All Data"
    filter_info = ", ".join(filter_info_parts) if filter_info_parts else ""

    popup = DetailsPopup(parent, title, df.reset_index(drop=True), filter_info)
    return popup
