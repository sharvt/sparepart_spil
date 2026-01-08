import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard Analisis Inventory",
    page_icon="📦",
    layout="wide"
)

# Judul Utama
st.title("📦 Dashboard Analisis Inventory")
st.markdown("Dashboard ini menampilkan insight utama dari data `Master_Barang_Rapih_V3.csv`.")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # Pastikan file CSV ada di direktori yang sama
    try:
        df = pd.read_csv('Master_Barang_Rapih_V3.csv')
        return df
    except FileNotFoundError:
        st.error("File 'Master_Barang_Rapih_V3.csv' tidak ditemukan. Pastikan file berada di folder yang sama.")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Data")
    
    # Filter berdasarkan COA
    all_coa = ['Semua'] + list(df['COA'].unique())
    selected_coa = st.sidebar.selectbox("Pilih COA (Chart of Account):", all_coa)

    if selected_coa != 'Semua':
        df_display = df[df['COA'] == selected_coa]
    else:
        df_display = df

    # --- KPI METRICS (High Level Insight) ---
    st.subheader("📊 Ringkasan Data")
    col1, col2, col3, col4 = st.columns(4)

    total_items = len(df_display)
    unique_brands = df_display['MEREK'].nunique()
    top_cat = df_display['KATEGORI'].mode()[0]
    # Hitung % LAIN-LAIN
    lain_lain_count = len(df_display[df_display['KATEGORI'] == 'LAIN-LAIN'])
    lain_lain_pct = (lain_lain_count / total_items) * 100 if total_items > 0 else 0

    with col1:
        st.metric("Total Item Inventory", f"{total_items:,}")
    with col2:
        st.metric("Jumlah Merek Unik", f"{unique_brands:,}")
    with col3:
        st.metric("Kategori Terbanyak", top_cat)
    with col4:
        st.metric("% Kategori 'LAIN-LAIN'", f"{lain_lain_pct:.1f}%", 
                  delta="- Perlu Dirapikan" if lain_lain_pct > 20 else "OK", delta_color="inverse")

    st.divider()

    # --- TABS FOR INSIGHTS ---
    tab1, tab2, tab3 = st.tabs(["📈 Kategori & Merek", "💰 Distribusi COA", "⚠️ Kualitas Data"])

    # TAB 1: KATEGORI & MEREK
    with tab1:
        col_cat, col_brand = st.columns(2)

        with col_cat:
            st.subheader("Top 10 Kategori Barang")
            cat_counts = df_display['KATEGORI'].value_counts().head(10).reset_index()
            cat_counts.columns = ['Kategori', 'Jumlah']
            
            fig_cat = px.bar(cat_counts, x='Jumlah', y='Kategori', orientation='h', 
                             text='Jumlah', color='Jumlah', color_continuous_scale='Viridis')
            fig_cat.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_cat, use_container_width=True)
            st.caption("Insight: Kategori 'LAIN-LAIN' mendominasi, menunjukkan perlunya klasifikasi ulang.")

        with col_brand:
            st.subheader("Top 10 Merek (Brand)")
            brand_counts = df_display['MEREK'].value_counts().head(10).reset_index()
            brand_counts.columns = ['Merek', 'Jumlah']
            
            fig_brand = px.bar(brand_counts, x='Jumlah', y='Merek', orientation='h', 
                               text='Jumlah', color='Jumlah', color_continuous_scale='Magma')
            fig_brand.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_brand, use_container_width=True)
            st.caption("Insight: YANMAR, CUMMINS, dan MITSUBISHI adalah merek paling dominan (Engine Parts).")

    # TAB 2: DISTRIBUSI COA
    with tab2:
        st.subheader("Distribusi Barang per COA")
        coa_counts = df['COA'].value_counts().reset_index()
        coa_counts.columns = ['COA', 'Jumlah']

        # Menggunakan Bar Chart karena nama COA panjang
        fig_coa = px.bar(coa_counts, x='Jumlah', y='COA', text='Jumlah', 
                         color='COA', title="Jumlah Item per Akun Anggaran")
        fig_coa.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig_coa, use_container_width=True)
        
        st.info("Mayoritas aset tercatat pada 'PERLENGKAPAN KAPAL - MESIN' (lebih dari 22.000 item).")

    # TAB 3: KUALITAS DATA (MISSING VALUES)
    with tab3:
        st.subheader("Analisis Kelengkapan Data (Missing Values)")
        
        # Menghitung persentase missing values
        missing_data = df[['MEREK', 'PART_NO', 'SPESIFIKASI']].isnull().mean() * 100
        missing_df = missing_data.reset_index()
        missing_df.columns = ['Kolom', 'Persentase Kosong (%)']
        
        # Gauge Charts atau Bar Chart untuk Missing Values
        fig_missing = px.bar(missing_df, x='Persentase Kosong (%)', y='Kolom', orientation='h',
                             color='Persentase Kosong (%)', range_x=[0, 100], color_continuous_scale='Reds')
        
        st.plotly_chart(fig_missing, use_container_width=True)
        
        col_warn1, col_warn2 = st.columns(2)
        with col_warn1:
            st.warning(f"⚠️ Data Merek Kosong: {missing_data['MEREK']:.1f}%")
        with col_warn2:
            st.warning(f"⚠️ Part Number Kosong: {missing_data['PART_NO']:.1f}%")
        
        st.markdown("""
        **Rekomendasi:**
        * Prioritaskan pengisian **Part Number** untuk item kategori *Engine Part* & *Valve*.
        * Prioritaskan pengisian **Merek** untuk menghindari kesalahan pemesanan suku cadang.
        """)
        
        # Cek Duplikasi Part Number
        st.subheader("Pengecekan Duplikasi Part Number")
        part_no_counts = df[df['PART_NO'].notnull()]['PART_NO'].value_counts()
        duplicates = part_no_counts[part_no_counts > 1]
        
        st.write(f"Ditemukan **{len(duplicates)}** Part Number yang muncul lebih dari satu kali.")
        if len(duplicates) > 0:
            st.dataframe(duplicates.head(10).rename("Jumlah Duplikasi"), use_container_width=True)

    # --- RAW DATA VIEW ---
    st.divider()
    with st.expander("📂 Lihat Data Mentah"):
        st.dataframe(df_display)

else:
    st.info("Silakan unggah atau letakkan file CSV di folder aplikasi.")