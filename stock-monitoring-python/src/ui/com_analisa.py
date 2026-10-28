"""
com_analisa.py — analisa "COM Tinggi"/"COM Rendah" di kolom CEK tab
Deviasi GR/PCS (v3.11.7; v3.11.8 + arah RENDAH).

User: "coba eksplore terkait COM yang ditambahkan di kolom CEK. Misal H=7
maka coba hitung selisih antara COM tanggal 1 dan ACR tgl 1, hitung
tanggal 2, 3 sampai 6. Misal ternyata selisih COM di tanggal 7 dengan
ACR > dari selisih median nya nah tambahkan analisa COM Tinggi. COM itu
maksudnya pemakaian aktual di resto sedangkan ACR itu pemakaian di
sistem." (v3.11.8: "enggak hanya com tinggi ya com rendah juga masuk
analisa" — d(H) < median → pemakaian tercatat sistem melampaui fisik.)

Semantik per pasangan (Nama Barang × NAMA RESTO) pada tanggal analisa H:

    d(t) = COM(t) − ACR(t)
    COM(t) = pemakaian aktual resto   — formula identik baris
              "6.PEMAKAIAN (COM)" tab 📋 Laporan Deviasi / pivot mode
              Tanggal:
              com(1)  = SALDO AWAL + IN(1) − BK(1) − SO(1)  (SA pair bila ada)
              com(t)  = SO(t−1) + IN(t) − BK(t) − SO(t)
    ACR(t) = pemakaian sistem (JENIS "9.ACR" — penjualan)

COM dan ACR seharusnya hampir sama; selisihnya stabil kecil per pasangan.
Bila d(H) MELAMPAUI median historis pasangan itu sendiri (median d(t)
utk t = 1..H−1) → pemakaian fisik melampaui pemakaian tercatat sistem →
pemicu deviasi stok → segmen "COM Tinggi (+x)" di teks CEK (x = selisih
di atas median). Bila d(H) JAUH DI BAWAH median (v3.11.8) → sistem
mencatat pemakaian LEBIH BESAR dari fisik → segmen "COM Rendah (−x)"
(x = selisih di bawah median). Satu pasangan hanya bisa memicu SATU
arah (d(H) > median XOR d(H) < median; sama persis dgn median → normal,
tak berlabel).

VALIDITAS (anti label palsu di data sparse — bukti v3.9.27: SO resto tak
selalu direkam tiap hari; tanpa SO tercatat di KEDUA ujung, com(t) tak
bisa dihitung bermakna):
  - t ≥ 2      : baris 1.SO ADA di t−1 DAN t (baris ADA ≠ nilai 0 —
                 pivot fill 0 tidak membedakan keduanya, makanya presence
                 dihitung terpisah);
  - t = 1      : baris 1.SO ADA di 1 DAN (SALDO AWAL ada ATAU 1.SO ada
                 di kolom kronologis terakhir bulan lalu — keduanya
                 basis sah saldo awal hari-1; tanpa keduanya com(1) tak
                 bermakna);
  - tanggal    : H sendiri harus valid (SO kemarin & hari ini tercatat)
                 — pasangan ber-SO(H) kosong (tampil '-') TIDAK diberi
                 label (jujur, tak terverifikasi);
  - median     : minimal 3 hari sampel valid di 1..H−1 — kurang dari itu
                 tak berlabel (statistik tipis, pola degrade repo).

Perbandingan BERTANDA (bukan absolut): d(H) > median memicu "COM
Tinggi" (pemakaian aktual di atas sistem); d(H) < median memicu
"COM Rendah" (v3.11.8 — sistem mencatat pemakaian lebih besar dari
fisik; selisih di bawah median). Tanpa margin/ambang tambahan
(spesifikasi user).

Konsumsi: deviasi_view._compute_pivot — segmen CEK tanggal analisa H.
Pure pandas (thread-safe — dipakai worker view GR & PCS). Cache DUA
lapis: matriks per IDENTITAS objek data (H-independen — ganti H tak
menghitung ulang pivot; pola _CACHE po_keterangan) + hasil per
(identitas data, h) — pemanggilan berulang (refresh filter, render
GR+PCS bersamaan via SharedPivotCache) tinggal lookup.
"""
import numpy as np
import pandas as pd

