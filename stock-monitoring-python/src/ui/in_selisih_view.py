"""
in_selisih_view.py — Tab "📤 Rekap Selisih IN" (v3.4).

Permintaan user: "Tambah 1 tab lagi untuk rekap Selisih IN dan kolom
Resto, tanggal, nama barang, satuan, IN, Barang masuk dan selisih IN
dan bisa drill down atau pop up muncul rincian IN yaitu 42.05, 3224,
dan 9901 beserta nomor nya."

Tabel utama — 1 baris per (Resto × Tanggal × Barang × Satuan):
  Resto | Tanggal | Nama Barang | Satuan | IN | Barang Masuk | Selisih IN
  - IN            = metric "4.IN"  (Accurate: 42.05 + 32.24 + 99.01)
  - Barang Masuk  = metric "5.BARANG MASUK" (input rekap SO harian)
  - Selisih IN    = metric "7.Selisih IN"  (= Barang Masuk − IN)
  Baris ditampilkan bila ada aktivitas (IN ≠ 0 atau BM ≠ 0).

Drill-down (double-click baris) → popup RINCIAN IN per dokumen:
  - ringkasan per sumber: 42.05 / 32.24 / 99.01 (+ 32.24 bulan lalu)
  - tabel dokumen: Source | Nomor | Nomor PO | Qty | #Tgl/Jam
  - copy Nomor (klik kanan / double-click cell / tombol Semua Nomor)
  - ⛶ Perbesar + ↔ Auto-Fit + Esc

Tanggal -25..-31 = data bulan lalu (mode FULL / LightMode OFF).
"""
import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Callable, Optional

from .theme import (
    C_BG, C_CARD, C_HEADER, C_TEXT_MUTED, C_ACCENT_DARK, font,
)
from .widgets import (
    Card, EmptyState, GhostButton, HeaderFilter, LoadingOverlay, add_tooltip,
    auto_fit_columns, enable_col_resize, insert_tree_items,
    open_tree_maximized, run_async, sort_tree_by_column,
)

# Kolom tabel utama: (column_id, width, anchor)
COLUMNS = [
    ("Resto", 74, "w"),
    ("Tanggal", 64, "e"),
    ("Nama Barang", 200, "w"),
    ("Satuan", 56, "w"),
    ("IN", 96, "e"),
    ("Barang Masuk", 110, "e"),
    ("Selisih IN", 100, "e"),
]

COL_IDS = [c[0] for c in COLUMNS]

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
# VIEW UTAMA — Rekap Selisih IN
# =============================================================================

