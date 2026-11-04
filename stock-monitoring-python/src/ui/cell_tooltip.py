"""cell_tooltip.py — v3.11.47 — Tooltip hover reusable untuk ttk.Treeview.

User: "kolom cek di tab deviasi gr dan deviasi pcs kan kadang terlalu
panjang ke kanan misal aku klik cell itu terus muncul pop up tampilan
lengkap nya bisa gak?" — pilih opsi 2A (tooltip hover saja, 0.5 dtk).

Modul ini dibuat reusable supaya bisa dipakai:
- ``deviasi_view`` untuk kolom CEK (panjang narasi anomali);
- ``saldo_minus_view`` untuk kolom Keterangan / Nomor PO / Status PO;
- ``analisa_kronis_view`` untuk kolom Rekomendasi (narasi panjang).

Pola Tkinter Toplevel + ``after(delay_ms)``: hover 500ms di cell target
→ Toplevel tip kecil dekat cursor (clamp ke layar); mouse leave / klik /
cell berubah → cancel + hide. Tidak mengganggu binding <Motion> yang
sudah ada (bind ``add="+"``). Tidak override single-click follow-up /
double-click drill-down (tooltip cuma Toplevel pasif, no grab).

Provider: fungsi ``provider(iid, col_id) -> str | None`` — view host
yang tahu sumber nilai (cache _cek_map / _minus_df / etc.) yang
menentukan teks tip per-cell. Return None / "" → tip tidak muncul.
"""
from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from .theme import font
from .widgets import identify_to_column

# Delay sebelum tip muncul (ms). 500ms = natural hover ( tidak flicker saat
# user cepat gerak melewati cell tanpa niat membaca).
_DEFAULT_DELAY_MS = 500
# Lebar maks tip (px). Teks panjang akan di-wrap (wraplength) supaya tip
# tidak melebar selebar layar.
_DEFAULT_MAX_WIDTH = 460