COM_TINGGI_LABEL = "COM Tinggi"
COM_RENDAH_LABEL = "COM Rendah"   # v3.11.8 — arah bawah median

# Median dipercaya bila ≥3 hari sampel valid (rekomendasi desain v3.11.7
# — di bawah itu statistik terlalu tipis utk membedakan blip vs anomali).
_MIN_VALID_DAYS = 3

_JENIS = ("SALDO AWAL", "1.SO", "4.IN", "8.BARANG KELUAR", "9.ACR")

# Cache matriks (H-independen) per identitas objek data.
_CACHE: dict = {"data": None, "mat": None}
# Cache hasil per (identitas data, h).
_RES: dict = {"data": None, "h": None, "map": {}}


def _chrono(t) -> tuple:
    """Kunci kronologis lintas bulan — konvensi satu app (po_keterangan
    / export_sheets): bulan-lalu (negatif) urut hari naik lalu bulan
    berjalan; t=−25 (hari ke-25 lalu) < t=−31 (hari terakhir lalu) < t=1."""
    return (0, -t) if t < 0 else (1, t)


def _closing_so(so: pd.DataFrame, so_pres: pd.DataFrame,
                col_keys) -> pd.Series:
    """v3.11.10 — FIX (audit 3-a) bug #2: SO penutupan per pasangan =
    nilai SO di kolom negatif kronologis TERAKHIR yang MEREKAM 1.SO
    pasangan itu (NaN bila pasangan tak pernah merekam SO bulan lalu) —
    basis sah com(1) tanpa baris SALDO AWAL. Kunci kalender terakhir
    bisa hanya ber-BM/IN tanpa 1.SO (probe_com_analisa BEBEK: −30
    ber-BM, penutupan nyata −28 ber-SO 40 → com(1) = 10, bukan −30)."""
    neg = [c for c in col_keys if int(c) < 0]
    out = pd.Series(np.nan, index=so.index)
    if not neg:
        return out
    sv = so[neg].to_numpy(dtype="float64")
    sp = so_pres[neg].to_numpy(dtype=bool)
    has = sp.any(axis=1)
    # kolom terakhir (dari kanan) yang True per baris = penutupan
    idx = sp.shape[1] - 1 - np.argmax(sp[:, ::-1], axis=1)
    out.loc[has] = sv[np.arange(sv.shape[0]), idx][has]
    return out


