# Stock Monitoring

Monitoring stok & deviasi resto berbasis export **Accurate Online**.
Awalnya Power Query M di Excel — kini berupa aplikasi Python (pipeline + UI Tkinter) dengan hasil identik, tanpa ketergantungan Excel/Windows.

> **Versi terkini: v3.11.29** — riwayat versi: [CHANGELOG](stock-monitoring-python/CHANGELOG.md)

## Isi Repository

| Item | Keterangan |
|---|---|
| `stock-monitoring-python/` | Aplikasi Python (pipeline data + UI Tkinter) |
| `01.1 CEK STOCK V2.xlsb` | File kerja asli (Power Query + pivot) — referensi |
| `20.AGUSTUS 2026.xlsx` | Sample file deviasi resmi |

## Mulai Cepat (Windows)

```bat
cd stock-monitoring-python
SETUP.bat    :: sekali saja — install dependency
MULAI.bat    :: buka aplikasi (tanpa jendela console)
```

Atau via CLI:

```bash
python -m src.main     # pipeline
python -m src.ui       # UI
```

Dokumentasi lengkap (config, tab, interaksi tabel, testing, build EXE):
**[stock-monitoring-python/README.md](stock-monitoring-python/README.md)**
