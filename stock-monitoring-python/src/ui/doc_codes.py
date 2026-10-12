"""
doc_codes.py — Parsing & analisa kode dokumen IN (SHARED, v3.9.23).

Dipakai bersama oleh in_selisih_view (popup Rincian IN + Catatan Audit)
dan deviasi_view (CEK "RI Balancing" kolom utama tab Deviasi GR/PCS).
Sebelumnya helper ini hidup di in_selisih_view.py; diangkat ke modul
sendiri supaya logika bisnis RI Balancing TIDAK diduplikasi (audit
34/37: duplikasi rumus = sumber bug senyap). in_selisih_view tetap
me-re-export nama lama (_doc_code_str/_doc_period/_doc_month/
_ri_balancing) — kompatibel test §29/§30 yang mengimpor dari sana.

Struktur kode dokumen: PREFIKS.TAHUN.BULAN.NOMOR
  "PO.2026.08.00571" / "RI.2026.10.10354" / "IT.2026.09.00123"
(segmen 2 = tahun, segmen 3 = bulan — bulan 1-2 digit, dibandingkan
NUMERIK; "8" == "08").

v3.9.23 (user: "kerjakan poin 6 dan kerjakan semua poin B"):
- CEK "RI Balancing" diangkat ke kolom CEK utama Deviasi GR/PCS
  (dulu hanya di popup Rincian IN);
- Catatan Audit tab Rekap Selisih IN diperkaya catatan otomatis
  (RI Balancing / Nomor Dobel / Selisih IN / BM kosong).
"""
import re

import pandas as pd

# v3.9.19 — struktur kode dokumen: PREFIKS.TAHUN.BULAN.NOMOR
# (mis. "PO.2026.08.00571" / "RI.2026.10.10354" — 2026 tahun, 08/10
# bulan). FIX 35-c1: bulan boleh 1-2 digit ("RI.2026.8.10354" non-
# zero-pad dulu gagal pola → CEK senyap kosong) + validasi 1..12.
_DOC_CODE_RE = re.compile(r"^[A-Za-z]+\.(\d{4})\.(\d{1,2})\.")


def _doc_code_str(code) -> str:
    """Kode dokumen → teks aman (None/pd.NA/NaN → "")."""
    if code is None:
        return ""
    try:
        if pd.isna(code):
            return ""
    except (TypeError, ValueError):
        pass
    return str(code).strip()


def _doc_period(code):
    """FIX 35-c1 — (tahun, bulan) dari kode dokumen
    "PO.2026.08.00571" → (2026, 8); None bila pola tidak cocok /
    bulan di luar 1..12 ("RI.2026.13.1" → None). Bulan 1-2 digit
    dibandingkan NUMERIK (8 == 08)."""
    m = _DOC_CODE_RE.match(_doc_code_str(code))
    if not m:
        return None
    try:
        year = int(m.group(1))
        month = int(m.group(2))
    except ValueError:
        return None
    if not 1 <= month <= 12:
        return None
    return (year, month)


def _doc_month(code) -> "int | None":
    """Bulan dari kode dokumen PO.2026.08.00571 → 8; None bila pola
    tidak cocok / nilai kosong (FIX 35-c1: bulan 1-2 digit + sanity
    1..12 via _doc_period)."""
    period = _doc_period(code)
    return period[1] if period is not None else None


def _ri_balancing(nomor, nomor_po) -> str:
    """v3.9.19 — keterangan CEK popup Rincian IN: bulan Nomor (dokumen
    penerimaan RI) ≠ bulan Nomor PO → "RI Balancing" (RI dibuat beda
    bulan dari pesanannya — entries balancing; contoh user: PO Agustus
    ↔ RI Oktober). FIX 35-c1 (RISK C3+C4): bandingkan PERIODE PENUH
    (tahun, bulan) — "RI.2027.08" vs "PO.2026.08" (bulan sama, tahun
    beda) kini di-flag: periode beda = entries balancing; dulu tahun
    diabaikan → lolos senyap. Bulan 1-2 digit cocok numerik
    ("RI.2026.8" == "PO.2026.08"). Hanya berlaku utk dokumen RI
    (Nomor berprefiks "RI." — dokumen PI 9901 adalah invoice
    pembelian, bukan balancing)."""
    n = _doc_code_str(nomor)
    if not n.upper().startswith("RI."):
        return ""
    p_ri = _doc_period(n)
    p_po = _doc_period(nomor_po)
    if p_ri is None or p_po is None or p_ri == p_po:
        return ""
    return "RI Balancing"


