import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="Inventory Dashboard", layout="wide")

# Judul Dashboard
st.title("📊 Dashboard Inventory Barang")
st.markdown("Analisis data inventory berdasarkan Kategori, Merek, dan COA.")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv("Master_Barang_Rapih_V3.csv")
    # Mengisi nilai NaN agar lebih rapi saat ditampilkan
    df['MEREK'] = df['MEREK'].fillna('TIDAK ADA MEREK')
    df['SPESIFIKASI'] = df['SPESIFIKASI'].fillna('-')
    df['PART_NO'] = df['PART_NO'].fillna('-')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File 'Master_Barang_Rapih_V3.csv' tidak ditemukan. Pastikan file ada di direktori yang sama.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Data")

# Filter Kategori
kategori_list = ['Semua'] + sorted(df['KATEGORI'].astype(str).unique().tolist())
selected_kategori = st.sidebar.selectbox("Pilih Kategori", kategori_list)

# Filter COA
coa_list = ['Semua'] + sorted(df['COA'].astype(str).unique().tolist())
selected_coa = st.sidebar.selectbox("Pilih COA", coa_list)

# Filter Data Berdasarkan Pilihan
df_filtered = df.copy()

if selected_kategori != 'Semua':
    df_filtered = df_filtered[df_filtered['KATEGORI'] == selected_kategori]

if selected_coa != 'Semua':
    df_filtered = df_filtered[df_filtered['COA'] == selected_coa]

# --- KPI METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Barang (Item)", f"{len(df_filtered):,}")
col2.metric("Total Kategori", df_filtered['KATEGORI'].nunique())
col3.metric("Total Merek", df_filtered['MEREK'].nunique())
col4.metric("Barang dengan Part No", f"{df_filtered[df_filtered['PART_NO'] != '-'].shape[0]:,}")

st.markdown("---")

# --- CHARTS AREA ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📦 Distribusi per Kategori")
    # Hitung jumlah per kategori
    cat_counts = df_filtered['KATEGORI'].value_counts().reset_index()
    cat_counts.columns = ['KATEGORI', 'JUMLAH']
    
    fig_cat = px.bar(cat_counts, x='KATEGORI', y='JUMLAH', 
                     text='JUMLAH', color='JUMLAH',
                     color_continuous_scale='Blues',
                     title="Jumlah Barang per Kategori")
    fig_cat.update_traces(textposition='outside')
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.subheader("🏷️ Top 10 Merek")
    # Hitung top 10 merek (mengecualikan 'TIDAK ADA MEREK' jika diinginkan, tapi di sini kita tampilkan semua)
    brand_counts = df_filtered['MEREK'].value_counts().head(10).reset_index()
    brand_counts.columns = ['MEREK', 'JUMLAH']
    
    fig_brand = px.pie(brand_counts, names='MEREK', values='JUMLAH', 
                       hole=0.4, title="Proporsi Top 10 Merek")
    st.plotly_chart(fig_brand, use_container_width=True)

# --- ANALISIS TAMBAHAN ---
st.subheader("📂 Distribusi Chart of Accounts (COA)")
coa_counts = df_filtered['COA'].value_counts().reset_index()
coa_counts.columns = ['COA', 'JUMLAH']
fig_coa = px.bar(coa_counts, x='JUMLAH', y='COA', orientation='h',
                 text='JUMLAH', color='COA', title="Jumlah Barang per COA")
fig_coa.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_coa, use_container_width=True)

# --- DATA TABLE ---
st.markdown("---")
st.subheader("📋 Detail Data Inventory")
st.markdown(f"Menampilkan **{len(df_filtered)}** baris data sesuai filter.")

# Tampilkan dataframe dengan fitur pencarian bawaan Streamlit
st.dataframe(df_filtered, use_container_width=True)

# Opsi Download Data
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(df_filtered)

st.download_button(
    label="📥 Download Data Terfilter sebagai CSV",
    data=csv,
    file_name='inventory_terfilter.csv',
    mime='text/csv',
)