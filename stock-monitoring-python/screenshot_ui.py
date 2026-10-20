"""
screenshot_ui.py — Render app (versi dinamis — lihat banner saat run)
+ screenshot tiap tab & fitur baru.

v3.9.69 — HARNESS v2.1 (audit eksternal ke-2, 6.1): 4 skenario sisa
audit: (25) filter aktif lintas-sesi (close→reopen app kedua),
(26) ☑ hide-empty dgn nilai NEGATIF (semantik v3.9.69 P1.1 — baris
negatif TAMPIL, baris semua-nol tersembunyi), (27) data parsial
"SELESAI PARSIAL" via jalur _load_view nyata, (28) clone ⛶ deviasi.

v3.9.68 — HARNESS v2 (audit eksternal T4): header versi DINAMIS ikut
APP_VERSION (dulu literal "v3.3" basi 14 rilis — bisa menyesatkan QA)
+ skenario baru: nominal per-resto, anak tab Tanpa Harga, zoom
50/80/100/200%, tabel kosong jujur (⧩ seleksi kosong), corong aktif,
popup filter deviasi, jendela kecil.

Jalankan di bawah Xvfb (DISPLAY=:99).

Output: /tmp/shots/*.png
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk

from src.ui.app import APP_VERSION, StockMonitorApp
from test_ui_redesign import (
    make_mock_append1,
    make_mock_rincian,
    select_and_wait,
    wait_view,
)

OUT = Path("/tmp/shots")
OUT.mkdir(exist_ok=True)


def shot(name, delay=0.35):
    time.sleep(delay)
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(xdisplay=os.environ.get("DISPLAY", ":99"))
        img.save(OUT / f"{name}.png")
        print(f"  📸 {name}.png ({img.size})")
    except Exception as e:
        print(f"  ! screenshot gagal {name}: {e}")


def pump(root, seconds=0.5):
    t0 = time.time()
    while time.time() - t0 < seconds:
        root.update()
        time.sleep(0.01)


def main():
    print(f"screenshot_ui.py — Render app v{APP_VERSION} "
          "+ screenshot tiap tab & fitur baru (harness v2).")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    root = tk.Tk()
    root.geometry("1440x900+0+0")
    app = StockMonitorApp(root)
    sys.stdout, sys.stderr = real_stdout, real_stderr

    append1 = make_mock_append1()
    rincian = make_mock_rincian()

    pump(root, 0.3)
    shot("1-config")

    # Proses tab (spinner idle)
    app.notebook.select(app.tab_proses)
    pump(root, 0.3)
    shot("2-proses")

    # Load data — pivot default mode RESTO (v3.2: lazy → select+wait)
    app.pivot_view.load_data(append1)
    select_and_wait(root, app, app.tab_pivot, app.pivot_view)
    shot("3-pivot-resto")

    # Header filter popup terbuka (klik heading #0)
    root.update()
    app.pivot_view.tree.event_generate("<Button-1>", x=20, y=10)
    pump(root, 0.4)
    shot("4-pivot-resto-headerfilter-open")

    # aktifkan filter (hanya 1 barang) → corong teal
    hf = app.pivot_view.header_filter
    if hf._popup is not None and hf._popup.winfo_exists():
        for v, var in hf._vars.items():
            var.set(v == "ADONAN GORENG MEKAR")
        hf._update_count()
        hf._emit()
        wait_view(root, app.pivot_view)
        pump(root, 0.4)
        shot("5-pivot-resto-filtered")
        hf._close()
        pump(root, 0.2)

    # Pivot mode TANGGAL
    app.pivot_view._on_mode_change(1)
    wait_view(root, app.pivot_view)
    shot("6-pivot-tanggal")

    # Perbesar (maximize) pivot resto
    app.pivot_view._on_mode_change(0)
    wait_view(root, app.pivot_view)
    win, mtree = app.pivot_view._maximize()
    pump(root, 1.0)
    shot("7-pivot-maximized")
    win.destroy()
    pump(root, 0.2)

    # Deviasi GR (v3.2: lazy + kolom ✓ + tanpa KPI row)
    app.deviasi_gr_view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_gr, app.deviasi_gr_view)
    shot("8-deviasi-gr")

    # v3.2: centang ✓ 2 baris pertama → ikut screenshot (☑ + badge tab)
    tree = app.deviasi_gr_view.tree
    class _Ev:
        pass
    for iid in list(tree.get_children(""))[:2]:
        bbox = tree.bbox(iid)
        if bbox:
            ev = _Ev()
            ev.widget = tree
            ev.x, ev.y = bbox[0] + 8, bbox[1] + bbox[3] // 2
            app.deviasi_gr_view._on_tree_click(ev)
    pump(root, 0.3)
    shot("8b-deviasi-gr-followup-checked")

    # Deviasi PCS
    app.deviasi_pcs_view.load_data(append1)
    select_and_wait(root, app, app.tab_deviasi_pcs, app.deviasi_pcs_view)
    shot("9-deviasi-pcs")

    # Laporan
    app.laporan_view.load_data(append1)
    select_and_wait(root, app, app.tab_laporan, app.laporan_view)
    shot("10-laporan")

    # v3.2: tab Follow Up (badge + snapshot rows)
    select_and_wait(root, app, app.tab_followup, app.followup_view)
    pump(root, 0.4)
    shot("10b-followup")

    # v3.4: tab Rekap Selisih IN + drill-down popup rincian dokumen
    from test_ui_redesign import make_mock_in_detail
    in_detail = make_mock_in_detail()
    app.in_selisih_view.load_data(append1, in_detail)
    select_and_wait(root, app, app.tab_in_selisih, app.in_selisih_view)
    shot("10c-rekap-selisih-in")

    # drill-down: double-click baris MLGPAR/AYAM FILET/Tgl 10
    from src.ui.in_selisih_view import InDetailPopup
    itree = app.in_selisih_view.tree
    for iid in itree.get_children(""):
        vals = itree.item(iid, "values")
        if vals[0] == "MLGPAR" and vals[1] == "10" and vals[2] == "AYAM FILET":
            bbox = itree.bbox(iid)
            class _Ev2:
                pass
            ev = _Ev2()
            ev.widget = itree
            ev.x, ev.y = bbox[0] + 10, bbox[1] + bbox[3] // 2
            app.in_selisih_view._on_double_click(ev)
            break
    pump(root, 0.5)
    shot("10d-rincian-in-popup")
    popups = [w for w in root.winfo_children()
              if isinstance(w, InDetailPopup) and w.winfo_exists()]
    if popups:
        popups[-1].destroy()
    pump(root, 0.2)

    # v3.4: ↔ Auto-Fit pada Rekap Selisih IN (kolom menyesuaikan konten)
    app.in_selisih_view._auto_fit()
    pump(root, 0.4)
    shot("10e-rekap-selisih-autofit")

    # Rincian PO
    app.rincian_view.load_data(rincian)
    select_and_wait(root, app, app.tab_rincian, app.rincian_view)
    shot("11-rincian")

    # Details popup (dari pivot resto — double-click style)
    from src.ui.details_popup import show_details_popup
    popup = show_details_popup(root, append1,
                               nama_barang="ADONAN GORENG MEKAR",
                               jenis="1.SO", filters={"NAMA RESTO": "MLGPAR"})
    wait_view(root, popup)
    pump(root, 0.4)
    shot("12-popup-detail")

    # Popup maximized
    pwin, pmtree = popup._maximize()
    pump(root, 1.0)
    shot("13-popup-maximized")
    pwin.destroy()
    pump(root, 0.2)

    # Loading overlay terlihat saat refresh (force show tanpa delay)
    popup.destroy()
    pump(root, 0.2)
    app.notebook.select(app.tab_pivot)
    pump(root, 0.2)
    app.pivot_view.overlay.show("Menghitung matrix pivot…", delay_ms=0)
    pump(root, 0.5)
    shot("14-loading-overlay")
    app.pivot_view.overlay.hide()

    # v3.9.68 — HARNESS v2 (audit eksternal T4): cakupan UI versi terkini.
    # (15) 🧮 Nominal Deviasi — tabel Per Resto
    app.nominal_resto_view.load_data(append1)
    select_and_wait(root, app, app.tab_nominal_resto,
                    app.nominal_resto_view)
    shot("15-nominal-deviasi-per-resto")

    # (16) 🧮 anak tab 'Tanpa Harga' (global)
    app.nominal_resto_view._sub_nb.select(
        app.nominal_resto_view._tab_noharga)
    pump(root, 0.5)
    shot("16-nominal-tanpa-harga")

    # (17-20) Zoom 50% / 80% / 100% / 200% (fonts-only — jendela tetap)
    app.notebook.select(app.tab_deviasi_gr)
    pump(root, 0.3)
    for _z, _nm in ((0.5, "17-zoom-50"), (0.8, "18-zoom-80"),
                    (1.0, "19-zoom-100"), (2.0, "20-zoom-200")):
        app._apply_ui_zoom(_z, resize_window=False)
        pump(root, 0.4)
        shot(_nm)
    app._apply_ui_zoom(0.8, resize_window=False)   # kembali default
    pump(root, 0.3)

    # (21) Tabel kosong JUJUR — seleksi ⧩ 'Nama Barang' KOSONG (tri-state
    # v3.9.68): status footer menjelaskan penyebab + cara keluar.
    _dv = app.deviasi_gr_view
    _dv._col_sel["Nama Barang"] = set()
    _dv.header_filters.set_selected("Nama Barang", set())
    _dv._refresh(sync=True)
    pump(root, 0.4)
    shot("21-deviasi-kosong-seleksi-kosong")

    # (22) Corong ⧩ AKTIF — 1 barang terpilih (ikon menyala + baris
    # tersaring) + status tersaring.
    _dv._col_sel["Nama Barang"] = {"ADONAN GORENG MEKAR"}
    _dv.header_filters.set_selected("Nama Barang", {"ADONAN GORENG MEKAR"})
    _dv._refresh(sync=True)
    pump(root, 0.4)
    shot("22-deviasi-corong-aktif")

    # (23) Popup filter ⧩ deviasi TERBUKA (pilih semua + counter + cari)
    _hf23 = _dv.header_filters._filters.get("Nama Barang")
    if _hf23 is not None:
        _hf23.open_popup()
        pump(root, 0.4)
        shot("23-deviasi-popup-filter-open")
        _hf23._close()
        pump(root, 0.2)

    # (24) Jendela KECIL (1024x620) — label tab compact + layout sempit
    _geo24 = root.geometry()
    root.geometry("1024x620+0+0")
    pump(root, 0.5)
    shot("24-jendela-kecil")
    root.geometry(_geo24)
    pump(root, 0.3)

    # =====================================================================
    # v3.9.69 — HARNESS v2.1 (audit eksternal ke-2, 6.1): 4 skenario sisa
    # =====================================================================

    # (25) FILTER PERSIST LINTAS-SESI — filter ⧩ deviasi (dari skenario
    # 22: hanya ADONAN GORENG MEKAR) di-capture + disimpan (jalur produksi
    # saat jendela ditutup) → APP KEDUA (Toplevel) membuka data yang sama
    # lalu restore → filter + corong AKTIF tanpa disentuh. _SETTINGS_PATH
    # dipindah ke TEMP dulu supaya settings.json NYATA tidak tertimpa
    # (side-effect harness = pola bersih followup.json v3.9.68).
    import shutil as _sh25
    import tempfile as _tf25
    from pathlib import Path as _Path25

    import src.ui.app as _appmod25
    _tmp25 = _tf25.mkdtemp(prefix="shots_persist_t3969_")
    _orig_sp25 = _appmod25._SETTINGS_PATH
    _appmod25._SETTINGS_PATH = _Path25(_tmp25) / "settings.json"
    _snap25 = app._capture_filter_state()
    _appmod25._save_filter_state(_snap25)
    top25 = tk.Toplevel(root)
    top25.geometry("1380x840+20+20")
    # StreamToQueue app KEDUA jangan menelan log harness — pola restore
    # yang sama dgn app pertama di main() (tanpa ini, print sesudah
    # sini — termasuk shot 25-28 + banner SELESAI — masuk queue app
    # kedua yang mati setelah destroy → log harness TERPOTONG senyap;
    # ditemukan empiris saat run: PNG 25-28 tersimpan tapi baris 📸-nya
    # lenyap dari output).
    _real25 = sys.stdout, sys.stderr
    app25 = StockMonitorApp(top25)
    sys.stdout, sys.stderr = _real25
    pump(root, 0.5)
    app25.deviasi_gr_view.load_data(append1)
    select_and_wait(top25, app25, app25.tab_deviasi_gr,
                    app25.deviasi_gr_view)
    # Guard produksi _apply_saved_filters_once menunda restore bila
    # append1_df masih None (belum ada run pipeline — "tunda ke run
    # berikutnya"). Mirror status pasca-pipeline (data tersedia) supaya
    # jalur restore PRODUksi betul-betul ditempuh — bukan restore
    # per-view manual.
    app25.append1_df = append1
    app25._apply_saved_filters_once()
    wait_view(top25, app25.deviasi_gr_view)
    pump(root, 0.4)
    shot("25-filter-persist-lintas-sesi")
    _appmod25._SETTINGS_PATH = _orig_sp25
    _sh25.rmtree(_tmp25, ignore_errors=True)
    top25.destroy()
    pump(root, 0.3)

    # (26) ☑ HIDE-EMPTY + NILAI NEGATIF — semantik v3.9.69 (P1.1):
    # "kosong" = SEMUA sel 0 (bukan total ≤ 0) → baris RETUR SUSU
    # (semua sel negatif) & CANCEL OUT (+10 MLGPAR / −10 SBYKET —
    # resto-BEDA, total 0 tapi sel ≠ 0) TAMPIL (minus merah per-cell),
    # BRG NOL (semua sel 0) tersembunyi. (NB: +10/−10 di RESTO-SAMA
    # tersembunyi — sel agregat 0; lihat §82a-3b.)
    _p26 = pd.DataFrame([
        {"Nama Barang": b, "NAMA RESTO": r, "SATUAN": "GR", "Tanggal": t,
         "JENIS": j, "NILAI": v, "KATEGORI": k, "SOURCE KIRIMAN": "GUDANG",
         "AKTIF/NON": "AKTIF"}
        for b, r, t, j, v, k in [
            ("RETUR SUSU", "MLGPAR", 1, "3.DEVIASI", -5.0, "BAHAN"),
            ("RETUR SUSU", "SBYKET", 2, "3.DEVIASI", -6.0, "BAHAN"),
            ("CANCEL OUT", "MLGPAR", 1, "3.DEVIASI", 10.0, "BAHAN"),
            ("CANCEL OUT", "SBYKET", 2, "3.DEVIASI", -10.0, "BAHAN"),
            ("BRG NOL", "MLGPAR", 1, "1.SO", 0.0, "BAHAN"),
            ("BRG NOL", "SBYKET", 2, "1.SO", 0.0, "BAHAN"),
        ]])
    app.pivot_view.load_data(_p26)
    select_and_wait(root, app, app.tab_pivot, app.pivot_view)
    pump(root, 0.3)
    shot("26-pivot-hideempty-negatif")
    app.pivot_view.load_data(append1)   # pulihkan utk skenario berikutnya
    select_and_wait(root, app, app.tab_pivot, app.pivot_view)

    # (27) DATA PARSIAL — "SELESAI PARSIAL" via jalur NYATA _load_view:
    # satu tampilan (🛒 Rincian PO) gagal memuat → status akhir oranye +
    # log [PERINGATAN] + view masih menampilkan data LAMA (kontrak
    # v3.9.46). _on_pipeline_done dipanggil dgn tampilan yang di-sabotase
    # (pola §80h — monkeypatch instance, dipulihkan setelahnya).
    _orig_load27 = app.rincian_view.load_data

    def _boom27(*_a, **_k):
        raise RuntimeError("simulasi-tampilan-gagal-t3969")

    app.rincian_view.load_data = _boom27
    app._on_pipeline_done(append1, None, None, None, None, False)
    app.rincian_view.load_data = _orig_load27
    pump(root, 1.0)
    shot("27-data-parsial-selesai-parsial")

    # (28) CLONE ⛶ DEVIASI — jendela perbesar tabel Deviasi GR (filter +
    # ikon corong + minus merah ikut; sebelumnya hanya pivot yang
    # di-screenshot dalam mode perbesar).
    app.notebook.select(app.tab_deviasi_gr)
    pump(root, 0.3)
    win28, _tree28 = app.deviasi_gr_view._maximize()
    pump(root, 0.8)
    shot("28-deviasi-maximized")
    win28.destroy()
    pump(root, 0.3)

    # v3.9.68 — BERSIHKAN STATE SIDE-EFFECT: skenario 8b men-✓ 2 baris ke
    # follow-up (store PERSISTEN followup.json) — tanpa pembersihan, run
    # harness membuat run suite BERIKUTNYA gagal di blok follow-up
    # (store app dibangun saat STARTUP — sebelum tes sempat menghapus
    # file-nya, baris sisa sudah di memori).
    try:
        app.followup_store.clear()
    except Exception as _e:  # noqa: BLE001 — cleanup best-effort harness
        print(f"  ! cleanup followup store: {_e}")

    pump(root, 0.2)
    root.destroy()
    print(f"SELESAI v{APP_VERSION} — semua screenshot di", OUT)


if __name__ == "__main__":
    main()
