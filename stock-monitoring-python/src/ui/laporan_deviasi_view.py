"""
laporan_deviasi_view.py — Long-format daily audit view (LAPORAN DEVIASI).

Inspired by the sample Excel sheet 'LAPORAN_DEVIASI' which provides a per-day
audit per (Resto, Nama Barang, Tanggal) with cumulative Saldo Kumulatif and
6-way Status Analisis Audit classification.

Features:
- 1 row per (Resto, Nama Barang, Tanggal)
- Columns: Tanggal, Resto, Nama Barang, Satuan, AKTIF/NON, SALDO AWAL,
           IN, OUT, BARANG KELUAR, SALDO AKHIR (Sistem), SO, DEVIASI,
           Saldo Kumulatif, Status Audit
- Status Audit 6-way classification:
    * OK (Matching)       — Deviasi = 0
    * OK (Dalam Cut-off) — |Deviasi| <= tolerance (small diff, considered OK)
    * DEVIASI MURNI       — |Deviasi| > tolerance, persists across days
    * VALID (Sistem Masuk) — SO > Sistem (system will catch up later)
    * CUT-OFF RESOLVED   — Deviasi was ≠ 0 on prev day, = 0 today
    * REVIEW             — default (needs manual check)
- Filter: Resto, Nama Barang, Status Audit, Tanggal range
- Sort: by |Deviasi| descending (biggest issues first)
- Double-click → popup source data
- Color coding per Status Audit
"""
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from typing import Optional