def _build_matrices(data: pd.DataFrame):
    """Matriks per (Nama Barang × NAMA RESTO) × tanggal kronologis:
    so / in / bk / acr (nilai, fill 0) + so_pres / sa_pres (presence —
    baris ASLI ada, membedakan 'tercatat 0' dari 'tidak direkam').

    Formula com identik _compute_com_matrix laporan_deviasi_view
    (audit 19-b #2: SALDO AWAL ditempel ke basis com(1) pair)."""
    cols = set(getattr(data, "columns", []))
    if not {"Nama Barang", "NAMA RESTO", "JENIS", "Tanggal", "NILAI"} <= cols:
        return None
    d = data[data["JENIS"].astype(str).isin(_JENIS)].copy()
    if d.empty:
        return None
    d["_tgl"] = pd.to_numeric(d["Tanggal"], errors="coerce")
    d = d.dropna(subset=["_tgl"])
    if d.empty:
        return None
    d["_tgl"] = d["_tgl"].astype("int64")
    d["_v"] = pd.to_numeric(d["NILAI"], errors="coerce").fillna(0.0)

    idx = ["Nama Barang", "NAMA RESTO", "JENIS"]
    try:
        piv = d.pivot_table(
            index=idx, columns="_tgl", values="_v",
            aggfunc="sum", fill_value=0)
        # presence: jumlah baris asli per sel (0 = fill, bukan baris).
        pres = d.pivot_table(
            index=idx, columns="_tgl", values="_v",
            aggfunc="size", fill_value=0)
    except Exception:  # noqa: BLE001 — pivot gagal → fitur mati sopan
        return None
    if piv.empty:
        return None

    col_keys = sorted(piv.columns.tolist(), key=_chrono)
    pairs = piv.index.droplevel("JENIS").unique()

    def _mat(jenis: str, presence: bool = False,
             fill: bool = True) -> pd.DataFrame:
        try:
            sub = piv.xs(jenis, level="JENIS")
            sub_pres = pres.xs(jenis, level="JENIS")
        except KeyError:
            sub = pd.DataFrame()
            sub_pres = pd.DataFrame()
        out = (sub.reindex(index=pairs, columns=col_keys)
               .astype("float64"))
        out_pres = (sub_pres.reindex(index=pairs, columns=col_keys)
                    .fillna(0).astype(bool))
        if presence:
            return out_pres
        # v3.11.10 — fill=False: TANPA fillna (NaN = tanpa baris asli) —
        # dipakai utk SALDO AWAL mentah (bedakan 'SA ada nilainya 0'
        # dari 'SA tidak ada'; komentar lama menuliskan 'tanpa fillna'
        # tapi _mat selalu fillna(0) → fallback mati — audit 3-a bug #2)
        return out.fillna(0.0) if fill else out

    so = _mat("1.SO")
    in_m = _mat("4.IN")
    bk = _mat("8.BARANG KELUAR")
    acr = _mat("9.ACR")
    so_pres = _mat("1.SO", presence=True)
    sa_pres = _mat("SALDO AWAL", presence=True)

    # com = so_prev + in − bk − so. v3.11.10 — FIX (audit 3-a) bug
    # #1/#2 (probe_com_analisa): com(t) hanya bermakna bila SO tercatat
    # di KEDUA ujung — basis = nilai SO kolom kronologis SEBELUMNYA bila
    # 1.SO pasangan tercatat di kolom itu (bukan dibaca 0); com(1) =
    # SALDO AWAL(1) bila ada, else SO penutupan (kolom negatif terakhir
    # yang MEREKAM SO); sel tanpa SO tercatat → NaN (bukan 0-based
    # garbage — com_gap_map memfilter hari valid via so_pres, dulu
    # median tercemar nilai fill: BEBEK d={−30,2,35,−19,0} → kini
    # {10,2,0}, gap 4 → 6).
    sa_raw = _mat("SALDO AWAL", fill=False)
    so_prev = so.shift(1, axis=1) \
        .where(so_pres.shift(1, axis=1, fill_value=False))
    pos1 = [c for c in col_keys if int(c) == 1]
    if pos1:
        key1 = pos1[0]
        so_prev[key1] = sa_raw[key1].fillna(
            _closing_so(so, so_pres, col_keys))
    com = (so_prev + in_m - bk - so).where(so_pres)

    return {
        "com": com, "acr": acr, "so_pres": so_pres, "sa_pres": sa_pres,
        "col_keys": col_keys,
    }


