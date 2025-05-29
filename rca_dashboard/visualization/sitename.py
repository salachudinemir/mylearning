import streamlit as st
import pandas as pd
import plotly.express as px

def show_sitename(filtered_df):
    if 'sitename' not in filtered_df.columns:
        st.warning("Kolom 'sitename' tidak ditemukan dalam data.")
        return

    st.markdown("## 📍 <span style='font-size:24px;'>Top Sitename dengan Repetisi Kasus Tertinggi (Minimal 3x)</span>", unsafe_allow_html=True)

    # Filter berdasarkan circle jika tersedia
    if 'circle' in filtered_df.columns:
        available_circles = sorted(filtered_df['circle'].dropna().unique())
        selected_circles = st.multiselect(
            "### Pilih Circle (opsional):",
            options=available_circles,
            default=available_circles
        )
        circle_filtered_df = filtered_df[filtered_df['circle'].isin(selected_circles)]
    else:
        st.warning("Kolom 'circle' tidak ditemukan dalam data. Menampilkan semua data.")
        circle_filtered_df = filtered_df

    sitename_counts = circle_filtered_df['sitename'].value_counts()
    sitename_counts = sitename_counts[sitename_counts >= 3].reset_index()
    sitename_counts.columns = ['Sitename', 'Jumlah Kejadian']

    if sitename_counts.empty:
        st.info("Tidak ada site dengan kejadian ≥ 3.")
        return

    sitename_to_circle = circle_filtered_df.groupby('sitename')['circle'].first().to_dict()

    sitename_counts['Sitename (Circle)'] = sitename_counts['Sitename'].apply(
        lambda x: f"{x} ({sitename_to_circle.get(x, '-')})"
    )

    def bulan_label_dengan_count(sitename):
        df_site = circle_filtered_df[circle_filtered_df['sitename'] == sitename]
        bulan_counts = df_site['bulan_label'].value_counts()
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

    all_sites = sitename_counts['Sitename (Circle)'].tolist()
    selected_sites = st.multiselect(
        "### Cari dan pilih site (opsional):",
        options=all_sites
    )

    if selected_sites:
        filtered_sites = sitename_counts[sitename_counts['Sitename (Circle)'].isin(selected_sites)]
    else:
        top_n = st.slider("Pilih Top-N Site untuk ditampilkan", min_value=5, max_value=50, value=10)
        filtered_sites = sitename_counts.head(top_n)

    fig = px.bar(
        filtered_sites,
        x='Jumlah Kejadian',
        y='Sitename (Circle)',
        orientation='h',
        text='Bulan Label',
        title="Sitename dengan Jumlah Kasus Terbanyak (≥ 3)",
        labels={'Jumlah Kejadian': 'Jumlah Kasus', 'Sitename (Circle)': 'Nama Site'}
    )
    fig.update_traces(textposition='inside', textfont_size=14)
    fig.update_layout(
        title_font_size=24,
        font=dict(size=16, color='black'),
        yaxis=dict(
            categoryorder='total ascending',
            title_font_size=18,
            tickfont_size=14
        ),
        xaxis=dict(
            title_font_size=18,
            tickfont_size=14
        ),
        height=600,
        margin=dict(l=180, r=40, t=60, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
