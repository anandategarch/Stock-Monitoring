"""
fn_konversi_satuan.py — Mirror persis fnKonversiSatuan di M code.
Master konversi satuan (Sheet1) → dipakai fnPI untuk konversi ke unit terkecil.
"""
import pandas as pd
from .helpers import fn_combine_folder, safe_to_str


def fn_konversi_satuan(folder_path: str) -> pd.DataFrame:
    """
    Mirror M: fnKonversiSatuan(folderPath).

    Output columns: Nama Barang, Satuan, Rasio
    - 4 sub-tabel (Satuan #2/3/4/5) di-combine.
    """
    # src = fnCombineFolder(folderPath, "Sheet1", true) — doPromote=true, no skip → header=0
    src = fn_combine_folder(folder_path, "Sheet1", header_row=0)
    if src.empty:
        return pd.DataFrame(columns=["Nama Barang", "Satuan", "Rasio"])

    # typed: all to text
    text_cols = ["Nama Barang",
                 "Satuan #2", "Rasio Satuan #2",
                 "Satuan #3", "Rasio Satuan #3",
                 "Satuan #4", "Rasio Satuan #4",
                 "Satuan #5", "Rasio Satuan #5"]
    for col in text_cols:
        if col in src.columns:
            src[col] = safe_to_str(src[col])

    # extract: Rasio Satuan#2/3/4/5 → Text.BeforeDelimiter(_, ".") → ambil integer part
    for col in ["Rasio Satuan #2", "Rasio Satuan #3", "Rasio Satuan #4", "Rasio Satuan #5"]:
        if col in src.columns:
            src[col] = src[col].apply(
                lambda x: None if x is None or (isinstance(x, float) and pd.isna(x))
                else str(x).split(".")[0]
            )

    # toInt: Rasio → Int64 (numeric)
    for col in ["Rasio Satuan #2", "Rasio Satuan #3", "Rasio Satuan #4", "Rasio Satuan #5"]:
        if col in src.columns:
            src[col] = pd.to_numeric(src[col], errors="coerce")

    # 4 sub-tabel
    subs = []
    for num in [2, 3, 4, 5]:
        satuan_col = f"Satuan #{num}"
        rasio_col = f"Rasio Satuan #{num}"
        needed = ["Nama Barang", satuan_col, rasio_col]
        available = [c for c in needed if c in src.columns]
        if len(available) < 3:
            continue
        s = src[available].copy()
        s = s.rename(columns={satuan_col: "Satuan", rasio_col: "Rasio"})
        subs.append(s)

    if not subs:
        return pd.DataFrame(columns=["Nama Barang", "Satuan", "Rasio"])

    # combined = Table.Combine({s2, s3, s4, s5})
    combined = pd.concat(subs, ignore_index=True)

    # cleaned = Table.SelectRows(combined, each [Satuan] <> null and [Satuan] <> "")
    mask = (
        combined["Satuan"].notna() &
        (combined["Satuan"].astype(str).str.strip() != "") &
        (combined["Satuan"].astype(str).str.strip() != "nan")
    )
    cleaned = combined[mask].reset_index(drop=True)

    return cleaned
