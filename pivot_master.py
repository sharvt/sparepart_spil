import pandas as pd
import re

# ==========================================
# 1. KONFIGURASI DAFTAR MEREK (DIPERLUAS)
# ==========================================

# Daftar Merek yang sudah diperbanyak
BRANDS = [
    # MEREK UMUM & OTOMOTIF
    'YANMAR', 'CUMMINS', 'MITSUBISHI', 'CATERPILLAR', 'CAT', 'KOMATSU', 'DAIHATSU', 
    'PERKINS', 'VOLVO', 'SCANIA', 'MAN', 'DEUTZ', 'WEICHAI', 'NISSAN', 'HINO', 'ISUZU', 
    'TOYOTA', 'HONDA', 'SUZUKI', 'YAMAHA', 'HYUNDAI', 'KIA', 'MAZDA', 'MERCEDES', 'BMW',
    'FORD', 'CHEVROLET', 'GM', 'JEEP', 'LAND ROVER', 'RENAULT', 'PEUGEOT', 'FIAT', 'IVECO',
    
    # FILTER & PART PENDUKUNG
    'DONALDSON', 'FLEETGUARD', 'SAKURA', 'JIMCO', 'UNION', 'BALDWIN', 'FRAM', 'MANN',
    'RACOR', 'PARKER', 'SURE', 'VIC', 'ASPIRA', 'DENSO', 'BOSCH', 'NGK', 'CHAMPION',
    
    # ELEKTRIKAL & INSTRUMEN
    'SCHNEIDER', 'ABB', 'SIEMENS', 'OMRON', 'FUJI', 'MITSUBISHI ELECTRIC', 'LG', 'LS', 
    'PHILIPS', 'OSRAM', 'PANASONIC', 'MATSUSHITA', 'TOSHIBA', 'HITACHI', 'YOKOGAWA',
    'CHINT', 'GAE', 'HAGER', 'LEGRAND', 'BROCO', 'UTEX', 'FLUKE', 'KYORITSU', 'SANWA',
    'AUTONICS', 'TELEMECANIQUE', 'MERLIN GERIN', 'SOCOMEC', 'FINDER', 'IDEC',
    
    # POMPA, VALVE & SISTEM PERPIPAAN
    'EBARA', 'GRUNDFOS', 'KSB', 'WILO', 'SULZER', 'FLOWSERVE', 'ITT', 'XYLEM', 'PENTAIR',
    'TAIKO', 'SHINKO', 'TEIKOKU', 'NANIWA', 'HEISHIN', 'SASAKURA', 'MIURA', 'VOLCANO',
    'KITZ', 'TOYO', 'YOSHITAKE', 'SHOWA', 'TOMOE', 'CRANE', 'JENKINS', 'SPIRAX SARCO',
    'TLV', 'VELAN', 'ONDAL', 'GF', 'AVK', 'ONDINE', 'HIGHLAND',
    
    # BEARING & SEAL
    'SKF', 'FAG', 'NTN', 'KOYO', 'TIMKEN', 'NSK', 'NACHI', 'ASAHI', 'IKO', 'INA', 'THK',
    'FYH', 'NOK', 'VALQUA', 'GARLOCK', 'KLINGRIT', 'CHESTERTON', 'JAMES WALKER',
    
    # MARINE & ENGINE KHUSUS
    'ALFA LAVAL', 'WESTFALIA', 'GEA', 'MITSUBISHI KAKOKI', 'SAMGONG', 'HANSHIN',
    'AKASAKA', 'MAK', 'WARTSILA', 'SULZER', 'MAN B&W', 'PIELSTICK', 'MTU', 'DETROIT',
    'NIIGATA', 'KAWASAKI', 'IHI', 'NAPIER', 'WOODWARD', 'GARRETT', 'HOLSET', 'BORGWARNER',
    'TANABE', 'HATLAPA', 'MACGREGOR', 'SPERRY', 'FURUNO', 'JRC', 'TOKYO KEIKI',
    
    # TOOLS & CHEMICALS
    'TEKIRO', 'KRISBOW', 'BOSCH', 'MAKITA', 'DEWALT', 'STANLEY', 'SNAP-ON', 'FACOM',
    'RIDGID', 'LOCTITE', 'DEVCON', 'WD-40', 'MOLYKOTE', 'THREEBOND', 'DEXBOND',
    'JOTUN', 'HEMPEL', 'INTERNATIONAL', 'NIPPON PAINT', 'KANSAI', 'SIGMA',
    
    # MEREK CINA/LAINNYA (SERING MUNCUL)
    'WUXI', 'ANTAI', 'GUANGZHOU', 'NANTONG', 'ZIBO', 'ZICHAI', 'SHANGHAI', 'HANGZHOU',
    'SANY', 'XCMG', 'LIUGONG', 'ZOOMLION', 'SHANTUI', 'FOTON', 'FAW', 'DONGFENG',
    'HOWO', 'SINOTRUK', 'JAC', 'WEICHAI', 'YUCHAI', 'ADVANCE', 'FESTO', 'SMC', 'CKD',
    'REXROTH', 'VICKERS', 'EATON', 'DANFOSS', 'HYDAC'
]

