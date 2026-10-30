"""
fn_9901.py — Baca file 9901 (mutasi barang tanpa nomor penerimaan) sebagai sumber IN.

Semua sheet dari semua file Excel di folder dibaca lalu di-concat (nama
sheet 9901 bervariasi); hasilnya digabung 42.05/32.24 di query_in. Output:
Tanggal, NAMA RESTO, Nama Barang, Value, Nomor, Nomor PO.

Filter:
- 'Nomor # Penerimaan Barang' = kosong — baris ber-penerimaan sudah
  tercatat di 32.24, tidak boleh dobel hitung.
- 'Jenis Barang Barang & Jasa' = 'Persediaan'.
- Kolom filter hilang → filter di-skip + WARNING mencolok di log.

Mapping kolom (fleksibel: exact match > substring terpendek; ikatan lewat
fallback di-log WARNING):
- #Prime.Qty → Value — kandidat fallback meng-exclude 'harga'/'nilai'
  agar tak nyasar ke kolom uang; Nama barang → Nama Barang.
- Nama cabang → NAMA RESTO = teks setelah titik TERAKHIR (helper
  resto_from_cabang_po; 'B.1001.MLGPAR' → 'MLGPAR'); Tanggal → day-of-month.
- Nomor # → Nomor; 'Nomor # Pesanan Pembelian' → Nomor PO.

Dedup: baris duplikat persis dibuang hanya LINTAS sumber (file × sheet);
baris identik SE-SUMBER dipertahankan (PO multi-baris legit). Baris dengan
NAMA RESTO kosong dibuang.
"""
import os

import pandas as pd

from .helpers import (
    date_to_day,
    resto_from_cabang_po,
    safe_to_numeric,
    safe_to_str,
)

# v3.11.10 — FIX (audit 3-b, bug #5): kolom tag SUMBER sementara (file ×
# sheet) untuk dedup LINTAS SUMBER — dibuang lagi sebelum pencarian kolom
# supaya tak pernah bocor ke output/log kolom tersedia.
_SRC_9901 = "__src_9901"


def _find_column(df_cols, candidates, contains_any=None, exclude=None):
    """Find column by priority: exact match > substring > exact-short match.

    candidates: list of preferred exact names (case-insensitive, trimmed).
    contains_any: list of substrings to match if no exact match found.
    exclude: list of substrings — if a matched column contains any of these, skip it.
    Returns column name or None.
    """
    if df_cols is None or len(df_cols) == 0:
        return None
    # Normalize for case-insensitive comparison
    cols_lower = {str(c).strip().lower(): c for c in df_cols}

    def _is_excluded(col_name_lower):
        if not exclude:
            return False
        return any(ex.lower() in col_name_lower for ex in exclude)

    # 1) Exact match (case-insensitive, trimmed)
    for cand in candidates or []:
        key = str(cand).strip().lower()
        if key in cols_lower and not _is_excluded(key):
            return cols_lower[key]

    # 2) Substring match (prefer SHORTEST column name to avoid false positives)
    if contains_any:
        for substr in contains_any:
            substr_l = str(substr).lower()
            # Collect all matching columns, then pick shortest (most specific)
            matches = []
            for clow, corig in cols_lower.items():
                if substr_l in clow and not _is_excluded(clow):
                    matches.append((len(clow), corig))
            if matches:
                matches.sort(key=lambda x: x[0])  # shortest first
                return matches[0][1]

    return None


