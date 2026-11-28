"""
synth_data.py — Generator dataset SINTETIS untuk benchmark (P1).

Menghasilkan pohon folder + workbook Excel yang meniru skema export
Accurate Online PERSIS skema test_mock.py (REKAP MENTAH per resto,
#22.05, #32.24 berjalan+lalu, #42.15, #42.05 berjalan+lalu, #42.17,
#41.09, konversi, DBS kategori, #32.43 PO, 9901) sehingga pipeline
produksi bisa dijalankan END-TO-END tanpa data bisnis nyata.

KEAMANAN DATA:
- Semua nama barang/resto/pemasok adalah SINTETIS generik
  ("BRG SYN 0001 (V.20)", "RS01A") — TIDAK ada nama restoran,
  barang, atau informasi bisnis operasional di dataset/log benchmark.
- File hanya ditulis ke folder temporary benchmark (data-dir), TIDAK
  menyentuh RootPath/config user.
- Deterministik: seed RNG sama → dataset byte-sama (cache read
  signature mtime+size tetap valid antar skenario).

Skala parametrik: n_restos × n_barangs = jumlah pasangan (pair).
Jumlah baris Append1 aktual diukur SETELAH pipeline (≈ pairs ×
~9 JENIS × tanggal teramati) — target skala (100k/300k/600k/900k)
adalah ORIENTASI, bukan klaim; angka aktual dilaporkan apa adanya.
"""
import json
import os
import random
from datetime import datetime
from pathlib import Path

import openpyxl

# Folder/sheet template — PERSIS test_mock.py (dibaca pipeline via
# config.json Folders/Sheets).
FOLDERS = {
    "RekapBerjalan":      "1. DEVIASI WEEKLY",
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

# Nilai tanggal/mock mengikuti konvensi test_mock (September 2026;
# bulan berjalan 1..31, bulan lalu 25..31 sebagai tanggal negatif).
TGL_BERJALAN = list(range(1, 32))
TGL_LALU = list(range(25, 32))


def resto_codes(n: int) -> list[str]:
    """Kode resto sintetis 4-karakter deterministik (RS01A, RS02B, ...)."""
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    out = []
    for i in range(n):
        out.append(f"RS{i:02d}{letters[i % len(letters)]}")
    return out


def barang_names(n: int) -> list[tuple[str, str]]:
    """(nama barang sintetis, satuan) — satuan bergantian KG/PCS
    supaya jalur 2-satuan ikut teruji."""
    out = []
    for i in range(n):
        sat = "KG" if i % 2 == 0 else "PCS"
        out.append((f"BRG SYN {i:04d} (V.20)", sat))
    return out


def _save(wb, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    wb.save(filepath)
    wb.close()


def _sheet_file(filepath, sheet_name, headers, rows):
    """File 4-baris metadata + header (row 5) + data — pola create_mock_file."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]
    for i in range(4):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i+1} - {sheet_name}")
    for c, h in enumerate(headers, 1):
        ws.cell(row=5, column=c, value=h)
    for r, row in enumerate(rows, 6):
        for c, v in enumerate(row, 1):
            if v is not None:
                ws.cell(row=r, column=c, value=v)
    _save(wb, filepath)


def write_rekap_mentah(filepath, resto, barangs, mode, rng):
    """REKAP MENTAH (header row 1) — SO + BARANG MASUK per barang.
    Nilai soal acak seeded supaya deviasi/growth bervariasi (bucket
    heatmap & minus ter-representasi)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "REKAP MENTAH"
    days = TGL_BERJALAN if mode == "berjalan" else TGL_LALU
    headers = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS",
               "NAMA BARANG", "SATUAN"] + [str(d) for d in days]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h)
    r = 2
    for barang, sat in barangs:
        # SO: tgl 1 pasti terisi (+ nilai acak di ~6 tanggal lain)
        so_vals = {1: 100 + rng.randrange(90)}
        for d in rng.sample(days, k=min(6, len(days))):
            so_vals.setdefault(d, rng.randrange(120))
        for jenis in ("SO", "BARANG MASUK"):
            row = [f"{resto}.001", "input so harian", jenis, "OK",
                   barang, sat]
            for d in days:
                v = so_vals.get(d, 0) if jenis == "SO" else (
                    rng.randrange(60) if d in (1, 5, 12, 19, 26) else 0)
                row.append(v)
            for c, v in enumerate(row, 1):
                ws.cell(row=r, column=c, value=v)
            r += 1
    _save(wb, filepath)


