# utils/preprocessing.py

import os
import io
import pandas as pd
import streamlit as st
import sqlite3
import hashlib
import json
import shutil
import numpy as np
import pyarrow.parquet as pq
import pyarrow.feather as feather
from sklearn.preprocessing import LabelEncoder

SUPPORTED_FORMATS = ['.csv', '.xls', '.xlsx', '.parquet', '.feather', '.db']
CACHE_DIR = ".streamlit_cache"
METADATA_FILE = os.path.join(CACHE_DIR, "cache_metadata.json")

def get_file_hash(file) -> str:
    """Hitung MD5 hash dari isi file untuk validasi cache."""
    file.seek(0)
    content = file.read()
    file.seek(0)
    return hashlib.md5(content).hexdigest()

def save_to_cache(file, hash_id) -> str:
    """Simpan file upload ke folder lokal berdasarkan hash dan nama file."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{hash_id}_{file.name}")

    if not os.path.exists(cache_path):
        # Tulis file ke cache hanya jika belum ada
        with open(cache_path, "wb") as f:
            f.write(file.read())
        file.seek(0)
    else:
        # Pastikan pointer file tetap di awal jika cache sudah ada
        file.seek(0)

    return cache_path

def read_metadata() -> dict:
    """Baca metadata hash file yang tersimpan, kalau ada."""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

def write_metadata(metadata: dict):
    """Tulis metadata cache ke file JSON."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f)

def load_and_cache_data(file, table_name=None, usecols=None, nrows=None) -> pd.DataFrame:
    """Load file dengan cache dan hash, dukung berbagai format file."""
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Format file tidak didukung. Gunakan salah satu: {', '.join(SUPPORTED_FORMATS)}")

    if usecols == []:
        usecols = None

    file_hash = get_file_hash(file)
    metadata = read_metadata()

    last_hash = metadata.get(file.name)

    if last_hash == file_hash:
        cache_path = os.path.join(CACHE_DIR, f"{file_hash}_{file.name}")
        if not os.path.exists(cache_path):
            cache_path = save_to_cache(file, file_hash)
    else:
        cache_path = save_to_cache(file, file_hash)
        metadata[file.name] = file_hash
        write_metadata(metadata)

    try:
        if file_ext == '.csv':
            try:
                return pd.read_csv(cache_path, encoding='utf-8', usecols=usecols, nrows=nrows)
            except UnicodeDecodeError:
                return pd.read_csv(cache_path, encoding='latin1', usecols=usecols, nrows=nrows)

        elif file_ext in ['.xls', '.xlsx']:
            return pd.read_excel(cache_path, usecols=usecols, nrows=nrows)

        elif file_ext == '.parquet':
            return pd.read_parquet(cache_path, columns=usecols)

        elif file_ext == '.feather':
            return pd.read_feather(cache_path, columns=usecols)

        elif file_ext == '.db':
            with sqlite3.connect(cache_path) as conn:
                cursor = conn.cursor()
                if not table_name:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                    raise ValueError(f"File .db memiliki banyak tabel. Pilih salah satu: {tables}")
                cols_str = ', '.join(usecols) if usecols else '*'
                query = f"SELECT {cols_str} FROM {table_name}"
                return pd.read_sql_query(query, conn)

    except Exception as e:
        raise RuntimeError(f"Gagal membaca file: {e}")

def load_cached_dataframe_if_any() -> pd.DataFrame | None:
    """
    Mencari file cache terbaru dan memuatnya jadi DataFrame.
    Return None jika tidak ada cache.
    """
    metadata = read_metadata()
    if not metadata:
        return None

    # Asumsikan metadata berisi dict: {filename: hash}
    # Cari file cache terbaru berdasarkan file hash dan nama
    latest_cache_path = None
    latest_hash = None

    for filename, filehash in metadata.items():
        cache_path = os.path.join(CACHE_DIR, f"{filehash}_{filename}")
        if os.path.exists(cache_path):
            latest_cache_path = cache_path
            latest_hash = filehash
            break  # Bisa juga ambil yang terbaru kalau kamu simpan timestamp

    if latest_cache_path is None:
        return None

    # Coba load csv dari cache, bisa kamu sesuaikan sesuai ekstensi
    file_ext = os.path.splitext(latest_cache_path)[1].lower()
    try:
        if file_ext == '.csv':
            try:
                return pd.read_csv(latest_cache_path, encoding='utf-8')
            except UnicodeDecodeError:
                return pd.read_csv(latest_cache_path, encoding='latin1')

        elif file_ext in ['.xls', '.xlsx']:
            return pd.read_excel(latest_cache_path)

        elif file_ext == '.parquet':
            return pd.read_parquet(latest_cache_path)

        elif file_ext == '.feather':
            return pd.read_feather(latest_cache_path)

        elif file_ext == '.db':
            # Untuk db butuh table_name, kalau tidak ada bisa return None
            return None

    except Exception as e:
        print(f"Error load cache dataframe: {e}")
        return None

