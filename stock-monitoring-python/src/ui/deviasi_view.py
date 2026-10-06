"""
deviasi_view.py — Wide matrix view untuk DEVIASI GR/PCS.
Menampilkan data Append1 sebagai wide matrix (1 row per Barang+Resto),
mirror sheet DEVIASI GR/PCS di file xlsb sample.

Features:
- Tanggal H dinamis (user set, default 25) → kolom H-2 s/d H+2
- Calculated columns: Deviasi, ABS, Rank, Max Deviasi, Stok Seharusnya
- Filter: Resto, Nama Barang
- Split by Satuan: GR vs non-GR (PCS/BOTOL/etc)
- Double-click → popup source rows (reuse details_popup)
- Color coding: negative red, Deviasi row yellow tint
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from typing import Optional


class DeviasiView(ttk.Frame):
    """Wide matrix view untuk DEVIASI GR/PCS.

    satuan_mode: "GR" → tampilkan hanya SATUAN=GR
                 "PCS" → tampilkan SATUAN selain GR (PCS, BOTOL, dll)
    """

    # Columns: (column_id, display_name, width, anchor)
    COLUMNS = [
        ("Resto", 70, "w"),
        ("Nama Barang", 180, "w"),
        ("Satuan", 50, "w"),
        ("SO_H-2", 70, "e"),    # SO Tanggal H-2
        ("SO_H-1", 70, "e"),    # SO Tanggal H-1
        ("In_H-1", 70, "e"),    # BARANG MASUK Tanggal H-1
        ("SO_H", 70, "e"),       # SO Tanggal H
        ("In_H", 70, "e"),       # BARANG MASUK Tanggal H
        ("Out_H", 70, "e"),      # OUT Tanggal H
        ("SO_H+1", 70, "e"),    # SO Tanggal H+1
        ("In_H+1", 70, "e"),    # BARANG MASUK Tanggal H+1
        ("SO_H+2", 70, "e"),    # SO Tanggal H+2
        ("Sistem", 80, "e"),     # SALDO AKHIR Tanggal H
        ("Deviasi", 80, "e"),    # SO_H - Sistem
        ("ABS", 80, "e"),        # abs(Deviasi)
        ("Rank", 50, "e"),       # rank per Nama Barang (by ABS, desc)
        ("Max Dev", 80, "e"),    # max(ABS) per Nama Barang
        ("Stok Seharusnya", 90, "e"),  # Sistem + In_H - Out_H
    ]

    def __init__(self, parent, satuan_mode: str = "GR"):
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None
        self.satuan_mode = satuan_mode  # "GR" or "PCS"
        self.tanggal_h = 25  # default H
        self._cached_pivot = None  # cache pivot result

        self._build_ui()
        self._setup_tags()
        if self.data is not None:
            self._refresh()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Filter bar ---
        filter_frame = ttk.LabelFrame(self, text="Filter")
        filter_frame.pack(fill=tk.X, pady=(0, 4))

        # Row 0: Resto, Nama Barang
        ttk.Label(filter_frame, text="NAMA RESTO:").grid(
            row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        self.resto_var = tk.StringVar(value="(All)")
        self.resto_combo = ttk.Combobox(
            filter_frame, textvariable=self.resto_var, state="readonly", width=15)
        self.resto_combo.grid(row=0, column=1, padx=(0, 12), pady=4)
        self.resto_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        ttk.Label(filter_frame, text="NAMA BARANG:").grid(
            row=0, column=2, padx=(0, 4), pady=4, sticky="w")
        self.barang_var = tk.StringVar(value="(All)")
        self.barang_combo = ttk.Combobox(
            filter_frame, textvariable=self.barang_var, state="readonly", width=25)
        self.barang_combo.grid(row=0, column=3, padx=(0, 12), pady=4)
        self.barang_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Row 1: Tanggal H, Reset
        ttk.Label(filter_frame, text="Tanggal H:").grid(
            row=1, column=0, padx=(8, 4), pady=4, sticky="w")
        self.tanggal_h_var = tk.StringVar(value=str(self.tanggal_h))
        tanggal_h_entry = ttk.Entry(filter_frame, textvariable=self.tanggal_h_var, width=8)
        tanggal_h_entry.grid(row=1, column=1, padx=(0, 12), pady=4, sticky="w")
        tanggal_h_entry.bind("<Return>", lambda e: self._on_tanggal_h_change())
        ttk.Button(filter_frame, text="Apply H", command=self._on_tanggal_h_change).grid(
            row=1, column=2, padx=4, pady=4, sticky="w")

        ttk.Button(filter_frame, text="Reset Filter", command=self._reset_filter).grid(
            row=1, column=3, padx=4, pady=4, sticky="w")

        # --- Treeview ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings", selectmode="browse")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50, anchor=anchor)
            # Dynamic heading: replace H with actual tanggal
            display = self._col_display_name(col_name)
            self.tree.heading(col_name, text=display,
                              command=lambda c=col_name: self._sort_by(c))

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # --- Hint + Status ---
        ttk.Label(
            self,
            text="💡 Double-click baris untuk melihat detail source data",
            font=("Segoe UI", 9, "italic"),
            foreground="#888",
        ).pack(anchor="w", pady=(2, 0))

        self.status_var = tk.StringVar(value="Belum ada data. Jalankan pipeline di tab Proses.")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", pady=(2, 0))

        # Bind double-click
        self.tree.bind("<Double-1>", self._on_double_click)

    def _setup_tags(self):
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        # Negative Deviasi → red font
        self.tree.tag_configure("negative", foreground="#CC0000")
        # Zero Deviasi → gray font
        self.tree.tag_configure("zero_dev", foreground="#999999")

    def _col_display_name(self, col_name: str) -> str:
        """Get display name for column, replacing H with actual tanggal."""
        for cid, name, _ in self.COLUMNS:
            if cid == col_name:
                # name is int (width), use col_name as display base
                # Replace H patterns in col_name with actual tanggal
                result = col_name
                if "H" in result:
                    result = result.replace("H", str(self.tanggal_h))
                return result
        return col_name

    def _update_headings(self):
        """Update column headings with current Tanggal H."""
        for col_name, _, _ in self.COLUMNS:
            display = self._col_display_name(col_name)
            self.tree.heading(col_name, text=display,
                              command=lambda c=col_name: self._sort_by(c))

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
        for col, combo in [("NAMA RESTO", self.resto_combo),
                           ("Nama Barang", self.barang_combo)]:
            if col in self.data.columns:
                values = ["(All)"] + sorted(
                    self.data[col].dropna().astype(str).unique().tolist())
                combo["values"] = values

    # =========================================================================
    # PIVOT COMPUTATION
    # =========================================================================
    def _compute_pivot(self) -> pd.DataFrame:
        """Compute wide matrix from Append1 long format.
        Returns DataFrame with 1 row per (Nama Barang, NAMA RESTO, SATUAN).
        """
        if self.data is None or self.data.empty:
            return pd.DataFrame()

        df = self.data
        h = self.tanggal_h

        # Filter to relevant JENIS + tanggal range (H-2 s/d H+2)
        tanggal_range = [h - 2, h - 1, h, h + 1, h + 2]
        relevant_jenis = ["1.SO", "2.SALDO AKHIR", "5.BARANG MASUK", "7.OUT"]

        # Ensure Tanggal is numeric
        df = df.copy()
        df["Tanggal_num"] = pd.to_numeric(df["Tanggal"], errors="coerce")
        df_filtered = df[
            (df["JENIS"].isin(relevant_jenis)) &
            (df["Tanggal_num"].isin(tanggal_range))
        ].copy()

        if df_filtered.empty:
            return pd.DataFrame()

        # Pivot: index = (Nama Barang, NAMA RESTO, SATUAN), columns = (JENIS, Tanggal)
        # Use pivot_table with multi-level columns
        try:
            pivot = df_filtered.pivot_table(
                index=["Nama Barang", "NAMA RESTO", "SATUAN"],
                columns=["JENIS", "Tanggal_num"],
                values="NILAI",
                aggfunc="sum",
                fill_value=0,
            )
        except Exception:
            return pd.DataFrame()

        if pivot.empty:
            return pd.DataFrame()

        # Flatten multi-level columns
        pivot = pivot.reset_index()

        # Build wide matrix columns
        def get_val(row, jenis, tgl):
            """Get value for (JENIS, Tanggal) from pivoted row."""
            col = (jenis, float(tgl))
            if col in row.index:
                val = row[col]
                if pd.isna(val):
                    return 0
                return float(val)
            return 0

        # Helper to safely extract scalar from row (handles Series if duplicate columns)
        def _scalar(val, default=""):
            if isinstance(val, pd.Series):
                val = val.iloc[0] if not val.empty else default
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return default
            return val

        # Build output rows
        output_rows = []
        for _, row in pivot.iterrows():
            nama_barang = str(_scalar(row.get("Nama Barang", "")))
            nama_resto = str(_scalar(row.get("NAMA RESTO", "")))
            satuan = str(_scalar(row.get("SATUAN", "")))

            so_h_minus_2 = get_val(row, "1.SO", h - 2)
            so_h_minus_1 = get_val(row, "1.SO", h - 1)
            in_h_minus_1 = get_val(row, "5.BARANG MASUK", h - 1)
            so_h = get_val(row, "1.SO", h)
            in_h = get_val(row, "5.BARANG MASUK", h)
            out_h = get_val(row, "7.OUT", h)
            so_h_plus_1 = get_val(row, "1.SO", h + 1)
            in_h_plus_1 = get_val(row, "5.BARANG MASUK", h + 1)
            so_h_plus_2 = get_val(row, "1.SO", h + 2)
            sistem = get_val(row, "2.SALDO AKHIR", h)

            deviasi = so_h - sistem
            abs_dev = abs(deviasi)
            stok_seharusnya = sistem + in_h - out_h

            output_rows.append({
                "Resto": nama_resto,
                "Nama Barang": nama_barang,
                "Satuan": satuan,
                "SO_H-2": so_h_minus_2,
                "SO_H-1": so_h_minus_1,
                "In_H-1": in_h_minus_1,
                "SO_H": so_h,
                "In_H": in_h,
                "Out_H": out_h,
                "SO_H+1": so_h_plus_1,
                "In_H+1": in_h_plus_1,
                "SO_H+2": so_h_plus_2,
                "Sistem": sistem,
                "Deviasi": deviasi,
                "ABS": abs_dev,
                "Stok Seharusnya": stok_seharusnya,
            })

        result = pd.DataFrame(output_rows)

        if result.empty:
            return result

        # Rank per Nama Barang (by ABS, descending — highest deviasi = rank 1)
        result["Rank"] = result.groupby("Nama Barang")["ABS"].rank(
            method="min", ascending=False).astype("Int64")

        # Max Deviasi per Nama Barang (max ABS across restos)
        result["Max Dev"] = result.groupby("Nama Barang")["ABS"].transform("max")

        return result

    # =========================================================================
    # RENDER
    # =========================================================================
    def _refresh(self):
        if self.data is None or self.data.empty:
            self.status_var.set("Belum ada data.")
            return

        # Compute pivot (cache by tanggal_h)
        if self._cached_pivot is None or self._cached_h != self.tanggal_h:
            self._cached_pivot = self._compute_pivot()
            self._cached_h = self.tanggal_h

        pivot_df = self._cached_pivot

        if pivot_df.empty:
            self.tree.delete(*self.tree.get_children())
            self.status_var.set("Tidak ada data.")
            return

        # Filter by Satuan mode
        if self.satuan_mode == "GR":
            filtered = pivot_df[pivot_df["Satuan"].astype(str).str.upper() == "GR"]
        else:  # PCS
            filtered = pivot_df[pivot_df["Satuan"].astype(str).str.upper() != "GR"]

        # Apply filters
        resto_val = self.resto_var.get()
        if resto_val and resto_val != "(All)":
            filtered = filtered[filtered["Resto"].astype(str) == resto_val]

        barang_val = self.barang_var.get()
        if barang_val and barang_val != "(All)":
            filtered = filtered[filtered["Nama Barang"].astype(str) == barang_val]

        # Clear tree
        self.tree.delete(*self.tree.get_children())

        if filtered.empty:
            self.status_var.set(f"Tidak ada data {'GR' if self.satuan_mode == 'GR' else 'PCS'} setelah filter.")
            return

        # Sort: by Nama Barang, then by ABS descending (highest deviasi first)
        filtered = filtered.sort_values(["Nama Barang", "ABS"], ascending=[True, False])

        # Render rows
        col_ids = [c[0] for c in self.COLUMNS]
        n = len(filtered)
        total_dev = 0

        for i, (_, row) in enumerate(filtered.iterrows()):
            values = []
            for col_id in col_ids:
                val = row.get(col_id, 0)
                if col_id in ("Rank",):
                    values.append(self._fmt_int(val))
                else:
                    values.append(self._fmt_num(val))

            # Tags
            tags = []
            deviasi = row.get("Deviasi", 0)
            if pd.notna(deviasi):
                if deviasi < 0:
                    tags.append("negative")
                elif deviasi == 0:
                    tags.append("zero_dev")
            tags.append("evenrow" if i % 2 == 0 else "oddrow")

            self.tree.insert("", "end", values=values, tags=tuple(tags))
            if pd.notna(deviasi):
                total_dev += abs(float(deviasi))

        # Update headings with current H
        self._update_headings()

        self.status_var.set(
            f"{n} rows ({self.satuan_mode}). Total ABS Deviasi: {self._fmt_num(total_dev)}. H={self.tanggal_h}"
        )

    def _on_tanggal_h_change(self):
        """Handle Tanggal H change from entry."""
        try:
            new_h = int(self.tanggal_h_var.get())
            if 1 <= new_h <= 31:
                self.tanggal_h = new_h
                self._cached_pivot = None  # invalidate cache
                self._refresh()
            else:
                tk.messagebox.showwarning("Invalid", "Tanggal H harus 1-31")
                self.tanggal_h_var.set(str(self.tanggal_h))
        except ValueError:
            tk.messagebox.showwarning("Invalid", "Tanggal H harus angka")
            self.tanggal_h_var.set(str(self.tanggal_h))

    def _reset_filter(self):
        self.resto_var.set("(All)")
        self.barang_var.set("(All)")
        self._refresh()

    def _sort_by(self, col: str):
        """Sort treeview by column."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            items.sort(key=lambda x: float(str(x[0]).replace(",", "").replace("(", "-").replace(")", "").replace("-", "0") or 0),
                       reverse=True)
        except (ValueError, AttributeError):
            items.sort(key=lambda x: str(x[0]), reverse=True)
        for i, (_, k) in enumerate(items):
            self.tree.move(k, "", i)

    # =========================================================================
    # DOUBLE-CLICK → POPUP
    # =========================================================================
    def _on_double_click(self, event):
        """Double-click row → show source data popup."""
        if self.data is None or self.data.empty:
            return

        row_iid = self.tree.identify_row(event.y)
        if not row_iid:
            return

        values = self.tree.item(row_iid, "values")
        if not values:
            return

        # Get Resto + Nama Barang from row
        col_ids = [c[0] for c in self.COLUMNS]
        row_data = dict(zip(col_ids, values))
        nama_barang = row_data.get("Nama Barang")
        nama_resto = row_data.get("Resto")

        if not nama_barang:
            return

        # Show popup with all source rows for this (Nama Barang, NAMA RESTO)
        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()

        # Build filters dict (include Resto if not All)
        active_filters = {}
        if nama_resto and nama_resto != "(All)":
            active_filters["NAMA RESTO"] = nama_resto

        show_details_popup(
            root, self.data,
            nama_barang=nama_barang,
            jenis=None,  # all JENIS
            tanggal=None,  # all Tanggal
            filters=active_filters,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _fmt_num(val) -> str:
        """Format number: thousand separators, 1 decimal, negative in parentheses."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val)
        if v == 0:
            return "-"
        if v == int(v):
            s = f"{v:,.0f}"
        else:
            s = f"{v:,.1f}"
        if v < 0:
            return f"({s[1:]})"
        return s

    @staticmethod
    def _fmt_int(val) -> str:
        """Format integer."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            return str(int(val))
        except (TypeError, ValueError):
            return str(val)
