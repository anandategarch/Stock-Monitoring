"""
main.py — Pipeline runner (orchestrator).
Menjalankan pipeline: build Append1 + Rincian PO + Audit Rekonsiliasi →
return DataFrames. Tidak ada Excel output — data ditampilkan langsung di UI.

Bisa dipanggil langsung (CLI) atau dari UI Tkinter.
"""
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

# Suppress openpyxl noise warnings (no default style, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Tambah parent dir ke sys.path untuk import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.pipeline.append1 import build_append1
from src.pipeline.fn_4109 import build_harga_map, fn_4109
from src.pipeline.fn_audit import (
    build_audit_from_app,
    detect_data_period,
    extract_po_pending,
    month_lengths,
)
from src.pipeline.rincian_po import build_rincian_po


def _extract_append1_maps(append1_df: "pd.DataFrame | None") -> "tuple[dict, dict]":
    """v3.10 — peta SALDO AWAL & BARANG KELUAR dari output append1
    (format long JENIS/NILAI) utk basis "SO kemarin" + kolom COM audit:

    - saldo_awal_map {(resto, barang): nilai} dari baris JENIS 'SALDO
      AWAL' (42.17 — first non-null per pasangan);
    - bk_map {(resto, barang, tgl): Σqty} dari baris JENIS
      '8.BARANG KELUAR' (42.15 Kirim).

    Frame kosong/tanpa kolom JENIS/NILAI → peta kosong (audit jalan
    tanpa SA/BK — fallback NaN/0 di fn_audit)."""
    sa: dict = {}
    bk: dict = {}
    if append1_df is None or getattr(append1_df, "empty", True):
        return sa, bk
    cols = set(getattr(append1_df, "columns", []))
    if "JENIS" not in cols or "NILAI" not in cols:
        return sa, bk
    jenis = append1_df["JENIS"].astype(str)
    _sa = append1_df[jenis == "SALDO AWAL"]
    if not _sa.empty and {"NAMA RESTO", "Nama Barang"} <= cols:
        _vals = pd.to_numeric(_sa["NILAI"], errors="coerce")
        for r, b, v in zip(_sa["NAMA RESTO"].astype(str),
                           _sa["Nama Barang"].astype(str), _vals):
            if pd.notna(v) and (r, b) not in sa:
                sa[(r, b)] = float(v)
    _bk = append1_df[jenis == "8.BARANG KELUAR"]
    if not _bk.empty and {"NAMA RESTO", "Nama Barang", "Tanggal"} <= cols:
        _t = pd.to_numeric(_bk["Tanggal"], errors="coerce")
        _vals = pd.to_numeric(_bk["NILAI"], errors="coerce").fillna(0.0)
        for r, b, t, v in zip(_bk["NAMA RESTO"].astype(str),
                              _bk["Nama Barang"].astype(str), _t, _vals):
            if pd.notna(t):
                key = (r, b, int(t))
                bk[key] = bk.get(key, 0.0) + float(v)
    return sa, bk


class PipelineStopped(Exception):
    """Raised when user requests stop via UI Stop button."""
    pass


