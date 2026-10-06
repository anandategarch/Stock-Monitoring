"""
excel_output.py — Generate output Excel "sama persis" dengan sample.
Menggunakan template-based approach: replace pivot cache records + definition,
keep pivot tables + slicers + styling dari template.

Alur:
1. Copy template xlsx → output
2. Unzip ke temp dir
3. Replace pivotCacheRecords1.xml + pivotCacheDefinition1.xml (data Append1)
4. Replace pivotCacheRecords2.xml + pivotCacheDefinition2.xml (data Rincian PO)
5. Modify pivotTable XML: remove <items> (biar Excel rebuild)
6. Modify slicerCache XML: remove <items>
7. Remove connections + Power Query (tidak dipakai)
8. Re-zip → output xlsx
"""
import os
import re
import shutil
import zipfile
import tempfile
import math
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


# =============================================================================
# FIELD CONFIGURATIONS (mirror persis struktur pivot cache di sample)
# =============================================================================

# Cache1 = Append1 (10 fields)
CACHE1_FIELDS = [
    {"name": "Nama Barang",              "type": "shared_text"},
    {"name": "NAMA RESTO",               "type": "shared_text"},
    {"name": "Tanggal",                   "type": "shared_int"},
    {"name": "JENIS",                     "type": "shared_text"},
    {"name": "NILAI",                     "type": "inline_num"},
    {"name": "Nomor",                     "type": "inline_str"},
    {"name": "Nomor PO",                  "type": "inline_str"},
    {"name": "#Tgl/Jam Pembuatan IT",     "type": "inline_str"},
    {"name": "KATEGORI",                  "type": "shared_text"},
    {"name": "SOURCE KIRIMAN",            "type": "shared_text"},
]

# Cache2 = Rincian PO (13 fields)
CACHE2_FIELDS = [
    {"name": "Nomor #",                   "type": "shared_text"},
    {"name": "Tanggal",                   "type": "shared_date"},
    {"name": "Cabang PO",                 "type": "shared_text"},
    {"name": "Pemasok",                   "type": "shared_text"},
    {"name": "Nama Barang",               "type": "shared_text"},
    {"name": "Satuan",                    "type": "shared_text"},
    {"name": "Kuantitas",                 "type": "inline_num"},
    {"name": "@Harga",                    "type": "inline_num"},
    {"name": "Total Harga",               "type": "inline_num"},
    {"name": "Keterangan PO",             "type": "shared_text"},
    {"name": "Status Pesanan Pembelian",  "type": "shared_text"},
    {"name": "Tgl/Jam Pembuatan",         "type": "shared_datetime"},
    {"name": "DBS_Kategori.KATEGORI",     "type": "shared_text"},
]


# =============================================================================
# XML HELPERS
# =============================================================================

