"""
append1.py — Mirror SANGAT PERSIS query Append1 di M code.
Pipeline utama yang menggabungkan semua sumber data, melakukan pivot, running stock,
deviasi, merge kategori, dan unpivot ke format long.

Output: DataFrame long format dengan kolom:
  Nama Barang, NAMA RESTO, Tanggal, JENIS, NILAI, Nomor, Nomor PO,
  #Tgl/Jam Pembuatan IT, KATEGORI, SOURCE KIRIMAN
"""
import pandas as pd
import numpy as np
from typing import List
from .queries import (
    query_4217, query_full_rekap_mentah_so, query_out, query_barang_keluar, query_in,
    query_27_konversi_satuan, query_dbs_kategori
)
from .fn_running_stock import fn_running_stock, fn_running_stock_grouped


def _value_to_text(val) -> str:
    """Mirror M: Text.From(_) — convert value to text.
    FIX BUG-21: float 0.0 → "0" (bukan "0.0") agar filter != "0" bekerja.
    Untuk datetime: format "DD/MM/YYYY HH:MM:SS".
    """
    if val is None:
        return None
    # Check for pandas/numpy NaN
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    # datetime → "DD/MM/YYYY HH:MM:SS"
    if isinstance(val, pd.Timestamp):
        return val.strftime("%d/%m/%Y %H:%M:%S")
    if hasattr(val, "strftime"):  # datetime object
        return val.strftime("%d/%m/%Y %H:%M:%S")
    # FIX: float yang whole number → format sebagai integer (mirror M Text.From)
    # M: Text.From(0.0) = "0", Text.From(1.0) = "1"
    if isinstance(val, (int, np.integer)):
        return str(val)
    if isinstance(val, (float, np.floating)):
        if val == int(val):
            return str(int(val))
        return str(val)
    return str(val).strip()


def _value_to_text_series(series: pd.Series) -> pd.Series:
    """Vectorized version of _value_to_text untuk pandas Series.
    OPTIMIZED: dtype-specific fast paths, no .apply().
    """
    # Fast path: datetime dtype
    if pd.api.types.is_datetime64_any_dtype(series):
        result = series.dt.strftime("%d/%m/%Y %H:%M:%S")
        return result.where(series.notna(), other=None)
    # Fast path: numeric dtype
    if pd.api.types.is_numeric_dtype(series):
        # Whole numbers → int string, others → float string
        is_nan = series.isna()
        # Use modulo to check integer-valued floats (avoid astype crash)
        is_int = ~is_nan & (series % 1 == 0)
        result = pd.Series(None, index=series.index, dtype=object)
        int_vals = series[is_int].astype('Int64').astype(str)
        result[is_int] = int_vals
        float_vals = series[~is_nan & ~is_int].astype(str)
        result[~is_nan & ~is_int] = float_vals
        return result
    # Object/mixed dtype: convert to str, preserve None
    is_null = series.isna()
    result = series.astype(str).where(~is_null, other=None)
    # Strip whitespace
    result = result.str.strip() if hasattr(result, 'str') else result
    return result


def _concat_valid_values(series: pd.Series) -> str:
    """
    Mirror M: untuk setiap InfoColumn di InformationGrouped.
    - Transform: null → null, else Text.Trim(Text.From(_))
    - Filter: not null, not "", not "0"
    - Distinct (preserve order)
    - Text.Combine dengan ", "

    OPTIMIZED: pre-convert series, avoid .apply() for common types.
    """
    # Fast path: if series is datetime dtype, use vectorized strftime
    if pd.api.types.is_datetime64_any_dtype(series):
        values = series.dt.strftime("%d/%m/%Y %H:%M:%S")
        values = values.where(series.notna(), other=None)
    elif pd.api.types.is_numeric_dtype(series):
        # Convert numeric to text (whole numbers as int, others as float)
        def _num_to_text(v):
            if pd.isna(v):
                return None
            if v == int(v):
                return str(int(v))
            return str(v)
        values = series.apply(_num_to_text)
    else:
        # Mixed/object dtype — use _value_to_text
        values = series.apply(_value_to_text)

    # Filter valid: not null, not "", not "0"
    mask = values.notna() & (values != "") & (values != "0")
    valid = values[mask]
    # Distinct (preserve order of first appearance)
    distinct = list(dict.fromkeys(valid.tolist()))
    # Join
    return ", ".join(distinct) if distinct else None


