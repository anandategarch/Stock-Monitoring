"""
po_keterangan.py — Keterangan "Potensi PO belum dibuat" per pasangan
barang × resto.

Keterangan menyala bila SEMUA terpenuhi pada suatu tanggal:
- Scope: SOURCE KIRIMAN pasangan ∈ {Eksternal, Campuran} ATAU nama
  barang muncul di file 32.24 mana pun (internal-only 42.05 murni
  tidak diberi — pemindahan internal tidak butuh PO).
- BARANG MASUK tercatat di rekap resto (JENIS '5.BARANG MASUK' > 0).
- SO NAIK vs SO tercatat TERAKHIR sebelum tanggal itu (t ≥ 2 di
  tengah bulan berjalan berkonvensi basis 0; tanggal tanpa basis
  tercatat — t=1 & blok bulan-lalu — tidak memicu).
- Penerimaan sistem 32.24 = 0 DAN 9901 = 0, dan tanggal TERVERIFIKABEL
  (file RI bulan-lalu hanya membawa 5 hari terakhir → 25•/26• aman).
→ fisik naik & rekap mencatat penerimaan, namun sistem tidak pernah
menerima → besar kemungkinan PO belum dibuat di Accurate.

Konsumsi: segmen CEK deviasi_view (tanggal analisa H) · kolom
"Keterangan PO" deviasi_popup (tab Deviasi GR/PCS) · kolom
"KETERANGAN PO" details_popup (tab Pivot).

Pure pandas (thread-safe utk worker & main-thread); cache dibangun
SEKALI per identitas objek (data, in_detail).
"""
import bisect

import pandas as pd

POTENSI_PO_LABEL = "Potensi PO belum dibuat"

_JENIS_SO = "1.SO"
_JENIS_BM = "5.BARANG MASUK"
# append1 LANGKAH 5b — nilai kolom SOURCE KIRIMAN persis:
# "Internal" (42.05) / "Eksternal" (32.24 & 9901) / "Campuran".
_SRC_EKSTERNAL = ("Eksternal", "Campuran")

_CACHE: dict = {"data": None, "in_detail": None, "map": {}}

# v3.11.1 — jendela import file RI bulan-lalu (fn_3224/fn_4205 mode
# 'lalu': Tanggal >= maxT-4 → hanya 5 hari terakhir FILE yang dibawa
# pipeline) sedangkan rekap lalu 7 hari (−25..−31) → tanggal 25•/26•
# TIDAK TERVERIFIKABEL oleh in_detail (audit 12-b bug 3).
_LALU_WINDOW = 4


def _chrono_key(t: int):
    """Kunci kronologis lintas bulan (v3.11.1): bulan-lalu (negatif)
    diurut HARI naik lalu bulan berjalan — t=−25 → (0,25) < t=−26 →
    (0,26) < t=1 → (1,1). Identik _chrono export_sheets / _k1/_k2
    fn_audit (satu konvensi app)."""
    return (0, -t) if t < 0 else (1, t)


