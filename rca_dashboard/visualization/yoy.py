import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def show_yoy(total_bulanan):
    # Proses agregasi per kuartal
    quarterly = total_bulanan.groupby('quarter').agg({'total_count': 'sum'}).reset_index()
    quarterly['year'] = quarterly['quarter'].dt.year
    quarterly['quarter_num'] = quarterly['quarter'].dt.quarter
    quarterly['quarter_label'] = 'Q' + quarterly['quarter_num'].astype(str)

    # Pivot data
    pivot_df = quarterly.pivot(index='quarter_num', columns='year', values='total_count')
    if pivot_df.shape[1] < 2:
        st.warning("Data tidak mencukupi untuk analisis YOY.")
        return

    tahun_terakhir = pivot_df.columns.max()
    tahun_sebelumnya = tahun_terakhir - 1

    if tahun_sebelumnya not in pivot_df.columns or tahun_terakhir not in pivot_df.columns:
        st.warning("Data tahun sebelumnya atau tahun saat ini tidak lengkap.")
        return

    # Hitung YOY Growth per kuartal (tanpa visualisasi)
    pivot_df['yoy_growth_%'] = ((pivot_df[tahun_terakhir] - pivot_df[tahun_sebelumnya]) / pivot_df[tahun_sebelumnya]) * 100
    pivot_df = pivot_df.reset_index()
    pivot_df['quarter_label'] = 'Q' + pivot_df['quarter_num'].astype(str)

    # Grafik komparasi bulanan YOY
    st.subheader("📈 Komparasi Jumlah Kasus Tahun Ini vs Tahun Lalu (YOY)")
    bulan_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    total_bulanan['bulan_short'] = total_bulanan['bulan_label'].str[:3]
    total_bulanan['bulan_short'] = pd.Categorical(total_bulanan['bulan_short'], categories=bulan_order, ordered=True)

    tahun_ini = total_bulanan[total_bulanan['bulan_label'].str.endswith(str(tahun_terakhir))].copy()
    tahun_lalu = total_bulanan[total_bulanan['bulan_label'].str.endswith(str(tahun_sebelumnya))].copy()
    tahun_ini.sort_values('bulan_short', inplace=True)
    tahun_lalu.sort_values('bulan_short', inplace=True)

    fig_compare, ax_compare = plt.subplots(figsize=(12, 6))
    ax_compare.plot(tahun_lalu['bulan_short'], tahun_lalu['total_count'], marker='o', label=str(tahun_sebelumnya), color='gray')
    ax_compare.plot(tahun_ini['bulan_short'], tahun_ini['total_count'], marker='o', label=str(tahun_terakhir), color='blue')

    for x, y in zip(tahun_lalu['bulan_short'], tahun_lalu['total_count']):
        if not pd.isna(y):
            ax_compare.text(x, y + max(tahun_lalu['total_count'].max() / 50, 5), f"{int(y)}", ha='center', fontsize=9, color='gray')
    for x, y in zip(tahun_ini['bulan_short'], tahun_ini['total_count']):
        if not pd.isna(y):
            ax_compare.text(x, y + max(tahun_ini['total_count'].max() / 50, 5), f"{int(y)}", ha='center', fontsize=9, color='blue')

    ax_compare.legend()
    ax_compare.set_title("Perbandingan Jumlah Kasus Bulanan")
    ax_compare.set_ylabel("Total Count")
    ax_compare.set_xlabel("Bulan")
    st.pyplot(fig_compare)

    # Tabel komparasi YOY bulanan
    st.subheader("📊 Tabel Year-over-Year (YOY) Growth per Bulan")
    tabel_yoy = pd.merge(
        tahun_ini[['bulan_short', 'total_count']],
        tahun_lalu[['bulan_short', 'total_count']],
        on='bulan_short', how='outer',
        suffixes=(f' Tahun {tahun_terakhir}', f' Tahun {tahun_sebelumnya}')
    )

    tabel_yoy['Growth YOY (%)'] = (
        (tabel_yoy[f'total_count Tahun {tahun_terakhir}'] - tabel_yoy[f'total_count Tahun {tahun_sebelumnya}']) /
        tabel_yoy[f'total_count Tahun {tahun_sebelumnya}']
    ) * 100

    st.dataframe(tabel_yoy.style.format({
        f'total_count Tahun {tahun_terakhir}': '{:,.0f}',
        f'total_count Tahun {tahun_sebelumnya}': '{:,.0f}',
        'Growth YOY (%)': '{:.2f}%'
    }))
