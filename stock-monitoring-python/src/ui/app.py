"""
app.py — Tkinter UI untuk Stock Monitoring - Python Edition.

7 tab:
  1. Config           : lihat & ubah RootPath, simpan ke config.json
  2. Proses           : tombol MULAI PROSES + Stop, log real-time, progress
  3. Pivot Table      : visualisasi pivot matrix Append1 (Excel-like)
  4. DEVIASI GR       : wide matrix + CEK anomaly detection (satuan GR)
  5. DEVIASI PCS      : wide matrix + CEK anomaly detection (satuan non-GR)
  6. LAPORAN DEVIASI  : long-format daily audit + 6-way Status Audit
  7. Rincian PO       : tabel Rincian PO dengan search + sort

Tidak ada Excel output — data ditampilkan langsung di UI.

Jalankan dengan:
    python -m src.ui.app

Pipeline dijalankan di thread terpisah supaya UI tidak freeze.
Log stdout dipipakan ke Text widget lewat queue (thread-safe).
Stop button benar-benar functional — mengirim stop_event yang dicek di
checkpoint major (4217, IN, Append1, Rincian PO) dan raise PipelineStopped.

FREEZE FIX (v2.1.1): log writes di-batch + truncate Text widget untuk
hindari UI not-responding saat pipeline cetak ribuan baris log.
"""
import os
import sys
import json
import queue
import threading
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
from src.ui.pivot_view import PivotTableView
from src.ui.deviasi_view import DeviasiView
from src.ui.laporan_deviasi_view import LaporanDeviasiView
from src.ui.rincian_po_view import RincianPoView

# --- Konstanta UI -----------------------------------------------------------
APP_TITLE = "Stock Monitoring - Python Edition"
APP_VERSION = "2.1.1"  # freeze fix + SettingWithCopyWarning fix
WINDOW_SIZE = "1200x700"

# Path config.json di root project
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"

# --- Freeze-fix konstanta ---------------------------------------------------
# Batch log writes untuk hindari UI not-responding saat pipeline cetak banyak log.
MAX_CHUNKS_PER_POLL = 200       # max chunks diproses per poll cycle
MAX_CHARS_PER_POLL = 50000      # max karakter di-append per poll (cap buffer)
MAX_LOG_LINES = 3000            # max baris di Text widget (truncate ke 2000 setelahnya)
LOG_POLL_INTERVAL_MS = 100     # interval poll (was 80 — sedikit lebih lama, lebih efisien)


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


