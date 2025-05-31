import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd

def plot_incident_per_region(df):
    if 'siteregion' not in df.columns:
        return plt.figure()
    counts = df['siteregion'].value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.barh(counts.index, counts.values, color='skyblue')
    ax.set_xlabel("Jumlah Insiden")
    ax.set_title("Jumlah Insiden per Region")
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    for bar in bars:
        width = bar.get_width()
        ax.text(width - (width*0.05), bar.get_y() + bar.get_height()/2,
                f"{int(width)}", va='center', ha='right', color='black', fontweight='bold')

    return fig

def plot_incident_per_severity(df):
    if 'severity' not in df.columns:
        return plt.figure()
    counts = df['severity'].value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.barh(counts.index, counts.values, color='salmon')
    ax.set_xlabel("Jumlah Insiden")
    ax.set_title("Jumlah Insiden per Severity")
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    for bar in bars:
        width = bar.get_width()
        ax.text(width - (width*0.05), bar.get_y() + bar.get_height()/2,
                f"{int(width)}", va='center', ha='right', color='white', fontweight='bold')

    return fig

def plot_restore_duration(df):
    if 'restore_duration' not in df.columns or df.empty:
        return plt.figure()
    fig, ax = plt.subplots(figsize=(10,5))
    ax.hist(df['restore_duration'].dropna(), bins=30, color='mediumseagreen', alpha=0.7)
    ax.set_xlabel("Restore Duration")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribusi Restore Duration")
    ax.grid(True, linestyle='--', alpha=0.5)
    return fig

def plot_sla_violation_pie(df):
    if 'sla_violated' not in df.columns:
        return plt.figure()
    counts = df['sla_violated'].value_counts()
    fig, ax = plt.subplots(figsize=(6,6))
    wedges, texts, autotexts = ax.pie(counts, labels=counts.index, autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
    ax.set_title("Analisis SLA Violation")
    return fig

def plot_by_circle(df):
    if 'circle' not in df.columns:
        return plt.figure()
    counts = df['circle'].value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.barh(counts.index, counts.values, color='orchid')
    ax.set_xlabel("Jumlah Insiden")
    ax.set_title("Jumlah Insiden per Circle")
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    for bar in bars:
        width = bar.get_width()
        ax.text(width - (width*0.05), bar.get_y() + bar.get_height()/2,
                f"{int(width)}", va='center', ha='right', color='white', fontweight='bold')

    return fig

def plot_by_alarmname(df):
    if 'alarmname' not in df.columns:
        return plt.figure()
    counts = df['alarmname'].value_counts().head(15).sort_values(ascending=True)  # Top 15
    fig, ax = plt.subplots(figsize=(10,6))
    bars = ax.barh(counts.index, counts.values, color='teal')
    ax.set_xlabel("Jumlah Insiden")
    ax.set_title("Top 15 Alarm Name")
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    for bar in bars:
        width = bar.get_width()
        ax.text(width - (width*0.05), bar.get_y() + bar.get_height()/2,
                f"{int(width)}", va='center', ha='right', color='white', fontweight='bold')

    return fig

def plot_by_subcause(df):
    if 'subcause' not in df.columns:
        return plt.figure()
    counts = df['subcause'].value_counts().head(15).sort_values(ascending=True)  # Top 15
    fig, ax = plt.subplots(figsize=(10,6))
    bars = ax.barh(counts.index, counts.values, color='coral')
    ax.set_xlabel("Jumlah Insiden")
    ax.set_title("Top 15 Subcause")
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    for bar in bars:
        width = bar.get_width()
        ax.text(width - (width*0.05), bar.get_y() + bar.get_height()/2,
                f"{int(width)}", va='center', ha='right', color='black', fontweight='bold')

    return fig

def plot_by_rootcause(df):
    if 'rootcause' not in df.columns:
        return plt.figure()
    counts = df['rootcause'].value_counts().head(15).sort_values(ascending=True)  # Top 15
    fig, ax = plt.subplots(figsize=(10,6))
    bars = ax.barh(counts.index, counts.values, color='royalblue')
    ax.set_xlabel("Jumlah Insiden")
    ax.set_title("Top 15 Root Cause")
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    for bar in bars:
        width = bar.get_width()
        ax.text(width - (width*0.05), bar.get_y() + bar.get_height()/2,
                f"{int(width)}", va='center', ha='right', color='white', fontweight='bold')

    return fig

def plot_line_with_labels(series, title="", xlabel="", ylabel=""):
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(series.index, series.values, marker='o', color='dodgerblue')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.5)

    for x, y in zip(series.index, series.values):
        ax.text(x, y, str(y), ha='center', va='bottom', fontsize=9, color='black')

    fig.autofmt_xdate()
    return fig

