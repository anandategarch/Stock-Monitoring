"""
widgets.py — Blok bangunan UI Stock Monitoring (v3.0 redesign).

Semua komponen dipakai lintas view supaya tampilan konsisten:
- Card            : kartu putih + border slate + judul opsional
- KpiCard/KpiRow  : kartu metrik (label kecil, angka besar, aksen warna)
- Toolbar         : bar gelap slate-900 di atas jendela (judul + aksi)
- StatusBar       : bar status bawah (dot status + teks + info kanan)
- EmptyState      : placeholder saat belum ada data + tombol CTA
- AccentButton    : tombol teal solid (aksi utama)
- DangerButton    : tombol putih teks merah (aksi berbahaya)
- ToolTip         : tooltip hover sederhana
- make_tree       : Treeview ter-style lengkap dgn scrollbar
- LegendRow       : chip legenda warna (untuk status/CEK)
- StatusDot       : titik warna + teks status
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .theme import (
    C_ACCENT, C_ACCENT_HOVER, C_ACCENT_DARK, C_BG, C_BORDER, C_BORDER_DARK,
    C_CARD, C_GREEN, C_HEADER, C_LOG_BG, C_LOG_FG, C_RED, C_RED_SOFT,
    C_TEXT_MUTED, C_TEXT_SOFT, font, font_family, mono, setup_tree_tags,
)

# Tombol aksen/berbahaya pakai tk.Button murni: kontrol penuh atas warna
# (ttk button tidak bisa diwarnai per-widget tanpa mendaftarkan style baru).
_BTN_BASE = dict(
    bd=0, highlightthickness=0, relief="flat",
    font=font(10, "bold"), cursor="hand2",
    activeforeground="#ffffff", padx=14, pady=7,
)


class AccentButton(tk.Button):
    """Tombol aksi utama — teal solid, putih teks, hover teal-800."""

    def __init__(self, parent, text: str, command=None, **kw):
        cfg = dict(_BTN_BASE, bg=C_ACCENT, fg="#ffffff",
                   activebackground=C_ACCENT_HOVER, text=text, command=command)
        cfg.update(kw)
        super().__init__(parent, **cfg)
        self.bind("<Enter>", lambda e: self._set_bg(C_ACCENT_HOVER, enabled=True))
        self.bind("<Leave>", lambda e: self._set_bg(C_ACCENT, enabled=True))

    def _set_bg(self, color: str, enabled: bool = True):
        if str(self.cget("state")) == "disabled":
            return
        self.configure(background=color)

    def set_enabled(self, enabled: bool):
        """Enable/disable dengan warna sesuai state."""
        if enabled:
            self.configure(state="normal", bg=C_ACCENT, fg="#ffffff",
                           activebackground=C_ACCENT_HOVER)
        else:
            self.configure(state="disabled", bg="#94a3b8", fg="#e2e8f0",
                           activebackground="#94a3b8")


class DangerButton(tk.Button):
    """Tombol stop/batal — putih, teks merah, hover latar merah lembut."""

    def __init__(self, parent, text: str, command=None, **kw):
        cfg = dict(_BTN_BASE, bg=C_CARD, fg=C_RED,
                   activebackground=C_RED_SOFT, activeforeground=C_RED,
                   text=text, command=command)
        cfg.update(kw)
        super().__init__(parent, **cfg)
        self.bind("<Enter>", lambda e: self._set_bg(C_RED_SOFT))
        self.bind("<Leave>", lambda e: self._set_bg(C_CARD))

    def _set_bg(self, color: str):
        if str(self.cget("state")) == "disabled":
            return
        self.configure(background=color)

    def set_enabled(self, enabled: bool):
        if enabled:
            self.configure(state="normal", bg=C_CARD, fg=C_RED,
                           activebackground=C_RED_SOFT)
        else:
            self.configure(state="disabled", bg="#f1f5f9", fg=C_TEXT_SOFT,
                           activebackground="#f1f5f9")


class GhostButton(ttk.Button):
    """Tombol sekunder — ttk default ter-style (putih + border slate)."""

    def __init__(self, parent, text: str, command=None, **kw):
        super().__init__(parent, text=text, style="TButton", command=command, **kw)


class Card(tk.Frame):
    """Kartu putih: border 1px slate-200, padding konsisten.

    Pakai grid/pack di dalam. Judul opsional dirender sebagai baris pertama.
    """

    def __init__(self, parent, title: str = "", subtitle: str = "",
                 padding: int = 12, **kw):
        super().__init__(parent, bg=C_CARD, highlightbackground=C_BORDER,
                         highlightthickness=1, **kw)
        self._padding = padding
        self._title = title
        self._subtitle = subtitle

        self.inner = tk.Frame(self, bg=C_CARD)
        if title:
            head = tk.Frame(self, bg=C_CARD)
            head.pack(fill="x", padx=padding, pady=(padding, 0))
            tk.Label(head, text=title, bg=C_CARD, fg=C_HEADER,
                     font=font(12, "bold")).pack(anchor="w")
            if subtitle:
                tk.Label(head, text=subtitle, bg=C_CARD, fg=C_TEXT_MUTED,
                         font=font(9)).pack(anchor="w", pady=(2, 0))
            self.inner.pack(fill="both", expand=True,
                            padx=padding, pady=(8 if subtitle else 6, padding))
        else:
            self.inner.pack(fill="both", expand=True, padx=padding, pady=padding)

    def body(self) -> tk.Frame:
        return self.inner


class KpiCard(tk.Frame):
    """Kartu KPI: aksen warna kiri, label kecil uppercase, angka besar, sub-teks.

    set_value(value, subtitle, accent) untuk update cepat.
    """

    def __init__(self, parent, label: str, value: str = "—",
                 subtitle: str = "", accent: str = C_ACCENT, **kw):
        super().__init__(parent, bg=C_CARD, highlightbackground=C_BORDER,
                         highlightthickness=1, **kw)
        self._accent = accent

        row = tk.Frame(self, bg=C_CARD)
        row.pack(fill="both", expand=True, padx=12, pady=10)
        self._bar = tk.Frame(row, bg=accent, width=4)
        self._bar.pack(side="left", fill="y", padx=(0, 10))
        txt = tk.Frame(row, bg=C_CARD)
        txt.pack(side="left", fill="both", expand=True)

        self._label_var = tk.StringVar(value=label.upper())
        tk.Label(txt, textvariable=self._label_var, bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(8, "bold"), anchor="w").pack(fill="x")

        self._value_var = tk.StringVar(value=value)
        tk.Label(txt, textvariable=self._value_var, bg=C_CARD, fg=C_HEADER,
                 font=font(16, "bold"), anchor="w").pack(fill="x", pady=(2, 0))

        self._sub_var = tk.StringVar(value=subtitle)
        self._sub = tk.Label(txt, textvariable=self._sub_var, bg=C_CARD,
                             fg=C_TEXT_SOFT, font=font(8), anchor="w")
        if subtitle:
            self._sub.pack(fill="x")

    def set_value(self, value: str, subtitle: str | None = None,
                  accent: str | None = None):
        self._value_var.set(value)
        if subtitle is not None:
            if not self._sub.winfo_ismapped():
                self._sub.pack(fill="x")
            self._sub_var.set(subtitle)
        if accent is not None and accent != self._accent:
            self._accent = accent
            self._bar.configure(bg=accent)


class KpiRow(tk.Frame):
    """Barisan KpiCard yang sama lebar (grid weight=1).

    PENTING: KpiCard harus dibuat dengan KpiRow sebagai parent-nya:
        kpi = KpiRow(parent)
        card = KpiCard(kpi, "Label", "—", "sub")
        kpi.add(card)
    (bukan in_= sibling — stacking order Tk membuat widget tak terlihat.)
    """

    def __init__(self, parent, cards: list[KpiCard] | None = None, **kw):
        super().__init__(parent, bg=C_BG, **kw)
        self._cards: list[KpiCard] = []
        if cards:
            for c in cards:
                self.add(c)

    def add(self, card: KpiCard):
        card.grid(row=0, column=len(self._cards), sticky="nsew",
                  padx=(0 if self._cards else 0, 8))
        self._cards.append(card)
        self.grid_columnconfigure(len(self._cards) - 1, weight=1)


class Toolbar(tk.Frame):
    """Bar gelap slate-900 paling atas: ikon+judul aplikasi, versi, aksi kanan.

    add_action(text, command, danger=False, accent=False) → tombol.
    """

    def __init__(self, parent, title: str, version: str = "", **kw):
        super().__init__(parent, bg=C_HEADER, height=48, **kw)
        self.pack_propagate(False)

        left = tk.Frame(self, bg=C_HEADER)
        left.pack(side="left", padx=(16, 0), pady=8)
        tk.Label(left, text=title, bg=C_HEADER, fg="#f1f5f9",
                 font=font(13, "bold")).pack(side="left")
        if version:
            tk.Label(left, text=f" v{version} ", bg="#1e293b", fg="#5eead4",
                     font=font(8, "bold"), padx=8, pady=2).pack(
                side="left", padx=(10, 0))

        self._actions = tk.Frame(self, bg=C_HEADER)
        self._actions.pack(side="right", padx=(8, 16), pady=8)

    def add_action(self, text: str, command=None, accent: bool = False,
                   danger: bool = False) -> tk.Button:
        bg = C_ACCENT if accent else "#1e293b"
        fg = "#ffffff" if accent else "#e2e8f0"
        hover = C_ACCENT_HOVER if accent else "#334155"
        btn = tk.Button(
            self._actions, text=text, command=command,
            bg=bg, fg=fg, activebackground=hover, activeforeground="#ffffff",
            bd=0, relief="flat", highlightthickness=0, cursor="hand2",
            font=font(9, "bold"), padx=12, pady=5,
        )
        btn.pack(side="left", padx=(6, 0))
        btn.bind("<Enter>", lambda e: btn.configure(background=hover)
                 if str(btn.cget("state")) != "disabled" else None)
        btn.bind("<Leave>", lambda e: btn.configure(background=bg))
        return btn


class StatusDot(tk.Frame):
    """Titik warna + teks status (mis. '● SIAP — menunggu pipeline')."""

    def __init__(self, parent, text: str = "SIAP", color: str = C_GREEN, **kw):
        super().__init__(parent, bg=C_CARD, **kw)
        self._canvas = tk.Canvas(self, width=10, height=10, bg=C_CARD,
                                 highlightthickness=0, bd=0)
        self._canvas.pack(side="left", padx=(0, 6))
        self._dot = self._canvas.create_oval(1, 1, 9, 9, fill=color,
                                             outline=color)
        self._color = color
        self._var = tk.StringVar(value=text)
        tk.Label(self, textvariable=self._var, bg=C_CARD, fg=C_HEADER,
                 font=font(9, "bold")).pack(side="left")

    def set(self, text: str, color: str):
        self._canvas.itemconfigure(self._dot, fill=color, outline=color)
        self._var.set(text)


class StatusBar(tk.Frame):
    """Bar status bawah: dot+kiri, info kanan (versi). Border atas slate."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C_CARD, highlightbackground=C_BORDER,
                         highlightthickness=1, **kw)
        self.configure(height=34)
        self.pack_propagate(False)

        left = tk.Frame(self, bg=C_CARD)
        left.pack(side="left", fill="y", padx=12, pady=6)
        self.dot = StatusDot(left, "SIAP — menunggu pipeline", C_GREEN)
        self.dot.pack(side="left")

        self._right_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._right_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(9)).pack(
            side="right", padx=12, pady=8)

    def set_status(self, text: str, color: str = C_GREEN):
        self.dot.set(text, color)

    def set_right(self, text: str):
        self._right_var.set(text)


