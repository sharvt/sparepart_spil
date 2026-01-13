import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Maintenance Dashboard (Debug Mode)",
    page_icon="🔧",
    layout="wide"
)

st.title("🚢 Vessel Maintenance Job Dashboard")

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # Menggunakan forward slash (/)
    file_2024 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    file_2025 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx"
    
    try:
        # Load file Excel (hanya kolom penting untuk menghemat memori)
        cols = ['VCJOBID', 'VESSELID', 'TAHUN', 'BULAN', 'COMPNAME', 'FREQ_TYPE', 'JOBTITLE', 'JOBREPORT_DATE', 'RH_THIS_MONTH_UNTIL_JOBDONE', 'JOBREPORT_REMARK', 'JOBFREQ']
        
        df1 = pd.read_excel(file_2024, usecols=lambda x: x in cols)
        df2 = pd.read_excel(file_2025, usecols=lambda x: x in cols)
        
        df = pd.concat([df1, df2], ignore_index=True)
        
        # LOGIKA TANGGAL & DATA CLEANING
        df['TAHUN'] = pd.to_numeric(df['TAHUN'], errors='coerce').fillna(0).astype(int)
        df['BULAN'] = pd.to_numeric(df['BULAN'], errors='coerce').fillna(0).astype(int)
        
        # Hapus data tahun/bulan invalid
        df = df[(df['TAHUN'] > 2000) & (df['BULAN'] >= 1) & (df['BULAN'] <= 12)]
        
        # Buat kolom Month_Year
        df['Month_Year'] = df['TAHUN'].astype(str) + "-" + df['BULAN'].astype(str).str.zfill(2)
        
        # Pastikan kolom string terisi
        df['COMPNAME'] = df['COMPNAME'].astype(str).fillna("-")
        df['JOBTITLE'] = df['JOBTITLE'].astype(str).fillna("-")
        
        df['RH_THIS_MONTH_UNTIL_JOBDONE'] = pd.to_numeric(df['RH_THIS_MONTH_UNTIL_JOBDONE'], errors='coerce').fillna(0)
        
        # Kosmetik tanggal
        df['JOBREPORT_DATE'] = pd.to_datetime(df['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
        
        return df
    except Exception as e:
        return str(e) # Return error message string

# Load data
data_raw = load_data()

# Cek apakah load data berhasil atau error
if isinstance(data_raw, str):
    st.error(f"❌ CRITICAL ERROR saat Load Data: {data_raw}")
    st.stop()
else:
    df = data_raw

if not df.empty:
    # --- SIDEBAR ---
    st.sidebar.header("🔍 Filter Data")
    
    years = sorted(df['TAHUN'].unique())
    sel_years = st.sidebar.multiselect("Tahun", years, default=years)
    
    vessels = sorted(df['VESSELID'].unique().tolist())
    sel_vessels = st.sidebar.multiselect("Kapal", ['ALL'] + vessels, default=['ALL'])
    
    freqs = sorted(df['FREQ_TYPE'].unique())
    sel_freq = st.sidebar.multiselect("Frekuensi", freqs, default=freqs)
    
    st.sidebar.markdown("---")
    # SAYA UBAH DEFAULT KE FALSE DULU UNTUK TEST
    exclude_saturday = st.sidebar.checkbox("Sembunyikan 'Saturday Routine'", value=False)
    
    # --- FILTER LOGIC ---
    if not sel_years: sel_years = years
    if not sel_freq: sel_freq = freqs
    
    # Filter Vessel
    if 'ALL' in sel_vessels or not sel_vessels:
        final_vessel_list = df['VESSELID'].unique()
    else:
        final_vessel_list = sel_vessels
        
    # Apply Filter Utama
    filtered_df = df[
        (df['TAHUN'].isin(sel_years)) &
        (df['VESSELID'].isin(final_vessel_list)) &
        (df['FREQ_TYPE'].isin(sel_freq))
    ]
    
    # Apply Saturday Logic
    df_analysis = filtered_df.copy()
    if exclude_saturday:
        mask = (
            df_analysis['COMPNAME'].str.contains('Saturday', case=False) | 
            df_analysis['JOBTITLE'].str.contains('Saturday', case=False)
        )
        df_analysis = df_analysis[~mask]

    # --- KPI SECTION (Singkat Saja) ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Jobs", len(filtered_df))
    c2.metric("Vessels", filtered_df['VESSELID'].nunique())
    c3.metric("Avg RH", int(filtered_df['RH_THIS_MONTH_UNTIL_JOBDONE'].mean()))
    
    st.markdown("---")
    
    # --- CHART ATAS (Harusnya Muncul) ---
    st.subheader("📈 Tren Maintenance Bulanan")
    if not filtered_df.empty:
        trend = filtered_df.groupby('Month_Year').size().reset_index(name='Count')
        fig = px.line(trend, x='Month_Year', y='Count', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================================
    # --- AREA MASALAH (DI SINI KITA PASANG DEBUGGER) ---
    # =========================================================================
    
    st.markdown("---")
    st.header("🕵️ DIAGNOSA AREA BAWAH")
    
    # 1. Tampilkan Status Data df_analysis
    st.write("Cek status data untuk grafik bawah:")
    
    col_dbg1, col_dbg2 = st.columns(2)
    with col_dbg1:
        row_count = len(df_analysis)
        if row_count == 0:
            st.error(f"❌ JUMLAH BARIS DATA: {row_count}")
            st.warning("Penyebab: Filter terlalu ketat atau data Saturday Routine menghapus semuanya.")
        else:
            st.success(f"✅ JUMLAH BARIS DATA: {row_count}")
            
    with col_dbg2:
        # Cek kolom COMPNAME
        if 'COMPNAME' in df_analysis.columns:
            null_comp = df_analysis['COMPNAME'].isnull().sum()
            st.info(f"Kolom COMPNAME ditemukan. (Null values: {null_comp})")
            st.write(f"Contoh isi COMPNAME: {df_analysis['COMPNAME'].unique()[:3]}")
        else:
            st.error("❌ Kolom COMPNAME TIDAK DITEMUKAN!")

    # 2. Coba Render Grafik dengan Try-Except (Agar tidak crash)
    st.subheader("🏆 Analisis Sparepart (Dengan Error Handling)")
    
    try:
        if row_count > 0:
            # Slider
            top_n = st.slider("Jumlah Top Komponen:", 3, 20, 5)
            
            # Step 1: Hitung Value Counts
            top_counts = df_analysis['COMPNAME'].value_counts()
            
            if top_counts.empty:
                st.warning("⚠️ Kolom COMPNAME ada, tapi isinya kosong/semua null.")
            else:
                top_components_list = top_counts.head(top_n).index.tolist()
                
                # Step 2: Filter Data Top N
                df_viz = df_analysis[df_analysis['COMPNAME'].isin(top_components_list)]
                
                # Step 3: Grouping
                comp_trend = df_viz.groupby(['Month_Year', 'COMPNAME']).size().reset_index(name='Count')
                comp_trend = comp_trend.sort_values('Month_Year')
                
                # Step 4: Plotting
                fig_comp_trend = px.bar(
                    comp_trend, 
                    x='Month_Year', 
                    y='Count', 
                    color='COMPNAME',
                    title=f"Tren Top {top_n} Sparepart",
                    text='Count' # Menampilkan angka di batang
                )
                fig_comp_trend.update_traces(textposition='inside')
                
                st.plotly_chart(fig_comp_trend, use_container_width=True)
                st.success("✅ Grafik Sparepart Berhasil Di-Render!")
                
                # --- VISUALISASI TAMBAHAN (Bar Chart Horizontal) ---
                st.subheader("⚙️ Top Komponen (Total)")
                
                df_top_total = top_counts.head(10).reset_index()
                df_top_total.columns = ['Nama Komponen', 'Frekuensi']
                
                fig_bar = px.bar(df_top_total, y='Nama Komponen', x='Frekuensi', orientation='h', color='Frekuensi')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
                
        else:
            st.warning("Data kosong, tidak bisa membuat grafik.")
            
    except Exception as e:
        st.error("❌ TERJADI CRASH SAAT MEMBUAT GRAFIK!")
        st.error(f"Pesan Error Detail: {e}")
        st.code(str(e)) # Tampilkan raw error message

else:
    st.warning("Dataframe utama kosong.")
