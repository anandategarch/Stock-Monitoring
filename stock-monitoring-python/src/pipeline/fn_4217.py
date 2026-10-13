"""
fn_4217.py — Mirror persis fn4217 di M code.
Kuantitas Barang per Gudang (modul 42.17) → SALDO AWAL.
OPTIMIZED: vectorized text operations.

v3.9.32 (user: "filter lebih awal data 42.17 pakai kolom kategori barang
[whitelist 5 kategori]" + barang 42.17-only tak muncul di Deviasi GR):
- KATEGORI BARANG dibaca sebagai KOLOM id SEBELUM melt (dulu kolom
  kategori/satuan/kode ter-melt jadi pseudo-baris NAMA RESTO → kosong →
  terbuang senyap). Kategori ber-pola header grup (nilai hanya di baris
  pertama tiap grup — sisanya NaN) → forward-fill.
- FILTER WHITELIST kategori DITERAPKAN SEBELUM melt (beban pipeline turun;
  default 5+1 kategori produksi — daftar BISA DIUBAH di config.json key
  "KategoriBarang4217"; file tanpa kolom kategori → tanpa filter +
  peringatan log; hasil 0 baris → filter di-bypass otomatis + peringatan
  [safety-net salah konfigurasi]).
- NAMA SATUAN per barang ikut keluar sebagai kolom SATUAN (fallback utk
  pasangan TANPA rekap — barang 42.17-only kini punya satuan di tabel
  Deviasi GR/PCS; pasangan ber-rekap tetap memakai satuan rekap).
- Matching kategori: normalisasi buang SEMUA whitespace + upper
  ('01. COST - PACKAGING - TIDAK BOLEH' == '01.COST-PACKAGING-TIDAKBOLEH')
  + PREFIX match supaya varian spasi/nama file user tetap cocok.
"""
import pandas as pd

from .helpers import fn_combine_folder

# Kandidat nama kolom (beda versi export Accurate — resolusi defensive)
_KANDIDAT_KATEGORI = ["Kategori Barang", "Kategori"]
_KANDIDAT_SATUAN = ["Nama Satuan", "Satuan"]

# Default whitelist kategori produksi (config.json "KategoriBarang4217"
# menimpa; prefix-match + case/space-insensitive). 5 kategori aktif V.2 +
# varian PACKAGING lama '- TIDAK BOLEH' (item lama yang masih bersaldo
# tetap terpantau — mencegah saldo hilang senyap).
DEFAULT_KATEGORI_WHITELIST = [
    "00.COST",
    "01.COST - PACKAGING V.2",
    "01. COST - PACKAGING - TIDAK BOLEH",
    "10.FOOD [BUMBU] - COM V.2",
    "10.FOOD [RM] - COM V.2",
    "10.FOOD [WIP] - COM V.2",
]

OUTPUT_COLUMNS = ["Nama Barang", "NAMA RESTO", "Value", "Tanggal",
                  "JENIS", "SATUAN"]


def _norm_kat(v) -> str:
    """Kategori → '01.COST-PACKAGING-TIDAKBOLEH' (buang SEMUA whitespace,
    upper); None/NaN/blank → ''."""
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(v).strip().upper()
    return "".join(s.split()) if s else ""


def _find_col(prom_columns, kandidat):
    """Kolom pertama yang cocok (case-insensitive) dari kandidat nama."""
    if prom_columns is None:
        return None
    lookup = {str(c).strip().lower(): c for c in prom_columns}
    for k in kandidat:
        c = lookup.get(str(k).strip().lower())
        if c is not None:
            return c
    return None


