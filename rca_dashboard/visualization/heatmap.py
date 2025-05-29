# heatmap.py

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def show_heatmap(pivot):
    """
    Menampilkan heatmap jumlah kasus RCA vs Severity.

    Parameters:
    - pivot: pd.DataFrame, pivot table dengan index=rca, columns=severity, dan values=count
    """

    st.subheader("🔥 Heatmap RCA vs Severity")

    # Tentukan urutan severity yang diinginkan
    severity_order = ['Emergency', 'Critical', 'Major']

    # Pastikan semua severity ada, agar tidak error saat reindex
    available_severity = [s for s in severity_order if s in pivot.columns]
    pivot_sorted = pivot.reindex(columns=available_severity)

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot_sorted, annot=True, fmt='d', cmap='YlGnBu', ax=ax)

    ax.set_xlabel("Severity")
    ax.set_ylabel("RCA")
    ax.set_title("Heatmap RCA vs Severity")

    st.pyplot(fig)
