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

def sla_violation_table(df):
    if 'slastatus' in df.columns:
        return df[df['slastatus'].str.lower() == 'sla_violation'][[
            'orderid', 'siteregion', 'rootcause', 'restoreduration'
        ]]
    else:
        return "Kolom 'slastatus' tidak ditemukan"
