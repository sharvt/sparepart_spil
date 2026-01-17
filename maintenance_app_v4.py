import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Maintenance Job Dashboard",
    page_icon="🔧",
    layout="wide"
)

# --- JUDUL DASHBOARD ---
st.title("🚢 Vessel Maintenance Job Dashboard")
st.markdown("Dashboard interaktif untuk memonitor laporan pekerjaan maintenance kapal tahun 2024-2025.")

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # Path file
    file_2024 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    file_2025 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx"
    
    try:
        # Load data
        df1 = pd.read_excel(file_2024)
        df2 = pd.read_excel(file_2025)
        
        # Gabungkan data
        df = pd.concat([df1, df2], ignore_index=True)
        
        # --- DATA CLEANING ---
        # 1. Pastikan TAHUN dan BULAN adalah angka
        df['TAHUN'] = pd.to_numeric(df['TAHUN'], errors='coerce').fillna(0).astype(int)
        df['BULAN'] = pd.to_numeric(df['BULAN'], errors='coerce').fillna(0).astype(int)
        
        # 2. Filter data valid
        df = df[(df['TAHUN'] > 2000) & (df['BULAN'] >= 1) & (df['BULAN'] <= 12)]
        
        # 3. Buat kolom Month_Year
        df['Month_Year'] = df['TAHUN'].astype(str) + "-" + df['BULAN'].astype(str).str.zfill(2)
        
        # 4. Handle Missing Values String
        df['COMPNAME'] = df['COMPNAME'].astype(str).fillna("-")
        df['JOBTITLE'] = df['JOBTITLE'].astype(str).fillna("-")
        df['VESSELID'] = df['VESSELID'].astype(str).fillna("Unknown")
        
        # 5. Konversi Running Hours
        df['RH_THIS_MONTH_UNTIL_JOBDONE'] = pd.to_numeric(df['RH_THIS_MONTH_UNTIL_JOBDONE'], errors='coerce').fillna(0)
        
        # 6. Kosmetik Tanggal
        df['JOBREPORT_DATE'] = pd.to_datetime(df['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data awal
df = load_data()

if not df.empty:
    # --- SIDEBAR: FILTER ---
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Tahun
    all_years = sorted(df['TAHUN'].unique())
    selected_years = st.sidebar.multiselect("Pilih Tahun", all_years, default=all_years)
    
    # Filter Vessel (Logic 'ALL')
    all_vessels = sorted(df['VESSELID'].unique().tolist())
    vessel_options = ['ALL'] + all_vessels
    
    selected_vessels = st.sidebar.multiselect(
        "Pilih Kapal (Vessel ID)", 
        options=vessel_options, 
        default=['ALL']
    )
    
    # Filter Tipe Frekuensi
    all_freqs = sorted(df['FREQ_TYPE'].unique())
    selected_freqs = st.sidebar.multiselect("Pilih Tipe Frekuensi", all_freqs, default=all_freqs)
    
    st.sidebar.markdown("---")
    
    # --- FILTER BERDASARKAN RUNNING HOURS (RH) ---
    # Ini jauh lebih akurat daripada filter teks
    exclude_zero_rh = st.sidebar.checkbox("Hanya Tampilkan Running Hours > 0", value=True)
    st.sidebar.caption("Jika dicentang, dashboard HANYA menampilkan pekerjaan mesin yang beroperasi (exclude monthly checking/inspeksi rutin).")

    # --- PENERAPAN FILTER ---
    
    # Handle default (jika kosong)
    if not selected_years: selected_years = all_years
    if not selected_freqs: selected_freqs = all_freqs
    
    # Logic Vessel ALL
    if 'ALL' in selected_vessels or not selected_vessels:
        vessel_filter = df['VESSELID'].unique()
    else:
        vessel_filter = selected_vessels

    # 1. Filter Utama
    filtered_df = df[
        (df['TAHUN'].isin(selected_years)) &
        (df['VESSELID'].isin(vessel_filter)) &
        (df['FREQ_TYPE'].isin(selected_freqs))
    ]
    
    # 2. Filter Running Hours
    df_analysis = filtered_df.copy()
    
    if exclude_zero_rh:
        # HANYA AMBIL DATA DENGAN RH > 0
        df_analysis = df_analysis[df_analysis['RH_THIS_MONTH_UNTIL_JOBDONE'] > 0]

    # --- KPI SUMMARY ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric("Total Jobs (Filtered)", f"{len(df_analysis):,}") 

    with kpi2:
        st.metric("Total Kapal Aktif", df_analysis['VESSELID'].nunique())

    with kpi3:
        if not df_analysis.empty:
            top_comp_name = df_analysis['COMPNAME'].mode()[0]
        else:
            top_comp_name = "-"
        st.metric("Top Komponen", top_comp_name)

    with kpi4:
        if not df_analysis.empty:
            avg_rh = df_analysis['RH_THIS_MONTH_UNTIL_JOBDONE'].mean()
        else:
            avg_rh = 0
        st.metric("Rata-rata Running Hours", f"{avg_rh:,.0f} Jam")

    st.markdown("---")

    # --- VISUALISASI UTAMA ---
    
    # Row 1: Tren & Distribusi
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.subheader("📈 Tren Maintenance Per Bulan")
        
        if not df_analysis.empty:
            jobs_per_month = df_analysis.groupby('Month_Year').size().reset_index(name='Count')
            jobs_per_month = jobs_per_month.sort_values('Month_Year')
            
            suffix = " (RH > 0)" if exclude_zero_rh else " (Semua)"
            
            fig_trend = px.line(jobs_per_month, x='Month_Year', y='Count', markers=True, 
                                title=f"Jumlah Job Report per Bulan{suffix}",
                                labels={'Month_Year': 'Bulan', 'Count': 'Jumlah Job'})
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Tidak ada data tren.")

    with row1_col2:
        st.subheader("🍩 Distribusi Tipe Frekuensi")
        if not df_analysis.empty:
            freq_counts = df_analysis['FREQ_TYPE'].value_counts().reset_index()
            freq_counts.columns = ['Tipe', 'Jumlah']
            
            fig_pie = px.pie(freq_counts, values='Jumlah', names='Tipe', 
                               hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Tidak ada data distribusi.")

    # --- VISUALISASI LEVEL 2: SPAREPART (URUTAN SESUAI RANKING) ---
    st.markdown("---")
    st.subheader("🏆 Analisis Sparepart & Komponen")
    
    col_viz_new, col_viz_right = st.columns([2, 1])
    
    with col_viz_new:
        if not df_analysis.empty:
            st.write("**Tren Komponen Paling Sering Di-Maintenance:**")
            
            # Slider
            top_n = st.slider("Jumlah Top Komponen:", min_value=3, max_value=15, value=5)
            
            # 1. Cari Top N komponen (List ini sudah URUT dari Terbanyak ke Sedikit)
            top_comps = df_analysis['COMPNAME'].value_counts().head(top_n).index.tolist()
            
            # 2. Filter data
            df_trend_comp = df_analysis[df_analysis['COMPNAME'].isin(top_comps)]
            
            # 3. Grouping
            comp_trend = df_trend_comp.groupby(['Month_Year', 'COMPNAME']).size().reset_index(name='Count')
            comp_trend = comp_trend.sort_values('Month_Year')
            
            # 4. Plot dengan URUTAN (Category Orders)
            fig_comp_trend = px.bar(
                comp_trend, 
                x='Month_Year', 
                y='Count', 
                color='COMPNAME',
                labels={'Month_Year': 'Bulan', 'Count': 'Frekuensi', 'COMPNAME': 'Sparepart'},
                text='Count',
                # Memaksa urutan warna sesuai ranking
                category_orders={'COMPNAME': top_comps} 
            )
            
            fig_comp_trend.update_traces(textposition='inside', textfont_size=10)
            st.plotly_chart(fig_comp_trend, use_container_width=True)
        else:
            st.info("Data kosong setelah filter diterapkan.")

    # --- CHART KANAN: TOP 10 TOTAL ---
    with col_viz_right:
        st.write("**Top 10 Komponen (Total Periode):**")
        if not df_analysis.empty:
            top_components = df_analysis['COMPNAME'].value_counts().head(10).reset_index()
            top_components.columns = ['Nama Komponen', 'Frekuensi']
            
            fig_comp = px.bar(top_components, y='Nama Komponen', x='Frekuensi', orientation='h',
                              text='Frekuensi', color='Frekuensi', color_continuous_scale='Reds')
            fig_comp.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    # --- ANALISIS KAPAL ---
    st.markdown("---")
    st.subheader("🚢 Aktivitas Kapal")
    
    if not df_analysis.empty:
        top_vessels = df_analysis['VESSELID'].value_counts().head(15).reset_index()
        top_vessels.columns = ['Vessel ID', 'Jumlah Maintenance']
        
        fig_vessel = px.bar(top_vessels, x='Vessel ID', y='Jumlah Maintenance', text='Jumlah Maintenance',
                            color='Jumlah Maintenance', color_continuous_scale='Blues',
                            title="Top Kapal dengan Maintenance Terbanyak")
        st.plotly_chart(fig_vessel, use_container_width=True)

    # --- TABEL DATA ---
    st.markdown("---")
    
    with st.expander("📄 Lihat Detail Data (Tabel)"):
        show_cols = ['JOBREPORT_DATE', 'VESSELID', 'COMPNAME', 'JOBTITLE', 'FREQ_TYPE', 'RH_THIS_MONTH_UNTIL_JOBDONE', 'JOBREPORT_REMARK']
        st.dataframe(df_analysis[show_cols], use_container_width=True)
        
        csv = df_analysis.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data CSV",
            data=csv,
            file_name='filtered_maintenance_data.csv',
            mime='text/csv',
        )

else:
    st.warning("⚠️ Data belum dimuat. Pastikan file Excel tersedia di folder yang benar.")

# Footer
st.markdown("""
<div style='text-align: center; margin-top: 50px; font-size: small; color: grey;'>
    Dashboard Created with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)
