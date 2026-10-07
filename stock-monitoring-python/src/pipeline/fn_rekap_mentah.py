"""
fn_rekap_mentah.py — Mirror persis fnRekapMentah di M code.
Membaca folder Rekap Mentah (SO + BARANG MASUK), unpivot kolom tanggal.

CRITICAL FIX: NAMA RESTO berasal dari FILE NAME (bukan sheet column).
Mirror M: fnCombineFolder → Name column → PromoteHeaders → firstColumn = file1's name
           → rename → "NAMA RESTO" → Text.BeforeDelimiter(_, ".")

v3.3.1 — FALLBACK "combined workbook":
Sumber SO user kini berupa SATU file gabungan (mis. "01.1 CEK STOCK V2.xlsb",
sheet '1  DEVIASI WEEKLY') berisi SEMUA resto dalam satu sheet dengan kolom
NAMA RESTO — bukan file per-resto dengan sheet "REKAP MENTAH". Format lama
tidak cocok (sheet beda nama + .xlsb tidak ter-glob) → SO tidak pernah
 terbaca → "Saldo SO kosong semua" di tab Deviasi GR/PCS.
Bila folder tidak punya file per-resto "REKAP MENTAH", reader otomatis:
  1. scan semua file Excel (termasuk .xlsb) di folder tsb (+ folder induk
     untuk mode "berjalan" — file gabungan kadang disimpan di RootPath)
  2. deteksi sheet ber-schema rekap-mentah (kolom NAMA RESTO + JENIS +
     NAMA BARANG + SATUAN + ≥3 kolom hari 1..31) pada ≤6 baris pertama
  3. baca sheet tsb, NAMA RESTO diambil dari KOLOM (bukan nama file)

OPTIMIZED: vectorized text operations.
"""
import os
import pandas as pd
from typing import Optional, List
from .helpers import (
    fn_combine_folder, promote_headers, safe_to_str, safe_to_numeric,
    _list_excel_files, _list_sheet_names, _xlsb_engine, _EXCEL_ENGINE,
)

# Kolom base schema rekap mentah (urutan output konsisten format lama)
_BASE_COLS = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS",
              "NAMA BARANG", "SATUAN"]


def _detect_rekap_header(peek: pd.DataFrame):
    """Deteksi baris header ber-schema rekap-mentah dalam peek (raw,
    header=None, ≤6 baris pertama). Format combined: kolom NAMA RESTO +
    JENIS + NAMA BARANG + SATUAN + ≥3 kolom hari (header 1..31).
    Return (header_row_idx, {posisi_kolom: nomor_hari}) atau None.

    Diverifikasi terhadap workbook gabungan user (16 sheet): hanya sheet
    '1  DEVIASI WEEKLY' yang lolos — sheet lain (SO BULAN INI, DEVIASI GR,
    Barang Masuk/Keluar, 29 Rekap, Follow UP, dll) tertolak karena tidak
    punya JENIS / NAMA RESTO persis / kolom hari.
    """
    if peek is None or peek.empty:
        return None
    for hr in range(min(6, len(peek))):
        headers = [str(h).strip() if h is not None else "" for h in peek.iloc[hr].tolist()]
        up = [h.upper() for h in headers]
        if "NAMA RESTO" not in up or "JENIS" not in up \
                or "NAMA BARANG" not in up or "SATUAN" not in up:
            continue
        day_pos = {}
        for i, h in enumerate(up):
            if h in ("", "NONE", "NAN"):
                continue
            try:
                d = int(float(h))
            except (TypeError, ValueError):
                continue
            if 1 <= d <= 31:
                day_pos[i] = d
        if len(day_pos) >= 3:
            return hr, day_pos
    return None


