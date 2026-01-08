import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# ==========================================
# KONFIGURASI FILE
# ==========================================
# Sesuaikan path file Anda di sini
FILE_MAINT_2023 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2023.xlsx'
FILE_MAINT_2024 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx'
FILE_MAINT_2025 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx'
FILE_MASTER_BARANG = 'Master_Barang_Rapih_V3.csv' # File hasil olahan sebelumnya

# ==========================================
# 1. LOAD DATA MAINTENANCE (3 TAHUN)
# ==========================================
print("\n--- [1] MEMUAT DATA MAINTENANCE ---")
try:
    df_2023 = pd.read_excel(FILE_MAINT_2023)
    df_2024 = pd.read_excel(FILE_MAINT_2024)
    df_2025 = pd.read_excel(FILE_MAINT_2025)
    
    df_2023['SOURCE_YEAR'] = 2023
    df_2024['SOURCE_YEAR'] = 2024
    df_2025['SOURCE_YEAR'] = 2025

    df_maint = pd.concat([df_2023, df_2024, df_2025], ignore_index=True)
    print(f"Sukses! Total Data Maintenance: {len(df_maint):,} baris.")

except FileNotFoundError:
    print("Error: File maintenance tidak ditemukan. Cek path file.")
    exit()

# ==========================================
# 2. LOAD DATA MASTER BARANG (UNTUK MERGE)
# ==========================================
print("\n--- [2] MEMUAT MASTER BARANG (SPAREPART) ---")
try:
    df_inventory = pd.read_csv(FILE_MASTER_BARANG)
    # Pastikan kolom string
    df_inventory['NAMA_BARANG_RAPIH'] = df_inventory['NAMA_BARANG_RAPIH'].astype(str)
    print(f"Sukses! Total Data Barang: {len(df_inventory):,} item.")
except FileNotFoundError:
    print("Warning: 'Master_Barang_Rapih_Final.csv' tidak ditemukan.")
    print("Fitur rekomendasi Part Number tidak akan berjalan maksimal.")
    df_inventory = pd.DataFrame(columns=['NAMA_BARANG_RAPIH', 'PART_NO', 'SPESIFIKASI'])

