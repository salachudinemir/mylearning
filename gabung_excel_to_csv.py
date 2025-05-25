import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Gabungkan File Excel/CSV", layout="wide")
st.title("📊 Gabungkan dan Rapihkan Beberapa File Excel / CSV")

uploaded_files = st.file_uploader(
    "📂 Pilih satu atau beberapa file Excel (.xlsx, .xls) atau CSV (.csv)",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

def clean_dataframe(df):
    # Rapihkan nama kolom
    df.columns = df.columns.str.strip()
    
    # Parsing kolom tanggal jika ada
    for col in ['dt_id', 'createfaultfirstoccurtime', 'faultrecoverytime']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

if uploaded_files:
    all_data = []
    
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8', errors='replace')
            else:
                df = pd.read_excel(file)
            
            df = clean_dataframe(df)
            df['Sumber_File'] = file.name  # Lacak asal file
            all_data.append(df)
            st.success(f"✅ Berhasil memuat: {file.name}")
        
        except Exception as e:
            st.error(f"❌ Gagal membaca {file.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        st.subheader("📋 Preview Data Gabungan")
        st.dataframe(combined_df.head(20), use_container_width=True)

        # Simpan sebagai CSV
        output = StringIO()
        combined_df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        st.download_button(
            label="💾 Unduh Hasil Gabungan sebagai CSV",
            data=output,
            file_name="data_gabungan.csv",
            mime="text/csv"
        )
else:
    st.info("⬆️ Unggah file Excel atau CSV terlebih dahulu untuk mulai.")
