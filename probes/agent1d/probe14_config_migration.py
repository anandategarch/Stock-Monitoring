"""PROBE 14 — config.json version migration & defensive startup (v3.9.69
claims re-verified on the REAL Config class):
  1. old-version config (pre-v3.9.17: no Pemindahan4205Lalu / SaldoSistem
     4217 / Harga / KategoriBarang4217 / KategoriManual / DeviasiBulanan*)
     → loads with in-memory defaults, no KeyError
  2. corrupted JSON (trailing comma) → RuntimeError with Indonesian message
     (not raw json.JSONDecodeError)
  3. missing mandatory key (no Sheets) → RuntimeError listing the key
  4. Folders as a LIST (bad manual edit) → RuntimeError, not AttributeError
  5. KategoriBarang4217 as a STRING → warning + default whitelist
  6. folder()/sheet() missing sub-key → RuntimeError (not KeyError)

EXPECTED : all degrade paths friendly; old config loads
ACTUAL   : (see output)
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/z/stock-audit/probes/agent1d")
import _harness as H  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="a1d_cfg"))
results = []

BASE = {
    "RootPath": "C:\\KERJA\\1. RESTO",
    "Folders": {"RekapBerjalan": "1. Rekap"},
    "Sheets": {"Penjualan2205": "#22.05"},
}

import src.config as cfgmod  # noqa: E402


def load(d, name):
    p = tmp / name
    p.write_text(json.dumps(d) if not isinstance(d, str) else d,
                 encoding="utf-8")
    return cfgmod.Config(str(p))


# 1. old config loads with defaults
try:
    c = load(BASE, "old.json")
    ok = (c.Folders["Pemindahan4205Lalu"] == "4.1 4205 Bulan Lalu"
          and c.Folders["SaldoSistem4217"] == "6. 42.17"
          and c.Folders["Harga"] == "09.Harga"
          and isinstance(c.KategoriBarang4217, list)
          and c.KategoriManual == {})
    results.append(("1: pre-v3.9.17 config loads with defaults", ok,
                    f"OK folders={len(c.Folders)}" if ok else "FAIL"))
except Exception as e:  # noqa: BLE001
    results.append(("1: pre-v3.9.17 config loads with defaults", False,
                    repr(e)))

# 2. corrupted JSON -> friendly RuntimeError
try:
    load('{"RootPath": "x", "Folders": {"a": "b"},}', "corrupt.json")
    results.append(("2: corrupt JSON -> RuntimeError(ID)", False,
                    "no exception raised"))
except cfgmod.json.JSONDecodeError as e:
    results.append(("2: corrupt JSON -> RuntimeError(ID)", False,
                    f"RAW JSONDecodeError leaked: {e!r}"))
except RuntimeError as e:
    ok = "config.json rusak" in str(e)
    results.append(("2: corrupt JSON -> RuntimeError(ID)", ok, str(e)[:80]))

# 3. missing mandatory key
d = dict(BASE); d.pop("Sheets")
try:
    load(d, "nosheets.json")
    results.append(("3: missing Sheets -> RuntimeError", False, "no raise"))
except RuntimeError as e:
    results.append(("3: missing Sheets -> RuntimeError",
                    "Sheets" in str(e), str(e)[:80]))

# 4. Folders as list
d = dict(BASE); d["Folders"] = ["a", "b"]
try:
    load(d, "folderslist.json")
    results.append(("4: Folders list -> RuntimeError", False, "no raise"))
except RuntimeError as e:
    results.append(("4: Folders list -> RuntimeError", "Folders" in str(e),
                    str(e)[:80]))
except (AttributeError, TypeError) as e:
    results.append(("4: Folders list -> RuntimeError", False,
                    f"raw {type(e).__name__}: {e}"))

# 5. KategoriBarang4217 string -> warning + default
d = dict(BASE); d["KategoriBarang4217"] = "DEVIASI"
try:
    c = load(d, "katstr.json")
    ok = c.KategoriBarang4217 != ["D", "E", "V", "I", "A", "S"] \
        and isinstance(c.KategoriBarang4217, list)
    results.append(("5: KategoriBarang4217 string -> default list", ok,
                    f"got {c.KategoriBarang4217[:3]}…"))
except Exception as e:  # noqa: BLE001
    results.append(("5: KategoriBarang4217 string -> default list", False,
                    repr(e)))

# 6. folder()/sheet() missing sub-key
try:
    c = load(BASE, "base.json")
    c.folder("TidakAda")
    results.append(("6: folder() missing key -> RuntimeError", False,
                    "no raise"))
except RuntimeError as e:
    results.append(("6: folder() missing key -> RuntimeError",
                    "'TidakAda'" in str(e), str(e)[:70]))
except KeyError as e:
    results.append(("6: folder() missing key -> RuntimeError", False,
                    f"raw KeyError {e}"))

all_ok = all(ok for _, ok, _ in results)
for label, ok, detail in results:
    H.out(f"[{'OK ' if ok else 'FAIL'}] {label:44s} {detail}")
H.out("EXPECTED : all migration/degrade paths friendly")
H.out(f"ACTUAL   : all_ok={all_ok}")
H.out("VERDICT  :", "NOT-BUG" if all_ok else "BUG")
sys.exit(0 if all_ok else 1)
