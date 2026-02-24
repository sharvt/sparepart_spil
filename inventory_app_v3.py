import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Inventory Dashboard Final", layout="wide")

st.title("📊 Dashboard Inventory: Consumables vs Spare Parts")
st.markdown("Analisis data dari `Master_Barang_Aktif_Final2.csv` dengan pemisahan antara pengadaan rutin (Consumables) dan suku cadang (Spare Parts).")

# --- LOAD DATA & KLASIFIKASI OTOMATIS ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("Master_Barang_Aktif_Final2.csv")
        
        # Cleaning data (Mengisi nilai kosong)
        df['MEREK'] = df['MEREK'].fillna('TANPA MEREK')
        df['PART_NO'] = df['PART_NO'].fillna('-')
        df['SPESIFIKASI'] = df['SPESIFIKASI'].fillna('-')
        df['KATEGORI_EKSTRAK'] = df['KATEGORI_EKSTRAK'].fillna('LAIN-LAIN')
        df['GABUNGAN_KATEGORI_ASLI'] = df['GABUNGAN_KATEGORI_ASLI'].fillna('UMUM')
        
        # --- LOGIKA KLASIFIKASI CONSUMABLE VS NON-CONSUMABLE ---
        # Kata kunci yang identik dengan barang habis pakai (Consumable)
        consumable_keywords = ['OLI', 'CAT', 'CHEMICAL', 'CONSUMABLE', 'KERTAS', 
                               'SABUN', 'MAJUN', 'GREASE', 'PELUMAS', 'CLEANER']
        
        def tentukan_jenis(row):
            kat_ekstrak = str(row['KATEGORI_EKSTRAK']).upper()
            kat_sistem = str(row['GABUNGAN_KATEGORI_ASLI']).upper()
            
            # 1. Cek Kategori Ekstrak Utama
            if kat_ekstrak in ['CHEMICAL', 'STATIONERY', 'SAFETY']:
                return 'CONSUMABLES'
            
            # 2. Cek kata kunci di Kategori Asli
            for keyword in consumable_keywords:
                if keyword in kat_sistem:
                    return 'CONSUMABLES'
            
            # Sisanya dianggap Non-Consumable / Spare Part
            return 'NON-CONSUMABLES (SPARE PARTS)'

        df['JENIS_BARANG'] = df.apply(tentukan_jenis, axis=1)
        
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.error("❌ File 'Master_Barang_Aktif_Final2.csv' tidak ditemukan. Pastikan file ada di folder yang sama dengan script.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Global")

# Filter Kategori Utama (Kategori Ekstrak)
kategori_list = ['Semua'] + sorted(df['KATEGORI_EKSTRAK'].astype(str).unique().tolist())
selected_kategori = st.sidebar.selectbox("Pilih Kategori Utama (Ekstrak)", kategori_list)

df_filtered = df.copy()
if selected_kategori != 'Semua':
    df_filtered = df_filtered[df_filtered['KATEGORI_EKSTRAK'] == selected_kategori]

# Pencarian Cepat 
search_query = st.sidebar.text_input("Cari Nama Barang / Kode", "")
if search_query:
    df_filtered = df_filtered[
        df_filtered['NAMA_BARANG_RAPIH'].str.contains(search_query, case=False, na=False) |
        df_filtered['GABUNGAN_KODEBARANG'].str.contains(search_query, case=False, na=False)
    ]

# --- TABS: PEMISAHAN BEHAVIOR ---
tab1, tab2, tab3 = st.tabs(["🏠 Ringkasan Global", "⚙️ Non-Consumables (Spare Parts)", "🛢️ Consumables"])

# =========================================
# TAB 1: RINGKASAN GLOBAL
# =========================================
with tab1:
    st.subheader("Overview Keseluruhan Master Data")
    
    # KPI Global
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Total Baris Barang", f"{len(df_filtered):,}")
    c2.metric("⚙️ Total Spare Parts", f"{len(df_filtered[df_filtered['JENIS_BARANG'] == 'NON-CONSUMABLES (SPARE PARTS)']):,}")
    c3.metric("🛢️ Total Consumables", f"{len(df_filtered[df_filtered['JENIS_BARANG'] == 'CONSUMABLES']):,}")
    
    st.markdown("---")
    
    col_ov1, col_ov2 = st.columns(2)
    with col_ov1:
        st.caption("Proporsi Item: Spare Parts vs Consumables")
        jenis_counts = df_filtered['JENIS_BARANG'].value_counts().reset_index()
        jenis_counts.columns = ['JENIS', 'JUMLAH']
        fig_pie = px.pie(jenis_counts, names='JENIS', values='JUMLAH', hole=0.5, 
                         color='JENIS', color_discrete_map={'CONSUMABLES':'#FFA07A', 'NON-CONSUMABLES (SPARE PARTS)':'#20B2AA'})
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_ov2:
        st.caption("Top 10 Main Kategori (KATEGORI_EKSTRAK)")
        top_cat = df_filtered['KATEGORI_EKSTRAK'].value_counts().head(10).reset_index()
        top_cat.columns = ['KATEGORI', 'JUMLAH']
        fig_bar = px.bar(top_cat, x='JUMLAH', y='KATEGORI', orientation='h', text='JUMLAH')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# =========================================
