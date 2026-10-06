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
                              output_path: str = None, chunk_size: int = 50000) -> str:
    """Generate pivotCacheRecords XML from DataFrame.
    STREAMING MODE: writes directly to file if output_path given (saves ~50% memory for large data).
    CHUNKED: processes in chunks to avoid building giant string list.

    Args:
        df: DataFrame with source data
        fields: field configuration list
        shared_data: pre-built shared items data
        output_path: if given, write directly to file (streaming). If None, return string.
        chunk_size: number of records per chunk (for streaming progress)
    """
    # === Pre-extract columns as Python lists (faster than pandas indexing) ===
    col_data = {}
    for i, field in enumerate(fields):
        name = field["name"]
        if name in df.columns:
            col_data[i] = df[name].tolist()
        else:
            col_data[i] = [None] * len(df)

    # Pre-extract lookups for shared fields (avoid dict lookup overhead in loop)
    field_lookup = {}
    for i, field in enumerate(fields):
        ftype = field["type"]
        if ftype in ("shared_text", "shared_int", "shared_date", "shared_datetime"):
            field_lookup[i] = shared_data[i]["lookup"]
        else:
            field_lookup[i] = None

    n = len(df)

    # === Helper: process a batch of records → list of XML strings ===
    def _process_batch(start: int, end: int) -> list:
        """Process records [start, end) and return list of XML record strings."""
        batch = []
        # Local variable binding for speed (avoid global lookup in loop)
        _escape = _xml_escape
        _val_str = _val_to_str
        _val_num = _val_to_num
        _val_date = _val_to_date_str

        for row_idx in range(start, end):
            parts = ["<r>"]
            for i, field in enumerate(fields):
                ftype = field["type"]
                val = col_data[i][row_idx]

                if ftype == "shared_text":
                    key = _val_str(val)
                    lookup = field_lookup[i]
                    idx = lookup.get(key) if key is not None else None
                    parts.append(f'<x v="{idx}"/>' if idx is not None else '<m/>')

                elif ftype == "shared_int":
                    try:
                        key = int(val) if val is not None and not (isinstance(val, float) and pd.isna(val)) else None
                    except (TypeError, ValueError):
                        key = None
                    lookup = field_lookup[i]
                    idx = lookup.get(key) if key is not None else None
                    parts.append(f'<x v="{idx}"/>' if idx is not None else '<m/>')

                elif ftype in ("shared_date", "shared_datetime"):
                    key = _val_date(val)
                    lookup = field_lookup[i]
                    idx = lookup.get(key) if key is not None else None
                    parts.append(f'<x v="{idx}"/>' if idx is not None else '<m/>')

                elif ftype == "inline_num":
                    num = _val_num(val)
                    if num is not None:
                        # Format: integer if whole, else float
                        if num == int(num):
                            parts.append(f'<n v="{int(num)}"/>')
                        else:
                            parts.append(f'<n v="{num}"/>')
                    else:
                        parts.append('<m/>')

                elif ftype == "inline_str":
                    s = _val_str(val)
                    parts.append(f'<s v="{_escape(s)}"/>' if s is not None else '<m/>')

            parts.append("</r>")
            batch.append("".join(parts))
        return batch

    # === STREAMING MODE: write directly to file ===
    if output_path is not None:
        with open(output_path, "w", encoding="utf-8", buffering=1 << 20) as f:  # 1MB buffer
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
            f.write('<pivotCacheRecords xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                    f'count="{n}">')

            # Process in chunks for progress reporting
            for start in range(0, n, chunk_size):
                end = min(start + chunk_size, n)
                batch = _process_batch(start, end)
                # Write all records in chunk at once (fewer I/O calls)
                f.write("".join(batch))
                # Progress for very large datasets
                if n >= 100000 and (start // chunk_size) % 10 == 0:
                    print(f"    ... records {end}/{n} ({100*end//n}%)", flush=True)

            f.write('</pivotCacheRecords>')
        return None  # Written to file

    # === IN-MEMORY MODE: return string (for small data or backward compat) ===
    else:
        parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n']
        parts.append('<pivotCacheRecords xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                     'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                     f'count="{n}">')
        # Process all at once (small data)
        all_records = _process_batch(0, n)
        parts.extend(all_records)
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
# PIVOT TABLE & SLICER MODIFICATION
# =============================================================================

def _remove_items_from_pivot_fields(xml: str) -> str:
    """Remove <items> from each <pivotField> in pivotTable XML.
    Excel will rebuild items on open.
    """
    # Replace <pivotField ...><items>...</items></pivotField> → <pivotField .../>
    # Or <pivotField ...><items>...</items> → <pivotField ...>
    # Strategy: remove all <items count="N">...</items> blocks inside pivotField

    # Find each pivotField element and remove its <items> child
    def replace_pivot_field(m):
        field_xml = m.group(0)
        # Remove <items ...>...</items>
        field_xml = re.sub(r'<items[^>]*>.*?</items>', '', field_xml, flags=re.DOTALL)
        # If pivotField is now empty (self-closing not needed), keep as is
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
                     template_path: str, output_path: str) -> str:
    """
    Generate output Excel "sama persis" dengan template.

    Args:
        append1_df: DataFrame dari build_append1() (long format, 10 columns)
        rincian_po_df: DataFrame dari build_rincian_po() (13 columns)
        template_path: Path ke template xlsx
        output_path: Path output xlsx

    Returns:
        Path ke output file.
    """
    print(f"  [Excel] Template: {template_path}")
    print(f"  [Excel] Output: {output_path}")
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

        # 3. Generate & replace Cache1 (Append1) — STREAMING MODE for large data
        print("  [Excel] Generating pivot cache 1 (Append1)...")
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

        # 4. Generate & replace Cache2 (Rincian PO) — STREAMING MODE
        print("  [Excel] Generating pivot cache 2 (Rincian PO)...")
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

        # 5. Modify pivotTable XML (remove items, let Excel rebuild)
        print("  [Excel] Modifying pivot tables...")
        for pt_file in ["pivotTable1.xml", "pivotTable2.xml"]:
            pt_path = os.path.join(temp_dir, "xl", "pivotTables", pt_file)
            if os.path.exists(pt_path):
                with open(pt_path, "r", encoding="utf-8") as f:
                    xml = f.read()
                xml = _remove_items_from_pivot_fields(xml)
                xml = _remove_page_field_items(xml)
                with open(pt_path, "w", encoding="utf-8") as f:
                    f.write(xml)

        # 6. Modify slicerCache XML (remove items)
        print("  [Excel] Modifying slicer caches...")
        for sc_file in ["slicerCache1.xml", "slicerCache2.xml"]:
            sc_path = os.path.join(temp_dir, "xl", "slicerCaches", sc_file)
            if os.path.exists(sc_path):
                with open(sc_path, "r", encoding="utf-8") as f:
                    xml = f.read()
                xml = _remove_slicer_items(xml)
                with open(sc_path, "w", encoding="utf-8") as f:
                    f.write(xml)

        # 7. Remove connections + Power Query
        print("  [Excel] Removing Power Query connections...")
        _remove_connections(temp_dir)

        # 8. Re-zip → output
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
