import streamlit as st
import pandas as pd
from utils.preprocessing import load_and_clean_data, fill_sub_root_cause
from utils.modeling import show_model_results
from utils.exporter import generate_excel_output
from visualization.trend import show_trend
from visualization.distribution import show_distribution
from visualization.mttr import show_mttr_per_rca, show_mttr_per_severity, show_mttr_per_circle
from visualization.heatmap import show_heatmap_rca_vs_severity, show_heatmap_circle_vs_severity
from visualization.sitename import show_sitename
from visualization.qoq import show_qoq
from visualization.yoy import show_yoy

st.set_page_config(page_title="RCA Dashboard", layout="wide")
st.title("📊 Dashboard Root Cause Analysis (RCA) by Salachudin Emir")

# Fungsi filter multiselect dengan opsi select all
def multi_select_filter(label, options, default_all=True):
    select_all = st.checkbox(f"Pilih Semua {label}", value=default_all)
    if select_all:
        selected = st.multiselect(f"Filter berdasarkan {label}:", options=options, default=options)
    else:
        selected = st.multiselect(f"Filter berdasarkan {label}:", options=options, default=[])
    return selected

# Fungsi filter data berdasar kolom
def filter_by_column(df, col_name, label):
    if col_name in df.columns:
        options = sorted(df[col_name].dropna().unique())
        selected = multi_select_filter(label, options)
        df_filtered = df[df[col_name].isin(selected)]
        st.write(f"✅ Setelah filter {label}: {len(df_filtered)} baris")
        if df_filtered.empty:
            st.warning(f"⚠️ Tidak ada data setelah filter {label}. Silakan sesuaikan pilihan filter.")
        return df_filtered
    else:
        st.warning(f"⚠️ Kolom '{col_name}' tidak ditemukan di data.")
        return df

