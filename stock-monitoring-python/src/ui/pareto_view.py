"""
pareto_view.py — Tab 🎯 Pareto: kombinasi (Resto × Barang) penyumbang
deviasi terbesar (v3.9.9).

Analisis Pareto 80/20 atas |Deviasi| tab Deviasi GR/PCS:
- Semua kombinasi (Barang × Resto × Satuan) diurut |Deviasi| MENURUN.
- Kontribusi % = |Deviasi baris| / Σ|Deviasi| — pangsa kombinasi itu
  terhadap total masalah.
- Kumulatif % = jumlah berjalan kontribusi (baris 1..N).
- FOKUS 🎯 = baris yang DIPERLUKAN mencapai CUTOFF % (default 80%) —
  prinsip 20% kombinasi menyumbang 80% deviasi; baris pelintas
  (yang MENCAPAI cutoff) ikut dihitung.

Tabel: ✓ follow-up (fingerprint IDENTIK tab Deviasi — baris sama =
satu entri Follow Up) · No · Resto · Nama Barang · Satuan · Deviasi ·
|Deviasi| · Kontribusi % · Kumulatif % · Fokus · CEK.

- MODE GR / PCS (SegmentBar — satuan sama dgn tab Deviasi) · TANGGAL H
  read-only (state bersama, ikut Apply H di tab 📦 Deviasi GR) ·
  CUTOFF % (input 1-100, default 80).
- KPI: KOMBINASI · TOTAL |DEVIASI| · FOKUS ≤CUTOFF (n · %) ·
  TOP 20% (% deviasi yang ditutup 20% baris teratas) (cek klasik 80/20 di data nyata).
- GRAFIK canvas: top-N batang |Deviasi| (teal = fokus) + garis
  kumulatif % amber + garis cutoff merah + garis batas fokus.
- Compute pivot DIBAGI via SharedPivotCache (identik tab Deviasi —
  kelas ini SUBCLASS DeviasiView, tanpa hitung ulang).
- Export 💾: sheet PARETO (angka mentah + meta H/mode/cutoff) —
  write_pareto_sheet() di export_sheets.py.
"""
import contextlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import pandas as pd

from .deviasi_view import DeviasiView
from .export_sheets import write_pareto_sheet
from .followup import CHECK_OFF, CHECK_ON, FollowUpStore, row_fingerprint
from .theme import (
    C_ACCENT,
    C_AMBER,
    C_BG,
    C_CARD,
    C_HEADER,
    C_RED,
    C_TEXT_MUTED,
    font,
)
from .widgets import (
    Card,
    ColumnManager,
    EmptyState,
    GhostButton,
    HeaderFilterGroup,
    LegendRow,
    LoadingOverlay,
    SegmentBar,
    TableExpander,
    apply_cell_tag,
    attach_clone_filters,
    enable_col_resize,
    open_tree_maximized,
    run_async,
    sort_tree_by_column,
)

NUMERIC_COLS = ("No", "Deviasi", "|Deviasi|", "Kontribusi %", "Kumulatif %")


