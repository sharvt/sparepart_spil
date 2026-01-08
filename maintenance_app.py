import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dashboard Maintenance 2023-2025",
    page_icon="🛠️",
    layout="wide"
)

# ==========================================
# KONFIGURASI FILE (HARDCODED)
# ==========================================
FILE_2023 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2023.xlsx'
FILE_2024 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx'
FILE_2025 = 'Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx'

# ==========================================
# KONFIGURASI TEMA (MERAH/ALERT)
# ==========================================
main_color = '#e74c3c'   # Merah Terang
cmap_heat = 'Reds'       # Skala Heatmap Merah
palette_bar = 'Reds_r'   # Gradasi Merah

# ==========================================
# FUNGSI LOAD DATA
# ==========================================
@st.cache_data
def load_data():
    try:
        # Load Data
        df_23 = pd.read_excel(FILE_2023)
        df_24 = pd.read_excel(FILE_2024)
        df_25 = pd.read_excel(FILE_2025)

        df_23['SOURCE_YEAR'] = 2023
        df_24['SOURCE_YEAR'] = 2024
        df_25['SOURCE_YEAR'] = 2025

        df_all = pd.concat([df_23, df_24, df_25], ignore_index=True)
        return df_all, None

    except FileNotFoundError as e:
        return None, f"File tidak ditemukan: {e}"
    except Exception as e:
        return None, f"Terjadi kesalahan: {e}"

# ==========================================
# LOGIKA UTAMA
# ==========================================
st.title("🛠️ Dashboard Visualisasi Maintenance")
st.markdown("Monitoring kinerja maintenance armada, analisis komponen, dan distribusi beban kerja.")

with st.spinner('Sedang memuat & memproses data...'):
    df_maint, error_msg = load_data()

if error_msg:
    st.error(error_msg)
    st.stop()

