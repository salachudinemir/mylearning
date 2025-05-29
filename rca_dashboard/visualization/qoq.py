import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def show_qoq(total_bulanan):
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

    # Garis horizontal nol
    ax_qoq.axhline(0, color='gray', linestyle='--')

    # Label tiap titik
    for i, (x, y) in enumerate(zip(quarterly['quarter_label'], quarterly['growth_qoq_%'])):
        if not np.isnan(y):
            ax_qoq.text(i, y + max(quarterly['growth_qoq_%'].max() * 0.02, 1), f"{y:.2f}%", ha='center', fontsize=9, color='green')

    ax_qoq.set_title("QoQ Growth per Kuartal")
    ax_qoq.set_ylabel("Growth QoQ (%)")
    ax_qoq.set_xlabel("Kuartal")

    st.pyplot(fig_qoq)

    # --- Bar Chart Total Count per Kuartal ---
    st.subheader("📊 Total Count per Kuartal")

    fig_bar, ax_bar = plt.subplots(figsize=(10, 5))
    bars = ax_bar.bar(quarterly['quarter_label'], quarterly['total_count'], color='orange')

    # Tambahkan label angka
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            ax_bar.text(bar.get_x() + bar.get_width() / 2, height - height * 0.1, f'{int(height)}',
                        ha='center', va='bottom', color='white', fontsize=9)

    ax_bar.set_ylabel("Total Count")
    ax_bar.set_xlabel("Kuartal")
    st.pyplot(fig_bar)

    # --- Tabel Komparasi QoQ Semua Kuartal ---
    st.subheader("📊 Tabel Komparasi Semua Kuartal (QoQ)")

    if len(quarterly) < 2:
        st.warning("Data tidak cukup untuk menghitung QoQ.")
    else:
        tabel_komparasi_qoq = quarterly[['quarter_label', 'total_count', 'growth_qoq_%']].copy()
        tabel_komparasi_qoq = tabel_komparasi_qoq.rename(columns={
            'quarter_label': 'Kuartal',
            'total_count': 'Total Count',
            'growth_qoq_%': 'Growth QoQ (%)'
        })

        st.dataframe(tabel_komparasi_qoq.style.format({
            'Total Count': '{:,.0f}',
            'Growth QoQ (%)': '{:.2f}%'
        }))
