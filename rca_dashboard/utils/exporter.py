import io
import pandas as pd
from sklearn.metrics import classification_report

def generate_excel_output(filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot, y_test, y_pred):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, sheet_name='Filtered Data', index=False)
        trend_bulanan.to_excel(writer, sheet_name='Trend Bulanan', index=False)
        total_bulanan.to_excel(writer, sheet_name='Total Bulanan', index=False)

        avg_mttr_df = avg_mttr.reset_index()
        avg_mttr_df.columns = ['RCA', 'Avg MTTR']
        avg_mttr_df.to_excel(writer, sheet_name='Avg MTTR', index=False)

        pivot.to_excel(writer, sheet_name='Pivot Severity')

        if y_test is not None and y_pred is not None:
            report_text = classification_report(y_test, y_pred, output_dict=False)
        else:
            report_text = "⚠️ Model tidak dijalankan atau tidak ada hasil prediksi karena data tidak mencukupi."

        report_lines = report_text.split('\n')
        report_df = pd.DataFrame({'Classification Report': report_lines})
        report_df.to_excel(writer, sheet_name='Classification Report', index=False)

    processed_data = output.getvalue()
    return processed_data
