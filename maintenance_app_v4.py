import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Vessel Maintenance Dashboard",
    page_icon="🚢",
    layout="wide"
)

# --- JUDUL DASHBOARD ---
st.title("🚢 Vessel Maintenance Job Dashboard")
st.markdown("Dashboard interaktif untuk memonitor laporan pekerjaan maintenance kapal tahun 2024-2025.")

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # Path file (Sesuaikan dengan struktur folder GitHub Anda)
    file_2024 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    file_2025 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx"
    
    try:
        # Load file Excel (Hanya kolom yang dibutuhkan agar lebih ringan)
        cols_needed = [
            'VESSELID', 'TAHUN', 'BULAN', 'COMPNAME', 'FREQ_TYPE', 
            'JOBTITLE', 'JOBREPORT_DATE', 'RH_THIS_MONTH_UNTIL_JOBDONE', 
            'JOBREPORT_REMARK', 'JOBFREQ'
        ]
        
        # Load dengan error handling per file
        try:
            df1 = pd.read_excel(file_2024, usecols=lambda x: x in cols_needed)
        except:
            df1 = pd.DataFrame()
            
        try:
            df2 = pd.read_excel(file_2025, usecols=lambda x: x in cols_needed)
        except:
            df2 = pd.DataFrame()
        
        df = pd.concat([df1, df2], ignore_index=True)
        
        if df.empty:
            return pd.DataFrame()

        # --- DATA CLEANING & PREPARATION ---
        
        # 1. Fix TAHUN & BULAN (Pastikan Angka)
        df['TAHUN'] = pd.to_numeric(df['TAHUN'], errors='coerce').fillna(0).astype(int)
        df['BULAN'] = pd.to_numeric(df['BULAN'], errors='coerce').fillna(0).astype(int)
        
        # 2. Filter Tanggal Valid
        df = df[(df['TAHUN'] > 2000) & (df['BULAN'] >= 1) & (df['BULAN'] <= 12)]
        
        # 3. Buat Kolom Month_Year (Kunci agar grafik waktu muncul)
        df['Month_Year'] = df['TAHUN'].astype(str) + "-" + df['BULAN'].astype(str).str.zfill(2)
        
        # 4. Handle Missing Values pada Text
        df['COMPNAME'] = df['COMPNAME'].astype(str).fillna("-")
        df['JOBTITLE'] = df['JOBTITLE'].astype(str).fillna("-")
        df['VESSELID'] = df['VESSELID'].astype(str).fillna("Unknown")
        
        # 5. Konversi Angka Lainnya
        df['RH_THIS_MONTH_UNTIL_JOBDONE'] = pd.to_numeric(df['RH_THIS_MONTH_UNTIL_JOBDONE'], errors='coerce').fillna(0)
        
        # 6. Kosmetik Tanggal Laporan
        df['JOBREPORT_DATE'] = pd.to_datetime(df['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
        return pd.DataFrame()

# Load Data
df = load_data()

if not df.empty:
    # --- SIDEBAR: FILTER ---
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Tahun
    all_years = sorted(df['TAHUN'].unique())
    sel_years = st.sidebar.multiselect("Pilih Tahun", all_years, default=all_years)
    
    # Filter Vessel (Logic 'ALL')
    all_vessels = sorted(df['VESSELID'].unique().tolist())
    sel_vessels = st.sidebar.multiselect("Pilih Kapal", ['ALL'] + all_vessels, default=['ALL'])
    
    # Filter Frekuensi
    all_freqs = sorted(df['FREQ_TYPE'].unique())
    sel_freqs = st.sidebar.multiselect("Pilih Frekuensi", all_freqs, default=all_freqs)
    
    st.sidebar.markdown("---")
    
    # Filter Saturday Routine
    exclude_saturday = st.sidebar.checkbox("Sembunyikan 'Saturday Routine'", value=True)
    st.sidebar.caption("Menyembunyikan maintenance rutin mingguan agar grafik fokus pada sparepart.")

    # --- PENERAPAN FILTER ---
    
    # 1. Handle default values (jika user hapus semua pilihan)
    if not sel_years: sel_years = all_years
    if not sel_freqs: sel_freqs = all_freqs
    
    # 2. Handle Vessel ALL
    if 'ALL' in sel_vessels or not sel_vessels:
        vessel_filter = all_vessels
    else:
        vessel_filter = sel_vessels

    # 3. Filter DataFrame Utama
    filtered_df = df[
        (df['TAHUN'].isin(sel_years)) &
        (df['VESSELID'].isin(vessel_filter)) &
        (df['FREQ_TYPE'].isin(sel_freqs))
    ]
    
    # 4. Buat DataFrame Khusus Analisis (Handle Saturday Routine)
    df_analysis = filtered_df.copy()
    if exclude_saturday:
        # Filter Case-Insensitive untuk kata 'Saturday' di Nama Komponen atau Judul Job
        mask_saturday = (
            df_analysis['COMPNAME'].str.contains('Saturday', case=False) | 
            df_analysis['JOBTITLE'].str.contains('Saturday', case=False)
        )
        df_analysis = df_analysis[~mask_saturday]

    # --- KPI SUMMARY ---
    st.markdown("### 📊 Ringkasan Maintenance")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    kpi1.metric("Total Jobs", f"{len(filtered_df):,}")
    kpi2.metric("Kapal Aktif", filtered_df['VESSELID'].nunique())
    
    # Komponen terbanyak (dari data yang sudah dibersihkan saturday routine)
    top_comp_name = df_analysis['COMPNAME'].mode()[0] if not df_analysis.empty else "-"
    kpi3.metric("Top Komponen", top_comp_name)
    
    avg_rh = int(filtered_df['RH_THIS_MONTH_UNTIL_JOBDONE'].mean()) if not filtered_df.empty else 0
    kpi4.metric("Avg Running Hours", f"{avg_rh:,} H")

    st.markdown("---")

    # --- VISUALISASI LEVEL 1: OVERVIEW ---
    
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.subheader("📈 Tren Maintenance Bulanan")
        # Gunakan df_analysis jika exclude saturday aktif agar tren sesuai konteks
        data_trend = df_analysis if exclude_saturday else filtered_df
        
        if not data_trend.empty:
            trend_data = data_trend.groupby('Month_Year').size().reset_index(name='Jumlah')
            trend_data = trend_data.sort_values('Month_Year')
            
            fig_line = px.line(
                trend_data, x='Month_Year', y='Jumlah', markers=True,
                title="Jumlah Laporan per Bulan",
                labels={'Month_Year': 'Periode', 'Jumlah': 'Total Job'}
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Tidak ada data tren.")

    with col_chart2:
        st.subheader("🍩 Distribusi Tipe")
        if not filtered_df.empty:
            dist_data = filtered_df['FREQ_TYPE'].value_counts().reset_index()
            dist_data.columns = ['Tipe', 'Jumlah']
            
            fig_pie = px.pie(
                dist_data, values='Jumlah', names='Tipe', 
                hole=0.4, title="Hours vs Months"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Tidak ada data distribusi.")

    # --- VISUALISASI LEVEL 2: ANALISIS SPAREPART (YANG SEBELUMNYA HILANG) ---
    st.markdown("---")
    st.subheader("🏆 Analisis Sparepart & Komponen")
    
    # Layout: Kiri (Stacked Bar per Bulan), Kanan (Top 10 Total)
    col_viz_new, col_viz_total = st.columns([2, 1])
    
    # --- CHART KIRI: TREN SPAREPART PER BULAN ---
    with col_viz_new:
        if not df_analysis.empty:
            # Slider interaktif
            top_n = st.slider("Jumlah Top Komponen untuk Ditampilkan:", 3, 15, 5)
            
            # 1. Ambil Top N Komponen
            top_comps = df_analysis['COMPNAME'].value_counts().head(top_n).index.tolist()
            
            # 2. Filter Data
            df_trend_comp = df_analysis[df_analysis['COMPNAME'].isin(top_comps)]
            
            # 3. Grouping
            if not df_trend_comp.empty:
                trend_grouped = df_trend_comp.groupby(['Month_Year', 'COMPNAME']).size().reset_index(name='Count')
                trend_grouped = trend_grouped.sort_values('Month_Year')
                
                # 4. Plot Stacked Bar
                fig_stacked = px.bar(
                    trend_grouped, x='Month_Year', y='Count', color='COMPNAME',
                    title=f"Tren Top {top_n} Sparepart per Bulan",
                    labels={'Count': 'Frekuensi Maintenance', 'Month_Year': 'Bulan'},
                    text='Count'
                )
                fig_stacked.update_traces(textposition='inside', textfont_size=10)
                st.plotly_chart(fig_stacked, use_container_width=True)
            else:
                st.warning("Data tidak cukup untuk membuat grafik tren komponen.")
        else:
            st.info("Data kosong setelah filter diterapkan.")

    # --- CHART KANAN: TOP 10 SPAREPART TOTAL ---
    with col_viz_total:
        if not df_analysis.empty:
            top_10_total = df_analysis['COMPNAME'].value_counts().head(10).reset_index()
            top_10_total.columns = ['Komponen', 'Total']
            
            fig_bar_h = px.bar(
                top_10_total, y='Komponen', x='Total', orientation='h',
                color='Total', color_continuous_scale='Reds',
                text='Total', title="Top 10 Komponen (Total)"
            )
            fig_bar_h.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar_h, use_container_width=True)
        else:
            st.info("Data kosong.")

    # --- VISUALISASI LEVEL 3: KAPAL ---
    st.markdown("---")
    st.subheader("🚢 Aktivitas Kapal")
    
    if not filtered_df.empty:
        top_vessels = filtered_df['VESSELID'].value_counts().head(15).reset_index()
        top_vessels.columns = ['Kapal', 'Jumlah Job']
        
        fig_vessel = px.bar(
            top_vessels, x='Kapal', y='Jumlah Job', 
            color='Jumlah Job', text='Jumlah Job',
            title="Top Kapal dengan Maintenance Terbanyak"
        )
        st.plotly_chart(fig_vessel, use_container_width=True)

    # --- TABEL DATA ---
    st.markdown("---")
    with st.expander("📄 Lihat Detail Data (Tabel)"):
        # Tampilkan kolom yang relevan saja
        display_cols = ['JOBREPORT_DATE', 'VESSELID', 'COMPNAME', 'JOBTITLE', 'FREQ_TYPE', 'JOBREPORT_REMARK']
        st.dataframe(df_analysis[display_cols], use_container_width=True)
        
        # Download Button
        csv_data = df_analysis.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data CSV",
            data=csv_data,
            file_name="maintenance_data_filtered.csv",
            mime="text/csv"
        )

else:
    st.warning("⚠️ Data belum dimuat. Pastikan file Excel tersedia di folder 'Magang Sparepart 2025' di GitHub Anda.")
