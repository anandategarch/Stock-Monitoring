"""
fn_audit.py — Audit rekonsiliasi BM resto vs penerimaan sistem (port engine VBA).

v3.14.0 — ENGINE AUDIT V2 (adaptasi macro VBA user
"modRekapSelisihIN_RULE_ENGINE_V2_FIX_FORMATSTATUS.bas" — user: "cek
logika rekap selisih ini ... kayaknya logika VBA tersebut lebih kuat
untuk analisa nya jadi adaptasi logika nya ya cuman jangan rubah
struktur output kolom nya") — port JalankanAuditV2 + TandaiRentangTerbuka
KE build_audit_rekap (struktur kolom output TIDAK berubah):
- CUT-OFF MAKSIMAL 1 HARI (MAX_CUTOFF_DAYS): rentang selisih yang belum
  kembali nol saat datang hari aktivitas > 1 hari setelah rentang dibuka
  LANGSUNG ditutup sebagai DEVIASI MURNI (tidak lagi menunggu akhir
  grup — IN yang datang terlambat tidak bisa meretro-aktif "resolve"
  deviasi lama; rentang BARU dimulai dari baris itu).
- PENDING CUT-OFF: rentang yang masih terbuka di akhir grup DAN berumur
  ≤ 1 hari dari hari referensi (bulan berjalan = hari ini; bulan
  tertutup = seluruh rentang akhir langsung DEVIASI MURNI).
- NO MOVEMENT - OPEN BALANCE: baris tanpa selisih baru tetapi masih ada
  saldo terbuka (menggantikan status "OK" pada baris nol di rentang
  gantung — kini jujur bahwa saldo belum pulih).
- VALID (Sistem Masuk) diverifikasi KETAT (bukan sekadar "SO naik"):
  kandidat BM=0 & IN>0 wajib (1) SO hari ini tercatat, (2) baseline SO
  tersedia — tgl 1: SO penutupan bulan lalu HARI TERAKHIR saja (tgl
  len_lalu), tgl lain: SO yang TERCATAT persis di hari kalender
  sebelumnya (bukan baris sebelumnya / ffill), (3) ΔSO > 0, (4) ΔSO =
  IN (toleransi 0.0001), (5) tidak ada rentang/saldo terbuka. Gagal
  verifikasi → baris tetap diakumulasi NORMAL + catatan PERLU REVIEW
  spesifik (mirror teks VBA).
- PERLU REVIEW: catatan review per baris digabung ke 'Detail & Catatan
  Audit' dengan format VBA BuildKeterangan ("PERLU REVIEW | alasan |
  Klasifikasi: status | detail engine") — termasuk review rentang yang
  kembali neto-nol tapi saldo pasangan belum pulih.
- Jeda "Beda N Hari" kini dihitung KRONOLOGIS lintas bulan (25• → 1 =
  1 hari; dulu abs(numerik) = 32 — salah arah di rentang lintas batas
  bulan pada mode 📆 Lalu + Ini).

build_audit_input — 10 kolom kanonik dari data app: Hasil SO ← rekap 'SO';
Qty SO Harian ← rekap 'BARANG MASUK' (BM); Qty SJ ← IN 42.05; Qty RI ← 32.24
(keduanya + varian Bulan Lalu); Qty Pembelian ← IN 99.01. Baris = union
tanggal ber-aktivitas, urut kronologis per (Resto, Item): bulan lalu 25•→31•
dulu lalu 1..31 (pembanding SO tgl 1 = SO terakhir bulan lalu).

build_audit_rekap — port 1:1 macro VBA (grup kontigu Resto+Item):
Penerimaan Sistem = SJ + RI + Pembelian; Selisih Harian = BM −
Penerimaan (rumus "BM − IN"). Status: VALID (Sistem Masuk) = SO naik + BM=0 +
IN>0 (input di-omit); OK (Matching) = selisih 0 & saldo 0; saldo kembali
±0.0001 → CUT-OFF RESOLVED / OK (Dalam Cut-off); sisa gantung akhir grup → DEVIASI MURNI.

build_audit_from_app — keduanya + perluasan:
- bulan_lalu: True (default) semua data; False = engine bulan berjalan saja
  (baris Tanggal negatif dibuang SETELAH basis SO-kemarin dihitung).
- Kolom analisa: Qty BM Rekap; Qty SO Kemarin (ffill per pasangan; baris
  pertama bulan berjalan → SALDO AWAL 42.17, fallback SO lalu); Qty Delta
  SO; Qty BK (bk_map); Qty COM = SO(t−1) + IN − BK − SO(t); KPI com_minus = jumlah COM < 0.
- PO menunggu (32.43 'Menunggu diproses') → kolom 'Qty PO Menunggu' + KPI
  dev_murni_po + catatan di DEVIASI MURNI; qty satuan terkecil via konversi.
- detect_data_period + month_lengths: panjang bulan sesuai kalender nyata (bukan hardcode 31).

v3.12.4 — (1) FIX CUT-OFF 1 HARI (user: "input barang masuk tgl 5 tapi IN
di tanggal 6 malah menghasilkan Deviasi murni yang harusnya cut off
resolved"): aturan VALID (Sistem Masuk) — SO naik + BM=0 + IN>0 → omit
selisih — kini hanya aktif bila TIDAK ada rentang gantung terbuka; dulu
penerimaan IN t6 yang menutup BM t5 di-omit → +BM gantung → DEVIASI MURNI
padahal pola 1-hari cut-off (kini CUT-OFF RESOLVED "Beda N Hari").
(2) KOLOM 'Kode IT/RI' — nomor dokumen penerimaan per baris ber-IN ≠ 0
(42.05 → IT.…, 32.24 → RI.…, 99.01 → PI.…; dedup + urut + gabung ', ')
via _kode_it_ri_map/_apply_kode_it_ri (user: "Tambah 1 kolom di sebelah
kanan PO menunggu ... cuman tiap ada data IN>0").
"""
import calendar
import re
from datetime import datetime

import numpy as np
import pandas as pd

from .helpers import (
    norm_nama_barang_key,
    norm_nama_resto_key,
    resto_from_cabang_po,
    stop_check,
)
from .konversi_satuan import lookup_rasio

# Kolom kanonik input audit (struktur identik input VBA / sheet 29)
AUDIT_INPUT_COLUMNS = [
    "Resto", "Nama Item", "UoM", "Tanggal", "Hasil SO",
    "Qty SO Harian", "Qty SJ", "Qty RI", "Qty Pembelian", "Selisih Qty",
]

_KEY_COLS = ["NAMA RESTO", "Nama Barang", "Tanggal"]