def fn_4217(folder_path: str, kategori_whitelist: list | None = None) -> pd.DataFrame:
    """
    Mirror M: fn4217(folderPath).

    kategori_whitelist: list kategori yang LOLOS (prefix-match normalisasi;
    None/kosong → tanpa filter). Sumber default: config "KategoriBarang4217".

    Output columns: Nama Barang, NAMA RESTO, Value, Tanggal, JENIS, SATUAN
    (SATUAN = 'Nama Satuan' file per barang; file tanpa kolom → '').
    """
    # expand + Skip(3) + Promote = header=4
    prom = fn_combine_folder(folder_path, "#42.17. Kuantitas Barang per Gu", header_row=4)
    if prom.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    # up = Table.UnpivotOtherColumns(prom, {"Nama Barang"}, "NAMA RESTO", "Value")
    # Cari kolom "Nama Barang"
    nama_barang_col = None
    for c in prom.columns:
        if str(c).strip().lower() == "nama barang":
            nama_barang_col = c
            break

    if nama_barang_col is None:
        nama_barang_col = prom.columns[0]

    if nama_barang_col != "Nama Barang":
        prom = prom.rename(columns={nama_barang_col: "Nama Barang"})

    # v3.9.32 — kolom KATEGORI BARANG + NAMA SATUAN sebagai id SEBELUM melt
    kat_col = _find_col(prom.columns, _KANDIDAT_KATEGORI)
    sat_col = _find_col(prom.columns, _KANDIDAT_SATUAN)

    if kat_col is not None and kat_col != "KATEGORI BARANG":
        prom = prom.rename(columns={kat_col: "KATEGORI BARANG"})
        kat_col = "KATEGORI BARANG"
    if sat_col is not None and sat_col != "SATUAN AWAL":
        # nama sementara supaya tidak bentrok dgn output "SATUAN"
        prom = prom.rename(columns={sat_col: "SATUAN AWAL"})
        sat_col = "SATUAN AWAL"

    # Kategori ber-pola header grup: nilai hanya di baris pertama grup →
    # forward-fill (mirror pembacaan kategori 41.09).
    if kat_col is not None:
        prom[kat_col] = prom[kat_col].ffill()

    # --- FILTER KATEGORI WHITELIST (SEBELUM melt — "lebih awal") ---
    prom_raw = prom.copy()          # utk safety-net bypass di bawah
    _kat_was = kat_col is not None
    _sat_was = sat_col
    if kat_col is not None and kategori_whitelist:
        wl_norm = [_norm_kat(k) for k in kategori_whitelist
                   if _norm_kat(k)]
        if wl_norm:
            kat_norm = prom[kat_col].map(_norm_kat)
            # prefix-match: entri whitelist '01.COST - PACKAGING V.2'
            # cocok dgn kategori file yang berawal sama (normalisasi).
            keep = kat_norm.map(
                lambda v: any(v.startswith(w) for w in wl_norm))
            n_total = len(prom)
            prom = prom[keep.fillna(False)]
            n_keep = len(prom)
            print(f"    4217 kategori filter: {n_keep:,}/{n_total:,} baris "
                  f"lolos whitelist ({len(wl_norm)} kategori)")
            if prom.empty and n_total:
                # SAFETY-NET: whitelist salah config (mis. nama kategori di
                # file user beda total) → JANGAN kosongkan saldo awal;
                # bypass filter + peringatan mencolok di log.
                print("    [PERINGATAN] 4217: whitelist kategori "
                      "menyaring SEMUA baris — filter di-bypass (cek "
                      "config.json 'KategoriBarang4217' vs kolom Kategori "
                      "Barang file 42.17)")
                prom = prom_raw
                kat_col = "KATEGORI BARANG" if _kat_was else None
                sat_col = _sat_was
    elif kat_col is None:
        print("    4217: kolom Kategori Barang tidak ditemukan — "
              "filter kategori tidak diterapkan")

    id_vars = ["Nama Barang"]
    if sat_col is not None and sat_col in prom.columns:
        id_vars.append(sat_col)

    up = prom.melt(id_vars=id_vars, var_name="NAMA RESTO", value_name="Value")

    # SATUAN → string bersih ('' bila kolom tak ada / kosong)
    if sat_col is not None and sat_col in up.columns:
        up = up.rename(columns={sat_col: "SATUAN"})
    else:
        up["SATUAN"] = ""
    up["SATUAN"] = (up["SATUAN"].astype(str).str.strip()
                    .replace({"nan": "", "None": "", "NaN": ""}))

    # ext = NAMA RESTO → BetweenDelimiters(_, "(", ")") — vectorized
    # (pseudo-baris non-resto — mis. 'Kode Barang' bila masih ada —
    # menghasilkan '' dan terbuang oleh mask bawah)
    from .helpers import vec_text_between_delimiters
    up["NAMA RESTO"] = vec_text_between_delimiters(up["NAMA RESTO"], "(", ")")

    # addT = Tanggal = 1
    up["Tanggal"] = pd.array([1] * len(up), dtype="Int64")

    # addJ = JENIS = "SALDO AWAL"
    up["JENIS"] = "SALDO AWAL"

    # Value → numeric
    up["Value"] = pd.to_numeric(up["Value"], errors="coerce")

    # fil = Table.SelectRows(addJ, each [Value] <> 0 and [Value] <> null and [NAMA RESTO] <> "")
    mask = (
        up["Value"].notna() &
        (up["Value"] != 0) &
        up["NAMA RESTO"].notna() &
        (up["NAMA RESTO"].astype(str).str.strip() != "")
    )
    fil = up[mask].reset_index(drop=True)

    return fil[OUTPUT_COLUMNS]