def _xml_escape(val: str) -> str:
    """Escape XML special characters."""
    if val is None:
        return ""
    return (str(val)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _val_to_str(val) -> Optional[str]:
    """Convert value to string for cache. None/NaN → None."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return str(val)


def _val_to_date_str(val) -> Optional[str]:
    """Convert date/datetime to ISO format for cache: YYYY-MM-DDTHH:MM:SS"""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%dT%H:%M:%S")
    # Try parse
    try:
        dt = pd.to_datetime(val)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return str(val)


def _val_to_num(val) -> Optional[float]:
    """Convert value to number. None/NaN → None."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


# =============================================================================
# SHARED ITEMS BUILDER
# =============================================================================

def _build_shared_items_text(values: List[str]) -> (List[str], Dict[str, int]):
    """Build shared items for text field.
    Returns (ordered list of unique values, value→index map).
    Null/None values are tracked separately (containsBlank).
    """
    seen = []
    lookup = {}
    has_blank = False
    for v in values:
        if v is None or v == "":
            has_blank = True
            continue
        if v not in lookup:
            lookup[v] = len(seen)
            seen.append(v)
    return seen, lookup, has_blank


def _build_shared_items_int(values: List[int]) -> (List[int], Dict[int, int]):
    """Build shared items for integer field."""
    seen = []
    lookup = {}
    for v in values:
        if v is None:
            continue
        v_int = int(v)
        if v_int not in lookup:
            lookup[v_int] = len(seen)
            seen.append(v_int)
    return seen, lookup


def _build_shared_items_date(values: List[str]) -> (List[str], Dict[str, int]):
    """Build shared items for date/datetime field (ISO format strings)."""
    seen = []
    lookup = {}
    for v in values:
        if v is None:
            continue
        if v not in lookup:
            lookup[v] = len(seen)
            seen.append(v)
    return seen, lookup


# =============================================================================
# CACHE GENERATION
# =============================================================================

def _generate_shared_items_xml(field: dict, shared_vals: list, has_blank: bool,
                                min_val=None, max_val=None) -> str:
    """Generate <sharedItems> XML for a cacheField."""
    ftype = field["type"]

    if ftype == "shared_text":
        count = len(shared_vals) + (1 if has_blank else 0)
        attrs = f'count="{count}"'
        if has_blank:
            attrs += ' containsBlank="1"'
        items = "".join(f'<s v="{_xml_escape(v)}"/>' for v in shared_vals)
        return f'<sharedItems {attrs}>{items}</sharedItems>'

    elif ftype == "shared_int":
        count = len(shared_vals)
        if count > 0:
            mn = min(shared_vals)
            mx = max(shared_vals)
            attrs = (f'containsSemiMixedTypes="0" containsString="0" '
                     f'containsNumber="1" containsInteger="1" '
                     f'minValue="{mn}" maxValue="{mx}" count="{count}"')
        else:
            attrs = 'count="0"'
        items = "".join(f'<n v="{v}"/>' for v in shared_vals)
        return f'<sharedItems {attrs}>{items}</sharedItems>'

    elif ftype == "shared_date":
        count = len(shared_vals)
        if count > 0:
            mn = min(shared_vals)
            mx = max(shared_vals)
            attrs = (f'containsSemiMixedTypes="0" containsNonDate="0" '
                     f'containsDate="1" containsString="0" '
                     f'minDate="{mn}" maxDate="{mx}" count="{count}"')
        else:
            attrs = 'count="0"'
        items = "".join(f'<d v="{v}"/>' for v in shared_vals)
        return f'<sharedItems {attrs}>{items}</sharedItems>'

    elif ftype == "shared_datetime":
        count = len(shared_vals)
        if count > 0:
            mn = min(shared_vals)
            mx = max(shared_vals)
            attrs = (f'containsSemiMixedTypes="0" containsNonDate="0" '
                     f'containsDate="1" containsString="0" '
                     f'minDate="{mn}" maxDate="{mx}" count="{count}"')
        else:
            attrs = 'count="0"'
        items = "".join(f'<d v="{v}"/>' for v in shared_vals)
        return f'<sharedItems {attrs}>{items}</sharedItems>'

    elif ftype == "inline_num":
        attrs = 'containsString="0" containsBlank="1" containsNumber="1"'
        if min_val is not None and max_val is not None:
            attrs += f' minValue="{min_val}" maxValue="{max_val}"'
        return f'<sharedItems {attrs}/>'

    elif ftype == "inline_str":
        return '<sharedItems/>'

    return '<sharedItems/>'


def _generate_cache_definition(fields: list, shared_data: list, record_count: int,
                                cache_id: str, refreshed_by: str = "Stock Monitor") -> str:
    """Generate pivotCacheDefinition XML."""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    # Excel serial date (approximate)
    serial_date = (datetime.now() - datetime(1899, 12, 30)).total_seconds() / 86400.0

    header = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<pivotCacheDefinition '
        f'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        f'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        f'mc:Ignorable="xr" '
        f'xmlns:xr="http://schemas.microsoft.com/office/spreadsheetml/2014/revision" '
        f'refreshedBy="{refreshed_by}" '
        f'refreshedDate="{serial_date:.15f}" '
        f'createdVersion="7" refreshedVersion="7" minRefreshableVersion="3" '
        f'recordCount="{record_count}" '
        f'xr:uid="{cache_id}">'
        f'<cacheSource type="external"/>'
        f'<cacheFields count="{len(fields)}">'
    )

    field_xmls = []
    for i, field in enumerate(fields):
        sd = shared_data[i]
        si_xml = _generate_shared_items_xml(
            field, sd["shared_vals"], sd["has_blank"],
            sd.get("min_val"), sd.get("max_val")
        )
        field_xmls.append(f'<cacheField name="{_xml_escape(field["name"])}" numFmtId="0">{si_xml}</cacheField>')

    footer = '</cacheFields></pivotCacheDefinition>'
    return header + "".join(field_xmls) + footer


