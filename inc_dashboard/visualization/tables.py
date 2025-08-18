# visualization/tables.py

import pandas as pd
import streamlit as st

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
    
def display_table_forecast(ts, forecast):
    # Geser tanggal forecast ke depan jika tumpang tindih dengan data historis
    if forecast.index[0] <= ts.index[-1]:
        offset = ts.index[-1] - forecast.index[0] + pd.Timedelta(days=1)
        forecast.index = forecast.index + offset

    # Buat dataframe Actual
    df_actual = pd.DataFrame({
        'Tanggal': ts.index,
        'Jumlah Gangguan': ts.values,
        'Tipe': 'Actual'
    })

    # Buat dataframe Forecast
    df_forecast = pd.DataFrame({
        'Tanggal': forecast.index,
        'Jumlah Gangguan': forecast.values,
        'Tipe': 'Forecast'
    })

    # Gabungkan Actual dan Forecast
    df_all = pd.concat([df_actual, df_forecast]).reset_index(drop=True)

    # Urutkan berdasarkan tanggal
    df_all = df_all.sort_values(by='Tanggal').reset_index(drop=True)

    # Pastikan 'Jumlah Gangguan' sebagai bilangan bulat
    df_all['Jumlah Gangguan'] = df_all['Jumlah Gangguan'].round().astype(int)

    # Hitung persentase perubahan
    df_all['Persentase Perubahan (%)'] = df_all['Jumlah Gangguan'].pct_change() * 100
    df_all['Persentase Perubahan (%)'] = df_all['Persentase Perubahan (%)'].round(2).fillna(0)

    # Tambahkan kolom Keterangan
    df_all['Keterangan'] = df_all['Tipe'].apply(
        lambda x: "Data Historis" if x == 'Actual' else "Forecast 7 Hari ke Depan"
    )

    # Format tanggal ke string
    df_all['Tanggal'] = pd.to_datetime(df_all['Tanggal']).dt.strftime('%Y-%m-%d')

    return df_all
