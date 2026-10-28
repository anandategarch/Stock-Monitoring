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
    """Create #32.24 sheet.
    v3.9.31: + kolom konversi 'Satuan' + 'Rasio Satuan' (mock KG→GR
    rasio 1000 — E2E konversi qty PO Menunggu ke satuan terkecil)."""
    headers = ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
               "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan",
               "Satuan", "Rasio Satuan"]
    data_rows = []
    for i, (barang, satuan) in enumerate(barang_list):
        tgl = 5 if mode == "berjalan" else 28
        data_rows.append([
            datetime(2026, 9, tgl),
            20 + i,
            barang,
            f"GUDANG MALANG ({resto_code})",
            f"IT.2026.09.{2000+i}",
            f"PO.2026.09.{3000+i}",
            datetime(2026, 9, 3, 16, 52, 12),
            satuan,          # v3.9.31 — satuan dokumen (KG)
            1000,            # v3.9.31 — rasio → satuan terkecil (GR)
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
    """Create #42.05 sheet (mode 'lalu': tanggal ujung bulan = 28).
    v3.9.31: + kolom konversi '#Sat. Kirim'/'Rasio Satuan'/
    '#Sat. Terkecil' (mock KG→GR rasio 1000 — E2E konversi PO)."""
    headers = ["Nomor #Terima", "Gudang #Terima", "Tanggal #Terima", "Nama Barang",
               "#Qty. Terkecil", "#Tgl/Jam Pembuatan IT",
               "#Sat. Kirim", "Rasio Satuan", "#Sat. Terkecil"]
    data_rows = []
    tgl = 5 if mode == "berjalan" else 28
    nomor_base = 4000 if mode == "berjalan" else 5000
    for i, (barang, satuan) in enumerate(barang_list):
        data_rows.append([
            f"IT.2026.09.{nomor_base+i}",
            f"GUDANG BANDUNG ({resto_code})",
            datetime(2026, 9, tgl),
            barang,
            15 + i,
            datetime(2026, 9, tgl - 1, 10, 30, 0),
            satuan,          # v3.9.31 — #Sat. Kirim (satuan dokumen KG)
            1000,            # v3.9.31 — Rasio Satuan
            "GR",            # v3.9.31 — #Sat. Terkecil
        ])
    create_mock_file(filepath, "#42.05. Rincian Pemindahan Bara", headers, data_rows, metadata_rows=4)


def create_mock_4217(filepath, resto_code, barang_list):
    """Create #42.17 sheet (saldo awal). UnpivotOtherColumns format.
    v3.9.32: kolom KATEGORI BARANG (pola header grup — hanya baris
    pertama grup berisi, sisanya None → uji ffill fn_4217) + KODE
    BARANG (pseudo-kolom non-resto — terbuang oleh mask NAMA RESTO,
    uji defensif) + NAMA SATUAN per barang + 2 barang ekstra:
    'BUMBU PASTA KUAH' (saldo-only — TIDAK ada di rekap/IN/out; uji
    fitur tampil di Deviasi GR + SATUAN fallback) & 'SUPPLIES ITEM'
    (kategori di luar whitelist → terfilter oleh fn_4217)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "#42.17. Kuantitas Barang per Gu"

    # Metadata (row 1-4)
    for i in range(4):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i+1}")

    # Headers (row 5) — urutan ala file asli (kategori/satuan sebagai kolom)
    ws.cell(row=5, column=1, value="Nama Barang")
    ws.cell(row=5, column=2, value="Kode Barang")
    ws.cell(row=5, column=3, value="Kategori Barang")
    ws.cell(row=5, column=4, value="Nama Satuan")
    ws.cell(row=5, column=5, value=f"RESTO MALANG ({resto_code})")

    # Data (row 6+)
    rows = []
    for i, (barang, satuan) in enumerate(barang_list):
        # kategori hanya di baris pertama grup (pola header grup real)
        rows.append([barang, 90000 + i,
                     "10.FOOD [RM] - COM V.2" if i == 0 else None,
                     satuan, 200 + i * 10])
    # v3.9.32 — barang saldo-only (kategori eksplisit; tanpa rekap)
    rows.append(["BUMBU PASTA KUAH", 90999,
                 "10.FOOD [RM] - COM V.2", "GR", 84])
    # v3.9.32 — barang kategori di luar whitelist (terfilter)
    rows.append(["SUPPLIES ITEM", 90998,
                 "SUPPLIES [OTHERS]", "PCS", 999])

    for r_idx, row_data in enumerate(rows, 6):
        for c_idx, val in enumerate(row_data, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def create_mock_4109(filepath, barang_list):
    """v3.9.32 — Create #41.09. Nilai Persediaan [ALL] (folder 09.Harga).

    Mirror struktur file user 4109.xlsx: 4 baris metadata + header 2
    baris (grup 'Saldo Awal/Masuk/Keluar/Saldo Akhir' + sub
    'Kuantitas/Nilai'; Keluar Nilai terpisah 1 kolom spacer) + baris
    subtotal 'Total Nama Barang' per grup + kategori ber-pola header
    grup (ffill di fn_4109). Harga contoh:
    - GULA (V.20): 18,25/GR (rekap KG → uji normalisasi ×1000 → 18.250/KG)
    - CINCAU (V.20): 15/KG (sama dgn rekap → harga langsung)
    - FRUCTOSE (V.20): Qty 0 → harga NaN (uji guard div-0)
    - BUMBU PASTA KUAH: 12/GR (saldo-only pair)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    # openpyxl tidak bisa menulis '[' pada judul sheet (file user asli
    # dibuat Accurate) — mock pakai nama tanpa kurung; fn_4109 punya
    # fallback resolusi nama sheet ternormalisasi (buang [ ] ( ) spasi).
    ws.title = "#41.09. Nilai Persediaan ALL"

    # Metadata (row 1-4)
    ws.cell(row=1, column=4, value="PPA")
    ws.cell(row=2, column=4, value="#41.09. Nilai Persediaan [ALL]")
    ws.cell(row=3, column=4, value="Dari 01 Okt 2026 s/d 07 Okt 2026")
    ws.cell(row=4, column=4, value="Cabang : [Semua Cabang]")

    # Header row 5-6 (0-idx 4/5): posisi ala file user
    # 0=Kategori 1=Nama 4=Kode 5=Satuan 6/7=SaldoAwal 8/9=Masuk
    # 10=Keluar Qty 12=Keluar Nilai 13/14=Saldo Akhir (Qty/Nilai)
    hdr = {4: ["Kategori Barang", "Nama Barang", None, None,
               "Kode Barang", "Nama Satuan", "Saldo Awal", None, "Masuk",
               None, "Keluar", None, None, "Saldo Akhir", None],
           5: [None, None, None, None, None, None, "Kuantitas", "Nilai",
               "Kuantitas", "Nilai", "Kuantitas", None, "Nilai",
               "Kuantitas", "Nilai"]}
    for r, vals in hdr.items():
        for c, v in enumerate(vals, 1):
            if v is not None:
                ws.cell(row=r, column=c, value=v)

    data = {
        "GULA (V.20)":        ("GR", 1000, 18250),    # 18,25/GR
        "FRUCTOSE SYRUP (V.20)": ("GR", 0, 0),        # Qty 0 → NaN
        "CINCAU (V.20)":      ("KG", 500, 7500),      # 15/KG
        "BUMBU PASTA KUAH":   ("GR", 700, 8400),      # 12/GR
    }
    rows = []
    kat_first = True
    for barang, (sat, qty, nil) in data.items():
        rows.append(["10.FOOD [RM] - COM V.2" if kat_first else None,
                     barang, None, None, 88001, sat,
                     qty, nil, 0, 0, 0, None, 0, qty, nil])
        kat_first = False
    rows.append(["21.COST.ASSET", "BARANG ASSET LAIN", None, None,
                 88999, "UNIT", 5, 5000, 0, 0, 0, None, 0, 5, 5000])
    # subtotal per grup (dibuang fn_4109)
    rows.append([None, "Total Nama Barang", None, None, None, None,
                 None, None, None, None, None, None, None,
                 sum(r[13] or 0 for r in rows), None])

    for r_idx, row_data in enumerate(rows, 7):
        for c_idx, val in enumerate(row_data, 1):
            if val is not None:
                ws.cell(row=r_idx, column=c_idx, value=val)

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

    for i, (barang, _) in enumerate(barang_list):
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


def run_test_v3949_rekap_kategori():
    """[6c] v3.9.49: KATEGORI Rekap Mentah DIBAWA (per-resto + combined)
    + PRIORITAS atas master '21. DBS Kategori' di append1 LANGKAH 5c
    (user: "sebenernya sudah ada KATEGORI dari file Rekap Mentah folder
    Deviasi Weekly jadi bisa ambil kategori dari situ"; default gabungan
    'COM DEVIASI - RESTO + Biaya Packaging - RESTO')."""
    n_ok = [0]

    def check49(name, cond, detail=""):
        assert cond, f"FAIL: {name} {detail}"
        n_ok[0] += 1
        print(f"    OK {name}" + ((" — " + detail) if detail else ""))

    print("\n  [6c] (v3.9.49) KATEGORI Rekap Mentah — bawa kolom + prioritas")
    tmp = tempfile.mkdtemp(prefix="t3949_kat_")
    root = os.path.join(tmp, "9.NEW QUERY")

    # --- 1. rekap BERJALAN per-resto DENGAN kolom KATEGORI (pola sheet
    #         user '1  DEVIASI WEEKLY': KATEGORI tepat setelah NAMA RESTO) —
    #         GULA → COM DEVIASI - RESTO; CINCAU → Biaya Packaging - RESTO.
    def _write_rekap_kat(filepath, mode, kategori_on, sheet="REKAP MENTAH"):
        days = list(range(1, 32)) if mode == "berjalan" else list(range(25, 32))
        headers = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS",
                   "NAMA BARANG", "SATUAN"]
        if kategori_on:
            headers.insert(1, "KATEGORI")
        headers += [str(d) for d in days]
        data = []
        for barang, satuan, kat in (
                ("GULA (V.20)", "GR", "COM DEVIASI - RESTO"),
                ("CINCAU (V.20)", "KG", "Biaya Packaging - RESTO")):
            for jenis in ("SO", "BARANG MASUK"):
                row = ["MLGPAR.001"]
                if kategori_on:
                    row.append(kat)
                row += ["input so harian", jenis, "OK", barang, satuan]
                row += [100 if (d == 1 and jenis == "SO") else 0
                        for d in days]
                data.append(row)
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
    _write_rekap_kat(os.path.join(root, "1. DEVIASI WEEKLY", "MLGPAR.xlsx"),
                     "berjalan", kategori_on=True)
    # rekap LALU TANPA KATEGORI (schema lama — back-compat: kolom opsional)
    _write_rekap_kat(os.path.join(root, "1.12 Rekap Mentah Bulan Lalu",
                                  "MLGPAR.xlsx"),
                     "lalu", kategori_on=False)
    # master: SEMUA barang → DEVIASI (harus DITIMPA kategori rekap utk
    # barang ber-rekap; BUMBU PASTA KUAH saldo-only TETAP master)
    create_mock_dbs_kategori(
        os.path.join(root, "21. DBS Kategori", "kategori.xlsx"),
        [("GULA (V.20)", "GR"), ("CINCAU (V.20)", "KG"),
         ("BUMBU PASTA KUAH", "GR")])
    # 42.17: BUMBU PASTA KUAH saldo-only (whitelist 10.FOOD — pola
    # create_mock_4217 barang ekstra)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "#42.17. Kuantitas Barang per Gu"
    for i in range(4):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i + 1}")
    ws.cell(row=5, column=1, value="Nama Barang")
    ws.cell(row=5, column=2, value="Kode Barang")
    ws.cell(row=5, column=3, value="Kategori Barang")
    ws.cell(row=5, column=4, value="Nama Satuan")
    ws.cell(row=5, column=5, value="RESTO MALANG (MLGPAR)")
    ws.cell(row=6, column=1, value="BUMBU PASTA KUAH")
    ws.cell(row=6, column=2, value=100383)
    ws.cell(row=6, column=3, value="10.FOOD [RM] - COM V.2")
    ws.cell(row=6, column=4, value="GR")
    ws.cell(row=6, column=5, value=84)
    os.makedirs(os.path.join(root, "6.1 42.17 Saldo Awal"), exist_ok=True)
    wb.save(os.path.join(root, "6.1 42.17 Saldo Awal", "saldo.xlsx"))
    wb.close()

    import json as _json  # noqa: F401 — konsisten pola seksi lain
    cfg_path = _v20_config(root, sheets={
        "RekapMentah": "REKAP MENTAH",
        "SaldoAwal4217": "#42.17. Kuantitas Barang per Gu",
        "DBSKategori": "Sheet1",
    })
    cfg = Config(cfg_path)

    # --- 2. fn_rekap_mentah: kolom KATEGORI dibawa (jalur per-resto) ---
    from src.pipeline.fn_rekap_mentah import fn_rekap_mentah
    rk = fn_rekap_mentah(cfg.folder("RekapBerjalan"), "berjalan",
                         ["BARANG MASUK", "SO"])
    check49("fn_rekap_mentah (per-resto): KATEGORI DIBAWA bila sheet "
            "punya kolom itu",
            "KATEGORI" in rk.columns and len(rk) > 0,
            f"cols={list(rk.columns)}")
    _gk = rk[rk["NAMA BARANG"] == "GULA (V.20)"]["KATEGORI"].dropna()
    check49("fn_rekap_mentah: nilai KATEGORI rekap utuh (GULA → "
            "COM DEVIASI - RESTO)",
            set(_gk) == {"COM DEVIASI - RESTO"}, f"got {set(_gk)}")
    rk_l = fn_rekap_mentah(cfg.folder("RekapLalu"), "lalu",
                           ["BARANG MASUK", "SO"])
    check49("fn_rekap_mentah: schema LAMA tanpa KATEGORI tetap didukung "
            "(kolom opsional — output tak berkolom KATEGORI)",
            "KATEGORI" not in rk_l.columns and len(rk_l) > 0,
            f"cols={list(rk_l.columns)}")

    # --- 3. combined workbook (fallback) bawa KATEGORI ------------------
    tmp2 = tempfile.mkdtemp(prefix="t3949_comb_")
    comb_dir = os.path.join(tmp2, "1. DEVIASI WEEKLY")
    # sheet BUKAN 'REKAP MENTAH' → jalur per-resto tak menemukan apa pun
    # → fallback combined (NAMA RESTO dari KOLOM — pola workbook user
    # '01.1 CEK STOCK V2.xlsb' sheet '1  DEVIASI WEEKLY').
    _write_rekap_kat(os.path.join(comb_dir, "CEK STOCK V2.xlsx"),
                     "berjalan", kategori_on=True,
                     sheet="1  DEVIASI WEEKLY")
    rkc = fn_rekap_mentah(comb_dir, "berjalan", ["BARANG MASUK", "SO"])
    check49("fn_rekap_mentah (combined fallback): KATEGORI DIBAWA",
            "KATEGORI" in rkc.columns and len(rkc) > 0,
            f"cols={list(rkc.columns)}")

    # --- 4. append1 LANGKAH 5c: prioritas rekap atas master -------------
    final = build_append1(cfg)
    check49("append1: barang ber-rekap → KATEGORI rekap MENIMPA master "
            "'DEVIASI' (GULA → COM DEVIASI - RESTO)",
            set(final[final["Nama Barang"] == "GULA (V.20)"]
                ["KATEGORI"].dropna()) == {"COM DEVIASI - RESTO"})
    check49("append1: CINCAU → Biaya Packaging - RESTO (rekap)",
            set(final[final["Nama Barang"] == "CINCAU (V.20)"]
                ["KATEGORI"].dropna()) == {"Biaya Packaging - RESTO"})
    check49("append1: BUMBU PASTA KUAH saldo-only (TANPA rekap) TETAP "
            "kategori master 'DEVIASI'",
            set(final[final["Nama Barang"] == "BUMBU PASTA KUAH"]
                ["KATEGORI"].dropna()) == {"DEVIASI"})

    # --- 5. unit helpers (dipakai semua view) ---------------------------
    import pandas as _pd

    from src.pipeline.helpers import (
        KATEGORI_DEFAULT_LABEL,
        kategori_filter_mask,
        kategori_has_default_values,
        kategori_multi_values,
        kategori_passthrough,
    )
    check49("kategori_multi_values: label gabungan → 2 nilai rekap",
            kategori_multi_values(KATEGORI_DEFAULT_LABEL) ==
            ("COM DEVIASI - RESTO", "Biaya Packaging - RESTO"))
    check49("kategori_multi_values: seleksi biasa/None → None",
            kategori_multi_values("DEVIASI") is None
            and kategori_multi_values(None) is None)
    check49("kategori_passthrough: HANYA legacy 'deviasi' (v3.9.53 — "
            "label gabungan kini STRICT: barang tanpa kategori TIDAK "
            "lagi lolos seleksi default, user BASKOM)",
            kategori_passthrough(KATEGORI_DEFAULT_LABEL) is False
            and kategori_passthrough("deviasi") is True
            and kategori_passthrough("BAHAN") is False)
    _s = _pd.Series(["COM DEVIASI - RESTO", "BAHAN", None,
                     "biaya packaging - resto"])
    check49("kategori_has_default_values: case-insensitive + strip",
            kategori_has_default_values(_s) is True
            and kategori_has_default_values(
                _pd.Series(["BAHAN", "DEVIASI"])) is False
            and kategori_has_default_values(None) is False)
    _m = kategori_filter_mask(_s, KATEGORI_DEFAULT_LABEL)
    check49("kategori_filter_mask: cocok 2 nilai (case-insensitive), "
            "bukan None bila label gabungan",
            _m is not None and _m.tolist() == [True, False, False, True])
    check49("kategori_filter_mask: None bila bukan label gabungan",
            kategori_filter_mask(_s, "DEVIASI") is None)

    print(f"    ✓ [6c] v3.9.49: {n_ok[0]}/{n_ok[0]} checks OK")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(tmp2, ignore_errors=True)
    return True