def write_4217(filepath, resto, barangs):
    """#42.17 saldo awal per resto (unpivot-other-columns, header row 5).
    + 1 barang saldo-only + 1 barang whitelist-out (paritas test_mock)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "#42.17. Kuantitas Barang per Gu"
    for i in range(4):
        ws.cell(row=i + 1, column=1, value=f"Metadata {i+1}")
    ws.cell(row=5, column=1, value="Nama Barang")
    ws.cell(row=5, column=2, value="Kode Barang")
    ws.cell(row=5, column=3, value="Kategori Barang")
    ws.cell(row=5, column=4, value="Nama Satuan")
    ws.cell(row=5, column=5, value=f"RESTO SYN ({resto})")
    rows = []
    for i, (barang, sat) in enumerate(barangs):
        rows.append([barang, 90000 + i,
                     "10.FOOD [RM] - COM V.2" if i == 0 else None,
                     sat, 200 + (i * 7) % 130])
    rows.append(["BRG SYN SALDO ONLY", 90999,
                 "10.FOOD [RM] - COM V.2", "GR", 84])
    rows.append(["BRG SYN SUPPLIES", 90998, "SUPPLIES [OTHERS]", "PCS", 999])
    for r, row in enumerate(rows, 6):
        for c, v in enumerate(row, 1):
            if v is not None:
                ws.cell(row=r, column=c, value=v)
    _save(wb, filepath)


def write_4109(filepath, barangs, rng):
    """#41.09 harga — 2-row header + subtotal (pola create_mock_4109)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "#41.09. Nilai Persediaan ALL"
    ws.cell(row=1, column=4, value="PPA")
    ws.cell(row=2, column=4, value="#41.09. Nilai Persediaan [ALL]")
    ws.cell(row=3, column=4, value="Dari 01 Sep 2026 s/d 30 Sep 2026")
    ws.cell(row=4, column=4, value="Cabang : [Semua Cabang]")
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
    rows = []
    for i, (barang, sat) in enumerate(barangs):
        qty = 1000 + rng.randrange(500)
        nil = qty * (10 + rng.randrange(20))
        rows.append(["10.FOOD [RM] - COM V.2" if i == 0 else None,
                     barang, None, None, 88001 + i, sat,
                     qty, nil, 0, 0, 0, None, 0, qty, nil])
    rows.append(["21.COST.ASSET", "BRG SYN ASSET", None, None,
                 88999, "UNIT", 5, 5000, 0, 0, 0, None, 0, 5, 5000])
    rows.append([None, "Total Nama Barang", None, None, None, None,
                 None, None, None, None, None, None, None,
                 sum(r[13] or 0 for r in rows), None])
    for r, row in enumerate(rows, 7):
        for c, v in enumerate(row, 1):
            if v is not None:
                ws.cell(row=r, column=c, value=v)
    _save(wb, filepath)