class InSelisihView(tk.Frame):
    """Rekap Selisih IN: Resto × Tanggal × Barang — IN vs Barang Masuk."""

    def __init__(self, parent, go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.data: Optional[pd.DataFrame] = None
        self.in_detail: Optional[pd.DataFrame] = None
        self.go_to_proses = go_to_proses
        self._name_selected: set | None = None
        self._busy = False
        self._pending = False
        self._dirty = False            # lazy refresh (ala v3.2)
        self._cached_base: pd.DataFrame | None = None
        self._satuan_map: dict = {}

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
                     "Masuk (dengan rincian dokumen 42.05 / 32.24 / 99.01).",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Filter card ---
        fcard = Card(self.content, title="Filter",
                     subtitle="Rentang tanggal 1-31 (tanggal -25 s/d -31 = "
                              "data bulan lalu, LightMode OFF). "
                              "Filter Nama Barang → klik header kolom (⧩).")
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
                    "lalu (hanya tersedia saat LightMode OFF).")
        GhostButton(r0, text="Apply", command=self._on_tanggal_change).pack(
            side="left", padx=(0, 18))

        self.only_selisih_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(
            r0, text="Hanya Selisih ≠ 0",
            variable=self.only_selisih_var,
            command=self._refresh)
        chk.pack(side="left")
        add_tooltip(chk, "Sembunyikan baris tanpa selisih\n"
                         "(IN == Barang Masuk)")

        GhostButton(r0, text="✕ Reset Filter",
                    command=self._reset_filter).pack(side="left", padx=(18, 0))

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        tk.Label(head, text="Rekap Selisih IN — IN (Accurate) vs Barang Masuk",
                 bg=C_CARD, fg=C_HEADER, font=font(10, "bold")).pack(side="left")
        btn_max = GhostButton(head, text="⛶ Perbesar", command=self._maximize)
        btn_max.pack(side="right")
        add_tooltip(btn_max, "Buka tabel ini dalam window besar\n"
                             "(Esc untuk menutup)")
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))
        add_tooltip(btn_fit, "Sesuaikan lebar semua kolom ke konten\n"
                             "(double-click tepi kolom = auto-fit 1 kolom;\n"
                             "drag tepi kolom = atur lebar manual)")

        self.tree = ttk.Treeview(tbody, columns=COL_IDS, show="headings",
                                 selectmode="browse")
        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=40, anchor=anchor)
            if col_name == "Nama Barang":
                # kolom filter corong (sort via popup filter)
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

        # v3.4: drag tepi heading = resize lebar kolom; double-click tepi =
        # auto-fit (dipasang SEBELUM HeaderFilter supaya "break" efektif)
        enable_col_resize(self.tree)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        tk.Label(foot, text="🖱 Double-click baris → rincian IN (42.05 / "
                            "32.24 / 99.01 + nomor) · klik judul kolom = sort",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(8)).pack(side="left")
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(8, "bold")).pack(side="right")

        self.overlay = LoadingOverlay(tbody, "Menghitung rekap Selisih IN…")

        # Filter "Nama Barang" menempel di header kolom
        self.header_filter = HeaderFilter(
            self.tree, "Nama Barang",
            get_values=self._name_values,
            on_apply=self._on_name_filter,
            label="Nama Barang",
            on_sort=lambda desc: self._sort_by("Nama Barang", reverse=desc))

        self.tree.bind("<Double-1>", self._on_double_click)

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("zero", foreground="#64748b")

    # ------------------------------------------------------------ DATA ----
    def load_data(self, data: pd.DataFrame, in_detail: pd.DataFrame | None = None):
        self.data = data
        self.in_detail = in_detail
        self._cached_base = None
        self._satuan_map = {}
        self._show_content()
        self._populate_filters()
        self._name_selected = None
        self.header_filter.clear()
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

    def _populate_filters(self):
        if self.data is None or self.data.empty:
            return
        if "NAMA RESTO" in self.data.columns:
            values = ["(All)"] + sorted(
                self.data["NAMA RESTO"].dropna().astype(str).unique().tolist())
            self.resto_combo["values"] = values

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

    # ------------------------------------------------------- COMPUTE ----
    def _compute_base(self) -> pd.DataFrame:
        """Pivot append1 → 1 baris per (Resto, Tanggal, Barang) dengan
        IN / BM / Selisih + lookup satuan. Pure pandas (thread-safe)."""
        df = self.data
        if df is None or df.empty:
            return pd.DataFrame()

        # satuan lookup per (Nama Barang, NAMA RESTO) — sumber sama dengan
        # lookup append1 (kolom SATUAN hasil merge dari rekap SO)
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

        return piv.sort_values(["Resto", "Tanggal", "Nama Barang"],
                               na_position="last").reset_index(drop=True)

    # ------------------------------------------------------------- REFRESH
    def _refresh(self, sync: bool = False):
        if self.data is None or self.data.empty:
            self.status_var.set("Belum ada data.")
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
            "resto": self.resto_var.get(),
            "name_selected": self._name_selected,
            "tgl_start": tgl_start,
            "tgl_end": tgl_end,
            "only_selisih": self.only_selisih_var.get(),
        }

        def work():
            if self._cached_base is None:
                self._cached_base = self._compute_base()
            return self._prepare_rows(st)

        def done(payload):
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menghitung rekap Selisih IN…", sync=sync)

    def _prepare_rows(self, st: dict) -> dict:
        base = self._cached_base
        if base is None or base.empty:
            return {"items": [], "status": "Tidak ada data."}

        f = base
        if st["tgl_start"] is not None and st["tgl_end"] is not None:
            t = pd.to_numeric(f["Tanggal"], errors="coerce")
            f = f[(t >= st["tgl_start"]) & (t <= st["tgl_end"])]
        resto_val = st["resto"]
        if resto_val and resto_val != "(All)":
            f = f[f["Resto"].astype(str) == resto_val]
        if st["name_selected"]:
            f = f[f["Nama Barang"].astype(str).isin(st["name_selected"])]
        if st["only_selisih"]:
            f = f[f["Selisih IN"] != 0]

        if f.empty:
            return {"items": [], "status": "Tidak ada data setelah filter."}

        n = len(f)
        total_in = float(f["IN"].sum())
        total_bm = float(f["Barang Masuk"].sum())
        total_sel = float(f["Selisih IN"].sum())

        cols_np = {
            "Resto": f["Resto"].astype(str).to_numpy(),
            "Nama Barang": f["Nama Barang"].astype(str).to_numpy(),
            "Satuan": f["Satuan"].astype(str).to_numpy(),
            "Tanggal": pd.to_numeric(f["Tanggal"], errors="coerce").to_numpy(),
            "IN": pd.to_numeric(f["IN"], errors="coerce").fillna(0).to_numpy(dtype="float64"),
            "Barang Masuk": pd.to_numeric(f["Barang Masuk"], errors="coerce").fillna(0).to_numpy(dtype="float64"),
            "Selisih IN": pd.to_numeric(f["Selisih IN"], errors="coerce").fillna(0).to_numpy(dtype="float64"),
        }
        items = []
        keys = []
        for i in range(n):
            t = cols_np["Tanggal"][i]
            values = (
                cols_np["Resto"][i],
                _fmt_int(t),
                cols_np["Nama Barang"][i],
                cols_np["Satuan"][i],
                _fmt_num(cols_np["IN"][i]),
                _fmt_num(cols_np["Barang Masuk"][i]),
                _fmt_num(cols_np["Selisih IN"][i]),
            )
            tags = []
            sel = cols_np["Selisih IN"][i]
            if sel < 0:
                tags.append("negative")
            elif sel == 0:
                tags.append("zero")
            tags.append("evenrow" if i % 2 == 0 else "oddrow")
            items.append(("", f"row_{i}", {"values": values,
                                            "tags": tuple(tags)}))
            # key utk drill-down: (resto, barang, tgl asli)
            keys.append((cols_np["Resto"][i], cols_np["Nama Barang"][i],
                         None if pd.isna(t) else int(t)))

        status = (f"{n} baris · Total IN {_fmt_num(total_in)} · "
                  f"BM {_fmt_num(total_bm)} · Selisih {_fmt_num(total_sel)}")
        return {"items": items, "status": status, "keys": keys}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self.header_filter.refresh_icon()
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
        self.resto_var.set("(All)")
        self.tgl_start_var.set("1")
        self.tgl_end_var.set("31")
        self.only_selisih_var.set(False)
        self._name_selected = None
        self.header_filter.clear()
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
            for col_name, _, _ in COLUMNS:
                if col_name == "Nama Barang":
                    new_tree.heading(col_name, text=col_name)
                else:
                    new_tree.heading(
                        col_name, text=col_name,
                        command=lambda c=col_name, t=new_tree:
                            self._sort_by(c, tree=t))

        win, new_tree = open_tree_maximized(
            self.tree, "Rekap Selisih IN",
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
        row = dict(zip(COL_IDS, values))
        resto = row.get("Resto")
        barang = row.get("Nama Barang")
        tgl_txt = str(row.get("Tanggal") or "")
        if not barang or not tgl_txt:
            return
        try:
            tgl = int(float(tgl_txt.replace(",", "")))
        except (TypeError, ValueError):
            return

        # baris asli (tree utama maupun clone ⛶) → cari key via iid
        det = self._detail_for(resto, barang, tgl, tree, row_iid)
        if det is None:
            return

        # ringkasan utk chip popup
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

    def _detail_for(self, resto, barang, tgl, tree, row_iid) -> Optional[pd.DataFrame]:
        """Ambil detail IN utk (resto, barang, tgl). Bila tree adalah clone ⛶,
        iid cocok dgn tree utama → pakai pemetaan _keys."""
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
