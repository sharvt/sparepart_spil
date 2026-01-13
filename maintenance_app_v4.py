import streamlit as st
import pandas as pd
import os

st.title("🕵️ Diagnostic Tool: File System Check")

# 1. Cek Folder Kerja Saat Ini
current_dir = os.getcwd()
st.write(f"📂 **Current Working Directory:** `{current_dir}`")

# 2. Cek List File di Root
st.subheader("1. List File di Root Directory")
files_in_root = os.listdir(current_dir)
st.code(files_in_root)

# 3. Cek Keberadaan Folder Data
folder_name = "Magang Sparepart 2025" # Nama folder persis seperti di kode Anda
st.subheader(f"2. Pengecekan Folder: '{folder_name}'")

if folder_name in files_in_root:
    st.success(f"✅ Folder '{folder_name}' DITEMUKAN!")
    
    # Cek isi dalam folder tersebut
    files_in_subfolder = os.listdir(os.path.join(current_dir, folder_name))
    st.write(f"Isi dalam folder `{folder_name}`:")
    st.code(files_in_subfolder)
    
    # 4. Coba Load Data Sampel
    st.subheader("3. Test Load Data (Excel)")
    
    # Nama file target
    file_target = "Maintenance Job Report ALL ACTIVE VESSEL 2024.xlsx"
    full_path = os.path.join(current_dir, folder_name, file_target)
    
    if file_target in files_in_subfolder:
        st.info(f"Mencoba membaca file: {full_path} ...")
        try:
            # Coba baca 5 baris saja untuk test engine
            df_test = pd.read_excel(full_path, nrows=5)
            st.success("✅ BERHASIL membaca file Excel!")
            st.dataframe(df_test)
        except Exception as e:
            st.error("❌ GAGAL membaca file Excel.")
            st.error(f"Error Message: {e}")
            st.warning("Tips: Pastikan library 'openpyxl' ada di requirements.txt")
    else:
        st.error(f"❌ File '{file_target}' TIDAK DITEMUKAN di dalam folder tersebut.")
        st.write("Pastikan nama file persis (termasuk huruf besar/kecil dan ekstensi .xlsx)")

else:
    st.error(f"❌ Folder '{folder_name}' TIDAK DITEMUKAN di root directory.")
    st.warning("Kemungkinan penyebab:")
    st.markdown("""
    1. Folder tidak ikut ter-upload ke GitHub (karena kosong atau `.gitignore`).
    2. Nama folder di GitHub berbeda huruf besar/kecil (misal: `magang sparepart` vs `Magang Sparepart`).
    3. File Excel berada langsung di root (sejajar dengan app.py), bukan di dalam folder.
    """)

# 5. Cek Requirements
st.subheader("4. Cek Library Terinstall")
try:
    import openpyxl
    st.success(f"✅ Library `openpyxl` terinstall (Versi: {openpyxl.__version__})")
except ImportError:
    st.error("❌ Library `openpyxl` BELUM terinstall. Tambahkan ke requirements.txt!")