class EmptyState(tk.Frame):
    """Placeholder besar saat belum ada data: ikon + judul + sub + tombol CTA.

    on_cta: callback tombol (biasanya: pindah ke tab Proses).
    """

    def __init__(self, parent, icon: str = "📭", title: str = "Belum ada data",
                 subtitle: str = "Jalankan pipeline untuk memuat data ke tampilan ini.",
                 cta_text: str = "🚀 Jalankan Pipeline", on_cta=None, **kw):
        super().__init__(parent, bg=C_CARD, highlightbackground=C_BORDER,
                         highlightthickness=1, **kw)
        # Frame center fixed 520x260 (place anchor center) — konten dipack
        # di dalam, pack_propagate(False) menjaga ukuran frame tetap.
        center = tk.Frame(self, bg=C_CARD)
        center.place(relx=0.5, rely=0.5, anchor="center",
                     width=520, height=260)
        center.pack_propagate(False)

        tk.Label(center, text=icon, bg=C_CARD, font=(font_family(), 40)).pack(
            pady=(28, 0))
        tk.Label(center, text=title, bg=C_CARD, fg=C_HEADER,
                 font=font(13, "bold")).pack(pady=(6, 2))
        tk.Label(center, text=subtitle, bg=C_CARD, fg=C_TEXT_MUTED,
                 font=font(10), wraplength=420, justify="center").pack()
        if on_cta is not None and cta_text:
            AccentButton(center, text=cta_text, command=on_cta).pack(
                pady=(14, 20))
        else:
            # tanpa CTA: jaga padding bawah agar frame tetap proporsional
            tk.Frame(center, bg=C_CARD, height=20).pack()