# ==========================================
# 3. CLEANING & PREPARATION
# ==========================================
df_maint['REPORT_DATE'] = pd.to_datetime(df_maint['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
df_maint['YYYYMM'] = df_maint['REPORT_DATE'].dt.to_period('M')

# Hanya ambil pekerjaan yang sudah selesai
df_done = df_maint.dropna(subset=['REPORT_DATE'])

# ==========================================
# 4. HITUNG MTBF (Mean Time Between Failures)
# ==========================================
print("\n--- [3] MENGHITUNG MTBF (UMUR PAKAI KOMPONEN) ---")

# Urutkan data berdasarkan Kapal -> Nama Komponen -> Tanggal Laporan
df_mtbf = df_done.sort_values(by=['VESSELID', 'COMPNAME', 'REPORT_DATE'])

# Hitung selisih hari dengan pekerjaan berikutnya (Shift -1)
df_mtbf['NEXT_JOB_DATE'] = df_mtbf.groupby(['VESSELID', 'COMPNAME'])['REPORT_DATE'].shift(-1)
df_mtbf['DAYS_BETWEEN'] = (df_mtbf['NEXT_JOB_DATE'] - df_mtbf['REPORT_DATE']).dt.days

# Hitung Rata-rata MTBF per Komponen (Diabaikan jika minus/error)
# Kita filter yang > 0 (jika ada input tanggal salah)
mtbf_valid = df_mtbf[df_mtbf['DAYS_BETWEEN'] > 0]
mtbf_summary = mtbf_valid.groupby('COMPNAME')['DAYS_BETWEEN'].agg(['mean', 'count']).reset_index()
mtbf_summary.columns = ['COMPNAME', 'MTBF_HARI', 'TOTAL_KEJADIAN']
mtbf_summary['MTBF_HARI'] = mtbf_summary['MTBF_HARI'].round(1)

print("MTBF Selesai dihitung. Contoh:")
print(mtbf_summary.head(3))

# ==========================================
# 5. ANALISIS TREN (PIVOT 3 TAHUN)
# ==========================================
print("\n--- [4] MENGHITUNG TREN TAHUNAN ---")
pivot_full = df_done.pivot_table(index='COMPNAME', columns='SOURCE_YEAR', aggfunc='size', fill_value=0)

for year in [2023, 2024, 2025]:
    if year not in pivot_full.columns: pivot_full[year] = 0

# Gabungkan dengan Data MTBF
pivot_full = pivot_full.reset_index()
final_analysis = pd.merge(pivot_full, mtbf_summary, on='COMPNAME', how='left')

# Hitung Tren
final_analysis['TREN_24_vs_25'] = final_analysis[2025] - final_analysis[2024]
final_analysis = final_analysis.sort_values(by=2025, ascending=False)

# ==========================================
# 6. FUNGSI PENCARI SPAREPART (MERGE LOGIC)
# ==========================================
def cari_sparepart_rekomendasi(nama_komponen):
    """
    Mencari sparepart di Master Barang berdasarkan kata kunci dari Nama Komponen.
    Contoh: Komponen "Seawater Pump" -> Cari "SEAWATER" dan "PUMP" di Inventory.
    """
    if pd.isna(nama_komponen): return "Tidak ditemukan"
    
    # Bersihkan nama komponen (Hapus #1, No.2, dll)
    keywords = re.findall(r'[a-zA-Z]{3,}', str(nama_komponen).upper())
    # Hapus kata umum yang tidak berguna untuk pencarian
    stop_words = ['THE', 'FOR', 'AND', 'UNIT', 'SET', 'KIT', 'ASSY', 'MAIN', 'AUX', 'NO']
    keywords = [k for k in keywords if k not in stop_words]
    
    if not keywords: return "Keyword tidak jelas"
    
    # Cari di inventory yang mengandung SALAH SATU keyword utama (Prioritas kata terakhir biasanya nama alat, misal 'PUMP')
    # Kita ambil max 3 rekomendasi teratas
    matches = []
    
    # Strategi: Cari yang mengandung kata paling spesifik (biasanya kata benda terakhir, misal PUMP atau ENGINE)
    search_term = keywords[-1] if keywords else ""
    
    if search_term:
        # Cari di kolom NAMA_BARANG_RAPIH
        hasil = df_inventory[df_inventory['NAMA_BARANG_RAPIH'].str.contains(search_term, case=False, na=False)]
        
        if not hasil.empty:
            # Ambil 3 part number unik
            top_parts = hasil[['NAMA_BARANG_RAPIH', 'PART_NO']].head(3)
            for _, row in top_parts.iterrows():
                pn = row['PART_NO'] if pd.notna(row['PART_NO']) else "No P/N"
                nama = row['NAMA_BARANG_RAPIH'][:30] # Potong biar gak kepanjangan
                matches.append(f"{nama} ({pn})")
    
    return " | ".join(matches) if matches else "Tidak ada match di Inventory"

# ==========================================
# 7. GENERATE LAPORAN LENGKAP
# ==========================================
print("\n--- [5] MENYUSUN REKOMENDASI FORECASTING & STOK ---")

print("="*80)
print(f"{'KOMPONEN':<30} | {'TREN 25':<8} | {'MTBF (HARI)':<12} | {'REKOMENDASI STOK (PART NUMBER)':<40}")
print("="*80)

# Ambil Top 15 Komponen yang Tren-nya NAIK atau SANGAT SERING dirawat
top_action_items = final_analysis.head(15)

export_data = []

for index, row in top_action_items.iterrows():
    comp = row['COMPNAME']
    tren = row['TREN_24_vs_25']
    mtbf = row['MTBF_HARI']
    
    # Logika Pencarian Sparepart
    sparepart_info = cari_sparepart_rekomendasi(comp)
    
    # Logika Status
    status_text = "STABIL"
    if tren > 0: status_text = f"NAIK (+{tren})"
    elif tren < 0: status_text = f"TURUN ({tren})"
    
    # Tampilkan di Layar
    print(f"{str(comp)[:30]:<30} | {status_text:<8} | {str(mtbf):<12} | {sparepart_info}")
    
    # Simpan untuk Excel
    export_data.append({
        'Nama Komponen': comp,
        'Total Job 2025': row[2025],
        'Tren vs 2024': status_text,
        'Rata-rata MTBF (Hari)': mtbf,
        'Estimasi Order Berikutnya': f"Setiap {mtbf} Hari" if mtbf > 0 else "Tidak Terprediksi",
        'Rekomendasi Part Number': sparepart_info
    })

# ==========================================
# 8. EXPORT HASIL
# ==========================================
df_export = pd.DataFrame(export_data)
filename = "Laporan_Forecasting_MTBF_Sparepart.csv"
df_export.to_csv(filename, index=False)
print("\n" + "="*80)
print(f"Laporan lengkap dengan MTBF & Rekomendasi Part Number disimpan di: {filename}")

# ==========================================
# 9. VISUALISASI TREN BULANAN (OPSIONAL)
# ==========================================
monthly_trend = df_done.groupby('YYYYMM').size()
plt.figure(figsize=(12, 5))
monthly_trend.plot(kind='line', marker='o', color='green')
plt.title('Tren Aktivitas Maintenance (2023-2025)')
plt.grid(True, linestyle='--')
plt.tight_layout()
plt.show()