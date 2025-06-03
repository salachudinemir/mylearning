import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 Gabungkan dan Rapihkan Beberapa File Excel / CSV by Salachudin Emir")

uploaded_files = st.file_uploader(
    "Pilih satu atau beberapa file Excel (.xlsx, .xls) atau CSV (.csv)",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

def clean_dataframe(df):
    df.columns = df.columns.str.strip()
    for col in ['dt_id', 'createfaultfirstoccurtime', 'faultrecoverytime']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    if 'mttr' in df.columns:
        df['mttr'] = (
            df['mttr']
            .astype(str)
            .str.replace(',', '.', regex=False)
        )
        df['mttr'] = pd.to_numeric(df['mttr'], errors='coerce')
    return df

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                # Coba beberapa encoding
                try:
                    df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file, sep=None, engine='python', encoding='latin1')
            else:
                df = pd.read_excel(file)

            df = clean_dataframe(df)
            df['Sumber_File'] = file.name
            all_data.append(df)
            st.success(f"✅ Berhasil memuat: {file.name}")

        except Exception as e:
            st.error(f"❌ Gagal membaca {file.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        st.subheader("📋 Preview Data Gabungan dan Rapih")
        st.dataframe(combined_df.head(20))

        output_excel = BytesIO()
        combined_df.to_excel(output_excel, index=False)
        output_excel.seek(0)

        output_csv = BytesIO()
        combined_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        output_csv.seek(0)

        st.download_button(
            label="💾 Unduh Gabungan sebagai Excel (.xlsx)",
            data=output_excel,
            file_name="data_gabungan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="💾 Unduh Gabungan sebagai CSV (.csv)",
            data=output_csv,
            file_name="data_gabungan.csv",
            mime="text/csv"
        )
else:
    st.info("⬆️ Unggah file Excel atau CSV terlebih dahulu untuk mulai.")
