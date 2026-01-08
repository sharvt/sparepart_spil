import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Inventory Dashboard", layout="wide")

# --- JUDUL ---
st.title("📊 Dashboard Inventory Barang")
st.markdown("Analisis data inventory berdasarkan Kategori, Merek, dan COA.")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("Master_Barang_Rapih_V3.csv")
        # Cleaning data sederhana
        df['MEREK'] = df['MEREK'].fillna('TIDAK ADA MEREK')
        df['KATEGORI'] = df['KATEGORI'].fillna('LAIN-LAIN')
        df['PART_NO'] = df['PART_NO'].fillna('-')
        df['COA'] = df['COA'].fillna('NON-COA')
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.error("❌ File 'Master_Barang_Rapih_V3.csv' tidak ditemukan. Mohon upload file csv ke dalam folder yang sama.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Data")

# Filter Kategori
kategori_list = ['Semua'] + sorted(df['KATEGORI'].astype(str).unique().tolist())
selected_kategori = st.sidebar.selectbox("Pilih Kategori", kategori_list)

# Filter COA
coa_list = ['Semua'] + sorted(df['COA'].astype(str).unique().tolist())
selected_coa = st.sidebar.selectbox("Pilih COA", coa_list)

# Terapkan Filter
df_filtered = df.copy()

if selected_kategori != 'Semua':
    df_filtered = df_filtered[df_filtered['KATEGORI'] == selected_kategori]

if selected_coa != 'Semua':
    df_filtered = df_filtered[df_filtered['COA'] == selected_coa]

# --- KPI METRICS ---
# Menggunakan st.container untuk membungkus metric agar rapi
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Barang", f"{len(df_filtered):,}")
    col2.metric("📑 Total Kategori", df_filtered['KATEGORI'].nunique())
    col3.metric("🏷️ Total Merek", df_filtered['MEREK'].nunique())
    col4.metric("⚙️ Part Number Ada", f"{df_filtered[df_filtered['PART_NO'] != '-'].shape[0]:,}")

st.markdown("---")

# --- CHARTS AREA (DIPERBAIKI) ---

# Menggunakan layout kolom 2:1 agar Pie Chart tidak terlalu gepeng
col_left, col_right = st.columns([2, 1], gap="medium")

with col_left:
    st.subheader("📦 Jumlah Barang per Kategori")
    cat_counts = df_filtered['KATEGORI'].value_counts().reset_index()
    cat_counts.columns = ['KATEGORI', 'JUMLAH']
    
    # PERBAIKAN: Menggunakan Horizontal Bar (x dan y dibalik) agar label tidak overlap
    fig_cat = px.bar(cat_counts, 
                     x='JUMLAH', 
                     y='KATEGORI', 
                     orientation='h',  # Horizontal
                     text='JUMLAH', 
                     color='JUMLAH',
                     color_continuous_scale='Blues')
    
    # Mengurutkan agar yang terbanyak di atas
    fig_cat.update_layout(yaxis={'categoryorder':'total ascending'})
    fig_cat.update_traces(textposition='auto') # Posisi teks otomatis menyesuaikan
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.subheader("🏷️ Top 10 Merek")
    brand_counts = df_filtered['MEREK'].value_counts().head(10).reset_index()
    brand_counts.columns = ['MEREK', 'JUMLAH']
    
    fig_brand = px.pie(brand_counts, names='MEREK', values='JUMLAH', hole=0.4)
    
    # PERBAIKAN: Legenda ditaruh di bawah agar grafik tidak tertutup
    fig_brand.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    st.plotly_chart(fig_brand, use_container_width=True)

# --- ANALISIS TAMBAHAN ---
st.markdown("---")
st.subheader("📂 Distribusi Chart of Accounts (COA)")

coa_counts = df_filtered['COA'].value_counts().reset_index()
coa_counts.columns = ['COA', 'JUMLAH']

fig_coa = px.bar(coa_counts, 
                 x='JUMLAH', 
                 y='COA', 
                 orientation='h', 
                 text='JUMLAH', 
                 color='COA')
fig_coa.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
fig_coa.update_traces(textposition='auto')
st.plotly_chart(fig_coa, use_container_width=True)

# --- DATA TABLE ---
st.markdown("---")
st.subheader("📋 Detail Data Inventory")

with st.expander("Klik untuk melihat Tabel Data Lengkap"):
    st.dataframe(df_filtered, use_container_width=True)

# --- DOWNLOAD BUTTON ---
csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Data CSV",
    data=csv,
    file_name='inventory_data.csv',
    mime='text/csv',
)
