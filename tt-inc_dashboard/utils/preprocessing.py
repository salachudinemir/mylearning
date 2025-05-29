import pandas as pd

def load_data(file):
    """
    Load CSV file menjadi DataFrame pandas.
    """
    df = pd.read_csv(file)
    return df

def clean_data(df):
    """
    Bersihkan dataframe:
    - Normalisasi nama kolom (lowercase, hapus spasi dan titik)
    - Hindari duplikat nama kolom dengan suffix angka
    - Convert kolom datetime tertentu ke tipe datetime
    - Tambahkan kolom week, month, quarter berdasarkan kolom 'createtime' dengan format yang rapi
    - Konversi kolom durasi ke numerik
    
    Return dataframe yang sudah dibersihkan.
    """
    # Bersihkan dan normalisasi nama kolom
    new_cols = []
    seen = set()
    for col in df.columns:
        col_clean = (
            col.strip()
               .lower()
               .replace(' ', '')
               .replace('.', '')
        )
        if col_clean in seen:
            suffix = 1
            while f"{col_clean}_{suffix}" in seen:
                suffix += 1
            col_clean = f"{col_clean}_{suffix}"
        seen.add(col_clean)
        new_cols.append(col_clean)
    df.columns = new_cols

    # List kolom datetime yang sering ada di dataset
    datetime_cols = ['createtime', 'faultfirstoccurtime', 'submittime', 'closetime', 'createat', 'closuretime']

    # Convert kolom datetime ke tipe datetime pandas
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Tambahkan kolom week, month, quarter dari kolom 'createtime'
    if 'createtime' in df.columns:
        dt_col = df['createtime']
        year = dt_col.dt.year.astype('Int64').astype(str)  # Gunakan Int64 untuk menangani NaT
        week = dt_col.dt.isocalendar().week.astype('Int64').astype(str).str.zfill(2)
        month = dt_col.dt.month.astype('Int64').astype(str).str.zfill(2)
        quarter = dt_col.dt.quarter.astype('Int64').astype(str)

        df['week'] = year + '-W' + week
        df['month'] = year + '-' + month
        df['quarter'] = year + '-Q' + quarter

    # Kolom durasi yang sering ada di dataset, convert ke numeric
    duration_cols = ['restoreduration', 'resolveduration', 'createduration', 'faultrecoverytime', 'faultresolvingtime']
    for col in duration_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df
