"""
app.py — Shell UI Stock Monitoring v3.0 (total redesign).

Struktur jendela (ala aplikasi Waste):
    ┌────────────────────────────────────────────────────┐
    │ ⬛ Toolbar gelap: 📊 judul + v3.0 + [Export] [❓]  │
    ├────────────────────────────────────────────────────┤
    │ Tab modern ber-ikon (7 tab, fungsi tidak berubah)  │
    ├────────────────────────────────────────────────────┤
    │ Konten card-based per view                          │
    ├────────────────────────────────────────────────────┤
    │ StatusBar: ● status data + ringkasan rows           │
    └────────────────────────────────────────────────────┘

7 tab (fungsi & logika pipeline 100% dipertahankan):
  1. ⚙️ Config          : RootPath + LightMode + info config
  2. 🚀 Proses          : kontrol pipeline + KPI + konsol log gelap
  3. 📊 Pivot Table     : pivot matrix Excel-like
  4. 📦 DEVIASI GR      : wide matrix + CEK anomaly (satuan GR)
  5. 🧩 DEVIASI PCS     : wide matrix + CEK anomaly (non-GR)
  6. 📋 Laporan Deviasi : audit harian + 6-way Status Audit
  7. 🛒 Rincian PO      : pivot PO dengan search + sort

Pipeline tetap dijalankan di thread terpisah; log stdout dipipakan lewat
queue thread-safe; Stop button mengirim stop_event yang dicek pipeline di
checkpoint major. Freeze-fix v2.1.1 (batch log + truncate) dipertahankan.
"""
import os
import sys
import json
import queue
import threading
import time
import warnings
from pathlib import Path

# Suppress openpyxl noise warnings (no default style, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

# Pastikan parent folder di sys.path agar `from src...` jalan
_BASE = Path(__file__).resolve().parent.parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from src.config import Config
from src.main import run_pipeline, PipelineStopped
from src.ui.theme import (
    C_BG, C_CARD, C_GREEN, C_HEADER, C_ORANGE, C_AMBER, C_RED, C_TEXT_MUTED,
    apply_theme, font, mono,
)
from src.ui.widgets import (
    AccentButton, DangerButton, GhostButton, KpiCard, KpiRow, LoadingOverlay,
    Spinner, StatusBar, Toolbar, add_tooltip, make_log_console, make_tree,
    run_async,
)
from src.ui.pivot_view import PivotTableView
from src.ui.deviasi_view import DeviasiView
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.rincian_po_view import RincianPoView

# --- Konstanta UI -----------------------------------------------------------
APP_TITLE = "Stock Monitoring"
APP_VERSION = "3.1.0"  # UX v3.1: header filter, perbesar tabel, copy popup,
                        # pivot per resto, loading animation di semua proses
WINDOW_SIZE = "1280x760"
WINDOW_MIN = (1020, 640)

# Path config.json di root project
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"

# --- Freeze-fix konstanta (dipertahankan dari v2.1.1) -----------------------
MAX_CHUNKS_PER_POLL = 200       # max chunks diproses per poll cycle
MAX_CHARS_PER_POLL = 50000      # max karakter di-append per poll (cap buffer)
MAX_LOG_LINES = 3000            # max baris di Text widget (truncate ke 2000)
LOG_POLL_INTERVAL_MS = 100      # interval poll

# Warna status pipeline
_ST_SIAP = ("SIAP — menunggu perintah", C_GREEN)
_ST_RUN = ("Pipeline berjalan…", C_ORANGE)
_ST_DONE = ("SELESAI", C_GREEN)
_ST_STOP = ("DIHENTIKAN oleh user", C_AMBER)
_ST_ERR = ("ERROR — lihat log", C_RED)


# --- Helper: redirect stdout ke Text widget via queue -----------------------
class StreamToQueue:
    """Object file-like yang menulis ke queue (thread-safe)."""

    def __init__(self, q: queue.Queue):
        self.q = q

    def write(self, s: str):
        if s:
            self.q.put(s)

    def flush(self):
        pass


