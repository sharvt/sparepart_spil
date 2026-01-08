import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# 1. LOAD DATA DARI 3 TAHUN
# ==========================================
print("Sedang memuat data...")
try:
    # Membaca file sesuai path yang Anda berikan
    # Pastikan file excel ada di folder 'Magang Sparepart 2025'
    df_2023 = pd.read_excel('Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2023.xlsx')
    df_2024 = pd.read_excel('Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx')
    df_2025 = pd.read_excel('Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx') 
    
    # Beri tanda tahun untuk identifikasi
    df_2023['SOURCE_YEAR'] = 2023
    df_2024['SOURCE_YEAR'] = 2024
    df_2025['SOURCE_YEAR'] = 2025

    # Gabungkan menjadi satu "Data Induk"
    df_all = pd.concat([df_2023, df_2024, df_2025], ignore_index=True)
    print(f"Sukses! Total data tergabung: {len(df_all)} baris.")

except FileNotFoundError as e:
    print(f"Error: File tidak ditemukan. {e}")
    print("Pastikan nama file dan foldernya sudah benar.")
    exit()

# ==========================================
# 2. DATA CLEANING & PREPARATION
# ==========================================
# Konversi Tanggal Laporan ke format DateTime
df_all['REPORT_DATE'] = pd.to_datetime(df_all['JOBREPORT_DATE'], dayfirst=True, errors='coerce')

# Buat kolom Bulan-Tahun untuk plot grafik (Contoh: 2023-01)
df_all['YYYYMM'] = df_all['REPORT_DATE'].dt.to_period('M')

# Filter: Hanya ambil pekerjaan yang statusnya sudah selesai (ada tanggal reportnya)
df_done = df_all.dropna(subset=['REPORT_DATE'])

# ==========================================
# 3. VISUALISASI TREN BULANAN (Grafik)
# ==========================================
print("Membuat grafik tren...")
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
# 4. ANALISIS FULL KOMPONEN & EXPORT CSV
# ==========================================
print("\nMenghitung statistik untuk SEMUA komponen...")

# Pivot table: Menjadikan Tahun sebagai kolom, Nama Komponen sebagai baris
# aggfunc='size' menghitung frekuensi kemunculan
pivot_full = df_done.pivot_table(index='COMPNAME', columns='SOURCE_YEAR', aggfunc='size', fill_value=0)

# Pastikan kolom tahun 2023, 2024, 2025 ada (untuk menghindari error jika data kosong)
for year in [2023, 2024, 2025]:
    if year not in pivot_full.columns:
        pivot_full[year] = 0

# Hitung Statistik Tambahan
pivot_full['TOTAL_3_TAHUN'] = pivot_full[2023] + pivot_full[2024] + pivot_full[2025]
pivot_full['TREN_24_vs_25'] = pivot_full[2025] - pivot_full[2024] # Positif berarti naik, Negatif berarti turun

# Urutkan data dari yang paling sering dimaintenance (High Frequency)
pivot_full = pivot_full.sort_values(by='TOTAL_3_TAHUN', ascending=False)

# Simpan hasil lengkap ke CSV
output_filename = 'Analisis_Maintenance_Lengkap_2023-2025.csv'
pivot_full.to_csv(output_filename)
print(f"[-] Data lengkap berhasil disimpan ke file: {output_filename}")

# ==========================================
# 5. INSIGHT & REKOMENDASI (Console Output)
# ==========================================
print("\n" + "="*50)
print("TOP 10 KOMPONEN PALING SERING MAINTENANCE (2023-2025)")
print("="*50)
print(pivot_full[[2023, 2024, 2025, 'TOTAL_3_TAHUN', 'TREN_24_vs_25']].head(10))

print("\n" + "="*50)
print("REKOMENDASI FORECASTING (Berdasarkan Top 20 Item)")
print("="*50)

# Ambil 20 item teratas untuk dianalisis trendnya
top_20_items = pivot_full.head(20)

for component_name, row in top_20_items.iterrows():
    diff = row['TREN_24_vs_25']
    total_2025 = row[2025]
    
    if diff > 0:
        # Jika tren naik
        print(f"[NAIK] {component_name}")
        print(f"   -> Aktivitas naik +{diff} job dibanding tahun lalu.")
        print(f"   -> Total 2025: {total_2025} job. SARAN: Tingkatkan stok sparepart terkait.")
    elif diff < 0:
        # Jika tren turun
        print(f"[TURUN] {component_name}")
        print(f"   -> Aktivitas turun {diff} job. (Cenderung aman/stabil)")
    else:
        print(f"[STABIL] {component_name} (Aktivitas sama dengan tahun lalu)")
    print("-" * 30)