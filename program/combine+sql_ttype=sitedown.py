import streamlit as st
import pandas as pd
import math
import io
import zipfile
import sqlite3
import tempfile
import os
import re

st.set_page_config(page_title="Gabung File Excel/CSV", layout="centered")

st.title("📊 Gabung File Excel / CSV dengan kondisi hanya pada Kolom TT Type = Baris Site Down")
st.markdown("Unggah beberapa file `.xlsx` atau `.csv`, lalu gabungkan dan unduh hasilnya.")

# --- Sidebar options ---
st.sidebar.header("⚙️ Opsi Ekspor")
output_format = st.sidebar.radio("Format Output", ["Excel (.xlsx)", "CSV (.csv)", "SQLite Database (.db)"])

# --- Fungsi Membaca File ---
def read_uploaded_files(uploaded_files):
    dataframes = []
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            dataframes.append(df)
        except Exception as e:
            st.error(f"Gagal membaca file: {uploaded_file.name}\n{e}")
    return dataframes

# --- Fungsi Ekspor ke ZIP Excel/CSV ---
def export_to_excel_zip(df, output_format):
    max_rows = 1048576
    total_rows = df.shape[0]
    num_parts = math.ceil(total_rows / max_rows)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for i in range(num_parts):
            start = i * max_rows
            end = min(start + max_rows, total_rows)
            chunk = df.iloc[start:end]
            part_buffer = io.BytesIO()
            filename = f"gabungan_part_{i+1}"

            if output_format == "Excel (.xlsx)":
                chunk.to_excel(part_buffer, index=False, engine='openpyxl')
                zip_file.writestr(f"{filename}.xlsx", part_buffer.getvalue())
            else:
                chunk.to_csv(part_buffer, index=False)
                zip_file.writestr(f"{filename}.csv", part_buffer.getvalue())

    zip_buffer.seek(0)
    return zip_buffer

# --- Fungsi Ekspor ke SQLite ---
def export_to_sqlite(df):
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        conn = sqlite3.connect(tmpfile_path)
        df.to_sql('data_gabungan', conn, if_exists='replace', index=False)
        conn.close()

        with open(tmpfile_path, "rb") as f:
            db_data = f.read()

        os.remove(tmpfile_path)
        return db_data

    except Exception as e:
        st.error(f"Gagal mengekspor ke SQLite: {e}")
        return None

# --- Main Logic ---

uploaded_files = st.file_uploader(
    "📁 Unggah File",
    type=["xlsx", "csv"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"{len(uploaded_files)} file berhasil diunggah.")
    dataframes = read_uploaded_files(uploaded_files)

    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)

        if 'TT Type' in combined_df.columns:
            # Pola dasar yang kita cari
            positive_pattern = r'\bsite[\s\-_]?down\b'

            # Pola untuk baris negatif yang ingin kita buang
            negative_pattern = r'\b(non|not)[\s\-_]?site[\s\-_]?down\b'

            # Cek yang mengandung 'site down' (positif)
            positive_mask = combined_df['TT Type'].astype(str).str.contains(
                positive_pattern, flags=re.IGNORECASE, na=False, regex=True
            )

            # Cek dan buang yang mengandung frasa negatif
            negative_mask = combined_df['TT Type'].astype(str).str.contains(
                negative_pattern, flags=re.IGNORECASE, na=False, regex=True
            )

            # Hanya ambil baris yang cocok positif tapi tidak cocok negatif
            filtered_df = combined_df[positive_mask & ~negative_mask]

            # ✅ Tampilkan hasil filter
            st.success(f"✅ Filter selesai! Ditemukan {len(filtered_df)} baris dengan 'TT Type' mengandung variasi 'Site Down' (tanpa 'Non/Not').")
            # st.write(f"✅ Preview Hasil Filter (TT Type = Site Down): {len(filtered_df)} baris")
            # st.write(filtered_df.head(20))  # Preview 20 baris pertama

            # Gunakan hasil filter untuk ekspor
            combined_df = filtered_df
        else:
            st.warning("⚠️ Kolom 'TT Type' tidak ditemukan di salah satu atau semua file. Data tidak difilter.")

        # --- Ekspor data hasil filter ---
        if output_format == "Excel (.xlsx)":
            if len(combined_df) <= 1048576:
                output_buffer = io.BytesIO()
                combined_df.to_excel(output_buffer, index=False, engine="openpyxl")
                output_buffer.seek(0)

                st.download_button(
                    label="⬇️ Unduh Hasil Gabungan (.xlsx)",
                    data=output_buffer,
                    file_name="hasil_gabungan.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                zip_buffer = export_to_excel_zip(combined_df, output_format)
                st.download_button(
                    label="⬇️ Unduh Hasil Gabungan (ZIP - Excel)",
                    data=zip_buffer,
                    file_name="hasil_gabungan.zip",
                    mime="application/zip"
                )

        elif output_format == "CSV (.csv)":
            output_buffer = io.StringIO()
            combined_df.to_csv(output_buffer, index=False)
            output_buffer.seek(0)

            st.download_button(
                label="⬇️ Unduh Hasil Gabungan (.csv)",
                data=output_buffer,
                file_name="hasil_gabungan.csv",
                mime="text/csv"
            )

        elif output_format == "SQLite Database (.db)":
            db_data = export_to_sqlite(combined_df)
            if db_data:
                st.download_button(
                    label="⬇️ Unduh File SQLite Database (.db)",
                    data=db_data,
                    file_name="hasil_gabungan.db",
                    mime="application/x-sqlite3"
                )