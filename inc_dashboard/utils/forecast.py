import os
import re
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import joblib
from pathlib import Path
from pmdarima import auto_arima
from prophet import Prophet
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
import shutil
from sklearn.metrics import mean_squared_error
from utils.preprocessing import (
    prepare_time_series,
    aggregate_time_series,
    fill_missing_values,
    create_datetime_features,
    create_lag_features,
    create_rolling_features,
    preprocess_for_lstm_multivariate,
    create_lstm_univariate_dataset,
    create_lstm_multivariate_dataset
)


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Menyembunyikan log INFO dan WARNING dari TensorFlow
from tensorflow import keras

# --- Komponen Keras --- 
EarlyStopping = keras.callbacks.EarlyStopping
Input = keras.layers.Input
LSTM = keras.layers.LSTM
Dense = keras.layers.Dense
Dropout = keras.layers.Dropout
Sequential = keras.models.Sequential
load_model = keras.models.load_model
MeanSquaredError = keras.losses.MeanSquaredError

# Direktori cache model
MODEL_PROPHET_DIR = Path("saved_model/prophet_cache")
MODEL_ARIMA_DIR = Path("saved_model/arima_cache")
MODEL_AUTO_ARIMA_DIR = Path("saved_model/auto_arima_cache")
MODEL_LSTM_UNIVARIATE_DIR = Path("saved_model/lstm_univariate")
MODEL_LSTM_MULTIVARIATE_DIR = Path("saved_model/lstm_multivariate")

# Utility: generate model key dari filter params
def get_model_key_from_params(params: dict):
    if params is None:
        params = {}
    return f"model_{abs(hash(str(sorted(params.items()))))}"

# Utility: generate key dari data time series dan order ARIMA
def get_model_key_from_series(ts_data: pd.Series, order=None):
    key_str = str(ts_data.index.tolist())
    if order:
        key_str += str(order)
    return f"arima_{abs(hash(key_str))}"

# Main: untuk semua jenis model
def get_model_key(model_type, ts_data=None, params=None, order=None):
    if model_type == "Manual ARIMA":
        return get_model_key_from_series(ts_data, order)
    else:
        return get_model_key_from_params(params)

# --- Data Preparation ---
@st.cache_data
def prepare_weekly_series(df, date_col='createtime'):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    ts_series = df.set_index(date_col).resample('W').size()
    ts_series.name = 'ticket_count'
    return ts_series

# ===== ARIMA Manual =====
@st.cache_resource
def train_arima(ts_data: pd.Series, order=(1, 1, 1), model_key=None):
    MODEL_ARIMA_DIR.mkdir(parents=True, exist_ok=True)
    if model_key is None:
        model_key = get_model_key(ts_data, order)
    model_path = MODEL_ARIMA_DIR / f"{model_key}.pkl"

    if model_path.exists():
        return joblib.load(model_path)

    model = ARIMA(ts_data, order=order)
    model_fit = model.fit()
    joblib.dump(model_fit, model_path)
    return model_fit

@st.cache_resource
def load_arima_model(model_key):
    model_path = MODEL_ARIMA_DIR / f"{model_key}.pkl"
    return joblib.load(model_path)

def forecast_arima(model, steps):
    return model.forecast(steps=steps)

# ===== Auto ARIMA =====
@st.cache_resource
def train_auto_arima(ts_data: pd.Series, model_key=None):
    MODEL_AUTO_ARIMA_DIR.mkdir(parents=True, exist_ok=True)
    if model_key is None:
        model_key = get_model_key(ts_data)
    model_path = MODEL_AUTO_ARIMA_DIR / f"{model_key}.pkl"

    if model_path.exists():
        return joblib.load(model_path)

    model = auto_arima(
        ts_data,
        start_p=0, start_q=0,
        max_p=5, max_q=5,
        seasonal=False,
        d=None,
        stepwise=True,
        suppress_warnings=True,
        error_action='ignore',
        trace=False
    )
    joblib.dump(model, model_path)
    return model

@st.cache_resource
def load_auto_arima_model(model_key):
    model_path = MODEL_AUTO_ARIMA_DIR / f"{model_key}.pkl"
    return joblib.load(model_path)

def forecast_auto_arima(model, steps):
    return model.predict(n_periods=steps)