class LaporanDeviasiView(ttk.Frame):
    """Long-format daily audit view (LAPORAN DEVIASI)."""

    # Columns: (column_id, display_name, width, anchor)
    COLUMNS = [
        ("Tanggal", 60, "e"),
        ("Resto", 90, "w"),
        ("Nama Barang", 200, "w"),
        ("Satuan", 50, "w"),
        ("AKTIF/NON", 70, "w"),
        ("Saldo Awal", 80, "e"),
        ("IN", 80, "e"),
        ("OUT", 80, "e"),
        ("BK", 80, "e"),
        ("Sistem", 80, "e"),
        ("SO", 80, "e"),
        ("Deviasi", 80, "e"),
        ("Saldo Kumulatif", 100, "e"),
        ("Kontribusi %", 80, "e"),
        ("Status Audit", 130, "w"),
    ]

    # Tolerance for "Dalam Cut-off" (small deviation considered OK)
    CUT_OFF_TOLERANCE = 5.0

    def __init__(self, parent):
        super().__init__(parent)
        self.data: Optional[pd.DataFrame] = None
        self._cached_result = None
        self._cached_signature = None  # (data len, tanggal range)

        self._build_ui()
        self._setup_tags()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Filter bar ---
        filter_frame = ttk.LabelFrame(self, text="Filter")
        filter_frame.pack(fill=tk.X, pady=(0, 4))

        # Row 0: Resto, Nama Barang, Status Audit
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

        ttk.Label(filter_frame, text="STATUS AUDIT:").grid(
            row=0, column=4, padx=(0, 4), pady=4, sticky="w")
        self.status_var = tk.StringVar(value="(All)")
        self.status_combo = ttk.Combobox(
            filter_frame, textvariable=self.status_var, state="readonly", width=20)
        self.status_combo.grid(row=0, column=5, padx=(0, 12), pady=4)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        # Row 1: Tanggal range, Reset
        ttk.Label(filter_frame, text="TANGGAL:").grid(
            row=1, column=0, padx=(8, 4), pady=4, sticky="w")
        self.tgl_start_var = tk.StringVar(value="1")
        self.tgl_end_var = tk.StringVar(value="31")
        # FIX: bind <Return> on both entries + add validation message
        tgl_start_entry = ttk.Entry(filter_frame, textvariable=self.tgl_start_var, width=5)
        tgl_start_entry.grid(row=1, column=1, padx=(0, 2), pady=4, sticky="w")
        tgl_start_entry.bind("<Return>", lambda e: self._on_tanggal_change())
        ttk.Label(filter_frame, text="-").grid(row=1, column=1, padx=(35, 0))
        tgl_end_entry = ttk.Entry(filter_frame, textvariable=self.tgl_end_var, width=5)
        tgl_end_entry.grid(row=1, column=1, padx=(55, 12), pady=4, sticky="w")
        tgl_end_entry.bind("<Return>", lambda e: self._on_tanggal_change())
        ttk.Button(filter_frame, text="Apply", command=self._on_tanggal_change).grid(
            row=1, column=2, padx=4, pady=4, sticky="w")
        ttk.Button(filter_frame, text="Reset Filter", command=self._reset_filter).grid(
            row=1, column=3, padx=4, pady=4, sticky="w")

        # Row 2: Search box for Nama Barang (FIX: substring search)
        ttk.Label(filter_frame, text="CARI BARANG:").grid(
            row=2, column=0, padx=(8, 4), pady=4, sticky="w")
        self.search_var = tk.StringVar(value="")
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=2, column=1, columnspan=2, padx=(0, 12), pady=4, sticky="ew")
        # FIX: bind KeyRelease for live substring filter
        search_entry.bind("<KeyRelease>", lambda e: self._refresh())
        ttk.Label(filter_frame,
            text="(substring match — kosongkan untuk lihat semua)",
            font=("Segoe UI", 8, "italic"), foreground="#666"
        ).grid(row=2, column=3, columnspan=2, padx=4, pady=4, sticky="w")

        # --- Treeview ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings", selectmode="browse")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50, anchor=anchor)
            self.tree.heading(col_name, text=col_name,
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

        self.status_var_label = tk.StringVar(
            value="Belum ada data. Jalankan pipeline di tab Proses.")
        ttk.Label(self, textvariable=self.status_var_label).pack(anchor="w", pady=(2, 0))

        # Bind double-click
        self.tree.bind("<Double-1>", self._on_double_click)

    def _setup_tags(self):
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow", background="#F5F5F5")
        # Status Audit colors
        self.tree.tag_configure("ok_match", foreground="#006600")        # green
        self.tree.tag_configure("ok_cutoff", foreground="#666600")     # olive
        self.tree.tag_configure("deviasi_murni", foreground="#CC0000")  # red — needs attention
        self.tree.tag_configure("valid_sistem", foreground="#0066CC")  # blue
        self.tree.tag_configure("cutoff_resolved", foreground="#009933")  # green-ish
        self.tree.tag_configure("review", foreground="#CC6600")        # orange
        # Negative Deviasi
        self.tree.tag_configure("negative", foreground="#CC0000")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        self._cached_result = None  # FIX: invalidate cache on new data
        self._cached_signature = None
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
        # Status filter is computed — populate after refresh
        self.status_combo["values"] = [
            "(All)",
            "OK (Matching)",
            "OK (Dalam Cut-off)",
            "DEVIASI MURNI",
            "VALID (Sistem Masuk)",
            "CUT-OFF RESOLVED",
            "REVIEW",
        ]

    # =========================================================================
    # COMPUTATION
    # =========================================================================
    def _compute_audit(self) -> pd.DataFrame:
        """Build long-format daily audit from Append1 long format.

        Returns DataFrame with 1 row per (Tanggal, Resto, Nama Barang).
        """
        if self.data is None or self.data.empty:
            return pd.DataFrame()

        df = self.data

        # Required columns
        required_jenis = [
            "SALDO AWAL", "1.SO", "2.SALDO AKHIR", "4.IN",
            "9.OUT", "8.BARANG KELUAR",
        ]
        df_filtered = df[df["JENIS"].isin(required_jenis)].copy()
        if df_filtered.empty:
            return pd.DataFrame()

        # Ensure Tanggal is numeric
        df_filtered["Tanggal_num"] = pd.to_numeric(
            df_filtered["Tanggal"], errors="coerce")
        df_filtered = df_filtered.dropna(subset=["Tanggal_num"])
        df_filtered["Tanggal_num"] = df_filtered["Tanggal_num"].astype("Int64")

        # Pivot: index = (Tanggal, NAMA RESTO, Nama Barang), columns = JENIS, values = NILAI
        try:
            pivot = df_filtered.pivot_table(
                index=["Tanggal_num", "NAMA RESTO", "Nama Barang"],
                columns="JENIS",
                values="NILAI",
                aggfunc="sum",
                fill_value=0,
            )
        except Exception:
            return pd.DataFrame()

        if pivot.empty:
            return pd.DataFrame()

        pivot = pivot.reset_index()
        pivot.columns.name = None

        # Build AKTIF/NON lookup (per Nama Barang from DBS Kategori)
        aktif_lookup = {}
        if "AKTIF/NON" in df.columns and "Nama Barang" in df.columns:
            aktif_df = (
                df[["Nama Barang", "AKTIF/NON"]]
                .dropna(subset=["AKTIF/NON"])
                .drop_duplicates(subset=["Nama Barang"], keep="first")
            )
            aktif_lookup = dict(zip(
                aktif_df["Nama Barang"].astype(str),
                aktif_df["AKTIF/NON"].astype(str)
            ))

        # Build SATUAN lookup (per Nama Barang + Resto)
        satuan_lookup = {}
        if "SATUAN" in df.columns and "Nama Barang" in df.columns:
            satuan_df = (
                df[["Nama Barang", "NAMA RESTO", "SATUAN"]]
                .dropna(subset=["SATUAN"])
                .drop_duplicates(subset=["Nama Barang", "NAMA RESTO"], keep="first")
            )
            satuan_lookup = {
                (r["Nama Barang"], r["NAMA RESTO"]): r["SATUAN"]
                for _, r in satuan_df.iterrows()
            }

        # Helper to safely get a column (default to 0 if not present)
        def gcol(df_, name):
            return df_[name] if name in df_.columns else pd.Series(0, index=df_.index)

        # Compute metrics
        saldo_awal = gcol(pivot, "SALDO AWAL").fillna(0)
        so = gcol(pivot, "1.SO").fillna(0)
        sistem = gcol(pivot, "2.SALDO AKHIR").fillna(0)
        in_val = gcol(pivot, "4.IN").fillna(0)
        out_val = gcol(pivot, "9.OUT").fillna(0)
        bk = gcol(pivot, "8.BARANG KELUAR").fillna(0)

        deviasi = so - sistem

        # Build output rows
        result = pd.DataFrame({
            "Tanggal": pivot["Tanggal_num"],
            "Resto": pivot["NAMA RESTO"].astype(str),
            "Nama Barang": pivot["Nama Barang"].astype(str),
            "Satuan": [satuan_lookup.get((nb, nr), "")
                       for nb, nr in zip(pivot["Nama Barang"].astype(str),
                                          pivot["NAMA RESTO"].astype(str))],
            "AKTIF/NON": [aktif_lookup.get(nb, "")
                          for nb in pivot["Nama Barang"].astype(str)],
            "Saldo Awal": saldo_awal,
            "IN": in_val,
            "OUT": out_val,
            "BK": bk,
            "Sistem": sistem,
            "SO": so,
            "Deviasi": deviasi,
        })

        # Saldo Kumulatif: running balance per (Resto, Nama Barang) sorted by Tanggal
        result = result.sort_values(["Resto", "Nama Barang", "Tanggal"]).reset_index(drop=True)
        result["Saldo Kumulatif"] = result.groupby(["Resto", "Nama Barang"])["SO"].cumsum()

        # Status Audit 6-way classification
        result["Status Audit"] = result.apply(self._classify_status, axis=1)

        # Need previous-day Deviasi for CUT-OFF RESOLVED detection
        # Group by (Resto, Nama Barang), shift Deviasi
        result["_prev_deviasi"] = result.groupby(
            ["Resto", "Nama Barang"])["Deviasi"].shift(1).fillna(0)

        # Re-classify with prev deviasi info (for CUT-OFF RESOLVED)
        result["Status Audit"] = result.apply(self._classify_status_v2, axis=1)
        result = result.drop(columns=["_prev_deviasi"])

        # Kontribusi % (per item's |Deviasi| / total |Deviasi|)
        total_abs_dev = result["Deviasi"].abs().sum()
        if total_abs_dev > 0:
            result["Kontribusi %"] = (result["Deviasi"].abs() / total_abs_dev * 100).round(2)
        else:
            result["Kontribusi %"] = 0.0

        return result.sort_values("Tanggal").reset_index(drop=True)

    def _classify_status(self, row) -> str:
        """First-pass classification (without prev-day info)."""
        deviasi = row["Deviasi"]
        so = row["SO"]
        sistem = row["Sistem"]

        if deviasi == 0:
            return "OK (Matching)"
        if abs(deviasi) <= self.CUT_OFF_TOLERANCE:
            return "OK (Dalam Cut-off)"
        if so > sistem:
            return "VALID (Sistem Masuk)"
        if abs(deviasi) > self.CUT_OFF_TOLERANCE:
            return "DEVIASI MURNI"
        return "REVIEW"

    def _classify_status_v2(self, row) -> str:
        """Second-pass classification (with prev-day Deviasi for cut-off detection)."""
        deviasi = row["Deviasi"]
        prev_deviasi = row["_prev_deviasi"]
        so = row["SO"]
        sistem = row["Sistem"]

        # CUT-OFF RESOLVED: prev day had deviation, today is OK (within tolerance)
        if abs(prev_deviasi) > self.CUT_OFF_TOLERANCE and abs(deviasi) <= self.CUT_OFF_TOLERANCE:
            return "CUT-OFF RESOLVED"

        if deviasi == 0:
            return "OK (Matching)"
        if abs(deviasi) <= self.CUT_OFF_TOLERANCE:
            return "OK (Dalam Cut-off)"
        if so > sistem:
            return "VALID (Sistem Masuk)"
        if abs(deviasi) > self.CUT_OFF_TOLERANCE:
            return "DEVIASI MURNI"
        return "REVIEW"

    # =========================================================================
    # RENDER
    # =========================================================================
    def _refresh(self):
        if self.data is None or self.data.empty:
            self.status_var_label.set("Belum ada data. Jalankan pipeline di tab Proses.")
            return

        # Compute (cache by signature)
        try:
            tgl_start = int(self.tgl_start_var.get())
            tgl_end = int(self.tgl_end_var.get())
        except ValueError:
            # FIX: validation message instead of silent popup
            self.status_var_label.set("Tanggal harus angka. Contoh: 1-31.")
            return

        # FIX: validate range
        if tgl_start < 1 or tgl_end < 1 or tgl_start > tgl_end:
            self.status_var_label.set("Range tanggal tidak valid. Contoh: 1-31.")
            return

        sig = (len(self.data), tgl_start, tgl_end)
        if self._cached_result is None or self._cached_signature != sig:
            self._cached_result = self._compute_audit()
            self._cached_signature = sig

        result = self._cached_result
        if result.empty:
            self.tree.delete(*self.tree.get_children())
            self.status_var_label.set("Tidak ada data.")
            return

        # Apply filters
        filtered = result[
            (result["Tanggal"] >= tgl_start) & (result["Tanggal"] <= tgl_end)
        ].copy()

        resto_val = self.resto_var.get()
        if resto_val and resto_val != "(All)":
            filtered = filtered[filtered["Resto"].astype(str) == resto_val]

        barang_val = self.barang_var.get()
        if barang_val and barang_val != "(All)":
            filtered = filtered[filtered["Nama Barang"].astype(str) == barang_val]

        # FIX: apply substring search (case-insensitive)
        search_val = self.search_var.get().strip().lower()
        if search_val:
            filtered = filtered[
                filtered["Nama Barang"].astype(str).str.lower().str.contains(search_val, regex=False)
            ]

        status_val = self.status_var.get()
        if status_val and status_val != "(All)":
            filtered = filtered[filtered["Status Audit"].astype(str) == status_val]

        # Clear tree
        self.tree.delete(*self.tree.get_children())

        if filtered.empty:
            # FIX: actionable empty state
            self.status_var_label.set(
                "Tidak ada data setelah filter. Klik 'Reset Filter' atau ubah filter."
            )
            return

        # Sort by |Deviasi| descending (biggest issues first)
        # FIX: use .assign() functional style to avoid SettingWithCopyWarning
        # (filtered is a slice of result; assigning a column to a slice triggers warning)
        filtered = (
            filtered
            .assign(_abs_dev=filtered["Deviasi"].abs())
            .sort_values("_abs_dev", ascending=False)
            .drop(columns=["_abs_dev"])
        )

        # Render rows
        col_ids = [c[0] for c in self.COLUMNS]
        n = len(filtered)
        total_dev = filtered["Deviasi"].abs().sum()

        # Status distribution stats
        status_counts = filtered["Status Audit"].value_counts().to_dict()

        for i, (_, row) in enumerate(filtered.iterrows()):
            values = []
            for col_id in col_ids:
                val = row.get(col_id, 0)
                if col_id in ("Tanggal",):
                    values.append(self._fmt_int(val))
                elif col_id == "Kontribusi %":
                    values.append(self._fmt_pct(val))
                else:
                    values.append(self._fmt_num(val))

            # Tags
            tags = []
            deviasi = row.get("Deviasi", 0)
            if pd.notna(deviasi) and deviasi < 0:
                tags.append("negative")
            status_aud = str(row.get("Status Audit", "") or "").strip()
            if status_aud == "OK (Matching)":
                tags.append("ok_match")
            elif status_aud == "OK (Dalam Cut-off)":
                tags.append("ok_cutoff")
            elif status_aud == "DEVIASI MURNI":
                tags.append("deviasi_murni")
            elif status_aud == "VALID (Sistem Masuk)":
                tags.append("valid_sistem")
            elif status_aud == "CUT-OFF RESOLVED":
                tags.append("cutoff_resolved")
            elif status_aud == "REVIEW":
                tags.append("review")
            tags.append("evenrow" if i % 2 == 0 else "oddrow")

            self.tree.insert("", "end", values=values, tags=tuple(tags))

        # Status summary
        summary = " | ".join(f"{k}: {v}" for k, v in sorted(status_counts.items()))
        self.status_var_label.set(
            f"{n} rows. Total |Deviasi|: {self._fmt_num(total_dev)}. Status: {summary}"
        )

    def _reset_filter(self):
        self.resto_var.set("(All)")
        self.barang_var.set("(All)")
        self.status_var.set("(All)")
        self.tgl_start_var.set("1")
        self.tgl_end_var.set("31")
        self.search_var.set("")  # FIX: reset search box too
        self._refresh()

    def _on_tanggal_change(self):
        """FIX: handle Apply button / Return key — validate then refresh."""
        try:
            int(self.tgl_start_var.get())
            int(self.tgl_end_var.get())
            self._refresh()
        except ValueError:
            self.status_var_label.set("Tanggal harus angka. Contoh: 1-31.")

    def _sort_by(self, col: str):
        """Sort treeview by column (handles accounting-style negatives)."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            def parse_val(s):
                s = str(s).replace(",", "").replace("%", "").strip()
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
        if self.data is None or self.data.empty:
            return

        row_iid = self.tree.identify_row(event.y)
        if not row_iid:
            return

        values = self.tree.item(row_iid, "values")
        if not values:
            return

        col_ids = [c[0] for c in self.COLUMNS]
        row_data = dict(zip(col_ids, values))
        nama_barang = row_data.get("Nama Barang")
        nama_resto = row_data.get("Resto")
        tgl_str = row_data.get("Tanggal")
        if not nama_barang:
            return

        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()

        active_filters = {}
        if nama_resto and nama_resto != "(All)":
            active_filters["NAMA RESTO"] = nama_resto

        try:
            tgl_int = int(float(tgl_str)) if tgl_str else None
        except (ValueError, TypeError):
            tgl_int = None

        show_details_popup(
            root, self.data,
            nama_barang=nama_barang,
            jenis=None,
            tanggal=tgl_int,
            filters=active_filters,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================
    @staticmethod
    def _fmt_num(val) -> str:
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
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            return str(int(val))
        except (TypeError, ValueError):
            return str(val)

    @staticmethod
    def _fmt_pct(val) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "-"
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val)
        if v == 0:
            return "-"
        return f"{v:.2f}%"
