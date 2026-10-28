#!/bin/bash
# run_probe.sh — start a private Xvfb :99 for the probe run (the sandbox
# reaps background processes between tool invocations), run probe, cleanup.
# Usage: ./run_probe.sh <probe.py> [extra args...]
PROBE="$1"
shift || true
export DISPLAY=:99

# if display already reachable, reuse it
if /home/z/.venv/bin/python3 -c "import tkinter as tk; tk.Tk().destroy()" 2>/dev/null; then
    echo "[run_probe] reusing existing X display :99"
else
    rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
    Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp >/tmp/xvfb-run-probe.log 2>&1 &
    XPID=$!
    for i in $(seq 1 40); do
        if /home/z/.venv/bin/python3 -c "import tkinter as tk; tk.Tk().destroy()" 2>/dev/null; then
            break
        fi
        sleep 0.25
    done
    echo "[run_probe] started Xvfb pid=$XPID"
fi

cd /home/z/stock-audit/probes/agent1b
/home/z/.venv/bin/python3 "$PROBE" "$@"
RC=$?

# kill only the Xvfb we started
if [ -n "$XPID" ]; then
    kill "$XPID" 2>/dev/null
fi
exit $RC