def plot_mccluster_repetitive(filtered_df: pd.DataFrame):
    st.subheader("🏙️ Top MC Cluster Berdasarkan Jumlah Insiden")

    if 'mccluster' not in filtered_df.columns or filtered_df.empty:
        st.warning("Data MC Cluster tidak tersedia atau kosong.")
        return

    # --- Bagian 1: Top 10 MC Cluster berdasarkan jumlah insiden ---
    mc_counts = filtered_df['mccluster'].value_counts()
    top_mc_df = mc_counts.head(10).reset_index()
    top_mc_df.columns = ['MC Cluster', 'Count']

    fig, ax = plt.subplots()
    bars = ax.bar(top_mc_df['MC Cluster'], top_mc_df['Count'], color='teal')
    ax.set_xlabel("MC Cluster")
    ax.set_ylabel("Jumlah Insiden")
    ax.set_title("Top 10 MC Cluster dengan Jumlah Insiden Terbanyak")
    ax.tick_params(axis='x', rotation=45)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    st.pyplot(fig)

    # --- Bagian 2: MC Cluster dengan insiden ≥ 2 ---
    cluster_counts = mc_counts[mc_counts >= 2].reset_index()
    cluster_counts.columns = ['MC Cluster', 'Jumlah Insiden']

    if cluster_counts.empty:
        st.info("Tidak ada MC Cluster dengan jumlah insiden ≥ 2.")
        return

    # Label berdasarkan minggu
    def minggu_label_dengan_count(mccluster):
        df_cluster = filtered_df[filtered_df['mccluster'] == mccluster]
        if 'minggu_label' not in df_cluster.columns:
            return ""
        minggu_counts = df_cluster['minggu_label'].value_counts()
        try:
            sorted_minggu = sorted(
                minggu_counts.index,
                key=lambda x: pd.to_datetime(x, format='%d %b %Y', errors='coerce') or pd.Timestamp('1970-01-01')
            )
        except Exception:
            sorted_minggu = list(minggu_counts.index)
        return ', '.join([f"{m} ({minggu_counts[m]})" for m in sorted_minggu])

    cluster_counts['Minggu Label'] = cluster_counts['MC Cluster'].apply(minggu_label_dengan_count)

    st.markdown("## 🔁 MC Cluster dengan Insiden Repetitif (≥ 2)")

    all_clusters = cluster_counts['MC Cluster'].tolist()
    selected_clusters = st.multiselect("### Cari dan pilih MC Cluster (opsional):", options=all_clusters)

    if selected_clusters:
        filtered_clusters = cluster_counts[cluster_counts['MC Cluster'].isin(selected_clusters)]
    else:
        top_n = st.slider("Pilih Top-N MC Cluster untuk ditampilkan", min_value=5, max_value=50, value=10)
        filtered_clusters = cluster_counts.head(top_n)

    fig2 = px.bar(
        filtered_clusters,
        x='Jumlah Insiden',
        y='MC Cluster',
        orientation='h',
        text='Minggu Label',
        title=f"Top {len(filtered_clusters)} MC Cluster dengan Insiden ≥ 2",
        labels={'Jumlah Insiden': 'Jumlah Kasus', 'MC Cluster': 'MC Cluster'}
    )
    fig2.update_traces(textposition='inside', textfont_size=14)
    fig2.update_layout(
        title_font_size=24,
        font=dict(size=16),
        yaxis=dict(categoryorder='total ascending'),
        height=600,
        margin=dict(l=180, r=40, t=60, b=40)
    )

    st.plotly_chart(fig2, use_container_width=True)