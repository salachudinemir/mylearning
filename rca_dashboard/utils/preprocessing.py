import pandas as pd
import os
import csv

def sniff_delimiter(uploaded_file):
    uploaded_file.seek(0)
    sample = uploaded_file.read(1024).decode('utf-8', errors='ignore')
    uploaded_file.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except Exception:
        return ','  # default fallback

def load_and_clean_data(uploaded_file, keep_all_columns=False, debug_log=False):
    def sniff_delimiter(uploaded_file):
        uploaded_file.seek(0)
        sample = uploaded_file.read(1024).decode('utf-8', errors='ignore')
        uploaded_file.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            return dialect.delimiter
        except Exception:
            return ','  # default fallback

    file_ext = os.path.splitext(uploaded_file.name)[-1].lower()

    if file_ext == ".csv":
        delimiter = sniff_delimiter(uploaded_file)
        uploaded_file.seek(0)
        try:
            df = pd.read_csv(uploaded_file, sep=delimiter, encoding='utf-8')
        except Exception:
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, sep=',', encoding='utf-8')
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    else:
        df = pd.read_excel(uploaded_file)

    if df is None or df.empty:
        raise ValueError("❌ Data tidak berhasil dimuat atau kosong.")

    # Bersihkan kolom
    df.columns = df.columns.str.strip().str.lower()
    df = df.loc[:, ~df.columns.duplicated()]

    # Normalisasi kolom circle
    df['circle'] = df['circle'].astype(str).str.strip()
    df.loc[df['circle'].isin(['', 'nan', 'NaN', 'None']), 'circle'] = 'Unknown'
    df['circle'] = df['circle'].fillna('Unknown')

    # Pastikan semua kolom subrootcause ada
    for col in ['sub_root_cause', 'subcause', 'subcause2']:
        if col not in df.columns:
            df[col] = None

    # Buat subrootcause gabungan
    df['sub_root_cause'] = df['sub_root_cause'].fillna(df['subcause']).fillna(df['subcause2']).fillna('Unknown') # <- Isi kolom sub_root_cause terlebih dahulu
    df['subrootcause'] = df['sub_root_cause']


    selected_cols = [
        'circle', 'createfaultfirstoccurtime', 'severity', 'mttr',
        'sub_root_cause', 'subcause', 'slastatus', 'rca',
        'sitename', 'subcause2', 'subrootcause'
    ]
    missing_cols = [col for col in selected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom berikut tidak ditemukan: {missing_cols}")

    if not keep_all_columns:
        df = df[selected_cols].copy()
    else:
        df = df.copy()

    # Konversi tanggal dan buat label bulan
    df['createfaultfirstoccurtime'] = pd.to_datetime(df['createfaultfirstoccurtime'], dayfirst=True, errors='coerce')
    mask_invalid_date = df['createfaultfirstoccurtime'].isna()
    if debug_log and mask_invalid_date.any():
        print(f"DEBUG: {mask_invalid_date.sum()} baris dengan tanggal tidak valid.")

    df['bulan_label'] = df['createfaultfirstoccurtime'].dt.strftime('%b %Y')
    df.loc[mask_invalid_date, 'bulan_label'] = 'Unknown'
    df['bulan_sort'] = df['createfaultfirstoccurtime'].dt.to_period('M').dt.to_timestamp()
    df.loc[mask_invalid_date, 'bulan_sort'] = pd.Timestamp('1970-01-01')

    # Normalisasi dan bersihkan sub_root_cause, subcause, subcause2
    for col in ['sub_root_cause', 'subcause', 'subcause2']:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({'': None, 'nan': None, 'NaN': None, 'None': None})

    # Gabungkan prioritas fallback ke subrootcause
    df['subrootcause'] = df['sub_root_cause']
    df['subrootcause'] = df['subrootcause'].fillna(df['subcause'])
    df['subrootcause'] = df['subrootcause'].fillna(df['subcause2'])
    df['subrootcause'] = df['subrootcause'].fillna('Unknown')

    # MTTR sebagai numeric
    df['mttr'] = df['mttr'].astype(str).str.replace(',', '.', regex=False)
    df['mttr'] = pd.to_numeric(df['mttr'], errors='coerce')

    # Sekarang baru assign ke filtered_df *setelah* semua modifikasi selesai
    filtered_df = df.copy()

    # Pastikan kolom penting tidak ada NaN di filtered_df
    filtered_df['bulan_label'] = filtered_df['bulan_label'].fillna('Unknown')
    filtered_df['bulan_sort'] = filtered_df['bulan_sort'].fillna(pd.Timestamp('1970-01-01'))
    filtered_df['rca'] = filtered_df['rca'].fillna('Unknown')
    filtered_df['severity'] = filtered_df['severity'].fillna('Unknown')

    # Buat trend bulanan RCA
    trend_bulanan = (
        filtered_df
        .groupby(['bulan_label', 'bulan_sort', 'rca'])
        .size().reset_index(name='count')
        .sort_values(by='bulan_sort')
    )

    # Total gangguan per bulan dan growth YoY/QoQ
    total_bulanan = (
        filtered_df
        .groupby(['bulan_sort'])
        .size().reset_index(name='total_count')
        .sort_values(by='bulan_sort')
    )
    total_bulanan['year'] = total_bulanan['bulan_sort'].dt.year
    total_bulanan['month'] = total_bulanan['bulan_sort'].dt.month
    total_bulanan['total_count_last_year'] = total_bulanan.groupby('month')['total_count'].shift(1)
    total_bulanan['yoy_growth_%'] = (
        (total_bulanan['total_count'] - total_bulanan['total_count_last_year']) /
        total_bulanan['total_count_last_year']
    ) * 100
    total_bulanan['quarter'] = total_bulanan['bulan_sort'].dt.to_period('Q')
    total_bulanan['total_count_last_quarter'] = total_bulanan['total_count'].shift(3)
    total_bulanan['qoq_growth_%'] = (
        (total_bulanan['total_count'] - total_bulanan['total_count_last_quarter']) /
        total_bulanan['total_count_last_quarter']
    ) * 100
    total_bulanan['bulan_label'] = total_bulanan['bulan_sort'].dt.strftime('%b %Y')

    # Rata-rata MTTR per RCA
    avg_mttr = filtered_df.groupby('rca')['mttr'].mean().sort_values(ascending=False)

    # Pivot table sesuai app.py (index=rca, columns=severity)
    pivot = filtered_df.pivot_table(
        index='rca',
        columns='severity',
        values='circle',
        aggfunc='count',
        fill_value=0
    )

    # Hapus kolom-kolom sumber yang sudah tidak diperlukan
    cols_to_drop = ['sub_root_cause', 'subcause', 'subcause2']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
    filtered_df = filtered_df.drop(columns=[col for col in cols_to_drop if col in filtered_df.columns])

    return df, filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot

def fill_sub_root_cause(df):
    # Pastikan kolom-kolom sumber ada dulu
    for col in ['sub_root_cause', 'subcause', 'subcause2']:
        if col not in df.columns:
            df[col] = None

    # Isi sub_root_cause yang kosong/NaN dengan fallback dari subcause, lalu subcause2
    df['sub_root_cause'] = df['sub_root_cause'].fillna(df['subcause'])
    df['sub_root_cause'] = df['sub_root_cause'].fillna(df['subcause2'])
    df['sub_root_cause'] = df['sub_root_cause'].fillna('Unknown')

    return df