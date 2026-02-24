import pandas as pd
import re

# ==========================================
# 1. KONFIGURASI DAFTAR MEREK & KATEGORI
# ==========================================
BRANDS = [
    'YANMAR', 'CUMMINS', 'MITSUBISHI', 'CATERPILLAR', 'CAT', 'KOMATSU', 'DAIHATSU', 
    'PERKINS', 'VOLVO', 'SCANIA', 'MAN', 'DEUTZ', 'WEICHAI', 'NISSAN', 'HINO', 'ISUZU', 
    'TOYOTA', 'HONDA', 'SUZUKI', 'YAMAHA', 'HYUNDAI', 'KIA', 'MAZDA', 'MERCEDES', 'BMW',
    'FORD', 'CHEVROLET', 'GM', 'JEEP', 'LAND ROVER', 'RENAULT', 'PEUGEOT', 'FIAT', 'IVECO',
    'DONALDSON', 'FLEETGUARD', 'SAKURA', 'JIMCO', 'UNION', 'BALDWIN', 'FRAM', 'MANN',
    'RACOR', 'PARKER', 'SURE', 'VIC', 'ASPIRA', 'DENSO', 'BOSCH', 'NGK', 'CHAMPION',
    'SCHNEIDER', 'ABB', 'SIEMENS', 'OMRON', 'FUJI', 'MITSUBISHI ELECTRIC', 'LG', 'LS', 
    'PHILIPS', 'OSRAM', 'PANASONIC', 'MATSUSHITA', 'TOSHIBA', 'HITACHI', 'YOKOGAWA',
    'CHINT', 'GAE', 'HAGER', 'LEGRAND', 'BROCO', 'UTEX', 'FLUKE', 'KYORITSU', 'SANWA',
    'AUTONICS', 'TELEMECANIQUE', 'MERLIN GERIN', 'SOCOMEC', 'FINDER', 'IDEC',
    'EBARA', 'GRUNDFOS', 'KSB', 'WILO', 'SULZER', 'FLOWSERVE', 'ITT', 'XYLEM', 'PENTAIR',
    'TAIKO', 'SHINKO', 'TEIKOKU', 'NANIWA', 'HEISHIN', 'SASAKURA', 'MIURA', 'VOLCANO',
    'KITZ', 'TOYO', 'YOSHITAKE', 'SHOWA', 'TOMOE', 'CRANE', 'JENKINS', 'SPIRAX SARCO',
    'TLV', 'VELAN', 'ONDAL', 'GF', 'AVK', 'ONDINE', 'HIGHLAND',
    'SKF', 'FAG', 'NTN', 'KOYO', 'TIMKEN', 'NSK', 'NACHI', 'ASAHI', 'IKO', 'INA', 'THK',
    'FYH', 'NOK', 'VALQUA', 'GARLOCK', 'KLINGRIT', 'CHESTERTON', 'JAMES WALKER',
    'ALFA LAVAL', 'WESTFALIA', 'GEA', 'MITSUBISHI KAKOKI', 'SAMGONG', 'HANSHIN',
    'AKASAKA', 'MAK', 'WARTSILA', 'SULZER', 'MAN B&W', 'PIELSTICK', 'MTU', 'DETROIT',
    'NIIGATA', 'KAWASAKI', 'IHI', 'NAPIER', 'WOODWARD', 'GARRETT', 'HOLSET', 'BORGWARNER',
    'TANABE', 'HATLAPA', 'MACGREGOR', 'SPERRY', 'FURUNO', 'JRC', 'TOKYO KEIKI',
    'TEKIRO', 'KRISBOW', 'BOSCH', 'MAKITA', 'DEWALT', 'STANLEY', 'SNAP-ON', 'FACOM',
    'RIDGID', 'LOCTITE', 'DEVCON', 'WD-40', 'MOLYKOTE', 'THREEBOND', 'DEXBOND',
    'JOTUN', 'HEMPEL', 'INTERNATIONAL', 'NIPPON PAINT', 'KANSAI', 'SIGMA',
    'WUXI', 'ANTAI', 'GUANGZHOU', 'NANTONG', 'ZIBO', 'ZICHAI', 'SHANGHAI', 'HANGZHOU',
    'SANY', 'XCMG', 'LIUGONG', 'ZOOMLION', 'SHANTUI', 'FOTON', 'FAW', 'DONGFENG',
    'HOWO', 'SINOTRUK', 'JAC', 'WEICHAI', 'YUCHAI', 'ADVANCE', 'FESTO', 'SMC', 'CKD',
    'REXROTH', 'VICKERS', 'EATON', 'DANFOSS', 'HYDAC'
]

