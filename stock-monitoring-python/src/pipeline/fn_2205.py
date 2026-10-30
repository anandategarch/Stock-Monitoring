"""
fn_2205.py — Baca export 22.05 (Rincian Penjualan per Barang) sebagai sumber OUT.

Mirror fn2205 di M code: gabung semua file di folder (sheet 22.05, header
baris 4), lalu keluarkan qty penjualan per (Tanggal, NAMA RESTO, Nama
Barang). Output: Tanggal (day-of-month), NAMA RESTO (teks di antara "("
dan ")" pada kolom Nama Pelanggan), Nama Barang, Value (dari Kuantitas).

Aturan filter saat ini:
- Baris dengan 'Nomor #' berawalan "SI" (case-sensitive) DIKECUALIKAN dari
  sumber OUT; semua kode lain (ACR./RETUR./dll.) tetap masuk. Jumlah baris
  SI yang dibuang dicatat di log sebagai INFO (bukan warning).
- 'Nomor #' kosong/NA dianggap BUKAN SI (baris tetap masuk); kolom tersebut
  bukan kolom wajib — hilang → baris diproses apa adanya + WARNING keras
  (kode SI tak bisa dikecualikan).
- Kolom identitas (Nama Pelanggan, Nama Barang) hilang → WARNING + baris
  sumber ini dibuang (degradasi per-sumber, schema output tetap).
- Kolom nilai (Kuantitas/Tanggal) hilang → NA + WARNING (bukan error).
- Baris dengan NAMA RESTO kosong dibuang.
"""
import pandas as pd

from .helpers import (
    date_to_day,
    fn_combine_folder,
    safe_to_numeric,
    safe_to_str,
    vec_text_between_delimiters,
)

# Nama sheet standar 22.05 (export Accurate) — v3.9.33 default param
SHEET_2205 = "#22.05. Rincian Penjualan per B"