def _combined_to_long(df: pd.DataFrame, mode: str,
                      jenis_filter: Optional[List[str]]) -> Optional[pd.DataFrame]:
    """Ubah sheet combined (header sudah promote) → format long rekap
    mentah (schema output identik alur per-resto lama)."""
    if df is None or df.empty:
        return None
    headers = [str(c).strip() if c is not None else "" for c in df.columns]
    up = [h.upper() for h in headers]

    def _first(name: str) -> Optional[int]:
        return up.index(name) if name in up else None

    # kolom hari: cari ulang dari header aktual (posisi = posisi peek)
    days = {}
    for i, h in enumerate(up):
        if h in ("", "NONE", "NAN"):
            continue
        try:
            d = int(float(h))
        except (TypeError, ValueError):
            continue
        if 1 <= d <= 31:
            days[i] = d
    # mode "lalu" (mirror M): hanya hari 25..31, dinegasikan
    if mode != "berjalan":
        days = {i: d for i, d in days.items() if 25 <= d <= 31}
    if not days:
        return None

    # base columns — posisi (dari kolom, bukan nama file)
    sel = pd.DataFrame(index=df.index)
    for name in _BASE_COLS:
        pos = _first(name)
        if pos is not None:
            col = df.iloc[:, pos]
        else:
            col = pd.Series(None, index=df.index, dtype=object)
        # strip spasi tepi — SATUAN 'GR ' → 'GR' (57 nilai di data user punya
        # trailing space; tanpa strip, baris GR bocor ke tab Deviasi PCS)
        stripped = col.astype(str).str.strip()
        sel[name] = stripped.where(col.notna(), other=None)

    # kolom hari → numeric
    for pos, d in days.items():
        sel[str(d)] = safe_to_numeric(df.iloc[:, pos])

    # filter JENIS (case-insensitive — mirror jenis_filter alur lama)
    if jenis_filter is not None:
        jf = {str(j).strip().upper() for j in jenis_filter}
        jj = sel["JENIS"].fillna("").astype(str).str.strip().str.upper()
        sel = sel[jj.isin(jf)]
        if sel.empty:
            return None

    # unpivot hari → (Attribute, Value)
    day_names = [str(d) for d in sorted(set(days.values()))]
    melted = sel.melt(
        id_vars=[c for c in _BASE_COLS if c in sel.columns],
        value_vars=day_names,
        var_name="Attribute",
        value_name="Value"
    )
    melted["Attribute"] = safe_to_numeric(melted["Attribute"]).astype("Int64")
    if mode != "berjalan":
        melted["Attribute"] = (-melted["Attribute"]).astype("Int64")
    melted["Value"] = safe_to_numeric(melted["Value"])
    melted = melted.dropna(subset=["Value"]).reset_index(drop=True)

    out_cols = [c for c in _BASE_COLS if c in melted.columns] + ["Attribute", "Value"]
    return melted[out_cols]


def _read_combined_file(file_path: str, mode: str,
                        jenis_filter: Optional[List[str]]) -> Optional[pd.DataFrame]:
    """Cari sheet rekap-mentah (combined) dalam satu file; baca → long."""
    if file_path.lower().endswith(".xlsb") and _xlsb_engine() is None:
        print(f"  [fn_rekap_mentah] SKIP {os.path.basename(file_path)}: file .xlsb "
              "butuh package pyxlsb/python-calamine (pip install pyxlsb)")
        return None
    if file_path.lower().endswith(".xlsb"):
        engine = _xlsb_engine()          # calamine > pyxlsb
    else:
        engine = _EXCEL_ENGINE           # calamine bila ada, else default
    engine_kwargs = {"engine": engine} if engine else {}
    for sn in _list_sheet_names(file_path):
        try:
            peek = pd.read_excel(file_path, sheet_name=sn, header=None,
                                 nrows=8, dtype=object, **engine_kwargs)
        except Exception:
            continue
        det = _detect_rekap_header(peek)
        if det is None:
            continue
        hr, _day_pos = det
        try:
            df = pd.read_excel(file_path, sheet_name=sn, header=hr,
                               dtype=object, **engine_kwargs)
        except Exception as e:
            print(f"  [fn_rekap_mentah] Gagal baca sheet '{sn}' "
                  f"{os.path.basename(file_path)}: {e}")
            continue
        out = _combined_to_long(df, mode, jenis_filter)
        if out is not None and not out.empty:
            print(f"  [fn_rekap_mentah] Combined workbook: {os.path.basename(file_path)} "
                  f"» sheet '{sn}' (header baris {hr + 1}) → {len(out)} baris "
                  f"(NAMA RESTO dari kolom)")
            return out
    return None


def _read_combined_rekap(folder_path: str, mode: str,
                         jenis_filter: Optional[List[str]]) -> Optional[pd.DataFrame]:
    """Fallback v3.3.1: cari workbook gabungan ber-schema rekap mentah.
    Urutan: folder itu sendiri → (mode 'berjalan' saja) folder induk/RootPath.
    Folder induk tidak discan untuk mode 'lalu' agar data bulan berjalan
    tidak tercampur ke bulan lalu."""
    search_paths = [folder_path]
    if mode == "berjalan":
        parent = os.path.dirname(os.path.abspath(folder_path))
        if parent and os.path.isdir(parent) \
                and os.path.abspath(parent) != os.path.abspath(folder_path):
            search_paths.append(parent)
    for base in search_paths:
        for f in _list_excel_files(base):
            out = _read_combined_file(f, mode, jenis_filter)
            if out is not None:
                return out
    print(f"  [fn_rekap_mentah] WARNING: tidak ada file per-resto 'REKAP MENTAH' "
          f"dan tidak ada sheet gabungan rekap-mentah di: {folder_path}")
    return None