def read_uploaded_file(file):
    filename = file.name.lower()
    
    if filename.endswith(".csv"):
        return pd.read_csv(file)

    elif filename.endswith((".xls", ".xlsx")):
        return pd.read_excel(file)

    elif filename.endswith(".parquet"):
        return pd.read_parquet(file)

    elif filename.endswith(".feather"):
        return pd.read_feather(file)

    elif filename.endswith(".db"):
        try:
            with sqlite3.connect(f"file:{file.name}?mode=ro", uri=True) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                if not tables:
                    st.warning("No tables found in the database.")
                    return pd.DataFrame()
                # Pilih tabel pertama secara default
                df = pd.read_sql_query(f"SELECT * FROM {tables[0][0]}", conn)
                return df
        except Exception as e:
            st.error(f"Failed to read .db file: {e}")
            return pd.DataFrame()
    else:
        st.error("Unsupported file format.")
        return None

def clear_cache():
    """Hapus semua cache dan metadata (gunakan di UI ketika user ingin clear cache)."""
    shutil.rmtree(CACHE_DIR, ignore_errors=True)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bersihkan dan enrich DataFrame:
    - Normalisasi nama kolom
    - Filter 'tttype' == 'site down'
    - Parsing kolom datetime
    - Konversi durasi ke numerik dan readable
    - Tambah kolom week, month, quarter dari 'createtime'
    """
    df = df.copy()

    # Normalisasi nama kolom agar uniform dan unik
    new_cols, seen = [], set()
    for col in df.columns:
        col_clean = col.strip().lower().replace(' ', '').replace('.', '')
        original = col_clean
        suffix = 1
        while col_clean in seen:
            col_clean = f"{original}_{suffix}"
            suffix += 1
        seen.add(col_clean)
        new_cols.append(col_clean)
    df.columns = new_cols

    # Filter data jika ada kolom 'tttype'
    if 'tttype' in df.columns:
        df = df[df['tttype'].astype(str).str.strip().str.lower() == 'site down']

    datetime_cols = ['createtime', 'faultfirstoccurtime', 'submittime', 'closetime', 'createat', 'closuretime']
    duration_cols = ['restoreduration', 'resolveduration', 'createduration', 'faultrecoverytime', 'faultresolvingtime']

    # Standarisasi orderid
    if 'orderid' in df.columns:
        df['orderid'] = df['orderid'].astype(str).str.replace('-', '', regex=False).str.upper()

    # Parsing kolom datetime dengan errors diabaikan
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Tambahkan kolom week, month, quarter dari createtime (kalau ada)
    if 'createtime' in df.columns:
        dt = df['createtime']
        year = dt.dt.year.astype('Int64').astype(str)
        week = dt.dt.isocalendar().week.astype('Int64').astype(str).str.zfill(2)
        month = dt.dt.month.astype('Int64').astype(str).str.zfill(2)
        quarter = dt.dt.quarter.astype('Int64').astype(str)
        df['week'] = year + '-W' + week
        df['month'] = year + '-' + month
        df['quarter'] = year + '-Q' + quarter

    # Konversi kolom durasi ke numerik
    for col in duration_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Tambahkan readable duration dalam bentuk timedelta (contoh: menit ke timedelta)
    if 'restoreduration' in df.columns:
        df['restoreduration_readable'] = pd.to_timedelta(df['restoreduration'], unit='m')

    return df

def normalize_col_name(col_name):
    """Normalisasi nama kolom: lowercase, hapus spasi dan underscore, strip ujung."""
    if not isinstance(col_name, str):
        return col_name
    return col_name.lower().replace(" ", "").replace("_", "").strip()

DROP_COLUMNS = ["weekno", "ems", "siteclass", "sitelocation", "nename", "impactedserviceornot",
                "impactscope", "description", "3gimpact", "5gimpact", "b2bimpact", "linkcongestion",
                "foowner", "alarmid"]

def drop_unwanted_columns(df, cols_to_drop=DROP_COLUMNS):
    """
    Menghapus kolom berdasarkan nama yang sudah dinormalisasi agar tidak error jika ada variasi.
    """
    normalized_to_original = {normalize_col_name(col): col for col in df.columns}
    normalized_cols_to_drop = [normalize_col_name(col) for col in cols_to_drop]
    to_drop_actual = [normalized_to_original[nc] for nc in normalized_cols_to_drop if nc in normalized_to_original]
    
    if to_drop_actual:
        return df.drop(columns=to_drop_actual)
    return df

def preview_columns_to_drop(df, cols_to_drop):
    """
    Mengembalikan list kolom yang akan dihapus (hasil cocokkan nama).
    """
    normalized_to_original = {normalize_col_name(col): col for col in df.columns}
    normalized_cols_to_drop = [normalize_col_name(col) for col in cols_to_drop]
    return [normalized_to_original[nc] for nc in normalized_cols_to_drop if nc in normalized_to_original]

# --- Encode kategorikal kolom di sla_violation ---
def encode_categorical_columns(df: pd.DataFrame, categorical_cols: list[str]) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    df_encoded = df.copy()
    encoders = {}

    for col in categorical_cols:
        if col in df_encoded.columns:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))  # Pastikan string
            encoders[col] = le
        else:
            print(f"⚠️ Kolom '{col}' tidak ada di dataframe.")

    return df_encoded, encoders

# --- Decode kategorikal kolom di sla_violation ---
def decode_categorical_columns(df: pd.DataFrame, encoders: dict[str, LabelEncoder]) -> pd.DataFrame:
    df = df.copy()
    for col, encoder in encoders.items():
        if col in df.columns:
            try:
                valid_classes = list(range(len(encoder.classes_)))
                df[col] = df[col].apply(lambda x: encoder.inverse_transform([x])[0] if x in valid_classes else x)
            except Exception:
                pass
    return df

# --- Tuning Time Series ----
def prepare_time_series(df, date_col='createtime', count_col='orderid', freq='D'):
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Pastikan yang dihitung adalah jumlah orderid per hari
    ts = df.set_index(date_col).resample(freq)[count_col].count()
    
    return ts

def aggregate_time_series(ts: pd.Series, freq_days=7):
    """
    Agregasi time series dengan frekuensi tertentu (misal 7 hari).
    """
    ts_agg = ts.resample(f'{freq_days}D').sum()
    return ts_agg

def fill_missing_values(ts: pd.Series, method='linear'):
    """
    Isi missing value dengan interpolasi linear atau forward fill.
    """
    if method == 'linear':
        ts_filled = ts.interpolate(method='linear')
    elif method == 'ffill':
        ts_filled = ts.fillna(method='ffill')
    else:
        raise ValueError("Method must be 'linear' or 'ffill'")
    return ts_filled

def create_datetime_features(ts: pd.Series):
    """
    Buat fitur tanggal: dayofweek, is_weekend, month.
    """
    df = pd.DataFrame({'target': ts})
    df['dayofweek'] = ts.index.dayofweek
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    df['month'] = ts.index.month
    return df

def create_datetime_features_df(df: pd.DataFrame):
    """
    Buat fitur tanggal: dayofweek, is_weekend, month dari index DatetimeIndex,
    untuk DataFrame dengan index datetime.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Index harus bertipe DatetimeIndex")
    
    df['dayofweek'] = df.index.dayofweek
    df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
    df['month'] = df.index.month
    return df

