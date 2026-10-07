"""
details_popup.py — Popup detail source rows Append1 (v3.0 redesign).

Muncul saat user double-click cell/baris di PivotTableView / DeviasiView /
LaporanDeviasiView. Logika filter identik versi lama; tampilan baru:
- Header band gelap dengan judul + info filter (chip)
- Tabel ter-style + footer status
- Tombol Tutup accent + shortcut Esc
"""

import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Optional

from .theme import (
    C_ACCENT, C_BG, C_BORDER, C_CARD, C_HEADER, C_TEXT_MUTED, font, mono,
)
from .widgets import AccentButton

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


class DetailsPopup(tk.Toplevel):
    """Popup window menampilkan source rows untuk kombinasi cell pivot."""

    def __init__(self, parent, title: str, df: pd.DataFrame,
                 filter_info: str = ""):
        super().__init__(parent)
        self.title(f"Detail — {title}")
        # Posisikan di tengah parent (modal nyaman, deterministik)
        try:
            pw, ph = 1100, 520
            px = parent.winfo_rootx() + (parent.winfo_width() - pw) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - ph) // 2
            self.geometry(f"{pw}x{ph}+{max(px, 0)}+{max(py, 0)}")
        except Exception:
            self.geometry("1100x520")
        self.minsize(800, 320)
        self.configure(bg=C_BG)

        # Modal — block parent sampai ditutup
        self.transient(parent)
        self.grab_set()

        # State
        self.df = df

        # Build UI
        self._build_ui(title, filter_info)

        # Render data
        self._render()

        # Focus + close on Escape
        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self, title: str, filter_info: str):
        # --- Header band gelap ---
        header = tk.Frame(self, bg=C_HEADER)
        header.pack(fill="x")
        head_in = tk.Frame(header, bg=C_HEADER)
        head_in.pack(fill="x", padx=16, pady=12)

        tk.Label(head_in, text=f"🔍 Detail Source Data", bg=C_HEADER,
                 fg="#5eead4", font=font(8, "bold")).pack(anchor="w")
        tk.Label(head_in, text=title, bg=C_HEADER, fg="#f1f5f9",
                 font=font(12, "bold"), wraplength=1000, justify="left"
                 ).pack(anchor="w", pady=(2, 0))
        if filter_info:
            tk.Label(head_in, text=f"Filter aktif: {filter_info}",
                     bg=C_HEADER, fg="#94a3b8", font=font(9)).pack(
                anchor="w", pady=(2, 0))

        # --- Body: tabel ---
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        card = tk.Frame(body, bg=C_CARD, highlightbackground=C_BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True)
        card_in = tk.Frame(card, bg=C_CARD)
        card_in.pack(fill="both", expand=True, padx=8, pady=8)

        col_ids = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(card_in, columns=col_ids, show="headings",
                                 selectmode="browse")

        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=50, anchor=anchor)
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(card_in, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(card_in, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card_in.grid_rowconfigure(0, weight=1)
        card_in.grid_columnconfigure(0, weight=1)

        # Zebra + negative
        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f8fafc")
        self.tree.tag_configure("negative", foreground="#dc2626")

        # --- Footer: status + tombol ---
        foot = tk.Frame(self, bg=C_BG)
        foot.pack(fill="x", padx=12, pady=(0, 12))

        self.status_var = tk.StringVar()
        tk.Label(foot, textvariable=self.status_var, bg=C_BG,
                 fg=C_TEXT_MUTED, font=font(9)).pack(side="left")

        AccentButton(foot, text="Tutup (Esc)", command=self.destroy).pack(
            side="right")

    def _render(self):
        """Render DataFrame ke Treeview (identik versi lama)."""
        self.tree.delete(*self.tree.get_children())

        if self.df is None or self.df.empty:
            self.status_var.set("Tidak ada source data untuk kombinasi ini.")
            return

        # Prepare column data as lists for fast iteration
        col_data = {}
        for col_name, _, _ in COLUMNS:
            if col_name in self.df.columns:
                col_data[col_name] = self.df[col_name].tolist()
            else:
                col_data[col_name] = [""] * len(self.df)

        n = len(self.df)
        total_nilai = 0
        for i in range(n):
            values = []
            has_negative = False
            for col_name, _, _ in COLUMNS:
                val = col_data[col_name][i]
                if col_name == "NILAI":
                    formatted, is_neg = self._fmt_nilai(val)
                    values.append(formatted)
                    if is_neg:
                        has_negative = True
                    try:
                        total_nilai += float(val) if val is not None and \
                            not pd.isna(val) else 0
                    except (TypeError, ValueError):
                        pass
                else:
                    values.append(self._fmt_cell(val, col_name))
            # Tags: negative + alternating
            tags = []
            if has_negative:
                tags.append("negative")
            tags.append("evenrow" if i % 2 == 0 else "oddrow")
            self.tree.insert("", "end", values=values, tags=tuple(tags))

        # Status
        if total_nilai == int(total_nilai):
            total_str = f"{int(total_nilai):,}"
        else:
            total_str = f"{total_nilai:,.1f}"
        self.status_var.set(f"{n} rows · Total NILAI: {total_str}")

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
    """Filter data + show popup (identik versi lama)."""
    if data is None or data.empty:
        popup = DetailsPopup(parent, "Tidak ada data", pd.DataFrame())
        return popup

    df = data.copy()

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
