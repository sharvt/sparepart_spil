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

# --- FUNGSI LOAD DATA (DIPERBAIKI) ---
@st.cache_data
def load_data():
    file_2024 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    file_2025 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx"
    
    try:
        # Load file Excel
        df1 = pd.read_excel(file_2024)
        df2 = pd.read_excel(file_2025)
        
        # Gabungkan data
        df = pd.concat([df1, df2], ignore_index=True)
        
        # --- PERBAIKAN UTAMA DI SINI ---
        # Daripada mengandalkan parsing tanggal yang sering error,
        # Kita gunakan kolom TAHUN dan BULAN yang sudah pasti ada angkanya.
        
        # 1. Pastikan TAHUN dan BULAN adalah angka
        df['TAHUN'] = pd.to_numeric(df['TAHUN'], errors='coerce').fillna(0).astype(int)
        df['BULAN'] = pd.to_numeric(df['BULAN'], errors='coerce').fillna(0).astype(int)
        
        # 2. Filter data sampah (Tahun 0 atau Bulan 0/13+)
        df = df[(df['TAHUN'] > 2000) & (df['BULAN'] >= 1) & (df['BULAN'] <= 12)]
        
        # 3. Buat kolom Month_Year Manual (Format: YYYY-MM)
        # Ini DIJAMIN akan mengurutkan data dengan benar dan tidak akan ada yang hilang
        df['Month_Year'] = df['TAHUN'].astype(str) + "-" + df['BULAN'].astype(str).str.zfill(2)
        
        # 4. Konversi JOBREPORT_DATE hanya untuk tampilan tabel (kosmetik)
        df['JOBREPORT_DATE'] = pd.to_datetime(df['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
        
        # 5. Konversi Running Hours
        df['RH_THIS_MONTH_UNTIL_JOBDONE'] = pd.to_numeric(df['RH_THIS_MONTH_UNTIL_JOBDONE'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data awal
df = load_data()

if not df.empty:
    # --- SIDEBAR: FILTER ---
    st.sidebar.header("🔍 Filter Data")
    
    # 1. Filter Tahun
    available_years = sorted(df['TAHUN'].unique())
    selected_years = st.sidebar.multiselect("Pilih Tahun", available_years, default=available_years)
    
    # 2. Filter Vessel (Kapal) dengan Opsi "ALL"
    vessel_list = sorted(df['VESSELID'].unique().tolist())
    vessel_options = ['ALL'] + vessel_list
    
    selected_vessels = st.sidebar.multiselect(
        "Pilih Kapal (Vessel ID)", 
        options=vessel_options, 
        default=['ALL'] 
    )
    
    # 3. Filter Tipe Frekuensi
    available_freq = sorted(df['FREQ_TYPE'].unique())
    selected_freq = st.sidebar.multiselect("Pilih Tipe Frekuensi", available_freq, default=available_freq)
    
    st.sidebar.markdown("---")
    # 4. Filter Saturday Routine
    exclude_saturday = st.sidebar.checkbox("Sembunyikan 'Saturday Routine'", value=True)
    st.sidebar.caption("Menyembunyikan pekerjaan rutin mingguan agar fokus pada analisis sparepart.")

    # --- FILTERING LOGIC ---
    if not selected_years: selected_years = available_years
    if not selected_freq: selected_freq = available_freq
    
    # Logic Vessel ALL
    if 'ALL' in selected_vessels or not selected_vessels:
        vessel_filter = df['VESSELID'].unique()
    else:
        vessel_filter = selected_vessels

    # Terapkan Filter
    filtered_df = df[
        (df['TAHUN'].isin(selected_years)) &
        (df['VESSELID'].isin(vessel_filter)) &
        (df['FREQ_TYPE'].isin(selected_freq))
    ]
    
    # DataFrame Khusus Analisis Komponen
    df_analysis = filtered_df.copy()
    if exclude_saturday:
        mask_saturday = (
            df_analysis['COMPNAME'].str.contains('Saturday Routine', case=False, na=False) | 
            df_analysis['JOBTITLE'].str.contains('Saturday Routine', case=False, na=False)
        )
        df_analysis = df_analysis[~mask_saturday]

    # --- BAGIAN UTAMA: KPI ---
    st.markdown("### 📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Maintenance (All)", f"{len(filtered_df):,}")

    with col2:
        st.metric("Total Kapal Terpilih", filtered_df['VESSELID'].nunique())

    with col3:
        if not df_analysis.empty:
            top_component = df_analysis['COMPNAME'].mode()[0]
        else:
            top_component = "-"
        st.metric("Komponen Terbanyak", top_component)

    with col4:
        avg_rh = filtered_df['RH_THIS_MONTH_UNTIL_JOBDONE'].mean()
        st.metric("Rata-rata Running Hours", f"{avg_rh:,.0f} Jam")

    st.markdown("---")

    # --- VISUALISASI UTAMA ---
    
    # Row 1: Tren Waktu & Distribusi Frekuensi
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.subheader("📈 Tren Maintenance Per Bulan")
        # Menggunakan data sesuai checkbox (df_analysis jika exclude, filtered_df jika include)
        data_trend = df_analysis if exclude_saturday else filtered_df
        
        if not data_trend.empty:
            # Grouping berdasarkan Month_Year yang sudah kita fix
            jobs_per_month = data_trend.groupby('Month_Year').size().reset_index(name='Count')
            jobs_per_month = jobs_per_month.sort_values('Month_Year')
            
            fig_trend = px.line(jobs_per_month, x='Month_Year', y='Count', markers=True, 
                                title="Jumlah Job Report per Bulan" + (" (Tanpa Saturday Routine)" if exclude_saturday else ""),
                                labels={'Month_Year': 'Bulan', 'Count': 'Jumlah Job'})
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    with row1_col2:
        st.subheader("🍩 Distribusi Tipe Frekuensi")
        if not filtered_df.empty:
            freq_counts = filtered_df['FREQ_TYPE'].value_counts().reset_index()
            freq_counts.columns = ['Tipe', 'Jumlah']
            
            fig_pie = px.pie(freq_counts, values='Jumlah', names='Tipe', 
                               title="Proporsi Tipe Maintenance",
                               hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    # --- VISUALISASI BARU: SPAREPART PER BULAN ---
    st.markdown("---")
    st.subheader("🏆 Analisis Sparepart Paling Sering Dimaintenance Per Bulan")
    
    col_viz_new, col_viz_opt = st.columns([3, 1])
    
    with col_viz_opt:
        st.markdown("**Pengaturan Grafik:**")
        top_n = st.slider("Jumlah Top Komponen:", min_value=3, max_value=15, value=5)
        
        if exclude_saturday:
            st.success("✅ Filter 'Saturday Routine' Aktif")
        else:
            st.warning("⚠️ Filter 'Saturday Routine' Non-Aktif")
    
    with col_viz_new:
        if not df_analysis.empty:
            # 1. Cari Top N komponen
            top_components_list = df_analysis['COMPNAME'].value_counts().head(top_n).index.tolist()
            
            # 2. Filter data
            df_top_comp = df_analysis[df_analysis['COMPNAME'].isin(top_components_list)]
            
            # 3. Group by (Menggunakan Month_Year yang sudah fix)
            comp_trend = df_top_comp.groupby(['Month_Year', 'COMPNAME']).size().reset_index(name='Count')
            comp_trend = comp_trend.sort_values('Month_Year')
            
            # 4. Plot
            fig_comp_trend = px.bar(comp_trend, x='Month_Year', y='Count', color='COMPNAME',
                                    title=f"Tren Maintenance Top {top_n} Komponen per Bulan",
                                    labels={'Month_Year': 'Bulan', 'Count': 'Jumlah Maintenance', 'COMPNAME': 'Sparepart'},
                                    text='Count')
            
            fig_comp_trend.update_traces(textposition='inside', textfont_size=10)
            st.plotly_chart(fig_comp_trend, use_container_width=True)
        else:
            st.info("Tidak ada data untuk visualisasi ini.")


    # Row 3: Analisis Kapal & Komponen (Total)
    row3_col1, row3_col2 = st.columns(2)

    with row3_col1:
        st.subheader("🚢 Top 10 Kapal dengan Maintenance Terbanyak")
        if not filtered_df.empty:
            top_vessels = filtered_df['VESSELID'].value_counts().head(10).reset_index()
            top_vessels.columns = ['Vessel ID', 'Jumlah Maintenance']
            
            fig_vessel = px.bar(top_vessels, x='Vessel ID', y='Jumlah Maintenance', text='Jumlah Maintenance',
                                color='Jumlah Maintenance', color_continuous_scale='Blues')
            st.plotly_chart(fig_vessel, use_container_width=True)

    with row3_col2:
        st.subheader("⚙️ Top 10 Komponen Maintained (Total)")
        if not df_analysis.empty:
            top_components = df_analysis['COMPNAME'].value_counts().head(10).reset_index()
            top_components.columns = ['Nama Komponen', 'Frekuensi']
            
            title_suffix = " (Tanpa Saturday Routine)" if exclude_saturday else ""
            
            fig_comp = px.bar(top_components, y='Nama Komponen', x='Frekuensi', orientation='h',
                              text='Frekuensi', color='Frekuensi', color_continuous_scale='Reds',
                              title=f"Top 10 Komponen{title_suffix}")
            fig_comp.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    # --- TABEL DATA DETAIL ---
    st.markdown("---")
    st.subheader("📋 Detail Data Laporan")
    
    with st.expander("Klik untuk melihat/menyembunyikan tabel data raw"):
        show_cols = ['JOBREPORT_DATE', 'VESSELID', 'JOBTITLE', 'COMPNAME', 'FREQ_TYPE', 'JOBFREQ', 'JOBREPORT_REMARK']
        st.dataframe(df_analysis[show_cols], use_container_width=True)
        
        csv = df_analysis.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data Terfilter sebagai CSV",
            data=csv,
            file_name='filtered_maintenance_data.csv',
            mime='text/csv',
        )

else:
    st.warning("Data belum dimuat. Pastikan file Excel berada di folder yang benar.")

# Footer
st.markdown("""
<div style='text-align: center; margin-top: 50px; font-size: small; color: grey;'>
    Dashboard Created with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)