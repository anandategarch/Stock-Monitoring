"""
anomali_radar_view.py — Tab 🚨 RADAR ANOMALI (v3.18): tabel SATU utk GR+PCS
berisi pasangan (Barang × Resto × Satuan) yang deviasinya TERGESER LEVEL
(menaik) — anomali kelas "konstan di level baru" yang TIDAK tertangkap
growth harian (tgl lompatan +282% lalu "tenang" +3-4% padahal level baru
menempel — kasus nyata user: BJMHAS · CUP 14 (V.20) PCS: stabil
(177)-(259) tgl 2-22 → (1.293) tgl 23 bersama IN 1.000 → konstan
(1.343)/(1.390) tgl 24-25).

Deteksi = engine anomali_shift (median/MAD dua-jendela per pasangan ×
satuan; level ≥ ×2 baseline & ≥2 hari di level baru; hint kecocokan
kiriman IN ±1 hari — lihat docstring modul itu). SATU tabel lintas
satuan (user: "jadi 1 aja GR dan PCS sekaligus").

v3.18.3 — KOLOM DISEDERHANAKAN (user: "bisa gak jadi lebih sederhana
aja tampilan nya ... Tampilan kolom nya menjadi gini aja: Resto ·
Nama Barang · Tanggal Kejadian · Durasi · Rasio · Deviasi — inti nya
itu berisi informasi dari tanggal berapa sih deviasi nya tuh
meningkat secara stabil dibanding base line? apa karna pengaruh IN
atau gimana meningkat?" + "jika deviasi meningkat di 1 hari dan
trend besok nya mulai turun maka gak perlu dijadikan analisa"): 18
kolom v3.18.2 → 8 INTI —
  ✓ · Resto · Nama Barang (satuan dilipat: "CUP 14 (V.20) · PCS") ·
  Tanggal Kejadian (tgl shift — tgl deviasi mulai naik stabil) ·
  Durasi (hari di level baru) · Rasio (×N, heat) · Deviasi (|dev|
  TANGGAL H — nilai terkini, BUKAN akumulasi; engine dev_h) ·
  Penyebab (3 keadaan: "Dipicu IN 1.000 tgl 23" hijau · "IN 300 tgl
  21 ≠ Δ 1.100" amber · "Tanpa kiriman IN" merah — baris diwarnai
  sesuai keadaan).
Bukti lengkap yang dulunya kolom (baseline, level, Δ, z, IN ± nomor
IT/RI & PO, BM, est nominal) dilipat ke TOOLTIP HOVER baris
(CellTooltip — pola kolom CEK tab 📦/🧩): tabel sederhana, analisa
tetap lengkap ("perkuat analisa sesuai kebutuhan ku").

Interaksi: hover baris = analisa lengkap · double-click baris = popup
Detail Deviasi pasangan itu (bukti per tanggal — pola tab 📦/🧩) ·
klik-kanan = salin sel/baris + "Buka di Deviasi GR" (deep-link
focus_pair) · ⧩ filter header · sort kolom · Ctrl+F cari · ⤢
perbesar. Legend menjelaskan metode + ambang.
Status footer: "N pasangan shift aktif · terbesar ×N (Barang — Resto)".
H mengikuti SharedTanggalH (tab 📦) — refresh saat H berubah.
Empty state: belum ada anomali ≠ error (normal / baseline kurang /
awal bulan) — dijelaskan + CTA ke tab Deviasi GR.

v3.18.2 — INTEGRASI FOLLOW UP (user: "Integrasi Follow Up"): kolom ✓
awal — klik = daftarkan pasangan shift ke daftar ☑ (asal 'RADAR';
snapshot so/sistem/deviasi per H dari frame — pola snap deviasi_view);
☑ LEVEL PASANGAN (entri lama GR/PCS/IMPOR ber-pasangan-sama ikut
menandai — isolasi satuan GR↔PCS tetap; mirror v3.12.3 deviasi_view);
uncek DIKONFIRMASI (jaga-jaga klik tak sengaja — pola _confirm_
unfollow); listener store → sel ✓ radar ikut sinkron saat toggle dari
tab mana pun.
"""
import tkinter as tk
from tkinter import messagebox, ttk

import pandas as pd

from ..pipeline.helpers import (  # v3.18.2 — kunci pasangan kanonik
    KATEGORI_BLANK_LABEL,  # v3.18.6 — filter kategori radar (mirror 📦)
    KATEGORI_DEFAULT_LABEL,  # v3.18.6 — entry gabungan default rekap
    kategori_has_default_values,  # v3.18.6 — entry default hanya bila ada
    kategori_match_mask,  # v3.18.6 — mask kanonik (semua cabang entri)
    norm_nama_barang_key,
    norm_nama_resto_key,
)
from .anomali_shift import (
    RATIO_CUT,  # v3.18 — legenda ambang
    detect_shift_anomalies,
)
from .cell_tooltip import CellTooltip  # v3.18.3 — tooltip hover
from .deviasi_view import SharedKategori  # v3.18.6 — kategori ter-link
from .followup import (  # v3.18.2 — kolom ✓ (pola deviasi_view)
    CHECK_OFF,
    CHECK_ON,
    row_fingerprint,
)
from .nominal_common import (
    fmt_rp_cell,  # v3.18.3 — est nominal di teks tooltip (Δ × harga)
    lookup_harga_pair,  # satuan-aware (pola kolom Nominal deviasi_view)
)
from .theme import (
    C_BG,
    C_CARD,
    C_HEADER,
    C_TEXT_MUTED,
    ROW_EVEN,
    ROW_ODD,
    font,
)
from .widgets import (
    CELL_TAGS_SUPPORTED,
    EmptyState,
    HeaderFilterGroup,
    LegendRow,
    TableExpander,
    apply_cell_tag,
    copy_tree_selection_tsv,  # v3.18 — Ctrl+C baris TSV (pola popup)
    enable_col_resize,
    enable_multi_select,
    fmt_int_id,
    identify_to_column,
    install_tree_find_binding,
    reset_autofit_once,
    run_async,
)

