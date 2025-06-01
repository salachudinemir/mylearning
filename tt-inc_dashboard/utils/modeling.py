import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json


MODEL_PATH = 'saved_model/model.pkl'
FEATURES_PATH = 'saved_model/model_features.json'


def train_model(df: pd.DataFrame, force_retrain=False, return_mae=False):
    if not force_retrain and os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        if return_mae:
            return model, None
        return model

    target = 'restoreduration'
    features = [
        'severity',
        'circle',
        'siteregion',
        'rootcause',
        'subcause',
        'subcause2',
        'mccluster',
        'orderid'
    ]

    missing_cols = [col for col in features + [target] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom berikut tidak ditemukan dalam data: {missing_cols}")

    df = df.dropna(subset=[target])
    X = df[features]
    y = df[target]

    cat_features = X.select_dtypes(include='object').columns.tolist()
    num_features = X.select_dtypes(exclude='object').columns.tolist()

    preprocessor = ColumnTransformer([
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OneHotEncoder(handle_unknown='ignore'))
        ]), cat_features),
        ('num', SimpleImputer(strategy='median'), num_features)
    ])

    model = Pipeline([
        ('preprocess', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    # Simpan fitur ke file json
    with open(FEATURES_PATH, 'w') as f:
        json.dump(features, f)

    if return_mae:
        return model, mae
    else:
        return model


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model tidak ditemukan di path: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    return model


def load_model_features():
    if not os.path.exists(FEATURES_PATH):
        return None
    with open(FEATURES_PATH, 'r') as f:
        features = json.load(f)
    return features


def predict_duration(model, input_df: pd.DataFrame):
    preds = model.predict(input_df)
    return preds


def user_input_features(df_filtered_dropped):
    filtered_df = df_filtered_dropped.copy()

    # Fungsi ini hanya mengembalikan list pilihan untuk UI,
    # tanpa UI Streamlit di sini supaya modul tetap murni.

    options = {}

    for col in ['orderid', 'severity', 'circle', 'siteregion', 'rootcause', 'subcause', 'subcause2', 'mccluster']:
        options[col] = filtered_df[col].dropna().unique().tolist()
        # Jika perlu, opsi bisa difilter satu per satu di UI app

    return options

def evaluate_prediction(df, model):
    if 'serviceinterruptiontime' not in df.columns:
        raise ValueError("Kolom 'serviceinterruptiontime' tidak ditemukan untuk evaluasi.")

    def convert_time_to_minutes(time_str):
        try:
            h, m = map(int, str(time_str).split(':'))
            return h * 60 + m
        except:
            return None

    df = df.copy()
    df['actual_minutes'] = df['serviceinterruptiontime'].apply(convert_time_to_minutes)

    if df['actual_minutes'].isnull().all():
        raise ValueError("Semua nilai 'serviceinterruptiontime' tidak dapat dikonversi ke menit.")

    feature_cols = load_model_features()
    missing_cols = set(feature_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Kolom fitur berikut tidak ditemukan di data evaluasi: {missing_cols}")

    X = df[feature_cols]

    if X.isnull().any().any():
        raise ValueError("Data fitur evaluasi mengandung NaN, mohon bersihkan atau isi terlebih dahulu.")

    y_true = df['actual_minutes']
    y_pred = model.predict(X)

    df_result = df.copy()
    df_result['Predicted_Restore_Duration'] = y_pred
    df_result['Actual_Service_Interruption'] = y_true

    metrics = {
        'MAE': mean_absolute_error(y_true, y_pred),
        'RMSE': mean_squared_error(y_true, y_pred, squared=False),
        'R2': r2_score(y_true, y_pred)
    }

    return df_result[['Predicted_Restore_Duration', 'Actual_Service_Interruption']], metrics
