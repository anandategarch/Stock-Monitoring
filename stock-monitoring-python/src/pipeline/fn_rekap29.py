"""
fn_rekap29.py — Sheet "29 Rekap Barang Masuk" + engine Audit Rekonsiliasi (v3.5).

DUA bagian:

1. query_29_rekap_bm(config)
   Reader sheet "29 Rekap Barang Masuk" dari workbook user (master CEK
   STOCK). Sheet ini adalah INPUT PERSIS macro VBA
   BuatLaporanDeviasiSampel: 10 kolom —
   Resto | Nama Item | UoM | Tanggal | Hasil SO | Qty Masuk SO Harian |
   Qty SJ (42.05) | Qty RI (32.24) | Qty Pembelian (99.01) | Selisih Qty.
   Scan: RootPath → semua folder config (nama sheet dinormalisasi: harus
   mengandung "REKAP" + "BARANG MASUK" — sheet pivot 'Barang Masuk'
   TIDAK boleh match).

2. build_audit_rekap(df)
   Port 1:1 algoritma rekonsiliasi VBA (grup kontigu Resto+Item, urut
   sheet — identik perilaku macro):
   - Penerimaan Sistem = SJ + RI + Pembelian
   - Selisih Harian    = Qty SO Harian − Penerimaan Sistem
   - ATURAN VALID: SO naik (deltaSO>0) + SO Harian=0 + Penerimaan>0
     → "VALID (Sistem Masuk)" (omit input harian)
   - "OK (Matching)" saat selisih=0 & saldo kumulatif=0
   - Saldo kumulatif per grup; kembali ±0.0001 → "CUT-OFF RESOLVED"
     (baris selisih≠0) / "OK (Dalam Cut-off)" (baris selisih=0)
   - Sisa gantung akhir grup → "DEVIASI MURNI" / "OK"
   - KPI: rows/cutoff/omit/deviasi_murni/deviasi_qty/ok
   Divalidasi 100% identik dgn sheet LAPORAN_DEVIASI user (output macro).
"""
import os
import re
from typing import Optional

import numpy as np
import pandas as pd

from .helpers import _list_excel_files, _list_sheet_names, _xlsb_engine, _EXCEL_ENGINE

# Kolom kanonik output reader
REKAP29_COLUMNS = [
    "Resto", "Nama Item", "UoM", "Tanggal", "Hasil SO",
    "Qty SO Harian", "Qty SJ", "Qty RI", "Qty Pembelian", "Selisih Qty",
]

_SHEET_HINT = ("REKAP", "BARANGMASUK")


def _norm(s) -> str:
    """Normalisasi nama sheet/kolom: upper + hapus non-alfanumerik."""
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _is_rekap29_sheet(sheet_name: str) -> bool:
    n = _norm(sheet_name)
    return all(h in n for h in _SHEET_HINT)


# Pemetaan kolom fuzzy: (predikat pada nama kolom ternormalisasi, kolom kanonik)
_COL_RULES = [
    (lambda n: "RESTO" in n, "Resto"),
    (lambda n: ("ITEM" in n) or ("NAMABARANG" in n), "Nama Item"),
    (lambda n: ("UOM" in n) or ("SATUAN" in n), "UoM"),
    (lambda n: ("TANGGAL" in n) or (n == "TGL"), "Tanggal"),
    (lambda n: "HASILSO" in n or n == "SO", "Hasil SO"),
    (lambda n: ("MASUK" in n and "SO" in n) or "SOHARIAN" in n, "Qty SO Harian"),
    (lambda n: "SJ" in n or "4205" in n or "42.05" in n, "Qty SJ"),
    (lambda n: "PEMBELIAN" in n or "9901" in n or "99.01" in n, "Qty Pembelian"),
    (lambda n: "RI" in n or "3224" in n or "32.24" in n, "Qty RI"),
    (lambda n: "SELISIH" in n, "Selisih Qty"),
]


def _map_columns(columns) -> Optional[dict]:
    """Peta nama kolom sheet → kolom kanonik. None bila minimal tidak lengkap."""
    mapping: dict = {}
    for col in columns:
        n = _norm(col)
        if not n:
            continue
        for rule, canon in _COL_RULES:
            if rule(n) and canon not in mapping.values():
                mapping[str(col)] = canon
                break
    # syarat minimal: kunci grup + tanggal + 3 sumber penerimaan
    required = {"Resto", "Nama Item", "Tanggal", "Qty SJ", "Qty RI", "Qty Pembelian"}
    if not required.issubset(set(mapping.values())):
        return None
    return mapping


