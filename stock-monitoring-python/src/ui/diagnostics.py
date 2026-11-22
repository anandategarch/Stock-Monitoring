"""diagnostics.py — observabilitas persisten: log file rotasi + crash.log
ber-timestamp + excepthook global (v3.15).

MENGAPA MODUL INI ADA (audit gap-analysis eksternal, temuan F1/F2):
- Semua log pipeline dulu hanya hidup di RAM (Text widget tab 🚀 Proses,
  dipangkas 3000→2000 baris) — app ditutup → seluruh jejak run hilang;
  4 modul sudah memakai ``logging`` tapi TAK SATUPUN handler terpasang
  (record _LOG.debug/info lenyap total). Laporan bug ke developer tanpa
  bukti tertinggal di disk.
- crash.log dulu hanya menangkap kegagalan startup (import / main()) dan
  DITIMPA tiap kejadian — crash beruntun saling menimpa jejak; exception
  runtime di callback Tk / thread hanya di-print ke konsol UI.

PERILAKU (v3.15):
- ``logs/app.log`` — RotatingFileHandler 2 MB × 3 backup, UTF-8, di
  ``app_base_dir()/logs/`` (frozen-aware: di samping .exe; DEV = root
  proyek — folder di-ignore .gitignore). Handler dipasang di ROOT logger
  → record ``logging`` dari modul mana pun + warning Python
  (captureWarnings) ikut tercatat.
- MIRROR KONSOL: StreamToQueue (redirect stdout/stderr app) menulis
  BARENG ke queue UI dan ke sini — log run pipeline utuh di disk,
  baris-utuh (buffer sampai newline), anti-rekursi (guard thread-local:
  error di dalam logging sendiri tidak boleh memicu logging lagi).
- crash.log — APPEND per-kejadian dgn header timestamp + versi + pid
  (tidak lagi menimpa). Sumber: excepthook utama, excepthook thread,
  callback Tk (report_callback_exception — tkinter merutekan callback
  SEMUA widget ke root), dan main() startup. Launcher (run_app.py /
  src.ui.__main__) TETAP stdlib-murni dgn writer append sendiri — jalur
  itu justru harus hidup saat modul proyek gagal di-import.
- IDEMPOTEN: setup dipanggil tiap StockMonitorApp dibuat (suite test
  membuat app puluhan kali) → handler tidak dobel; base_dir pindah →
  handler lama diganti. Best-effort total: kegagalan menulis log tidak
  boleh menjatuhkan app (pola repo: suppress, jangan masking error asli).
"""
import contextlib
import logging
import os
import sys
import threading
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "app.log"
LOG_MAX_BYTES = 2_000_000
LOG_BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
_MIRROR_LOGGER = "stockmonitor.mirror"

_state_lock = threading.Lock()
_handler: RotatingFileHandler | None = None
_base_dir: Path | None = None
_app_version: str | None = None
_hooks_installed = False

# Guard anti-rekursi mirror: logging bisa menulis ke stderr (raiseExceptions
# / lastResort) — bila stderr = StreamToQueue → mirror_text lagi → loop.
# Flag thread-local (bukan global): thread lain boleh tetap mirror.
_mirror_tls = threading.local()
_mirror_lock = threading.Lock()
_mirror_buf: list[str] = []

# Hook asli dirantai SETELAH jejak tertulis — perilaku default (print ke
# stderr / propagasi) tidak berubah, hanya DITAMBAHI jejak file.
_orig_sys_excepthook = sys.excepthook
_orig_thread_excepthook = threading.excepthook


