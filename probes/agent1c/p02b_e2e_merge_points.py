"""P02b — E2E regression (audit 3-b, bug #6): SEMUA titik merge append1 pada
pasangan ber-drift ejaan (bukan hanya pivot).

Drift: rekap 'gula (v.20)' (lowercase) vs 32.24 'GULA (V.20)' vs 42.17
'GULA (V.20) ' (trailing space). Dengan fix bug #6 semua sumber menyatu
menjadi SATU pasangan; ejaan display = perwakilan PRIORITAS REKAP
('gula (v.20)' — lihat _pair_key_reps). Titik merge yang HARUS tetap
nempel pada pasangan gabungan (semuanya merge ke frame final ber-ejaan
kanonik dari frame eksternal ber-ejaan mentah):
  - SATUAN rekap (LANGKAH 8)          → 'KG'
  - SOURCE DATA rekap (LANGKAH 9)     → 'input so harian'
  - SOURCE KIRIMAN (LANGKAH 5b)       → 'Eksternal' (IN 32.24)
  - KATEGORI master (LANGKAH 5 _KEY)  → 'MASTER KAT'
  - DEVIASI@1 = SO 100 − SA 80 = 20
  - kolom kunci temp __k_barang/__k_resto TIDAK bocor ke output.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.append1 import build_append1  # noqa: E402


def main():
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("gula (v.20)", "KG", "SO", "input so harian", {1: 100}),
    ])
    b_2205(root, [])
    b_4205(root, [])
    b_3224(root, [("2026-10-05", 20, "GULA (V.20)", "GUDANG X (MLGPAR)",
                   123.0, "PO.2026.09.002", "2026-10-05 08:00:00")])
    b_4217(root, [("GULA (V.20) ", "10.FOOD [RM] - COM V.2", "GR",
                   {"RESTO MALANG (MLGPAR)": 80})])
    b_dbs(root, [("GULA (V.20)", "MASTER KAT", "AKTIF")])
    final = build_append1(Config(make_config(root)))

    pairs = final[["Nama Barang", "NAMA RESTO"]].drop_duplicates().values.tolist()
    print("distinct pairs:", pairs)
    print("EXPECTED: 1 pair, display = ejaan rekap 'gula (v.20)'")
    print(f"ACTUAL  : {len(pairs)} pair, display = {pairs[0][0]!r}")
    ok = len(pairs) == 1
    if ok:
        ok &= pairs[0][0] == "gula (v.20)" and pairs[0][1] == "MLGPAR"
        so = final[final["JENIS"] == "1.SO"]
        dev1 = final[(final["JENIS"] == "3.DEVIASI")
                     & (final["Tanggal"] == 1)]
        checks = {
            "SATUAN rekap nempel 'KG'":
                so["SATUAN"].notna().all() and (so["SATUAN"] == "KG").all(),
            "SOURCE DATA nempel 'input so harian'":
                (so["SOURCE DATA"] == "input so harian").all(),
            "SOURCE KIRIMAN 'Eksternal' (32.24)":
                (final["SOURCE KIRIMAN"] == "Eksternal").all(),
            "KATEGORI master 'MASTER KAT'":
                (final["KATEGORI"] == "MASTER KAT").all(),
            "DEVIASI@1 = 20":
                len(dev1) == 1 and abs(dev1["NILAI"].iloc[0] - 20.0) < 1e-9,
            "kolom __k_* tak bocor":
                "__k_barang" not in final.columns
                and "__k_resto" not in final.columns,
        }
        for k, v in checks.items():
            print(f"  [{'OK' if v else 'FAIL'}] {k}")
            ok &= bool(v)
    print("VERDICT:", "NOT-BUG" if ok else
          "BUG — titik merge append1 miss pada pasangan ber-drift")


if __name__ == "__main__":
    main()
