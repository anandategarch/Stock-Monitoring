"""
refresh_sources.py — Dialog 🔄 Refresh File Sumber (v3.9.37).

User: "ada tombol refresh untuk file sumber, bisa gak? dan gak harus
refresh semua tapi".

- List SEMUA file Excel sumber pipeline (folder Folders + RootPath utk
  workbook gabungan rekap) dgn checkbox per file.
- Default tercentang = file yang BERUBAH sejak proses terakhir (mtime >
  waktu pipeline terakhir selesai) — sisanya tidak dibaca ulang.
- "🔄 Refresh Terpilih" → hanya file tercentang dibaca ulang dari disk
  (entry cache bacaan file lain tetap dipakai — invalidasi selektif
  lewat helpers.read_cache_invalidate(paths)).
- "🔄 Refresh Semua" → seluruh cache dibuang (semua file dibaca ulang).
- Kolom: ☑ · Folder · File · Diubah · Ukuran; file berubah diberi tanda
  "● berubah" (amber per-cell) + waktu modifikasi tampil di kolom File
  tooltip-free (ringkas d-m-Y H:M).
"""
import datetime
import os
import tkinter as tk
from collections.abc import Callable

from src.pipeline.helpers import _list_excel_files, read_cache_stats

from .theme import (
    C_AMBER,
    C_BG,
    C_BORDER,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    font,
)
from .widgets import AccentButton, GhostButton, apply_cell_tag, make_tree

_ICON_ON = "☑"
_ICON_OFF = "☐"


def _fmt_size(n: float) -> str:
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{int(n)} B"


def _fmt_mtime(ts: float) -> str:
    dt = datetime.datetime.fromtimestamp(ts)
    return (f"{dt.day:02d}-{dt.month:02d}-{dt.year} "
            f"{dt.hour:02d}:{dt.minute:02d}")


