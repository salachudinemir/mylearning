import io
import pandas as pd
from sklearn.metrics import classification_report

def generate_excel_output(filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot, y_test, y_pred):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Filtered RCA Data')
        trend_bulanan.to_excel(writer, index=False, sheet_name='Trend RCA Bulanan')
        total_bulanan.to_excel(writer, index=False, sheet_name='YOY_QOQ Growth')
        avg_mttr.to_frame(name='Average_MTTR').to_excel(writer, sheet_name='Average MTTR')
        pivot.to_excel(writer, sheet_name='Heatmap RCA vs Severity')

        report_text = classification_report(y_test, y_pred, output_dict=False)
        report_sheet = writer.book.add_worksheet('Classification Report')
        for i, line in enumerate(report_text.split('\n')):
            report_sheet.write(i, 0, line)

    output.seek(0)
    return output

