import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def show_visualizations(filtered_df, trend_bulanan, avg_mttr, pivot, total_bulanan):
    st.subheader("📈 Trend Distribusi RCA per Bulan")
    fig_trend, ax_trend = plt.subplots(figsize=(12, 6))
    for rca_type in trend_bulanan['rca'].unique():
        data_plot = trend_bulanan[trend_bulanan['rca'] == rca_type]
        ax_trend.plot(data_plot['bulan_label'], data_plot['count'], marker='o', label=rca_type)
    ax_trend.set_xlabel("Bulan")
    ax_trend.set_ylabel("Jumlah Kasus RCA")
    ax_trend.set_title("Trend RCA per Bulan")
    ax_trend.legend(title='RCA', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig_trend)

    st.subheader("📌 Distribusi RCA")
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    countplot = sns.countplot(data=filtered_df, x='rca', order=filtered_df['rca'].value_counts().index, ax=ax1)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
    for p in countplot.patches:
        ax1.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=9)
    st.pyplot(fig1)

    st.subheader("⏱️ MTTR Rata-rata per RCA")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    avg_mttr.plot(kind='bar', ax=ax2)
    ax2.set_ylabel("MTTR (Mean)")
    ax2.set_xticklabels(avg_mttr.index, rotation=45)
    for i, val in enumerate(avg_mttr):
        ax2.text(i, val, f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    st.pyplot(fig2)

    st.subheader("🔥 Heatmap RCA vs Severity")
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=True, fmt='d', cmap='YlGnBu', ax=ax3)
    st.pyplot(fig3)

    st.subheader("📉 Grafik Year-over-Year (YOY) Growth per Bulan")
    fig_yoy, ax_yoy = plt.subplots(figsize=(12, 6))
    ax_yoy.plot(total_bulanan['bulan_label'], total_bulanan['yoy_growth_%'], marker='o', linestyle='-')
    ax_yoy.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax_yoy.set_xlabel("Bulan")
    ax_yoy.set_ylabel("YOY Growth (%)")
    ax_yoy.set_title("Trend YOY Growth Kasus per Bulan")
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(fig_yoy)

    st.subheader("📉 Grafik Quarter-over-Quarter (QOQ) Growth per Bulan")
    fig_qoq, ax_qoq = plt.subplots(figsize=(12, 6))
    ax_qoq.plot(total_bulanan['bulan_label'], total_bulanan['qoq_growth_%'], marker='o', linestyle='-', color='orange')
    ax_qoq.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax_qoq.set_xlabel("Bulan")
    ax_qoq.set_ylabel("QOQ Growth (%)")
    ax_qoq.set_title("Trend QOQ Growth Kasus per Bulan")
    plt.xticks(rotation=45)
    plt.grid(True)
    st.pyplot(fig_qoq)

    # Tambahan: Komparasi Tahun Ini vs Tahun Lalu (Jumlah Kasus per Bulan)
    st.subheader("📈 Komparasi Jumlah Kasus Tahun Ini vs Tahun Lalu (YOY)")
    tahun_terakhir = total_bulanan['bulan_label'].iloc[-1].split()[-1]  # ambil tahun terakhir dari label bulan
    tahun_terakhir = int(tahun_terakhir)

    tahun_ini = total_bulanan[total_bulanan['bulan_label'].str.endswith(str(tahun_terakhir))].copy()
    tahun_lalu = total_bulanan[total_bulanan['bulan_label'].str.endswith(str(tahun_terakhir - 1))].copy()

    # Ekstrak nama bulan untuk sorting kronologis
    bulan_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    tahun_ini['bulan_short'] = tahun_ini['bulan_label'].str[:3]
    tahun_ini['bulan_short'] = pd.Categorical(tahun_ini['bulan_short'], categories=bulan_order, ordered=True)
    tahun_lalu['bulan_short'] = tahun_lalu['bulan_label'].str[:3]
    tahun_lalu['bulan_short'] = pd.Categorical(tahun_lalu['bulan_short'], categories=bulan_order, ordered=True)

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