def fn_rekap_mentah(folder_path: str, mode: str, jenis_filter: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Mirror M: fnRekapMentah(folderPath, mode, optional jenisFilter).

    mode: "berjalan" (tanggal 1..31) atau "lalu" (tanggal 25..31, dinegasikan).
    jenis_filter: list JENIS yang di-keep. None = no filter.

    Output columns: NAMA RESTO, SOURCE DATA, JENIS, STATUS, NAMA BARANG, SATUAN, Attribute, Value
    """
    # === STEP 1: fnCombineFolder(folderPath, "REKAP MENTAH") dengan doPromote=null ===
    # raw=True: baca tanpa header, add_name_col=True: tambah kolom "Name" (file name)
    expand = fn_combine_folder(folder_path, "REKAP MENTAH", raw=True, add_name_col=True)
    if expand.empty:
        # v3.3.1 FALLBACK: sumber gabungan (.xlsb / sheet apa pun ber-schema
        # rekap mentah, NAMA RESTO dari kolom) — fix "Saldo SO kosong semua"
        combined = _read_combined_rekap(folder_path, mode, jenis_filter)
        if combined is not None:
            return combined
        return pd.DataFrame(columns=_BASE_COLS + ["Attribute", "Value"])

    # === STEP 2: prom = Table.PromoteHeaders(expand, [PromoteAllScalars = true]) ===
    # Row 0 (file1's header row) → column names
    # Name column → renamed to file1's name (e.g., "MLGPAR.xlsx")
    prom = promote_headers(expand)

    # === STEP 3: firstColumn = Table.ColumnNames(prom){0} ===
    # firstColumn = file1's name (e.g., "MLGPAR.xlsx")
    first_column = prom.columns[0]

    # === STEP 4: ren = Table.RenameColumns(prom, {{firstColumn, "NAMA RESTO"}}) ===
    ren = prom.rename(columns={first_column: "NAMA RESTO"})

    # === STEP 4b: Handle duplicate "NAMA RESTO" columns ===
    # After rename, there may be TWO "NAMA RESTO" columns:
    #   1. Former Name column (file names) at position 0 — this is the one we want
    #   2. Sheet's original "NAMA RESTO" column (from PromoteHeaders) at position 1
    # M's Table.SelectColumns keeps the FIRST occurrence.
    # In pandas, we select by POSITION (not name) to keep only the first.
    cols = ren.columns.tolist()
    keep_positions = []
    seen_nama_resto = False
    for i, c in enumerate(cols):
        if c == "NAMA RESTO":
            if not seen_nama_resto:
                seen_nama_resto = True
                keep_positions.append(i)
            # else: skip duplicate (position 1+)
        else:
            keep_positions.append(i)
    ren = ren.iloc[:, keep_positions]

    # === STEP 5: clean = NAMA RESTO → Text.BeforeDelimiter(_, ".") ===
    # NAMA RESTO column berisi file names (e.g., "MLGPAR.xlsx", "BDGUKU.xlsx")
    # Text.BeforeDelimiter(_, ".") → "MLGPAR", "BDGUKU"
    # Vectorized: .str.split(".").str[0]
    nama_resto_series = ren["NAMA RESTO"]
    if isinstance(nama_resto_series, pd.DataFrame):
        # Still a DataFrame if duplicate wasn't resolved — take first column
        nama_resto_series = nama_resto_series.iloc[:, 0]
    ren["NAMA RESTO"] = nama_resto_series.astype(str).str.split(".").str[0]

    # === STEP 6: base columns + days ===
    base = ["NAMA RESTO", "SOURCE DATA", "JENIS", "STATUS", "NAMA BARANG", "SATUAN"]
    if mode == "berjalan":
        days = [str(d) for d in range(1, 32)]
    else:  # "lalu"
        days = [str(d) for d in range(25, 32)]

    # === STEP 7: sel = Table.SelectColumns(clean, base & days) ===
    all_cols = base + days
    available = [c for c in all_cols if c in ren.columns]
    sel = ren[available].copy()

    # === STEP 8: fil = filter JENIS (if jenisFilter given) ===
    if jenis_filter is not None:
        sel_jenis = sel["JENIS"].astype(str)
        sel = sel[sel_jenis.isin([str(j) for j in jenis_filter])].copy()

    # === STEP 9: Type cast: base → text, days → number ===
    # Vectorized text conversion
    for col in base:
        if col in sel.columns:
            sel[col] = safe_to_str(sel[col])
    for col in days:
        if col in sel.columns:
            sel[col] = safe_to_numeric(sel[col])

    # === STEP 10: up = Table.Unpivot(typed, days, "Attribute", "Value") ===
    available_days = [d for d in days if d in sel.columns]
    if not available_days:
        return pd.DataFrame(columns=base + ["Attribute", "Value"])

    up = sel.melt(
        id_vars=[c for c in base if c in sel.columns],
        value_vars=available_days,
        var_name="Attribute",
        value_name="Value"
    )

    # === STEP 11: final type conversion ===
    # berjalan → Attribute as Int64; lalu → Attribute = -Number.From(Attribute)
    up["Attribute"] = safe_to_numeric(up["Attribute"])
    if mode == "berjalan":
        up["Attribute"] = up["Attribute"].astype("Int64")
    else:
        up["Attribute"] = (-up["Attribute"]).astype("Int64")

    # Value → numeric
    up["Value"] = safe_to_numeric(up["Value"])

    # Drop rows where Value is null (M's Table.Unpivot doesn't create rows for nulls)
    up = up.dropna(subset=["Value"]).reset_index(drop=True)

    return up
