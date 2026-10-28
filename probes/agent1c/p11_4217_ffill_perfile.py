"""P11 — fn_4217 kategori ffill must stay PER-FILE (v3.9.33 fix) — regression
guard incl. the v3.9.37 read-cache path (2nd call served from cache).

file-1: barang G1 with kategori whitelist-passing, saldo 5.
file-2: barang G2 with BLANK Kategori Barang, saldo 7 (no pair elsewhere).
EXPECTED: G2 DROPPED (blank kategori fails whitelist; per-file ffill must
          not let file-2 inherit file-1's last kategori value).
ACTUAL (bleed): G2 kept with G1's kategori -> phantom saldo.
Also: running fn_4217 twice (2nd from read cache) must give IDENTICAL output.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT, b_4217, make_config, make_root

sys.path.insert(0, PROJECT)
from src.config import Config  # noqa: E402
from src.pipeline.fn_4217 import fn_4217  # noqa: E402

KAT = "10.FOOD [RM] - COM V.2"


def main():
    root = make_root()
    cfg = Config(make_config(root))
    folder = cfg.folder("SaldoAwal4217")
    b_4217(root, [("G1", KAT, "KG", {"RESTO MALANG (MLGPAR)": 5})],
           fname="saldo_a.xlsx")
    b_4217(root, [("G2", None, "KG", {"RESTO MALANG (MLGPAR)": 7})],
           fname="saldo_b.xlsx")

    # NOTE: production always passes the config whitelist
    # (queries.query_4217 -> KategoriBarang4217, default
    # DEFAULT_KATEGORI_WHITELIST). None would mean "no filter" by design.
    wl = cfg.KategoriBarang4217
    out1 = fn_4217(folder, kategori_whitelist=wl)
    names1 = sorted(out1["Nama Barang"].unique().tolist())
    out2 = fn_4217(folder, kategori_whitelist=wl)   # 2nd call — cache path
    names2 = sorted(out2["Nama Barang"].unique().tolist())

    print(f"run#1 (disk read) barang = {names1}")
    print(f"run#2 (cache hit)  barang = {names2}")
    print("EXPECTED: ['G1'] — G2 (blank kategori, no protected pair) dropped")
    ok = names1 == ["G1"] and names2 == ["G1"]
    ident = out1.reset_index(drop=True).equals(out2.reset_index(drop=True))
    print(f"cache-path identical output: {ident}")
    print("VERDICT:", "NOT-BUG" if (ok and ident) else
          "BUG — kategori ffill bled across files (or cache served tainted "
          "frame); phantom saldo G2 survives whitelist")


if __name__ == "__main__":
    main()
