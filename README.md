# Stock-Monitoring

Repository berisi:

1. **`Mutasi Barang - New - Copy.xlsx`** — File Excel asli dengan Power Query + Pivot Tables (monitoring stok resto berbasis Accurate Online export).

2. **`stock-monitoring-python/`** — Porting Python dari Power Query M code. Pipeline lengkap yang menghasilkan output Excel "sama persis" dengan sample, tanpa dependency Excel/Windows.

## Quick Start (Python Edition)

```bash
cd stock-monitoring-python
SETUP.bat   # Windows: install pandas, openpyxl, numpy
MULAI.bat   # Windows: buka Tkinter UI
```

Atau CLI:
```bash
python -m src.main
```

Lihat `stock-monitoring-python/README.md` untuk dokumentasi lengkap.