# Kolom (id, lebar, anchor) — GR+PCS SATU tabel (pasangan GR/PCS = 2
# baris terpisah, satuan DILIPAT ke Nama Barang "CUP 14 (V.20) · PCS" —
# user v3.18.3 minta kolom inti saja).
# v3.18.2 — kolom ✓ AWAL (tambah/keluarkan daftar ☑ Follow Up — pola
# deviasi GR/PCS; satu-satunya kolom ikon-only, dikecualikan dari ⧩).
# v3.18.3 — KOLOM INTI (user): "Resto · Nama Barang · Tanggal Kejadian
# (tanggal shift) · Durasi · Rasio · Deviasi (tanggal H — bukan
# akumulasi)" + Penyebab (pertanyaan inti user: "apa karna pengaruh
# IN atau gimana meningkat?") — bukti lain di tooltip hover baris.
COLUMNS = [
    ("✓", 34, "center"),
    ("Resto", 70, "w"),
    ("Nama Barang", 235, "w"),
    ("Tanggal Kejadian", 95, "e"),  # tgl shift — tgl mulai stabil naik
    ("Durasi", 60, "e"),           # hari di level baru (bukan jendela)
    ("Rasio", 60, "e"),            # level ÷ baseline (×N) — sort default ↓
    ("Deviasi", 90, "e"),           # |dev| tanggal H — nilai terkini
    ("Penyebab", 205, "w"),         # dipicu IN / IN ≠ Δ / tanpa kiriman
]

# Kolom numerik (sort/filter numeric-aware) vs teks.
_NUM_COLS = {"Tanggal Kejadian", "Durasi", "Rasio", "Deviasi"}

# v3.18 — pewarnaan sel Rasio (heat 3 bucket: ×2 merah muda → ×8 kuat)
RASIO_BG = {"ras_1": "#FFEBEE", "ras_2": "#FFCDD2", "ras_3": "#EF9A9A"}
RASIO_EDGES = (2.0, 4.0, 8.0)


