"""
laporan_deviasi_view.py — Long-format daily audit view (v3.2).

Audit harian per (Resto, Nama Barang, Tanggal) + klasifikasi 6-way Status
Audit — hasil komputasi identik, kini Status Audit dihitung VEKTORISASI
np.select (bukan .apply(axis=1) — 10-50× lebih cepat).

Fitur v3.2:
- 6 kartu KPI status di atas tabel DIHAPUS (tabel jadi lebar & besar;
  filter status tetap ada di combo STATUS; distribusi ada di footer)
- Kolom ✓ follow-up: klik sel ✓ = daftarkan baris ke tab ☑ Follow Up
- Lazy refresh: compute hanya saat tab terlihat (app → ensure_refreshed)

Fitur v3.1 (dipertahankan):
- Filter Nama Barang menempel di header kolom (corong, Excel-like)
- Tombol ⛶ Perbesar: buka tabel fullscreen
- Loading overlay + compute/render async (UI tidak membeku)
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
from typing import Optional, Callable

from .theme import (
    C_BG, C_CARD, C_HEADER, C_TEXT_MUTED,
    font,
)
from .widgets import (
    Card, EmptyState, GhostButton, HeaderFilterGroup,
    ColumnManager, LoadingOverlay, TableExpander, add_tooltip,
    attach_clone_filters, auto_fit_columns, enable_col_resize,
    identify_to_column, insert_tree_items, open_tree_maximized, run_async,
    sort_tree_by_column,
)
from .followup import CHECK_OFF, CHECK_ON, FollowUpStore, row_fingerprint

class LaporanDeviasiView(tk.Frame):
    """Long-format daily audit view (LAPORAN DEVIASI) — tampilan baru."""

    COLUMNS = [
        ("✓", 34, "center"),
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

    def __init__(self, parent, go_to_proses: Callable | None = None,
                 followup_store: FollowUpStore | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self._cached_result = None
        self._cached_signature = None
        self.go_to_proses = go_to_proses
        self.store = followup_store       # shared FollowUpStore (v3.2)
        self._fp_map: dict[str, str] = {}     # iid → fingerprint
        self._row_snaps: dict[str, dict] = {}  # iid → snapshot raw
        self._busy = False
        self._pending = False
        self._dirty = False                # lazy refresh (v3.2)

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

        # (v3.2) 6 kartu KPI status + intro DIHAPUS — tabel jadi lebar &
        # besar; distribusi status ada di status footer bawah tabel
        # (v3.5: filter STATUS pindah ke header kolom ⧩).

        # --- Filter card (v3.5: RESTO/STATUS combo DIHAPUS → header ⧩) ---
        fcard = Card(self.content, title="Filter",
                     subtitle="Rentang tanggal. Filter RESTO / STATUS / "
                              "kolom lainnya → klik judul kolom (ikon "
                              "corong ⧩) di tabel. Sort default: "
                              "|Deviasi| terbesar dulu.")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        fbody = fcard.body()

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
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        # Header tabel: judul + tombol perbesar
        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        title_label = tk.Label(head, text="Audit Harian — 6 Status Audit",
                               bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        title_label.pack(side="left")
        # v3.9 (ala Waste): ⛶ = Layar Penuh (window terpisah)
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        add_tooltip(btn_max, "Buka tabel ini dalam window besar\n"
                             "(filter & sort juga jalan di window besar;\n"
                             "Esc untuk menutup)")
        # v3.9 (ala Waste): ⤢ = Perbesar Tabel (in-place)
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel")
        btn_expand.pack(side="right", padx=(0, 6))
        add_tooltip(btn_expand,
                    "Sembunyikan kartu Filter & judul supaya tabel "
                    "memakai seluruh tinggi tampilan.\nKlik lagi (⤡ "
                    "Tampilkan Filter & KPI) untuk mengembalikan.")
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        add_tooltip(btn_cols, "Sembunyikan / tampilkan kolom\n"
                              "(juga bisa: klik kanan judul kolom)")
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))
        add_tooltip(btn_fit, "Sesuaikan lebar semua kolom ke konten\n"
                             "(double-click tepi kolom = auto-fit 1 kolom;\n"
                             "drag tepi kolom = atur lebar manual)")

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="browse")

        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34, anchor=anchor)
            # v3.5: SEMUA kolom pakai filter header ⧩ (sort via popup);
            # ✓ tetap toggle follow-up via klik sel
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        # v3.4: drag tepi heading = resize lebar kolom; double-click tepi =
        # auto-fit (dipasang SEBELUM HeaderFilter supaya "break" efektif)
        enable_col_resize(self.tree)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Label(foot, text="🖱 Double-click baris → detail · ✓ = masuk Follow "
                            "Up · klik judul kolom ⧩ = filter + sort",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(side="left")
        self.status_var_label = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var_label, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold")).pack(side="right")

        # Loading overlay (stacking di atas tree)
        self.overlay = LoadingOverlay(tbody, "Menghitung audit harian…")

        # v3.5: filter header ⧩ di SEMUA kolom (kecuali ✓ = toggle)
        _filter_cols = [c[0] for c in self.COLUMNS if c[0] != "✓"]
        self._col_sel: dict = {c: None for c in _filter_cols}
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        # v3.6: hide/unhide kolom (klik kanan heading / tombol ◱ Kolom)
        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))

        # v3.9 (ala Waste): ⤢ Perbesar Tabel — ciutkan kartu Filter + judul
        self._expander = TableExpander(btn_expand, [fcard, title_label])

        self.tree.bind("<Double-1>", self._on_double_click)
        # v3.2: klik sel kolom ✓ → toggle follow-up (tree-agnostic)
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

    # =========================================================================
    # ✓ FOLLOW-UP (v3.2) — klik sel ✓ = daftarkan / keluarkan
    # =========================================================================
    def _on_tree_click(self, event):
        tree = event.widget
        try:
            if tree.identify_region(event.x, event.y) != "cell":
                return
            # v3.7 FIX: cocokkan NAMA kolom (bukan posisi display '#1') —
            # setelah kolom ✓ disembunyikan, posisi #1 jatuh ke kolom lain
            # → toggle follow-up terpicu dari kolom yang salah.
            col = identify_to_column(tree, tree.identify_column(event.x))
            if col != "✓":
                return
            row_iid = tree.identify_row(event.y)
        except Exception:
            return
        if not row_iid or self.store is None:
            return
        fp = self._fp_map.get(row_iid)
        snap = self._row_snaps.get(row_iid)
        if not fp or snap is None:
            return
        added = self.store.toggle(fp, snap)
        try:
            tree.set(row_iid, "✓", CHECK_ON if added else CHECK_OFF)
        except tk.TclError:
            pass
        n = len(self.store)
        self.status_var_label.set(
            f"{'Masuk' if added else 'Keluar'} daftar Follow Up — total "
            f"{n} baris" if n else "Dikeluarkan — daftar Follow Up kosong")

    def ensure_refreshed(self):
        """Lazy refresh (v3.2): compute hanya saat tab ini terlihat."""
        if self._dirty and self.data is not None and not self.data.empty:
            self._dirty = False
            self._refresh()

    def _col_values(self, col: str) -> list:
        """Nilai unik TERFORMAT utk popup filter header (v3.5 — semua kolom)."""
        result = self._cached_result
        if result is None or result.empty or col not in result.columns:
            return []
        return self._format_col_series(col, result[col]).unique().tolist()

    def _format_col_series(self, col: str, series):
        """Format kolom → string tampilan (identik render tabel — dipakai
        filter header supaya nilai popup == nilai yang tampil)."""
        if col == "Tanggal":
            return series.map(self._fmt_int)
        if col == "Kontribusi %":
            return series.map(self._fmt_pct)
        return series.map(self._fmt_num)

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
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
        # v3.9: pulihkan layout bila sedang di-perbesar ⤢
        if getattr(self, "_expander", None) is not None:
            self._expander.reset()
        self._show_content()
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        # (v3.2) lazy refresh — compute hanya bila tab terlihat
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    # =========================================================================
    # COMPUTATION (v3.2 — Status Audit VEKTORISASI np.select; hasil identik)
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
            # v3.2: zip (bukan iterrows — jauh lebih cepat)
            satuan_lookup = {
                (nb, nr): sat
                for nb, nr, sat in zip(satuan_df["Nama Barang"].astype(str),
                                       satuan_df["NAMA RESTO"].astype(str),
                                       satuan_df["SATUAN"].astype(str))
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

        # v3.2: Status Audit vektorisasi np.select (semantik PERSIS
        # _classify_status_v2 versi lama; .apply(axis=1) lama — yang
        # pertama bahkan dead-code hasilnya ditimpa — dihapus)
        prev = result.groupby(
            ["Resto", "Nama Barang"])["Deviasi"].shift(1).fillna(0)
        tol = self.CUT_OFF_TOLERANCE
        dev = result["Deviasi"].to_numpy(dtype="float64")
        prv = prev.to_numpy(dtype="float64")
        so_np = result["SO"].to_numpy(dtype="float64")
        sis_np = result["Sistem"].to_numpy(dtype="float64")
        result["Status Audit"] = np.select(
            [(np.abs(prv) > tol) & (np.abs(dev) <= tol),
             dev == 0,
             np.abs(dev) <= tol,
             so_np > sis_np,
             np.abs(dev) > tol],
            ["CUT-OFF RESOLVED", "OK (Matching)", "OK (Dalam Cut-off)",
             "VALID (Sistem Masuk)", "DEVIASI MURNI"],
            default="REVIEW",
        )

        total_abs_dev = result["Deviasi"].abs().sum()
        if total_abs_dev > 0:
            result["Kontribusi %"] = (result["Deviasi"].abs() /
                                      total_abs_dev * 100).round(2)
        else:
            result["Kontribusi %"] = 0.0

        return result.sort_values("Tanggal").reset_index(drop=True)

    # (_classify_status / _classify_status_v2 skalar dihapus — digantikan
    #  np.select di atas; semantik identik, urutan kondisi dipertahankan)

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

        # v3.3: signature tanpa rentang tanggal — _compute_audit() tidak
        # bergantung tgl_start/tgl_end (filter rentang terjadi di
        # _prepare_rows) → ganti rentang tidak lagi recompute 230ms sia-sia
        sig = id(self.data)
        st = {
            "tgl_start": tgl_start,
            "tgl_end": tgl_end,
            "col_sel": {c: s for c, s in self._col_sel.items() if s},
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
            return {"items": [], "status": "Tidak ada data."}

        tgl_start, tgl_end = st["tgl_start"], st["tgl_end"]
        filtered = result[
            (result["Tanggal"] >= tgl_start) & (result["Tanggal"] <= tgl_end)
        ]

        # v3.5: filter header ⧩ — kecocokan nilai TERFORMAT (identik dgn
        # yang tampil di tabel; menggantikan RESTO/STATUS/Nama Barang combo)
        for col, sel in st["col_sel"].items():
            if col in filtered.columns:
                fmt = self._format_col_series(col, filtered[col])
                filtered = filtered[fmt.isin(sel)]

        if filtered.empty:
            return {"items": [],
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
        fp_map = {}
        row_snaps = {}
        store = self.store
        # v3.3.1 FIX (pola sama dgn deviasi_view): vektorisasi v3.2 lupa
        # memasukkan Saldo Awal/IN/OUT/BK/Saldo Kumulatif ke cols_np → kolom
        # tersebut selalu tampil "-" walau datanya ada.
        cols_np = {c: filtered[c].to_numpy() for c in
                   ("Tanggal", "Resto", "Nama Barang", "Satuan",
                    "AKTIF/NON", "SO", "Sistem", "Deviasi",
                    "Status Audit", "Kontribusi %")}
        for c in ("Saldo Awal", "IN", "OUT", "BK", "Saldo Kumulatif"):
            cols_np[c] = pd.to_numeric(
                filtered[c], errors="coerce").fillna(0).to_numpy(
                dtype="float64")
        for i in range(n):
            values = [""] * len(col_ids)  # ✓ diisi di bawah
            for j, col_id in enumerate(col_ids):
                if col_id == "✓":
                    continue
                val = cols_np[col_id][i] if col_id in cols_np else 0
                if col_id == "Tanggal":
                    values[j] = self._fmt_int(val)
                elif col_id == "Kontribusi %":
                    values[j] = self._fmt_pct(val)
                else:
                    values[j] = self._fmt_num(val)

            # v3.2: fingerprint + snapshot (raw, tanpa format tampilan)
            barang = str(cols_np["Nama Barang"][i])
            snap = {
                "asal": "LAPORAN",
                "resto": str(cols_np["Resto"][i]),
                "barang": barang,
                "satuan": str(cols_np["Satuan"][i]),
                "aktif": str(cols_np["AKTIF/NON"][i]),
                "h": cols_np["Tanggal"][i],
                "so": float(cols_np["SO"][i]),
                "sistem": float(cols_np["Sistem"][i]),
                "deviasi": float(cols_np["Deviasi"][i]),
                "cek": str(cols_np["Status Audit"][i]),
            }
            fp = row_fingerprint(snap)
            checked = store is not None and store.has(fp)
            values[0] = CHECK_ON if checked else CHECK_OFF
            fp_map[f"row_{i}"] = fp
            row_snaps[f"row_{i}"] = snap

            tags = []
            deviasi = cols_np["Deviasi"][i]
            if pd.notna(deviasi) and deviasi < 0:
                tags.append("negative")
            status_aud = str(cols_np["Status Audit"][i]).strip()
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

        summary = " · ".join(f"{k}: {v}" for k, v in
                             sorted(status_counts.items()))
        status = (f"{n} rows · Total |Deviasi|: {self._fmt_num(total_dev)} · "
                  f"{summary}")
        return {"items": items, "status": status,
                "fp_map": fp_map, "row_snaps": row_snaps}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self.header_filters.refresh_icons()
        self._fp_map = payload.get("fp_map", {})
        self._row_snaps = payload.get("row_snaps", {})
        # distribusi status ada di status footer (v3.2 — kartu KPI dihapus)
        self.status_var_label.set(payload["status"])

        def render_done():
            self._busy = False
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=500,
                          on_done=render_done)

    def _reset_filter(self):
        self.tgl_start_var.set("1")
        self.tgl_end_var.set("31")
        for c in self._col_sel:
            self._col_sel[c] = None
        self.header_filters.clear_all()
        self._refresh()

    # =========================================================================
    # ⛶ PERBESAR (fullscreen)
    # =========================================================================
    def _maximize(self):
        def filter_setup(new_tree):
            # v3.6: funnel ⧩ + sort jalan juga di window besar
            attach_clone_filters(
                new_tree,
                [c[0] for c in self.COLUMNS if c[0] != "✓"],
                get_values=self._col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_by(c, reverse=d,
                                                               tree=t))

        win, new_tree = open_tree_maximized(
            self.tree, "Laporan Deviasi — Audit Harian",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_filter_setup=filter_setup)
        # v3.2: kolom ✓ aktif juga di window perbesar (iid identik)
        new_tree.bind("<Button-1>", self._on_tree_click, add="+")
        return win, new_tree

    def _on_tanggal_change(self):
        try:
            int(self.tgl_start_var.get())
            int(self.tgl_end_var.get())
            self._refresh()
        except ValueError:
            self.status_var_label.set("Tanggal harus angka. Contoh: 1-31.")

    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        """Sort kolom — engine LINEAR v3.3 (delete+reinsert; tree.move
        O(n²) dulu membekukan UI 45s saat sort 50k baris)."""
        if self._busy and tree is None:
            return   # render batch masih berjalan — sort ditunda (v3.3)
        tree = tree if tree is not None else self.tree
        sort_tree_by_column(tree, col, reverse=reverse)

    def _auto_fit(self):
        """v3.4 — auto-fit lebar semua kolom ke konten."""
        auto_fit_columns(self.tree)

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

        # v3.3: double-click di sel kolom ✓ = toggle follow-up
        # v3.7 FIX: cocokkan NAMA kolom (bukan posisi display '#1')
        try:
            if identify_to_column(tree, tree.identify_column(event.x)) == "✓":
                self._on_tree_click(event)
                return
        except Exception:
            pass

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
