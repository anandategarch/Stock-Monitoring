"""P15 — main._extract_append1_maps + fn_audit.build_audit_input /
_attach_so_kemarin: "SO kemarin" basis correctness (v3.10 / v3.10.1 fixes).

Scenario:
  pair X: rekap SO t=1:100, t=3:90, t=5:80; BM t=3:5; 42.17 SA=70
  pair Y: rekap SO t=2:50 only;                  42.17 SA=40
  pair Z: IN only (no rekap) -> absent from audit keys by design
EXPECTED:
  X: t=1 SO-kemarin=70 (SALDO AWAL priority), t=3 -> 100, t=5 -> 90
  Y: t=2 SO-kemarin=40 (SA at FIRST current-month row — v3.10.1)
  no cross-pair leakage (X t=1 never sees Y/Z values)
  saldo_awal_map = {('MLGPAR','X'): 70, ('MLGPAR','Y'): 40}  (resto,barang)
"""
import os
import pandas as pd
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (PROJECT, b_2205, b_3224, b_4205, b_4217, b_dbs, b_rekap,
                    make_config, make_root)

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.main import _extract_append1_maps  # noqa: E402
from src.pipeline.append1 import build_append1  # noqa: E402
from src.pipeline.fn_audit import build_audit_input  # noqa: E402

KAT = "10.FOOD [RM] - COM V.2"


def main():
    root = make_root()
    b_rekap(root, "MLGPAR", [
        ("X", "KG", "SO", "input so harian", {1: 100, 3: 90, 5: 80}),
        ("X", "KG", "BARANG MASUK", "input so harian", {3: 5}),
        ("Y", "KG", "SO", "input so harian", {2: 50}),
    ])
    b_2205(root, [])
    b_4205(root, [])
    b_3224(root, [("2026-10-05", 9, "Z", "GUDANG X (MLGPAR)",
                   "RI.2026.10.0001", "PO.2026.09.001", "2026-10-05 08:00")])
    b_4217(root, [("X", KAT, "KG", {"RESTO MALANG (MLGPAR)": 70}),
                  ("Y", KAT, "KG", {"RESTO MALANG (MLGPAR)": 40})])
    b_dbs(root, [("X", "COM DEVIASI - RESTO", "AKTIF"),
                 ("Y", "COM DEVIASI - RESTO", "AKTIF")])

    in_detail = {}
    rekap_so = {}
    final = build_append1(Config(make_config(root)),
                          in_detail_out=in_detail, rekap_so_out=rekap_so)
    sa_map, bk_map = _extract_append1_maps(final)
    print(f"saldo_awal_map = {sa_map}")
    print(f"bk_map         = {bk_map}")

    audit = build_audit_input(rekap_so["df"], in_detail["df"], sa_map)
    cols = ["Resto", "Nama Item", "Tanggal", "Hasil SO", "Qty SO Harian",
            "Qty SO Kemarin"]
    print(audit[cols].to_string(index=False))

    def sk(b, t):
        r = audit[(audit["Nama Item"] == b) & (audit["Tanggal"] == t)]
        return float(r["Qty SO Kemarin"].iloc[0]) if len(r) else None

    checks = {
        "X@1 = 70 (SA priority)": sk("X", 1) == 70,
        "X@3 = 100": sk("X", 3) == 100,
        "X@5 = 90": sk("X", 5) == 90,
        "Y@2 = 40 (SA first cur row)": sk("Y", 2) == 40,
        # Z (IN-only, resto rekap) IS in audit input BY DESIGN ("union
        # tanggal dengan aktivitas ... atau ada penerimaan sistem");
        # it must have NO SO basis (NaN), not an inherited one.
        "Z@5 present, SO-kemarin NaN": (
            len(audit[audit["Nama Item"] == "Z"]) == 1
            and pd.isna(sk("Z", 5))),
        "sa_map exact": sa_map == {("MLGPAR", "X"): 70.0,
                                   ("MLGPAR", "Y"): 40.0},
    }
    for k, v in checks.items():
        print(f"  {k}: {'OK' if v else 'FAIL'}")
    ok = all(checks.values())
    print("\nEXPECTED: all checks hold")
    print("VERDICT:", "NOT-BUG" if ok else
          "BUG — SO-kemarin basis / saldo_awal_map extraction broken")


if __name__ == "__main__":
    main()