def build_append1(config) -> pd.DataFrame:
    """
    Mirror M: shared Append1.
    Pipeline lengkap dari source data sampai output long format.

    LightMode (config.LightMode=True):
    - Skip InfoColumns (Nomor, Nomor PO, #Tgl/Jam) — hemat kolom & grouping time
    - Pre-filter KATEGORI=DEVIASI di awal — hemat ~60% data
    """
    print(f"  [Append1] Mode: {'LIGHT' if config.LightMode else 'FULL'}")
    print("  [Append1] Loading master data...")
    # Pre-load master queries (dipakai multiple times)
    konversi = query_27_konversi_satuan(config)
    dbs_kategori = query_dbs_kategori(config)
    print(f"    Konversi Satuan: {len(konversi)} rows")
    print(f"    DBS Kategori: {len(dbs_kategori)} rows")

    # =========================================================================
    # 1. SOURCE — Table.Combine({4217, Full Rekap Mentah SO, OUT, BARANG KELUAR, IN})
    # =========================================================================
    print("  [Append1] Loading transaction data...")
    q4217 = query_4217(config)
    print(f"    4217 (Saldo Awal): {len(q4217)} rows")

    full_rekap_so = query_full_rekap_mentah_so(config)
    print(f"    Full Rekap Mentah SO: {len(full_rekap_so)} rows")

    out_df = query_out(config)
    print(f"    OUT (22.05 sales): {len(out_df)} rows")

    keluar_df = query_barang_keluar(config)
    print(f"    BARANG KELUAR (42.15 Kirim): {len(keluar_df)} rows")

    in_df = query_in(config, konversi)
    print(f"    IN: {len(in_df)} rows")

    # Combine all 5 sources
    parts = []
    for df in [q4217, full_rekap_so, out_df, keluar_df, in_df]:
        if not df.empty:
            parts.append(df)

    if not parts:
        print("  [Append1] WARNING: No source data found!")
        return pd.DataFrame(columns=[
            "Nama Barang", "NAMA RESTO", "Tanggal", "JENIS", "NILAI",
            "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT", "KATEGORI", "SOURCE KIRIMAN"
        ])

    # Table.Buffer equivalent — just use the DataFrame (already in memory)
    source = pd.concat(parts, ignore_index=True, sort=False)
    print(f"    Combined source: {len(source)} rows")

    # =========================================================================
    # 1.5 LightMode: Pre-filter KATEGORI=DEVIASI
    # =========================================================================
    if config.LightMode and len(dbs_kategori) > 0 and "Nama Barang" in source.columns:
        # Merge kategori dulu untuk filter
        kat_filter = dbs_kategori[["NAMA BARANG", "KATEGORI"]].copy()
        kat_filter = kat_filter.rename(columns={"NAMA BARANG": "Nama Barang"})
        kat_filter = kat_filter[kat_filter["KATEGORI"] == "DEVIASI"]
        # Get set of barang with KATEGORI=DEVIASI
        deviasi_barang = set(kat_filter["Nama Barang"].astype(str).unique())
        # Filter source
        before = len(source)
        source["Nama Barang"] = source["Nama Barang"].astype(str)
        source = source[source["Nama Barang"].isin(deviasi_barang)].reset_index(drop=True)
        print(f"    LightMode pre-filter KATEGORI=DEVIASI: {before} → {len(source)} rows")

    # =========================================================================
    # 2. KONFIGURASI
    # =========================================================================
    InfoColumns = ["Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT"]
    KeyColumns = ["Nama Barang", "NAMA RESTO", "Tanggal"]
    # FIX: jangan skip InfoColumns (Nomor/Nomor PO perlu terisi)
    # LightMode tetap proses InfoColumns untuk popup details
    AvailableInfoColumns = [c for c in InfoColumns if c in source.columns]


    # =========================================================================
    # 3. INFORMATION — group by KeyColumns, concat valid values for InfoColumns
    # =========================================================================
    print("  [Append1] Building information (grouped)...")
    info_cols = KeyColumns + AvailableInfoColumns
    info_available = [c for c in info_cols if c in source.columns]
    information = source[info_available].copy()

    if AvailableInfoColumns and len(information) > 0:
        # OPTIMIZED: pre-convert InfoColumns to text + filter invalid, THEN groupby + join
        # Old approach: groupby.agg(_concat_valid_values) — slow because .apply() per group
        # New approach: vectorized pre-processing + groupby.agg(', '.join)
        info_prep = information.copy()

        # Pre-process each InfoColumn: convert to text, replace invalid values with None
        for col in AvailableInfoColumns:
            if col in info_prep.columns:
                info_prep[col] = _value_to_text_series(info_prep[col])
                # Set invalid values (None, "", "0", "0.0") to None
                mask_valid = info_prep[col].notna() & (info_prep[col] != "") & (info_prep[col] != "0")
                info_prep[col] = info_prep[col].where(mask_valid, other=None)

        # Group by KeyColumns, aggregate each InfoColumn:
        # - drop None values
        # - distinct (preserve order)
        # - join with ", "
        def _smart_join(series):
            """Fast join: drop None, dedupe preserving order, join with ', '.
            OPTIMIZED: use pd.unique (C-level) instead of Python set+loop."""
            vals = series.dropna()
            if vals.empty:
                return None
            # pd.unique is C-level, preserves order of first appearance
            distinct = pd.unique(vals)
            return ", ".join(str(v) for v in distinct)

        agg_dict = {col: _smart_join for col in AvailableInfoColumns if col in info_prep.columns}
        information_grouped = info_prep.groupby(KeyColumns, as_index=False, dropna=False).agg(agg_dict)
    else:
        information_grouped = information[KeyColumns].drop_duplicates().reset_index(drop=True) if KeyColumns else information.copy()

    # =========================================================================
    # 4. PERHITUNGAN — pivot, replace null→0, group+fnRunningStock, deviasi, selisih, rename
    # =========================================================================
    print("  [Append1] Pivot + running stock + calculations...")
    calc_columns = KeyColumns + ["JENIS", "Value"]
    calc_available = [c for c in calc_columns if c in source.columns]
    calculation_source = source[calc_available].copy()

    # pivoted = Table.Pivot(CalculationSource, distinct JENIS, "JENIS", "Value", List.Sum)
    if len(calculation_source) > 0 and "JENIS" in calculation_source.columns:
        # Ensure Value is numeric
        calculation_source["Value"] = pd.to_numeric(calculation_source["Value"], errors="coerce").fillna(0)

        # Pivot: group by KeyColumns, columns = JENIS, values = sum(Value)
        pivoted = calculation_source.pivot_table(
            index=KeyColumns,
            columns="JENIS",
            values="Value",
            aggfunc="sum",
            dropna=False
        ).reset_index()
        # Flatten column index (pivot_table creates MultiIndex column when using columns param)
        pivoted.columns.name = None
    else:
        pivoted = pd.DataFrame(columns=KeyColumns)

    # ReplaceColumns = {"SALDO AWAL", "SO", "BARANG MASUK", "OUT", "IN", "BARANG KELUAR"}
    # AvailableReplaceColumns = intersection with pivoted columns
    # FIX: include BARANG KELUAR (was missing after OUT/BK split)
    replace_columns = ["SALDO AWAL", "SO", "BARANG MASUK", "OUT", "IN", "BARANG KELUAR"]
    available_replace = [c for c in replace_columns if c in pivoted.columns]

    # replaced = Table.ReplaceValue(pivoted, null, 0, ..., AvailableReplaceColumns)
    for col in available_replace:
        pivoted[col] = pivoted[col].fillna(0)

    # grouped = Table.Group(replaced, {Nama Barang, NAMA RESTO}, fnRunningStock)
    # OPTIMIZED: pakai fn_running_stock_grouped (pre-sort + groupby C-level)
    group_keys = ["Nama Barang", "NAMA RESTO"]
    available_group_keys = [c for c in group_keys if c in pivoted.columns]

    if len(pivoted) > 0 and len(available_group_keys) == 2:
        # Use optimized grouped version (pre-sort once, iterate at C-level)
        combined = fn_running_stock_grouped(pivoted, available_group_keys)
    else:
        combined = pivoted.copy()
        if "SALDO AKHIR" not in combined.columns:
            combined["SALDO AKHIR"] = 0.0

    # typed = SALDO AKHIR → number
    if "SALDO AKHIR" in combined.columns:
        combined["SALDO AKHIR"] = pd.to_numeric(combined["SALDO AKHIR"], errors="coerce").fillna(0)

    # deviasi = SO - SALDO AKHIR (try [SO] otherwise 0)
    so_vals = combined["SO"] if "SO" in combined.columns else pd.Series(0, index=combined.index)
    saldo_akhir_vals = combined["SALDO AKHIR"] if "SALDO AKHIR" in combined.columns else pd.Series(0, index=combined.index)
    combined["DEVIASI"] = so_vals.fillna(0) - saldo_akhir_vals.fillna(0)

    # noNull = filter Nama Barang not null
    if "Nama Barang" in combined.columns:
        combined = combined[combined["Nama Barang"].notna()].reset_index(drop=True)

    # selisih = BARANG MASUK - IN (try [BARANG MASUK] otherwise 0 - try [IN] otherwise 0)
    bm_vals = combined["BARANG MASUK"] if "BARANG MASUK" in combined.columns else pd.Series(0, index=combined.index)
    in_vals = combined["IN"] if "IN" in combined.columns else pd.Series(0, index=combined.index)
    combined["Selisih IN"] = bm_vals.fillna(0) - in_vals.fillna(0)

    # renamed — beri prefix nomor (NEW numbering scheme after OUT/BK split)
    #   7.Selisih IN (was 6.Selisih IN)
    #   8.BARANG KELUAR (NEW — was not in rename_map before)
    #   9.OUT (was 7.OUT)
    rename_map = {
        "SALDO AKHIR": "2.SALDO AKHIR",
        "SO": "1.SO",
        "DEVIASI": "3.DEVIASI",
        "IN": "4.IN",
        "BARANG MASUK": "5.BARANG MASUK",
        "Selisih IN": "7.Selisih IN",
        "BARANG KELUAR": "8.BARANG KELUAR",
        "OUT": "9.OUT",
    }
    # Only rename columns that exist
    valid_rename = {old: new for old, new in rename_map.items() if old in combined.columns}
    renamed = combined.rename(columns=valid_rename)

    # =========================================================================
    # 5. MERGE INFORMATION + KATEGORI
    # =========================================================================
    print("  [Append1] Merging information + kategori...")
    # MergedInformation = LeftOuter join renamed × InformationGrouped on KeyColumns
    if AvailableInfoColumns and len(information_grouped) > 0:
        # Ensure KeyColumns exist in both
        merge_keys = [c for c in KeyColumns if c in renamed.columns and c in information_grouped.columns]
        if merge_keys:
            # Drop InfoColumns from renamed that will come from InformationGrouped (to avoid suffix)
            info_cols_to_drop = [c for c in AvailableInfoColumns if c in renamed.columns]
            renamed_clean = renamed.drop(columns=info_cols_to_drop, errors="ignore")
            expanded_information = renamed_clean.merge(
                information_grouped, on=merge_keys, how="left"
            )
        else:
            expanded_information = renamed.copy()
            for col in AvailableInfoColumns:
                expanded_information[col] = None
    else:
        expanded_information = renamed.copy()

    # mergedKategori = LeftOuter join × DBS_Kategori on Nama Barang = NAMA BARANG
    # FIX: also bring AKTIF/NON column (was missing → AKTIF/NON always empty in UI)
    if len(dbs_kategori) > 0 and "Nama Barang" in expanded_information.columns:
        # Prepare DBS_Kategori for merge — include AKTIF/NON if present
        kat_cols = ["NAMA BARANG", "KATEGORI", "SOURCE KIRIMAN"]
        if "AKTIF/NON" in dbs_kategori.columns:
            kat_cols.append("AKTIF/NON")
        kat = dbs_kategori[kat_cols].copy()
        kat = kat.rename(columns={"NAMA BARANG": "Nama Barang"})
        # Ensure Nama Barang is string for merge
        expanded_information["Nama Barang"] = expanded_information["Nama Barang"].astype(str)
        kat["Nama Barang"] = kat["Nama Barang"].astype(str)
        expanded_kategori = expanded_information.merge(kat, on="Nama Barang", how="left")
    else:
        expanded_kategori = expanded_information.copy()
        expanded_kategori["KATEGORI"] = None
        expanded_kategori["SOURCE KIRIMAN"] = None
        expanded_kategori["AKTIF/NON"] = None

    # =========================================================================
    # 6. UNPIVOT — 8 metric columns + SALDO AWAL → (JENIS, NILAI)
    # =========================================================================
    print("  [Append1] Unpivoting metrics...")
    # FIX: include 8.BARANG KELUAR (was missing → all BK data lost)
    # FIX: use new numbering 7.Selisih IN + 9.OUT (matches pivot_view METRICS)
    unpivot_columns = [
        "2.SALDO AKHIR", "1.SO", "3.DEVIASI", "4.IN",
        "5.BARANG MASUK", "7.Selisih IN", "8.BARANG KELUAR", "9.OUT", "SALDO AWAL"
    ]
    available_unpivot = [c for c in unpivot_columns if c in expanded_kategori.columns]

    if not available_unpivot:
        print("  [Append1] WARNING: No metric columns found for unpivot!")
        return pd.DataFrame(columns=[
            "Nama Barang", "NAMA RESTO", "Tanggal", "JENIS", "NILAI",
            "Nomor", "Nomor PO", "#Tgl/Jam Pembuatan IT", "KATEGORI", "SOURCE KIRIMAN"
        ])

    # id_vars = all columns except the unpivot columns
    id_vars = [c for c in expanded_kategori.columns if c not in available_unpivot]
    unpivoted = expanded_kategori.melt(
        id_vars=id_vars,
        value_vars=available_unpivot,
        var_name="JENIS",
        value_name="NILAI"
    )

    # Drop rows where NILAI is null (M's Table.Unpivot doesn't create rows for nulls)
    # After ReplaceValue null→0, metrics are 0 not null. But SALDO AWAL might have nulls.
    unpivoted = unpivoted.dropna(subset=["NILAI"]).reset_index(drop=True)

    # =========================================================================
    # 7. RESTORE URUTAN KOLOM FINAL
    # =========================================================================
    final_columns = KeyColumns + ["JENIS", "NILAI"] + AvailableInfoColumns + [
        "KATEGORI", "SOURCE KIRIMAN", "SATUAN", "AKTIF/NON"]
    available_final = [c for c in final_columns if c in unpivoted.columns]
    final = unpivoted[available_final].copy()

    # Type: Tanggal → Int64, NILAI → numeric
    if "Tanggal" in final.columns:
        final["Tanggal"] = pd.to_numeric(final["Tanggal"], errors="coerce").astype("Int64")
    if "NILAI" in final.columns:
        final["NILAI"] = pd.to_numeric(final["NILAI"], errors="coerce")

    # =========================================================================
    # 8. LOOKUP SATUAN (untuk DEVIASI GR/PCS split)
    # =========================================================================
    # SATUAN hanya ada di Full Rekap Mentah SO (dari fn_rekap_mentah).
    # Di pivot+unpivot, SATUAN hilang. Lookup dari full_rekap_so berdasarkan (Nama Barang, NAMA RESTO).
    if full_rekap_so is not None and "SATUAN" in full_rekap_so.columns:
        # Build SATUAN mapping: (Nama Barang, NAMA RESTO) → SATUAN (first non-null)
        satuan_map = (
            full_rekap_so[["Nama Barang", "NAMA RESTO", "SATUAN"]]
            .dropna(subset=["SATUAN"])
            .drop_duplicates(subset=["Nama Barang", "NAMA RESTO"], keep="first")
        )
        if not satuan_map.empty:
            # Merge SATUAN to final (creates SATUAN column if not exists, fills if exists)
            if "SATUAN" in final.columns:
                final = final.merge(
                    satuan_map.rename(columns={"SATUAN": "_SATUAN_LOOKUP"}),
                    on=["Nama Barang", "NAMA RESTO"], how="left"
                )
                final["SATUAN"] = final["SATUAN"].fillna(final["_SATUAN_LOOKUP"])
                final = final.drop(columns=["_SATUAN_LOOKUP"])
            else:
                final = final.merge(satuan_map, on=["Nama Barang", "NAMA RESTO"], how="left")

    print(f"  [Append1] DONE: {len(final)} rows")
    return final
