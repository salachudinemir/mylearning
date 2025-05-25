import streamlit as st
from utils.preprocessing import load_and_clean_data
from utils.visualization import show_visualizations
from utils.modeling import show_model_results
from utils.exporter import generate_excel_output

st.set_page_config(page_title="RCA Dashboard", layout="wide")
st.title("📊 Dashboard Analisis Root Cause (RCA) Gangguan Jaringan")

uploaded_file = st.file_uploader("Unggah file data (CSV / Excel)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    try:
        df, filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot = load_and_clean_data(uploaded_file)

        show_visualizations(filtered_df, trend_bulanan, avg_mttr, pivot, total_bulanan)

        y_test, y_pred = show_model_results(filtered_df)

        excel_output = generate_excel_output(
            filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot, y_test, y_pred
        )

        st.download_button(
            label="💾 Unduh Semua Output (Excel)",
            data=excel_output,
            file_name="output_analisis_rca_lengkap.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
else:
    st.info("Silakan unggah file data terlebih dahulu.")

