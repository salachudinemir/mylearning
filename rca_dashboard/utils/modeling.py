import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
import matplotlib.pyplot as plt
import seaborn as sns


def encode_categorical_columns(df):
    """Encode semua kolom kategorikal dengan LabelEncoder dan kembalikan dict encoder."""
    le_dict = {}
    df_enc = df.copy()
    for col in df_enc.columns:
        if df_enc[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df_enc[col]):
            le = LabelEncoder()
            df_enc[col] = le.fit_transform(df_enc[col].astype(str))
            le_dict[col] = le
    return df_enc, le_dict


def validate_data_for_training(X, y):
    """Validasi data sebelum training."""
    if len(X) < 10:
        st.warning("⚠️ Data terlalu sedikit untuk pelatihan model yang baik.")
        return False
    class_counts = y.value_counts()
    if len(class_counts) < 2:
        st.warning("⚠️ Data hanya memiliki satu kelas RCA.")
        return False
    if (class_counts < 2).any():
        st.warning("❗ Beberapa kelas RCA hanya memiliki 1 data. Tidak cukup untuk stratifikasi.")
        st.write(class_counts[class_counts < 2])
        return False
    return True


def plot_confusion_matrix(y_test, y_pred, labels):
    """Tampilkan confusion matrix dengan heatmap."""
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='YlGnBu', xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    ax.set_title('Confusion Matrix - Random Forest')
    st.pyplot(fig)


def show_model_results(filtered_df):
    if 'rca' not in filtered_df.columns:
        st.error("Kolom 'rca' tidak ditemukan.")
        return None, None

    df_enc = filtered_df.dropna(subset=['rca']).copy()

    # Drop kolom datetime jika ada
    datetime_cols = df_enc.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
    if datetime_cols:
        df_enc.drop(columns=datetime_cols, inplace=True)

    # Encode kolom kategorikal
    df_enc, le_dict = encode_categorical_columns(df_enc)

    # Siapkan fitur dan target
    X = df_enc.drop(columns=['rca', 'bulan_label'], errors='ignore')
    y = df_enc['rca']

    if not validate_data_for_training(X, y):
        return None, None

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    except Exception as e:
        st.error(f"Gagal split data: {e}")
        return None, None

    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    st.subheader("📄 Classification Report")
    st.text(classification_report(y_test, y_pred))

    # Ambil label asli jika ada encoder 'rca', jika tidak ambil langsung
    labels = le_dict['rca'].classes_ if 'rca' in le_dict else sorted(filtered_df['rca'].unique())
    plot_confusion_matrix(y_test, y_pred, labels)

    # Hitung metrik tambahan
    acc = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    metrics_df = pd.DataFrame({
        'Metrik': ['Accuracy', 'Precision (Weighted)', 'Recall (Weighted)', 'F1-Score (Weighted)'],
        'Nilai': [acc, precision, recall, f1]
    })
    metrics_df['Nilai'] = metrics_df['Nilai'].apply(lambda x: f"{x:.2%}")

    st.subheader("📊 Ringkasan Metrik Model")
    st.table(metrics_df)

    return y_test, y_pred