def generate_tree(data_dir: str, n_restos: int, n_barangs: int,
                  seed: int = 20260901) -> dict:
    """Buat seluruh pohon data sintetis + config.json.

    Return: {"root": RootPath, "config_path": ..., "n_pairs": ...,
             "n_files": ..., "files": [semua path]}
    """
    rng = random.Random(seed)
    root = Path(data_dir)
    restos = resto_codes(n_restos)
    barangs = barang_names(n_barangs)
    files = []

    # Rekap mentah per resto (berjalan + lalu)
    for resto in restos:
        p1 = str(root / FOLDERS["RekapBerjalan"] / f"{resto}.xlsx")
        p2 = str(root / FOLDERS["RekapLalu"] / f"{resto}.xlsx")
        write_rekap_mentah(p1, resto, barangs, "berjalan", rng)
        write_rekap_mentah(p2, resto, barangs, "lalu", rng)
        files += [p1, p2]
    # 42.17 saldo awal per resto
    for resto in restos:
        p = str(root / FOLDERS["SaldoAwal4217"] / f"{resto}.xlsx")
        write_4217(p, resto, barangs)
        files.append(p)

    # Transactional sheets — SATU file gabungan semua resto
    rows_2205 = []
    rows_3224 = []
    rows_3224_lalu = []
    rows_4215 = []
    rows_4205 = []
    rows_4205_lalu = []
    rows_po = []
    rows_9901 = []
    for ri, resto in enumerate(restos):
        for bi, (barang, sat) in enumerate(barangs):
            nbase = ri * 100000 + bi * 10
            rows_2205.append([
                f"ACR.2026.09.{100000 + nbase}",
                datetime(2026, 9, 5 + (bi % 20)),
                f"RESTO SYN ({resto})", barang, 10 + (bi % 30)])
            # 32.24: 2 event per pair (tanggal 5 & 12)
            for t in (5, 12):
                rows_3224.append([
                    datetime(2026, 9, t), 20 + (bi % 25), barang,
                    f"GUDANG SYN ({resto})",
                    f"IT.2026.09.{200000 + nbase + t}",
                    f"PO.2026.09.{300000 + nbase + t}",
                    datetime(2026, 9, 3, 16, 52, 12), sat, 1000])
            rows_3224_lalu.append([
                datetime(2026, 9, 28), 20 + (bi % 25), barang,
                f"GUDANG SYN ({resto})",
                f"IT.2026.08.{200000 + nbase}",
                f"PO.2026.08.{300000 + nbase}",
                datetime(2026, 8, 25, 9, 0, 0), sat, 1000])
            # 42.15 Kirim (BK): 1 event per pair
            rows_4215.append([
                datetime(2026, 9, 5 + (bi % 20)), f"GUDANG SYN ({resto})",
                barang, 5 + (bi % 15)])
            # 42.05 (IN): 1 event per pair (berjalan & lalu)
            rows_4205.append([
                f"IT.2026.09.{400000 + nbase}", f"GUDANG SYN ({resto})",
                datetime(2026, 9, 5), barang, 15 + (bi % 20),
                datetime(2026, 9, 4, 10, 30, 0), sat, 1000, "GR"])
            rows_4205_lalu.append([
                f"IT.2026.08.{500000 + nbase}", f"GUDANG SYN ({resto})",
                datetime(2026, 8, 28), barang, 15 + (bi % 20),
                datetime(2026, 8, 27, 10, 30, 0), sat, 1000, "GR"])
            # PO 32.43: 1 baris per pair
            rows_po.append([
                f"PO.2026.09.{600000 + nbase}", datetime(2026, 9, 5),
                f"1370.{resto}", "PM SYN BENCHMARK", barang, sat,
                10 + (bi % 20), 27000, (10 + (bi % 20)) * 27000, "REP",
                "Diproses Sebagian" if bi % 3 == 0 else "Diproses",
                datetime(2026, 9, 1, 8, 0, 0)])
        # 9901: 2 baris valid + 1 terfilter per resto
        for k in range(2):
            rows_9901.append([None, "Persediaan", 5.0 * (k + 1),
                              barangs[k][0], f"1137.{resto}", 5 + k])
        rows_9901.append(["RI-900", "Persediaan", 99.0, barangs[0][0],
                          f"1137.{resto}", 7])

    p = str(root / FOLDERS["Penjualan2205"] / "penjualan.xlsx")
    _sheet_file(p, SHEETS["Penjualan2205"],
                ["Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang",
                 "Kuantitas"], rows_2205)
    files.append(p)
    p = str(root / FOLDERS["RI3224"] / "ri.xlsx")
    _sheet_file(p, SHEETS["Penerimaan3224"],
                ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
                 "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan",
                 "Satuan", "Rasio Satuan"], rows_3224)
    files.append(p)
    p = str(root / FOLDERS["RI3224Lalu"] / "ri_lalu.xlsx")
    _sheet_file(p, SHEETS["Penerimaan3224"],
                ["Tanggal", "Kts (Unit#1)", "Nama Barang", "Nama Gudang",
                 "Nomor # RI", "Nomor # PO", "Tgl/Jam Pembuatan",
                 "Satuan", "Rasio Satuan"], rows_3224_lalu)
    files.append(p)
    p = str(root / FOLDERS["Kirim4215"] / "kirim.xlsx")
    _sheet_file(p, SHEETS["Pemindahan4215"],
                ["Tanggal", "Gudang Pengirim", "Nama Barang",
                 "Kts Diterima"], rows_4215)
    files.append(p)
    p = str(root / FOLDERS["Pemindahan4205"] / "pemindahan.xlsx")
    _sheet_file(p, SHEETS["Pemindahan4205"],
                ["Nomor #Terima", "Gudang #Terima", "Tanggal #Terima",
                 "Nama Barang", "#Qty. Terkecil",
                 "#Tgl/Jam Pembuatan IT", "#Sat. Kirim", "Rasio Satuan",
                 "#Sat. Terkecil"], rows_4205)
    files.append(p)
    p = str(root / FOLDERS["Pemindahan4205Lalu"] / "pemindahan_lalu.xlsx")
    _sheet_file(p, SHEETS["Pemindahan4205"],
                ["Nomor #Terima", "Gudang #Terima", "Tanggal #Terima",
                 "Nama Barang", "#Qty. Terkecil",
                 "#Tgl/Jam Pembuatan IT", "#Sat. Kirim", "Rasio Satuan",
                 "#Sat. Terkecil"], rows_4205_lalu)
    files.append(p)
    p = str(root / FOLDERS["RincianPO"] / "po.xlsx")
    _sheet_file(p, SHEETS["PesananPO"],
                ["Nomor #", "Tanggal", "Cabang PO", "Pemasok",
                 "Nama Barang", "Satuan", "Kuantitas", "@Harga",
                 "Total Harga", "Keterangan PO",
                 "Status Pesanan Pembelian", "Tgl/Jam Pembuatan"],
                rows_po)
    files.append(p)
    p = str(root / FOLDERS["Data9901"] / "mutasi.xlsx")
    _sheet_file(p, "Sheet1",
                ["Nomor # Penerimaan Barang", "Jenis Barang Barang & Jasa",
                 "#Prime.Qty", "Nama barang", "Nama cabang", "Tanggal"],
                rows_9901)
    files.append(p)

    # Konversi satuan (Sheet1 header row 1)
    p = str(root / FOLDERS["KonversiSatuan"] / "konversi.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    hdr = ["Nama Barang", "Satuan #2", "Rasio Satuan #2", "Satuan #3",
           "Rasio Satuan #3", "Satuan #4", "Rasio Satuan #4",
           "Satuan #5", "Rasio Satuan #5"]
    for c, h in enumerate(hdr, 1):
        ws.cell(row=1, column=c, value=h)
    for i, (barang, sat) in enumerate(barangs):
        ws.cell(row=2 + i, column=1, value=barang)
        ws.cell(row=2 + i, column=2, value=sat)
        ws.cell(row=2 + i, column=3, value="1")
        ws.cell(row=2 + i, column=4, value="DUS")
        ws.cell(row=2 + i, column=5, value="12")
    _save(wb, p)
    files.append(p)

    # DBS kategori (Sheet1 header row 1)
    p = str(root / FOLDERS["DBSKategori"] / "kategori.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for c, h in enumerate(["NAMA BARANG", "KATEGORI", "JENIS",
                            "SOURCE KIRIMAN"], 1):
        ws.cell(row=1, column=c, value=h)
    for i, (barang, _) in enumerate(barangs):
        ws.cell(row=2 + i, column=1, value=barang)
        ws.cell(row=2 + i, column=2, value="DEVIASI")
        ws.cell(row=2 + i, column=3, value="BAHAN BAKU")
        ws.cell(row=2 + i, column=4, value="INTERNAL")
    _save(wb, p)
    files.append(p)

    # 41.09 harga
    p = str(root / FOLDERS["Harga"] / "4109.xlsx")
    write_4109(p, barangs, rng)
    files.append(p)

    # config.json
    config = {
        "RootPath": str(root) + os.sep,
        "Folders": dict(FOLDERS),
        "Sheets": dict(SHEETS),
        "KategoriBarang4217": ["10.FOOD [RM] - COM V.2"],
        "DpiAware": True,
    }
    config_path = str(root / "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return {"root": str(root), "config_path": config_path,
            "n_pairs": n_restos * n_barangs, "n_files": len(files),
            "files": files}