def fn_2205(folder_path: str, sheet_name: str = SHEET_2205,
            stop_event=None) -> pd.DataFrame:
    """
    Mirror M: fn2205(folderPath).

    sheet_name: v3.9.33 — AUDIT FIX (48-a): default SHEET_2205; query
    berjalan me-resolve config Sheets['Penjualan2205'].

    stop_event: v3.9.72 — diteruskan ke fn_combine_folder (checkpoint ⏹
    antar file — audit 1-d). Default None = perilaku lama.

    Output columns: Tanggal, NAMA RESTO, Nama Barang, Value
    """
    # expand = fnCombineFolder(folderPath, sheet, true) + Skip(3) + PromoteHeaders = header=4
    prom = fn_combine_folder(folder_path, sheet_name, header_row=4,
                             stop_event=stop_event)
    if prom.empty:
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # sel = Table.SelectColumns(prom, {"Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang", "Kuantitas"})
    # v3.9.71 — 'Nomor #' DIBACA LAGI sebagai kunci filter SI (user:
    # "22.05 tanpa kode SI") — tetap BUKAN kolom wajib identitas
    # (ident-guard tetap cukup Nama Pelanggan + Nama Barang; kolom
    # hilang → baris diproses APA ADANYA + WARNING, lihat blok filter).
    needed = ["Nomor #", "Tanggal", "Nama Pelanggan", "Nama Barang",
              "Kuantitas"]
    available = [c for c in needed if c in prom.columns]
    sel = prom[available].copy()

    # v3.9.33 — AUDIT FIX (48-a): kolom IDENTITAS hilang (header file
    # bergeser/versi export beda) → dulu KeyError mematikan SELURUH
    # pipeline. Sekarang: WARNING keras (nama kolom + jumlah baris) +
    # baris dibuang → frame kosong ber-schema standar (degradasi
    # per-sumber: sumber lain tetap jalan; schema output IDENTIK —
    # concat query_out/append1 tak berubah). VALUE hilang → NA.
    # v3.9.70 — 'Nomor #' dicabut dari identitas (bukan lagi kunci
    # filter ACR — cukup Nama Pelanggan + Nama Barang).
    _ident_hilang = [c for c in ("Nama Pelanggan", "Nama Barang")
                     if c not in sel.columns]
    if _ident_hilang:
        print(f"  [fn_2205] WARNING: kolom identitas hilang "
              f"{_ident_hilang} — {len(sel)} baris dibuang (header file "
              f"bergeser? pipeline lanjut tanpa sumber 22.05 ini)")
        return pd.DataFrame(columns=["Tanggal", "NAMA RESTO", "Nama Barang", "Value"])

    # v3.9.71 — TANPA KODE SI (user: "22.05 tanpa kode SI ya maaf aku
    # lupa bilang kemarin"): v3.9.70 membuka SEMUA kode masuk; kini
    # hanya kode SI yang dikecualikan — semua kode lain (ACR./RETUR./
    # dll.) tetap masuk. Mirror semantik filter M lama (Text.StartsWith
    # case-sensitive): prefix "SI" case-sensitive, bukan "si.", dan
    # Nomor # kosong/NA dianggap BUKAN SI (baris tetap masuk).
    # 'Nomor #' tetap BUKAN kolom wajib identitas: hilang → baris
    # diproses APA ADANYA + WARNING keras (kode SI tak teridentifikasi
    # — data berpotensi tercemar SI; peringatan ini ikut menaikkan
    # status akhir run, pola §82b).
    if "Nomor #" in sel.columns:
        _kode = safe_to_str(sel["Nomor #"])
        _si = _kode.str.startswith("SI", na=False)
        if bool(_si.any()):
            print(f"  [fn_2205] INFO: {int(_si.sum())} baris kode SI "
                  f"dikecualikan dari perhitungan (22.05 tanpa kode "
                  f"SI — kode lain tetap masuk)")
        fil = sel.loc[~_si].copy()
    else:
        print(f"  [fn_2205] WARNING: kolom 'Nomor #' tidak ditemukan — "
              f"{len(sel)} baris diproses APA ADANYA, kode SI TIDAK "
              f"bisa dikecualikan (header di-rename/hilang oleh export "
              f"baru Accurate?)")
        fil = sel.copy()

    # typed: vectorized
    fil["Nama Pelanggan"] = safe_to_str(fil["Nama Pelanggan"])
    fil["Nama Barang"] = safe_to_str(fil["Nama Barang"])
    # v3.9.33 — AUDIT FIX (48-a): VALUE hilang → NA (bukan KeyError)
    if "Kuantitas" in fil.columns:
        fil["Kuantitas"] = safe_to_numeric(fil["Kuantitas"])

    # ext: Tanggal → Date.Day (Int64), Nama Pelanggan → BetweenDelimiters("(", ")")
    # Vectorized: .str.extract for between delimiters
    if "Tanggal" in fil.columns:
        fil["Tanggal"] = date_to_day(fil["Tanggal"])
    else:
        # v3.9.67 — HARDENING FORMAT: Tanggal hilang dulu NA SENYAP
        # (baris tanpa hari → lenyap dari kolom hari pivot).
        print(f"  [fn_2205] WARNING: kolom 'Tanggal' tidak ditemukan — "
              f"{len(fil)} baris masuk dengan Tanggal NA (header "
              f"di-rename/hilang oleh export baru Accurate?)")
        fil["Tanggal"] = pd.array([pd.NA] * len(fil), dtype="Int64")
    fil["NAMA RESTO"] = vec_text_between_delimiters(fil["Nama Pelanggan"], "(", ")")

    # ren: Kuantitas → Value
    if "Kuantitas" in fil.columns:
        fil = fil.rename(columns={"Kuantitas": "Value"})
    if "Value" not in fil.columns:
        # v3.9.67 — HARDENING FORMAT: kolom VALUE hilang dulu NA SENYAP —
        # qty OUT 22.05 lenyap dari pivot tanpa jejak di log.
        print(f"  [fn_2205] WARNING: kolom VALUE 'Kuantitas' tidak "
              f"ditemukan — {len(fil)} baris masuk dengan Value NA "
              f"(qty OUT 22.05 lenyap — header di-rename/hilang oleh "
              f"export baru Accurate?)")
        fil["Value"] = pd.Series([float("nan")] * len(fil), index=fil.index)

    # fin = Table.SelectColumns(ren, {"Tanggal", "NAMA RESTO", "Nama Barang", "Value"})
    fin = fil[["Tanggal", "NAMA RESTO", "Nama Barang", "Value"]].copy()

    # Drop rows dengan NAMA RESTO null
    fin = fin.dropna(subset=["NAMA RESTO"]).reset_index(drop=True)

    return fin
