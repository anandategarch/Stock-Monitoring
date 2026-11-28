#!/usr/bin/env python3
"""
benchmark_report.py — Rapikan hasil JSON benchmark menjadi laporan
markdown (dipakai AUDIT_PERFORMANCE_REPORT.md).

Pemakaian:
  python benchmarks/benchmark_report.py [--results-dir benchmarks/results]
      [--out benchmarks/results/REPORT.md] [--tag-filter 100k,300k]

Membaca semua pipeline_*.json + views_*.json, menghasilkan tabel:
  - pipeline: per skenario (cold/warm/refresh) — total_s, peak RSS,
    append1 rows, cache hit/miss, fingerprint match
  - views: pivot compute/render/filter/sort/export, deviasi,
    nominal, event-loop maxgap
"""
import argparse
import glob
import json
import os
from pathlib import Path


def load_all(results_dir, tag_filter=None):
    out = {"pipeline": [], "views": []}
    for p in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:  # noqa: BLE001 — file rusak di-skip, bukan jalur bisnis
            print(f"  (skip {p}: {e})")
            continue
        if not isinstance(d, dict) or "kind" not in d:
            continue
        if tag_filter and d.get("tag") not in tag_filter:
            continue
        d["_file"] = os.path.basename(p)
        if d["kind"] == "benchmark_pipeline":
            out["pipeline"].append(d)
        elif d["kind"] == "benchmark_views":
            out["views"].append(d)
    # dedupe: per kind+tag, simpan run TERAKHIR (timestamp di nama file)
    for kind in ("pipeline", "views"):
        seen = {}
        for d in out[kind]:
            key = d.get("tag")
            seen[key] = d  # urutan glob sorted → terakhir = terbaru
        out[kind] = list(seen.values())
    return out


def fmt_mb(v):
    return f"{v:,.1f}" if isinstance(v, (int, float)) else "-"


def table_pipeline(runs):
    lines = [("| Skala | Skenario | Total (s) | Peak RSS (MB) | "
              "Append1 rows | Cache hit/miss | FP sama |"),
             "|---|---|---|---|---|---|---|"]
    for d in runs:
        for scen, r in d.get("scenarios", {}).items():
            if "error" in r:
                lines.append(f"| {d['tag']} | {scen} | ERROR | - | - | "
                             f"- | - |")
                continue
            fp = r.get("fingerprint_match_prev")
            fp_s = "-" if fp is None else ("YA" if fp else "TIDAK!")
            cache = r.get("cache", {})
            hit = cache.get("hit_files", "-")
            miss = cache.get("miss_files", "-")
            lines.append(
                f"| {d['tag']} | {scen} | {r['total_s']:.2f} | "
                f"{fmt_mb(r['peak_rss_mb'])} | "
                f"{r.get('append1_rows', 0):,} | "
                f"{hit}/{miss} | "
                f"{fp_s} |")
    return lines


def table_stages(runs):
    lines = [("| Skala | Skenario | Config | Append1 | Rincian PO | Maps | "
              "Audit penuh | Audit bln-ini | Harga | Sum stage | Total |"),
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in runs:
        for scen, r in d.get("scenarios", {}).items():
            if "error" in r:
                continue

            def s(k, _r=r):
                v = _r.get(f"stage_{k}_s")
                return f"{v:.2f}" if isinstance(v, (int, float)) else "-"

            lines.append(
                f"| {d['tag']} | {scen} | {s('1_config')} | "
                f"{s('2_append1')} | {s('3_rincian_po')} | {s('4_maps')} | "
                f"{s('5_audit_full')} | {s('6_audit_bulan_ini')} | "
                f"{s('7_harga_4109')} | "
                f"{r.get('stage_sum_s', 0):.2f} | {r['total_s']:.2f} |")
    return lines


def table_views(runs):
    lines = [
        ("| Skala (rows) | Pivot compute resto | Pivot compute "
         "tanggal | Pivot render | Filter 25% | Reset | Deviasi "
         "compute+render | Sort kolom | Nominal compute | Export | "
         "Maxgap loop |"),
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for d in runs:
        m = d.get("measures", {})
        rows = d.get("data", {}).get("rows", 0)

        def g(k, _m=m):
            v = _m.get(k)
            return f"{v:.2f}" if isinstance(v, (int, float)) else "-"

        lines.append(
            f"| {rows:,} | {g('pivot_compute_resto_s')} | "
            f"{g('pivot_compute_tanggal_s')} | {g('pivot_render_s')} | "
            f"{g('pivot_filter25_s')} | {g('pivot_filter_reset_s')} | "
            f"{g('deviasi_compute_render_s')} | {g('deviasi_sort_s')} | "
            f"{g('nominal_compute_s')} | {g('pivot_export_s')} | "
            f"{m.get('pivot_render_eventloop_maxgap_s', '-')}s |")
    return lines


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default=str(here / "results"))
    ap.add_argument("--out", default=str(here / "results" / "REPORT.md"))
    ap.add_argument("--tag-filter", default=None,
                    help="Koma terpisah, mis. '100k,300k,600k,900k'")
    a = ap.parse_args()
    tags = set(a.tag_filter.split(",")) if a.tag_filter else None
    data = load_all(a.results_dir, tags)

    parts = ["# Hasil Benchmark (digenerate otomatis)\n"]
    if data["pipeline"]:
        parts.append("## Pipeline — ringkasan skenario\n")
        parts += table_pipeline(data["pipeline"])
        parts.append("\n## Pipeline — rincian tahap (detik)\n")
        parts += table_stages(data["pipeline"])
    if data["views"]:
        parts.append("\n## Views/UI (detik)\n")
        parts += table_views(data["views"])
    parts.append("\n---\n_Sumber file JSON: benchmarks/results/ "
                 "(catatan keamanan & keterbatasan: lihat "
                 "AUDIT_PERFORMANCE_REPORT.md)._\n")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"laporan: {a.out}")
    print("\n".join(parts))


if __name__ == "__main__":
    main()
