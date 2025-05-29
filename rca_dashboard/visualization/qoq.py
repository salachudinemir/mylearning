import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def show_qoq(total_bulanan):
    if 'quarter' not in total_bulanan.columns:
        st.error("Data tidak mengandung kolom 'quarter' yang dibutuhkan untuk QoQ.")
        return

    # --- Proses agregasi data per kuartal ---
    quarterly = total_bulanan.groupby('quarter').agg({'total_count': 'sum'}).reset_index()
    quarterly['year'] = quarterly['quarter'].dt.year
    quarterly['quarter_num'] = quarterly['quarter'].dt.quarter
    quarterly['quarter_label'] = 'Q' + quarterly['quarter_num'].astype(str) + ' ' + quarterly['year'].astype(str)

    # Sort data untuk keperluan QoQ
    quarterly = quarterly.sort_values(by=['year', 'quarter_num']).reset_index(drop=True)

    # Hitung Growth QoQ
    quarterly['total_count_prev'] = quarterly['total_count'].shift(1)
    quarterly['growth_qoq_%'] = (
        (quarterly['total_count'] - quarterly['total_count_prev']) / quarterly['total_count_prev'] * 100
    )

    # --- Grafik QoQ Growth ---
    st.subheader("📈 Grafik Quarter-over-Quarter (QoQ) Growth per Kuartal")

    fig_qoq, ax_qoq = plt.subplots(figsize=(10, 5))
    ax_qoq.plot(quarterly['quarter_label'], quarterly['growth_qoq_%'], marker='o', linestyle='-', color='green')
    ax_qoq.axhline(0, color='gray', linestyle='--')

    for i, (x, y) in enumerate(zip(quarterly['quarter_label'], quarterly['growth_qoq_%'])):
        if not np.isnan(y):
            ax_qoq.text(i, y + max(quarterly['growth_qoq_%'].max() * 0.02, 1), f"{y:.2f}%", ha='center', fontsize=10, color='green')

    ax_qoq.set_title("QoQ Growth per Kuartal")
    ax_qoq.set_ylabel("Growth QoQ (%)")
    ax_qoq.set_xlabel("Kuartal")
    st.pyplot(fig_qoq)

    # --- Bar Chart Total Count per Kuartal ---
    st.subheader("📊 Total Count per Kuartal")

    fig_bar, ax_bar = plt.subplots(figsize=(10, 5))
    bars = ax_bar.bar(quarterly['quarter_label'], quarterly['total_count'], color='orange')

    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            ax_bar.text(bar.get_x() + bar.get_width() / 2, height - height * 0.1, f'{int(height):,}',
                        ha='center', va='bottom', color='white', fontsize=10)

    ax_bar.set_ylabel("Total Count")
    ax_bar.set_xlabel("Kuartal")
    st.pyplot(fig_bar)

    # --- Tabel Komparasi QoQ Semua Kuartal ---
    st.subheader("📊 Tabel Komparasi Semua Kuartal (QoQ)")

    if len(quarterly) < 2:
        st.warning("Data tidak cukup untuk menghitung QoQ.")
        return

    tabel_komparasi_qoq = quarterly[['quarter_label', 'total_count', 'total_count_prev', 'growth_qoq_%']].copy()
    tabel_komparasi_qoq = tabel_komparasi_qoq.rename(columns={
        'quarter_label': 'Kuartal',
        'total_count': 'Total Count',
        'total_count_prev': 'Total Count Kuartal Sebelumnya',
        'growth_qoq_%': 'Growth QoQ (%)'
    })

    tabel_komparasi_qoq['Total Count'] = tabel_komparasi_qoq['Total Count'].map('{:,.0f}'.format)
    tabel_komparasi_qoq['Total Count Kuartal Sebelumnya'] = tabel_komparasi_qoq['Total Count Kuartal Sebelumnya'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else '-')
    tabel_komparasi_qoq['Growth QoQ (%)'] = tabel_komparasi_qoq['Growth QoQ (%)'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '-')

    # HTML + CSS styling agar font lebih besar dan rapi
    st.markdown(
        """
        <style>
            .big-font-table {
                font-size: 18px;
                border-collapse: collapse;
                width: 100%;
            }
            .big-font-table th, .big-font-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .big-font-table th {
                background-color: #f2f2f2;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        tabel_komparasi_qoq.to_html(classes='big-font-table', index=False, escape=False),
        unsafe_allow_html=True
    )