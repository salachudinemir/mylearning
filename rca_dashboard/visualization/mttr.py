import streamlit as st
import matplotlib.pyplot as plt

def show_mttr_per_rca(avg_mttr_rca):
    # MTTR Rata-rata per RCA
    st.subheader("⏱️ MTTR Rata-rata per RCA")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    avg_mttr_rca.plot(kind='bar', ax=ax2)
    ax2.set_ylabel("MTTR (Mean)")
    ax2.set_xticklabels(avg_mttr_rca.index, rotation=45)

    for i, val in enumerate(avg_mttr_rca):
        ax2.text(i, val / 2, f'{val:.1f}', ha='center', va='center', fontsize=9, color='white')

    st.pyplot(fig2)

def show_mttr_per_circle(avg_mttr_circle):
    # MTTR Rata-rata per Circle
    st.subheader("⏱️ MTTR Rata-rata per Circle")
    fig, ax = plt.subplots(figsize=(10, 5))
    avg_mttr_circle.plot(kind='bar', ax=ax, color='steelblue')
    ax.set_ylabel("MTTR (Mean)")
    ax.set_xticklabels(avg_mttr_circle.index, rotation=45)

    for i, val in enumerate(avg_mttr_circle):
        ax.text(i, val / 2, f'{val:.1f}', ha='center', va='center', fontsize=9, color='white')

    st.pyplot(fig)

def show_mttr_per_severity(avg_mttr_severity):
    # MTTR Rata-rata per Severity
    st.subheader("⏱️ MTTR Rata-rata per Severity")
    fig, ax = plt.subplots(figsize=(8, 5))
    avg_mttr_severity.plot(kind='bar', ax=ax, color='darkorange')
    ax.set_ylabel("MTTR (Mean)")
    ax.set_xticklabels(avg_mttr_severity.index, rotation=45)

    for i, val in enumerate(avg_mttr_severity):
        ax.text(i, val / 2, f'{val:.1f}', ha='center', va='center', fontsize=9, color='white')

    st.pyplot(fig)