class LegendRow(tk.Frame):
    """Baris chip legenda: titik warna + label (untuk CEK / Status Audit)."""

    def __init__(self, parent, items: list[tuple[str, str]], bg: str = C_CARD, **kw):
        """items: list [(label, warna_hex)]"""
        super().__init__(parent, bg=bg, **kw)
        for label, color in items:
            chip = tk.Frame(self, bg=bg)
            chip.pack(side="left", padx=(0, 14))
            cv = tk.Canvas(chip, width=9, height=9, bg=bg,
                           highlightthickness=0, bd=0)
            cv.pack(side="left", padx=(0, 5))
            cv.create_oval(0, 0, 8, 8, fill=color, outline=color)
            tk.Label(chip, text=label, bg=bg, fg=C_TEXT_MUTED,
                     font=font(8)).pack(side="left")


class ToolTip:
    """Tooltip hover sederhana (Toplevel borderless, muncul ~600ms)."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 600):
        self.widget = widget
        self.text = text
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _e=None):
        self._cancel()
        self._after_id = self.widget.after(600, self._show)

    def _cancel(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip is not None:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return
        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, bg=C_HEADER, fg="#e2e8f0",
                 font=font(9), padx=10, pady=5, justify="left").pack()

    def _hide(self, _e=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


def add_tooltip(widget: tk.Widget, text: str) -> ToolTip:
    """Helper singkat: add_tooltip(btn, 'Deskripsi...')"""
    return ToolTip(widget, text)


def make_tree(parent, columns: list[str], show: str = "headings",
              extra_tags: dict | None = None) -> ttk.Treeview:
    """Buat Treeview ter-style lengkap dgn scrollbar v+h. Return tree.

    Kolom diatur oleh pemanggil (column/heading per view).
    """
    frame = tk.Frame(parent, bg=C_CARD)
    frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(frame, columns=columns, show=show, selectmode="browse")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    setup_tree_tags(tree, extra_tags)
    tree._sm_frame = frame  # untuk akses layout jika perlu
    return tree


def make_log_console(parent, **kw) -> tuple[tk.Text, tk.Frame]:
    """Konsol log gelap ala Waste (#0b1220 + Consolas). Return (text, frame)."""
    frame = tk.Frame(parent, bg=C_LOG_BG, highlightbackground=C_BORDER,
                     highlightthickness=1)
    frame.pack(fill="both", expand=True, **kw)

    text = tk.Text(frame, wrap="word", bg=C_LOG_BG, fg=C_LOG_FG,
                   insertbackground=C_LOG_FG, font=mono(10), relief="flat",
                   bd=0, padx=12, pady=10, state="disabled")
    scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scroll.set)

    text.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return text, frame