class RefreshSourcesDialog(tk.Toplevel):
    """Dialog pilih file sumber yang mau dibaca ulang (refresh selektif).

    Parameter:
    - config: objek src.config.Config (RootPath + Folders dipakai utk
      memindai file sumber).
    - last_run_at: waktu (time.time()) pipeline TERAKHIR selesai — file
      dengan mtime > last_run_at dianggap BERUBAH (tercentang default).
      None = belum pernah run (tak ada yang tercentang default).
    - on_refresh: callback(paths) — None = refresh SEMUA (buang seluruh
      cache), list[str] = refresh file terpilih tersebut.
    """

    def __init__(self, parent, config, last_run_at: float | None = None,
                 on_refresh: Callable[[list | None], None] | None = None,
                 can_refresh: Callable[[], bool] | None = None):
        super().__init__(parent)
        self.title("🔄 Refresh File Sumber")
        self.configure(bg=C_BG)
        self.minsize(880, 560)
        try:
            self.transient(parent)
        except tk.TclError:
            pass
        self._on_refresh = on_refresh
        # v3.9.46 — audit 66 temuan #4: gate status pipeline — dipanggil
        # di _do_refresh SEBELUM dialog menutup dirinya (pipeline hidup →
        # dialog menolak + tetap terbuka, user bisa mencoba lagi)
        self._can_refresh = can_refresh
        self._last_run_at = last_run_at
        self._checked: set = set()

        self._entries = self._scan_sources(config)

        self._build_ui()
        self._populate()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda e: self.destroy())
        # v3.9.46 — audit 66 temuan #4: dialog kini MODAL (grab_set) —
        # dulu hanya transient: jendela utama tetap bisa diklik & pipeline
        # bisa DIMULAI selama dialog terbuka → tombol Refresh kemudian
        # menolak di _start_pipeline SETELAH cache diinvalidasi (cache
        # terbuang tanpa refresh). Dengan grab, interaksi ke jendela utama
        # diblok sampai dialog ditutup (grab dilepas otomatis saat destroy).
        try:
            self.grab_set()
        except tk.TclError:
            pass  # display/parent tak mendukung grab — jalan non-modal

    # =================================================================
    # SCAN FILE SUMBER
    # =================================================================
    def _scan_sources(self, config) -> list:
        """Pindai semua file Excel sumber: tiap folder Folders[key] +
        RootPath (workbook gabungan rekap — mis. 01.1 CEK STOCK V2.xlsb
        sering diletakkan di RootPath; dibaca fn_rekap_mentah fallback).

        Return list dict {label, path, mtime, size, changed} urut
        (folder, nama file)."""
        entries: list = []
        seen: set = set()
        root_path = ""
        folders: dict = {}
        if config is not None:
            root_path = str(getattr(config, "RootPath", "") or "")
            folders = dict(getattr(config, "Folders", {}) or {})

        def _add(label: str, folder: str):
            if not folder or not os.path.isdir(folder):
                return
            try:
                files = _list_excel_files(folder)
            except OSError:
                return
            for f in files:
                key = os.path.normcase(os.path.normpath(f))
                if key in seen:
                    continue  # 2 key Folders bisa menunjuk folder sama
                seen.add(key)
                try:
                    st = os.stat(f)
                    mtime, size = st.st_mtime, st.st_size
                except OSError:
                    mtime, size = 0.0, 0.0
                entries.append({
                    "label": label,
                    "path": f,
                    "mtime": mtime,
                    "size": size,
                    "changed": (self._last_run_at is not None
                                and mtime > self._last_run_at),
                })

        for key in sorted(folders):
            sub = folders[key]
            folder = os.path.join(root_path, str(sub)) if root_path \
                else str(sub)
            _add(f"{key} · {sub}", folder)
        # RootPath sendiri (level induk — workbook gabungan rekap)
        if root_path:
            _add("RootPath · workbook gabungan", root_path)

        entries.sort(key=lambda e: (e["label"],
                                    os.path.basename(e["path"]).lower()))
        return entries

    # =================================================================
    # UI
    # =================================================================
    def _build_ui(self):
        head = tk.Frame(self, bg=C_BG)
        head.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(head, text="🔄 Refresh File Sumber",
                 bg=C_BG, fg=C_HEADER, font=font(13, "bold")).pack(anchor="w")
        tk.Label(head,
                 text="Centang file yang mau dibaca ulang — file lain pakai "
                      "bacaan terakhir (cache). Kolom Diubah = file berubah "
                      "sejak proses terakhir.",
                 bg=C_BG, fg=C_TEXT_MUTED, font=font(9)).pack(anchor="w",
                                                              pady=(2, 0))

        # kartu tabel
        card = tk.Frame(self, bg=C_CARD, highlightbackground=C_BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True, padx=16, pady=8)

        tools = tk.Frame(card, bg=C_CARD)
        tools.pack(fill="x", padx=12, pady=(12, 4))
        GhostButton(tools, text="✓ Semua",
                    command=lambda: self._check_all(True)).pack(side="left")
        GhostButton(tools, text="✓ Kosongkan",
                    command=lambda: self._check_all(False)).pack(
                        side="left", padx=(6, 0))
        GhostButton(tools, text="✓ Berubah",
                    command=self._check_changed).pack(side="left", padx=(6, 0))

        # make_tree: frame internal-nya di-PACK fill+expand ke kartu —
        # beri padding setelah dibuat (pola tree._sm_frame).
        self.tree = make_tree(card, ["cek", "folder", "file", "diubah",
                                     "ukuran"])
        try:
            self.tree._sm_frame.pack_configure(fill="both", expand=True,
                                               padx=12, pady=(0, 8))
        except (AttributeError, tk.TclError):
            pass
        for col, w, anch in (("cek", 40, "center"), ("folder", 260, "w"),
                             ("file", 300, "w"), ("diubah", 110, "w"),
                             ("ukuran", 80, "e")):
            self.tree.column(col, width=w, minwidth=40, anchor=anch,
                             stretch=(col in ("folder", "file")))
            self.tree.heading(col, text={
                "cek": "", "folder": "Folder Sumber", "file": "File",
                "diubah": "Diubah", "ukuran": "Ukuran"}[col])
        # tanda amber per-cell utk kolom Diubah file berubah
        self.tree.tag_configure("src_changed", foreground=C_AMBER)
        # klik baris (area sel) = toggle centang; Space = toggle terpilih
        self.tree.bind("<Button-1>", self._on_click, add="+")
        self.tree.bind("<space>", self._on_space, add="+")
        self.tree.bind("<Double-1>", lambda e: "break")

        # baris status + tombol aksi
        foot = tk.Frame(self, bg=C_BG)
        foot.pack(fill="x", padx=16, pady=(0, 14))
        self.info_var = tk.StringVar(value="")
        tk.Label(foot, textvariable=self.info_var, bg=C_BG,
                 fg=C_TEXT_MUTED, font=font(9, "bold")).pack(side="left")

        self.btn_semua = GhostButton(foot, text="🔄 Refresh Semua",
                                     command=lambda: self._do_refresh(None))
        self.btn_semua.pack(side="right")
        self.btn_terpilih = AccentButton(
            foot, text="🔄 Refresh Terpilih (0)",
            command=self._do_selected)
        self.btn_terpilih.pack(side="right", padx=(0, 6))
        GhostButton(foot, text="Tutup",
                    command=self.destroy).pack(side="right", padx=(0, 6))

    # =================================================================
    # POPULATE + INTERAKSI
    # =================================================================
    def _populate(self):
        for iid in self.tree.get_children(""):
            self.tree.delete(iid)
        self._checked.clear()
        cells_changed: list = []
        for i, e in enumerate(self._entries):
            iid = f"src_{i}"
            self.tree.insert("", "end", iid, values=(
                _ICON_OFF, e["label"], os.path.basename(e["path"]),
                "● berubah" if e["changed"] else "",
                _fmt_size(e["size"])))
            if e["changed"]:
                self._checked.add(iid)
                self.tree.set(iid, "cek", _ICON_ON)
                cells_changed.append((iid, "diubah"))
            elif e["mtime"]:
                # waktu modifikasi sbg info kolom Diubah file tak berubah
                self.tree.set(iid, "diubah", _fmt_mtime(e["mtime"]))
        apply_cell_tag(self.tree, "src_changed", cells_changed)
        self._update_state()

    def _row_iid(self, y: int) -> str:
        try:
            iid = self.tree.identify_row(y)
        except tk.TclError:
            return ""
        return str(iid) if iid else ""

    def _toggle(self, iid: str) -> None:
        if not iid or not iid.startswith("src_"):
            return
        if iid in self._checked:
            self._checked.discard(iid)
            self.tree.set(iid, "cek", _ICON_OFF)
        else:
            self._checked.add(iid)
            self.tree.set(iid, "cek", _ICON_ON)
        self._update_state()

    def _on_click(self, event):
        # hanya area baris data (bukan heading/separator/scrollbar)
        try:
            region = self.tree.identify("region", event.x, event.y)
        except tk.TclError:
            return
        if region not in ("cell", "tree"):
            return
        self._toggle(self._row_iid(event.y))

    def _on_space(self, _event):
        for iid in self.tree.selection():
            self._toggle(str(iid))
        return "break"

    def _check_all(self, on: bool):
        self._checked.clear()
        for iid in self.tree.get_children(""):
            iid = str(iid)
            if on:
                self._checked.add(iid)
                self.tree.set(iid, "cek", _ICON_ON)
            else:
                self.tree.set(iid, "cek", _ICON_OFF)
        self._update_state()

    def _check_changed(self):
        self._checked.clear()
        for i, e in enumerate(self._entries):
            iid = f"src_{i}"
            if e["changed"]:
                self._checked.add(iid)
                self.tree.set(iid, "cek", _ICON_ON)
            else:
                self.tree.set(iid, "cek", _ICON_OFF)
        self._update_state()

    def selected_paths(self) -> list:
        """Path file yang tercentang (urut tampil)."""
        out = []
        for iid in sorted(self._checked, key=lambda s: int(s.split("_")[-1])):
            idx = int(iid.split("_")[-1])
            if 0 <= idx < len(self._entries):
                out.append(self._entries[idx]["path"])
        return out

    def _update_state(self):
        n = len(self._entries)
        m = sum(1 for e in self._entries if e["changed"])
        _ent, _nf, _hit, _miss = read_cache_stats()
        self.info_var.set(
            f"{n} file sumber · {m} berubah sejak proses terakhir · "
            f"cache: {_nf} file tersimpan")
        k = len(self._checked)
        self.btn_terpilih.configure(text=f"🔄 Refresh Terpilih ({k})")
        self.btn_terpilih.set_enabled(k > 0)
        self.btn_semua.set_enabled(n > 0)

    # =================================================================
    # AKSI
    # =================================================================
    def _do_selected(self):
        self._do_refresh(self.selected_paths())

    def _do_refresh(self, paths):
        """Konfirmasi ringan bila 0 terpilih (hanya refresh semua yang
        bisa jalan); panggil callback + tutup dialog.

        v3.9.46 — audit 66 temuan #4: (a) gate can_refresh dicek SEBELUM
        dialog menutup dirinya — pipeline hidup → refresh DITOLAK, dialog
        TETAP TERBUKA + info jelas (dulu dialog selalu menutup diri dulu,
        lalu callback menolak di _start_pipeline SETELAH cache
        diinvalidasi — cache terbuang tanpa refresh, senyap); (b) grab
        dilepas DULU sebelum destroy supaya callback (messagebox dari
        app bila pipeline ternyata berjalan) tidak terblok oleh grab
        dialog yang sudah mati."""
        if paths is not None and not paths:
            return
        if self._can_refresh is not None and not self._can_refresh():
            self.info_var.set(
                "⚠ Pipeline sedang berjalan / masih menghentikan — "
                "refresh DITUNDA (cache tidak dibuang). Tunggu status "
                "berubah, lalu tekan Refresh lagi.")
            return
        cb = self._on_refresh
        try:
            self.grab_release()
        except tk.TclError:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass
        if cb is not None:
            cb(paths)
