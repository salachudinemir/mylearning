import streamlit as st
import pandas as pd
from utils.preprocessing import load_and_clean_data
from utils.visualization import show_visualizations
from utils.modeling import show_model_results
from utils.exporter import generate_excel_output

st.set_page_config(page_title="RCA Dashboard", layout="wide")
st.title("📊 Dashboard Root Cause Analysis (RCA) by Salachudin Emir")

uploaded_file = st.file_uploader("Unggah file data (CSV / Excel)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    try:
        # Load & bersihkan data awal
        df, filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot = load_and_clean_data(uploaded_file)
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
        st.stop()

    # Pastikan kolom 'bulan_label' ada dan ubah ke datetime
    if 'bulan_label' in filtered_df.columns:
        filtered_df['bulan_label_dt'] = pd.to_datetime(filtered_df['bulan_label'], format='%b %Y', errors='coerce')
        # Ambil tahun dan bulan (nama bulan)
        filtered_df['tahun'] = filtered_df['bulan_label_dt'].dt.year.astype('Int64')
        filtered_df['bulan'] = filtered_df['bulan_label_dt'].dt.strftime('%b')
    else:
        st.warning("Kolom 'bulan_label' tidak ditemukan di data.")
        st.stop()

    # # Filter tahun dulu
    # available_tahun = sorted(filtered_df['tahun'].dropna().unique())
    # selected_tahun = st.multiselect(
    #     "Filter berdasarkan Tahun:",
    #     options=available_tahun,
    #     default=available_tahun
    # )

    # filtered_df = filtered_df[filtered_df['tahun'].isin(selected_tahun)]

    # if filtered_df.empty:
    #     st.warning("⚠️ Tidak ada data setelah filter Tahun diterapkan.")
    #     st.stop()

    # # Filter bulan berdasar pilihan tahun
    # available_bulan = sorted(filtered_df['bulan'].dropna().unique())
    # selected_bulan = st.multiselect(
    #     "Filter berdasarkan Bulan:",
    #     options=available_bulan,
    #     default=available_bulan
    # )

    # filtered_df = filtered_df[filtered_df['bulan'].isin(selected_bulan)]

    # if filtered_df.empty:
    #     st.warning("⚠️ Tidak ada data setelah filter Bulan diterapkan.")
    #     st.stop()

    # Pastikan ada kolom datetime dari bulan_label
    filtered_df['bulan_label_dt'] = pd.to_datetime(filtered_df['bulan_label'], format='%b %Y', errors='coerce')

    # Buat dataframe unik bulan_label dengan kolom datetime
    bulan_label_df = filtered_df[['bulan_label', 'bulan_label_dt']].drop_duplicates()

    # Urutkan dari terlama ke terbaru berdasarkan datetime
    bulan_label_df = bulan_label_df.sort_values('bulan_label_dt')

    # Ambil list bulan_label yang sudah terurut
    available_bulan_label = bulan_label_df['bulan_label'].tolist()

    # Checkbox untuk Select All
    select_all_bulan = st.checkbox("Pilih Semua Bulan & Tahun", value=True)

    if select_all_bulan:
        selected_bulan_label = st.multiselect(
            "Filter berdasarkan Bulan & Tahun (contoh: Jan 2024):",
            options=available_bulan_label,
            default=available_bulan_label  # semua otomatis terpilih
        )
    else:
        selected_bulan_label = st.multiselect(
            "Filter berdasarkan Bulan & Tahun (contoh: Jan 2024):",
            options=available_bulan_label,
            default=[]  # tidak ada yang dipilih defaultnya
        )

    filtered_df = filtered_df[filtered_df['bulan_label'].isin(selected_bulan_label)]

    if filtered_df.empty:
        st.warning("⚠️ Tidak ada data setelah filter Bulan & Tahun diterapkan.")
        st.stop()

    # Filter Severity
    if 'severity' in filtered_df.columns:
        available_severities = sorted(filtered_df['severity'].dropna().unique())
        selected_severity = st.multiselect(
            "Filter berdasarkan Severity:",
            options=available_severities,
            default=available_severities
        )
        filtered_df = filtered_df[filtered_df['severity'].isin(selected_severity)]

        if filtered_df.empty:
            st.warning("⚠️ Tidak ada data setelah filter severity diterapkan.")
            st.stop()
    else:
        st.warning("Kolom 'severity' tidak ditemukan di data.")
        st.stop()

    # Filter RCA
    if 'rca' in filtered_df.columns:
        available_rca = sorted(filtered_df['rca'].dropna().unique())
        selected_rca = st.multiselect(
            "Filter berdasarkan RCA:",
            options=available_rca,
            default=available_rca
        )
        filtered_df = filtered_df[filtered_df['rca'].isin(selected_rca)]

        if filtered_df.empty:
            st.warning("⚠️ Tidak ada data setelah filter RCA diterapkan.")
            st.stop()
    else:
        st.warning("Kolom 'rca' tidak ditemukan di data.")
        st.stop()

    # Tambahkan kolom total_count jika belum ada
    if 'total_count' not in filtered_df.columns:
        filtered_df['total_count'] = 1

    # Buat kolom quarter
    filtered_df['quarter'] = filtered_df['bulan_label_dt'].dt.to_period('Q').dt.to_timestamp()

    # Hitung ulang agregasi berdasarkan data yang sudah difilter
    trend_bulanan = filtered_df.groupby(['bulan_label', 'rca']).size().reset_index(name='count')
    avg_mttr = filtered_df.groupby('rca')['mttr'].mean()
    pivot = filtered_df.pivot_table(index='rca', columns='severity', values='total_count', aggfunc='sum', fill_value=0)
    total_bulanan = filtered_df.groupby(['quarter', 'bulan_label']).agg({'total_count': 'sum'}).reset_index()

    # Visualisasi
    show_visualizations(filtered_df, trend_bulanan, avg_mttr, pivot, total_bulanan)

    # Modeling
    y_test, y_pred = show_model_results(filtered_df)

    # Export Excel
    if y_test is not None and y_pred is not None:
        excel_output = generate_excel_output(
            filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot, y_test, y_pred
        )
    else:
        excel_output = generate_excel_output(
            filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot, None, None
        )

    st.download_button(
        label="💾 Unduh Semua Output (Excel)",
        data=excel_output,
        file_name="output_analisis_rca_lengkap.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan unggah file data terlebih dahulu.")