# ===== Prophet =====
def train_prophet(ts_data: pd.Series, model_key: str):
    df_prophet = pd.DataFrame({
        'ds': ts_data.index,
        'y': ts_data.values
    })

    model = Prophet()
    model.fit(df_prophet)

    model_path = MODEL_PROPHET_DIR / f"prophet_model_{model_key}.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return model

def load_prophet_model(model_key: str):
    model_path = MODEL_PROPHET_DIR / f"prophet_model_{model_key}.pkl"
    if model_path.exists():
        return joblib.load(model_path)
    return None

def save_or_load_prophet_model(ts_data: pd.Series, model_key: str):
    """
    Gunakan model Prophet dari cache jika tersedia, jika tidak akan dilatih dan disimpan.
    """
    model = load_prophet_model(model_key)
    if model is None:
        model = train_prophet(ts_data, model_key)
    return model

def forecast_prophet(model, steps, last_date):
    future = pd.DataFrame({
        'ds': pd.date_range(start=last_date + pd.Timedelta(days=7), periods=steps, freq='7D')
    })
    forecast = model.predict(future)
    forecast_series = pd.Series(forecast['yhat'].values, index=future['ds'])
    return forecast_series

# ===== LSTM Univariate =====
def train_lstm_univariate(ts_train: pd.Series, model_key: str, window_size=7, epochs=100, batch_size=16, verbose=1):
    ts_train = ts_train.sort_index().interpolate(method='linear')

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_train = scaler.fit_transform(ts_train.values.reshape(-1, 1))

    X_train, y_train = create_lstm_univariate_dataset(pd.Series(scaled_train.flatten()), window_size)
    split_idx = int(len(X_train) * 0.9)
    X_tr, X_val = X_train[:split_idx], X_train[split_idx:]
    y_tr, y_val = y_train[:split_idx], y_train[split_idx:]

    model = Sequential([
        LSTM(64, activation='tanh', return_sequences=True, input_shape=(window_size, 1)),
        Dropout(0.2),
        LSTM(32, activation='tanh'),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    history = model.fit(X_tr, y_tr, validation_data=(X_val, y_val),
                        epochs=epochs, batch_size=batch_size, verbose=verbose,
                        callbacks=[early_stop])

    # Save model dan scaler
    model_dir = MODEL_LSTM_UNIVARIATE_DIR / model_key
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save(model_dir / "model.h5")
    joblib.dump(scaler, model_dir / "scaler.pkl")

    return model, scaler, history

def load_lstm_univariate_model(model_key: str):
    model_dir = MODEL_LSTM_UNIVARIATE_DIR / model_key
    model_path = model_dir / "model.h5"
    scaler_path = model_dir / "scaler.pkl"

    if model_path.exists() and scaler_path.exists():
        model = load_model(model_path)
        scaler = joblib.load(scaler_path)
        return model, scaler
    return None, None

def save_or_load_lstm_univariate_model(ts_train: pd.Series, model_key: str, window_size=7):
    model, scaler = load_lstm_univariate_model(model_key)
    if model is None or scaler is None:
        model, scaler, _ = train_lstm_univariate(ts_train, model_key, window_size=window_size)
    return model, scaler

def forecast_lstm_univariate(model, scaler, ts_train: pd.Series, steps=4, window_size=7, freq='7D'):
    ts_train = ts_train.sort_index()
    scaled_train = scaler.transform(ts_train.values.reshape(-1, 1)).flatten()
    input_seq = list(scaled_train[-window_size:])
    preds_scaled = []

    for _ in range(steps):
        X = np.array(input_seq[-window_size:]).reshape((1, window_size, 1))
        yhat = model.predict(X, verbose=0)[0][0]
        preds_scaled.append(yhat)
        input_seq.append(yhat)

    preds = scaler.inverse_transform(np.array(preds_scaled).reshape(-1, 1)).flatten()

    last_date = ts_train.index[-1]
    idx = pd.date_range(start=last_date + pd.Timedelta(days=pd.Timedelta(freq).days), periods=steps, freq=freq)

    return pd.Series(preds, index=idx)

# ===== LSTM Multivariate =====
def preprocess_for_lstm_multivariate(
    df: pd.DataFrame,
    target_column: str,
    resample_freq='D',
    fill_method='linear'
) -> pd.DataFrame:
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Index DataFrame harus bertipe datetime.")

    if target_column not in df.columns:
        raise ValueError(f"Kolom target '{target_column}' tidak ditemukan di DataFrame.")

    # Urutkan, resample dan isi missing
    df = df.sort_index()
    df = df.resample(resample_freq).sum()
    df = df.interpolate(method=fill_method)

    # Tambahkan fitur waktu jika perlu (komentar jika tidak dipakai)
    df = create_datetime_features(df.copy())  # Misalnya dayofweek, month dsb
    # Bisa juga tambahkan lag/rolling jika perlu

    return df

def train_lstm_multivariate(
    ts_train: pd.DataFrame,
    target_column: str,
    model_key: str,
    window_size=7,
    epochs=100,
    batch_size=16,
    verbose=1
):
    ts_train = ts_train.sort_index().interpolate(method='linear')

    scaler = MinMaxScaler()
    scaled_values = scaler.fit_transform(ts_train)
    scaled_df = pd.DataFrame(scaled_values, index=ts_train.index, columns=ts_train.columns)

    X, y = create_lstm_multivariate_dataset(scaled_df, target_column, window_size)

    split_idx = int(len(X) * 0.9)
    X_tr, X_val = X[:split_idx], X[split_idx:]
    y_tr, y_val = y[:split_idx], y[split_idx:]

    model = Sequential([
        LSTM(64, activation='tanh', return_sequences=True, input_shape=(window_size, X.shape[2])),
        Dropout(0.2),
        LSTM(32, activation='tanh'),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')

    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

    history = model.fit(
        X_tr, y_tr,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        verbose=verbose,
        callbacks=[early_stop]
    )
    X, y = create_lstm_multivariate_dataset(scaled_df, target_column, window_size)
    print('X shape:', X.shape)  # harus (samples, window_size, n_features)
    print('y shape:', y.shape)  # harus (samples,)

    # Simpan model dan scaler ke folder cache
    model_dir = MODEL_LSTM_MULTIVARIATE_DIR / model_key
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save(model_dir / "model.h5")
    joblib.dump(scaler, model_dir / "scaler.pkl")

    return model, scaler, history

def load_lstm_multivariate_model(model_key: str):
    model_dir = MODEL_LSTM_MULTIVARIATE_DIR / model_key
    model_path = model_dir / "model.h5"
    scaler_path = model_dir / "scaler.pkl"

    if model_path.exists() and scaler_path.exists():
        model = load_model(model_path)
        scaler = joblib.load(scaler_path)
        return model, scaler
    return None, None

def save_or_load_lstm_multivariate_model(ts_train: pd.DataFrame, target_column: str, model_key: str, window_size=7):
    model, scaler = load_lstm_multivariate_model(model_key)
    if model is None or scaler is None:
        model, scaler, _ = train_lstm_multivariate(ts_train, target_column, model_key, window_size=window_size)
    return model, scaler

def forecast_lstm_multivariate(
    model,
    scaler,
    ts_train: pd.DataFrame,
    target_column: str,
    steps=4,
    window_size=7,
    freq='7D'
):
    ts_train = ts_train.sort_index()
    scaled_values = scaler.transform(ts_train)
    scaled_df = pd.DataFrame(scaled_values, index=ts_train.index, columns=ts_train.columns)

    input_seq = scaled_df[-window_size:].values
    preds_scaled = []

    target_idx = ts_train.columns.get_loc(target_column)

    for _ in range(steps):
        X = np.expand_dims(input_seq, axis=0)  # (1, window_size, n_features)
        yhat = model.predict(X, verbose=0)[0][0]
        preds_scaled.append(yhat)

        last_row = input_seq[-1].copy()
        last_row[target_idx] = yhat
        input_seq = np.vstack([input_seq[1:], last_row])

    # Parsing freq string
    match = re.match(r'(\d+)([A-Za-z]+)', freq)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
    else:
        num = 1
        unit = freq

    forecast_index = pd.date_range(
        start=ts_train.index[-1] + pd.Timedelta(num, unit=unit),
        periods=steps,
        freq=freq
    )

    dummy = np.tile(input_seq[-1], (steps, 1))
    dummy[:, target_idx] = preds_scaled
    preds_rescaled = scaler.inverse_transform(dummy)[:, target_idx]

    return pd.Series(preds_rescaled, index=forecast_index)
