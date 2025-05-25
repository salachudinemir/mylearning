import streamlit as st
import pandas as pd
from io import BytesIO, StringIO

st.title("📊 Gabungkan dan Rapihkan Beberapa File Excel / CSV")

uploaded_files = st.file_uploader(
    "Pilih satu atau beberapa file Excel (.xlsx, .xls) atau CSV (.csv)",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

def clean_dataframe(df):
    # Contoh rapihkan nama kolom (strip spasi)
    df.columns = df.columns.str.strip()
    # Contoh parsing tanggal jika ada kolom dt_id dan createfaultfirstoccurtime
    for col in ['dt_id', 'createfaultfirstoccurtime', 'faultrecoverytime']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    # Kamu bisa tambahkan step parsing lain di sini
    return df

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
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

        output = BytesIO()
        combined_df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="💾 Unduh Hasil Gabungan sebagai Excel",
            data=output,
            file_name="data_gabungan_csv.csv",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("⬆️ Unggah file Excel atau CSV terlebih dahulu untuk mulai.")