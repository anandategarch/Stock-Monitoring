"""
fn_9901.py — Process 9901 file (mutasi barang tanpa nomor penerimaan).
Sumber data IN tambahan (digabung dengan 3224, 4205 di query_in).

Filter:
  - "Nomor # Penerimaan Barang" = Blank (kosong)
  - "Jenis Barang Barang & Jasa" = "Persediaan"

Column mapping:
  - #Prime.Qty     → Value
  - Nama barang    → Nama Barang
  - Nama cabang    → NAMA RESTO (extract after ".", e.g., "1137.CKGPAH" → "CKGPAH")
                   CONSISTENT with fn_3224/fn_4215/fn_4217/fn_4205 which extract
                   from between parentheses "(" and ")"
  - Tanggal        → Tanggal (day-of-month)
"""
import pandas as pd
from .helpers import (
    safe_to_str, safe_to_numeric, date_to_day, vec_text_after_delimiter
)


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


def fn_9901(folder_path: str) -> pd.DataFrame:
    """
    Process 9901 file in folder_path. Returns DataFrame with columns:
    Tanggal, NAMA RESTO, Nama Barang, Value
    """
    # The 9901 file may have varying sheet names. Try common ones.
    # First, attempt to list files and find a sheet name.
    from .helpers import _list_excel_files, fn_buka_sheet
    files = _list_excel_files(folder_path)
    if not files:
        print(f"  [fn_9901] No Excel files found in: {folder_path}")
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    dfs = []
    for f in files:
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
                dfs.append(df)

    if not dfs:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    prom = pd.concat(dfs, ignore_index=True, sort=False)

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
    col_qty = _find_column(
        prom.columns,
        candidates=["#Prime.Qty", "Prime.Qty", "Prime Qty", "#Prime Qty"],
        contains_any=["prime", "qty", "kuantiti", "kuantitas", "jumlah"]
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
        # If column missing, assume all rows match (no filter applied)
        print(f"  [fn_9901] 'Nomor # Penerimaan Barang' column not found — skipping blank filter")

    # --- Filter 2: Jenis Barang Barang & Jasa = Persediaan ---
    if col_jenis is not None:
        jenis_series = prom[col_jenis].astype(str).str.strip().str.lower()
        mask_persediaan = jenis_series == "persediaan"
        prom = prom[mask_persediaan].copy()
        print(f"  [fn_9901] After filter Jenis = Persediaan: {len(prom)} rows")
    else:
        print(f"  [fn_9901] 'Jenis Barang Barang & Jasa' column not found — skipping jenis filter")

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
    # FIX: extract text AFTER first "." (e.g., "1137.CKGPAH" → "CKGPAH")
    # supaya konsisten dengan fn_3224/fn_4215/fn_4217/fn_4205 yang pakai
    # vec_text_between_delimiters(..., "(", ")") untuk extract resto code.
    # Sebelumnya pakai safe_to_str langsung → "1137.CKGPAH" dianggap resto berbeda
    # dari "CKGPAH" di source lain → pivot melihat 2 resto yang sebenarnya sama.
    if col_nama_cabang is not None:
        out["NAMA RESTO"] = vec_text_after_delimiter(prom[col_nama_cabang], ".")
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

    # Drop rows where NAMA RESTO is empty (mirror fn_3224 behavior)
    mask_valid_resto = out["NAMA RESTO"].notna() & (
        out["NAMA RESTO"].astype(str).str.strip() != "")
    out = out[mask_valid_resto].reset_index(drop=True)

    print(f"  [fn_9901] DONE: {len(out)} rows")
    return out
