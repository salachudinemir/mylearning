# simpan file ini sebagai gabung_excel_app.py lalu jalankan: streamlit run gabung_excel_app.py

import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 Gabungkan Beberapa File Excel")

# Upload file
uploaded_files = st.file_uploader(
    "Pilih satu atau beberapa file Excel (.xlsx atau .xls)",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
            df['Sumber_File'] = file.name  # Tambah kolom sumber file
            all_data.append(df)
            st.success(f"✅ Berhasil memuat: {file.name}")
        except Exception as e:
            st.error(f"❌ Gagal membaca {file.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        st.subheader("📋 Preview Data Gabungan")
        st.dataframe(combined_df.head())

        # Simpan ke Excel dan tawarkan unduhan
        output = BytesIO()
        combined_df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="💾 Unduh Hasil Gabungan sebagai Excel",
            data=output,
            file_name="data_gabungan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("⬆️ Unggah file Excel terlebih dahulu untuk mulai.")
