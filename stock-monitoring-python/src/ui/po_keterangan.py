"""
po_keterangan.py — keterangan PO "Potensi PO belum dibuat" (v3.11).

User: "khusus nama barang yang ada di file 32.24 atau eksternal atau
campuran tambah logika misal BARANG MASUK ada SO naik tapi 3224 0 dan
9901 0 maka tambah keterangan = Potensi PO belum dibuat"

Semantik: pasangan barang×resto yang suplainya EKSTERNAL/CAMPURAN
(penerimaan sistem via 32.24 RI / 9901 pembelian — bukan pemindahan
internal 42.05) yang pada suatu tanggal:
  - BARANG MASUK tercatat di rekap resto (JENIS '5.BARANG MASUK' > 0),
    DAN
  - SO NAIK (SO(t) > SO(t−1); SO(t−1) tak tercatat → 0 — konvensi
    arr() deviasi_view; t=1 → dibandingkan dgn kunci −1 penutupan
    bulan lalu, mirror _day_key deviasi), TAPI
  - penerimaan sistem 32.24 = 0 DAN 9901 = 0 (tak ada dokumen RI/
    mutasi Accurate utk pasangan itu pada tanggal itu)
→ fisik naik & rekap mencatat penerimaan, namun sistem tidak pernah
  menerima → besar kemungkinan PO belum dibuat di Accurate (tanpa PO,
  RI tidak bisa diinput) → keterangan "Potensi PO belum dibuat".

Scope pasangan (siapa yang diberi keterangan):
  - SOURCE KIRIMAN pasangan ∈ {"Eksternal", "Campuran"} (klasifikasi
    append1 LANGKAH 5b dari tag SOURCE IN baris 42.05/32.24/9901 —
    "eksternal atau campuran"), ATAU
  - nama barang muncul di file 32.24 manapun (item-level lintas resto
    — "nama barang yang ada di file 32.24"; termasuk 32.24 Bulan Lalu).
    Internal-only (suplai 42.05 murni) TIDAK diberi keterangan —
    pemindahan internal tidak butuh PO.

Konsumsi:
  - deviasi_view._compute_pivot — segmen CEK pada Tanggal analisa H;
  - deviasi_popup — kolom "Keterangan PO" per baris Tanggal (popup
    tab Deviasi GR/PCS);
  - details_popup (tab Pivot) — kolom "KETERANGAN PO" per baris sumber
    (menggantikan kolom KATEGORI & SOURCE KIRIMAN yang dihapus).

Pure pandas (thread-safe — dipakai worker view & main-thread popup).
Cache: peta dibangun SEKALI per identitas objek (data, in_detail) —
double-click popup berulang / refresh filter dgn data sama tidak
menghitung ulang (pola _PERF_CACHE deviasi_popup; cache MEMEGANG
referensi objek → identitas 'is' aman dari reuse alamat GC).
"""
import pandas as pd

POTENSI_PO_LABEL = "Potensi PO belum dibuat"

_JENIS_SO = "1.SO"
_JENIS_BM = "5.BARANG MASUK"
# append1 LANGKAH 5b — nilai kolom SOURCE KIRIMAN persis:
# "Internal" (42.05) / "Eksternal" (32.24 & 9901) / "Campuran".
_SRC_EKSTERNAL = ("Eksternal", "Campuran")

_CACHE: dict = {"data": None, "in_detail": None, "map": {}}


def _prev_day_key(t: int):
    """Tanggal kunci SO hari SEBELUM ``t`` (konvensi rekap/deviasi):
    t>1 → t−1 · t==1 → −1 (saldo penutupan bulan lalu — mirror
    deviasi_view._day_key(0)) · t<0 → t+1 (hari sebelumnya bulan lalu:
    prev 25• = 24• — urutan kronologis bulan lalu menurun numerik) ·
    t==0/t==−1→None (hari tak ada → SO prev dibaca 0)."""
    if t == 1:
        return -1
    if t > 1:
        return t - 1
    if t < 0:
        p = t + 1
        return p if p != 0 else None
    return None


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

    # --- SO per (pasangan, tgl) — peta lookup.
    so_map: dict = {}
    _so = core[(core["_j"] == _JENIS_SO) & core["_t"].notna()]
    if not _so.empty:
        _so = _so.assign(_t=lambda d: d["_t"].astype("int64"))
        for k, x in _so.groupby(["_b", "_r", "_t"])["_v"].sum().items():
            so_map[k] = float(x)

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

    # --- trigger per kandidat: BM ada + SO naik + 3224=0 + 9901=0.
    out: dict = {}
    for bb, rr, tt in zip(cand["_b"], cand["_r"], cand["_t"]):
        ti = int(tt)
        so_t = so_map.get((bb, rr, ti), 0.0)
        _pk = _prev_day_key(ti)
        so_prev = so_map.get((bb, rr, _pk), 0.0) if _pk is not None else 0.0
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
