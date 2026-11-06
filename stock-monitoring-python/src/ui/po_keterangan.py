"""
po_keterangan.py — Keterangan "Potensi PO belum dibuat" per pasangan
barang × resto.

v3.11.59 — KUNCI PASANGAN KANONIK: semua peta di modul ini (potensi /
Nomor PO 3224 / Nomor+Status PO 3243) ber-kunci `norm_nama_barang_key`
× `norm_nama_resto_key` (UPPER + rapat-spasi + segmen resto setelah
titik — konvensi append1 sejak v3.11.10, paritas fn_audit v3.11.34);
lookup tipis (potensi_po_label_for / po_nomor_for / po_nomor_3243_for)
menormalkan kunci sisi pemanggil dgn helper yang sama.

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

# v3.11.59 — FIX (task 3-e bug 2+3): helper kanonik kunci pasangan dari
# pipeline (helpers import-free dari ui — tak ada circular; paritas
# widgets.py yang juga import level-modul). Naik dari lazy import lama
# (resto_from_cabang_po) karena kini dipakai _build_map + 3 peta PO.
from ..pipeline.helpers import (
    norm_nama_barang_key,
    norm_nama_barang_key_series,
    norm_nama_resto_key,
    norm_nama_resto_key_series,
    resto_from_cabang_po,
)

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

    # v3.11.59 — FIX (task 3-e bug 2, P1 diakui CHANGELOG v3.11.35 "Yang
    # TIDAK di-fix"): kunci pasangan KANONIK di KEDUA sisi. Dulu core
    # (data append1 — ejaan kanonik sejak v3.11.10) dicocokkan dgn
    # in_detail RAW (ejaan file 32.24/99.01) → pasangan ber-drift case/
    # whitespace ("Air Mineral 600ML" vs "AIR MINERAL 600ML") MISS di
    # item_3224/in32/in99 → 3224 dianggap 0 → label "Potensi PO belum
    # dibuat" MENYALA PALSU. norm_nama_*_key_series dipakai TANPA
    # astype(str) dulu (paritas append1: float utuh 100383.0 → "100383",
    # bukan "100383.0"; NA → sentinel sama di kedua sisi). Kunci peta
    # OUTPUT pun kanonik — pemanggil (deviasi_view / details_popup /
    # saldo_minus_view) memakai nilai data yang sama-sama kanonik.
    core = pd.DataFrame({
        "_b": norm_nama_barang_key_series(data["Nama Barang"]),
        "_r": norm_nama_resto_key_series(data["NAMA RESTO"]),
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
    # v3.11.59 — FIX (task 3-e bug 2): kunci KANONIK (dibangun dari ejaan
    # RAW file 32.24) supaya cocok dgn core["_b"] kanonik di isin bawah
    # (dulu RAW × kanonik → scope item-level miss utk pasangan drift).
    item_3224 = frozenset(norm_nama_barang_key_series(
        in_detail.loc[_si.str.startswith("32.24"),
                      "Nama Barang"]).tolist())
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
    # v3.11.59 — FIX (task 3-e bug 2): kunci KANONIK (dulu RAW — drift
    # ejaan vs core membuat in32/in99 miss → 3224/9901 dianggap 0 →
    # label potensi palsu utk pasangan ber-drift).
    det = pd.DataFrame({
        "_b": norm_nama_barang_key_series(in_detail["Nama Barang"]),
        "_r": norm_nama_resto_key_series(in_detail["NAMA RESTO"]),
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
    (lookup tipis di atas potensi_po_map — tidak menghitung ulang).
    v3.11.59 — kunci lookup KANONIK (paritas _build_map: peta kini
    ber-kunci norm_nama_*; pemanggil deviasi_popup meneruskan nama dari
    data append1 yang sudah kanonik — norm idempoten)."""
    try:
        ti = int(float(tanggal))
    except (TypeError, ValueError):
        return ""
    tgls = potensi_po_map(data, in_detail).get(
        (norm_nama_barang_key(nama_barang),
         norm_nama_resto_key(nama_resto)))
    if tgls and ti in tgls:
        return POTENSI_PO_LABEL
    return ""


