import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Inventory Dashboard - Split View", layout="wide")

# --- JUDUL ---
st.title("📊 Dashboard Inventory: Consumables vs Non-Consumables")
st.markdown("Dashboard ini telah disesuaikan untuk memisahkan analisis spare parts (repair) dan consumables (cost projection).")

# --- LOAD DATA & KLASIFIKASI OTOMATIS ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("Master_Barang_Rapih_V3.csv")
        # Cleaning data sederhana
        df['MEREK'] = df['MEREK'].fillna('TIDAK ADA MEREK')
        df['KATEGORI'] = df['KATEGORI'].fillna('LAIN-LAIN')
        df['PART_NO'] = df['PART_NO'].fillna('-')
        df['COA'] = df['COA'].fillna('NON-COA')
        
        # --- LOGIKA BARU: MEMBUAT KOLOM JENIS_BARANG ---
        # Jika COA mengandung kata "BIAYA", kita anggap CONSUMABLE
        # Sisanya (PERLENGKAPAN, INVENTARIS) kita anggap NON-CONSUMABLE (SPARE PART)
        def klasifikasi_jenis(coa):
            coa_str = str(coa).upper()
            if 'BIAYA' in coa_str:
                return 'CONSUMABLES'
            else:
                return 'NON-CONSUMABLES (SPARE PARTS)'
        
        df['JENIS_BARANG'] = df['COA'].apply(klasifikasi_jenis)
        
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.error("❌ File 'Master_Barang_Rapih_V3.csv' tidak ditemukan.")
    st.stop()

# --- SIDEBAR FILTERS (GLOBAL) ---
st.sidebar.header("🔍 Global Filter")

# Filter Kategori (Dinamis berdasarkan data yang ada)
kategori_list = ['Semua'] + sorted(df['KATEGORI'].astype(str).unique().tolist())
selected_kategori = st.sidebar.selectbox("Pilih Kategori", kategori_list)

# Terapkan Filter Kategori
df_filtered = df.copy()
if selected_kategori != 'Semua':
    df_filtered = df_filtered[df_filtered['KATEGORI'] == selected_kategori]

# --- TABS: PEMISAHAN KONTEKS ---
# Tab 1: Ringkasan, Tab 2: Spare Parts (Non-Consumable), Tab 3: Consumables
tab1, tab2, tab3 = st.tabs(["🏠 Overview", "⚙️ Non-Consumables (Spare Parts)", "🛢️ Consumables"])

# =========================================
# TAB 1: OVERVIEW
# =========================================
with tab1:
    st.subheader("Ringkasan Seluruh Inventory")
    
    # KPI Global
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Item Inventory", f"{len(df_filtered):,}")
    c2.metric("Total Spare Parts", f"{len(df_filtered[df_filtered['JENIS_BARANG']=='NON-CONSUMABLES (SPARE PARTS)']):,}")
    c3.metric("Total Consumables", f"{len(df_filtered[df_filtered['JENIS_BARANG']=='CONSUMABLES']):,}")
    
    st.markdown("---")
    
    # Grafik Proporsi Split
    col_ov1, col_ov2 = st.columns([1, 1])
    
    with col_ov1:
        st.caption("Proporsi Item: Spare Parts vs Consumables")
        jenis_counts = df_filtered['JENIS_BARANG'].value_counts().reset_index()
        jenis_counts.columns = ['JENIS', 'JUMLAH']
        fig_pie = px.pie(jenis_counts, names='JENIS', values='JUMLAH', hole=0.4, color='JENIS',
                         color_discrete_map={'CONSUMABLES':'#FFA07A', 'NON-CONSUMABLES (SPARE PARTS)':'#20B2AA'})
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_ov2:
        st.caption("Top 5 Kategori Terbanyak (Gabungan)")
        top_cat = df_filtered['KATEGORI'].value_counts().head(5).reset_index()
        top_cat.columns = ['KATEGORI', 'JUMLAH']
        fig_bar = px.bar(top_cat, x='JUMLAH', y='KATEGORI', orientation='h', text='JUMLAH')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# =========================================