# --- Aplikasi utama ---------------------------------------------------------
class StockMonitorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(900, 600)

        # State
        self.log_queue: queue.Queue = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.is_running = False
        # FIX: stop_event actually interrupts pipeline at checkpoints (was placebo)
        self.stop_event = threading.Event()
        self.append1_df = None
        self.rincian_po_df = None
        # FIX: track log line count for efficient truncation (was no limit)
        self._log_line_count = 0

        # Style ttk
        self._setup_style()

        # Build UI
        self._build_footer()
        self._build_notebook()

        # Redirect stdout/stderr ke queue
        sys.stdout = StreamToQueue(self.log_queue)
        sys.stderr = StreamToQueue(self.log_queue)

        # Poll queue untuk update log (FIX: batched, throttled)
        self._poll_log_queue()

        # Load config awal ke tab Config
        self._load_config_to_form()

    # --- Style --------------------------------------------------------------
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", padding=6)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=4)
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("TNotebook", tabmargins=(4, 4, 4, 0))
        style.configure("TNotebook.Tab", padding=(14, 6), font=("Segoe UI", 10))
        style.configure("Footer.TLabel", font=("Segoe UI", 9), foreground="#666")
        # Treeview font + row height for better readability
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=22)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    # --- Footer -------------------------------------------------------------
    def _build_footer(self):
        footer = ttk.Frame(self.root)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(footer, orient="horizontal").pack(fill=tk.X)
        ttk.Label(
            footer,
            text=f"Stock Monitoring - Python Edition  |  v{APP_VERSION}  |  7 tabs: Config • Proses • Pivot • DEVIASI GR • DEVIASI PCS • LAPORAN DEVIASI • Rincian PO",
            style="Footer.TLabel",
        ).pack(anchor="w", padx=8, pady=4)

    # --- Notebook + 7 tab ---------------------------------------------------
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=6, pady=6)

        self.tab_config = ttk.Frame(self.notebook)
        self.tab_proses = ttk.Frame(self.notebook)
        self.tab_pivot = ttk.Frame(self.notebook)
        self.tab_deviasi_gr = ttk.Frame(self.notebook)
        self.tab_deviasi_pcs = ttk.Frame(self.notebook)
        self.tab_laporan = ttk.Frame(self.notebook)  # LAPORAN DEVIASI tab
        self.tab_rincian = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_config, text="Config")
        self.notebook.add(self.tab_proses, text="Proses")
        self.notebook.add(self.tab_pivot, text="Pivot Table")
        self.notebook.add(self.tab_deviasi_gr, text="DEVIASI GR")
        self.notebook.add(self.tab_deviasi_pcs, text="DEVIASI PCS")
        self.notebook.add(self.tab_laporan, text="LAPORAN DEVIASI")
        self.notebook.add(self.tab_rincian, text="Rincian PO")

        self._build_config_tab()
        self._build_proses_tab()
        self._build_pivot_tab()
        self._build_deviasi_gr_tab()
        self._build_deviasi_pcs_tab()
        self._build_laporan_tab()
        self._build_rincian_tab()

    # --- TAB: Config --------------------------------------------------------
    def _build_config_tab(self):
        tab = self.tab_config

        ttk.Label(tab, text="Konfigurasi Path", style="Header.TLabel").pack(
            anchor="w", pady=(0, 6))
        ttk.Label(
            tab,
            text="Ubah RootPath sesuai lokasi folder data Anda. Folder & sheet name HARUS sesuai export Accurate Online.",
            wraplength=900, justify="left",
        ).pack(anchor="w", pady=(0, 10))

        form = ttk.Frame(tab)
        form.pack(fill=tk.X)

        ttk.Label(form, text="RootPath:").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.rootpath_var = tk.StringVar()
        self.entry_rootpath = ttk.Entry(form, textvariable=self.rootpath_var)
        self.entry_rootpath.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        btn_browse = ttk.Button(form, text="Browse...", command=self._browse_folder)
        btn_browse.grid(row=0, column=2, padx=4, pady=4)

        form.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="Simpan Config", command=self._save_config).pack(
            side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frame, text="Reload Config", command=self._load_config_to_form).pack(
            side=tk.LEFT)

        # LightMode toggle
        self.lightmode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            btn_frame, text="LightMode (ringan: skip bulan lalu, filter DEVIASI)",
            variable=self.lightmode_var,
        ).pack(side=tk.LEFT, padx=(20, 0))

        # Info read-only: Folders & Sheets
        info = ttk.LabelFrame(tab, text="Info Config (read-only)")
        info.pack(fill="both", expand=True, pady=(6, 0))

        self.info_text = tk.Text(
            info, height=12, wrap="word", relief="flat", background="#f5f5f5")
        self.info_text.pack(side=tk.LEFT, fill="both", expand=True, padx=4, pady=4)
        info_scroll = ttk.Scrollbar(info, command=self.info_text.yview)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.configure(yscrollcommand=info_scroll.set, state="disabled")

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
            self._set_info_text("[ERROR] config.json tidak ditemukan di:\n" + str(CONFIG_PATH))
            self.rootpath_var.set("")
            return
        except json.JSONDecodeError as e:
            self._set_info_text(f"[ERROR] config.json rusak (JSON invalid):\n{e}")
            self.rootpath_var.set("")
            return

        self.rootpath_var.set(data.get("RootPath", ""))
        self.lightmode_var.set(data.get("LightMode", True))

        folders = data.get("Folders", {})
        sheets = data.get("Sheets", {})

        lines = ["== Folders =="]
        for k, v in folders.items():
            lines.append(f"  {k:18s} -> {v}")
        lines.append("")
        lines.append("== Sheets ==")
        for k, v in sheets.items():
            lines.append(f"  {k:18s} -> {v}")
        lines.append("")
        lines.append(f"== LightMode: {data.get('LightMode', True)} ==")

        self._set_info_text("\n".join(lines))

    def _set_info_text(self, text: str):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", text)
        self.info_text.configure(state="disabled")

    def _save_config(self):
        new_root = self.rootpath_var.get().strip()
        if not new_root:
            messagebox.showwarning("Validasi", "RootPath tidak boleh kosong.", parent=self.root)
            return

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError as e:
            messagebox.showerror("Config Rusak",
                f"config.json tidak bisa dibaca (JSON invalid):\n{e}", parent=self.root)
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
            messagebox.showerror("Gagal Simpan", f"Tidak bisa menulis config.json:\n{e}", parent=self.root)
            return

        messagebox.showinfo("Berhasil",
            f"Config disimpan.\n\nRootPath: {new_root}\nLightMode: {data['LightMode']}",
            parent=self.root)
        self._load_config_to_form()

    # --- TAB: Proses --------------------------------------------------------
    def _build_proses_tab(self):
        tab = self.tab_proses

        top = ttk.Frame(tab)
        top.pack(fill=tk.X, pady=(0, 6))

        self.btn_mulai = ttk.Button(
            top, text="MULAI PROSES", style="Big.TButton", command=self._start_pipeline)
        self.btn_mulai.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = ttk.Button(
            top, text="Stop", state="disabled", command=self._stop_pipeline)
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        self.btn_bersih = ttk.Button(
            top, text="Bersihkan Log", command=self._clear_log)
        self.btn_bersih.pack(side=tk.LEFT, padx=4)

        self.btn_export = ttk.Button(
            top, text="Export ke Excel", state="disabled", command=self._export_excel)
        self.btn_export.pack(side=tk.LEFT, padx=4)

        prog_frame = ttk.Frame(tab)
        prog_frame.pack(fill=tk.X, pady=(0, 6))
        self.status_var = tk.StringVar(value="Status: siap.")
        ttk.Label(prog_frame, textvariable=self.status_var).pack(anchor="w")
        self.progress = ttk.Progressbar(prog_frame, mode="indeterminate", orient="horizontal")
        self.progress.pack(fill=tk.X, pady=(2, 0))

        log_frame = ttk.LabelFrame(tab, text="Log Proses")
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", height=14, font=("Consolas", 10))
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True, padx=4, pady=4)
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scroll.set, state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._log_line_count = 0  # FIX: reset counter

    # =========================================================================
    # FREEZE FIX: _append_log_batched — batch semua chunks jadi 1 string,
    # lalu lakukan 1 insert + 1 see(tk.END). Hindari ribuan Tcl calls per poll.
    # Plus: truncate Text widget kalau sudah > MAX_LOG_LINES baris.
    # =========================================================================
    def _append_log_batched(self, text: str):
        """FIX: Append batch text to log widget dengan truncation otomatis."""
        if not text:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text)

        # Hitung baris baru untuk tracking
        new_lines = text.count("\n")
        self._log_line_count += new_lines

        # Truncate kalau terlalu banyak baris (hapus baris awal, simpan terakhir)
        if self._log_line_count > MAX_LOG_LINES:
            # Hapus 1000 baris pertama
            self.log_text.delete("1.0", "1001.0")
            self._log_line_count -= 1000

        # Hanya 1 see(tk.END) per batch (sebelumnya 1 per chunk = expensive)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _poll_log_queue(self):
        """FIX: batch log writes — ambil semua chunks dari queue (dengan cap),
        gabungkan jadi 1 string, lalu lakukan 1 insert. Hindari UI freeze.
        """
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
            batch_text = "".join(chunks)
            self._append_log_batched(batch_text)

        # Schedule next poll (sedikit lebih lama = 100ms, lebih efisien dari 80ms)
        self.root.after(LOG_POLL_INTERVAL_MS, self._poll_log_queue)

    def _start_pipeline(self):
        if self.is_running:
            messagebox.showinfo("Sedang Berjalan",
                "Pipeline sedang berjalan. Tunggu hingga selesai atau klik Stop.", parent=self.root)
            return

        if not CONFIG_PATH.exists():
            messagebox.showerror("Config Tidak Ada",
                f"config.json tidak ditemukan:\n{CONFIG_PATH}", parent=self.root)
            return

        self.notebook.select(self.tab_proses)
        self.is_running = True
        self.stop_event.clear()  # FIX: reset stop flag
        self.btn_mulai.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_export.configure(state="disabled")
        self.status_var.set("Status: menjalankan pipeline...")
        self.progress.start(12)

        self._append_log_batched("\n" + "=" * 60 + "\n")
        self._append_log_batched("  Memulai pipeline...\n")

        self.worker_thread = threading.Thread(
            target=self._run_pipeline_worker, daemon=True)
        self.worker_thread.start()

    def _run_pipeline_worker(self):
        """Worker thread: jalankan run_pipeline, tangkap error.
        FIX: pass stop_event to run_pipeline."""
        try:
            append1_df, rincian_po_df = run_pipeline(
                verbose=True, stop_event=self.stop_event)
            self.append1_df = append1_df
            self.rincian_po_df = rincian_po_df
            self.root.after(0, lambda: self._on_pipeline_done(append1_df, rincian_po_df, None))
        except PipelineStopped as e:
            self.root.after(0, lambda: self._on_pipeline_done(None, None, (e, None)))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.root.after(0, lambda: self._on_pipeline_done(None, None, (e, tb)))

    def _on_pipeline_done(self, append1_df, rincian_po_df, error):
        """Dijadwalkan ke main thread via after()."""
        self.progress.stop()
        self.is_running = False
        self.btn_mulai.configure(state="normal")
        self.btn_stop.configure(state="disabled")

        # FIX: handle PipelineStopped (user-initiated) gracefully
        if error is not None:
            exc, tb = error
            if isinstance(exc, PipelineStopped):
                self.status_var.set("Status: DIHENTIKAN oleh user.")
                self._append_log_batched(f"\n[STOP] {exc}\n")
                return
            self.status_var.set("Status: ERROR.")
            self._append_log_batched("\n[ERROR] Pipeline gagal:\n")
            self._append_log_batched(str(exc) + "\n")
            if tb:
                self._append_log_batched("\n" + tb + "\n")
            messagebox.showerror("Pipeline Gagal",
                f"Terjadi error:\n{exc}\n\nLihat log di tab Proses untuk detail.",
                parent=self.root)
            return

        # Sukses — load data into pivot + rincian views
        self.status_var.set("Status: SELESAI.")
        self._append_log_batched(f"\n  Append1: {len(append1_df)} rows\n")
        self._append_log_batched(f"  Rincian PO: {len(rincian_po_df)} rows\n")

        # Load data into views
        self.pivot_view.load_data(append1_df)
        self.deviasi_gr_view.load_data(append1_df)
        self.deviasi_pcs_view.load_data(append1_df)
        self.laporan_view.load_data(append1_df)
        self.rincian_view.load_data(rincian_po_df)
        self.btn_export.configure(state="normal")

        # Switch to Pivot Table tab (default view)
        self.notebook.select(self.tab_pivot)

        messagebox.showinfo("Selesai",
            f"Pipeline selesai.\n\nAppend1: {len(append1_df)} rows\nRincian PO: {len(rincian_po_df)} rows\n\n"
            f"Lihat data di tab Pivot Table, DEVIASI GR, DEVIASI PCS, LAPORAN DEVIASI & Rincian PO.",
            parent=self.root)

    def _stop_pipeline(self):
        """Stop the pipeline (graceful — sets stop_event, pipeline checks it
        at major checkpoints and raises PipelineStopped)."""
        if not self.is_running:
            return
        self.stop_event.set()
        self.is_running = False
        self.btn_stop.configure(state="disabled")
        self.status_var.set("Status: menghentikan pipeline...")
        self._append_log_batched("\n[STOP] Permintaan stop dikirim. Pipeline akan berhenti di checkpoint berikutnya.\n")

    def _export_excel(self):
        """Export current data (Append1 + Rincian PO) to Excel."""
        if self.append1_df is None and self.rincian_po_df is None:
            messagebox.showwarning("Export", "Belum ada data. Jalankan pipeline dulu.", parent=self.root)
            return
        filepath = filedialog.asksaveasfilename(
            title="Simpan sebagai Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="stock_monitoring_export.xlsx",
        )
        if not filepath:
            return
        try:
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                if self.append1_df is not None and not self.append1_df.empty:
                    self.append1_df.to_excel(writer, sheet_name="Append1", index=False)
                if self.rincian_po_df is not None and not self.rincian_po_df.empty:
                    self.rincian_po_df.to_excel(writer, sheet_name="Rincian PO", index=False)
            messagebox.showinfo("Export Berhasil", f"Data di-export ke:\n{filepath}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Export Gagal", f"Tidak bisa export:\n{e}", parent=self.root)

    # --- TAB: Pivot Table ---------------------------------------------------
    def _build_pivot_tab(self):
        self.pivot_view = PivotTableView(self.tab_pivot)
        self.pivot_view.pack(fill="both", expand=True)

    # --- TAB: DEVIASI GR ----------------------------------------------------
    def _build_deviasi_gr_tab(self):
        self.deviasi_gr_view = DeviasiView(self.tab_deviasi_gr, satuan_mode="GR")
        self.deviasi_gr_view.pack(fill="both", expand=True)

    # --- TAB: DEVIASI PCS ---------------------------------------------------
    def _build_deviasi_pcs_tab(self):
        self.deviasi_pcs_view = DeviasiView(self.tab_deviasi_pcs, satuan_mode="PCS")
        self.deviasi_pcs_view.pack(fill="both", expand=True)

    # --- TAB: LAPORAN DEVIASI -----------------------------------------------
    def _build_laporan_tab(self):
        """Long-format daily audit with 6-way Status Audit classification."""
        self.laporan_view = LaporanDeviasiView(self.tab_laporan)
        self.laporan_view.pack(fill="both", expand=True)

    # --- TAB: Rincian PO ----------------------------------------------------
    def _build_rincian_tab(self):
        self.rincian_view = RincianPoView(self.tab_rincian)
        self.rincian_view.pack(fill="both", expand=True)


# --- Entry point ------------------------------------------------------------
def main():
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