# TAB 2: NON-CONSUMABLES (SPARE PARTS)
# =========================================
with tab2:
    st.info("ℹ️ **Konteks:** Barang yang difokuskan untuk perawatan mesin, perbaikan, dan membutuhkan spesifikasi/part number yang tepat.")
    
    df_nc = df_filtered[df_filtered['JENIS_BARANG'] == 'NON-CONSUMABLES (SPARE PARTS)']
    
    # KPI Non-Consumables
    nc1, nc2, nc3 = st.columns(3)
    nc1.metric("Jumlah Item Spareparts", f"{len(df_nc):,}")
    nc_merek_count = df_nc[df_nc['MEREK'] != 'TANPA MEREK']['MEREK'].nunique()
    nc2.metric("Merek Berbeda (Tercatat)", f"{nc_merek_count:,}")
    nc_part_count = df_nc[df_nc['PART_NO'] != '-'].shape[0]
    nc3.metric("Item Memiliki Part No", f"{nc_part_count:,}")
    
    st.markdown("---")
    
    col_nc1, col_nc2 = st.columns([2, 1])
    with col_nc1:
        st.subheader("Distribusi Kategori")
        nc_cat = df_nc['KATEGORI_EKSTRAK'].value_counts().head(15).reset_index()
        nc_cat.columns = ['KATEGORI_HASIL', 'JUMLAH']
        fig_nc_cat = px.bar(nc_cat, x='JUMLAH', y='KATEGORI_HASIL', orientation='h', 
                            text='JUMLAH', color='JUMLAH', color_continuous_scale='Teal')
        fig_nc_cat.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_nc_cat, use_container_width=True)
        
    with col_nc2:
        st.subheader("Top 10 Merek Terdaftar")
        nc_brand = df_nc[df_nc['MEREK'] != 'TANPA MEREK']['MEREK'].value_counts().head(10).reset_index()
        nc_brand.columns = ['MEREK', 'JUMLAH']
        if not nc_brand.empty:
            fig_nc_brand = px.pie(nc_brand, names='MEREK', values='JUMLAH', hole=0.4)
            fig_nc_brand.update_traces(textposition='inside', textinfo='percent+label')
            fig_nc_brand.update_layout(showlegend=False)
            st.plotly_chart(fig_nc_brand, use_container_width=True)
        else:
            st.warning("Tidak ada data merek pada filter ini.")

    st.subheader("📋 Tabel Detail Spare Parts")
    st.dataframe(df_nc[['GABUNGAN_KODEBARANG', 'NAMA_BARANG_RAPIH', 'GABUNGAN_KATEGORI_ASLI', 'MEREK', 'PART_NO', 'SPESIFIKASI']], use_container_width=True)

# =========================================
# TAB 3: CONSUMABLES
# =========================================
with tab3:
    st.success("💰 **Konteks:** Barang habis pakai (Bahan Kimia, Pelumas, Cat, Alat Tulis) yang berfokus pada volume pemakaian (Cost Projection).")
    
    df_c = df_filtered[df_filtered['JENIS_BARANG'] == 'CONSUMABLES']
    
    c1, c2 = st.columns(2)
    c1.metric("Total Items Consumables", f"{len(df_c):,}")
    c2.metric("Kategori Yang Terlibat", df_c['KATEGORI_EKSTRAK'].nunique())
    
    st.markdown("---")
    
    st.subheader("Kelompok Consumables Terbanyak")
    
    c_cat_counts = df_c['KATEGORI_EKSTRAK'].value_counts().head(15).reset_index()
    c_cat_counts.columns = ['KATEGORI_HASIL', 'JUMLAH']
    
    fig_c_cat = px.bar(c_cat_counts, x='JUMLAH', y='KATEGORI_HASIL', orientation='h', 
                       text='JUMLAH', color='KATEGORI_HASIL', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_c_cat.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_c_cat, use_container_width=True)

    st.subheader("📋 Tabel Detail Consumables")
    st.dataframe(df_c[['GABUNGAN_KODEBARANG', 'NAMA_BARANG_RAPIH', 'GABUNGAN_KATEGORI_ASLI', 'KATEGORI_EKSTRAK', 'SATUAN_RAPIH']], use_container_width=True)

# --- DOWNLOAD AREA ---
st.markdown("---")
st.subheader("📥 Export Data Terekstrak")
col_down1, col_down2 = st.columns(2)

with col_down1:
    csv_nc = df_nc.to_csv(index=False).encode('utf-8')
    st.download_button("Download Data Spare Parts (CSV)", data=csv_nc, file_name='spare_parts_filtered.csv', mime='text/csv')

with col_down2:
    csv_c = df_c.to_csv(index=False).encode('utf-8')
    st.download_button("Download Data Consumables (CSV)", data=csv_c, file_name='consumables_filtered.csv', mime='text/csv')