def query_29_rekap_bm(config) -> pd.DataFrame:
    """Cari & baca sheet '29 Rekap Barang Masuk' → DataFrame 10 kolom kanonik.

    Urutan scan: file di RootPath → file di tiap folder config (unik).
    Return DataFrame kosong bila sheet tidak ditemukan (tab UI menampilkan
    pesan eksplisit — TIDAK ada fallback diam-diam).
    """
    search_dirs = []
    root = getattr(config, "RootPath", "")
    if root and os.path.isdir(root):
        search_dirs.append(root)
    folders = getattr(config, "Folders", None) or {}
    for name in folders:
        try:
            p = config.folder(name)
        except Exception:
            continue
        if p and os.path.isdir(p) and os.path.abspath(p) not in \
                [os.path.abspath(d) for d in search_dirs]:
            search_dirs.append(p)

    seen_files = set()
    for d in search_dirs:
        for f in _list_excel_files(d):
            af = os.path.abspath(f)
            if af in seen_files:
                continue
            seen_files.add(af)
            df = _read_rekap29_file(f)
            if df is not None:
                return df

    print("  [Rekap29] Sheet '29 Rekap Barang Masuk' tidak ditemukan "
          f"(scan: {', '.join(search_dirs) or '-'})")
    return pd.DataFrame(columns=REKAP29_COLUMNS)