def _agg_sum(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Groupby (resto, barang, tgl) → sum(value)."""
    d = df[_KEY_COLS + [value_col]].copy()
    d["Tanggal"] = pd.to_numeric(d["Tanggal"], errors="coerce")
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    d = d.dropna(subset=_KEY_COLS)
    return d.groupby(_KEY_COLS, as_index=False, dropna=False)[value_col].sum()


# v3.10 — kode dokumen RI/IT/PI: PREFIKS.TAHUN.BULAN.NOMOR (utk deteksi
# periode data bila kolom timestamp kosong — mirror doc_codes, TANPA
# import modul ui dari pipeline (arah import ui→pipeline saja).
_PERIOD_CODE_RE = re.compile(r"^[A-Za-z]+\.(\d{4})\.(\d{1,2})\.")


def detect_data_period(in_detail_df: pd.DataFrame | None):
    """v3.10 — (tahun, bulan) periode data berjalan dari detail IN:
    bulan dari TIMESTAMP dokumen terbaru ('#Tgl/Jam Pembuatan IT'),
    fallback bulan terbesar dari kode dokumen Nomor ('RI.2026.09.1'),
    fallback None (pemanggil memakai bulan sistem). Dipakai utk PANJANG
    BULAN asli (September 30 hari → tak ada tanggal 31; bulan kemarin
    juga sesuai kalender)."""
    best = None
    if in_detail_df is None or getattr(in_detail_df, "empty", True):
        return None
    cols = set(getattr(in_detail_df, "columns", []))
    if "#Tgl/Jam Pembuatan IT" in cols:
        t = pd.to_datetime(in_detail_df["#Tgl/Jam Pembuatan IT"],
                           errors="coerce").dropna()
        if not t.empty:
            # v3.10.1 — FIX P2 (bug hunt 1-a): 1 timestamp nyasar bulan
            # DEPAN (typo tanggal dokumen) dulu membalik periode →
            # month_len/rentang tanggal view salah. Bulan depan relatif
            # jam sistem tidak mungkin jadi periode data yang sah —
            # dibuang; data bulan-bulan lampau tetap sah (app memproses
            # data lama). Semua terbuang → fallback kode Nomor.
            _now = pd.Timestamp.now()
            t = t[(t.dt.year * 12 + t.dt.month)
                  <= (_now.year * 12 + _now.month)]
        if not t.empty:
            best = (int(t.max().year), int(t.max().month))
    if best is None and "Nomor" in cols:
        for v in in_detail_df["Nomor"]:
            m = _PERIOD_CODE_RE.match(str(v or "").strip())
            if m:
                try:
                    y, mo = int(m.group(1)), int(m.group(2))
                except ValueError:
                    continue
                if 1 <= mo <= 12 and (best is None or (y, mo) > best):
                    best = (y, mo)
    return best


def month_lengths(period) -> "tuple[int, int]":
    """v3.10 — (panjang_bulan_ini, panjang_bulan_lalu) dari (tahun, bulan)
    hasil detect_data_period — kalender ASLI (September 30 hari → tak ada
    tanggal 31; Februari ikut kabisat). None/invalid → (31, 31) —
    perilaku lama (rentang penuh 1..31 / -31..31)."""
    try:
        y, m = int(period[0]), int(period[1])
        assert 1 <= m <= 12
    except (TypeError, ValueError, IndexError, AssertionError):
        return 31, 31
    len_ini = calendar.monthrange(y, m)[1]
    pm = m - 1 or 12
    py = y - 1 if m == 1 else y
    len_lalu = calendar.monthrange(py, pm)[1]
    return len_ini, len_lalu


def _attach_so_kemarin(out: pd.DataFrame,
                       saldo_awal_map: "dict | None" = None) -> pd.DataFrame:
    """v3.10 — tambahkan kolom basis "SO kemarin" ke input audit
    (out SUDAH kronologis per (Resto, Nama Item)):

    - "Qty BM Rekap"    : salinan BM rekap lama (display — bukan basis);
    - "Qty SO Kemarin"  : SO(t−1) — pengamatan SO TERAKHIR sebelum t
                          (ffill PER-PASANGAN — v3.10.1: tidak pernah
                          mewarisi lintas pasangan; baris tanpa SO sendiri
                          tetap dapat SO-kemarin utk display, ΔSO-nya
                          NaN); BARIS PERTAMA pasangan di bulan berjalan
                          → SALDO AWAL prioritas (v3.10.1: dulu hanya
                          tgl==1; mirror pivot _compute_com v3.9.5),
                          fallback SO lalu; baris pertama pasangan /
                          baris bulan lalu tanpa observasi → NaN;
    - "Qty Delta SO"    : Hasil SO − Qty SO Kemarin (NaN bila SO(t)
                          belum direkam / tak ada basis).
    """
    bm = (out["Qty SO Harian"].copy() if "Qty SO Harian" in out.columns
          else pd.Series(np.nan, index=out.index, dtype="float64"))
    out["Qty BM Rekap"] = bm

    so = pd.to_numeric(out["Hasil SO"], errors="coerce") \
        .astype("float64")
    # v3.11.35 — kunci pasangan DINORMALISASI kanonik (UPPER + rapat-spasi
    # utk Nama Item; UPPER + segmen setelah titik utk Resto) paritas
    # append1.py yg menormalkan append1_df (sumber saldo_awal_map /
    # bk_map). Sebelumnya cuma .astype(str) (RAW) → mismatch saat rekap
    # raw case/whitespace beda dari append1 canonical → saldo_awal_map
    # .get() miss → SO Kemarin salah → ΔSO/COM/Selisih wrong.
    resto = out["Resto"].map(norm_nama_resto_key)
    item = out["Nama Item"].map(norm_nama_barang_key)
    new_pair = (resto != resto.shift(1)) | (item != item.shift(1))

    # ffill SO DALAM PASANGAN: nilai teramati TERAKHIR sebelum baris t.
    # v3.10.1 — FIX P0 (bug hunt 1-a/1-b): ffill GLOBAL + patch anti-bocor
    # lama (null baris PERTAMA pasangan tanpa SO) hanya menyembuhkan 2
    # baris pertama — baris ke-3+ pasangan yang belum punya SO tetap
    # MEWARISI SO pasangan SEBELUMNYA ("SO Kemarin" = stok barang lain;
    # ΔSO baris-SO-pertama pasangan dibandingkan ke SO pasangan lain →
    # Selisih/Status/COM salah). Kini ffill & shift PER-PASANGAN via
    # groupby id pasangan — tidak ada warisan lintas pasangan sama sekali
    # (baris pertama pasangan otomatis NaN oleh groupby-shift).
    pair_id = np.cumsum(new_pair.to_numpy(dtype="int64"))
    so_ff = so.groupby(pair_id).ffill()
    so_prev = so_ff.groupby(pair_id).shift(1)

    # SALDO AWAL prioritas di batas bulan (parity pivot COM v3.9.5).
    # v3.10.1 — FIX P1 (bug hunt 1-a): jangkar SA diperluas dari tgl==1
    # ke BARIS PERTAMA pasangan di bulan berjalan (tgl berapapun):
    # pasangan tanpa baris tanggal 1 (aktivitas pertama tgl 2+) sebelumnya
    # TANPA basis sama sekali (ΔSO NaN→0 → Selisih −IN phantom "gantung
    # semu" di varian Bulan Ini) padahal SA tersedia. Baris tgl 1 selalu
    # baris pertama bulan-berjalan pasangannya (sort kronologis) →
    # generalisasi ini MENGULANGI perilaku tgl-1 lama + menutup lubangnya.
    tgl = pd.to_numeric(out["Tanggal"], errors="coerce")
    if saldo_awal_map:
        sa_vals = [saldo_awal_map.get((r, b))
                   for r, b in zip(resto, item)]
        sa = pd.to_numeric(pd.Series(sa_vals, index=out.index),
                           errors="coerce")
        is_cur = (tgl >= 1).fillna(False)
        first_cur = is_cur.groupby(pair_id).cumsum() == 1
        so_prev = so_prev.mask(first_cur & sa.notna(), sa)

    out["Qty SO Kemarin"] = so_prev.astype("float64")
    out["Qty Delta SO"] = (so - so_prev).astype("float64")
    return out


def build_audit_input(rekap_so_df: pd.DataFrame | None,
                      in_detail_df: pd.DataFrame | None,
                      saldo_awal_map: "dict | None" = None) -> pd.DataFrame:
    """Bangun input audit (10 kolom kanonik + 3 kolom basis v3.10) dari
    data app.

    rekap_so_df : rekap mentah long (JENIS 'SO' / 'BARANG MASUK') —
                  keluaran query_full_rekap_mentah_so (dipapankan dari
                  build_append1 via rekap_so_out).
    in_detail_df: detail IN per dokumen (SOURCE IN 42.05 / 42.05 (Bulan
                  Lalu) / 32.24 / 32.24 (Bulan Lalu) / 99.01).
    saldo_awal_map: v3.10 — {(resto, barang): nilai SA 42.17} basis
                  "SO kemarin" di Tanggal 1 (None = tanpa SA — fallback
                  SO terakhir / NaN; kompatibel pemanggil lama).
    """
    empty = pd.DataFrame(columns=AUDIT_INPUT_COLUMNS)

    so = pd.DataFrame()
    bm = pd.DataFrame()
    if rekap_so_df is not None and not rekap_so_df.empty \
            and "JENIS" in rekap_so_df.columns:
        jenis = rekap_so_df["JENIS"].fillna("").astype(str) \
            .str.strip().str.upper()
        so = rekap_so_df[jenis == "SO"]
        bm = rekap_so_df[jenis == "BARANG MASUK"]

    so_agg = _agg_sum(so, "Value").rename(columns={"Value": "Hasil SO"}) \
        if not so.empty else pd.DataFrame(columns=_KEY_COLS + ["Hasil SO"])
    bm_agg = _agg_sum(bm, "Value").rename(columns={"Value": "Qty SO Harian"}) \
        if not bm.empty else pd.DataFrame(columns=_KEY_COLS + ["Qty SO Harian"])

    sj = ri = pb = pd.DataFrame()
    if in_detail_df is not None and not in_detail_df.empty \
            and "SOURCE IN" in in_detail_df.columns:
        src = in_detail_df["SOURCE IN"].fillna("").astype(str).str.strip()
        # v3.9.17: 42.05 bulan lalu ikut Qty SJ (Kiriman HO) — sumber IN
        sj = in_detail_df[src.isin(["42.05", "42.05 (Bulan Lalu)"])]
        ri = in_detail_df[src.isin(["32.24", "32.24 (Bulan Lalu)"])]
        pb = in_detail_df[src == "99.01"]
    sj_agg = _agg_sum(sj, "Value").rename(columns={"Value": "Qty SJ"}) \
        if not sj.empty else pd.DataFrame(columns=_KEY_COLS + ["Qty SJ"])
    ri_agg = _agg_sum(ri, "Value").rename(columns={"Value": "Qty RI"}) \
        if not ri.empty else pd.DataFrame(columns=_KEY_COLS + ["Qty RI"])
    pb_agg = _agg_sum(pb, "Value").rename(columns={"Value": "Qty Pembelian"}) \
        if not pb.empty else pd.DataFrame(columns=_KEY_COLS + ["Qty Pembelian"])

    # baris = union tanggal dengan aktivitas:
    # SO direkam (baris rekap ada — hadir walaupun nilainya 0),
    # BM diinput, atau ada penerimaan sistem (IN ≠ 0)
    parts = []
    for d in (so_agg, bm_agg):
        if not d.empty:
            parts.append(d[_KEY_COLS])
    for d in (sj_agg, ri_agg, pb_agg):
        if not d.empty:
            nz = d[d.columns[-1]] != 0
            parts.append(d.loc[nz, _KEY_COLS])
    if not parts:
        return empty
    keys = pd.concat(parts, ignore_index=True).drop_duplicates()

    out = keys.merge(so_agg, on=_KEY_COLS, how="left") \
        .merge(bm_agg, on=_KEY_COLS, how="left") \
        .merge(sj_agg, on=_KEY_COLS, how="left") \
        .merge(ri_agg, on=_KEY_COLS, how="left") \
        .merge(pb_agg, on=_KEY_COLS, how="left")

    out = out.rename(columns={"NAMA RESTO": "Resto",
                              "Nama Barang": "Nama Item"})
    out["UoM"] = ""          # Satuan dipetakan view dari append1
    out["Tanggal"] = pd.to_numeric(out["Tanggal"], errors="coerce")
    out = out.dropna(subset=["Tanggal"])
    out["Tanggal"] = out["Tanggal"].astype("Int64")
    for c in ("Hasil SO", "Qty SO Harian", "Qty SJ", "Qty RI",
              "Qty Pembelian"):
        out[c] = pd.to_numeric(out[c], errors="coerce")  # NaN = tidak ada
    out["Selisih Qty"] = (
        out["Qty SO Harian"].fillna(0.0)
        - (out["Qty SJ"].fillna(0.0) + out["Qty RI"].fillna(0.0)
           + out["Qty Pembelian"].fillna(0.0))
    )
    out["Resto"] = out["Resto"].astype(str)
    out["Nama Item"] = out["Nama Item"].astype(str)
    out = out[AUDIT_INPUT_COLUMNS]
    # urut per (Resto, Nama Item) → grup kontigu; tanggal KRONOLOGIS:
    # bulan lalu (negatif) duluan urut hari NAIK (25•→31• = -25→-31),
    # lalu bulan berjalan 1..31.
    # v3.9.6 (permintaan user: "tab selisih in jika tanggal 1 pembanding
    # SO nya SO bulan lalu"): sort numerik lama membalik urutan bulan lalu
    # (−31/31• tampil PERTAMA, baris terakhir sebelum tgl 1 = −25/25•) —
    # delta SO di tanggal 1 membanding SO tgl 25 bulan lalu, BUKAN SO
    # terakhir bulan lalu (31•). Dengan sort kronologis, baris tepat
    # sebelum tanggal 1 = SO terakhir bulan lalu → pembanding benar.
    tgl_num = pd.to_numeric(out["Tanggal"], errors="coerce")
    _k1 = np.where(tgl_num < 0, 0, 1)          # 0 = bulan lalu, 1 = berjalan
    _k2 = np.where(tgl_num < 0, -tgl_num, tgl_num)  # hari (25..31 / 1..31)
    out = out.assign(_k1=_k1, _k2=_k2)
    out = out.sort_values(["Resto", "Nama Item", "_k1", "_k2"],
                          kind="mergesort", na_position="last")
    out = out.drop(columns=["_k1", "_k2"]).reset_index(drop=True)
    # v3.10 — basis "SO kemarin" SETELAH sort (butuh urutan kronologis
    # per pasangan); kolom kanonik 10 tetap DI DEPAN (struktur input VBA
    # utuh — engine & pemanggil lama tak tersentuh).
    return _attach_so_kemarin(out, saldo_awal_map)


# =============================================================================
# ENGINE AUDIT REKONSILIASI (port 1:1 VBA BuatLaporanDeviasiSampel)
# =============================================================================

# Status (persis string VBA)
ST_OK_MATCH = "OK (Matching)"
ST_VALID = "VALID (Sistem Masuk)"
ST_CUTOFF = "CUT-OFF RESOLVED"
ST_IN_CUTOFF = "OK (Dalam Cut-off)"
ST_DEV_MURNI = "DEVIASI MURNI"
ST_OK = "OK"

# v3.14 — ENGINE AUDIT V2 (adaptasi macro modRekapSelisihIN RULE ENGINE
# V2): status baru + batas cut-off. PENDING CUT-OFF = rentang masih
# terbuka tapi berumur ≤ MAX_CUTOFF_DAYS dari hari referensi (IN masih
# mungkin datang); NO MOVEMENT - OPEN BALANCE = baris tanpa selisih baru
# namun saldo pasangan belum pulih.
ST_PENDING = "PENDING CUT-OFF"
ST_OPEN_BAL = "NO MOVEMENT - OPEN BALANCE"
ST_REVIEW = "PERLU REVIEW"
MAX_CUTOFF_DAYS = 1   # mirror VBA MAX_CUTOFF_DAYS ("ubah ke 2 bila SOP
                      # mengizinkan dua hari")

# v3.9.30 — status Pesanan Pembelian 32.43 yang berarti PO SUDAH dibuat
# tapi belum diproses jadi penerimaan (RI) — hipotesis user: penyebab
# deviasi murni (PO ada, penerimaan belum di-update sistem → Qty RI 0
# → selisih SO Harian − Penerimaan gantung).
PO_STATUS_MENUNGGU = "menunggu diproses"

_EPS = 0.0001


def _fmt_qty(v: float) -> str:
    """Format mirip VBA '#,##0' dgn locale Indonesia: bulat + titik ribuan
    (identik output macro user: 'SO Naik +63.405', 'Sisa Gantung: -5.705')."""
    iv = int(v + (0.5 if v >= 0 else -0.5))   # round half away from zero
    return f"{iv:,}".replace(",", ".")


def _fmt_signed(v: float) -> str:
    """Format VBA '+#,##0;-#,##0;0' (locale Indonesia) utk Sisa Gantung.
    VBA membulatkan ke integer DULU lalu pilih pola (+/-/0) — nilai
    -0.0004 tampil '0', bukan '-0'."""
    iv = int(v + (0.5 if v >= 0 else -0.5))
    if iv > 0:
        return f"+{f'{iv:,}'.replace(',', '.')}"
    if iv < 0:
        return f"-{f'{-iv:,}'.replace(',', '.')}"
    return "0"


def build_audit_rekap(df: pd.DataFrame,
                      stop_event=None,
                      len_lalu: int = 31,
                      reference_day: "int | None" = None,
                      so_lalu_map: "dict | None" = None,
                      ) -> tuple[pd.DataFrame, dict]:
    """Jalankan algoritma rekonsiliasi → (df hasil + kolom audit, KPI dict).

    v3.14 — ENGINE AUDIT V2: port 1:1 JalankanAuditV2 +
    TandaiRentangTerbuka macro VBA modRekapSelisihIN RULE ENGINE V2
    (STRUKTUR KOLOM OUTPUT TIDAK BERUBAH — hanya aturan klasifikasi
    yang menguat):

    - Rentang selisih (window) berumur > MAX_CUTOFF_DAYS (1 hari)
      terhadap HARI KALENDER ditutup LANGSUNG sebagai DEVIASI MURNI
      (rentang baru boleh dibuka baris itu juga) — tidak menunggu
      akhir grup; IN terlambat tak bisa meretro-resolve deviasi lama.
    - Rentang terbuka di akhir grup: berumur ≤ 1 hari dari hari
      referensi → PENDING CUT-OFF; selebihnya (atau bulan data sudah
      tertutup — ``reference_day`` None) → DEVIASI MURNI.
    - Baris tanpa selisih baru saat saldo terbuka → NO MOVEMENT -
      OPEN BALANCE (dulu "OK"/tanpa status — tidak jujur).
    - VALID (Sistem Masuk) KETAT: kandidat BM=0 & IN>0 diverifikasi
      (SO hari ini ada · baseline SO hari kalender SEBELUMNYA ada ·
      ΔSO>0 · ΔSO=IN · tanpa rentang/saldo terbuka); gagal → catatan
      PERLU REVIEW spesifik + akumulasi normal (tidak omit).
    - Review per baris digabung ke 'Detail & Catatan Audit' format
      BuildKeterangan VBA: "PERLU REVIEW | alasan | Klasifikasi:
      <status> | <detail engine>".

    Param V2 (opsional — default kompatibel pemanggil lama):
    - ``len_lalu``: panjang bulan lalu ASLI (kalender) — aritmetika
      hari lintas batas bulan (25• → 1 = 1 hari) + syarat baseline
      tgl 1 (hari terakhir bulan lalu = tgl len_lalu).
    - ``reference_day``: hari referensi "hari ini" (Day(Date) VBA)
      utk status PENDING vs DEVIASI rentang akhir; None = bulan data
      TERTUTUP → semua rentang akhir langsung DEVIASI MURNI.
    - ``so_lalu_map``: {(resto, item): (tgl_negatif, SO)} observasi
      SO bulan lalu TERAKHIR per pasangan (sumber baseline tgl 1 —
      dibangun build_audit_from_app dari frame PRA-filter bulan ini
      supaya varian "Bulan Ini" tetap punya baseline tgl 1).

    Baris diproses PERSIS urutan input; grup = blok kontigu dengan
    pasangan (Resto, Nama Item) sama — perilaku identik macro VBA
    (input sudah diurutkan per Resto+Item+Tanggal kronologis).
    FIX 6f-02: pasangan dibandingkan sebagai TUPLE (bukan
    konkatenasi 'Resto|Item' — kolisi bila nilai memuat '|').

    stop_event: threading.Event opsional — checkpoint per GRUP + tiap
    1024 baris dalam grup patologis. Default None = perilaku lama.
    """
    n = len(df)
    kpi = {
        "rows": n, "cutoff": 0, "omit": 0, "deviasi_murni": 0,
        "deviasi_qty": 0.0, "ok": 0,
        # v3.14 — KPI V2 (aditif; pemanggil lama pakai .get default 0)
        "pending": 0, "open_bal": 0, "review": 0,
    }
    out = df.copy()
    if n == 0:
        for c in ("Penerimaan Sistem", "Selisih Harian", "Saldo Kumulatif",
                  "Status Analisis Audit", "Detail & Catatan Audit"):
            out[c] = pd.Series(dtype="object")
        return out, kpi

    # --- array numerik (NaN → 0, kecuali Hasil SO yang mempertahankan
    # kehadiran — mirror IsNumeric/IsEmpty VBA) ---
    def _col(name: str) -> np.ndarray:
        return pd.to_numeric(df[name], errors="coerce").fillna(0.0) \
            .to_numpy(dtype="float64")

    hasil_so = pd.to_numeric(df["Hasil SO"], errors="coerce") \
        .to_numpy(dtype="float64")            # NaN = sel Hasil SO kosong
    so_harian = _col("Qty SO Harian")
    sj = _col("Qty SJ")
    ri = _col("Qty RI")
    pb = _col("Qty Pembelian")
    penerimaan = sj + ri + pb
    selisih = so_harian - penerimaan
    tgl = pd.to_numeric(df["Tanggal"], errors="coerce").fillna(0) \
        .to_numpy(dtype="float64")

    # FIX 6f-02 (audit 6-f): kunci grup = TUPLE (resto, item) — bukan
    # konkatenasi 'Resto|Item'. Tuple dibandingkan eksak; konsisten dgn
    # kunci pasangan (resto, barang) di _po_menunggu_pairs.
    resto_s = df["Resto"].astype(str).tolist()
    item_s = df["Nama Item"].astype(str).tolist()
    keys = list(zip(resto_s, item_s))

    # v3.14 — SO TERCATAT per (pasangan, tanggal): peta lookup baseline
    # V2 (mirror mSo VBA — SO harus tercatat PERSIS di hari kalender
    # sebelumnya, bukan baris sebelumnya / ffill).
    so_at: dict = {}
    for i in range(n):
        if not np.isnan(hasil_so[i]):
            so_at[(resto_s[i], item_s[i], int(tgl[i]))] = hasil_so[i]

    # v3.14 — indeks kronologis HARIAAN lintas bulan (mirror kunci
    # _k1/_k2 + panjang bulan asli): 25•→25 … 31•→31, lalu 1→len_lalu+1,
    # 2→len_lalu+2 … — selisih indeks = selisih HARI KALENDER yang benar
    # untuk rentang lintas batas bulan (mode 📆 Lalu + Ini).
    _len_lalu = int(len_lalu) if len_lalu else 31

    def _cidx(t: float) -> int:
        return -int(t) if t < 0 else _len_lalu + int(t)

    tgl_idx = [_cidx(t) for t in tgl]

    # Hari referensi "hari ini" (Day(Date) VBA) → indeks kronologis;
    # None = bulan data TERTUTUP (historis) — semua rentang akhir grup
    # langsung expired (tak ada IN yang masih bisa datang).
    ref_idx = None if reference_day is None else _cidx(reference_day)

    saldo = [0.0] * n
    status = [""] * n
    detail = [""] * n
    # v3.14 — catatan review per baris (mirror aReview VBA; dedup
    # persis — InStr VBA ≈ membership list).
    review: "list[list[str] | None]" = [None] * n

    def _add_review(i: int, note: str) -> None:
        if review[i] is None:
            review[i] = [note]
            kpi["review"] += 1
        elif note not in review[i]:
            review[i].append(note)

    def _tgl_int(i: int) -> int:
        return int(tgl[i])

    def _tgl_lbl(v: int) -> str:
        # v3.11.1 — label tanggal utk catatan audit — bulan-lalu
        # negatif → '28•' (konvensi '•' = bulan lalu, mirror label
        # tabel & export).
        return f"{-int(v)}•" if v < 0 else str(int(v))

    def _tandai_rentang(first_row: int, last_row: int, net_range: float,
                        pending: bool, total_balance: float) -> None:
        """Port TandaiRentangTerbuka VBA — tutup rentang terbuka:
        baris ber-selisih → PENDING CUT-OFF (masih dalam jendela) /
        DEVIASI MURNI (melewati batas); baris nol → NO MOVEMENT -
        OPEN BALANCE. Saldo berjalan total disertakan bila belum nol."""
        if first_row < 0 or last_row < first_row:
            return
        start_t = int(tgl[first_row])
        for j in range(first_row, last_row + 1):
            if status[j] != "":
                continue
            if selisih[j] != 0.0:
                if pending:
                    status[j] = ST_PENDING
                    detail[j] = (f"Saldo rentang {_fmt_signed(net_range)} "
                                 f"(Sejak Tgl {_tgl_lbl(start_t)}) — "
                                 f"jendela cut-off {MAX_CUTOFF_DAYS} hari "
                                 f"masih aktif")
                    kpi["pending"] += 1
                else:
                    status[j] = ST_DEV_MURNI
                    detail[j] = (f"Sisa Gantung: {_fmt_signed(net_range)} "
                                 f"(Sejak Tgl {_tgl_lbl(start_t)}) — "
                                 f"melewati batas cut-off {MAX_CUTOFF_DAYS} "
                                 f"hari")
                    kpi["deviasi_murni"] += 1
                if abs(total_balance) >= _EPS:
                    detail[j] += (f"; saldo berjalan "
                                  f"{_fmt_signed(total_balance)}")
            else:
                status[j] = ST_OPEN_BAL
                detail[j] = (f"Tidak ada selisih baru; rentang sejak Tgl "
                             f"{_tgl_lbl(start_t)} masih memiliki saldo "
                             f"{_fmt_signed(net_range)}")
                kpi["open_bal"] += 1

    group_start = 0
    while group_start < n:
        # checkpoint ⏹ per grup (audit 1-d; engine = loop baris Python
        # murni — ⏹ tak terasa sampai engine selesai)
        if not (group_start & 1023):
            stop_check(stop_event,
                       f"audit rekonsiliasi (baris {group_start:,}/{n:,})")
        group_end = group_start
        while group_end + 1 < n and keys[group_end + 1] == keys[group_start]:
            group_end += 1

        cum = 0.0                 # runningBalance VBA
        start_idx = -1            # jendela terbuka (VBA startIdx=0, 1-based)
        window_net = 0.0          # windowNet VBA

        for i in range(group_start, group_end + 1):
            # checkpoint ⏹ tiap 1024 baris dalam grup patologis
            if not (i & 1023):
                stop_check(stop_event,
                           f"audit rekonsiliasi (baris {i:,}/{n:,})")
            sel_val = selisih[i]
            this_day = int(tgl[i])
            this_idx = tgl_idx[i]

            # (V2) Tutup jendela lama SEBELUM memproses hari yang sudah
            # melewati batas cut-off: umur = selisih HARI KALENDER
            # (kronologis lintas bulan), bukan jumlah baris.
            if start_idx >= 0 \
                    and this_idx - tgl_idx[start_idx] > MAX_CUTOFF_DAYS:
                _tandai_rentang(start_idx, i - 1, window_net, False, cum)
                kpi["deviasi_qty"] += window_net
                start_idx = -1
                window_net = 0.0

            # (V2) Baseline SO: tgl 1 → SO penutupan bulan lalu HARI
            # TERAKHIR saja (tgl len_lalu — mirror syarat
            # mLastSOLaluDay==31 VBA, panjang bulan ASLI); hari lain →
            # SO yang TERCATAT persis di hari kalender sebelumnya
            # (lookup langsung — bukan baris sebelumnya / ffill).
            # Hari bulan lalu (negatif): encoding terbalik — hari
            # sebelumnya = t+1 (25• sebelum 26•).
            has_so = not np.isnan(hasil_so[i])
            has_baseline = False
            baseline = 0.0
            review_text = ""
            if this_day == 1:
                info = (so_lalu_map or {}).get(keys[i])
                if info is None:
                    _v0 = so_at.get((resto_s[i], item_s[i], -_len_lalu))
                    if _v0 is not None:
                        info = (-_len_lalu, _v0)
                if info is not None:
                    _d, _v = info
                    if -int(_d) == _len_lalu:
                        baseline = float(_v)
                        has_baseline = True
                    else:
                        review_text = (
                            f"SO penutupan bulan lalu terakhir tercatat "
                            f"pada tgl {-int(_d)}; baseline tgl "
                            f"{_len_lalu} tidak tersedia")
            else:
                prev_day = this_day + 1 if this_day < 0 else this_day - 1
                _v = so_at.get((resto_s[i], item_s[i], prev_day))
                if _v is not None:
                    baseline = float(_v)
                    has_baseline = True
            delta_so = (hasil_so[i] - baseline) \
                if (has_so and has_baseline) else 0.0

            # (V2) Kandidat VALID diverifikasi KETAT — bukti tidak
            # lengkap/tidak cocok → baris tetap masuk saldo selisih +
            # catatan PERLU REVIEW (mirror urutan cek VBA).
            is_verified_valid = False
            if abs(so_harian[i]) < _EPS and penerimaan[i] > _EPS:
                if not has_so:
                    review_text = (
                        f"BM=0 dan IN={_fmt_signed(penerimaan[i])}, "
                        f"tetapi Hasil SO hari ini tidak tercatat")
                elif not has_baseline:
                    if not review_text:
                        review_text = (
                            "SO hari ini tercatat, tetapi SO baseline "
                            "hari sebelumnya tidak tersedia")
                elif delta_so <= _EPS:
                    review_text = (
                        f"IN={_fmt_signed(penerimaan[i])}, tetapi SO "
                        f"tidak meningkat (delta SO="
                        f"{_fmt_signed(delta_so)})")
                elif abs(delta_so - penerimaan[i]) > _EPS:
                    review_text = (
                        f"Kenaikan SO={_fmt_signed(delta_so)} tidak sama "
                        f"dengan IN={_fmt_signed(penerimaan[i])}")
                elif start_idx >= 0 or abs(cum) >= _EPS:
                    review_text = (
                        "Delta SO sama dengan IN, tetapi masih ada "
                        "saldo/rentang sebelumnya yang terbuka")
                else:
                    is_verified_valid = True

            if is_verified_valid:
                # IN terbukti masuk melalui kenaikan SO — tidak
                # menambah selisih/saldo (omit, perilaku lama).
                saldo[i] = cum
                status[i] = ST_VALID
                detail[i] = (f"Kenaikan SO {_fmt_signed(delta_so)} sesuai "
                             f"IN {_fmt_signed(penerimaan[i])}; BM=0 dan "
                             f"baseline SO tersedia")
                kpi["omit"] += 1
            else:
                if review_text:
                    _add_review(i, review_text)

                cum += sel_val
                saldo[i] = cum

                if start_idx < 0:
                    if abs(sel_val) < _EPS:
                        if abs(cum) < _EPS:
                            status[i] = ST_OK_MATCH
                            detail[i] = "-"
                            kpi["ok"] += 1
                        else:
                            # (V2) saldo lama belum pulih — jujur
                            # "NO MOVEMENT - OPEN BALANCE" (dulu: tanpa
                            # status / "OK").
                            status[i] = ST_OPEN_BAL
                            detail[i] = (f"Tidak ada selisih baru; saldo "
                                         f"sebelumnya masih terbuka "
                                         f"{_fmt_signed(cum)}")
                            kpi["open_bal"] += 1
                    else:
                        start_idx = i
                        window_net = sel_val
                else:
                    window_net += sel_val

                # (V2) Rentang kembali neto-nol DI DALAM jendela cut-off
                # → resolved; saldo global belum pulih → review.
                if start_idx >= 0 and abs(window_net) < _EPS:
                    start_t = _tgl_int(start_idx)
                    jeda = this_idx - tgl_idx[start_idx]
                    range_text = (f"Beda {jeda} Hari (Periode Tgl "
                                  f"{_tgl_lbl(start_t)} - "
                                  f"{_tgl_lbl(this_day)})")
                    overall_text = ""
                    res_review = ""
                    if abs(cum) >= _EPS:
                        overall_text = (f"; masih ada saldo keseluruhan "
                                        f"{_fmt_signed(cum)}")
                        res_review = (
                            f"Rentang ini kembali neto nol, tetapi saldo "
                            f"pasangan masih {_fmt_signed(cum)} dari "
                            f"deviasi periode sebelumnya di luar jendela "
                            f"cut-off; perlu rekonsiliasi manual")
                    for j in range(start_idx, i + 1):
                        if status[j] == "":
                            if selisih[j] != 0.0:
                                status[j] = ST_CUTOFF
                                detail[j] = range_text + overall_text
                                kpi["cutoff"] += 1
                            else:
                                status[j] = ST_IN_CUTOFF
                                detail[j] = (f"Rentang Cut-off Tgl "
                                             f"{_tgl_lbl(start_t)} - "
                                             f"{_tgl_lbl(this_day)}"
                                             f"{overall_text}")
                        if res_review:
                            _add_review(j, res_review)
                    start_idx = -1
                    window_net = 0.0

        # (V2) Sisa rentang di akhir grup: masih dalam jendela cut-off
        # hari referensi → PENDING CUT-OFF; selebihnya (atau bulan data
        # tertutup) → DEVIASI MURNI.
        if start_idx >= 0:
            pending = (ref_idx is not None
                       and ref_idx - tgl_idx[start_idx] <= MAX_CUTOFF_DAYS)
            _tandai_rentang(start_idx, group_end, window_net, pending, cum)
            if not pending:
                kpi["deviasi_qty"] += window_net

        group_start = group_end + 1

    out["Penerimaan Sistem"] = penerimaan
    out["Selisih Harian"] = selisih
    out["Saldo Kumulatif"] = saldo
    # (V2) Gabung catatan review — format BuildKeterangan VBA:
    # "PERLU REVIEW | alasan | Klasifikasi: <status> | <detail engine>".
    detail_out = []
    for i in range(n):
        rv = review[i]
        base = detail[i]
        if rv:
            status_txt = status[i] if status[i] else \
                "PERLU REVIEW - STATUS TIDAK TERBENTUK"
            parts = [f"{ST_REVIEW} | {' ; '.join(rv)}",
                     f"Klasifikasi: {status_txt}"]
            if base and base != "-":
                parts.append(base)
            detail_out.append(" | ".join(parts))
        else:
            detail_out.append(base)
    out["Status Analisis Audit"] = status
    out["Detail & Catatan Audit"] = detail_out
    return out, kpi


def _filter_bulan_ini(df: "pd.DataFrame | None") -> "pd.DataFrame | None":
    """v3.9.27 — buang baris Tanggal NEGATIF (data bulan lalu: rekap lalu
    25..31 dinegasikan + IN 42.05/32.24 bulan lalu) supaya engine audit
    berjalan di atas BULAN BERJALAN saja — perilaku identik sheet
    LAPORAN_DEVIASI workbook user (tgl 1..31, tanpa baris negatif).
    Baris tanpa Tanggal valid dibiarkan (dibuang lagi oleh
    build_audit_input dropna)."""
    if df is None or getattr(df, "empty", True) \
            or "Tanggal" not in getattr(df, "columns", []):
        return df
    t = pd.to_numeric(df["Tanggal"], errors="coerce")
    return df[(t >= 1) | t.isna()]


# =============================================================================
# v3.9.30 — PO MENUNGGU DIPROSES (32.43) → PENJELAS DEVIASI MURNI
# (user: "cek Rincian PO file 32.43 — ada nama resto+barang dengan status
# pesanan 'Menunggu diproses'; PO sudah ada tapi penerimaan belum
# di-update di sistem → bisa jadi penyebab deviasi murni")
# =============================================================================

def _po_nomor_str(v) -> str:
    """Nomor PO → string bersih (None/NaN → ''; float integral tanpa
    '.0') — mirror _doc_code_str/rincian _resto_name NA-safety."""
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def extract_po_pending(po_df: "pd.DataFrame | None") -> pd.DataFrame:
    """v3.9.30 — subset Rincian PO 32.43 ber-Status Pesanan Pembelian
    'Menunggu diproses' (case/whitespace-insensitive).

    Input boleh frame MENTAH (hasil merge build_rincian_po tanpa filter
    KATEGORI) maupun yang sudah terfilter — fungsi idempoten. Kolom
    status hilang / None / kosong → frame kosong (audit tanpa PO)."""
    if po_df is None or getattr(po_df, "empty", True):
        return pd.DataFrame()
    if "Status Pesanan Pembelian" not in getattr(po_df, "columns", []):
        return pd.DataFrame()
    status = po_df["Status Pesanan Pembelian"].fillna("") \
        .astype(str).str.strip().str.lower()
    return po_df[status == PO_STATUS_MENUNGGU].copy()


def _po_menunggu_pairs(po_pending_df: "pd.DataFrame | None",
                      konversi: "dict | None" = None) -> dict:
    """{(resto, barang): [(nomor, qty, satuan_label, unconverted), ...]}
    dari PO menunggu.

    resto = resto_from_cabang_po(Cabang PO '1370.MLGPAR' → 'MLGPAR') —
    join key identik dgn Resto audit; barang di-strip; nomor & qty
    defensif (kolom hilang → ''/0.0); urut per nomor; pasangan tanpa
    resto/barang valid dibuang.

    v3.9.31 — KONVERSI SATUAN: bila ``konversi`` (peta dari
    konversi_satuan.build_konversi_map — 42.05 '#Sat. Kirim'+'Rasio
    Satuan' + 32.24 'Satuan'+'Rasio Satuan') diberikan:
    qty × rasio[(barang, Satuan PO)] → SATUAN TERKECIL (apple-to-apple
    dgn Selisih/Saldo audit — user: "air mineral PO karton, barang
    masuk botol — tidak match waktu cari deviasi murni"); label =
    satuan terkecil barang. Lookup gagal (pasangan (barang, satuan-PO)
    tak terdaftar di 42.05/32.24) → qty AS-IS + label satuan PO +
    penanda unconverted=True (catatan diberi '*'). ``konversi`` None →
    perilaku v3.9.30 persis (qty mentah, tanpa label/penanda).
    """
    out: dict = {}
    if po_pending_df is None or getattr(po_pending_df, "empty", True):
        return out
    cols = set(getattr(po_pending_df, "columns", []))
    if not {"Cabang PO", "Nama Barang"} <= cols:
        return out
    n = len(po_pending_df)
    nomors = (po_pending_df["Nomor #"].tolist() if "Nomor #" in cols
              else [None] * n)
    qtys = (pd.to_numeric(po_pending_df["Kuantitas"], errors="coerce")
            .fillna(0.0).tolist() if "Kuantitas" in cols else [0.0] * n)
    satuans = (po_pending_df["Satuan"].tolist() if "Satuan" in cols
               else [None] * n)
    for cab, brg, nomor, qty, sat in zip(po_pending_df["Cabang PO"],
                                         po_pending_df["Nama Barang"],
                                         nomors, qtys, satuans):
        # v3.11.34 — FIX PO Menunggu "tidak sesuai nama barang": kunci
        # pasangan DINORMALISASI kanonik (UPPER + rapat-spasi utk barang;
        # UPPER + segmen setelah titik utk resto) — sama dgn append1.py
        # yg menormalkan sisi audit. Sebelumnya sisi PO cuma .strip()
        # (case/whitespace mentah) → pasangan beda ejaan tak cocok →
        # Qty PO Menunggu 0 padahal PO ada (user: "kok tidak sesuai
        # nama barangnya ya").
        resto = norm_nama_resto_key(resto_from_cabang_po(cab))
        b = norm_nama_barang_key(_po_nomor_str(brg))
        if not resto or not b:
            continue
        qty = float(qty)
        if konversi is None:
            # legacy v3.9.30 — qty mentah, tanpa label/penanda
            out.setdefault((resto, b), []).append(
                (_po_nomor_str(nomor), qty, "", False))
            continue
        rasio, terk = lookup_rasio(konversi, b, sat)
        if rasio is not None and rasio > 0:
            out.setdefault((resto, b), []).append(
                (_po_nomor_str(nomor), qty * float(rasio),
                 str(terk) if terk else "", False))
        else:
            # fallback (disetujui user): qty PO as-is + penanda '*'
            _sat = _po_nomor_str(sat).upper()
            out.setdefault((resto, b), []).append(
                (_po_nomor_str(nomor), qty, _sat, True))
    for lst in out.values():
        lst.sort()
    return out


def _po_menunggu_note(items) -> str:
    """Catatan 'PO Menunggu: PO.xxx (qty 120 BOTOL), PO.yyy (qty 5
    KARTON*) (+2)' — maks 2 nomor dituliskan, sisanya dihitung (pola
    B1/B2 catatan audit view v3.9.23).

    v3.9.31 — qty menyertai LABEL SATUAN hasil konversi (satuan
    terkecil — apple-to-apple dgn Selisih/Saldo audit); '*' = tidak
    terkonversi (pasangan (barang, satuan-PO) tak ada di peta 42.05/
    32.24 — qty tampil dalam satuan PO asli, disetujui user)."""
    shown = []
    for n, q, sat, unconv in items[:2]:
        qtxt = _fmt_qty(q)
        if sat:
            qtxt = f"{qtxt} {sat}"
        if unconv:
            qtxt += "*"
        shown.append(f"{n} (qty {qtxt})" if n else f"(qty {qtxt})")
    extra = len(items) - len(shown)
    txt = ", ".join(shown)
    if extra > 0:
        txt += f" (+{extra})"
    return f"PO Menunggu: {txt}"


def _join_engine_note(existing: str, note: str) -> str:
    """Append catatan app ke catatan engine ('-' dianggap kosong) —
    mirror in_selisih_view._join_notes (VBA tetap PERTAMA, dipisah ' | ')."""
    s = str(existing).strip() if existing is not None else ""
    if s in ("", "-", "nan", "None"):
        return note
    return f"{s} | {note}"


# =============================================================================
# v3.12.4 — KOLOM 'Kode IT/RI' (user: "Tambah 1 kolom di sebelah kanan PO
# menunggu yaitu kolom KODE IT/RI ... dari 42.05 dengan nomor misal
# IT.2026.10.24306 atau dari 3224 misal RI.2026.11.16044 atau kode PI....
# dari 9901. Itu cuman tiap ada data IN>0 ya") — nomor dokumen penerimaan
# per baris audit ber-IN ≠ 0.
# =============================================================================

def _kode_it_ri_map(in_detail_df: "pd.DataFrame | None") -> dict:
    """{(resto, barang, tgl): 'IT.2026.10.24306, RI.2026.11.16044'} dari
    detail IN — nomor dokumen penerimaan (42.05/42.05 Lalu → IT/SJ,
    32.24/32.24 Lalu → RI, 99.01 → PI), HANYA baris ber-Value ≠ 0
    ("cuman tiap ada data IN>0"). Nomor ganda (multi line-item satu
    dokumen) di-dedupe; hasil diurut; baris tanpa Nomor dilewati.

    Kunci DINORMALISASI kanonik (UPPER + rapat-spasi barang; UPPER +
    segmen-titik resto — paritas _apply_po_menunggu v3.11.34) supaya
    cocok dgn pasangan audit apa pun ejaannya; Tanggal dipakai APA ADANYA
    (negatif = bulan lalu — identik kunci agregasi _agg_sum audit).
    """
    out: dict = {}
    if in_detail_df is None or getattr(in_detail_df, "empty", True):
        return out
    cols = set(getattr(in_detail_df, "columns", []))
    if not {"NAMA RESTO", "Nama Barang", "Tanggal", "Value"} <= cols:
        return out
    d = in_detail_df
    _v = pd.to_numeric(d["Value"], errors="coerce").fillna(0.0)
    d = d.loc[_v != 0.0]
    _t = pd.to_numeric(d["Tanggal"], errors="coerce")
    _has_nomor = "Nomor" in cols
    for r, b, t, n in zip(d["NAMA RESTO"], d["Nama Barang"], _t,
                          (d["Nomor"] if _has_nomor
                           else [None] * len(d))):
        if pd.isna(t):
            continue
        resto = norm_nama_resto_key(r)
        brg = norm_nama_barang_key(_po_nomor_str(b))
        if not resto or not brg:
            continue
        nom = _po_nomor_str(n)
        if not nom:
            continue
        lst = out.setdefault((resto, brg, int(t)), [])
        if nom not in lst:
            lst.append(nom)
    for lst in out.values():
        lst.sort()
    return out


def _apply_kode_it_ri(audit: pd.DataFrame, kode_map: dict) -> None:
    """v3.12.4 — kolom 'Kode IT/RI' ke hasil audit (mutasi in place —
    frame fresh milik build_audit_from_app): nomor dokumen penerimaan per
    baris, digabung ', ' bila >1 dokumen di tanggal itu (dedup + urut);
    baris tanpa IN ≠ 0 → '' (view/export menampilkan '-'). Baris bulan
    lalu (42.05/32.24 Lalu ber-Tanggal negatif) ikut terkode — kunci
    persis kunci agregasi audit. kode_map kosong → kolom '' penuh (skema
    tetap konsisten utk pemanggil/view)."""
    audit["Kode IT/RI"] = ""
    if not kode_map or audit.empty:
        return
    resto = audit["Resto"].map(norm_nama_resto_key)
    item = audit["Nama Item"].map(norm_nama_barang_key)
    tgl = pd.to_numeric(audit["Tanggal"], errors="coerce")
    vals = []
    for r, b, t in zip(resto, item, tgl):
        if pd.notna(t):
            lst = kode_map.get((r, b, int(t)))
            if lst:
                vals.append(", ".join(lst))
                continue
        vals.append("")
    audit["Kode IT/RI"] = vals


def _apply_po_menunggu(audit: pd.DataFrame, kpi: dict,
                       pairs: dict, stop_event=None) -> None:
    """v3.9.30 — perkaya hasil audit dgn info PO Menunggu (mutasi in
    place — frame fresh milik build_audit_from_app):

    - kolom 'Qty PO Menunggu': TOTAL qty PO menunggu pasangan (nilai
      konstanta di SEMUA baris pasangan itu — 0 bila tak ada); sumber
      utk kolom tabel 'PO Menunggu' Rekap Selisih IN + export.
      v3.9.31: nilai TERKONVERSI ke satuan terkecil bila peta konversi
      aktif (disetujui user "tampilkan nilai terkonversi") — baris
      tak terkonversi tampil qty satuan PO asli (penanda '*' di
      catatan).
      v3.9.33 — AUDIT FIX (48-b): pasangan CAMPURAN (sebagian PO
      terkonversi, sebagian fallback satuan PO asli) → kolom menjumlah
      baris TERKONVERSI SAJA (jumlah mentah '120 BOTOL + 3 KARTON =
      123' mencampur dua satuan — bukan angka apple-to-apple dgn
      Selisih/Saldo). Semua-terkonversi / semua-fallback → total
      persis perilaku lama; mix tetap tampil utuh di catatan (qty
      per-PO + penanda '*') dan desc ('N tdk terkonversi').
    - catatan 'PO Menunggu: …' di-append ke 'Detail & Catatan Audit'
      HANYA baris DEVIASI MURNI yang pasangannya punya PO menunggu —
      membedakan deviasi murni EXPLAINABLE (menunggu PO diproses →
      akan resolve saat RI masuk) vs yang perlu audit fisik.
    - KPI 'dev_murni_po': jumlah baris DEVIASI MURNI ber-PO menunggu.

    stop_event: v3.9.72 — threading.Event opsional; checkpoint ⏹ tiap
    2048 baris (audit 1-d — loop Python murni atas SEMUA baris audit;
    dipanggil 2× per run: varian penuh + varian bulan-ini).
    """
    audit["Qty PO Menunggu"] = 0.0
    kpi["dev_murni_po"] = 0
    if not pairs or audit.empty:
        return
    # v3.11.34 — kunci sisi audit DINORMALISASI kanonik (UPPER + rapat-
    # spasi utk Nama Item; UPPER + segmen setelah titik utk Resto) —
    # paritas sisi PO (_po_menunggu_pairs) yg juga menormalkan. Sebelumnya
    # cuma .str.strip() (case/whitespace mentah) → mismatch saat audit
    # frame belum dinormalkan append1 (test/mock) atau drift ejaan.
    resto = audit["Resto"].map(norm_nama_resto_key)
    item = audit["Nama Item"].map(norm_nama_barang_key)
    status = audit["Status Analisis Audit"].astype(str)
    detail = audit["Detail & Catatan Audit"].astype(str).tolist()
    # pandas 3 (CoW): to_numpy() tanpa konversi dtype → view READ-ONLY →
    # qty[i] = ... ValueError "assignment destination is read-only"
    # (fresh install requirements pandas>=2.0.0 kini resolve ke 3.x).
    # copy=True aman utk pandas 2 & 3 (kwarg ada sejak lama).
    qty = audit["Qty PO Menunggu"].to_numpy(dtype="float64", copy=True)
    n_flagged = 0
    for i in range(len(audit)):
        # v3.9.72 — checkpoint ⏹ tiap 2048 baris (audit 1-d; pasangan PO
        # menunggu sedikit tapi scan-nya SELURUH baris audit)
        if not (i & 2047):
            stop_check(stop_event,
                       f"perkaya PO Menunggu (baris {i:,}/{len(audit):,})")
        items = pairs.get((resto.iat[i], item.iat[i]))
        if not items:
            continue
        # v3.9.33 — AUDIT FIX (48-b): jangan campur satuan di kolom TOTAL.
        # Semua PO satu kondisi (semua terkonversi / semua fallback) →
        # jumlah seluruh baris (perilaku lama). Pasangan CAMPURAN →
        # hanya baris TERKONVERSI (satuan terkecil) yang dijumlahkan
        # supaya tetap apple-to-apple dgn Selisih/Saldo; baris fallback
        # (satuan PO asli) tetap tampil di CATATAN '(qty 3 KARTON*)' +
        # desc 'N tdk terkonversi' — mix tetap transparan.
        _n_unconv = sum(1 for _n, _q, _s, u in items if u)
        if _n_unconv == 0 or _n_unconv == len(items):
            qty[i] = sum(q for _, q, _, _ in items)
        else:
            qty[i] = sum(q for _n, q, _s, u in items if not u)
        if status.iat[i] == ST_DEV_MURNI:
            detail[i] = _join_engine_note(
                detail[i], _po_menunggu_note(items))
            n_flagged += 1
    audit["Qty PO Menunggu"] = qty
    audit["Detail & Catatan Audit"] = detail
    kpi["dev_murni_po"] = n_flagged


def build_audit_from_app(rekap_so_df: pd.DataFrame | None,
                         in_detail_df: pd.DataFrame | None,
                         po_pending_df: "pd.DataFrame | None" = None,
                         bulan_lalu: bool = True,
                         konversi: "dict | None" = None,
                         saldo_awal_map: "dict | None" = None,
                         bk_map: "dict | None" = None,
                         period=None,
                         stop_event=None
                         ) -> tuple[pd.DataFrame, dict, str]:
    """Input dari data app + engine sekali jalan.

    v3.14 — ENGINE AUDIT V2 (adaptasi macro RULE ENGINE V2): param baru
    ``period`` (tahun, bulan) periode data — None = deteksi otomatis
    via detect_data_period(in_detail_df) (fallback jam sistem). Dari
    periode: ``len_lalu`` (panjang bulan lalu ASLI — aritmetika hari
    lintas batas bulan + syarat baseline tgl 1) + ``reference_day``:
    - periode = bulan BERJALAN → hari ini (Day(Date) VBA) — rentang
      akhir ≤ 1 hari dari hari ini → PENDING CUT-OFF;
    - periode = bulan LAMPAU (tertutup) → None — semua rentang akhir
      langsung DEVIASI MURNI (tak ada IN yang masih bisa datang).
    ``so_lalu_map`` {(resto, item): (tgl_negatif, SO)} dibangun dari
    frame PRA-filter (observasi SO bulan lalu TERAKHIR per pasangan —
    supaya varian "Bulan Ini" yang membuang baris negatif tetap punya
    baseline tgl 1).
    KPI baru (aditif): ``pending`` · ``open_bal`` · ``review``.

    v3.11.5 — KEMBALI KE RUMUS LAMA (user: "kembali ke rumus lama"):
    slot engine "Qty SO Harian" = BM REKAP persis pra-v3.10 → Selisih
    Harian = BM − Penerimaan Sistem; swap slot + rename output v3.10
    DIHAPUS (engine menerima raw build_audit_input apa adanya).
    Kolom v3.10 (Qty BM Rekap · Qty SO Kemarin · Qty Delta SO · Qty BK ·
    Qty COM) + KPI com_minus TETAP dihitung (display / bahan COM /
    analisa). Param ``saldo_awal_map`` (basis SO-kemarin t=1) &
    ``bk_map`` (bahan COM) tetap berlaku:
    - ``saldo_awal_map``: {(resto, barang): SA 42.17} — basis t=1
      (None = tanpa SA, fallback SO terakhir/NaN — kompatibel pemanggil
      lama/test);
    - ``bk_map``: {(resto, barang, tgl): qty BK 42.15} — bahan kolom
      "Qty COM" (None = COM dihitung dgn BK 0 — masih valid utk data
      tanpa 42.15).

    v3.10 — BASIS "SELISIH DENGAN SO KEMARIN" (kini DIPULIHKAN ke BM
    rekap oleh v3.11.5): slot engine "Qty SO Harian" diisi ΔSO → Selisih
    Harian = (SO(t)−SO(t−1)) − Penerimaan Sistem — basis ini hanya
    bertahan v3.10..v3.11.4.

    v3.9.27 (user: "pada rekap selisih in bisa mode hitung bulan lalu dan
    hanya hitung bulan ini. Tapi default hitung bulan ini aja") — param
    ``bulan_lalu``:
    - True  : SEMUA data (default pipeline; baris bulan lalu ber-Tanggal
              negatif ikut — saldo kumulatif menyambung dari bulan lalu).
    - False : baris Tanggal negatif dibuang SETELAH basis SO-kemarin
              dihitung (v3.10.1 — dulu sebelum build_audit_input, basis
              baris pertama bulan berjalan ikut lenyap) → audit murni
              bulan berjalan (1..31) — mirror sheet LAPORAN_DEVIASI
              (output macro VBA user = 2.798 pasangan × 31 hari, tanpa
              tanggal negatif). Pembanding tanggal pertama = SALDO AWAL
              / SO terakhir bulan lalu (masih diketahui dari basis).

    v3.9.30 — param ``po_pending_df``: Rincian PO 32.43 (frame mentah
    tanpa filter KATEGORI — difilter status 'Menunggu diproses' internal
    via extract_po_pending; None = pemanggil lama, output tak tersentuh).
    Pasangan (resto dari Cabang PO, barang) ber-PO menunggu → kolom
    'Qty PO Menunggu' + catatan 'PO Menunggu: …' di baris DEVIASI MURNI
    + KPI 'dev_murni_po' (lihat _apply_po_menunggu). PO menunggu adalah
    keadaan TERKINI (bukan transaksi bertanggal) → TIDAK difilter
    varian bulan — kedua varian (Lalu+Ini / Bulan Ini) memakai pasangan
    PO yang sama.

    v3.9.31 — param ``konversi``: peta konversi satuan (append1
    konversi_out['map'] — konversi_satuan.build_konversi_map dari
    42.05+32.24). Qty PO dikonversi ke SATUAN TERKECIL (apple-to-apple
    dgn Selisih/Saldo); catatan berlabel satuan '(qty 120 BOTOL)'; tak
    terkonversi → qty as-is + '*' (disetujui user). None = perilaku
    v3.9.30 persis (qty satuan PO tanpa label).

    stop_event: v3.9.72 — threading.Event opsional (audit 1-d: fase
    audit TIDAK punya checkpoint sama sekali — ⏹ menunggu KEDUA varian
    engine + enrichment selesai). Dicek antar tahap (filter bulan →
    input → engine → PO menunggu) & diteruskan ke loop baris internal
    (build_audit_rekap/_apply_po_menunggu). Default None = perilaku
    lama (pemanggil test tanpa stop tetap jalan).

    Return (audit_df, kpi, source_desc). audit_df kosong + kpi["rows"]=0
    bila tidak ada data rekap SO / IN sama sekali; source_desc menjelaskan
    asal data (untuk status UI).
    """
    # v3.9.72 — checkpoint ⏹ sebelum tahap apapun (Stop saat fase
    # sebelumnya — mis. ⏹ ditekan pas Rincian PO selesai — langsung
    # terasa; dulu harus menunggu varian audit PERTAMA selesai penuh)
    stop_check(stop_event, "audit rekonsiliasi (persiapan)")
    raw = build_audit_input(rekap_so_df, in_detail_df,
                            saldo_awal_map=saldo_awal_map)

    # v3.14 — PARAM ENGINE V2: periode data (diberikan pipeline main.py
    # — deteksiTimestamp IN + fallback kode Nomor; None = deteksi
    # internal, fallback jam sistem = perilaku VBA yang selalu memproses
    # bulan berjalan).
    if period is None:
        period = detect_data_period(in_detail_df)
    if period is None:
        _now = datetime.now()
        period = (_now.year, _now.month)
    try:
        _len_ini, len_lalu = month_lengths(period)
    except (TypeError, ValueError):
        len_lalu = 31
    # Hari referensi "hari ini": bulan data = bulan berjalan → hari ini
    # (PENDING CUT-OFF masih mungkin); bulan lampau/berbeda = TERTUTUP →
    # None (seluruh rentang akhir grup langsung DEVIASI MURNI).
    _now = datetime.now()
    if (int(period[0]), int(period[1])) == (_now.year, _now.month):
        reference_day = _now.day
    else:
        reference_day = None

    # v3.14 — so_lalu_map: observasi SO bulan lalu TERAKHIR per pasangan
    # {(resto, item): (tgl_negatif, SO)} dari frame PRA-filter (SEBELUM
    # _filter_bulan_ini membuang baris negatif — varian Bulan Ini tetap
    # punya baseline tgl 1; kunci RAW pasangan = kunci grup engine).
    so_lalu_map: dict = {}
    if not raw.empty:
        _rt = pd.to_numeric(raw["Tanggal"], errors="coerce")
        _rs = pd.to_numeric(raw["Hasil SO"], errors="coerce")
        for _r, _b, _t, _s in zip(raw["Resto"].astype(str),
                                  raw["Nama Item"].astype(str),
                                  _rt, _rs):
            if pd.isna(_t) or pd.isna(_s) or _t >= 0:
                continue
            _k = (_r, _b)
            _d = int(_t)
            _prev = so_lalu_map.get(_k)
            if _prev is None or _d > _prev[0]:
                so_lalu_map[_k] = (_d, float(_s))

    if not bulan_lalu:
        # v3.10.1 — FIX P1 (bug hunt 1-a): baris bulan lalu dibuang SETELAH
        # basis SO-kemarin dihitung (dulu difilter SEBELUM build_audit_input
        # → SO bulan lalu ikut terbuang → baris PERTAMA bulan berjalan
        # pasangan tanpa baris tgl-1 TANPA basis: ΔSO NaN→0 → Selisih −IN
        # phantom "gantung semu" di varian Bulan Ini, padahal varian PENUH
        # atas baris yang sama menampilkan angka benar). Engine tetap murni
        # bulan berjalan (saldo kumulatif mulai dari baris pertama bulan
        # ini — kontrak mirror LAPORAN_DEVIASI v3.9.27 utuh); yang membawa
        # informasi bulan lalu HANYA kolom basis "Qty SO Kemarin".
        raw = _filter_bulan_ini(raw).reset_index(drop=True)
    # v3.9.72 — checkpoint ⏹ pasca build input (agregasi groupby vektor;
    # Stop saat agregasi tak perlu menunggu engine jalan)
    stop_check(stop_event, "audit rekonsiliasi (input)")
    po_pairs = _po_menunggu_pairs(
        extract_po_pending(po_pending_df), konversi) \
        if po_pending_df is not None else None
    if raw.empty:
        kpi0 = {"rows": 0, "cutoff": 0, "omit": 0, "deviasi_murni": 0,
                "deviasi_qty": 0.0, "ok": 0, "com_minus": 0,
                # v3.14 — KPI V2 (skema konsisten walau kosong)
                "pending": 0, "open_bal": 0, "review": 0}
        # v3.10 — skema konsisten walau kosong (kolom basis baru hadir)
        for c in ("Qty BM Rekap", "Qty SO Kemarin", "Qty Delta SO",
                  "Qty BK", "Qty COM"):
            raw[c] = pd.Series(dtype="float64")
        if po_pairs is not None:
            # skema konsisten walau tanpa data rekap (kolom + kpi PO ada)
            raw["Qty PO Menunggu"] = pd.Series(
                dtype="float64")
            kpi0["dev_murni_po"] = 0
        # v3.12.4 — skema konsisten walau kosong (kolom kode dokumen IN)
        raw["Kode IT/RI"] = pd.Series(dtype="object")
        return raw, kpi0, "tidak ada data rekap SO / IN utk audit"

    # v3.11.5 — KEMBALI KE RUMUS LAMA (user: "kembali ke rumus lama"):
    # swap slot v3.10 ("Qty SO Harian" ← ΔSO) + rename output DIHAPUS —
    # engine menerima raw APA ADANYA: slot "Qty SO Harian" = BM rekap
    # (persis pra-v3.10) → Selisih Harian = BM − Penerimaan Sistem;
    # aturan VALID (SO naik + BM=0 + IN>0) aktif lagi. Kolom basis v3.10
    # (BM Rekap/SO Kemarin/Delta SO) tetap hadir sbg display/bahan COM.
    # v3.14 — ENGINE AUDIT V2: len_lalu (aritmetika hari lintas bulan +
    # baseline tgl 1) · reference_day (PENDING vs DEVIASI rentang akhir)
    # · so_lalu_map (baseline tgl 1 varian Bulan Ini) diteruskan ke
    # build_audit_rekap (lihat docstring-nya utk aturan V2 lengkap).
    audit, kpi = build_audit_rekap(raw, stop_event=stop_event,
                                   len_lalu=len_lalu,
                                   reference_day=reference_day,
                                   so_lalu_map=so_lalu_map)
    if po_pairs is not None:
        _apply_po_menunggu(audit, kpi, po_pairs, stop_event=stop_event)
    # v3.12.4 — kolom 'Kode IT/RI' (nomor dokumen penerimaan — IT/RI/PI)
    # tepat setelah enrich PO Menunggu: per baris ber-IN ≠ 0 saja.
    _apply_kode_it_ri(audit, _kode_it_ri_map(in_detail_df))

    # v3.10 — KOLOM COM (formula kanonik pivot): COM = SO(t−1) + IN −
    # BK − SO(t); NaN bila SO(t) atau basis tak tersedia.
    # Qty BK per baris dari bk_map {(resto, barang, tgl)} (loop Python
    # di worker — ≤86k baris, sekali per run).
    # v3.11.10 — FIX (audit 3-a) bug #4: klaim "PERSIS formula pivot —
    # jangan bikin rumus keempat" dipulihkan (probe_fn_audit_com: 2/6
    # baris BEBEK beda, kini parity). Basis COM ≠ "Qty SO Kemarin"
    # (kolom display/ΔSO TETAP ffill-last-observed — kontrak v3.10.1
    # utuh): basis hanya dari baris yang BENAR-BENAR merekam SO (tanpa
    # ffill — BEBEK t4: baris t3 ber-IN tanpa SO → NaN; dulu ffill
    # SO(2) → 10 ≠ popup); Tanggal 1 → SA(1) / SO penutupan bulan lalu
    # (nilai "Qty SO Kemarin" baris tgl-1 = anchor SA / ffill
    # penutupan — persis basis kanonik). SO(t) tak direkam → NaN
    # (undefined ≠ 0 — tak memicu KPI com_minus, tampil '-' / blank di
    # export).
    # v3.11.59 — FIX BUG 3 (MEDIUM-HIGH): semantik basis t>1 diselaraskan
    # PENUH ke kanonik _compute_com_series (deviasi_popup — satu-satunya
    # rumus presence-aware bersama com_analisa). Basis lama = SO BARIS
    # AKTIVITAS PASANGAN SENDIRI sebelumnya (raw shift per-pasangan) —
    # padahal kolom kanonik = UNION tanggal aktivitas SEMUA pasangan.
    # Bukti eksekusi: SO(2)=100, IN(5)=50, SO(5)=90 (+ pasangan lain
    # merekam tgl 3&4) → basis lama SO(2) → COM(5)=+60; kanonik: kolom
    # global sebelum tgl 5 = TGL 4, pasangan TIDAK merekam SO di situ →
    # COM(5) ABSENT/NaN (pivot lama malah −40 — 3 nilai beda dari input
    # sama). Kini basis t>1 = SO pasangan HANYA bila pasangan merekam
    # SO persis di TANGGAL AKTIVITAS GLOBAL tepat sebelumnya (bila tidak
    # → NaN, TIDAK mencari SO yang lebih lama); jangkar t=1 ("Qty SO
    # Kemarin" = SA 42.17 / penutupan bulan lalu, v3.10.1) & baris
    # bulan-lalu-tanpa-COM (t<0 → NaN) TETAP utuh.
    _so = pd.to_numeric(audit["Hasil SO"], errors="coerce")
    _prev = pd.to_numeric(audit["Qty SO Kemarin"], errors="coerce")
    _in_sys = pd.to_numeric(audit["Penerimaan Sistem"],
                            errors="coerce").fillna(0.0)
    _bk_vals = []
    # v3.11.35 — kunci bk_map DINORMALISASI kanonik paritas append1.py
    # (sumber bk_map). Sebelumnya .astype(str) RAW → mismatch → Qty BK
    # NaN → COM = SO_prev + IN − 0 − SO wrong.
    _r = audit["Resto"].map(norm_nama_resto_key)
    _b = audit["Nama Item"].map(norm_nama_barang_key)
    _t = pd.to_numeric(audit["Tanggal"], errors="coerce") \
        .astype("float64")
    if bk_map:
        for r, b, t in zip(_r, _b, _t):
            key = (r, b, int(t)) if pd.notna(t) else None
            _bk_vals.append(
                float(bk_map[key]) if key is not None and key in bk_map
                else np.nan)
    else:
        _bk_vals = [np.nan] * len(audit)
    _bk = pd.Series(_bk_vals, index=audit.index, dtype="float64")
    audit["Qty BK"] = _bk
    _pid = np.cumsum(((_r != _r.shift(1)) | (_b != _b.shift(1)))
                     .to_numpy(dtype="int64"))
    # KOLOM GLOBAL (v3.11.59 — mirror col_keys _compute_com_series):
    # union TANGGAL AKTIVITAS semua pasangan (frame audit = union
    # baris aktivitas), urut KRONOLOGIS (negatif dulu hari naik — kunci
    # _k1/_k2 build_audit_input / tgl_chrono_key: −25=25• < −31=31• < 1).
    _du = _t.dropna().unique().tolist()
    _du.sort(key=lambda v: (0, -v) if v < 0 else (1, v))
    _g_prev = {d: _du[j - 1] for j, d in enumerate(_du) if j > 0}
    # Peta SO TERCATAT per (pasangan, tanggal) — baris ADA ≠ nilai 0
    # (Hasil SO notna); duplikat (pasangan, tanggal) — drift ejaan RAW
    # yang melebur ke satu kunci kanonik — dijumlahkan defensif
    # (mirror aggfunc="sum" pivot kanonik).
    _so_at: dict = {}
    for _p, _d, _s in zip(_pid, _t, _so):
        if pd.notna(_d) and pd.notna(_s):
            _k = (_p, _d)
            _so_at[_k] = _so_at.get(_k, 0.0) + float(_s)
    # Basis t>1: SO pasangan di tanggal aktivitas global TEPAT sebelum
    # t — HANYA bila pasangan merekam SO persis di tanggal itu (miss →
    # NaN, tidak ffill ke SO yang lebih lama).
    _g = _t.map(_g_prev)
    _prev_com = pd.Series(
        [_so_at.get((_p, _gvi), np.nan) if pd.notna(_gvi) else np.nan
         for _p, _gvi in zip(_pid, _g)],
        index=audit.index, dtype="float64")
    # t=1: jangkar SA(1) / SO penutupan bulan lalu = "Qty SO Kemarin"
    # baris tgl-1 (v3.10.1 utuh); t<0 / t NaN: tanpa COM (perilaku lama).
    _prev_com = _prev_com.mask(_t == 1, _prev)
    _prev_com = _prev_com.where(_t.notna() & (_t >= 1))
    _com = (_prev_com + _in_sys - _bk.fillna(0.0) - _so).astype("float64")
    _com = _com.where(_so.notna() & _prev_com.notna(), np.nan)
    audit["Qty COM"] = _com
    # NaN AMAN utk KPI: NaN < 0 = False → baris tanpa basis/SO(t) tak
    # dihitung com_minus; frame tanpa COM sama sekali → 0 (tanpa crash).
    kpi["com_minus"] = int((_com < 0).sum())

    # v3.9.72 — checkpoint ⏹ pasca engine (varian kedua tak perlu mulai
    # bila Stop sudah masuk — engine dipanggil 2× per run)
    stop_check(stop_event, "audit rekonsiliasi (perkaya PO menunggu selesai)")
    n_so = int(pd.to_numeric(raw["Hasil SO"], errors="coerce")
               .notna().sum())
    n_in = int((pd.to_numeric(audit["Penerimaan Sistem"], errors="coerce")
                .fillna(0) != 0).sum())
    cakupan = "incl. bulan lalu" if bulan_lalu else "bulan berjalan saja"
    # v3.14 — desc menyebut engine V2 + hari referensi (transparansi
    # status PENDING CUT-OFF vs DEVIASI MURNI rentang akhir).
    _ref_txt = (f"hari ini tgl {reference_day}" if reference_day
                else "bulan tertutup")
    desc = (f"Data app (rekap SO + BM + IN 42.05/32.24/99.01 "
            f"{cakupan}) · "
            f"{len(raw):,} baris · {raw['Resto'].nunique()} resto · "
            f"SO {n_so:,} · IN {n_in:,} · "
            f"basis selisih: BM rekap (BM − IN)"
            f" · engine V2 cut-off {MAX_CUTOFF_DAYS} hari "
            f"(referensi: {_ref_txt})"
            f" · COM minus {kpi.get('com_minus', 0):,}")
    if po_pairs:
        _tot_po = sum(q for v in po_pairs.values()
                      for _n, q, _s, _u in v)
        if konversi is not None:
            # v3.9.31 — qty terkonversi satuan terkecil + hitungan
            # baris PO yg tak terkonversi (transparansi fallback)
            _n_unc = sum(1 for v in po_pairs.values()
                         for _n, _q, _s, u in v if u)
            _qty_txt = f"{_fmt_qty(_tot_po)} qty sat. terkecil"
            if _n_unc:
                _qty_txt += f", {_n_unc} tdk terkonversi"
        else:
            _qty_txt = f"{_fmt_qty(_tot_po)} qty"
        desc += (f" · PO menunggu {len(po_pairs)} pasangan "
                 f"({_qty_txt})")
    return audit, kpi, desc
