import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import matplotlib.dates as mdates
import numpy as np

def plot_incident_per_circle(df):
    circle_counts = df['circle'].value_counts().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = sns.barplot(
        x=circle_counts.index,
        y=circle_counts.values,
        ax=ax,
        palette='Set2'
    )

    ax.set_title("Jumlah Insiden per Circle", fontsize=14)
    ax.set_xlabel("Circle", fontsize=12)
    ax.set_ylabel("Jumlah Insiden", fontsize=12)
    ax.tick_params(axis='x', rotation=45)

    # Tambahkan label angka di dalam batang
    for i, value in enumerate(circle_counts.values):
        ax.text(i, value / 2, str(value), ha='center', va='center', color='white', fontsize=10, fontweight='bold')

    plt.tight_layout()
    return fig

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
    col = 'restoreduration' 
    if col not in df.columns or df.empty:
        return plt.figure()

    fig, ax = plt.subplots(figsize=(10,5))

    durations = df[col].dropna()

    ax.hist(durations, bins=30, color='mediumseagreen', alpha=0.7)

    # Statistik
    mean_val = durations.mean()
    median_val = durations.median()

    ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.1f} min')
    ax.axvline(median_val, color='blue', linestyle='--', label=f'Median: {median_val:.1f} min')

    ax.set_xlabel("Restore Duration (minutes)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribusi Durasi Restore")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    return fig

