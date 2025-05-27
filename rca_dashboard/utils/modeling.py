import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

def show_model_results(filtered_df):
    df_enc = filtered_df.copy()

    # Validasi kolom 'rca'
    if 'rca' not in df_enc.columns:
        st.error("Kolom 'rca' tidak ditemukan.")
        return None, None

    df_enc = df_enc.dropna(subset=['rca'])

    # Hapus kolom datetime
    datetime_cols = df_enc.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
    df_enc = df_enc.drop(columns=datetime_cols)

    # Label Encoding untuk kolom kategorikal
    le_dict = {}
    for col in df_enc.columns:
        if df_enc[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df_enc[col]):
            le = LabelEncoder()
            df_enc[col] = le.fit_transform(df_enc[col].astype(str))
            le_dict[col] = le

    # Siapkan fitur dan target
    X = df_enc.drop(columns=['rca', 'bulan_label'], errors='ignore')
    y = df_enc['rca']

    # Validasi jumlah data dan kelas
    if len(X) < 10:
        st.warning("⚠️ Data terlalu sedikit untuk pelatihan model yang baik.")
        return None, None

    class_counts = y.value_counts()
    if len(class_counts) < 2:
        st.warning("⚠️ Data hanya memiliki satu kelas RCA.")
        return None, None
    if (class_counts < 2).any():
        st.warning("❗ Beberapa kelas RCA hanya memiliki 1 data. Tidak cukup untuk stratifikasi.")
        st.write(class_counts[class_counts < 2])
        return None, None

    # Split data
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    except Exception as e:
        st.error(f"Gagal split data: {e}")
        return None, None

    # Train Random Forest
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    # Report
    st.subheader("📄 Classification Report")
    st.text(classification_report(y_test, y_pred))

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    labels = le_dict['rca'].classes_ if 'rca' in le_dict else sorted(filtered_df['rca'].unique())

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='YlGnBu', xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    ax.set_title('Confusion Matrix - Random Forest')
    st.pyplot(fig)

    acc = accuracy_score(y_test, y_pred)
    st.success(f"🎯 Akurasi Model Random Forest: {acc:.2%}")

    return y_test, y_pred