# TAB 2: NON-CONSUMABLES (SPARE PARTS)
# =========================================
with tab2:
    st.info("ℹ️ **Fokus:** Perbaikan Kapal & Manajemen Spareparts (Engine, Deck, dll).")
    
    # Filter Khusus Non-Consumable
    df_nc = df_filtered[df_filtered['JENIS_BARANG'] == 'NON-CONSUMABLES (SPARE PARTS)']
    
    # KPI Non-Consumable
    nc1, nc2, nc3 = st.columns(3)
    nc1.metric("Item Spareparts", f"{len(df_nc):,}")
    nc2.metric("Jumlah Merek (Brand)", df_nc['MEREK'].nunique())
    nc3.metric("Item dengan Part No", f"{df_nc[df_nc['PART_NO'] != '-'].shape[0]:,}")
    
    st.markdown("---")
    
    # Layout Grafik
    col_nc1, col_nc2 = st.columns([2, 1])
    
    with col_nc1:
        st.subheader("Distribusi Kategori Spareparts")
        nc_cat_counts = df_nc['KATEGORI'].value_counts().reset_index()
        nc_cat_counts.columns = ['KATEGORI', 'JUMLAH']
        
        fig_nc_cat = px.bar(nc_cat_counts, x='JUMLAH', y='KATEGORI', orientation='h', 
                            text='JUMLAH', color='JUMLAH', color_continuous_scale='Teal')
        fig_nc_cat.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_nc_cat, use_container_width=True)
        
    with col_nc2:
        st.subheader("Top Merek Spareparts")
        nc_brand = df_nc['MEREK'].value_counts().head(10).reset_index()
        nc_brand.columns = ['MEREK', 'JUMLAH']
        fig_nc_brand = px.pie(nc_brand, names='MEREK', values='JUMLAH', hole=0.4)
        fig_nc_brand.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_nc_brand, use_container_width=True)

    # Tabel Data Spareparts
    with st.expander("📋 Lihat Data Detail Spareparts"):
        st.dataframe(df_nc[['BARANG', 'KATEGORI', 'MEREK', 'PART_NO', 'COA']], use_container_width=True)

# =========================================
# TAB 3: CONSUMABLES
# =========================================
with tab3:
    st.success("💰 **Fokus:** Cost Projection (Cat, Oli, Chemical, dll).")
    
    # Filter Khusus Consumable
    df_c = df_filtered[df_filtered['JENIS_BARANG'] == 'CONSUMABLES']
    
    # KPI Consumable
    c_1, c_2 = st.columns(2)
    c_1.metric("Total Item Consumables", f"{len(df_c):,}")
    c_2.metric("Kelompok Biaya (COA)", df_c['COA'].nunique())
    
    st.markdown("---")
    
    # Visualisasi Fokus ke COA (Cost Center)
    st.subheader("Distribusi Item per Kelompok Biaya (COA)")
    st.caption("Grafik ini membantu melihat pos biaya mana yang memiliki varian item terbanyak.")
    
    c_coa_counts = df_c['COA'].value_counts().reset_index()
    c_coa_counts.columns = ['COA', 'JUMLAH']
    
    fig_c_coa = px.bar(c_coa_counts, x='JUMLAH', y='COA', orientation='h', 
                       text='JUMLAH', color='COA', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_c_coa.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_c_coa, use_container_width=True)
    
    # Analisis Kategori dalam Consumables
    st.subheader("Kategori dalam Consumables")
    c_cat_counts = df_c['KATEGORI'].value_counts().reset_index()
    c_cat_counts.columns = ['KATEGORI', 'JUMLAH']
    fig_c_cat = px.bar(c_cat_counts, x='KATEGORI', y='JUMLAH', text='JUMLAH', color='JUMLAH')
    st.plotly_chart(fig_c_cat, use_container_width=True)

    # Tabel Data Consumables
    with st.expander("📋 Lihat Data Detail Consumables"):
        st.dataframe(df_c[['BARANG', 'KATEGORI', 'COA']], use_container_width=True)

# --- DOWNLOAD GLOBAL ---
st.markdown("---")
st.subheader("📥 Download Data")
csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Semua Data (CSV)",
    data=csv,
    file_name='inventory_split.csv',
    mime='text/csv',
)