# === convert menit ke jam menit untuk Restore Duration ===
def menit_to_jam_menit(menit):
    jam = int(menit // 60)
    sisa_menit = int(menit % 60)
    if jam > 0:
        return f"{jam}h {sisa_menit}m"
    else:
        return f"{sisa_menit}m"

# === Restore Duration ===
def plot_restore_duration(df):
    col = 'restoreduration' 
    if col not in df.columns or df.empty:
        return plt.figure()

    fig, ax = plt.subplots(figsize=(10,5))

    durations = df[col].dropna()

    ax.hist(durations, bins=30, color='mediumseagreen', alpha=0.7)

    # Statistik
    mean_val = durations.mean()
    median_val = durations.median()

    ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {menit_to_jam_menit(mean_val)}')
    ax.axvline(median_val, color='blue', linestyle='--', label=f'Median: {menit_to_jam_menit(median_val)}')

    ax.set_xlabel("Restore Duration (minutes)")
    ax.set_ylabel("Frequency")
    ax.set_title("Restore Duration Distribution")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    return fig

def plot_restore_duration_by_rootcause(df):
    if 'restoreduration' not in df.columns or 'rootcause' not in df.columns:
        return st.warning("Kolom 'restoreduration' atau 'rootcause' tidak tersedia.")
    
    result = df.groupby('rootcause')['restoreduration'].agg(['count', 'mean']).sort_values(by='mean', ascending=False)
    result['avg_restore_duration_formatted'] = result['mean'].apply(menit_to_jam_menit)

    st.subheader("🔍 Restore Duration Rata-rata per Root Cause (Top 10)")
    st.dataframe(result.head(10)[['count', 'avg_restore_duration_formatted']].rename(columns={'avg_restore_duration_formatted': 'Avg Restore Duration'}))

def plot_restore_duration_by_severity(df):
    if 'restoreduration' not in df.columns or 'severity' not in df.columns:
        return plt.figure()

    df = df.dropna(subset=['restoreduration', 'severity'])
    df['severity'] = df['severity'].astype(str)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    df.boxplot(column='restoreduration', by='severity', ax=ax)
    ax.set_title("Restore Duration berdasarkan Severity")
    ax.set_ylabel("Restore Duration (minutes)")  # Tetap pakai menit agar sumbu tetap akurat
    plt.suptitle("")

    # Tambahkan label mean per severity dalam jam-menit di atas boxplot (opsional)
    means = df.groupby('severity')['restoreduration'].mean()
    for i, sev in enumerate(sorted(means.index)):
        mean_val = means[sev]
        label = menit_to_jam_menit(mean_val)
        ax.text(i + 1, mean_val, label, ha='center', va='bottom', fontsize=9, color='red')

    return fig

def plot_restore_duration_by_circle(df):
    if 'restoreduration' not in df.columns or 'circle' not in df.columns:
        return st.warning("Kolom 'restoreduration' atau 'circle' tidak tersedia.")
    
    result = df.groupby('circle')['restoreduration'].agg(['count', 'mean']).sort_values(by='mean', ascending=False)
    # Tambah kolom format jam-menit
    result['avg_restore_duration_formatted'] = result['mean'].apply(menit_to_jam_menit)

    st.subheader("📍 Circle dengan Restore Duration Rata-rata Terlama")
    st.dataframe(
        result.head(10)[['count', 'avg_restore_duration_formatted']].rename(
            columns={'avg_restore_duration_formatted': 'Avg Restore Duration'}
        )
    )

def plot_combined_rootcause_severity(df):
    if {'restoreduration', 'rootcause', 'severity'}.issubset(df.columns):
        combo = df.groupby(['rootcause', 'severity'])['restoreduration'].agg(['count', 'mean'])
        combo = combo.sort_values(by='mean', ascending=False).head(10)
        combo['avg_restore_duration_formatted'] = combo['mean'].apply(menit_to_jam_menit)

        st.subheader("🔗 Kombinasi Rootcause dan Severity dengan Restore Duration Terlama")
        st.dataframe(
            combo[['count', 'avg_restore_duration_formatted']].rename(
                columns={'avg_restore_duration_formatted': 'Avg Restore Duration'}
            )
        )

def plot_sla_violation_pie(df):
    if 'slastatus' not in df.columns:
        return plt.figure()

    # Mapping nilai agar lebih jelas
    status_mapping = {
        'sla_violation': 'Violated',
        'normal': 'Met'
    }

    status_series = df['slastatus'].map(status_mapping)

    counts = status_series.value_counts()

    if len(counts) == 0:
        return plt.figure()
    elif len(counts) == 1:
        # Tambahkan kategori dummy supaya pie chart tetap bisa ditampilkan
        dummy_label = 'Met' if 'Violated' in counts.index else 'Violated'
        counts[dummy_label] = 0

    fig, ax = plt.subplots(figsize=(6,6))
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=counts.index,
        autopct='%1.1f%%',
        colors=["#99ffb1", "#ff0755"]
    )
    ax.set_title("Analisis SLA Violation")
    fig.tight_layout()
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

    # --- Bagian 2: MC Cluster dengan insiden ≥ 3 ---
    cluster_counts = mc_counts[mc_counts >= 3].reset_index()
    cluster_counts.columns = ['MC Cluster', 'Jumlah Insiden']

    if cluster_counts.empty:
        st.info("Tidak ada MC Cluster dengan jumlah insiden ≥ 3.")
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

    st.markdown("## 🔁 MC Cluster dengan Insiden Repetitif (≥ 3)")

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
        title=f"Top {len(filtered_clusters)} MC Cluster dengan Insiden ≥ 3",
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

