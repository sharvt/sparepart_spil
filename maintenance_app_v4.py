import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    # Daftar file
    file_2024 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    file_2025 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx"
    
    try:
        # Load kedua file
        df1 = pd.read_excel(file_2024)
        df2 = pd.read_excel(file_2025)
        
        # Gabungkan data
        df = pd.concat([df1, df2], ignore_index=True)
        
        # Konversi kolom tanggal (format DD/MM/YYYY)
        df['JOBREPORT_DATE'] = pd.to_datetime(df['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
        
        # Buat kolom Bulan-Tahun untuk grouping
        df['Month_Year'] = df['JOBREPORT_DATE'].dt.to_period('M').astype(str)
        
        # Konversi kolom angka
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
    
    # 2. Filter Vessel (Kapal)
    available_vessels = sorted(df['VESSELID'].unique())
    selected_vessels = st.sidebar.multiselect("Pilih Kapal (Vessel ID)", available_vessels, default=available_vessels[:5]) # Default pilih 5 pertama agar tidak berat
    
    # 3. Filter Tipe Frekuensi (Hours/Months)
    available_freq = sorted(df['FREQ_TYPE'].unique())
    selected_freq = st.sidebar.multiselect("Pilih Tipe Frekuensi", available_freq, default=available_freq)
    
    # --- FILTERING LOGIC ---
    # Jika user tidak memilih filter, gunakan semua data (kecuali vessel default)
    if not selected_years:
        selected_years = available_years
    if not selected_vessels:
        selected_vessels = available_vessels
    if not selected_freq:
        selected_freq = available_freq

    filtered_df = df[
        (df['TAHUN'].isin(selected_years)) &
        (df['VESSELID'].isin(selected_vessels)) &
        (df['FREQ_TYPE'].isin(selected_freq))
    ]

    # --- BAGIAN UTAMA: KPI ---
    st.markdown("### 📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_jobs = len(filtered_df)
        st.metric("Total Maintenance", f"{total_jobs:,}")

    with col2:
        unique_vessels = filtered_df['VESSELID'].nunique()
        st.metric("Total Kapal Aktif", unique_vessels)

    with col3:
        # Komponen paling sering dimaintenance
        if not filtered_df.empty:
            top_component = filtered_df['COMPNAME'].mode()[0]
        else:
            top_component = "-"
        st.metric("Komponen Terbanyak", top_component)

    with col4:
        # Rata-rata Running Hours
        avg_rh = filtered_df['RH_THIS_MONTH_UNTIL_JOBDONE'].mean()
        st.metric("Rata-rata Running Hours", f"{avg_rh:,.0f} Jam")

    st.markdown("---")

    # --- VISUALISASI ---
    
    # Row 1: Tren Waktu & Distribusi Frekuensi
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.subheader("📈 Tren Maintenance Per Bulan")
        if not filtered_df.empty:
            jobs_per_month = filtered_df.groupby('Month_Year').size().reset_index(name='Count')
            jobs_per_month = jobs_per_month.sort_values('Month_Year')
            
            fig_trend = px.line(jobs_per_month, x='Month_Year', y='Count', markers=True, 
                                title="Jumlah Job Report per Bulan",
                                labels={'Month_Year': 'Bulan', 'Count': 'Jumlah Job'})
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Tidak ada data untuk ditampilkan.")

    with row1_col2:
        st.subheader("🍩 Distribusi Tipe Frekuensi")
        if not filtered_df.empty:
            freq_counts = filtered_df['FREQ_TYPE'].value_counts().reset_index()
            freq_counts.columns = ['Tipe', 'Jumlah']
            
            # GUNAKAN px.pie DENGAN PARAMETER hole UNTUK MEMBUAT DONUT CHART
            fig_pie = px.pie(freq_counts, values='Jumlah', names='Tipe', 
                               title="Proporsi Tipe Maintenance (Hours vs Months)",
                               hole=0.4) # Parameter hole ini yang mengubah Pie menjadi Donut
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    # Row 2: Analisis Kapal & Komponen
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("🚢 Top 10 Kapal dengan Maintenance Terbanyak")
        if not filtered_df.empty:
            top_vessels = filtered_df['VESSELID'].value_counts().head(10).reset_index()
            top_vessels.columns = ['Vessel ID', 'Jumlah Maintenance']
            
            fig_vessel = px.bar(top_vessels, x='Vessel ID', y='Jumlah Maintenance', text='Jumlah Maintenance',
                                color='Jumlah Maintenance', color_continuous_scale='Blues')
            st.plotly_chart(fig_vessel, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    with row2_col2:
        st.subheader("⚙️ Top 10 Komponen Maintained")
        if not filtered_df.empty:
            top_components = filtered_df['COMPNAME'].value_counts().head(10).reset_index()
            top_components.columns = ['Nama Komponen', 'Frekuensi']
            
            fig_comp = px.bar(top_components, y='Nama Komponen', x='Frekuensi', orientation='h',
                              text='Frekuensi', color='Frekuensi', color_continuous_scale='Reds')
            fig_comp.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    # --- TABEL DATA DETAIL ---
    st.markdown("---")
    st.subheader("📋 Detail Data Laporan")
    
    with st.expander("Klik untuk melihat/menyembunyikan tabel data raw"):
        # Menampilkan kolom-kolom penting saja agar tabel rapi
        show_cols = ['JOBREPORT_DATE', 'VESSELID', 'JOBTITLE', 'COMPNAME', 'FREQ_TYPE', 'JOBFREQ', 'JOBREPORT_REMARK']
        st.dataframe(filtered_df[show_cols], use_container_width=True)
        
        # Download Button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data Terfilter sebagai CSV",
            data=csv,
            file_name='filtered_maintenance_data.csv',
            mime='text/csv',
        )

else:
    st.warning("Data belum dimuat. Pastikan file CSV berada di folder yang sama.")

# Footer
st.markdown("""
<div style='text-align: center; margin-top: 50px; font-size: small; color: grey;'>
    Dashboard Created with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)
