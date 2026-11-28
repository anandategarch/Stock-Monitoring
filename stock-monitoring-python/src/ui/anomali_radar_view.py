"""
anomali_radar_view.py — Tab 🚨 RADAR ANOMALI (v3.18): tabel SATU utk GR+PCS
berisi pasangan (Barang × Resto × Satuan) yang deviasinya TERGESER LEVEL
(menaik) — anomali kelas "konstan di level baru" yang TIDAK tertangkap
growth harian (tgl lompatan +282% lalu "tenang" +3-4% padahal level baru
menempel — kasus nyata user: BJMHAS · CUP 14 (V.20) PCS: stabil
(177)-(259) tgl 2-22 → (1.293) tgl 23 bersama IN 1.000 → konstan
(1.343)/(1.390) tgl 24-25).

Deteksi = engine anomali_shift (median/MAD dua-jendela per pasangan ×
satuan; level ≥ ×2 baseline & ≥2 hari di level baru; hint kecocokan
kiriman IN ±1 hari — lihat docstring modul itu). SATU tabel lintas
satuan (kolom Satuan — user: "jadi 1 aja GR dan PCS sekaligus").

Kolom: Resto · Nama Barang · Satuan · Tgl Shift · Durasi · Baseline ·
Level Kini · Rasio · Δ Deviasi · Z · Kecocokan IN · IN Tgl · Nomor
(IT/RI) · Nomor PO · BM · BM Tgl · Est. Nominal (Δ × harga 41.09).

Interaksi: double-click baris = popup Detail Deviasi pasangan itu (bukti
per tanggal — pola tab 📦/🧩) · klik-kanan = salin sel/baris + "Buka di
Deviasi GR" (deep-link focus_pair) · ⧩ filter header · sort kolom ·
Ctrl+F cari · ⤢ perbesar. Legend menjelaskan metode + ambang.
Status footer: "N pasangan shift aktif · terbesar ×N (Barang — Resto)".
H mengikuti SharedTanggalH (tab 📦) — refresh saat H berubah.
Empty state: belum ada anomali ≠ error (normal / baseline kurang / awal
bulan) — dijelaskan + CTA ke tab Deviasi GR.
"""
import tkinter as tk
from tkinter import ttk

import pandas as pd

from .anomali_shift import (
    RATIO_CUT,  # v3.18 — legenda ambang
    detect_shift_anomalies,
)
from .nominal_common import (
    fmt_rp_cell,  # v3.18 — Est. Nominal (Δ × harga 41.09)
    lookup_harga_pair,  # satuan-aware (pola kolom Nominal deviasi_view)
)
from .theme import (
    C_BG,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    ROW_EVEN,
    ROW_ODD,
    font,
)
from .widgets import (
    CELL_TAGS_SUPPORTED,
    EmptyState,
    HeaderFilterGroup,
    LegendRow,
    TableExpander,
    apply_cell_tag,
    copy_tree_selection_tsv,  # v3.18 — Ctrl+C baris TSV (pola popup)
    enable_col_resize,
    enable_multi_select,
    fmt_int_id,
    identify_to_column,
    install_tree_find_binding,
    reset_autofit_once,
    run_async,
)

# Kolom (id, lebar, anchor) — GR+PCS SATU tabel (kolom Satuan tampil
# selalu — beda tab 📦/🧩 yang menyembunyikannya karena per-tab seragam).
COLUMNS = [
    ("Resto", 70, "w"),
    ("Nama Barang", 190, "w"),
    ("Satuan", 55, "w"),
    ("Tgl Shift", 62, "e"),
    ("Durasi", 55, "e"),        # hari di level baru (bukan ukuran jendela)
    ("Baseline", 75, "e"),      # median |dev| pra-shift
    ("Level Kini", 80, "e"),    # median |dev| pasca-shift
    ("Rasio", 58, "e"),         # level ÷ baseline (×N) — sort default ↓
    ("Δ Deviasi", 85, "e"),     # level − baseline
    ("Z", 55, "e"),             # robust z (MAD)
    ("Kecocokan IN", 150, "w"),
    ("IN Tgl", 55, "e"),
    ("Nomor (IT/RI)", 135, "w"),
    ("Nomor PO", 125, "w"),
    ("BM", 55, "e"),
    ("BM Tgl", 55, "e"),
    ("Est. Nominal", 95, "e"),
]