class ParetoDeviasiView(DeviasiView):
    """Subclass DeviasiView — mewarisi _compute_pivot + SharedPivotCache
    + load_data + ✓ follow-up + sort engine; MENG-OVERRIDE UI, kolom &
    _prepare_rows (komputasi Pareto). satuan_mode GANTIABLE via
    SegmentBar (self.satuan_mode di-mutasi + _refresh)."""

    COLUMNS = [
        ("✓", 34, "center"),
        ("No", 44, "e"),
        ("Resto", 70, "w"),
        ("Nama Barang", 180, "w"),
        ("Satuan", 50, "w"),
        ("Deviasi", 85, "e"),        # heading dinamis "Deviasi (H=..)"
        ("|Deviasi|", 85, "e"),      # heading dinamis "|Deviasi| (H=..)"
        ("Kontribusi %", 85, "e"),
        ("Kumulatif %", 90, "e"),    # heading dinamis "Kumulatif % (≤80%)"
        ("Fokus", 54, "center"),
        ("CEK", 120, "w"),
    ]

    FOCUS_ON, FOCUS_OFF = "🎯", "—"
    CHART_TOP_N = 30          # jumlah batang maksimum di grafik

    def __init__(self, parent, go_to_proses=None,
                 followup_store: FollowUpStore | None = None,
                 shared_cache=None, h_state=None):
        # satuan_mode awal GR; h_editable=False → chip read-only
        # (input H hanya di tab 📦 Deviasi GR — v3.9).
        super().__init__(parent, satuan_mode="GR",
                         go_to_proses=go_to_proses,
                         followup_store=followup_store,
                         shared_cache=shared_cache, h_state=h_state,
                         h_editable=False)
        self.cutoff_pct = 80.0
        self._result_df = None      # hasil pareto utk popup filter header
        self._fokus_cells: list = []   # [(iid, "Fokus")] sel 🎯 teal
        self._last_rows_raw: list = []  # bahan export terakhir
        self._last_totals: dict = {}

    # =========================================================================
    # UI BUILD (override — total beda dari DeviasiView)
    # =========================================================================
    def _build_ui(self):
        self.empty = EmptyState(
            self, icon="🎯", title="Belum ada data Pareto",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card: mode GR/PCS · chip H · cutoff · reset ---
        fcard = Card(self.content, title="Filter")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        self._fcard = fcard
        fbody = fcard.body()

        r0 = tk.Frame(fbody, bg=C_CARD)
        r0.pack(fill="x")
        self._segment = SegmentBar(r0, ["GR", "PCS"],
                                   command=self._on_mode_changed)
        self._segment.pack(side="left")

        tk.Label(r0, text="TANGGAL H", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left", padx=(18, 0))
        # chip read-only — H dibagikan dari tab 📦 Deviasi GR (pola PCS)
        self._h_chip_var = tk.StringVar(value=str(self.tanggal_h))
        chip = tk.Frame(r0, bg="#f1f5f9", highlightbackground="#e2e8f0",
                        highlightthickness=1)
        chip.pack(side="left", padx=(6, 18))
        tk.Label(chip, textvariable=self._h_chip_var, bg="#f1f5f9",
                 fg=C_ACCENT, font=font(11, "bold")).pack(
            padx=10, pady=(2, 3))

        tk.Label(r0, text="CUTOFF %", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._cutoff_var = tk.StringVar(value="80")
        cutoff_entry = ttk.Entry(r0, textvariable=self._cutoff_var,
                                 width=5)
        cutoff_entry.pack(side="left", padx=(6, 0))
        cutoff_entry.bind("<Return>", lambda e: self._on_cutoff_change())
        cutoff_entry.bind("<FocusOut>", lambda e: self._on_cutoff_change())

        GhostButton(r0, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left", padx=(18, 0))

        # --- KPI strip (data ringkasan Pareto) ---
        self._kpi_row = tk.Frame(self.content, bg=C_BG)
        self._kpi_row.pack(fill="x", padx=12, pady=(8, 0))
        self._kpi_vars = {}
        for key, label in (
                ("n", "KOMBINASI"), ("total", "TOTAL |DEVIASI|"),
                ("fokus", "FOKUS ≤ CUTOFF"), ("top20", "TOP 20%")):
            box = tk.Frame(self._kpi_row, bg="#f1f5f9",
                           highlightbackground="#e2e8f0",
                           highlightthickness=1)
            box.pack(side="left", padx=(0, 8))
            var = tk.StringVar(value="-")
            self._kpi_vars[key] = var
            tk.Label(box, text=label, bg="#f1f5f9", fg=C_TEXT_MUTED,
                     font=font(7, "bold")).pack(anchor="w", padx=10,
                                                pady=(4, 0))
            tk.Label(box, textvariable=var, bg="#f1f5f9", fg=C_HEADER,
                     font=font(11, "bold")).pack(anchor="w", padx=10,
                                                 pady=(0, 4))

        # --- Chart card (grafik Pareto top-N) ---
        self._chart_card = Card(self.content, title="Pareto")
        self._chart_card.pack(fill="x", padx=12, pady=(8, 0))
        cbody = self._chart_card.body()
        self._chart = tk.Canvas(cbody, bg=C_CARD, height=170,
                                highlightthickness=0)
        self._chart.pack(fill="x", padx=2, pady=2)
        self._chart_data = None
        self._chart.bind("<Configure>", self._on_chart_resize)

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._title_label = tk.Label(
            head, text="Pareto Deviasi — Kontributor Terbesar",
            bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        self._title_label.pack(side="left")
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel")
        btn_expand.pack(side="right", padx=(0, 6))
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))
        btn_export = GhostButton(head, text="💾 Export Excel",
                                 command=self._export_excel)
        btn_export.pack(side="right", padx=(0, 6))
        self._btn_export = btn_export

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="browse")
        for col_name, width, anchor in self.COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        enable_col_resize(self.tree)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(8, "bold")).pack(side="right")

        self.overlay = LoadingOverlay(tbody, "Menghitung pareto…")

        _filter_cols = [c[0] for c in self.COLUMNS if c[0] != "✓"]
        self._col_sel: dict = {c: None for c in _filter_cols}
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))

        # Legend CEK + fokus (decode nilai data — bukan instruksi)
        legend = LegendRow(self.content, [
            ("🎯 = kumulatif ≤ cutoff", C_ACCENT),
            ("Kosong/Non Aktif", "#b45309"),
            ("Beda Tanggal", "#2563eb"),
            ("Hitung Manual", "#ea580c"),
            ("Turun Drastis", "#dc2626"),
            ("ACR to BOM", "#7c3aed"),
            ("negatif (merah)", "#dc2626"),
        ])
        legend.pack(fill="x", padx=12, pady=(6, 0))
        self._legend = legend

        self._expander = TableExpander(
            btn_expand, [self._fcard, self._kpi_row, self._chart_card,
                         self._title_label, legend])

        # Berlangganan H bersama (pola laporan — unsubscribe saat destroy)
        if self._h_state is not None:
            self._h_state.subscribe(self._on_shared_h_changed)
            self.bind("<Destroy>", self._on_view_destroy, add="+")

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

    def _on_view_destroy(self, event):
        if event.widget is self and self._h_state is not None:
            with contextlib.suppress(Exception):
                self._h_state.unsubscribe(self._on_shared_h_changed)

    # =========================================================================
    # TAGS (super + fokus)
    # =========================================================================
    def _setup_tags(self, tree=None):
        super()._setup_tags(tree)
        tree = tree if tree is not None else self.tree
        # baris fokus: latar teal lembut — dipakai TANPA zebra supaya
        # prioritas tag tidak ambigu
        tree.tag_configure("focus_row", background="#ccfbf1")
        tree.tag_configure("focus_cell", foreground=C_ACCENT)

    # =========================================================================
    # MODE / CUTOFF / H
    # =========================================================================
    def _on_mode_changed(self, idx: int):
        self.satuan_mode = "GR" if idx == 0 else "PCS"
        if self.data is not None and not self.data.empty:
            self._refresh()

    def _on_cutoff_change(self):
        try:
            val = float(str(self._cutoff_var.get()).replace(",", "."))
        except ValueError:
            self._cutoff_var.set(f"{self.cutoff_pct:g}")
            return
        if not (1 <= val <= 100):
            messagebox.showwarning("Invalid", "CUTOFF harus 1-100",
                                   parent=self.winfo_toplevel())
            self._cutoff_var.set(f"{self.cutoff_pct:g}")
            return
        val = round(val, 2)
        if val == self.cutoff_pct:
            self._cutoff_var.set(f"{val:g}")
            return
        self.cutoff_pct = val
        self._cutoff_var.set(f"{val:g}")
        if self.data is not None and not self.data.empty:
            self._refresh()

    def _on_shared_h_changed(self, new_h: int):
        """Pola laporan (v3.9.5 audit 19-c #3): pane tersembunyi cukup
        dirty + chip; refresh saat benar-benar terlihat."""
        self.tanggal_h = int(new_h)
        self._cached_pivot = None
        self._cached_h = None
        if hasattr(self, "_h_chip_var"):
            self._h_chip_var.set(str(new_h))
        if self._dirty:
            return
        if not self.winfo_ismapped():
            self._dirty = True
            return
        if self.data is not None and not self.data.empty:
            self._refresh()

    # =========================================================================
    # FILTER HEADER (nilai terformat — sumber _result_df pareto)
    # =========================================================================
    def _col_values(self, col: str) -> list:
        result = self._result_df
        if result is None or result.empty or col not in result.columns:
            return []
        return self._format_col_series(col, result[col]).unique().tolist()

    def _format_col_series(self, col: str, series):
        if col in ("Kontribusi %", "Kumulatif %"):
            return series.map(self._fmt_pct)
        if col in ("Deviasi", "|Deviasi|", "No"):
            return series.map(self._fmt_num)
        return series.astype(str)

    # =========================================================================
    # KOMPUTASI PARETO (override _prepare_rows — thread worker)
    # =========================================================================
    def _prepare_rows(self, st: dict) -> dict:
        pivot_df = self._cached_pivot
        if pivot_df is None or pivot_df.empty:
            self._result_df = None
            return {"items": [], "kpi": (0, 0.0, 0),
                    "status": "Tidak ada data.",
                    "chart": None, "rows_raw": [], "totals": None}

        if self.satuan_mode == "GR":
            filtered = pivot_df[pivot_df["Satuan"].astype(str)
                                .str.upper() == "GR"]
        else:
            filtered = pivot_df[pivot_df["Satuan"].astype(str)
                                .str.upper() != "GR"]

        h = st["tanggal_h"]
        cutoff = self.cutoff_pct / 100.0

        # --- inti Pareto: urut |Deviasi| menurun → kontribusi & kumulatif
        out = (filtered
               .assign(_abs=filtered["Deviasi"].abs())
               .sort_values(["_abs", "Nama Barang", "Resto"],
                            ascending=[False, True, True],
                            kind="mergesort")
               .drop(columns=["_abs"])
               .reset_index(drop=True))
        total = float(out["Deviasi"].abs().sum())
        if total > 0:
            kontribusi = (out["Deviasi"].abs() / total).to_numpy(
                dtype="float64")
            kumulatif = np.cumsum(kontribusi)
        else:
            kontribusi = np.zeros(len(out), dtype="float64")
            kumulatif = np.zeros(len(out), dtype="float64")
        # FOKUS = baris yang DIPERLUKAN mencapai cutoff: semua baris
        # sebelum pelintas + baris pelintas itu sendiri
        # (kumulatif_sebelumnya < cutoff).
        if len(out):
            fokus = (kumulatif - kontribusi) < cutoff
        else:
            fokus = np.zeros(0, dtype=bool)
        n_fokus = int(fokus.sum())

        # snapshot utk popup filter header (SEBELUM filter header)
        out = out.assign(**{
            "No": np.arange(1, len(out) + 1),
            "Deviasi": pd.to_numeric(out["Deviasi"],
                                     errors="coerce").fillna(0.0),
            "|Deviasi|": pd.to_numeric(out["Deviasi"],
                                       errors="coerce").fillna(0.0).abs(),
            "Kontribusi %": kontribusi,
            "Kumulatif %": kumulatif,
            "Fokus": np.where(fokus, self.FOCUS_ON, self.FOCUS_OFF),
        })
        self._result_df = out[
            ["No", "Resto", "Nama Barang", "Satuan", "Deviasi",
             "|Deviasi|", "Kontribusi %", "Kumulatif %", "Fokus", "CEK"]
        ].copy()

        # filter header ⧩ — kecocokan nilai TERFORMAT
        for col, sel in st["col_sel"].items():
            if col in out.columns and sel:
                fmt = self._format_col_series(col, out[col])
                out = out[fmt.isin(sel)]

        if out.empty:
            return {"items": [], "kpi": (0, total, 0),
                    "status": "Tidak ada baris setelah filter.",
                    "chart": None, "rows_raw": [], "totals": None}

        # TOP 20% (klasik 80/20): ceil(20% × N) baris teratas menutup
        # berapa persen total deviasi (dari deret PENUH pra-filter)
        kum_full = kumulatif
        n20 = max(1, int(np.ceil(0.20 * len(kum_full))))
        top20_cover = float(kum_full[n20 - 1] * 100) if len(kum_full) else 0.0

        n = len(out)
        cek_series = out["CEK"].astype(str).str.strip()
        cols_np = {c: out[c].to_numpy() for c in
                   ("Resto", "Nama Barang", "Satuan", "AKTIF/NON",
                    "CEK", "Fokus")}
        for c in ("SO_H", "Sistem", "Deviasi", "|Deviasi|",
                  "Dev to BOM%", "SO_H-1", "SO_H-2", "SO_H+1", "SO_H+2"):
            if c in out.columns:
                cols_np[c] = pd.to_numeric(
                    out[c], errors="coerce").fillna(0).to_numpy(
                    dtype="float64")
            else:
                cols_np[c] = np.zeros(n, dtype="float64")
        kon_np = out["Kontribusi %"].to_numpy(dtype="float64")
        kum_np = out["Kumulatif %"].to_numpy(dtype="float64")
        no_np = out["No"].to_numpy()

        items = []
        fp_map = {}
        row_snaps = {}
        neg_cells = []
        zero_cells = []
        fokus_cells = []     # sel "Fokus" 🎯 teal per-cell
        rows_raw = []
        store = self.store
        asal = f"DEVIASI {self.satuan_mode}"   # identik Deviasi → dedup
        for i in range(n):
            barang = str(cols_np["Nama Barang"][i])
            resto = str(cols_np["Resto"][i])
            dev = float(cols_np["Deviasi"][i])
            fok = str(cols_np["Fokus"][i]) == self.FOCUS_ON
            values = [
                "", str(int(no_np[i])), resto, barang,
                str(cols_np["Satuan"][i]),
                self._fmt_num(dev), self._fmt_num(abs(dev)),
                self._fmt_pct(kon_np[i]), self._fmt_pct(kum_np[i]),
                self.FOCUS_ON if fok else self.FOCUS_OFF,
                str(cols_np["CEK"][i]),
            ]

            snap = {
                "asal": asal,
                "resto": resto,
                "barang": barang,
                "satuan": str(cols_np["Satuan"][i]),
                "aktif": str(cols_np["AKTIF/NON"][i]),
                "h": h,
                "so": float(cols_np["SO_H"][i]),
                "sistem": float(cols_np["Sistem"][i]),
                "deviasi": dev,
                "cek": str(cols_np["CEK"][i]),
                "so_m2": float(cols_np["SO_H-2"][i]),
                "so_m1": float(cols_np["SO_H-1"][i]),
                "so_p1": float(cols_np["SO_H+1"][i]),
                "so_p2": float(cols_np["SO_H+2"][i]),
                "loss_bom": float(cols_np["Dev to BOM%"][i]),
            }
            fp = row_fingerprint(snap)
            checked = store is not None and store.has(fp)
            values[0] = CHECK_ON if checked else CHECK_OFF
            fp_map[f"row_{i}"] = fp
            row_snaps[f"row_{i}"] = snap

            rows_raw.append({
                "no": int(no_np[i]), "resto": resto, "barang": barang,
                "satuan": str(cols_np["Satuan"][i]), "deviasi": dev,
                "abs_dev": float(cols_np["|Deviasi|"][i]),
                "kontribusi": float(kon_np[i]),
                "kumulatif": float(kum_np[i]), "fokus": fok,
                "cek": str(cols_np["CEK"][i]),
            })

            tags = []
            if fok:
                tags.append("focus_row")     # tanpa zebra — prioritas jelas
                fokus_cells.append((f"row_{i}", "Fokus"))
            else:
                tags.append("evenrow" if i % 2 == 0 else "oddrow")
            if dev < 0:
                if self._cell_tags:
                    neg_cells.append((f"row_{i}", "Deviasi"))
                else:
                    tags.append("negative")
            elif dev == 0:
                if self._cell_tags:
                    zero_cells.append((f"row_{i}", "Deviasi"))
                else:
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

            items.append(("", f"row_{i}", {"values": values,
                                            "tags": tuple(tags)}))

        # grafik: deret top-N pra-filter (grafik = pareto penuh)
        chart_abs = pd.to_numeric(
            self._result_df["|Deviasi|"], errors="coerce").fillna(0.0)
        chart_kum = pd.to_numeric(
            self._result_df["Kumulatif %"], errors="coerce").fillna(0.0)
        chart_fokus = (self._result_df["Fokus"].astype(str)
                       == self.FOCUS_ON).to_numpy()
        m = min(self.CHART_TOP_N, len(chart_abs))
        chart = {
            "abs": chart_abs.iloc[:m].tolist(),
            "kum": (chart_kum.iloc[:m] * 100).tolist(),
            "fokus": chart_fokus[:m].tolist(),
            "n_total": len(self._result_df),
            "n_fokus_total": int(chart_fokus.sum()),
            "cutoff": self.cutoff_pct,
            "total": total,
            "top20_cover": top20_cover,
        }

        status = (
            f"{n} baris {self.satuan_mode} · Total |Deviasi| "
            f"{self._fmt_num(total)} · Fokus ≤{self.cutoff_pct:g}%: "
            f"{n_fokus} baris ({(n_fokus / n * 100 if n else 0):.0f}% dari N)"
            f" · H={h}")
        return {"items": items, "kpi": (n, total, n_fokus),
                "status": status, "fp_map": fp_map,
                "row_snaps": row_snaps, "neg_cells": neg_cells,
                "zero_cells": zero_cells, "fokus_cells": fokus_cells,
                "chart": chart, "rows_raw": rows_raw,
                "totals": {"n": n, "total": total, "n_fokus": n_fokus,
                           "top20_cover": top20_cover, "h": h,
                           "mode": self.satuan_mode,
                           "cutoff": self.cutoff_pct}}

    # =========================================================================
    # RENDER (super + KPI + grafik + cache export)
    # =========================================================================
    def _render_rows(self, payload: dict):
        super()._render_rows(payload)
        self._fokus_cells = payload.get("fokus_cells", [])
        self._last_rows_raw = payload.get("rows_raw", [])
        self._last_totals = payload.get("totals")
        self._update_kpi(payload.get("totals"))
        self._draw_chart(payload.get("chart"))

    def _update_kpi(self, totals):
        if not totals:
            for v in self._kpi_vars.values():
                v.set("-")
            return
        n = totals["n"]
        self._kpi_vars["n"].set(f"{n}")
        self._kpi_vars["total"].set(self._fmt_num(totals["total"]))
        nf = totals["n_fokus"]
        pct = (nf / n * 100) if n else 0.0
        self._kpi_vars["fokus"].set(f"{nf} ({pct:.0f}% dari N)")
        self._kpi_vars["top20"].set(f"{totals['top20_cover']:.1f}%")

    # =========================================================================
    # GRAFIK PARETO (canvas — batang + garis kumulatif + cutoff)
    # =========================================================================
    def _on_chart_resize(self, _event):
        if self._chart_data is not None:
            self._draw_chart(self._chart_data)

    def _draw_chart(self, chart):
        self._chart_data = chart
        cv = self._chart
        try:
            cv.delete("all")
        except tk.TclError:
            return
        if not chart or not chart["abs"]:
            return

        try:
            w = max(int(cv.winfo_width()), 200)
            ht = max(int(cv.winfo_height()), 150)
        except tk.TclError:
            return
        pad_l, pad_r, pad_t, pad_b = 56, 42, 16, 18
        plot_w = max(w - pad_l - pad_r, 20)
        plot_h = max(ht - pad_t - pad_b, 20)

        abs_vals = [float(v) for v in chart["abs"]]
        kum_vals = [float(v) for v in chart["kum"]]
        fokus_flags = list(chart["fokus"])
        cutoff = float(chart["cutoff"])
        n = len(abs_vals)
        vmax = max(abs_vals) if abs_vals else 1.0
        vmax = vmax if vmax > 0 else 1.0

        bw = plot_w / n
        x0 = pad_l
        y_base = pad_t + plot_h

        # sumbu & grid + label sumbu (kiri |Dev|, kanan %)
        cv.create_line(x0, y_base, x0 + plot_w, y_base, fill="#cbd5e1")
        for frac, lbl in ((0.0, "0"), (0.5, self._compact(vmax / 2)),
                          (1.0, self._compact(vmax))):
            y = y_base - frac * plot_h
            cv.create_line(x0, y, x0 + plot_w, y, fill="#e2e8f0")
            cv.create_text(x0 - 6, y, text=lbl, anchor="e",
                           font=font(7), fill=C_TEXT_MUTED)
        for pct in (0, 50, 100):
            y = y_base - (pct / 100.0) * plot_h
            cv.create_text(x0 + plot_w + 6, y, text=f"{pct}%",
                           anchor="w", font=font(7), fill=C_TEXT_MUTED)

        # batang |Deviasi| (teal fokus / teal pudar non-fokus)
        for i, v in enumerate(abs_vals):
            bh = (v / vmax) * plot_h
            color = C_ACCENT if (i < len(fokus_flags)
                                 and fokus_flags[i]) else "#a7cdc9"
            cv.create_rectangle(x0 + i * bw + 1, y_base - bh,
                                x0 + (i + 1) * bw - 1, y_base,
                                fill=color, outline="")

        # garis kumulatif % (amber, marker jarang)
        pts = []
        for i, k in enumerate(kum_vals):
            px = x0 + (i + 0.5) * bw
            py = y_base - (min(k, 100.0) / 100.0) * plot_h
            pts.extend((px, py))
        if len(pts) >= 4:
            cv.create_line(*pts, fill=C_AMBER, width=2)
        for i in range(0, n, max(1, n // 15)):
            px, py = pts[2 * i], pts[2 * i + 1]
            cv.create_oval(px - 2, py - 2, px + 2, py + 2,
                           fill=C_AMBER, outline="")

        # garis cutoff (merah putus-putus)
        y_cut = y_base - (cutoff / 100.0) * plot_h
        seg = int(x0)
        while seg < x0 + plot_w:
            cv.create_line(seg, y_cut, min(seg + 4, x0 + plot_w), y_cut,
                           fill=C_RED)
            seg += 8
        cv.create_text(x0 + plot_w + 6, y_cut, text=f"{cutoff:g}%",
                       anchor="w", font=font(7, "bold"), fill=C_RED)

        # garis vertikal batas fokus (indeks data ke-n_fokus)
        nf = chart.get("n_fokus_total", 0)
        if 0 < nf <= n:
            xb = x0 + nf * bw
            cv.create_line(xb, pad_t, xb, y_base, fill=C_ACCENT,
                           dash=(4, 3))
            cv.create_text(xb + 4, pad_t + 2, text=f"n={nf}",
                           anchor="nw", font=font(7, "bold"),
                           fill=C_ACCENT)

        cv.create_text(x0 + 2, pad_t - 4, anchor="nw", font=font(7),
                       fill=C_TEXT_MUTED,
                       text=f"top {n} dari {chart.get('n_total', n)} · "
                            f"total {self._compact(chart.get('total', 0))}")

    @staticmethod
    def _compact(v) -> str:
        """Angka ringkas utk label grafik: 1,2jt / 12,5rb / 890."""
        try:
            v = float(v)
        except (TypeError, ValueError):
            return str(v)
        if abs(v) >= 1_000_000_000:
            return f"{v / 1_000_000_000:.1f}M".replace(".", ",")
        if abs(v) >= 1_000_000:
            return f"{v / 1_000_000:.1f}jt".replace(".", ",")
        if abs(v) >= 1_000:
            return f"{v / 1_000:.1f}rb".replace(".", ",")
        if v == int(v):
            return str(int(v))
        return f"{v:.1f}".replace(".", ",")

    # =========================================================================
    # HEADING DINAMIS (Deviasi/H + Kumulatif/cutoff)
    # =========================================================================
    def _update_headings(self):
        self.tree.heading("Deviasi", text=f"Deviasi (H={self.tanggal_h})")
        self.tree.heading("|Deviasi|", text=f"|Deviasi| (H={self.tanggal_h})")
        self.tree.heading("Kumulatif %",
                          text=f"Kumulatif % (≤{self.cutoff_pct:g}%)")
        if getattr(self, "header_filters", None) is not None:
            self.header_filters.refresh_icons()

    # =========================================================================
    # REAPPLY PER-CELL (super + sel Fokus)
    # =========================================================================
    def _reapply_cell_tags(self, tree):
        super()._reapply_cell_tags(tree)
        if self._cell_tags and self._fokus_cells:
            apply_cell_tag(tree, "focus_cell", self._fokus_cells)

    # =========================================================================
    # SORT (kolom numerik pareto — parser Indonesia)
    # =========================================================================
    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        if self._busy and tree is None:
            return
        tree = tree if tree is not None else self.tree
        parse = self._parse_num_id if col in NUMERIC_COLS else None
        sort_tree_by_column(tree, col, reverse=reverse, parse=parse)
        self._reapply_cell_tags(tree)

    # =========================================================================
    # MAXIMIZE (judul pareto)
    # =========================================================================
    def _maximize(self):
        def filter_setup(new_tree):
            attach_clone_filters(
                new_tree,
                [c[0] for c in self.COLUMNS if c[0] != "✓"],
                get_values=self._col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_by(
                    c, reverse=d, tree=t))

        win, new_tree = open_tree_maximized(
            self.tree, "Pareto Deviasi — Kontributor Terbesar",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_filter_setup=filter_setup,
            on_render_done=self._reapply_cell_tags)
        new_tree.bind("<Button-1>", self._on_tree_click, add="+")
        return win, new_tree

    # =========================================================================
    # EXPORT EXCEL (sheet PARETO — angka mentah + meta)
    # =========================================================================
    def _export_excel(self):
        rows_raw = list(self._last_rows_raw or [])
        if not rows_raw:
            messagebox.showwarning(
                "Export", "Belum ada data Pareto.",
                parent=self.winfo_toplevel())
            return
        filepath = filedialog.asksaveasfilename(
            title="Simpan sebagai Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="pareto_deviasi.xlsx",
            parent=self.winfo_toplevel(),
        )
        if not filepath:
            return

        totals = dict(self._last_totals or {})

        if not hasattr(self, "_export_overlay"):
            self._export_overlay = LoadingOverlay(self.winfo_toplevel(),
                                                  "Mengekspor Pareto…")
        self._export_overlay.show("Mengekspor Pareto…", delay_ms=0)
        self._btn_export.configure(state="disabled")

        def work():
            return write_pareto_sheet(filepath, rows_raw, totals)

        def done(path):
            self._btn_export.configure(state="normal")
            messagebox.showinfo(
                "Export Berhasil", f"Pareto di-export ke:\n{path}",
                parent=self.winfo_toplevel())

        def on_error(e):
            self._btn_export.configure(state="normal")
            messagebox.showerror(
                "Export Gagal", f"Tidak bisa export:\n{e}",
                parent=self.winfo_toplevel())

        run_async(self, work, done, overlay=self._export_overlay,
                  loading_text="Mengekspor Pareto…", on_error=on_error)

    def _reset_filter(self):
        """Reset filter header + cutoff → 80 (H milik state bersama —
        di-handle super() lewat SharedTanggalH)."""
        if self.cutoff_pct != 80.0:
            self.cutoff_pct = 80.0
            self._cutoff_var.set("80")
        super()._reset_filter()
