"""followup_view.py — Tab "☑ Follow Up" (v3.2.0) — ala repo Waste.

v3.9.6 (permintaan user: "Format Follow UP Seperti File Sample"):
format tabel mengikuti sheet Follow UP workbook asli user (01.1 CEK
STOCK V2.xlsb): Resto · Nama Barang · SO per tanggal (heading ANGKA
TANGGAL — H=25 → 23/24/25/26/27, persis kolom "22.0..27.0" sample) ·
Sistem · Deviasi · Loss Surplus to BOM · Keterangan · kolom kerja FU:
SO · DEVIASI · Selisih · Selisih Deviasi · Cek FU · PIC · Status TL ·
Ditambahkan. Snapshot lama tanpa field tanggal tetap dimuat (kolom
  tampil "-"). Export Excel mengikuti format yang sama.

Daftar baris anomali yang di-CENTANG (kolom ✓) di tab DEVIASI GR /
DEVIASI PCS / LAPORAN DEVIASI — shortlist investigasi berbentuk SNAPSHOT
(nilai apa adanya saat baris dicentang; TIDAK ikut filter/H aktif).

Perilaku:
- Baris menetap: tertutup aplikasi pun aman (followup.json, atomic write).
- Klik sel ✓ di tabel ini = KELUARKAN baris dari daftar.
- 💾 Export Excel: format file sample + kolom kerja FU (SO · DEVIASI ·
  Selisih · Selisih Deviasi · Cek FU · PIC — diisi petugas).
  (v3.8: fitur 📥 Impor Hasil TL DIHAPUS — permintaan user "gak terlalu
  perlu".)
- ✕ Kosongkan: hapus seluruh daftar (konfirmasi).
- Double-click baris → pop-up detail source (bila data pipeline tersedia).
- Sort kolom via klik judul (parse angka negatif kurung).
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

import pandas as pd

from .followup import CHECK_ON, DATE_COL_IDS, FollowUpStore
from .theme import (
    C_BG,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    font,
)
from .widgets import (
    AccentButton,
    Card,
    ColumnManager,
    DangerButton,
    EmptyState,
    GhostButton,
    HeaderFilterGroup,
    LoadingOverlay,
    TableExpander,
    attach_clone_filters,
    auto_fit_columns,
    enable_col_resize,
    identify_to_column,
    insert_tree_items,
    open_tree_maximized,
    run_async,
    sort_tree_by_column,
)

# kolom tabel Follow Up — FORMAT FILE SAMPLE (v3.9.6):
# ✓ · Resto · Nama Barang · [SO tgl H-2..H+2 — id "T-2".."T+2", heading
# dinamis angka tanggal] · Sistem · Deviasi · Loss Surplus to BOM ·
# Keterangan · SO · DEVIASI · Selisih · Selisih Deviasi · Cek FU · PIC ·
# Status TL · Ditambahkan (kolom kerja FU dari resolved store; Asal &
# tracking app tetap dibawa di bagian akhir).
COLUMNS = [
    ("✓", 34, "center"),
    ("Resto", 90, "w"),
    ("Nama Barang", 220, "w"),
    ("T-2", 64, "e"),
    ("T-1", 64, "e"),
    ("T", 64, "e"),
    ("T+1", 64, "e"),
    ("T+2", 64, "e"),
    ("Sistem", 80, "e"),
    ("Deviasi", 80, "e"),
    ("Loss Surplus to BOM", 105, "e"),
    ("Keterangan", 140, "w"),
    ("SO", 80, "e"),
    ("DEVIASI", 80, "e"),
    ("Selisih", 70, "e"),
    ("Selisih Deviasi", 90, "e"),
    ("Cek FU", 70, "center"),
    ("Asal", 100, "w"),
    ("Status TL", 90, "w"),
    ("PIC", 110, "w"),
    ("Ditambahkan", 120, "w"),
]


class FollowUpView(tk.Frame):
    """Tab Follow Up: tabel snapshot baris tercentang + ekspor."""

    def __init__(self, parent, store: FollowUpStore,
                 get_data: Optional[Callable[[], Optional[pd.DataFrame]]] = None,
                 go_to_proses: Callable | None = None):
        super().__init__(parent, bg=C_BG)
        self.store = store
        self.get_data = get_data      # akses append1_df (untuk popup detail)
        self.go_to_proses = go_to_proses
        # v3.3: peta iid → fingerprint (BUKAN index) — klik ✓ / double-click
        # mengenai baris yang benar WALAUPUN tabel sudah di-sort/di-reorder
        # (bug v3.2: tree.index() + _fp_order → salah baris setelah sort)
        self._iid_fp: dict[str, str] = {}

        self._build_ui()
        self._setup_tags()
        store.add_listener(self._on_store_changed)
        self._render()

    # =========================================================================
    # UI BUILD
    # =========================================================================
    def _build_ui(self):
        # --- Empty state ---
        self.empty = EmptyState(
            self, icon="📌", title="Daftar Follow Up masih kosong",
            cta_text="🚀 Jalankan Pipeline",
            on_cta=lambda: self.go_to_proses() if self.go_to_proses else None)
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Konten utama ---
        self.content = tk.Frame(self, bg=C_BG)

        # --- Kartu aksi (ringkas — tanpa KPI row) ---
        ccard = Card(self.content, title="Daftar Follow Up")
        ccard.pack(fill="x", padx=12, pady=(12, 0))
        cbody = ccard.body()

        r0 = tk.Frame(cbody, bg=C_CARD)
        r0.pack(fill="x")
        self.btn_export = AccentButton(r0, text="💾 Export Excel",
                                       command=self._on_export)
        self.btn_export.pack(side="left")

        self.btn_import = None  # v3.8: Impor Hasil TL DIHAPUS (user)

        self.btn_clear = DangerButton(r0, text="✕ Kosongkan",
                                      command=self._on_clear)
        self.btn_clear.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="0 baris.")
        tk.Label(r0, textvariable=self.status_var, bg=C_CARD, fg=C_HEADER,
                 font=font(9, "bold")).pack(side="right")

        # --- Tabel card ---
        tcard = Card(self.content)
        tcard.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tbody = tcard.body()

        head = tk.Frame(tbody, bg=C_CARD)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        title_label = tk.Label(head, text="Follow Up — baris anomali terpilih",
                               bg=C_CARD, fg=C_HEADER, font=font(10, "bold"))
        title_label.pack(side="left")
        # v3.9 (ala Waste): ⛶ = Layar Penuh (window terpisah)
        btn_max = GhostButton(head, text="⛶ Layar Penuh",
                              command=self._maximize)
        btn_max.pack(side="right")
        # v3.9 (ala Waste): ⤢ = Perbesar Tabel (in-place)
        btn_expand = GhostButton(head, text="⤢ Perbesar Tabel")
        btn_expand.pack(side="right", padx=(0, 6))
        btn_cols = GhostButton(head, text="◱ Kolom",
                               command=lambda: self._colmgr.open_panel())
        btn_cols.pack(side="right", padx=(0, 6))
        btn_fit = GhostButton(head, text="↔ Auto-Fit", command=self._auto_fit)
        btn_fit.pack(side="right", padx=(0, 6))

        col_ids = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="browse")
        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            # v3.5: SEMUA kolom pakai filter header ⧩ (sort via popup);
            # ✓ = keluarkan via klik sel
            self.tree.heading(col_name, text=col_name)

        vsb = ttk.Scrollbar(tbody, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        # v3.4: drag tepi heading = resize lebar kolom; double-click tepi =
        # auto-fit (dipasang SEBELUM handler klik view supaya "break" efektif)
        enable_col_resize(self.tree)

        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        # Loading overlay
        self.overlay = LoadingOverlay(tbody, "Menyiapkan daftar…")

        # v3.5: filter header ⧩ di SEMUA kolom (kecuali ✓)
        _filter_cols = [c[0] for c in COLUMNS if c[0] != "✓"]
        self._col_sel: dict = {c: None for c in _filter_cols}
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        # v3.6: hide/unhide kolom (klik kanan heading / tombol ◱ Kolom)
        self._colmgr = ColumnManager(
            self.tree,
            open_filter=lambda c: self.header_filters.open_popup(c))

        # v3.9 (ala Waste): ⤢ Perbesar Tabel — ciutkan kartu aksi + judul
        self._expander = TableExpander(btn_expand, [ccard, title_label])

        self.tree.bind("<Double-1>", self._on_double_click, add="+")  # FIX B-04
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

    def _setup_tags(self):
        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f8fafc")
        self.tree.tag_configure("negative", foreground="#dc2626")
        self.tree.tag_configure("resolved", foreground="#059669")
        self.tree.tag_configure("pending", foreground="#b45309")

    # =========================================================================
    # RENDER
    # =========================================================================
    def _on_store_changed(self, store):
        # dipanggil listener store (toggle dari tab lain)
        try:
            if self.winfo_exists():
                self.after(0, self._render)
        except tk.TclError:
            pass

    def _show_empty(self):
        self.content.pack_forget()
        self.empty.pack(fill="both", expand=True, padx=12, pady=12)

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    def _col_values(self, col: str) -> list:
        """Nilai unik TERFORMAT utk popup filter header (v3.5)."""
        rows = list(self.store.rows.values())
        if not rows:
            return []
        idx = [i for i, c in enumerate(COLUMNS) if c[0] == col]
        if not idx:
            return []
        j = idx[0]
        vals = []
        for snap in rows:
            info = self.store.resolved.get(snap.get("fp", ""), {})
            vals.append(str(self._fu_row_values(snap, bool(info), info)[j]))
        return sorted(set(vals))

    def _on_col_filter(self, col: str, selected):
        self._col_sel[col] = selected
        self._render()

    @staticmethod
    def _fu_num(v):
        try:
            f = float(v)
            return f"{f:,.0f}" if f == int(f) else f"{f:,.1f}"
        except (TypeError, ValueError):
            return str(v or "-")

    @staticmethod
    def _fu_pct(v):
        """Loss Surplus to BOM — rasio gaya file sample (1.0053 → '1.01';
        0.0524 → '0.05'; minus kurung). Format mengikuti konvensi _fu_num
        (desimal titik) supaya parser sort _sort_by tetap benar."""
        try:
            f = float(v)
        except (TypeError, ValueError):
            return "-" if v in ("", None) else str(v)
        if f == 0:
            return "-"
        s = f"{f:,.2f}"
        return f"({s[1:]})" if f < 0 else s

    def _fu_row_values(self, snap, resolved, info) -> list:
        """Nilai terformat satu baris follow-up (urutan COLUMNS — dipakai
        render + filter header supaya nilai popup == yang tampil).
        v3.9.6: urutan FORMAT FILE SAMPLE — SO per tanggal (H-2..H+2),
        Sistem, Deviasi, Loss Surplus to BOM, Keterangan, kolom kerja FU
        (SO/DEVIASI salinan + Selisih/Selisih Deviasi/Cek FU dari info)."""
        dev = snap.get("deviasi", 0)
        try:
            dev_f = float(dev)
        except (TypeError, ValueError):
            dev_f = 0.0
        dev_txt = self._fu_num(dev) if dev_f else "-"
        if dev_f < 0:
            dev_txt = f"({dev_txt[1:] if dev_txt.startswith('-') else dev_txt})"

        def _so(v):
            try:
                return self._fu_num(float(v)) if v not in ("", None) else "-"
            except (TypeError, ValueError):
                return "-"

        # snapshot lama (pre-v3.9.6) tanpa field tanggal → "-"
        return [
            CHECK_ON,
            snap.get("resto", ""),
            snap.get("barang", ""),
            _so(snap.get("so_m2")), _so(snap.get("so_m1")),
            _so(snap.get("so")), _so(snap.get("so_p1")),
            _so(snap.get("so_p2")),
            _so(snap.get("sistem")),
            dev_txt,
            self._fu_pct(snap.get("loss_bom")),
            snap.get("cek", "") or "-",
            _so(snap.get("so")),
            dev_txt,
            self._fu_num(info.get("Selisih")) if info.get("Selisih")
            not in ("", None) else "-",
            self._fu_num(info.get("Selisih Deviasi"))
            if info.get("Selisih Deviasi") not in ("", None) else "-",
            str(info.get("Cek FU", "") or "-"),
            snap.get("asal", ""),
            "Selesai" if resolved else "Menunggu",
            info.get("PIC", ""),
            (snap.get("added_at", "") or "")[:16].replace("T", " "),
        ]

    def _refresh_date_headings(self, rows):
        """v3.9.6: heading kolom tanggal = ANGKA TANGGAL dari H snapshot
        terbaru (H=25 → '23'..'27' — persis sheet Follow UP file sample
        '22.0..27.0'). H tidak ada → id default T-2..T+2."""
        h_ref = None
        for snap in reversed(rows):
            h_val = snap.get("h")
            if isinstance(h_val, (int, float)) and h_val:
                h_ref = int(h_val)
                break
        if h_ref is None:
            for col_id in DATE_COL_IDS:
                self.tree.heading(col_id, text=col_id)
        else:
            for col_id, off in zip(DATE_COL_IDS, (-2, -1, 0, 1, 2)):
                self.tree.heading(col_id, text=str(h_ref + off))
        if getattr(self, "header_filters", None) is not None:
            self.header_filters.refresh_icons()

    def _render(self):
        rows = list(self.store.rows.values())
        self.tree.delete(*self.tree.get_children())
        self._iid_fp = {}
        if self.header_filters is not None:
            self.header_filters.refresh_icons()

        if not rows:
            self._show_empty()
            self._refresh_date_headings(rows)
            return
        self._show_content()
        self._refresh_date_headings(rows)

        # v3.5: filter header ⧩ (display-only — daftar store tidak berubah)
        col_idx = {c[0]: j for j, c in enumerate(COLUMNS)}
        active = [(col_idx[c], s) for c, s in self._col_sel.items() if s]

        items = []
        n_shown = 0
        for i, snap in enumerate(rows):
            fp = snap.get("fp", "")
            info = self.store.resolved.get(fp, {})
            resolved = bool(info)
            dev = snap.get("deviasi", 0)
            try:
                dev_f = float(dev)
            except (TypeError, ValueError):
                dev_f = 0.0

            values = self._fu_row_values(snap, resolved, info)
            if active and not all(str(values[j]) in s for j, s in active):
                continue

            self._iid_fp[f"fu_{n_shown}"] = fp
            tags = ["evenrow" if n_shown % 2 == 0 else "oddrow"]
            if dev_f < 0:
                tags.append("negative")
            tags.append("resolved" if resolved else "pending")
            items.append(("", f"fu_{n_shown}", {"values": values,
                                                  "tags": tuple(tags)}))
            n_shown += 1

        n = len(rows)
        selesai = self.store.resolved_count()
        self.status_var.set(
            f"{n} baris · {selesai} selesai · {n - selesai} menunggu"
            + (f" · {n_shown} tampil (filter ⧩)" if n_shown != n else ""))
        self.btn_clear.set_enabled(n > 0)
        self.btn_export.set_enabled(n > 0)

        # FIX D-03 (audit 2-d): batalkan batch insert LAMA sebelum render
        # baru — listener store memicu _render SINKRON tiap toggle ✓;
        # dulu chunk loop lama tetap berjalan setelah tree.delete →
        # baris duplikat / TclError iid 'fu_N' sudah ada → render baru
        # TERPOTONG diam-diam (pola komparasi/laporan: cancel disimpan).
        if getattr(self, "_insert_cancel", None) is not None:
            self._insert_cancel()
        self._insert_cancel = insert_tree_items(self.tree, items, batch=500)

    # =========================================================================
    # ✓ KLIK = KELUARKAN (v3.3: iid-based — benar setelah sort)
    # =========================================================================
    def _on_tree_click(self, event):
        tree = event.widget
        try:
            if tree.identify_region(event.x, event.y) != "cell":
                return
            # v3.7 FIX: cocokkan NAMA kolom (bukan posisi display '#1') —
            # setelah kolom ✓ disembunyikan, posisi #1 jatuh ke kolom lain
            # → toggle keluarkan-baris terpicu dari kolom yang salah.
            col = identify_to_column(tree, tree.identify_column(event.x))
            if col != "✓":
                return
            row_iid = tree.identify_row(event.y)
        except Exception:
            return
        if not row_iid:
            return
        fp = self._iid_fp.get(row_iid)
        snap = self.store.rows.get(fp)
        if snap:
            # toggle → off (keluarkan); _render dipanggil via listener
            self.store.toggle(fp, snap)

    # =========================================================================
    # AKSI: EXPORT / KOSONGKAN
    # =========================================================================
    def _on_export(self):
        if not self.store.rows:
            messagebox.showinfo(
                "Export", "Daftar follow-up masih kosong.", parent=self)
            return
        filepath = filedialog.asksaveasfilename(
            title="Simpan Daftar Follow Up",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="follow_up.xlsx",
            parent=self,
        )
        if not filepath:
            return

        def work():
            return self.store.export_xlsx(filepath)

        def done(path):
            # FIX C-06 (audit 2-c): frasa instruksi "Kolom PIC / ...
            # diisi petugas" dihapus (aturan UI-clean v3.9.8 — dialog
            # sukses cukup memberi tahu hasil, bukan cara pakai).
            messagebox.showinfo(
                "Export Berhasil",
                f"Daftar follow-up di-export ke:\n{path}",
                parent=self)

        def on_error(e):
            messagebox.showerror(
                "Export Gagal", f"Tidak bisa export:\n{e}", parent=self)

        run_async(self, work, done, overlay=self.overlay,
                  loading_text="Mengekspor follow-up…", on_error=on_error)

    def _on_clear(self):
        if not self.store.rows:
            return
        if not messagebox.askyesno(
                "Kosongkan Follow Up",
                f"Hapus SEMUA {len(self.store.rows)} baris dari daftar "
                "follow-up?\n\nCentangan di tab Deviasi/Laporan ikut lepas.",
                parent=self):
            return
        self.store.clear()   # _render via listener

    # =========================================================================
    # ⛶ PERBESAR
    # =========================================================================
    def _maximize(self):
        def filter_setup(new_tree):
            # v3.6: funnel ⧩ + sort jalan juga di window besar
            attach_clone_filters(
                new_tree,
                [c[0] for c in COLUMNS if c[0] != "✓"],
                get_values=self._col_values,
                on_sort=lambda c, d, t=new_tree: self._sort_by(c, reverse=d,
                                                               tree=t))

        win, new_tree = open_tree_maximized(
            self.tree, "Daftar Follow Up",
            setup_tags=lambda t: self._setup_tags(),
            on_double_click=self._on_double_click,
            on_filter_setup=filter_setup)
        new_tree.bind("<Button-1>", self._on_tree_click, add="+")
        return win, new_tree

    # =========================================================================
    # SORT (v3.3: engine linear + parse khusus status TL)
    # =========================================================================
    def _auto_fit(self):
        """v3.4 — auto-fit lebar semua kolom ke konten."""
        auto_fit_columns(self.tree)

    def _sort_by(self, col: str, reverse: bool = True, tree=None):
        tree = tree if tree is not None else self.tree

        def parse_fu(s):
            s = str(s).replace(",", "").strip()
            if s in ("Menunggu", "Selesai"):
                return 1 if s == "Menunggu" else 2
            if s in ("-", ""):
                return 0
            if s.startswith("(") and s.endswith(")"):
                return -float(s[1:-1])
            return float(s)

        sort_tree_by_column(tree, col, reverse=reverse, parse=parse_fu)

    # =========================================================================
    # DOUBLE-CLICK → POPUP DETAIL (v3.3: iid-based — benar setelah sort;
    # double-click di kolom ✓ = toggle keluarkan)
    # =========================================================================
    def _on_double_click(self, event):
        tree = event.widget
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return

        # v3.3: double-click sel ✓ = keluarkan baris (bukan popup) —
        # jalan juga saat data source belum tersedia
        # v3.7 FIX: cocokkan NAMA kolom (bukan posisi display '#1')
        try:
            if identify_to_column(tree, tree.identify_column(event.x)) == "✓":
                self._on_tree_click(event)
                return
        except Exception:
            pass

        data = self.get_data() if self.get_data else None
        if data is None or data.empty:
            return

        fp = self._iid_fp.get(row_iid)
        snap = self.store.rows.get(fp)
        if not snap:
            return

        from src.ui.details_popup import show_details_popup
        show_details_popup(
            self.winfo_toplevel(), data,
            nama_barang=snap.get("barang"),
            jenis=None,
            tanggal=None,
            filters={"NAMA RESTO": snap.get("resto")} if snap.get("resto")
            else None,
        )