def _generate_cache_records(df: pd.DataFrame, fields: list, shared_data: list,
                              output_path: str = None, chunk_size: int = 100000) -> str:
    """Generate pivotCacheRecords XML from DataFrame.
    STREAMING MODE: writes directly to file if output_path given.
    CHUNKED: processes in chunks of 100k records.

    ULTRA-OPTIMIZED: pre-compute XML map per shared field, then .map() (C-level).
    Inline fields use .map() with format function.
    Records built with zip + join (single pass).
    """
    n = len(df)

    # === STEP 1: Pre-convert each column to a list of XML fragment strings ===
    col_lists = []

    for i, field in enumerate(fields):
        ftype = field["type"]
        name = field["name"]

        if name in df.columns:
            col = df[name]
        else:
            col = pd.Series([None] * n)

        if ftype == "shared_text":
            lookup = shared_data[i]["lookup"]
            # Pre-compute XML map: index → '<x v="N"/>', plus NaN → '<m/>'
            max_idx = max(lookup.values()) if lookup else -1
            xml_map = {v: f'<x v="{v}"/>' for v in lookup.values()}
            # .map(lookup) = C-level dict lookup → Series of int or NaN
            indices = col.astype(str).map(lookup)
            # .map(xml_map) = C-level dict lookup → Series of XML strings
            xml_series = indices.map(xml_map)
            # Fill NaN (values not in lookup) with '<m/>'
            xml_list = xml_series.fillna('<m/>').tolist()

        elif ftype == "shared_int":
            lookup = shared_data[i]["lookup"]
            max_idx = max(lookup.values()) if lookup else -1
            xml_map = {v: f'<x v="{v}"/>' for v in lookup.values()}
            nums = pd.to_numeric(col, errors="coerce")
            # Map each number to lookup index
            indices = nums.map(lambda v: lookup.get(int(v)) if pd.notna(v) else None)
            xml_series = indices.map(xml_map) if xml_map else None
            if xml_series is not None:
                xml_list = xml_series.fillna('<m/>').tolist()
            else:
                xml_list = ['<m/>'] * n

        elif ftype in ("shared_date", "shared_datetime"):
            lookup = shared_data[i]["lookup"]
            xml_map = {v: f'<x v="{v}"/>' for v in lookup.values()}
            dt = pd.to_datetime(col, errors="coerce")
            iso_vals = dt.dt.strftime("%Y-%m-%dT%H:%M:%S")
            indices = iso_vals.map(lookup)
            xml_series = indices.map(xml_map) if xml_map else None
            if xml_series is not None:
                xml_list = xml_series.fillna('<m/>').tolist()
            else:
                xml_list = ['<m/>'] * n

        elif ftype == "inline_num":
            nums = pd.to_numeric(col, errors="coerce")
            # Split into 3 categories: NaN, integer-valued, float
            # FIX BUG: jangan pakai .astype('Int64') — crash kalau ada float non-integer (e.g., 0.5)
            # Gunakan modulo check: 5.0 % 1 == 0 (int), 5.5 % 1 == 0.5 (float)
            is_nan = nums.isna()
            is_int = ~is_nan & (nums % 1 == 0)
            is_float = ~is_nan & ~is_int

            xml = pd.Series('<m/>', index=col.index, dtype=object)
            # Integers: '<n v="N"/>'
            int_vals = nums[is_int].astype(int).astype(str)
            xml[is_int] = '<n v="' + int_vals + '"/>'
            # Floats: '<n v="X"/>'
            float_vals = nums[is_float].astype(str)
            xml[is_float] = '<n v="' + float_vals + '"/>'
            xml_list = xml.tolist()

        elif ftype == "inline_str":
            _escape = _xml_escape
            # Convert to string, escape XML, wrap in <s v="..."/>
            # NaN/None → '<m/>'
            is_null = col.isna()
            str_vals = col.astype(str).where(~is_null, other='')
            escaped = str_vals.apply(_escape)
            xml = pd.Series('<m/>', index=col.index, dtype=object)
            xml[~is_null] = '<s v="' + escaped[~is_null] + '"/>'
            xml_list = xml.tolist()

        col_lists.append(xml_list)

    # === STEP 2: Build records with zip + join ===
    if output_path is not None:
        with open(output_path, "w", encoding="utf-8", buffering=1 << 20) as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
            f.write('<pivotCacheRecords xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                    f'count="{n}">')

            for start in range(0, n, chunk_size):
                end = min(start + chunk_size, n)
                chunk_cols = [col[start:end] for col in col_lists]
                records = ['<r>' + ''.join(parts) + '</r>' for parts in zip(*chunk_cols)]
                f.write("".join(records))

                if n >= 100000 and (start // chunk_size) % 5 == 0 and start > 0:
                    print(f"    ... records {end}/{n} ({100*end//n}%)", flush=True)

            f.write('</pivotCacheRecords>')
        return None
    else:
        records = ['<r>' + ''.join(parts) + '</r>' for parts in zip(*col_lists)]
        parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n']
        parts.append('<pivotCacheRecords xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                     'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                     f'count="{n}">')
        parts.extend(records)
        parts.append('</pivotCacheRecords>')
        return "".join(parts)


def _build_shared_data(df: pd.DataFrame, fields: list) -> list:
    """Build shared items data for each field."""
    shared_data = []
    for field in fields:
        name = field["name"]
        ftype = field["type"]
        col = df[name] if name in df.columns else pd.Series(dtype=object)

        if ftype == "shared_text":
            vals = [_val_to_str(v) for v in col.tolist()]
            shared_vals, lookup, has_blank = _build_shared_items_text(vals)
            shared_data.append({"shared_vals": shared_vals, "lookup": lookup, "has_blank": has_blank})

        elif ftype == "shared_int":
            vals = []
            for v in col.tolist():
                try:
                    if v is not None and not (isinstance(v, float) and pd.isna(v)):
                        vals.append(int(v))
                except (TypeError, ValueError):
                    pass
            shared_vals, lookup = _build_shared_items_int(vals)
            shared_data.append({"shared_vals": shared_vals, "lookup": lookup, "has_blank": False})

        elif ftype in ("shared_date", "shared_datetime"):
            vals = [_val_to_date_str(v) for v in col.tolist()]
            vals = [v for v in vals if v is not None]
            shared_vals, lookup = _build_shared_items_date(vals)
            shared_data.append({"shared_vals": shared_vals, "lookup": lookup, "has_blank": False})

        elif ftype == "inline_num":
            nums = [_val_to_num(v) for v in col.tolist()]
            nums_valid = [n for n in nums if n is not None]
            min_val = min(nums_valid) if nums_valid else None
            max_val = max(nums_valid) if nums_valid else None
            shared_data.append({"shared_vals": [], "lookup": {}, "has_blank": False,
                                "min_val": min_val, "max_val": max_val})

        elif ftype == "inline_str":
            shared_data.append({"shared_vals": [], "lookup": {}, "has_blank": False})

    return shared_data


# =============================================================================
# LIGHT MODE — WORKSHEET SOURCE APPROACH
# =============================================================================
# When light_mode=True, we don't generate pivotCacheRecords1.xml/2.xml.
# Instead we write the raw data to new sheets (SourceData1, SourceData2) and
# regenerate pivotCacheDefinition1.xml/2.xml with cacheSource type="worksheet"
# pointing at those sheets. The pivotTable XML gets refreshOnLoad="1" and its
# rowItems/colItems are emptied so Excel rebuilds them on first refresh.

def _col_letter(col_idx: int) -> str:
    """0-indexed column number → Excel letter (0=A, 25=Z, 26=AA, 702=AAA)."""
    result = ""
    col_idx += 1
    while col_idx > 0:
        col_idx, rem = divmod(col_idx - 1, 26)
        result = chr(65 + rem) + result
    return result


def _format_cell_value_xml(val) -> str:
    """Format a single Python/pandas value as the inner XML of <c>.
    Returns "" for null/NaN. Caller is responsible for wrapping <c r="..." ...>.

    Strings → escaped inline (caller adds t="str")
    Numbers (int/float) → numeric body
    Datetime → ISO string (caller adds t="str")
    """
    # Handle null / NaN
    if val is None:
        return ""
    try:
        if pd.isna(val):
            return ""
    except (TypeError, ValueError):
        pass

    # Booleans (must check before int because bool is subclass of int)
    if isinstance(val, (bool, np.bool_)):
        return "1" if val else "0"

    # Datetime / Timestamp
    if isinstance(val, (datetime, date, pd.Timestamp)):
        if isinstance(val, pd.Timestamp):
            return _xml_escape(val.strftime("%Y-%m-%d %H:%M:%S"))
        return _xml_escape(val.strftime("%Y-%m-%d %H:%M:%S"))

    # Integer
    if isinstance(val, (int, np.integer)):
        return str(int(val))

    # Float — preserve integers-as-int formatting (5.0 → "5", 5.5 → "5.5")
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return ""
        if val == int(val):
            return str(int(val))
        return repr(float(val))

    # Fallback: stringify
    return _xml_escape(str(val))


def _cell_value_type(val) -> str:
    """Return cell type attribute for OOXML inline string cells.
    Returns "str" for text/datetime, "" (numeric default) for numbers.
    """
    if val is None:
        return "str"  # null cell, render as empty t="str"
    try:
        if pd.isna(val):
            return "str"
    except (TypeError, ValueError):
        pass
    if isinstance(val, (bool, np.bool_)):
        return ""
    if isinstance(val, (datetime, date, pd.Timestamp)):
        return "str"
    if isinstance(val, (int, np.integer)):
        return ""
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return "str"
        return ""
    return "str"


def _write_sheet_xml_streaming(df: pd.DataFrame, output_xml_path: str,
                                columns: list, chunk_size: int = 50000) -> int:
    """Write DataFrame to sheet XML file (streaming, chunked).
    Header at row 1, data from row 2.

    Args:
        df: DataFrame to write
        output_xml_path: path to output XML file
        columns: ordered list of column names to write (defines column order
                 in the sheet; columns not present in df are written as empty)
        chunk_size: number of rows per write chunk

    Returns:
        Last row number written (1 = header only, 2 = 1 data row, etc.)
    """
    n = len(df)
    n_cols = len(columns)
    last_col_letter = _col_letter(n_cols - 1)
    last_row = n + 1  # header + n data rows

    # Pre-resolve column Series for fast access (None if missing)
    col_series = []
    for col_name in columns:
        if col_name in df.columns:
            col_series.append(df[col_name])
        else:
            col_series.append(None)

    # Write XML
    with open(output_xml_path, "w", encoding="utf-8", buffering=1 << 20) as f:
        # XML header + worksheet open tag
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        f.write(
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        )
        # Dimension
        f.write(f'<dimension ref="A1:{last_col_letter}{last_row}"/>')
        # Sheet views — plain (no frozen panes for source data)
        f.write('<sheetViews><sheetView workbookViewId="0"/></sheetViews>')
        f.write('<sheetFormatPr defaultRowHeight="14.5"/>')
        f.write('<sheetData>')

        # Header row (row 1)
        f.write('<row r="1" spans="1:%d">' % n_cols)
        for col_idx, col_name in enumerate(columns):
            cell_ref = f"{_col_letter(col_idx)}1"
            f.write(f'<c r="{cell_ref}" t="str"><v>{_xml_escape(col_name)}</v></c>')
        f.write('</row>')

        # Data rows (rows 2..n+1) — chunked
        if n > 0:
            for chunk_start in range(0, n, chunk_size):
                chunk_end = min(chunk_start + chunk_size, n)
                # Pre-extract chunk data per column as Python lists (fast .tolist())
                chunk_data = []
                for s in col_series:
                    if s is None:
                        chunk_data.append([None] * (chunk_end - chunk_start))
                    else:
                        chunk_data.append(s.iloc[chunk_start:chunk_end].tolist())

                for i in range(chunk_end - chunk_start):
                    row_num = chunk_start + i + 2  # 1-indexed Excel row
                    f.write('<row r="%d" spans="1:%d">' % (row_num, n_cols))
                    for col_idx in range(n_cols):
                        val = chunk_data[col_idx][i]
                        cell_ref = f"{_col_letter(col_idx)}{row_num}"
                        body = _format_cell_value_xml(val)
                        if body == "":
                            # Null/empty cell — write empty <c t="str"/>
                            f.write(f'<c r="{cell_ref}" t="str"/>')
                        else:
                            t_attr = _cell_value_type(val)
                            t_attr_str = f' t="{t_attr}"' if t_attr else ""
                            f.write(f'<c r="{cell_ref}"{t_attr_str}><v>{body}</v></c>')
                    f.write('</row>')

                # Progress print for very large datasets
                if n >= 100000 and (chunk_start // chunk_size) % 5 == 0 and chunk_start > 0:
                    print(f"    ... sheet rows {chunk_end}/{n} ({100*chunk_end//n}%)", flush=True)

        # Close sheetData + worksheet
        f.write('</sheetData></worksheet>')

    return last_row


def _generate_cache_definition_worksheet(fields: list, sheet_name: str,
                                          last_row: int, cache_id: str,
                                          refreshed_by: str = "Stock Monitor") -> str:
    """Generate pivotCacheDefinition XML for worksheet source approach.
    Empty sharedItems — Excel will rebuild from worksheet on first refresh.
    """
    n_cols = len(fields)
    ref = f"A1:{_col_letter(n_cols - 1)}{last_row}"
    now_serial = (datetime.now() - datetime(1899, 12, 30)).total_seconds() / 86400.0
    record_count = max(0, last_row - 1)

    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n']
    parts.append(
        f'<pivotCacheDefinition '
        f'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        f'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        f'mc:Ignorable="xr" '
        f'xmlns:xr="http://schemas.microsoft.com/office/spreadsheetml/2014/revision" '
        f'refreshedBy="{_xml_escape(refreshed_by)}" '
        f'refreshedDate="{now_serial:.15f}" '
        f'createdVersion="7" refreshedVersion="7" minRefreshableVersion="3" '
        f'recordCount="{record_count}" '
        f'xr:uid="{cache_id}">'
    )
    parts.append(
        f'<cacheSource type="worksheet">'
        f'<worksheetSource ref="{ref}" sheet="{_xml_escape(sheet_name)}"/>'
        f'</cacheSource>'
    )
    parts.append(f'<cacheFields count="{n_cols}">')
    for field in fields:
        parts.append(
            f'<cacheField name="{_xml_escape(field["name"])}" numFmtId="0">'
            f'<sharedItems/>'
            f'</cacheField>'
        )
    parts.append('</cacheFields>')
    parts.append('</pivotCacheDefinition>')
    return "".join(parts)


def _modify_pivot_table_for_worksheet_source(xml: str) -> str:
    """Modify pivotTable XML for worksheet source + refreshOnLoad.
    1. Add refreshOnLoad="1" to <pivotTableDefinition> root (if not already present)
    2. Remove <rowItems>...</rowItems> content (keep empty element)
    3. Remove <colItems>...</colItems> content (keep empty element)
    4. Also clear <pivotField> items (existing _remove_items_from_pivot_fields)
    """
    # 1. Add refreshOnLoad="1" if not present
    if 'refreshOnLoad="' not in xml[:xml.find('>') + 1]:
        xml = re.sub(r'(<pivotTableDefinition\b[^>]*?)(>)',
                     r'\1 refreshOnLoad="1"\2', xml, count=1)

    # 2. Empty <rowItems>...</rowItems>
    xml = re.sub(r'(<rowItems\b[^>]*>).*?</rowItems>',
                 r'\1</rowItems>', xml, flags=re.DOTALL)
    # Handle self-closing <rowItems/> (no-op, but be safe)
    xml = re.sub(r'(<rowItems\b[^>]*/>)', r'\1', xml)

    # 3. Empty <colItems>...</colItems>
    xml = re.sub(r'(<colItems\b[^>]*>).*?</colItems>',
                 r'\1</colItems>', xml, flags=re.DOTALL)
    xml = re.sub(r'(<colItems\b[^>]*/>)', r'\1', xml)

    # 4. Clear pivotField items (let Excel rebuild)
    xml = _remove_items_from_pivot_fields(xml)

    # 5. Reset pageField item filters (Excel will reapply defaults on refresh)
    xml = _remove_page_field_items(xml)

    return xml


def _next_rid(rels_xml: str) -> str:
    """Find next available rId in workbook.xml.rels.
    Parses existing Id="rIdN" attributes and returns "rId{max+1}".
    """
    ids = re.findall(r'Id="rId(\d+)"', rels_xml)
    if not ids:
        return "rId1"
    max_id = max(int(x) for x in ids)
    return f"rId{max_id + 1}"


def _next_sheet_id(workbook_xml: str) -> int:
    """Find next available sheetId in workbook.xml."""
    ids = re.findall(r'sheetId="(\d+)"', workbook_xml)
    if not ids:
        return 1
    return max(int(x) for x in ids) + 1


def _update_workbook_xml_add_sheets(workbook_xml: str, sheet_specs: list) -> str:
    """Add <sheet> entries to <sheets> in workbook.xml.

    Args:
        workbook_xml: original workbook.xml content
        sheet_specs: list of dicts: {"name": ..., "sheetId": int, "rId": ...}

    Returns:
        Modified workbook.xml
    """
    new_entries = "".join(
        f'<sheet name="{_xml_escape(s["name"])}" sheetId="{s["sheetId"]}" r:id="{s["rId"]}"/>'
        for s in sheet_specs
    )
    # Insert before </sheets>
    return workbook_xml.replace('</sheets>', new_entries + '</sheets>')


def _update_workbook_rels_add_sheets(rels_xml: str, sheet_specs: list) -> str:
    """Add <Relationship> entries for new worksheet sheets in workbook.xml.rels.

    Args:
        rels_xml: original workbook.xml.rels content
        sheet_specs: list of dicts: {"rId": ..., "target": "worksheets/sheetN.xml"}

    Returns:
        Modified rels XML
    """
    new_rels = "".join(
        f'<Relationship Id="{s["rId"]}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="{s["target"]}"/>'
        for s in sheet_specs
    )
    return rels_xml.replace('</Relationships>', new_rels + '</Relationships>')


def _update_content_types_add_sheets(content_types_xml: str, sheet_paths: list) -> str:
    """Add <Override> entries for new sheet XML files in [Content_Types].xml.

    Args:
        content_types_xml: original [Content_Types].xml content
        sheet_paths: list of part names, e.g. "/xl/worksheets/sheet3.xml"

    Returns:
        Modified content_types XML
    """
    new_overrides = "".join(
        f'<Override PartName="{p}" '
        f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for p in sheet_paths
    )
    return content_types_xml.replace('</Types>', new_overrides + '</Types>')


def _empty_pivot_cache_rels(rels_xml: str) -> str:
    """Empty a pivotCacheDefinitionN.xml.rels file (remove pivotCacheRecords
    relationship since records file is deleted in LightMode).
    """
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')


# =============================================================================
# LIGHT MODE — MAIN ENTRY POINT
# =============================================================================

def _generate_output_light_mode(append1_df: pd.DataFrame,
                                 rincian_po_df: pd.DataFrame,
                                 temp_dir: str) -> None:
    """LightMode Excel output: worksheet source approach.
    Mutates files inside temp_dir.
    """
    # ---- Filter append1_df: NILAI != 0 (reduce rows ~50%) ----
    if not append1_df.empty and "NILAI" in append1_df.columns:
        append1_filtered = append1_df[append1_df["NILAI"] != 0].reset_index(drop=True)
    else:
        append1_filtered = append1_df.copy()
    print(f"  [Excel][Light] Append1 filtered (NILAI != 0): "
          f"{len(append1_df)} → {len(append1_filtered)} rows")

    # ---- Determine column order: full CACHE1_FIELDS (10 cols) ----
    # Even if append1_df doesn't have InfoColumns (LightMode pipeline),
    # the pivotTable1.xml references 10 fields, so we must keep 10 columns
    # in SourceData1 to match cacheField count.
    append1_columns = [f["name"] for f in CACHE1_FIELDS]
    rincian_columns = [f["name"] for f in CACHE2_FIELDS]

    # ---- Write sheet3.xml (SourceData1) ----
    print("  [Excel][Light] Writing SourceData1 sheet (Append1)...")
    sheet3_path = os.path.join(temp_dir, "xl", "worksheets", "sheet3.xml")
    last_row_1 = _write_sheet_xml_streaming(
        append1_filtered, sheet3_path, append1_columns
    )

    # ---- Write sheet4.xml (SourceData2) ----
    print("  [Excel][Light] Writing SourceData2 sheet (Rincian PO)...")
    sheet4_path = os.path.join(temp_dir, "xl", "worksheets", "sheet4.xml")
    last_row_2 = _write_sheet_xml_streaming(
        rincian_po_df, sheet4_path, rincian_columns
    )

    # ---- Generate pivotCacheDefinition1.xml (worksheet source) ----
    print("  [Excel][Light] Generating pivotCacheDefinition1 (worksheet source)...")
    def1_xml = _generate_cache_definition_worksheet(
        CACHE1_FIELDS, "SourceData1", last_row_1,
        "{8DF41EF9-DA36-4297-80B1-A53D88DC21E8}"
    )
    with open(os.path.join(temp_dir, "xl", "pivotCache",
                            "pivotCacheDefinition1.xml"), "w", encoding="utf-8") as f:
        f.write(def1_xml)

    # ---- Generate pivotCacheDefinition2.xml (worksheet source) ----
    print("  [Excel][Light] Generating pivotCacheDefinition2 (worksheet source)...")
    def2_xml = _generate_cache_definition_worksheet(
        CACHE2_FIELDS, "SourceData2", last_row_2,
        "{D76DDFB7-5659-4E65-A107-530BC38ABF47}"
    )
    with open(os.path.join(temp_dir, "xl", "pivotCache",
                            "pivotCacheDefinition2.xml"), "w", encoding="utf-8") as f:
        f.write(def2_xml)

    # ---- Delete pivotCacheRecords1.xml & pivotCacheRecords2.xml ----
    print("  [Excel][Light] Deleting pivotCacheRecords files...")
    for fn in ("pivotCacheRecords1.xml", "pivotCacheRecords2.xml"):
        p = os.path.join(temp_dir, "xl", "pivotCache", fn)
        if os.path.exists(p):
            os.remove(p)

    # ---- Empty pivotCacheDefinitionN.xml.rels (remove records relationship) ----
    for fn in ("pivotCacheDefinition1.xml.rels", "pivotCacheDefinition2.xml.rels"):
        p = os.path.join(temp_dir, "xl", "pivotCache", "_rels", fn)
        if os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(_empty_pivot_cache_rels(""))

    # ---- Modify pivotTable1.xml & pivotTable2.xml ----
    print("  [Excel][Light] Modifying pivot tables (refreshOnLoad + clear items)...")
    for pt_file in ["pivotTable1.xml", "pivotTable2.xml"]:
        pt_path = os.path.join(temp_dir, "xl", "pivotTables", pt_file)
        if os.path.exists(pt_path):
            with open(pt_path, "r", encoding="utf-8") as f:
                xml = f.read()
            xml = _modify_pivot_table_for_worksheet_source(xml)
            with open(pt_path, "w", encoding="utf-8") as f:
                f.write(xml)

    # ---- Modify slicerCache XML (remove items) ----
    print("  [Excel][Light] Modifying slicer caches...")
    for sc_file in ["slicerCache1.xml", "slicerCache2.xml"]:
        sc_path = os.path.join(temp_dir, "xl", "slicerCaches", sc_file)
        if os.path.exists(sc_path):
            with open(sc_path, "r", encoding="utf-8") as f:
                xml = f.read()
            xml = _remove_slicer_items(xml)
            with open(sc_path, "w", encoding="utf-8") as f:
                f.write(xml)

    # ---- Remove connections + Power Query ----
    print("  [Excel][Light] Removing Power Query connections...")
    _remove_connections(temp_dir)

    # ---- Update workbook.xml: add SourceData1 + SourceData2 sheets ----
    print("  [Excel][Light] Updating workbook.xml + rels + content-types...")
    wb_path = os.path.join(temp_dir, "xl", "workbook.xml")
    with open(wb_path, "r", encoding="utf-8") as f:
        wb_xml = f.read()

    wb_rels_path = os.path.join(temp_dir, "xl", "_rels", "workbook.xml.rels")
    with open(wb_rels_path, "r", encoding="utf-8") as f:
        wb_rels_xml = f.read()

    # Find next available rId and sheetId
    rid1 = _next_rid(wb_rels_xml)
    rid2 = _next_rid(wb_rels_xml + f'<Relationship Id="{rid1}"')  # bump past rid1
    sheet_id_1 = _next_sheet_id(wb_xml)
    sheet_id_2 = sheet_id_1 + 1

    sheet_specs = [
        {"name": "SourceData1", "sheetId": sheet_id_1, "rId": rid1,
         "target": "worksheets/sheet3.xml"},
        {"name": "SourceData2", "sheetId": sheet_id_2, "rId": rid2,
         "target": "worksheets/sheet4.xml"},
    ]

    wb_xml = _update_workbook_xml_add_sheets(
        wb_xml,
        [{"name": s["name"], "sheetId": s["sheetId"], "rId": s["rId"]}
         for s in sheet_specs]
    )
    with open(wb_path, "w", encoding="utf-8") as f:
        f.write(wb_xml)

    # ---- Update workbook.xml.rels ----
    wb_rels_xml = _update_workbook_rels_add_sheets(
        wb_rels_xml,
        [{"rId": s["rId"], "target": s["target"]} for s in sheet_specs]
    )
    with open(wb_rels_path, "w", encoding="utf-8") as f:
        f.write(wb_rels_xml)

    # ---- Update [Content_Types].xml ----
    ct_path = os.path.join(temp_dir, "[Content_Types].xml")
    with open(ct_path, "r", encoding="utf-8") as f:
        ct_xml = f.read()
    ct_xml = _update_content_types_add_sheets(
        ct_xml,
        ["/xl/worksheets/sheet3.xml", "/xl/worksheets/sheet4.xml"]
    )
    with open(ct_path, "w", encoding="utf-8") as f:
        f.write(ct_xml)


# =============================================================================
# PIVOT TABLE & SLICER MODIFICATION
# =============================================================================

def _remove_items_from_pivot_fields(xml: str) -> str:
    """Remove <items> from each <pivotField> in pivotTable XML.
    Excel will rebuild items on open.
    FIX BUG-24: handle BOTH <items>...</items> AND self-closing <items .../>.
    """
    # Find each pivotField element and remove its <items> child
    def replace_pivot_field(m):
        field_xml = m.group(0)
        # Remove <items ...>...</items> (open-close form)
        field_xml = re.sub(r'<items[^>]*>.*?</items>', '', field_xml, flags=re.DOTALL)
        # Remove self-closing <items .../> (FIX BUG-24)
        field_xml = re.sub(r'<items[^>]*/>', '', field_xml)
        return field_xml

    # Match <pivotField ...>...</pivotField> or <pivotField .../>
    result = re.sub(r'<pivotField\b[^>]*(?:/>|>.*?</pivotField>)', replace_pivot_field, xml, flags=re.DOTALL)
    return result


def _remove_page_field_items(xml: str) -> str:
    """Remove item attribute from <pageField> elements (reset filter to All)."""
    return re.sub(r'(<pageField\b[^>]*?)\s+item="\d+"', r'\1', xml)


def _remove_slicer_items(xml: str) -> str:
    """Remove <items> from slicerCache XML."""
    return re.sub(r'<items>.*?</items>', '', xml, flags=re.DOTALL)


# =============================================================================
# CONNECTIONS & POWER QUERY REMOVAL
# =============================================================================

def _remove_connections(temp_dir: str):
    """Remove Power Query connections and DataMashup.
    The pivot cache uses embedded records, so connections are not needed.
    """
    # Empty the connections.xml file (keep valid XML structure)
    conn_path = os.path.join(temp_dir, "xl", "connections.xml")
    if os.path.exists(conn_path):
        with open(conn_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                    '<connections xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
                    'mc:Ignorable="xr16" '
                    'xmlns:xr16="http://schemas.microsoft.com/office/spreadsheetml/2017/revision16" '
                    'count="0"/>')

    # Remove customXml/item1.xml (Power Query DataMashup)
    customxml_path = os.path.join(temp_dir, "customXml", "item1.xml")
    if os.path.exists(customxml_path):
        os.remove(customxml_path)
    customxml_rels = os.path.join(temp_dir, "customXml", "_rels", "item1.xml.rels")
    if os.path.exists(customxml_rels):
        os.remove(customxml_rels)


# =============================================================================
# MAIN OUTPUT GENERATOR
# =============================================================================

def generate_output(append1_df: pd.DataFrame, rincian_po_df: pd.DataFrame,
                     template_path: str, output_path: str,
                     light_mode: bool = True) -> str:
    """
    Generate output Excel "sama persis" dengan template.

    Args:
        append1_df: DataFrame dari build_append1() (long format, 10 columns)
        rincian_po_df: DataFrame dari build_rincian_po() (13 columns)
        template_path: Path ke template xlsx
        output_path: Path output xlsx
        light_mode: True (default) → worksheet source approach (Excel refresh
                    pivot on open). False → pivot cache records approach
                    (embedded records, current FULL behavior).

    Returns:
        Path ke output file.
    """
    print(f"  [Excel] Template: {template_path}")
    print(f"  [Excel] Output: {output_path}")
    print(f"  [Excel] Mode: {'LIGHT (worksheet source)' if light_mode else 'FULL (pivot cache records)'}")
    print(f"  [Excel] Append1 data: {len(append1_df)} rows")
    print(f"  [Excel] Rincian PO data: {len(rincian_po_df)} rows")

    # Create output directory if needed
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # 1. Copy template → output
    shutil.copy2(template_path, output_path)

    # 2. Unzip to temp dir
    with tempfile.TemporaryDirectory() as temp_dir:
        print("  [Excel] Unzipping template...")
        with zipfile.ZipFile(output_path, "r") as zf:
            zf.extractall(temp_dir)

        # 3. Dispatch to mode-specific generator
        if light_mode:
            _generate_output_light_mode(append1_df, rincian_po_df, temp_dir)
        else:
            _generate_output_full_mode(append1_df, rincian_po_df, temp_dir)

        # 4. Re-zip → output
        print("  [Excel] Re-zipping output...")
        os.remove(output_path)  # Remove the copy, we'll create fresh
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zf.write(file_path, arcname)

    print(f"  [Excel] DONE → {output_path}")
    return output_path


def _generate_output_full_mode(append1_df: pd.DataFrame,
                                rincian_po_df: pd.DataFrame,
                                temp_dir: str) -> None:
    """FullMode Excel output: pivot cache records approach (original behavior).
    Mutates files inside temp_dir.
    """
    # 1. Generate & replace Cache1 (Append1) — STREAMING MODE for large data
    print("  [Excel][Full] Generating pivot cache 1 (Append1)...")
    if not append1_df.empty:
        shared_data1 = _build_shared_data(append1_df, CACHE1_FIELDS)
        # STREAMING: write directly to file (avoid building 500MB+ string in memory)
        records1_path = os.path.join(temp_dir, "xl", "pivotCache", "pivotCacheRecords1.xml")
        _generate_cache_records(append1_df, CACHE1_FIELDS, shared_data1, output_path=records1_path)
        def_xml1 = _generate_cache_definition(
            CACHE1_FIELDS, shared_data1, len(append1_df),
            "{8DF41EF9-DA36-4297-80B1-A53D88DC21E8}"
        )
        with open(os.path.join(temp_dir, "xl", "pivotCache", "pivotCacheDefinition1.xml"), "w", encoding="utf-8") as f:
            f.write(def_xml1)

    # 2. Generate & replace Cache2 (Rincian PO) — STREAMING MODE
    print("  [Excel][Full] Generating pivot cache 2 (Rincian PO)...")
    if not rincian_po_df.empty:
        shared_data2 = _build_shared_data(rincian_po_df, CACHE2_FIELDS)
        records2_path = os.path.join(temp_dir, "xl", "pivotCache", "pivotCacheRecords2.xml")
        _generate_cache_records(rincian_po_df, CACHE2_FIELDS, shared_data2, output_path=records2_path)
        def_xml2 = _generate_cache_definition(
            CACHE2_FIELDS, shared_data2, len(rincian_po_df),
            "{D76DDFB7-5659-4E65-A107-530BC38ABF47}"
        )
        with open(os.path.join(temp_dir, "xl", "pivotCache", "pivotCacheDefinition2.xml"), "w", encoding="utf-8") as f:
            f.write(def_xml2)

    # 3. Modify pivotTable XML (remove items, let Excel rebuild)
    print("  [Excel][Full] Modifying pivot tables...")
    for pt_file in ["pivotTable1.xml", "pivotTable2.xml"]:
        pt_path = os.path.join(temp_dir, "xl", "pivotTables", pt_file)
        if os.path.exists(pt_path):
            with open(pt_path, "r", encoding="utf-8") as f:
                xml = f.read()
            xml = _remove_items_from_pivot_fields(xml)
            xml = _remove_page_field_items(xml)
            with open(pt_path, "w", encoding="utf-8") as f:
                f.write(xml)

    # 4. Modify slicerCache XML (remove items)
    print("  [Excel][Full] Modifying slicer caches...")
    for sc_file in ["slicerCache1.xml", "slicerCache2.xml"]:
        sc_path = os.path.join(temp_dir, "xl", "slicerCaches", sc_file)
        if os.path.exists(sc_path):
            with open(sc_path, "r", encoding="utf-8") as f:
                xml = f.read()
            xml = _remove_slicer_items(xml)
            with open(sc_path, "w", encoding="utf-8") as f:
                f.write(xml)

    # 5. Remove connections + Power Query
    print("  [Excel][Full] Removing Power Query connections...")
    _remove_connections(temp_dir)