# Urutkan merek berdasarkan panjang teks (terpanjang duluan) untuk prioritas regex
# Contoh: Agar "MITSUBISHI ELECTRIC" terambil utuh, bukan cuma "MITSUBISHI"
BRANDS.sort(key=len, reverse=True)

# Buat Pola Regex Satu Kali (Optimasi Kinerja)
# \b artinya word boundary (batas kata), mencegah ITT terambil dari FITTING
brand_pattern = r'\b(' + '|'.join(map(re.escape, BRANDS)) + r')\b'

# Konfigurasi Kategori (Sama seperti sebelumnya)
CATEGORIES = {
    'BEARING': ['BEARING', 'LAHER', 'BANTALAN', 'BALL BEARING', 'ROLLER BEARING', 'PILLOW BLOCK', 'CONE', 'CUP'],
    'SEAL': ['SEAL', 'SIL', 'OIL SEAL', 'O-RING', 'ORING', 'GASKET', 'PACKING', 'PAKING', 'MECHANICAL SEAL'],
    'VALVE': ['VALVE', 'KRAN', 'GATE', 'GLOBE', 'BALL', 'BUTTERFLY', 'CHECK', 'SAFETY', 'RELIEF', 'SOLENOID', 'ANGLE', 'COCK'],
    'FILTER': ['FILTER', 'SARINGAN', 'STRAINER', 'SEPARATOR', 'PURIFIER', 'ELEMENT', 'CARTRIDGE', 'BREATHER'],
    'PUMP': ['PUMP', 'POMPA', 'IMPELLER', 'CASING', 'SHAFT', 'ROTOR', 'STATOR', 'VOLUTE', 'DIFFUSER'],
    'ENGINE PART': ['PISTON', 'LINER', 'RING', 'ROD', 'CRANKSHAFT', 'CAMSHAFT', 'HEAD', 'ROCKER', 'INJECTOR', 'NOZZLE', 'PLUNGER', 'TURBO', 'ENGINE', 'DIESEL', 'METAL'],
    'ELECTRICAL': ['KABEL', 'CABLE', 'WIRE', 'LAMPU', 'LAMP', 'LIGHT', 'BOHLAM', 'FUSE', 'MCB', 'MCCB', 'CONTACTOR', 'RELAY', 'SENSOR', 'SWITCH', 'MOTOR', 'GENERATOR', 'AVR', 'BATTERY', 'PANEL', 'TRAFO'],
    'PIPE FITTING': ['PIPE', 'PIPA', 'HOSE', 'FLANGE', 'ELBOW', 'TEE', 'REDUCER', 'COUPLING', 'UNION', 'NIPPLE', 'SOCKET', 'ADAPTER', 'FITTING', 'CONNECTOR'],
    'FASTENER': ['BAUT', 'MUR', 'BOLT', 'NUT', 'SCREW', 'WASHER', 'STUD', 'PIN', 'RIVET', 'CLAMP', 'CLIP', 'BRACKET'],
    'TOOL': ['TOOL', 'ALAT', 'KUNCI', 'WRENCH', 'SPANNER', 'HAMMER', 'OBENG', 'DRILL', 'GERINDA', 'CUTTER', 'MEASURE', 'PLIER', 'TANG'],
    'CHEMICAL': ['CAT', 'PAINT', 'THINNER', 'GREASE', 'OLI', 'OIL', 'LUBRICANT', 'LEM', 'GLUE', 'SEALANT', 'RESIN', 'HARDENER', 'CLEANER'],
    'SAFETY': ['SAFETY', 'HELMET', 'GLOVE', 'SHOE', 'BOOT', 'MASKER', 'GOGGLE', 'WEARPACK', 'HARNESS', 'LIFE', 'EXTINGUISHER', 'APAR'],
    'STATIONERY': ['KERTAS', 'PEN', 'BUKU', 'BINDER', 'MAP', 'STAPLES', 'TINTA', 'TONER', 'CARTON', 'LAKBAN', 'TAPE']
}

# ==========================================
# 2. FUNGSI UTAMA
# ==========================================