def ri_balancing_docs(in_detail: pd.DataFrame | None):
    """v3.9.23 — daftar dokumen IN "RI Balancing" per pasangan
    (Nama Barang, NAMA RESTO) dari frame detail IN per-dokumen.

    Return dict {(barang, resto): [nomor, ...]} — nomor dokumen RI
    yang bulannya ≠ bulan Nomor PO-nya (urut, unik). Frame in_detail
    berasal dari query_in: kolom NAMA RESTO · Nama Barang · Tanggal ·
    Value · Nomor · Nomor PO · SOURCE IN · JENIS (per dokumen × item —
    pemetaan Nomor↔Nomor PO BERSIH, tidak ter-campur seperti kolom
    gabungan di frame final). Dipakai:
    - deviasi_view → CEK "RI Balancing" kolom utama (pasangan
      ber-dokumen balancing TERFLAG);
    - in_selisih_view → Catatan Audit (nomor dokumen dituliskan).
    """
    out: dict = {}
    if in_detail is None or getattr(in_detail, "empty", True):
        return out
    if not {"Nomor", "Nomor PO", "Nama Barang", "NAMA RESTO"} <= set(
            getattr(in_detail, "columns", [])):
        return out
    for nomor, nomor_po, b, r in zip(in_detail["Nomor"],
                                     in_detail["Nomor PO"],
                                     in_detail["Nama Barang"],
                                     in_detail["NAMA RESTO"]):
        if _ri_balancing(nomor, nomor_po) == "":
            continue
        key = (str(b), str(r))
        n = _doc_code_str(nomor)
        if n and n not in out.setdefault(key, []):
            out[key].append(n)
    return out


def duplicated_doc_numbers(in_detail: pd.DataFrame | None) -> dict:
    """v3.9.23 (poin B — catatan audit) — deteksi NOMOR DOBEL pada
    detail IN per dokumen: nomor dokumen sama muncul >1 baris untuk
    (Resto, Barang) PASANGAN YANG SAMA = input ganda (double-entry /
    sheet kembar — gejala RISK R2 audit 37-a: fn_9901 membaca semua
    sheet → IN terhitung 2×).

    Satu dokumen yang sah memuat >1 item berbeda TIDAK terflag
    (grouping per pasangan barang); begitu pula dokumen yang berisi
    item yang sama di resto lain. Return dict
    {(barang, resto): {nomor: jumlah_baris}} hanya utk pasangan yang
    punya nomor dobel.
    """
    out: dict = {}
    if in_detail is None or getattr(in_detail, "empty", True):
        return out
    cols = {"Nomor", "Nama Barang", "NAMA RESTO"}
    if not cols <= set(getattr(in_detail, "columns", [])):
        return out
    d = in_detail[in_detail["Nomor"].notna()].copy()
    if d.empty:
        return out
    d["_nomor"] = d["Nomor"].map(_doc_code_str)
    d = d[d["_nomor"].ne("")]
    if d.empty:
        return out
    grp = d.groupby(["Nama Barang", "NAMA RESTO", "_nomor"],
                    dropna=False).size().reset_index(name="_n")
    dup = grp[grp["_n"] > 1]
    for b, r, nomor, n in zip(dup["Nama Barang"], dup["NAMA RESTO"],
                              dup["_nomor"], dup["_n"]):
        out.setdefault((str(b), str(r)), {})[str(nomor)] = int(n)
    return out
