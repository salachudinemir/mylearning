import streamlit as st
import matplotlib.pyplot as plt

def show_mttr(avg_mttr):
    # 3. MTTR Rata-rata per RCA
    st.subheader("⏱️ MTTR Rata-rata per RCA")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    avg_mttr.plot(kind='bar', ax=ax2)
    ax2.set_ylabel("MTTR (Mean)")
    ax2.set_xticklabels(avg_mttr.index, rotation=45)

    for i, val in enumerate(avg_mttr):
        ax2.text(i, val / 2, f'{val:.1f}', ha='center', va='center', fontsize=9, color='white')

    st.pyplot(fig2)
