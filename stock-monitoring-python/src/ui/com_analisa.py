"""
com_analisa.py — Analisa "COM Tinggi"/"COM Rendah" (segmen CEK tab Deviasi
GR/PCS; dipakai deviasi_view).

Semantik per pasangan (Nama Barang × Nama Resto) di tanggal analisa H:

    d(t) = COM(t) − ACR(t)
    COM(t) = pemakaian aktual resto — com(1) = SALDO AWAL + IN(1) −
              BK(1) − SO(1) (SA pasangan bila ada); com(t) = SO(t−1) +
              IN(t) − BK(t) − SO(t) (formula identik 6.PEMAKAIAN).
    ACR(t) = pemakaian sistem (JENIS "9.ACR").

- d(H) > median d(t), t=1..H−1 → segmen "COM Tinggi (+x)" (pemakaian
  fisik melampaui sistem; x = selisih di atas median); d(H) < median →
  "COM Rendah (−x)". Satu pasangan maksimal SATU arah; tepat sama dgn
  median → tanpa label.
- Ambang persen (min_pct): selisih baru signifikan bila melampaui
  min_pct% × |median| (strict >; default modul 0 = semua selisih; view
  meneruskan nilai spinbox, default 50).
- Validitas (anti label palsu data sparse): SO tercatat di KEDUA ujung
  tiap hari sampel (t=1 boleh SALDO AWAL / SO penutupan bulan lalu); H
  sendiri valid; median butuh ≥ 3 hari sampel valid.
- Pure pandas (thread-safe). Cache dua lapis: matriks H-independen per
  identitas objek data + hasil per (identitas, h, min_pct).
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
# Cache hasil per (identitas data, h, min_pct).
_RES: dict = {"data": None, "h": None, "pct": None, "map": {}}


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


def com_gap_map(data: pd.DataFrame, h, min_pct: float = 0.0) -> dict:
    """v3.11.8 — peta segmen COM BERSAMA dua arah:
    {(Nama Barang, NAMA RESTO): (sisi, selisih_dari_median)} — sisi
    "tinggi" (d(H) > median; selisih = d(H) − median, positif) atau
    "rendah" (d(H) < median; selisih = median − d(H), positif).
    HANYA pasangan terpicu (d(H) valid; ≥3 hari sampel valid di
    1..H−1). Frame kosong / kolom kurang / h < 4 → peta kosong
    (degrade jujur, mirror po_keterangan). Hasil di-cache per
    (identitas data, h, min_pct).

    v3.11.12 — min_pct: AMBANG persen dari |median| (user: "set 50% >
    atau <") — gap wajib MELAMPAUI (min_pct/100) × |median| sebelum
    pasangan diberi label (0 = semua selisih = perilaku lama;
    median 0 → semua gap nonzero; lihat header modul)."""
    if data is None or getattr(data, "empty", True):
        return {}
    try:
        h = int(h)
    except (TypeError, ValueError):
        return {}
    if h < _MIN_VALID_DAYS + 1:
        return {}
    try:
        min_pct = float(min_pct)
    except (TypeError, ValueError):
        min_pct = 0.0
    if not (0.0 <= min_pct <= 10000.0):
        min_pct = 0.0

    if _CACHE["data"] is not data or _CACHE["mat"] is None:
        _CACHE["mat"] = _build_matrices(data)
        _CACHE["data"] = data
    mat = _CACHE["mat"]
    if not mat:
        return {}
    if (_RES["data"] is data and _RES["h"] == h
            and _RES["pct"] == min_pct):
        return _RES["map"]

    com = mat["com"]
    acr = mat["acr"]
    so_pres = mat["so_pres"]
    sa_pres = mat["sa_pres"]
    col_keys = mat["col_keys"]

    pos_cols = [c for c in col_keys if int(c) >= 1]
    if h not in pos_cols:
        _RES.update(data=data, h=h, pct=min_pct, map={})
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
        # v3.11.12 — AMBANG (user: "bisa gak set 50% > atau < COM
        # rendah atau COM tinggi nya?"): gap wajib MELAMPAUI ambang% ×
        # |median| (min_pct=0 → perilaku lama semua-selisih; median 0
        # → ruas kanan 0 → semua gap nonzero; strict > — gap TEPAT di
        # ambang tak memicu).
        _cut = (min_pct / 100.0) * abs(med)
        if d_h > med and (d_h - med) > _cut:
            out[(str(pair[0]), str(pair[1]))] = ("tinggi", d_h - med)
        elif d_h < med and (med - d_h) > _cut:
            out[(str(pair[0]), str(pair[1]))] = ("rendah", med - d_h)

    _RES.update(data=data, h=h, pct=min_pct, map=out)
    return out


def com_tinggi_map(data: pd.DataFrame, h, min_pct: float = 0.0) -> dict:
    """Peta segmen COM Tinggi: {(Nama Barang, NAMA RESTO): selisih di
    atas median (float)} — HANYA pasangan arah TINGGI (back-compat
    v3.11.7; turunan tipis com_gap_map — tanpa hitung ulang; min_pct
    v3.11.12 diteruskan apa adanya)."""
    return {p: d for p, (s, d) in com_gap_map(data, h, min_pct).items()
            if s == "tinggi"}


def com_rendah_map(data: pd.DataFrame, h, min_pct: float = 0.0) -> dict:
    """v3.11.8 — peta segmen COM Rendah: {(Nama Barang, NAMA RESTO):
    selisih di bawah median (float positif)} — HANYA pasangan arah
    RENDAH (turunan tipis com_gap_map; min_pct v3.11.12
    diteruskan)."""
    return {p: d for p, (s, d) in com_gap_map(data, h, min_pct).items()
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
