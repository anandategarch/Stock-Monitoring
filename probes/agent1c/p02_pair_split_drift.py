"""P02 — append1 pivot splits pairs on whitespace/case drift between source
files (asymmetric normalization).

The kategori merge (LANGKAH 5) normalizes keys (strip+upper, v3.9.33), the
saldo-sistem lookup in views normalizes (v3.11.1), the 4217 whitelist
protects pairs via _norm_barang (v3.9.39) — but the CORE pivot
(`calculation_source.groupby(KeyColumns)`) still groups on RAW strings.
A trailing space (or case drift) in the 42.17 file vs the Rekap Mentah file
splits ONE physical pair into TWO pivot groups: the saldo lands in one group
and the SO/IN in another → SALDO AKHIR / DEVIASI silently wrong for BOTH.

Scenario A: 42.17 'GULA (V.20) ' (trailing space) vs rekap 'GULA (V.20)'.
Scenario B: 42.17 numeric cell 100383 (int) vs rekap text '100383'
            (dtype trap: groupby int vs str = different groups).

EXPECTED: ONE pair — SALDO AWAL 80, SO(1)=100 → DEVIASI(1) = 100-80 = 20.
ACTUAL  : TWO pairs — saldo-only pair DEVIASI(1) = -80, SO-pair
          DEVIASI(1) = 100 (saldo & SO never meet).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    long_subset, make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.append1 import build_append1  # noqa: E402

KAT = "10.FOOD [RM] - COM V.2"   # in DEFAULT_KATEGORI_WHITELIST


def build(root, saldo_name):
    b_rekap(root, "MLGPAR", [
        ("GULA (V.20)", "KG", "SO", "input so harian", {1: 100}),
        ("GULA (V.20)", "KG", "BARANG MASUK", "input so harian", {1: 50}),
    ])
    b_2205(root, [("ACR.2026.09.1", "2026-10-05", "RESTO MALANG (MLGPAR)",
                   "GULA (V.20)", 5)])
    b_4205(root, [("IT.2026.10.1", "GUDANG HO (MLGPAR)", "2026-10-05",
                   "GULA (V.20)", 30, "2026-10-05 08:00:00")])
    b_3224(root, [])
    b_4217(root, [(saldo_name, KAT, "KG",
                   {"RESTO MALANG (MLGPAR)": 80})])
    b_dbs(root, [("GULA (V.20)", "COM DEVIASI - RESTO", "AKTIF")])
    return Config(make_config(root))


def check(tag, saldo_name):
    root = make_root()
    cfg = build(root, saldo_name)
    final = build_append1(cfg)

    sa = long_subset(final, "SALDO AWAL")
    so = long_subset(final, "1.SO")
    dev1 = long_subset(final, "3.DEVIASI")
    dev1 = dev1[dev1["Tanggal"] == 1]
    pairs = final[["Nama Barang", "NAMA RESTO"]].drop_duplicates()
    n_pairs = len(pairs[pairs["NAMA RESTO"] == "MLGPAR"])

    print(f"--- {tag} (42.17 name={saldo_name!r}) ---")
    print("SALDO AWAL rows:", sa[["Nama Barang", "Tanggal", "NILAI"]]
          .to_dict("records"))
    print("1.SO@1 rows    :", so[so["Tanggal"] == 1][["Nama Barang", "NILAI"]]
          .to_dict("records"))
    print("3.DEVIASI@1   :", dev1[["Nama Barang", "NILAI"]].to_dict("records"))
    print(f"distinct pairs (MLGPAR) = {n_pairs}")
    print("EXPECTED: 1 pair; SALDO AWAL=80 at t=1; DEVIASI@1 = 100-80 = 20")
    print(f"ACTUAL  : {n_pairs} pair(s); DEVIASI@1 = "
          f"{sorted(dev1['NILAI'].tolist())}")
    ok = (n_pairs == 1
          and len(dev1) == 1 and abs(float(dev1['NILAI'].iloc[0]) - 20.0) < 1e-9)
    print("VERDICT:", "NOT-BUG" if ok else
          "BUG (P1) — pivot groups on RAW keys: whitespace/dtype drift "
          "between 42.17 and Rekap splits one pair into two → SALDO AKHIR "
          "& DEVIASI wrong for both halves (silent wrong numbers)")
    print()


if __name__ == "__main__":
    check("A: trailing-space drift", "GULA (V.20) ")
    check("B: numeric-cell drift", 100383)
    check("C: control (exact name)", "GULA (V.20)")