def _build_map(data: pd.DataFrame, in_detail) -> dict:
    cols = set(getattr(data, "columns", []))
    if not {"Nama Barang", "NAMA RESTO", "Tanggal", "JENIS", "NILAI"} <= cols:
        return {}
    # v3.11 — KONDISI WAJIB: rincian IN per sumber (SOURCE IN) harus
    # tersedia — tanpa itu "3224 0 dan 9901 0" tak bisa diverifikasi →
    # keterangan TIDAK pernah menyala (pola degrade repo: kondisi tak
    # berlaku utk pemanggil lama/test — mirror RI Balancing v3.9.23).
    _det_cols = set(getattr(in_detail, "columns", [])) \
        if in_detail is not None else set()
    _det_ok = (in_detail is not None and not in_detail.empty
               and {"Nama Barang", "NAMA RESTO", "Tanggal", "Value",
                    "SOURCE IN"} <= _det_cols)
    if not _det_ok:
        return {}

    core = pd.DataFrame({
        "_b": data["Nama Barang"].astype(str),
        "_r": data["NAMA RESTO"].astype(str),
        "_t": pd.to_numeric(data["Tanggal"], errors="coerce"),
        "_j": data["JENIS"].astype(str),
        "_v": pd.to_numeric(data["NILAI"], errors="coerce").fillna(0.0),
    })

    # --- scope pasangan: SOURCE KIRIMAN eksternal/campuran ATAU barang
    # --- pernah muncul di file 32.24 (item-level, semua resto).
    in_scope = pd.Series(False, index=core.index)
    if "SOURCE KIRIMAN" in cols:
        sk = data["SOURCE KIRIMAN"].astype(str).str.strip()
        in_scope |= sk.isin(_SRC_EKSTERNAL)
    item_3224: frozenset = frozenset()
    _si = in_detail["SOURCE IN"].astype(str).str.strip()
    # "32.24" + "32.24 (Bulan Lalu)" — startswith menutup keduanya.
    item_3224 = frozenset(
        in_detail.loc[_si.str.startswith("32.24"),
                       "Nama Barang"].astype(str))
    if item_3224:
        in_scope |= core["_b"].isin(item_3224)

    # --- kandidat: baris BM > 0 (rekap resto mencatat penerimaan) pada
    # --- pasangan scope; agregasi defensif per (pasangan, tgl).
    cand = core[in_scope & (core["_j"] == _JENIS_BM) & (core["_v"] > 0)
                & core["_t"].notna()]
    if cand.empty:
        return {}
    cand = cand.assign(_t=lambda d: d["_t"].astype("int64")) \
        .groupby(["_b", "_r", "_t"], as_index=False)["_v"].sum()

    # --- SO per (pasangan, tgl) — peta lookup + struktur kronologis
    # per pasangan (v3.11.1: basis SO terakhir tercatat sebelum t).
    so_map: dict = {}
    _so = core[(core["_j"] == _JENIS_SO) & core["_t"].notna()]
    if not _so.empty:
        _so = _so.assign(_t=lambda d: d["_t"].astype("int64"))
        for k, x in _so.groupby(["_b", "_r", "_t"])["_v"].sum().items():
            so_map[k] = float(x)
    so_pairs: dict = {}
    for (b, r, t), v in so_map.items():
        so_pairs.setdefault((b, r), []).append((_chrono_key(t), t, v))
    for k, entries in list(so_pairs.items()):
        lst = sorted(entries, key=lambda e: e[0])
        so_pairs[k] = ([e[0] for e in lst], [e[2] for e in lst])

    # --- penerimaan sistem 32.24 / 9901 per (pasangan, tgl) — peta.
    in32: dict = {}
    in99: dict = {}
    det = pd.DataFrame({
        "_b": in_detail["Nama Barang"].astype(str),
        "_r": in_detail["NAMA RESTO"].astype(str),
        "_t": pd.to_numeric(in_detail["Tanggal"], errors="coerce"),
        "_v": pd.to_numeric(in_detail["Value"],
                            errors="coerce").fillna(0.0),
        "_s": in_detail["SOURCE IN"].astype(str).str.strip(),
    }).dropna(subset=["_t"])
    if not det.empty:
        det = det.assign(_t=lambda d: d["_t"].astype("int64"))
        for tag, target in (("32.24", in32), ("99.01", in99)):
            _d = det[det["_s"].str.startswith(tag)]
            if _d.empty:
                continue
            for k, x in _d.groupby(["_b", "_r", "_t"])["_v"].sum().items():
                target[k] = float(x)

    # --- v3.11.1 — cakupan VERIFIABLE sumber 32.24 bulan-lalu: jendela
    # import fn_3224/fn_4205 'lalu' = [maxT−4, maxT] hari file; hari
    # maksimum yang ter-import di in_detail = hari maksimum file.
    # Tanpa baris 32.24-lalu sama sekali (folder/file tak ada) → seluruh
    # blok bulan-lalu tak terverifikasi.
    _si32_lalu = det["_s"].str.startswith("32.24") & (det["_t"] < 0)
    _lalu_max = (int(-det.loc[_si32_lalu, "_t"].max())
                 if bool(_si32_lalu.any()) else None)

    def _lalu_verifiable(ti: int) -> bool:
        if ti >= 0:
            return True
        if _lalu_max is None:
            return False
        d = -ti
        return (_lalu_max - _LALU_WINDOW) <= d <= _lalu_max

    # --- trigger per kandidat: BM ada + SO naik (vs SO terakhir
    # tercatat sebelum t) + tanggal terverifikasi + 3224=0 + 9901=0.
    out: dict = {}
    for bb, rr, tt in zip(cand["_b"], cand["_r"], cand["_t"]):
        ti = int(tt)
        if not _lalu_verifiable(ti):
            continue
        so_t = so_map.get((bb, rr, ti), 0.0)
        ckeys, vals = so_pairs.get((bb, rr), ((), ()))
        i = bisect.bisect_left(ckeys, _chrono_key(ti)) - 1
        if i >= 0:
            so_prev = vals[i]
        elif ti >= 2:
            # tengah bulan berjalan tanpa SO tercatat lebih awal →
            # konvensi arr() 0 (perilaku lama dipertahankan).
            so_prev = 0.0
        else:
            # t=1 / blok bulan-lalu TANPA basis SO tercatat → "SO naik"
            # tak terverifikasi → jangan memicu (degrade — audit 12-b
            # bug 1/2: label palsu di batas bulan).
            continue
        if not so_t > so_prev:
            continue
        if in32.get((bb, rr, ti), 0.0) != 0.0:
            continue
        if in99.get((bb, rr, ti), 0.0) != 0.0:
            continue
        out.setdefault((bb, rr), set()).add(ti)
    return {k: frozenset(v) for k, v in out.items()}


