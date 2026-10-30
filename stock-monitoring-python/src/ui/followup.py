"""
followup.py — Store daftar follow-up baris anomali (centang ✓ di tab
DEVIASI GR / PCS / LAPORAN DEVIASI): SNAPSHOT nilai saat dicentang,
tidak ikut filter/TANGGAL H aktif; persist followup.json (+backup .bad
utk file korup, flag last_recovery / last_save_error).

- row_fingerprint(row) = md5 identitas baris — 9 field di-join "|":
  Asal · Resto · Barang · Satuan · H · SO · Sistem · Deviasi · CEK
  (tiap part di-escape; stabil lintas sesi).
- SNAPSHOT_FIELDS = asal · resto · barang · satuan · aktif · h · so ·
  sistem · deviasi · cek · so_m2/so_m1/so_p1/so_p2 (SO tanggal H±2) ·
  loss_bom · barang_app/resto_app (nama versi APP baris KOMPARASI).
- FollowUpStore: dict {fp: snapshot} + status resolved (PIC · Cek FU ·
  Selisih · Selisih Deviasi · ts) — persist followup_resolved.json.
- auto_resolve_pending(append1_df) — dipanggil app pasca-pipeline:
  baris DEVIASI GR/PCS MENUNGGU yang deviasinya tidak ada lagi di
  data revisi → AUTO-DONE (PIC "AUTO" + auto_reason); deviasi masih
  ≠ 0 tetap MENUNGGU; entri resolved lain tak disentuh.
- export_xlsx(path) → sheet "FOLLOW UP": kolom BERHENTI di Keterangan
  (Resto · Nama Barang · SO tanggal H−2..H+2 · Sistem · Deviasi ·
  Loss Surplus to BOM · Keterangan) + number-format "#,##0;[Red](#,##0)"
  dan persen "0.00%;[Red](0.00%)"; tulis atomik.
- Modul murni — tanpa Tk saat import (dialog pemulihan lazy, GUI saja).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from ..config import app_base_dir as _app_base_dir  # v3.9.62 — frozen-aware

_LOG = logging.getLogger("stock_monitoring.followup")

# Snapshot row keys (persis kolom tabel Follow Up, tanpa ✓/status TL).
# v3.9.6 (permintaan user: "format Follow UP seperti file sample" — sheet
# Follow UP workbook asli user): snapshot diperluas — SO per tanggal
# (H-2..H+2) + Loss Surplus to BOM (= Dev to BOM% tab Deviasi).
SNAPSHOT_FIELDS = [
    "asal", "resto", "barang", "satuan", "aktif", "h",
    "so", "sistem", "deviasi", "cek",
    "so_m2", "so_m1", "so_p1", "so_p2", "loss_bom",
    # v3.9.54 (audit 8-a P1-3) — nama versi APP baris asal KOMPARASI
    # ('resto' snap = bentuk pendek ternormalisasi, 'barang' = nama FILE
    # → popup detail exact-match data app = 0 baris / popup KOSONG).
    # Snap lama tanpa field ini → fallback 'barang'/'resto' (perilaku
    # lama). TIDAK mengubah fingerprint (row_fingerprint md5 9 field).
    "barang_app", "resto_app",
]
# Kolom tanggal SO di tabel/export (posisi H relatif — heading dinamis
# menampilkan angka tanggal, mis. H=25 → 23/24/25/26/27)
DATE_COL_IDS = ["T-2", "T-1", "T", "T+1", "T+2"]

# Kolom serah-terima FU (diisi petugas follow-up di TABEL UI app) —
# mengikuti sheet Follow UP file sample: SO · DEVIASI · Selisih ·
# Selisih Deviasi · Cek FU (+ PIC utk pelacakan app).
# v3.11.4 — TIDAK lagi ikut EXPORT (user: "Setelah kolom keterangan
# kapus aja" — export berhenti di Keterangan); tetap dipakai UI tabel
# (dokumentasi kolom kerja FU — nilai resolved tetap tersimpan).
HANDOVER_COLS = ["SO", "DEVIASI", "Selisih", "Selisih Deviasi",
                  "Cek FU", "PIC"]

# Nama kolom sheet FOLLOW UP (export) — urutan PERSIS sheet Follow UP
# file sample user: Resto · Nama Barang · [SO tgl H-2..H+2] · Sistem ·
# Deviasi · Loss Surplus to BOM · Keterangan.
# v3.11.4 — BERHENTI di Keterangan (user: "Setelah kolom keterangan
# kapus aja"): kolom kerja FU + pelacakan app DIHAPUS dari export.
EXPORT_COLS = [
    "Resto", "Nama Barang",
] + DATE_COL_IDS + [
    "Sistem", "Deviasi", "Loss Surplus to BOM", "Keterangan",
]

# v3.11.4 — number-format export (user: "kolom 23 24 25 26 27 Sistem
# Deviasi pakai separator , dan tanpa desimal. kolom Loss Surplus to BOM
# pakai persen"): nilai mentah ditulis apa adanya + format tampil — pola
# export v3.11.2/3 (minus merah kurung via number-format Excel [Red],
# bukan objek Font per sel).
_INT_NUMFMT = "#,##0;[Red](#,##0)"
_PCT_NUMFMT = "0.00%;[Red](0.00%)"

# Pergeseran kolom tanggal relatif H (T-2 → h−2 … T+2 → h+2)
DATE_COL_OFFSETS = dict(zip(DATE_COL_IDS, (-2, -1, 0, 1, 2)))

CHECK_ON, CHECK_OFF = "☑", "☐"

# FIX 6d1-04 (audit 6-d1 LOW) — 7 label anomali CEK KANONIK (mirror
# deviasi_view._CEK_CHECK_LABELS — READ ONLY, jangan uba dua-duanya
# sekaligus tanpa koordinasi): snapshot 'cek' baris asal DEVIASI dapat
# berisi segmen ANALISA lalu→kini ('Berubah Arah' / 'Peningkatan
# Tertinggi +p%' / 'Penurunan Tertinggi -p%') bila baris TIDAK ber-label
# anomali — footer CEK tab Deviasi tidak menghitungnya sbg anomali.
# Display Follow Up menandainya 'Analisa: …' supaya dua tab konsisten
# (bukan tertukar dgn label anomali).
_CEK_CANONICAL_LABELS = (
    "Promix 04", "RI Balancing", "Kosong/Non Aktif", "Beda Tanggal",
    "Hitung Manual", "Turun Drastis", "ACR to BOM",
)
_ANALISA_PREFIXES = ("Berubah Arah", "Peningkatan Tertinggi",
                     "Penurunan Tertinggi")


def _cek_display_text(v) -> str:
    """FIX 6d1-04 — teks kolom Keterangan (CEK) Follow Up: label
    kanonik tampil apa adanya; segmen ANALISA diberi prefiks
    'Analisa: ' (baris tsb BUKAN anomali CEK — definisi footer/popup
    tab Deviasi); label lain (status LAPORAN-COM: MINUS / > MEDIAN /
    MINUS + > MEDIAN) tetap apa adanya — konsisten dgn tab asalnya."""
    t = str(v or "").strip()
    if not t:
        return "-"
    if t in _CEK_CANONICAL_LABELS:
        return t
    if t.startswith(_ANALISA_PREFIXES):
        return f"Analisa: {t}"
    return t

# Path (dynamis — pola config.json di app.py)
# v3.9.62 — frozen-aware (app_base_dir): mode PyInstaller → folder .exe.
_BASE = _app_base_dir()


def followup_path() -> Path:
    return _BASE / "followup.json"


def resolved_path() -> Path:
    return _BASE / "followup_resolved.json"


def _norm_num(v) -> str:
    """Normalisasi angka utk fingerprint: 5 == 5.0 == '5.0' → '5'."""
    try:
        f = float(v)
        if f == int(f):
            return str(int(f))
        return repr(round(f, 6))
    except (TypeError, ValueError):
        return "" if v is None else str(v).strip()


def _pyval(v):
    """Konversi nilai snapshot → tipe Python murni (numpy int64/float64
    → int/float; pd.NA → None) supaya JSON-serializable."""
    if v is None:
        return ""
    if v is pd.NA:
        return ""
    item = getattr(v, "item", None)   # numpy scalar / pd.Timestamp
    if callable(item):
        try:
            return v.item()
        except Exception:
            pass
    if isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def row_fingerprint(row: dict) -> str:
    """md5 identitas baris (stabil lintas sesi).

    v3.9.69 — hardening (audit eksternal ke-2, risiko rendah): tiap part
    di-ESCAPE dulu (``\\`` → ``\\\\``, ``|`` → ``\\|``) sebelum di-join —
    menutup bentrok teoretis "A|B"+"C" ≡ "A"+"B|C" (nilai memuat pipe).
    BACKWARD-COMPAT: utk data bebas-pipe (semua data nyata saat ini —
    audit: "belum terbukti di data sekarang") hash TIDAK berubah sama
    sekali, jadi followup.json lama tetap cocok; hash berubah HANYA utk
    nilai yang memang ber-pipe (yang dulu ambigu sejak awal)."""
    def _esc(v: str) -> str:
        return v.replace("\\", "\\\\").replace("|", "\\|")

    parts = [
        _esc(str(row.get("asal", "") or "").strip()),
        _esc(str(row.get("resto", "") or "").strip()),
        _esc(str(row.get("barang", "") or "").strip()),
        _esc(str(row.get("satuan", "") or "").strip()),
        _esc(_norm_num(row.get("h"))),
        _esc(_norm_num(row.get("so"))),
        _esc(_norm_num(row.get("sistem"))),
        _esc(_norm_num(row.get("deviasi"))),
        _esc(str(row.get("cek", "") or "").strip()),
    ]
    key = "|".join(parts)
    return hashlib.md5(key.encode("utf-8", "surrogatepass")).hexdigest()


def _backup_corrupt(p: Path) -> None:
    """File korup di-rename .bad (tidak hilang) — pola Waste."""
    try:
        os.replace(p, p.with_suffix(p.suffix + ".bad"))
    except OSError:
        pass


def _notify_recovery(store, p: Path, reason: str) -> None:
    """v3.9.59 — FIX 2f-07 (audit 2-f MED): pulihan file korup kini
    TERLIHAT oleh user (dulu SENYAP: file di-rename .bad + daftar mulai
    kosong tanpa pesan — _LOG.warning jatuh ke stderr yang dibuang
    pythonw/MULAI.bat, user kehilangan seluruh daftar follow-up tanpa
    tahu cadangan .bad ada).

    Tiga kanal (aman utk jalur headless/test — tanpa root Tk dialog
    TIDAK pernah dicoba):
    1. ``store.last_recovery`` = pesan ringkas — view/app (listener
       v3.9.42) bisa men-surface flash status (API utk view).
    2. print [WARNING] — stdout app dialihkan ke log internal tab 🚀
       Proses (pola save-gagal followup v3.9.42).
    3. messagebox showwarning HANYA bila root Tk default hidup (mode
       GUI; dibungkus try — store bisa dibuat sebelum mainloop/di
       thread non-main)."""
    bad = str(p) + ".bad"
    msg = (f"File {p.name} rusak ({reason}). Cadangan: {bad}. "
           "Daftar dimulai kosong.")
    if store is not None:
        store.last_recovery = msg
    print(f"[WARNING] followup: {msg}")
    try:
        import tkinter as tk
    except ImportError:
        return  # Tk tak tersedia (jalur headless) — cukup flag + log
    if getattr(tk, "_default_root", None) is None:
        return  # tanpa root default (test headless) — JANGAN dialog
    try:
        from tkinter import messagebox
        messagebox.showwarning("Follow-Up Rusak", msg)
    except (tk.TclError, RuntimeError):
        _LOG.debug("dialog followup-rusak gagal (non-main thread?)",
                   exc_info=True)


def _atomic_save(path: Path, data: dict) -> bool:
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        return True
    except OSError as e:
        _LOG.warning("gagal simpan %s: %s", path.name, e)
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        return False


class FollowUpStore:
    """Store follow-up: snapshot baris tercentang + status tindak lanjut."""

    def __init__(self):
        self.rows: dict[str, dict] = {}      # fp → snapshot
        self.resolved: dict[str, dict] = {}  # fp → {PIC, KATEGORI, TINDAKAN, ts}
        self._listeners: list = []
        # v3.9.59 — FIX 2f-07: pesan pulihan file korup TERAKHIR (None =
        # tak ada) — dibaca view/app utk flash status (lihat
        # _notify_recovery).
        self.last_recovery: str | None = None
        # v3.9.59 — FIX 2f-08: pesan gagal persist TERAKHIR (None = sehat)
        # — dibaca view/listener setelah toggle/clear (lihat toggle).
        self.last_save_error: str | None = None
        # v3.9.72 — FIX 3 (task 2-b): mode TANGGUH penulisan JSON. Toggle
        # ✓ di tab Follow Up memicu 2 tulis file SINKRON di UI thread
        # (followup.json + followup_resolved.json); rapid toggle = badai
        # I/O disk. View memasang mode ini SEKITAR toggle-nya sendiri lalu
        # menjadwalkan SATU flush debounce 200ms (after) — default tetap
        # SINKRON (toggle dari tab lain / pemanggil test tak berubah).
        self._defer_saves = False
        self._dirty_saves = False
        self.load()

    # -- sinkronisasi UI ------------------------------------------------------
    def add_listener(self, cb) -> None:
        """cb(store) dipanggil setiap perubahan (toggle/clear)."""
        if cb not in self._listeners:
            self._listeners.append(cb)

    def remove_listener(self, fn) -> None:
        """v3.9.42 — audit 61-c/61-d (F5 P3): lepas listener (defensif,
        idempoten — fn yang tak terdaftar diabaikan senyap). Store hanya
        punya add_listener: view yang di-destroy / direbuild tidak bisa
        berhenti berlangganan → callback _notify mendarat di widget mati
        (traceback noise) + listener menumpuk seumur app. API disiapkan
        utk dipakai view pemanggil add_listener saat teardown (dipanggil
        di deviasi_view / komparasi_deviasi_view — dikerjakan pusat).

        (v3.9.33 48-e FIX 11 memakai guard winfo_exists di sisi view —
        remove_listener memberi akar fix, keduanya kompatibel.)"""
        try:
            self._listeners.remove(fn)
        except ValueError:
            pass  # fn memang tak terdaftar (defensif)

    def _notify(self):
        for cb in list(self._listeners):
            try:
                cb(self)
            except Exception:
                pass

    # -- query ------------------------------------------------------------------
    def has(self, fp: str) -> bool:
        return fp in self.rows

    def __len__(self) -> int:
        return len(self.rows)

    def resolved_count(self) -> int:
        return sum(1 for fp in self.rows if fp in self.resolved)

    # -- mutasi -------------------------------------------------------------------
    def set_defer_saves(self, enabled: bool) -> None:
        """v3.9.72 — FIX 3 (task 2-b): aktif/nonaktif mode TANGGUH
        penulisan JSON (dipakai view Follow Up sekitar toggle ✓-nya
        sendiri). Saat aktif, _persist_* hanya MENANDAI dirty — penulisan
        dicatat utk SATU flush gabungan via flush_saves() (debounce
        after(200ms) milik view). Default nonaktif = perilaku lama
        (sinkron) — toggle dari tab lain / pemanggil programatik / test
        tak berubah."""
        self._defer_saves = bool(enabled)

    def flush_saves(self) -> None:
        """v3.9.72 — FIX 3: tulis followup.json + followup_resolved.json
        SEKARANG bila ada perubahan tertunda (dipanggil debounce view /
        teardown view). Gagal → flag ``last_save_error`` + [WARNING]
        (pola toggle v3.9.42/2f-08 — view men-surface flash status)."""
        if not self._dirty_saves:
            return
        self._dirty_saves = False
        ok = self.save()
        ok_r = self.save_resolved()
        self.last_save_error = None if (ok and ok_r) else (
            "gagal menyimpan status followup (file terkunci/disk?) "
            "— perubahan hanya di memori")
        if self.last_save_error:
            print(f"[WARNING] followup: {self.last_save_error}")

    def _persist_rows(self) -> bool:
        """v3.9.72 — FIX 3: satu pintu penulisan rows — sinkron default;
        mode defer = tandai dirty (flush via flush_saves, hasil optimistik
        True — kegagalan dilaporkan saat flush)."""
        if self._defer_saves:
            self._dirty_saves = True
            return True
        return self.save()

    def _persist_resolved(self) -> bool:
        """v3.9.72 — FIX 3: idem _persist_rows utk followup_resolved.json."""
        if self._defer_saves:
            self._dirty_saves = True
            return True
        return self.save_resolved()

    def toggle(self, fp: str, row: dict) -> bool:
        """Tambah/hapus baris. Return True bila kini TERDAFTAR.

        v3.9.42 — audit 61-c/61-d (F5 P3): hasil save()/save_resolved()
        dulu DIABAIKAN — persist gagal (file terkunci / disk penuh)
        senyap: user yakin baris ter-uncheck padahal restart
        mengembalikannya. Kini gagal → print [WARNING] (stdout app
        dialihkan ke log internal; JANGAN messagebox — context bisa
        bukan main thread). Perubahan tetap di memori (degrade soft).
        v3.9.59 — FIX 2f-08: gagal juga men-set flag
        ``self.last_save_error`` SEBELUM _notify() supaya view yang
        mendengarkan store bisa men-surface flash status di tempat
        user mencentang (log tab Proses saja terlalu jauh)."""
        if fp in self.rows:
            del self.rows[fp]
            # v3.9.33 — AUDIT FIX (48-e FIX 9): resolved dihapus dari
            # memori tapi TIDAK ditulis ke followup_resolved.json → fp
            # orphan tetap hidup di file dan muncul lagi setelah restart.
            # Simpan sekarang (baris yang ditambah ulang mulai bersih).
            self.resolved.pop(fp, None)
            # v3.9.72 — FIX 3: _persist_* = sinkron default / defer bila
            # view Follow Up sedang mode tangguh (debounce 200ms).
            ok_resolved = self._persist_resolved()
            ok = self._persist_rows()
            self.last_save_error = None if (ok and ok_resolved) else (
                "gagal menyimpan status followup (file terkunci/disk?) "
                "— perubahan hanya di memori")
            self._notify()
            if self.last_save_error:
                print(f"[WARNING] followup: {self.last_save_error}")
            return False
        snap = {k: _pyval(row.get(k, "")) for k in SNAPSHOT_FIELDS}
        snap["fp"] = fp
        snap["added_at"] = datetime.now().isoformat(timespec="seconds")
        self.rows[fp] = snap
        # v3.9.72 — FIX 3: idem jalur hapus (satu pintu _persist_*).
        ok = self._persist_rows()
        self.last_save_error = None if ok else (
            "gagal menyimpan status followup (file terkunci/disk?) "
            "— perubahan hanya di memori")
        self._notify()
        if self.last_save_error:
            print(f"[WARNING] followup: {self.last_save_error}")
        return True

    def clear(self) -> None:
        if not self.rows:
            return
        self.rows.clear()
        self.resolved.clear()
        # v3.9.42 — audit 61-c/61-d (F5 P3): pola toggle — hasil save tidak
        # diabaikan (gagal persist → [WARNING], lihat toggle).
        # v3.9.59 — FIX 2f-08: + flag last_save_error utk view (lihat toggle).
        ok = self.save()
        ok_r = self.save_resolved()
        self.last_save_error = None if (ok and ok_r) else (
            "gagal menyimpan status followup (file terkunci/disk?) "
            "— perubahan hanya di memori")
        self._notify()
        if self.last_save_error:
            print(f"[WARNING] followup: {self.last_save_error}")

    # -- v3.11.6 — AUTO-DONE saat file source direvisi ----------------------
    def auto_resolve_pending(self, append1_df) -> list:
        """Tandai SELESAI (auto-done) baris follow-up DEVIASI GR/PCS yang
        deviasinya TIDAK ADA LAGI di data revisi (user: "bisa gak misal
        aku udah klik data hingga masuk ke follow up kemudian file source
        nya aku revisi. Otomatis di follow nya udah status done").

        Sumber kebenaran = append1_df pipeline BARU (kolom Nama Barang /
        NAMA RESTO / Tanggal / JENIS / NILAI — baris JENIS "3.DEVIASI"
        adalah Deviasi = SO−SA per pasangan per tanggal, persis kolom
        Deviasi tab 📦/🧩). Per baris follow-up BERSTATUS MENUNGGU dengan
        asal DEVIASI GR/PCS:
        1. pasangan (resto, barang) HILANG total dari data revisi
           → SELESAI "pasangan tidak ada lagi di data";
        2. pasangan ada tapi TANPA baris 3.DEVIASI → SELESAI "tanpa
           baris deviasi";
        3. H snapshot ADA di data: Deviasi(H) == 0 → SELESAI "deviasi
           H kini 0"; ≠ 0 → TETAP MENUNGGU (anomali masih ada);
        4. H tak tercakup data (rentang bergeser): SELESAI hanya bila
           SEMUA deviasi pasangan itu 0; ada yang ≠ 0 → TETAP MENUNGGU
           (konservatif — tak bisa diverifikasi, jangan salah tandai).

        Entri resolved ber-PIC "AUTO" + Cek FU "AUTO-DONE (…)" + field
        auto_reason/Selisih/Selisih Deviasi (kolom kerja FU tetap
        terisi informatif; Status TL = Selesai). Entri yang SUDAH
        resolved (manual/auto sebelumnya) TIDAK disentuh. Asal lain
        (LAPORAN-COM / KOMPARASI — deviasi bukan basis pasangan-tanggal
        append1) tidak diproses.

        Return [(fp, reason)] baris yang baru di-auto-done (dipakai app
        utk log transparan). Persist followup_resolved.json + _notify
        (view/badge ikut menyegarkan)."""
        if append1_df is None or getattr(append1_df, "empty", True):
            return []
        need = {"Nama Barang", "NAMA RESTO", "Tanggal", "JENIS", "NILAI"}
        if not need <= set(getattr(append1_df, "columns", [])):
            return []
        pending = [
            (fp, s) for fp, s in self.rows.items()
            if fp not in self.resolved
            and str(s.get("asal", "")).upper().startswith("DEVIASI")
        ]
        if not pending:
            return []

        def _pair(r, b) -> tuple:
            return (str(r or "").strip(), str(b or "").strip())

        df = append1_df
        pairs_all = {
            _pair(r, b) for r, b in zip(
                df["NAMA RESTO"].astype(str).str.strip(),
                df["Nama Barang"].astype(str).str.strip())}
        dev = df[df["JENIS"].astype(str).str.strip() == "3.DEVIASI"]
        dev_map: dict = {}
        if not dev.empty:
            # vektor: agregat Σ NILAI per (resto, barang, tanggal) —
            # sum menutup duplikat baris (defensif; append1 normalnya
            # unik per kunci).
            tnum = pd.to_numeric(dev["Tanggal"], errors="coerce")
            agg = (pd.to_numeric(dev["NILAI"], errors="coerce")
                   .fillna(0).groupby(
                       [dev["NAMA RESTO"].astype(str).str.strip(),
                        dev["Nama Barang"].astype(str).str.strip(),
                        tnum]).sum())
            for (r, b, t), v in agg.items():
                if pd.notna(t):
                    dev_map.setdefault((r, b), {})[float(t)] = float(v)

        done: list = []
        now = datetime.now().isoformat(timespec="seconds")
        for fp, snap in pending:
            key = _pair(snap.get("resto"), snap.get("barang"))
            if key not in pairs_all:
                reason = "pasangan resto×barang tidak ada lagi di data revisi"
                dev_now = None
            else:
                tmap = dev_map.get(key)
                if not tmap:
                    reason = "tanpa baris deviasi di data revisi"
                    dev_now = None
                else:
                    try:
                        h = int(float(snap.get("h")))
                    except (TypeError, ValueError):
                        h = None
                    if h is not None and h in tmap:
                        dev_now = tmap[h]
                        if dev_now != 0:
                            continue       # anomali MASIH ada di H → menunggu
                        reason = f"deviasi H={h} kini 0 di data revisi"
                    else:
                        if any(v != 0 for v in tmap.values()):
                            continue       # tak terverifikasi → menunggu
                        reason = ("seluruh deviasi pasangan kini 0 di data "
                                  "revisi (H tidak tercakup)")
                        dev_now = 0.0
            try:
                old_dev = float(snap.get("deviasi", 0) or 0)
            except (TypeError, ValueError):
                old_dev = 0.0
            info = {
                "PIC": "AUTO",
                "Cek FU": f"AUTO-DONE ({reason})",
                "Selisih": dev_now,
                "Selisih Deviasi": (
                    round(dev_now - old_dev, 6)
                    if dev_now is not None else None),
                "ts": now,
                "auto": True,
                "auto_reason": reason,
            }
            self.resolved[fp] = info
            done.append((fp, reason))
        if done:
            # persist status TL saja (rows tidak berubah); gagal → flag
            # last_save_error (pola toggle v3.9.42/2f-08) — view men-
            # surface flash status; entri tetap di memori (degrade soft).
            ok = self.save_resolved()
            self.last_save_error = None if ok else (
                "gagal menyimpan status followup (file terkunci/disk?) "
                "— perubahan hanya di memori")
            if self.last_save_error:
                print(f"[WARNING] followup: {self.last_save_error}")
            self._notify()
        return done

    # -- persistensi ---------------------------------------------------------------
    def save(self) -> bool:
        return _atomic_save(followup_path(), {
            "version": 1,
            "rows": {fp: r for fp, r in self.rows.items()},
        })

    def save_resolved(self) -> bool:
        return _atomic_save(resolved_path(), {
            "version": 1, "rows": self.resolved,
        })

    def load(self) -> None:
        p = followup_path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                rows = data.get("rows", {}) if isinstance(data, dict) else {}
                if isinstance(rows, dict):
                    self.rows = {
                        str(k): r for k, r in rows.items()
                        if isinstance(r, dict)
                    }
            except (json.JSONDecodeError, ValueError, OSError) as e:
                _LOG.warning("followup.json korup (%s) — mulai kosong", e)
                _backup_corrupt(p)
                self.rows = {}
                # v3.9.59 — FIX 2f-07: pulihan kini TERLIHAT (flag +
                # [WARNING] log internal + dialog bila GUI — dulu senyap,
                # user kehilangan seluruh daftar tanpa pesan).
                _notify_recovery(self, p, str(e))
        pr = resolved_path()
        if pr.exists():
            try:
                data = json.loads(pr.read_text(encoding="utf-8"))
                rows = data.get("rows", {})
                if isinstance(rows, dict):
                    self.resolved = {str(k): r for k, r in rows.items()
                                     if isinstance(r, dict)}
            except Exception as e:
                _LOG.warning("followup_resolved.json korup → backup .bad")
                _backup_corrupt(pr)
                self.resolved = {}
                # v3.9.59 — FIX 2f-07: mirror jalur followup.json — status
                # TL/PIC yang hilang juga diberitahukan (flag + log).
                _notify_recovery(self, pr, f"korup: {e}")

    # -- export ------------------------------------------------------------------
    def export_xlsx(self, path: str) -> str:
        """Tulis sheet 'FOLLOW UP' — FORMAT FILE SAMPLE (v3.9.6 → v3.11.4).

        Urutan kolom v3.11.4 (user: "Setelah kolom keterangan kapus aja")
        BERHENTI di Keterangan — kolom kerja FU (SO · DEVIASI · Selisih ·
        Selisih Deviasi · Cek FU · PIC) + kolom pelacakan app (Asal ·
        Status TL · Ditambahkan) DIHAPUS dari export (tabel UI tetap
        lengkap — pengerjaan FU tetap di app): Resto · Nama Barang ·
        [SO tgl H-2..H+2 — heading angka tanggal, mis. H=25 →
        23/24/25/26/27] · Sistem · Deviasi · Loss Surplus to BOM ·
        Keterangan.

        Format angka v3.11.4 (user: "kolom 23 24 25 26 27 Sistem Deviasi
        pakai separator , dan tanpa desimal. kolom Loss Surplus to BOM
        pakai persen"): nilai MENTAH numerik tetap ditulis (bisa dihitung
        ulang di Excel — pola export v3.11.2 "SESUAI TAMPILAN") +
        number-format Excel per kolom: tanggal/Sistem/Deviasi
        "#,##0;[Red](#,##0)" — pemisah ribuan TANPA desimal, minus
        otomatis merah dalam kurung (menggantikan Font merah per-sel
        lama); Loss Surplus to BOM "0.00%;[Red](0.00%)" — rasio snapshot
        (1.0053) tampil "100.53%" (2 desimal — paritas presisi Dev to
        BOM% tab Deviasi). Snapshot lama tanpa field tanggal → sel
        string kosong (tak ter-format). Freeze + autofilter + ATOMIK.
        """
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font
        from openpyxl.utils import get_column_letter

        # heading kolom tanggal = angka tanggal (dari H snapshot terbaru)
        h_ref = None
        for snap in reversed(list(self.rows.values())):
            h_val = snap.get("h")
            if isinstance(h_val, (int, float)) and h_val:
                h_ref = int(h_val)
                break
        if h_ref is None:
            header = list(EXPORT_COLS)
        else:
            header = [f"{h_ref + DATE_COL_OFFSETS[c]}" if c in DATE_COL_IDS
                      else c for c in EXPORT_COLS]

        wb = Workbook()
        ws = wb.active
        ws.title = "FOLLOW UP"
        ws.append(header)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        # v3.11.4 — posisi kolom (indeks 0-based) utk number-format:
        # tanggal = posisi DATE_COL_IDS di EXPORT_COLS (stabil 1:1 dgn
        # header) + Sistem + Deviasi → "#,##0" tanpa desimal; Loss
        # Surplus to BOM → persen.
        _date_pos = {i for i, c in enumerate(EXPORT_COLS)
                     if c in DATE_COL_IDS}
        _int_pos = _date_pos | {
            header.index(c) for c in ("Sistem", "Deviasi") if c in header}
        _pct_pos = {header.index(c) for c in ("Loss Surplus to BOM",)
                    if c in header}

        order = list(self.rows.values())
        for i, snap in enumerate(order):
            r = i + 2
            vals = [
                snap.get("resto", ""), snap.get("barang", ""),
                snap.get("so_m2", ""), snap.get("so_m1", ""),
                snap.get("so", ""), snap.get("so_p1", ""),
                snap.get("so_p2", ""),
                snap.get("sistem", ""), snap.get("deviasi", ""),
                snap.get("loss_bom", ""), snap.get("cek", ""),
            ]
            for j, v in enumerate(vals):
                cell = ws.cell(row=r, column=j + 1, value=v)
                # number-format HANYA utk sel numerik sah — bool / NaN
                # / string snapshot-lama tak tersentuh.
                if (isinstance(v, (int, float))
                        and not isinstance(v, bool) and pd.notna(v)):
                    if j in _int_pos:
                        cell.number_format = _INT_NUMFMT
                    elif j in _pct_pos:
                        cell.number_format = _PCT_NUMFMT

        ws.freeze_panes = "A2"
        if order:
            ws.auto_filter.ref = (
                f"A1:{get_column_letter(len(header))}{len(order) + 1}")
        widths = {"Resto": 10, "Nama Barang": 30, "Sistem": 11,
                  "Deviasi": 11, "Loss Surplus to BOM": 12,
                  "Keterangan": 18}
        for j, c in enumerate(header, start=1):
            ws.column_dimensions[get_column_letter(j)].width = \
                widths.get(c, 8 if c.isdigit() else 12)
        # v3.9.59 — FIX 2f-04 (audit 2-f): tulis ATOMIK (tmp + os.replace —
        # pola 6a-02 app._export_excel). wb.save() dulu menulis LANGSUNG
        # ke path tujuan → exception di tengah (disk penuh / styling)
        # meninggalkan .xlsx PARSIAL yang MENIMPA export LAMA yang baik
        # di path sama. Kini file tujuan hanya tersentuh os.replace()
        # atomik SETELAH sukses penuh; kegagalan apa pun (finally)
        # menghapus tmp (tmp ber-ekstensi .xlsx).
        tmp_path = str(path) + ".tmp.xlsx"
        _ok = False
        try:
            wb.save(tmp_path)
            os.replace(tmp_path, str(path))
            _ok = True
        finally:
            if not _ok:
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except OSError:
                    pass
        return path


