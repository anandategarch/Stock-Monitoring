"""
deviasi_popup.py — Popup RINGKAS tab Deviasi GR/PCS (v3.9.18).

v3.9.20 (deep audit 34-b/fix 35-b): popup memfilter SATUAN (angka =
baris GR/PCS yang DIKLIK — dulu menjumlah lintas satuan) + _chrono_key
float-safe (urutan 25•..31• benar utk Tanggal float64).

Permintaan user: "pop up di deviasi GR ataupun PCS hanya tampilkan:
nama barang, nama resto, nilai saldo akhir, nilai SO, nilai IN,
nilai deviasi."

v3.9.22 (permintaan user: "Pop up di tab Deviasi GR dan PCS ada Nomor
nya juga Misal IT...... atau RI......"): kolom NOMOR DOKUMEN IN per
tanggal (IT. = pemindahan 42.05, RI. = penerimaan 32.24; >1 dokumen
digabung koma, didedup + diurut).

v3.9.25 (permintaan user: "POP UP DI tab deviasi gr dan deviasi pcs
perbesar lagi dan tambah kolom nomor po dan COM"): jendela diperbesar
880×480 → 1180×640 (judul wraplength ikut melebar) + DUA kolom baru:
- "Nomor PO" — nomor pesanan pembelian (PO......) baris 4.IN per
  tanggal, didedup + diurut (pola kolom Nomor v3.9.22);
- "COM" — pemakaian harian per tanggal, FORMULA IDENTIK baris
  6.PEMAKAIAN (COM) tab Pivot / 🚨 Anomali COM (port
  laporan_deviasi_view._compute_com_matrix → _compute_com_series;
  kolom tanggal GLOBAL union 4 JENIS — parity 48/48 nilai):
      com(t) = so_prev(t) + IN(t) − BK(t) − SO(t)
  so_prev(t) = SO pasangan di tanggal kolom global sebelumnya
  (SALDO AWAL/1.SO/4.IN/8.BARANG KELUAR — kolom pertama 0), tanggal 1
  memakai SALDO AWAL pasangan bila ada (audit fix v3.9.5), fallback
  so_prev. Tanggal yang TIDAK ada di kolom global (mis. hanya baris
  2.SALDO AKHIR) → COM kosong (tab lain juga tak punya nilainya).
  Dihitung DALAM grup satuan yang diklik (pola FIX 35-b).

Mengganti popup source rows (details_popup.DetailsPopup — JENIS/Nomor/
Nomor PO/#Tgl-Jam/KATEGORI/SOURCE KIRIMAN) yang DULU terbuka dari tab
Deviasi GR/PCS:

- NAMA BARANG + NAMA RESTO tampil di judul popup (dua-duanya).
- Tabel ringkas PER TANGGAL — 8 kolom (v3.9.25):
    Tanggal · Saldo Akhir (2.SALDO AKHIR / sistem) · SO (1.SO) ·
    IN (4.IN) · Nomor (dokumen IN — v3.9.22) · Nomor PO (pesanan
    pembelian — v3.9.25) · COM (pemakaian harian — v3.9.25) ·
    Deviasi (= SO − Saldo Akhir, identik kolom Deviasi tab Deviasi
    GR/PCS & JENIS 3.DEVIASI pipeline).
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
    enable_multi_select,
    fmt_int_id,
)

# (column_id, width, anchor) — persis daftar user: saldo akhir, SO, IN,
# deviasi (+ kolom Tanggal sbg sumbu baris; barang & resto di judul).
# v3.9.22 — kolom Nomor (permintaan user: "Pop up di tab Deviasi GR dan
# PCS ada Nomor nya juga Misal IT...... atau RI......"): nomor dokumen
# transaksi IN (IT. = pemindahan 42.05 / RI. = penerimaan 32.24) per
# tanggal — gabungan bila >1 dokumen.
# v3.9.25 — kolom Nomor PO (permintaan user: "tambah kolom nomor po dan
# COM"): nomor pesanan pembelian baris 4.IN per tanggal (pola Nomor) +
# kolom COM (pemakaian harian — formula identik Anomali COM).
COLUMNS = [
    ("Tanggal", 76, "e"),
    ("Saldo Akhir", 110, "e"),
    ("SO", 110, "e"),
    ("IN", 110, "e"),
    ("Nomor", 200, "w"),
    ("Nomor PO", 190, "w"),
    ("COM", 100, "e"),
    ("Deviasi", 110, "e"),
]

COL_IDS = [c[0] for c in COLUMNS]

_H_ROW_BG = "#fef3c7"   # sama dgn HIGHLIGHT_BG deviasi_view (v3.9.18)

_JENIS_SALDO = "2.SALDO AKHIR"
_JENIS_SO = "1.SO"
_JENIS_IN = "4.IN"

# v3.9.25 — JENIS input formula COM (persis jenis_needed
# laporan_deviasi_view._compute_com_matrix / pivot 6.PEMAKAIAN).
_JENIS_SA = "SALDO AWAL"
_JENIS_BK = "8.BARANG KELUAR"
_COM_JENIS = (_JENIS_SA, _JENIS_SO, _JENIS_IN, _JENIS_BK)


class DeviasiPopup(tk.Toplevel):
    """Popup ringkas: nilai kunci per Tanggal utk 1 pasangan (barang, resto)."""

    def __init__(self, parent, title: str, rows: pd.DataFrame,
                 h_label: str = ""):
        super().__init__(parent)
        self._title = title
        self.title(f"Detail Deviasi — {title}")
        try:
            # v3.9.25: 880×480 → 1180×640 (permintaan user "perbesar
            # lagi" + 2 kolom baru Nomor PO & COM).
            # v3.9.33 — AUDIT FIX (48-c MEDIUM): ukuran ADAPTIF + clamp
            # posisi KEDUA SISI (mirror DetailsPopup v3.9.32) — dulu
            # fixed 1180×640 hanya clamp batas 0 → di layar kecil popup
            # melebihi layar / posisi off-screen kanan-bawah.
            sw = max(int(self.winfo_screenwidth()), 1024)
            sh = max(int(self.winfo_screenheight()), 640)
            pw = min(1180, int(sw * 0.90))
            ph = min(640, int(sh * 0.86))
            px = parent.winfo_rootx() + (parent.winfo_width() - pw) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - ph) // 2
            px = max(0, min(px, sw - pw))
            py = max(0, min(py, sh - ph))
            self.geometry(f"{pw}x{ph}+{px}+{py}")
        except Exception:
            self.geometry("1180x640")
        self.minsize(820, 340)
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
                 font=font(12, "bold"), wraplength=1020,
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
                                 selectmode="extended")
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
        enable_multi_select(self.tree)  # v3.9.32

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
            # v3.9.22 — kolom Nomor ikut (posisi mengikuti COLUMNS)
            values = [rec.get(c, "") for c in COL_IDS]
            tags = []
            if self._h_label and rec["Tanggal"] == self._h_label:
                tags.append("h_row")       # baris Tanggal H — latar lembut
            else:
                tags.append("evenrow" if i % 2 == 0 else "oddrow")
            has_neg = False
            # v3.9.25 — COM ikut minus merah per-cell (kolom numerik)
            for col in ("Saldo Akhir", "SO", "IN", "COM", "Deviasi"):
                if _is_neg_display(rec.get(col, "")):
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
    kronologis: 25•, 26•, … 31•, 1, 2, … 31 (konvensi pivot_view).

    FIX 35-b (audit 34-b RISK-3): parse via float — Tanggal float64
    (mis. ada NaN → pd.to_numeric menghasilkan float) membuat str(t)
    = '-25.0' yang GAGAL di int() → guard 999999 → bulan lalu TERBALIK
    senyap (31• dulu). int(float(...)) menerima '-25.0'/'-25' sama
    saja; guard 999999 tetap sbg fallback terakhir (NA/label non-angka).
    """
    try:
        d = int(float(str(t).rstrip("•")))
    except (TypeError, ValueError):
        return 999999
    return abs(d) if d < 0 else 100 + d


