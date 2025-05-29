import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

def show_trend(filtered_df):
    """
    Menampilkan grafik trend distribusi per bulan berdasarkan pilihan: RCA, Circle, atau Severity.
    Digunakan sebagai bagian dari dashboard visualisasi.
    """
    st.subheader("📈 Trend Distribusi per Bulan")

    # Siapkan data trend per kategori
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

    # Dropdown untuk memilih kategori tren
    pilihan = st.selectbox(
        "Pilih Trend yang Ingin Ditampilkan:",
        options=['RCA', 'Circle', 'Severity'],
        key='trend_selector'
    )

    # Mapping pilihan ke data dan parameter plotting
    if pilihan == 'RCA':
        data = trend_rca
        group_col = 'rca'
        ylabel = "Jumlah Kasus RCA"
        title = "Trend Distribusi RCA per Bulan"
    elif pilihan == 'Circle':
        data = trend_circle
        group_col = 'circle'
        ylabel = "Jumlah Kasus Circle"
        title = "Trend Distribusi Circle per Bulan"
    else:
        data = trend_severity
        group_col = 'severity'
        ylabel = "Jumlah Kasus Severity"
        title = "Trend Distribusi Severity per Bulan"

    # Plot tren
    fig, ax = plt.subplots(figsize=(12, 6))

    for group in data[group_col].dropna().unique():
        subset = data[data[group_col] == group]
        ax.plot(subset['date'], subset['count'], marker='o', label=group)

        # Tambahkan label angka di atas titik
        for x, y in zip(subset['date'], subset['count']):
            ax.text(x, y + 0.5, str(y), ha='center', va='bottom', fontsize=8)

    ax.set_xlabel("Bulan")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(title=group_col.capitalize(), bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)
