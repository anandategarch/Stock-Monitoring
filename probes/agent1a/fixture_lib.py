"""
fixture_lib.py — end-to-end synthetic pipeline fixture for audit probes.

Builds a minimal but realistic Accurate-export folder tree and runs the REAL
build_append1 pipeline. Designed to expose the "valid days / presence /
com(1) basis" semantics on sparse SO data:

Resto MLGPAR, satuan GR.
- AYAM (V.20)   : in 42.17 (SA=200); SO recorded days 1,2,4,5,6; no IN/BK/ACR.
- BEBEK (V.20)  : NOT in 42.17; rekap-lalu SO day28=40 (penutupan), BM day30=5;
                  SO berjalan days 1,2,4,5,6; IN(42.05) day3=10; ACR days 2,4,5,6.
- CITRA (V.20)  : in 42.17 (SA=100); rekap-lalu SO day28=100; SO days 5,6;
                  BM day2=7; IN(42.05) day2=5; ACR day6=20.

Usage:
    from fixture_lib import build
    final, in_detail, cfg = build()   # final = append1 long output
"""
import json
import os
import shutil
import tempfile
from datetime import datetime

import openpyxl

RESTO = "MLGPAR"

FOLDERS = {
    "RekapBerjalan":      "1. DEVIATION WEEKLY",
    "RekapLalu":          "1.12 Rekap Mentah Bulan Lalu",
    "Penjualan2205":      "2. 22.05",
    "Kirim4215":          "3.1 42.15 Kirim",
    "Terima4215":         "3. 42.15",
    "RI3224":             "13. 32.24 RI",
    "RI3224Lalu":         "13.2 3224 RI Bulan Lalu",
    "PI":                 "26.Rincian PI",
    "SaldoAwal4217":      "6.1 42.17 Saldo Awal",
    "KonversiSatuan":     "27.Konversi Satuan Dex",
    "DBSKategori":        "21. DBS Kategori",
    "Pemindahan4205":     "4. 42.05",
    "Pemindahan4205Lalu": "4.1 4205 Bulan Lalu",
    "RincianPO":          "25. Rincian PO",
    "Data9901":           "30. 9901",
    "Harga":              "09.Harga",
}
SHEETS = {
    "RekapMentah":     "REKAP MENTAH",
    "Penjualan2205":   "#22.05. Rincian Penjualan per B",
    "Pemindahan4215":  "#42.15. Pemindahan Barang (KIRI",
    "Penerimaan3224":  "#32.24. Rincian Penerimaan Bara",
    "SaldoAwal4217":   "#42.17. Kuantitas Barang per Gu",
    "FakturPembelian": "#32.42. Rincian Faktur Pembelia",
    "KonversiSatuan":  "Sheet1",
    "DBSKategori":     "Sheet1",
    "Pemindahan4205":  "#42.05. Rincian Pemindahan Bara",
    "PesananPO":       "#32.43. Rincian Pesanan Pembeli",
}


