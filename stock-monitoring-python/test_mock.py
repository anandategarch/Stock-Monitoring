"""
test_mock.py — Test pipeline dengan mock data yang match format Accurate Online export.
Membuat folder + file Excel mock, lalu menjalankan pipeline end-to-end.
v3.9.20: + seksi [6b] cek deep-audit pipeline (agent 35-d — append1
LANGKAH 9 tie/NA/strip, fn_4205 'lalu' anchor resto, resolusi sheet
folder bulan-lalu, query_in end-to-end; 35 check TANPA Tk).
"""
import os
import shutil
import sys
import tempfile
from datetime import datetime

# zipfile + re no longer needed (Excel output removed)
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import openpyxl

from src.config import Config
from src.pipeline.append1 import build_append1
from src.pipeline.rincian_po import build_rincian_po

# Excel output removed — data displayed in UI


def create_mock_file(filepath, sheet_name, headers, data_rows, metadata_rows=4):
    """Create a mock Excel file matching Accurate export format.
    metadata_rows: jumlah row metadata SEBELUM header row (default 4 = rows 1-4).
    Header row is at index metadata_rows (row 5 if metadata_rows=4).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]  # Excel sheet name max 31 chars

    # Write metadata rows (rows 1 to metadata_rows)
    for i in range(metadata_rows):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i+1} - {sheet_name}")

    # Write header row (row metadata_rows + 1)
    header_row = metadata_rows + 1
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=header_row, column=col_idx, value=header)

    # Write data rows
    for row_idx, row_data in enumerate(data_rows, header_row + 1):
        for col_idx, val in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def create_mock_rekap_mentah(filepath, resto_code, barang_list, mode="berjalan"):
    """Create REKAP MENTAH sheet (header at row 1, no metadata)."""
    headers = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS", "NAMA BARANG", "SATUAN"]
    if mode == "berjalan":
        headers += [str(d) for d in range(1, 32)]  # 1..31
    else:
        headers += [str(d) for d in range(25, 32)]  # 25..31

    data_rows = []
    for barang, satuan in barang_list:
        # SO row (v3.9.19: SOURCE DATA realistis — "input so harian";
        # varian promix dites di test_ui §29 via kolom SOURCE DATA app)
        row = [f"{resto_code}.001", "input so harian", "SO", "OK", barang, satuan]
        row += [100 if d == 1 else 0 for d in (range(1, 32) if mode == "berjalan" else range(25, 32))]
        data_rows.append(row)
        # BARANG MASUK row
        row = [f"{resto_code}.001", "input so harian", "BARANG MASUK", "OK", barang, satuan]
        row += [50 if d == 1 else 0 for d in (range(1, 32) if mode == "berjalan" else range(25, 32))]
        data_rows.append(row)

    # This sheet has header at row 1 (no metadata) → header=0 in pandas
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "REKAP MENTAH"
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=h)
    for row_idx, row_data in enumerate(data_rows, 2):
        for col_idx, val in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def create_mock_2205(filepath, resto_code, barang_list):
    """Create #22.05 sheet (4 metadata rows, header at row 5)."""
    headers = ["Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"]
    data_rows = []
    for i, (barang, _) in enumerate(barang_list):
        data_rows.append([
            f"ACR.2026.09.{1000+i}",
            datetime(2026, 9, 5),
            f"RESTO MALANG ({resto_code})",
            barang,
            10 + i
        ])
    create_mock_file(filepath, "#22.05. Rincian Penjualan per B", headers, data_rows, metadata_rows=4)


def create_mock_3224(filepath, resto_code, barang_list, mode="berjalan"):
    """Create #32.24 sheet."""
    headers = ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
               "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan"]
    data_rows = []
    for i, (barang, _) in enumerate(barang_list):
        tgl = 5 if mode == "berjalan" else 28
        data_rows.append([
            datetime(2026, 9, tgl),
            20 + i,
            barang,
            f"GUDANG MALANG ({resto_code})",
            f"IT.2026.09.{2000+i}",
            f"PO.2026.09.{3000+i}",
            datetime(2026, 9, 3, 16, 52, 12)
        ])
    create_mock_file(filepath, "#32.24. Rincian Penerimaan Bara", headers, data_rows, metadata_rows=4)


def create_mock_4215(filepath, resto_code, barang_list):
    """Create #42.15 sheet (kirim)."""
    headers = ["Tanggal", "Gudang Pengirim", "Nama Barang", "Kts Diterima"]
    data_rows = []
    for i, (barang, _) in enumerate(barang_list):
        data_rows.append([
            datetime(2026, 9, 5),
            f"GUDANG MALANG ({resto_code})",
            barang,
            5 + i
        ])
    create_mock_file(filepath, "#42.15. Pemindahan Barang (KIRI", headers, data_rows, metadata_rows=4)


def create_mock_4205(filepath, resto_code, barang_list, mode="berjalan"):
    """Create #42.05 sheet (mode 'lalu': tanggal ujung bulan = 28)."""
    headers = ["Nomor #Terima", "Gudang #Terima", "Tanggal #Terima", "Nama Barang",
               "#Qty. Terkecil", "#Tgl/Jam Pembuatan IT"]
    data_rows = []
    tgl = 5 if mode == "berjalan" else 28
    nomor_base = 4000 if mode == "berjalan" else 5000
    for i, (barang, _) in enumerate(barang_list):
        data_rows.append([
            f"IT.2026.09.{nomor_base+i}",
            f"GUDANG BANDUNG ({resto_code})",
            datetime(2026, 9, tgl),
            barang,
            15 + i,
            datetime(2026, 9, tgl - 1, 10, 30, 0)
        ])
    create_mock_file(filepath, "#42.05. Rincian Pemindahan Bara", headers, data_rows, metadata_rows=4)


def create_mock_4217(filepath, resto_code, barang_list):
    """Create #42.17 sheet (saldo awal). UnpivotOtherColumns format."""
    # Row 1-4: metadata
    # Row 5: headers = Nama Barang + resto column names
    # Row 6+: data
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "#42.17. Kuantitas Barang per Gu"

    # Metadata
    for i in range(4):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i+1}")

    # Headers (row 5)
    ws.cell(row=5, column=1, value="Nama Barang")
    ws.cell(row=5, column=2, value=f"RESTO MALANG ({resto_code})")

    # Data (row 6+)
    for i, (barang, _) in enumerate(barbar_list):
        ws.cell(row=6 + i, column=1, value=barang)
        ws.cell(row=6 + i, column=2, value=200 + i * 10)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def create_mock_pi(filepath, resto_code, barang_list):
    """Create #32.42 sheet (faktur pembelian)."""
    headers = ["Nama Cabang#", "Tgl Pengiriman", "Nama Barang", "Kuantitas", "Nama Satuan"]
    data_rows = []
    for i, (barang, satuan) in enumerate(barang_list):
        data_rows.append([
            f"1370.{resto_code}",
            datetime(2026, 9, 5),
            barang,
            10 + i,
            satuan
        ])
    create_mock_file(filepath, "#32.42. Rincian Faktur Pembelia", headers, data_rows, metadata_rows=4)


