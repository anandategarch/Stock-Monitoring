"""followup.py — Daftar follow-up baris anomali (v3.2.0) — ala repo Waste.

Konsep: user mencentang baris mencurigakan (kolom ✓) di tabel DEVIASI GR /
DEVIASI PCS / LAPORAN DEVIASI → baris terkumpul di tab "☑ Follow Up" sebagai
SNAPSHOT baris (nilai apa adanya saat dicentang). Daftar menetap — TIDAK ikut
filter/H aktif; tertutup aplikasi pun aman (followup.json).

Struktur (pola waste_anomaly/followup.py):
- ``row_fingerprint(fields)`` — md5 identitas baris: Asal|Resto|Barang|Satuan|
  H|SO|Sistem|Deviasi|CEK. Stabil lintas sesi (str(float) dinormalisasi).
- ``FollowUpStore`` — dict {fp: snapshot} + status tindak lanjut (resolved):
  - toggle(fp, row) → tambah/hapus, return status baru
  - save/load (atomic write + backup .bad utk file korup)
  - export_xlsx(path) → sheet "FOLLOW UP" + kolom serah-terima kosong
    (PIC / KATEGORI MASALAH / TINDAKAN — diisi petugas, konvensi rekap)
  (v3.8: import_workbook DIHAPUS — fitur "Impor Hasil TL" tidak perlu
  lagi, permintaan user; resolved lama tetap dimuat agar status/PIC
  yang sudah tersimpan sebelumnya tetap tampil.)
- Modul murni (tanpa Tk) — dipakai view + app.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

_LOG = logging.getLogger("stock_monitoring.followup")

# Snapshot row keys (persis kolom tabel Follow Up, tanpa ✓/status TL)
SNAPSHOT_FIELDS = [
    "asal", "resto", "barang", "satuan", "aktif", "h",
    "so", "sistem", "deviasi", "cek",
]
# Kolom serah-terima di export (diisi petugas follow-up)
HANDOVER_COLS = ["PIC", "KATEGORI MASALAH", "TINDAKAN"]

# Nama kolom sheet FOLLOW UP (export) — urutan tetap
EXPORT_COLS = [
    "Asal", "Resto", "Nama Barang", "Satuan", "AKTIF/NON", "H",
    "SO", "Sistem", "Deviasi", "CEK / Status",
] + HANDOVER_COLS

CHECK_ON, CHECK_OFF = "☑", "☐"

# Path (dynamis — pola config.json di app.py)
_BASE = Path(__file__).resolve().parent.parent.parent


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
    """md5 identitas baris (stabil lintas sesi)."""
    parts = [
        str(row.get("asal", "") or "").strip(),
        str(row.get("resto", "") or "").strip(),
        str(row.get("barang", "") or "").strip(),
        str(row.get("satuan", "") or "").strip(),
        _norm_num(row.get("h")),
        _norm_num(row.get("so")),
        _norm_num(row.get("sistem")),
        _norm_num(row.get("deviasi")),
        str(row.get("cek", "") or "").strip(),
    ]
    key = "|".join(parts)
    return hashlib.md5(key.encode("utf-8", "surrogatepass")).hexdigest()


def _backup_corrupt(p: Path) -> None:
    """File korup di-rename .bad (tidak hilang) — pola Waste."""
    try:
        os.replace(p, p.with_suffix(p.suffix + ".bad"))
    except OSError:
        pass


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
        self.load()

    # -- sinkronisasi UI ------------------------------------------------------
    def add_listener(self, cb) -> None:
        """cb(store) dipanggil setiap perubahan (toggle/clear)."""
        if cb not in self._listeners:
            self._listeners.append(cb)

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
    def toggle(self, fp: str, row: dict) -> bool:
        """Tambah/hapus baris. Return True bila kini TERDAFTAR."""
        if fp in self.rows:
            del self.rows[fp]
            self.resolved.pop(fp, None)
            self.save()
            self._notify()
            return False
        snap = {k: _pyval(row.get(k, "")) for k in SNAPSHOT_FIELDS}
        snap["fp"] = fp
        snap["added_at"] = datetime.now().isoformat(timespec="seconds")
        self.rows[fp] = snap
        self.save()
        self._notify()
        return True

    def clear(self) -> None:
        if not self.rows:
            return
        self.rows.clear()
        self.resolved.clear()
        self.save()
        self.save_resolved()
        self._notify()

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
        pr = resolved_path()
        if pr.exists():
            try:
                data = json.loads(pr.read_text(encoding="utf-8"))
                rows = data.get("rows", {})
                if isinstance(rows, dict):
                    self.resolved = {str(k): r for k, r in rows.items()
                                     if isinstance(r, dict)}
            except Exception:
                _LOG.warning("followup_resolved.json korup → backup .bad")
                _backup_corrupt(pr)
                self.resolved = {}

    # -- export ------------------------------------------------------------------
    def export_xlsx(self, path: str) -> str:
        """Tulis sheet 'FOLLOW UP' — snapshot + kolom serah-terima.

        Baris yang sudah resolved membawa nilai PIC/KATEGORI/TINDAKAN
        tersimpan. Deviasi negatif diberi font merah. Freeze + autofilter.
        """
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = "FOLLOW UP"
        ws.append(EXPORT_COLS)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        order = list(self.rows.values())
        for i, snap in enumerate(order):
            r = i + 2
            info = self.resolved.get(snap.get("fp", ""), {})
            vals = [
                snap.get("asal", ""), snap.get("resto", ""),
                snap.get("barang", ""), snap.get("satuan", ""),
                snap.get("aktif", ""), snap.get("h", ""),
                snap.get("so", ""), snap.get("sistem", ""),
                snap.get("deviasi", ""), snap.get("cek", ""),
                info.get("PIC", ""), info.get("KATEGORI MASALAH", ""),
                info.get("TINDAKAN", ""),
            ]
            for j, v in enumerate(vals):
                cell = ws.cell(row=r, column=j + 1, value=v)
                if j == 8 and isinstance(v, (int, float)) and v < 0:
                    cell.font = Font(color="DC2626")
            # resolved → fill hijau lembut di kolom handover
            if info:
                fill = PatternFill("solid", start_color="ECFDF5")
                for j in range(11, 14):
                    ws.cell(row=r, column=j).fill = fill

        ws.freeze_panes = "A2"
        if order:
            ws.auto_filter.ref = (
                f"A1:{get_column_letter(len(EXPORT_COLS))}{len(order) + 1}")
        widths = {"Asal": 10, "Resto": 10, "Nama Barang": 30, "Satuan": 8,
                  "AKTIF/NON": 12, "H": 5, "SO": 10, "Sistem": 10,
                  "Deviasi": 10, "CEK / Status": 18, "PIC": 14,
                  "KATEGORI MASALAH": 20, "TINDAKAN": 28}
        for j, c in enumerate(EXPORT_COLS, start=1):
            ws.column_dimensions[get_column_letter(j)].width = widths.get(c, 12)
        wb.save(path)
        return path