# --- Panduan singkat ---------------------------------------------------------
_HELP_TEXT = """PANDUAN SINGKAT — STOCK MONITORING v3.1

ALUR KERJA
  1. Tab ⚙️ Config   : pastikan RootPath menunjuk folder data export Accurate Online.
  2. Tab 🚀 Proses   : klik MULAI PROSES → pantau log → tunggu "SELESAI".
     (semua proses panjang menampilkan animasi loading / progress)
  3. Data otomatis terisi ke tab 📊 Pivot, 📦 Deviasi GR, 🧩 Deviasi PCS,
     📋 Laporan Deviasi, dan 🛒 Rincian PO.

TAB PIVOT TABLE
  • PIVOT PER: 🏪 Resto (default) atau 📅 Tanggal.
    - Resto   : kolom = resto, nilai = total per resto; hanya baris dengan
      nilai total > 0 yang tampil (baris kosong disembunyikan, kolom Total
      tidak ditampilkan). Contoh: item yang hanya ada di satu resto tetap
      muncul di kolom resto tersebut.
    - Tanggal : kolom = tanggal (seperti v3.0) + rentang tanggal.
  • Filter Nama Barang: klik header kolom "Nama Barang" (ikon corong ⧩).
  • Double-click cell → pop-up baris source data pendukung.

FILTER NAMA BARANG (SEMUA TAB)
  • Klik header kolom "Nama Barang" → popup filter ala Excel AutoFilter:
    pencarian nilai + daftar checkbox + Pilih semua + sort A→Z/Z→A.
  • Corong header berubah teal saat filter aktif.

TOMBOL ⛶ PERBESAR
  • Di setiap tabel: klik ⛶ Perbesar → window besar berisi tabel lengkap.
    Esc untuk menutup. Sort & double-click tetap berfungsi di sana.

TAB DEVIASI GR / PCS
  • 1 baris per (Resto × Barang × Satuan) di sekitar Tanggal H (H-2 … H+2).
  • Kolom CEK = deteksi anomali otomatis. Ubah Tanggal H + Enter.

TAB LAPORAN DEVIASI
  • Audit harian + 6 Status Audit. Klik kartu KPI untuk memfilter status.

TAB RINCIAN PO
  • Pivot PO: Nomor # (induk) → detail barang. Filter Cabang & Status.

POP-UP DETAIL — COPY NOMOR / NOMOR PO
  • Klik kanan baris     : Copy Nomor, Copy Nomor PO, copy baris,
                          copy SEMUA Nomor / Nomor PO (unik).
  • Double-click cell Nomor / Nomor PO : langsung copy nilai cell.
  • Ctrl+C               : copy Nomor baris terpilih.

SEMUA TABEL
  • Klik judul kolom untuk sort. Angka negatif (merah); nol = "-".

EXPORT
  • Tombol 💾 Export Excel di toolbar atas (aktif setelah pipeline selesai).
"""


