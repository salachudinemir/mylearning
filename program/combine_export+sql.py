import streamlit as st
import pandas as pd
import math
import io
import zipfile
import sqlite3
import tempfile
import os

st.set_page_config(page_title="Gabung File Excel/CSV", layout="centered")

st.title("📊 Gabung File Excel / CSV")
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
# def export_to_sqlite(df):
#     try:
#         mem_conn = sqlite3.connect(":memory:")
#         df.to_sql('data_gabungan', mem_conn, if_exists='replace', index=False)

#         with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmpfile:
#             tmpfile_path = tmpfile.name

#         disk_conn = sqlite3.connect(tmpfile_path)
#         query = "".join(mem_conn.iterdump())
#         disk_conn.executescript(query)
#         disk_conn.commit()

#         disk_conn.close()
#         mem_conn.close()

#         with open(tmpfile_path, "rb") as f:
#             db_data = f.read()

#         os.remove(tmpfile_path)
#         return db_data

#     except Exception as e:
#         st.error(f"Gagal mengekspor ke SQLite: {e}")
#         return None

#  ---  Fungsi ini untuk langsung menulis ke file SQLite tanpa melalui memory-to-disk dump, untuk menghindari batas query string ---
def export_to_sqlite(df):
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        # Langsung simpan ke SQLite di disk (bukan di memori)
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
        st.success(f"✅ Gabungan selesai! Total: {len(combined_df)} baris, {combined_df.shape[1]} kolom.")

        if output_format in ["Excel (.xlsx)", "CSV (.csv)"]:
            zip_buffer = export_to_excel_zip(combined_df, output_format)

            st.download_button(
                label="⬇️ Unduh Hasil Gabungan (ZIP)",
                data=zip_buffer,
                file_name="hasil_gabungan.zip",
                mime="application/zip"
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
