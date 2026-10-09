"""
in_selisih_view.py — Tab "📤 Rekap Selisih IN" (v3.4 → v3.6).

Permintaan user (v3.4): "Tambah 1 tab lagi untuk rekap Selisih IN dan kolom
Resto, tanggal, nama barang, satuan, IN, Barang masuk dan selisih IN
dan bisa drill down atau pop up muncul rincian IN yaitu 42.05, 3224,
dan 9901 beserta nomor nya."

v3.6 (permintaan user: "audit rekonsiliasi tidak perlu ambil dari sheet
29 — aplikasikan logika nya dengan tambah kolom SO dan kolom hasil audit
nya, bisa difilter"):
- SATU tabel (segment Ringkas|Audit dihapus) — baris per (Resto, Tanggal,
  Barang) dihitung pipeline fn_audit dari DATA APP (rekap SO + BARANG
  MASUK + IN per tanggal; sheet '29 Rekap Barang Masuk' TIDAK dibaca):
    IN            = Penerimaan Sistem (Accurate: 42.05 + 32.24 + 99.01)
    Barang Masuk  = Qty SO Harian (input rekap JENIS='BARANG MASUK')
    Selisih IN    = Barang Masuk − IN
    Hasil SO      = kolom SO (rekap JENIS='SO'; hadir hanya di tanggal
                    yang SO benar-benar direkam — sel '-' = tidak ada SO)
    Saldo         = saldo kumulatif per (Resto × Barang) urut tanggal
    Hasil Audit   = port macro VBA BuatLaporanDeviasiSampel — VALID
                    (Sistem Masuk) / OK (Matching) / CUT-OFF RESOLVED /
                    OK (Dalam Cut-off) / DEVIASI MURNI
- Semua kolom difilter via header ⧩ (display-only: saldo & status
  dihitung dari data penuh, tidak terpotong rentang tanggal).
- v3.6: klik kanan heading / tombol ◱ Kolom = sembunyikan/tampilkan
  kolom; window ⛶ punya filter + sort sendiri.

Drill-down (double-click baris) → popup RINCIAN IN per dokumen:
  - ringkasan per sumber: 42.05 / 32.24 / 99.01 (+ 32.24 bulan lalu)
  - tabel dokumen: Source | Nomor | Nomor PO | Qty | #Tgl/Jam
  - copy Nomor (klik kanan / double-click cell / tombol Semua Nomor)
  - ⛶ Perbesar + ↔ Auto-Fit + Esc

Tanggal -25..-31 = data bulan lalu (selalu terbaca — LightMode dihapus v3.5).
v3.8: Default rentang 1 s/d 31 = periode BULAN BERJALAN saja (tanpa
bulan lalu — permintaan user "rekap selisih in hanya periode 1-31").
v3.6 (lama): default -26 s/d 31.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import contextlib
import pandas as pd
from typing import Callable, Optional

from .theme import (
    C_BG, C_CARD, C_HEADER, C_TEXT_MUTED, C_ACCENT_DARK, font,
)
from .widgets import (
    Card, EmptyState, GhostButton, HeaderFilterGroup, LoadingOverlay,
    ColumnManager, TableExpander, attach_clone_filters,
    auto_fit_columns, enable_col_resize, identify_to_column,
    insert_tree_items, open_tree_maximized, run_async, sort_tree_by_column,
    fmt_int_id, validated_tgl_entry, apply_cell_tag, CELL_TAGS_SUPPORTED,
)
from .export_sheets import (
    AUDIT_EXPORT_COLUMNS, build_selisih_export_df, write_selisih_sheet,
)

# --- Kolom tabel (v3.6: SATU tabel — Ringkas + Audit digabung) -------------
COLUMNS = [
    ("Resto", 74, "w"),
    ("Tanggal", 64, "e"),
    ("Nama Barang", 200, "w"),
    ("KATEGORI", 110, "w"),
    ("Satuan", 56, "w"),
    ("Hasil SO", 90, "e"),         # ← kolom SO (v3.6)
    ("Barang Masuk", 110, "e"),    # = Qty SO Harian (input rekap)
    ("IN", 96, "e"),               # = Penerimaan Sistem (42.05+32.24+99.01)
    ("Selisih IN", 100, "e"),      # = Barang Masuk − IN
    ("Saldo", 100, "e"),           # saldo kumulatif audit
    ("Hasil Audit", 150, "w"),     # ← kolom hasil audit (v3.6)
    ("Catatan Audit", 260, "w"),
]

_ALL_COLS = [c[0] for c in COLUMNS]

# Kolom numerik (utk format & filter nilai)
_NUM_COLS = {"Hasil SO", "Barang Masuk", "IN", "Selisih IN", "Saldo"}

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
    # FIX C-03: format angka gaya Indonesia — 1.234.567 / 1.234,5
    # (sebelumnya koma gaya Inggris: 1,234,567 / 1,234.5).
    if v == int(v):
        s = fmt_int_id(v)
    else:
        s = f"{v:,.1f}".replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")
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
        # v3.9.2: minus merah PER CELL (kolom Qty) — fallback Tk 8 per baris
        self._cell_tags = CELL_TAGS_SUPPORTED
        self._neg_cells: list = []

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
        tree.tag_configure("neg_cell", foreground="#dc2626")  # v3.9.2
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
        neg_cells = []   # v3.9.2 — per-cell minus (kolom Qty)
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
                    # v3.9.2: minus merah PER CELL (kolom Qty saja) —
                    # sebelumnya satu nilai minus membuat SELURUH BARIS merah
                    if self._cell_tags:
                        neg_cells.append((f"doc_{len(items)}", "Qty"))
                    else:
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
        self._neg_cells = neg_cells

        def _done():
            # v3.9.2: pasang tag PER-CELL setelah semua baris ter-insert
            self._reapply_cell_tags(self.tree)

        insert_tree_items(self.tree, items, batch=400, on_done=_done)

    def _reapply_cell_tags(self, tree):
        """v3.9.2 — pasang ulang tag per-cell minus (juga utk clone ⛶)."""
        if self._cell_tags and self._neg_cells:
            apply_cell_tag(tree, "neg_cell", self._neg_cells)

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
        # v3.7 FIX (deep audit): resolve posisi-display → NAMA kolom
        # aktual — dulu index posisi ke _POPUP_IDS (urutan LOGIS) → setelah
        # kolom disembunyikan (clone ⛶ punya ColumnManager), double-click
        # men-copy nilai kolom yang SALAH.
        col = tree.identify_column(event.x)
        col_name = identify_to_column(tree, col)
        if col_name in ("Nomor", "Nomor PO"):
            val = tree.set(iid, col_name)
            if val:
                self._copy_to_clipboard(val, col_name)
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
            on_context_menu=self._on_context_menu,
            on_render_done=self._reapply_cell_tags)  # v3.9.2 per-cell


# =============================================================================
# VIEW UTAMA — Rekap Selisih IN (Ringkas + Audit Rekonsiliasi)
# =============================================================================

class InSelisihView(tk.Frame):
    """Rekap Selisih IN + Audit Rekonsiliasi (v3.6: logika macro VBA × data
    app — tanpa sheet 29; SATU tabel dgn kolom SO & Hasil Audit yang bisa
    difilter lewat header ⧩)."""

    def __init__(self, parent, go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self.in_detail: Optional[pd.DataFrame] = None
        self.audit_df: Optional[pd.DataFrame] = None
        self.audit_kpi: dict = {}
        self.audit_desc: str = ""
        self.go_to_proses = go_to_proses
        self._col_sel: dict = {c: None for c in _ALL_COLS}   # header filter ⧩
        self._busy = False
        self._pending = False
        self._dirty = False            # lazy refresh (ala v3.2)
        self._cached_base: pd.DataFrame | None = None
        self._satuan_map: dict = {}
        self._kategori_map: dict = {}
        self._keys: list = []
        self.header_filters: HeaderFilterGroup | None = None
        self._colmgr: ColumnManager | None = None

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
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card (v3.5: RESTO combo DIHAPUS → header filter ⧩) ---
        fcard = Card(self.content, title="Filter")
        fcard.pack(fill="x", padx=12, pady=(12, 0))
        fbody = fcard.body()

        r0 = tk.Frame(fbody, bg=C_CARD)
        r0.pack(fill="x")
        tk.Label(r0, text="TANGGAL", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self.tgl_start_var = tk.StringVar(value="1")  # v3.8: 1–31 berjalan saja
        entry_start = ttk.Entry(r0, textvariable=self.tgl_start_var, width=6)
        entry_start.pack(side="left", padx=(6, 2))
        entry_start.bind("<Return>", lambda e: self._on_tanggal_change())
        tk.Label(r0, text="–", bg=C_CARD, fg=C_TEXT_MUTED).pack(side="left")
        self.tgl_end_var = tk.StringVar(value="31")  # v3.6: 31 BULAN BERJALAN
        entry_end = ttk.Entry(r0, textvariable=self.tgl_end_var, width=6)
        entry_end.pack(side="left", padx=(2, 8))
        entry_end.bind("<Return>", lambda e: self._on_tanggal_change())
        GhostButton(r0, text="Apply", command=self._on_tanggal_change).pack(
            side="left", padx=(0, 18))

        self.only_selisih_var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(
            r0, text="Hanya Selisih ≠ 0",
            variable=self.only_selisih_var,
            command=self._refresh)
        chk.pack(side="left")

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
            head, text="Rekap Selisih IN & Audit Rekonsiliasi — BM vs IN + "
                       "Hasil SO",
            bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        self.title_label.pack(side="left")
        # v3.9 (ala Waste): ⛶ = Layar Penuh (window terpisah)
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        # v3.9 (ala Waste): ⤢ = Perbesar Tabel (in-place)
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel")
        btn_expand.pack(side="right", padx=(0, 6))
        # v3.8: export rekap Selisih IN per resto (permintaan user)
        btn_export = GhostButton(head, text="💾 Export",
                                 command=self._on_export)
        btn_export.pack(side="right", padx=(0, 6))
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))

        self.tree = ttk.Treeview(tbody, columns=[c[0] for c in COLUMNS],
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
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(8, "bold")).pack(side="right")

        self.overlay = LoadingOverlay(tbody, "Menghitung rekap Selisih IN…")

        # v3.9 (ala Waste): ⤢ Perbesar Tabel — ciutkan kartu Filter + KPI
        # chips + judul; tombol toolbar tetap tampil utk mengembalikan.
        self._expander = TableExpander(
            btn_expand, [fcard, self.kpi_card, self.title_label])

        self._apply_columns()

        self.tree.bind("<Double-1>", self._on_double_click)

    def _apply_columns(self):
        """(Re)pasang kolom tree + heading + HeaderFilterGroup +
        ColumnManager (v3.6: satu set kolom — tanpa mode)."""
        # lepas binding filter lama dulu — mencegah binding ganda saat
        # kolom dikonfigurasi ulang (HeaderFilter.bind add="+")
        if self.header_filters is not None:
            self.header_filters.detach_all()
            self.header_filters = None

        col_ids = [c[0] for c in COLUMNS]
        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=col_ids)
        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=40,
                             anchor=anchor)
            # sort via popup filter — klik heading membuka popup ⧩
            self.tree.heading(col_name, text=col_name)

        # buang state filter kolom yang tidak dikenal
        for c in list(self._col_sel.keys()):
            if c not in col_ids:
                self._col_sel[c] = None

        # filter header ⧩ di SEMUA kolom (incl. SO & Hasil Audit)
        self.header_filters = HeaderFilterGroup(
            self.tree, col_ids,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        # v3.6: hide/unhide kolom (sekali saja — columns() dibaca live)
        if self._colmgr is None:
            self._colmgr = ColumnManager(
                self.tree,
                open_filter=lambda c: self.header_filters and
                self.header_filters.open_popup(c))
        else:
            # v3.7: pastikan state kolom tersembunyi tetap diterapkan
            # setelah reconfigure columns (defensive — displaycolumns
            # bisa di-reset Tk saat kolom dikonfigurasi ulang)
            self._colmgr.apply()

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
        self._satuan_map = {}
        self._kategori_map = {}
        self._show_content()
        # v3.9: pulihkan layout bila sedang di-perbesar ⤢ (kpi_card akan
        # di-pack ulang oleh _render_kpi_chips di bawah)
        if getattr(self, "_expander", None) is not None:
            self._expander.reset()
        self._apply_columns()
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
        """KPI 'EXECUTIVE RECONCILIATION SUMMARY' — dihitung dari data
        penuh (tidak terpengaruh filter tampilan)."""
        for w in self.kpi_inner.winfo_children():
            w.destroy()
        if not self.audit_kpi:
            self.kpi_card.pack_forget()
            return
        k = self.audit_kpi
        # FIX C-03: KPI chips ikut format Indonesia (1.234.567, bukan
        # 1,234,567) — konsisten dgn formatter tabel.
        chips = [
            ("TOTAL BARIS", f"{k.get('rows', 0):,}", "#0f766e"),
            ("OK (MATCHING)", fmt_int_id(k.get('ok', 0)), "#16a34a"),
            ("VALID (SISTEM MASUK)", fmt_int_id(k.get('omit', 0)), "#1f4e78"),
            ("CUT-OFF RESOLVED", fmt_int_id(k.get('cutoff', 0)), "#806000"),
            ("DEVIASI MURNI", fmt_int_id(k.get('deviasi_murni', 0)), "#c65911"),
            ("SISA GANTUNG (NET)",
             fmt_int_id(k.get('deviasi_qty', 0.0)),
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
    def _col_values(self, col: str) -> list:
        base = self._cached_base
        if base is None:
            base = self._compute_base()
            self._cached_base = base
        if base is None or base.empty or col not in base.columns:
            return []
        return _format_col_values(col, base[col]).unique().tolist()

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
        self._refresh()

    # ------------------------------------------------------- COMPUTE ----
    def _compute_base(self) -> pd.DataFrame:
        """Bangun tabel tampilan dari hasil audit fn_audit (data app) +
        map Satuan/KATEGORI (v3.6)."""
        df = self.audit_df
        if df is None or df.empty:
            return pd.DataFrame()
        if self.data is not None and not self.data.empty:
            self._ensure_maps(self.data)

        out = pd.DataFrame({
            "Resto": df["Resto"].astype(str),
            "Tanggal": pd.to_numeric(df["Tanggal"], errors="coerce"),
            "Nama Barang": df["Nama Item"].astype(str),
            "Hasil SO": pd.to_numeric(df["Hasil SO"], errors="coerce"),
            "Barang Masuk": pd.to_numeric(df["Qty SO Harian"],
                                           errors="coerce"),
            "IN": pd.to_numeric(df["Penerimaan Sistem"], errors="coerce"),
            "Selisih IN": pd.to_numeric(df["Selisih Harian"],
                                         errors="coerce"),
            "Saldo": pd.to_numeric(df["Saldo Kumulatif"], errors="coerce"),
            "Hasil Audit": df["Status Analisis Audit"].astype(str),
            "Catatan Audit": df["Detail & Catatan Audit"].astype(str),
        })
        # v3.8: komponen IN per sumber (utk 💾 Export per resto — kolom
        # Kiriman HO / Kiriman Supplier / Pembelian by Resto; tidak
        # ditampilkan di tabel, hanya dibawa oleh base)
        for col_out, col_in in (("42.05", "Qty SJ"),
                                 ("32.24", "Qty RI"),
                                 ("99.01", "Qty Pembelian")):
            out[col_out] = pd.to_numeric(df.get(col_in),
                                         errors="coerce") \
                if col_in in df.columns else pd.Series(
                    [pd.NA] * len(out), dtype="Float64")
        out.insert(3, "KATEGORI",
                   [self._kategori_map.get(b, "-")
                    for b in out["Nama Barang"]])
        out["Satuan"] = [self._satuan_map.get((b, r), "-")
                          for b, r in zip(out["Nama Barang"],
                                          out["Resto"])]
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
        if (self.audit_df is None or self.audit_df.empty) and \
                (self.data is None or self.data.empty):
            self.status_var.set("Belum ada data.")
            return
        if self._busy:
            self._pending = True
            return
        self._busy = True
        # FIX B-02: validasi konsisten (warning + revert) — sebelumnya
        # fallback senyap ke 1/31.
        tgl_start = validated_tgl_entry(self.tgl_start_var, lo=-31, hi=31,
                                        fallback=1, label="Tanggal awal",
                                        parent=self)
        tgl_end = validated_tgl_entry(self.tgl_end_var, lo=-31, hi=31,
                                      fallback=31, label="Tanggal akhir",
                                      parent=self)
        st = {
            "tgl_start": tgl_start,
            "tgl_end": tgl_end,
            "only_selisih": self.only_selisih_var.get(),
            "col_sel": {c: s for c, s in self._col_sel.items() if s},
        }

        def work():
            if self._cached_base is None:
                self._cached_base = self._compute_base()
            return self._prepare_rows(st)

        def done(payload):
            self._render_rows(payload)

        # FIX B-01: _busy wajib di-reset saat compute GAGAL — tanpa ini
        # view mati permanen setelah 1x error (filter/reset ditelan senyap).
        def on_error(err):
            self._busy = False
            self._pending = False
            self.status_var.set(f"⚠ Gagal menghitung rekap Selisih IN: {err}")

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung rekap Selisih IN…",
                  on_error=on_error, sync=sync)

    def _prepare_rows(self, st: dict) -> dict:
        base = self._cached_base
        if base is None or base.empty:
            return {"items": [], "status": "Tidak ada data."}

        f = base
        # rentang tanggal — display-only (audit dihitung dari data penuh;
        # ini hanya menyembunyikan baris dari tampilan)
        if st["tgl_start"] is not None and st["tgl_end"] is not None:
            t = pd.to_numeric(f["Tanggal"], errors="coerce")
            f = f[(t >= st["tgl_start"]) & (t <= st["tgl_end"])]

        # filter header ⧩ — kecocokan nilai TERFORMAT (identik dgn
        # yang tampil di tabel)
        for col, sel in st["col_sel"].items():
            if col in f.columns:
                fmt = _format_col_values(col, f[col])
                f = f[fmt.isin(sel)]

        if st["only_selisih"] and "Selisih IN" in f.columns:
            sv = pd.to_numeric(f["Selisih IN"], errors="coerce").fillna(0)
            f = f[sv != 0]

        if f.empty:
            return {"items": [], "status": "Tidak ada data setelah filter."}

        col_ids = [c[0] for c in COLUMNS]

        # format kolom sekali (vektor per kolom — lebih cepat dari per-sel)
        formatted = {}
        for c in col_ids:
            if c in f.columns:
                formatted[c] = _format_col_values(c, f[c]).tolist()

        status_s = f["Hasil Audit"].astype(str).tolist()

        resto_np = f["Resto"].astype(str).to_numpy()
        barang_np = f["Nama Barang"].astype(str).to_numpy()
        tgl_np = pd.to_numeric(f["Tanggal"], errors="coerce").to_numpy()

        n = len(f)
        items = []
        keys = []
        for i in range(n):
            values = tuple(formatted[c][i] for c in col_ids)
            st_tag = _STATUS_TAG.get(status_s[i])
            tags = [st_tag] if st_tag else \
                ["evenrow" if i % 2 == 0 else "oddrow"]
            items.append(("", f"row_{i}", {"values": values,
                                            "tags": tuple(tags)}))
            # key utk drill-down: (resto, barang, tgl asli)
            t = tgl_np[i]
            keys.append((resto_np[i], barang_np[i],
                         None if pd.isna(t) else int(t)))

        # ringkasan status
        status_txt = f"{n} baris · " + " · ".join(
            f"{k}: {v:,}" for k, v in
            pd.Series(status_s).value_counts().head(3).items())
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

    # --------------------------------------------------------- EXPORT --
    def _export_options_dialog(self):
        """v3.9 — dialog opsi export: tambah kolom hasil audit atau tidak.

        Permintaan user: "waktu ekspor tambahin hasil auditnya aja tapi ada
        opsi buat tambahin kolom tersebut atau tidak". Return list kolom
        audit terpilih (bisa kosong) atau None bila dibatalkan.
        """
        parent = self.winfo_toplevel()
        win = tk.Toplevel(parent)
        win.title("Opsi Export — Rekap Selisih IN")
        win.configure(bg=C_CARD)
        win.transient(parent)
        win.resizable(False, False)
        with contextlib.suppress(Exception):
            win.grab_set()

        result = {"cols": None}

        body = tk.Frame(win, bg=C_CARD)
        body.pack(fill="both", expand=True, padx=16, pady=14)

        tk.Label(body, text="💾 Export Rekap Selisih IN per Resto",
                 bg=C_CARD, fg=C_HEADER, font=font(11, "bold")).pack(
            anchor="w")

        vars_ = {}
        for col in AUDIT_EXPORT_COLUMNS:
            v = tk.BooleanVar(value=True)
            vars_[col] = v
            row = tk.Frame(body, bg=C_CARD)
            row.pack(fill="x", pady=2)
            cb = ttk.Checkbutton(row, text=col, variable=v)
            cb.pack(side="left")

        btns = tk.Frame(body, bg=C_CARD)
        btns.pack(fill="x", pady=(12, 0))

        def _ok():
            result["cols"] = [c for c, v in vars_.items() if v.get()]
            win.destroy()

        from .widgets import AccentButton
        AccentButton(btns, text="💾 Export Sekarang", command=_ok).pack(
            side="right")
        GhostButton(btns, text="Tanpa Kolom Audit",
                    command=lambda: (result.update(cols=[]),
                                     win.destroy())).pack(
            side="right", padx=(0, 8))
        GhostButton(btns, text="✕ Batal",
                    command=win.destroy).pack(side="left")

        win.bind("<Escape>", lambda e: win.destroy())
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()
                                     - win.winfo_reqwidth()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height()
                                     - win.winfo_reqheight()) // 2
        win.geometry(f"+{max(px, 0)}+{max(py, 0)}")
        win.wait_window()
        return result["cols"]

    def _on_export(self):
        """v3.8/v3.9 — Export rekap Selisih IN per resto ke Excel.

        Dialog opsi (v3.9) → pilih file → export async. Semua baris dalam
        rentang tanggal aktif (default 1–31 bulan berjalan); filter
        tampilan (⧩ / Hanya Selisih ≠ 0) tidak ikut — export = REKAP
        lengkap per resto + kolom hasil audit sesuai pilihan.
        """
        if (self.audit_df is None or self.audit_df.empty) and \
                (self.data is None or self.data.empty):
            messagebox.showwarning(
                "Export", "Belum ada data. Jalankan pipeline dulu.",
                parent=self.winfo_toplevel())
            return
        audit_cols = self._export_options_dialog()
        if audit_cols is None:
            return          # dibatalkan
        filepath = filedialog.asksaveasfilename(
            title="Simpan Rekap Selisih IN per Resto",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="selisih_in_per_resto.xlsx",
            parent=self.winfo_toplevel(),
        )
        if not filepath:
            return
        self._do_export(filepath, audit_cols)

    def _do_export(self, filepath: str, audit_cols: list):
        """Export inti (v3.9) — dipisah dari _on_export supaya bisa
        dipanggil langsung oleh test tanpa dialog."""
        # FIX B-02: jalur export ikut validasi konsisten (bukan fallback
        # senyap ke 1/31 seperti sebelumnya).
        tgl_start = validated_tgl_entry(self.tgl_start_var, lo=-31, hi=31,
                                        fallback=1, label="Tanggal awal",
                                        parent=self)
        tgl_end = validated_tgl_entry(self.tgl_end_var, lo=-31, hi=31,
                                      fallback=31, label="Tanggal akhir",
                                      parent=self)
        if tgl_start > tgl_end:
            tgl_start, tgl_end = tgl_end, tgl_start

        def work():
            base = self._cached_base
            if base is None:
                base = self._compute_base()
            df = build_selisih_export_df(base, tgl_start, tgl_end,
                                         audit_cols=audit_cols)
            if df.empty:
                return None
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                write_selisih_sheet(writer, df)
            return filepath, len(df)

        def done(res):
            if res is None:
                messagebox.showwarning(
                    "Export", "Tidak ada baris dalam rentang tanggal "
                              f"{tgl_start}–{tgl_end}.",
                    parent=self.winfo_toplevel())
                return
            path, n = res
            self.status_var.set(
                f"Export {n:,} baris → {path}")
            messagebox.showinfo(
                "Export Berhasil",
                f"Rekap Selisih IN per resto ({n:,} baris)\n"
                f"di-export ke:\n{path}",
                parent=self.winfo_toplevel())

        def on_error(e):
            messagebox.showerror(
                "Export Gagal", f"Tidak bisa export:\n{e}",
                parent=self.winfo_toplevel())

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Mengekspor rekap Selisih IN…",
                  on_error=on_error)

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
        self.tgl_start_var.set("1")    # v3.8: 1–31 bulan berjalan saja
        self.tgl_end_var.set("31")
        self.only_selisih_var.set(True)
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
        def filter_setup(new_tree):
            # v3.6: funnel ⧩ + sort jalan juga di window besar
            attach_clone_filters(
                new_tree, [c[0] for c in COLUMNS],
                get_values=self._col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_by(c, reverse=d,
                                                               tree=t))

        win, new_tree = open_tree_maximized(
            self.tree, "Rekap Selisih IN & Audit Rekonsiliasi",
            setup_tags=lambda t: self._setup_tags(t),
            on_double_click=self._on_double_click,
            on_filter_setup=filter_setup)
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

        # ringkasan utk chip popup (nilai mentah dari baris)
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