def _read_rekap29_file(file_path: str) -> Optional[pd.DataFrame]:
    """Baca sheet 29 dari satu file; None bila tidak ada / gagal parse."""
    try:
        sheets = _list_sheet_names(file_path)
    except Exception:
        return None
    for sn in sheets:
        if not _is_rekap29_sheet(sn):
            continue
        if file_path.lower().endswith(".xlsb") and _xlsb_engine() is None:
            print(f"  [Rekap29] SKIP {os.path.basename(file_path)}: .xlsb "
                  "butuh pyxlsb/calamine")
            return None
        engine = _xlsb_engine() if file_path.lower().endswith(".xlsb") \
            else (_EXCEL_ENGINE or None)
        kwargs = {"engine": engine} if engine else {}
        try:
            peek = pd.read_excel(file_path, sheet_name=sn, header=None,
                                 nrows=6, dtype=object, **kwargs)
        except Exception:
            continue
        # deteksi baris header: kolom pertama mengandung "Resto"
        header_row = None
        for i in range(min(len(peek), 6)):
            if "RESTO" in _norm(peek.iloc[i, 0]):
                header_row = i
                break
        if header_row is None:
            continue
        try:
            df = pd.read_excel(file_path, sheet_name=sn, header=header_row,
                               dtype=object, **kwargs)
        except Exception as e:
            print(f"  [Rekap29] Gagal baca '{sn}' {os.path.basename(file_path)}: {e}")
            continue
        mapping = _map_columns(df.columns)
        if mapping is None:
            continue
        df = df.rename(columns=mapping)
        df = df[df["Resto"].notna()].copy()
        if df.empty:
            continue
        for c in REKAP29_COLUMNS:
            if c not in df.columns:
                df[c] = np.nan
        df = df[REKAP29_COLUMNS].reset_index(drop=True)
        # numerik: Tanggal → Int64, sisanya float (NaN = sel kosong)
        df["Tanggal"] = pd.to_numeric(df["Tanggal"], errors="coerce").astype("Int64")
        for c in ("Hasil SO", "Qty SO Harian", "Qty SJ", "Qty RI",
                  "Qty Pembelian", "Selisih Qty"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        for c in ("Resto", "Nama Item", "UoM"):
            df[c] = df[c].astype(str).replace("nan", "")
        print(f"  [Rekap29] {os.path.basename(file_path)} » sheet '{sn}' "
              f"→ {len(df)} baris (input Audit Rekonsiliasi)")
        return df
    return None


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


def build_audit_rekap(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Jalankan algoritma rekonsiliasi → (df hasil + kolom audit, KPI dict).

    Baris diproses PERSIS urutan sheet; grup = blok kontigu dengan
    (Resto|Nama Item) sama — perilaku identik macro VBA.
    """
    n = len(df)
    kpi = {
        "rows": n, "cutoff": 0, "omit": 0, "deviasi_murni": 0,
        "deviasi_qty": 0.0, "ok": 0,
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

    keys = (df["Resto"].astype(str) + "|" + df["Nama Item"].astype(str)) \
        .to_numpy()

    saldo = [0.0] * n
    status = [""] * n
    detail = [""] * n

    def _tgl_int(i: int) -> int:
        return int(tgl[i])

    group_start = 0
    while group_start < n:
        group_end = group_start
        while group_end + 1 < n and keys[group_end + 1] == keys[group_start]:
            group_end += 1

        cum = 0.0
        start_idx = -1          # sentinel (VBA startIdx = 0, array 1-based)

        for i in range(group_start, group_end + 1):
            sel_val = selisih[i]
            has_so = not np.isnan(hasil_so[i])
            delta_so = 0.0
            if i > group_start:
                has_prev = not np.isnan(hasil_so[i - 1])
                if has_so and has_prev:
                    delta_so = hasil_so[i] - hasil_so[i - 1]

            # ATURAN BISNIS: SO Naik + Penerimaan Sistem > 0 + SO Harian = 0
            if delta_so > 0 and so_harian[i] == 0.0 and penerimaan[i] > 0.0:
                saldo[i] = cum
                status[i] = ST_VALID
                detail[i] = (f"SO Naik +{_fmt_qty(delta_so)} | Omit Input "
                             "SO Harian (Penerimaan Sistem OK)")
                kpi["omit"] += 1
            else:
                if sel_val == 0.0 and cum == 0.0:
                    saldo[i] = 0.0
                    status[i] = ST_OK_MATCH
                    detail[i] = "-"
                    kpi["ok"] += 1
                else:
                    if cum == 0.0 and sel_val != 0.0:
                        start_idx = i
                    cum += sel_val
                    saldo[i] = cum

                    if abs(cum) < _EPS and start_idx >= 0:
                        start_tgl = _tgl_int(start_idx)
                        end_tgl = _tgl_int(i)
                        jeda = abs(end_tgl - start_tgl)
                        for j in range(start_idx, i + 1):
                            if status[j] == "":
                                if selisih[j] != 0.0:
                                    status[j] = ST_CUTOFF
                                    detail[j] = (f"Beda {jeda} Hari "
                                                 f"(Periode Tgl {start_tgl} - "
                                                 f"{end_tgl})")
                                    kpi["cutoff"] += 1
                                else:
                                    status[j] = ST_IN_CUTOFF
                                    detail[j] = (f"Rentang Cut-off Tgl "
                                                 f"{start_tgl} - {end_tgl}")
                        cum = 0.0
                        start_idx = -1

        # sisa gantung di akhir grup → Deviasi Murni
        if start_idx >= 0 and abs(cum) >= _EPS:
            open_tgl = _tgl_int(start_idx)
            for j in range(start_idx, group_end + 1):
                if status[j] == "":
                    if selisih[j] != 0.0:
                        status[j] = ST_DEV_MURNI
                        detail[j] = (f"Sisa Gantung: {_fmt_signed(cum)} "
                                     f"(Sejak Tgl {open_tgl})")
                        kpi["deviasi_murni"] += 1
                    else:
                        status[j] = ST_OK
                        detail[j] = "-"
            kpi["deviasi_qty"] += cum

        group_start = group_end + 1

    out["Penerimaan Sistem"] = penerimaan
    out["Selisih Harian"] = selisih
    out["Saldo Kumulatif"] = saldo
    out["Status Analisis Audit"] = status
    out["Detail & Catatan Audit"] = detail
    return out, kpi


def build_audit_from_config(config) -> tuple[pd.DataFrame, dict, str]:
    """Reader + engine sekali jalan.

    Return (audit_df, kpi, source_desc). audit_df kosong + kpi["rows"]=0
    bila sheet 29 tidak ditemukan; source_desc menjelaskan asal data
    (untuk footer/status UI).
    """
    raw = query_29_rekap_bm(config)
    if raw.empty:
        return raw, {"rows": 0, "cutoff": 0, "omit": 0, "deviasi_murni": 0,
                     "deviasi_qty": 0.0, "ok": 0}, "sheet '29 Rekap Barang Masuk' tidak ditemukan"
    audit, kpi = build_audit_rekap(raw)
    desc = (f"29 Rekap Barang Masuk · {len(raw):,} baris · "
            f"{raw['Resto'].nunique()} resto")
    return audit, kpi, desc
