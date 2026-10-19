#!/usr/bin/env bash
# run_tests.sh — v3.9.62 — HARNESS UJI OTOMATIS (auto-Xvfb).
#
# Manfaat plugin pytest-xvbf TANPA konversi pytest: suite kita adalah
# skrip mandiri (test_ui_redesign.py, 1400+ cek) — harness ini hanya
# menjamin display virtual HIDUP sebelum suite berjalan, lalu
# meneruskan exit code suite (CI-friendly).
#
# Pemakaian (dari folder stock-monitoring-python):
#   bash run_tests.sh                  # pakai .venv/bin/python bila ada
#   PYTHON=python3 bash run_tests.sh   # pakai interpreter lain
#   DISPLAY_NUM=62 bash run_tests.sh   # display Xvfb lain
#
# Xvfb sengaja DIBIARKAN HIDUP setelah selesai (nyaman utk iterasi dev);
# matikan manual: pkill -f "Xvfb :61"
set -u -o pipefail

cd "$(dirname "$0")"

DISPLAY_NUM="${DISPLAY_NUM:-61}"
export DISPLAY_NUM

# --- pilih interpreter ------------------------------------------------------
if [ -z "${PYTHON:-}" ]; then
  if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
  else
    PY="python3"
  fi
else
  PY="$PYTHON"
fi

if ! command -v xdpyinfo >/dev/null 2>&1; then
  echo "[test] xdpyinfo tidak ada — pasang paket x11-utils (atau jalankan" >&2
  echo "[test] dengan DISPLAY aktif: DISPLAY=:0 bash run_tests.sh)" >&2
  exit 2
fi

# --- pastikan Xvfb :N hidup --------------------------------------------------
if ! xdpyinfo -display ":$DISPLAY_NUM" >/dev/null 2>&1; then
  echo "[test] memulai Xvfb :$DISPLAY_NUM ..."
  (setsid Xvfb ":$DISPLAY_NUM" -screen 0 1920x1080x24 \
     >"/tmp/xvfb_${DISPLAY_NUM}.log" 2>&1 &)
  for _ in $(seq 1 60); do
    xdpyinfo -display ":$DISPLAY_NUM" >/dev/null 2>&1 && break
    sleep 0.1
  done
fi

if ! xdpyinfo -display ":$DISPLAY_NUM" >/dev/null 2>&1; then
  echo "[test] Xvfb :$DISPLAY_NUM GAGAL hidup — cek /tmp/xvfb_${DISPLAY_NUM}.log" >&2
  exit 2
fi

echo "[test] DISPLAY=:$DISPLAY_NUM · interpreter: $PY"
echo "[test] menjalankan: $PY test_ui_redesign.py $*"
DISPLAY=":$DISPLAY_NUM" exec "$PY" test_ui_redesign.py "$@"