# ---------------------------------------------------------------------------
# In-memory append1-like DataFrame besar (untuk benchmark_views — tanpa
# Excel sama sekali; kolom & JENIS persis output build_append1).
# ---------------------------------------------------------------------------
APPEND1_COLUMNS = ["Nama Barang", "NAMA RESTO", "Tanggal", "JENIS",
                   "NILAI", "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT",
                   "KATEGORI", "SOURCE KIRIMAN", "SOURCE DATA",
                   "SATUAN", "AKTIF/NON"]
APPEND1_JENIS = ["SALDO AWAL", "1.SO", "2.SALDO AKHIR", "3.DEVIASI",
                 "4.IN", "5.BARANG MASUK", "7.Selisih IN",
                 "8.BARANG KELUAR", "9.ACR"]


def make_big_append1(n_restos: int, n_barangs: int,
                     seed: int = 20260901) -> "tuple":
    """DataFrame append1-like in-memory: pairs × 9 JENIS × tanggal 1..31
    (long) — skala = baris. Return (df, n_pairs)."""
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(seed)
    restos = resto_codes(n_restos)
    barangs = barang_names(n_barangs)
    pairs = [(b, r) for r in restos for b, _ in barangs]
    n_pairs = len(pairs)
    dates = np.arange(1, 32)
    # Baris: setiap pair × setiap JENIS × tanggal 1..31 → long frame.
    n_rows = n_pairs * len(APPEND1_JENIS) * len(dates)
    idx = np.arange(n_rows)
    pi = idx // (len(APPEND1_JENIS) * len(dates))
    rem = idx % (len(APPEND1_JENIS) * len(dates))
    ji = rem // len(dates)
    di = rem % len(dates)
    df = pd.DataFrame({
        "Nama Barang": [pairs[i][0] for i in pi],
        "NAMA RESTO": [pairs[i][1] for i in pi],
        "Tanggal": (di + 1).astype("int64"),
        "JENIS": [APPEND1_JENIS[i] for i in ji],
        "NILAI": rng.normal(0, 500, n_rows).round(2),
        "Nomor": None, "Nomor PO": None, "#Tgl/Jam Pembuatan IT": None,
        "KATEGORI": "DEVIASI", "SOURCE KIRIMAN": "INTERNAL",
        "SOURCE DATA": "input so harian", "SATUAN": "GR",
        "AKTIF/NON": "AKTIF",
    })
    df["Tanggal"] = df["Tanggal"].astype("Int64")
    df["NILAI"] = pd.to_numeric(df["NILAI"])
    return df, n_pairs


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate synthetic dataset")
    ap.add_argument("--out", required=True, help="Target data dir")
    ap.add_argument("--restos", type=int, default=12)
    ap.add_argument("--barang", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20260901)
    a = ap.parse_args()
    info = generate_tree(a.out, a.restos, a.barang, a.seed)
    print(f"root={info['root']}")
    print(f"files={info['n_files']} pairs={info['n_pairs']}")
    print(f"config={info['config_path']}")