# =============================================================================
# MAIN TEST
# =============================================================================

def run_test_v3950_audit_fixes():
    """[6d] v3.9.50 (deep audit 3-b): LANGKAH 5c — token blank '-'
    tidak menimpa master + precedence BERJALAN atas LALU (keep=last)
    + deteksi KATEGORI per-resto whitespace-tolerant + helper
    case-insensitive."""
    n_ok = [0]

    def check50(name, cond, detail=""):
        assert cond, f"FAIL: {name} {detail}"
        n_ok[0] += 1
        print(f"    OK {name}" + ((" — " + detail) if detail else ""))

    print("\n  [6d] (v3.9.50) audit 3-b: filter '-' 5c + precedence berjalan "
          "+ header whitespace-tolerant")
    tmp = tempfile.mkdtemp(prefix="t3950_kat_")
    root = os.path.join(tmp, "9.NEW QUERY")

    def _write_rekap(filepath, mode, kategori_on, sheet="REKAP MENTAH",
                     resto="MLGPAR.001", kat_header="KATEGORI",
                     items=(("GULA (V.20)", "GR", "COM DEVIASI - RESTO"),)):
        days = list(range(1, 32)) if mode == "berjalan" else list(range(25, 32))
        headers = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS",
                   "NAMA BARANG", "SATUAN"]
        if kategori_on:
            headers.insert(1, kat_header)
        headers += [str(d) for d in days]
        data = []
        for barang, satuan, kat in items:
            for jenis in ("SO", "BARANG MASUK"):
                row = [resto]
                if kategori_on:
                    row.append(kat)
                row += ["input so harian", jenis, "OK", barang, satuan]
                row += [100 if (d == 1 and jenis == "SO") else 0
                        for d in days]
                data.append(row)
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

    # BERJALAN: GULA → COM DEVIASI - RESTO; SAOS → '-' (token blank,
    # TIDAK boleh menimpa master 'DEVIASI')
    _write_rekap(
        os.path.join(root, "1. DEVIASI WEEKLY", "MLGPAR.xlsx"), "berjalan",
        kategori_on=True,
        items=(("GULA (V.20)", "GR", "COM DEVIASI - RESTO"),
               ("SAOS (V.20)", "GR", "-"),
               ("CINCAU (V.20)", "KG", "Biaya Packaging - RESTO")))
    # LALU: GULA → 'LALU STALE' (nilai basi — HARUS kalah dari berjalan)
    _write_rekap(
        os.path.join(root, "1.12 Rekap Mentah Bulan Lalu", "MLGPAR.xlsx"),
        "lalu", kategori_on=True,
        items=(("GULA (V.20)", "GR", "LALU STALE"),))
    # master: semua barang DEVIASI
    create_mock_dbs_kategori(
        os.path.join(root, "21. DBS Kategori", "kategori.xlsx"),
        [("GULA (V.20)", "GR"), ("SAOS (V.20)", "GR"),
         ("CINCAU (V.20)", "KG"), ("BUMBU PASTA KUAH", "GR")])
    # 42.17: BUMBU saldo-only (barang TANPA rekap → tetap master)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "#42.17. Kuantitas Barang per Gu"
    for i in range(4):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i + 1}")
    ws.cell(row=5, column=1, value="Nama Barang")
    ws.cell(row=5, column=2, value="Kode Barang")
    ws.cell(row=5, column=3, value="Kategori Barang")
    ws.cell(row=5, column=4, value="Nama Satuan")
    ws.cell(row=5, column=5, value="RESTO MALANG (MLGPAR)")
    ws.cell(row=6, column=1, value="BUMBU PASTA KUAH")
    ws.cell(row=6, column=2, value=100383)
    ws.cell(row=6, column=3, value="10.FOOD [RM] - COM V.2")
    ws.cell(row=6, column=4, value="GR")
    ws.cell(row=6, column=5, value=84)
    os.makedirs(os.path.join(root, "6.1 42.17 Saldo Awal"), exist_ok=True)
    wb.save(os.path.join(root, "6.1 42.17 Saldo Awal", "saldo.xlsx"))
    wb.close()

    cfg = Config(_v20_config(root, sheets={
        "RekapMentah": "REKAP MENTAH",
        "SaldoAwal4217": "#42.17. Kuantitas Barang per Gu",
        "DBSKategori": "Sheet1",
    }))

    # --- 1. append1 5c: precedence + '-' + master fallback -------------
    final = build_append1(cfg)
    check50("5c keep=last: GULA ada di rekap LALU ('LALU STALE') DAN "
            "BERJALAN ('COM DEVIASI - RESTO') → BERJALAN menang (bulan "
            "berjalan otoritatif; dulu nilai basi lalu menang diam-diam)",
            set(final[final["Nama Barang"] == "GULA (V.20)"]
                ["KATEGORI"].dropna()) == {"COM DEVIASI - RESTO"})
    check50("5c token blank '-': SAOS ber-rekap '-' TIDAK menimpa master "
            "'(tetap DEVIASI — cermin kategori_blank_mask)",
            set(final[final["Nama Barang"] == "SAOS (V.20)"]
                ["KATEGORI"].dropna()) == {"DEVIASI"})
    check50("5c barang TANPA rekap tetap master: BUMBU saldo-only → "
            "DEVIASI",
            set(final[final["Nama Barang"] == "BUMBU PASTA KUAH"]
                ["KATEGORI"].dropna()) == {"DEVIASI"})
    check50("5c nilai rekap normal tetap menimpa: CINCAU → "
            "Biaya Packaging - RESTO",
            set(final[final["Nama Barang"] == "CINCAU (V.20)"]
                ["KATEGORI"].dropna()) == {"Biaya Packaging - RESTO"})

    # --- 2. fn_rekap_mentah per-resto: header 'KATEGORI ' (trailing
    #         space) tetap terdeteksi (whitespace-tolerant) -------------
    tmp2 = tempfile.mkdtemp(prefix="t3950_ws_")
    _write_rekap(os.path.join(tmp2, "MLGPAR.xlsx"), "berjalan",
                 kategori_on=True, kat_header="KATEGORI ")
    from src.pipeline.fn_rekap_mentah import fn_rekap_mentah
    rk_ws = fn_rekap_mentah(tmp2, "berjalan", ["BARANG MASUK", "SO"])
    check50("fn_rekap_mentah per-resto: header 'KATEGORI ' (trailing "
            "space) tetap DIBAWA (dulu dibuang senyap — parity jalur "
            "combined)",
            "KATEGORI" in rk_ws.columns and len(rk_ws) > 0
            and rk_ws["KATEGORI"].dropna().astype(str).str.strip().eq(
                "COM DEVIASI - RESTO").any(),
            f"cols={list(rk_ws.columns)}")

    # --- 3. helper case-insensitive (audit 3-b asimetri) ---------------
    from src.pipeline.helpers import kategori_multi_values as _kmv
    check50("kategori_multi_values: label gabungan LOWERCASE dikenali "
            "(case-insensitive — parity passthrough)",
            _kmv("com deviasi - resto + biaya packaging - resto")
            == ("COM DEVIASI - RESTO", "Biaya Packaging - RESTO"))
    check50("kategori_multi_values: label lain tetap None (strict)",
            _kmv("DEVIASI") is None and _kmv(None) is None)

    print(f"    ✓ [6d] v3.9.50: {n_ok[0]}/{n_ok[0]} checks OK")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(tmp2, ignore_errors=True)
    return True


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
    # v3.9.32: BUMBU PASTA KUAH (saldo-only) ikut master DBS supaya
    # lolos filter KATEGORI default 'Deviasi' di tab Deviasi GR
    create_mock_dbs_kategori(os.path.join(root_path, "21. DBS Kategori", "kategori.xlsx"),
                              barbar_list + [("BUMBU PASTA KUAH", "GR")])
    # v3.9.32 — harga 41.09 (folder 09.Harga; key config disetdefault)
    create_mock_4109(os.path.join(root_path, "09.Harga", "4109.xlsx"), barbar_list)
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
            "Data9901":       "30. 9901",
            "Harga":          "09.Harga"   # v3.9.32 (setdefault juga jalan)
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
    print("    ✓ run_pipeline returns 4 DataFrames correctly (incl. IN detail v3.4 + audit v3.5)")
    print(f"    Append1: {len(append1_result)} rows, cols: {list(append1_result.columns)}")
    print(f"    Rincian PO: {len(rincian_result)} rows")
    print(f"    IN detail: {len(in_detail_result)} rows")

    # v3.9.37 — 🔄 REFRESH FILE SUMBER (cache bacaan, user: "ada tombol
    # refresh untuk file sumber, bisa gak? dan gak harus refresh semua
    # tapi"): (1) run di atas mengisi cache bacaan per file+sheet; (2) SATU
    # file sumber diubah (penjualan 22.05 + barang baru) + invalidasi
    # SELEKTIF file itu saja; (3) run ulang → data barang baru MASUK
    # (bacaan baru dipakai) TANPA membaca ulang file lain (statistik
    # miss/hit per file).
    from src.pipeline.helpers import (
        read_cache_invalidate,
        read_cache_reset_counters,
        read_cache_stats,
    )
    _ent0, _nf0, _hit0, _miss0 = read_cache_stats()
    assert _nf0 >= 5, (
        f"v3.9.37: cache bacaan harus terisi oleh run di atas — got {_nf0} file")
    _penj37 = os.path.join(root_path, "2. 22.05", "penjualan.xlsx")
    assert os.path.exists(_penj37)
    _n_inv37 = read_cache_invalidate([_penj37])
    assert _n_inv37 >= 1, (
        f"v3.9.37: invalidasi selektif penjualan.xlsx harus membuang >=1 "
        f"entry — got {_n_inv37}")
    # ubah isi file (barang baru) — bacaan baru harus dipakai run berikut
    create_mock_2205(_penj37, resto, barbar_list + [("SUSU UHT V37", "LTR")])
    read_cache_reset_counters()
    _a37, _r37, _in37, _aud37 = run_pipeline(config_path=config_path,
                                             verbose=False)
    _susu37 = _a37[_a37["Nama Barang"] == "SUSU UHT V37"]
    assert len(_susu37) > 0, (
        "v3.9.37: barang baru di file yang di-refresh harus masuk "
        f"append1 — got {len(_susu37)} rows")
    _ent37, _nf37, _hit37, _miss37 = read_cache_stats()
    assert _miss37 == 1, (
        "v3.9.37: HANYA file yang di-refresh boleh dibaca ulang dari "
        f"disk — got miss={_miss37} file")
    assert _hit37 >= _nf0 - 1, (
        "v3.9.37: file lain harus disajikan dari cache (gak harus "
        f"refresh semua) — hit={_hit37} dari {_nf0} file")
    print(f"    ✓ v3.9.37 Refresh File Sumber: barang baru masuk via "
          f"refresh selektif 1 file; file lain dari cache "
          f"(dibaca ulang: {_miss37} · cache: {_hit37})")

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

    # v3.9.30 — PO MENUNGGU DIPROSES (32.43) ikut audit lewat pipeline:
    # kolom 'Qty PO Menunggu' + KPI 'dev_murni_po' di KEDUA varian (mock
    # PO semua ber-status 'Menunggu diproses' dgn Cabang PO
    # '1370.MLGPAR' → pasangan mock barang MLGPAR ke-match)
    for _k30 in ("df", "df_bulan_ini"):
        assert "Qty PO Menunggu" in audit_result[_k30].columns, (
            f"v3.9.30: Missing 'Qty PO Menunggu' in audit_result[{_k30!r}]")
    for _k30 in ("kpi", "kpi_bulan_ini"):
        assert "dev_murni_po" in audit_result[_k30], (
            f"v3.9.30: Missing KPI 'dev_murni_po' in audit_result[{_k30!r}]")
    _po_qty_m = pd.to_numeric(_aud_full["Qty PO Menunggu"],
                              errors="coerce").fillna(0)
    assert _po_qty_m.sum() > 0, (
        "v3.9.30: Qty PO Menunggu harus > 0 utk pasangan mock (PO mock "
        "ber-status 'Menunggu diproses' — join Cabang PO→resto gagal?)")
    print(f"    ✓ v3.9.30 PO Menunggu di audit: kolom + KPI di kedua "
          f"varian · dev_murni_po={audit_result['kpi'].get('dev_murni_po')} "
          f"· qty total {_po_qty_m.sum():.0f}")

    # v3.9.31 — KONVERSI SATUAN PO MENUNGGU (mock 42.05/32.24 ber-kolom
    # 'Rasio Satuan' KG→GR 1000; PO mock Satuan=KG): qty PO dikalikan
    # rasio → satuan terkecil (GULA 10, FRUCTOSE 11, CINCAU 12 KG →
    # 10.000 / 11.000 / 12.000 GR) — apple-to-apple dgn Selisih/Saldo
    # (dulu qty satuan PO mentah 10/11/12)
    assert _po_qty_m.max() == 12000.0, (
        f"v3.9.31: konversi KG×1000 gagal — max Qty PO Menunggu = "
        f"{_po_qty_m.max()} (harusnya 12.000 utk CINCAU 12 KG)")
    _note31 = " | ".join(
        _aud_full.loc[_po_qty_m > 0, "Detail & Catatan Audit"]
        .astype(str).tolist())
    assert "(qty 12.000 GR)" in _note31, (
        "v3.9.31: catatan PO Menunggu harus berlabel satuan terkecil "
        f"'(qty 12.000 GR)' — got {_note31!r}")
    assert "qty sat. terkecil" in audit_result["desc"], (
        "v3.9.31: desc audit harus menyebut 'qty sat. terkecil' — got "
        f"{audit_result['desc']!r}")
    print("    ✓ v3.9.31 konversi satuan PO: max 12.000 GR (12 KG × "
          "1000) · catatan '(qty 12.000 GR)' · desc 'qty sat. terkecil'")

    # v3.9.32 — (4) FILTER KATEGORI 42.17 + SATUAN 42.17 + (3) SALDO-ONLY
    # + (5) HARGA 41.09 (E2E pipeline): mock 4217 ber-kolom Kategori
    # Barang (pola grup) + Nama Satuan + 2 barang ekstra (BUMBU PASTA
    # KUAH saldo-only & SUPPLIES ITEM di luar whitelist) + mock 41.09.
    from src.pipeline.fn_4217 import DEFAULT_KATEGORI_WHITELIST as _WL
    from src.pipeline.fn_4217 import fn_4217 as _fn4217
    _q17 = _fn4217(config.folder("SaldoAwal4217"),
                    kategori_whitelist=_WL)
    _q17_names = set(_q17["Nama Barang"].astype(str))
    assert "SUPPLIES ITEM" not in _q17_names, (
        "v3.9.32: whitelist kategori harus menyaring 'SUPPLIES ITEM'")
    assert "BUMBU PASTA KUAH" in _q17_names, (
        "v3.9.32: barang kategori RM V.2 harus lolos whitelist")
    assert "SATUAN" in _q17.columns and (
        _q17[_q17["Nama Barang"] == "BUMBU PASTA KUAH"]["SATUAN"]
        .astype(str).str.strip() == "GR").all(), (
        "v3.9.32: kolom Nama Satuan 42.17 harus keluar sebagai SATUAN")
    _q17_nofilter = _fn4217(config.folder("SaldoAwal4217"))
    assert "SUPPLIES ITEM" in set(
        _q17_nofilter["Nama Barang"].astype(str)), (
        "v3.9.32: tanpa whitelist → tanpa filter (kompatibel)")
    # append1: pasangan saldo-only dapat SATUAN fallback 42.17 (rekap
    # tetap menang utk pasangan ber-rekap)
    _bp = append1_result[append1_result["Nama Barang"]
                         == "BUMBU PASTA KUAH"]
    assert not _bp.empty and (_bp["SATUAN"].astype(str).str.strip()
                              == "GR").all(), (
        "v3.9.32: pasangan 42.17-only harus dapat SATUAN dari file 42.17")
    assert "SUPPLIES ITEM" not in set(
        append1_result["Nama Barang"].astype(str)), (
        "v3.9.32: saldo barang di luar whitelist tidak boleh masuk "
        "pipeline (filter lebih awal)")
    # (5) harga 41.09 E2E
    assert "harga_map" in audit_result and "konversi_map" in \
        audit_result, "v3.9.32: audit_result harus bawa harga_map + konversi_map"
    _hm = audit_result["harga_map"]
    assert _hm.get("GULA (V.20)") == (18.25, "GR"), (
        f"v3.9.32: harga GULA harus 18,25/GR — got {_hm.get('GULA (V.20)')}")
    assert _hm.get("CINCAU (V.20)") == (15.0, "KG"), (
        f"v3.9.32: harga CINCAU harus 15/KG — got {_hm.get('CINCAU (V.20)')}")
    assert _hm.get("FRUCTOSE SYRUP (V.20)")[0] is None, (
        "v3.9.32: Qty Saldo Akhir 0 → harga None (guard div-0)")
    assert "BARANG ASSET LAIN" in _hm, "v3.9.32: barang non-DEVIASI tetap dibaca 41.09"
    _hmm_rows = [r for r in ["GULA (V.20)", "CINCAU (V.20)",
                             "FRUCTOSE SYRUP (V.20)", "BUMBU PASTA KUAH",
                             "BARANG ASSET LAIN"]]
    assert all(r in _hm for r in _hmm_rows), "v3.9.32: semua barang mock 41.09 masuk peta"
    print(f"    ✓ v3.9.32: 4217 kategori whitelist ({len(_q17)}/{len(_q17_nofilter)}"
          f" baris) + SATUAN fallback + harga 41.09 ({len(_hm)} barang)")

    # v3.9.20 — deep-audit pipeline fixes (agent 35-d): LANGKAH 9 tie/NA/
    # strip, fn_4205 lalu anchor resto, resolusi sheet folder lalu, e2e
    run_test_v3920_fixes()

    # v3.9.49 — KATEGORI Rekap Mentah: bawa kolom + prioritas atas master
    run_test_v3949_rekap_kategori()
    run_test_v3950_audit_fixes()

    # Test view widgets (smoke test)
    print("\n  [7] Testing view widgets...")
    import time
    import tkinter as tk

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

    # v3.9.32 — (3) BARANG 42.17-ONLY TAMPIL (BUMBU PASTA KUAH saldo 84
    # tanpa rekap): H=25 (window 23..27 — dulu pasangan lenyap karena
    # fn_4217 hardcode Tanggal=1) → Sistem = saldo 42.17 = 84, Deviasi
    # = 0 − 84 = (84)
    dv.tanggal_h = 25
    dv._dirty = True
    dv.ensure_refreshed()
    wait_view(root, dv)
    _bp_iid = None
    for _iid in dv.tree.get_children(""):
        if "BUMBU PASTA KUAH" in str(dv.tree.item(_iid, "values")):
            _bp_iid = _iid
            break
    assert _bp_iid is not None, (
        "v3.9.32: barang 42.17-only (BUMBU PASTA KUAH) harus tampil di "
        "Deviasi GR saat H=25")
    assert dv.tree.set(_bp_iid, "Sistem") == "84", (
        f"v3.9.32: Sistem saldo-only = saldo 42.17 (84) — got "
        f"{dv.tree.set(_bp_iid, 'Sistem')!r}")
    assert dv.tree.set(_bp_iid, "Deviasi") == "(84)", (
        f"v3.9.32: Deviasi saldo-only = 0−84 format (84) — got "
        f"{dv.tree.set(_bp_iid, 'Deviasi')!r}")
    assert dv.tree.set(_bp_iid, "Satuan") == "GR", (
        "v3.9.32: Satuan pair saldo-only harus dari 42.17 'Nama Satuan'")
    print("    ✓ v3.9.32: BUMBU PASTA KUAH (42.17-only) tampil di GR — "
          "Sistem 84 · Deviasi (84) · Satuan GR")

    # v3.9.32 — (6) MODE NOMINAL E2E: Harga 41.09 × Qty Deviasi +
    # normalisasi satuan (GULA 18,25/GR → 18.250/KG utk rekap KG via
    # peta rasio; CINCAU 15/KG langsung) + baris TOTAL + FRUCTOSE tanpa
    # harga (Qty 0 → None → tak dihitung)
    from src.ui.nominal_deviasi_view import NominalDeviasiView
    nv = NominalDeviasiView(root)
    nv.load_data(append1_result,
                 harga_map=audit_result["harga_map"],
                 konversi_map=audit_result["konversi_map"])
    # H=1: mock SO(1)=100; saldo(1) = SA + IN-9901(1) → GULA 205 → DEV
    # −105; FRUCTOSE 220 → DEV −120 (tanpa harga); CINCAU 220 → DEV −120
    nv.tanggal_h = 1
    nv._dirty = True
    nv.ensure_refreshed()
    wait_view(root, nv)
    _nv_rows = {dv0: nv.tree.item(iid, "values")
                for iid, dv0 in [(i, str(nv.tree.set(i, "Nama Barang")))
                                 for i in nv.tree.get_children("")]}
    _g = _nv_rows.get("GULA (V.20)")
    assert _g is not None and _g[3] == "18.250 KG" and _g[5] == "(Rp 1.916.250)", (
        f"v3.9.51: GULA nominal = 18.250/KG × DEV −105 = (Rp 1.916.250) "
        f"— Currency Rp — got {_g}")
    _c = _nv_rows.get("CINCAU (V.20)")
    assert _c is not None and _c[3] == "15 KG" and _c[5] == "(Rp 1.800)", (
        f"v3.9.51: CINCAU nominal = 15/KG × DEV −120 = (Rp 1.800) — got {_c}")
    _f = _nv_rows.get("FRUCTOSE SYRUP (V.20)")
    assert _f is not None and _f[5] == "-", (
        f"v3.9.32: FRUCTOSE tanpa harga → nominal '-' — got {_f}")
    _t = _nv_rows.get("TOTAL")
    assert _t is not None and _t[5] == "(Rp 1.919.058)" and _t[4] == "(429)", (
        f"v3.9.51: baris TOTAL = −1.919.050? qty −429 (GULA−105 + "
        f"FRUCTOSE−120 + CINCAU−120 + BUMBU−84; nominal Rp tanpa "
        f"FRUCTOSE) — got {_t}")
    print("    ✓ v3.9.51: Nominal E2E Currency Rp — GULA "
          "(Rp 1.916.250) + CINCAU (Rp 1.800) + BUMBU (Rp 1.008) + "
          "TOTAL (Rp 1.919.058) · FRUCTOSE '-' tanpa harga")

    # v3.9.34 — (6b) TAB 🧮 NOMINAL DEVIASI E2E (user: "isinya total
    # sum dari nama barang ... cuman ini disum per resto"): Σ nominal
    # per resto + N barang + tanpa harga + baris TOTAL + kolom Nominal
    # tab Deviasi GR (Harga 41.09 dinormalkan × Deviasi).
    from src.ui.nominal_resto_view import NominalRestoView
    rv = NominalRestoView(root)
    rv.load_data(append1_result,
                 harga_map=audit_result["harga_map"],
                 konversi_map=audit_result["konversi_map"])
    rv.tanggal_h = 1
    rv._dirty = True
    rv.ensure_refreshed()
    wait_view(root, rv)
    _rrows = {str(rv.tree.set(i, "Resto")): rv.tree.item(i, "values")
              for i in rv.tree.get_children("")}
    # v3.9.63 — kolom N Barang/Tanpa Harga dihapus; kini [Resto, COM
    # Deviasi, Biaya Packaging, Nominal, Lalu, Persen] — mock tanpa
    # kategori COM/Packaging → '-' (Σ 0 via fmt_rp_cell).
    _m = _rrows.get("MLGPAR")
    assert _m is not None and str(_m[1]) == "-" and str(_m[2]) == "-" \
        and _m[3] == "(Rp 1.919.058)", (
        f"v3.9.63: MLGPAR Σ (Rp 1.919.058) "
        f"(GULA 1.916.250 + CINCAU 1.800 + BUMBU 1.008; FRUCTOSE tak "
        f"ikut; COM/Packaging '-' tanpa klas kategori) — got {_m}")
    _rt = _rrows.get("TOTAL")
    assert _rt is not None and str(_rt[1]) == "-" and str(_rt[2]) == "-" \
        and _rt[3] == "(Rp 1.919.058)", (
        f"v3.9.63: baris TOTAL Σ (Rp 1.919.058) — got {_rt}")
    assert "H=1" in str(rv.tree.heading("Nominal Deviasi")["text"]), (
        "v3.9.34: heading dinamis 'Nominal Deviasi (H=1)'")
    print("    ✓ v3.9.63: Nominal Deviasi E2E — MLGPAR Σ (Rp 1.919.058) "
          "+ COM/Packaging '-' + TOTAL + heading H dinamis")

    # v3.9.34 — (6c) KOLOM Nominal tab Deviasi GR (harga × Deviasi)
    dv34 = DeviasiView(root, satuan_mode="GR")
    dv34.load_data(append1_df,
                   harga_map=audit_result["harga_map"],
                   konversi_map=audit_result["konversi_map"])
    dv34.tanggal_h = 1     # H=1: GULA DEV −105 (sama dgn E2E Nominal)
    dv34._dirty = True
    dv34.ensure_refreshed()
    wait_view(root, dv34)
    # BUMBU PASTA KUAH = satuan GR (tampil di tab GR — GULA satuan KG
    # hanya tampil di tab PCS); DEV (84) × harga 12/GR = (1.008)
    _nom34 = None
    for _i34 in dv34.tree.get_children(""):
        if "BUMBU PASTA KUAH" in str(dv34.tree.item(_i34, "values")):
            _nom34 = str(dv34.tree.set(_i34, "Nominal"))
            break
    assert _nom34 == "(Rp 1.008)", (
        f"v3.9.51: Deviasi GR kolom Nominal BUMBU = 12/GR × DEV (84) "
        f"= (Rp 1.008) — Currency Rp — got {_nom34}")
    assert "Out_H" not in [c for c in dv34.tree["columns"]] and \
        "BK_H" not in [c for c in dv34.tree["columns"]], (
        "v3.9.34: kolom Out_H/BK_H dihapus dari tampilan Deviasi GR")
    print("    ✓ v3.9.51: Deviasi GR kolom Nominal BUMBU (Rp 1.008) + "
          "Out_H/BK_H dihapus dari tampilan")

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
