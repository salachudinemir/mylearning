import io
import pandas as pd
import streamlit as st
import altair as alt
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
from utils.preprocessing import (
    load_data,
    clean_data
)
from utils.modeling import (
    train_model,
    load_model,
    predict_duration,
    user_input_features,
    load_model_features,
    evaluate_prediction
)
from visualization.plots import (
    plot_restore_duration,
    plot_incident_per_region,
    plot_incident_per_severity,
    plot_sla_violation_pie,
    plot_by_circle,
    plot_by_alarmname,
    plot_by_subcause,
    plot_mccluster_repetitive
)
from visualization.tables import (
    top_rootcause_table,
    sla_violation_table,
    top_subcause_table,
    top_rootcause_subcause_table,
    top_mccluster_table
)

st.set_page_config(page_title="TT Incident Dashboard by Salachudin Emir", layout="wide")
st.title("📊 TT Incident Dashboard by Salachudin Emir")

uploaded_file = st.file_uploader("Upload CSV File", type="csv")

if uploaded_file:
    df = load_data(uploaded_file)
    df = clean_data(df)

    st.sidebar.header("🧰 Filter Data")

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

    # Filter Alarm Name
    alarmname_options = df_for_filter['alarmname'].dropna().unique() if 'alarmname' in df_for_filter.columns else []
    alarmname_filter = safe_multiselect("Alarm Name", alarmname_options, key="filter_alarmname", with_select_all=False, default_selected=[])
    if alarmname_filter:
        df_for_filter = df_for_filter[df_for_filter['alarmname'].isin(alarmname_filter)]

    # Filter Date Range
    if 'createtime' in df.columns and not df['createtime'].isnull().all():
        min_date = df['createtime'].min()
        max_date = df['createtime'].max()

        if pd.isna(min_date) or pd.isna(max_date):
            start_date = end_date = None
        else:
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

    # Terapkan semua filter ke dataframe asli (df_filtered)
    df_filtered = df.copy()

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
    if alarmname_filter:
        df_filtered = df_filtered[df_filtered['alarmname'].isin(alarmname_filter)]

    if start_date and end_date:
        df_filtered = df_filtered[
            (df_filtered['createtime'] >= pd.to_datetime(start_date)) &
            (df_filtered['createtime'] <= pd.to_datetime(end_date))
        ]

    # --- Drop kolom yang tidak ingin ditampilkan di preview & export ---
    columns_to_drop = [
        "weekno", "nename", "ems", "foowner", "escalatetovendor", "alarmid", "currentoperator", "currentoperator_1", "createdat", "closuretime", "restore_duration", "resolve_duration", 
        "orderid_1", "circle_id", "subrootcause2", "faultrecoverytime", "faultresolvingtime", "create_duration", "ticketcreatedby", "92", "<1", 
        "10nedownundersite14smg0266_usmanjanatin_mt,mc-semarangkotautara,java", "fo_ajiznurdin", "5gimpact"
    ]
    cols_exist = [col for col in columns_to_drop if col in df_filtered.columns]
    df_filtered_dropped = df_filtered.drop(columns=cols_exist)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📍 Per Region",
        "🔥 Root Cause",
        "⏳ Durasi",
        "🚨 SLA Violation",
        "📅 Waktu Teraktif",
        "🏘️ MC Cluster",
        "🤖 Model",
        "🧪 Debug Filter"
    ])

    with tab1:
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
        st.subheader("Durasi Restore")
        if 'restore_duration' in df_filtered.columns and not df_filtered.empty:
            fig = plot_restore_duration(df_filtered)
            st.pyplot(fig)
        else:
            st.info("Data restore_duration tidak tersedia atau kosong.")

    with tab4:
        st.subheader("SLA Violation Pie Chart")
        if not df_filtered.empty and 'slastatus' in df_filtered.columns:
            fig = plot_sla_violation_pie(df_filtered)
            st.pyplot(fig)
        else:
            st.info("Data kosong atau kolom 'slastatus' tidak ditemukan.")

        st.subheader("Tabel SLA Violation")

        # Pastikan df_filtered_dropped punya data sebelum ditampilkan
        if not df_filtered_dropped.empty:
            st.dataframe(sla_violation_table(df_filtered_dropped))
        else:
            st.info("Data kosong untuk tabel SLA Violation.")

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
    
    with tab7:
        st.subheader("🤖 Modeling Machine Learning")

        force_retrain = st.checkbox("🏋️‍♂️ Latih ulang model", value=False)

        if force_retrain:
            with st.spinner("Melatih model..."):
                model, mae = train_model(df_filtered, force_retrain=True, return_mae=True)
            st.success(f"Model dilatih dengan MAE: {mae:.2f} menit")
        else:
            model = train_model(df_filtered, force_retrain=False)
            st.info("Model dimuat dari file.")

        # --- PREDIKSI (Manual Input)
        st.subheader("📥 Prediksi Restore Duration (Manual Input)")

        options = user_input_features(df_filtered)
        
        filtered_df = df_filtered.copy()

        orderid = st.selectbox("Order ID", options=filtered_df['orderid'].dropna().unique())
        filtered_df = filtered_df[filtered_df['orderid'] == orderid]

        severity = st.selectbox("Severity", options=filtered_df['severity'].dropna().unique())
        filtered_df = filtered_df[filtered_df['severity'] == severity]

        circle = st.selectbox("Circle", options=filtered_df['circle'].dropna().unique())
        filtered_df = filtered_df[filtered_df['circle'] == circle]

        siteregion = st.selectbox("Site Region", options=filtered_df['siteregion'].dropna().unique())
        filtered_df = filtered_df[filtered_df['siteregion'] == siteregion]

        rootcause = st.selectbox("Root Cause", options=filtered_df['rootcause'].dropna().unique())
        filtered_df = filtered_df[filtered_df['rootcause'] == rootcause]

        subcause = st.selectbox("Subcause", options=filtered_df['subcause'].dropna().unique())
        filtered_df = filtered_df[filtered_df['subcause'] == subcause]

        subcause2 = st.selectbox("Subcause 2", options=filtered_df['subcause2'].dropna().unique())
        filtered_df = filtered_df[filtered_df['subcause2'] == subcause2]

        mccluster = st.selectbox("MC Cluster", options=filtered_df['mccluster'].dropna().unique())
        filtered_df = filtered_df[filtered_df['mccluster'] == mccluster]

        input_data = pd.DataFrame([{
            'orderid': orderid,
            'severity': severity,
            'circle': circle,
            'siteregion': siteregion,
            'rootcause': rootcause,
            'subcause': subcause,
            'subcause2': subcause2,
            'mccluster': mccluster
        }])

        try:
            # Load fitur model
            expected_features = load_model_features()

            # Jika fitur model tidak ditemukan, retrain
            if expected_features is None:
                st.warning("Fitur dari model tidak ditemukan. Melatih ulang model...")
                model, mae = train_model(df_filtered, force_retrain=True, return_mae=True)
                expected_features = model.named_steps['preprocess'].transformers_[0][2] + model.named_steps['preprocess'].transformers_[1][2]
                st.success(f"Model dilatih ulang dengan MAE: {mae:.2f}")

            # Cek apakah ada fitur yang hilang di input_data
            missing_features = set(expected_features) - set(input_data.columns)
            if missing_features:
                st.error(f"Fitur berikut tidak ada di input data: {missing_features}")
            elif input_data.isnull().any().any():
                st.error("Input data masih mengandung NaN. Pastikan semua kolom diisi dengan benar.")
            else:
                # Lakukan prediksi dengan fitur yang sesuai
                prediction = predict_duration(model, input_data[expected_features])
                pred_minutes = np.round(prediction[0], 2)
                hours = int(pred_minutes // 60)
                minutes = int(pred_minutes % 60)

                st.success(f"Prediksi Restore Duration: {pred_minutes} menit ({hours} jam {minutes} menit)")

            # Evaluasi prediksi (gunakan df_filtered_dropped yang sudah disiapkan sebelumnya)
            df_eval, metrics = evaluate_prediction(df_filtered_dropped, model)

            st.markdown("#### 📄 Perbandingan Prediksi vs Aktual")
            st.dataframe(df_eval)

            st.markdown("#### 📈 Metrik Evaluasi")
            col1, col2, col3 = st.columns(3)
            col1.metric("MAE", f"{metrics['MAE']:.2f} menit")
            col2.metric("RMSE", f"{metrics['RMSE']:.2f} menit")
            col3.metric("R² Score", f"{metrics['R2']:.2f}")

        except ValueError as e:
            st.warning(f"⚠️ {str(e)}")
        except Exception as e:
            st.error(f"❌ Terjadi error saat prediksi atau evaluasi: {e}")

    with tab8:
        st.subheader("🧪 Debug Data Filter")

        st.markdown("### 🔵 Data Sebelum Filter (df)")
        st.dataframe(df.head(10))
        # Debug: tampilkan kolom yang tersedia sebelum difilter
        st.write("Kolom tersedia di df_filtered:", df.columns.tolist())

        st.markdown("### 🟢 Data Setelah Drop Kolom (df_filtered_dropped)")
        st.dataframe(df_filtered_dropped.head(10))
        # # Debug: tampilkan kolom yang tersedia setelah difilter
        st.write("Kolom tersedia di df_filtered_dropped:", df_filtered_dropped.columns.tolist())

    # Export file Excel pakai fungsi generate_excel_output
    from utils.exporter import generate_excel_output, drop_columns

    # Drop kolom yg gak mau ditampilkan/export
    df_dropped = drop_columns(df_filtered)

    # Generate excel file
    excel_bytes = generate_excel_output(df_filtered)

    st.download_button(
        label="⬇️ Unduh Data Filter (Excel .xlsx)",
        data=excel_bytes,
        file_name='filtered_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

else:
    st.info("Silakan upload file CSV terlebih dahulu.")