def create_lag_features(df: pd.DataFrame, target_col='target', lags=[1,7,14]):
    """
    Tambah fitur lag.
    """
    for lag in lags:
        df[f'lag_{lag}'] = df[target_col].shift(lag)
    return df

def create_rolling_features(df: pd.DataFrame, target_col='target', windows=[7]):
    """
    Tambah fitur rolling mean dan std.
    """
    for window in windows:
        df[f'rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()
        df[f'rolling_std_{window}'] = df[target_col].rolling(window=window).std()
    return df

# === preprocessing untuk LSTM Multivariat ====
def preprocess_for_lstm_multivariate(series, lags=[1], rolling_windows=[3]):
    ts_filled = fill_missing_values(series, method='linear')  # ✅ diperbaiki
    df = create_datetime_features(ts_filled)
    df['y'] = ts_filled.values
    df = create_lag_features(df, target_col='y', lags=lags)
    df = create_rolling_features(df, target_col='y', windows=rolling_windows)
    df = df.dropna()
    return df

def create_lstm_univariate_dataset(series, window_size=7):
    X, y = [], []
    values = series.values
    for i in range(len(values) - window_size):
        X.append(values[i:i+window_size])
        y.append(values[i+window_size])
    X, y = np.array(X), np.array(y)
    return X.reshape((X.shape[0], X.shape[1], 1)), y

def create_lstm_multivariate_dataset(df: pd.DataFrame, target_column: str, window_size=7):
    X, y = [], []
    data = df.values  # numpy array shape (n_samples, n_features)
    target_idx = df.columns.get_loc(target_column)

    for i in range(len(df) - window_size):
        X.append(data[i:i+window_size])  # slice window_size baris, semua fitur
        y.append(data[i + window_size, target_idx])  # target pada waktu berikutnya

    X = np.array(X)  # shape (samples, window_size, features)
    y = np.array(y)  # shape (samples, )

    return X, y