def _write_rekap(filepath, mode, rows):
    """Sheet 'REKAP MENTAH', header at Excel row 1 (per-resto file path).

    rows: list of (jenis, barang, {day: value}) — days not in dict are EMPTY
    (None) = 'tidak direkam', vs 0 = 'tercatat 0'.
    """
    days = list(range(1, 32)) if mode == "berjalan" else list(range(25, 32))
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "REKAP MENTAH"
    headers = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS",
               "NAMA BARANG", "SATUAN"] + [str(d) for d in days]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    for r, (jenis, barang, vals) in enumerate(rows, 2):
        base = [f"{RESTO}.001", "input so harian", jenis, "OK", barang, "GR"]
        for c, v in enumerate(base, 1):
            ws.cell(row=r, column=c, value=v)
        for i, d in enumerate(days):
            v = vals.get(d)
            if v is not None:
                ws.cell(row=r, column=7 + i, value=v)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def _write_meta_sheet(filepath, sheet, headers, data_rows, meta=4):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet[:31]
    for i in range(meta):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i+1}")
    hr = meta + 1
    for c, h in enumerate(headers, 1):
        ws.cell(row=hr, column=c, value=h)
    for r, row in enumerate(data_rows, hr + 1):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def build_tree(root):
    """Create all mock source files under root. Returns root."""
    rek = os.path.join(root, FOLDERS["RekapBerjalan"], f"{RESTO}.xlsx")
    _write_rekap(rek, "berjalan", [
        ("SO", "AYAM (V.20)",  {1: 190, 2: 185, 4: 175, 5: 170, 6: 165}),
        ("SO", "BEBEK (V.20)", {1: 30, 2: 25, 4: 15, 5: 10, 6: 8}),
        ("SO", "CITRA (V.20)", {5: 100, 6: 160}),
        ("BARANG MASUK", "CITRA (V.20)", {2: 7}),
    ])
    rk_lalu = os.path.join(root, FOLDERS["RekapLalu"], f"{RESTO}.xlsx")
    _write_rekap(rk_lalu, "lalu", [
        ("SO", "AYAM (V.20)",  {28: 200}),
        ("SO", "BEBEK (V.20)", {28: 40}),
        ("SO", "CITRA (V.20)", {28: 100}),
        ("BARANG MASUK", "BEBEK (V.20)", {30: 5}),
    ])
    # 22.05 penjualan (ACR) — BEBEK days 2,4,5,6 ; CITRA day 6
    p2205 = os.path.join(root, FOLDERS["Penjualan2205"], "penjualan.xlsx")
    rows = []
    for i, (brg, d, q) in enumerate([
            ("BEBEK (V.20)", 2, 3), ("BEBEK (V.20)", 4, 4),
            ("BEBEK (V.20)", 5, 5), ("BEBEK (V.20)", 6, 6),
            ("CITRA (V.20)", 6, 20)]):
        rows.append([f"ACR.2026.09.{1000+i}", datetime(2026, 9, d),
                     f"RESTO MALANG ({RESTO})", brg, q])
    _write_meta_sheet(p2205, "#22.05. Rincian Penjualan per B",
                      ["Nomor #", "Tanggal", "Nama Pelanggan",
                       "Nama Barang", "Kuantitas"], rows)
    # 42.05 pemindahan (IN) — BEBEK day3=10, CITRA day2=5
    p4205 = os.path.join(root, FOLDERS["Pemindahan4205"], "pemindahan.xlsx")
    rows = []
    for i, (brg, d, q) in enumerate([
            ("BEBEK (V.20)", 3, 10), ("CITRA (V.20)", 2, 5)]):
        rows.append([f"IT.2026.09.{4000+i}", f"GUDANG BANDUNG ({RESTO})",
                     datetime(2026, 9, d), brg, q,
                     datetime(2026, 9, d - 1, 10, 30, 0),
                     "GR", 1, "GR"])
    _write_meta_sheet(p4205, "#42.05. Rincian Pemindahan Bara",
                      ["Nomor #Terima", "Gudang #Terima", "Tanggal #Terima",
                       "Nama Barang", "#Qty. Terkecil",
                       "#Tgl/Jam Pembuatan IT", "#Sat. Kirim",
                       "Rasio Satuan", "#Sat. Terkecil"], rows)
    # 42.17 saldo awal — AYAM 200, CITRA 100 (BEBEK sengaja TIDAK ada)
    p4217 = os.path.join(root, FOLDERS["SaldoAwal4217"], "saldo.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "#42.17. Kuantitas Barang per Gu"
    for i in range(4):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i+1}")
    for c, h in enumerate(["Nama Barang", "Kode Barang", "Kategori Barang",
                           "Nama Satuan", f"RESTO MALANG ({RESTO})"], 1):
        ws.cell(row=5, column=c, value=h)
    for r, row in enumerate([
            ["AYAM (V.20)", 90001, "10.FOOD [RM] - COM V.2", "GR", 200],
            ["CITRA (V.20)", 90002, "10.FOOD [RM] - COM V.2", "GR", 100]], 6):
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=v)
    os.makedirs(os.path.dirname(p4217), exist_ok=True)
    wb.save(p4217)
    wb.close()
    return root


def make_config(root):
    cfg_path = os.path.join(root, "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"RootPath": root + os.sep, "Folders": FOLDERS,
                   "Sheets": SHEETS,
                   "Output": {"TemplateFile": "t.xlsx",
                              "DefaultOutput": "o.xlsx"}}, f)
    return cfg_path


def build():
    """Run REAL pipeline on synthetic tree → (append1_long, in_detail, cfg)."""
    import sys
    sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
    from src.config import Config
    from src.pipeline.append1 import build_append1

    tmp = tempfile.mkdtemp(prefix="a1a_fix_")
    root = build_tree(os.path.join(tmp, "root"))
    cfg = Config(make_config(root))
    in_detail_out = {}
    rekap_out = {}
    konv_out = {}
    ss_out = {}
    final = build_append1(cfg, in_detail_out=in_detail_out,
                          rekap_so_out=rekap_out, konversi_out=konv_out,
                          saldo_sistem_out=ss_out)
    return final, in_detail_out.get("df"), rekap_out.get("df"), cfg, tmp


if __name__ == "__main__":
    final, det, rek, cfg, tmp = build()
    import pandas as pd
    pd.set_option("display.width", 200)
    print("append1 rows:", len(final))
    print(final[["Nama Barang", "NAMA RESTO", "Tanggal", "JENIS", "NILAI"]]
          .to_string(max_rows=200))
    print("\ntmpdir:", tmp)