# Kolom numerik (sort/filter numeric-aware) vs teks.
_NUM_COLS = {"Tgl Shift", "Durasi", "Baseline", "Level Kini", "Rasio",
             "Δ Deviasi", "Z", "BM", "Est. Nominal"}

# v3.18 — pewarnaan sel Rasio (heat 3 bucket: ×2 merah muda → ×8 kuat)
RASIO_BG = {"ras_1": "#FFEBEE", "ras_2": "#FFCDD2", "ras_3": "#EF9A9A"}
RASIO_EDGES = (2.0, 4.0, 8.0)


class AnomaliRadarView(tk.Frame):
    """Tabel radar anomali shift deviasi (GR+PCS sekaligus)."""

    def __init__(self, parent, go_to_proses=None, go_to_deviasi=None,
                 h_state=None, saldo_sistem_state=None,
                 on_count_changed=None):
        super().__init__(parent, bg=C_BG)
        self.go_to_proses = go_to_proses
        self.go_to_deviasi = go_to_deviasi
        self.on_count_changed = on_count_changed
        self.h_state = h_state
        self.tanggal_h = int(h_state.h) if h_state is not None else 25
        self.saldo_sistem_mode = (saldo_sistem_state.mode
                                  if saldo_sistem_state is not None
                                  else "4217")
        self.saldo_sistem_state = saldo_sistem_state

        self.data: pd.DataFrame | None = None
        self.in_detail: pd.DataFrame | None = None
        self.harga_map: dict = {}
        self.konversi_map: dict | None = None
        self.saldo_sistem_map: dict = {}

        self._rows: list[dict] = []        # baris tampil (raw+disp)
        self._rows_all: list[dict] = []    # pra-filter ⧩
        self._rows_by_iid: dict = {}
        self._busy = False
        self._dirty = False
        self._last_count = 0

        self._col_sel: dict = {c: None for c, _, _ in COLUMNS}
        self._sort_col = "Rasio"
        self._sort_rev = True

        self._build()
        if self.h_state is not None:
            self.h_state.subscribe(self._on_shared_h_changed)

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        # Empty state (belum ada data / belum ada anomali ≠ error).
        self.empty = EmptyState(
            self, title="Belum ada anomali shift",
            subtitle="Belum ada data — jalankan pipeline, atau memang tidak "
            "ada pasangan dengan pergeseran level deviasi (normal).",
            cta_text="Buka Tab Proses",
            on_cta=(self.go_to_proses if self.go_to_proses else None))
        # Konten utama
        self.content = tk.Frame(self, bg=C_BG)

        head = tk.Frame(self.content, bg=C_BG)
        head.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(head, text="🚨 Radar Anomali — pergeseran level deviasi",
                 bg=C_BG, fg=C_HEADER, font=font(12, "bold")).pack(
            anchor="w")
        tk.Label(head, bg=C_BG, fg=C_TEXT_MUTED, font=font(9), wraplength=980,
                 justify="left", text=(
                     "Pasangan (Barang × Resto × Satuan) dengan |deviasi| "
                     "melompat ke LEVEL BARU yang bertahan — median "
                     "dua-jendela vs baseline pasangan sendiri (bukan "
                     "ambang global). Double-click = bukti per tanggal; "
                     f"Rasio ≥ ×{RATIO_CUT:g} & durasi ≥ 2 hari di level "
                     "baru.")).pack(anchor="w", pady=(2, 0))
        # toolbar ⤢ TERPISAH dari target expander (button tetap terlihat)
        toolbar = tk.Frame(self.content, bg=C_BG)
        toolbar.pack(fill="x", padx=12, pady=(2, 0))

        tbody = tk.Frame(self.content, bg=C_BG)
        tbody.pack(fill="both", expand=True, padx=12, pady=(4, 8))
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        col_ids = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="extended")
        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name, anchor=anchor)
        vsb = ttk.Scrollbar(tbody, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        enable_col_resize(self.tree)
        enable_multi_select(self.tree)
        install_tree_find_binding(self, lambda: self.tree)

        # tag pewarnaan
        self.tree.tag_configure("evenrow", background=ROW_EVEN)
        self.tree.tag_configure("oddrow", background=ROW_ODD)
        self.tree.tag_configure("cocok_in", foreground="#059669")
        self.tree.tag_configure("tanpa_kiriman", foreground="#dc2626")
        self.tree.tag_configure("neg_cell", foreground="#dc2626")
        for _t, _bg in RASIO_BG.items():
            self.tree.tag_configure(_t, background=_bg)

        # Footer status
        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold"), anchor="e").pack(
            side="right", fill="x", expand=True)

        self.overlay = None   # LoadingOverlay dibuat lazy (perlu window)

        # ⧩ filter header (semua kolom) + sort
        self.header_filters = HeaderFilterGroup(
            self.tree, col_ids,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        # Interaksi
        self.tree.bind("<Double-1>", self._on_double_click, add="+")
        self.tree.bind("<Button-3>", self._on_context_menu, add="+")
        self.tree.bind("<Control-c>", self._on_copy, add="+")

        # Legend metode (transparansi deteksi)
        legend = LegendRow(self.content, [
            (("Shift Deviasi · level |deviasi| ≥ ×2 baseline (median "
              "dua-jendela per pasangan)"), "#c026d3"),
            (("Durasi ≥ 2 hari di level baru — spike 1 hari tidak "
              "dilaporkan"), "#475569"),
            ("Cocok IN · Δ ≈ kiriman sistem ±1 hari (cut-off?) — hijau",
             "#059669"),
            ("Tanpa kiriman · pergeseran tanpa sebab sistem — merah",
             "#dc2626"),
            ("Rasio · heat merah muda → kuat (×2 / ×4 / ×8)", "#EF9A9A"),
            ("Est. Nominal = Δ Deviasi × harga 41.09 (satuan-aware)",
             "#475569"),
        ])
        legend.pack(fill="x", padx=12, pady=(6, 0))
        self._expander = TableExpander(toolbar, [head, legend])

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------
    def load_data(self, data: pd.DataFrame,
                  in_detail: pd.DataFrame | None = None,
                  harga_map: dict | None = None,
                  konversi_map: dict | None = None,
                  saldo_sistem_map: dict | None = None):
        """Data baru dari pipeline (pola fan-out _on_pipeline_done app)."""
        self.data = data
        self.in_detail = in_detail
        self.harga_map = harga_map or {}
        self.konversi_map = konversi_map
        self.saldo_sistem_map = saldo_sistem_map or {}
        if self.saldo_sistem_state is not None:
            self.saldo_sistem_mode = self.saldo_sistem_state.mode
        self._rows_all = []
        self._rows = []
        self._col_sel = {c: None for c, _, _ in COLUMNS}
        self.header_filters.clear_all()
        reset_autofit_once(self)
        _empty = data is None or getattr(data, "empty", True)
        if not _empty:
            self._show_content()
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True
        if _empty:
            self._show_empty()
            self.status_var.set(
                "Belum ada data — 0 baris terbaca dari pipeline "
                "(cek folder data / RootPath di tab Config).")
            self._notify_count(0)

    def ensure_refreshed(self):
        """Lazy refresh (pola tab lain — dipanggil _on_tabChanged app)."""
        if self._dirty and self.winfo_ismapped():
            self._dirty = False
            self._refresh()

    def _on_shared_h_changed(self, new_h: int):
        """H berubah (tab 📦) → deteksi ulang (baseline/level ikut H)."""
        self.tanggal_h = int(new_h)
        if self.data is None or self.data.empty:
            return
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def _refresh(self, sync: bool = False):
        if self._busy:
            return
        self._busy = True
        data, h = self.data, self.tanggal_h
        harga_map, konversi_map = self.harga_map, self.konversi_map

        def work():
            anoms = detect_shift_anomalies(data, h)
            rows = []
            for rec in anoms.to_dict("records"):
                harga = None
                if harga_map:
                    harga = lookup_harga_pair(
                        harga_map, konversi_map,
                        str(rec.get("barang")), str(rec.get("satuan")))[0]
                rows.append(self._row_build(rec, harga))
            return {"rows": rows}

        def done(payload):
            self._busy = False
            self._rows_all = payload["rows"]
            self._apply_filters(render=True)
            self._notify_count(len(self._rows_all))

        def on_error(err):
            self._busy = False
            self.status_var.set(f"⚠ Gagal menghitung radar: {err}")

        run_async(self, work, done, on_error=on_error, sync=sync)

    def _notify_count(self, n: int):
        self._last_count = n
        cb = self.on_count_changed
        if cb is not None:
            try:
                cb(n)
            except tk.TclError:
                pass

    # ------------------------------------------------------------------
    # ROW BUILD (pure — thread-safe)
    # ------------------------------------------------------------------
    @staticmethod
    def _fmt_num(val) -> str:
        if val is None:
            return ""
        try:
            if pd.isna(val):
                return ""
        except (TypeError, ValueError):
            pass
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val)
        if v == int(v):
            return fmt_int_id(v)
        s = f"{v:,.1f}".replace(",", "\u00a0").replace(
            ".", ",").replace("\u00a0", ".")
        return s

    @classmethod
    def _fmt_ratio(cls, ratio) -> str:
        try:
            ratio = float(ratio)
        except (TypeError, ValueError):
            return "-"
        if pd.isna(ratio):
            return "-"
        if ratio == float("inf"):
            return "×∞"
        return f"×{cls._fmt_num(ratio)}"

    @classmethod
    def _fmt_z(cls, z) -> str:
        try:
            z = float(z)
        except (TypeError, ValueError):
            return "-"
        if pd.isna(z):
            return "-"
        if z == float("inf"):
            return "∞"
        return cls._fmt_num(round(z, 1))

    def _row_build(self, rec: dict, harga) -> dict:
        """Baris tampil: display strings + raw values (sort/filter) +
        record engine (popup/follow-up)."""
        in_qty = rec.get("in_qty")
        has_in = in_qty is not None and not (
            isinstance(in_qty, float) and pd.isna(in_qty))
        delta = rec.get("delta")
        if has_in and delta:
            pct = round(100.0 * float(in_qty) / float(delta))
            cocok = ("Cocok IN" if rec.get("in_match")
                     else "IN ≠ Δ")
            cocok_txt = f"{cocok} {self._fmt_num(in_qty)} ({pct}%)"
        else:
            cocok_txt = "Tanpa IN ±1 hari"
        bm_qty = rec.get("bm_qty")
        bm_has = bm_qty is not None and not (
            isinstance(bm_qty, float) and pd.isna(bm_qty))
        nominal = (None if harga is None
                   else float(harga) * float(rec.get("delta") or 0.0))
        disp = {
            "Resto": str(rec.get("resto") or ""),
            "Nama Barang": str(rec.get("barang") or ""),
            "Satuan": str(rec.get("satuan") or "-"),
            "Tgl Shift": str(rec.get("tgl_shift")),
            "Durasi": f"{int(rec.get('durasi'))} hari",
            "Baseline": self._fmt_num(rec.get("baseline")),
            "Level Kini": self._fmt_num(rec.get("level")),
            "Rasio": self._fmt_ratio(rec.get("ratio")),
            "Δ Deviasi": self._fmt_num(delta),
            "Z": self._fmt_z(rec.get("z")),
            "Kecocokan IN": cocok_txt,
            "IN Tgl": self._fmt_num(rec.get("in_tgl")),
            "Nomor (IT/RI)": str(rec.get("in_nomor") or "-"),
            "Nomor PO": str(rec.get("in_nomor_po") or "-"),
            "BM": self._fmt_num(bm_qty) if bm_has else "-",
            "BM Tgl": self._fmt_num(rec.get("bm_tgl")) if bm_has else "-",
            "Est. Nominal": fmt_rp_cell(nominal),
        }
        raw = {
            "Resto": disp["Resto"], "Nama Barang": disp["Nama Barang"],
            "Satuan": disp["Satuan"],
            "Tgl Shift": float(rec.get("tgl_shift") or 0),
            "Durasi": float(rec.get("durasi") or 0),
            "Baseline": float(rec.get("baseline") or 0),
            "Level Kini": float(rec.get("level") or 0),
            "Rasio": (float("inf") if (r := rec.get("ratio")) is None
                      else float(r)),
            "Δ Deviasi": float(delta or 0),
            "Z": float(rec.get("z") or 0),
            "Kecocokan IN": (1 if has_in and rec.get("in_match")
                             else (0 if has_in else -1)),
            "IN Tgl": float(rec.get("in_tgl") or 0),
            "Nomor (IT/RI)": disp["Nomor (IT/RI)"],
            "Nomor PO": disp["Nomor PO"],
            "BM": float(bm_qty or 0) if bm_has else 0.0,
            "BM Tgl": float(rec.get("bm_tgl") or 0),
            "Est. Nominal": (nominal if nominal is not None
                             else float("nan")),
        }
        return {"disp": disp, "raw": raw, "rec": rec}

    # ------------------------------------------------------------------
    # FILTER + SORT + RENDER
    # ------------------------------------------------------------------
    def _col_values(self, col: str) -> list:
        vals = []
        for row in self._rows_all:
            v = row["disp"].get(col, "")
            if v not in vals:
                vals.append(v)
        return vals

    def _on_col_filter(self, col: str, sel):
        self._col_sel[col] = sel
        self._apply_filters(render=True)

    def _apply_filters(self, render: bool = False):
        rows = self._rows_all
        for col, sel in self._col_sel.items():
            if not sel:
                continue
            rows = [r for r in rows
                    if r["disp"].get(col) in sel
                    or str(r["raw"].get(col)) in sel]
        self._rows = rows
        if render:
            self._render_rows()

    def _sort_by(self, col: str, reverse: bool = True):
        self._sort_col = col
        self._sort_rev = reverse
        self._render_rows()

    def _render_rows(self):
        self._busy = True
        try:
            self.tree.delete(*self.tree.get_children(""))
            col_ids = [c[0] for c in COLUMNS]
            rows = list(self._rows)
            key_col = self._sort_col if self._sort_col in col_ids \
                else "Rasio"
            rev = self._sort_rev

            def _key(row):
                v = row["raw"].get(key_col, "")
                if key_col in _NUM_COLS:
                    try:
                        return (0, float(v))
                    except (TypeError, ValueError):
                        return (1, 0.0)
                return (1, str(v))

            try:
                rows.sort(key=_key, reverse=rev)
            except TypeError:
                rows.sort(key=lambda r: str(r["raw"].get(key_col, "")),
                          reverse=rev)

            # heat sel Rasio (Tk 9 per-cell; Tk 8.6: pola melewatkan)
            # — kumpulkan per-TAG lalu satu panggilan (pola deviasi_view).
            rasio_cells: dict = {"ras_1": [], "ras_2": [], "ras_3": []}
            for i, row in enumerate(rows):
                disp = [row["disp"][c] for c, _, _ in COLUMNS]
                tags = ["evenrow" if i % 2 == 0 else "oddrow"]
                rec = row["rec"]
                if rec.get("in_match"):
                    tags.append("cocok_in")
                else:
                    tags.append("tanpa_kiriman")
                iid = f"row_{i}"
                self.tree.insert("", "end", iid=iid,
                                  values=disp, tags=tuple(tags))
                ratio = row["raw"].get("Rasio")
                if not pd.isna(ratio):
                    tag = ("ras_3" if ratio >= RASIO_EDGES[2]
                           else "ras_2" if ratio >= RASIO_EDGES[1]
                           else "ras_1" if ratio >= RASIO_EDGES[0]
                           else None)
                    if tag:
                        rasio_cells[tag].append((iid, "Rasio"))
            if CELL_TAGS_SUPPORTED:
                for _tag, _cells in rasio_cells.items():
                    apply_cell_tag(self.tree, _tag, _cells)
            self._rows_by_iid = {f"row_{i}": r for i, r in enumerate(rows)}
            self._update_status()
        finally:
            self._busy = False

    def _update_status(self):
        n = len(self._rows)
        n_all = len(self._rows_all)
        if not n_all:
            self.status_var.set(
                "Tidak ada anomali shift aktif — normal / baseline data "
                "belum cukup / awal bulan (lihat metode di legend).")
            return
        best = max(self._rows_all,
                   key=lambda r: (r["raw"].get("Rasio") or 0.0,
                                  r["raw"].get("Δ Deviasi") or 0.0))
        ratio = best["raw"].get("Rasio") or 0.0
        ratio_txt = ("×∞" if ratio == float("inf")
                     else f"×{ratio:,.1f}".replace(",", "."))
        who = (f" ({best['disp']['Nama Barang']} — "
               f"{best['disp']['Resto']})") if n_all else ""
        extra = f" dari {n_all}" if n != n_all else ""
        self.status_var.set(
            f"{n}{extra} pasangan shift aktif · terbesar {ratio_txt}{who}"
            f" · H={self.tanggal_h} · GR+PCS")

    def _show_empty(self):
        self.empty.pack(fill="both", expand=True)
        self.content.pack_forget()

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # INTERAKSI
    # ------------------------------------------------------------------
    def _row_rec(self, iid: str) -> dict | None:
        return (self._rows_by_iid.get(str(iid), {}) or {}).get("rec")

    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return
        row_iid = event.widget.identify_row(event.y)
        if not row_iid:
            return
        rec = self._row_rec(row_iid)
        if rec is None:
            return
        from .deviasi_popup import show_deviasi_popup
        show_deviasi_popup(
            self.winfo_toplevel(), self.data,
            nama_barang=str(rec.get("barang")),
            nama_resto=str(rec.get("resto")),
            satuan=(str(rec.get("satuan"))
                    if str(rec.get("satuan") or "-") != "-" else None),
            h=self.tanggal_h,
            in_detail=self.in_detail,
            saldo_sistem_map=self.saldo_sistem_map,
            saldo_sistem_mode=self.saldo_sistem_mode,
        )

    def _on_copy(self, _event=None):
        copy_tree_selection_tsv(self.tree)

    def _on_context_menu(self, event):
        row_iid = event.widget.identify_row(event.y)
        if not row_iid:
            return
        if row_iid not in self.tree.selection():
            self.tree.selection_set(row_iid)
        rec = self._row_rec(row_iid)
        menu = tk.Menu(self, tearoff=0)
        try:
            col = identify_to_column(self.tree,
                                     self.tree.identify_column(event.x))
            val = self.tree.set(row_iid, col) if col else ""
            if val:
                menu.add_command(label=f"Salin sel ('{val}')",
                                 command=lambda v=str(val): self._copy_text(v))
        except tk.TclError:
            pass
        menu.add_command(label="Salin baris (TSV)",
                        command=self._on_copy)
        if self.go_to_deviasi is not None and rec is not None:
            menu.add_separator()
            menu.add_command(
                label="Buka di Deviasi GR",
                command=lambda: self.go_to_deviasi(
                    str(rec.get("resto")), str(rec.get("barang"))))
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _copy_text(self, txt: str):
        """Salin teks sel ke clipboard (via tree — widget hidup)."""
        try:
            self.tree.clipboard_clear()
            self.tree.clipboard_append(txt)
        except tk.TclError:
            pass
