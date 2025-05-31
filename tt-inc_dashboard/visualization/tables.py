import pandas as pd

def top_rootcause_table(df, n=10):
    if 'rootcause' in df.columns:
        return (
            df['rootcause']
            .value_counts()
            .head(n)
            .reset_index()
            .rename(columns={'index': 'Rootcause', 'rootcause': 'Count'})
        )
    else:
        return "Kolom 'rootcause' tidak ditemukan"

def top_subcause_table(df, n=10):
    if 'subcause' in df.columns:
        return (
            df['subcause']
            .value_counts()
            .head(n)
            .reset_index()
            .rename(columns={'index': 'Subcause', 'subcause': 'Count'})
        )
    else:
        return "Kolom 'subcause' tidak ditemukan"
    
def top_rootcause_subcause_table(df, n_rootcause=5, n_subcause=5):
    if 'rootcause' in df.columns and 'subcause' in df.columns:
        top_roots = df['rootcause'].value_counts().head(n_rootcause).index.tolist()
        df_filtered = df[df['rootcause'].isin(top_roots)]

        grouped = (
            df_filtered.groupby(['rootcause', 'subcause'])
            .size()
            .reset_index(name='Count')
            .sort_values(['rootcause', 'Count'], ascending=[True, False])
        )

        # Ambil N subcause teratas per rootcause
        top_subs_per_root = (
            grouped.groupby('rootcause')
            .head(n_subcause)
            .reset_index(drop=True)
        )

        return top_subs_per_root
    else:
        return "Kolom 'rootcause' atau 'subcause' tidak ditemukan"

def sla_violation_table(df):
    if 'slastatus' in df.columns:
        return df[df['slastatus'].str.lower() == 'sla_violation'][[
            'orderid', 'siteregion', 'rootcause', 'restoreduration'
        ]]
    else:
        return "Kolom 'slastatus' tidak ditemukan"

def top_mccluster_table(df, n=10):
    if 'mccluster' in df.columns:
        return (
            df['mccluster']
            .value_counts()
            .head(n)
            .reset_index()
            .rename(columns={'index': 'MC Cluster', 'mccluster': 'Count'})
        )
    else:
        return "Kolom 'mccluster' tidak ditemukan"