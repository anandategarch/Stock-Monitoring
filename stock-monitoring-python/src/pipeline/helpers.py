"""
helpers.py — Helper functions yang mirror persis fnBukaSheet, fnCombineFolder,
dan fungsi text delimiter di Power Query M code.

OPTIMIZED untuk speed: vectorized text operations via .str accessor.
"""
import os
import re
import glob
import pandas as pd
import numpy as np
from typing import Optional, List


# =============================================================================
# TEXT DELIMITER FUNCTIONS (vectorized via .str accessor)
# =============================================================================

def text_before_delimiter(s, delimiter: str = ".") -> Optional[str]:
    """Mirror M: Text.BeforeDelimiter(text, delimiter). Single value."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    s = str(s)
    idx = s.find(delimiter)
    if idx < 0:
        return s
    return s[:idx]


def text_after_delimiter(s, delimiter: str = ".") -> Optional[str]:
    """Mirror M: Text.AfterDelimiter(text, delimiter). Single value."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    s = str(s)
    idx = s.find(delimiter)
    if idx < 0:
        return s
    return s[idx + len(delimiter):]


def text_between_delimiters(s, open_delim: str = "(", close_delim: str = ")") -> Optional[str]:
    """Mirror M: Text.BetweenDelimiters(text, openDelim, closeDelim). Single value."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    s = str(s)
    start = s.find(open_delim)
    if start < 0:
        return None
    start += len(open_delim)
    end = s.find(close_delim, start)
    if end < 0:
        return None
    return s[start:end]


# === VECTORIZED VERSIONS (for pandas Series — 10-50x faster than .apply) ===

def vec_text_before_delimiter(series: pd.Series, delimiter: str = ".") -> pd.Series:
    """Vectorized Text.BeforeDelimiter untuk pandas Series."""
    s = series.astype(str).where(series.notna(), other=np.nan)
    idx = s.str.find(delimiter)
    result = s.where(idx < 0, s.str.slice(0, idx.where(idx >= 0, 0)))
    # Where idx >= 0, take slice(0, idx). Where idx < 0, keep original.
    mask_no_delim = idx < 0
    result = s.copy()
    has_delim = idx >= 0
    if has_delim.any():
        # Use numpy indexing for speed
        positions = idx[has_delim].values
        vals = s[has_delim].values
        sliced = [str(v)[:int(p)] for v, p in zip(vals, positions)]
        result[has_delim] = sliced
    result = result.where(series.notna(), other=None)
    return result


def vec_text_after_delimiter(series: pd.Series, delimiter: str = ".") -> pd.Series:
    """Vectorized Text.AfterDelimiter untuk pandas Series."""
    s = series.astype(str)
    parts = s.str.split(delimiter, n=1, expand=True)
    if parts.shape[1] < 2:
        # No delimiter found in any row
        return series
    result = parts[1].fillna(series.astype(str))
    result = result.where(series.notna(), other=None)
    return result


def vec_text_between_delimiters(series: pd.Series, open_delim: str = "(", close_delim: str = ")") -> pd.Series:
    """Vectorized Text.BetweenDelimiters untuk pandas Series.
    Uses regex: extract text between first open_delim and next close_delim.
    """
    # Escape regex special chars in delimiters
    open_esc = re.escape(open_delim)
    close_esc = re.escape(close_delim)
    pattern = f"{open_esc}([^{close_esc}]*){close_esc}"
    result = series.astype(str).str.extract(pattern, expand=False)
    # Where no match, result is NaN → convert to None
    result = result.where(result.notna(), other=None)
    # Also preserve original NaN
    result = result.where(series.notna(), other=None)
    return result


# =============================================================================
# COMBINE FOLDER (mirror fnCombineFolder + fnBukaSheet)
# =============================================================================

def _list_excel_files(folder_path: str) -> List[str]:
    """List semua file Excel di folder, exclude hidden & temp files."""
    if not os.path.isdir(folder_path):
        return []
    patterns = ["*.xlsx", "*.xls", "*.xlsm"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(folder_path, p)))
    # Filter: exclude hidden files (check basename, not full path) & temp lock files (~$...)
    files = [f for f in files if not os.path.basename(f).startswith("~$")]
    files = [f for f in files if not os.path.basename(f).startswith(".")]
    return sorted(files)


def fn_buka_sheet(file_path: str, sheet_name: str, header_row: int = 0,
                   raw: bool = False) -> pd.DataFrame:
    """
    Mirror M: fnBukaSheet(binary, sheetName, doPromote).
    Baca sheet tertentu dari file Excel.

    raw=True: baca tanpa header (header=None), kolom = Column1, Column2, ...
              Mirror M doPromote=null/false.
    raw=False: baca dengan header di baris header_row (0-indexed).
              Mirror M doPromote=true + Skip(N) + PromoteHeaders.
              header_row=4 = skip rows 0-3, row 4 jadi header.
    """
    if raw:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, dtype=object)
    else:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, dtype=object)
    return df


def fn_combine_folder(folder_path: str, sheet_name: str, header_row: int = 0,
                       raw: bool = False, add_name_col: bool = False) -> pd.DataFrame:
    """
    Mirror M: fnCombineFolder(folderPath, sheetName, doPromote).

    raw=True: baca tanpa header per file, gabungkan raw.
              Mirror M doPromote=null/false.
    raw=False: baca dengan header_row per file, gabungkan by column name.
              Mirror M doPromote=true.

    add_name_col: jika True, tambah kolom "Name" berisi nama file (basename).
                  Diperlukan untuk fnRekapMentah (NAMA RESTO dari file name).
    """
    files = _list_excel_files(folder_path)
    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            if raw:
                df = fn_buka_sheet(f, sheet_name, raw=True)
            else:
                df = fn_buka_sheet(f, sheet_name, header_row=header_row)
            if df is not None and len(df) > 0:
                if add_name_col:
                    # Insert Name column at position 0
                    df.insert(0, "Name", os.path.basename(f))
                dfs.append(df)
        except Exception as e:
            print(f"  [WARNING] Skip file {os.path.basename(f)}: {e}")

    if not dfs:
        return pd.DataFrame()

    if raw:
        # Raw mode: concat by position (columns are 0, 1, 2, ...)
        # Use ignore_index + sort=False for speed
        combined = pd.concat(dfs, ignore_index=True, sort=False)
    else:
        # Header mode: concat by column name
        combined = pd.concat(dfs, ignore_index=True, sort=False)
    return combined


def promote_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mirror M: Table.PromoteHeaders(table, [PromoteAllScalars = true]).
    Row 0 jadi header, drop row 0.
    Jika ada duplicate column names after promote, keep first.
    """
    if df.empty:
        return df

    # Extract row 0 as headers
    headers = df.iloc[0].tolist()

    # Drop row 0
    result = df.iloc[1:].reset_index(drop=True)

    # Set new headers
    # Handle None/NaN in headers → replace with "ColumnN"
    new_cols = []
    seen = {}
    for i, h in enumerate(headers):
        if h is None or (isinstance(h, float) and pd.isna(h)):
            h = f"Column{i+1}"
        h = str(h)
        # Handle duplicates: append _1, _2, etc.
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        new_cols.append(h)

    result.columns = new_cols
    return result


def table_skip(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Mirror M: Table.Skip(table, n). Skip first n rows."""
    if df.empty or n <= 0:
        return df
    return df.iloc[n:].reset_index(drop=True)


# =============================================================================
# COLUMN OPERATIONS (mirror M Table functions)
# =============================================================================

def table_select_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Mirror M: Table.SelectColumns(table, columns, MissingField.Ignore)."""
    available = [c for c in columns if c in df.columns]
    return df[available].copy()


def table_rename_columns(df: pd.DataFrame, rename_map: dict) -> pd.DataFrame:
    """Mirror M: Table.RenameColumns(table, {{old, new}, ...}, MissingField.Ignore)."""
    valid = {old: new for old, new in rename_map.items() if old in df.columns}
    return df.rename(columns=valid)


def safe_to_numeric(series: pd.Series) -> pd.Series:
    """Convert series ke numeric, null untuk yang gagal. Mirror Table.TransformColumnTypes ke number."""
    return pd.to_numeric(series, errors="coerce")


def safe_to_str(series: pd.Series) -> pd.Series:
    """Convert series ke string, null tetap null. Mirror Table.TransformColumnTypes ke text.
    OPTIMIZED: vectorized, no .apply()."""
    # Use vectorized approach: where notna, convert to str; where na, keep None
    mask = series.notna()
    result = pd.Series(index=series.index, dtype=object)
    result[mask] = series[mask].astype(str)
    result[~mask] = None
    return result


def date_to_day(series: pd.Series) -> pd.Series:
    """
    Mirror M: Table.TransformColumns(t, {{"Tanggal", Date.Day, Int64.Type}}).
    Ambil day-of-month dari datetime/date column. Return Int64.
    OPTIMIZED: vectorized via .dt accessor.
    """
    dt = pd.to_datetime(series, errors="coerce")
    return dt.dt.day.astype("Int64")
