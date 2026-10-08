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

import math
import threading
import time as _time

import tkinter as tk
from tkinter import ttk, messagebox as _mb

from .theme import (
    C_ACCENT, C_ACCENT_HOVER, C_BG, C_BORDER,
    C_BORDER_DARK, C_CARD, C_GREEN, C_HEADER, C_LOG_BG, C_LOG_FG, C_RED,
    C_RED_SOFT, C_TEXT_MUTED, C_TEXT_SOFT, font, font_family, mono,
    setup_tree_tags,
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


# =============================================================================
# v3.1 — Komponen baru: loading spinner, overlay, segment, header-filter,
#         maximize table, async helper, insert batched
# =============================================================================

def _mix_hex(c1: str, c2: str, t: float) -> str:
    """Interpolasi dua warna hex (t=0 → c1, t=1 → c2)."""

    def parse(c: str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))

    r1, g1, b1 = parse(c1)
    r2, g2, b2 = parse(c2)
    return "#{:02x}{:02x}{:02x}".format(
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
    )


class Spinner(tk.Canvas):
    """Spinner animasi (8 titik memudar) — indikasi loading proses."""

    def __init__(self, parent, size: int = 26, color: str = C_ACCENT,
                 bg: str = C_CARD, speed: int = 90, **kw):
        super().__init__(parent, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0, **kw)
        self._bg = bg
        self._speed = speed
        self._after_id = None
        self._phase = 0
        self._color = color
        cx = size / 2.0
        r = size / 2.0 - 3.0
        d = max(3.0, size * 0.17)
        self._dots = []
        for i in range(8):
            ang = i * (math.pi / 4)
            x = cx + r * math.cos(ang)
            y = cx + r * math.sin(ang)
            dot = self.create_oval(x - d / 2, y - d / 2, x + d / 2, y + d / 2,
                                   fill=color, outline=color)
            self._dots.append(dot)
        self._render()

    def _render(self):
        for i, dot in enumerate(self._dots):
            dist = (i - self._phase) % 8
            shade = _mix_hex(self._color, self._bg, (dist / 8.0) * 0.85)
            self.itemconfigure(dot, fill=shade, outline=shade)

    def start(self):
        self.stop()

        def tick():
            if not self.winfo_exists():
                self._after_id = None
                return
            self._phase = (self._phase + 1) % 8
            self._render()
            self._after_id = self.after(self._speed, tick)

        self._after_id = self.after(self._speed, tick)

    def stop(self):
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None


class LoadingOverlay(tk.Frame):
    """Chip loading melayang di tengah parent: spinner + teks.

    show(text, delay_ms=180) — chip hanya benar-benar muncul bila proses
    berjalan lebih lama dari delay (anti-kedip untuk operasi cepat).
    """

    def __init__(self, parent, text: str = "Memuat…", **kw):
        super().__init__(parent, bg=C_CARD, highlightbackground=C_BORDER_DARK,
                         highlightthickness=1, **kw)
        inner = tk.Frame(self, bg=C_CARD)
        inner.pack(padx=24, pady=14)
        self.spinner = Spinner(inner, bg=C_CARD)
        self.spinner.pack(side="left", padx=(0, 12))
        self._var = tk.StringVar(value=text)
        tk.Label(inner, textvariable=self._var, bg=C_CARD, fg=C_HEADER,
                 font=font(11, "bold")).pack(side="left")
        self._show_after = None
        self._visible = False

    def show(self, text: str | None = None, delay_ms: int = 180):
        if text:
            self._var.set(text)
        if self._visible:
            return
        self._visible = True
        if delay_ms and delay_ms > 0:
            self._show_after = self.after(delay_ms, self._place)
        else:
            self._place()

    def _place(self):
        if not self._visible:
            return
        try:
            if not self.winfo_exists():
                return
            self.place(relx=0.5, rely=0.5, anchor="center")
            self.lift()
            self.spinner.start()
            self.winfo_toplevel().configure(cursor="watch")
        except tk.TclError:
            pass

    def hide(self):
        self._visible = False
        if self._show_after:
            try:
                self.after_cancel(self._show_after)
            except Exception:
                pass
            self._show_after = None
        try:
            self.place_forget()
            self.spinner.stop()
            self.winfo_toplevel().configure(cursor="")
        except tk.TclError:
            pass


