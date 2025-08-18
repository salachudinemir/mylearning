# /app.py

import io
import os
import re
import tempfile
import hashlib
import pandas as pd
import streamlit as st

# --- Page config ---
st.set_page_config(page_title="🚀 Incident App by Salachudin Emir", layout="wide")

from streamlit.runtime.scriptrunner.script_runner import RerunException, RerunData
import altair as alt
import sqlite3
import zipfile
import math

from utils.preprocessing import *
from visualization.plots import *
from visualization.tables import *
from utils.preprocessing import *
from visualization.plots import *
from visualization.tables import *
from tab.tab4_slaviolation import *
from tab.tab7_forecast import *
from tab.tab8_raw_visual import *
from tab.tab10_chatbot import *
from tab.tab99_settings import *

# --- Sidebar Mode Selection ---
st.sidebar.title("🔀 Select Mode")
mode = st.sidebar.radio("Select Mode Application", ["Dashboard", "Combine Data"])

# --- Helper Functions ---
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

df = None
selected_table = None

# --- MODE: GABUNG FILE ---
if mode == "Combine Data":
    st.title("📁 Combine File Excel / CSV by Salachudin Emir")
    st.markdown("Upload several .xlsx or .csv files, combine them, and download the result.")

    output_format = st.sidebar.radio("Format Output", ["Excel (.xlsx)", "CSV (.csv)", "SQLite Database (.db)"])
    uploaded_files = st.file_uploader("Unggah File", type=["xlsx", "csv"], accept_multiple_files=True)

    if uploaded_files:
        with st.spinner("📦 Loading & Cleaning Data..."):
            st.info(f"{len(uploaded_files)} file berhasil diunggah.")
            dataframes = read_uploaded_files(uploaded_files)

            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                st.success(f"✅ Gabungan selesai! Total: {len(combined_df)} baris, {combined_df.shape[1]} kolom.")
                st.dataframe(combined_df)

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

# --- Helper untuk baca file lokal ---
def get_local_file():
    """
    Cek apakah ada file lokal yang bisa digunakan.
    Urutan prioritas: absolute path tertentu -> file default di working dir.
    """
    candidates = [
        r"C:\Users\Salachudin Emir\Documents\Python Workspace\Dataset\TT-INC\Incident Ticket_ManualFO_W02-W32_2025.xlsx",
        "data.csv", "data.xlsx", "data.xls",
        "data.db", "data.parquet", "data.feather"
    ]
    for fname in candidates:
        if os.path.exists(fname):
            return fname
    return None


def open_file_as_uploaded(path):
    """
    Buka file lokal agar kompatibel dengan streamlit uploader (punya atribut .name).
    """
    with open(path, "rb") as f:
        file_bytes = io.BytesIO(f.read())
    file_bytes.name = os.path.basename(path)
    return file_bytes


# --- Dashboard Mode ---
if mode == "Dashboard":
    st.title("📊 Dashboard TT Incident by Salachudin Emir")

    # --- Cek file lokal lebih dulu ---
    local_file = get_local_file()

    if local_file:
        st.info(f"📂 Membaca data dari file lokal: **{local_file}**")
        uploaded_file = open_file_as_uploaded(local_file)
    else:
        uploaded_file = st.file_uploader(
            "Upload File Data (CSV, Excel, Parquet, Feather, atau SQLite DB)", 
            type=["csv", "xls", "xlsx", "db", "parquet", "feather"]
        )

    if uploaded_file:
        with st.spinner("📦 Loading & Cleaning Data..."):
            try:
                file_ext = uploaded_file.name.split('.')[-1].lower()

                # --- Jika file SQLite (.db) ---
                if file_ext == 'db':
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                        tmp.write(uploaded_file.read())
                        db_path = tmp.name

                    try:
                        with sqlite3.connect(db_path) as conn:
                            tables = pd.read_sql_query(
                                "SELECT name FROM sqlite_master WHERE type='table';", conn
                            )
                            table_list = tables['name'].tolist()

                        selected_table = st.sidebar.selectbox("📂 Pilih Tabel Database:", table_list)

                        with open(db_path, 'rb') as db_file:
                            raw_df = load_and_cache_data(db_file, table_name=selected_table)
                    finally:
                        if os.path.exists(db_path):
                            os.remove(db_path)

                # --- Jika file non-DB ---
                else:
                    raw_df = load_and_cache_data(uploaded_file)

                # --- Clean data ---
                df = clean_data(raw_df)
                st.session_state["df_clean"] = df
                st.success("✅ Data berhasil dimuat dan dibersihkan.")

                # --- Simpan df_clean ke pickle untuk dipakai Telegram Bot ---
                try:
                    df.to_pickle("df_clean.pkl")
                    st.info("💾 Data juga disimpan ke df_clean.pkl (untuk Telegram Bot).")
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan df_clean.pkl: {e}")

            except Exception as e:
                st.error(f"❌ Gagal memuat data: {e}")