BRANDS.sort(key=len, reverse=True)
brand_pattern = r'\b(' + '|'.join(map(re.escape, BRANDS)) + r')\b'

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
# 2. FUNGSI PEMERSIHAN (BARANG & SATUAN)
# ==========================================
def clean_satuan(satuan):
    if not isinstance(satuan, str) or pd.isna(satuan):
        return 'UNKNOWN'
        
    s = str(satuan).strip().upper()
    s = s.replace('`', '').replace(';', '').replace('[', '').replace(']', '')
    
    mapping_satuan = {
        'PC': 'PCS', 'BH': 'PCS', 'BUAH': 'PCS', 'BJ': 'PCS', 'BIJI': 'PCS', 'EA': 'PCS', 
        'PCE': 'PCS', 'PIECE': 'PCS', 'PIECES': 'PCS', 'PCS.': 'PCS', 'PCSX30': 'PCS', 
        'PCS (G)': 'PCS', 'BPCS': 'PCS', 'P0CS': 'PCS', 'APCS': 'PCS', '6PCS': 'PCS', 
        'SPCS': 'PCS', 'EPCS': 'PCS', 'PCCCCCCS': 'PCS', '0BH': 'PCS', 'BBH': 'PCS', 
        'PCC': 'PCS', 'POCS': 'PCS', 'PCD': 'PCS', 'PCA': 'PCS', 'PCT': 'PCS', 
        'PCR': 'PCS', 'OCS': 'PCS', 'CS': 'PCS', 'PCS3': 'PCS', 'PSC': 'PCS', 'N00163.5BH': 'PCS',
        'UNT': 'UNIT', 'UNITS': 'UNIT', 'UNIIT': 'UNIT', 'UMIT': 'UNIT', 'UNI': 'UNIT', '1 UNIT': 'UNIT', 'UNIT/SET': 'UNIT',
        'S/E': 'SET', 'SETS': 'SET', 'SET/E': 'SET', 'SET ENG': 'SET', 'SET CYL': 'SET', 
        'SET ENGINE': 'SET', 'ENGINE SET': 'SET', 'SET/ENG': 'SET', 'SETY': 'SET', 
        'SSET': 'SET', 'SETT': 'SET', 'SET UNIT': 'SET', 'ST': 'SET', 'S': 'SET',
        'PAIR': 'PSG', 'PRS': 'PSG', 'PR': 'PSG', 'PS': 'PSG', 'PAIRS': 'PSG', 'PASANG': 'PSG', 'PSNG': 'PSG', 
        'LSN': 'LUSIN', 'DOZ': 'LUSIN', 'DZN': 'LUSIN', 'DZ': 'LUSIN', 'DOZEN': 'LUSIN',
        'METER': 'MTR', 'M': 'MTR', 'MTRS': 'MTR', 'METERS': 'MTR', 'METRES': 'MTR', 'METRE': 'MTR', 'MTS': 'MTR',
        'LJR': 'LJR', 'LONJOR': 'LJR', 'LENGTH': 'LJR', 'LENGHT': 'LJR', 'LGHT': 'LJR', 
        'LGH': 'LJR', 'LGTH': 'LJR', 'LNJR': 'LJR', 'LNJ': 'LJR', 'LJG': 'LJR',
        'BTG': 'BTG', 'BATANG': 'BTG', 'BTNG': 'BTG', 'BTTG': 'BTG',
        'PTG': 'PTG', 'PTNG': 'PTG', 'POTONG': 'PTG',
        'LITER': 'LTR', 'L': 'LTR', 'LTRS': 'LTR', 'LITRES': 'LTR', 'LITRE': 'LTR', 
        'LT': 'LTR', 'LTS': 'LTR', 'KILO LITER': 'LTR',
        'KGS': 'KG', 'KILOGRAM': 'KG', 'KGM': 'KG', 'KILO': 'KG', 'KG/PKT': 'KG',
        'GR': 'GRAM', 'GRM': 'GRAM', 'G': 'GRAM',
        'LBS': 'LBS', 'ONS': 'ONS', 'TON': 'TON', 'TONS': 'TON',
        'GLN': 'GALON', 'GALLON': 'GALON',
        'ML': 'ML', 'CC': 'ML',
        'ROL': 'ROLL', 'ROLLS': 'ROLL', 'REEL': 'ROLL', 'COIL': 'ROLL', 'COILS': 'ROLL', 
        'REELS': 'ROLL', 'ROOL': 'ROLL', 'ROL (3 MTR': 'ROLL',
        'DOS': 'BOX', 'DUS': 'BOX', 'KOTAK': 'BOX', 'B0X': 'BOX', 'KTK': 'BOX', 
        'CASE': 'BOX', 'KIST': 'BOX', 'KDS': 'BOX', 'CARTON': 'BOX', 'CTN': 'BOX',
        'PAK': 'PACK', 'PKT': 'PACK', 'PACKS': 'PACK', 'PACKET': 'PACK', 'BKS': 'PACK', 
        'BUNGKUS': 'PACK', 'PAKET': 'PACK', 'PKTS': 'PACK', 'PCK': 'PACK', 'PAX': 'PACK', 'SACHET': 'PACK',
        'KALENG': 'KLG', 'CAN': 'KLG', 'CANS': 'KLG', 'TIN': 'KLG', 'KLNG': 'KLG', 'NKLG': 'KLG',
        'BOTOL': 'BTL', 'BOTTLE': 'BTL', 'BTLS': 'BTL', 'BTS': 'BTL', 'TUBE': 'TUBE', 'TUB': 'TUBE', 'AMPUL': 'TUBE', 'VIAL': 'TUBE', 'VIALS': 'TUBE',
        'LEMBAR': 'LBR', 'LMB': 'LBR', 'LMBR': 'LBR', 'SHT': 'LBR', 'SHEET': 'LBR', 'SHEETS': 'LBR', 'LB': 'LBR',
        'TBG': 'TABUNG', 'CYL': 'TABUNG', 'CYLINDER': 'TABUNG', '/CYL': 'TABUNG', 'TANKI': 'TABUNG',
        'JRG': 'JERIGEN', 'JRGN': 'JERIGEN', 'JAR': 'JERIGEN',
        'TBLT': 'TAB', 'TABLET': 'TAB', 'TABS': 'TAB', 'TBL': 'TAB',
        'SAK': 'SAK', 'KRG': 'SAK', 'KARUNG': 'SAK', 'BAG': 'SAK', 'BAGS': 'SAK', 'ZAK': 'SAK',
        'RIM': 'RIM', 'REAM': 'RIM', 'RIM/LBR': 'RIM',
        'SLOP': 'SLOP'
    }
    return mapping_satuan.get(s, s)

