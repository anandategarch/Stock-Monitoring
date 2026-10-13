"""
theme.py — Design system global untuk Stock Monitoring UI (v3.0 redesign).

Di-porting dari design language aplikasi Waste (PySide6): slate + teal,
card-based, dark toolbar, konsol log gelap. Token warna identik supaya
kedua aplikasi terasa satu keluarga.

Palet:
    C_BG       #f1f5f9  slate-100  — latar utama
    C_CARD     #ffffff             — kartu
    C_HEADER   #0f172a  slate-900  — judul + toolbar gelap
    C_BORDER   #e2e8f0  slate-200  — border kartu
    C_MUTED    #64748b  slate-500  — teks sekunder
    C_ACCENT   #0f766e  teal-700   — tombol aksi utama

Font: resolusi otomatis — Segoe UI (Windows) → Noto Sans → DejaVu Sans
(Linux) supaya metrik teks jujur di semua platform.
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

# --- Palet warna -----------------------------------------------------------
C_BG = "#f1f5f9"            # slate-100 — latar utama
C_CARD = "#ffffff"           # kartu
C_HEADER = "#0f172a"         # slate-900 — teks judul + toolbar
C_BORDER = "#e2e8f0"         # slate-200 — border kartu
C_BORDER_DARK = "#cbd5e1"    # slate-300 — hover border
C_TEXT_MUTED = "#64748b"     # slate-500 — teks sekunder
C_TEXT_SOFT = "#94a3b8"      # slate-400 — teks jauh/disabled

C_ACCENT = "#0f766e"         # teal-700 — aksi utama
C_ACCENT_HOVER = "#115e59"   # teal-800
C_ACCENT_SOFT = "#ccfbf1"    # teal-100 — seleksi baris
C_ACCENT_DARK = "#134e4a"    # teal-900 — teks di atas seleksi

# Status colors — identik dengan STATUS_COLORS Waste
# (v3.3: varian *_SOFT & C_BLUE/C_PURPLE/C_LOG_MUTED yang tak terpakai
#  dihapus — view memakai hex literal untuk warna baris khusus)
C_RED = "#dc2626"
C_RED_SOFT = "#fef2f2"
C_ORANGE = "#ea580c"
C_AMBER = "#b45309"
C_GREEN = "#16a34a"

# Konsol log (mirror Waste: #0b1220)
C_LOG_BG = "#0b1220"
C_LOG_FG = "#cbd5e1"

# Zebra rows tabel
ROW_EVEN = "#ffffff"
ROW_ODD = "#f8fafc"

# --- Font -------------------------------------------------------------------
_FONT_CANDIDATES = [
    "Segoe UI",      # Windows
    "Noto Sans",     # Linux modern
    "DejaVu Sans",   # Linux fallback
    "Helvetica",     # macOS
    "Arial",
]
_MONO_CANDIDATES = ["Consolas", "Cascadia Mono", "JetBrains Mono", "DejaVu Sans Mono", "Courier New"]

_font_family: str | None = None
_mono_family: str | None = None


def _pick_family(candidates: list[str], fallback: str) -> str | None:
    """Pilih family font pertama yang tersedia di platform ini.

    v3.9.33 — AUDIT FIX (48-c HIGH-1): return None bila daftar family
    TIDAK bisa di-query (belum ada Tk root — tkfont.families() raise).
    None = sinyal "belum bisa resolve" bagi pemanggil supaya fallback
    TIDAK di-cache (lihat font_family/mono_family)."""
    try:
        available = set(tkfont.families())
    except Exception:
        return None
    for name in candidates:
        if name in available:
            return name
    return fallback


def font_family() -> str:
    """Family font UI utama (resolve sekali setelah root ada, lalu cache).

    v3.9.33 — AUDIT FIX (48-c HIGH-1): dulu fallback "DejaVu Sans"
    ter-CACHE PERMANEN saat resolusi dipanggil SEBELUM tk.Tk() ada
    (import-time, mis. widgets._BTN_BASE) → rantai kandidat
    "Segoe UI → Noto Sans → DejaVu" tidak pernah jalan di Windows
    produksi. Kini: kegagalan resolve (belum ada root) TIDAK di-cache —
    fallback dikembalikan sebagai nilai HIDUP dan resolusi dicoba ulang
    tiap pemanggilan sampai berhasil SEKALI (apply_theme pasca-root),
    baru hasilnya di-cache."""
    global _font_family
    if _font_family is None:
        fam = _pick_family(_FONT_CANDIDATES, "DejaVu Sans")
        if fam is None:
            # Belum ada root — JANGAN cache; kembalikan fallback hidup.
            return "DejaVu Sans"
        _font_family = fam
    return _font_family


def mono_family() -> str:
    """Family font monospace untuk log konsol.

    v3.9.33 — AUDIT FIX (48-c HIGH-1): pola lazy yang sama (jalur ini
    memang baru terpakai pasca-root via make_log_console, tapi dibuat
    konsisten + defensive)."""
    global _mono_family
    if _mono_family is None:
        fam = _pick_family(_MONO_CANDIDATES, "Courier New")
        if fam is None:
            return "Courier New"
        _mono_family = fam
    return _mono_family


def font(size: int = 10, weight: str = "normal") -> tuple:
    """Tuple font Tkinter standar: (family, size, weight)."""
    return (font_family(), size, weight)


def mono(size: int = 10) -> tuple:
    return (mono_family(), size)


# --- Setup ttk style ---------------------------------------------------------
def apply_theme(root: tk.Tk) -> ttk.Style:
    """Pasang tema global ke root window. Dipanggil sekali di startup.

    Return objek ttk.Style (bisa dipakai untuk kustomisasi lanjutan).
    """
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    fam = font_family()

    # --- Base widgets ---
    style.configure(".", background=C_BG, foreground=C_HEADER,
                    font=(fam, 10), borderwidth=0)
    style.configure("TFrame", background=C_BG, padding=0)
    style.configure("Card.TFrame", background=C_CARD, padding=0)

    style.configure("TLabel", background=C_BG, foreground=C_HEADER, font=(fam, 10))
    style.configure("Card.TLabel", background=C_CARD, foreground=C_HEADER, font=(fam, 10))
    style.configure("CardMuted.TLabel", background=C_CARD, foreground=C_TEXT_MUTED,
                    font=(fam, 9))
    style.configure("Muted.TLabel", background=C_BG, foreground=C_TEXT_MUTED, font=(fam, 9))
    style.configure("Title.TLabel", background=C_CARD, foreground=C_HEADER,
                    font=(fam, 13, "bold"))
    style.configure("Subtitle.TLabel", background=C_CARD, foreground=C_TEXT_MUTED,
                    font=(fam, 10))
    style.configure("Toolbar.TLabel", background=C_HEADER, foreground="#f1f5f9",
                    font=(fam, 11))
    style.configure("ToolbarTitle.TLabel", background=C_HEADER, foreground="#f1f5f9",
                    font=(fam, 12, "bold"))

    # --- Tombol (ghost/default — pakai ttk) ---
    # v3.9 (ala Waste): padding tombol 6px/14px → Tk (14, 7)
    style.configure("TButton", background=C_CARD, foreground=C_HEADER,
                    font=(fam, 10), padding=(14, 7), borderwidth=1,
                    focuscolor=C_CARD)
    style.map("TButton",
              background=[("active", "#f8fafc"), ("disabled", "#f1f5f9")],
              foreground=[("disabled", C_TEXT_SOFT)])

    # --- Notebook (tab) ---
    style.configure("TNotebook", background=C_BG, borderwidth=0,
                    tabmargins=(6, 8, 6, 0))
    # FIX H-1 (audit 2-a — terkonfirmasi Xvfb): padding (18,9)+label
    # spasi-ganda = ±1280px utk 10 tab > minsize 1020px → tab kanan
    # terpotong. Kini (12,9): ±912px — muat dgn margin; tinggi tab tetap.
    style.configure("TNotebook.Tab", background="#e2e8f0", foreground=C_TEXT_MUTED,
                    padding=(12, 9), font=(fam, 10), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", C_CARD), ("active", "#eef2f7")],
              foreground=[("selected", C_HEADER), ("active", C_HEADER)],
              font=[("selected", (fam, 10, "bold"))])
    style.configure("TNotebook.Pane", background=C_BG, borderwidth=0)

    # --- Entry / Combobox ---
    style.configure("TEntry", fieldbackground=C_CARD, foreground=C_HEADER,
                    bordercolor=C_BORDER, insertcolor=C_HEADER, padding=(8, 4))
    style.map("TEntry", bordercolor=[("focus", C_ACCENT)])
    style.configure("TCombobox", fieldbackground=C_CARD, foreground=C_HEADER,
                    bordercolor=C_BORDER, arrowcolor=C_TEXT_MUTED, padding=(8, 4))
    style.map("TCombobox",
              bordercolor=[("focus", C_ACCENT)],
              fieldbackground=[("readonly", C_CARD), ("disabled", "#f8fafc")],
              foreground=[("disabled", C_TEXT_SOFT)])

    # Dropdown list Combobox (via option database)
    root.option_add("*TCombobox*Listbox.background", C_CARD)
    root.option_add("*TCombobox*Listbox.foreground", C_HEADER)
    root.option_add("*TCombobox*Listbox.selectBackground", C_ACCENT_SOFT)
    root.option_add("*TCombobox*Listbox.selectForeground", C_ACCENT_DARK)
    root.option_add("*TCombobox*Listbox.font", (fam, 10))

    # --- Checkbutton ---
    style.configure("TCheckbutton", background=C_CARD, foreground=C_HEADER,
                    font=(fam, 10), focuscolor=C_CARD)
    style.map("TCheckbutton",
              background=[("active", C_CARD)],
              indicatorcolor=[("selected", C_ACCENT), ("!selected", "#ffffff")])

    # --- Progressbar ---
    style.configure("Horizontal.TProgressbar", background=C_ACCENT,
                    troughcolor="#e2e8f0", borderwidth=0, thickness=8)

    # --- Scrollbar ---
    style.configure("Vertical.TScrollbar", background="#e2e8f0",
                    troughcolor="#f1f5f9", bordercolor="#f1f5f9",
                    arrowcolor=C_TEXT_MUTED, relief="flat", arrowsize=12)
    style.map("Vertical.TScrollbar", background=[("active", "#cbd5e1")])
    style.configure("Horizontal.TScrollbar", background="#e2e8f0",
                     troughcolor="#f1f5f9", bordercolor="#f1f5f9",
                     arrowcolor=C_TEXT_MUTED, relief="flat", arrowsize=12)
    style.map("Horizontal.TScrollbar", background=[("active", "#cbd5e1")])

    # --- Treeview (tabel utama) ---
    # v3.9 "PERBESAR TABEL" (permintaan user — mirror aplikasi Waste:
    # font tabel 13px + item padding 3px/8px + baris lapang):
    # font 9 → 10, rowheight 26 → 30 — tabel terlihat besar & mudah dibaca.
    style.configure("Treeview", background=ROW_EVEN, fieldbackground=ROW_EVEN,
                    foreground=C_HEADER, rowheight=30, font=(fam, 10),
                    bordercolor=C_BORDER, relief="solid")
    style.configure("Treeview.Heading", background="#f8fafc", foreground=C_HEADER,
                    font=(fam, 10, "bold"), relief="flat", bordercolor=C_BORDER,
                    padding=(8, 8))
    style.map("Treeview.Heading", background=[("active", "#e8edf3")])
    style.map("Treeview",
              background=[("selected", C_ACCENT_SOFT)],
              foreground=[("selected", C_ACCENT_DARK)])

    # --- Separator ---
    style.configure("TSeparator", background=C_BORDER)

    return style


# --- Zebra tags helper -------------------------------------------------------
def setup_tree_tags(tree: ttk.Treeview, extra_tags: dict | None = None) -> None:
    """Pasang tag zebra-row + negative standar ke sebuah Treeview.

    extra_tags: dict {tag: {"foreground": ..., "background": ...}} untuk
    pewarnaan spesifik view (status, CEK, dsb).
    """
    tree.tag_configure("evenrow", background=ROW_EVEN)
    tree.tag_configure("oddrow", background=ROW_ODD)
    tree.tag_configure("negative", foreground=C_RED)
    if extra_tags:
        for tag, cfg in extra_tags.items():
            tree.tag_configure(tag, **cfg)
