# tab/tab4_slaviolation.py

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from utils.preprocessing import (
    load_and_cache_data,
    clean_data,
    clear_cache,
    read_uploaded_file,
    encode_categorical_columns,
    decode_categorical_columns
)

uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx", "xls", "db", "parquet", "feather"])
if uploaded_file is not None:
    df = read_uploaded_file(uploaded_file)

    categorical_columns = ['severity', 'mccluster', 'siteid', 'rootcause', 'subcause',
                           'circle', 'siteregion', 'slastatus']

    df_encoded, label_encoders = encode_categorical_columns(df, categorical_columns)

def plot_sla_violation_pie(df):
    sla_counts = df['slastatus'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(sla_counts, labels=sla_counts.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    return fig

def sla_violation_table(df):
    columns = ['orderid', 'slastatus', 'severity', 'circle', 'siteregion', 'mccluster', 'siteid', 'rootcause', 'subcause', 'alarmname', '2gimpact', '4gimpact', 'restoreduration']
    return df[[col for col in columns if col in df.columns]]

def render_sla_visualization(df_filtered, df_filtered_dropped):
    st.subheader("📊 SLA Violation Pie Chart")
    if not df_filtered.empty and 'slastatus' in df_filtered.columns:
        fig = plot_sla_violation_pie(df_filtered)
        st.pyplot(fig)
    else:
        st.info("Data kosong atau kolom 'slastatus' tidak ditemukan.")

    st.subheader("🧾 Tabel SLA Violation")
    if not df_filtered_dropped.empty:
        st.dataframe(sla_violation_table(df_filtered_dropped))
    else:
        st.info("Data kosong untuk tabel SLA Violation.")

def run_sla_classifier(df, feature_cols):
    df = df.dropna(subset=['slastatus'])
    df['label'] = df['slastatus'].apply(lambda x: 1 if str(x).strip().lower() == 'sla_violation' else 0)
    df[feature_cols] = df[feature_cols].fillna(0)

    le = LabelEncoder()
    for col in feature_cols:
        if df[col].dtype == 'object':
            df[col] = le.fit_transform(df[col])

    X = df[feature_cols]
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = DecisionTreeClassifier()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    return clf, X, y, y_test, y_pred

def plot_confusion_matrix(y_test, y_pred, labels):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots()
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    return fig

def plot_classification_report(y_test, y_pred, labels):
    report_dict = classification_report(y_test, y_pred, target_names=labels, output_dict=True)
    metrics = ['precision', 'recall', 'f1-score']
    data = {label: [report_dict[label][metric] for metric in metrics] for label in labels}
    df_scores = pd.DataFrame(data, index=metrics)

    fig, ax = plt.subplots()
    df_scores.plot(kind='bar', ax=ax)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Score")
    ax.set_title("Precision, Recall, F1-score per Class")
    ax.legend(title="Class")
    plt.xticks(rotation=0)
    return fig

def render_sla_classification():
    st.subheader("Klasifikasi SLA Status: sla_violation vs normal")

    df = st.session_state.get("df_clean")
    if df is None or df.empty:
        st.warning("Silakan upload dan proses data terlebih dahulu.")
        return

    if 'slastatus' not in df.columns:
        st.error("Kolom 'slastatus' tidak ditemukan.")
        return

    df = df.dropna(subset=['slastatus'])
    df['label'] = df['slastatus'].apply(lambda x: 1 if str(x).strip().lower() == 'sla_violation' else 0)

    desired_features = ['orderid', 'severity', 'circle', 'siteregion', 'mccluster', 'siteid', 'rootcause', 'subcause', 'alarmname', '2gimpact', '4gimpact', 'restoreduration']
    feature_cols = [col for col in desired_features if col in df.columns and not df[col].isnull().all()]
    if not feature_cols:
        st.error("Tidak ada fitur valid yang tersedia.")
        return

    df[feature_cols] = df[feature_cols].fillna(0)

    # Simpan encoder untuk severity
    severity_encoder = None
    label_encoders = {}

    for col in feature_cols:
        if df[col].dtype == 'object':
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
            if col == 'severity':
                severity_encoder = le

    X = df[feature_cols]
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = DecisionTreeClassifier()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    display_classification_results(y_test, y_pred)

    st.subheader("📌 Baris yang Salah Klasifikasi (Misclassified)")

    X_test_with_info = X_test.copy()
    X_test_with_info['actual'] = y_test.values
    X_test_with_info['predicted'] = y_pred

    mismatches = X_test_with_info[X_test_with_info["actual"] != X_test_with_info["predicted"]]

    if mismatches.empty:
        st.success("✅ Semua prediksi sesuai!")
    else:
        mismatch_indices = mismatches.index.intersection(df.index)
        additional_cols = [
            'orderid', 'createtime', 'mccluster', 'siteid', 'rootcause', 'subcause',
            'circle', 'siteregion', 'severity', 'slastatus',
        ]
        available_cols = [col for col in additional_cols if col in df.columns]
        # detail_df = df.loc[mismatch_indices, available_cols].copy()
        detail_df = df.loc[mismatch_indices, available_cols].copy()

        detail_df['actual'] = mismatches.loc[mismatch_indices, 'actual']
        detail_df['predicted'] = mismatches.loc[mismatch_indices, 'predicted']

        # Kembalikan kolom encoded ke bentuk string
        detail_df = decode_categorical_columns(detail_df, label_encoders)

        st.subheader("Sebelum decode:")
        st.dataframe(detail_df[['rootcause', 'subcause']].head())

        st.subheader("Setelah decode:")
        st.dataframe(detail_df[['rootcause', 'subcause']].head())

        st.dataframe(detail_df)

def display_classification_results(y_test, y_pred):
    # === Akurasi ===
    acc = accuracy_score(y_test, y_pred)
    st.metric(label="🎯 Akurasi Model", value=f"{acc:.2%}")

    # === Classification Report sebagai DataFrame ===
    st.markdown("### 📊 Classification Report")
    report_dict = classification_report(y_test, y_pred, target_names=["normal", "sla_violation"], output_dict=True)
    report_df = pd.DataFrame(report_dict).transpose()
    st.dataframe(report_df.style.format(precision=2))

    # === Confusion Matrix ===
    st.markdown("### 🔍 Confusion Matrix")
    cm = confusion_matrix(y_test, y_pred)
    labels = ["Normal", "SLA Violation"]

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    st.pyplot(fig)

def render_tab4_app(
    df_filtered,
    createmode_filter=None,
    circle_filter=None,
    severity_filter=None,
    start_date=None,
    end_date=None
):
    if df_filtered is None or df_filtered.empty:
        st.warning("Data kosong. Silakan upload dan filter data terlebih dahulu.")
        return

    # Filter baris yang memiliki nilai slastatus (untuk visualisasi)
    df_filtered_dropped = df_filtered.dropna(subset=['slastatus'])

    # Simpan ke session_state untuk digunakan oleh render_sla_classification
    st.session_state["df_clean"] = df_filtered.copy()

    # === VISUALISASI SLA ===
    render_sla_visualization(df_filtered, df_filtered_dropped)

    # === KLASIFIKASI SLA VIOLATION ===
    st.markdown("---")
    render_sla_classification()