def _compute_com_series(df: pd.DataFrame, nama_barang: str,
                        nama_resto: str, satuan: str | None = None) -> dict:
    """v3.9.25 — COM (pemakaian) per tanggal utk 1 pasangan (barang, resto).

    PORT PERSIS laporan_deviasi_view._compute_com_matrix (tab 🚨 Anomali
    COM / baris 6.PEMAKAIAN (COM) — formula v3.9.5):
        com(t) = so_prev(t) + IN(t) − BK(t) − SO(t)

    SEMANTIK KOLOM GLOBAL (diverifikasi parity vs matrix laporan):
    so_prev(t) = SO pasangan di tanggal kolom GLOBAL SEBELUM t — kolom
    global = union tanggal baris 4 JENIS (SALDO AWAL · 1.SO · 4.IN ·
    8.BARANG KELUAR) dari SEMUA pasangan di frame (persis col_keys
    laporan). Pasangan TANPA baris SO di kolom global t−1 dibaca 0
    (fillna — BUKAN SO tanggal pair-sebelumnya): pair dgn SO di t=1 &
    t=3 mendapat com(3) = 0 − SO(3) bila kolom global t=2 ada (dari
    pasangan lain), = SO(1) − SO(3) bila t=2 tidak ada di frame —
    identik perilaku Anomali COM (dan M Table.Pivot atas kolom yang
    sama). Tanggal pertama kolom → so_prev 0; tanggal 1 → SALDO AWAL
    pasangan BILA ada (dibaca TANPA fill — 'SA ada nilainya 0' ≠
    'SA tidak ada'), fallback so_prev (tanggal negatif bulan lalu).

    Dihitung DALAM grup satuan yang diklik (pola FIX 35-b — konsisten
    dgn angka popup GR/PCS; matriks Anomali COM level pasangan tanpa
    satuan → identik utk pasangan 1-satuan, seluruh data real).
    Return: {tanggal(float) → nilai com} — kosong bila tak ada baris.
    """
    if df is None or df.empty:
        return {}

    jenis_s = df["JENIS"].astype(str)
    # kolom GLOBAL (semua pasangan — mirror col_keys laporan)
    glob_t = pd.to_numeric(
        df.loc[jenis_s.isin(_COM_JENIS), "Tanggal"], errors="coerce")
    col_keys = sorted(set(glob_t.dropna().tolist()), key=_chrono_key)
    if not col_keys:
        return {}

    # baris pasangan (+satuan) 4 JENIS
    mask = (
        (df["Nama Barang"].astype(str) == str(nama_barang))
        & (df["NAMA RESTO"].astype(str) == str(nama_resto))
        & jenis_s.isin(_COM_JENIS)
    )
    if satuan is not None:
        mask &= df["SATUAN"].astype(str) == str(satuan)
    sub = df[mask]
    if sub.empty:
        return {}

    tgl = pd.to_numeric(sub["Tanggal"], errors="coerce")
    nilai = pd.to_numeric(sub["NILAI"], errors="coerce")
    sub = sub.assign(_t=tgl, _v=nilai).dropna(subset=["_t"])
    if sub.empty:
        return {}

    # SALDO AWAL mentah per tanggal (TANPA fill — bedakan 'SA ada' dari
    # 'SA tidak ada'; mirror jenis_df(..., fill=False) laporan; dobel
    # SA dijumlahkan defensif — pivot laporan memakai aggfunc sum).
    sa_raw: dict = {}
    sa_rows = sub[sub["JENIS"].astype(str) == _JENIS_SA] \
        .dropna(subset=["_v"])
    for t, v in zip(sa_rows["_t"], sa_rows["_v"]):
        sa_raw[t] = sa_raw.get(t, 0.0) + float(v)

    # pivot SO/IN/BK per tanggal pasangan (fill 0 — mirror jenis_df
    # fill=True laporan; reindex ke kolom GLOBAL dilakukan via .get)
    piv = sub[sub["JENIS"].astype(str)
              .isin((_JENIS_SO, _JENIS_IN, _JENIS_BK))] \
        .pivot_table(index="_t", columns="JENIS", values="_v",
                     aggfunc="sum", fill_value=0.0)
    for col in (_JENIS_SO, _JENIS_IN, _JENIS_BK):
        if col not in piv.columns:
            piv[col] = 0.0

    def _num(v) -> float:
        """float() NaN/invalid-safe → 0.0 (defensif — pivot sudah
        fill 0, jalur .get default 0.0)."""
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        return 0.0 if pd.isna(f) else f

    so_s = piv[_JENIS_SO]
    in_s = piv[_JENIS_IN]
    bk_s = piv[_JENIS_BK]

    com: dict = {}
    for i, t in enumerate(col_keys):
        try:
            is_t1 = int(float(t)) == 1
        except (TypeError, ValueError):
            is_t1 = False
        if is_t1 and t in sa_raw:
            base = sa_raw[t]           # base com(1) = SA pair (audit fix)
        elif i == 0:
            base = 0.0
        else:
            base = _num(so_s.get(col_keys[i - 1], 0.0))
        com[t] = (base + _num(in_s.get(t, 0.0)) - _num(bk_s.get(t, 0.0))
                  - _num(so_s.get(t, 0.0)))
    return com


