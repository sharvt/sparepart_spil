import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# KONFIGURASI FILE
# ==========================================
# Sesuaikan path file Anda di sini
FILE_MAINT_2023 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2023.xlsx'
FILE_MAINT_2024 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx'
FILE_MAINT_2025 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx'

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
    print("Error: File maintenance tidak ditemukan. Cek path file dan nama folder.")
    exit()

# ==========================================
# 2. CLEANING & PREPARATION
# ==========================================
# Konversi Tanggal Laporan ke format DateTime
df_maint['REPORT_DATE'] = pd.to_datetime(df_maint['JOBREPORT_DATE'], dayfirst=True, errors='coerce')

# Buat kolom Bulan-Tahun untuk plot grafik (Contoh: 2023-01)
df_maint['YYYYMM'] = df_maint['REPORT_DATE'].dt.to_period('M')

# Hanya ambil pekerjaan yang sudah selesai (memiliki tanggal laporan)
df_done = df_maint.dropna(subset=['REPORT_DATE'])

# ==========================================
# 3. VISUALISASI TREN BULANAN (GRAFIK)
# ==========================================
print("\n--- [2] MEMBUAT GRAFIK TREN ---")
monthly_trend = df_done.groupby('YYYYMM').size()

plt.figure(figsize=(15, 6))
monthly_trend.plot(kind='line', marker='o', color='b', linewidth=2)
plt.title('Tren Total Pekerjaan Maintenance (2023-2025)', fontsize=14)
plt.xlabel('Bulan', fontsize=12)
plt.ylabel('Jumlah Pekerjaan', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show() # Jendela grafik akan muncul

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
# Kita filter yang > 0
mtbf_valid = df_mtbf[df_mtbf['DAYS_BETWEEN'] > 0]
mtbf_summary = mtbf_valid.groupby('COMPNAME')['DAYS_BETWEEN'].agg(['mean', 'count']).reset_index()
mtbf_summary.columns = ['COMPNAME', 'MTBF_HARI', 'TOTAL_KEJADIAN_MTBF']
mtbf_summary['MTBF_HARI'] = mtbf_summary['MTBF_HARI'].round(1)

print("MTBF Selesai dihitung. Contoh hasil:")
print(mtbf_summary.head(3))

# ==========================================
# 5. ANALISIS TREN & MERGE DATA
# ==========================================
print("\n--- [4] MENYUSUN ANALISIS LENGKAP ---")

# Pivot table: Menjadikan Tahun sebagai kolom, Nama Komponen sebagai baris
pivot_full = df_done.pivot_table(index='COMPNAME', columns='SOURCE_YEAR', aggfunc='size', fill_value=0)

# Pastikan kolom tahun 2023, 2024, 2025 ada
for year in [2023, 2024, 2025]:
    if year not in pivot_full.columns: 
        pivot_full[year] = 0

# Gabungkan Pivot Table dengan Data MTBF
pivot_full = pivot_full.reset_index()
final_analysis = pd.merge(pivot_full, mtbf_summary, on='COMPNAME', how='left')

# Hitung Statistik Tambahan
final_analysis['TOTAL_3_TAHUN'] = final_analysis[2023] + final_analysis[2024] + final_analysis[2025]
final_analysis['TREN_24_vs_25'] = final_analysis[2025] - final_analysis[2024]

# Isi NaN pada MTBF dengan strip atau info (untuk file CSV)
final_analysis['MTBF_HARI'] = final_analysis['MTBF_HARI'].fillna('Belum Cukup Data')

# Urutkan data dari yang paling sering dimaintenance
final_analysis = final_analysis.sort_values(by='TOTAL_3_TAHUN', ascending=False)

# ==========================================
# 6. EXPORT HASIL KE CSV
# ==========================================
output_filename = 'Analisis_Maintenance_Lengkap_MTBF_2023-2025.csv'
final_analysis.to_csv(output_filename, index=False)
print(f"\n[-] Data lengkap berhasil disimpan ke file: {output_filename}")

# ==========================================
# 7. INSIGHT & REKOMENDASI FORECASTING
# ==========================================
print("\n" + "="*80)
print(f"{'TOP 10 KOMPONEN PALING SERING MAINTENANCE':<50} | {'TOTAL':<8} | {'TREN':<8}")
print("="*80)
print(final_analysis[['COMPNAME', 'TOTAL_3_TAHUN', 'TREN_24_vs_25']].head(10))

print("\n" + "="*80)
print("REKOMENDASI FORECASTING (Berdasarkan Top 20 Item)")
print("="*80)

# Ambil 20 item teratas untuk dianalisis trennya
top_20_items = final_analysis.head(20)

for index, row in top_20_items.iterrows():
    component_name = row['COMPNAME']
    diff = row['TREN_24_vs_25']
    total_2025 = row[2025]
    mtbf_val = row['MTBF_HARI']
    
    # Info MTBF
    mtbf_info = f"Rata-rata rusak setiap {mtbf_val} hari." if mtbf_val != 'Belum Cukup Data' else "Pola kerusakan belum terbaca."

    if diff > 0:
        # Jika tren naik
        print(f"[NAIK] {component_name}")
        print(f"   -> Aktivitas naik +{diff} job dibanding tahun lalu.")
        print(f"   -> {mtbf_info}")
        print(f"   -> SARAN: Tingkatkan stok sparepart. Cek kondisi alat.")
    elif diff < 0:
        # Jika tren turun
        print(f"[TURUN] {component_name}")
        print(f"   -> Aktivitas turun {diff} job.")
        print(f"   -> {mtbf_info}")
    else:
        print(f"[STABIL] {component_name} (Aktivitas sama dengan tahun lalu)")
    print("-" * 50)