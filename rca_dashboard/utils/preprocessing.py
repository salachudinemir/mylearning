import pandas as pd
import os

def load_and_clean_data(uploaded_file):
    file_ext = os.path.splitext(uploaded_file.name)[-1].lower()

    if file_ext == ".csv":
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip().str.lower()

        # Definisi selected_cols di sini
    selected_cols = ['createfaultfirstoccurtime', 'severity', 'mttr', 'sub_root_cause', 'subcause', 'slastatus', 'rca', 'sitename']

    # Cek apakah kolom-kolom ini ada
    missing_cols = [col for col in selected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom berikut tidak ditemukan: {missing_cols}")
    
    # Filter kolom yang dibutuhkan
    df = df[selected_cols].copy()
    
    # Parsing dan pembersihan data
    df['createfaultfirstoccurtime'] = pd.to_datetime(df['createfaultfirstoccurtime'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['createfaultfirstoccurtime'])
    
    df['severity'] = df['severity'].astype(str).str.strip()
    df['mttr'] = df['mttr'].astype(str).str.replace(',', '.', regex=False)
    df['mttr'] = pd.to_numeric(df['mttr'], errors='coerce')
    df = df.dropna(subset=['mttr'])
    
    # Buat label dan urutan bulan
    df['bulan_label'] = df['createfaultfirstoccurtime'].dt.strftime('%b %Y')
    df['bulan_sort'] = df['createfaultfirstoccurtime'].dt.to_period('M').dt.to_timestamp()
    
    # Simpan salinan untuk analisis lebih lanjut
    filtered_df = df.copy()

    trend_bulanan = (
        filtered_df.groupby(['bulan_label', 'bulan_sort', 'rca'])
        .size().reset_index(name='count')
        .sort_values(by='bulan_sort')
    )

    total_bulanan = (
        filtered_df.groupby(['bulan_sort'])
        .size().reset_index(name='total_count')
        .sort_values(by='bulan_sort')
    )
    total_bulanan['year'] = total_bulanan['bulan_sort'].dt.year
    total_bulanan['month'] = total_bulanan['bulan_sort'].dt.month
    total_bulanan['total_count_last_year'] = total_bulanan.groupby('month')['total_count'].shift(1)
    total_bulanan['yoy_growth_%'] = (
        (total_bulanan['total_count'] - total_bulanan['total_count_last_year']) / total_bulanan['total_count_last_year']
    ) * 100
    total_bulanan['quarter'] = total_bulanan['bulan_sort'].dt.to_period('Q')
    total_bulanan['total_count_last_quarter'] = total_bulanan['total_count'].shift(3)
    total_bulanan['qoq_growth_%'] = (
        (total_bulanan['total_count'] - total_bulanan['total_count_last_quarter']) / total_bulanan['total_count_last_quarter']
    ) * 100
    total_bulanan['bulan_label'] = total_bulanan['bulan_sort'].dt.strftime('%b %Y')

    avg_mttr = filtered_df.groupby('rca')['mttr'].mean().sort_values(ascending=False)

    pivot = filtered_df.pivot_table(index='severity', columns='rca', aggfunc='size', fill_value=0)

    return df, filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot
