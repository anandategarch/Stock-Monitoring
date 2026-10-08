"""
in_selisih_view.py — Tab "📤 Rekap Selisih IN" (v3.4 + v3.5).

Permintaan user (v3.4): "Tambah 1 tab lagi untuk rekap Selisih IN dan kolom
Resto, tanggal, nama barang, satuan, IN, Barang masuk dan selisih IN
dan bisa drill down atau pop up muncul rincian IN yaitu 42.05, 3224,
dan 9901 beserta nomor nya."

v3.5:
- Mode 🔍 AUDIT REKONSILIASI (default bila tersedia): port 1:1 macro VBA
  "BuatLaporanDeviasiSampel" — input sheet '29 Rekap Barang Masuk' (dibaca
  pipeline fn_rekap29). 12 kolom (Hasil SO / Qty SO Harian / Penerimaan
  Sistem / Selisih Harian / Saldo Kumulatif / Status Analisis Audit /
  Detail & Catatan Audit) + KPI chips + status berwarna (mirror
  conditional formatting VBA). Filter = display-only; audit dihitung dari
  sheet penuh (saldo kumulatif tidak terpotong rentang tanggal).
- Kolom KATEGORI + filter header ⧩ di SEMUA kolom (ala Excel AutoFilter).
  Filter RESTO combo di card atas DIHAPUS (duplikat → header Resto).
- Mode 📋 Ringkas (perilaku v3.4):
    IN            = metric "4.IN"  (Accurate: 42.05 + 32.24 + 99.01)
    Barang Masuk  = metric "5.BARANG MASUK" (input rekap SO harian)
    Selisih IN    = metric "7.Selisih IN"  (= Barang Masuk − IN)

Drill-down (double-click baris, kedua mode) → popup RINCIAN IN per dokumen:
  - ringkasan per sumber: 42.05 / 32.24 / 99.01 (+ 32.24 bulan lalu)
  - tabel dokumen: Source | Nomor | Nomor PO | Qty | #Tgl/Jam
  - copy Nomor (klik kanan / double-click cell / tombol Semua Nomor)
  - ⛶ Perbesar + ↔ Auto-Fit + Esc

Tanggal -25..-31 = data bulan lalu (selalu terbaca — LightMode dihapus v3.5).
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Callable, Optional

from .theme import (
    C_BG, C_CARD, C_HEADER, C_TEXT_MUTED, C_ACCENT_DARK, font,
)
from .widgets import (
    Card, EmptyState, GhostButton, HeaderFilterGroup, LoadingOverlay,
    SegmentBar, add_tooltip, auto_fit_columns, enable_col_resize,
    insert_tree_items, open_tree_maximized, run_async, sort_tree_by_column,
)

# --- Kolom per mode: (column_id, width, anchor) ------------------------------
RINGKAS_COLUMNS = [
    ("Resto", 74, "w"),
    ("Tanggal", 64, "e"),
    ("Nama Barang", 200, "w"),
    ("KATEGORI", 110, "w"),
    ("Satuan", 56, "w"),
    ("IN", 96, "e"),
    ("Barang Masuk", 110, "e"),
    ("Selisih IN", 100, "e"),
]

# Mirror laporan VBA "LAPORAN_DEVIASI" (nama kolom app-consistent)
AUDIT_COLUMNS = [
    ("Resto", 74, "w"),
    ("Tanggal", 64, "e"),
    ("Nama Barang", 200, "w"),
    ("KATEGORI", 110, "w"),
    ("Satuan", 56, "w"),
    ("Hasil SO", 90, "e"),
    ("Qty SO Harian", 110, "e"),
    ("Penerimaan Sistem", 120, "e"),
    ("Selisih Harian", 100, "e"),
    ("Saldo Kumulatif", 110, "e"),
    ("Status Analisis Audit", 140, "w"),
    ("Detail & Catatan Audit", 260, "w"),
]

_ALL_COLS = [c[0] for c in RINGKAS_COLUMNS] + \
    [c[0] for c in AUDIT_COLUMNS if c[0] not in
     {c[0] for c in RINGKAS_COLUMNS}]

# Kolom numerik (utk format & filter nilai)
_NUM_COLS = {"IN", "Barang Masuk", "Selisih IN", "Hasil SO", "Qty SO Harian",
             "Penerimaan Sistem", "Selisih Harian", "Saldo Kumulatif"}

# Warna status — mirror conditional formatting VBA (soft colors)
_STATUS_TAG = {
    "OK (Matching)": "st_ok",
    "OK (Dalam Cut-off)": "st_ok",
    "VALID (Sistem Masuk)": "st_valid",
    "CUT-OFF RESOLVED": "st_cutoff",
    "DEVIASI MURNI": "st_dev",
}
_STATUS_TAG_CFG = {
    # hijau soft — OK (RGB 226,239,218 / 55,86,35)
    "st_ok": {"background": "#e2efda", "foreground": "#375623"},
    # biru soft executive — VALID (RGB 222,235,247 / 31,78,120)
    "st_valid": {"background": "#deebf7", "foreground": "#1f4e78"},
    # kuning soft — CUT-OFF (RGB 255,242,204 / 128,96,0)
    "st_cutoff": {"background": "#fff2cc", "foreground": "#806000"},
    # merah soft — DEVIASI MURNI (RGB 252,228,214 / 198,89,17)
    "st_dev": {"background": "#fce4d4", "foreground": "#c65911"},
}

# Urutan sumber IN di popup rincian (+ warna chip ringkasan)
_SOURCES = [
    ("42.05", "#b45309"),              # amber — pemindahan/SJ
    ("32.24", "#2563eb"),              # biru — rincian penerimaan/RI
    ("32.24 (Bulan Lalu)", "#7c3aed"), # ungu — RI bulan lalu
    ("99.01", "#9C5700"),              # oranye — pembelian tanpa penerimaan
]

_POPUP_COLUMNS = [
    ("Source", 130, "w"),
    ("Nomor", 160, "w"),
    ("Nomor PO", 160, "w"),
    ("Qty", 90, "e"),
    ("#Tgl/Jam Pembuatan IT", 150, "w"),
]
_POPUP_IDS = [c[0] for c in _POPUP_COLUMNS]


def _fmt_num(val) -> str:
    """Format angka: 0 → '-', ribuan koma, negatif dalam kurung (merah via tag)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "-"
    try:
        if pd.isna(val):
            return "-"
    except (TypeError, ValueError):
        pass
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