def clean_and_parse_v2(text):
    if not isinstance(text, str) or pd.isna(text) or text.strip() == '':
        return pd.Series(['LAIN-LAIN', '', '', '', 'LAIN-LAIN (TIDAK ADA NAMA)'])
    
    original_text = str(text).upper().strip()
    
    found_brands = re.findall(brand_pattern, original_text)
    brand = max(found_brands, key=len) if found_brands else ''
    
    category = 'LAIN-LAIN'
    for cat, keywords in CATEGORIES.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', original_text) for kw in keywords):
            category = cat
            break
            
    part_no = ''
    pn_match = re.search(r'(?:P/N|NO\.|REF|CODE|PART NO)[\s:.]*([A-Z0-9\-\.]+)', original_text)
    if pn_match:
        part_no = pn_match.group(1).strip('.')
    else:
        tokens = original_text.replace(',', ' ').split()
        if tokens:
            first = tokens[0]
            blacklist = ['10K', '5K', '16K', '20K', '30K', 'PN10', 'PN16', 'SCH40', 'SCH80', 'TYPE', 'SIZE']
            if any(char.isdigit() for char in first) and len(first) > 2 and first not in blacklist:
                 part_no = first

    specs = []
    dim_matches = re.findall(r'\b\d+(?:[\.,]\d+)?\s*[xX\*]\s*\d+(?:[\.,]\d+)?(?:\s*[xX\*]\s*\d+(?:[\.,]\d+)?)?\b', original_text)
    specs.extend(dim_matches)
    unit_matches = re.findall(r'\b\d+(?:[\.,]\d+)?\s*(?:MM|CM|M|INCH|KG|LTR|VOLT|WATT|AMP|A|HP|KW|KVA|BAR|PSI|V|HZ|")', original_text)
    specs.extend(unit_matches)
    rating_matches = re.findall(r'\b(?:10K|5K|16K|20K|30K|SCH\s*\d+|PN\s*\d+|JIS|ANSI|DIN|DN\d+)\b', original_text)
    specs.extend(rating_matches)
    
    spec_str = ', '.join(sorted(set(specs), key=len, reverse=True))
    
    remainder = original_text
    if brand: remainder = re.sub(r'\b' + re.escape(brand) + r'\b', '', remainder)
    if part_no: remainder = remainder.replace(part_no, '')
    
    descriptive_name = re.sub(r'[^\w\s]', ' ', remainder)
    descriptive_name = re.sub(r'\s+', ' ', descriptive_name).strip()
    
    components = [category]
    if descriptive_name: components.append(descriptive_name)
    if spec_str: components.append(spec_str)
    if brand: components.append(brand)
    if part_no: components.append(f"(P/N: {part_no})")
        
    tidy_name = ' '.join(components)
    
    if tidy_name == 'LAIN-LAIN':
        tidy_name = f"LAIN-LAIN - {original_text}"

    return pd.Series([category, brand, part_no, spec_str, tidy_name])

