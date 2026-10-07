"""
details_popup.py — Popup detail source rows Append1 (v3.1).

Muncul saat user double-click cell/baris di PivotTableView / DeviasiView /
LaporanDeviasiView. Fitur v3.1:
- COPY Nomor / Nomor PO: klik-kanan (menu konteks), Ctrl+C, atau
  double-click cell kolom Nomor / Nomor PO → langsung tersalin ke clipboard
- Copy semua Nomor / Nomor PO (unik) via menu konteks / tombol footer
- Filter Nama Barang menempel di header kolom (corong, Excel-like)
- Tombol ⛶ Perbesar: buka tabel popup dalam window besar
- Loading overlay saat render
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Optional

from .theme import (
    C_ACCENT_DARK, C_ACCENT_SOFT, C_BG, C_BORDER, C_CARD,
    C_HEADER, C_TEXT_MUTED, font, font_family,
)
from .widgets import (
    AccentButton, GhostButton, HeaderFilter, LoadingOverlay, add_tooltip,
    insert_tree_items, open_tree_maximized, run_async,
)

# Column definitions: (column_id, width, anchor)
COLUMNS = [
    ("Nama Barang", 140, "w"),
    ("NAMA RESTO", 80, "w"),
    ("Tanggal", 60, "e"),
    ("JENIS", 100, "w"),
    ("NILAI", 90, "e"),
    ("Nomor", 130, "w"),
    ("Nomor PO", 130, "w"),
    ("#Tgl/Jam Pembuatan IT", 140, "w"),
    ("KATEGORI", 80, "w"),
    ("SOURCE KIRIMAN", 100, "w"),
]

COL_IDS = [c[0] for c in COLUMNS]


class DetailsPopup(tk.Toplevel):
    """Popup window menampilkan source rows untuk kombinasi cell pivot."""

    def __init__(self, parent, title: str, df: pd.DataFrame,
                 filter_info: str = ""):
        super().__init__(parent)
        self._title = title
        self.title(f"Detail — {title}")
        # Posisikan di tengah parent (modal nyaman, deterministik)
        try:
            pw, ph = 1100, 540
            px = parent.winfo_rootx() + (parent.winfo_width() - pw) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - ph) // 2
            self.geometry(f"{pw}x{ph}+{max(px, 0)}+{max(py, 0)}")
        except Exception:
            self.geometry("1100x540")
        self.minsize(800, 320)
        self.configure(bg=C_BG)

        # Modal — block parent sampai ditutup
        self.transient(parent)
        self.grab_set()

        # State
        self.df = df
        self._name_selected: set | None = None
        self._busy = False
        self._pending = False
        self._base_status = ""
        self._flash_after = None
        self._render_df: Optional[pd.DataFrame] = df

        # Build UI
        self._build_ui(title, filter_info)

        # Render data
        self._render()

        # Focus + close on Escape
        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    # =====================================================================
    # UI BUILD
    # =====================================================================
    def _build_ui(self, title: str, filter_info: str):
        # --- Header band gelap ---
        header = tk.Frame(self, bg=C_HEADER)
        header.pack(fill="x")
        head_in = tk.Frame(header, bg=C_HEADER)
        head_in.pack(fill="x", padx=16, pady=12)

        tk.Label(head_in, text="🔍 Detail Source Data", bg=C_HEADER,
                 fg="#5eead4", font=font(8, "bold")).pack(anchor="w")
        tk.Label(head_in, text=title, bg=C_HEADER, fg="#f1f5f9",
                 font=font(12, "bold"), wraplength=760,
                 justify="left").pack(anchor="w", pady=(2, 0))
        if filter_info:
            tk.Label(head_in, text=f"Filter aktif: {filter_info}",
                     bg=C_HEADER, fg="#94a3b8", font=font(9)).pack(
                anchor="w", pady=(2, 0))

        # Aksi di kanan band: ⛶ Perbesar
        btn_max = tk.Button(
            head_in, text="⛶ Perbesar", command=self._maximize,
            bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
            activeforeground="#ffffff", bd=0, relief="flat",
            highlightthickness=0, cursor="hand2", font=font(9, "bold"),
            padx=12, pady=5)
        btn_max.pack(side="right", anchor="ne")
        add_tooltip(btn_max, "Buka tabel detail dalam window besar\n"
                             "(klik kanan di sana juga bisa copy)")

        # --- Body: tabel ---
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        card = tk.Frame(body, bg=C_CARD, highlightbackground=C_BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True)
        card_in = tk.Frame(card, bg=C_CARD)
        card_in.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(card_in, columns=COL_IDS, show="headings",
                                 selectmode="browse")

        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50, anchor=anchor)
            # kolom Nomor / Nomor PO tanpa sort-click (heading dipakai filter
            # Nama Barang; copy via klik kanan / double-click)
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(card_in, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(card_in, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card_in.grid_rowconfigure(0, weight=1)
        card_in.grid_columnconfigure(0, weight=1)

        self._setup_tags(self.tree)

        # loading overlay (stacking di atas tree)
        self.overlay = LoadingOverlay(card_in, "Menyiapkan detail…")

        # interaksi copy
        self.tree.bind("<Button-3>", self._on_context_menu)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Control-c>", self._on_copy_key)
        self.tree.bind("<Control-C>", self._on_copy_key)

        # filter Nama Barang menempel di header kolom
        self.header_filter = HeaderFilter(
            self.tree, "Nama Barang",
            get_values=self._name_values,
            on_apply=self._on_name_filter,
            label="Nama Barang")

        # --- Footer: status + tombol ---
        foot = tk.Frame(self, bg=C_BG)
        foot.pack(fill="x", padx=12, pady=(0, 12))

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(foot, textvariable=self.status_var,
                                     bg=C_BG, fg=C_TEXT_MUTED, font=font(9))
        self.status_label.pack(side="left")

        btn_copy_nomor = GhostButton(
            foot, text="📋 Semua Nomor",
            command=lambda: self._copy_all_unique("Nomor"))
        btn_copy_nomor.pack(side="right", padx=(6, 0))
        add_tooltip(btn_copy_nomor, "Copy SEMUA Nomor unik (newline-separated) "
                                    "ke clipboard")
        btn_copy_po = GhostButton(
            foot, text="📋 Semua Nomor PO",
            command=lambda: self._copy_all_unique("Nomor PO"))
        btn_copy_po.pack(side="right", padx=(6, 0))
        add_tooltip(btn_copy_po, "Copy SEMUA Nomor PO unik (newline-separated) "
                                 "ke clipboard")

        AccentButton(foot, text="Tutup (Esc)", command=self.destroy).pack(
            side="right", padx=(6, 0))

    def _name_values(self) -> list:
        if self.df is None or self.df.empty or \
                "Nama Barang" not in self.df.columns:
            return []
        return self.df["Nama Barang"].dropna().astype(str).unique().tolist()

    def _on_name_filter(self, selected):
        self._name_selected = selected
        self._render()

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("negative", foreground="#dc2626")

    # =====================================================================
    # RENDER (async + batched)
    # =====================================================================
    def _render(self, sync: bool = False):
        if self._busy:
            self._pending = True
            return
        self._busy = True
        df = self.df

        def work():
            return self._prepare_rows(df, self._name_selected)

        def done(payload):
            self._render_rows(payload)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Menyiapkan detail…", sync=sync)

    @staticmethod
    def _prepare_rows(df: pd.DataFrame, name_selected: set | None) -> dict:
        """Pure: filter + format baris → payload render (thread-safe)."""
        if df is None or df.empty:
            return {"items": [], "status": "Tidak ada source data untuk "
                                           "kombinasi ini.", "total": 0}

        render_df = df
        if name_selected and "Nama Barang" in df.columns:
            render_df = df[df["Nama Barang"].astype(str).isin(name_selected)]

        if render_df.empty:
            return {"items": [], "status": "Tidak ada source data untuk "
                                           "kombinasi ini.", "total": 0}

        col_data = {}
        for col_name, _, _ in COLUMNS:
            if col_name in render_df.columns:
                col_data[col_name] = render_df[col_name].tolist()
            else:
                col_data[col_name] = [""] * len(render_df)

        items = []
        n = len(render_df)
        total_nilai = 0.0
        for i in range(n):
            values = []
            has_negative = False
            for col_name, _, _ in COLUMNS:
                val = col_data[col_name][i]
                if col_name == "NILAI":
                    formatted, is_neg = DetailsPopup._fmt_nilai(val)
                    values.append(formatted)
                    if is_neg:
                        has_negative = True
                    try:
                        total_nilai += float(val) if val is not None and \
                            not pd.isna(val) else 0
                    except (TypeError, ValueError):
                        pass
                else:
                    values.append(DetailsPopup._fmt_cell(val, col_name))
            tags = []
            if has_negative:
                tags.append("negative")
            tags.append("evenrow" if i % 2 == 0 else "oddrow")
            items.append(("", f"row_{i}", {"values": values,
                                           "tags": tuple(tags)}))

        if total_nilai == int(total_nilai):
            total_str = f"{int(total_nilai):,}"
        else:
            total_str = f"{total_nilai:,.1f}"
        status = f"{n} rows · Total NILAI: {total_str}"
        return {"items": items, "status": status, "total": total_nilai,
                "render_df_len": n}

    def _render_rows(self, payload: dict):
        self.tree.delete(*self.tree.get_children())
        self._base_status = payload["status"]
        self.status_label.configure(fg=C_TEXT_MUTED)
        self.status_var.set(payload["status"])
        # simpan df tampilan saat ini (untuk copy semua unik)
        self._render_df = self._apply_name_filter_df()
        self.header_filter.refresh_icon()

        def render_done():
            self._busy = False
            if self._pending:
                self._pending = False
                self._render()

        insert_tree_items(self.tree, payload["items"], batch=400,
                          on_done=render_done)

    def _apply_name_filter_df(self) -> pd.DataFrame:
        df = self.df
        if df is None or df.empty:
            return df
        if self._name_selected and "Nama Barang" in df.columns:
            return df[df["Nama Barang"].astype(str).isin(self._name_selected)]
        return df

    # =====================================================================
    # COPY Nomor / Nomor PO
    # =====================================================================
    def _copy_to_clipboard(self, text, label: str):
        text = str(text or "").strip()
        if not text:
            self._flash_status("⚠ Tidak ada yang bisa di-copy (nilai kosong).")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        shown = text if len(text) <= 60 else text[:60] + "…"
        self._flash_status(f"📋 {label} TERSALIN ke clipboard: {shown}")

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
        row = dict(zip(COL_IDS, values))
        nomor = str(row.get("Nomor", "") or "")
        nomor_po = str(row.get("Nomor PO", "") or "")

        def _lbl(s: str) -> str:
            s = s.strip()
            if not s:
                return "(kosong)"
            return s[:26] + ("…" if len(s) > 26 else "")

        menu = tk.Menu(self, tearoff=0, bg=C_CARD, fg=C_HEADER,
                       activebackground=C_ACCENT_SOFT,
                       activeforeground=C_ACCENT_DARK,
                       font=(font_family(), 9), bd=0, relief="flat")
        menu.add_command(
            label=f"📋 Copy Nomor — {_lbl(nomor)}",
            command=lambda: self._copy_to_clipboard(nomor, "Nomor"))
        menu.add_command(
            label=f"📋 Copy Nomor PO — {_lbl(nomor_po)}",
            command=lambda: self._copy_to_clipboard(nomor_po, "Nomor PO"))
        menu.add_separator()
        menu.add_command(
            label="📋 Copy seluruh baris (tab-separated)",
            command=lambda: self._copy_row(iid, tree))
        menu.add_command(
            label="📋 Copy SEMUA Nomor (unik)",
            command=lambda: self._copy_all_unique("Nomor"))
        menu.add_command(
            label="📋 Copy SEMUA Nomor PO (unik)",
            command=lambda: self._copy_all_unique("Nomor PO"))
        menu.add_separator()
        menu.add_command(label="⛶ Perbesar tabel",
                         command=self._maximize)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    def _copy_row(self, iid, tree):
        values = tree.item(iid, "values")
        if not values:
            return
        self._copy_to_clipboard("\t".join(str(v) for v in values),
                                "Baris lengkap")

    def _copy_all_unique(self, col: str):
        df = self._render_df
        if df is None or df.empty or col not in df.columns:
            self._flash_status("Tidak ada data untuk di-copy.")
            return
        vals = df[col].dropna().astype(str).str.strip()
        vals = vals[vals != ""]
        uniq = sorted(set(vals.tolist()))
        if not uniq:
            self._flash_status("Tidak ada nilai untuk di-copy.")
            return
        self._copy_to_clipboard("\n".join(uniq),
                                f"{len(uniq)} nilai {col} (unik)")

    def _on_double_click(self, event):
        """Double-click cell Nomor / Nomor PO → langsung copy nilai cell."""
        tree = event.widget
        iid = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not iid or not col or col == "#0":
            return
        try:
            idx = int(col.replace("#", "")) - 1
        except ValueError:
            return
        if 0 <= idx < len(COL_IDS):
            col_name = COL_IDS[idx]
            if col_name in ("Nomor", "Nomor PO"):
                val = tree.set(iid, col_name)
                self._copy_to_clipboard(val, col_name)

    def _on_copy_key(self, _event):
        """Ctrl+C — copy Nomor baris terpilih (fallback Nomor PO)."""
        tree = self.tree
        sel = tree.selection()
        if not sel:
            return
        values = tree.item(sel[0], "values")
        if not values:
            return
        row = dict(zip(COL_IDS, values))
        val = str(row.get("Nomor", "") or "")
        if not val:
            val = str(row.get("Nomor PO", "") or "")
        if val:
            self._copy_to_clipboard(val, "Nomor")

    # =====================================================================
    # ⛶ PERBESAR
    # =====================================================================
    def _maximize(self):
        return open_tree_maximized(
            self.tree, f"Detail — {self._title}",
            setup_tags=lambda t: self._setup_tags(t),
            on_context_menu=self._on_context_menu,
            on_double_click=self._on_double_click)

    # =====================================================================
    # FORMAT (identik versi lama)
    # =====================================================================
    @staticmethod
    def _fmt_nilai(val):
        """Format NILAI: separator ribuan, negatif dalam kurung, 1 desimal."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "", False
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val), False
        is_neg = v < 0
        if v == 0:
            return "-", False
        if v == int(v):
            s = f"{v:,.0f}"
        else:
            s = f"{v:,.1f}"
        if is_neg:
            return f"({s[1:]})", True
        return s, False

    @staticmethod
    def _fmt_cell(val, col_name: str) -> str:
        """Format cell value for display (identik versi lama)."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        if col_name in ("#Tgl/Jam Pembuatan IT",):
            if hasattr(val, "strftime"):
                return val.strftime("%d/%m/%Y %H:%M:%S")
            try:
                return pd.to_datetime(val).strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                return str(val)
        if col_name == "Tanggal":
            try:
                return str(int(val))
            except (TypeError, ValueError):
                return str(val)
        return str(val)


def show_details_popup(parent, data: pd.DataFrame, nama_barang: str = None,
                        jenis: str = None, tanggal=None,
                        filters: dict = None):
    """Filter data + show popup.

    v3.3: tanpa ``data.copy()`` upfront — setiap filter boolean sudah
    menghasilkan DataFrame baru, dan ``reset_index(drop=True)`` di ujung
    selalu mengembalikan objek baru (hemat ~10ms + memori di 200k baris).
    """
    if data is None or data.empty:
        popup = DetailsPopup(parent, "Tidak ada data", pd.DataFrame())
        return popup

    df = data

    # Build title parts
    title_parts = []
    if nama_barang:
        df = df[df["Nama Barang"].astype(str) == str(nama_barang)]
        title_parts.append(nama_barang)
    if jenis:
        df = df[df["JENIS"].astype(str) == str(jenis)]
        title_parts.append(jenis)
    if tanggal is not None:
        try:
            tgl_int = int(tanggal)
            df = df[pd.to_numeric(df["Tanggal"], errors="coerce") == tgl_int]
            title_parts.append(f"Tgl {tgl_int}")
        except (TypeError, ValueError):
            pass

    # Apply additional filters (from active pivot filters)
    filter_info_parts = []
    if filters:
        for col, val in filters.items():
            if val and val != "(All)" and col in df.columns:
                df = df[df[col].astype(str) == str(val)]
                filter_info_parts.append(f"{col}={val}")

    title = " / ".join(title_parts) if title_parts else "All Data"
    filter_info = ", ".join(filter_info_parts) if filter_info_parts else ""

    popup = DetailsPopup(parent, title, df.reset_index(drop=True), filter_info)
    return popup