def create_mock_konversi(filepath, barang_list):
    """Create Sheet1 (konversi satuan). Header at row 1."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    headers = ["Nama Barang", "Satuan #2", "Rasio Satuan #2",
               "Satuan #3", "Rasio Satuan #3",
               "Satuan #4", "Rasio Satuan #4",
               "Satuan #5", "Rasio Satuan #5"]
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=h)

    for i, (barang, satuan) in enumerate(barang_list):
        ws.cell(row=2 + i, column=1, value=barang)
        ws.cell(row=2 + i, column=2, value=satuan)
        ws.cell(row=2 + i, column=3, value="1")
        ws.cell(row=2 + i, column=4, value="DUS")
        ws.cell(row=2 + i, column=5, value="12")
        ws.cell(row=2 + i, column=6, value=None)
        ws.cell(row=2 + i, column=7, value=None)
        ws.cell(row=2 + i, column=8, value=None)
        ws.cell(row=2 + i, column=9, value=None)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def create_mock_9901(filepath, resto, barang_list):
    """Create mock 9901 (mutasi barang tanpa nomor penerimaan).
    Header at row 1. Nama cabang format '1137.<RESTO>' sesuai export asli."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    headers = ["Nomor # Penerimaan Barang", "Jenis Barang Barang & Jasa",
               "#Prime.Qty", "Nama barang", "Nama cabang", "Tanggal"]
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=h)

    # 2 baris valid (nomor penerimaan blank + jenis Persediaan)
    # + 1 baris yang harus terfilter (ada nomor penerimaan)
    rows = []
    for i, (barang, _) in enumerate(barang_list[:2]):
        rows.append([None, "Persediaan", 5.0 * (i + 1), barang,
                     f"1137.{resto}", 5 + i])
    rows.append(["RI-900", "Persediaan", 99.0, barang_list[0][0],
                 f"1137.{resto}", 7])

    for r_idx, row_data in enumerate(rows, 2):
        for c_idx, val in enumerate(row_data, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def create_mock_dbs_kategori(filepath, barang_list):
    """Create Sheet1 (DBS kategori). Header at row 1."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    headers = ["NAMA BARANG", "KATEGORI", "JENIS", "SOURCE KIRIMAN"]
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=h)

    for i, (barang, _) in enumerate(barbar_list):
        ws.cell(row=2 + i, column=1, value=barang)
        ws.cell(row=2 + i, column=2, value="DEVIASI")
        ws.cell(row=2 + i, column=3, value="BAHAN BAKU")
        ws.cell(row=2 + i, column=4, value="INTERNAL")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def create_mock_rincian_po(filepath, resto_code, barang_list):
    """Create #32.43 sheet (rincian PO). 5 metadata rows (skip 4+1), header at row 5."""
    # Rincian PO has: skip(3) + skip(1) = skip 4 → header at row 5 (index 4)
    headers = ["Nomor #", "Tanggal", "Cabang PO", "Pemasok", "Nama Barang",
               "Satuan", "Kuantitas", "@Harga", "Total Harga", "Keterangan PO",
               "Status Pesanan Pembelian", "Tgl/Jam Pembuatan"]
    data_rows = []
    for i, (barang, satuan) in enumerate(barbar_list):
        data_rows.append([
            f"PO.2026.09.{5000+i}",
            datetime(2026, 9, 5),
            f"1370.{resto_code}",
            "PT KREASI REMPAH INDONESIA",
            barang,
            satuan,
            10 + i,
            27000,
            (10 + i) * 27000,
            "REP",
            "Menunggu diproses",
            datetime(2026, 9, 3, 18, 12, 33)
        ])
    create_mock_file(filepath, "#32.43. Rincian Pesanan Pembeli", headers, data_rows, metadata_rows=4)


# =============================================================================
# v3.9.20 — DEEP AUDIT & FIX (gelombang audit 34-a..34-e + fix 35-a..35-d):
# cek pipeline agent 35-d (append1 LANGKAH 9 · fn_4205 mode 'lalu' ·
# resolusi sheet folder bulan-lalu · query_in end-to-end) — mock-Excel +
# assert, pola test_mock (35 check, TANPA Tk).
# =============================================================================

def _v20_mock_4205(filepath, rows, sheet="#42.05. Rincian Pemindahan Bara"):
    """Mock 42.05 utk cek 35-d. rows: (Nomor, Gudang, day, Barang, Qty)."""
    headers = ["Nomor #Terima", "Gudang #Terima", "Tanggal #Terima",
               "Nama Barang", "#Qty. Terkecil", "#Tgl/Jam Pembuatan IT"]
    data = [[n, g, datetime(2026, 8, d), b, q, datetime(2026, 8, 1, 10, 0)]
            for n, g, d, b, q in rows]
    create_mock_file(filepath, sheet, headers, data, metadata_rows=4)


def _v20_mock_3224(filepath, rows, sheet="#32.24. Rincian Penerimaan Bara"):
    """Mock 32.24 utk cek 35-d. rows: (day, Gudang, Barang, Qty)."""
    headers = ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
               "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan"]
    data = [[datetime(2026, 8, d), q, b, g,
             f"RI.2026.08.{i}", "PO.2026.08.1",
             datetime(2026, 8, 1, 10, 0)]
            for i, (d, g, b, q) in enumerate(rows)]
    create_mock_file(filepath, sheet, headers, data, metadata_rows=4)