def _fmt_int(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    try:
        return str(int(val))
    except (TypeError, ValueError):
        return str(val)


def _fmt_jam(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    try:
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass
    if hasattr(val, "strftime"):
        return val.strftime("%d/%m/%Y %H:%M:%S")
    try:
        return pd.to_datetime(val).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(val)


def _format_col_values(col: str, series: pd.Series) -> pd.Series:
    """Format satu kolom DataFrame → string tampilan (dipakai filter header
    & render — nilai filter selalu identik dgn yang tampil di tabel)."""
    if col == "Tanggal":
        return series.map(_fmt_int)
    if col in _NUM_COLS:
        return series.map(_fmt_num)
    return series.astype(str)


# =============================================================================
# POPUP RINCIAN IN (drill-down)
# =============================================================================

class InDetailPopup(tk.Toplevel):
    """Popup rincian IN per (Resto, Barang, Tanggal): breakdown dokumen
    42.05 / 32.24 / 99.01 (+ 32.24 bulan lalu) beserta nomornya."""

    def __init__(self, parent, resto: str, barang: str, tanggal,
                 detail_df: pd.DataFrame, row_summary: dict | None = None):
        super().__init__(parent)
        tgl_txt = _fmt_int(tanggal)
        self.title(f"Rincian IN — {barang} · {resto} · Tgl {tgl_txt}")
        try:
            pw, ph = 880, 560
            px = parent.winfo_rootx() + (parent.winfo_width() - pw) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - ph) // 2
            self.geometry(f"{pw}x{ph}+{max(px, 0)}+{max(py, 0)}")
        except Exception:
            self.geometry("880x560")
        self.minsize(640, 340)
        self.configure(bg=C_BG)
        self.transient(parent)
        self.grab_set()

        self.detail_df = detail_df
        self._flash_after = None
        self._base_status = ""
        self._render_df: pd.DataFrame = detail_df

        self._build_ui(barang, resto, tgl_txt, row_summary)
        self._render()
        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    # ---------------------------------------------------------------- UI ----
    def _build_ui(self, barang, resto, tgl_txt, row_summary):
        # --- Header band gelap ---
        header = tk.Frame(self, bg=C_HEADER)
        header.pack(fill="x")
        head_in = tk.Frame(header, bg=C_HEADER)
        head_in.pack(fill="x", padx=16, pady=12)
        tk.Label(head_in, text="📥 Rincian IN — dokumen pendukung",
                 bg=C_HEADER, fg="#5eead4", font=font(8, "bold")).pack(anchor="w")
        tk.Label(head_in,
                 text=f"{barang} · {resto} · Tanggal {tgl_txt}",
                 bg=C_HEADER, fg="#f1f5f9", font=font(12, "bold"),
                 wraplength=700, justify="left").pack(anchor="w", pady=(2, 0))

        btn_fit = tk.Button(
            head_in, text="↔ Auto-Fit", command=lambda: auto_fit_columns(self.tree),
            bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
            activeforeground="#ffffff", bd=0, relief="flat",
            highlightthickness=0, cursor="hand2", font=font(9, "bold"),
            padx=12, pady=5)
        btn_fit.pack(side="right", anchor="ne", padx=(0, 6))
        btn_max = tk.Button(
            head_in, text="⛶ Perbesar", command=self._maximize,
            bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
            activeforeground="#ffffff", bd=0, relief="flat",
            highlightthickness=0, cursor="hand2", font=font(9, "bold"),
            padx=12, pady=5)
        btn_max.pack(side="right", anchor="ne")

        # --- Ringkasan per sumber (chips) ---
        sum_card = tk.Frame(self, bg=C_CARD, highlightbackground="#e2e8f0",
                            highlightthickness=1)
        sum_card.pack(fill="x", padx=12, pady=(12, 0))
        chips = tk.Frame(sum_card, bg=C_CARD)
        chips.pack(fill="x", padx=12, pady=10)

        df = self.detail_df
        totals = {}
        if df is not None and not df.empty and "SOURCE IN" in df.columns:
            g = df.groupby("SOURCE IN")["Value"].sum()
            totals = {k: float(v) for k, v in g.items()}
        total_in = sum(totals.values())
        for src, color in _SOURCES:
            self._chip(chips, f"{src}", totals.get(src, 0.0), color)
        self._chip(chips, "IN TOTAL", total_in, C_ACCENT_DARK)
        if row_summary:
            self._chip(chips, "Barang Masuk", row_summary.get("bm", 0.0), "#006100")
            self._chip(chips, "Selisih IN", row_summary.get("selisih", 0.0),
                       "#CC0000")

        # --- Tabel dokumen ---
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        card = tk.Frame(body, bg=C_CARD, highlightbackground="#e2e8f0",
                        highlightthickness=1)
        card.pack(fill="both", expand=True)
        cin = tk.Frame(card, bg=C_CARD)
        cin.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(cin, columns=_POPUP_IDS, show="headings",
                                 selectmode="browse")
        for col_name, width, anchor in _POPUP_COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50, anchor=anchor)
            self.tree.heading(col_name, text=col_name)
        vsb = ttk.Scrollbar(cin, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(cin, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        cin.grid_rowconfigure(0, weight=1)
        cin.grid_columnconfigure(0, weight=1)

        self._setup_tags(self.tree)
        # v3.4: drag tepi heading = resize; double-click tepi = auto-fit
        # (dipasang SEBELUM interaksi lain supaya "break" efektif)
        enable_col_resize(self.tree)

        self.overlay = LoadingOverlay(cin, "Menyiapkan rincian…")

        # interaksi copy
        self.tree.bind("<Button-3>", self._on_context_menu)
        self.tree.bind("<Double-1>", self._on_double_click)

        # --- Footer ---
        foot = tk.Frame(self, bg=C_BG)
        foot.pack(fill="x", padx=12, pady=(0, 12))
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(foot, textvariable=self.status_var,
                                     bg=C_BG, fg=C_TEXT_MUTED, font=font(9))
        self.status_label.pack(side="left")
        btn_copy = GhostButton(foot, text="📋 Semua Nomor",
                               command=lambda: self._copy_all_unique())
        btn_copy.pack(side="right", padx=(6, 0))
        add_tooltip(btn_copy, "Copy SEMUA Nomor unik (newline-separated)")
        from .widgets import AccentButton
        AccentButton(foot, text="Tutup (Esc)", command=self.destroy).pack(
            side="right", padx=(6, 0))

    def _chip(self, parent, label, value, color):
        box = tk.Frame(parent, bg="#f1f5f9", highlightbackground="#e2e8f0",
                       highlightthickness=1)
        box.pack(side="left", padx=(0, 8))
        tk.Label(box, text=label.upper(), bg="#f1f5f9", fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(anchor="w", padx=10, pady=(6, 0))
        tk.Label(box, text=_fmt_num(value), bg="#f1f5f9", fg=color,
                 font=font(11, "bold")).pack(anchor="w", padx=10, pady=(0, 6))

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("subtotal", background="#f1f5f9",
                           foreground=C_HEADER)

    # ------------------------------------------------------------- RENDER ---
    def _render(self, sync: bool = True):
        df = self.detail_df
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            self._base_status = "Tidak ada dokumen IN untuk kombinasi ini."
            self.status_var.set(self._base_status)
            return

        items = []
        n_docs = 0
        subtotal_rows = []
        for src, _color in _SOURCES:
            sub = df[df["SOURCE IN"] == src]
            if sub.empty:
                continue
            sub = sub.sort_values(["Nomor", "Value"],
                                  ascending=[True, False],
                                  na_position="last")
            i = 0
            for _r, row in sub.iterrows():
                qty = row.get("Value")
                qty_txt, is_neg = _fmt_num(qty), (pd.notna(qty) and qty < 0)
                tags = []
                if is_neg:
                    tags.append("negative")
                tags.append("evenrow" if i % 2 == 0 else "oddrow")
                items.append(("", f"doc_{len(items)}", {
                    "values": (
                        str(row.get("SOURCE IN") or ""),
                        str(row.get("Nomor") or "") if pd.notna(row.get("Nomor")) else "",
                        str(row.get("Nomor PO") or "") if pd.notna(row.get("Nomor PO")) else "",
                        qty_txt,
                        _fmt_jam(row.get("#Tgl/Jam Pembuatan IT")),
                    ),
                    "tags": tuple(tags),
                }))
                n_docs += 1
                i += 1
            # baris subtotal per sumber
            subtotal_rows.append((len(items), f"TOTAL {src}",
                                  float(sub["Value"].sum())))

        # sisipkan subtotal mundur supaya index stabil
        for pos, label, total in reversed(subtotal_rows):
            items.insert(pos, ("", f"sub_{pos}", {
                "values": (label, "", "", _fmt_num(total), ""),
                "tags": ("subtotal",),
            }))
        if items:
            total_in = float(df["Value"].sum())
            items.append(("", "grand_total", {
                "values": ("TOTAL IN", "", "", _fmt_num(total_in), ""),
                "tags": ("subtotal",),
            }))

        self._base_status = (f"{n_docs} dokumen · "
                             f"Total IN: {_fmt_num(df['Value'].sum())}")
        self.status_var.set(self._base_status)
        insert_tree_items(self.tree, items, batch=400)

    # --------------------------------------------------------------- COPY ---
    def _copy_to_clipboard(self, text, label: str = "Nomor"):
        text = str(text or "").strip()
        if not text:
            self._flash_status("⚠ Tidak ada yang bisa di-copy (nilai kosong).")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        shown = text if len(text) <= 60 else text[:60] + "…"
        self._flash_status(f"📋 {label} TERSALIN: {shown}")

    def _flash_status(self, msg: str):
        if self._flash_after:
            try:
                self.after_cancel(self._flash_after)
            except Exception:
                pass
        self.status_var.set(msg)
        self.status_label.configure(fg=C_ACCENT_DARK)

        def restore():
            self.status_var.set(self._base_status)
            self.status_label.configure(fg=C_TEXT_MUTED)

        self._flash_after = self.after(3000, restore)

    def _on_context_menu(self, event):
        tree = event.widget
        iid = tree.identify_row(event.y)
        if not iid:
            return
        try:
            tree.selection_set(iid)
            tree.focus(iid)
        except Exception:
            pass
        values = tree.item(iid, "values")
        if not values:
            return
        row = dict(zip(_POPUP_IDS, values))
        nomor = str(row.get("Nomor", "") or "")
        menu = tk.Menu(tree, tearoff=0)
        if nomor:
            menu.add_command(label=f"📋 Copy Nomor: {nomor[:40]}",
                             command=lambda: self._copy_to_clipboard(nomor))
        po = str(row.get("Nomor PO", "") or "")
        if po:
            menu.add_command(label=f"📋 Copy Nomor PO: {po[:40]}",
                             command=lambda: self._copy_to_clipboard(po, "Nomor PO"))
        menu.add_separator()
        menu.add_command(label="📋 Copy baris (tab-separated)",
                         command=lambda: self._copy_row(values))
        if nomor or po:
            menu.add_separator()
        if nomor:
            menu.add_command(label="Copy SEMUA Nomor unik",
                             command=self._copy_all_unique)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_row(self, values):
        self._copy_to_clipboard("\t".join(str(v) for v in values), "Baris")

    def _on_double_click(self, event):
        tree = event.widget
        iid = tree.identify_row(event.y)
        if not iid:
            return
        try:
            col = tree.identify_column(event.x)
            idx = int(col.replace("#", "")) - 1
        except (ValueError, AttributeError):
            idx = -1
        if 0 <= idx < len(_POPUP_IDS) and _POPUP_IDS[idx] in ("Nomor", "Nomor PO"):
            val = tree.set(iid, _POPUP_IDS[idx])
            if val:
                self._copy_to_clipboard(val, _POPUP_IDS[idx])
                return
        # double-click baris biasa → copy Nomor (bila ada)
        nomor = tree.set(iid, "Nomor")
        if nomor:
            self._copy_to_clipboard(nomor, "Nomor")

    def _copy_all_unique(self):
        df = self._render_df
        if df is None or df.empty or "Nomor" not in df.columns:
            self._flash_status("⚠ Tidak ada Nomor untuk di-copy.")
            return
        vals = [str(v) for v in df["Nomor"].dropna().astype(str)
                if str(v).strip()]
        uniq = list(dict.fromkeys(vals))
        if not uniq:
            self._flash_status("⚠ Tidak ada Nomor untuk di-copy.")
            return
        self._copy_to_clipboard("\n".join(uniq),
                                f"{len(uniq)} Nomor unik")

    # ---------------------------------------------------------- PERBESAR ---
    def _maximize(self):
        return open_tree_maximized(
            self.tree, f"Rincian IN — {self.title().replace('Rincian IN — ', '')}",
            setup_tags=lambda t: self._setup_tags(t),
            on_context_menu=self._on_context_menu)


# =============================================================================
# VIEW UTAMA — Rekap Selisih IN (Ringkas + Audit Rekonsiliasi)
# =============================================================================

class InSelisihView(tk.Frame):
    """Rekap Selisih IN: mode 📋 Ringkas (IN vs Barang Masuk) dan mode 🔍
    Audit Rekonsiliasi (port macro VBA — sheet '29 Rekap Barang Masuk')."""

    def __init__(self, parent, go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self.in_detail: Optional[pd.DataFrame] = None
        self.audit_df: Optional[pd.DataFrame] = None
        self.audit_kpi: dict = {}
        self.audit_desc: str = ""
        self.go_to_proses = go_to_proses
        self.mode = "ringkas"        # "ringkas" | "audit"
        self._mode_initialized = False   # default audit saat load pertama
        self._col_sel: dict = {c: None for c in _ALL_COLS}   # header filter ⧩
        self._busy = False
        self._pending = False
        self._dirty = False            # lazy refresh (ala v3.2)
        self._cached_base: pd.DataFrame | None = None      # ringkas
        self._cached_audit: pd.DataFrame | None = None     # audit display
        self._satuan_map: dict = {}
        self._kategori_map: dict = {}
        self._keys: list = []
        self.header_filters: HeaderFilterGroup | None = None

        self._build_ui()
        self._setup_tags()
        if self.data is not None:
            self._refresh()
        else:
            self._show_empty()

    # ---------------------------------------------------------------- UI ----
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="📤",
            title="Belum ada data Rekap Selisih IN",
            subtitle="Jalankan pipeline untuk memuat rekap IN vs Barang "
                     "Masuk + Audit Rekonsiliasi (29 Rekap Barang Masuk).",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card (v3.5: RESTO combo DIHAPUS → header filter ⧩) ---
        fcard = Card(self.content, title="Filter",
                     subtitle="Rentang tanggal & mode tampilan. Filter "
                              "RESTO / KATEGORI / STATUS / nilai kolom → "
                              "klik judul kolom (ikon corong ⧩) di tabel. "
                              "Mode Audit: filter hanya menyembunyikan "
                              "baris — audit dihitung dari sheet penuh.")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        fbody = fcard.body()

        r0 = tk.Frame(fbody, bg=C_CARD)
        r0.pack(fill="x")
        tk.Label(r0, text="TANGGAL", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.tgl_start_var = tk.StringVar(value="1")
        entry_start = ttk.Entry(r0, textvariable=self.tgl_start_var, width=5)
        entry_start.pack(side="left", padx=(6, 2))
        entry_start.bind("<Return>", lambda e: self._on_tanggal_change())
        tk.Label(r0, text="–", bg=C_CARD, fg=C_TEXT_MUTED).pack(side="left")
        self.tgl_end_var = tk.StringVar(value="31")
        entry_end = ttk.Entry(r0, textvariable=self.tgl_end_var, width=5)
        entry_end.pack(side="left", padx=(2, 8))
        entry_end.bind("<Return>", lambda e: self._on_tanggal_change())
        add_tooltip(entry_start,
                    "Rentang hari 1..31.\nNilai negatif (-25..-31) = bulan "
                    "lalu.\nMode Audit: hanya menyembunyikan baris dari "
                    "tampilan (saldo kumulatif tetap dihitung penuh).")
        GhostButton(r0, text="Apply", command=self._on_tanggal_change).pack(
            side="left", padx=(0, 18))

        self.only_selisih_var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(
            r0, text="Hanya Selisih ≠ 0",
            variable=self.only_selisih_var,
            command=self._refresh)
        chk.pack(side="left")
        add_tooltip(chk, "Sembunyikan baris tanpa selisih\n"
                         "(Ringkas: IN == Barang Masuk ·\n"
                         "Audit: Qty SO Harian == Penerimaan Sistem)")

        GhostButton(r0, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left", padx=(18, 0))

        # --- KPI chips (mode Audit — mirror "EXECUTIVE RECONCILIATION
        #     SUMMARY" VBA) ---
        self.kpi_card = tk.Frame(self.content, bg=C_CARD,
                                 highlightbackground="#e2e8f0",
                                 highlightthickness=1)
        self.kpi_inner = tk.Frame(self.kpi_card, bg=C_CARD)
        self.kpi_inner.pack(fill="x", padx=12, pady=8)

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        self._tcard = tcard          # anchor pack utk kpi_card (before=)
        tbody = tcard.body()

        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.title_label = tk.Label(
            head, text="Rekap Selisih IN — IN (Accurate) vs Barang Masuk",
            bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        self.title_label.pack(side="left")
        self.mode_seg = SegmentBar(
            head, ["📋 Ringkas", "🔍 Audit Rekonsiliasi"], bg=C_CARD,
            command=self._on_mode_change)
        self.mode_seg.pack(side="left", padx=(14, 0))
        add_tooltip(self.mode_seg,
                    "📋 Ringkas: IN vs Barang Masuk (metric pipeline).\n"
                    "🔍 Audit Rekonsiliasi: port macro VBA — sheet '29 "
                    "Rekap Barang Masuk' (Hasil SO, saldo kumulatif, "
                    "cut-off, deviasi murni).")
        btn_max = GhostButton(head, text="⛶ Perbesar", command=self._maximize)
        btn_max.pack(side="right")
        add_tooltip(btn_max, "Buka tabel ini dalam window besar\n"
                             "(Esc untuk menutup)")
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))
        add_tooltip(btn_fit, "Sesuaikan lebar semua kolom ke konten\n"
                             "(double-click tepi kolom = auto-fit 1 kolom;\n"
                             "drag tepi kolom = atur lebar manual)")

        self.tree = ttk.Treeview(tbody, columns=[c[0] for c in RINGKAS_COLUMNS],
                                 show="headings", selectmode="browse")

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
        self.hint_label = tk.Label(foot, text="", bg=C_CARD, fg=C_TEXT_MUTED,
                                   font=font(8))
        self.hint_label.pack(side="left")
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(8, "bold")).pack(side="right")

        self.overlay = LoadingOverlay(tbody, "Menghitung rekap Selisih IN…")

        self._apply_mode_columns()

        self.tree.bind("<Double-1>", self._on_double_click)

    def _apply_mode_columns(self):
        """(Re)pasang kolom tree + heading + HeaderFilterGroup sesuai mode."""
        # lepas binding filter lama dulu — mencegah binding ganda saat
        # kolom dikonfigurasi ulang (HeaderFilter.bind add="+")
        if self.header_filters is not None:
            self.header_filters.detach_all()
            self.header_filters = None

        cols_def = AUDIT_COLUMNS if self.mode == "audit" else RINGKAS_COLUMNS
        col_ids = [c[0] for c in cols_def]
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=col_ids)
        for col_name, width, anchor in cols_def:
            self.tree.column(col_name, width=width, minwidth=40, anchor=anchor)
            # v3.5: SEMUA kolom pakai filter header ⧩ (sort via popup —
            # klik heading membuka popup, bukan sort langsung)
            self.tree.heading(col_name, text=col_name)

        # buang state filter kolom yang tidak ada di mode ini
        for c in list(self._col_sel.keys()):
            if c not in col_ids:
                self._col_sel[c] = None

        # v3.5: filter header di SEMUA kolom
        self.header_filters = HeaderFilterGroup(
            self.tree, col_ids,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        # judul + hint per mode
        if self.mode == "audit":
            self.title_label.configure(
                text="Audit Rekonsiliasi — LAPORAN DEVIASI (port macro VBA)")
            self.hint_label.configure(
                text="🖱 Double-click baris → rincian IN (42.05 / 32.24 / "
                     "99.01 + nomor) · klik judul kolom ⧩ = filter + sort · "
                     "status & saldo dihitung dari sheet penuh (filter hanya "
                     "menyembunyikan baris)")
        else:
            self.title_label.configure(
                text="Rekap Selisih IN — IN (Accurate) vs Barang Masuk")
            self.hint_label.configure(
                text="🖱 Double-click baris → rincian IN (42.05 / 32.24 / "
                     "99.01 + nomor) · klik judul kolom ⧩ = filter + sort")

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("zero", foreground="#64748b")
        # v3.5: warna status audit (mirror conditional formatting VBA)
        for tag, cfg in _STATUS_TAG_CFG.items():
            tree.tag_configure(tag, **cfg)

    # ------------------------------------------------------------ DATA ----
    def load_data(self, data: pd.DataFrame, in_detail: pd.DataFrame | None = None,
                  audit_result: dict | None = None):
        self.data = data
        self.in_detail = in_detail
        if audit_result:
            self.audit_df = audit_result.get("df")
            self.audit_kpi = audit_result.get("kpi") or {}
            self.audit_desc = audit_result.get("desc") or ""
        else:
            self.audit_df = None
            self.audit_kpi = {}
            self.audit_desc = ""
        self._cached_base = None
        self._cached_audit = None
        self._satuan_map = {}
        self._kategori_map = {}
        self._show_content()

        audit_ok = self.audit_df is not None and not self.audit_df.empty
        if not self._mode_initialized:
            # default pertama kali: Audit bila tersedia (permintaan user)
            self.mode = "audit" if audit_ok else "ringkas"
            self._mode_initialized = True
        elif self.mode == "audit" and not audit_ok:
            # audit dipilih tapi datanya hilang → balik ke ringkas
            self.mode = "ringkas"
        self.mode_seg.set_active_silent(1 if self.mode == "audit" else 0)
        # default 'Hanya Selisih ≠ 0': audit ON (fokus anomali, render cepat),
        # ringkas OFF (perilaku v3.4)
        self.only_selisih_var.set(self.mode == "audit")
        self._apply_mode_columns()
        self._reset_filter_states()
        self._render_kpi_chips()
        # lazy refresh — hanya compute bila tab terlihat
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def ensure_refreshed(self):
        """Lazy refresh: compute hanya saat tab ini terlihat."""
        if self._dirty and self.data is not None and not self.data.empty:
            self._dirty = False
            self._refresh()

    def _reset_filter_states(self):
        for c in self._col_sel:
            self._col_sel[c] = None
        if self.header_filters is not None:
            self.header_filters.clear_all()

    # ------------------------------------------------------- KPI CHIPS ----
    def _render_kpi_chips(self):
        """KPI 'EXECUTIVE RECONCILIATION SUMMARY' (mode Audit saja) —
        dihitung dari sheet penuh (tidak terpengaruh filter tampilan)."""
        for w in self.kpi_inner.winfo_children():
            w.destroy()
        if self.mode != "audit" or not self.audit_kpi:
            self.kpi_card.pack_forget()
            return
        k = self.audit_kpi
        chips = [
            ("TOTAL BARIS", f"{k.get('rows', 0):,}", "#0f766e"),
            ("OK (MATCHING)", f"{k.get('ok', 0):,}", "#16a34a"),
            ("VALID (SISTEM MASUK)", f"{k.get('omit', 0):,}", "#1f4e78"),
            ("CUT-OFF RESOLVED", f"{k.get('cutoff', 0):,}", "#806000"),
            ("DEVIASI MURNI", f"{k.get('deviasi_murni', 0):,}", "#c65911"),
            ("SISA GANTUNG (NET)",
             f"{k.get('deviasi_qty', 0.0):,.0f}",
             "#dc2626" if abs(k.get("deviasi_qty", 0.0)) > 0.0001 else "#16a34a"),
        ]
        for label, value, color in chips:
            box = tk.Frame(self.kpi_inner, bg="#f8fafc",
                           highlightbackground="#e2e8f0", highlightthickness=1)
            box.pack(side="left", padx=(0, 8))
            tk.Label(box, text=label, bg="#f8fafc", fg=C_TEXT_MUTED,
                     font=font(8, "bold")).pack(anchor="w", padx=10,
                                                pady=(6, 0))
            tk.Label(box, text=value, bg="#f8fafc", fg=color,
                     font=font(11, "bold")).pack(anchor="w", padx=10,
                                                 pady=(0, 6))
        self.kpi_card.pack(fill="x", padx=12, pady=(10, 0),
                           before=self._tcard)

    # --------------------------------------------------- VALUES & FILTER ---
    def _base_of_mode(self) -> pd.DataFrame:
        if self.mode == "audit":
            if self._cached_audit is None:
                self._cached_audit = self._compute_audit_display()
            return self._cached_audit
        if self._cached_base is None:
            self._cached_base = self._compute_base()
        return self._cached_base

    def _col_values(self, col: str) -> list:
        base = self._base_of_mode()
        if base is None or base.empty or col not in base.columns:
            return []
        return _format_col_values(col, base[col]).unique().tolist()

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
        self._refresh()

    # ------------------------------------------------------------- MODES ---
    def _on_mode_change(self, idx: int):
        new_mode = "audit" if idx == 1 else "ringkas"
        if new_mode == "audit" and (self.audit_df is None
                                    or self.audit_df.empty):
            # tidak ada data audit — balik ke ringkas + pesan jelas
            self.mode_seg.set_active_silent(0)
            self.status_var.set(
                "⚠ Sheet '29 Rekap Barang Masuk' tidak ditemukan — jalankan "
                "pipeline / cek RootPath (mode Audit tidak tersedia).")
            return
        self.mode = new_mode
        # default 'Hanya Selisih ≠ 0' per mode (audit: ON — fokus anomali)
        self.only_selisih_var.set(self.mode == "audit")
        self._reset_filter_states()
        self._apply_mode_columns()
        self._render_kpi_chips()
        self._refresh()

    # ------------------------------------------------------- COMPUTE ----
    def _compute_base(self) -> pd.DataFrame:
        """Mode Ringkas — pivot append1 → 1 baris per (Resto, Tanggal,
        Barang) dengan IN / BM / Selisih + satuan + kategori (v3.5)."""
        df = self.data
        if df is None or df.empty:
            return pd.DataFrame()

        self._ensure_maps(df)

        m = df[df["JENIS"].isin(["4.IN", "5.BARANG MASUK", "7.Selisih IN"])]
        if m.empty:
            return pd.DataFrame()

        tnum = pd.to_numeric(m["Tanggal"], errors="coerce")
        m = m.assign(_tgl=tnum)

        piv = m.pivot_table(
            index=["NAMA RESTO", "Nama Barang", "_tgl"],
            columns="JENIS", values="NILAI",
            aggfunc="sum", fill_value=0,
        ).reset_index()
        piv.columns.name = None

        for col in ("4.IN", "5.BARANG MASUK", "7.Selisih IN"):
            if col not in piv.columns:
                piv[col] = 0.0
            piv[col] = pd.to_numeric(piv[col], errors="coerce").fillna(0)

        # aktivitas: baris dengan IN≠0 atau BM≠0 (baris full-nol tidak
        # informatif — data user bisa 86k baris nol)
        piv = piv[(piv["4.IN"] != 0) | (piv["5.BARANG MASUK"] != 0)]
        if piv.empty:
            return pd.DataFrame()

        piv = piv.rename(columns={
            "NAMA RESTO": "Resto",
            "Nama Barang": "Nama Barang",
            "_tgl": "Tanggal",
            "4.IN": "IN",
            "5.BARANG MASUK": "Barang Masuk",
            "7.Selisih IN": "Selisih IN",
        })
        # selisih konsisten dgn metric (BM - IN) — recompute agar aman
        piv["Selisih IN"] = piv["Barang Masuk"] - piv["IN"]

        barang_s = piv["Nama Barang"].astype(str)
        resto_s = piv["Resto"].astype(str)
        piv["Satuan"] = [self._satuan_map.get((b, r), "-")
                         for b, r in zip(barang_s, resto_s)]
        piv["KATEGORI"] = [self._kategori_map.get(b, "-")
                           for b in barang_s]

        return piv.sort_values(["Resto", "Tanggal", "Nama Barang"],
                               na_position="last").reset_index(drop=True)

    def _compute_audit_display(self) -> pd.DataFrame:
        """Mode Audit — hasil engine VBA (fn_rekap29) + kolom tampilan.

        Baris & status PERSIS output macro (tidak difilter apa pun);
        kolom 'Nama Item'/'UoM' VBA ditampilkan sbg 'Nama Barang'/'Satuan'
        (app-consistent)."""
        df = self.audit_df
        if df is None or df.empty:
            return pd.DataFrame()
        if self.data is not None and not self.data.empty:
            self._ensure_maps(self.data)

        out = pd.DataFrame({
            "Resto": df["Resto"].astype(str),
            "Tanggal": pd.to_numeric(df["Tanggal"], errors="coerce"),
            "Nama Barang": df["Nama Item"].astype(str),
            "Satuan": df["UoM"].astype(str),
            "Hasil SO": pd.to_numeric(df["Hasil SO"], errors="coerce"),
            "Qty SO Harian": pd.to_numeric(df["Qty SO Harian"], errors="coerce"),
            "Penerimaan Sistem": pd.to_numeric(df["Penerimaan Sistem"], errors="coerce"),
            "Selisih Harian": pd.to_numeric(df["Selisih Harian"], errors="coerce"),
            "Saldo Kumulatif": pd.to_numeric(df["Saldo Kumulatif"], errors="coerce"),
            "Status Analisis Audit": df["Status Analisis Audit"].astype(str),
            "Detail & Catatan Audit": df["Detail & Catatan Audit"].astype(str),
        })
        barang_s = out["Nama Barang"]
        out.insert(3, "KATEGORI",
                   [self._kategori_map.get(b, "-") for b in barang_s])
        return out

    def _ensure_maps(self, df):
        """Lookup satuan per (barang, resto) + kategori per barang (v3.5)."""
        if not self._satuan_map and "SATUAN" in df.columns:
            sat = (df[["Nama Barang", "NAMA RESTO", "SATUAN"]]
                   .dropna(subset=["SATUAN"])
                   .drop_duplicates(subset=["Nama Barang", "NAMA RESTO"],
                                    keep="first"))
            self._satuan_map = {
                (str(b), str(r)): str(s)
                for b, r, s in zip(sat["Nama Barang"], sat["NAMA RESTO"],
                                   sat["SATUAN"])
            }
        if not self._kategori_map and "KATEGORI" in df.columns:
            kat = (df[["Nama Barang", "KATEGORI"]]
                   .dropna(subset=["KATEGORI"])
                   .drop_duplicates(subset=["Nama Barang"], keep="first"))
            self._kategori_map = {
                str(b): str(k)
                for b, k in zip(kat["Nama Barang"], kat["KATEGORI"])
            }

    # ------------------------------------------------------------- REFRESH
    def _refresh(self, sync: bool = False):
        audit_ok = self.audit_df is not None and not self.audit_df.empty
        if (self.data is None or self.data.empty) and not audit_ok:
            self.status_var.set("Belum ada data.")
            return
        if self.mode == "audit" and not audit_ok:
            self.status_var.set("⚠ Sheet '29 Rekap Barang Masuk' tidak "
                                "ditemukan — mode Audit tidak tersedia.")
            return
        if self._busy:
            self._pending = True
            return
        self._busy = True
        try:
            tgl_start = int(float(self.tgl_start_var.get()))
        except (TypeError, ValueError):
            tgl_start = 1
        try:
            tgl_end = int(float(self.tgl_end_var.get()))
        except (TypeError, ValueError):
            tgl_end = 31
        st = {
            "mode": self.mode,
            "tgl_start": tgl_start,
            "tgl_end": tgl_end,
            "only_selisih": self.only_selisih_var.get(),
            "col_sel": {c: s for c, s in self._col_sel.items() if s},
        }

        def work():
            if self.mode == "audit":
                if self._cached_audit is None:
                    self._cached_audit = self._compute_audit_display()
            elif self._cached_base is None:
                self._cached_base = self._compute_base()
            return self._prepare_rows(st)

        def done(payload):
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung rekap Selisih IN…", sync=sync)

    def _prepare_rows(self, st: dict) -> dict:
        base = self._cached_audit if st["mode"] == "audit" else self._cached_base
        if base is None or base.empty:
            return {"items": [], "status": "Tidak ada data."}

        f = base
        # rentang tanggal — display-only (audit tetap dihitung dari sheet
        # penuh; ini hanya menyembunyikan baris dari tampilan)
        if st["tgl_start"] is not None and st["tgl_end"] is not None:
            t = pd.to_numeric(f["Tanggal"], errors="coerce")
            f = f[(t >= st["tgl_start"]) & (t <= st["tgl_end"])]

        # v3.5: filter header ⧩ — kecocokan nilai TERFORMAT (identik dgn
        # yang tampil di tabel)
        for col, sel in st["col_sel"].items():
            if col in f.columns:
                fmt = _format_col_values(col, f[col])
                f = f[fmt.isin(sel)]

        sel_col = "Selisih Harian" if st["mode"] == "audit" else "Selisih IN"
        if st["only_selisih"] and sel_col in f.columns:
            sv = pd.to_numeric(f[sel_col], errors="coerce").fillna(0)
            f = f[sv != 0]

        if f.empty:
            return {"items": [], "status": "Tidak ada data setelah filter."}

        is_audit = st["mode"] == "audit"
        cols_def = AUDIT_COLUMNS if is_audit else RINGKAS_COLUMNS
        col_ids = [c[0] for c in cols_def]

        # format kolom sekali (vektor per kolom — lebih cepat dari per-sel)
        formatted = {}
        for c in col_ids:
            if c in f.columns:
                formatted[c] = _format_col_values(c, f[c]).tolist()

        if is_audit:
            status_s = f["Status Analisis Audit"].astype(str).tolist()
        else:
            sel_np = pd.to_numeric(f["Selisih IN"], errors="coerce") \
                .fillna(0).to_numpy()

        resto_np = f["Resto"].astype(str).to_numpy()
        barang_np = f["Nama Barang"].astype(str).to_numpy()
        tgl_np = pd.to_numeric(f["Tanggal"], errors="coerce").to_numpy()

        n = len(f)
        items = []
        keys = []
        for i in range(n):
            values = tuple(formatted[c][i] for c in col_ids)
            tags = []
            if is_audit:
                st_tag = _STATUS_TAG.get(status_s[i])
                if st_tag:
                    tags.append(st_tag)
                else:
                    tags.append("evenrow" if i % 2 == 0 else "oddrow")
            else:
                sel = sel_np[i]
                if sel < 0:
                    tags.append("negative")
                elif sel == 0:
                    tags.append("zero")
                tags.append("evenrow" if i % 2 == 0 else "oddrow")
            items.append(("", f"row_{i}", {"values": values,
                                            "tags": tuple(tags)}))
            # key utk drill-down: (resto, barang, tgl asli)
            t = tgl_np[i]
            keys.append((resto_np[i], barang_np[i],
                         None if pd.isna(t) else int(t)))

        # ringkasan status (mode audit)
        if is_audit:
            status_txt = f"{n} baris · " + " · ".join(
                f"{k}: {v:,}" for k, v in
                pd.Series(status_s).value_counts().head(3).items())
        else:
            total_in = float(pd.to_numeric(f["IN"], errors="coerce").sum())
            total_bm = float(pd.to_numeric(f["Barang Masuk"], errors="coerce").sum())
            total_sel = float(pd.to_numeric(f["Selisih IN"], errors="coerce").sum())
            status_txt = (f"{n} baris · Total IN {_fmt_num(total_in)} · "
                          f"BM {_fmt_num(total_bm)} · Selisih {_fmt_num(total_sel)}")
        return {"items": items, "status": status_txt, "keys": keys}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        if self.header_filters is not None:
            self.header_filters.refresh_icons()
        self.status_var.set(payload["status"])
        self._keys = payload.get("keys", [])

        def render_done():
            self._busy = False
            if self._pending:
                self._pending = False
                self._refresh()

        insert_tree_items(self.tree, payload["items"], batch=500,
                          on_done=render_done)

    # ------------------------------------------------------------ FILTERS
    def _on_tanggal_change(self):
        try:
            s = int(float(self.tgl_start_var.get()))
            e = int(float(self.tgl_end_var.get()))
            if not (-31 <= s <= 31 and -31 <= e <= 31):
                raise ValueError
            if s > e:
                s, e = e, s
                self.tgl_start_var.set(str(s))
                self.tgl_end_var.set(str(e))
            self._refresh()
        except ValueError:
            self.status_var.set("Tanggal harus angka -31..31 (contoh: 1–31).")

    def _reset_filter(self):
        self.tgl_start_var.set("1")
        self.tgl_end_var.set("31")
        self.only_selisih_var.set(self.mode == "audit")
        self._reset_filter_states()
        self._refresh()

    # -------------------------------------------------------------- SORT
    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        if self._busy and tree is None:
            return  # render batch masih berjalan — sort ditunda
        tree = tree if tree is not None else self.tree
        sort_tree_by_column(tree, col, reverse=reverse)

    def _auto_fit(self):
        """v3.4 — auto-fit lebar semua kolom ke konten."""
        auto_fit_columns(self.tree)

    # ------------------------------------------------- ⛶ PERBESAR (clone)
    def _maximize(self):
        def sort_setup(new_tree):
            for col_name, _, _ in (AUDIT_COLUMNS if self.mode == "audit"
                                   else RINGKAS_COLUMNS):
                new_tree.heading(col_name, text=col_name,
                                 command=lambda c=col_name, t=new_tree:
                                 self._sort_by(c, tree=t))

        title = ("Audit Rekonsiliasi — LAPORAN DEVIASI"
                 if self.mode == "audit" else "Rekap Selisih IN")
        win, new_tree = open_tree_maximized(
            self.tree, title,
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_sort_setup=sort_setup)
        return win, new_tree

    # ------------------------------------------------- DOUBLE-CLICK POPUP
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
        col_ids = list(tree["columns"])
        row = dict(zip(col_ids, values))
        resto = row.get("Resto")
        barang = row.get("Nama Barang")
        tgl_txt = str(row.get("Tanggal") or "")
        if not barang or not tgl_txt:
            return
        try:
            tgl = int(float(tgl_txt.replace(",", "")))
        except (TypeError, ValueError):
            return

        det = self._detail_for(resto, barang, tgl)
        if det is None:
            return

        # ringkasan utk chip popup (nilai mentah dari baris — audit:
        # Qty SO Harian & Selisih Harian; ringkas: BM & Selisih IN)
        def _num(v):
            s = str(v).replace(",", "").strip()
            if s in ("", "-", "None"):
                return 0.0
            if s.startswith("(") and s.endswith(")"):
                return -float(s[1:-1])
            try:
                return float(s)
            except ValueError:
                return 0.0

        if self.mode == "audit":
            row_summary = {
                "bm": _num(row.get("Qty SO Harian")),
                "selisih": _num(row.get("Selisih Harian")),
            }
        else:
            row_summary = {
                "bm": _num(row.get("Barang Masuk")),
                "selisih": _num(row.get("Selisih IN")),
            }
        InDetailPopup(self.winfo_toplevel(), resto, barang, tgl, det,
                      row_summary=row_summary)

    def _detail_for(self, resto, barang, tgl) -> Optional[pd.DataFrame]:
        """Ambil detail IN utk (resto, barang, tgl)."""
        det = self.in_detail
        if det is None or det.empty:
            # tidak ada detail IN (mis. sumber 42.05/3224/9901 kosong) —
            # tampilkan popup kosong supaya user tahu tidak ada dokumen
            return pd.DataFrame(columns=["NAMA RESTO", "Nama Barang",
                                         "Tanggal", "Value", "Nomor",
                                         "Nomor PO", "#Tgl/Jam Pembuatan IT",
                                         "SOURCE IN", "JENIS"])
        d = det
        d = d[d["NAMA RESTO"].astype(str) == str(resto)]
        d = d[d["Nama Barang"].astype(str) == str(barang)]
        t = pd.to_numeric(d["Tanggal"], errors="coerce")
        d = d[t == tgl]
        if d.empty:
            return d
        return d.reset_index(drop=True)

    # ------------------------------------------------------------ SHOW ---
    def _show_empty(self):
        self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)
        # posisi kpi_card dikelola penuh oleh _render_kpi_chips()
        # (pack before tabel card / pack_forget)
