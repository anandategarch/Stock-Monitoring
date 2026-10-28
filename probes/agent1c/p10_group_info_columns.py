"""P10 — append1._group_info_columns semantics (v3.7 ENGINE TURBO).

Parity claims vs the old per-group UDF, probed on nasty inputs:
 1. distinct values keep FIRST-APPEARANCE order, joined with ', '
 2. group whose info values are ALL invalid (None) -> None (not NaN string)
 3. Int64 Tanggal keys containing pd.NA still merge (NA group keeps info)
 4. dtype-normalization branch: key col that arrives float64-with-NaN from
    groupby must still match the object/Int64 base keys after astype
 5. two different pairs never cross-contaminate info
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT

sys.path.insert(0, PROJECT)
from src.pipeline.append1 import _group_info_columns  # noqa: E402


def main():
    print("=== 1+2+5: order, None semantics, pair isolation ===")
    info = pd.DataFrame({
        "Nama Barang": ["A", "A", "A", "B", "B", "A"],
        "NAMA RESTO": ["R", "R", "R", "R", "R", "R"],
        "Tanggal": pd.array([1, 1, 2, 1, 1, 1], dtype="Int64"),
        "Nomor": ["IT.9", "IT.1", None, None, None, "IT.9"],
    })
    res = _group_info_columns(info, ["Nama Barang", "NAMA RESTO", "Tanggal"],
                              ["Nomor"])
    print(res.to_string(index=False))
    a1 = res[(res["Nama Barang"] == "A") & (res["Tanggal"] == 1)]
    a2 = res[(res["Nama Barang"] == "A") & (res["Tanggal"] == 2)]
    b1 = res[(res["Nama Barang"] == "B") & (res["Tanggal"] == 1)]
    ok_order = a1["Nomor"].iloc[0] == "IT.9, IT.1"     # first appearance
    ok_none = b1["Nomor"].iloc[0] is None and a2["Nomor"].iloc[0] is None
    print(f"order preserved: {ok_order}; all-invalid -> None: {ok_none}")

    print("=== 3: NA Tanggal key keeps its info ===")
    info2 = pd.DataFrame({
        "Nama Barang": ["A", "A"],
        "NAMA RESTO": ["R", "R"],
        "Tanggal": pd.array([1, pd.NA], dtype="Int64"),
        "Nomor": ["IT.1", "IT.2"],
    })
    res2 = _group_info_columns(info2, ["Nama Barang", "NAMA RESTO", "Tanggal"],
                               ["Nomor"])
    print(res2.to_string(index=False))
    na_row = res2[res2["Tanggal"].isna()]
    ok_na = len(na_row) == 1 and na_row["Nomor"].iloc[0] == "IT.2"
    print(f"NA-key row keeps info: {ok_na}")

    print("=== 4: float64-NaN groupby key vs object base key ===")
    info3 = pd.DataFrame({
        "Nama Barang": pd.array(["A", "A"], dtype=object),
        "NAMA RESTO": pd.array(["R", "R"], dtype=object),
        "Tanggal": pd.array([np.nan, np.nan], dtype="float64"),
        "Nomor": ["IT.1", "IT.2"],
    })
    try:
        res3 = _group_info_columns(
            info3, ["Nama Barang", "NAMA RESTO", "Tanggal"], ["Nomor"])
        print(res3.to_string(index=False))
        ok4 = (len(res3) == 1 and res3["Nomor"].iloc[0] == "IT.1, IT.2")
    except Exception as e:
        print(f"  raised: {type(e).__name__}: {e}")
        ok4 = False
    print(f"float-NaN key merge ok: {ok4}")

    verdict = ok_order and ok_none and ok_na and ok4
    print("\nEXPECTED: order/None/NA-key/dtype-normalization all hold")
    print("VERDICT:", "NOT-BUG" if verdict else
          "BUG — _group_info_columns parity broken")


if __name__ == "__main__":
    main()
