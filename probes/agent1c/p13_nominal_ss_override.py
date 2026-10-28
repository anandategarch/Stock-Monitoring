"""P13 — nominal_common.hitung_nominal_pairs saldo-sistem override (v3.11.8).

Checks the normalized-key override (Qty Deviasi = SO_H − saldo sistem 42.17):
 1. whitespace/dotted drift between the pair in `data` ('GULA (V.20)',
    resto 'B.1001.MLGPAR') and the map key ('GULA (V.20) ', 'MLGPAR')
    must STILL override (norm: upper+collapse spaces; resto after last dot)
 2. pair absent from the map keeps raw 3.DEVIASI
 3. pair in map without any 1.SO row at H -> 0 − saldo sistem
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT

sys.path.insert(0, PROJECT)
from src.ui.nominal_common import hitung_nominal_pairs  # noqa: E402


def row(b, r, t, j, v, sat="KG"):
    return {"Nama Barang": b, "NAMA RESTO": r, "Tanggal": t, "JENIS": j,
            "NILAI": v, "SATUAN": sat, "KATEGORI": "COM DEVIASI - RESTO"}


def main():
    data = pd.DataFrame([
        # pair A — drift vs map key
        row("GULA (V.20)", "B.1001.MLGPAR", 10, "1.SO", 50),
        row("GULA (V.20)", "B.1001.MLGPAR", 10, "3.DEVIASI", 5),
        # pair B — not in map
        row("TEH", "MLGPAR", 10, "3.DEVIASI", 7),
        # pair C — in map, no SO at H
        row("KOPI", "MLGPAR", 10, "3.DEVIASI", 2),
        # noise at other dates
        row("TEH", "MLGPAR", 9, "3.DEVIASI", 99),
    ])
    ss_map = {("GULA (V.20) ", "MLGPAR"): 30.0,
              ("KOPI", "MLGPAR"): 30.0}

    out = hitung_nominal_pairs(data, 10, None, None, ss_map)
    print(out[["Nama Barang", "Resto", "Qty Deviasi"]].to_string(index=False))

    def q(b):
        r = out[out["Nama Barang"] == b]
        return float(r["Qty Deviasi"].iloc[0]) if len(r) else None

    a, b_, c = q("GULA (V.20)"), q("TEH"), q("KOPI")
    print(f"A(override, drift)={a}  B(no map)={b_}  C(no SO@H)={c}")
    print("EXPECTED: A=20 (50-30), B=7 (raw 3.DEVIASI), C=-30 (0-30)")
    ok = a == 20.0 and b_ == 7.0 and c == -30.0
    print("VERDICT:", "NOT-BUG" if ok else
          "BUG — saldo-sistem override keys/normalization broken in "
          "hitung_nominal_pairs")


if __name__ == "__main__":
    main()
