import io
import pandas as pd
from sklearn.metrics import classification_report


def drop_unwanted_columns(df, cols_to_drop):
    """Hapus kolom yang tidak diinginkan jika ada di dataframe."""
    return df.drop(columns=[col for col in cols_to_drop if col in df.columns])


def save_df_to_excel(writer, df, sheet_name, index=False, empty_msg=None, rename_cols=None):
    """Simpan dataframe ke sheet Excel, atau simpan pesan jika df kosong."""
    if df is None or df.empty:
        info_df = pd.DataFrame({'Info': [empty_msg or 'Data kosong / tidak tersedia.']})
        info_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        if rename_cols:
            df = df.rename(columns=rename_cols)
        df.to_excel(writer, sheet_name=sheet_name, index=index)


def save_classification_report(writer, y_test, y_pred, sheet_name='Classification Report'):
    """Generate dan simpan classification report ke Excel."""
    if y_test is not None and y_pred is not None:
        try:
            report_text = classification_report(y_test, y_pred, output_dict=False)
        except Exception as e:
            report_text = f"⚠️ Gagal membuat classification report: {e}"
    else:
        report_text = "⚠️ Model tidak dijalankan atau tidak ada hasil prediksi karena data tidak mencukupi."

    report_lines = report_text.split('\n')
    report_df = pd.DataFrame({sheet_name: report_lines})
    report_df.to_excel(writer, sheet_name=sheet_name, index=False)


def generate_excel_output(filtered_df, trend_bulanan, total_bulanan, avg_mttr, pivot, y_test, y_pred):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Drop kolom yang tidak perlu simpan
        filtered_df_clean = drop_unwanted_columns(filtered_df, ['sub_root_cause', 'subcause', 'subcause2'])
        save_df_to_excel(writer, filtered_df_clean, 'Filtered Data', index=False)
        save_df_to_excel(writer, trend_bulanan, 'Trend Bulanan', index=False)
        save_df_to_excel(writer, total_bulanan, 'Total Bulanan', index=False)
        save_df_to_excel(writer, avg_mttr.reset_index() if not avg_mttr.empty else None,
                         'Avg MTTR', index=False, empty_msg='Data Avg MTTR kosong / tidak tersedia.',
                         rename_cols={'index': 'RCA', 0: 'Avg MTTR'})
        save_df_to_excel(writer, pivot, 'Pivot Severity', empty_msg='Pivot kosong / tidak tersedia.')

        save_classification_report(writer, y_test, y_pred)

    return output.getvalue()