class CellTooltip:
    """Hover tooltip reusable untuk ttk.Treeview.

    Pemakaian::

        tip = CellTooltip(tree, provider=lambda iid, col: (
            tree.set(iid, col) if len(tree.set(iid, col)) > 30 else None
        ))

    ``provider`` dipanggil saat timer delay habis — return ``None`` / "" →
    tidak ada tip; ``str`` → tip muncul dgn teks itu. Gunakan kontrak ini
    utk filter "cuma tampilkan tip bila cell terpotong" (lihat
    ``CellTooltip.truncate_provider``).
    """

    def __init__(
        self,
        tree: ttk.Treeview,
        *,
        provider: Callable[[str, str], str | None] | None = None,
        delay_ms: int = _DEFAULT_DELAY_MS,
        max_width: int = _DEFAULT_MAX_WIDTH,
        bg: str = "#1f2937",       # slate-800
        fg: str = "#f9fafb",       # gray-50
        border: str = "#0f172a",   # slate-900
    ):
        self._tree = tree
        self._provider = provider
        self._delay_ms = max(50, int(delay_ms))
        self._max_width = max(120, int(max_width))
        self._bg = bg
        self._fg = fg
        self._border = border
        # state
        self._tip: tk.Toplevel | None = None
        self._after_id: str | None = None
        self._cur_iid: str | None = None
        self._cur_col: str | None = None
        self._destroyed = False
        # v3.11.48 — FIX audit #1: capture funcid tiap bind (add="+") supaya
        # destroy() hanya melepas binding CellTooltip sendiri, BUKAN semua
        # binding sequence itu di tree (yc deviasi_view _on_tree_motion cursor
        # hand2, enable_multi_select Button-1 handler, dll — wiped sebelumnya
        # oleh unbind(seq, None) yg jalan tk.call('bind', w, seq, '')).
        # Tkinter bind(add="+") return funcid str di Python 3.x (verifikasi
        # CPython source _bind); bila None (teoretis Tk lama) → unbind di-skip.
        self._motion_funcid = tree.bind(
            "<Motion>", self._on_motion, add="+")
        self._leave_funcid = tree.bind(
            "<Leave>", self._on_leave, add="+")
        self._button1_funcid = tree.bind(
            "<Button-1>", self._hide_now, add="+")
        self._destroy_funcid = tree.bind(
            "<Destroy>", self._on_tree_destroy, add="+")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def destroy(self) -> None:
        """Lepas binding + tutup tip (view host _on_view_destroy).

        v3.11.48 — FIX audit: hanya unbind funcid CellTooltip sendiri
        (bukan unbind(seq) tanpa funcid yg akan wipe SEMUA binding seq itu).
        """
        if self._destroyed:
            return
        self._destroyed = True
        self._cancel_schedule()
        self._hide_now()
        for seq, fid in (
            ("<Motion>", self._motion_funcid),
            ("<Leave>", self._leave_funcid),
            ("<Button-1>", self._button1_funcid),
            ("<Destroy>", self._destroy_funcid),
        ):
            if fid:
                with contextlib.suppress(tk.TclError):
                    self._tree.unbind(seq, fid)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _on_motion(self, event) -> None:
        if self._destroyed:
            return
        tree = event.widget
        try:
            region = tree.identify_region(event.x, event.y)
            if region != "cell":
                self._cancel_and_hide()
                return
            iid = tree.identify_row(event.y)
            col = identify_to_column(tree, tree.identify_column(event.x))
            if not iid or not col:
                self._cancel_and_hide()
                return
        except tk.TclError:
            self._cancel_and_hide()
            return
        # sama cell? biarkan timer berjalan (jangan restart — flicker)
        if iid == self._cur_iid and col == self._cur_col:
            return
        # v3.11.48 — FIX audit #4: cell berubah → sembunyikan tip LAMA
        # segera (sebelum schedule tip baru) — standar tooltip UX, bukan
        # tip stale cell A nempel 500ms saat user hover cell B.
        self._hide_now()
        self._cur_iid = iid
        self._cur_col = col
        self._cancel_schedule()
        self._after_id = tree.after(
            self._delay_ms, lambda: self._show(iid, col))

    def _on_leave(self, event) -> None:
        # v3.11.48 — FIX audit #3: <Leave> fires spuriously saat pointer
        # masuk CHILD widget tree (yc label overlay CellColorOverlay utk
        # cell ber-tag warna). Cek apakah pointer MASIH di dalam tree
        # (atau child tree) — bila ya, jangan cancel timer / hide tip.
        try:
            x_root = event.x_root
            y_root = event.y_root
        except AttributeError:
            x_root = y_root = None
        if x_root is not None and y_root is not None:
            try:
                containing = self._tree.winfo_containing(x_root, y_root)
            except tk.TclError:
                containing = None
            if containing is not None:
                # pointer masih di tree atau child-nya → biarkan timer jalan
                # (bukan benar-benar leave tree).
                tree_self = self._tree
                try:
                    # cek containing == tree ATAU descendant tree
                    w = containing
                    while w is not None:
                        if w is tree_self:
                            return  # masih di dalam tree — skip cancel
                        try:
                            w = w.master
                        except AttributeError:
                            break
                except tk.TclError:
                    pass
        self._cancel_and_hide()

    def _on_tree_destroy(self, event) -> None:
        # tree di-destroy → tip ikut dibunuh (no dangling Toplevel)
        with contextlib.suppress(Exception):
            self.destroy()

    def _cancel_schedule(self) -> None:
        if self._after_id is not None:
            with contextlib.suppress(Exception):
                self._tree.after_cancel(self._after_id)
            self._after_id = None

    def _cancel_and_hide(self) -> None:
        self._cancel_schedule()
        self._cur_iid = None
        self._cur_col = None
        self._hide_now()

    def _hide_now(self, *args: Any) -> None:
        if self._tip is not None:
            with contextlib.suppress(tk.TclError):
                if self._tip.winfo_exists():
                    self._tip.destroy()
            self._tip = None

    def _show(self, iid: str, col: str) -> None:
        if self._destroyed:
            return
        self._after_id = None
        # cell masih under cursor?
        if (iid, col) != (self._cur_iid, self._cur_col):
            return
        if self._provider is None:
            return
        try:
            text = self._provider(iid, col)
        except Exception as exc:  # noqa: BLE001 — provider host gagal ≠ tooltip crash
            # v3.11.48 — FIX audit #7: log exception utk diagnostic (sebelumnya
            # senyap). Pakai logging (bukan print) supaya tidak ke tab Proses.
            import logging
            logging.getLogger(__name__).debug(
                "CellTooltip provider error: %r", exc)
            text = None
        if not text:
            return
        text = str(text)
        self._render_tip(text)

    def _render_tip(self, text: str) -> None:
        tree = self._tree
        if not tree.winfo_exists():
            return
        if self._tip is None or not self._tip.winfo_exists():
            self._tip = tk.Toplevel(tree)
            self._tip.wm_overrideredirect(True)
            # v3.11.49 — FIX regression v3.11.48: HAPUS wm_transient —
            # konflik dgn overrideredirect(True) di Windows Tk: transient
            # trigger WM interaction → posisi reset ke (0,0) → tip muncul
            # di POJOK KIRI ATAS layar (user report: "tooltip berada di
            # pojok kirii atas?"). Audit #5 concern (tip obscured by
            # other Toplevels in X11) sudah diatasi oleh lift() saja
            # (line bawah) — tidak butuh transient.
            self._tip.attributes("-topmost", True)
            self._tip.configure(bg=self._border)
            lbl = tk.Label(
                self._tip, text=text, justify="left",
                bg=self._bg, fg=self._fg, relief="flat",
                font=font(9), padx=10, pady=7,
                wraplength=self._max_width)
            lbl.pack(fill="both", expand=True, padx=1, pady=1)
        else:
            # update text pada label yang sudah ada
            for child in self._tip.winfo_children():
                try:
                    child.configure(text=text)
                except tk.TclError:
                    pass
        # posisi dekat cursor (sedikit offset kanan-bawah)
        try:
            px = tree.winfo_pointerx()
            py = tree.winfo_pointery()
        except tk.TclError:
            return
        x = px + 14
        y = py + 18
        # clamp ke layar
        self._tip.update_idletasks()
        try:
            w = self._tip.winfo_reqwidth()
            h = self._tip.winfo_reqheight()
            sw = tree.winfo_screenwidth()
            sh = tree.winfo_screenheight()
            # v3.11.48 — FIX audit #6: tip lebih tinggi dari layar →
            # kurangi wraplength proporsional supaya muat.
            if h > sh - 8 and self._max_width > 200:
                new_wl = max(200, int(self._max_width * (sh - 8) / h))
                for child in self._tip.winfo_children():
                    try:
                        child.configure(wraplength=new_wl)
                    except tk.TclError:
                        pass
                self._tip.update_idletasks()
                w = self._tip.winfo_reqwidth()
                h = self._tip.winfo_reqheight()
            if x + w > sw - 4:
                x = max(4, sw - w - 4)
            if y + h > sh - 4:
                # tampilkan di atas cursor bila tidak muat di bawah
                y = max(py - h - 8, 4)
            # v3.11.49 — set geometry PERSIS sebelum lift; gunakan
            # format lengkap WxH+X+Y utk reliability cross-platform
            # (hanya +X+Y kadang tidak stick di beberapa Tk version).
            self._tip.wm_geometry(f"{w}x{h}+{x}+{y}")
            # v3.11.48 — FIX audit #5: lift() memaksa tip ke atas stack
            # window (redundant dgn -topmost tapi lebih reliable di X11).
            self._tip.lift()
        except tk.TclError:
            pass


__all__ = ["CellTooltip"]