def po_nomor_map(in_detail) -> dict:
    """v3.11.40 — peta Nomor PO dari file 32.24 per (barang, resto, tgl).

    {(Nama Barang, NAMA RESTO, Tanggal): "PO-001, PO-002, ..."} — Nomor PO
    unik (di-dedup + urut) dari baris in_detail ber-SOURCE IN '32.24'
    (file 3224 — Rincian Penerimaan Barang; kolom 'Nomor PO' hasil rename
    'Nomor # PO' fn_3224). in_detail None/kosong/tak ber-Nomor PO → {}.
    v3.11.59 — kunci (barang, resto) KANONIK norm_nama_* (dulu RAW
    astype(str) — drift ejaan vs pemanggil kanonik → Nomor PO kosong).

    Dipakai kolom 'KETERANGAN PO' popup details (tab Pivot) — user: "Pop up
    keterangan PO di pivot tabel kok gak muncul? itu ambil dari file 3224
    keterangan PO kalau gak salah". Label potensi PO belum dibuat sering
    KOSONG karena kondisi ketat (BM>0 + SO naik + 3224=0 + 9901=0 + tanggal
    terverifiable); Nomor PO 3224 SELALU tersedia bila ada penerimaan →
    kolom kini informatif (menampilkan PO yg tercatat di Accurate).

    Catatan: Nomor PO muncul ⇒ 3224 penerimaan > 0 ⇒ kondisi '3224=0' label
    potensi TIDAK terpenuhi (kedua info saling eksklusif per tanggal — popup
    menampilkan SALAH SATU: Nomor PO bila ada penerimaan 3224, label potensi
    bila 3224=0 dan kondisi lain terpenuhi, kosong bila keduanya tidak)."""
    if in_detail is None or getattr(in_detail, "empty", True):
        return {}
    cols = set(getattr(in_detail, "columns", []))
    if not {"Nama Barang", "NAMA RESTO", "Tanggal", "SOURCE IN"} <= cols:
        return {}
    if "Nomor PO" not in cols:
        return {}
    # v3.11.59 — FIX (task 3-e bug 3): kunci KANONIK (dulu RAW astype(str)
    # — "Air Mineral  600ML" file ≠ "AIR MINERAL 600ML" pemanggil →
    # fallback Nomor PO 3224 kosong utk pasangan drifted).
    det = pd.DataFrame({
        "_b": norm_nama_barang_key_series(in_detail["Nama Barang"]),
        "_r": norm_nama_resto_key_series(in_detail["NAMA RESTO"]),
        "_t": pd.to_numeric(in_detail["Tanggal"], errors="coerce"),
        "_s": in_detail["SOURCE IN"].astype(str).str.strip(),
        "_p": in_detail["Nomor PO"].astype(str).str.strip(),
    }).dropna(subset=["_t"])
    mask = (det["_s"].str.startswith("32.24")
            & (det["_p"] != "")
            & (det["_p"].str.lower() != "nan"))
    det = det[mask]
    if det.empty:
        return {}
    det = det.assign(_t=lambda d: d["_t"].astype("int64"))
    out: dict = {}
    for (b, r, t), grp in det.groupby(["_b", "_r", "_t"])["_p"]:
        pos = sorted(set(grp.tolist()))
        out[(b, r, int(t))] = ", ".join(pos)
    return out