def setup_diagnostics(base_dir: Path | str,
                      app_version: str | None = None) -> logging.Logger | None:
    """Pasang log file rotasi + excepthook global (idempoten).

    Dipanggil StockMonitorApp.__init__ PERTAMA (sebelum redirect konsol).
    Gagal membuat file/folder log → None (app tetap jalan penuh — log
    disk adalah best-effort, bukan dependensi).
    """
    global _handler, _base_dir, _app_version, _hooks_installed
    base = Path(base_dir)
    with _state_lock:
        if app_version:
            _app_version = app_version
        if _handler is not None and _base_dir == base:
            return logging.getLogger()          # sudah terpasang — no-op
        # Base pindah (rekonfigurasi): lepas handler lama TANPA
        # menyentuh handler pihak lain di root logger.
        if _handler is not None:
            with contextlib.suppress(Exception):
                logging.getLogger().removeHandler(_handler)
            with contextlib.suppress(Exception):
                _handler.close()
            _handler = None
        try:
            log_dir = base / LOG_DIR_NAME
            log_dir.mkdir(parents=True, exist_ok=True)
            _handler = RotatingFileHandler(
                log_dir / LOG_FILE_NAME, maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
            _handler.setFormatter(logging.Formatter(LOG_FORMAT))
            root = logging.getLogger()
            root.addHandler(_handler)
            root.setLevel(logging.INFO)
            _base_dir = base
            logging.captureWarnings(True)
        except Exception:  # noqa: BLE001 — setup best-effort: gagal apa
            _handler = None      # pun (disk read-only/penuh) → app tetap
            _base_dir = None     # jalan penuh, log disk bukan dependensi
            return None
    if not _hooks_installed:
        _hooks_installed = True
        sys.excepthook = _sys_excepthook
        threading.excepthook = _thread_excepthook
    return logging.getLogger()


def mirror_text(text: str) -> None:
    """Mirror satu fragmen stdout/stderr konsol UI ke log file.

    Baris-utuh: fragmen di-buffer sampai newline (print() memanggil
    write() dua kali — teks, lalu karakter newline). Dijauhkan dari
    rekursi via guard thread-local; kegagalan apa pun ditelan (konsol
    UI adalah sumber kebenaran primer, file hanya salinan).
    """
    if not text or _handler is None:
        return
    if getattr(_mirror_tls, "busy", False):
        return
    _mirror_tls.busy = True
    try:
        with _mirror_lock:
            _mirror_buf.append(text)
            if "\n" not in text:
                return
            chunk = "".join(_mirror_buf)
            _mirror_buf.clear()
            with contextlib.suppress(Exception):
                for line in chunk.splitlines():
                    if line.strip():
                        logging.getLogger(_MIRROR_LOGGER).info(line)
    finally:
        _mirror_tls.busy = False


def log_crash(kind: str, tb_text: str,
              base_dir: Path | str | None = None) -> None:
    """Append jejak crash ke crash.log (header timestamp, versi, pid) +
    mirror ke app.log. Best-effort total — tidak boleh raise (dipanggil
    dari jalur error; exception kedua akan masking error asli)."""
    base = Path(base_dir) if base_dir is not None else _base_dir
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    head = (f"\n===== [{ts}] {kind}"
            + (f" — v{_app_version}" if _app_version else "")
            + f" — pid {os.getpid()} =====\n")
    body = tb_text if tb_text.endswith("\n") else tb_text + "\n"
    if base is not None:
        with contextlib.suppress(Exception), \
                open(base / "crash.log", "a", encoding="utf-8") as f:
            f.write(head + body)
    if _handler is not None:
        with contextlib.suppress(Exception):
            logging.getLogger().error("CRASH %s\n%s", kind, tb_text.strip())


def log_callback_exception(exc_type, exc_value, exc_tb) -> None:
    """report_callback_exception Tk (dipasang di instance root app —
    tkinter merutekan _report_exception SEMUA widget ke root).

    Menambah jejak persisten (app.log + crash.log) TANPA mengubah
    perilaku default Tkinter (print "Exception in Tkinter callback" +
    traceback ke stderr + sys.last_* — persis implementasi bawaan;
    stderr app = StreamToQueue → konsol UI + mirror file)."""
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_crash("EXCEPTION callback Tk", tb_text)
    with contextlib.suppress(Exception):
        sys.last_exc = exc_value
        sys.last_type = exc_type
        sys.last_value = exc_value
        sys.last_traceback = exc_tb
        print("Exception in Tkinter callback", file=sys.stderr)
        sys.stderr.write(tb_text if tb_text.endswith("\n")
                         else tb_text + "\n")


def _sys_excepthook(exc_type, exc_value, exc_tb) -> None:
    """sys.excepthook global: exception utama TIDAK TERTANGKAP kini
    meninggalkan jejak file sebelum perilaku default. SystemExit /
    KeyboardInterrupt diteruskan tanpa crash.log (bukan crash)."""
    if not issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
        tb_text = "".join(
            traceback.format_exception(exc_type, exc_value, exc_tb))
        log_crash("EXCEPTION utama (sys.excepthook)", tb_text)
    _orig_sys_excepthook(exc_type, exc_value, exc_tb)


def _thread_excepthook(args) -> None:
    """threading.excepthook global: exception thread tak-tertangkap
    (mis. run_async) kini tercatat di file sebelum perilaku default."""
    if args.exc_type is not None and not issubclass(
            args.exc_type, (SystemExit, KeyboardInterrupt)):
        tb_text = "".join(traceback.format_exception(
            args.exc_type, args.exc_value, args.exc_traceback))
        tname = (getattr(args.thread, "name", "?")
                 if args.thread is not None else "?")
        log_crash(f"EXCEPTION thread '{tname}'", tb_text)
    _orig_thread_excepthook(args)