def _v20_mock_rekap(filepath, sheet, rows, days):
    """Mock rekap combined-workbook (header baris 1).
    rows: dict(resto, src, jenis, barang, satuan, d<day>=value)."""
    headers = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS",
               "NAMA BARANG", "SATUAN"] + [str(d) for d in days]
    data = []
    for row in rows:
        vals = [row.get("resto", "MLGPAR"), row.get("src"), row["jenis"],
                "OK", row["barang"], row.get("satuan", "KG")]
        vals += [row.get(f"d{d}") for d in days]
        data.append(vals)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet[:31]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    for r, vals in enumerate(data, 2):
        for c, v in enumerate(vals, 1):
            if v is not None:
                ws.cell(row=r, column=c, value=v)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def _v20_config(root, sheets=None, folders=None):
    """Config utk cek 35-d (key dedikasi Sheets['Pemindahan4205Lalu'])."""
    import json as _json
    cfg = {
        "RootPath": root + os.sep,
        "Folders": {
            "RekapBerjalan": "1. DEVIASI WEEKLY",
            "RekapLalu": "1.12 Rekap Mentah Bulan Lalu",
            "Penjualan2205": "2. 22.05",
            "Kirim4215": "3.1 42.15 Kirim",
            "Terima4215": "3. 42.15",
            "RI3224": "13. 32.24 RI",
            "RI3224Lalu": "13.2 3224 RI Bulan Lalu",
            "SaldoAwal4217": "6.1 42.17 Saldo Awal",
            "DBSKategori": "21. DBS Kategori",
            "Pemindahan4205": "4. 42.05",
            "Pemindahan4205Lalu": "4.1 4205 Bulan Lalu",
            "RincianPO": "25. Rincian PO",
            "Data9901": "30. 9901",
        },
        "Sheets": {
            "Pemindahan4205": "#42.05. Rincian Pemindahan Bara",
        },
    }
    if sheets:
        cfg["Sheets"].update(sheets)
    if folders:
        cfg["Folders"].update(folders)
    path = os.path.join(root, "config.json")
    os.makedirs(root, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        _json.dump(cfg, f)
    return path


# Fixture 35-d: rekap berjalan dgn tie / padded / whitespace-only SOURCE DATA
_V20_REKAP_BERJALAN = [
    # TIE-1: same day 10, so-harian + promix take away
    {"barang": "BRG-TIE1", "src": "input so harian", "jenis": "SO",
     "d10": 5},
    {"barang": "BRG-TIE1", "src": "input promix 04 take away",
     "jenis": "SO", "d10": 7},
    # TIE-2: same day 12, two promix variants
    {"barang": "BRG-TIE2", "src": "input promix 04 dine in",
     "jenis": "SO", "d12": 3},
    {"barang": "BRG-TIE2", "src": "input promix 04 take away",
     "jenis": "SO", "d12": 4},
    # PAD: padded SOURCE DATA (nilai jalur per-resto tanpa strip)
    {"barang": "BRG-PAD", "src": " input so harian ", "jenis": "SO",
     "d5": 10},
    # SPC: whitespace-only SOURCE DATA
    {"barang": "BRG-SPC", "src": "   ", "jenis": "SO", "d4": 60},
    # PREF: running d20 promix > running d5 so-harian (semantics intact)
    {"barang": "BRG-PREF", "src": "input so harian", "jenis": "SO",
     "d5": 10},
    {"barang": "BRG-PREF", "src": "input promix 04 dine in",
     "jenis": "SO", "d20": 8},
    # POS: berjalan +1 so-harian vs lalu -28 promix → positif menang
    {"barang": "BRG-POS", "src": "input so harian", "jenis": "SO",
     "d1": 15},
    # NA: SO row tanpa SOURCE DATA → pasangan NaN (BM src diabaikan)
    {"barang": "BRG-NA", "src": None, "jenis": "SO", "d7": 40},
    {"barang": "BRG-NA", "src": "BM SOURCE", "jenis": "BARANG MASUK",
     "d3": 30},
]
_V20_REKAP_LALU = [
    {"barang": "BRG-POS", "src": "input promix 04 dine in",
     "jenis": "SO", "d28": 9},
]


def _v20_pair_source(final, barang, resto="MLGPAR"):
    """Nilai SOURCE DATA pasangan dari output append1 final (semua nilai
    unik — v3.9.21 per-tanggal: satu pasangan bisa punya >1 sumber utk
    tanggal berbeda)."""
    import pandas as _pd
    sub = final[(final["Nama Barang"] == barang)
                & (final["NAMA RESTO"] == resto)]
    if "SOURCE DATA" not in sub.columns:
        return None
    s = sub["SOURCE DATA"]
    assert not isinstance(s, _pd.DataFrame), "duplicate SOURCE DATA columns"
    vals = s.dropna().unique().tolist()
    return vals if vals else None


def _v20_source_at(final, barang, tanggal, resto="MLGPAR"):
    """v3.9.21 — SOURCE DATA pasangan PADA TANGGAL tertentu (semantik
    per-tanggal: sumber menempel baris final per (pasangan, Tanggal))."""
    sub = final[(final["Nama Barang"] == barang)
                & (final["NAMA RESTO"] == resto)
                & (final["Tanggal"] == tanggal)]
    if sub.empty or "SOURCE DATA" not in sub.columns:
        return None
    vals = sub["SOURCE DATA"].dropna().unique().tolist()
    return vals[0] if vals else None


def _v20_rekap_tree(root, tie_order="normal", with_source=True):
    berjalan = list(_V20_REKAP_BERJALAN)
    if tie_order == "reversed":
        ties = [r for r in berjalan
                if r["barang"] in ("BRG-TIE1", "BRG-TIE2")]
        rest = [r for r in berjalan
                if r["barang"] not in ("BRG-TIE1", "BRG-TIE2")]
        berjalan = ties[::-1] + rest
    days_b = list(range(1, 32))
    days_l = list(range(25, 32))
    _v20_mock_rekap(
        os.path.join(root, "1. DEVIASI WEEKLY", "CEK STOCK V2.xlsx"),
        "1  DEVIASI WEEKLY" if with_source else "1  DEVIASI WEEKLY NOSRC",
        [dict(r, src=(r["src"] if with_source else None))
         for r in berjalan] if with_source else
        [{k: v for k, v in r.items() if k != "src"} for r in berjalan],
        days_b)
    _v20_mock_rekap(
        os.path.join(root, "1.12 Rekap Mentah Bulan Lalu", "SO LALU.xlsx"),
        "SO LALU" if with_source else "SO LALU NOSRC",
        _V20_REKAP_LALU if with_source else
        [{k: v for k, v in r.items() if k != "src"} for r in _V20_REKAP_LALU],
        days_l)
    return _v20_config(root)


def run_test_v3920_fixes():
    """[6b] v3.9.20 (agent 35-d): LANGKAH 9 tie/NA/strip + fn_4205 lalu
    window + resolusi sheet lalu + query_in end-to-end — 35 check."""
    import json as _json

    import pandas as _pd

    from src.pipeline.fn_3224 import fn_3224
    from src.pipeline.fn_4205 import fn_4205
    from src.pipeline.queries import (
        query_3224_bulan_lalu,
        query_4205_bulan_lalu,
        query_in,
    )
    n_ok = [0]

    def check20(name, cond, detail=""):
        assert cond, f"FAIL: {name} {detail}"
        n_ok[0] += 1
        print(f"    OK {name}" + ((" — " + detail) if detail else ""))

    print("\n  [6b] (v3.9.20/35-d + v3.9.21 per-tanggal) append1 LANGKAH 9")
    tmp = tempfile.mkdtemp(prefix="t35d_l9_")
    final = build_append1(Config(_v20_rekap_tree(tmp, "normal")))

    check20("T1a tie so-harian vs promix TANGGAL SAMA → 'input so harian' "
            "(hitungan manual menang — v3.9.21)",
            _v20_source_at(final, "BRG-TIE1", 10) == "input so harian",
            repr(_v20_source_at(final, "BRG-TIE1", 10)))
    check20("T1b tie dua varian promix → take away (string terbesar)",
            _v20_source_at(final, "BRG-TIE2", 12)
            == "input promix 04 take away")

    tmp_r = tempfile.mkdtemp(prefix="t35d_l9r_")
    final_r = build_append1(Config(_v20_rekap_tree(tmp_r, "reversed")))
    check20("T2a winner order-independent (baris sheet dibalik)",
            all(_v20_source_at(final_r, b, t) == _v20_source_at(final, b, t)
                for b, t in (("BRG-TIE1", 10), ("BRG-TIE2", 12),
                             ("BRG-PAD", 5), ("BRG-SPC", 4),
                             ("BRG-PREF", 5), ("BRG-PREF", 20))))

    tmp_s = tempfile.mkdtemp(prefix="t35d_l9s_")
    final_s = build_append1(Config(_v20_rekap_tree(tmp_s, "normal")))
    check20("T2b deterministik re-run fixture identik",
            _v20_source_at(final_s, "BRG-TIE1", 10) == "input so harian")

    check20("T3a padded ' input so harian ' → 'input so harian' (strip)",
            _v20_source_at(final, "BRG-PAD", 5) == "input so harian")
    check20("T3b whitespace-only '   ' → TANPA sumber (v3.9.21: dibuang)",
            _v20_source_at(final, "BRG-SPC", 4) is None,
            repr(_v20_source_at(final, "BRG-SPC", 4)))
    check20("T3c tidak lower-case (nilai tampilan dipertahankan)",
            _v20_source_at(final, "BRG-PREF", 20)
            == "input promix 04 dine in")
    check20("T3d SO row tanpa SOURCE DATA → tanpa sumber (NaN)",
            _v20_source_at(final, "BRG-NA", 7) is None)

    check20("T4a berjalan & lalu PUNYA sumber masing-masing per tanggal "
            "(d1 so-harian; -28 promix — v3.9.21)",
            _v20_source_at(final, "BRG-POS", 1) == "input so harian"
            and _v20_source_at(final, "BRG-POS", -28)
            == "input promix 04 dine in")
    check20("T4b pasangan campuran: d5 so-harian, d20 promix (per-tanggal)",
            _v20_source_at(final, "BRG-PREF", 5) == "input so harian"
            and _v20_source_at(final, "BRG-PREF", 20)
            == "input promix 04 dine in")

    tmp_ns = tempfile.mkdtemp(prefix="t35d_l9n_")
    final_ns = build_append1(Config(_v20_rekap_tree(tmp_ns, "normal",
                                                    with_source=False)))
    check20("T5a tanpa inflasi baris (dgn vs tanpa kolom SOURCE DATA)",
            len(final) == len(final_ns),
            f"{len(final)} == {len(final_ns)}")
    check20("T5b kolom SOURCE DATA tunggal (bukan duplikat)",
            list(final.columns).count("SOURCE DATA") == 1)
    so_rows = final[(final["JENIS"] == "1.SO")
                    & final["SOURCE DATA"].notna()]
    check20("T5d sumber konstan per (pasangan, tanggal) — v3.9.21",
            so_rows.groupby(["Nama Barang", "NAMA RESTO", "Tanggal"])
            ["SOURCE DATA"].nunique().max() == 1,
            f"{so_rows['Nama Barang'].nunique()} pasangan")

    # v3.9.21 — replikasi ekspresi LANGKAH 9 BARU (per-tanggal, non-nol,
    # harian menang): baris nilai 0 & whitespace-only dibuang; NA-Tanggal
    # tak pernah match kunci merge.
    so = _pd.DataFrame({
        "Nama Barang": ["X", "X", "X", "X", "X"],
        "NAMA RESTO": ["R", "R", "R", "R", "R"],
        "JENIS": ["SO", "SO", "SO", "SO", "SO"],
        "Tanggal": _pd.array([25, 25, 25, None, 24], dtype="Int64"),
        "Value": [10.0, 0.0, 7.0, 9.0, 5.0],
        "SOURCE DATA": ["input promix 04 take away", "input so harian",
                        "input so harian", "input promix NaN-date",
                        "   "],
    })
    _val = _pd.to_numeric(so["Value"], errors="coerce")
    _src = so["SOURCE DATA"].map(
        lambda v: v.strip() if isinstance(v, str) else v)
    _s = _src.astype(str)
    _t0 = _pd.to_numeric(so["Tanggal"], errors="coerce")
    out = (so.assign(_src=_src, _s=_s,
                    _harian=_s.str.strip().str.lower() == "input so harian")
           .loc[(_val.fillna(0) != 0) & _s.str.strip().ne("")
                & _t0.notna()]
           .sort_values(["_harian", "_s"], kind="mergesort")
           .drop_duplicates(subset=["Nama Barang", "NAMA RESTO", "Tanggal"],
                            keep="last")
           [["Nama Barang", "NAMA RESTO", "Tanggal", "_src"]]
           .rename(columns={"_src": "SOURCE DATA"}))
    check20("T6a baris nilai-0 & whitespace & NA-Tanggal dibuang; tie d25 "
            "harian menang",
            len(out) == 1 and out["SOURCE DATA"].iloc[0] == "input so harian"
            and out["Tanggal"].iloc[0] == 25,
            str(out.to_dict("records")))

    # bukti ekspresi v3.9.20 (pair-level) memang tak melihat nilai — baris
    # template promix nilai-0 memenangkan race pair-level → label Promix
    # TANPA data promix aktual (persis phantom user; diganti v3.9.21)
    so_old = _pd.DataFrame({
        "Nama Barang": ["Y", "Y"],
        "NAMA RESTO": ["R", "R"],
        "JENIS": ["SO", "SO"],
        "Tanggal": _pd.array([25, 24], dtype="Int64"),
        "Value": [0.0, 10.0],
        "SOURCE DATA": ["input promix 04 take away", "input so harian"],
    })
    out_old = (so_old.assign(
        _t=_pd.to_numeric(so_old["Tanggal"], errors="coerce"),
        _s=so_old["SOURCE DATA"].astype(str))
        .sort_values(["_t", "_s"], kind="mergesort", na_position="first")
        .drop_duplicates(subset=["Nama Barang", "NAMA RESTO"], keep="last"))
    check20("T6b ekspresi LAMA: baris promix nilai-0 menang pair-level → "
            "label Promix tanpa data (phantom — diganti v3.9.21)",
            out_old["SOURCE DATA"].iloc[0] == "input promix 04 take away"
            and float(out_old["Value"].iloc[0]) == 0.0,
            str(out_old[["Tanggal", "Value", "SOURCE DATA"]].to_dict("records")))

    print("    [6b.2] fn_4205 mode 'lalu' — FIX 5 (R-4): anchor resto")
    d = tempfile.mkdtemp(prefix="t35d_w1_")
    _v20_mock_4205(os.path.join(d, "x.xlsx"), [
        ("IT.2026.08.31", "GUDANG TANPA RESTO", 31, "BRG", 1),
    ] + [(f"IT.2026.08.{dd}", "GUDANG HO (MLGPAR)", dd, "BRG", dd)
         for dd in (25, 26, 27, 28)])
    r4 = fn_4205(d, mode="lalu")
    check20("T7a semua baris resto masuk jendela (anchor = max resto 28)",
            sorted(r4["Tanggal"].tolist()) == [-28, -27, -26, -25],
            str(sorted(r4["Tanggal"].tolist())))
    check20("T7b baris NA-resto di luar output (mirror fn_3224)",
            r4["NAMA RESTO"].notna().all()
            and "MLGPAR" in r4["NAMA RESTO"].unique().tolist())

    d3 = tempfile.mkdtemp(prefix="t35d_w1b_")
    _v20_mock_3224(os.path.join(d3, "y.xlsx"),
                   [(31, "GUDANG TANPA RESTO", "BRG", 1)]
                   + [(dd, "GUDANG HO (MLGPAR)", "BRG", dd)
                      for dd in (25, 26, 27, 28)])
    r3 = fn_3224(d3, "lalu")
    check20("T7c paritas mirror fn_3224 (Tanggal identik)",
            sorted(r3["Tanggal"].tolist()) == sorted(r4["Tanggal"].tolist()))

    d2 = tempfile.mkdtemp(prefix="t35d_w2_")
    _v20_mock_4205(os.path.join(d2, "x.xlsx"), [
        ("IT.2026.08.28", "GUDANG TANPA RESTO", 28, "BRG", 99),
        ("IT.2026.08.27", "GUDANG HO (MLGPAR)", 27, "BRG", 1),
        ("IT.2026.08.28", "GUDANG HO (MLGPAR)", 28, "BRG", 2),
    ])
    r = fn_4205(d2, mode="lalu")
    check20("T8a NA-resto dalam jendela ikut dikecualikan",
            sorted(r["Tanggal"].tolist()) == [-28, -27]
            and r["NAMA RESTO"].notna().all())

    d4 = tempfile.mkdtemp(prefix="t35d_w3_")
    _v20_mock_4205(os.path.join(d4, "x.xlsx"),
                   [(f"IT.2026.08.{dd}", "GUDANG HO (MLGPAR)", dd,
                     "BRG", dd) for dd in range(25, 32)])
    r_std = fn_4205(d4, mode="lalu")
    check20("T9a jendela 5 hari standar utuh (25..31 → -27..-31)",
            sorted(r_std["Tanggal"].tolist()) == [-31, -30, -29, -28, -27])

    d5 = tempfile.mkdtemp(prefix="t35d_w4_")
    _v20_mock_4205(os.path.join(d5, "x.xlsx"), [
        ("IT.2026.08.5", "GUDANG TANPA RESTO", 5, "BRG", 1),
        ("IT.2026.08.5", "GUDANG HO (MLGPAR)", 5, "BRG", 2),
    ])
    r_b = fn_4205(d5, mode="berjalan")
    check20("T9b mode berjalan TIDAK berubah (NA-resto tetap lolos)",
            len(r_b) == 2 and r_b["NAMA RESTO"].isna().sum() == 1)

    r_miss = fn_4205(os.path.join(d, "TIDAK ADA"), mode="lalu")
    r_empty = fn_4205(tempfile.mkdtemp(prefix="t35d_w5_"), mode="lalu")
    check20("T9c folder hilang/kosong → 0 baris senyap",
            len(r_miss) == 0 and len(r_empty) == 0)

    print("    [6b.3] queries lalu sheet — FIX 4 (R-3)")
    root = tempfile.mkdtemp(prefix="t35d_s1_")
    rp = os.path.join(root, "9.NEW QUERY")
    _v20_mock_4205(
        os.path.join(rp, "4.1 4205 Bulan Lalu", "lalu.xlsx"),
        [("IT.2026.08.28", "GUDANG HO (MLGPAR)", 28, "BRG", 10)],
        sheet="#42.05. Rincian Pemindahan LALU")
    _v20_mock_3224(
        os.path.join(rp, "13.2 3224 RI Bulan Lalu", "ri_lalu.xlsx"),
        [(28, "GUDANG HO (MLGPAR)", "BRG", 10)],
        sheet="#32.24. Rincian Penerimaan LALU")

    cfg = Config(_v20_config(rp))
    r4205 = query_4205_bulan_lalu(cfg)
    check20("T10a 4205-lalu sheet beda nama → rows ditemukan (bukan 0 senyap)",
            len(r4205) == 1 and r4205["Tanggal"].iloc[0] == -28,
            f"{len(r4205)} rows")
    r3224 = query_3224_bulan_lalu(cfg)
    check20("T10b 3224-lalu sheet beda nama → rows ditemukan",
            len(r3224) == 1 and r3224["Tanggal"].iloc[0] == -28,
            f"{len(r3224)} rows")

    root2 = tempfile.mkdtemp(prefix="t35d_s2_")
    rp2 = os.path.join(root2, "9.NEW QUERY")
    _v20_mock_4205(
        os.path.join(rp2, "4.1 4205 Bulan Lalu", "lalu.xlsx"),
        [("IT.2026.08.28", "GUDANG HO (MLGPAR)", 28, "BRG", 10)])
    r_exact = query_4205_bulan_lalu(Config(_v20_config(rp2)))
    check20("T11 nama sheet persis → perilaku lama utuh (tanpa fallback)",
            len(r_exact) == 1)

    cfg_path20 = _v20_config(rp2)
    with open(cfg_path20, encoding="utf-8") as f:
        cfg_data = _json.load(f)
    cfg_data["Sheets"] = {k: v for k, v in cfg_data["Sheets"].items()
                          if k != "Pemindahan4205Lalu"}
    cp_old = os.path.join(root2, "config_old.json")
    with open(cp_old, "w", encoding="utf-8") as f:
        _json.dump(cfg_data, f)
    cfg_old = Config(cp_old)
    check20("T12a config lama tanpa key → default = nilai berjalan, 0 KeyError",
            cfg_old.sheet("Pemindahan4205Lalu")
            == cfg_old.sheet("Pemindahan4205"))
    r_old = query_4205_bulan_lalu(cfg_old)
    check20("T12b config lama → rows tetap ditemukan", len(r_old) == 1)

    cfg_data["Sheets"]["Pemindahan4205Lalu"] = \
        "#42.05. Rincian Pemindahan Bara"
    cp_ded = os.path.join(root2, "config_ded.json")
    with open(cp_ded, "w", encoding="utf-8") as f:
        _json.dump(cfg_data, f)
    cfg_ded = Config(cp_ded)
    check20("T12c key dedikasi eksplisit dipakai bila ada",
            cfg_ded.sheet("Pemindahan4205Lalu")
            == "#42.05. Rincian Pemindahan Bara")

    cfg_miss = Config(_v20_config(os.path.join(root2, "NOPE")))
    check20("T13 folder lalu hilang → 0 baris senyap",
            len(query_4205_bulan_lalu(cfg_miss)) == 0
            and len(query_3224_bulan_lalu(cfg_miss)) == 0)

    print("    [6b.4] End-to-end: query_in + build_append1 (lalu beda nama)")

    def build_tree(lalu_sheet_4205, lalu_sheet_3224):
        root_e = tempfile.mkdtemp(prefix="t35d_e2e_")
        rpe = root_e
        _v20_mock_rekap(
            os.path.join(rpe, "1. DEVIASI WEEKLY", "CEK.xlsx"),
            "1  DEVIASI WEEKLY", _V20_REKAP_BERJALAN, list(range(1, 32)))
        _v20_mock_rekap(
            os.path.join(rpe, "1.12 Rekap Mentah Bulan Lalu", "LALU.xlsx"),
            "SO LALU", _V20_REKAP_LALU, list(range(25, 32)))
        _v20_mock_4205(os.path.join(rpe, "4. 42.05", "a.xlsx"),
                       [("IT.2026.08.5", "GUDANG HO (MLGPAR)", 5,
                         "BRG-PREF", 15)])
        _v20_mock_4205(
            os.path.join(rpe, "4.1 4205 Bulan Lalu", "lalu.xlsx"),
            [("IT.2026.08.28", "GUDANG HO (MLGPAR)", 28, "BRG-PREF", 40)],
            sheet=lalu_sheet_4205)
        _v20_mock_3224(os.path.join(rpe, "13. 32.24 RI", "b.xlsx"),
                       [(5, "GUDANG HO (MLGPAR)", "BRG-PREF", 20)])
        _v20_mock_3224(
            os.path.join(rpe, "13.2 3224 RI Bulan Lalu", "lalu.xlsx"),
            [(28, "GUDANG HO (MLGPAR)", "BRG-PREF", 40)],
            sheet=lalu_sheet_3224)
        return _v20_config(root_e)

    cfg_a = Config(build_tree("#42.05. Rincian Pemindahan LALU",
                              "#32.24. Rincian Penerimaan LALU"))
    det = {}
    qin = query_in(cfg_a, detail_out=det)
    srcs = set(det["df"]["SOURCE IN"].unique())
    check20("T14a query_in menemukan SEMUA 4 sumber (lalu beda nama)",
            {"32.24", "32.24 (Bulan Lalu)", "42.05", "42.05 (Bulan Lalu)"}
            <= srcs, str(sorted(srcs)))
    check20("T14b semua baris JENIS IN", (qin["JENIS"] == "IN").all())

    cfg_b = Config(build_tree("#42.05. Rincian Pemindahan Bara",
                              "#32.24. Rincian Penerimaan Bara"))
    det_b = {}
    qin_b = query_in(cfg_b, detail_out=det_b)
    check20("T14c jumlah baris IN identik (fallback ≠ duplikat/inflasi)",
            len(qin) == len(qin_b) and len(det["df"]) == len(det_b["df"]),
            f"{len(qin)} == {len(qin_b)}")

    final_e = build_append1(cfg_a)
    check20("T15a SOURCE DATA sampai output final (1.SO per tanggal)",
            _v20_source_at(final_e, "BRG-TIE1", 10) == "input so harian"
            and _v20_source_at(final_e, "BRG-PAD", 5) == "input so harian")
    so_pair = final_e[(final_e["JENIS"] == "4.IN")
                      & (final_e["Nama Barang"] == "BRG-PREF")
                      & (final_e["Tanggal"] == -28)]
    check20("T15b IN lalu (-28) dari 42.05+32.24 lalu masuk metrik",
            len(so_pair) == 1 and so_pair["NILAI"].iloc[0] == 80,
            f"NILAI={so_pair['NILAI'].tolist() if len(so_pair) else '-'}")

    print(f"    ✓ [6b] v3.9.20/35-d: {n_ok[0]}/{n_ok[0]} checks OK")
    return True


# =============================================================================
# MAIN TEST
# =============================================================================

def run_test():
    """Run full pipeline test with mock data."""
    print("=" * 60)
    print("  TESTING PIPELINE WITH MOCK DATA")
    print("=" * 60)

    # Create temp dir for mock data
    test_dir = tempfile.mkdtemp(prefix="stock_test_")
    root_path = os.path.join(test_dir, "9.NEW QUERY")
    os.makedirs(root_path, exist_ok=True)

    # Global barang list (used across all mock files)
    global barbar_list
    barbar_list = [
        ("GULA (V.20)", "KG"),
        ("FRUCTOSE SYRUP (V.20)", "KG"),
        ("CINCAU (V.20)", "KG"),
    ]

    resto = "MLGPAR"

    print("\n  [1] Creating mock data files...")

    # Create all mock files
    create_mock_rekap_mentah(os.path.join(root_path, "1. DEVIASI WEEKLY", f"{resto}.xlsx"), resto, barbar_list, "berjalan")
    create_mock_rekap_mentah(os.path.join(root_path, "1.12 Rekap Mentah Bulan Lalu", f"{resto}.xlsx"), resto, barbar_list, "lalu")
    create_mock_2205(os.path.join(root_path, "2. 22.05", "penjualan.xlsx"), resto, barbar_list)
    create_mock_3224(os.path.join(root_path, "13. 32.24 RI", "ri.xlsx"), resto, barbar_list, "berjalan")
    create_mock_3224(os.path.join(root_path, "13.2 3224 RI Bulan Lalu", "ri_lalu.xlsx"), resto, barbar_list, "lalu")
    create_mock_4215(os.path.join(root_path, "3.1 42.15 Kirim", "kirim.xlsx"), resto, barbar_list)
    create_mock_4205(os.path.join(root_path, "4. 42.05", "pemindahan.xlsx"), resto, barbar_list)
    # v3.9.17: sumber IN baru — 4.1 4205 Bulan Lalu (mirror 32.24 lalu)
    create_mock_4205(os.path.join(root_path, "4.1 4205 Bulan Lalu", "pemindahan_lalu.xlsx"), resto, barbar_list, "lalu")
    create_mock_4217(os.path.join(root_path, "6.1 42.17 Saldo Awal", "saldo.xlsx"), resto, barbar_list)
    create_mock_pi(os.path.join(root_path, "26.Rincian PI", "pi.xlsx"), resto, barbar_list)
    create_mock_konversi(os.path.join(root_path, "27.Konversi Satuan Dex", "konversi.xlsx"), barbar_list)
    create_mock_dbs_kategori(os.path.join(root_path, "21. DBS Kategori", "kategori.xlsx"), barbar_list)
    create_mock_rincian_po(os.path.join(root_path, "25. Rincian PO", "po.xlsx"), resto, barbar_list)
    create_mock_9901(os.path.join(root_path, "30. 9901", "mutasi.xlsx"), resto, barbar_list)

    print(f"  Mock data created at: {root_path}")

    # Create config
    config_path = os.path.join(test_dir, "config.json")
    import json
    config_data = {
        "RootPath": root_path + os.sep,
        "Folders": {
            "RekapBerjalan":  "1. DEVIASI WEEKLY",
            "RekapLalu":      "1.12 Rekap Mentah Bulan Lalu",
            "Penjualan2205":  "2. 22.05",
            "Kirim4215":      "3.1 42.15 Kirim",
            "Terima4215":     "3. 42.15",
            "RI3224":         "13. 32.24 RI",
            "RI3224Lalu":     "13.2 3224 RI Bulan Lalu",
            "PI":             "26.Rincian PI",
            "SaldoAwal4217":  "6.1 42.17 Saldo Awal",
            "KonversiSatuan": "27.Konversi Satuan Dex",
            "DBSKategori":    "21. DBS Kategori",
            "Pemindahan4205": "4. 42.05",
            "Pemindahan4205Lalu": "4.1 4205 Bulan Lalu",
            "RincianPO":      "25. Rincian PO",
            "Data9901":       "30. 9901"
        },
        "Sheets": {
            "RekapMentah":     "REKAP MENTAH",
            "Penjualan2205":   "#22.05. Rincian Penjualan per B",
            "Pemindahan4215":  "#42.15. Pemindahan Barang (KIRI",
            "Penerimaan3224":  "#32.24. Rincian Penerimaan Bara",
            "SaldoAwal4217":   "#42.17. Kuantitas Barang per Gu",
            "FakturPembelian": "#32.42. Rincian Faktur Pembelia",
            "KonversiSatuan":  "Sheet1",
            "DBSKategori":     "Sheet1",
            "Pemindahan4205":  "#42.05. Rincian Pemindahan Bara",
            "PesananPO":       "#32.43. Rincian Pesanan Pembeli"
        },
        "Output": {
            "TemplateFile": "template/Mutasi Barang - Template.xlsx",
            "DefaultOutput": "output/Mutasi Barang.xlsx"
        }
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    # Load config
    config = Config(config_path)
    # v3.5: LightMode dihapus — pipeline selalu FULL (10 InfoColumns
    # selalu diproses). Tidak perlu override apa pun.

    # Test individual fn modules
    print("\n  [2] Testing individual fn modules...")

    from src.pipeline.fn_2205 import fn_2205
    from src.pipeline.fn_3224 import fn_3224
    from src.pipeline.fn_4205 import fn_4205
    from src.pipeline.fn_4215 import fn_4215
    from src.pipeline.fn_4217 import fn_4217

    # NOTE: fn_pi + fn_konversi_satuan dihapus di refactor
    # "hapus PI + Konversi Satuan" — test PI/Konversi dihapus sesuai pipeline.
    from src.pipeline.fn_dbs_kategori import fn_dbs_kategori
    from src.pipeline.fn_rekap_mentah import fn_rekap_mentah
    from src.pipeline.fn_running_stock import fn_running_stock

    # Test fn_dbs_kategori
    kat = fn_dbs_kategori(config.folder("DBSKategori"))
    print(f"    fn_dbs_kategori: {len(kat)} rows, cols={list(kat.columns)}")
    assert len(kat) > 0, "DBS Kategori should have data"

    # Test fn_2205
    q2205 = fn_2205(config.folder("Penjualan2205"))
    print(f"    fn_2205: {len(q2205)} rows, cols={list(q2205.columns)}")
    assert len(q2205) > 0, "2205 should have data"
    assert "NAMA RESTO" in q2205.columns
    # Check resto code extraction
    assert q2205["NAMA RESTO"].iloc[0] == "MLGPAR", f"Expected MLGPAR, got {q2205['NAMA RESTO'].iloc[0]}"

    # Test fn_3224
    q3224 = fn_3224(config.folder("RI3224"), "berjalan")
    print(f"    fn_3224 (berjalan): {len(q3224)} rows, cols={list(q3224.columns)}")
    assert len(q3224) > 0, "3224 berjalan should have data"

    q3224_lalu = fn_3224(config.folder("RI3224Lalu"), "lalu")
    print(f"    fn_3224 (lalu): {len(q3224_lalu)} rows")
    if len(q3224_lalu) > 0:
        # Tanggal should be negative for lalu
        assert q3224_lalu["Tanggal"].iloc[0] < 0, "3224 lalu Tanggal should be negative"

    # Test fn_4215
    q4215 = fn_4215(config.folder("Kirim4215"), "kirim")
    print(f"    fn_4215: {len(q4215)} rows, cols={list(q4215.columns)}")
    assert len(q4215) > 0, "4215 should have data"

    # Test fn_4205
    q4205 = fn_4205(config.folder("Pemindahan4205"))
    print(f"    fn_4205: {len(q4205)} rows, cols={list(q4205.columns)}")
    assert len(q4205) > 0, "4205 should have data"

    # v3.9.17: fn_4205 mode "lalu" — 5 hari terakhir + Tanggal negatif
    q4205_lalu = fn_4205(config.folder("Pemindahan4205Lalu"), mode="lalu")
    print(f"    fn_4205 (lalu): {len(q4205_lalu)} rows")
    assert len(q4205_lalu) > 0, "4205 lalu should have data"
    assert (q4205_lalu["Tanggal"] < 0).all(), "4205 lalu Tanggal should be negative"
    assert (q4205_lalu["Tanggal"] == -28).all(), "4205 lalu = max tanggal (28) negated"
    # query_in: sumber baru masuk gabungan + detail per dokumen
    from src.pipeline.queries import query_in
    _det = {}
    qin = query_in(config, detail_out=_det)
    _srcs = set(_det["df"]["SOURCE IN"].unique())
    assert "42.05 (Bulan Lalu)" in _srcs, f"42.05 (Bulan Lalu) missing: {_srcs}"
    assert (qin["JENIS"] == "IN").all()
    print(f"    query_in (v3.9.17): {len(qin)} rows; sources={sorted(_srcs)}")

    # v3.9.17: folder tidak ada → 0 baris senyap (bulan tanpa file lalu)
    q4205_missing = fn_4205(
        os.path.join(root_path, "4.1 4205 Bulan Lalu TIDAK ADA"), mode="lalu")
    assert len(q4205_missing) == 0, "missing folder should return 0 rows"
    print("    fn_4205 (folder tidak ada): 0 rows — senyap OK")

    # v3.9.17: config lama TANPA key Pemindahan4205Lalu → Config men-default
    # key kanonis (anti KeyError saat git pull config ter-modifikasi)
    from src.pipeline.queries import query_4205_bulan_lalu
    _cfg_lama_data = json.loads(json.dumps(config_data))
    _cfg_lama_data["Folders"] = {
        k: v for k, v in config_data["Folders"].items()
        if k != "Pemindahan4205Lalu"}
    _tmp_cfg = os.path.join(test_dir, "config_lama.json")
    with open(_tmp_cfg, "w", encoding="utf-8") as _f:
        json.dump(_cfg_lama_data, _f)
    _cfg_from_file = Config(config_path=_tmp_cfg)
    assert _cfg_from_file.folder("Pemindahan4205Lalu") == \
        os.path.join(root_path, "4.1 4205 Bulan Lalu"), \
        "Config harus men-default key baru"
    q4205_lama = query_4205_bulan_lalu(_cfg_from_file)
    assert len(q4205_lama) > 0, "config lama (default) harus tetap menemukan folder"
    os.unlink(_tmp_cfg)
    print("    config lama tanpa key baru → default kanonis (0 KeyError)")

    # Test fn_4217
    q4217 = fn_4217(config.folder("SaldoAwal4217"))
    print(f"    fn_4217: {len(q4217)} rows, cols={list(q4217.columns)}")
    assert len(q4217) > 0, "4217 should have data"
    assert q4217["JENIS"].iloc[0] == "SALDO AWAL"
    assert q4217["Tanggal"].iloc[0] == 1

    # Test fn_rekap_mentah
    rekap = fn_rekap_mentah(config.folder("RekapBerjalan"), "berjalan", ["BARANG MASUK", "SO"])
    print(f"    fn_rekap_mentah (berjalan): {len(rekap)} rows, cols={list(rekap.columns)}")
    assert len(rekap) > 0, "Rekap mentah should have data"

    # Test fn_running_stock
    import pandas as pd
    test_rs = pd.DataFrame({
        "Nama Barang": ["GULA"] * 5,
        "NAMA RESTO": ["MLGPAR"] * 5,
        "Tanggal": [-2, -1, 1, 2, 3],
        "IN": [0, 0, 30, 40, 50],
        "OUT": [0, 0, 10, 10, 10],
        "SALDO AWAL": [100, 100, 100, 100, 100],
    })
    rs_result = fn_running_stock(test_rs)
    print(f"    fn_running_stock: {len(rs_result)} rows, SALDO AKHIR={rs_result['SALDO AKHIR'].tolist()}")
    expected = [0, 0, 120, 150, 190]
    actual = rs_result["SALDO AKHIR"].tolist()
    assert actual == expected, f"Running stock mismatch: expected {expected}, got {actual}"
    print("    ✓ Running stock algorithm CORRECT!")

    print("\n  [3] All fn modules PASSED!")

    # Test full pipeline (Append1 + Rincian PO)
    print("\n  [4] Testing full pipeline (Append1)...")
    append1_df = build_append1(config)
    print(f"    Append1: {len(append1_df)} rows")
    print(f"    Columns: {list(append1_df.columns)}")

    expected_cols = ["Nama Barang", "NAMA RESTO", "Tanggal", "JENIS", "NILAI",
                     "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT", "KATEGORI", "SOURCE KIRIMAN"]
    for col in expected_cols:
        assert col in append1_df.columns, f"Missing column: {col}"

    # Check JENIS values
    jenis_values = set(append1_df["JENIS"].unique())
    print(f"    JENIS values: {jenis_values}")
    expected_jenis = {"1.SO", "2.SALDO AKHIR", "3.DEVIASI", "4.IN", "5.BARANG MASUK", "7.Selisih IN", "8.BARANG KELUAR", "9.ACR", "SALDO AWAL"}
    assert jenis_values == expected_jenis, f"JENIS mismatch: expected {expected_jenis}, got {jenis_values}"

    # Check KATEGORI
    kat_values = set(append1_df["KATEGORI"].dropna().unique())
    print(f"    KATEGORI values: {kat_values}")
    assert "DEVIASI" in kat_values

    # v3.9.19 — SOURCE DATA rekap mentah (JENIS SO) dibawa sampai output
    # append1 (merge per pasangan barang×resto — bahan CEK "Promix 04"
    # di deviasi_view; mock menulis "input so harian")
    assert "SOURCE DATA" in append1_df.columns, "Missing column: SOURCE DATA"
    _so_rows = append1_df[append1_df["JENIS"] == "1.SO"]
    _src_vals = set(_so_rows["SOURCE DATA"].dropna().astype(str))
    print(f"    SOURCE DATA (1.SO): {_src_vals}")
    assert _src_vals == {"input so harian"}, \
        f"SOURCE DATA mismatch: got {_src_vals}"

    print("\n  [5] Testing Rincian PO...")
    rincian_po_df = build_rincian_po(config)
    print(f"    Rincian PO: {len(rincian_po_df)} rows")
    assert len(rincian_po_df) > 0, "Rincian PO should have data (filtered by DEVIASI)"
    assert "DBS_Kategori.KATEGORI" in rincian_po_df.columns
    # All rows should be DEVIASI
    assert all(rincian_po_df["DBS_Kategori.KATEGORI"] == "DEVIASI")

    # Test DataFrame return (no Excel output — data displayed in UI)
    print("\n  [6] Testing pipeline DataFrame return...")
    from src.main import run_pipeline
    # v3.5: run_pipeline return 4 (append1, rincian_po, in_detail, audit_result)
    append1_result, rincian_result, in_detail_result, audit_result = run_pipeline(
        config_path=config_path, verbose=False)
    # Verify DataFrames returned with correct columns (not exact row count — LightMode may differ)
    expected_append1_cols = ["Nama Barang", "NAMA RESTO", "Tanggal", "JENIS", "NILAI",
                             "KATEGORI", "SOURCE KIRIMAN"]
    for col in expected_append1_cols:
        assert col in append1_result.columns, f"Missing column in run_pipeline result: {col}"
    assert len(append1_result) > 0, "run_pipeline Append1 should have data"
    assert len(rincian_result) > 0, "run_pipeline Rincian PO should have data"
    # v3.4: IN detail per dokumen (42.05/32.24/99.01 + nomor)
    assert in_detail_result is not None, "run_pipeline should return in_detail DataFrame"
    expected_detail_cols = ["NAMA RESTO", "Nama Barang", "Tanggal", "Value",
                            "Nomor", "SOURCE IN"]
    for col in expected_detail_cols:
        assert col in in_detail_result.columns, f"Missing in_detail column: {col}"
    print(f"    ✓ run_pipeline returns 4 DataFrames correctly (incl. IN detail v3.4 + audit v3.5)")
    print(f"    Append1: {len(append1_result)} rows, cols: {list(append1_result.columns)}")
    print(f"    Rincian PO: {len(rincian_result)} rows")
    print(f"    IN detail: {len(in_detail_result)} rows")

    # v3.9.27 — audit_result membawa KEDUA varian (mode Hitung Bulan Ini
    # / Lalu + Ini tab Rekap Selisih IN): kunci lama tetap varian PENUH,
    # kunci baru = varian bulan berjalan saja (baris Tanggal negatif
    # dibuang sebelum engine — mirror sheet LAPORAN_DEVIASI).
    for k in ("df", "kpi", "desc", "df_bulan_ini", "kpi_bulan_ini",
              "desc_bulan_ini"):
        assert k in audit_result, f"Missing audit_result key: {k}"
    _aud_full = audit_result["df"]
    _aud_bi = audit_result["df_bulan_ini"]
    assert _aud_full is not None and _aud_bi is not None
    _t_full = pd.to_numeric(_aud_full["Tanggal"], errors="coerce")
    _t_bi = pd.to_numeric(_aud_bi["Tanggal"], errors="coerce")
    assert (_t_bi >= 1).all(), (
        "varian bulan-ini masih memuat baris Tanggal negatif/bulan lalu")
    assert not (_t_full < 0).any() or len(_aud_bi) <= len(_aud_full), (
        "varian bulan-ini tidak boleh lebih besar dari varian penuh")
    assert audit_result["kpi_bulan_ini"].get("rows") == len(_aud_bi)
    print(f"    ✓ v3.9.27 audit_result 2 varian: penuh {len(_aud_full)} "
          f"baris · bulan-ini {len(_aud_bi)} baris (tanpa Tanggal "
          f"negatif)")

    # v3.9.20 — deep-audit pipeline fixes (agent 35-d): LANGKAH 9 tie/NA/
    # strip, fn_4205 lalu anchor resto, resolusi sheet folder lalu, e2e
    run_test_v3920_fixes()

    # Test view widgets (smoke test)
    print("\n  [7] Testing view widgets...")
    import time
    import tkinter as tk
    from tkinter import ttk

    def wait_view(root, view, timeout=15.0):
        """Pump event loop sampai render async view selesai (v3.1)."""
        t0 = time.time()
        while getattr(view, "_busy", False) and time.time() - t0 < timeout:
            root.update()
            time.sleep(0.01)
        t0 = time.time()
        while time.time() - t0 < 0.4:
            root.update()
            time.sleep(0.01)

    root = tk.Tk()
    root.withdraw()  # don't show window

    # v3.2: load_data kini LAZY (view tak terlihat → defer). Test memanggil
    # ensure_refreshed() langsung — persis yang app lakukan saat tab dipilih.

    # Test PivotTableView (long format pivot)
    from src.ui.pivot_view import PivotTableView
    pv = PivotTableView(root)
    pv.load_data(append1_df)
    pv.ensure_refreshed()
    wait_view(root, pv)
    children = pv.tree.get_children()
    assert len(children) > 0, "Pivot tree should have rows after load_data"
    print(f"    ✓ PivotTableView loaded: {len(children)} item rows")

    # Test DeviasiView (GR + PCS) — mock pakai SATUAN "KG" → PCS(non-GR)
    # berisi baris, GR memang 0 (perilaku benar utk data KG)
    from src.ui.deviasi_view import DeviasiView
    dv = DeviasiView(root, satuan_mode="GR")
    dv.load_data(append1_df)
    dv.ensure_refreshed()
    wait_view(root, dv)
    children = dv.tree.get_children()
    print(f"    ✓ DeviasiView (GR) loaded: {len(children)} rows (KG≠GR)")

    dv2 = DeviasiView(root, satuan_mode="PCS")
    dv2.load_data(append1_df)
    dv2.ensure_refreshed()
    wait_view(root, dv2)
    children2 = dv2.tree.get_children()
    assert len(children2) > 0, "Deviasi PCS (non-GR/KG) tree should have rows"
    print(f"    ✓ DeviasiView (PCS) loaded: {len(children2)} rows")

    # Test rincian view widget
    from src.ui.rincian_po_view import RincianPoView
    rv = RincianPoView(root)
    rv.load_data(rincian_po_df)
    rv.ensure_refreshed()
    wait_view(root, rv)
    children = rv.tree.get_children()
    assert len(children) > 0, "Rincian tree should have rows after load_data"
    print(f"    ✓ RincianPoView loaded: {len(children)} rows")

    # v3.2: FollowUpView + toggle ✓ (roundtrip kecil)
    from src.ui.followup import FollowUpStore
    from src.ui.followup_view import FollowUpView
    fs = FollowUpStore()
    fu = FollowUpView(root, fs, get_data=lambda: append1_df)
    snap = {"asal": "DEVIASI GR", "resto": "MLGPAR",
            "barang": "AYAM FILET", "satuan": "GR", "aktif": "AKTIF",
            "h": 25, "so": 80.0, "sistem": 10.0, "deviasi": 70.0,
            "cek": "Hitung Manual"}
    from src.ui.followup import row_fingerprint
    fp = row_fingerprint(snap)
    fs.toggle(fp, snap)
    root.update()
    assert len(fu.tree.get_children("")) == 1, \
        "Follow Up tree should render snapshot"
    print("    ✓ FollowUpView renders snapshot + toggle ✓")
    fs.toggle(fp, snap)
    root.destroy()

    print("\n  [8] UI widgets PASSED!")

    # Cleanup
    print("\n  [9] Cleaning up test data...")
    shutil.rmtree(test_dir)

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED! ✓")
    print("=" * 60)

    return True


if __name__ == "__main__":
    barbar_list = []
    try:
        success = run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