def build_popup_rows(data: pd.DataFrame, nama_barang: str,
                     nama_resto: str, satuan: str | None = None
                     ) -> pd.DataFrame:
    """Pure pandas (thread-safe) — siapkan baris popup per Tanggal.

    Hanya 3 JENIS yang dipakai (permintaan user: nilai saldo akhir, SO,
    IN, deviasi — TANPA OUT/BARANG KELUAN/BARANG MASUK):
      Saldo Akhir = Σ 2.SALDO AKHIR · SO = Σ 1.SO · IN = Σ 4.IN
      Deviasi = SO − Saldo Akhir (identik 3.DEVIASI & tabel utama).

    v3.9.25 — dua kolom baru (user: "tambah kolom nomor po dan COM"):
      Nomor PO = nomor pesanan pembelian baris 4.IN per tanggal
                 (split koma → dedup → urut → gabung — pola Nomor);
      COM      = pemakaian harian, formula PERSIS
                 laporan_deviasi_view._compute_com_matrix
                 (_compute_com_series — kolom tanggal GLOBAL, parity
                 48/48 nilai vs matrix Anomali COM). Tanggal tampil di
                 luar kolom global (mis. hanya 2.SALDO AKHIR) → COM
                 kosong (tab Anomali COM juga tak punya nilainya).

    satuan (FIX 35-b / audit 34-b RISK-2): tabel utama memivot per
    (Nama Barang × NAMA RESTO × SATUAN) — pasangan yang punya baris GR
    DAN PCS menghasilkan 2 baris terpisah, jadi popup HARUS mengagregasi
    grup satuan yang sama dgn BARIS YANG DIKLIK (dulu jumlah lintas-
    satuan: GR Dev 2 + PCS Dev 5 → popup 7, tak cocok dgn keduanya).
    KEPUTUSAN kesamaan STRICT (TANPA OR satuan-NA): pivot utama
    (pivot_table dropna default) MENGHAPUS baris ber-SATUAN NA dari
    semua grup — baris NA tidak pernah menyumbang nilai baris tabel
    utama manapun (probe 35b_probe_na_satuan), jadi memasukkannya akan
    membuat popup LEBIH BESAR dari baris utama DAN terhitung ganda di
    popup GR maupun PCS. Di output pipeline append1 SATUAN memang
    konstan per pasangan (lookup LANGKAH 8 fillna per pasangan) — bentuk
    2-satuan hanya dari data satuan eksplisit, persis bentuk yang
    dimodelkan indeks pivot. None = tanpa filter satuan (perilaku lama
    utk pemanggil lain).
    """
    empty = pd.DataFrame(columns=["Tanggal", "Saldo Akhir", "SO", "IN",
                                  "Nomor", "Nomor PO", "COM", "Deviasi"])
    if data is None or data.empty:
        return empty

    df = data
    mask = (
        (df["Nama Barang"].astype(str) == str(nama_barang))
        & (df["NAMA RESTO"].astype(str) == str(nama_resto))
        & (df["JENIS"].isin((_JENIS_SALDO, _JENIS_SO, _JENIS_IN)))
    )
    # FIX 35-b — filter SATUAN grup yang diklik (astype(str) dua sisi:
    # encoding identik dgn nilai kolom Satuan yang dirender tree).
    if satuan is not None:
        mask &= df["SATUAN"].astype(str) == str(satuan)
    sub = df[mask]
    if sub.empty:
        return empty

    tgl = pd.to_numeric(sub["Tanggal"], errors="coerce")
    nilai = pd.to_numeric(sub["NILAI"], errors="coerce")
    sub = sub.assign(_t=tgl, _v=nilai).dropna(subset=["_t"])

    if sub.empty:
        return empty

    # v3.9.22 — Nomor dokumen IN per tanggal (user: "Pop up di tab
    # Deviasi GR dan PCS ada Nomor nya juga Misal IT...... atau
    # RI......"): kumpulkan Nomor baris 4.IN per tanggal (satu baris
    # bisa memuat beberapa nomor sekaligus, dipisah koma di data sumber
    # → dipecah, didedup, diurut, digabung kembali).
    _nomor_per_tgl: dict = {}
    # v3.9.25 — Nomor PO baris 4.IN per tanggal (pola Nomor: split koma
    # → dedup → urut → gabung; IT. pemindahan biasanya tanpa PO → kosong).
    _po_per_tgl: dict = {}
    if "Nomor" in sub.columns:
        in_rows = sub[sub["JENIS"] == _JENIS_IN]
        for _t, _no in zip(in_rows["_t"], in_rows["Nomor"]):
            if pd.isna(_no):
                continue
            for part in str(_no).split(","):
                part = part.strip()
                if part:
                    _nomor_per_tgl.setdefault(_t, set()).add(part)
        if "Nomor PO" in in_rows.columns:
            for _t, _po in zip(in_rows["_t"], in_rows["Nomor PO"]):
                if pd.isna(_po):
                    continue
                for part in str(_po).split(","):
                    part = part.strip()
                    if part:
                        _po_per_tgl.setdefault(_t, set()).add(part)

    # v3.9.25 — COM per tanggal (formula identik Anomali COM; dihitung
    # TERPISAH dari pivot tampilan 3 JENIS supaya union tanggal-nya =
    # persis union 4 JENIS laporan — baris tampilan tidak berubah).
    _com_by_t = _compute_com_series(df, nama_barang, nama_resto, satuan)

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
    out["Nomor"] = [", ".join(sorted(_nomor_per_tgl.get(t, ())))
                    for t in out["_t"]]
    out["Nomor PO"] = [", ".join(sorted(_po_per_tgl.get(t, ())))
                       for t in out["_t"]]
    # v3.9.25 — COM: numerik mentah (belum diformat) supaya minus tetap
    # terdeteksi _is_neg_display setelah diformat; tanggal di luar union
    # 4 JENIS → NaN (kolom kosong, bukan 0).
    out["COM"] = [_com_by_t.get(t, float("nan")) for t in out["_t"]]

    # label tampilan + urut kronologis (numerik — negatif abs 25..31
    # < positif 101..131, jadi bulan lalu dulu lalu 1..31)
    out["Tanggal"] = out["_t"].map(_fmt_tanggal)
    out = out.assign(_k=out["_t"].map(_chrono_key)) \
        .sort_values("_k") \
        .drop(columns=["_k"]).reset_index(drop=True)

    # format angka Indonesia (string — siap render)
    for col in ("Saldo Akhir", "SO", "IN", "COM", "Deviasi"):
        out[col] = out[col].map(DeviasiPopup._fmt_num)

    return out[["Tanggal", "Saldo Akhir", "SO", "IN", "Nomor",
                "Nomor PO", "COM", "Deviasi"]]


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

    rows = build_popup_rows(data, nama_barang, nama_resto, satuan=satuan)
    h_label = _fmt_tanggal(h) if h is not None else ""
    popup = DeviasiPopup(parent, title, rows, h_label=h_label)
    return popup