# --- FILTER SECTION ---
if df is not None and not df.empty:
    st.sidebar.header("🧰 Filter Data")

    # Helper: multiselect dengan "Pilih Semua"
    def safe_multiselect(label, options, key, with_select_all=True, default_selected=None):
        if not options:
            return []
        if with_select_all:
            select_all_key = f"{key}_select_all"
            select_all = st.sidebar.checkbox(f"Pilih Semua {label}", key=select_all_key)
            default = sorted(options) if select_all else (default_selected or [])
        else:
            default = default_selected or []
        return st.sidebar.multiselect(label, options=sorted(options), default=default, key=key)

    df_for_filter = df.copy()

    # Fungsi multiselect dengan 'Pilih Semua'
    def safe_multiselect(label, options, key, with_select_all=True, default_selected=None):
        if options is not None and len(options) > 0:
            if with_select_all:
                select_all_key = f"{key}_select_all"
                select_all = st.sidebar.checkbox(f"Pilih Semua {label}", key=select_all_key)
                if select_all:
                    default = sorted(options)
                else:
                    default = default_selected if default_selected is not None else []
                return st.sidebar.multiselect(label, options=sorted(options), default=default, key=key)
            else:
                # Tanpa checkbox 'Pilih Semua', default sesuai param default_selected atau kosong
                default = default_selected if default_selected is not None else []
                return st.sidebar.multiselect(label, options=sorted(options), default=default, key=key)
        else:
            return []

    df_for_filter = df.copy()

    # Filter Create Mode
    createmode_options = df_for_filter['createmode'].dropna().unique() if 'createmode' in df_for_filter.columns else []
    createmode_filter = safe_multiselect("Create Mode", createmode_options, key="filter_createmode")
    if createmode_filter:
        df_for_filter = df_for_filter[df_for_filter['createmode'].isin(createmode_filter)]

    # Filter Circle
    circle_options = df_for_filter['circle'].dropna().unique() if 'circle' in df_for_filter.columns else []
    circle_filter = safe_multiselect("Circle", circle_options, key="filter_circle")
    if circle_filter:
        df_for_filter = df_for_filter[df_for_filter['circle'].isin(circle_filter)]

    # Filter Region
    region_options = df_for_filter['siteregion'].dropna().unique() if 'siteregion' in df_for_filter.columns else []
    region_filter = safe_multiselect("Region", region_options, key="filter_region")
    if region_filter:
        df_for_filter = df_for_filter[df_for_filter['siteregion'].isin(region_filter)]

    # Filter Severity
    severity_options = df_for_filter['severity'].dropna().unique() if 'severity' in df_for_filter.columns else []
    severity_filter = safe_multiselect("Severity", severity_options, key="filter_severity")
    if severity_filter:
        df_for_filter = df_for_filter[df_for_filter['severity'].isin(severity_filter)]

    # Filter Root Cause
    rootcause_options = df_for_filter['rootcause'].dropna().unique() if 'rootcause' in df_for_filter.columns else []
    rootcause_filter = safe_multiselect("Root Cause", rootcause_options, key="filter_rootcause")
    if rootcause_filter:
        df_for_filter = df_for_filter[df_for_filter['rootcause'].isin(rootcause_filter)]

    # Filter Subcause
    subcause_options = df_for_filter['subcause'].dropna().unique() if 'subcause' in df_for_filter.columns else []
    subcause_filter = safe_multiselect("Subcause", subcause_options, key="filter_subcause")
    if subcause_filter:
        df_for_filter = df_for_filter[df_for_filter['subcause'].isin(subcause_filter)]

    # Filter MC Cluster
    mccluster_options = df_for_filter['mccluster'].dropna().unique() if 'mccluster' in df_for_filter.columns else []
    mccluster_filter = safe_multiselect("MC Cluster", mccluster_options, key="filter_mccluster", with_select_all=False, default_selected=[])
    if mccluster_filter:
        df_for_filter = df_for_filter[df_for_filter['mccluster'].isin(mccluster_filter)]

    # Filter Date Range
    if 'createtime' in df.columns and not df['createtime'].isnull().all():
        min_date = df['createtime'].min()
        max_date = df['createtime'].max()

        if not pd.isna(min_date) and not pd.isna(max_date):
            min_date = min_date.date()
            max_date = max_date.date()

            date_range = st.sidebar.date_input(
                "Tanggal (Createtime) Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="date_range"
            )

            if isinstance(date_range, (tuple, list)):
                if len(date_range) == 2:
                    start_date, end_date = date_range
                elif len(date_range) == 1:
                    start_date = end_date = date_range[0]
                else:
                    start_date = end_date = None
            else:
                start_date = end_date = date_range
        else:
            start_date = end_date = None
    else:
        start_date = end_date = None

    # Load dan bersihkan data
    df = load_and_cache_data(uploaded_file, table_name=selected_table)
    df = clean_data(df)
    df = drop_unwanted_columns(df, DROP_COLUMNS)

    # Salin ke dataframe untuk difilter
    df_filtered = df.copy()

    # Terapkan filter
    if createmode_filter:
        df_filtered = df_filtered[df_filtered['createmode'].isin(createmode_filter)]
    if circle_filter:
        df_filtered = df_filtered[df_filtered['circle'].isin(circle_filter)]
    if region_filter:
        df_filtered = df_filtered[df_filtered['siteregion'].isin(region_filter)]
    if severity_filter:
        df_filtered = df_filtered[df_filtered['severity'].isin(severity_filter)]
    if rootcause_filter:
        df_filtered = df_filtered[df_filtered['rootcause'].isin(rootcause_filter)]
    if subcause_filter:
        df_filtered = df_filtered[df_filtered['subcause'].isin(subcause_filter)]
    if mccluster_filter:
        df_filtered = df_filtered[df_filtered['mccluster'].isin(mccluster_filter)]
    if start_date and end_date:
        df_filtered = df_filtered[
            (df_filtered['createtime'] >= pd.to_datetime(start_date)) &
            (df_filtered['createtime'] <= pd.to_datetime(end_date))
        ]

    # Preview kolom yang akan dihapus
    cols_to_drop_preview = preview_columns_to_drop(df_filtered, DROP_COLUMNS)

    # Ekspor dan hapus kolom jika diminta
    st.sidebar.subheader("⚙️ Ekspor Data")
    drop_confirm = st.sidebar.checkbox("Hapus kolom tertentu sebelum ekspor & analisis?", value=True)

    if drop_confirm:
        df_filtered_dropped = drop_unwanted_columns(df_filtered, DROP_COLUMNS)
    else:
        df_filtered_dropped = df_filtered.copy()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab99 = st.tabs([
        "📍 Bar Incident",  # tab1
        "🔥 Root Cause",  # tab2
        "⏳ Restore Duration",  # tab3
        "🚨 SLA Violation",  # tab4
        "📅 Waktu Teraktif",  # tab5
        "🏘️ Repetitive",  # tab6
        "🔄 Forecast",  # tab7
        "🔍 Raw Visual",  # tab8
        "🧪 Debug Filter",  # tab9
        "🤖 Chatbot",  # tab10
        "⚙️ Settting"  # tab99
    ])

    with tab1:
        st.subheader("📍 Jumlah Insiden per Circle")  # Tambahan bagian Circle
        if 'circle' in df_filtered_dropped.columns and not df_filtered_dropped.empty:
            fig = plot_incident_per_circle(df_filtered_dropped)
            st.pyplot(fig)
        else:
            st.info("Data circle tidak tersedia atau kosong.")

        st.subheader("🗺️ Jumlah Insiden per Region")
        if 'siteregion' in df_filtered_dropped.columns and not df_filtered_dropped.empty:
            fig = plot_incident_per_region(df_filtered_dropped)
            st.pyplot(fig)
        else:
            st.info("Data Region tidak tersedia atau hasil filter kosong.")

        st.subheader("📶 Jumlah Insiden per Severity")
        if 'severity' in df_filtered_dropped.columns and not df_filtered_dropped.empty:
            fig = plot_incident_per_severity(df_filtered_dropped)
            st.pyplot(fig)
        else:
            st.info("Data severity tidak tersedia atau kosong.")

    with tab2:
        st.subheader("Top Root Causes")
        st.dataframe(top_rootcause_table(df_filtered_dropped))

        st.subheader("Top Subcauses")
        st.dataframe(top_subcause_table(df_filtered_dropped))

        st.subheader("🔍 Relasi Rootcause dan Subcause")
        st.caption("Menampilkan subcause teratas untuk masing-masing rootcause utama.")
        st.dataframe(top_rootcause_subcause_table(df_filtered_dropped))

    with tab3:
        st.subheader("Restore Duration")

        if 'restoreduration' in df_filtered.columns and not df_filtered.empty:
            # Visualisasi distribusi umum (histogram)
            fig = plot_restore_duration(df_filtered)
            st.pyplot(fig)

            # Insight rata-rata restore duration per rootcause
            plot_restore_duration_by_rootcause(df_filtered)

            # Visualisasi restore duration per severity (boxplot)
            st.pyplot(plot_restore_duration_by_severity(df_filtered))

            # Insight restore duration per circle
            plot_restore_duration_by_circle(df_filtered)

            # Bonus: kombinasi rootcause + severity
            plot_combined_rootcause_severity(df_filtered)

        else:
            st.info("Data restoreduration tidak tersedia atau kosong.")

    with tab4:
        st.subheader("⏳ SLA Violation Visualization & Classification")
        render_tab4_app(
            df_filtered=df_filtered,
            createmode_filter=createmode_filter,
            circle_filter=circle_filter,
            severity_filter=severity_filter,
            start_date=start_date,
            end_date=end_date
        )

    with tab5:
        st.subheader("📈 Trend Jumlah Insiden")
        if 'createtime' in df_filtered_dropped.columns and not df_filtered_dropped.empty:
            if 'week_str' not in df_filtered_dropped.columns:
                df_filtered_dropped['week_str'] = df_filtered_dropped['createtime'].dt.strftime('%Y-W%V')
            if 'month_str' not in df_filtered_dropped.columns:
                df_filtered_dropped['month_str'] = df_filtered_dropped['createtime'].dt.strftime('%Y-%m')
            if 'quarter_str' not in df_filtered_dropped.columns:
                df_filtered_dropped['quarter_str'] = (
                    df_filtered_dropped['createtime'].dt.year.astype(str) + '-Q' + df_filtered_dropped['createtime'].dt.quarter.astype(str)
                )

            weekly_count = df_filtered_dropped['week_str'].value_counts().sort_index()
            monthly_count = df_filtered_dropped['month_str'].value_counts().sort_index()
            quarterly_count = df_filtered_dropped['quarter_str'].value_counts().sort_index()

            # 📅 Mingguan
            st.markdown("### 📅 Jumlah Insiden per Minggu")
            weekly_df = weekly_count.reset_index()
            weekly_df.columns = ['week', 'count']
            weekly_chart = alt.Chart(weekly_df).mark_line(point=True).encode(
                x=alt.X('week:N', title='Minggu'),
                y=alt.Y('count:Q', title='Jumlah Insiden'),
                tooltip=['week', 'count']
            ) + alt.Chart(weekly_df).mark_text(
                align='center',
                baseline='bottom',
                dy=-5
            ).encode(
                x='week:N',
                y='count:Q',
                text='count:Q'
            ).properties(width=700, height=300)
            st.altair_chart(weekly_chart, use_container_width=True)

            # 🗓️ Bulanan
            st.markdown("### 🗓️ Jumlah Insiden per Bulan")
            monthly_df = monthly_count.reset_index()
            monthly_df.columns = ['month', 'count']
            monthly_chart = alt.Chart(monthly_df).mark_line(point=True).encode(
                x=alt.X('month:N', title='Bulan'),
                y=alt.Y('count:Q', title='Jumlah Insiden'),
                tooltip=['month', 'count']
            ) + alt.Chart(monthly_df).mark_text(
                align='center',
                baseline='bottom',
                dy=-5
            ).encode(
                x='month:N',
                y='count:Q',
                text='count:Q'
            ).properties(width=700, height=300)
            st.altair_chart(monthly_chart, use_container_width=True)

            # 🕓 Kuartalan
            st.markdown("### 🕓 Jumlah Insiden per Kuartal")
            quarterly_df = quarterly_count.reset_index()
            quarterly_df.columns = ['quarter', 'count']
            quarterly_chart = alt.Chart(quarterly_df).mark_bar().encode(
                x=alt.X('quarter:N', title='Kuartal'),
                y=alt.Y('count:Q', title='Jumlah Insiden'),
                tooltip=['quarter', 'count']
            ) + alt.Chart(quarterly_df).mark_text(
                align='center',
                baseline='bottom',
                dy=-5
            ).encode(
                x='quarter:N',
                y='count:Q',
                text='count:Q'
            ).properties(width=700, height=300)
            st.altair_chart(quarterly_chart, use_container_width=True)

            # 🏆 Periode Tertinggi
            top_week = weekly_count.idxmax() if not weekly_count.empty else "N/A"
            top_month = monthly_count.idxmax() if not monthly_count.empty else "N/A"
            top_quarter = quarterly_count.idxmax() if not quarterly_count.empty else "N/A"

            st.markdown("### 🏆 Periode dengan Insiden Terbanyak")
            col1, col2, col3 = st.columns(3)
            col1.metric("📆 Minggu", top_week)
            col2.metric("🗓️ Bulan", top_month)
            col3.metric("🕓 Kuartal", top_quarter)

            # 🥇 Ranking Region
            st.markdown("### 🥇 Peringkat Region per Bulan")
            region_month = (
                df_filtered_dropped.groupby(['month_str', 'siteregion'])
                .size()
                .reset_index(name='incident_count')
            )
            region_month_sorted = region_month.sort_values(['month_str', 'incident_count'], ascending=[True, False])
            region_pivot = region_month_sorted.pivot(index='siteregion', columns='month_str', values='incident_count').fillna(0).astype(int)
            st.dataframe(region_pivot.style.background_gradient(cmap='OrRd', axis=0), use_container_width=True)
        else:
            st.warning("Kolom `createtime` tidak tersedia atau data kosong.")

    with tab6:
        st.subheader("🏙️ Top MC Cluster Berdasarkan Jumlah Insiden")
        plot_mccluster_repetitive(df_filtered_dropped)
        st.subheader("🏙️ Top Site ID Jumlah Insiden")
        plot_siteid_repetitive(df_filtered_dropped)
    
    with tab7:
        render_tab7(
            df_filtered=df_filtered,
            createmode_filter=createmode_filter,
            circle_filter=circle_filter,
            severity_filter=severity_filter,
            start_date=start_date,
            end_date=end_date
        )

    with tab8:
        st.header("Visualisasi Similarity (Fuzzy Matching)")
        show_similar_pairs(df, 'rootcause')
        show_similar_pairs(df, 'subcause')
        
    with tab9:
        st.subheader("🧪 Debug Data Filter")

        st.markdown("### 🔵 Data Sebelum Filter (df)")
        st.dataframe(df.head(10))
        st.write("Kolom tersedia di df:", df.columns.tolist())

        st.markdown("### 🟠 Kolom yang akan dihapus:")
        st.write(cols_to_drop_preview)

        st.markdown("### 🟢 Data Setelah Drop Kolom (df_filtered_dropped)")
        st.dataframe(df_filtered_dropped.head(10))
        st.write("Kolom tersedia di df_filtered_dropped:", df_filtered_dropped.columns.tolist())

    with tab10:
        with st.spinner("🤖 Chatbot sedang berpikir... 🔄"):
            chatbot_ui()

    with tab99:
        settings_ui()
        
    def generate_excel_output(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        return output.getvalue()

    # Misal kamu sudah punya df_filtered dan df_filtered_dropped
    excel_filtered = generate_excel_output(df_filtered)
    excel_dropped = generate_excel_output(df_filtered_dropped)

    st.download_button(
        label="⬇️ Download Data Full",
        data=excel_filtered,
        file_name='data_full.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.download_button(
        label="⬇️ Download Data Filtered",
        data=excel_dropped,
        file_name='data_filtered.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )