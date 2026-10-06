"""
helpers.py — Helper functions yang mirror persis fnBukaSheet, fnCombineFolder,
dan fungsi text delimiter di Power Query M code.

PENTING: Pola skip+promote di M code diterjemahkan ke parameter `header` pandas:
- M: doPromote=true + Skip(3) + PromoteHeaders  →  pandas: header=4
  (Row 1 jadi header by fnBukaSheet, lalu skip 3 data rows = row 2,3,4,
   lalu promote row 5 = index 4)
- M: doPromote=false + Skip(3) + Skip(1) + PromoteHeaders  →  pandas: header=4
  (Skip 4 rows total, promote row 5 = index 4)
- M: doPromote=false + PromoteHeaders (no skip)  →  pandas: header=0
- M: doPromote=true (no skip, no re-promote)  →  pandas: header=0

Hasil akhirnya sama: header row ada di index `header` (0-indexed).
"""
import os
import re
import glob
import pandas as pd
import numpy as np
from typing import Optional, List


# =============================================================================
# TEXT DELIMITER FUNCTIONS (mirror persis M code)
# =============================================================================

def text_before_delimiter(s, delimiter: str = ".") -> Optional[str]:
    """
    Mirror M: Text.BeforeDelimiter(text, delimiter).
    Return bagian SEBELUM delimiter pertama. Jika tidak ada delimiter, return text utuh.
    """
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    s = str(s)
    idx = s.find(delimiter)
    if idx < 0:
        return s
    return s[:idx]


def text_after_delimiter(s, delimiter: str = ".") -> Optional[str]:
    """
    Mirror M: Text.AfterDelimiter(text, delimiter).
    Return bagian SETELAH delimiter pertama. Jika tidak ada delimiter, return text utuh.
    """
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    s = str(s)
    idx = s.find(delimiter)
    if idx < 0:
        return s
    return s[idx + len(delimiter):]


def text_between_delimiters(s, open_delim: str = "(", close_delim: str = ")") -> Optional[str]:
    """
    Mirror M: Text.BetweenDelimiters(text, openDelim, closeDelim).
    Return text antara openDelim pertama dan closeDelim setelahnya.
    Jika tidak ditemukan, return null.
    """
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
    # Filter: exclude hidden files & temp lock files (~$...)
    files = [f for f in files if not os.path.basename(f).startswith("~$")]
    files = [f for f in files if not f.startswith(".")]
    return sorted(files)


def fn_buka_sheet(file_path: str, sheet_name: str, header_row: int = 0) -> pd.DataFrame:
    """
    Mirror M: fnBukaSheet(binary, sheetName, doPromote).
    Baca sheet tertentu dari file Excel.

    header_row: index baris (0-indexed) yang menjadi header.
                Setara dengan: baca tanpa header → skip N rows → promote.
                - header_row=0  =  M: doPromote=true (no further skip/promote)
                - header_row=4  =  M: doPromote=true + Skip(3) + PromoteHeaders
                                   atau M: doPromote=false + Skip(3) + Skip(1) + PromoteHeaders
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, dtype=object)
    return df


def fn_combine_folder(folder_path: str, sheet_name: str, header_row: int = 0) -> pd.DataFrame:
    """
    Mirror M: fnCombineFolder(folderPath, sheetName, doPromote).
    Baca semua file Excel di folder, ambil sheet tertentu, gabungkan.

    header_row: lihat fn_buka_sheet.

    CATATAN: Berbeda dengan M code, kita TIDAK menambah kolom "Name" (nama file).
    Kolom Name di M code tidak pernah dipakai downstream (hanya menimbulkan
    duplikat kolom setelah PromoteHeaders). Output akhir sama.
    """
    files = _list_excel_files(folder_path)
    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            df = fn_buka_sheet(f, sheet_name, header_row=header_row)
            if df is not None and len(df) > 0:
                dfs.append(df)
        except Exception as e:
            print(f"  [WARNING] Skip file {os.path.basename(f)}: {e}")

    if not dfs:
        return pd.DataFrame()

    # Combine — align by column name (sama dengan Table.ExpandTableColumn di M)
    combined = pd.concat(dfs, ignore_index=True)
    return combined


# =============================================================================
# COLUMN OPERATIONS (mirror M Table functions)
# =============================================================================

def table_select_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Mirror M: Table.SelectColumns(table, columns, MissingField.Ignore).
    Pilih kolom yang ada, ignore yang tidak ada.
    """
    available = [c for c in columns if c in df.columns]
    return df[available].copy()


def table_rename_columns(df: pd.DataFrame, rename_map: dict) -> pd.DataFrame:
    """
    Mirror M: Table.RenameColumns(table, {{old, new}, ...}, MissingField.Ignore).
    Rename kolom yang ada, ignore yang tidak ada.
    """
    valid = {old: new for old, new in rename_map.items() if old in df.columns}
    return df.rename(columns=valid)


def safe_to_numeric(series: pd.Series) -> pd.Series:
    """Convert series ke numeric, null untuk yang gagal. Mirror Table.TransformColumnTypes ke number."""
    return pd.to_numeric(series, errors="coerce")


def safe_to_str(series: pd.Series) -> pd.Series:
    """Convert series ke string, null tetap null. Mirror Table.TransformColumnTypes ke text."""
    return series.apply(lambda x: None if x is None or (isinstance(x, float) and np.isnan(x)) else str(x))


def date_to_day(series: pd.Series) -> pd.Series:
    """
    Mirror M: Table.TransformColumns(t, {{"Tanggal", Date.Day, Int64.Type}}).
    Ambil day-of-month dari datetime/date column. Return Int64.
    """
    # Parse ke datetime jika belum
    dt = pd.to_datetime(series, errors="coerce")
    return dt.dt.day.astype("Int64")
