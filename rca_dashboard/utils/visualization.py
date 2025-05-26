import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import plotly.express as px

def show_visualizations(filtered_df, avg_mttr, pivot, total_bulanan):
    # 1. Visualisasi Sitename dengan Repetisi Tinggi
    if 'sitename' not in filtered_df.columns:
        st.warning("Kolom 'sitename' tidak ditemukan dalam data.")
    else:
        st.subheader("📍 Top Sitename dengan Repetisi Kasus Tertinggi")
        sitename_counts = filtered_df['sitename'].value_counts().reset_index()
        sitename_counts.columns = ['Sitename', 'Jumlah Kejadian']

        top_n = st.slider("Pilih Top-N Site untuk ditampilkan", min_value=5, max_value=50, value=10)
        top_sites = sitename_counts.head(top_n)

        fig = px.bar(
            top_sites,
            x='Jumlah Kejadian',
            y='Sitename',
            orientation='h',
            title=f"Top {top_n} Sitename dengan Jumlah Kasus Terbanyak",
            labels={'Jumlah Kejadian': 'Jumlah Kasus', 'Sitename': 'Nama Site'}
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)

    # 2. Visualisasi Distribusi RCA
    if 'rca' not in filtered_df.columns:
        st.warning("Kolom 'rca' tidak ditemukan dalam data.")
    else:
        st.subheader("📌 Distribusi RCA")
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        order_rca = filtered_df['rca'].value_counts().index
        sns.countplot(data=filtered_df, x='rca', order=order_rca, ax=ax1)
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
        for p in ax1.patches:
            height = p.get_height()
            ax1.annotate(f'{int(height)}', (p.get_x() + p.get_width()/2, height),
                         ha='center', va='bottom', fontsize=9)
        st.pyplot(fig1)

    # 3. MTTR rata-rata per RCA
    if avg_mttr is None or len(avg_mttr) == 0:
        st.warning("Data rata-rata MTTR tidak tersedia.")
    else:
        st.subheader("⏱️ MTTR Rata-rata per RCA")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        avg_mttr.plot(kind='bar', ax=ax2, color='skyblue')
        ax2.set_ylabel("MTTR (Mean)")
        ax2.set_xticklabels(avg_mttr.index, rotation=45)
        for i, val in enumerate(avg_mttr):
            ax2.text(i, val, f'{val:.1f}', ha='center', va='bottom', fontsize=9)
        st.pyplot(fig2)

    # 4. Heatmap RCA vs Severity
    if pivot is None or pivot.empty:
        st.warning("Data pivot RCA vs Severity tidak tersedia.")
    else:
        st.subheader("🔥 Heatmap RCA vs Severity")

        severity_order = ['Emergency', 'Critical', 'Major']

        # Reindex dengan fill_value=0 dan pastikan numeric
        pivot_sorted = pivot.reindex(index=severity_order, columns=severity_order, fill_value=0)
        pivot_sorted = pivot_sorted.apply(pd.to_numeric, errors='coerce').fillna(0)

        fig3, ax3 = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot_sorted, annot=True, fmt='.0f', cmap='YlGnBu', ax=ax3)
        ax3.set_xlabel("Severity")
        ax3.set_ylabel("RCA")
        st.pyplot(fig3)

    # 5. Visualisasi QOQ Growth per Kuartal
    if total_bulanan is None or total_bulanan.empty:
        st.warning("Data total bulanan tidak tersedia.")
    else:
        st.subheader("📉 Grafik Quarter-over-Quarter (QOQ) Growth per Kuartal")

        # Pastikan kolom quarter dan total_count ada dan quarter bertipe datetime
        if 'quarter' not in total_bulanan.columns or 'total_count' not in total_bulanan.columns:
            st.warning("Kolom 'quarter' dan/atau 'total_count' tidak ditemukan di total_bulanan.")
        else:
            total_bulanan['quarter'] = pd.to_datetime(total_bulanan['quarter'])
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

            # Tabel QOQ Growth
            st.subheader("📊 Tabel Quarter-over-Quarter (QOQ) Growth per Kuartal")
            tabel_qoq = pd.merge(
                data_tahun_ini[['quarter_label', 'total_count', 'qoq_growth_%']],
                data_tahun_lalu[['quarter_label', 'total_count', 'qoq_growth_%']],
                on='quarter_label',
                how='outer',
                suffixes=(f' Tahun {tahun_terakhir}', f' Tahun {tahun_terakhir - 1}')
            ).fillna('-')

            st.dataframe(tabel_qoq.style.format({
                f'total_count Tahun {tahun_terakhir}': '{:,.0f}',
                f'qoq_growth_% Tahun {tahun_terakhir}': '{:.2f}%',
                f'total_count Tahun {tahun_terakhir - 1}': '{:,.0f}',
                f'qoq_growth_% Tahun {tahun_terakhir - 1}': '{:.2f}%'
            }))

    # 6. Visualisasi YOY Growth per Bulan
    if total_bulanan is None or total_bulanan.empty or 'bulan_label' not in total_bulanan.columns:
        st.warning("Data total bulanan untuk YOY tidak tersedia atau kolom 'bulan_label' hilang.")
    else:
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
            / tabel_yoy[f'total_count Tahun {tahun_terakhir - 1}'].replace(0, np.nan)
        ) * 100

        tabel_yoy.replace([np.inf, -np.inf], np.nan, inplace=True)

        st.dataframe(tabel_yoy.style.format({
            f'total_count Tahun {tahun_terakhir}': '{:,.0f}',
            f'total_count Tahun {tahun_terakhir - 1}': '{:,.0f}',
            'Growth YOY (%)': '{:.2f}%'
        }))
