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

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    # Path file
    file_2024 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    file_2025 = "Magang Sparepart 2025/Maintenance Job Report ALL ACTIVE VESSEL 2025.xlsx"
    
    try:
        # Load data
        df1 = pd.read_excel(file_2024)
        df2 = pd.read_excel(file_2025)
        
        # Gabungkan data
        df = pd.concat([df1, df2], ignore_index=True)
        
        # --- DATA CLEANING ---
        # 1. Pastikan TAHUN dan BULAN adalah angka
        df['TAHUN'] = pd.to_numeric(df['TAHUN'], errors='coerce').fillna(0).astype(int)
        df['BULAN'] = pd.to_numeric(df['BULAN'], errors='coerce').fillna(0).astype(int)
        
        # 2. Filter data valid
        df = df[(df['TAHUN'] > 2000) & (df['BULAN'] >= 1) & (df['BULAN'] <= 12)]
        
        # 3. Buat kolom Month_Year
        df['Month_Year'] = df['TAHUN'].astype(str) + "-" + df['BULAN'].astype(str).str.zfill(2)
        
        # 4. Handle Missing Values String
        df['COMPNAME'] = df['COMPNAME'].astype(str).fillna("-")
        df['JOBTITLE'] = df['JOBTITLE'].astype(str).fillna("-")
        df['VESSELID'] = df['VESSELID'].astype(str).fillna("Unknown")
        
        # 5. Konversi Running Hours
        df['RH_THIS_MONTH_UNTIL_JOBDONE'] = pd.to_numeric(df['RH_THIS_MONTH_UNTIL_JOBDONE'], errors='coerce').fillna(0)
        
        # 6. Format Tanggal (PENTING UNTUK DELAY)
        df['JOBREPORT_DATE'] = pd.to_datetime(df['JOBREPORT_DATE'], dayfirst=True, errors='coerce')
        df['JOB_TIMESTAMP'] = pd.to_datetime(df['JOB_TIMESTAMP'], dayfirst=True, errors='coerce')
        
        # 7. HITUNG DELAY (Timestamp - Report Date)
        # Menghitung selisih hari antara pekerjaan dilakukan vs diinput ke sistem
        df['Delay_Days'] = (df['JOB_TIMESTAMP'] - df['JOBREPORT_DATE']).dt.days
        
        # Bersihkan delay negatif (error input tanggal) menjadi 0
        df.loc[df['Delay_Days'] < 0, 'Delay_Days'] = 0
        df['Delay_Days'] = df['Delay_Days'].fillna(0).astype(int)
        
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
    all_years = sorted(df['TAHUN'].unique())
    selected_years = st.sidebar.multiselect("Pilih Tahun", all_years, default=all_years)
    
    # --- FILTER KAPAL (ADVANCED) ---
    st.sidebar.subheader("🚢 Filter Kapal")
    
    all_vessels = sorted(df['VESSELID'].unique().tolist())
    
    # A. INCLUDE
    selected_vessels_include = st.sidebar.multiselect(
        "Include Kapal (Tampilkan)", 
        options=['ALL'] + all_vessels, 
        default=['ALL']
    )
    
    # B. EXCLUDE
    selected_vessels_exclude = st.sidebar.multiselect(
        "Exclude Kapal (Sembunyikan)",
        options=all_vessels,
        default=[],
        help="Kapal ini TIDAK akan ditampilkan."
    )
    
    # C. LOW ACTIVITY FILTER
    show_low_activity = st.sidebar.checkbox(
        "Hanya Tampilkan Kapal 'Low Activity'", 
        value=False,
        help="Hanya menampilkan kapal dengan rata-rata laporan < 100 per tahun."
    )
    
    st.sidebar.markdown("---")
    
    # Filter Tipe Frekuensi
    all_freqs = sorted(df['FREQ_TYPE'].unique())
    selected_freqs = st.sidebar.multiselect("Pilih Tipe Frekuensi", all_freqs, default=all_freqs)
    
    st.sidebar.markdown("---")
    
    # Filter Running Hours (RH)
    exclude_zero_rh = st.sidebar.checkbox("Hanya Tampilkan Running Hours > 0", value=True)
    st.sidebar.caption("Filter ini membuang pekerjaan rutin (Checking/Cleaning) agar fokus pada perbaikan mesin.")

    # --- LOGIKA PENERAPAN FILTER ---
    
    if not selected_years: selected_years = all_years
    if not selected_freqs: selected_freqs = all_freqs
    
    # Logic Vessel Include
    if 'ALL' in selected_vessels_include or not selected_vessels_include:
        target_vessels = all_vessels
    else:
        target_vessels = selected_vessels_include
        
    # Logic Vessel Exclude
    if selected_vessels_exclude:
        target_vessels = [v for v in target_vessels if v not in selected_vessels_exclude]
        
    # Logic Low Activity
    temp_df = df[(df['TAHUN'].isin(selected_years)) & (df['VESSELID'].isin(target_vessels))]
    
    if show_low_activity:
        vessel_counts = temp_df['VESSELID'].value_counts()
        num_years = len(selected_years) if len(selected_years) > 0 else 1
        threshold = 100 * num_years
        low_activity_vessels = vessel_counts[vessel_counts < threshold].index.tolist()
        target_vessels = [v for v in target_vessels if v in low_activity_vessels]
        st.sidebar.info(f"Filter Low Activity Aktif: {len(target_vessels)} kapal.")

    # Apply Final Filter
    filtered_df = df[
        (df['TAHUN'].isin(selected_years)) &
        (df['VESSELID'].isin(target_vessels)) &
        (df['FREQ_TYPE'].isin(selected_freqs))
    ]
    
    # Filter Running Hours
    df_analysis = filtered_df.copy()
    if exclude_zero_rh:
        df_analysis = df_analysis[df_analysis['RH_THIS_MONTH_UNTIL_JOBDONE'] > 0]

    # --- KPI SUMMARY ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric("Total Jobs (Filtered)", f"{len(df_analysis):,}") 

    with kpi2:
        st.metric("Total Kapal Aktif", df_analysis['VESSELID'].nunique())

    with kpi3:
        if not df_analysis.empty:
            top_comp_name = df_analysis['COMPNAME'].mode()[0]
        else:
            top_comp_name = "-"
        st.metric("Top Komponen", top_comp_name)

    with kpi4:
        if not df_analysis.empty:
            avg_rh = df_analysis['RH_THIS_MONTH_UNTIL_JOBDONE'].mean()
        else:
            avg_rh = 0
        st.metric("Rata-rata Running Hours", f"{avg_rh:,.0f} Jam")

    st.markdown("---")

    # --- VISUALISASI UTAMA ---
    
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.subheader("📈 Tren Maintenance Per Bulan")
        if not df_analysis.empty:
            jobs_per_month = df_analysis.groupby('Month_Year').size().reset_index(name='Count').sort_values('Month_Year')
            suffix = " (RH > 0)" if exclude_zero_rh else " (Semua)"
            fig_trend = px.line(jobs_per_month, x='Month_Year', y='Count', markers=True, 
                                title=f"Jumlah Job Report per Bulan{suffix}")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Tidak ada data tren.")

    with row1_col2:
        st.subheader("🍩 Distribusi Frekuensi")
        if not df_analysis.empty:
            freq_counts = df_analysis['FREQ_TYPE'].value_counts().reset_index()
            freq_counts.columns = ['Tipe', 'Jumlah']
            fig_pie = px.pie(freq_counts, values='Jumlah', names='Tipe', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    # --- VISUALISASI SPAREPART ---
    st.markdown("---")
    st.subheader("🏆 Analisis Sparepart & Komponen")
    
    col_viz_new, col_viz_right = st.columns([2, 1])
    
    with col_viz_new:
        if not df_analysis.empty:
            st.write("**Tren Komponen Paling Sering Di-Maintenance:**")
            top_n = st.slider("Jumlah Top Komponen:", 3, 15, 5)
            top_comps = df_analysis['COMPNAME'].value_counts().head(top_n).index.tolist()
            df_trend_comp = df_analysis[df_analysis['COMPNAME'].isin(top_comps)]
            comp_trend = df_trend_comp.groupby(['Month_Year', 'COMPNAME']).size().reset_index(name='Count').sort_values('Month_Year')
            
            fig_comp_trend = px.bar(
                comp_trend, x='Month_Year', y='Count', color='COMPNAME',
                text='Count', category_orders={'COMPNAME': top_comps} 
            )
            fig_comp_trend.update_traces(textposition='inside', textfont_size=10)
            st.plotly_chart(fig_comp_trend, use_container_width=True)
        else:
            st.info("Data kosong.")

    with col_viz_right:
        st.write("**Top 10 Komponen (Total Periode):**")
        if not df_analysis.empty:
            top_components = df_analysis['COMPNAME'].value_counts().head(10).reset_index()
            top_components.columns = ['Nama Komponen', 'Frekuensi']
            fig_comp = px.bar(top_components, y='Nama Komponen', x='Frekuensi', orientation='h',
                              text='Frekuensi', color='Frekuensi', color_continuous_scale='Reds')
            fig_comp.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    # --- VISUALISASI KAPAL & DELAY (FITUR BARU) ---
    st.markdown("---")
    st.header("🚢 Evaluasi Kapal & Kepatuhan Pelaporan")
    
    col_delay1, col_delay2 = st.columns(2)

    if not df_analysis.empty:
        # 1. TOP KAPAL DENGAN MAINTENANCE TERBANYAK
        with col_delay1:
            st.subheader("Aktivitas Maintenance Kapal")
            limit_vessels = 50 if show_low_activity else 15
            top_vessels = df_analysis['VESSELID'].value_counts().head(limit_vessels).reset_index()
            top_vessels.columns = ['Vessel ID', 'Jumlah Job']
            
            fig_vessel = px.bar(top_vessels, x='Vessel ID', y='Jumlah Job', text='Jumlah Job',
                                color='Jumlah Job', color_continuous_scale='Blues',
                                title="Top Kapal Berdasarkan Jumlah Laporan")
            st.plotly_chart(fig_vessel, use_container_width=True)

        # 2. TOP KAPAL PALING SERING TELAT LAPOR
        with col_delay2:
            st.subheader("Keterlambatan Pelaporan (Delay)")
            
            # Hitung rata-rata delay per kapal
            delay_per_vessel = df_analysis.groupby('VESSELID')['Delay_Days'].mean().reset_index()
            # Ambil Top 15 Paling Telat
            delay_per_vessel = delay_per_vessel.sort_values('Delay_Days', ascending=False).head(15)
            delay_per_vessel.columns = ['Vessel ID', 'Avg Delay (Hari)']
            
            fig_delay = px.bar(
                delay_per_vessel, 
                x='Avg Delay (Hari)', 
                y='Vessel ID', 
                orientation='h',
                color='Avg Delay (Hari)', 
                color_continuous_scale='Reds',
                text_auto='.1f',
                title="Top Kapal dengan Rata-rata Delay Tertinggi"
            )
            fig_delay.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_delay, use_container_width=True)
            
        # 3. PIE CHART KEPATUHAN
        st.markdown("---")
        st.subheader("Statistik Kepatuhan Global")
        
        # Kategorisasi Delay
        def categorize_delay(days):
            if days <= 1: return "Tepat Waktu (<24 Jam)"
            elif days <= 7: return "Telat Ringan (2-7 Hari)"
            elif days <= 30: return "Telat Sedang (8-30 Hari)"
            else: return "Telat Berat (>30 Hari)"
            
        df_analysis['Kategori_Delay'] = df_analysis['Delay_Days'].apply(categorize_delay)
        delay_counts = df_analysis['Kategori_Delay'].value_counts().reset_index()
        delay_counts.columns = ['Kategori', 'Jumlah']
        
        col_pie_delay, col_kpi_delay = st.columns([2, 1])
        
        with col_pie_delay:
            fig_pie_delay = px.pie(
                delay_counts, values='Jumlah', names='Kategori',
                title="Distribusi Ketepatan Waktu Pelaporan",
                color='Kategori',
                color_discrete_map={
                    "Tepat Waktu (<24 Jam)": "green",
                    "Telat Ringan (2-7 Hari)": "yellow",
                    "Telat Sedang (8-30 Hari)": "orange",
                    "Telat Berat (>30 Hari)": "red"
                },
                hole=0.4
            )
            st.plotly_chart(fig_pie_delay, use_container_width=True)
            
        with col_kpi_delay:
            avg_delay_all = df_analysis['Delay_Days'].mean()
            on_time_pct = len(df_analysis[df_analysis['Delay_Days'] <= 1]) / len(df_analysis) * 100
            
            st.metric("Rata-rata Delay Pelaporan", f"{avg_delay_all:.1f} Hari")
            st.metric("Persentase Tepat Waktu", f"{on_time_pct:.1f}%")
            st.caption("*Tepat Waktu = Input di hari yang sama atau H+1")

    # --- TABEL DATA ---
    st.markdown("---")
    
    with st.expander("📄 Lihat Detail Data (Tabel)"):
        # Menambahkan kolom Delay ke tabel
        show_cols = ['JOBREPORT_DATE', 'JOB_TIMESTAMP', 'Delay_Days', 'VESSELID', 'COMPNAME', 'JOBTITLE', 'RH_THIS_MONTH_UNTIL_JOBDONE']
        st.dataframe(df_analysis[show_cols], use_container_width=True)
        
        csv = df_analysis.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Data CSV",
            data=csv,
            file_name='filtered_maintenance_data.csv',
            mime='text/csv',
        )

    # =========================================================================
    # --- FITUR TAMBAHAN: SMART FORECASTING (FIXED DATE ERROR) ---
    # =========================================================================
    st.markdown("---")
    st.header("🔮 Prediksi Waktu Maintenance (Smart ARIMA)")
    
    st.markdown("""
    <div style="background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <strong>Metode: Log-ARIMA dengan Auto-Validation</strong><br>
        Sistem menggunakan transformasi logaritma otomatis untuk menstabilkan varian data.
        Skor akurasi (MAE/RMSE) dihitung secara <em>real-time</em> menggunakan data 3 bulan terakhir sebagai ujian.
    </div>
    """, unsafe_allow_html=True)

    # Cek Library
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        import plotly.graph_objects as go
        import numpy as np 
        has_libraries = True
    except ImportError:
        st.error("❌ Library `statsmodels` atau `numpy` belum terinstall.")
        has_libraries = False

    if has_libraries and not df_analysis.empty:
        col_fc1, col_fc2 = st.columns([1, 2])
        
        with col_fc1:
            st.subheader("⚙️ Konfigurasi")
            
            # Filter minimal 5 data historis
            comp_counts = df_analysis['COMPNAME'].value_counts()
            valid_comps = comp_counts[comp_counts >= 5].index.tolist()
            
            if not valid_comps:
                st.warning("Data historis terlalu sedikit (< 5 kejadian).")
            else:
                target_comp = st.selectbox("Pilih Sparepart:", valid_comps)
                forecast_steps = st.slider("Durasi Prediksi (Bulan):", 1, 12, 6)
                
                # --- PREPROCESSING ---
                df_ts = df_analysis[df_analysis['COMPNAME'] == target_comp].copy()
                df_ts['Date'] = pd.to_datetime(dict(year=df_ts['TAHUN'], month=df_ts['BULAN'], day=1))
                
                # Agregasi & Resampling
                ts_data = df_ts.groupby('Date').size().reset_index(name='Count')
                ts_data = ts_data.set_index('Date')
                
                # Resampling & Fill Missing Values
                ts_resampled = ts_data.resample('MS').sum().fillna(0)
                ts_series = ts_resampled['Count'] # Pastikan format Series
                
                st.info(f"Basis Data Historis: {len(ts_series)} Bulan")

        with col_fc2:
            if valid_comps and len(ts_series) >= 10: 
                try:
                    # =========================================================
                    # 1. BACKTESTING (3 BULAN TERAKHIR)
                    # =========================================================
                    train_data = ts_series.iloc[:-3]
                    test_data = ts_series.iloc[-3:]

                    train_log = np.log1p(train_data)

                    model_eval = SARIMAX(
                        train_log,
                        order=(1, 1, 1),
                        seasonal_order=(1, 0, 1, 12),
                        enforce_stationarity=False,
                        enforce_invertibility=False
                    )
                    fit_eval = model_eval.fit(disp=False)

                    fc_eval_log = fit_eval.get_forecast(steps=3)
                    pred_eval = np.expm1(fc_eval_log.predicted_mean)
                    pred_eval.index = test_data.index

                    # Error Metrics
                    mae = (test_data - pred_eval).abs().mean()
                    rmse = ((test_data - pred_eval) ** 2).mean() ** 0.5

                    mean_actual = test_data.mean()
                    nmae = mae / mean_actual if mean_actual != 0 else 0

                    # =========================================================
                    # 2. MODEL FINAL (FULL DATA)
                    # =========================================================
                    full_log = np.log1p(ts_series)

                    model_main = SARIMAX(
                        full_log,
                        order=(1, 1, 1),
                        seasonal_order=(1, 0, 1, 12),
                        enforce_stationarity=False,
                        enforce_invertibility=False
                    )
                    fit_main = model_main.fit(disp=False)

                    fc_res = fit_main.get_forecast(steps=forecast_steps)
                    pred_future = np.expm1(fc_res.predicted_mean)

                    conf_int_log = fc_res.conf_int()
                    lower = np.expm1(conf_int_log.iloc[:, 0])
                    upper = np.expm1(conf_int_log.iloc[:, 1])

                    # =========================================================
                    # 3. KPI AKURASI (RELATIF, BUKAN ABSOLUT)
                    # =========================================================
                    col_score1, col_score2, col_score3 = st.columns(3)

                    col_score1.metric("MAE", f"{mae:.2f}")
                    col_score2.metric("RMSE", f"{rmse:.2f}")
                    col_score3.metric("NMAE", f"{nmae:.2f}", help="MAE / rata-rata aktual")

                    if nmae < 0.2:
                        st.success("✅ Akurasi Tinggi (Stabil)")
                    elif nmae < 0.5:
                        st.warning("⚠️ Akurasi Sedang (Data Fluktuatif)")
                    else:
                        st.error("❌ Akurasi Rendah (High Uncertainty)")

                    # =========================================================
                    # 4. VISUALISASI
                    # =========================================================
                    hist_df = ts_series.reset_index()
                    hist_df.columns = ['Date', 'Count']

                    pred_df = pd.DataFrame({
                        'Date': pred_future.index,
                        'Prediksi': pred_future.values,
                        'Lower': lower.values,
                        'Upper': upper.values
                    })

                    numeric_cols = ['Prediksi', 'Lower', 'Upper']
                    pred_df[numeric_cols] = pred_df[numeric_cols].clip(lower=0)

                    fig_arima = go.Figure()

                    fig_arima.add_trace(go.Scatter(
                        x=hist_df['Date'], y=hist_df['Count'],
                        mode='lines+markers',
                        name='Aktual'
                    ))

                    fig_arima.add_trace(go.Scatter(
                        x=pred_df['Date'], y=pred_df['Prediksi'],
                        mode='lines+markers',
                        name='Prediksi',
                        line=dict(dash='dash')
                    ))

                    fig_arima.add_trace(go.Scatter(
                        x=pred_df['Date'], y=pred_df['Upper'],
                        mode='lines', line=dict(width=0),
                        showlegend=False
                    ))
                    fig_arima.add_trace(go.Scatter(
                        x=pred_df['Date'], y=pred_df['Lower'],
                        mode='lines', line=dict(width=0),
                        fill='tonexty',
                        name='Confidence Interval'
                    ))

                    fig_arima.update_layout(
                        title=f"Forecast Maintenance: {target_comp}",
                        xaxis_title="Periode",
                        yaxis_title="Frekuensi Maintenance",
                        hovermode="x unified"
                    )

                    st.plotly_chart(fig_arima, use_container_width=True)

                    # =========================================================
                    # 5. INSIGHT RINGKAS
                    # =========================================================
                    total_pred = int(pred_df['Prediksi'].sum())
                    st.info(f"💡 Estimasi total **{total_pred}** kejadian maintenance dalam {forecast_steps} bulan ke depan.")


                except Exception as e:
                    st.error(f"Gagal memproses model: {e}")
                    st.caption("Kemungkinan data historis tidak stabil atau memiliki gap yang terlalu lebar.")
            
            elif valid_comps:
                st.warning("⚠️ Data historis kurang dari 10 bulan. Prediksi tidak akurat.")
            else:
                st.info("👈 Pilih komponen di menu sebelah kiri.")
else:
    st.warning("⚠️ Data belum dimuat. Pastikan file Excel tersedia di folder yang benar.")

# Footer
st.markdown("""
<div style='text-align: center; margin-top: 50px; font-size: small; color: grey;'>
    Dashboard Created with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)