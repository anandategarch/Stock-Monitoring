"""
test_mock.py — Test pipeline dengan mock data yang match format Accurate Online export.
Membuat folder + file Excel mock, lalu menjalankan pipeline end-to-end.
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