def potensi_po_map(data: pd.DataFrame, in_detail=None) -> dict:
    """Peta keterangan PO: {(Nama Barang, NAMA RESTO): frozenset(Tanggal)}
    — tanggal-tanggal dgn kondisi "Potensi PO belum dibuat" (lihat
    docstring modul). Frame kosong / kolom kurang / in_detail None·kosong·
    tanpa kolom sumber → peta KOSONG (kondisi tak berlaku — "3224 0 dan
    9901 0" tak bisa diverifikasi tanpa rincian IN per sumber; pola
    degrade pemanggil lama/test, mirror RI Balancing v3.9.23). Hasil
    di-cache per identitas (data, in_detail)."""
    if data is None or getattr(data, "empty", True):
        return {}
    if in_detail is None or getattr(in_detail, "empty", True):
        return {}
    if _CACHE["data"] is data and _CACHE["in_detail"] is in_detail:
        return _CACHE["map"]
    out = _build_map(data, in_detail)
    _CACHE["data"] = data
    _CACHE["in_detail"] = in_detail
    _CACHE["map"] = out
    return out


def potensi_po_label_for(data: pd.DataFrame, in_detail, nama_barang: str,
                         nama_resto: str, tanggal) -> str:
    """Label keterangan utk SATU (pasangan, tanggal) — dipakai popup:
    POTENSI_PO_LABEL bila kondisi menyala di tanggal itu, '' lainnya.
    (lookup tipis di atas potensi_po_map — tidak menghitung ulang)."""
    try:
        ti = int(float(tanggal))
    except (TypeError, ValueError):
        return ""
    tgls = potensi_po_map(data, in_detail).get(
        (str(nama_barang), str(nama_resto)))
    if tgls and ti in tgls:
        return POTENSI_PO_LABEL
    return ""