def plot_siteid_repetitive(filtered_df: pd.DataFrame):
    if 'siteid' not in filtered_df.columns or filtered_df.empty:
        st.warning("Data Site ID tidak tersedia atau kosong.")
        return

    # --- Bagian 1: Top 10 Site ID berdasarkan jumlah insiden ---
    site_counts = filtered_df['siteid'].value_counts()
    top_site_df = site_counts.head(10).reset_index()
    top_site_df.columns = ['Site ID', 'Count']

    fig, ax = plt.subplots()
    bars = ax.bar(top_site_df['Site ID'], top_site_df['Count'], color='darkorange')
    ax.set_xlabel("Site ID")
    ax.set_ylabel("Jumlah Insiden")
    ax.set_title("Top 10 Site ID dengan Jumlah Insiden Terbanyak")
    ax.tick_params(axis='x', rotation=45)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    st.pyplot(fig)

    # --- Bagian 2: Site ID dengan insiden ≥ 3 ---
    repetitive_counts = site_counts[site_counts >= 3].reset_index()
    repetitive_counts.columns = ['Site ID', 'Jumlah Insiden']

    if repetitive_counts.empty:
        st.info("Tidak ada Site ID dengan jumlah insiden ≥ 3.")
        return

    # Label berdasarkan minggu
    def minggu_label_siteid(siteid):
        df_site = filtered_df[filtered_df['siteid'] == siteid]
        if 'minggu_label' not in df_site.columns:
            return ""
        minggu_counts = df_site['minggu_label'].value_counts()
        try:
            sorted_minggu = sorted(
                minggu_counts.index,
                key=lambda x: pd.to_datetime(x, format='%d %b %Y', errors='coerce') or pd.Timestamp('1970-01-01')
            )
        except Exception:
            sorted_minggu = list(minggu_counts.index)
        return ', '.join([f"{m} ({minggu_counts[m]})" for m in sorted_minggu])

    repetitive_counts['Minggu Label'] = repetitive_counts['Site ID'].apply(minggu_label_siteid)

    st.markdown("## 📍 Site ID dengan Insiden Repetitif (≥ 3)")

    all_sites = repetitive_counts['Site ID'].tolist()
    selected_sites = st.multiselect("### Cari dan pilih Site ID (opsional):", options=all_sites)

    if selected_sites:
        filtered_sites = repetitive_counts[repetitive_counts['Site ID'].isin(selected_sites)]
    else:
        top_n = st.slider("Pilih Top-N Site ID untuk ditampilkan", min_value=5, max_value=50, value=10)
        filtered_sites = repetitive_counts.head(top_n)

    fig2 = px.bar(
        filtered_sites,
        x='Jumlah Insiden',
        y='Site ID',
        orientation='h',
        text='Minggu Label',
        title=f"Top {len(filtered_sites)} Site ID dengan Insiden ≥ 3",
        labels={'Jumlah Insiden': 'Jumlah Kasus', 'Site ID': 'Site ID'}
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

def plot_forecast(ts, forecast, interactive=False, start_date=None, end_date=None, title="📈 Forecast Gangguan Mingguan"):

    # Cek dan geser forecast index jika overlap dengan actual
    if (forecast is not None) and (len(forecast) > 0) and (forecast.index[0] <= ts.index[-1]):
        offset = (ts.index[-1] - forecast.index[0]) + pd.Timedelta(days=1)
        forecast.index = forecast.index + offset

    # Filter actual time series berdasarkan start_date dan end_date (jika diberikan)
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        ts = ts[(ts.index >= start_date) & (ts.index <= end_date)]
        # Jangan filter forecast agar tetap lengkap ditampilkan

    if interactive:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts.index, y=ts.values,
            mode='lines+markers+text',
            name='Actual',
            text=[str(int(val)) for val in ts.values],
            textposition='top center',
            marker=dict(color='blue'),
            line=dict(color='blue'),
            hovertemplate='Tanggal: %{x}<br>Jumlah Gangguan: %{y}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=forecast.index, y=forecast.values,
            mode='lines+markers+text',
            name='Forecast',
            text=[str(int(val)) for val in forecast.values],
            textposition='top center',
            marker=dict(color='red'),
            line=dict(color='red', dash='dash'),
            hovertemplate='Tanggal: %{x}<br>Forecast Gangguan: %{y}<extra></extra>'
        ))
        fig.update_layout(
            title=title,
            xaxis_title='Tanggal',
            yaxis_title='Jumlah Gangguan',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(
                tickformat='%Y-%m-%d',
                tickangle=45
            )
        )
        return fig
    else:
        fig, ax = plt.subplots(figsize=(12, 5))
        ts.plot(ax=ax, label="Actual", marker='o', color='blue')
        forecast.plot(ax=ax, label="Forecast", linestyle='--', marker='o', color='red')

        y_max = max(ts.max(), forecast.max())
        for x, y in zip(ts.index, ts.values):
            ax.text(x, y + y_max * 0.02, f"{int(y)}", ha='center', fontsize=8, color='blue')
        for x, y in zip(forecast.index, forecast.values):
            ax.text(x, y + y_max * 0.02, f"{int(y)}", ha='center', fontsize=8, color='red')

        ax.set_title(title)
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Jumlah Gangguan")
        ax.legend()
        ax.grid(True)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        return fig