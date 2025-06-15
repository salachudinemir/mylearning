# app.py

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

def get_dynamic_height(num_points):
    if num_points <= 10:
        return 500
    elif num_points <= 50:
        return 700
    elif num_points <= 100:
        return 900
    else:
        return 1000

def main():
    st.set_page_config(layout="wide")
    st.title("📍 Peta Lokasi Network Elements (NE)")

    df = None  # Inisialisasi

    uploaded = st.file_uploader("Upload data NE (CSV/XLS/XLSX)", type=["csv", "xls", "xlsx"])
    if uploaded:
        file_type = uploaded.name.split(".")[-1].lower()

        try:
            if file_type == "csv":
                df = pd.read_csv(uploaded)
            elif file_type in ["xls", "xlsx"]:
                df = pd.read_excel(uploaded)
            else:
                st.error("Format file tidak didukung.")
                return

            df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
            df["LONG"] = pd.to_numeric(df["LONG"], errors="coerce")
            df = df.dropna(subset=["LAT", "LONG"])

        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            return

    if df is not None and not df.empty:
        st.subheader("📄 Data NE:")
        st.dataframe(df)

        # Buat peta
        m = folium.Map(location=[df["LAT"].mean(), df["LONG"].mean()], zoom_start=6)

        for _, row in df.iterrows():
            popup_text = f"<b>NE:</b> {row['NE NAME']}<br><b>SITE:</b> {row['SITE NAME']} ({row['SITE ID']})"
            folium.Marker(
                location=[row["LAT"], row["LONG"]],
                popup=popup_text,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        # Gunakan tinggi dinamis
        dynamic_height = get_dynamic_height(len(df))

        st.subheader("🗺️ Visualisasi Peta NE:")
        st_folium(m, use_container_width=True, height=dynamic_height)

    elif uploaded:
        st.warning("Data kosong atau tidak valid setelah dibersihkan.")

if __name__ == "__main__":
    main()
