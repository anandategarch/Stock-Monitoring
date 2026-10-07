"""
deviasi_view.py — Wide matrix view DEVIASI GR/PCS (v3.2).

1 row per (Barang × Resto) di sekitar Tanggal H (H-2 … H+2) — logika
komputasi 100% identik versi lama (pivot + CEK anomaly detection), kini
VEKTORISASI numpy (tanpa iterrows — 5-10× lebih cepat).

Fitur v3.2:
- KPI row di atas tabel DIHAPUS (permintaan user: tabel jadi lebar &
  besar; ringkasan tetap ada di status footer)
- Kolom ✓ follow-up: klik sel ✓ = daftarkan/keluarkan baris ke tab
  ☑ Follow Up (ala repo Waste; persist followup.json)
- Lazy refresh: view hanya compute saat tab-nya terlihat (app memanggil
  ensure_refreshed saat tab dipilih)

Fitur v3.1 (dipertahankan):
- Filter Nama Barang menempel di header kolom (corong, Excel-like)
- Tombol ⛶ Perbesar: buka tabel fullscreen (+ ✓ aktif di sana)
- Loading overlay + compute/render async (UI tidak membeku)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from typing import Optional, Callable

from .theme import (
    C_BG, C_CARD, C_HEADER, C_TEXT_MUTED,
    font,
)
from .widgets import (
    Card, EmptyState, GhostButton, HeaderFilter, LegendRow,
    LoadingOverlay, add_tooltip, insert_tree_items, open_tree_maximized,
    run_async, sort_tree_by_column,
)
from .followup import CHECK_OFF, CHECK_ON, FollowUpStore, row_fingerprint


class SharedPivotCache:
    """Cache pivot Deviasi yang DIBAGI antar view GR & PCS (v3.3).

    _compute_pivot() tidak bergantung satuan (filter GR/PCS terjadi di
    _prepare_rows) — sebelumnya tab DEVIASI GR dan DEVIASI PCS masing-
    masing menghitung pivot identik 2× (waktu + memori ganda).
    """

    def __init__(self):
        self._entry: tuple | None = None   # (data_ref, h, pivot_df)

    def get(self, data, h):
        ent = self._entry
        if ent is not None and ent[0] is data and ent[1] == h:
            return ent[2]
        return None

    def put(self, data, h, pivot):
        self._entry = (data, h, pivot)

    def clear(self):
        self._entry = None


class DeviasiView(tk.Frame):
    """Wide matrix view untuk DEVIASI GR/PCS.

    satuan_mode: "GR" → hanya SATUAN=GR
                 "PCS" → SATUAN selain GR (PCS, BOTOL, dll)
    """

    COLUMNS = [
        ("✓", 34, "center"),
        ("Resto", 70, "w"),
        ("Nama Barang", 180, "w"),
        ("Satuan", 50, "w"),
        ("AKTIF/NON", 70, "w"),
        ("SO_H-2", 70, "e"),
        ("SO_H-1", 70, "e"),
        ("In_H-1", 70, "e"),
        ("SO_H", 70, "e"),
        ("In_H", 70, "e"),
        ("Out_H", 70, "e"),
        ("BK_H", 70, "e"),
        ("SO_H+1", 70, "e"),
        ("In_H+1", 70, "e"),
        ("SO_H+2", 70, "e"),
        ("Sistem", 80, "e"),
        ("Deviasi", 80, "e"),
        ("Rank", 50, "e"),
        ("CEK", 120, "w"),
    ]

    CEK_THRESHOLD = 1.3

    def __init__(self, parent, satuan_mode: str = "GR",
                 go_to_proses: Callable | None = None,
                 followup_store: FollowUpStore | None = None,
                 shared_cache: SharedPivotCache | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self.satuan_mode = satuan_mode
        self.tanggal_h = 25
        self._cached_pivot = None
        self._cached_h = None
        self._shared_cache = shared_cache   # dibagi GR & PCS (v3.3)
        self._aktif_lookup = {}
        self.go_to_proses = go_to_proses
        self._name_selected: set | None = None
        self._busy = False
        self._pending = False
        self._dirty = False                # lazy refresh (v3.2)
        self.store = followup_store       # shared FollowUpStore (v3.2)
        self._fp_map: dict[str, str] = {}     # iid → fingerprint
        self._row_snaps: dict[str, dict] = {}  # iid → snapshot raw (v3.2)
        self._tnum = None                 # cache pd.to_numeric(Tanggal)

        self._build_ui()
        self._setup_tags()
        if self.data is not None:
            self._refresh()
        else:
            self._show_empty()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        mode_label = "GR" if self.satuan_mode == "GR" else "PCS / non-GR"

        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="📦" if self.satuan_mode == "GR" else "🧩",
            title=f"Belum ada data Deviasi {mode_label}",
            subtitle="Jalankan pipeline untuk memuat matrix deviasi "
                     f"(satuan {mode_label}) ke tampilan ini.",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # (v3.2) KPI row DIHAPUS — tabel kini lebar & besar; ringkasan
        # (baris · total deviasi · anomali CEK) ada di status footer.

        # --- Filter card ---
        fcard = Card(self.content, title="Filter",
                     subtitle="Tanggal H = titik fokus analisis (kolom H-2 … "
                              "H+2). Filter Nama Barang → klik header kolom "
                              "(ikon corong ⧩) di tabel.")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        fbody = fcard.body()

        r0 = tk.Frame(fbody, bg=C_CARD)
        r0.pack(fill="x")
        tk.Label(r0, text="RESTO", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.resto_var = tk.StringVar(value="(All)")
        self.resto_combo = ttk.Combobox(r0, textvariable=self.resto_var,
                                        state="readonly", width=16)
        self.resto_combo.pack(side="left", padx=(6, 18))
        self.resto_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Label(r0, text="TANGGAL H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.tanggal_h_var = tk.StringVar(value=str(self.tanggal_h))
        tanggal_h_entry = ttk.Entry(r0, textvariable=self.tanggal_h_var,
                                    width=6)
        tanggal_h_entry.pack(side="left", padx=(6, 8))
        tanggal_h_entry.bind("<Return>", lambda e: self._on_tanggal_h_change())
        add_tooltip(tanggal_h_entry,
                    "Tanggal fokus (1-31). Kolom tampil: SO di H-2 s/d H+2.")
        GhostButton(r0, text="Apply H", command=self._on_tanggal_h_change).pack(
            side="left", padx=(0, 18))

        GhostButton(r0, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left")

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        # Header tabel: judul + tombol perbesar
        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        mode_label = "GR" if self.satuan_mode == "GR" else "PCS / non-GR"
        tk.Label(head, text=f"Matrix Deviasi {mode_label} — CEK Anomaly",
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
            self.tree.column(col_name, width=width, minwidth=34, anchor=anchor)
            display = self._col_display_name(col_name)
            # kolom Nama Barang: klik heading = filter (sort via popup filter)
            # kolom ✓: heading tanpa sort (klik sel = toggle follow-up)
            if col_name in ("Nama Barang", "✓"):
                self.tree.heading(col_name, text=display)
            else:
                self.tree.heading(col_name, text=display,
                                  command=lambda c=col_name: self._sort_by(c))

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        # Footer: hint + status
        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Label(foot, text="🖱 Double-click baris → detail · ✓ = masuk Follow "
                            "Up · klik judul kolom = sort · ⧩ Nama Barang = filter",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(side="left")
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(8, "bold")).pack(side="right")

        # Loading overlay (stacking di atas tree)
        self.overlay = LoadingOverlay(tbody, "Menghitung deviasi…")

        # Filter "Nama Barang" menempel di header kolom
        self.header_filter = HeaderFilter(
            self.tree, "Nama Barang",
            get_values=self._name_values,
            on_apply=self._on_name_filter,
            label="Nama Barang",
            on_sort=lambda desc: self._sort_by("Nama Barang", reverse=desc))

        # Legend CEK
        legend = LegendRow(self.content, [
            ("Kosong/Non Aktif", "#b45309"),
            ("Beda Tanggal", "#2563eb"),
            ("Hitung Manual", "#ea580c"),
            ("Turun Drastis", "#dc2626"),
            ("negatif (merah)", "#dc2626"),
        ])
        legend.pack(fill="x", padx=12, pady=(6, 0))

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
            col = tree.identify_column(event.x)
            if not col or int(col.replace("#", "")) != 1:  # kolom data #1 = ✓
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
        self.status_var.set(
            f"{'Masuk' if added else 'Keluar'} daftar Follow Up — total "
            f"{n} baris" if n else "Dikeluarkan — daftar Follow Up kosong")

    def ensure_refreshed(self):
        """Lazy refresh (v3.2): compute hanya saat tab ini terlihat."""
        if self._dirty and self.data is not None and not self.data.empty:
            self._dirty = False
            self._refresh()

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
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("zero_dev", foreground="#64748b")
        # CEK — palet modern (sejalan design system)
        tree.tag_configure("cek_kosong", foreground="#b45309")   # amber
        tree.tag_configure("cek_tanggal", foreground="#2563eb")  # blue
        tree.tag_configure("cek_manual", foreground="#ea580c")   # orange
        tree.tag_configure("cek_drastis", foreground="#dc2626")  # red
        tree.tag_configure("cek_acr", foreground="#7c3aed")      # purple

    # =========================================================================
    # LOGIKA (identik versi lama)
    # =========================================================================
    @staticmethod
    def _compute_cek(aktif_non, so_h, so_h_prev, in_h, out_h,
                     stok_seharusnya, threshold=1.3):
        """Port formula LET Excel (4 dari 5 kondisi — ACR butuh BOM, TODO)."""
        aktif = str(aktif_non or "").strip().upper()

        # 1. KondisiKosong → "Kosong/Non Aktif"
        if aktif == "AKTIF" and so_h < 0:
            return "Kosong/Non Aktif"
        if aktif == "NON AKTIF" and so_h > 0:
            return "Kosong/Non Aktif"

        # 2. KondisiNaikturun → "Beda Tanggal"
        if in_h > 0 and so_h < so_h_prev and out_h == 0:
            return "Beda Tanggal"
        if so_h_prev > 0:
            if so_h > so_h_prev + (0.5 * so_h_prev) and in_h == 0 and out_h == 0:
                return "Beda Tanggal"

        # 3. KondisiHitungManual → "Hitung Manual"
        if stok_seharusnya == 0:
            if so_h != 0:
                return "Hitung Manual"
        else:
            ratio = abs(so_h - stok_seharusnya) / abs(stok_seharusnya)
            if ratio > threshold:
                return "Hitung Manual"

        # 4. KondisiTurunDrastis → "Turun Drastis"
        if so_h_prev > 0 and (so_h / so_h_prev) < 0.5:
            return "Turun Drastis"

        return ""

    def _col_display_name(self, col_name: str) -> str:
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
        for col_name, _, _ in self.COLUMNS:
            display = self._col_display_name(col_name)
            if col_name in ("Nama Barang", "✓"):
                # Nama Barang = filter corong (sort via popup) · ✓ = toggle
                self.tree.heading(col_name, text=display)
            else:
                self.tree.heading(col_name, text=display,
                                  command=lambda c=col_name: self._sort_by(c))

    # =========================================================================
    # DATA LOADING
    # =========================================================================
    def load_data(self, data: pd.DataFrame):
        self.data = data
        self._cached_pivot = None
        self._cached_h = None
        if self._shared_cache is not None:
            self._shared_cache.clear()
        self._aktif_lookup = {}
        self._tnum = None  # reset cache to_numeric(Tanggal)
        self._show_content()
        self._populate_filters()
        self._name_selected = None
        self.header_filter.clear()
        # (v3.2) lazy refresh: hanya compute bila tab ini sedang terlihat;
        # tab lain menunggu dipilih (app memanggil ensure_refreshed).
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def _populate_filters(self):
        if self.data is None or self.data.empty:
            return
        for col, combo in [("NAMA RESTO", self.resto_combo)]:
            if col in self.data.columns:
                values = ["(All)"] + sorted(
                    self.data[col].dropna().astype(str).unique().tolist())
                combo["values"] = values

    # =========================================================================
    # PIVOT COMPUTATION (v3.2 — VEKTORISASI numpy, hasil identik versi lama)
    # =========================================================================
    def _compute_pivot(self) -> pd.DataFrame:
        if self.data is None or self.data.empty:
            return pd.DataFrame()

        df = self.data
        h = self.tanggal_h

        tanggal_range = [h - 2, h - 1, h, h + 1, h + 2]
        relevant_jenis = ["1.SO", "2.SALDO AKHIR", "4.IN", "9.OUT",
                          "8.BARANG KELUAR"]

        # cache to_numeric(Tanggal) per objek data (hindari recompute tiap H)
        tnum = self._tnum
        if tnum is None:
            tnum = pd.to_numeric(df["Tanggal"], errors="coerce")
            self._tnum = tnum
        mask = (df["JENIS"].isin(relevant_jenis)) & (tnum.isin(tanggal_range))
        df_filtered = df[mask].assign(Tanggal_num=tnum[mask].to_numpy())

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

        pivot = pivot.reset_index()
        n = len(pivot)

        def arr(jenis: str, tgl) -> np.ndarray:
            """Kolom (JENIS, Tanggal) sebagai array float64 (0 bila absen) —
            semantik identik get_val versi lama (NaN → 0)."""
            key = (jenis, float(tgl))
            if key in pivot.columns:
                return pd.to_numeric(
                    pivot[key], errors="coerce").fillna(0).to_numpy(
                    dtype="float64")
            return np.zeros(n, dtype="float64")

        so_m2 = arr("1.SO", h - 2)
        so_m1 = arr("1.SO", h - 1)
        in_m1 = arr("4.IN", h - 1)
        so_h = arr("1.SO", h)
        in_h = arr("4.IN", h)
        out_h = arr("9.OUT", h)
        bk_h = arr("8.BARANG KELUAR", h)
        so_p1 = arr("1.SO", h + 1)
        in_p1 = arr("4.IN", h + 1)
        so_p2 = arr("1.SO", h + 2)
        sistem = arr("2.SALDO AKHIR", h)

        deviasi = so_h - sistem
        stok = sistem + in_h - out_h - bk_h

        # --- CEK vektorisasi (np.select — urutan kondisi PERSIS versi lama) ---
        barang_s = pivot["Nama Barang"].astype(str)
        aktif_s = (barang_s.map(self._aktif_lookup).fillna("")
                   .astype(str).str.strip().str.upper())
        a = aktif_s.to_numpy()

        cond_kosong = ((a == "AKTIF") & (so_h < 0)) | \
                      ((a == "NON AKTIF") & (so_h > 0))

        cond_tanggal = ((in_h > 0) & (so_h < so_m1) & (out_h == 0)) | \
                       ((so_m1 > 0) & (so_h > so_m1 + 0.5 * so_m1) &
                        (in_h == 0) & (out_h == 0))

        stok_safe = np.where(stok == 0, 1.0, stok)
        ratio = np.abs(so_h - stok) / np.abs(stok_safe)
        cond_manual = np.where(stok == 0, so_h != 0, ratio > 1.3)

        with np.errstate(divide="ignore", invalid="ignore"):
            drop_ratio = np.divide(
                so_h, so_m1, out=np.full(n, np.inf), where=so_m1 > 0)
        cond_drastis = (so_m1 > 0) & (drop_ratio < 0.5)

        cek = np.select(
            [cond_kosong, cond_tanggal, cond_manual, cond_drastis],
            ["Kosong/Non Aktif", "Beda Tanggal", "Hitung Manual",
             "Turun Drastis"],
            default="",
        )

        result = pd.DataFrame({
            "Resto": pivot["NAMA RESTO"].astype(str).to_numpy(),
            "Nama Barang": barang_s.to_numpy(),
            "Satuan": pivot["SATUAN"].astype(str).to_numpy(),
            "AKTIF/NON": aktif_s.to_numpy(),
            "SO_H-2": so_m2,
            "SO_H-1": so_m1,
            "In_H-1": in_m1,
            "SO_H": so_h,
            "In_H": in_h,
            "Out_H": out_h,
            "BK_H": bk_h,
            "SO_H+1": so_p1,
            "In_H+1": in_p1,
            "SO_H+2": so_p2,
            "Sistem": sistem,
            "Deviasi": deviasi,
            "_ABS": np.abs(deviasi),
            "CEK": cek,
        })

        if result.empty:
            return result

        result["Rank"] = result.groupby("Nama Barang")["_ABS"].rank(
            method="min", ascending=False).astype("Int64")

        result = result.drop(columns=["_ABS"])
        return result

    # =========================================================================
    # RENDER (async + batched — logika filter identik versi lama)
    # =========================================================================
    def _refresh(self, sync: bool = False):
        if self.data is None or self.data.empty:
            self.status_var.set("Belum ada data.")
            return
        if self._busy:
            self._pending = True
            return
        self._busy = True
        st = {
            "resto": self.resto_var.get(),
            "name_selected": self._name_selected,
            "tanggal_h": self.tanggal_h,
        }

        def work():
            pivot = None
            if self._shared_cache is not None:
                pivot = self._shared_cache.get(self.data, self.tanggal_h)
            if pivot is None:
                pivot = self._compute_pivot()
                if self._shared_cache is not None and pivot is not None:
                    self._shared_cache.put(self.data, self.tanggal_h, pivot)
            self._cached_pivot = pivot
            self._cached_h = self.tanggal_h
            return self._prepare_rows(st)

        def done(payload):
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung deviasi…", sync=sync)

    def _prepare_rows(self, st: dict) -> dict:
        """Pure pandas: filter cached pivot + sort → items tree (thread-safe)."""
        pivot_df = self._cached_pivot
        if pivot_df is None or pivot_df.empty:
            return {"items": [], "kpi": (0, 0.0, 0),
                    "status": "Tidak ada data."}

        # Filter by Satuan mode
        if self.satuan_mode == "GR":
            filtered = pivot_df[pivot_df["Satuan"].astype(str).str.upper() == "GR"]
        else:
            filtered = pivot_df[pivot_df["Satuan"].astype(str).str.upper() != "GR"]

        resto_val = st["resto"]
        if resto_val and resto_val != "(All)":
            filtered = filtered[filtered["Resto"].astype(str) == resto_val]

        if st["name_selected"]:
            filtered = filtered[filtered["Nama Barang"].astype(str)
                                .isin(st["name_selected"])]

        if filtered.empty:
            return {"items": [], "kpi": (0, 0.0, 0),
                    "status": f"Tidak ada data "
                              f"{'GR' if self.satuan_mode == 'GR' else 'PCS'} "
                              f"setelah filter."}

        filtered = (
            filtered
            .assign(_abs_dev=filtered["Deviasi"].abs())
            .sort_values(["Nama Barang", "_abs_dev"], ascending=[True, False])
            .drop(columns=["_abs_dev"])
        )

        col_ids = [c[0] for c in self.COLUMNS]
        n = len(filtered)
        total_dev = float(filtered["Deviasi"].abs().sum())
        cek_series = filtered["CEK"].astype(str).str.strip()
        cek_count = int((cek_series != "").sum())
        items = []
        fp_map = {}
        row_snaps = {}
        store = self.store
        asal = f"DEVIASI {self.satuan_mode}"
        cols_np = {c: filtered[c].to_numpy() for c in
                   ("Resto", "Nama Barang", "Satuan", "AKTIF/NON",
                    "SO_H", "Sistem", "Deviasi", "CEK", "Rank")}
        for i in range(n):
            barang = str(cols_np["Nama Barang"][i])
            resto = str(cols_np["Resto"][i])
            values = [""] * len(col_ids)  # ✓ diisi di bawah
            for j, col_id in enumerate(col_ids):
                if col_id == "✓":
                    continue
                val = cols_np[col_id][i] if col_id in cols_np else 0
                if col_id == "Rank":
                    values[j] = self._fmt_int(val)
                else:
                    values[j] = self._fmt_num(val)

            # v3.2: fingerprint + snapshot (raw, tanpa format tampilan)
            snap = {
                "asal": asal,
                "resto": resto,
                "barang": barang,
                "satuan": str(cols_np["Satuan"][i]),
                "aktif": str(cols_np["AKTIF/NON"][i]),
                "h": st["tanggal_h"],
                "so": float(cols_np["SO_H"][i]),
                "sistem": float(cols_np["Sistem"][i]),
                "deviasi": float(cols_np["Deviasi"][i]),
                "cek": str(cols_np["CEK"][i]),
            }
            fp = row_fingerprint(snap)
            checked = store is not None and store.has(fp)
            values[0] = CHECK_ON if checked else CHECK_OFF
            fp_map[f"row_{i}"] = fp
            row_snaps[f"row_{i}"] = snap

            tags = []
            deviasi = cols_np["Deviasi"][i]
            if pd.notna(deviasi):
                if deviasi < 0:
                    tags.append("negative")
                elif deviasi == 0:
                    tags.append("zero_dev")
            cek_val = cek_series.iloc[i]
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

            items.append(("", f"row_{i}", {"values": values,
                                            "tags": tuple(tags)}))

        status = (
            f"{n} baris {self.satuan_mode} · Total |Deviasi| "
            f"{self._fmt_num(total_dev)} · CEK {cek_count} · "
            f"H={st['tanggal_h']}")
        return {"items": items, "kpi": (n, total_dev, cek_count),
                "status": status, "fp_map": fp_map, "row_snaps": row_snaps}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self._update_headings()
        self.header_filter.refresh_icon()
        self._fp_map = payload.get("fp_map", {})
        self._row_snaps = payload.get("row_snaps", {})
        # ringkasan (baris · total deviasi · anomali) ada di status footer —
        # KPI row atas tabel sudah dihapus (v3.2)
        self.status_var.set(payload["status"])

        def render_done():
            self._busy = False
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=500,
                          on_done=render_done)

    # =========================================================================
    # ⛶ PERBESAR (fullscreen)
    # =========================================================================
    def _maximize(self):
        mode_label = "GR" if self.satuan_mode == "GR" else "PCS"

        def sort_setup(new_tree):
            for col_name, _, _ in self.COLUMNS:
                if col_name in ("Nama Barang", "✓"):
                    new_tree.heading(col_name,
                                     text=self._col_display_name(col_name))
                else:
                    new_tree.heading(
                        col_name, text=self._col_display_name(col_name),
                        command=lambda c=col_name, t=new_tree:
                            self._sort_by(c, tree=t))

        win, new_tree = open_tree_maximized(
            self.tree, f"Deviasi {mode_label} — CEK Anomaly",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_sort_setup=sort_setup)
        # v3.2: kolom ✓ aktif juga di window perbesar (iid identik)
        new_tree.bind("<Button-1>", self._on_tree_click, add="+")
        return win, new_tree

    def _on_tanggal_h_change(self):
        try:
            new_h = int(self.tanggal_h_var.get())
            if 1 <= new_h <= 31:
                self.tanggal_h = new_h
                self._cached_pivot = None
                self._refresh()
            else:
                messagebox.showwarning("Invalid", "Tanggal H harus 1-31",
                                       parent=self.winfo_toplevel())
                self.tanggal_h_var.set(str(self.tanggal_h))
        except ValueError:
            messagebox.showwarning("Invalid", "Tanggal H harus angka",
                                   parent=self.winfo_toplevel())
            self.tanggal_h_var.set(str(self.tanggal_h))

    def _reset_filter(self):
        self.resto_var.set("(All)")
        self._name_selected = None
        self.header_filter.clear()
        self._refresh()

    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        """Sort kolom — engine LINEAR v3.3 (delete+reinsert, bukan
        tree.move O(n²) yang membekukan UI di tabel besar)."""
        if self._busy and tree is None:
            return   # render batch masih berjalan — sort ditunda (v3.3)
        tree = tree if tree is not None else self.tree
        sort_tree_by_column(tree, col, reverse=reverse)

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
        # (dulu tetap membuka popup detail — kurang intuitif)
        try:
            if tree.identify_column(event.x) == "#1":
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

        if not nama_barang:
            return

        from src.ui.details_popup import show_details_popup
        root = self.winfo_toplevel()

        active_filters = {}
        if nama_resto and nama_resto != "(All)":
            active_filters["NAMA RESTO"] = nama_resto

        show_details_popup(
            root, self.data,
            nama_barang=nama_barang,
            jenis=None,
            tanggal=None,
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
