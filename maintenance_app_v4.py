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

# --- FUNGSI LOAD DATA (DIPERBAIKI) ---
@st.cache_data
def load_data():
    file_2024 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    file_2025 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx"
    
    try:
        df1 = pd.read_excel(file_2024)
        df2 = pd.read_excel(file_2025)
        df = pd.concat([df1, df2], ignore_index=True)
        
        # --- 1. PERBAIKAN TANGGAL (FIX) ---
        df['TAHUN'] = pd.to_numeric(df['TAHUN'], errors='coerce').fillna(0).astype(int)
        df['BULAN'] = pd.to_numeric(df['BULAN'], errors='coerce').fillna(0).astype(int)
        df = df[(df['TAHUN'] > 2000) & (df['BULAN'] >= 1) & (df['BULAN'] <= 12)]
        df['Month_Year'] = df['TAHUN'].astype(str) + "-" + df['BULAN'].astype(str).str.zfill(2)
        
        # --- 2. PERBAIKAN STRING (INI SOLUSI MASALAH ANDA) ---
        # Paksa semua kolom teks menjadi string agar tidak error saat filter/plot
        df['COMPNAME'] = df['COMPNAME'].astype(str).str.strip()
        df['JOBTITLE'] = df['JOBTITLE'].astype(str).str.strip()
        df['VESSELID'] = df['VESSELID'].astype(str).str.strip()
        
        # Ubah "nan" string kembali menjadi "-" agar rapi
        df['COMPNAME'] = df['COMPNAME'].replace(['nan', 'NaN', ''], '-')
        
        # --- 3. PERBAIKAN ANGKA ---
        df['RH_THIS_MONTH_UNTIL_JOBDONE'] = pd.to_numeric(df['RH_THIS_MONTH_UNTIL_JOBDONE'], errors='coerce').fillna(0)
        
        # Kosmetik Tanggal
        df['JOBREPORT_DATE'] = pd.to_datetime(df['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load Data
df = load_data()

if not df.empty:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Tahun
    all_years = sorted(df['TAHUN'].unique())
    sel_years = st.sidebar.multiselect("Tahun", all_years, default=all_years)
    
    # Filter Vessel (Default ALL)
    all_vessels = sorted(df['VESSELID'].unique().tolist())
    sel_vessels = st.sidebar.multiselect("Kapal", ['ALL'] + all_vessels, default=['ALL'])
    
    # Filter Freq
    all_freq = sorted(df['FREQ_TYPE'].unique())
    sel_freq = st.sidebar.multiselect("Frekuensi", all_freq, default=all_freq)
    
    st.sidebar.markdown("---")
    exclude_saturday = st.sidebar.checkbox("Sembunyikan 'Saturday Routine'", value=True)
    
    # --- FILTERING LOGIC ---
    if not sel_years: sel_years = all_years
    if not sel_freq: sel_freq = all_freq
    
    # Vessel Logic
    if 'ALL' in sel_vessels or not sel_vessels:
        target_vessels = df['VESSELID'].unique()
    else:
        target_vessels = sel_vessels
        
    # Apply Filter
    filtered_df = df[
        (df['TAHUN'].isin(sel_years)) &
        (df['VESSELID'].isin(target_vessels)) &
        (df['FREQ_TYPE'].isin(sel_freq))
    ]
    
    # Saturday Logic
    df_analysis = filtered_df.copy()
    if exclude_saturday:
        # Karena sudah dipaksa string di atas (.astype(str)), fungsi .str.contains ini AMAN sekarang
        mask = (
            df_analysis['COMPNAME'].str.contains('Saturday', case=False) | 
            df_analysis['JOBTITLE'].str.contains('Saturday', case=False)
        )
        df_analysis = df_analysis[~mask]
        
    # --- KPI SECTION ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jobs", len(filtered_df))
    c2.metric("Total Kapal", filtered_df['VESSELID'].nunique())
    
    top_comp_name = "-"
    if not df_analysis.empty:
        top_comp_name = df_analysis['COMPNAME'].mode()[0]
    c3.metric("Top Komponen", top_comp_name)
    
    avg_rh = filtered_df['RH_THIS_MONTH_UNTIL_JOBDONE'].mean()
    c4.metric("
