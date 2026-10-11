"""
deviasi_popup.py — Popup RINGKAS tab Deviasi GR/PCS (v3.9.18).

Permintaan user: "pop up di deviasi GR ataupun PCS hanya tampilkan:
nama barang, nama resto, nilai saldo akhir, nilai SO, nilai IN,
nilai deviasi."

Mengganti popup source rows (details_popup.DetailsPopup — JENIS/Nomor/
Nomor PO/#Tgl-Jam/KATEGORI/SOURCE KIRIMAN) yang DULU terbuka dari tab
Deviasi GR/PCS:

- NAMA BARANG + NAMA RESTO tampil di judul popup (dua-duanya).
- Tabel ringkas PER TANGGAL — hanya 5 kolom:
    Tanggal · Saldo Akhir (2.SALDO AKHIR / sistem) · SO (1.SO) ·
    IN (4.IN) · Deviasi (= SO − Saldo Akhir, identik kolom Deviasi
    tab Deviasi GR/PCS & JENIS 3.DEVIASI pipeline).
- Baris Tanggal H diberi latar lembut (#fef3c7 — sama dgn highlight
  kolom Deviasi/SO_H di tabel utama v3.9.18) supaya mudah ditemukan.
- Tanggal bulan lalu (negatif) diberi label '25•' (konvensi pivot_view
  — '• = bulan lalu', urut kronologis 25•…31• lalu 1…31).
- Minus merah PER CELL (tag cell Tk 9 — fallback Tk 8 tag baris,
  pola v3.9.2). Popup source rows LAMA tetap dipakai tab lain
  (Pivot/Laporan) — tidak tersentuh.
"""
import tkinter as tk
from tkinter import ttk

import pandas as pd

from .theme import (
    C_BG,
    C_BORDER,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    font,
)
from .widgets import (
    CELL_TAGS_SUPPORTED,
    AccentButton,
    apply_cell_tag,
    auto_fit_columns,
    enable_col_resize,
    fmt_int_id,
)

# (column_id, width, anchor) — persis daftar user: saldo akhir, SO, IN,
# deviasi (+ kolom Tanggal sbg sumbu baris; barang & resto di judul).
COLUMNS = [
    ("Tanggal", 76, "e"),
    ("Saldo Akhir", 110, "e"),
    ("SO", 110, "e"),
    ("IN", 110, "e"),
    ("Deviasi", 110, "e"),
]

COL_IDS = [c[0] for c in COLUMNS]

_H_ROW_BG = "#fef3c7"   # sama dgn HIGHLIGHT_BG deviasi_view (v3.9.18)

_JENIS_SALDO = "2.SALDO AKHIR"
_JENIS_SO = "1.SO"
_JENIS_IN = "4.IN"


