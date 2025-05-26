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
    # 1. Trend Distribusi RCA per Bulan 
    st.subheader("📈 Trend Distribusi RCA per Bulan")
    trend_bulanan['date'] = pd.to_datetime(trend_bulanan['bulan_label'], format='%b %Y')
    trend_bulanan = trend_bulanan.sort_values('date')

    fig_trend, ax_trend = plt.subplots(figsize=(12, 6))
    for rca_type in trend_bulanan['rca'].unique():
        data_plot = trend_bulanan[trend_bulanan['rca'] == rca_type]
        ax_trend.plot(data_plot['date'], data_plot['count'], marker='o', label=rca_type)

    ax_trend.set_xlabel("Bulan")
    ax_trend.set_ylabel("Jumlah Kasus RCA")
    ax_trend.set_title("Trend RCA per Bulan")
    ax_trend.legend(title='RCA', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax_trend.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig_trend)

    # 2. Visualisasi Distribusi RCA
    st.subheader("📌 Distribusi RCA")
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    countplot = sns.countplot(data=filtered_df, x='rca', order=filtered_df['rca'].value_counts().index, ax=ax1)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
    for p in countplot.patches:
        ax1.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=9)
    st.pyplot(fig1)

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
        st.subheader("📍 Top Sitename dengan Repetisi Kasus Tertinggi")

        sitename_counts = filtered_df['sitename'].value_counts().reset_index()
        sitename_counts.columns = ['Sitename', 'Jumlah Kejadian']

        # 🔍 Tambahkan fitur pencarian site
        all_sites = sitename_counts['Sitename'].tolist()
        selected_sites = st.multiselect("Cari dan pilih site (opsional):", options=all_sites)

        # Filter berdasarkan pilihan user
        if selected_sites:
            filtered_sites = sitename_counts[sitename_counts['Sitename'].isin(selected_sites)]
        else:
            top_n = st.slider("Pilih Top-N Site untuk ditampilkan", min_value=5, max_value=50, value=10)
            filtered_sites = sitename_counts.head(top_n)

        # 📊 Visualisasi bar chart
        fig = px.bar(
            filtered_sites,
            x='Jumlah Kejadian',
            y='Sitename',
            orientation='h',
            title=f"Sitename dengan Jumlah Kasus Terbanyak",
            labels={'Jumlah Kejadian': 'Jumlah Kasus', 'Sitename': 'Nama Site'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
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