class SegmentBar(tk.Frame):
    """Segmented control kecil: beberapa opsi, satu aktif (teal)."""

    def __init__(self, parent, options: list[str], command=None,
                 bg: str = C_CARD, **kw):
        super().__init__(parent, bg=bg, **kw)
        self._command = command
        self._buttons: list[tk.Button] = []
        self._active = 0
        for i, opt in enumerate(options):
            b = tk.Button(self, text=opt, font=font(9, "bold"),
                          bd=0, relief="flat", highlightthickness=0,
                          cursor="hand2", padx=14, pady=5,
                          command=lambda idx=i: self._select(idx))
            b.pack(side="left", padx=(0 if i == 0 else 4, 0))
            self._buttons.append(b)
        self._render()

    def _select(self, idx: int):
        if idx == self._active:
            return
        self._active = idx
        self._render()
        if self._command:
            self._command(idx)

    @property
    def active(self) -> int:
        return self._active

    def set_active_silent(self, idx: int):
        """Set opsi aktif TANPA memicu command (dipakai saat inisialisasi
        / load_data supaya tidak refresh ganda)."""
        if idx != self._active:
            self._active = idx
            self._render()

    def _render(self):
        for i, b in enumerate(self._buttons):
            if i == self._active:
                b.configure(bg=C_ACCENT, fg="#ffffff",
                            activebackground=C_ACCENT_HOVER,
                            activeforeground="#ffffff")
            else:
                b.configure(bg="#f1f5f9", fg=C_TEXT_MUTED,
                            activebackground="#e2e8f0",
                            activeforeground=C_HEADER)


# --- Ikon corong utk header filter (digambar via PhotoImage, tanpa PIL) -----
_FUNNEL_CACHE: dict = {}


def funnel_image(color: str = "#94a3b8") -> tk.PhotoImage:
    """Ikon corong kecil 11x8 px (alpha via PhotoImage Tk 8.6)."""
    if color in _FUNNEL_CACHE:
        return _FUNNEL_CACHE[color]
    w, h = 11, 8
    img = tk.PhotoImage(width=w, height=h)
    # bentuk corong: cone melebar + stem
    shape = [
        (1, 9),   # rim atas
        (2, 8),
        (3, 7),
        (4, 6),
        (5, 5),   # ujung cone
        (5, 5),   # stem
        (5, 5),
        (5, 5),
    ]
    for y in range(h):
        x0, x1 = shape[y]
        for x in range(w):
            if x0 <= x <= x1:
                img.put(color, (x, y))
            else:
                try:
                    img.transparency_set(x, y, True)
                except Exception:
                    pass
    _FUNNEL_CACHE[color] = img
    return img