# --- Aplikasi utama ---------------------------------------------------------
class StockMonitorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_TITLE} — Python Edition")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*WINDOW_MIN)
        self.root.configure(bg=C_BG)

        # State
        self.log_queue: queue.Queue = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.is_running = False
        # stop_event benar-benar memotong pipeline di checkpoint (dipertahankan)
        self.stop_event = threading.Event()
        self.append1_df = None
        self.rincian_po_df = None
        self._log_line_count = 0
        self._run_start_time: float | None = None
        self._elapsed_after_id = None

        # Style ttk (design system global)
        apply_theme(self.root)

        # Build UI
        self._build_toolbar()
        self._build_statusbar()
        self._build_notebook()

        # Redirect stdout/stderr ke queue
        sys.stdout = StreamToQueue(self.log_queue)
        sys.stderr = StreamToQueue(self.log_queue)

        # Poll queue untuk update log (batched + throttled — freeze fix)
        self._poll_log_queue()

        # Load config awal ke tab Config
        self._load_config_to_form()

    # =====================================================================
    # SHELL: TOOLBAR + STATUSBAR + NOTEBOOK
    # =====================================================================
    def _build_toolbar(self):
        self.toolbar = Toolbar(self.root, f"📊 {APP_TITLE}", APP_VERSION)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.btn_export_tb = self.toolbar.add_action(
            "💾 Export Excel", command=self._export_excel, accent=True)
        add_tooltip(self.btn_export_tb,
                    "Export Append1 + Rincian PO ke Excel\n(aktif setelah pipeline selesai)")
        self.btn_export_tb.configure(state="disabled")

        self.toolbar.add_action("❓ Bantuan", command=self._show_help)

    def _build_statusbar(self):
        self.statusbar = StatusBar(self.root)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.statusbar.set_right(f"v{APP_VERSION} · Python Edition")

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=(2, 6))

        self.tab_config = tk.Frame(self.notebook, bg=C_BG)
        self.tab_proses = tk.Frame(self.notebook, bg=C_BG)
        self.tab_pivot = tk.Frame(self.notebook, bg=C_BG)
        self.tab_deviasi_gr = tk.Frame(self.notebook, bg=C_BG)
        self.tab_deviasi_pcs = tk.Frame(self.notebook, bg=C_BG)
        self.tab_laporan = tk.Frame(self.notebook, bg=C_BG)
        self.tab_rincian = tk.Frame(self.notebook, bg=C_BG)

        self.notebook.add(self.tab_config, text="  ⚙️ Config  ")
        self.notebook.add(self.tab_proses, text="  🚀 Proses  ")
        self.notebook.add(self.tab_pivot, text="  📊 Pivot Table  ")
        self.notebook.add(self.tab_deviasi_gr, text="  📦 Deviasi GR  ")
        self.notebook.add(self.tab_deviasi_pcs, text="  🧩 Deviasi PCS  ")
        self.notebook.add(self.tab_laporan, text="  📋 Laporan Deviasi  ")
        self.notebook.add(self.tab_rincian, text="  🛒 Rincian PO  ")

        self._build_config_tab()
        self._build_proses_tab()
        self._build_pivot_tab()
        self._build_deviasi_gr_tab()
        self._build_deviasi_pcs_tab()
        self._build_laporan_tab()
        self._build_rincian_tab()

    # =====================================================================
    # TAB: CONFIG
    # =====================================================================
    def _build_config_tab(self):
        tab = self.tab_config
        wrap = tk.Frame(tab, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Card: Lokasi Data ---
        card = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                        highlightthickness=1)
        card.pack(fill="x")
        inner = tk.Frame(card, bg=C_CARD)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(inner, text="Lokasi Data (RootPath)", bg=C_CARD,
                 fg=C_HEADER, font=font(12, "bold")).pack(anchor="w")
        tk.Label(inner,
                 text="Ubah RootPath sesuai lokasi folder data Anda. Folder & sheet name "
                      "harus sesuai export Accurate Online.",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(9),
                 wraplength=760, justify="left").pack(anchor="w", pady=(2, 10))

        form = tk.Frame(inner, bg=C_CARD)
        form.pack(fill="x")
        tk.Label(form, text="RootPath", bg=C_CARD, fg=C_HEADER,
                 font=font(9, "bold")).grid(row=0, column=0, sticky="nw", pady=6)
        self.rootpath_var = tk.StringVar()
        self.entry_rootpath = ttk.Entry(form, textvariable=self.rootpath_var)
        self.entry_rootpath.grid(row=0, column=1, sticky="ew", padx=(10, 8), pady=6)
        add_tooltip(self.entry_rootpath,
                    "Folder utama berisi sub-folder export Accurate Online\n"
                    "(1. DEVIASI WEEKLY, 2. 22.05, dst. — lihat Info Config)")
        btn_browse = GhostButton(form, text="📂 Browse…", command=self._browse_folder)
        btn_browse.grid(row=0, column=2, pady=6)
        form.columnconfigure(1, weight=1)

        opt = tk.Frame(inner, bg=C_CARD)
        opt.pack(fill="x", pady=(4, 10))
        self.lightmode_var = tk.BooleanVar(value=True)
        self.chk_light = ttk.Checkbutton(
            opt, text="LightMode — pipeline ringan (skip bulan lalu, filter DEVIASI)",
            variable=self.lightmode_var)
        self.chk_light.pack(side="left")
        add_tooltip(self.chk_light,
                    "ON: skip Rekap bulan lalu + pre-filter KATEGORI=DEVIASI "
                    "(lebih cepat)\nOFF: proses semua data (mode penuh)")

        btn_row = tk.Frame(inner, bg=C_CARD)
        btn_row.pack(fill="x")
        AccentButton(btn_row, text="💾 Simpan Config",
                     command=self._save_config).pack(side="left")
        GhostButton(btn_row, text="↻ Reload Config",
                    command=self._load_config_to_form).pack(
            side="left", padx=(8, 0))

        # --- Card: Info Config (read-only) ---
        info_card = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                             highlightthickness=1)
        info_card.pack(fill="both", expand=True, pady=(12, 0))
        info_inner = tk.Frame(info_card, bg=C_CARD)
        info_inner.pack(fill="both", expand=True, padx=16, pady=(14, 16))

        tk.Label(info_inner, text="Info Config (read-only)", bg=C_CARD,
                 fg=C_HEADER, font=font(12, "bold")).pack(anchor="w")
        tk.Label(info_inner,
                 text="Folder & sheet yang akan dibaca pipeline dari RootPath.",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(9)).pack(
            anchor="w", pady=(2, 8))

        self.info_tree = make_tree(info_inner, ["item", "value"], show="headings")
        self.info_tree.column("item", width=260, minwidth=160, anchor="w")
        self.info_tree.heading("item", text="Item")
        self.info_tree.column("value", width=420, minwidth=200, anchor="w")
        self.info_tree.heading("value", text="Nilai")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Pilih RootPath")
        if folder:
            if not folder.endswith(os.sep):
                folder += os.sep
            self.rootpath_var.set(folder)

    def _load_config_to_form(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self._set_info_error(
                f"config.json tidak ditemukan di:\n{CONFIG_PATH}")
            self.rootpath_var.set("")
            return
        except json.JSONDecodeError as e:
            self._set_info_error(f"config.json rusak (JSON invalid):\n{e}")
            self.rootpath_var.set("")
            return

        self.rootpath_var.set(data.get("RootPath", ""))
        self.lightmode_var.set(data.get("LightMode", True))
        self._render_info_tree(data)

    def _render_info_tree(self, data: dict):
        self.info_tree.delete(*self.info_tree.get_children())
        for section, key in [("FOLDERS", "Folders"), ("SHEETS", "Sheets")]:
            sec_id = self.info_tree.insert(
                "", "end", values=(f"== {section} ==", ""))
            self.info_tree.item(sec_id, open=True)
            for k, v in (data.get(key, {}) or {}).items():
                self.info_tree.insert(sec_id, "end", values=(k, v))
        self.info_tree.insert(
            "", "end", values=("LightMode", str(data.get("LightMode", True))),
            tags=("bold",))
        self.info_tree.tag_configure("bold", font=font(9, "bold"))

    def _set_info_error(self, msg: str):
        self.info_tree.delete(*self.info_tree.get_children())
        self.info_tree.insert("", "end", values=("ERROR", msg), tags=("err",))
        self.info_tree.tag_configure("err", foreground="#dc2626")

    def _save_config(self):
        new_root = self.rootpath_var.get().strip()
        if not new_root:
            messagebox.showwarning("Validasi", "RootPath tidak boleh kosong.",
                                   parent=self.root)
            return

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError as e:
            messagebox.showerror(
                "Config Rusak",
                f"config.json tidak bisa dibaca (JSON invalid):\n{e}",
                parent=self.root)
            return

        data["RootPath"] = new_root
        data["LightMode"] = self.lightmode_var.get()

        backup_path = CONFIG_PATH.with_suffix(".json.bak")
        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror(
                "Gagal Simpan", f"Tidak bisa menulis config.json:\n{e}",
                parent=self.root)
            return

        messagebox.showinfo(
            "Berhasil",
            f"Config disimpan.\n\nRootPath: {new_root}\n"
            f"LightMode: {'ON' if data['LightMode'] else 'OFF'}",
            parent=self.root)
        self._load_config_to_form()

    # =====================================================================
    # TAB: PROSES
    # =====================================================================
    def _build_proses_tab(self):
        tab = self.tab_proses
        wrap = tk.Frame(tab, bg=C_BG)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Card: Kontrol Pipeline ---
        ctrl = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                        highlightthickness=1)
        ctrl.pack(fill="x")
        ctrl_inner = tk.Frame(ctrl, bg=C_CARD)
        ctrl_inner.pack(fill="x", padx=16, pady=14)

        tk.Label(ctrl_inner, text="Kontrol Pipeline", bg=C_CARD, fg=C_HEADER,
                 font=font(12, "bold")).pack(anchor="w")
        tk.Label(ctrl_inner,
                 text="Baca seluruh export Accurate Online → gabung → pivot → "
                      "hitung running stock & deviasi → tampilkan di UI.",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(9)).pack(
            anchor="w", pady=(2, 10))

        btns = tk.Frame(ctrl_inner, bg=C_CARD)
        btns.pack(fill="x", pady=(0, 10))
        self.btn_mulai = AccentButton(btns, text="🚀 MULAI PROSES",
                                      command=self._start_pipeline)
        self.btn_mulai.pack(side="left")
        add_tooltip(self.btn_mulai, "Jalankan pipeline penuh (Append1 + Rincian PO)")

        self.btn_stop = DangerButton(btns, text="⏹ Stop", state="disabled",
                                     command=self._stop_pipeline)
        self.btn_stop.pack(side="left", padx=(8, 0))
        add_tooltip(self.btn_stop,
                    "Hentikan pipeline secara graceful (dicek di checkpoint major)")

        self.btn_bersih = GhostButton(btns, text="🧹 Bersihkan Log",
                                      command=self._clear_log)
        self.btn_bersih.pack(side="left", padx=(8, 0))

        self.btn_export = GhostButton(btns, text="💾 Export ke Excel",
                                      state="disabled",
                                      command=self._export_excel)
        self.btn_export.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Status: siap.")
        status_row = tk.Frame(ctrl_inner, bg=C_CARD)
        status_row.pack(fill="x")
        self.status_spinner = Spinner(status_row, size=18, bg=C_CARD)
        self.status_spinner.pack(side="left", padx=(0, 8))
        self.status_spinner.stop()
        tk.Label(status_row, textvariable=self.status_var, bg=C_CARD,
                 fg=C_HEADER, font=font(10, "bold")).pack(anchor="w")
        self.progress = ttk.Progressbar(ctrl_inner, mode="indeterminate",
                                        orient="horizontal")
        self.progress.pack(fill="x", pady=(6, 2))

        # --- KPI row ---
        kpi_row = KpiRow(wrap)
        self.kpi_status = KpiCard(kpi_row, "Status Pipeline", "SIAP",
                                  "menunggu perintah", C_GREEN)
        self.kpi_elapsed = KpiCard(kpi_row, "Waktu Berjalan", "0.0 dtk",
                                   "sejak MULAI PROSES", C_HEADER)
        self.kpi_append = KpiCard(kpi_row, "Rows Append1", "—",
                                  "pipeline belum jalan")
        self.kpi_rincian = KpiCard(kpi_row, "Rows Rincian PO", "—",
                                   "pipeline belum jalan")
        for c in (self.kpi_status, self.kpi_elapsed, self.kpi_append,
                  self.kpi_rincian):
            kpi_row.add(c)
        kpi_row.pack(fill="x", pady=12)

        # --- Konsol log gelap ---
        log_card = tk.Frame(wrap, bg=C_CARD, highlightbackground="#e2e8f0",
                            highlightthickness=1)
        log_card.pack(fill="both", expand=True)
        log_head = tk.Frame(log_card, bg=C_CARD)
        log_head.pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(log_head, text="Log Proses", bg=C_CARD, fg=C_HEADER,
                 font=font(12, "bold")).pack(anchor="w")
        tk.Label(log_head, text="stdout pipeline real-time (batched, anti-freeze)",
                 bg=C_CARD, fg=C_TEXT_MUTED, font=font(9)).pack(anchor="w")

        log_wrap = tk.Frame(log_card, bg=C_CARD)
        log_wrap.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        self.log_text, _ = make_log_console(log_wrap)

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._log_line_count = 0

    # =====================================================================
    # LOG QUEUE (freeze fix dipertahankan)
    # =====================================================================
    def _append_log_batched(self, text: str):
        """Append batch text ke konsol log dengan truncation otomatis."""
        if not text:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text)

        new_lines = text.count("\n")
        self._log_line_count += new_lines

        if self._log_line_count > MAX_LOG_LINES:
            self.log_text.delete("1.0", "1001.0")
            self._log_line_count -= 1000

        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _poll_log_queue(self):
        """Batch log writes — ambil semua chunks dari queue (dengan cap)."""
        chunks = []
        total_chars = 0
        chunk_count = 0
        try:
            while chunk_count < MAX_CHUNKS_PER_POLL and total_chars < MAX_CHARS_PER_POLL:
                chunk = self.log_queue.get_nowait()
                chunks.append(chunk)
                total_chars += len(chunk)
                chunk_count += 1
        except queue.Empty:
            pass

        if chunks:
            self._append_log_batched("".join(chunks))

        self.root.after(LOG_POLL_INTERVAL_MS, self._poll_log_queue)

    # =====================================================================
    # PIPELINE CONTROL
    # =====================================================================
    def _start_pipeline(self):
        if self.is_running:
            messagebox.showinfo(
                "Sedang Berjalan",
                "Pipeline sedang berjalan. Tunggu hingga selesai atau klik Stop.",
                parent=self.root)
            return

        if not CONFIG_PATH.exists():
            messagebox.showerror(
                "Config Tidak Ada",
                f"config.json tidak ditemukan:\n{CONFIG_PATH}", parent=self.root)
            return

        self.notebook.select(self.tab_proses)
        self.is_running = True
        self.stop_event.clear()
        self.btn_mulai.set_enabled(False)
        self.btn_stop.set_enabled(True)
        self.btn_export.configure(state="disabled")
        self.btn_export_tb.configure(state="disabled")
        self.status_var.set("Status: menjalankan pipeline…")
        self.status_spinner.start()
        self.statusbar.set_status(*_ST_RUN)
        self.kpi_status.set_value("MENJALANKAN", "pipeline sedang diproses…",
                                  C_ORANGE)
        self.progress.start(12)
        self._run_start_time = time.time()
        self._tick_elapsed()

        self._append_log_batched("\n" + "=" * 60 + "\n  Memulai pipeline…\n")

        self.worker_thread = threading.Thread(
            target=self._run_pipeline_worker, daemon=True)
        self.worker_thread.start()

    def _tick_elapsed(self):
        """Update KPI waktu berjalan tiap detik selama pipeline aktif."""
        if self._run_start_time is None:
            return
        elapsed = time.time() - self._run_start_time
        if elapsed < 60:
            txt = f"{elapsed:.0f} dtk"
        else:
            txt = f"{int(elapsed // 60)} mnt {elapsed % 60:.0f} dtk"
        self.kpi_elapsed.set_value(txt)
        self._elapsed_after_id = self.root.after(1000, self._tick_elapsed)

    def _stop_elapsed(self):
        if self._elapsed_after_id:
            try:
                self.root.after_cancel(self._elapsed_after_id)
            except Exception:
                pass
            self._elapsed_after_id = None

    def _run_pipeline_worker(self):
        """Worker thread: jalankan run_pipeline, tangkap error."""
        try:
            append1_df, rincian_po_df = run_pipeline(
                verbose=True, stop_event=self.stop_event)
            self.root.after(0, lambda: self._on_pipeline_done(
                append1_df, rincian_po_df, None))
        except PipelineStopped as e:
            self.root.after(0, lambda: self._on_pipeline_done(None, None, (e, None)))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.root.after(0, lambda: self._on_pipeline_done(None, None, (e, tb)))

    def _on_pipeline_done(self, append1_df, rincian_po_df, error):
        """Dijadwalkan ke main thread via after()."""
        self.progress.stop()
        self.status_spinner.stop()
        self._stop_elapsed()
        self.is_running = False
        self.btn_mulai.set_enabled(True)
        self.btn_stop.set_enabled(False)

        # Final elapsed
        if self._run_start_time is not None:
            elapsed = time.time() - self._run_start_time
            self.kpi_elapsed.set_value(f"{elapsed:.1f} dtk", "total waktu proses")
            self._run_start_time = None

        if error is not None:
            exc, tb = error
            if isinstance(exc, PipelineStopped):
                self.status_var.set("Status: DIHENTIKAN oleh user.")
                self.statusbar.set_status(*_ST_STOP)
                self.kpi_status.set_value("DIHENTIKAN", "oleh user", C_AMBER)
                self._append_log_batched(f"\n[STOP] {exc}\n")
                return
            self.status_var.set("Status: ERROR.")
            self.statusbar.set_status(*_ST_ERR)
            self.kpi_status.set_value("ERROR", "lihat log untuk detail", C_RED)
            self._append_log_batched("\n[ERROR] Pipeline gagal:\n")
            self._append_log_batched(str(exc) + "\n")
            if tb:
                self._append_log_batched("\n" + tb + "\n")
            messagebox.showerror(
                "Pipeline Gagal",
                f"Terjadi error:\n{exc}\n\nLihat log di tab Proses untuk detail.",
                parent=self.root)
            return

        # Sukses — simpan + muat data ke semua view
        self.append1_df = append1_df
        self.rincian_po_df = rincian_po_df
        self.status_var.set("Status: SELESAI.")
        self.statusbar.set_status(
            f"SELESAI — Append1: {len(append1_df):,} rows · "
            f"Rincian PO: {len(rincian_po_df):,} rows", C_GREEN)
        self.kpi_status.set_value("SELESAI", "data siap dianalisis", C_GREEN)
        self.kpi_append.set_value(f"{len(append1_df):,}",
                                  "baris pivot siap di tab 📊")
        self.kpi_rincian.set_value(f"{len(rincian_po_df):,}",
                                   "baris PO siap di tab 🛒")
        self._append_log_batched(f"\n  Append1: {len(append1_df)} rows\n")
        self._append_log_batched(f"  Rincian PO: {len(rincian_po_df)} rows\n")

        # Load data into views
        self.pivot_view.load_data(append1_df)
        self.deviasi_gr_view.load_data(append1_df)
        self.deviasi_pcs_view.load_data(append1_df)
        self.laporan_view.load_data(append1_df)
        self.rincian_view.load_data(rincian_po_df)
        self.btn_export.configure(state="normal")
        self.btn_export_tb.configure(state="normal")

        # Switch to Pivot Table tab (default view)
        self.notebook.select(self.tab_pivot)

        messagebox.showinfo(
            "Selesai",
            f"Pipeline selesai.\n\nAppend1: {len(append1_df):,} rows\n"
            f"Rincian PO: {len(rincian_po_df):,} rows\n\n"
            "Lihat data di tab Pivot Table, Deviasi GR, Deviasi PCS,\n"
            "Laporan Deviasi & Rincian PO.",
            parent=self.root)

    def _stop_pipeline(self):
        """Stop graceful — set stop_event, pipeline memeriksa di checkpoint."""
        if not self.is_running:
            return
        self.stop_event.set()
        self.is_running = False
        self.btn_stop.set_enabled(False)
        self.status_var.set("Status: menghentikan pipeline…")
        self.statusbar.set_status("menghentikan pipeline…", C_AMBER)
        self.kpi_status.set_value("MENGHENTIKAN…", "menunggu checkpoint", C_AMBER)
        self._append_log_batched(
            "\n[STOP] Permintaan stop dikirim. Pipeline akan berhenti "
            "di checkpoint berikutnya.\n")

    def _export_excel(self):
        """Export data (Append1 + Rincian PO) ke Excel — async + loading."""
        if self.append1_df is None and self.rincian_po_df is None:
            messagebox.showwarning(
                "Export", "Belum ada data. Jalankan pipeline dulu.",
                parent=self.root)
            return
        filepath = filedialog.asksaveasfilename(
            title="Simpan sebagai Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="stock_monitoring_export.xlsx",
        )
        if not filepath:
            return

        append1_df = self.append1_df
        rincian_po_df = self.rincian_po_df

        # loading overlay di tengah jendela utama (dibuat lazily)
        if not hasattr(self, "_export_overlay"):
            self._export_overlay = LoadingOverlay(self.root,
                                                  "Mengekspor ke Excel…")
        self._export_overlay.show("Mengekspor ke Excel…", delay_ms=0)
        self.btn_export.configure(state="disabled")
        self.btn_export_tb.configure(state="disabled")

        def work():
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                if append1_df is not None and not append1_df.empty:
                    append1_df.to_excel(writer, sheet_name="Append1",
                                        index=False)
                if rincian_po_df is not None and not rincian_po_df.empty:
                    rincian_po_df.to_excel(writer, sheet_name="Rincian PO",
                                           index=False)
            return filepath

        def done(path):
            if self.append1_df is not None:
                self.btn_export.configure(state="normal")
                self.btn_export_tb.configure(state="normal")
            messagebox.showinfo(
                "Export Berhasil", f"Data di-export ke:\n{path}",
                parent=self.root)

        def on_error(e):
            if self.append1_df is not None:
                self.btn_export.configure(state="normal")
                self.btn_export_tb.configure(state="normal")
            messagebox.showerror(
                "Export Gagal", f"Tidak bisa export:\n{e}", parent=self.root)

        run_async(self.root, work, done, overlay=self._export_overlay,
                  loading_text="Mengekspor ke Excel…", on_error=on_error)

    # =====================================================================
    # BANTUAN
    # =====================================================================
    def _show_help(self):
        win = tk.Toplevel(self.root)
        win.title(f"Bantuan — {APP_TITLE} v{APP_VERSION}")
        # Posisikan di tengah parent
        try:
            pw, ph = 640, 560
            px = self.root.winfo_rootx() + (self.root.winfo_width() - pw) // 2
            py = self.root.winfo_rooty() + (self.root.winfo_height() - ph) // 2
            win.geometry(f"{pw}x{ph}+{max(px, 0)}+{max(py, 0)}")
        except Exception:
            win.geometry("640x560")
        win.transient(self.root)
        win.configure(bg=C_BG)

        head = tk.Frame(win, bg=C_HEADER)
        head.pack(fill="x")
        tk.Label(head, text=f"❓ Panduan — {APP_TITLE} v{APP_VERSION}",
                 bg=C_HEADER, fg="#f1f5f9", font=font(12, "bold")).pack(
            anchor="w", padx=16, pady=12)

        body = tk.Frame(win, bg=C_CARD, highlightbackground="#e2e8f0",
                        highlightthickness=1)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        txt = tk.Text(body, wrap="word", bg=C_CARD, fg=C_HEADER,
                      font=mono(10), relief="flat", bd=0, padx=14, pady=12)
        scroll = ttk.Scrollbar(body, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        txt.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        txt.insert("1.0", _HELP_TEXT)
        txt.configure(state="disabled")

        foot = tk.Frame(win, bg=C_BG)
        foot.pack(fill="x", pady=(0, 12))
        AccentButton(foot, text="Tutup", command=win.destroy).pack(
            side="right", padx=12)
        win.bind("<Escape>", lambda e: win.destroy())
        win.focus_set()

    # =====================================================================
    # TAB LAIN (view)
    # =====================================================================
    def _build_pivot_tab(self):
        self.pivot_view = PivotTableView(
            self.tab_pivot, go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.pivot_view.pack(fill="both", expand=True)

    def _build_deviasi_gr_tab(self):
        self.deviasi_gr_view = DeviasiView(
            self.tab_deviasi_gr, satuan_mode="GR",
            go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.deviasi_gr_view.pack(fill="both", expand=True)

    def _build_deviasi_pcs_tab(self):
        self.deviasi_pcs_view = DeviasiView(
            self.tab_deviasi_pcs, satuan_mode="PCS",
            go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.deviasi_pcs_view.pack(fill="both", expand=True)

    def _build_laporan_tab(self):
        self.laporan_view = LaporanDeviasiView(
            self.tab_laporan,
            go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.laporan_view.pack(fill="both", expand=True)

    def _build_rincian_tab(self):
        self.rincian_view = RincianPoView(
            self.tab_rincian,
            go_to_proses=lambda: self.notebook.select(self.tab_proses))
        self.rincian_view.pack(fill="both", expand=True)


# --- Entry point ------------------------------------------------------------
def main():
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