class DeviasiPopup(tk.Toplevel):
    """Popup ringkas: nilai kunci per Tanggal utk 1 pasangan (barang, resto)."""

    def __init__(self, parent, title: str, rows: pd.DataFrame,
                 h_label: str = ""):
        super().__init__(parent)
        self._title = title
        self.title(f"Detail Deviasi — {title}")
        try:
            pw, ph = 640, 460
            px = parent.winfo_rootx() + (parent.winfo_width() - pw) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - ph) // 2
            self.geometry(f"{pw}x{ph}+{max(px, 0)}+{max(py, 0)}")
        except tk.TclError:
            self.geometry("640x460")
        self.minsize(460, 260)
        self.configure(bg=C_BG)

        # Modal — block parent sampai ditutup (pola DetailsPopup)
        self.transient(parent)
        self.grab_set()

        self.rows = rows
        self._h_label = h_label
        # v3.9.2 (pola): minus merah PER CELL — fallback Tk 8 tag baris
        self._cell_tags = CELL_TAGS_SUPPORTED
        self._neg_cells: list = []

        self._build_ui(title)

        self._render()

        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

    # =====================================================================
    # UI
    # =====================================================================
    def _build_ui(self, title: str):
        # --- Header band gelap (pola DetailsPopup) ---
        header = tk.Frame(self, bg=C_HEADER)
        header.pack(fill="x")
        head_in = tk.Frame(header, bg=C_HEADER)
        head_in.pack(fill="x", padx=16, pady=12)

        tk.Label(head_in, text="🔍 Detail Deviasi", bg=C_HEADER,
                 fg="#5eead4", font=font(8, "bold")).pack(anchor="w")
        # judul = NAMA BARANG — NAMA RESTO (dua-duanya, permintaan user)
        tk.Label(head_in, text=title, bg=C_HEADER, fg="#f1f5f9",
                 font=font(12, "bold"), wraplength=560,
                 justify="left").pack(anchor="w", pady=(2, 0))

        btn_fit = tk.Button(
            head_in, text="↔ Auto-Fit", command=self._auto_fit,
            bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
            activeforeground="#ffffff", bd=0, relief="flat",
            highlightthickness=0, cursor="hand2", font=font(9, "bold"),
            padx=12, pady=5)
        btn_fit.pack(side="right", anchor="ne")

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
            self.tree.column(col_name, width=width, minwidth=50,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(card_in, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(card_in, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card_in.grid_rowconfigure(0, weight=1)
        card_in.grid_columnconfigure(0, weight=1)

        self._setup_tags(self.tree)
        # v3.4 (pola): drag tepi heading = resize; double-click = auto-fit
        enable_col_resize(self.tree)

        # --- Footer: status + tutup ---
        foot = tk.Frame(self, bg=C_BG)
        foot.pack(fill="x", padx=12, pady=(0, 12))

        self.status_var = tk.StringVar()
        tk.Label(foot, textvariable=self.status_var, bg=C_BG,
                 fg=C_TEXT_MUTED, font=font(9)).pack(side="left")
        AccentButton(foot, text="Tutup (Esc)",
                     command=self.destroy).pack(side="right")

    def _setup_tags(self, tree=None):
        tree = tree if tree is not None else self.tree
        tree.tag_configure("evenrow", background="#ffffff")
        tree.tag_configure("oddrow", background="#f8fafc")
        tree.tag_configure("negative", foreground="#dc2626")
        tree.tag_configure("neg_cell", foreground="#dc2626")  # v3.9.2 pola
        # v3.9.18 — baris Tanggal H (satu-satunya tag utk baris H:
        # TANPA evenrow — tidak ada konflik opsi background antar tag)
        tree.tag_configure("h_row", background=_H_ROW_BG)

    # =====================================================================
    # RENDER (sync — tabel kecil ≤ ~62 baris)
    # =====================================================================
    def _render(self):
        self.tree.delete(*self.tree.get_children())
        self._neg_cells = []
        rows = self.rows
        n = len(rows)

        if n == 0:
            self.status_var.set("Tidak ada data utk kombinasi ini.")
            return

        for i, rec in enumerate(rows.to_dict("records")):
            values = [rec["Tanggal"], rec["Saldo Akhir"], rec["SO"],
                      rec["IN"], rec["Deviasi"]]
            tags = []
            if self._h_label and rec["Tanggal"] == self._h_label:
                tags.append("h_row")       # baris Tanggal H — latar lembut
            else:
                tags.append("evenrow" if i % 2 == 0 else "oddrow")
            has_neg = False
            for j, col in enumerate(("Saldo Akhir", "SO", "IN", "Deviasi")):
                if _is_neg_display(values[j + 1]):
                    has_neg = True
                    if self._cell_tags:
                        self._neg_cells.append((f"row_{i}", col))
            if has_neg and not self._cell_tags:
                tags.append("negative")     # fallback Tk 8 — tag baris
            self.tree.insert("", "end", iid=f"row_{i}", values=values,
                             tags=tuple(tags))

        if self._cell_tags and self._neg_cells:
            apply_cell_tag(self.tree, "neg_cell", self._neg_cells)

        # footer status: jumlah baris + legenda '•' bila ada bulan lalu
        has_lalu = any(str(v).endswith("•") for v in rows["Tanggal"])
        status = f"{n} baris"
        if has_lalu:
            status += " · • = bulan lalu"
        if self._h_label:
            status += f" · H={self._h_label}"
        self.status_var.set(status)

    def _auto_fit(self):
        """v3.4 (pola) — auto-fit lebar kolom ke konten."""
        auto_fit_columns(self.tree)

    # =====================================================================
    # FORMAT
    # =====================================================================
    @staticmethod
    def _fmt_num(val) -> str:
        """Format angka Indonesia (pola DeviasiView._fmt_num): 0 → '-',
        minus dalam kurung, 1 desimal bila pecahan."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val)
        if v == 0:
            return "-"
        if v == int(v):
            s = fmt_int_id(v)
        else:
            s = f"{v:,.1f}".replace(",", "\u00a0").replace(".", ",") \
                .replace("\u00a0", ".")
        if v < 0:
            return f"({s[1:]})"
        return s


def _is_neg_display(s) -> bool:
    """True bila string tampilan bernilai minus — '(1.234)' / '(12,5)'."""
    t = str(s or "").strip()
    return t.startswith("(") and t.endswith(")")


def _fmt_tanggal(t) -> str:
    """Tanggal → label: positif '25'; bulan lalu (negatif) '25•'
    (konvensi pivot_view — kronologis: 25• … 31• lalu 1 … 31)."""
    try:
        d = int(t)
    except (TypeError, ValueError):
        return str(t)
    if d < 0:
        return f"{-d}•"
    return str(d)


def _chrono_key(t):
    """Kunci urut numerik: bulan lalu (25•…31•) dulu, lalu 1..31 —
    negatif → abs(d) (25..31), positif → 100+d (101..131); ascending
    kronologis: 25•, 26•, … 31•, 1, 2, … 31 (konvensi pivot_view)."""
    try:
        d = int(str(t).rstrip("•"))
    except (TypeError, ValueError):
        return 999999
    return abs(d) if d < 0 else 100 + d


def build_popup_rows(data: pd.DataFrame, nama_barang: str,
                     nama_resto: str) -> pd.DataFrame:
    """Pure pandas (thread-safe) — siapkan baris popup per Tanggal.

    Hanya 3 JENIS yang dipakai (permintaan user: nilai saldo akhir, SO,
    IN, deviasi — TANPA OUT/BARANG KELUAN/BARANG MASUK):
      Saldo Akhir = Σ 2.SALDO AKHIR · SO = Σ 1.SO · IN = Σ 4.IN
      Deviasi = SO − Saldo Akhir (identik 3.DEVIASI & tabel utama).
    """
    empty = pd.DataFrame(columns=["Tanggal", "Saldo Akhir", "SO", "IN",
                                  "Deviasi"])
    if data is None or data.empty:
        return empty

    df = data
    mask = (
        (df["Nama Barang"].astype(str) == str(nama_barang))
        & (df["NAMA RESTO"].astype(str) == str(nama_resto))
        & (df["JENIS"].isin((_JENIS_SALDO, _JENIS_SO, _JENIS_IN)))
    )
    sub = df[mask]
    if sub.empty:
        return empty

    tgl = pd.to_numeric(sub["Tanggal"], errors="coerce")
    nilai = pd.to_numeric(sub["NILAI"], errors="coerce")
    sub = sub.assign(_t=tgl, _v=nilai).dropna(subset=["_t"])

    if sub.empty:
        return empty

    wide = sub.pivot_table(index="_t", columns="JENIS", values="_v",
                           aggfunc="sum", fill_value=0.0)

    for col in (_JENIS_SALDO, _JENIS_SO, _JENIS_IN):
        if col not in wide.columns:
            wide[col] = 0.0

    out = pd.DataFrame({
        "_t": wide.index,
        "Saldo Akhir": wide[_JENIS_SALDO].to_numpy(),
        "SO": wide[_JENIS_SO].to_numpy(),
        "IN": wide[_JENIS_IN].to_numpy(),
    })
    # Deviasi = SO − Saldo Akhir (identik kolom Deviasi tabel utama)
    out["Deviasi"] = out["SO"] - out["Saldo Akhir"]

    # label tampilan + urut kronologis (numerik — negatif abs 25..31
    # < positif 101..131, jadi bulan lalu dulu lalu 1..31)
    out["Tanggal"] = out["_t"].map(_fmt_tanggal)
    out = out.assign(_k=out["_t"].map(_chrono_key)) \
        .sort_values("_k") \
        .drop(columns=["_k"]).reset_index(drop=True)

    # format angka Indonesia (string — siap render)
    for col in ("Saldo Akhir", "SO", "IN", "Deviasi"):
        out[col] = out[col].map(DeviasiPopup._fmt_num)

    return out[["Tanggal", "Saldo Akhir", "SO", "IN", "Deviasi"]]


def show_deviasi_popup(parent, data: pd.DataFrame, nama_barang: str,
                       nama_resto: str, satuan: str | None = None,
                       h: int | None = None):
    """Buka popup ringkas utk pasangan (barang, resto).

    Dipanggil dari DeviasiView._on_double_click (tab Deviasi GR & PCS,
    termasuk window clone ⛶ — event.widget-agnostic).
    """
    title = f"{nama_barang} — {nama_resto}"
    if satuan:
        title += f"  ({satuan})"

    rows = build_popup_rows(data, nama_barang, nama_resto)
    h_label = _fmt_tanggal(h) if h is not None else ""
    popup = DeviasiPopup(parent, title, rows, h_label=h_label)
    return popup
