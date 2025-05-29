import matplotlib.pyplot as plt
import seaborn as sns

def plot_restore_duration(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df['restoreduration'].dropna(), bins=30, kde=True, ax=ax)
    ax.set_xlabel("Restore Duration (minutes)")
    ax.set_title("Distribusi Durasi Pemulihan")
    return fig

def plot_incident_per_region(df):
    if df.empty or 'siteregion' not in df.columns or df['siteregion'].dropna().empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        ax.axis('off')
        return fig
    else:
        fig, ax = plt.subplots()
        df['siteregion'].value_counts().plot(kind='bar', color='skyblue', ax=ax)
        ax.set_title("Jumlah Insiden per Region")
        ax.set_xlabel("Region")
        ax.set_ylabel("Jumlah Insiden")
        return fig

def plot_sla_violation_pie(df):
    if df.empty or 'slastatus' not in df.columns or df['slastatus'].dropna().empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        ax.axis('off')
        return fig
    sla_counts = df['slastatus'].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(sla_counts, labels=sla_counts.index, autopct="%1.1f%%", startangle=90, colors=['red', 'green'])
    ax.set_title("Proporsi SLA Violation")
    return fig

def plot_by_circle(df):
    fig, ax = plt.subplots()
    if df.empty or 'circle' not in df.columns or df['circle'].dropna().empty:
        ax.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        ax.axis('off')
    else:
        df['circle'].value_counts().plot(kind='bar', color='mediumseagreen', ax=ax)
        ax.set_title("Jumlah Insiden per Circle")
        ax.set_xlabel("Circle")
        ax.set_ylabel("Jumlah Insiden")
    return fig

def plot_by_severity(df):
    fig, ax = plt.subplots()
    if df.empty or 'severity' not in df.columns or df['severity'].dropna().empty:
        ax.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        ax.axis('off')
    else:
        df['severity'].value_counts().plot(kind='bar', color='orangered', ax=ax)
        ax.set_title("Jumlah Insiden per Severity")
        ax.set_xlabel("Severity")
        ax.set_ylabel("Jumlah Insiden")
    return fig

def plot_by_alarmname(df):
    fig, ax = plt.subplots()
    if df.empty or 'alarmname' not in df.columns or df['alarmname'].dropna().empty:
        ax.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        ax.axis('off')
    else:
        df['alarmname'].value_counts().head(10).plot(kind='barh', color='steelblue', ax=ax)
        ax.set_title("Top 10 Alarm Name")
        ax.set_xlabel("Jumlah Insiden")
        ax.set_ylabel("Alarm Name")
    return fig

def plot_by_subcause(df):
    fig, ax = plt.subplots()
    if df.empty or 'subcause' not in df.columns or df['subcause'].dropna().empty:
        ax.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        ax.axis('off')
    else:
        df['subcause'].value_counts().head(10).plot(kind='bar', color='purple', ax=ax)
        ax.set_title("Top 10 Subcause")
        ax.set_xlabel("Subcause")
        ax.set_ylabel("Jumlah Insiden")
    return fig