def com_gap_map(data: pd.DataFrame, h) -> dict:
    """v3.11.8 — peta segmen COM BERSAMA dua arah:
    {(Nama Barang, NAMA RESTO): (sisi, selisih_dari_median)} — sisi
    "tinggi" (d(H) > median; selisih = d(H) − median, positif) atau
    "rendah" (d(H) < median; selisih = median − d(H), positif).
    HANYA pasangan terpicu (d(H) valid; ≥3 hari sampel valid di
    1..H−1). Frame kosong / kolom kurang / h < 4 → peta kosong
    (degrade jujur, mirror po_keterangan). Hasil di-cache per
    (identitas data, h)."""
    if data is None or getattr(data, "empty", True):
        return {}
    try:
        h = int(h)
    except (TypeError, ValueError):
        return {}
    if h < _MIN_VALID_DAYS + 1:
        return {}

    if _CACHE["data"] is not data or _CACHE["mat"] is None:
        _CACHE["mat"] = _build_matrices(data)
        _CACHE["data"] = data
    mat = _CACHE["mat"]
    if not mat:
        return {}
    if (_RES["data"] is data and _RES["h"] == h):
        return _RES["map"]

    com = mat["com"]
    acr = mat["acr"]
    so_pres = mat["so_pres"]
    sa_pres = mat["sa_pres"]
    col_keys = mat["col_keys"]

    pos_cols = [c for c in col_keys if int(c) >= 1]
    if h not in pos_cols:
        _RES.update(data=data, h=h, map={})
        return {}

    # kolom negatif: cukup ADA yang MEREKAM SO utk pasangan ini (basis
    # com(1) = penutupan = kolom negatif kronologis TERAKHIR yang
    # merekam). v3.11.10 — FIX (audit 3-a) bug #1: cek lalu terikat kunci
    # kalender TERAKHIR (bisa hanya ber-BM/IN tanpa 1.SO → hari-1 salah
    # invalid; mirror _com_acr_avg — probe_com_analisa BEBEK n 2 → 3,
    # gap None → ('rendah', 6.0)).
    neg_cols = [c for c in col_keys if int(c) < 0]
    neg_has_so = (so_pres[neg_cols].any(axis=1) if neg_cols
                  else pd.Series(False, index=com.index))

    com_c = com[[c for c in pos_cols if int(c) <= h]]
    acr_c = acr[com_c.columns]
    so_p = so_pres[com_c.columns]
    sa_p = sa_pres.reindex(index=com.index, columns=[c for c in sa_pres.columns
                                                     if int(c) == 1])
    sa1 = sa_p.iloc[:, 0] if (sa_p is not None and not sa_p.empty) \
        else pd.Series(False, index=com.index)

    out: dict = {}
    days = [int(c) for c in com_c.columns]
    for pair in com.index:
        row_com = com_c.loc[pair].to_numpy(dtype="float64")
        row_acr = acr_c.loc[pair].to_numpy(dtype="float64")
        row_so = so_p.loc[pair].to_numpy(dtype=bool)
        # d(t) valid: SO tercatat di t & t−1 (t≥2); t=1: SO(1) & (SA ada
        # atau SO penutupan bulan lalu ada).
        valid = np.zeros(len(days), dtype=bool)
        for j, t in enumerate(days):
            if t == 1:
                ok_prev = bool(sa1.loc[pair]) or bool(neg_has_so.loc[pair])
                valid[j] = row_so[j] and ok_prev
            else:
                valid[j] = (row_so[j]
                            and (t - 1) in days
                            and row_so[days.index(t - 1)])
        if not valid.any():
            continue
        d_all = row_com - row_acr
        # window median: tanggal 1..h−1 yang valid; hari H sendiri diuji.
        idx_h = days.index(h)
        win_mask = valid.copy()
        win_mask[idx_h] = False
        win = d_all[win_mask]
        if int(win_mask.sum()) < _MIN_VALID_DAYS:
            continue
        if not valid[idx_h]:
            continue
        med = float(np.median(win))
        d_h = float(d_all[idx_h])
        # v3.11.8 — DUA ARAH (user: "enggak hanya com tinggi ya com
        # rendah juga masuk analisa"): d(H) > median → pemakaian fisik
        # melampaui sistem ("tinggi", excess positif); d(H) < median →
        # sistem mencatat pemakaian lebih besar dari fisik ("rendah",
        # gap di bawah median dilaporkan positif). Sama persis dgn
        # median → normal, tak berlabel (strict dua sisi — mirror
        # strict > v3.11.7).
        if d_h > med:
            out[(str(pair[0]), str(pair[1]))] = ("tinggi", d_h - med)
        elif d_h < med:
            out[(str(pair[0]), str(pair[1]))] = ("rendah", med - d_h)

    _RES.update(data=data, h=h, map=out)
    return out


def com_tinggi_map(data: pd.DataFrame, h) -> dict:
    """Peta segmen COM Tinggi: {(Nama Barang, NAMA RESTO): selisih di
    atas median (float)} — HANYA pasangan arah TINGGI (back-compat
    v3.11.7; turunan tipis com_gap_map — tanpa hitung ulang)."""
    return {p: d for p, (s, d) in com_gap_map(data, h).items()
            if s == "tinggi"}


def com_rendah_map(data: pd.DataFrame, h) -> dict:
    """v3.11.8 — peta segmen COM Rendah: {(Nama Barang, NAMA RESTO):
    selisih di bawah median (float positif)} — HANYA pasangan arah
    RENDAH (turunan tipis com_gap_map)."""
    return {p: d for p, (s, d) in com_gap_map(data, h).items()
            if s == "rendah"}


def com_tinggi_segment(data: pd.DataFrame, h, nama_barang: str,
                       nama_resto: str) -> str:
    """Label segmen utk SATU (pasangan, H) — dipakai popup/debug:
    'COM Tinggi' bila terpicu arah tinggi, '' lainnya (lookup tipis di
    atas com_tinggi_map — tidak menghitung ulang)."""
    m = com_tinggi_map(data, h)
    if (str(nama_barang), str(nama_resto)) in m:
        return COM_TINGGI_LABEL
    return ""
