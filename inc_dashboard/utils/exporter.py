import io
import pandas as pd
from sklearn.metrics import classification_report
from utils.preprocessing import drop_unwanted_columns

def save_df_to_excel(writer, df, sheet_name, index=False, empty_msg=None, rename_cols=None):
    """
    Menyimpan DataFrame ke sheet Excel.
    Jika DataFrame kosong, tampilkan pesan info.
    """
    if df is None or df.empty:
        info_msg = empty_msg or 'Data kosong / tidak tersedia.'
        info_df = pd.DataFrame({'Info': [info_msg]})
        info_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        if rename_cols:
            df = df.rename(columns=rename_cols)
        df.to_excel(writer, sheet_name=sheet_name, index=index)


def save_classification_report(writer, y_test, y_pred, sheet_name='Classification Report'):
    """
    Menyimpan classification report ke Excel sheet.
    Jika gagal atau data tidak cukup, tampilkan pesan fallback.
    """
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


def generate_excel_output(df):
    """
    Menghasilkan file Excel (bytes) dari DataFrame setelah kolom tertentu di-drop.
    """
    if df is None or df.empty:
        raise ValueError("DataFrame kosong saat akan diekspor ke Excel.")

    try:
        df_clean = drop_unwanted_columns(df)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_clean.to_excel(writer, index=False, sheet_name='Filtered Data')
        return output.getvalue()

    except Exception as e:
        raise RuntimeError(f"Gagal generate file Excel: {e}")