class HeaderFilter:
    """Filter kolom yang MENEMPEL DI HEADER Treeview (ala Excel AutoFilter).

    - Ikon corong dipasang di heading kolom; klik heading → popup filter.
    - Popup: pencarian nilai + daftar checkbox nilai unik + pilih-semua
      + sort A→Z / Z→A (opsional) + reset.
    - Setiap toggle checkbox langsung memanggil on_apply(selection):
        None      → semua nilai tampil (tanpa filter)
        set(...)  → hanya nilai terpilih yang tampil
    - get_values() dipanggil saat popup dibuka (nilai unik terbaru).
    """

    MAX_CHECKS = 600  # batas render checkbox — pakai 🔍 untuk list besar

    def __init__(self, tree: ttk.Treeview, col_id: str, *, get_values,
                 on_apply, label: str = "Nama Barang", on_sort=None,
                 popup_width: int = 330):
        self.tree = tree
        self.col_id = col_id
        self.get_values = get_values
        self.on_apply = on_apply
        self.on_sort = on_sort
        self.label = label
        self.popup_width = popup_width
        self.selected: set | None = None
        self._popup: tk.Toplevel | None = None
        self._closed_at = 0.0
        self._checks: dict[str, ttk.Checkbutton] = {}
        self._vars: dict[str, tk.BooleanVar] = {}
        self._search_var = tk.StringVar()
        self._all_var = tk.BooleanVar(value=True)
        self._count_var = tk.StringVar(value="")
        self.refresh_icon()
        self._bind_id = tree.bind("<Button-1>", self._on_tree_press, add="+")

    def detach(self):
        """Lepas binding klik-heading dari tree (dipakai saat kolom
        dikonfigurasi ulang — mencegah binding ganda/orsos)."""
        if getattr(self, "_bind_id", None):
            try:
                self.tree.unbind("<Button-1>", self._bind_id)
            except Exception:
                pass
            self._bind_id = None

    # -- ikon corong ---------------------------------------------------------
    def refresh_icon(self):
        active = self.selected is not None
        try:
            self.tree.heading(
                self.col_id,
                image=funnel_image(C_ACCENT if active else "#94a3b8"))
        except tk.TclError:
            pass

    # -- klik heading --------------------------------------------------------
    def _on_tree_press(self, event):
        try:
            if self.tree.identify_region(event.x, event.y) != "heading":
                return
            if self.tree.identify_column(event.x) != self.col_id:
                return
        except Exception:
            return
        # hindari langsung terbuka lagi setelah ditutup (toggle natural)
        if _time.time() - self._closed_at < 0.35:
            return
        self.open_popup()

    # -- popup ----------------------------------------------------------------
    def open_popup(self):
        if self._popup is not None and self._popup.winfo_exists():
            self._close()
            return
        values = []
        try:
            values = sorted({str(v) for v in self.get_values()
                             if str(v) and str(v) != "nan"})
        except Exception:
            values = []
        if not values:
            _mb.showinfo("Filter", "Tidak ada nilai yang bisa difilter.",
                         parent=self.tree)
            return

        root = self.tree.winfo_toplevel()
        win = tk.Toplevel(root)
        self._popup = win
        win.title(f"Filter — {self.label}")
        win.configure(bg=C_CARD)
        win.transient(root)
        win.resizable(False, False)
        try:
            win.grab_set()
        except Exception:
            pass

        body = tk.Frame(win, bg=C_CARD)
        body.pack(fill="both", expand=True, padx=14, pady=12)

        # pencarian nilai (menyaring daftar, bukan data)
        srow = tk.Frame(body, bg=C_CARD)
        srow.pack(fill="x")
        tk.Label(srow, text="🔍", bg=C_CARD, fg=C_TEXT_MUTED).pack(side="left")
        entry = ttk.Entry(srow, textvariable=self._search_var)
        entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        entry.bind("<KeyRelease>", lambda e: self._filter_list())

        # pilih semua + counter
        arow = tk.Frame(body, bg=C_CARD)
        arow.pack(fill="x", pady=(10, 2))
        ttk.Checkbutton(arow, text=f"Pilih semua ({len(values)} nilai)",
                        variable=self._all_var,
                        command=self._toggle_all).pack(side="left")
        tk.Label(arow, textvariable=self._count_var, bg=C_CARD,
                 fg=C_TEXT_MUTED, font=font(8)).pack(side="right")

        # daftar nilai (scrollable checkbox)
        wrap = tk.Frame(body, bg=C_CARD, highlightbackground=C_BORDER,
                        highlightthickness=1)
        wrap.pack(fill="both", expand=True, pady=(6, 10))
        cv = tk.Canvas(wrap, bg=C_CARD, highlightthickness=0, bd=0,
                       width=self.popup_width - 30, height=300)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=cv.yview)
        inner = tk.Frame(cv, bg=C_CARD)
        inner.bind("<Configure>",
                   lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=inner, anchor="nw",
                         width=self.popup_width - 30)
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        # scroll wheel
        cv.bind("<MouseWheel>",
                lambda e: cv.yview_scroll(-1 * (e.delta // 120), "units"))

        self._vars.clear()
        self._checks.clear()
        for v in values[: self.MAX_CHECKS]:
            var = tk.BooleanVar(
                value=self.selected is None or v in self.selected)
            self._vars[v] = var
            cb = ttk.Checkbutton(inner, text=v, variable=var,
                                 command=self._on_toggle)
            cb.pack(fill="x", padx=8, pady=1)
            self._checks[v] = cb
        if len(values) > self.MAX_CHECKS:
            tk.Label(inner, text=f"… {len(values) - self.MAX_CHECKS} nilai "
                                 "lainnya — gunakan 🔍 di atas",
                     bg=C_CARD, fg=C_TEXT_SOFT, font=font(8)).pack(
                fill="x", padx=8, pady=4)

        # tombol aksi
        brow = tk.Frame(body, bg=C_CARD)
        brow.pack(fill="x")
        GhostButton(brow, text="↺ Reset", command=self._reset).pack(side="left")
        if self.on_sort is not None:
            GhostButton(brow, text="↕ Sort A→Z",
                        command=lambda: self._do_sort(False)).pack(
                side="left", padx=(6, 0))
            GhostButton(brow, text="↕ Sort Z→A",
                        command=lambda: self._do_sort(True)).pack(
                side="left", padx=(6, 0))
        GhostButton(brow, text="✕ Tutup (Esc)", command=self._close).pack(
            side="right")

        self._update_count()
        self._filter_list()

        # posisikan tepat di bawah heading kolom
        win.update_idletasks()
        px, py = self._popup_position()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        px = min(max(px, 8), max(8, sw - win.winfo_reqwidth() - 8))
        py = min(max(py, 8), max(8, sh - win.winfo_reqheight() - 8))
        win.geometry(f"+{px}+{py}")
        entry.focus_set()
        win.bind("<Escape>", lambda e: self._close())

    def _popup_position(self):
        tree = self.tree
        try:
            cols = ["#0"] + list(tree["columns"])
            x = 0
            if self.col_id in cols:
                x = sum(tree.column(c, "width")
                        for c in cols[:cols.index(self.col_id)])
                first = tree.xview()[0]
                if first > 0:
                    content_w = sum(tree.column(c, "width") for c in cols)
                    visible_w = tree.winfo_width()
                    if content_w > visible_w:
                        x -= first * (content_w - visible_w)
            px = int(tree.winfo_rootx() + max(0, x))
            hy = 30
            for iid in tree.get_children(""):
                bbox = tree.bbox(iid)
                if bbox:
                    hy = bbox[1] + 4
                    break
            py = int(tree.winfo_rooty() + hy)
        except Exception:
            px, py = tree.winfo_rootx(), tree.winfo_rooty() + 40
        return px, py

    # -- aksi popup ------------------------------------------------------------
    def _on_toggle(self):
        self._update_count()
        self._emit()

    def _toggle_all(self):
        to = self._all_var.get()
        for var in self._vars.values():
            var.set(to)
        self._update_count()
        self._emit()

    def _emit(self):
        checked = {v for v, var in self._vars.items() if var.get()}
        if not checked or len(checked) == len(self._vars):
            self.selected = None
        else:
            self.selected = checked
        self.refresh_icon()
        if self.on_apply:
            self.on_apply(self.selected)

    def _update_count(self):
        checked = sum(1 for var in self._vars.values() if var.get())
        total = len(self._vars)
        self._all_var.set(total > 0 and checked == total)
        self._count_var.set(f"{checked}/{total} dipilih")

    def _filter_list(self):
        q = (self._search_var.get() or "").strip().lower()
        for v, cb in self._checks.items():
            if not q or q in v.lower():
                cb.pack(fill="x", padx=8, pady=1)
            else:
                cb.pack_forget()

    def _reset(self):
        for var in self._vars.values():
            var.set(True)
        self._update_count()
        self._emit()

    def _do_sort(self, descending: bool):
        if self.on_sort is not None:
            self.on_sort(descending)
        self._close()

    def _close(self):
        if self._popup is not None:
            try:
                self._popup.grab_release()
            except Exception:
                pass
            try:
                self._popup.destroy()
            except Exception:
                pass
        self._popup = None
        self._closed_at = _time.time()

    def clear(self):
        """Reset state filter dari luar (dipanggil tombol Reset Filter view).
        TIDAK memanggil on_apply — view memicu refresh sendiri."""
        self.selected = None
        for var in self._vars.values():
            var.set(True)
        self.refresh_icon()


class HeaderFilterGroup:
    """Pasang HeaderFilter di BANYAK kolom sekaligus (v3.5).

    "Semua header punya filter" — klik judul kolom mana pun membuka popup
    filter (nilai unik + search + checkbox) ala Excel AutoFilter; sort
    tersedia di dalam popup (tombol ↕ Sort A→Z / Z→A via on_sort).

    Pemakaian:
        group = HeaderFilterGroup(tree, cols,
                                   get_values=view._col_values,
                                   on_apply=view._on_col_filter,
                                   on_sort=lambda c, d: view._sort_by(c, reverse=d))
        # view menyimpan state: self._col_sel[col] = selected_set_or_None
        group.clear_all()   # dipanggil tombol Reset Filter (tanpa refresh)
    """

    def __init__(self, tree: ttk.Treeview, cols: list,
                 *, get_values, on_apply, on_sort=None):
        self._filters: dict = {}
        for col in cols:
            self._filters[col] = HeaderFilter(
                tree, col,
                get_values=(lambda c=col: get_values(c)),
                on_apply=(lambda sel, c=col: on_apply(c, sel)),
                label=col,
                on_sort=((lambda desc, c=col: on_sort(c, desc))
                         if on_sort is not None else None),
            )

    def clear_all(self):
        for f in self._filters.values():
            f.clear()

    def refresh_icons(self):
        for f in self._filters.values():
            f.refresh_icon()

    def detach_all(self):
        """Lepas SEMUA binding klik-heading (saat ganti mode/kolom tree)."""
        for f in self._filters.values():
            f.detach()


# --- Async + render batched ---------------------------------------------------

# BUG WORKAROUND (CPython 3.12 + Tk 9 di beberapa build): objek Thread daemon
# yang baru selesai dapat di-finalisasi oleh GC tepat saat main thread
# mengeksekusi Tk after(), yang bisa memicu segfault level C. Menyimpan
# referensi thread yang sudah selesai (bounded) mencegah finalisasi Thread
# oleh GC pada momen acak.
_worker_threads: list = []
_MAX_KEPT_THREADS = 40


def _spawn_worker(target) -> threading.Thread:
    t = threading.Thread(target=target, daemon=True)
    _worker_threads.append(t)
    if len(_worker_threads) > _MAX_KEPT_THREADS:
        del _worker_threads[: _MAX_KEPT_THREADS // 2]
    t.start()
    return t


def run_async(widget, work, on_done, overlay: LoadingOverlay | None = None,
              loading_text: str | None = None, on_error=None,
              sync: bool = False) -> dict:
    """Jalankan work() (compute murni, TANPA sentuhan widget) di thread
    terpisah; hasil dikirim ke on_done(result) di main thread.

    Overlay otomatis show/hide. sync=True → blocking (untuk test).
    Return dict job: {"busy": bool, "cancel": callable}.
    """
    job = {"busy": True, "cancelled": False, "result": None, "error": None,
           "traceback": None}

    def finish():
        if overlay is not None:
            overlay.hide()
        err = job["error"]
        if err is not None:
            if on_error is not None:
                on_error(err)
            else:
                try:
                    _mb.showerror(
                        "Error Memproses",
                        f"Gagal memproses data:\n\n{err}", parent=widget)
                except Exception:
                    print(job.get("traceback") or err)
        else:
            on_done(job["result"])

    def runner():
        # PENTING: matikan GC otomatis selama work() berjalan di thread ini.
        # Tanpa ini, GC yang dipicu pandas bisa mem-finalisasi objek tkinter
        # (__del__ memanggil Tcl) dari NON-MAIN thread → Tk tidak thread-safe
        # → segfault. GC diaktifkan kembali setelah work() selesai; finalisasi
        # tkinter objects kemudian terjadi di main thread (aman).
        import gc as _gc
        _gc_was_enabled = _gc.isenabled()
        _gc.disable()
        try:
            job["result"] = work()
        except Exception as e:  # pragma: no cover
            import traceback as _tb
            job["error"] = e
            job["traceback"] = _tb.format_exc()
        finally:
            if _gc_was_enabled:
                _gc.enable()
        job["busy"] = False

    if sync:
        runner()
        finish()
        return job

    if overlay is not None:
        overlay.show(loading_text)
    _spawn_worker(runner)

    def poll():
        if job["cancelled"]:
            return
        try:
            if not widget.winfo_exists():
                return  # widget sudah ditutup — buang hasil
        except tk.TclError:
            return
        if job["busy"]:
            widget.after(70, poll)
            return
        finish()

    widget.after(70, poll)
    job["cancel"] = lambda: job.update(cancelled=True)
    return job


def insert_tree_items(tree: ttk.Treeview, items: list, *, batch: int = 400,
                      on_done=None, chunk_callback=None, delay: int | None = None):
    """Insert items [(parent_iid, iid, kwargs)] bertahap per-batch via after()
    supaya UI tetap responsif (spinner tetap hidup) saat render data besar.

    v3.3: delay adaptif — tabel besar (>20k baris) memakai 1ms/batch,
    jadi 50k baris tidak lagi menunggu +1 detik ekstra (dulu 10ms/batch).

    Return fungsi cancel() utk membatalkan sisa batch.
    """
    if delay is None:
        delay = 10 if len(items) <= 20_000 else 1
    state = {"i": 0, "cancelled": False}

    def chunk():
        if state["cancelled"]:
            return
        try:
            if not tree.winfo_exists():
                return
        except tk.TclError:
            return
        start = state["i"]
        end = min(start + batch, len(items))
        try:
            for parent_iid, iid, kw in items[start:end]:
                tree.insert(parent_iid, "end", iid=iid, **kw)
        except tk.TclError:
            return
        state["i"] = end
        if chunk_callback:
            try:
                chunk_callback(end, len(items))
            except Exception:
                pass
        if end < len(items):
            try:
                tree.after(delay, chunk)
            except tk.TclError:
                pass
        elif on_done:
            on_done()

    if items:
        chunk()
    elif on_done:
        on_done()

    def cancel():
        state["cancelled"] = True

    return cancel


# --- Sort engine linear (v3.3) ------------------------------------------------

def sort_tree_by_column(tree: ttk.Treeview, col: str, reverse: bool = True,
                        parse=None) -> None:
    """Sort baris top-level tree berdasarkan kolom — WAKTU LINEAR (v3.3).

    Versi lama (v3.0-v3.2): ``tree.move(k, "", i)`` per baris → O(n²)
    internal Tk — klik judul kolom di Laporan Deviasi (50k baris)
    MEMBEKANKAN UI sampai 45 detik.

    Versi baru: 1x ``tree.item()`` per baris (snapshot values+tags) →
    ``delete`` semua → insert ulang berurutan di posisi 'end' (append
    cepat) → O(n). Benchmark @50k baris: 45.1s → 1.1s (42×).

    iid dipertahankan → pemetaan iid→fingerprint (_fp_map) dan toggle
    kolom ✓ tetap mengenai baris yang benar setelah sort.
    """
    children = list(tree.get_children(""))
    if len(children) < 2:
        return
    try:
        col_idx = list(tree["columns"]).index(col)
    except (ValueError, tk.TclError):
        col_idx = -1

    info = {}
    keys = []
    for k in children:
        it = tree.item(k)
        info[k] = it
        vals = it.get("values") or []
        raw = vals[col_idx] if 0 <= col_idx < len(vals) else ""
        keys.append((raw, k))

    if parse is None:
        def parse(s):
            s = str(s).replace(",", "").replace("%", "").strip()
            if s in ("-", ""):
                return 0
            if s.startswith("(") and s.endswith(")"):
                return -float(s[1:-1])
            return float(s)
    try:
        keys.sort(key=lambda x: parse(x[0]), reverse=reverse)
    except (ValueError, TypeError):
        keys.sort(key=lambda x: str(x[0]), reverse=reverse)

    order = [k for _, k in keys]
    if order == children:
        return
    try:
        sel = set(tree.selection())
    except tk.TclError:
        sel = set()
    tree.delete(*children)
    for k in order:
        it = info[k]
        tree.insert("", "end", iid=k, values=it.get("values"),
                    tags=tuple(it.get("tags") or ()))
    keep = [k for k in order if k in sel]
    if keep:
        try:
            tree.selection_set(keep)
        except tk.TclError:
            pass


# --- Column resize + auto-fit (v3.4) -------------------------------------------

def _tree_display_columns(tree: ttk.Treeview) -> list[str]:
    """Kolom yang tampil (urutan layout): ['#0' bila show tree] + columns."""
    try:
        raw = tree.cget("show")
        parts = " ".join(str(x) for x in raw) if isinstance(raw, (tuple, list)) \
            else str(raw)
    except Exception:
        parts = "headings"
    cols = []
    if "tree" in parts:
        cols.append("#0")
    cols += list(tree["columns"])
    return cols


def _tree_content_x(tree: ttk.Treeview, event_x: int) -> float:
    """Konversi x event (relatif widget) → koordinat konten kolom
    (memperhitungkan scroll horizontal)."""
    try:
        frac = tree.xview()[0]
        content_w = sum(tree.column(c, "width")
                        for c in _tree_display_columns(tree))
        visible_w = tree.winfo_width()
        offset = frac * max(0, content_w - visible_w)
    except Exception:
        offset = 0
    return event_x + offset


def enable_col_resize(tree: ttk.Treeview, *, edge_px: int = 7):
    """v3.4 — Resize lebar kolom MANUAL via drag + AUTO-FIT double-click.

    Masalah lama: lebar kolom terasa "tidak bisa di-adjust" —
    - zona separator bawaan Tk sangat sempit & sulit ditemukan;
    - klik heading men-trigger sort/popup filter (HeaderFilter membuka
      Toplevel + grab_set di Button-1 → pointer "dicuri" → drag mati).

    Solusi: binding sendiri yang DIPASANG PERTAMA (sebelum HeaderFilter/
    handler klik view lain) supaya `return "break"` saat drag mematikan
    sort/filter bawaan:
    - Press di area heading dalam `edge_px` px dari tepi KANAN kolom
      → mulai drag-resize kolom itu.
    - Drag (B1-Motion) → lebar mengikuti mouse (clamp minwidth).
    - Double-click di tepi kolom → auto-fit kolom itu ke lebar konten.
    """
    state = {"col": None, "start_x": 0, "start_w": 0}

    def _edges():
        cols = _tree_display_columns(tree)
        x = 0
        out = []
        for c in cols:
            x += tree.column(c, "width")
            out.append((x, c))
        return out

    def _near_edge(cx):
        best = None
        for edge_x, col in _edges():
            if abs(cx - edge_x) <= edge_px:
                best = col  # pilih yang terakhir dalam toleransi
        return best

    def _on_press(event):
        if state["col"] is not None:
            return "break"
        try:
            region = tree.identify_region(event.x, event.y)
        except Exception:
            return None
        if region not in ("heading", "separator"):
            return None
        col = _near_edge(_tree_content_x(tree, event.x))
        if col is None:
            return None  # klik heading biasa → sort/filter tetap jalan
        state["col"] = col
        state["start_x"] = event.x
        state["start_w"] = tree.column(col, "width")
        return "break"

    def _on_motion(event):
        if state["col"] is None:
            return None
        try:
            min_w = tree.column(state["col"], "minwidth") or 24
        except Exception:
            min_w = 24
        new_w = int(max(min_w, state["start_w"] + (event.x - state["start_x"])))
        try:
            tree.column(state["col"], width=new_w)
        except tk.TclError:
            pass
        return "break"

    def _on_release(_event):
        if state["col"] is None:
            return None
        state["col"] = None
        return "break"

    def _on_double(event):
        try:
            region = tree.identify_region(event.x, event.y)
        except Exception:
            return None
        if region not in ("heading", "separator"):
            return None
        col = _near_edge(_tree_content_x(tree, event.x))
        if col is None:
            return None
        auto_fit_columns(tree, columns=[col])
        return "break"

    tree.bind("<Button-1>", _on_press, add="+")
    tree.bind("<B1-Motion>", _on_motion, add="+")
    tree.bind("<ButtonRelease-1>", _on_release, add="+")
    tree.bind("<Double-1>", _on_double, add="+")
    return tree


def auto_fit_columns(tree: ttk.Treeview, columns=None, *,
                     max_width: int = 340, min_width: int = 44,
                     pad: int = 24, sample_rows: int = 400):
    """v3.4 — Auto-fit lebar kolom ke konten (judul + sampel baris).

    Ukuran dihitung dari font tabel (family, 9) via Font.measure:
    max(lebar judul, lebar isi terpanjang sampel) + pad, dibatasi
    [min_width, max_width]. Untuk tabel besar hanya sampel `sample_rows`
    baris merata yang diukur (ukur 400×30 sel < 100ms).
    """
    import tkinter.font as tkfont
    from .theme import font_family

    cols = list(columns) if columns is not None else _tree_display_columns(tree)
    try:
        meas = tkfont.Font(family=font_family(), size=9).measure
    except Exception:
        def meas(s):  # fallback kasar
            return 7 * len(str(s))

    try:
        children = tree.get_children("")
    except tk.TclError:
        return
    n = len(children)
    if n > sample_rows:
        step = n / float(sample_rows)
        idxs = sorted({min(n - 1, int(i * step)) for i in range(sample_rows)})
    else:
        idxs = list(range(n))

    # cache values per baris sampel (1 panggilan Tcl per baris)
    sampled_vals = []
    sampled_texts = []
    for i in idxs:
        it = tree.item(children[i])
        sampled_vals.append(it.get("values") or [])
        sampled_texts.append(str(it.get("text") or ""))

    col_pos = {c: k for k, c in enumerate(_tree_display_columns(tree))}
    # values[] TIDAK memuat #0 — shift index hanya bila kolom tree tampil
    disp = _tree_display_columns(tree)
    tree_shift = 1 if (disp and disp[0] == "#0") else 0
    for col in cols:
        try:
            w = meas(str(tree.heading(col, "text") or "")) + pad + 10
        except tk.TclError:
            continue
        if col == "#0":
            for t in sampled_texts:
                w = max(w, meas(t) + pad + 18)
        else:
            k = col_pos.get(col, 0) - tree_shift
            for vals in sampled_vals:
                if 0 <= k < len(vals):
                    w = max(w, meas(str(vals[k])) + pad)
        try:
            tree.column(col, width=int(min(max(w, min_width), max_width)))
        except tk.TclError:
            continue


# --- Maximize table (fullscreen clone) ----------------------------------------

def open_tree_maximized(source_tree: ttk.Treeview, title: str, *,
                        setup_tags=None, on_double_click=None,
                        on_sort_setup=None, on_context_menu=None):
    """Buka window besar berisi clone penuh dari source_tree — tombol ⛶.

    setup_tags(new_tree)   : pasang tag styling (mis. self._setup_tags).
    on_double_click(event) : handler double-click — harus tree-agnostic
                             (identifikasi baris via event.widget).
    on_sort_setup(new_tree): pasang command sort heading per view.
    on_context_menu(event) : handler klik-kanan (copy Nomor/Nomor PO, dll).

    Return (win, new_tree).
    """
    root = source_tree.winfo_toplevel()
    win = tk.Toplevel(root)
    win.title(f"{title} — Perbesar")
    win.configure(bg=C_BG)
    win.transient(root)

    try:
        rw, rh = root.winfo_width(), root.winfo_height()
        rw = rw if rw > 300 else 1280
        rh = rh if rh > 300 else 760
        w, h = int(rw * 0.95), int(rh * 0.92)
        x = int(root.winfo_rootx() + (rw - w) / 2)
        y = int(root.winfo_rooty() + (rh - h) / 2)
        win.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
    except Exception:
        win.geometry("1240x760")

    # -- header band gelap --
    head = tk.Frame(win, bg=C_HEADER)
    head.pack(fill="x")
    hi = tk.Frame(head, bg=C_HEADER)
    hi.pack(fill="x", padx=16, pady=10)
    tk.Label(hi, text="⛶", bg=C_HEADER, fg="#5eead4",
             font=(font_family(), 12, "bold")).pack(side="left")
    tk.Label(hi, text=title, bg=C_HEADER, fg="#f1f5f9",
             font=font(12, "bold")).pack(side="left", padx=(8, 0))
    tk.Button(
        hi, text="↔ Auto-Fit", command=lambda: auto_fit_columns(new_tree),
        bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
        activeforeground="#ffffff", bd=0, relief="flat",
        highlightthickness=0, cursor="hand2", font=font(9, "bold"),
        padx=12, pady=5,
    ).pack(side="right", padx=(0, 6))
    tk.Button(
        hi, text="✕ Tutup (Esc)", command=win.destroy,
        bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
        activeforeground="#ffffff", bd=0, relief="flat",
        highlightthickness=0, cursor="hand2", font=font(9, "bold"),
        padx=12, pady=5,
    ).pack(side="right")

    # -- body --
    body = tk.Frame(win, bg=C_BG)
    body.pack(fill="both", expand=True, padx=12, pady=12)
    card = tk.Frame(body, bg=C_CARD, highlightbackground=C_BORDER,
                    highlightthickness=1)
    card.pack(fill="both", expand=True)
    cin = tk.Frame(card, bg=C_CARD)
    cin.pack(fill="both", expand=True, padx=8, pady=8)

    try:
        # Tk 9.x: cget("show") mengembalikan tuple index-object —
        # deteksi via representasi string (kompatibel Tk 8 & 9)
        raw = source_tree.cget("show")
        parts = " ".join(str(x) for x in raw) if isinstance(raw, (tuple, list)) \
            else str(raw)
        show_opt = "tree headings" if "tree" in parts else "headings"
    except Exception:
        show_opt = "headings"
    new_tree = ttk.Treeview(cin, columns=list(source_tree["columns"]),
                            show=show_opt, selectmode="browse")

    for cid in ["#0"] + list(source_tree["columns"]):
        try:
            cfg = source_tree.column(cid)
            new_tree.column(cid, width=cfg.get("width", 100),
                            minwidth=cfg.get("minwidth", 40),
                            anchor=cfg.get("anchor", "w"),
                            stretch=cfg.get("stretch", True))
            h = source_tree.heading(cid)
            kw = {"text": h.get("text", "")}
            if h.get("image"):
                kw["image"] = h["image"]
            new_tree.heading(cid, **kw)
        except tk.TclError:
            continue

    if setup_tags:
        try:
            setup_tags(new_tree)
        except Exception:
            pass

    # v3.4: resize kolom manual + auto-fit — dipasang PERTAMA supaya
    # "break" saat drag/double-click tepi kolom mematikan handler view
    enable_col_resize(new_tree)

    vsb = ttk.Scrollbar(cin, orient="vertical", command=new_tree.yview)
    hsb = ttk.Scrollbar(cin, orient="horizontal", command=new_tree.xview)
    new_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    new_tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    cin.grid_rowconfigure(0, weight=1)
    cin.grid_columnconfigure(0, weight=1)

    foot = tk.Frame(cin, bg=C_CARD)
    foot.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
    count_var = tk.StringVar(value="Menyalin tabel…")
    tk.Label(foot, textvariable=count_var, bg=C_CARD, fg=C_TEXT_MUTED,
             font=font(9)).pack(side="left")
    tk.Label(foot, text="🖱 Double-click = detail · klik kanan = copy "
                        "(bila tersedia) · Esc = tutup",
             bg=C_CARD, fg=C_TEXT_SOFT, font=font(8)).pack(side="right")

    overlay = LoadingOverlay(cin, "Menyalin tabel…")
    overlay.show(delay_ms=120)

    items = []

    def collect(parent):
        for iid in source_tree.get_children(parent):
            it = source_tree.item(iid)
            items.append((parent, iid, {
                "text": it.get("text", ""),
                "values": it.get("values", ""),
                "tags": it.get("tags", ""),
                "open": it.get("open", False),
            }))
            collect(iid)

    collect("")

    def done():
        overlay.hide()
        count_var.set(f"{len(items):,} baris · {title}")

    insert_cancel = insert_tree_items(new_tree, items, batch=600,
                                      on_done=done,
                                      chunk_callback=lambda n, t: count_var.set(
                                          f"Menyalin {n:,}/{t:,} baris…"))

    def _on_win_destroy(event):
        # batalkan batch + timer yang masih pending saat window ditutup
        if event.widget is win:
            insert_cancel()
            overlay.hide()

    win.bind("<Destroy>", _on_win_destroy, add="+")

    if on_double_click:
        new_tree.bind("<Double-1>", on_double_click)
    if on_context_menu:
        new_tree.bind("<Button-3>", on_context_menu)
    if on_sort_setup:
        on_sort_setup(new_tree)

    win.bind("<Escape>", lambda e: win.destroy())
    win.focus_set()
    return win, new_tree