# ==========================================
# 3. EKSEKUSI PADA FILE ANDA
# ==========================================

file_path = "Magang Sparepart 2025/20260211 - Master Barang Aktif.xlsx"
print(f"Membaca file {file_path}...")
df_barang = pd.read_excel(file_path)

print("Mengekstraksi, merapikan data, dan membersihkan satuan...")

df_barang['SATUAN_RAPIH'] = df_barang['SATUAN'].apply(clean_satuan)
df_barang[['KATEGORI_EKSTRAK', 'MEREK', 'PART_NO', 'SPESIFIKASI', 'NAMA_BARANG_RAPIH']] = df_barang['NAMABARANG'].apply(clean_and_parse_v2)

# Susun Kolom untuk Output Awal
output_cols = [
    'KODEBARANG', 'NAMABARANG', 'NAMA_BARANG_RAPIH', 'SATUAN', 'SATUAN_RAPIH',
    'NAMAKATEGORI', 'KATEGORI_EKSTRAK', 'MEREK', 'PART_NO', 'SPESIFIKASI'
]
df_final = df_barang[output_cols]

print("Mengelompokkan data...")
# --- PERUBAHAN UTAMA ADA DI BAGIAN BAWAH INI ---
df_grouped = df_final.groupby(['NAMA_BARANG_RAPIH', 'SATUAN_RAPIH']).agg({
    'KODEBARANG': lambda x: ', '.join(x),
    'NAMABARANG': lambda x: ' | '.join(x),
    # Menggabungkan kategori-kategori asli yang berbeda, membuang duplikatnya
    'NAMAKATEGORI': lambda x: ', '.join(sorted(set(str(val) for val in x if pd.notna(val)))),
    'KATEGORI_EKSTRAK': 'first',
    'MEREK': 'first',
    'PART_NO': 'first',
    'SPESIFIKASI': 'first'
}).reset_index()

# Ubah nama kolom agar lebih jelas
df_grouped.rename(columns={
    'KODEBARANG': 'GABUNGAN_KODEBARANG', 
    'NAMABARANG': 'VARIAN_NAMA_ASLI',
    'NAMAKATEGORI': 'GABUNGAN_KATEGORI_ASLI' # Nama kolom diganti agar memperjelas kalau isinya gabungan kategori
}, inplace=True)

# Susun ulang urutan kolom final agar enak dibaca
final_output_cols = [
    'GABUNGAN_KODEBARANG',
    'NAMA_BARANG_RAPIH',
    'SATUAN_RAPIH',
    'KATEGORI_EKSTRAK',
    'MEREK',
    'PART_NO',
    'SPESIFIKASI',
    'VARIAN_NAMA_ASLI',
    'GABUNGAN_KATEGORI_ASLI' # Kolom ini ditaruh di paling belakang
]
df_grouped = df_grouped[final_output_cols]

# Simpan hasil menjadi 1 file saja
output_file = 'Master_Barang_Aktif_Final2.csv'
df_grouped.to_csv(output_file, index=False)

print(f"Sukses! Data telah digabungkan dan disimpan di: {output_file}")