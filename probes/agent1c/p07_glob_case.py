"""P07 — _list_excel_files glob is case-sensitive on Linux (uppercase
extensions invisible).

App targets Windows (case-insensitive glob), but the README claims Linux
compat paths exist (run_tests.sh, MULAI.bat fallback python). On a
case-sensitive filesystem, 'DATA.XLSX' / 'ri.XLSB' are silently NEVER read —
folder preflight reports 0 files, pipeline 'finishes' with empty frames.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PROJECT

sys.path.insert(0, PROJECT)
from src.pipeline.helpers import _list_excel_files  # noqa: E402
import tempfile  # noqa: E402
import openpyxl  # noqa: E402


def main():
    d = tempfile.mkdtemp(prefix="a1c_glob_")
    names = ["a1.xlsx", "A2.XLSX", "b1.xlsb", "B2.XLSB", "c1.XLS",
             "d1.xlsm", "D2.XLSM"]
    for n in names:
        wb = openpyxl.Workbook()
        os.makedirs(d, exist_ok=True)
        wb.save(os.path.join(d, n))
        wb.close()

    got = [os.path.basename(f) for f in _list_excel_files(d)]
    print(f"files created : {sorted(names)}")
    print(f"files visible : {sorted(got)}")
    missing = sorted(set(names) - set(got))
    print(f"EXPECTED: all 7 visible (Windows behavior)")
    print(f"ACTUAL  : {len(got)} visible; missing = {missing}")
    print("VERDICT:", "NOT-BUG" if not missing else
          f"BUG (P3, platform) — uppercase-extension files {missing} are "
          f"invisible to _list_excel_files on case-sensitive filesystems "
          f"(glob lowercase-only patterns; Windows unaffected)")


if __name__ == "__main__":
    main()
