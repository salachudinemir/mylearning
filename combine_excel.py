import streamlit as st
import pandas as pd
from io import BytesIO

# Ubah batas upload size Streamlit (max 1GB)
st.set_option('server.maxUploadSize', 1024)

st.title("📊 Gabungkan dan Rapihkan Beberapa File Excel / CSV (Ukuran Besar Didukung)")

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
        df['mttr'] = df['mttr'].astype(str).str.replace(',', '.', regex=False)
        df['mttr'] = pd.to_numeric(df['mttr'], errors='coerce')
    return df

@st.cache_data(show_spinner=False)
def read_large_csv(file):
    # Pakai chunksize agar efisien
    chunk_list = []
    try:
        chunks = pd.read_csv(file, chunksize=100_000, encoding='utf-8')
        for chunk in chunks:
            cleaned = clean_dataframe(chunk)
            chunk_list.append(cleaned)
    except UnicodeDecodeError:
        file.seek(0)
        chunks = pd.read_csv(file, chunksize=100_000, encoding='latin1')
        for chunk in chunks:
            cleaned = clean_dataframe(chunk)
            chunk_list.append(cleaned)
    df = pd.concat(chunk_list, ignore_index=True)
    return df

@st.cache_data(show_spinner=False)
def read_large_excel(file):
    # Streamlit uploads file-like object, reset pointer
    file.seek(0)
    df = pd.read_excel(file, engine='openpyxl')  # atau 'xlrd' untuk .xls
    df = clean_dataframe(df)
    return df

if uploaded_files:
    all_data = []
    progress_bar = st.progress(0)
    total_files = len(uploaded_files)

    for idx, file in enumerate(uploaded_files):
        try:
            st.write(f"📂 Memproses file: `{file.name}` ({file.size / (1024 * 1024):.2f} MB)")
            if file.name.endswith('.csv'):
                df = read_large_csv(file)
            else:
                df = read_large_excel(file)
            df['Sumber_File'] = file.name
            all_data.append(df)
            st.success(f"✅ Selesai: {file.name}")
        except Exception as e:
            st.error(f"❌ Gagal memproses {file.name}: {e}")
        progress_bar.progress((idx + 1) / total_files)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        st.subheader("📋 Preview Data Gabungan")
        st.dataframe(combined_df.head(20))

        # Export ke Excel
        output_excel = BytesIO()
        combined_df.to_excel(output_excel, index=False, engine='openpyxl')
        output_excel.seek(0)

        # Export ke CSV
        output_csv = BytesIO()
        combined_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        output_csv.seek(0)

        st.download_button("💾 Unduh Excel (.xlsx)", data=output_excel, file_name="data_gabungan.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("💾 Unduh CSV (.csv)", data=output_csv, file_name="data_gabungan.csv", mime="text/csv")

else:
    st.info("⬆️ Silakan unggah file terlebih dahulu.")
