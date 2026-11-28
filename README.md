# Stock Monitoring

Monitoring stok & deviasi resto berbasis export **Accurate Online**.
Awalnya Power Query M di Excel — kini berupa aplikasi desktop Python (pipeline + UI Tkinter) dengan hasil identik. Berjalan di Windows + Python 3.12 (lihat [README aplikasi](stock-monitoring-python/README.md)); EXE rilis dibangun otomatis tiap tag `v*`.

> **Versi terkini: v3.17.2** — riwayat versi: [CHANGELOG](stock-monitoring-python/CHANGELOG.md)

## Isi Repository

| Item | Keterangan |
|---|---|
| `stock-monitoring-python/` | Aplikasi Python (pipeline data + UI Tkinter) — source, test, build EXE |
| `stock-monitoring-python/benchmarks/` | Benchmark performa P1 (pipeline cold/warm + peak RAM + views) — dataset sintetis |

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
