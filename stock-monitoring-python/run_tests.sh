#!/usr/bin/env bash
# run_tests.sh — v3.9.62 — HARNESS UJI OTOMATIS (auto-Xvfb).
#
# Manfaat plugin pytest-xvbf TANPA konversi pytest: suite kita adalah
# skrip mandiri (test_ui_redesign.py, 1400+ cek) — harness ini hanya
# menjamin display virtual HIDUP sebelum suite berjalan, lalu
# meneruskan exit code suite (CI-friendly).
#
# v3.9.64 — FIX (audit 15-c F-06): xdpyinfo TIDAK lagi hard-require —
# display hidup dicek via xdpyinfo BILA ADA, fallback probe Tk singkat.
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

# --- v3.9.64 — FIX (audit 15-c F-06): cek display TANPA hard-require -----
# xdpyinfo. Dulu script exit 2 walau Xvfb :N SUDAH HIDUP hanya karena
# xdpyinfo tidak terpasang (x11-utils opsional). Kini: pakai xdpyinfo bila
# ada; kalau tidak, probe socket X + sambungan Tk singkat via interpreter
# terpilih (Python selalu ada di jalur harness ini).
_xvfb_alive() {
  [ -S "/tmp/.X11-unix/X${DISPLAY_NUM}" ] || return 1
  if command -v xdpyinfo >/dev/null 2>&1; then
    xdpyinfo -display ":$DISPLAY_NUM" >/dev/null 2>&1
  else
    DISPLAY=":$DISPLAY_NUM" timeout 6 "$PY" \
      -c "import tkinter; tkinter.Tk().destroy()" >/dev/null 2>&1
  fi
}

# --- pastikan Xvfb :N hidup --------------------------------------------------
if ! _xvfb_alive; then
  echo "[test] memulai Xvfb :$DISPLAY_NUM ..."
  (setsid Xvfb ":$DISPLAY_NUM" -screen 0 1920x1080x24 \
     >"/tmp/xvfb_${DISPLAY_NUM}.log" 2>&1 &)
  for _ in $(seq 1 60); do
    _xvfb_alive && break
    sleep 0.1
  done
fi

if ! _xvfb_alive; then
  echo "[test] Xvfb :$DISPLAY_NUM GAGAL hidup — cek /tmp/xvfb_${DISPLAY_NUM}.log" >&2
  echo "[test] (pastikan Xvfb terpasang: apt install xvfb / x11-utils opsional" >&2
  echo "[test]  sejak v3.9.64 — display hidup dicek tanpa xdpyinfo)" >&2
  exit 2
fi

echo "[test] DISPLAY=:$DISPLAY_NUM · interpreter: $PY"

# v3.9.69 — 6.2 (audit eksternal ke-2): test_mock.py IKUT dijalankan oleh
# harness lokal (dulu hanya test_ui_redesign — baterai mock pipeline tak
# pernah tesar lewat jalur ini; job CI 'tests' sudah menjalankan keduanya
# sejak v3.9.68 — kini jalur lokal pun setara). Exit code = gagal bila
# SALAH SATU saja gagal (CI-friendly, tanpa exec supaya keduanya tetap
# dijalankan dan kegagalan pertama tak menyembunyikan yang kedua).
_rc=0
echo "[test] menjalankan: $PY test_ui_redesign.py $*"
DISPLAY=":$DISPLAY_NUM" "$PY" test_ui_redesign.py "$@" || _rc=$?
echo "[test] menjalankan: $PY test_mock.py"
DISPLAY=":$DISPLAY_NUM" "$PY" test_mock.py || _rc=$?
if [ "$_rc" -ne 0 ]; then
  echo "[test] GAGAL — exit code $_rc (lihat output blok yang gagal di atas)" >&2
fi
exit "$_rc"
