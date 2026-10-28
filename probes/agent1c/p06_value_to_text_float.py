"""P06 — whole-float text conversion inconsistency (scalar fix vs vectorized
object path) — '0.0'/'123.0' leak where M Text.From produces '0'/'123'.

FIX BUG-21 made the SCALAR _value_to_text format whole floats as ints so the
downstream `!= "0"` filter works. The VECTORIZED _value_to_text_series only
implements that on the numeric-dtype fast path — the OBJECT-dtype path does a
plain astype(str) -> '0.0' / '123.0'. Object dtype is exactly what the
pipeline produces everywhere (all readers use dtype=object), and the
append1 LANGKAH-3 invalid-value filter compares against the string "0", so
float-zero document numbers LEAK into the Nomor/Nomor PO info as '0.0'.

Also checks _concat_valid_values distinctness: '5' vs '5.0' both survive as
"distinct" values (M would collapse them to one).
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.append1 import (  # noqa: E402
    _concat_valid_values, _value_to_text, _value_to_text_series,
    build_append1)


def main():
    print("=== unit: scalar vs vectorized (object dtype) ===")
    s_obj = pd.Series([0.0, 5.0, 12.5, None], dtype=object)
    scalar = [_value_to_text(v) for v in s_obj]
    vec = list(_value_to_text_series(s_obj))
    print(f"  scalar     = {scalar}")
    print(f"  vectorized = {vec}")
    m_parity = scalar == vec
    print(f"  parity: {'OK' if m_parity else 'MISMATCH'}")

    print("=== unit: append1 invalid-value filter on '0.0' ===")
    # append1 does: mask_valid = notna & != '' & != '0'
    vals = _value_to_text_series(s_obj)
    leak = list(vals[vals.notna() & (vals != "") & (vals != "0")])
    print(f"  values passing the 'not 0' filter: {leak}")
    leak_ok = "0.0" not in leak
    print(f"  '0.0' filtered as invalid: {'OK' if leak_ok else 'LEAK'}")

    print("=== unit: _concat_valid_values distinct '5' vs '5.0' ===")
    mixed = pd.Series([5, 5.0, "5", 12.5], dtype=object)
    joined = _concat_valid_values(mixed)
    print(f"  joined = {joined!r}")
    join_ok = joined == "5, 12.5"
    print(f"  collapse whole floats: {'OK' if join_ok else 'MISMATCH'}")

    print("=== E2E: numeric Nomor # RI cell -> popup Nomor string ===")
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("GULA (V.20)", "KG", "SO", "input so harian", {1: 100}),
    ])
    b_2205(root, [])
    b_4205(root, [])
    b_3224(root, [
        ("2026-10-05", 20, "GULA (V.20)", "GUDANG X (MLGPAR)",
         123.0, "PO.2026.09.002", "2026-10-05 08:00:00"),   # numeric RI no.
    ])
    b_4217(root, [("GULA (V.20)", "10.FOOD [RM] - COM V.2", "KG",
                   {"RESTO MALANG (MLGPAR)": 80})])
    b_dbs(root, [("GULA (V.20)", "COM DEVIASI - RESTO", "AKTIF")])
    final = build_append1(Config(make_config(root)))
    row = final[(final["JENIS"] == "4.IN") & (final["Tanggal"] == 5)]
    nomor = row["Nomor"].iloc[0] if len(row) else None
    print(f"  Nomor in long output = {nomor!r}")
    print("  EXPECTED: '123' (M Text.From); ACTUAL above")
    e2e_ok = nomor == "123"

    verdict = m_parity and leak_ok and join_ok and e2e_ok
    print(f"\n[unit parity OK={m_parity}] [filter-leak OK={leak_ok}] "
          f"[join OK={join_ok}] [E2E xlsx OK={e2e_ok}]")
    print("VERDICT:", "NOT-BUG" if verdict else
          "BUG (P3) — _value_to_text_series OBJECT path drops the BUG-21 "
          "whole-float formatting that the scalar _value_to_text has: "
          "float 0.0 -> '0.0' escapes append1's `!= '0'` invalid filter and "
          "'5.0'/'123.0' strings survive as document info (scalar M-parity "
          "path gives '0'/'5'). E2E via .xlsx is clean (xlsx normalizes "
          "123.0 -> 123); reachable via pyxlsb float cells / programmatic "
          "frames. Display/info-level, not a numbers bug")


if __name__ == "__main__":
    main()