class AnomaliRadarView(tk.Frame):
    """Tabel radar anomali shift deviasi (GR+PCS sekaligus)."""

    def __init__(self, parent, go_to_proses=None, go_to_deviasi=None,
                 h_state=None, saldo_sistem_state=None,
                 on_count_changed=None,
                 followup_store=None,
                 kategori_state: SharedKategori | None = None):
        super().__init__(parent, bg=C_BG)
        self.go_to_proses = go_to_proses
        self.go_to_deviasi = go_to_deviasi
        self.on_count_changed = on_count_changed
        self.h_state = h_state
        self.tanggal_h = int(h_state.h) if h_state is not None else 25
        self.saldo_sistem_mode = (saldo_sistem_state.mode
                                  if saldo_sistem_state is not None
                                  else "4217")
        self.saldo_sistem_state = saldo_sistem_state
        # v3.18.2 — store Follow Up (kolom ✓; listener reaktif — pola
        # deviasi_view: toggle dari tab mana pun menyinkronkan sel ✓).
        self.store = followup_store
        # v3.18.6 — seleksi KATEGORI DIBAGI dgn tab 📦 Deviasi GR & 🧩 PCS
        # (user: "di tab radar anomali juga bisa filter kategori ya misal
        # Deviasi atau packaging sama kaya di tab deviasi gr dan pcs dan
        # kateogri nya ngelink ke deviasi gr dan pcs misal di situ buka
        # apa maka di radar anomali juga bakal memfilter kateogri itu"):
        # ganti kategori di 📦/🧩 → radar ikut; ganti di radar → 📦/🧩 ikut
        # (pola SharedTanggalH).
        self._kategori_state = kategori_state
        self._kategori_sel: str | None = None

        self.data: pd.DataFrame | None = None
        self.in_detail: pd.DataFrame | None = None
        self.harga_map: dict = {}
        self.konversi_map: dict | None = None
        self.saldo_sistem_map: dict = {}

        self._rows: list[dict] = []        # baris tampil (raw+disp)
        self._rows_all: list[dict] = []    # pra-filter ⧩
        self._rows_by_iid: dict = {}
        self._fp_map: dict = {}            # v3.18.2 — iid → fp stabil
        self._busy = False
        self._dirty = False
        self._last_count = 0

        self._col_sel: dict = {c: None for c, _, _ in COLUMNS
                               if c != "✓"}
        self._sort_col = "Rasio"
        self._sort_rev = True

        self._build()
        if self.h_state is not None:
            self.h_state.subscribe(self._on_shared_h_changed)
        if self.store is not None:
            self.store.add_listener(self._on_store_changed)
        # v3.18.6 — listener kategori bersama (pola listener H).
        if self._kategori_state is not None:
            self._kategori_state.subscribe(
                self._on_shared_kategori_changed)

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        # Empty state (belum ada data / belum ada anomali ≠ error).
        self.empty = EmptyState(
            self, title="Belum ada anomali shift",
            subtitle="Belum ada data — jalankan pipeline, atau memang tidak "
            "ada pasangan dengan pergeseran level deviasi (normal).",
            cta_text="Buka Tab Proses",
            on_cta=(self.go_to_proses if self.go_to_proses else None))
        # Konten utama
        self.content = tk.Frame(self, bg=C_BG)

        head = tk.Frame(self.content, bg=C_BG)
        head.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(head, text="🚨 Radar Anomali — pergeseran level deviasi",
                 bg=C_BG, fg=C_HEADER, font=font(12, "bold")).pack(
            anchor="w")
        tk.Label(head, bg=C_BG, fg=C_TEXT_MUTED, font=font(9), wraplength=980,
                 justify="left", text=(
                     "Dari tanggal berapa deviasi naik STABIL dibanding "
                     "baseline pasangan — dan apakah dipicu kiriman IN? "
                     "Naik 1 hari lalu besoknya turun = spike, tidak "
                     "dianalisa (≥2 hari di level baru, Rasio ≥ "
                     f"×{RATIO_CUT:g}). Naik BERTAHAP sepanjang bulat "
                     "(ramp) juga bukan shift — hanya yang MELONJAK lalu "
                     "menempel di level baru. Hover baris = analisa "
                     "lengkap; double-click = bukti per tanggal.")).pack(
            anchor="w", pady=(2, 0))

        # v3.18.6 — filter KATEGORI (user: "di tab radar anomali juga bisa
        # filter kategori ya misal Deviasi atau packaging sama kaya di tab
        # deviasi gr dan pcs dan kateogri nya ngelink ke deviasi gr dan
        # pcs"): combobox + ter-link 2-ARAH dgn tab 📦/🧩 lewat
        # SharedKategori — nilai gabungan default / (Tanpa Kategori) /
        # nilai master, LINTAS satuan (radar = GR+PCS satu tabel).
        kf = tk.Frame(head, bg=C_BG)
        kf.pack(anchor="w", pady=(5, 0))
        tk.Label(kf, text="KATEGORI", bg=C_BG, fg=C_TEXT_MUTED,
                 font=font(8, "bold")).pack(side="left")
        self._kategori_var = tk.StringVar(value="Semua")
        self._kategori_combo = ttk.Combobox(
            kf, textvariable=self._kategori_var, state="readonly",
            width=34, font=font(9))
        self._kategori_combo.pack(side="left", padx=(6, 0))
        self._kategori_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self._on_kategori_changed())
        tk.Label(kf, text="— ter-link dgn tab 📦 Deviasi GR & 🧩 PCS "
                         "(ganti di salah satu → semua ikut)",
                 bg=C_BG, fg=C_TEXT_MUTED, font=font(8)).pack(
            side="left", padx=(10, 0))

        # toolbar ⤢ TERPISAH dari target expander (button tetap terlihat)
        toolbar = tk.Frame(self.content, bg=C_BG)
        toolbar.pack(fill="x", padx=12, pady=(2, 0))

        tbody = tk.Frame(self.content, bg=C_BG)
        tbody.pack(fill="both", expand=True, padx=12, pady=(4, 8))
        tbody.grid_rowconfigure(1, weight=1)
        tbody.grid_columnconfigure(0, weight=1)

        col_ids = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(tbody, columns=col_ids, show="headings",
                                 selectmode="extended")
        for col_name, width, anchor in COLUMNS:
            self.tree.column(col_name, width=width, minwidth=34,
                             anchor=anchor)
            self.tree.heading(col_name, text=col_name, anchor=anchor)
        vsb = ttk.Scrollbar(tbody, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(tbody, orient="horizontal",
                            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        enable_col_resize(self.tree)
        enable_multi_select(self.tree)
        install_tree_find_binding(self, lambda: self.tree)

        # tag pewarnaan
        self.tree.tag_configure("evenrow", background=ROW_EVEN)
        self.tree.tag_configure("oddrow", background=ROW_ODD)
        # v3.18.3 — warna baris = keadaan Penyebab (pertanyaan inti user:
        # "apa karna pengaruh IN atau gimana meningkat?"): dipicu IN hijau
        # · IN ≠ Δ amber (kiriman tak menjelaskan) · tanpa kiriman merah.
        self.tree.tag_configure("cocok_in", foreground="#059669")
        self.tree.tag_configure("in_sebagian", foreground="#b45309")
        self.tree.tag_configure("tanpa_kiriman", foreground="#dc2626")
        for _t, _bg in RASIO_BG.items():
            self.tree.tag_configure(_t, background=_bg)

        # Footer status
        foot = tk.Frame(tbody, bg=C_CARD)
        foot.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.status_var = tk.StringVar(value="Belum ada data.")
        tk.Label(foot, textvariable=self.status_var, bg=C_CARD,
                 fg=C_HEADER, font=font(8, "bold"), anchor="e").pack(
            side="right", fill="x", expand=True)

        self.overlay = None   # LoadingOverlay dibuat lazy (perlu window)

        # v3.18.2 — ⧩ filter header semua kolom KECUALI ✓ (toggle — pola
        # deviasi_view; kolom ikon-only tanpa affordance dikecualikan).
        _filter_cols = [c[0] for c in COLUMNS if c[0] != "✓"]
        self.header_filters = HeaderFilterGroup(
            self.tree, _filter_cols,
            get_values=self._col_values,
            on_apply=self._on_col_filter,
            on_sort=lambda c, d: self._sort_by(c, reverse=d))

        # Interaksi
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")
        self.tree.bind("<Double-1>", self._on_double_click, add="+")
        self.tree.bind("<Button-3>", self._on_context_menu, add="+")
        self.tree.bind("<Control-c>", self._on_copy, add="+")
        # v3.18.3 — tooltip hover: analisa lengkap per baris (bukti yang
        # dulunya kolom — baseline/level/Δ/z/IN±nomor/PO/BM/nominal —
        # pola CellTooltip kolom CEK tab 📦/🧩; pasif, no grab).
        self._tip = CellTooltip(self.tree,
                                provider=self._tooltip_provider)

        # Legend metode (transparansi deteksi)
        legend = LegendRow(self.content, [
            (("Shift Deviasi · |dev| ≥ ×2 baseline (median dua-jendela "
              "per pasangan) & ≥2 hari di level baru"), "#c026d3"),
            (("Naik BERTAHAP (ramp) ≠ shift — jendela level masih "
              "memanjat ≥35% × Δ → dilewati (v3.18.4)"), "#475569"),
            ("Deviasi = nilai tanggal H (terkini) — BUKAN akumulasi",
             "#475569"),
            (("Dipicu IN · Δ ≈ kiriman sistem ±1 hari — cut-off input? "
              "(hijau)"), "#059669"),
            (("IN ≠ Δ · ada kiriman tapi tak menjelaskan lompatan "
              "(amber)"), "#b45309"),
            ("Tanpa kiriman · naik tanpa sebab sistem (merah)",
             "#dc2626"),
            ("Rasio · heat merah muda → kuat (×2 / ×4 / ×8)", "#EF9A9A"),
            (("Hover baris = analisa lengkap (baseline, Δ, IN, nomor, "
              "PO, BM, est nominal)"), "#475569"),
            # v3.18.2 — kolom ✓ (pola legenda ✓ tab 📦/🧩 v3.12.3).
            (("✓ = tambah/keluarkan daftar pantauan (tab Follow Up; "
              "☑ = baris/pasangan sudah masuk daftar — uncek ada "
              "konfirmasi)"), "#475569"),
        ])
        legend.pack(fill="x", padx=12, pady=(6, 0))
        self._legend = legend   # v3.18.2 — chip ✓ dibaca test/legenda
        self._expander = TableExpander(toolbar, [head, legend])

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------
    def load_data(self, data: pd.DataFrame,
                  in_detail: pd.DataFrame | None = None,
                  harga_map: dict | None = None,
                  konversi_map: dict | None = None,
                  saldo_sistem_map: dict | None = None):
        """Data baru dari pipeline (pola fan-out _on_pipeline_done app)."""
        self.data = data
        self.in_detail = in_detail
        self.harga_map = harga_map or {}
        self.konversi_map = konversi_map
        self.saldo_sistem_map = saldo_sistem_map or {}
        if self.saldo_sistem_state is not None:
            self.saldo_sistem_mode = self.saldo_sistem_state.mode
        # v3.18.6 — populasi nilai combobox KATEGORI (LINTAS satuan —
        # radar GR+PCS satu tabel) + ikut seleksi shared saat ini (bukan
        # reset: default kategori dipegang tab 📦/🧩 via _reset_kategori
        # mereka yang men-broadcast lewat SharedKategori).
        self._repopulate_kategori_combo()
        self._rows_all = []
        self._rows = []
        self._col_sel = {c: None for c, _, _ in COLUMNS if c != "✓"}
        self.header_filters.clear_all()
        reset_autofit_once(self)
        _empty = data is None or getattr(data, "empty", True)
        if not _empty:
            self._show_content()
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True
        if _empty:
            self._show_empty()
            self.status_var.set(
                "Belum ada data — 0 baris terbaca dari pipeline "
                "(cek folder data / RootPath di tab Config).")
            self._notify_count(0)

    # v3.18.6 — nilai combobox KATEGORI radar: entry "Semua" +
    # gabungan default rekap (bila data memuat) + (Tanpa Kategori) +
    # nilai KATEGORI master terurut — LINTAS satuan (GR+PCS — mirror
    # _repopulate_kategori_combo deviasi_view tanpa scoping satuan).
    def _repopulate_kategori_combo(self):
        data = self.data
        if (data is not None and "KATEGORI"
                in getattr(data, "columns", [])):
            _kv = (data["KATEGORI"].dropna().astype(str)
                   .str.strip())
            kategori_vals = sorted(v for v in _kv.unique() if v)
        else:
            kategori_vals = []
        kv = ["Semua"]
        if kategori_has_default_values(
                data.get("KATEGORI") if data is not None else None):
            kv.append(KATEGORI_DEFAULT_LABEL)
        kv.append(KATEGORI_BLANK_LABEL)
        kv += kategori_vals
        try:
            self._kategori_combo["values"] = kv
        except tk.TclError:
            pass
        # ikut seleksi shared saat ini (valid ke daftar baru bila ada).
        if self._kategori_state is not None:
            cur = self._kategori_state.value
            if cur in kv:
                self._kategori_var.set(cur)
                self._kategori_sel = (None if cur == "Semua" else cur)

    def ensure_refreshed(self):
        """Lazy refresh (pola tab lain — dipanggil _on_tabChanged app)."""
        if self._dirty and self.winfo_ismapped():
            self._dirty = False
            self._refresh()

    def _on_shared_h_changed(self, new_h: int):
        """H berubah (tab 📦) → deteksi ulang (baseline/level ikut H)."""
        self.tanggal_h = int(new_h)
        if self.data is None or self.data.empty:
            return
        if self.winfo_ismapped():
            self._refresh()
        else:
            self._dirty = True

    def _refresh(self, sync: bool = False):
        if self._busy:
            return
        self._busy = True
        data, h = self.data, self.tanggal_h
        harga_map, konversi_map = self.harga_map, self.konversi_map

        def work():
            anoms = detect_shift_anomalies(data, h)
            # v3.18.2 — peta SO/SALDO/DEVIASI per (kb, kr, satn) utk
            # snapshot follow-up baris radar (nilai per tanggal — pola
            # snap deviasi_view; pure, thread-safe).
            so_map, sa_map, dv_map = _pair_series_maps(data, h)
            # v3.18.6 — peta kategori per pasangan (filter KATEGORI —
            # linked tab 📦/🧩; kategori = atribut barang, first
            # non-blank menang).
            kat_map = _pair_kategori_map(data)
            rows = []
            for rec in anoms.to_dict("records"):
                harga = None
                if harga_map:
                    harga = lookup_harga_pair(
                        harga_map, konversi_map,
                        str(rec.get("barang")), str(rec.get("satuan")))[0]
                rows.append(self._row_build(rec, harga, h,
                                             so_map, sa_map, dv_map,
                                             kat_map))
            return {"rows": rows}

        def done(payload):
            self._busy = False
            self._rows_all = payload["rows"]
            self._apply_filters(render=True)
            self._notify_count(len(self._rows_all))

        def on_error(err):
            self._busy = False
            self.status_var.set(f"⚠ Gagal menghitung radar: {err}")

        run_async(self, work, done, on_error=on_error, sync=sync)

    def _notify_count(self, n: int):
        self._last_count = n
        cb = self.on_count_changed
        if cb is not None:
            try:
                cb(n)
            except tk.TclError:
                pass

    # ------------------------------------------------------------------
    # ROW BUILD (pure — thread-safe)
    # ------------------------------------------------------------------
    @staticmethod
    def _fmt_num(val) -> str:
        if val is None:
            return ""
        try:
            if pd.isna(val):
                return ""
        except (TypeError, ValueError):
            pass
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val)
        if v == int(v):
            return fmt_int_id(v)
        s = f"{v:,.1f}".replace(",", "\u00a0").replace(
            ".", ",").replace("\u00a0", ".")
        return s

    @classmethod
    def _fmt_ratio(cls, ratio) -> str:
        try:
            ratio = float(ratio)
        except (TypeError, ValueError):
            return "-"
        if pd.isna(ratio):
            return "-"
        if ratio == float("inf"):
            return "×∞"
        return f"×{cls._fmt_num(ratio)}"

    @classmethod
    def _fmt_z(cls, z) -> str:
        try:
            z = float(z)
        except (TypeError, ValueError):
            return "-"
        if pd.isna(z):
            return "-"
        if z == float("inf"):
            return "∞"
        return cls._fmt_num(round(z, 1))

    def _row_build(self, rec: dict, harga, h,
                   so_map: dict | None = None,
                   sa_map: dict | None = None,
                   dv_map: dict | None = None,
                   kat_map: dict | None = None) -> dict:
        """Baris tampil: display strings + raw values (sort/filter) +
        record engine (popup) + snapshot follow-up (v3.18.2 — nilai
        so/sistem/deviasi per tanggal H dari frame, pola snap
        deviasi_view; kosong bila tanggal tak terekam) + v3.18.3
        cause_tag & tooltip (analisa lengkap — bukti yang dulunya
        kolom) + v3.18.6 kategori pasangan (filter linked 📦/🧩)."""
        in_qty = rec.get("in_qty")
        has_in = in_qty is not None and not (
            isinstance(in_qty, float) and pd.isna(in_qty))
        delta = rec.get("delta")
        # v3.18.3 — Penyebab 3 keadaan (pertanyaan inti user: "apa karna
        # pengaruh IN atau gimana meningkat?"): dipicu IN (cocok, hijau)
        # · IN ≠ Δ (kiriman ada tapi tak menjelaskan, amber) · tanpa
        # kiriman (naik tanpa sebab sistem, merah).
        if has_in:
            qty_txt = self._fmt_num(in_qty)
            if rec.get("in_match"):
                penyebab = f"Dipicu IN {qty_txt} tgl {self._fmt_num(rec.get('in_tgl'))}"
                cause_tag = "cocok_in"
            else:
                penyebab = (f"IN {qty_txt} tgl "
                            f"{self._fmt_num(rec.get('in_tgl'))} ≠ Δ "
                            f"{self._fmt_num(delta)}")
                cause_tag = "in_sebagian"
        else:
            penyebab = "Tanpa kiriman IN"
            cause_tag = "tanpa_kiriman"
        dev_h = rec.get("dev_h")
        has_dev = dev_h is not None and not (
            isinstance(dev_h, float) and pd.isna(dev_h))
        # v3.18.3 — satuan DILIPAT ke Nama Barang ("CUP 14 (V.20) · PCS"
        # — user minta kolom inti; pasangan GR/PCS tetap 2 baris).
        barang = str(rec.get("barang") or "")
        satuan = str(rec.get("satuan") or "")
        nama = f"{barang} · {satuan}" if satuan and satuan != "-" else barang
        disp = {
            "Resto": str(rec.get("resto") or ""),
            "Nama Barang": nama,
            "Tanggal Kejadian": self._fmt_num(rec.get("tgl_shift")),
            "Durasi": f"{int(rec.get('durasi') or 0)} hari",
            "Rasio": self._fmt_ratio(rec.get("ratio")),
            # |dev| TANGGAL H — nilai terkini, BUKAN akumulasi (user).
            "Deviasi": self._fmt_num(dev_h) if has_dev else "-",
            "Penyebab": penyebab,
        }
        raw = {
            "Resto": disp["Resto"], "Nama Barang": nama,
            "Tanggal Kejadian": float(rec.get("tgl_shift") or 0),
            "Durasi": float(rec.get("durasi") or 0),
            "Rasio": (float("inf") if (r := rec.get("ratio")) is None
                      else float(r)),
            "Deviasi": (float(dev_h) if has_dev else float("nan")),
            "Penyebab": (1 if has_in and rec.get("in_match")
                         else (0 if has_in else -1)),
        }
        # v3.18.2 — snapshot follow-up baris radar (fp STABIL: cek "" —
        # pola _fp_stable deviasi_view; nilai so/sistem/deviasi + so_m2..
        # p2 dari peta per tanggal, kosong bila tak terekam).
        key = (rec.get("kb"), rec.get("kr"), rec.get("satn"))
        so_map = so_map or {}
        sa_map = sa_map or {}
        dv_map = dv_map or {}
        kat_map = kat_map or {}
        _val = lambda m, t: m.get(key, {}).get(t, "")
        # v3.18.6 — kategori pasangan (atribut barang — first non-blank
        # dari frame; kosong = '(Tanpa Kategori)' jalur filter).
        kategori = kat_map.get(key, "")
        snap = {
            "asal": "RADAR",
            "resto": str(rec.get("resto") or ""),
            "barang": str(rec.get("barang") or ""),
            "satuan": str(rec.get("satuan") or ""),
            "aktif": "",
            "h": h,
            "so": _val(so_map, h),
            "sistem": _val(sa_map, h),
            "deviasi": _val(dv_map, h),
            "cek": "",
            "so_m2": _val(so_map, h - 2),
            "so_m1": _val(so_map, h - 1),
            "so_p1": _val(so_map, h + 1),
            "so_p2": _val(so_map, h + 2),
            "loss_bom": "",
            "barang_app": str(rec.get("barang") or ""),
            "resto_app": str(rec.get("resto") or ""),
        }
        return {"disp": disp, "raw": raw, "rec": rec, "snap": snap,
                "fp": row_fingerprint(snap),
                # v3.18.3 — keadaan penyebab (warna baris) + tooltip
                # analisa lengkap (dihitung pure di worker thread).
                "cause_tag": cause_tag,
                "kategori": kategori,   # v3.18.6 — filter linked 📦/🧩
                "tip": _tooltip_text(rec, harga, kategori=kategori)}

    # ------------------------------------------------------------------
    # FILTER + SORT + RENDER
    # ------------------------------------------------------------------
    def _col_values(self, col: str) -> list:
        vals = []
        for row in self._rows_all:
            v = row["disp"].get(col, "")
            if v not in vals:
                vals.append(v)
        return vals

    def _on_col_filter(self, col: str, sel):
        self._col_sel[col] = sel
        self._apply_filters(render=True)

    # v3.18.6 — combobox KATEGORI radar (linked 2-arah tab 📦/🧩 —
    # pola _on_kategori_changed deviasi_view): push ke SharedKategori
    # → tab satuan-saudara ikut memfilter kategori yang sama.
    def _on_kategori_changed(self):
        val = self._kategori_var.get()
        self._kategori_sel = None if (not val or val == "Semua") else val
        if self._kategori_state is not None:
            self._kategori_state.set(val)
        self._apply_filters(render=True)

    # v3.18.6 — listener SharedKategori (kategori diganti di tab 📦/🧩 —
    # user: "misal di situ buka apa maka di radar anomali juga bakal
    # memfilter kateogri itu"): sinkron combobox + filter ulang baris
    # (murah — _rows_all sudah terbangun, tanpa recompute engine).
    def _on_shared_kategori_changed(self, new_val: str):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if self._kategori_var.get() == new_val:
            return   # sudah sinkron (pemanggil asal)
        self._kategori_var.set(new_val)
        self._kategori_sel = None if (not new_val or new_val == "Semua") \
            else new_val
        self._apply_filters(render=True)

    def _apply_filters(self, render: bool = False):
        rows = self._rows_all
        # v3.18.6 — filter KATEGORI (linked tab 📦/🧩): mask kanonik
        # kategori_match_mask (entry gabungan / (Tanpa Kategori) /
        # passthrough legacy / exact — semantik PERSIS tab 📦/🧩).
        if self._kategori_sel:
            _kats = pd.Series([r.get("kategori", "") for r in rows])
            _m = kategori_match_mask(_kats, self._kategori_sel)
            if _m is not None:
                rows = [r for r, keep in zip(rows, _m.tolist())
                        if bool(keep)]
        for col, sel in self._col_sel.items():
            if not sel:
                continue
            rows = [r for r in rows
                    if r["disp"].get(col) in sel
                    or str(r["raw"].get(col)) in sel]
        self._rows = rows
        if render:
            self._render_rows()

    def _sort_by(self, col: str, reverse: bool = True):
        self._sort_col = col
        self._sort_rev = reverse
        self._render_rows()

    def _render_rows(self):
        self._busy = True
        try:
            self.tree.delete(*self.tree.get_children(""))
            col_ids = [c[0] for c in COLUMNS]
            rows = list(self._rows)
            key_col = self._sort_col if self._sort_col in col_ids \
                else "Rasio"
            rev = self._sort_rev

            def _key(row):
                v = row["raw"].get(key_col, "")
                if key_col in _NUM_COLS:
                    try:
                        return (0, float(v))
                    except (TypeError, ValueError):
                        return (1, 0.0)
                return (1, str(v))

            try:
                rows.sort(key=_key, reverse=rev)
            except TypeError:
                rows.sort(key=lambda r: str(r["raw"].get(key_col, "")),
                          reverse=rev)

            # heat sel Rasio (Tk 9 per-cell; Tk 8.6: pola melewatkan)
            # — kumpulkan per-TAG lalu satu panggilan (pola deviasi_view).
            rasio_cells: dict = {"ras_1": [], "ras_2": [], "ras_3": []}
            fp_map: dict = {}
            pair_idx = self._pair_key_index()   # v3.18.2 — ☑ level pasangan
            for i, row in enumerate(rows):
                snap = row.get("snap")
                fp = row.get("fp")
                fp_map[f"row_{i}"] = fp
                checked = (self.store is not None and fp is not None and
                           (self.store.has(fp)
                            or bool(self._pair_matched_keys(snap, pair_idx))))
                disp = [CHECK_ON if checked else CHECK_OFF] + [
                    row["disp"][c] for c, _, _ in COLUMNS if c != "✓"]
                tags = ["evenrow" if i % 2 == 0 else "oddrow"]
                # v3.18.3 — warna baris = keadaan Penyebab (cause_tag
                # dihitung _row_build — pure, thread-safe).
                cause = row.get("cause_tag")
                if cause:
                    tags.append(cause)
                iid = f"row_{i}"
                self.tree.insert("", "end", iid=iid,
                                  values=disp, tags=tuple(tags))
                ratio = row["raw"].get("Rasio")
                if not pd.isna(ratio):
                    tag = ("ras_3" if ratio >= RASIO_EDGES[2]
                           else "ras_2" if ratio >= RASIO_EDGES[1]
                           else "ras_1" if ratio >= RASIO_EDGES[0]
                           else None)
                    if tag:
                        rasio_cells[tag].append((iid, "Rasio"))
            if CELL_TAGS_SUPPORTED:
                for _tag, _cells in rasio_cells.items():
                    apply_cell_tag(self.tree, _tag, _cells)
            self._rows_by_iid = {f"row_{i}": r for i, r in enumerate(rows)}
            self._fp_map = fp_map   # v3.18.2 — sel ✓ toggle/refresh
            self._update_status()
        finally:
            self._busy = False

    def _update_status(self):
        n = len(self._rows)
        n_all = len(self._rows_all)
        if not n_all:
            self.status_var.set(
                "Tidak ada anomali shift aktif — normal / baseline data "
                "belum cukup / awal bulan (lihat metode di legend).")
            return
        best = max(self._rows_all,
                   key=lambda r: (r["raw"].get("Rasio") or 0.0,
                                  float(r["rec"].get("delta") or 0.0)))
        ratio = best["raw"].get("Rasio") or 0.0
        ratio_txt = ("×∞" if ratio == float("inf")
                     else f"×{ratio:,.1f}".replace(",", "."))
        who = (f" ({best['disp']['Nama Barang']} — "
               f"{best['disp']['Resto']})") if n_all else ""
        extra = f" dari {n_all}" if n != n_all else ""
        self.status_var.set(
            f"{n}{extra} pasangan shift aktif · terbesar {ratio_txt}{who}"
            f" · H={self.tanggal_h} · GR+PCS")

    def _show_empty(self):
        self.empty.pack(fill="both", expand=True)
        self.content.pack_forget()

    def _show_content(self):
        self.empty.pack_forget()
        self.content.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # ✓ FOLLOW-UP (v3.18.2 — pola deviasi_view: klik sel ✓ = daftar/
    # keluar; ☑ level PASANGAN; uncek dikonfirmasi; listener store)
    # ------------------------------------------------------------------
    @staticmethod
    def _pair_key_parts(snap: dict) -> tuple[str, str, str]:
        """(resto, barang, satuan) ternormalisasi — kunci pasangan
        (mirror DeviasiView._pair_key_parts v3.12.3; satuan upper+strip)."""
        return (
            norm_nama_resto_key(snap.get("resto", "") or ""),
            norm_nama_barang_key(snap.get("barang", "") or ""),
            str(snap.get("satuan", "") or "").strip().upper(),
        )

    def _pair_key_index(self) -> dict:
        """{(resto, barang, satuan) → [kunci store]} SELURUH entri follow-up
        (asal apapun — RADAR/GR/PCS/IMPOR; pola deviasi_view._pair_key_index
        v3.12.3 — thread-safe snapshot iterasi)."""
        store = self.store
        if store is None or not store.rows:
            return {}
        try:
            items = list(store.rows.items())
        except RuntimeError:
            return {}
        idx: dict = {}
        for k, s in items:
            idx.setdefault(self._pair_key_parts(s), []).append(k)
        return idx

    def _pair_matched_keys(self, snap: dict | None, pair_idx: dict) -> list:
        """Kunci store ber-pasangan-sama dgn snap (satuan SAMA + satuan
        KOSONG impor; GR↔PCS terisolasi — mirror v3.12.3)."""
        if not snap or not pair_idx:
            return []
        r, b, s = self._pair_key_parts(snap)
        out: list = []
        for key in ((r, b, s), (r, b, "")):
            for k in pair_idx.get(key) or ():
                if k not in out:
                    out.append(k)
        return out

    def _confirm_unfollow(self, snap: dict, n_ent: int) -> bool:
        """Konfirmasi sebelum mengeluarkan (pola deviasi_view v3.12.3):
        return True = lanjut hapus; False = batal. Opt-out programmatic:
        ``view.confirm_unfollow = False``."""
        if not self.confirm_unfollow:
            return True
        extra = (f"\n({n_ent} entri lama pasangan ini ikut terhapus)"
                 if n_ent > 1 else "")
        try:
            return messagebox.askyesno(
                "Keluarkan dari daftar Follow Up?",
                "Keluarkan baris ini dari daftar ☑ Follow Up?\n\n"
                f"Resto : {snap.get('resto', '')}\n"
                f"Barang : {snap.get('barang', '')}{extra}\n\n"
                "Klik Tidak bila centang ini lepas tanpa sengaja — "
                "baris tetap dipantau.\n"
                "Daftar yang terhapus masih bisa dipulihkan lewat "
                "📥 Impor Excel di tab ☑ Follow Up (bila ada file "
                "export).",
                parent=self.winfo_toplevel())
        except tk.TclError:
            return True

    confirm_unfollow: bool = True

    def _on_tree_click(self, event):
        """Klik sel ✓ = toggle follow-up (pola deviasi_view._on_tree_click:
        identifikasi kolom by NAME — bukan posisi display)."""
        tree = event.widget
        try:
            if tree.identify_region(event.x, event.y) != "cell":
                return
            if identify_to_column(tree, tree.identify_column(event.x)) != "✓":
                return
            row_iid = tree.identify_row(event.y)
        except tk.TclError:
            return
        if not row_iid or self.store is None:
            return
        fp = self._fp_map.get(row_iid)
        snap = (self._rows_by_iid.get(row_iid) or {}).get("snap")
        if not fp or snap is None:
            return
        keys = self._pair_matched_keys(snap, self._pair_key_index())
        if keys:
            if not self._confirm_unfollow(snap, len(keys)):
                try:
                    self.status_var.set(
                        "Batal — baris tetap di daftar ☑ Follow Up "
                        f"(total {len(self.store)} baris)")
                except tk.TclError:
                    pass
                return
            for k in keys:
                self.store.toggle(k, snap)
            checked_now = bool(self._pair_matched_keys(
                snap, self._pair_key_index()))
        else:
            checked_now = self.store.toggle(fp, snap)
        try:
            tree.set(row_iid, "✓", CHECK_ON if checked_now else CHECK_OFF)
        except tk.TclError:
            pass
        n = len(self.store)
        self.status_var.set(
            f"{'Masuk' if checked_now else 'Keluar'} daftar Follow Up — "
            f"total {n} baris" if n else "Dikeluarkan — daftar kosong")

    def _on_store_changed(self, _store=None):
        """Listener FollowUpStore (toggle dari tab mana pun) → jadwalkan
        pembaruan sel ✓ radar di main thread (pola deviasi_view — tanpa
        re-render penuh; view mati → telan TclError)."""
        try:
            if not self.winfo_exists():
                return
            self.after(0, self._refresh_check_cells)
        except tk.TclError:
            pass

    def _refresh_check_cells(self):
        """Perbarui sel ✓ dari state store (☑ level pasangan — v3.12.3
        mirror: entri lama/IMPOR ber-pasangan-sama ikut menandai)."""
        if self.store is None or not getattr(self, "_fp_map", None):
            return
        try:
            children = self.tree.get_children("")
        except tk.TclError:
            return
        pair_idx = self._pair_key_index()
        for iid in children:
            fp = self._fp_map.get(iid)
            snap = (self._rows_by_iid.get(iid) or {}).get("snap")
            if fp is None or snap is None:
                continue
            checked = (self.store.has(fp)
                       or bool(self._pair_matched_keys(snap, pair_idx)))
            try:
                self.tree.set(iid, "✓",
                              CHECK_ON if checked else CHECK_OFF)
            except tk.TclError:
                pass

    # ------------------------------------------------------------------
    # INTERAKSI
    # ------------------------------------------------------------------
    def _row_rec(self, iid: str) -> dict | None:
        return (self._rows_by_iid.get(str(iid), {}) or {}).get("rec")

    def _tooltip_provider(self, iid: str, _col: str):
        """v3.18.3 — teks tooltip baris (sama utk semua kolom — analisa
        lengkap muncul di hover bagian baris mana pun; CellTooltip pola
        kolom CEK tab 📦/🧩)."""
        row = self._rows_by_iid.get(str(iid))
        if not row:
            return None
        tip = row.get("tip")
        return tip if tip else None

    def _on_double_click(self, event):
        if self.data is None or self.data.empty:
            return
        row_iid = event.widget.identify_row(event.y)
        if not row_iid:
            return
        rec = self._row_rec(row_iid)
        if rec is None:
            return
        from .deviasi_popup import show_deviasi_popup
        # v3.18.5 — mark_tgl = TANGGAL KEJADIAN (tgl_shift): popup Detail
        # Deviasi menandai tanggal itu dgn ⚑ + latar amber kuat (user:
        # "waktu pop up muncul di tab radar anomali kasih tanda dong di
        # bagian tanggal nya yang terpicu nya mungkin warna gitu biar aku
        # langsung lihat oh dari tanggal ini kelihata anomali nya").
        _tgl_shift = rec.get("tgl_shift")
        show_deviasi_popup(
            self.winfo_toplevel(), self.data,
            nama_barang=str(rec.get("barang")),
            nama_resto=str(rec.get("resto")),
            satuan=(str(rec.get("satuan"))
                    if str(rec.get("satuan") or "-") != "-" else None),
            h=self.tanggal_h,
            in_detail=self.in_detail,
            saldo_sistem_map=self.saldo_sistem_map,
            saldo_sistem_mode=self.saldo_sistem_mode,
            mark_tgl=(int(_tgl_shift)
                      if _tgl_shift is not None else None),
        )

    def _on_copy(self, _event=None):
        copy_tree_selection_tsv(self.tree)

    def _on_context_menu(self, event):
        row_iid = event.widget.identify_row(event.y)
        if not row_iid:
            return
        if row_iid not in self.tree.selection():
            self.tree.selection_set(row_iid)
        rec = self._row_rec(row_iid)
        menu = tk.Menu(self, tearoff=0)
        try:
            col = identify_to_column(self.tree,
                                     self.tree.identify_column(event.x))
            val = self.tree.set(row_iid, col) if col else ""
            if val:
                menu.add_command(label=f"Salin sel ('{val}')",
                                 command=lambda v=str(val): self._copy_text(v))
        except tk.TclError:
            pass
        menu.add_command(label="Salin baris (TSV)",
                        command=self._on_copy)
        if self.go_to_deviasi is not None and rec is not None:
            menu.add_separator()
            menu.add_command(
                label="Buka di Deviasi GR",
                command=lambda: self.go_to_deviasi(
                    str(rec.get("resto")), str(rec.get("barang"))))
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    def _copy_text(self, txt: str):
        """Salin teks sel ke clipboard (via tree — widget hidup)."""
        try:
            self.tree.clipboard_clear()
            self.tree.clipboard_append(txt)
        except tk.TclError:
            pass


def _tooltip_text(rec: dict, harga=None, kategori: str = "") -> str:
    """v3.18.3 — Narasi lengkap utk tooltip hover baris radar: seluruh
    bukti yang DULU-nya kolom tabel (baseline, level, Δ, z, IN + nomor
    IT/RI & PO, BM, est nominal) dilipat ke satu teks — tabel kolom
    inti, analisa tetap lengkap (user: "bisa gak jadi lebih sederhana
    aja tampilan nya" + "perkuat analisa sesuai kebutuhan ku"). Pure —
    dihitung di worker thread _row_build.
    v3.18.6 — baris kategori pasangan (transparansi filter linked 📦/🧩)."""
    F = AnomaliRadarView._fmt_num
    lines = [
        (f"{rec.get('resto') or ''} · {rec.get('barang') or ''}"
         f" · {rec.get('satuan') or '-'}"),
    ]
    if kategori:
        lines.append(f"Kategori: {kategori}")
    lines += [
        (f"Deviasi naik stabil sejak tgl {F(rec.get('tgl_shift'))} — "
         f"{int(rec.get('durasi') or 0)} hari di level baru (naik 1 hari "
         "lalu turun = spike, bukan anomali)"),
        (f"Baseline {F(rec.get('baseline'))} "
         f"({int(rec.get('n_baseline') or 0)} hari) → level baru "
         f"{F(rec.get('level'))} (median pasca-shift)"),
    ]
    dev_h = rec.get("dev_h")
    if dev_h is not None and not (isinstance(dev_h, float)
                                  and pd.isna(dev_h)):
        lines.append(f"Deviasi H (tgl {F(rec.get('dev_h_tgl'))}): "
                     f"{F(dev_h)} — nilai terkini, BUKAN akumulasi")
    delta = float(rec.get("delta") or 0.0)
    lines.append(f"Rasio {AnomaliRadarView._fmt_ratio(rec.get('ratio'))}"
                 f" · Δ +{F(delta)} · z {AnomaliRadarView._fmt_z(rec.get('z'))}")
    in_qty = rec.get("in_qty")
    has_in = in_qty is not None and not (
        isinstance(in_qty, float) and pd.isna(in_qty))
    if has_in:
        try:
            pct = (f" ({round(100.0 * float(in_qty) / delta)}% dari Δ)"
                   if delta else "")
        except (ZeroDivisionError, ValueError):
            pct = ""
        verdict = ("≈ Δ — cocok kiriman, pola cut-off input?"
                   if rec.get("in_match")
                   else "≠ Δ — kiriman tak menjelaskan seluruh lompatan")
        lines.append(f"IN sistem {F(in_qty)} tgl "
                     f"{F(rec.get('in_tgl'))}{pct} · {verdict}")
        if rec.get("in_nomor"):
            lines.append(f"Nomor IT/RI: {rec.get('in_nomor')}")
        if rec.get("in_nomor_po"):
            lines.append(f"Nomor PO: {rec.get('in_nomor_po')}")
    else:
        lines.append("Tanpa kiriman IN ±1 hari sekitar tgl shift — naik "
                     "tanpa sebab sistem")
    bm_qty = rec.get("bm_qty")
    if bm_qty is not None and not (isinstance(bm_qty, float)
                                   and pd.isna(bm_qty)):
        lines.append(f"BM rekap tgl {F(rec.get('bm_tgl'))}: "
                     f"{F(bm_qty)} (pembanding fisik resto)")
    if harga is not None:
        try:
            nominal = float(harga) * delta
            lines.append(f"Est. nominal: Δ {F(delta)} × harga "
                         f"{F(harga)} = {fmt_rp_cell(nominal)}")
        except (TypeError, ValueError):
            pass
    lines.append("Double-click = bukti per tanggal · ✓ = daftarkan ke "
                 "Follow Up")
    return "\n".join(lines)


def _pair_series_maps(df, h) -> tuple[dict, dict, dict]:
    """v3.18.2 — Peta {(kb, kr, satn): {tgl: nilai}} utk 1.SO /
    2.SALDO AKHIR / 3.DEVIASI (tgl ≥ 1 semua tanggal terekam — lookup
    so/sistem/deviasi + so_m2..so_p2 snapshot follow-up baris radar).
    Pure pandas — thread-safe (dipanggil worker _refresh)."""
    empty = ({}, {}, {})
    if df is None or getattr(df, "empty", True):
        return empty
    cols = set(df.columns)
    if not {"Nama Barang", "NAMA RESTO", "JENIS", "NILAI"} <= cols:
        return empty
    tnum = pd.to_numeric(df["Tanggal"], errors="coerce")
    nilai = pd.to_numeric(df["NILAI"], errors="coerce").fillna(0)
    jenis = df["JENIS"].astype(str)
    _sat = (df["SATUAN"].fillna("").astype(str).str.strip().str.upper()
            if "SATUAN" in cols
            else pd.Series([""] * len(df), index=df.index))
    kb_s = df["Nama Barang"].astype(str).map(norm_nama_barang_key)
    kr_s = df["NAMA RESTO"].astype(str).map(norm_nama_resto_key)
    out: tuple = ({}, {}, {})
    for j, target in (("1.SO", out[0]), ("2.SALDO AKHIR", out[1]),
                      ("3.DEVIASI", out[2])):
        m = (tnum.notna() & (tnum >= 1) & (jenis == j))
        if not bool(m.any()):
            continue
        for k, t, v in zip(zip(kb_s[m].tolist(), kr_s[m].tolist(),
                               _sat[m].tolist()),
                           tnum[m].astype("Int64").tolist(),
                           nilai[m].tolist()):
            target.setdefault(k, {})[int(t)] = float(v)
    return out


def _pair_kategori_map(df) -> dict:
    """v3.18.6 — Peta {(kb, kr, satn): KATEGORI} dari frame utk filter
    kategori radar (linked tab 📦/🧩). Kategori = atribut barang
    (merge master '21. DBS Kategori' + rekap mentah di append1) —
    first NON-BLANK per pasangan menang (baris blank/'-'/'nan' tak
    menimpa nilai terisi). Pure pandas — worker-thread-safe."""
    out: dict = {}
    if df is None or getattr(df, "empty", True):
        return out
    cols = set(df.columns)
    if "KATEGORI" not in cols or "Nama Barang" not in cols \
            or "NAMA RESTO" not in cols:
        return out
    _sat = (df["SATUAN"].fillna("").astype(str).str.strip().str.upper()
            if "SATUAN" in cols
            else pd.Series([""] * len(df), index=df.index))
    kb_s = df["Nama Barang"].astype(str).map(norm_nama_barang_key)
    kr_s = df["NAMA RESTO"].astype(str).map(norm_nama_resto_key)
    _blank = {"", "nan", "none", "-", "—"}
    for k, kat in zip(zip(kb_s.tolist(), kr_s.tolist(),
                          _sat.tolist()),
                      df["KATEGORI"].astype(str).str.strip().tolist()):
        if k not in out and kat.lower() not in _blank:
            out[k] = kat
    return out