def po_nomor_for(in_detail, nama_barang: str, nama_resto: str,
                 tanggal) -> str:
    """Nomor PO 3224 utk SATU (pasangan, tanggal) — dipakai popup (lookup
    tipis di atas po_nomor_map). '' bila tak ada penerimaan 3224 / Nomor PO
    kosong / in_detail None. v3.11.59 — kunci lookup KANONIK (paritas
    po_nomor_map)."""
    try:
        ti = int(float(tanggal))
    except (TypeError, ValueError):
        return ""
    return po_nomor_map(in_detail).get(
        (norm_nama_barang_key(nama_barang),
         norm_nama_resto_key(nama_resto), ti), "")


def po_nomor_map_3243(rincian_po_df) -> dict:
    """v3.11.41 — peta Nomor PO dari file 32.43 (Rincian Pesanan Pembelian)
    per pasangan (barang, resto), TANPA filter tanggal (Opsi A — user:
    "tampilkan SEMUA PO utk pasangan bulan ini" — semua Nomor # unik dari
    3243 utk pasangan itu, tidak peduli Tanggal PO).

    {(Nama Barang, NAMA RESTO): "PO-001, PO-002, ..."} — Nomor PO unik
    (di-dedup + urut) dari baris rincian_po_df. NAMA RESTO diturunkan dari
    kolom 'Cabang PO' via ``resto_from_cabang_po`` ("1370.MLGPAR" →
    "MLGPAR" — logika bersama pipeline fn_audit PO Menunggu + UI
    rincian_po_view). rincian_po_df None/kosong/tak ber-Nomor # → {}.

    Dipakai kolom 'KETERANGAN PO' popup details (tab Pivot) — Opsi A:
    prioritas NOMOR PO dari 3243 (PO itu sendiri — lebih lengkap: semua
    PO termasuk yg belum diterima / "Menunggu diproses"); fallback ke
    po_nomor_map (3224 — PO tautan saat penerimaan, bisa miss bila PO
    belum ditautkan saat terima) bila 3243 tidak tersedia; lalu label
    'Potensi PO belum dibuat' bila keduanya tidak ada.

    3243 vs 3224 (analisa mendalam — user: "Nomor PO dan keterangan dari
    file 3243 harusnya coba cek mendalam"):
    - 3224 = Rincian Penerimaan Barang (RI diterima). Kolom 'Nomor # PO'
      → Nomor PO. Hanya muncul bila penerimaan SUDAH terjadi DAN PO
      ditautkan ke RI. Bisa KOSONG bila terima tanpa PO / PO belum
      ditautkan saat terima.
    - 3243 = Rincian Pesanan Pembelian (PO itu sendiri). Kolom 'Nomor #'
      = Nomor PO. SELALU ada (semua PO yg pernah dibuat, termasuk yg
      belum diterima / Menunggu). Punya juga 'Keterangan PO' + 'Status
      Pesanan Pembelian'.
    → 3243 lebih lengkap & relevan utk "Nomor PO" popup.

    v3.11.59 — kunci (barang, resto) KANONIK: norm_nama_barang_key(b) +
    norm_nama_resto_key(resto_from_cabang_po(cab)) — dulu RAW astype(str)
    ("1370.mlgpar" → "mlgpar" ≠ "MLGPAR" milik pemanggil kanonik
    details_popup/saldo_minus_view → Nomor/Status PO kosong utk pasangan
    drifted; contoh nyata v3.11.34: "Air Mineral  600ML" @ "1370.mlgpar").
    """
    if rincian_po_df is None or getattr(rincian_po_df, "empty", True):
        return {}
    cols = set(getattr(rincian_po_df, "columns", []))
    if not {"Nama Barang", "Cabang PO", "Nomor #"} <= cols:
        return {}
    # resto_from_cabang_po kini import level-modul (v3.11.59 — lihat
    # kepala modul; helpers import-free dari ui, tak ada circular).
    det = pd.DataFrame({
        # v3.11.59 — FIX (task 3-e bug 3): kunci KANONIK kedua sisi peta —
        # resto: resto_from_cabang_po DULU ("1370.mlgpar" → "mlgpar") lalu
        # norm ("mlgpar" → "MLGPAR"); barang: norm langsung dari ejaan RAW
        # file 32.43. Supaya cocok dgn kunci pemanggil kanonik (data
        # append1). Resto "" (Cabang PO kosong) tetap terbuang mask bawah.
        "_b": norm_nama_barang_key_series(rincian_po_df["Nama Barang"]),
        "_r": norm_nama_resto_key_series(
            rincian_po_df["Cabang PO"].map(resto_from_cabang_po)),
        "_p": rincian_po_df["Nomor #"].astype(str).str.strip(),
    })
    mask = ((det["_p"] != "")
            & (det["_p"].str.lower() != "nan")
            & (det["_r"] != ""))
    det = det[mask]
    if det.empty:
        return {}
    out: dict = {}
    for (b, r), grp in det.groupby(["_b", "_r"])["_p"]:
        pos = sorted(set(grp.tolist()))
        out[(b, r)] = ", ".join(pos)
    return out


