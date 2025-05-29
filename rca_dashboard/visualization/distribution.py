# distribution.py

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def show_distribution(filtered_df):
    """
    Menampilkan distribusi RCA, Circle, atau Severity dari dataframe yang telah difilter.

    Parameters:
    - filtered_df: pd.DataFrame, dataframe yang sudah difilter
    """

    st.subheader("📌 Distribusi RCA, Circle, atau Severity")

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

    # Label angka di dalam bar (tengah vertikal)
    for p in countplot.patches:
        height = p.get_height()
        ax.annotate(f'{int(height)}',
                    (p.get_x() + p.get_width() / 2, height / 2),
                    ha='center', va='center',
                    fontsize=9,
                    color='white')

    plt.tight_layout()
    st.pyplot(fig)
