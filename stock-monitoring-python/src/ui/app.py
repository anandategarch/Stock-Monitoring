"""
app.py — Tkinter UI untuk Stock Monitoring - Python Edition.

3 tab:
  1. Config  : lihat & ubah RootPath, simpan ke config.json
  2. Proses  : tombol MULAI PROSES, log real-time, progress
  3. Output  : lihat path output, Buka File / Buka Folder

Jalankan dengan:
    python -m src.ui.app

Pipeline dijalankan di thread terpisah supaya UI tidak freeze.
Log stdout dipipakan ke Text widget lewat queue (thread-safe).
"""
import os
import sys
import json
import queue
import threading
import subprocess
import warnings
from pathlib import Path

# Suppress openpyxl noise warnings (no default style, etc.)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Pastikan parent folder di sys.path agar `from src...` jalan
# saat dijalankan sebagai `python -m src.ui.app`
_BASE = Path(__file__).resolve().parent.parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

from src.config import Config
from src.main import run_pipeline

# --- Konstanta UI -----------------------------------------------------------
APP_TITLE = "Stock Monitoring - Python Edition"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "700x500"

# Path config.json di root project
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"


# --- Helper: redirect stdout ke Text widget via queue -----------------------
class StreamToQueue:
    """
    Object file-like yang menulis ke queue.
    Thread worker menulis stdout ke sini, lalu main thread poll & tampilkan.
    """

    def __init__(self, q: queue.Queue):
        self.q = q

    def write(self, s: str):
        if s:
            self.q.put(s)

    def flush(self):
        # Tidak perlu melakukan apa-apa; queue otomatis terdrain oleh after().
        pass