def po_nomor_3243_for(rincian_po_df, nama_barang: str,
                      nama_resto: str) -> str:
    """Nomor PO 3244 utk SATU pasangan (barang, resto) — dipakai popup
    (lookup tipis di atas po_nomor_map_3243). '' bila tak ada PO 3243 /
    rincian_po_df None. v3.11.59 — kunci lookup KANONIK (paritas
    po_nomor_map_3243)."""
    return po_nomor_map_3243(rincian_po_df).get(
        (norm_nama_barang_key(nama_barang),
         norm_nama_resto_key(nama_resto)), "")


def po_status_map_3243(rincian_po_df) -> dict:
    """v3.11.42 — peta Status Pesanan Pembelian dari file 32.43 per
    pasangan (barang, resto).

    {(Nama Barang, NAMA RESTO): "Menunggu diproses, Diproses"} — Status
    unik (di-dedup + urut) dari kolom 'Status Pesanan Pembelian'
    rincian_po_df. NAMA RESTO diturunkan dari 'Cabang PO' via
    ``resto_from_cabang_po`` (mirror po_nomor_map_3243). rincian_po_df
    None/kosong/tak ber-Status → {}.

    Dipakai kolom 'Status PO' anak tab "Saldo Sistem Minus" tab 🧮
    Nominal Deviasi (ide J — konteks "minus karena PO belum diterima /
    Menunggu diproses").

    v3.11.59 — kunci (barang, resto) KANONIK (mirror po_nomor_map_3243
    — dulu RAW: pasangan drifted ber-Status PO kosong di saldo_minus_view).
    """
    if rincian_po_df is None or getattr(rincian_po_df, "empty", True):
        return {}
    cols = set(getattr(rincian_po_df, "columns", []))
    if not {"Nama Barang", "Cabang PO", "Status Pesanan Pembelian"} <= cols:
        return {}
    # resto_from_cabang_po kini import level-modul (v3.11.59 — lihat
    # kepala modul; helpers import-free dari ui, tak ada circular).
    det = pd.DataFrame({
        # v3.11.59 — FIX (task 3-e bug 3): kunci KANONIK (mirror
        # po_nomor_map_3243 — norm setelah resto_from_cabang_po).
        "_b": norm_nama_barang_key_series(rincian_po_df["Nama Barang"]),
        "_r": norm_nama_resto_key_series(
            rincian_po_df["Cabang PO"].map(resto_from_cabang_po)),
        "_s": rincian_po_df["Status Pesanan Pembelian"]
                .astype(str).str.strip(),
    })
    mask = ((det["_s"] != "")
            & (det["_s"].str.lower() != "nan")
            & (det["_r"] != ""))
    det = det[mask]
    if det.empty:
        return {}
    out: dict = {}
    for (b, r), grp in det.groupby(["_b", "_r"])["_s"]:
        statuses = sorted(set(grp.tolist()))
        out[(b, r)] = ", ".join(statuses)
    return out