def clean_and_parse_v2(text):
    if not isinstance(text, str):
        return pd.Series(['', '', '', '', ''])
    
    original_text = text.upper()
    
    # --- 1. CARI MEREK (METODE BARU - LEBIH AKURAT) ---
    # Mencari semua merek yang cocok dengan pola "kata utuh"
    found_brands = re.findall(brand_pattern, original_text)
    
    brand = ''
    if found_brands:
        # Jika ada banyak merek (misal "FILTER OLI CAT FOR KOMATSU"), 
        # kita ambil yang paling spesifik/panjang atau yang pertama muncul.
        # Di sini saya ambil yang terpanjang sebagai prioritas.
        brand = max(found_brands, key=len)
    
    # --- 2. CARI KATEGORI ---
    category = 'LAIN-LAIN'
    for cat, keywords in CATEGORIES.items():
        # Menggunakan word boundary juga untuk kategori agar lebih akurat
        # (Misal: mencegah 'METAL' terambil dari 'METALIC')
        if any(re.search(r'\b' + re.escape(kw) + r'\b', original_text) for kw in keywords):
            category = cat
            break
            
    # --- 3. CARI PART NUMBER ---
    part_no = ''
    # Regex P/N yang diperbaiki: Menangkap P/N: XXX atau pola angka-huruf di awal
    pn_match = re.search(r'(?:P/N|NO\.|REF|CODE|PART NO)[\s:.]*([A-Z0-9\-\.]+)', original_text)
    if pn_match:
        part_no = pn_match.group(1).strip('.')
    else:
        # Heuristik Token Pertama
        tokens = original_text.replace(',', ' ').split()
        if tokens:
            first = tokens[0]
            # Syarat: Ada angka, panjang > 2, bukan kata umum/rating
            blacklist = ['10K', '5K', '16K', '20K', '30K', 'PN10', 'PN16', 'SCH40', 'SCH80', 'TYPE', 'SIZE']
            if any(char.isdigit() for char in first) and len(first) > 2 and first not in blacklist:
                 part_no = first

    # --- 4. CARI SPESIFIKASI (UKURAN/RATING) ---
    specs = []
    
    # Dimensi (10x20, 10*20, 10 X 20)
    dim_matches = re.findall(r'\b\d+(?:[\.,]\d+)?\s*[xX\*]\s*\d+(?:[\.,]\d+)?(?:\s*[xX\*]\s*\d+(?:[\.,]\d+)?)?\b', original_text)
    specs.extend(dim_matches)
    
    # Satuan Unit (termasuk " untuk inchi)
    # Menambahkan \b di depan angka agar tidak memotong kata (misal A20 tidak jadi 20)
    unit_matches = re.findall(r'\b\d+(?:[\.,]\d+)?\s*(?:MM|CM|M|INCH|KG|LTR|VOLT|WATT|AMP|A|HP|KW|KVA|BAR|PSI|V|HZ|")', original_text)
    specs.extend(unit_matches)
    
    # Rating/Standar
    rating_matches = re.findall(r'\b(?:10K|5K|16K|20K|30K|SCH\s*\d+|PN\s*\d+|JIS|ANSI|DIN|DN\d+)\b', original_text)
    specs.extend(rating_matches)
    
    spec_str = ', '.join(sorted(set(specs), key=len, reverse=True)) # Urutkan dari yang terpanjang
    
    # --- 5. SUSUN NAMA BERSIH ---
    # Hapus elemen yang sudah terdeteksi dari teks asli
    remainder = original_text
    if brand: remainder = re.sub(r'\b' + re.escape(brand) + r'\b', '', remainder)
    if part_no: remainder = remainder.replace(part_no, '')
    
    # Bersihkan sisa karakter non-alphanumeric
    descriptive_name = re.sub(r'[^\w\s]', ' ', remainder)
    descriptive_name = re.sub(r'\s+', ' ', descriptive_name).strip()
    
    # Susunan Akhir
    components = [category]
    if descriptive_name: components.append(descriptive_name)
    if spec_str: components.append(spec_str)
    if brand: components.append(brand)
    if part_no: components.append(f"(P/N: {part_no})")
        
    tidy_name = ' '.join(components)
    
    return pd.Series([category, brand, part_no, spec_str, tidy_name])

# ==========================================
# 3. EKSEKUSI (GANTI NAMA FILE ANDA DI SINI)
# ==========================================

print(f"Sedang membaca file...")
# Menggunakan engine='openpyxl' untuk membaca xlsx
try:
    df_barang = pd.read_excel("Magang Sparepart 2025/pivot master barang.xlsx", engine='openpyxl')
except FileNotFoundError:
    print("Error: File tidak ditemukan. Pastikan nama file dan path benar.")
    exit()

print("Sedang merapikan data...")
# Terapkan fungsi
df_barang[['KATEGORI', 'MEREK', 'PART_NO', 'SPESIFIKASI', 'NAMA_BARANG_RAPIH']] = df_barang['BARANG'].apply(clean_and_parse_v2)

# Pilih Kolom Output
output_cols = ['BARANG', 'NAMA_BARANG_RAPIH', 'KATEGORI', 'MEREK', 'SPESIFIKASI', 'PART_NO', 'COA']
df_final = df_barang[output_cols]

# Simpan
output_file = 'Master_Barang_Rapih_V3.csv'
df_final.to_csv(output_file, index=False)

print(f"Sukses! Hasil disimpan di: {output_file}")
print(df_final.head())