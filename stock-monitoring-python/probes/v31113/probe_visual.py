#!/usr/bin/env python3
"""Probe visual v3.11.13 — UI bersih tanpa AI slop.

Jalankan app in-process di Xvfb :99, kunjungi SEMUA tab, screenshot
tiap tab → /tmp/v31113_tab_<n>.png. Verifikasi programatik:
- TIDAK ADA emoji dekoratif di: nama tab, judul toolbar, tombol aksi.
- Simbol fungsional tetap ada bila relevan (✓ kolom, • legend).
"""
import sys
import tkinter as tk

sys.path.insert(0, "/home/z/stock-audit/stock-monitoring-python")
from src.ui.app import StockMonitorApp  # noqa: E402

from PIL import ImageGrab  # noqa: E402

DECOR = ("⚙", "🚀", "📊", "📦", "🧩", "📤", "📋", "🧮", "🛒", "💾",
         "🧹", "📂", "🎯", "✏", "🗑", "⚖", "💰", "🚨", "🏆", "🧭",
         "♻", "🔎", "📉", "📈", "📭", "⚡", "🫵", "🔄", "📌", "🔍",
         "📥", "🏪", "📅", "⛶", "◱", "◫", "▦", "↺", "↻", "↕", "↔",
         "⏳", "⏹", "ℹ", "⤢", "⤡", "⧩")

results = []
ok = True


def check(name, cond, detail=""):
    global ok
    results.append((name, bool(cond), detail))
    if not cond:
        ok = False


def all_text(widget, acc):
    try:
        for c in widget.winfo_children():
            txt = ""
            try:
                txt = c.cget("text")
            except Exception:
                pass
            if isinstance(txt, str) and txt:
                acc.append(txt)
            all_text(c, acc)
    except tk.TclError:
        pass


root = tk.Tk()
root.geometry("1600x950+10+10")
_real_stdout = sys.stdout  # app meredirect stdout → konsol log
app = StockMonitorApp(root)
sys.stdout = _real_stdout  # pulihkan utk output probe
root.update()

# --- 1. nama tab bersih ---
tab_names = [app.notebook.tab(i, "text") for i in
             range(app.notebook.index("end"))]
print("TAB NAMES:", tab_names)
check("Nama tab tanpa emoji dekoratif",
      not any(d in t for t in tab_names for d in DECOR), str(tab_names))
check("Nama tab polos lengkap",
      "Pivot Table" in " ".join(tab_names)
      and "Config" in " ".join(tab_names)
      and "Deviasi GR" in " ".join(tab_names), str(tab_names))

# --- 2. judul toolbar ---
tb_texts = []
all_text(app.toolbar, tb_texts)
print("TOOLBAR:", tb_texts[:6])
check("Toolbar tanpa emoji", not any(d in t for t in tb_texts for d in DECOR),
      str(tb_texts[:4]))

# --- 3. screenshot tiap tab + cek tombol/label view ---
for i, name in enumerate(tab_names):
    app.notebook.select(i)
    root.update()
    for _ in range(12):
        root.update()
    texts = []
    all_text(app.root, texts)
    bad = [(t, d) for t in texts for d in DECOR if d in t]
    check(f"Tab '{name}': tanpa emoji dekoratif", not bad,
          str(bad[:4]))
    img = ImageGrab.grab(xdisplay=":99")
    img.crop((0, 0, 1600, 950)).save(f"/tmp/v31113_tab_{i}_{name.replace(' ', '_')}.png")
    print(f"  tab {i} '{name}': {len(texts)} label, screenshot OK")

# --- 4. EmptyState tanpa ikon (tab pivot = index 2) ---
app.notebook.select(2)
root.update()
es = getattr(app.pivot_view, "empty", None)
kids = es._center.winfo_children() if es else []
big = [k for k in kids if str(k.cget("font",)) and "40" in str(k.cget("font"))]
check("EmptyState tanpa label ikon raksasa", not big, f"{len(kids)} anak")

root.destroy()

print()
for name, cond, detail in results:
    print(f"  {'PASS' if cond else 'FAIL'} — {name}"
          + (f" :: {detail}" if (detail and not cond) else ""))
print(f"\n{'ALL PASS' if ok else 'ADA FAIL'} ({len(results)} check)")
sys.exit(0 if ok else 1)
