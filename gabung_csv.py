# Simpan sebagai: gabung_csv_app.py
# Jalankan dengan: streamlit run gabung_csv_app.py

import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📁 Gabungkan Beberapa File CSV")

# Upload beberapa file CSV
uploaded_files = st.file_uploader(
    "Pilih satu atau beberapa file CSV",
    type=["csv"],
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            df['Sumber_File'] = file.name  # Tambah kolom nama file
            all_data.append(df)
            st.success(f"✅ Berhasil memuat: {file.name}")
        except Exception as e:
            st.error(f"❌ Gagal membaca {file.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        st.subheader("🧾 Preview Data Gabungan")
        st.dataframe(combined_df.head())

        # Simpan ke Excel
        excel_buffer = BytesIO()
        combined_df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        st.download_button(
            label="💾 Unduh sebagai Excel",
            data=excel_buffer,
            file_name="data_gabungan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Simpan ke CSV
        csv_buffer = BytesIO()
        combined_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        st.download_button(
            label="💾 Unduh sebagai CSV",
            data=csv_buffer,
            file_name="data_gabungan.csv",
            mime="text/csv"
        )
else:
    st.info("⬆️ Silakan upload satu atau beberapa file CSV.")
