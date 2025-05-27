import io
import pandas as pd
from sklearn.metrics import classification_report

def generate_excel_output(filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot, y_test, y_pred):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Hapus kolom yang tidak ingin disimpan
        cols_to_drop = ['sub_root_cause', 'subcause', 'subcause2']
        filtered_df = filtered_df.drop(columns=[col for col in cols_to_drop if col in filtered_df.columns])

        # Simpan data utama yang telah difilter
        filtered_df.to_excel(writer, sheet_name='Filtered Data', index=False)

        # Simpan trend RCA bulanan
        trend_bulanan.to_excel(writer, sheet_name='Trend Bulanan', index=False)

        # Simpan total bulanan RCA
        total_bulanan.to_excel(writer, sheet_name='Total Bulanan', index=False)

        # Simpan rata-rata MTTR per RCA (jika tersedia)
        if not avg_mttr.empty:
            avg_mttr_df = avg_mttr.reset_index()
            avg_mttr_df.columns = ['RCA', 'Avg MTTR']
            avg_mttr_df.to_excel(writer, sheet_name='Avg MTTR', index=False)
        else:
            pd.DataFrame({'Info': ['Data Avg MTTR kosong / tidak tersedia.']}).to_excel(
                writer, sheet_name='Avg MTTR', index=False
            )

        # Simpan pivot severity-RCA (jika tersedia)
        if not pivot.empty:
            pivot.to_excel(writer, sheet_name='Pivot Severity')
        else:
            pd.DataFrame({'Info': ['Pivot kosong / tidak tersedia.']}).to_excel(
                writer, sheet_name='Pivot Severity', index=False
            )

        # Simpan laporan klasifikasi model (jika tersedia)
        if y_test is not None and y_pred is not None:
            try:
                report_text = classification_report(y_test, y_pred, output_dict=False)
            except Exception as e:
                report_text = f"⚠️ Gagal membuat classification report: {e}"
        else:
            report_text = "⚠️ Model tidak dijalankan atau tidak ada hasil prediksi karena data tidak mencukupi."

        report_lines = report_text.split('\n')
        report_df = pd.DataFrame({'Classification Report': report_lines})
        report_df.to_excel(writer, sheet_name='Classification Report', index=False)

    return output.getvalue()