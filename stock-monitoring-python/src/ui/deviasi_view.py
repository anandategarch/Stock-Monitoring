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
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from typing import Optional


class DeviasiView(ttk.Frame):
    """Wide matrix view untuk DEVIASI GR/PCS.

    satuan_mode: "GR" → tampilkan hanya SATUAN=GR
                 "PCS" → tampilkan SATUAN selain GR (PCS, BOTOL, dll)
    """

    # Columns: (column_id, display_name, width, anchor)
    # Display names use H±N pattern → actual date computed dynamically
    COLUMNS = [
        ("Resto", 70, "w"),
        ("Nama Barang", 180, "w"),
        ("Satuan", 50, "w"),
        ("AKTIF/NON", 70, "w"),
        ("SO_H-2", 70, "e"),
        ("SO_H-1", 70, "e"),
        ("In_H-1", 70, "e"),
        ("SO_H", 70, "e"),
        ("In_H", 70, "e"),
        ("Out_H", 70, "e"),      # OUT Tanggal H (22.05 sales)
        ("BK_H", 70, "e"),       # BARANG KELUAR Tanggal H (42.15 Kirim)
        ("SO_H+1", 70, "e"),
        ("In_H+1", 70, "e"),
        ("SO_H+2", 70, "e"),
        ("Sistem", 80, "e"),
        ("Deviasi", 80, "e"),
        ("Rank", 50, "e"),
        ("CEK", 120, "w"),
    ]

    # Threshold for Hitung Manual condition (mirrors $Y$1 in Excel = 1.3 = 130%)
    CEK_THRESHOLD = 1.3

    def __init__(self, parent, satuan_mode: str = "GR"):
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None
        self.satuan_mode = satuan_mode  # "GR" or "PCS"
        self.tanggal_h = 25  # default H
        self._cached_pivot = None  # cache pivot result
        self._cached_h = None  # FIX: track tanggal_h used for cache (was missing)
        self._aktif_lookup = {}  # FIX: AKTIF/NON lookup by Nama Barang (lost in pivot_table)

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

        # Row 2: Search box for Nama Barang (FIX: substring search)
        ttk.Label(filter_frame, text="CARI BARANG:").grid(
            row=2, column=0, padx=(8, 4), pady=4, sticky="w")
        self.search_var = tk.StringVar(value="")
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=2, column=1, columnspan=3, padx=(0, 12), pady=4, sticky="ew")
        # FIX: bind KeyRelease for live substring filter
        search_entry.bind("<KeyRelease>", lambda e: self._refresh())
        ttk.Label(filter_frame,
            text="(substring match — kosongkan untuk lihat semua)",
            font=("Segoe UI", 8, "italic"), foreground="#666"
        ).grid(row=2, column=4, padx=4, pady=4, sticky="w")

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
        # FIX: contrast #888 → #666 (WCAG AA)
        ttk.Label(
            self,
            text="Double-click baris untuk melihat detail source data",
            font=("Segoe UI", 9, "italic"),
            foreground="#666",
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
        # FIX: contrast #999999 → #777777 (WCAG AA)
        self.tree.tag_configure("zero_dev", foreground="#777777")
        # CEK categories — color-coded for quick visual scan
        self.tree.tag_configure("cek_kosong", foreground="#996633")       # brown — Kosong/Non Aktif
        self.tree.tag_configure("cek_tanggal", foreground="#0066CC")       # blue — Beda Tanggal
        self.tree.tag_configure("cek_manual", foreground="#CC6600")       # orange — Hitung Manual
        self.tree.tag_configure("cek_drastis", foreground="#CC0000")       # red — Turun Drastis
        self.tree.tag_configure("cek_acr", foreground="#660099")            # purple — ACR to BOM

    @staticmethod
    def _compute_cek(aktif_non, so_h, so_h_prev, in_h, out_h,
                     stok_seharusnya, threshold=1.3):
        """Port Excel LET formula (4 of 5 conditions — ACR condition needs BOM, TODO).

        Priority: KondisiKosong → KondisiNaikturun → KondisiHitungManual →
                  KondisiTurunDrastis. (KondisiACR skipped — needs Dev to BOM%.)

        Returns: anomaly category string ("Kosong/Non Aktif", "Beda Tanggal",
                 "Hitung Manual", "Turun Drastis", or "" = no anomaly).
        """
        aktif = str(aktif_non or "").strip().upper()

        # 1. KondisiKosong → "Kosong/Non Aktif"
        if aktif == "AKTIF" and so_h < 0:
            return "Kosong/Non Aktif"
        if aktif == "NON AKTIF" and so_h > 0:
            return "Kosong/Non Aktif"

        # 2. KondisiNaikturun → "Beda Tanggal"
        #    a) ada barang masuk (In>0), SO turun (H<F), tidak ada OUT (J=0)
        if in_h > 0 and so_h < so_h_prev and out_h == 0:
            return "Beda Tanggal"
        #    b) SO naik >50% dari kemarin, tanpa In & Out
        if so_h_prev > 0:
            if so_h > so_h_prev + (0.5 * so_h_prev) and in_h == 0 and out_h == 0:
                return "Beda Tanggal"

        # 3. KondisiHitungManual → "Hitung Manual"
        #    FIX: restructure dead-code branch — old code had unreachable inner
        #    `if so_h != 0 and stok_seharusnya == 0` inside `if stok_seharusnya != 0`
        #    New logic: handle stok_seharusnya == 0 case FIRST (top-level), then ratio.
        if stok_seharusnya == 0:
            # System reckons 0 but SO says non-zero → manual count suspected
            if so_h != 0:
                return "Hitung Manual"
        else:
            # Stok seharusnya non-zero — check ratio
            ratio = abs(so_h - stok_seharusnya) / abs(stok_seharusnya)
            if ratio > threshold:
                return "Hitung Manual"

        # 4. KondisiTurunDrastis → "Turun Drastis"
        if so_h_prev > 0 and (so_h / so_h_prev) < 0.5:
            return "Turun Drastis"

        # 5. KondisiACR → "ACR to BOM" (SKIPPED — needs Dev to BOM%)
        # TODO: add when BOM data from 22.05 is available

        return ""

    def _col_display_name(self, col_name: str) -> str:
        """Get display name: parse H±N pattern and compute actual date.

        Example: 'SO_H-1' with tanggal_h=3 → 'SO_2' (not 'SO_3-1').
                 'In_H+1' with tanggal_h=3 → 'In_4'.
        """
        import re
        h = self.tanggal_h
        m = re.match(r"^(.*)_H([+-]\d+)?$", col_name)
        if m:
            prefix = m.group(1)
            offset_str = m.group(2)
            offset = int(offset_str) if offset_str else 0
            date = h + offset
            return f"{prefix}_{date}"
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
        """Load new data from pipeline. FIX: invalidate cached pivot so stale
        data isn't served after a re-run with the same tanggal_h."""
        self.data = data
        self._cached_pivot = None  # FIX: invalidate cache (was missing → stale data)
        self._cached_h = None
        self._aktif_lookup = {}
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
        # FIX: use new numbering 9.OUT (was 7.OUT after OUT/BK split)
        relevant_jenis = ["1.SO", "2.SALDO AKHIR", "4.IN", "9.OUT", "8.BARANG KELUAR"]

        # Ensure Tanggal is numeric
        df = df.copy()
        df["Tanggal_num"] = pd.to_numeric(df["Tanggal"], errors="coerce")
        df_filtered = df[
            (df["JENIS"].isin(relevant_jenis)) &
            (df["Tanggal_num"].isin(tanggal_range))
        ].copy()

        # FIX: Build AKTIF/NON lookup BEFORE pivot_table (which drops string cols)
        # AKTIF/NON is per Nama Barang (from DBS Kategori merge in append1.py)
        if "AKTIF/NON" in df.columns and "Nama Barang" in df.columns:
            aktif_df = (
                df[["Nama Barang", "AKTIF/NON"]]
                .dropna(subset=["AKTIF/NON"])
                .drop_duplicates(subset=["Nama Barang"], keep="first")
            )
            self._aktif_lookup = dict(zip(
                aktif_df["Nama Barang"].astype(str),
                aktif_df["AKTIF/NON"].astype(str)
            ))
        else:
            self._aktif_lookup = {}

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
            # FIX: AKTIF/NON is dropped by pivot_table (aggfunc=sum on string col)
            # Use lookup dict built before pivot
            aktif_non = str(self._aktif_lookup.get(nama_barang, ""))

            so_h_minus_2 = get_val(row, "1.SO", h - 2)
            so_h_minus_1 = get_val(row, "1.SO", h - 1)
            in_h_minus_1 = get_val(row, "4.IN", h - 1)
            so_h = get_val(row, "1.SO", h)
            in_h = get_val(row, "4.IN", h)
            # FIX: use new numbering 9.OUT (was 7.OUT)
            out_h = get_val(row, "9.OUT", h)
            bk_h = get_val(row, "8.BARANG KELUAR", h)
            so_h_plus_1 = get_val(row, "1.SO", h + 1)
            in_h_plus_1 = get_val(row, "4.IN", h + 1)
            so_h_plus_2 = get_val(row, "1.SO", h + 2)
            sistem = get_val(row, "2.SALDO AKHIR", h)

            deviasi = so_h - sistem
            # Stok Seharusnya (used internally for CEK formula only — not displayed)
            stok_seharusnya = sistem + in_h - out_h - bk_h

            # CEK formula (ported from Excel LET formula — 4 of 5 conditions)
            # ACR condition (KondisiACR) skipped — needs BOM data from 22.05 (TODO)
            cek = self._compute_cek(
                aktif_non, so_h, so_h_minus_1, in_h, out_h,
                stok_seharusnya, self.CEK_THRESHOLD
            )

            output_rows.append({
                "Resto": nama_resto,
                "Nama Barang": nama_barang,
                "Satuan": satuan,
                "AKTIF/NON": aktif_non,
                "SO_H-2": so_h_minus_2,
                "SO_H-1": so_h_minus_1,
                "In_H-1": in_h_minus_1,
                "SO_H": so_h,
                "In_H": in_h,
                "Out_H": out_h,
                "BK_H": bk_h,
                "SO_H+1": so_h_plus_1,
                "In_H+1": in_h_plus_1,
                "SO_H+2": so_h_plus_2,
                "Sistem": sistem,
                "Deviasi": deviasi,
                "_ABS": abs(deviasi),  # internal — for Rank only, not displayed
                "CEK": cek,
            })

        result = pd.DataFrame(output_rows)

        if result.empty:
            return result

        # Rank per Nama Barang (by |Deviasi|, descending — highest deviasi = rank 1)
        result["Rank"] = result.groupby("Nama Barang")["_ABS"].rank(
            method="min", ascending=False).astype("Int64")

        # Drop internal helper column before returning
        result = result.drop(columns=["_ABS"])

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

        # Sort: by Nama Barang, then by |Deviasi| descending (highest deviasi first)
        filtered["_abs_dev"] = filtered["Deviasi"].abs()
        filtered = filtered.sort_values(["Nama Barang", "_abs_dev"], ascending=[True, False])
        filtered = filtered.drop(columns=["_abs_dev"])

        # Render rows
        col_ids = [c[0] for c in self.COLUMNS]
        n = len(filtered)
        total_dev = 0.0

        for i, (_, row) in enumerate(filtered.iterrows()):
            values = []
            for col_id in col_ids:
                val = row.get(col_id, 0)
                if col_id == "Rank":
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
            # CEK color tag
            cek_val = str(row.get("CEK", "") or "").strip()
            if cek_val == "Kosong/Non Aktif":
                tags.append("cek_kosong")
            elif cek_val == "Beda Tanggal":
                tags.append("cek_tanggal")
            elif cek_val == "Hitung Manual":
                tags.append("cek_manual")
            elif cek_val == "Turun Drastis":
                tags.append("cek_drastis")
            elif cek_val == "ACR to BOM":
                tags.append("cek_acr")
            tags.append("evenrow" if i % 2 == 0 else "oddrow")

            self.tree.insert("", "end", values=values, tags=tuple(tags))
            if pd.notna(deviasi):
                total_dev += abs(float(deviasi))

        # Update headings with current H
        self._update_headings()

        self.status_var.set(
            f"{n} rows ({self.satuan_mode}). Total |Deviasi|: {self._fmt_num(total_dev)}. H={self.tanggal_h}"
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
                messagebox.showwarning("Invalid", "Tanggal H harus 1-31", parent=self.winfo_toplevel())
                self.tanggal_h_var.set(str(self.tanggal_h))
        except ValueError:
            messagebox.showwarning("Invalid", "Tanggal H harus angka", parent=self.winfo_toplevel())
            self.tanggal_h_var.set(str(self.tanggal_h))

    def _reset_filter(self):
        self.resto_var.set("(All)")
        self.barang_var.set("(All)")
        self._refresh()

    def _sort_by(self, col: str):
        """Sort treeview by column (handles accounting-style negatives in parentheses)."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            def parse_val(s):
                s = str(s).replace(",", "").strip()
                if s == "-" or s == "":
                    return 0
                if s.startswith("(") and s.endswith(")"):
                    return -float(s[1:-1])
                return float(s)
            items.sort(key=lambda x: parse_val(x[0]), reverse=True)
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
