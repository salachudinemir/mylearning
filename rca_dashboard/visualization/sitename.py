# sitename.py

import streamlit as st
import pandas as pd
import plotly.express as px

def show_sitename(filtered_df):
    """
    Menampilkan visualisasi Top Sitename dengan repetisi kasus tertinggi (minimal 3 kali),
    dengan filter Circle opsional, pencarian site, dan info jumlah kasus per bulan.

    Parameters:
    - filtered_df: pd.DataFrame, dataframe yang sudah difilter
    """

    if 'sitename' not in filtered_df.columns:
        st.warning("Kolom 'sitename' tidak ditemukan dalam data.")
        return

    st.subheader("📍 Top Sitename dengan Repetisi Kasus Tertinggi (Minimal 3x)")

    # Filter berdasarkan circle jika kolom 'circle' tersedia
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

    if sitename_counts.empty:
        st.info("Tidak ada site dengan kejadian ≥ 3.")
        return

    # Mapping sitename ke circle (ambil circle pertama dari data yang sudah difilter)
    sitename_to_circle = circle_filtered_df.groupby('sitename')['circle'].first().to_dict()

    # Tambahkan kolom 'Sitename (Circle)'
    sitename_counts['Sitename (Circle)'] = sitename_counts['Sitename'].apply(
        lambda x: f"{x} ({sitename_to_circle.get(x, '-')})"
    )

    # Fungsi buat label bulan per sitename dengan count per bulan
    def bulan_label_dengan_count(sitename):
        df_site = circle_filtered_df[circle_filtered_df['sitename'] == sitename]
        bulan_counts = df_site['bulan_label'].value_counts()
        # Sorting berdasarkan tanggal asli (handle Unknown)
        try:
            sorted_bulan = sorted(
                bulan_counts.index,
                key=lambda b: pd.to_datetime(b, format='%b %Y', errors='coerce') or pd.Timestamp('1970-01-01')
            )
        except Exception:
            sorted_bulan = list(bulan_counts.index)
        labels = [f"{bulan} ({bulan_counts[bulan]})" for bulan in sorted_bulan]
        return ', '.join(labels)

    sitename_counts['Bulan Label'] = sitename_counts['Sitename'].apply(bulan_label_dengan_count)

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
        height=600,
        margin=dict(l=150)
    )

    st.plotly_chart(fig, use_container_width=True)