if df_maint is not None:
    # --- DATA CLEANING ---
    df_maint['REPORT_DATE'] = pd.to_datetime(df_maint['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
    df_maint['YYYYMM'] = df_maint['REPORT_DATE'].dt.to_period('M')
    
    # Ambil data yang valid (sudah dikerjakan)
    df_done = df_maint.dropna(subset=['REPORT_DATE'])
    
    # Sidebar Info
    st.sidebar.title("Info Dashboard")
    st.sidebar.info(f"Total Pekerjaan Selesai:\n**{len(df_done):,}** Job")
    st.sidebar.caption("Periode Data: 2023 - 2025")
    
    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # ==========================================
    # TABS DASHBOARD
    # ==========================================
    tab1, tab2, tab3 = st.tabs(["📈 Tren Waktu", "📊 Dashboard Visualisasi", "📋 Tabel MTBF"])

    # --- TAB 1: TREN WAKTU ---
    with tab1:
        st.subheader("Tren Aktivitas Maintenance Bulanan")
        monthly_trend = df_done.groupby('YYYYMM').size()
        monthly_trend.index = monthly_trend.index.astype(str)
        
        fig, ax = plt.subplots(figsize=(15, 5))
        ax.plot(monthly_trend.index, monthly_trend.values, marker='o', color=main_color, linewidth=2.5)
        ax.fill_between(monthly_trend.index, monthly_trend.values, color=main_color, alpha=0.1)
        ax.set_title('Total Pekerjaan per Bulan', fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    # --- TAB 2: VISUALISASI UTAMA + TABEL TOP ---
    with tab2:
        st.subheader("Analisis Mendalam (Deep Dive)")
        
        # ROW 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 1. Top 10 Kapal Paling Sibuk Maintenance")
            top_vessels = df_done['VESSELID'].value_counts().head(10)
            
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            sns.barplot(x=top_vessels.values, y=top_vessels.index, palette=palette_bar, ax=ax1)
            ax1.set_xlabel("Jumlah Pekerjaan")
            st.pyplot(fig1)
            
        with col2:
            st.markdown("#### 2. Distribusi Tipe Frekuensi")
            freq_dist = df_done['FREQ_TYPE'].value_counts()
            
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            colors = sns.color_palette(palette_bar, len(freq_dist))
            ax2.pie(freq_dist.values, labels=freq_dist.index, autopct='%1.1f%%', startangle=90, colors=colors)
            ax2.axis('equal')  
            st.pyplot(fig2)

        st.divider()

        # ROW 2
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### 3. Top 10 Maker (Pabrikan) yang Sparepartnya Sering Maintenance")
            valid_makers = df_done[~df_done['MAKERS_NAME'].isin([0, '0', '-'])] 
            top_makers = valid_makers['MAKERS_NAME'].value_counts().head(10)
            
            fig3, ax3 = plt.subplots(figsize=(8, 5))
            sns.barplot(x=top_makers.values, y=top_makers.index, palette=palette_bar, ax=ax3)
            ax3.set_xlabel("Frekuensi Maintenance")
            st.pyplot(fig3)
            
        with col4:
            st.markdown("#### 4. Top 10 Judul Pekerjaan (Job Title)")
            top_jobs = df_done['JOBTITLE'].value_counts().head(10)
            
            fig4, ax4 = plt.subplots(figsize=(8, 5))
            sns.barplot(x=top_jobs.values, y=top_jobs.index, palette=palette_bar, ax=ax4)
            ax4.set_xlabel("Jumlah")
            st.pyplot(fig4)
            
        st.divider()
        
        # ROW 3: HEATMAP (FULL WIDTH)
        st.markdown("#### 5. Heatmap Kesibukan: Kapal vs Bulan")
        df_done['BulanNum'] = df_done['REPORT_DATE'].dt.month
        top_15_vessels_list = df_done['VESSELID'].value_counts().head(15).index
        df_heat = df_done[df_done['VESSELID'].isin(top_15_vessels_list)]
        
        heatmap_data = df_heat.pivot_table(index='VESSELID', columns='BulanNum', aggfunc='size', fill_value=0)
        
        fig5, ax5 = plt.subplots(figsize=(15, 6))
        sns.heatmap(heatmap_data, cmap=cmap_heat, linewidths=.5, ax=ax5, cbar_kws={'label': 'Jumlah Job'})
        ax5.set_xlabel("Bulan (1-12)")
        st.pyplot(fig5)
        
        st.divider()

        st.subheader("📋 Tabel Data Peringkat Tertinggi")
        
        st.markdown("##### 🏆 Top 10 Komponen Paling Sering Dirawat")
        top_comp_table = df_done['COMPNAME'].value_counts().head(10).reset_index()
        top_comp_table.columns = ['Nama Komponen', 'Frekuensi']
        # Reset index agar mulai dari 1
        top_comp_table.index += 1
        st.dataframe(top_comp_table, use_container_width=True)

        st.divider()

        st.markdown("##### 📝 Top 10 Deskripsi Pekerjaan (Detail)")
        # Menggunakan JOBDESC agar lebih detail daripada JOBTITLE
        top_desc_table = df_done['JOBDESC'].value_counts().head(10).reset_index()
        top_desc_table.columns = ['Deskripsi Pekerjaan', 'Frekuensi']
        top_desc_table.index += 1
        st.dataframe(top_desc_table, use_container_width=True)

        st.divider()

        st.markdown("##### 🏆 Top 10 Maker")
        top_maker_table = valid_makers['MAKERS_NAME'].value_counts().head(10).reset_index()
        top_maker_table.columns = ['Nama Maker', 'Jumlah Job']
        top_maker_table.index += 1
        st.dataframe(top_maker_table, use_container_width=True)

    # --- TAB 3: TABEL ANALISIS & MTBF ---
    with tab3:
        st.subheader("Data Analisis Komponen & MTBF")
        
        # Hitung MTBF
        df_mtbf = df_done.sort_values(by=['VESSELID', 'COMPNAME', 'REPORT_DATE'])
        df_mtbf['NEXT_JOB_DATE'] = df_mtbf.groupby(['VESSELID', 'COMPNAME'])['REPORT_DATE'].shift(-1)
        df_mtbf['DAYS_BETWEEN'] = (df_mtbf['NEXT_JOB_DATE'] - df_mtbf['REPORT_DATE']).dt.days
        
        mtbf_valid = df_mtbf[df_mtbf['DAYS_BETWEEN'] > 0]
        mtbf_summary = mtbf_valid.groupby('COMPNAME')['DAYS_BETWEEN'].agg(['mean', 'count']).reset_index()
        mtbf_summary.columns = ['COMPNAME', 'MTBF_HARI', 'TOTAL_KEJADIAN']
        mtbf_summary['MTBF_HARI'] = mtbf_summary['MTBF_HARI'].round(1)
        
        # Pivot Tahunan
        pivot_full = df_done.pivot_table(index='COMPNAME', columns='SOURCE_YEAR', aggfunc='size', fill_value=0)
        for year in [2023, 2024, 2025]:
            if year not in pivot_full.columns: pivot_full[year] = 0
            
        pivot_full = pivot_full.reset_index()
        final_analysis = pd.merge(pivot_full, mtbf_summary, on='COMPNAME', how='left')
        
        final_analysis['TOTAL_3_TAHUN'] = final_analysis[2023] + final_analysis[2024] + final_analysis[2025]
        final_analysis['MTBF_HARI'] = final_analysis['MTBF_HARI'].fillna("-")
        
        # Ranking
        final_analysis = final_analysis.sort_values(by='TOTAL_3_TAHUN', ascending=False)
        final_analysis = final_analysis.reset_index(drop=True)
        final_analysis.index = final_analysis.index + 1 
        
        st.dataframe(final_analysis, use_container_width=True)
        
        csv = final_analysis.to_csv().encode('utf-8')
        st.download_button("📥 Download Tabel CSV", csv, "Analisis_Maintenance.csv", "text/csv")