import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import plotly.express as px


# Fungsi kecil untuk mengurutkan pivot RCA vs Severity
def sort_pivot_by_severity(pivot_df, severity_order=None):
    """
    Urutkan index dan kolom pivot table berdasarkan severity_order.
    Jika severity_order tidak diberikan, gunakan urutan default dari index dan kolom pivot.

    Parameters:
    - pivot_df: pd.DataFrame, pivot RCA vs Severity
    - severity_order: list of str or None, daftar severity urutan prioritas (opsional)

    Returns:
    - pd.DataFrame: pivot terurut
    """
    if severity_order is None:
        severity_order = list(pivot_df.index)

    filtered_index = [s for s in severity_order if s in pivot_df.index]
    filtered_columns = [s for s in severity_order if s in pivot_df.columns]

    return pivot_df.reindex(index=filtered_index, columns=filtered_columns)


def show_visualizations(filtered_df, trend_bulanan, avg_mttr, pivot, total_bulanan):
    # 1. Trend Distribusi per Bulan 
    st.subheader("📈 Trend Distribusi per Bulan")
    def show_combined_trend(filtered_df):
        # Prepare data untuk ketiga tipe trend
        trend_rca = (
            filtered_df.groupby(['bulan_label', 'bulan_sort', 'rca'])
            .size().reset_index(name='count')
            .sort_values('bulan_sort')
        )
        trend_rca['date'] = pd.to_datetime(trend_rca['bulan_label'], format='%b %Y')

        trend_circle = (
            filtered_df.groupby(['bulan_label', 'bulan_sort', 'circle'])
            .size().reset_index(name='count')
            .sort_values('bulan_sort')
        )
        trend_circle['date'] = pd.to_datetime(trend_circle['bulan_label'], format='%b %Y')

        trend_severity = (
            filtered_df.groupby(['bulan_label', 'bulan_sort', 'severity'])
            .size().reset_index(name='count')
            .sort_values('bulan_sort')
        )
        trend_severity['date'] = pd.to_datetime(trend_severity['bulan_label'], format='%b %Y')

        # Dropdown untuk pilih tipe trend
        pilihan = st.selectbox(
            "Pilih Trend yang Ingin Ditampilkan:",
            options=['RCA', 'Circle', 'Severity']
        )

        # Tentukan data yang akan dipakai sesuai pilihan
        if pilihan == 'RCA':
            data = trend_rca
            group_col = 'rca'
            ylabel = "Jumlah Kasus RCA"
            title = "Trend Distribusi RCA per Bulan"
        elif pilihan == 'Circle':
            data = trend_circle
            group_col = 'circle'  # Ganti ke huruf kecil
            ylabel = "Jumlah Kasus Circle"
            title = "Trend Distribusi Circle per Bulan"
        else:
            data = trend_severity
            group_col = 'severity'
            ylabel = "Jumlah Kasus Severity"
            title = "Trend Distribusi Severity per Bulan"

        # Plotting
        fig, ax = plt.subplots(figsize=(12, 6))

        for group in data[group_col].unique():
            subset = data[data[group_col] == group]
            ax.plot(subset['date'], subset['count'], marker='o', label=group)

            # Label angka di atas titik
            for x, y in zip(subset['date'], subset['count']):
                ax.text(x, y + 0.5, str(y), ha='center', va='bottom', fontsize=8, rotation=0)

        ax.set_xlabel("Bulan")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(title=group_col.capitalize(), bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        st.pyplot(fig)

    # Panggil fungsi show_combined_trend di dalam show_visualizations
    show_combined_trend(filtered_df)


    # 2. Visualisasi Distribusi RCA, Circle, atau Severity
    st.subheader("📌 Distribusi RCA, Circle, atau Severity")
    def show_distribution(filtered_df):
        pilihan = st.selectbox(
            "Pilih distribusi yang ingin ditampilkan:",
            options=['RCA', 'Circle', 'Severity']
        )

        kolom = pilihan.lower()

        fig, ax = plt.subplots(figsize=(10, 5))

        order = filtered_df[kolom].value_counts().index

        countplot = sns.countplot(data=filtered_df, x=kolom, order=order, ax=ax)
        ax.set_xlabel(kolom.capitalize())
        ax.set_ylabel("Jumlah Kasus")
        ax.set_title(f"Distribusi {pilihan}")

        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

        for p in countplot.patches:
            ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        st.pyplot(fig)

    show_distribution(filtered_df)

    # 3. MTTR Rata-rata per RCA
    st.subheader("⏱️ MTTR Rata-rata per RCA")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    avg_mttr.plot(kind='bar', ax=ax2)
    ax2.set_ylabel("MTTR (Mean)")
    ax2.set_xticklabels(avg_mttr.index, rotation=45)
    for i, val in enumerate(avg_mttr):
        ax2.text(i, val, f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    st.pyplot(fig2)

    # 4. Visualisasi Heatmap RCA vs Severity
    st.subheader("🔥 Heatmap RCA vs Severity")

    # Tentukan urutan severity
    severity_order = ['Emergency', 'Critical', 'Major']

    # Urutkan pivot berdasarkan kolom (dan index jika perlu)
    pivot_sorted = pivot.reindex(columns=severity_order)

    # Buat heatmap dengan data yang sudah diurutkan
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot_sorted, annot=True, fmt='d', cmap='YlGnBu', ax=ax3)
    st.pyplot(fig3)

    # 5. Visualisasi Sitename dengan Repetisi Tinggi
    if 'sitename' not in filtered_df.columns:
        st.warning("Kolom 'sitename' tidak ditemukan dalam data.")
    else:
        st.subheader("📍 Top Sitename dengan Repetisi Kasus Tertinggi (Minimal 3x)")

        # Pastikan kolom 'circle' ada
        if 'circle' in filtered_df.columns:
            available_circles = sorted(filtered_df['circle'].dropna().unique())
            selected_circles = st.multiselect(
                "Pilih Circle (opsional):",
                options=available_circles,
                default=available_circles
            )
            circle_filtered_df = filtered_df[filtered_df['circle'].isin(selected_circles)]
        else:
            st.warning("Kolom 'circle' tidak ditemukan dalam data. Menampilkan semua data.")
            circle_filtered_df = filtered_df

        # Hitung jumlah kejadian per sitename (minimal 3)
        sitename_counts = circle_filtered_df['sitename'].value_counts()
        sitename_counts = sitename_counts[sitename_counts >= 3].reset_index()
        sitename_counts.columns = ['Sitename', 'Jumlah Kejadian']

        # Buat mapping sitename ke circle (ambil circle pertama dari data yang sudah difilter)
        sitename_to_circle = circle_filtered_df.groupby('sitename')['circle'].first().to_dict()

        # Tambahkan kolom 'Sitename (Circle)'
        sitename_counts['Sitename (Circle)'] = sitename_counts['Sitename'].apply(
            lambda x: f"{x} ({sitename_to_circle.get(x, '-')})"
        )

        # Fungsi buat label bulan per sitename dengan count per bulan
        def bulan_label_dengan_count(sitename):
            df_site = circle_filtered_df[circle_filtered_df['sitename'] == sitename]
            bulan_counts = df_site['bulan_label'].value_counts()
            sorted_bulan = sorted(bulan_counts.index, key=lambda b: pd.to_datetime(b, format='%b %Y'))
            labels = [f"{bulan} ({bulan_counts[bulan]})" for bulan in sorted_bulan]
            return ', '.join(labels)

        sitename_counts['Bulan Label'] = sitename_counts['Sitename'].apply(bulan_label_dengan_count)

        if sitename_counts.empty:
            st.info("Tidak ada site dengan kejadian ≥ 3.")
        else:
            # 🔍 Fitur pencarian site
            all_sites = sitename_counts['Sitename (Circle)'].tolist()
            selected_sites = st.multiselect("Cari dan pilih site (opsional):", options=all_sites)

            if selected_sites:
                filtered_sites = sitename_counts[sitename_counts['Sitename (Circle)'].isin(selected_sites)]
            else:
                top_n = st.slider("Pilih Top-N Site untuk ditampilkan", min_value=5, max_value=50, value=10)
                filtered_sites = sitename_counts.head(top_n)

            # 📊 Bar chart dengan label bulan dan count per bulan
            fig = px.bar(
                filtered_sites,
                x='Jumlah Kejadian',
                y='Sitename (Circle)',
                orientation='h',
                text='Bulan Label',
                title="Sitename dengan Jumlah Kasus Terbanyak (≥ 3)",
                labels={'Jumlah Kejadian': 'Jumlah Kasus', 'Sitename (Circle)': 'Nama Site'}
            )
            fig.update_traces(textposition='inside', textfont_size=10)
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

    # 6. Visualisasi Grafik Quarter-over-Quarter (QOQ) Growth per Kuartal
    st.subheader("📉 Grafik Quarter-over-Quarter (QOQ) Growth per Kuartal")
    quarterly = total_bulanan.groupby('quarter').agg({'total_count': 'sum'}).reset_index()
    quarterly['year'] = quarterly['quarter'].dt.year
    quarterly['quarter_num'] = quarterly['quarter'].dt.quarter
    quarterly['qoq_growth_%'] = quarterly['total_count'].pct_change() * 100

    tahun_terakhir = quarterly['year'].max()
    data_tahun_ini = quarterly[quarterly['year'] == tahun_terakhir].copy()
    data_tahun_lalu = quarterly[quarterly['year'] == tahun_terakhir - 1].copy()

    data_tahun_ini['quarter_label'] = 'Q' + data_tahun_ini['quarter_num'].astype(str)
    data_tahun_lalu['quarter_label'] = 'Q' + data_tahun_lalu['quarter_num'].astype(str)

    fig_qoq, ax_qoq = plt.subplots(figsize=(12, 6))
    ax_qoq.plot(
        data_tahun_ini['quarter_label'],
        data_tahun_ini['qoq_growth_%'],
        marker='o', linestyle='-', color='orange', label=f'QOQ Growth Tahun {tahun_terakhir}'
    )
    ax_qoq.plot(
        data_tahun_lalu['quarter_label'],
        data_tahun_lalu['qoq_growth_%'],
        marker='o', linestyle='--', color='gray', label=f'QOQ Growth Tahun {tahun_terakhir - 1}'
    )
    ax_qoq.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax_qoq.set_xlabel("Kuartal")
    ax_qoq.set_ylabel("QOQ Growth (%)")
    ax_qoq.set_title("Trend QOQ Growth Kasus per Kuartal: Tahun Ini vs Tahun Lalu")
    plt.xticks(rotation=45)
    plt.grid(True)
    ax_qoq.legend()
    st.pyplot(fig_qoq)

    # 7. Visualisasi Tabel Quarter-over-Quarter (QOQ) Growth per Kuartal
    st.subheader("📊 Tabel Quarter-over-Quarter (QOQ) Growth per Kuartal")
    tabel_qoq = pd.merge(
        data_tahun_ini[['quarter_label', 'total_count', 'qoq_growth_%']],
        data_tahun_lalu[['quarter_label', 'total_count', 'qoq_growth_%']],
        on='quarter_label',
        how='outer',
        suffixes=(f' Tahun {tahun_terakhir}', f' Tahun {tahun_terakhir - 1}')
    )
    tabel_qoq = tabel_qoq.replace('-', np.nan)

    st.dataframe(tabel_qoq.style.format({
        f'total_count Tahun {tahun_terakhir}': '{:,.0f}',
        f'qoq_growth_% Tahun {tahun_terakhir}': '{:.2f}%',
        f'total_count Tahun {tahun_terakhir - 1}': '{:,.0f}',
        f'qoq_growth_% Tahun {tahun_terakhir - 1}': '{:.2f}%'
    }))

    # 8. Visualisasi Komparasi Jumlah Kasus Tahun Ini vs Tahun Lalu (YOY)
    st.subheader("📈 Komparasi Jumlah Kasus Tahun Ini vs Tahun Lalu (YOY)")
    tahun_terakhir = int(total_bulanan['bulan_label'].iloc[-1].split()[-1])
    tahun_ini = total_bulanan[total_bulanan['bulan_label'].str.endswith(str(tahun_terakhir))].copy()
    tahun_lalu = total_bulanan[total_bulanan['bulan_label'].str.endswith(str(tahun_terakhir - 1))].copy()

    bulan_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    tahun_ini['bulan_short'] = pd.Categorical(tahun_ini['bulan_label'].str[:3], categories=bulan_order, ordered=True)
    tahun_lalu['bulan_short'] = pd.Categorical(tahun_lalu['bulan_label'].str[:3], categories=bulan_order, ordered=True)

    tahun_ini.sort_values('bulan_short', inplace=True)
    tahun_lalu.sort_values('bulan_short', inplace=True)

    fig_compare, ax_compare = plt.subplots(figsize=(12, 6))
    ax_compare.plot(tahun_lalu['bulan_short'], tahun_lalu['total_count'], marker='o', label=f"Tahun {tahun_terakhir - 1}", color='gray')
    ax_compare.plot(tahun_ini['bulan_short'], tahun_ini['total_count'], marker='o', label=f"Tahun {tahun_terakhir}", color='blue')
    ax_compare.set_xlabel("Bulan")
    ax_compare.set_ylabel("Jumlah Kasus")
    ax_compare.set_title("Komparasi Jumlah Kasus per Bulan: Tahun Ini vs Tahun Lalu")
    ax_compare.legend()
    plt.grid(True)
    st.pyplot(fig_compare)

    # 9. Visualisasi Tabel Year-over-Year (YOY) Growth per Bulan
    st.subheader("📊 Tabel Year-over-Year (YOY) Growth per Bulan")
    tabel_yoy = pd.merge(
        tahun_ini[['bulan_short', 'total_count']],
        tahun_lalu[['bulan_short', 'total_count']],
        on='bulan_short',
        how='outer',
        suffixes=(f' Tahun {tahun_terakhir}', f' Tahun {tahun_terakhir - 1}')
    )

    tabel_yoy['Growth YOY (%)'] = (
        (tabel_yoy[f'total_count Tahun {tahun_terakhir}'] - tabel_yoy[f'total_count Tahun {tahun_terakhir - 1}'])
        / tabel_yoy[f'total_count Tahun {tahun_terakhir - 1}']
    ) * 100
    tabel_yoy.replace([np.inf, -np.inf], np.nan, inplace=True)

    st.dataframe(tabel_yoy.style.format({
        f'total_count Tahun {tahun_terakhir}': '{:,.0f}',
        f'total_count Tahun {tahun_terakhir - 1}': '{:,.0f}',
        'Growth YOY (%)': '{:.2f}%'
    }))