def run_pipeline(config_path: str = None, verbose: bool = True, stop_event=None):
    """
    Jalankan pipeline lengkap. Return DataFrames (no Excel output).

    Args:
        config_path: Path ke config.json (default: config.json di root project)
        verbose: Print progress
        stop_event: threading.Event — jika set, pipeline akan berhenti di checkpoint
                    berikutnya dengan raise PipelineStopped
                    v3.9.72 (audit 1-d): checkpoint kini JUGA di dalam fase
                    baca file (fn_combine_folder/fn_9901/fn_rekap_mentah/
                    fn_4109 — antar file/sheet), fase Rincian PO & Audit
                    (rincian_po.build_rincian_po, fn_audit.build_audit_
                    from_app + loop baris internal) — bukan lagi 5 titik
                    kasar yang menunggu fase penuh selesai.

    Returns:
        Tuple (append1_df, rincian_po_df, in_detail_df, audit_result)
        v3.4: in_detail_df = detail IN per dokumen (42.05 / 32.24 / 99.01
        + nomor) untuk tab "Rekap Selisih IN".
        v3.6: audit_result = dict {"df": audit_df, "kpi": kpi, "desc": ...}
        — logika macro VBA BuatLaporanDeviasiSampel diaplikasikan ke DATA
        APP (rekap SO + BARANG MASUK + IN per tanggal; sheet '29 Rekap
        Barang Masuk' TIDAK dibaca lagi) + kolom SO & hasil audit di tab
        Rekap Selisih IN.
        v3.9.27: + kunci "df_bulan_ini"/"kpi_bulan_ini"/"desc_bulan_ini" —
        varian audit BULAN BERJALAN SAJA (baris Tanggal negatif dibuang
        sebelum engine; mirror sheet LAPORAN_DEVIASI tgl 1..31) utk mode
        "Hanya Hitung Bulan Ini" tab Rekap Selisih IN (DEFAULT); kunci
        lama tetap varian PENUH (incl. bulan lalu) utk mode "Hitung
        Bulan Lalu + Bulan Ini".
        v3.9.30: Rincian PO 32.43 dibaca SEKALIGUS tanpa filter
        KATEGORI (semua_out) → pasangan ber-status 'Menunggu diproses'
        (extract_po_pending) diteruskan ke KEDUA varian audit sebagai
        penjelas deviasi murni (kolom 'Qty PO Menunggu' + catatan +
        KPI 'dev_murni_po' — lihat fn_audit._apply_po_menunggu).
    v3.9.31: peta KONVERSI SATUAN dari baris IN 42.05+32.24
        (append1 konversi_out — 'Rasio Satuan' + '#Sat. Kirim'/'Satuan')
        → qty PO Menunggu dikonversi ke satuan terkecil (apple-to-apple
        dgn Selisih/Saldo; user: "PO karton vs barang masuk botol tidak
        match waktu cari deviasi murni"; fallback qty as-is + '*').
    v3.9.32: HARGA 41.09 (folder '09.Harga' — Folders.Harga bisa diubah
        user) → audit_result['harga_map'] {barang: (harga, satuan)} +
        audit_result['konversi_map'] (peta rasio v3.9.31) — input mode
        'Nominal (H)' tab Laporan Deviasi (Harga × Qty Deviasi; harga
        dinormalkan ke satuan rekap via peta rasio).
    v3.9.33 — AUDIT FIX (48-b): harga 41.09 dibaca dalam try/except — 1
        file harga rusak kini hanya menonaktifkan peta harga (warning
        log + harga_map kosong), BUKAN menggagalkan seluruh pipeline.
    """
    start_time = time.time()

    # 1. Load config
    if verbose:
        print("=" * 60)
        print("  STOCK MONITORING - PIPELINE RUNNER")
        print("=" * 60)

    config = Config(config_path)

    if verbose:
        print(f"\n  RootPath: {config.RootPath}")
        print("  Mode: FULL (LightMode dihapus v3.5 — bulan lalu selalu terbaca)")

    # 2. Build Append1 (+ IN detail v3.4)
    if verbose:
        print("\n" + "-" * 60)
        print("  [1/3] Building Append1 (main pipeline)...")
        print("-" * 60)

    in_detail_holder: dict = {}
    rekap_so_holder: dict = {}
    konversi_holder: dict = {}
    append1_df = build_append1(config, stop_event=stop_event,
                               in_detail_out=in_detail_holder,
                               rekap_so_out=rekap_so_holder,
                               konversi_out=konversi_holder)

    # FIX: check stop_event after Append1 build
    if stop_event is not None and stop_event.is_set():
        raise PipelineStopped("Pipeline dihentikan oleh user setelah Append1")

    if verbose:
        print(f"\n  Append1 result: {len(append1_df)} rows")
        if not append1_df.empty:
            print(f"  Columns: {list(append1_df.columns)}")

    # 3. Build Rincian PO
    if verbose:
        print("\n" + "-" * 60)
        print("  [2/3] Building Rincian PO...")
        print("-" * 60)

    # v3.9.30 — salinan TANPA filter KATEGORI utk audit PO Menunggu
    # (barang non-DEVIASI-master pun PO-nya ikut terbaca; query utama
    # tab 🛒 Rincian PO tetap terfilter DEVIASI persis mirror M)
    po_semua: dict = {}
    rincian_po_df = build_rincian_po(config, semua_out=po_semua,
                                     stop_event=stop_event)
    po_pending_df = extract_po_pending(po_semua.get("df"))

    # FIX: check stop_event after Rincian PO build
    if stop_event is not None and stop_event.is_set():
        raise PipelineStopped("Pipeline dihentikan oleh user setelah Rincian PO")

    if verbose:
        print(f"\n  Rincian PO result: {len(rincian_po_df)} rows")
        if po_pending_df is not None and not po_pending_df.empty:
            print(f"  PO Menunggu diproses (v3.9.30): {len(po_pending_df)} "
                  f"rows — penjelas deviasi murni di audit")

    in_detail_df = in_detail_holder.get("df")
    if in_detail_df is None:
        in_detail_df = pd.DataFrame()
    if verbose:
        print(f"  IN detail (v3.4): {len(in_detail_df)} rows")

    # v3.10 — basis "SO kemarin" + COM: peta SA 42.17 & BK 42.15 dari
    # append1 + periode data (panjang bulan ASLI — September 30 hari →
    # tak ada tanggal 31; bulan kemarin ikut kalender; user: "Misal bulan
    # ini hanya sampai tanggal 30 maka tidak perlu ada tanggal 31 begitu
    # juga di bulan kemarin").
    saldo_awal_map, bk_map = _extract_append1_maps(append1_df)
    period = detect_data_period(in_detail_df)
    if period is None:
        import datetime as _dt
        _now = _dt.datetime.now()
        period = (_now.year, _now.month)
    month_len, lalu_month_len = month_lengths(period)
    if verbose:
        print(f"  Basis selisih v3.10: SO kemarin (ΔSO − IN) · "
              f"SA {len(saldo_awal_map):,} pasangan · BK {len(bk_map):,} "
              f"baris · periode {period[0]:04d}-{period[1]:02d} "
              f"({month_len} hari; lalu {lalu_month_len} hari)")

    # 4. Audit Rekonsiliasi (v3.6 — dari DATA APP: rekap SO + BM + IN per
    #    tanggal; tanpa sheet '29 Rekap Barang Masuk')
    if verbose:
        print("\n" + "-" * 60)
        print("  [3/3] Audit Rekonsiliasi (logika VBA × data app)...")
        print("-" * 60)
    audit_df, audit_kpi, audit_desc = build_audit_from_app(
        rekap_so_holder.get("df"), in_detail_df,
        po_pending_df=po_pending_df,
        konversi=konversi_holder.get("map"),
        saldo_awal_map=saldo_awal_map,
        bk_map=bk_map,
        stop_event=stop_event)
    audit_result = {"df": audit_df, "kpi": audit_kpi, "desc": audit_desc,
                    # v3.10 — panjang bulan asli utk rentang filter view
                    "period": [int(period[0]), int(period[1])],
                    "month_len": int(month_len),
                    "lalu_month_len": int(lalu_month_len)}

    # v3.9.27 — VARIAN KEDUA utk mode "HITUNG BULAN INI SAJA" tab Rekap
    # Selisih IN (user: "pada rekap selisih in bisa mode hitung bulan lalu
    # dan hanya hitung bulan ini. Tapi default hitung bulan ini aja"):
    # baris Tanggal negatif (bulan lalu) dibuang sebelum engine → audit
    # murni bulan berjalan, mirror sheet LAPORAN_DEVIASI (tgl 1..31).
    # Dihitung SEKALI di pipeline; view memilih varian saat mode diubah
    # (tanpa recompute). Kunci "df"/"kpi"/"desc" TETAP varian penuh —
    # pemanggil lama (app.py log + export "Laporan Deviasi (Audit)")
    # tidak berubah.
    audit_df2, audit_kpi2, audit_desc2 = build_audit_from_app(
        rekap_so_holder.get("df"), in_detail_df, po_pending_df=po_pending_df,
        bulan_lalu=False, konversi=konversi_holder.get("map"),
        saldo_awal_map=saldo_awal_map,
        bk_map=bk_map,
        stop_event=stop_event)
    audit_result["df_bulan_ini"] = audit_df2
    audit_result["kpi_bulan_ini"] = audit_kpi2
    audit_result["desc_bulan_ini"] = audit_desc2

    # v3.9.32 — HARGA 41.09 (user: "harga dari file 4109 (41.09) folder
    # 09.Harga [alamat bisa diubah] — kolom harga = Nilai/Kuantitas
    # Saldo Akhir") + peta konversi v3.9.31 → input mode 'Nominal (H)'
    # tab Laporan Deviasi. Folder/sheet diatur config (setdefault).
    # v3.9.33 — AUDIT FIX (48-b): baca harga SETELAH append1+audit selesai
    # — 1 file harga rusak/struktur aneh dulu menggagalkan SELURUH run
    # (hasil append1+audit yang SUDAH dihitung ikut terbuang). Bungkus
    # try/except → log warning + peta harga kosong (mode Nominal (H)
    # menonaktifkan diri dgn anggun; view lain tetap jalan).
    try:
        harga_df = fn_4109(config.folder("Harga"), config.sheet("Harga"),
                           stop_event=stop_event)
        audit_result["harga_map"] = build_harga_map(harga_df)
    except PipelineStopped:
        # v3.9.72 — ⏹ saat baca harga 41.09: teruskan ke checkpoint utama
        # di bawah — JANGAN didegradasi jadi peta harga kosong (Stop =
        # permintaan user, bukan file rusak; jalur degradasi by-design
        # hanya utk kerusakan struktur file)
        raise
    except Exception as e:  # noqa: BLE001 — degradasi anggun by design
        print(f"  [WARNING] Harga 41.09 dilewati: {e}")
        audit_result["harga_map"] = {}
    audit_result["konversi_map"] = konversi_holder.get("map")
    if verbose and audit_result["harga_map"]:
        _nh = len(audit_result["harga_map"])
        print(f"  Harga 41.09 (v3.9.32): {_nh:,} barang — mode Nominal "
              f"(H) siap (Harga × Qty Deviasi)")
    if verbose:
        n_neg = (pd.to_numeric(audit_df["Tanggal"], errors="coerce") < 0
                 ).sum() if not audit_df.empty else 0
        print(f"  Audit (mode Bulan Ini): {len(audit_df2)} rows "
              f"(varian penuh {len(audit_df)} rows, "
              f"{int(n_neg)} baris bulan lalu)")

    if stop_event is not None and stop_event.is_set():
        raise PipelineStopped("Pipeline dihentikan oleh user setelah Audit")

    if verbose:
        k = audit_kpi
        print(f"  Audit: {len(audit_df)} rows | OK {k['ok']:,} | "
              f"Cut-off {k['cutoff']:,} | Valid {k['omit']:,} | "
              f"Deviasi Murni {k['deviasi_murni']:,} | "
              f"Sisa Gantung {k['deviasi_qty']:,.0f}")
        if k.get("dev_murni_po", 0):
            print(f"  Deviasi Murni ber-PO Menunggu (v3.9.30): "
                  f"{k['dev_murni_po']:,} baris — explainable, "
                  f"sisanya perlu audit fisik")
        _km31 = konversi_holder.get("map") or {}
        if _km31.get("n_rasio"):
            print(f"  Konversi satuan PO (v3.9.31): peta "
                  f"{_km31['n_rasio']:,} rasio / "
                  f"{_km31['n_barang']:,} barang — qty PO Menunggu "
                  f"tampil satuan terkecil")

    elapsed = time.time() - start_time
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"  SELESAI dalam {elapsed:.1f} detik")
        print(f"  Append1: {len(append1_df)} rows | Rincian PO: {len(rincian_po_df)} rows"
              f" | IN detail: {len(in_detail_df)} rows"
              f" | Audit: {len(audit_df)} rows")
        print(f"{'=' * 60}")

    return append1_df, rincian_po_df, in_detail_df, audit_result


if __name__ == "__main__":
    # CLI mode — just run pipeline and print summary
    import argparse
    parser = argparse.ArgumentParser(description="Stock Monitoring Pipeline")
    parser.add_argument("--config", default=None, help="Path ke config.json")
    args = parser.parse_args()

    try:
        append1_df, rincian_po_df, in_detail_df, audit = run_pipeline(
            config_path=args.config)
        print(f"\nAppend1: {len(append1_df)} rows")
        print(f"Rincian PO: {len(rincian_po_df)} rows")
        print(f"IN detail: {len(in_detail_df)} rows")
        print(f"Audit: {len(audit['df'])} rows — {audit['kpi']}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
