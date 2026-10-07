"""
laporan_deviasi_view.py — Long-format daily audit view (v3.1).

Audit harian per (Resto, Nama Barang, Tanggal) + klasifikasi 6-way Status
Audit — logika komputasi 100% identik versi lama.

Fitur v3.1:
- Filter Nama Barang menempel di header kolom (corong, Excel-like) —
  search box lama DIHAPUS
- Tombol ⛶ Perbesar: buka tabel fullscreen
- Loading overlay + compute/render async (UI tidak membeku)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from typing import Optional, Callable

from .theme import (
    C_ACCENT, C_BG, C_CARD, C_BORDER, C_HEADER, C_TEXT_MUTED,
    C_GREEN, C_AMBER, C_RED, C_BLUE, C_ORANGE,
    font,
)
from .widgets import (
    Card, EmptyState, GhostButton, HeaderFilter, KpiCard, KpiRow,
    LoadingOverlay, add_tooltip, insert_tree_items, open_tree_maximized,
    run_async,
)

# 6 Status Audit: (nama, warna aksen) — dipakai KPI + pewarnaan baris
_STATUS_DEFS = [
    ("OK (Matching)", C_GREEN, "ok_match"),
    ("OK (Dalam Cut-off)", "#65a30d", "ok_cutoff"),
    ("DEVIASI MURNI", C_RED, "deviasi_murni"),
    ("VALID (Sistem Masuk)", C_BLUE, "valid_sistem"),
    ("CUT-OFF RESOLVED", "#059669", "cutoff_resolved"),
    ("REVIEW", C_ORANGE, "review"),
]


class _StatusKpi(tk.Frame):
    """Kartu KPI status yang bisa diklik untuk toggle filter status."""

    def __init__(self, parent, label: str, accent: str, on_click, **kw):
        super().__init__(parent, bg=C_CARD, highlightbackground=C_BORDER,
                         highlightthickness=1, cursor="hand2", **kw)
        self._accent = accent
        self._on_click = on_click
        self._active = False

        row = tk.Frame(self, bg=C_CARD)
        row.pack(fill="both", expand=True, padx=10, pady=8)
        bar = tk.Frame(row, bg=accent, width=4)
        bar.pack(side="left", fill="y", padx=(0, 8))
        txt = tk.Frame(row, bg=C_CARD)
        txt.pack(side="left", fill="both", expand=True)

        tk.Label(txt, text=label.upper(), bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(7, "bold"), anchor="w", wraplength=120,
                 justify="left").pack(fill="x")
        self._value_var = tk.StringVar(value="0")
        tk.Label(txt, textvariable=self._value_var, bg=C_CARD, fg=C_HEADER,
                 font=font(15, "bold"), anchor="w").pack(fill="x", pady=(2, 0))

        for w in (self, row, txt):
            w.bind("<Button-1>", lambda e: self._click())
        self._bar = bar

    def _click(self):
        if self._on_click:
            self._on_click()

    def set_value(self, value: str):
        self._value_var.set(value)

    def set_active(self, active: bool):
        self._active = active
        self.configure(
            highlightbackground=C_ACCENT if active else C_BORDER,
            highlightthickness=2 if active else 1,
            bg="#f0fdfa" if active else C_CARD)
        # re-style children bg
        for child in self.winfo_children():
            try:
                child.configure(bg="#f0fdfa" if active else C_CARD)
                for sub in child.winfo_children():
                    sub.configure(bg="#f0fdfa" if active else C_CARD)
                    for sub2 in sub.winfo_children():
                        if sub2.winfo_class() == "Frame":
                            continue
                        sub2.configure(
                            bg="#f0fdfa" if active else C_CARD)
            except tk.TclError:
                pass


class LaporanDeviasiView(tk.Frame):
    """Long-format daily audit view (LAPORAN DEVIASI) — tampilan baru."""

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

    CUT_OFF_TOLERANCE = 5.0

    def __init__(self, parent, go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self._cached_result = None
        self._cached_signature = None
        self.go_to_proses = go_to_proses
        self._status_kpis: dict[str, _StatusKpi] = {}
        self._name_selected: set | None = None
        self._busy = False
        self._pending = False

        self._build_ui()
        self._setup_tags()
        self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="📋", title="Belum ada Laporan Deviasi",
            subtitle="Jalankan pipeline untuk memuat audit harian per "
                     "(Resto × Barang × Tanggal) dengan 6-way Status Audit.",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # 6 KPI status — klik untuk filter
        intro = tk.Frame(self.content, bg=C_BG)
        intro.pack(fill="x", padx=12, pady=(12, 4))
        tk.Label(intro, text="Distribusi Status Audit — klik kartu untuk "
                             "memfilter status",
                 bg=C_BG, fg=C_TEXT_MUTED, font=font(9)).pack(side="left")

        kpi_wrap = tk.Frame(self.content, bg=C_BG)
        kpi_wrap.pack(fill="x", padx=12)
        for i, (label, accent, _) in enumerate(_STATUS_DEFS):
            kpi = _StatusKpi(kpi_wrap, label, accent,
                             on_click=lambda l=label: self._toggle_status(l))
            kpi.grid(row=0, column=i, sticky="nsew",
                     padx=(0 if i == 0 else 6, 0))
            kpi_wrap.grid_columnconfigure(i, weight=1)
            add_tooltip(kpi, f"Klik: tampilkan hanya baris '{label}'.\n"
                             "Klik lagi untuk melepas filter.")
            self._status_kpis[label] = kpi

        # --- Filter card ---
        fcard = Card(self.content, title="Filter",
                     subtitle="Sort default: |Deviasi| terbesar dulu. Filter "
                              "Nama Barang → klik header kolom (ikon corong ⧩) "
                              "di tabel.")
        fcard.pack(fill="x", padx=12, pady=(10, 0))
        fbody = fcard.body()

        r0 = tk.Frame(fbody, bg=C_CARD)
        r0.pack(fill="x", pady=(0, 6))
        tk.Label(r0, text="RESTO", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.resto_var = tk.StringVar(value="(All)")
        self.resto_combo = ttk.Combobox(r0, textvariable=self.resto_var,
                                        state="readonly", width=16)
        self.resto_combo.pack(side="left", padx=(6, 18))
        self.resto_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Label(r0, text="STATUS", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.status_var = tk.StringVar(value="(All)")
        self.status_combo = ttk.Combobox(r0, textvariable=self.status_var,
                                         state="readonly", width=22)
        self.status_combo.pack(side="left", padx=(6, 0))
        self.status_combo.bind("<<ComboboxSelected>>",
                               lambda e: self._sync_kpi_selection())

        r1 = tk.Frame(fbody, bg=C_CARD)
        r1.pack(fill="x")
        tk.Label(r1, text="TANGGAL", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.tgl_start_var = tk.StringVar(value="1")
        tgl_start_entry = ttk.Entry(r1, textvariable=self.tgl_start_var, width=5)
        tgl_start_entry.pack(side="left", padx=(6, 2))
        tgl_start_entry.bind("<Return>", lambda e: self._on_tanggal_change())
        tk.Label(r1, text="–", bg=C_CARD, fg=C_TEXT_MUTED).pack(side="left")
        self.tgl_end_var = tk.StringVar(value="31")
        tgl_end_entry = ttk.Entry(r1, textvariable=self.tgl_end_var, width=5)
        tgl_end_entry.pack(side="left", padx=(2, 8))
        tgl_end_entry.bind("<Return>", lambda e: self._on_tanggal_change())
        add_tooltip(tgl_start_entry, "Rentang tanggal (1-31). Enter/Apply untuk "
                                     "terapkan.")
        GhostButton(r1, text="Apply", command=self._on_tanggal_change).pack(
            side="left", padx=(0, 18))

        GhostButton(r1, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left")

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(8, 0))
        tbody = tcard.body()

        # Header tabel: judul + tombol perbesar
        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        tk.Label(head, text="Audit Harian — 6 Status Audit",
                 bg=C_CARD, fg=C_HEADER, font=font(10, "bold")).pack(
            side="left")
        btn_max = GhostButton(head, text="⛶ Perbesar", command=self._maximize)
        btn_max.pack(side="right")
        add_tooltip(btn_max, "Buka tabel ini dalam window besar\n"
                             "(Esc untuk menutup)")

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="browse")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50, anchor=anchor)
            # kolom Nama Barang: klik heading = filter (sort via popup filter)
            if col_name == "Nama Barang":
                self.tree.heading(col_name, text=col_name)
            else:
                self.tree.heading(col_name, text=col_name,
                                  command=lambda c=col_name: self._sort_by(c))

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Label(foot, text="🖱 Double-click baris → detail source · klik "
                            "judul kolom = sort · ⧩ header Nama Barang = filter",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(side="left")
        self.status_var_label = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var_label, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold")).pack(side="right")

        # Loading overlay (stacking di atas tree)
        self.overlay = LoadingOverlay(tbody, "Menghitung audit harian…")

        # Filter "Nama Barang" menempel di header kolom
        self.header_filter = HeaderFilter(
            self.tree, "Nama Barang",
            get_values=self._name_values,
            on_apply=self._on_name_filter,
            label="Nama Barang",
            on_sort=lambda desc: self._sort_by("Nama Barang", reverse=desc))

        self.tree.bind("<Double-1>", self._on_double_click)

    def _name_values(self) -> list:
        if self.data is None or self.data.empty or \
                "Nama Barang" not in self.data.columns:
            return []
        return self.data["Nama Barang"].dropna().astype(str).unique().tolist()

    def _on_name_filter(self, selected):
        self._name_selected = selected
        self._refresh()

    def _show_empty(self):
        self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("ok_match", foreground="#16a34a")
        tree.tag_configure("ok_cutoff", foreground="#65a30d")
        tree.tag_configure("deviasi_murni", foreground="#dc2626")
        tree.tag_configure("valid_sistem", foreground="#2563eb")
        tree.tag_configure("cutoff_resolved", foreground="#059669")
        tree.tag_configure("review", foreground="#ea580c")
        tree.tag_configure("negative", foreground="#dc2626")

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        self._cached_result = None
        self._cached_signature = None
        self._show_content()
        self._populate_filters()
        self._name_selected = None
        self.header_filter.clear()
        self._refresh()

    def _populate_filters(self):
        if self.data is None or self.data.empty:
            return
        for col, combo in [("NAMA RESTO", self.resto_combo)]:
            if col in self.data.columns:
                values = ["(All)"] + sorted(
                    self.data[col].dropna().astype(str).unique().tolist())
                combo["values"] = values
        self.status_combo["values"] = ["(All)"] + [s[0] for s in _STATUS_DEFS]

    def _toggle_status(self, label: str):
        """Klik KPI status → set/lepas filter status lalu refresh."""
        current = self.status_var.get()
        self.status_var.set("(All)" if current == label else label)
        self._sync_kpi_selection()

    def _sync_kpi_selection(self):
        active = self.status_var.get()
        for label, kpi in self._status_kpis.items():
            kpi.set_active(label == active and label != "(All)")
        self._refresh()

    # =========================================================================
    # COMPUTATION (identik versi lama)
    # =========================================================================
    def _compute_audit(self) -> pd.DataFrame:
        if self.data is None or self.data.empty:
            return pd.DataFrame()

        df = self.data

        required_jenis = [
            "SALDO AWAL", "1.SO", "2.SALDO AKHIR", "4.IN",
            "9.OUT", "8.BARANG KELUAR",
        ]
        df_filtered = df[df["JENIS"].isin(required_jenis)].copy()
        if df_filtered.empty:
            return pd.DataFrame()

        df_filtered["Tanggal_num"] = pd.to_numeric(
            df_filtered["Tanggal"], errors="coerce")
        df_filtered = df_filtered.dropna(subset=["Tanggal_num"])
        df_filtered["Tanggal_num"] = df_filtered["Tanggal_num"].astype("Int64")

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

        satuan_lookup = {}
        if "SATUAN" in df.columns and "Nama Barang" in df.columns:
            satuan_df = (
                df[["Nama Barang", "NAMA RESTO", "SATUAN"]]
                .dropna(subset=["SATUAN"])
                .drop_duplicates(subset=["Nama Barang", "NAMA RESTO"],
                                 keep="first")
            )
            satuan_lookup = {
                (r["Nama Barang"], r["NAMA RESTO"]): r["SATUAN"]
                for _, r in satuan_df.iterrows()
            }

        def gcol(df_, name):
            return df_[name] if name in df_.columns else pd.Series(
                0, index=df_.index)

        saldo_awal = gcol(pivot, "SALDO AWAL").fillna(0)
        so = gcol(pivot, "1.SO").fillna(0)
        sistem = gcol(pivot, "2.SALDO AKHIR").fillna(0)
        in_val = gcol(pivot, "4.IN").fillna(0)
        out_val = gcol(pivot, "9.OUT").fillna(0)
        bk = gcol(pivot, "8.BARANG KELUAR").fillna(0)

        deviasi = so - sistem

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

        result = result.sort_values(
            ["Resto", "Nama Barang", "Tanggal"]).reset_index(drop=True)
        result["Saldo Kumulatif"] = result.groupby(
            ["Resto", "Nama Barang"])["SO"].cumsum()

        result["Status Audit"] = result.apply(self._classify_status, axis=1)

        result["_prev_deviasi"] = result.groupby(
            ["Resto", "Nama Barang"])["Deviasi"].shift(1).fillna(0)

        result["Status Audit"] = result.apply(self._classify_status_v2, axis=1)
        result = result.drop(columns=["_prev_deviasi"])

        total_abs_dev = result["Deviasi"].abs().sum()
        if total_abs_dev > 0:
            result["Kontribusi %"] = (result["Deviasi"].abs() /
                                      total_abs_dev * 100).round(2)
        else:
            result["Kontribusi %"] = 0.0

        return result.sort_values("Tanggal").reset_index(drop=True)

    def _classify_status(self, row) -> str:
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
        deviasi = row["Deviasi"]
        prev_deviasi = row["_prev_deviasi"]
        so = row["SO"]
        sistem = row["Sistem"]

        if abs(prev_deviasi) > self.CUT_OFF_TOLERANCE and \
                abs(deviasi) <= self.CUT_OFF_TOLERANCE:
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
    # RENDER (async + batched — logika identik versi lama)
    # =========================================================================
    def _refresh(self, sync: bool = False):
        if self.data is None or self.data.empty:
            self.status_var_label.set(
                "Belum ada data. Jalankan pipeline di tab Proses.")
            return

        try:
            tgl_start = int(self.tgl_start_var.get())
            tgl_end = int(self.tgl_end_var.get())
        except ValueError:
            self.status_var_label.set("Tanggal harus angka. Contoh: 1-31.")
            return

        if tgl_start < 1 or tgl_end < 1 or tgl_start > tgl_end:
            self.status_var_label.set(
                "Range tanggal tidak valid. Contoh: 1-31.")
            return

        if self._busy:
            self._pending = True
            return
        self._busy = True

        sig = (len(self.data), tgl_start, tgl_end)
        st = {
            "tgl_start": tgl_start,
            "tgl_end": tgl_end,
            "resto": self.resto_var.get(),
            "status": self.status_var.get(),
            "name_selected": self._name_selected,
        }

        def work():
            if self._cached_result is None or self._cached_signature != sig:
                self._cached_result = self._compute_audit()
                self._cached_signature = sig
            return self._prepare_rows(st)

        def done(payload):
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung audit harian…", sync=sync)

    def _prepare_rows(self, st: dict) -> dict:
        """Pure pandas: filter result + sort → items tree (thread-safe)."""
        result = self._cached_result
        if result is None or result.empty:
            return {"items": [], "kpis": {}, "status": "Tidak ada data."}

        tgl_start, tgl_end = st["tgl_start"], st["tgl_end"]
        filtered = result[
            (result["Tanggal"] >= tgl_start) & (result["Tanggal"] <= tgl_end)
        ].copy()

        resto_val = st["resto"]
        if resto_val and resto_val != "(All)":
            filtered = filtered[filtered["Resto"].astype(str) == resto_val]

        if st["name_selected"]:
            filtered = filtered[filtered["Nama Barang"].astype(str)
                                .isin(st["name_selected"])]

        status_val = st["status"]
        if status_val and status_val != "(All)":
            filtered = filtered[filtered["Status Audit"].astype(str) == status_val]

        if filtered.empty:
            # KPI status tetap dihitung dari basis non-status-filter
            dist = self._apply_non_status_filters(
                result, tgl_start, tgl_end, resto_val,
                st["name_selected"])
            return {"items": [], "kpis": dist["Status Audit"].value_counts()
                        .to_dict() if not dist.empty else {},
                    "status": "Tidak ada data setelah filter. Klik 'Reset "
                              "Filter' atau ubah filter."}

        filtered = (
            filtered
            .assign(_abs_dev=filtered["Deviasi"].abs())
            .sort_values("_abs_dev", ascending=False)
            .drop(columns=["_abs_dev"])
        )

        col_ids = [c[0] for c in self.COLUMNS]
        n = len(filtered)
        total_dev = filtered["Deviasi"].abs().sum()
        status_counts = filtered["Status Audit"].value_counts().to_dict()

        items = []
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

            items.append(("", f"row_{i}", {"values": values,
                                            "tags": tuple(tags)}))

        # KPI status — distribusi mengabaikan filter status
        dist_base = self._apply_non_status_filters(
            result, tgl_start, tgl_end, resto_val, st["name_selected"])
        kpis = dist_base["Status Audit"].value_counts().to_dict() \
            if not dist_base.empty else {}

        summary = " · ".join(f"{k}: {v}" for k, v in
                             sorted(status_counts.items()))
        status = (f"{n} rows · Total |Deviasi|: {self._fmt_num(total_dev)} · "
                  f"{summary}")
        return {"items": items, "kpis": kpis, "status": status}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self.header_filter.refresh_icon()
        kpis = payload.get("kpis", {}) or {}
        for label, kpi in self._status_kpis.items():
            kpi.set_value(f"{kpis.get(label, 0):,}")
        self.status_var_label.set(payload["status"])

        def render_done():
            self._busy = False
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=400,
                          on_done=render_done)

    def _apply_non_status_filters(self, result, tgl_start, tgl_end,
                                  resto_val, name_selected):
        """Distribusi status mengabaikan filter status (untuk KPI)."""
        out = result[(result["Tanggal"] >= tgl_start) &
                     (result["Tanggal"] <= tgl_end)]
        if resto_val and resto_val != "(All)":
            out = out[out["Resto"].astype(str) == resto_val]
        if name_selected:
            out = out[out["Nama Barang"].astype(str).isin(name_selected)]
        return out

    def _reset_filter(self):
        self.resto_var.set("(All)")
        self.status_var.set("(All)")
        self.tgl_start_var.set("1")
        self.tgl_end_var.set("31")
        self._name_selected = None
        self.header_filter.clear()
        self._sync_kpi_selection()

    # =========================================================================
    # ⛶ PERBESAR (fullscreen)
    # =========================================================================
    def _maximize(self):
        def sort_setup(new_tree):
            for col_name, _, _ in self.COLUMNS:
                new_tree.heading(
                    col_name, text=col_name,
                    command=lambda c=col_name, t=new_tree:
                        self._sort_by(c, tree=t))

        return open_tree_maximized(
            self.tree, "Laporan Deviasi — Audit Harian",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_sort_setup=sort_setup)

    def _on_tanggal_change(self):
        try:
            int(self.tgl_start_var.get())
            int(self.tgl_end_var.get())
            self._refresh()
        except ValueError:
            self.status_var_label.set("Tanggal harus angka. Contoh: 1-31.")

    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        tree = tree if tree is not None else self.tree
        items = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            def parse_val(s):
                s = str(s).replace(",", "").replace("%", "").strip()
                if s == "-" or s == "":
                    return 0
                if s.startswith("(") and s.endswith(")"):
                    return -float(s[1:-1])
                return float(s)
            items.sort(key=lambda x: parse_val(x[0]), reverse=reverse)
        except (ValueError, AttributeError):
            items.sort(key=lambda x: str(x[0]), reverse=reverse)
        for i, (_, k) in enumerate(items):
            tree.move(k, "", i)

    # =========================================================================
    # DOUBLE-CLICK → POPUP (tree-agnostic via event.widget)
    # =========================================================================
    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return

        tree = event.widget
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return

        values = tree.item(row_iid, "values")
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
    # HELPERS (identik versi lama)
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