uploaded_file = st.file_uploader("Unggah file data (CSV / Excel)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    try:
        # Load dan bersihkan data
        df, filtered_df, trend_bulanan, total_bulanan, avg_mttr_dummy, pivot = load_and_clean_data(
            uploaded_file,
            keep_all_columns=True,
            debug_log=True
        )

        # Tampilkan preview data awal sebelum filter apapun
        st.subheader("📋 Preview Data Awal (Head 10 Baris)")
        st.dataframe(filtered_df.head(10))

        # Cek tanggal tidak valid
        invalid_date_rows = df[df['createfaultfirstoccurtime'].isna()]
        if not invalid_date_rows.empty:
            st.warning(f"⚠️ Ditemukan {len(invalid_date_rows)} baris dengan tanggal tidak valid (`createfaultfirstoccurtime`).")
            with st.expander("Lihat baris yang bermasalah"):
                st.dataframe(invalid_date_rows)

        st.write(f"✅ Data awal dimuat: {len(df)} baris")

        # Isi sub_root_cause yang kosong
        filtered_df = fill_sub_root_cause(filtered_df)
        st.write(f"✅ Setelah isi sub_root_cause: {len(filtered_df)} baris")

        # Pastikan kolom 'bulan_label' ada
        if 'bulan_label' not in filtered_df.columns:
            st.warning("⚠️ Kolom 'bulan_label' tidak ditemukan di data. Proses berhenti.")
            st.stop()

        # Parsing 'bulan_label' ke datetime dan ekstrak tahun, bulan
        filtered_df['bulan_label_dt'] = pd.to_datetime(filtered_df['bulan_label'], format='%b %Y', errors='coerce')
        filtered_df['tahun'] = filtered_df['bulan_label_dt'].dt.year.astype('Int64')
        filtered_df['bulan'] = filtered_df['bulan_label_dt'].dt.strftime('%b')

        st.write("🗓️ Sampel parsing bulan_label:")
        st.dataframe(filtered_df[['bulan_label', 'bulan_label_dt', 'tahun', 'bulan']].head())

        # Filter Tahun
        available_tahun = sorted(filtered_df['tahun'].dropna().unique())
        select_all_tahun = st.checkbox("Pilih Semua Tahun", value=True)
        selected_tahun = st.multiselect(
            "Filter berdasarkan Tahun:",
            options=available_tahun,
            default=available_tahun if select_all_tahun else []
        )
        filtered_df = filtered_df[filtered_df['tahun'].isin(selected_tahun)]
        st.write(f"✅ Setelah filter Tahun: {len(filtered_df)} baris")

        # Filter Bulan & Tahun
        bulan_label_df = filtered_df[['bulan_label', 'bulan_label_dt']].drop_duplicates().sort_values('bulan_label_dt')
        available_bulan_label = bulan_label_df['bulan_label'].tolist()

        select_all_bulan = st.checkbox("Pilih Semua Bulan", value=True)
        selected_bulan_label = st.multiselect(
            "Filter berdasarkan Bulan & Tahun:",
            options=available_bulan_label,
            default=available_bulan_label if select_all_bulan else []
        )

        # Urutkan pilihan bulan sesuai tanggal asli
        selected_bulan_label = [bl for bl in bulan_label_df['bulan_label'] if bl in selected_bulan_label]
        filtered_df = filtered_df[filtered_df['bulan_label'].isin(selected_bulan_label)]
        st.write(f"✅ Setelah filter Bulan & Tahun: {len(filtered_df)} baris")

        # Filter kolom RCA, circle, severity
        for col_name, label in [('circle', 'Circle'), ('severity', 'Severity'), ('rca', 'RCA')]:
            filtered_df = filter_by_column(filtered_df, col_name, label)

        # Pastikan kolom total_count ada sebelum digunakan
        if 'total_count' not in filtered_df.columns:
            filtered_df['total_count'] = 1

        # Filter kolom subrootcause
        filtered_df = filter_by_column(filtered_df, 'subrootcause', 'Subrootcause')

        filtered_df['quarter'] = filtered_df['bulan_label_dt'].dt.to_period('Q').dt.to_timestamp()

        st.write(f"📦 Data akhir setelah semua filter: {len(filtered_df)} baris")
        st.dataframe(filtered_df.head())

        if filtered_df.empty:
            st.error("❌ Tidak ada data yang bisa divisualisasikan. Coba ubah filter.")
            st.stop()

        # Hitung ulang agregasi untuk visualisasi
        trend_bulanan = filtered_df.groupby(['bulan_label', 'rca']).size().reset_index(name='count')

        avg_mttr_per_rca = filtered_df.groupby('rca')['mttr'].mean().sort_values(ascending=False)
        avg_mttr_per_circle = filtered_df.groupby('circle')['mttr'].mean().sort_values(ascending=False)
        avg_mttr_per_severity = filtered_df.groupby('severity')['mttr'].mean().sort_values(ascending=False)

        pivot = filtered_df.pivot_table(index='rca', columns='severity', values='total_count', aggfunc='sum', fill_value=0)
        pivot_circle = filtered_df.pivot_table(index='circle', columns='severity', values='total_count', aggfunc='sum', fill_value=0)
        total_bulanan = filtered_df.groupby(['quarter', 'bulan_label']).agg({'total_count': 'sum'}).reset_index()

        # Modeling dan prediksi (jika ada)
        y_test, y_pred = show_model_results(filtered_df)

        # Fungsi untuk menampilkan semua visualisasi
        def show_visualizations(filtered_df, trend_bulanan, avg_mttr_per_rca, avg_mttr_per_severity, avg_mttr_per_circle, pivot, pivot_circle, total_bulanan):
            show_trend(filtered_df)                             # Menampilkan trend dengan pilihan
            show_distribution(filtered_df)                      # Menampilkan distribution dengan pilihan
            show_mttr_per_rca(avg_mttr_per_rca)                 # Menampilkan MTTR per RCA
            show_mttr_per_severity(avg_mttr_per_severity)       # Menampilkan MTTR per Severity
            show_mttr_per_circle(avg_mttr_per_circle)           # Menampilkan MTTR per Circle
            show_heatmap_rca_vs_severity(pivot)                 # Menampilkan heatmap RCA vs Severity
            show_heatmap_circle_vs_severity(pivot_circle)       # Menampilkan heatmap Circle vs Severity
            show_sitename(filtered_df)                          # Menampilkan sitename dengan pilihan
            show_qoq(total_bulanan)                             # Menampilkan QoQ
            show_yoy(total_bulanan)                             # Menampilkan YoY

        # Tampilkan visualisasi
        show_visualizations(filtered_df, trend_bulanan, avg_mttr_per_rca, avg_mttr_per_severity, avg_mttr_per_circle, pivot, pivot_circle, total_bulanan)

        # Export data ke Excel
        excel_output = generate_excel_output(
            filtered_df, trend_bulanan, total_bulanan, avg_mttr_per_rca, pivot,
            y_test if y_test is not None else None,
            y_pred if y_pred is not None else None
        )

        st.download_button(
            label="💾 Unduh Semua Output (Excel)",
            data=excel_output,
            file_name="output_analisis_rca_lengkap.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat memproses file: {e}")
        st.stop()

else:
    st.info("Silakan unggah file data terlebih dahulu.")