# --- Aplikasi utama ---------------------------------------------------------
class StockMonitorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(600, 420)

        # State
        self.log_queue: queue.Queue = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.is_running = False
        self.output_path: str | None = None

        # Style ttk
        self._setup_style()

        # Build UI
        self._build_footer()
        self._build_notebook()

        # Redirect stdout/stderr ke queue
        sys.stdout = StreamToQueue(self.log_queue)
        sys.stderr = StreamToQueue(self.log_queue)

        # Poll queue untuk update log
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

        style.configure("TFrame", padding=8)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=4)
        style.configure(
            "Big.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=10,
        )
        style.configure("TNotebook", tabmargins=(4, 4, 4, 0))
        style.configure("TNotebook.Tab", padding=(14, 6), font=("Segoe UI", 10))
        style.configure("Footer.TLabel", font=("Segoe UI", 9), foreground="#666")

    # --- Footer -------------------------------------------------------------
    def _build_footer(self):
        footer = ttk.Frame(self.root)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(footer, orient="horizontal").pack(fill=tk.X)
        ttk.Label(
            footer,
            text=f"Stock Monitoring - Python Edition  |  v{APP_VERSION}  |  Pipeline: build_append1 + rincian_po -> Excel",
            style="Footer.TLabel",
        ).pack(anchor="w", padx=8, pady=4)

    # --- Notebook + 3 tab ---------------------------------------------------
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=6, pady=6)

        self.tab_config = ttk.Frame(self.notebook)
        self.tab_proses = ttk.Frame(self.notebook)
        self.tab_output = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_config, text="Config")
        self.notebook.add(self.tab_proses, text="Proses")
        self.notebook.add(self.tab_output, text="Output")

        self._build_config_tab()
        self._build_proses_tab()
        self._build_output_tab()

    # --- TAB: Config --------------------------------------------------------
    def _build_config_tab(self):
        tab = self.tab_config

        ttk.Label(tab, text="Konfigurasi Path", style="Header.TLabel").pack(
            anchor="w", pady=(0, 6)
        )
        ttk.Label(
            tab,
            text="Ubah RootPath sesuai lokasi folder data Anda. Folder & sheet name HARUS sesuai export Accurate Online.",
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        form = ttk.Frame(tab)
        form.pack(fill=tk.X)

        ttk.Label(form, text="RootPath:").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=4
        )
        self.rootpath_var = tk.StringVar()
        self.entry_rootpath = ttk.Entry(form, textvariable=self.rootpath_var)
        self.entry_rootpath.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        btn_browse = ttk.Button(form, text="Browse...", command=self._browse_folder)
        btn_browse.grid(row=0, column=2, padx=4, pady=4)

        form.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(
            btn_frame, text="Simpan Config", command=self._save_config
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            btn_frame, text="Reload Config", command=self._load_config_to_form
        ).pack(side=tk.LEFT)

        # Info read-only: Folders & Sheets
        info = ttk.LabelFrame(tab, text="Info Config (read-only)")
        info.pack(fill="both", expand=True, pady=(6, 0))

        self.info_text = tk.Text(
            info, height=10, wrap="word", relief="flat", background="#f5f5f5"
        )
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
        """Baca config.json dan tampilkan ke form. Handle missing/malformed."""
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

        # Tampilkan ringkasan Folders & Sheets
        folders = data.get("Folders", {})
        sheets = data.get("Sheets", {})
        output = data.get("Output", {})

        lines = []
        lines.append("== Folders ==")
        for k, v in folders.items():
            lines.append(f"  {k:18s} -> {v}")
        lines.append("")
        lines.append("== Sheets ==")
        for k, v in sheets.items():
            lines.append(f"  {k:18s} -> {v}")
        lines.append("")
        lines.append("== Output ==")
        for k, v in output.items():
            lines.append(f"  {k:18s} -> {v}")

        self._set_info_text("\n".join(lines))

    def _set_info_text(self, text: str):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", text)
        self.info_text.configure(state="disabled")

    def _save_config(self):
        """Simpan RootPath baru ke config.json, preserve section lain."""
        new_root = self.rootpath_var.get().strip()
        if not new_root:
            messagebox.showwarning(
                "Validasi", "RootPath tidak boleh kosong.", parent=self.root
            )
            return

        # Baca config lama
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError as e:
            messagebox.showerror(
                "Config Rusak",
                f"config.json tidak bisa dibaca (JSON invalid):\n{e}\n\n"
                "Perbaiki manual dulu, atau hapus file lalu restart app.",
                parent=self.root,
            )
            return

        # Update RootPath
        data["RootPath"] = new_root

        # Backup dulu
        backup_path = CONFIG_PATH.with_suffix(".json.bak")
        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # backup gagal tidak fatal

        # Tulis ulang
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror(
                "Gagal Simpan", f"Tidak bisa menulis config.json:\n{e}", parent=self.root
            )
            return

        messagebox.showinfo(
            "Berhasil",
            f"RootPath disimpan:\n{new_root}\n\nBackup: {backup_path.name}",
            parent=self.root,
        )
        self._load_config_to_form()

    # --- TAB: Proses --------------------------------------------------------
    def _build_proses_tab(self):
        tab = self.tab_proses

        top = ttk.Frame(tab)
        top.pack(fill=tk.X, pady=(0, 6))

        self.btn_mulai = ttk.Button(
            top, text="MULAI PROSES", style="Big.TButton", command=self._start_pipeline
        )
        self.btn_mulai.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_bersih = ttk.Button(
            top, text="Bersihkan Log", command=self._clear_log
        )
        self.btn_bersih.pack(side=tk.LEFT, padx=4)

        # Progress bar + label status
        prog_frame = ttk.Frame(tab)
        prog_frame.pack(fill=tk.X, pady=(0, 6))
        self.status_var = tk.StringVar(value="Status: siap.")
        ttk.Label(prog_frame, textvariable=self.status_var).pack(anchor="w")
        self.progress = ttk.Progressbar(
            prog_frame, mode="indeterminate", orient="horizontal"
        )
        self.progress.pack(fill=tk.X, pady=(2, 0))

        # Log area
        log_frame = ttk.LabelFrame(tab, text="Log Proses")
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame, wrap="word", height=14, font=("Consolas", 10)
        )
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True, padx=4, pady=4)
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scroll.set, state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def _append_log(self, text: str):
        """Append text ke log widget (dipanggil dari main thread)."""
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _poll_log_queue(self):
        """Drain queue dan append ke log widget. Dipanggil periodik oleh after()."""
        try:
            while True:
                chunk = self.log_queue.get_nowait()
                self._append_log(chunk)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_log_queue)

    def _start_pipeline(self):
        if self.is_running:
            messagebox.showinfo(
                "Sedang Berjalan",
                "Pipeline sedang berjalan. Tunggu hingga selesai.",
                parent=self.root,
            )
            return

        # Validasi config ada
        if not CONFIG_PATH.exists():
            messagebox.showerror(
                "Config Tidak Ada",
                f"config.json tidak ditemukan:\n{CONFIG_PATH}\n\n"
                "Buat / perbaiki di tab Config.",
                parent=self.root,
            )
            return

        # Switch ke tab Proses & mulai
        self.notebook.select(self.tab_proses)
        self.is_running = True
        self.btn_mulai.configure(state="disabled")
        self.status_var.set("Status: menjalankan pipeline...")
        self.progress.start(12)

        self._append_log("\n" + "=" * 60 + "\n")
        self._append_log("  Memulai pipeline...\n")

        self.worker_thread = threading.Thread(
            target=self._run_pipeline_worker, daemon=True
        )
        self.worker_thread.start()

    def _run_pipeline_worker(self):
        """Worker thread: jalankan run_pipeline, tangkap error."""
        try:
            result_path = run_pipeline(verbose=True)
            self.output_path = result_path
            self.root.after(0, lambda: self._on_pipeline_done(result_path, None))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.root.after(0, lambda: self._on_pipeline_done(None, (e, tb)))

    def _on_pipeline_done(self, result_path, error):
        """Dijadwalkan ke main thread via after()."""
        self.progress.stop()
        self.is_running = False
        self.btn_mulai.configure(state="normal")

        if error is not None:
            exc, tb = error
            self.status_var.set("Status: ERROR.")
            self._append_log("\n[ERROR] Pipeline gagal:\n")
            self._append_log(str(exc) + "\n")
            self._append_log("\n" + tb + "\n")
            messagebox.showerror(
                "Pipeline Gagal",
                f"Terjadi error:\n{exc}\n\nLihat log di tab Proses untuk detail.",
                parent=self.root,
            )
            return

        # Sukses
        self.status_var.set("Status: SELESAI.")
        self._append_log("\n  Output dihasilkan:\n")
        self._append_log(f"  {result_path}\n")

        # Update tab Output
        self._refresh_output_tab(result_path)

        messagebox.showinfo(
            "Selesai",
            f"Pipeline selesai.\n\nOutput:\n{result_path}",
            parent=self.root,
        )

    # --- TAB: Output --------------------------------------------------------
    def _build_output_tab(self):
        tab = self.tab_output

        ttk.Label(tab, text="Output File", style="Header.TLabel").pack(
            anchor="w", pady=(0, 6)
        )
        ttk.Label(
            tab,
            text="File Excel hasil pipeline. Berisi pivot tables + slicers (sama persis dengan template).",
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        out_frame = ttk.LabelFrame(tab, text="Path Output")
        out_frame.pack(fill=tk.X, pady=(0, 8))

        self.output_path_var = tk.StringVar(value="(belum ada — jalankan proses dulu)")
        ttk.Label(out_frame, textvariable=self.output_path_var, wraplength=640).pack(
            anchor="w", padx=8, pady=8
        )

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=4)
        self.btn_buka_file = ttk.Button(
            btn_frame, text="Buka File", command=self._buka_file, state="disabled"
        )
        self.btn_buka_file.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_buka_folder = ttk.Button(
            btn_frame, text="Buka Folder", command=self._buka_folder, state="disabled"
        )
        self.btn_buka_folder.pack(side=tk.LEFT, padx=4)
        ttk.Button(
            btn_frame, text="Pilih File Lain...", command=self._pilih_file_lain
        ).pack(side=tk.LEFT, padx=4)

        # Hint
        ttk.Label(
            tab,
            text="Tips: jika tombol tidak aktif, jalankan pipeline di tab Proses dulu.",
            style="Footer.TLabel",
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

    def _refresh_output_tab(self, path: str):
        self.output_path = path
        self.output_path_var.set(path)
        if path and os.path.exists(path):
            self.btn_buka_file.configure(state="normal")
            self.btn_buka_folder.configure(state="normal")
        else:
            self.btn_buka_file.configure(state="disabled")
            self.btn_buka_folder.configure(state="disabled")

    def _pilih_file_lain(self):
        path = filedialog.askopenfilename(
            title="Pilih file output Excel",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if path:
            self._refresh_output_tab(path)

    def _buka_file(self):
        if not self.output_path or not os.path.exists(self.output_path):
            messagebox.showwarning(
                "File Tidak Ada",
                f"File tidak ditemukan:\n{self.output_path}",
                parent=self.root,
            )
            return
        self._open_path(self.output_path)

    def _buka_folder(self):
        if not self.output_path:
            return
        folder = os.path.dirname(self.output_path) or "."
        if not os.path.isdir(folder):
            messagebox.showwarning(
                "Folder Tidak Ada",
                f"Folder tidak ditemukan:\n{folder}",
                parent=self.root,
            )
            return

        # Buka folder, di Windows highlight file via explorer select
        if os.name == "nt":
            try:
                subprocess.Popen(
                    ["explorer", f"/select,{os.path.normpath(self.output_path)}"]
                )
                return
            except Exception:
                pass
        # Fallback: buka folder saja
        self._open_path(folder)

    def _open_path(self, path: str):
        """Buka file/folder cross-platform."""
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror(
                "Gagal Membuka", f"Tidak bisa membuka:\n{path}\n\n{e}", parent=self.root
            )


# --- Entry point ------------------------------------------------------------
def main():
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
