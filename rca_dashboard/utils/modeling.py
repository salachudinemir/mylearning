import streamlit as st
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def show_model_results(filtered_df):
    df_enc = filtered_df.copy()

    # Cek duplikat kolom (kalau ada, tambahkan suffix)
    if df_enc.columns.duplicated().any():
        st.warning("Ada kolom duplikat, akan diubah namanya.")
        df_enc = df_enc.loc[:,~df_enc.columns.duplicated()]  # Drop kolom duplikat langsung

    # Drop kolom datetime jika ada
    datetime_cols = df_enc.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
    if datetime_cols:
        df_enc = df_enc.drop(columns=datetime_cols)

    # Encode semua kolom object atau kategorikal yang tersisa
    le_dict = {}
    for col in df_enc.columns:
        if pd.api.types.is_object_dtype(df_enc[col]) or pd.api.types.is_categorical_dtype(df_enc[col]):
            le = LabelEncoder()
            df_enc[col] = le.fit_transform(df_enc[col].astype(str))
            le_dict[col] = le

    # Tentukan fitur dan target
    drop_cols = ['rca', 'bulan_label'] if 'bulan_label' in df_enc.columns else ['rca']
    X = df_enc.drop(columns=drop_cols, errors='ignore')
    y = df_enc['rca']

    # Cek lagi kolom bertipe object di fitur
    if X.select_dtypes(include=['object']).shape[1] > 0:
        st.error("Masih ada kolom bertipe object di fitur, harap encode semua kolom tersebut terlebih dahulu!")
        st.write(X.select_dtypes(include=['object']).columns.tolist())
        return None, None

    if len(df_enc) < 5:
        st.warning("⚠️ Data terlalu sedikit untuk pelatihan model.")
        return None, None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    st.text("📄 Classification Report:")
    report = classification_report(y_test, y_pred)
    st.text(report)

    cm = confusion_matrix(y_test, y_pred)
    labels = le_dict['rca'].classes_ if 'rca' in le_dict else sorted(filtered_df['rca'].unique())

    fig, ax = plt.subplots(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    ax.set_title('Confusion Matrix')
    st.pyplot(fig)

    return y_test, y_pred