def fn_9901(folder_path: str, stop_event=None) -> pd.DataFrame:
    """
    Process 9901 file in folder_path. Returns DataFrame with columns:
    Tanggal, NAMA RESTO, Nama Barang, Value

    stop_event: v3.9.72 — threading.Event opsional; checkpoint ⏹ di kepala
    loop file & sheet (audit 1-d: dulu ⏹ menunggu folder 9901 penuh
    terbaca). Cek DI LUAR try/except-skip supaya PipelineStopped tidak
    tertelan jalur skip-sheet. Default None = perilaku lama.
    """
    # The 9901 file may have varying sheet names. Try common ones.
    # First, attempt to list files and find a sheet name.
    from .helpers import _list_excel_files, fn_buka_sheet, stop_check
    files = _list_excel_files(folder_path)
    if not files:
        print(f"  [fn_9901] No Excel files found in: {folder_path}")
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    dfs = []
    for f in files:
        # v3.9.72 — checkpoint ⏹ ANTAR file (di luar try: Stop ≠ skip-file)
        stop_check(stop_event, f"baca 9901 {os.path.basename(f)!r}")
        try:
            # Try to find a suitable sheet. Many 9901 exports have a single sheet
            # or use the default first sheet. We'll read all sheets and concat.
            import openpyxl
            wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
            sheet_names = wb.sheetnames
            wb.close()
        except Exception:
            sheet_names = [0]  # fallback to first sheet

        for sn in sheet_names:
            # v3.9.72 — checkpoint ⏹ ANTAR sheet (di luar try: Stop ≠
            # skip-sheet; file 9901 bisa multi-sheet besar per file)
            stop_check(stop_event, f"baca sheet 9901 {os.path.basename(f)!r}:{sn}")
            try:
                df = fn_buka_sheet(f, sn, header_row=0)
            except Exception:
                # Fallback: read with default openpyxl
                try:
                    df = pd.read_excel(f, sheet_name=sn, header=0, dtype=object)
                except Exception as e:
                    print(f"  [fn_9901] Skip sheet '{sn}' in {f}: {e}")
                    continue
            if df is not None and len(df) > 0:
                # v3.11.10 — FIX (audit 3-b, bug #5): tag SUMBER per frame
                # (file × sheet) — cache bacaan aman dimutasi (fn_buka_sheet
                # menyajikan copy defensif; lihat helpers._read_cache_get).
                df[_SRC_9901] = f"{os.path.basename(f)}::{sn}"
                dfs.append(df)
                # v3.9.33 — AUDIT FIX (48-a): kontribusi baris per sheet
                # (file + sheet + jumlah baris) — sheet backup/salinan
                # yang kebaca dobel jadi KELIHATAN di log.
                print(f"  [fn_9901] {os.path.basename(f)} :: sheet "
                      f"'{sn}': {len(df)} baris")

    if not dfs:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    prom = pd.concat(dfs, ignore_index=True, sort=False)

    # v3.9.33 — AUDIT FIX (48-a HIGH): concat SEMUA sheet × SEMUA file tanpa
    # dedup → baris identik masuk 2× (sheet backup / ringkasan / file
    # salinan di folder bulan) → qty IN terhitung DOBEL senyap di pivot
    # append1. Buang baris duplikat persis; jika ada yang terbuang → log
    # KERAS supaya user cek foldernya.
    # v3.11.10 — FIX (audit 3-b, bug #5): dedup global drop_duplicates()
    # juga membuang baris transaksi LEGIT yang identik DALAM SATU sheet
    # (PO multi-baris: item sama × qty sama × tanggal sama — export 9901
    # tanpa kolom nomor baris; probe p01: 2 baris Σ14 terpotong jadi 1
    # Σ7 → Selisih IN/deviasi salah). Kini dedup dibatasi LINTAS SUMBER:
    # baris identik dari sheet/file LAIN tetap dibuang (kasus backup
    # v3.9.33 — README: "dedup baris duplikat persis lintas sheet/file"),
    # baris identik SE-SUMBER dipertahankan. Implementasi: sumber PERTAMA
    # tiap grup nilai-baris menang utuh; sumber berikutnya dibuang.
    n_before = len(prom)
    # Kunci grup = SEMUA kolom nilai POSISI-per-posisi (bukan label —
    # sheet 9901 dgn header duplikat membuat groupby label raise
    # "Grouper not 1-dimensional"; drop_duplicates lama kebal itu).
    if _SRC_9901 in prom.columns:
        _tag_pos = prom.columns.get_loc(_SRC_9901)
        _key_series = [prom.iloc[:, i]
                       for i in range(prom.columns.size) if i != _tag_pos]
        _first_src = prom.groupby(
            _key_series, dropna=False, sort=False)[_SRC_9901].transform("first")
        _drop = prom[_SRC_9901] != _first_src
        if _drop.any():
            prom = prom[~_drop]
            print(f"  [fn_9901] 9901 v3.9.33/v3.11.10: "
                  f"{n_before - len(prom)} baris duplikat persis LINTAS "
                  f"sheet/file dibuang (sheet backup/salinan? — baris "
                  f"identik se-sheet dipertahankan, PO multi-baris legit)")
    prom = prom.drop(columns=[_SRC_9901])

    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # --- Locate columns (flexible matching) ---
    # Per screenshot from user: actual headers seen = 'Nomor # Penerimaan' (no 'Barang' suffix), 'Barang'
    col_nomor_penerimaan = _find_column(
        prom.columns,
        candidates=["Nomor # Penerimaan Barang", "Nomor # Penerimaan",
                    "Nomor Penerimaan Barang", "Nomor Penerimaan"],
        contains_any=["penerimaan"]
    )
    col_jenis = _find_column(
        prom.columns,
        candidates=["Jenis Barang Barang & Jasa", "Jenis Barang", "Barang & Jasa"],
        contains_any=["jenis", "barang & jasa", "barang jasa"]
    )
    # v3.9.33 — AUDIT FIX (48-a): "jumlah" DIHAPUS dari kandidat fallback
    # (bisa nyasar kolom uang "Jumlah Harga") + exclude nama kolom yang
    # mengandung 'harga'/'nilai' (kolom nilai rupiah, bukan qty).
    col_qty = _find_column(
        prom.columns,
        candidates=["#Prime.Qty", "Prime.Qty", "Prime Qty", "#Prime Qty"],
        contains_any=["prime", "qty", "kuantiti", "kuantitas"],
        exclude=["harga", "nilai"]
    )
    # Nama Barang: exclude Jenis column to avoid collision. Also accept 'Barang' alone.
    col_nama_barang = _find_column(
        prom.columns,
        candidates=["Nama barang", "Nama Barang", "NAMA BARANG", "Barang"],
        contains_any=["nama barang"],
        exclude=["jenis"]
    )
    # Fallback: if still not found, look for column containing 'barang' but not 'jenis'
    if col_nama_barang is None:
        col_nama_barang = _find_column(
            prom.columns,
            candidates=[],
            contains_any=["barang"],
            exclude=["jenis", "penerimaan", "kirim", "masuk", "keluar"]
        )
    col_nama_cabang = _find_column(
        prom.columns,
        candidates=["Nama cabang", "Nama Cabang", "Cabang"],
        contains_any=["cabang"]
    )
    col_tanggal = _find_column(
        prom.columns,
        candidates=["Tanggal", "TGL", "Date"],
        contains_any=["tanggal", "tgl", "date"]
    )
    # v3.4: nomor faktur pembelian (PI.2026…) + nomor pesanan (PO.2026…)
    col_nomor = _find_column(
        prom.columns,
        candidates=["Nomor #", "Nomor"],
        contains_any=[],
    )
    # pastikan col_nomor bukan kolom penerimaan/pesanan/aset
    if col_nomor is not None:
        cl = str(col_nomor).strip().lower()
        if any(x in cl for x in ("penerimaan", "pesanan", "aset", "kirim",
                                 "faktur pajak")):
            col_nomor = None
    col_nomor_po = _find_column(
        prom.columns,
        candidates=["Nomor # Pesanan Pembelian", "Nomor Pesanan Pembelian",
                    "Nomor # Pesanan"],
        contains_any=["pesanan pembelian", "pesanan"],
    )

    # Diagnostic logging (helps user debug if mapping fails)
    missing = []
    if col_nomor_penerimaan is None:
        missing.append("Nomor # Penerimaan Barang")
    if col_jenis is None:
        missing.append("Jenis Barang Barang & Jasa")
    if col_qty is None:
        missing.append("#Prime.Qty")
    if col_nama_barang is None:
        missing.append("Nama barang")
    if col_nama_cabang is None:
        missing.append("Nama cabang")
    if col_tanggal is None:
        missing.append("Tanggal")
    if missing:
        print(f"  [fn_9901] WARNING: could not find columns: {missing}")
        print(f"  [fn_9901] Available columns: {list(prom.columns)}")

    # v3.9.67 — HARDENING FORMAT: kolom yang diikat lewat FALLBACK
    # (substring match — bukan nama persis kandidat) kini DI-LOG keras.
    # Uji mutasi format: rename 'Nama barang' → 'Nama Item' + kolom
    # 'Kode Barang' terisi → fallback mengikat Nama Barang ke KODE
    # BARANG secara SENYAP (qty/resto benar, nama nyasar ke kode item;
    # barang lalu tak cocok sumber lain → tersekat di pivot tanpa jejak).
    _fallback_binds = []
    for _label, _col, _cands in (
        ("Nomor # Penerimaan", col_nomor_penerimaan,
         ("Nomor # Penerimaan Barang", "Nomor # Penerimaan",
          "Nomor Penerimaan Barang", "Nomor Penerimaan")),
        ("Jenis Barang", col_jenis,
         ("Jenis Barang Barang & Jasa", "Jenis Barang", "Barang & Jasa")),
        ("Qty", col_qty,
         ("#Prime.Qty", "Prime.Qty", "Prime Qty", "#Prime Qty")),
        ("Nama Barang", col_nama_barang,
         ("Nama barang", "Nama Barang", "NAMA BARANG", "Barang")),
        ("Nama Cabang", col_nama_cabang,
         ("Nama cabang", "Nama Cabang", "Cabang")),
        ("Tanggal", col_tanggal, ("Tanggal", "TGL", "Date")),
    ):
        if _col is not None:
            _cand_l = {str(c).strip().lower() for c in _cands}
            if str(_col).strip().lower() not in _cand_l:
                _fallback_binds.append(f"{_label}→'{_col}'")
    if _fallback_binds:
        print(f"  [fn_9901] WARNING: kolom diikat lewat FALLBACK (bukan "
              f"nama persis): {', '.join(_fallback_binds)} — cek header "
              f"file 9901 (di-rename/diubah oleh export baru Accurate?)")

    # --- Filter 1: Nomor # Penerimaan Barang = Blank ---
    if col_nomor_penerimaan is not None:
        nomor_series = prom[col_nomor_penerimaan]
        # Treat NaN, None, empty string, whitespace as blank
        is_blank = nomor_series.isna() | (
            nomor_series.astype(str).str.strip().isin(["", "nan", "None", "NaT"])
        )
        prom = prom[is_blank].copy()
        print(f"  [fn_9901] After filter Nomor # Penerimaan Barang = Blank: {len(prom)} rows")
    else:
        # If column missing, assume all rows match (no filter applied).
        # v3.9.33 — AUDIT FIX (48-a): skip tetap dipertahankan (perilaku
        # lama) tapi TIDAK lagi senyap — WARNING mencolok + jumlah baris
        # yang dianggap lolos (risiko dobel hitung vs 32.24: baris
        # ber-penerimaan ikut terbaca sebagai IN 99.01).
        print(f"  [fn_9901] 9901 WARNING: kolom 'Nomor # Penerimaan' "
              f"tidak ditemukan — {len(prom)} baris dianggap tanpa "
              f"penerimaan (risiko dobel hitung vs 32.24)")

    # --- Filter 2: Jenis Barang Barang & Jasa = Persediaan ---
    if col_jenis is not None:
        jenis_series = prom[col_jenis].astype(str).str.strip().str.lower()
        mask_persediaan = jenis_series == "persediaan"
        prom = prom[mask_persediaan].copy()
        print(f"  [fn_9901] After filter Jenis = Persediaan: {len(prom)} rows")
    else:
        # v3.9.33 — AUDIT FIX (48-a): mirror warning filter penerimaan —
        # baris jasa/aset ikut dianggap Persediaan (skip tidak senyap).
        print(f"  [fn_9901] 9901 WARNING: kolom 'Jenis Barang Barang & "
              f"Jasa' tidak ditemukan — {len(prom)} baris dianggap "
              f"Persediaan (risiko baris jasa/aset ikut terhitung vs "
              f"32.24)")

    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # --- Build output ---
    out = pd.DataFrame()

    # Tanggal → day-of-month
    if col_tanggal is not None:
        out["Tanggal"] = date_to_day(prom[col_tanggal])
    else:
        out["Tanggal"] = pd.NA

    # NAMA RESTO from Nama cabang
    # v3.9.42 — AUDIT FIX (61-a, F3): resto = bagian setelah titik TERAKHIR
    # lewat helper bersama resto_from_cabang_po (NA/float-safe; dipakai
    # juga fn_audit PO Menunggu + rincian_po_view) — dulu membelah di
    # titik PERTAMA: 'B.1001.MLGPAR' → '1001.MLGPAR' (resto phantom yang
    # tak cocok dgn sumber lain → IN 9901 resto itu lenyap dari pivot).
    # Scalar-safe → .map() per baris (fn_9901 ribuan baris — murah).
    if col_nama_cabang is not None:
        out["NAMA RESTO"] = prom[col_nama_cabang].map(resto_from_cabang_po)
    else:
        out["NAMA RESTO"] = pd.NA

    # Nama Barang
    if col_nama_barang is not None:
        out["Nama Barang"] = safe_to_str(prom[col_nama_barang])
    else:
        out["Nama Barang"] = pd.NA

    # Value from #Prime.Qty
    if col_qty is not None:
        out["Value"] = safe_to_numeric(prom[col_qty])
    else:
        out["Value"] = pd.NA

    # v3.4 — Nomor (faktur pembelian PI…) & Nomor PO (pesanan PO…)
    if col_nomor is not None:
        out["Nomor"] = safe_to_str(prom[col_nomor])
    else:
        out["Nomor"] = pd.NA
    if col_nomor_po is not None:
        out["Nomor PO"] = safe_to_str(prom[col_nomor_po])
    else:
        out["Nomor PO"] = pd.NA

    # Drop rows where NAMA RESTO is empty (mirror fn_3224 behavior)
    mask_valid_resto = out["NAMA RESTO"].notna() & (
        out["NAMA RESTO"].astype(str).str.strip() != "")
    out = out[mask_valid_resto].reset_index(drop=True)

    print(f"  [fn_9901] DONE: {len(out)} rows")
    return out
