import io
import pandas as pd
from sklearn.metrics import classification_report


def normalize_col_name(col_name):
    """
    Normalisasi nama kolom:
    - lowercase semua
    - hapus semua spasi
    - hapus underscore (_), strip juga
    """
    if not isinstance(col_name, str):
        return col_name
    return col_name.lower().replace(" ", "").replace("_", "").strip()


def drop_unwanted_columns(df, cols_to_drop):
    """
    Hapus kolom dari dataframe berdasarkan list cols_to_drop yang sudah dinormalisasi juga.
    Normalisasi nama kolom df dan cols_to_drop supaya matching lebih baik.
    """
    normalized_to_original = {normalize_col_name(col): col for col in df.columns}
    normalized_cols_to_drop = [normalize_col_name(col) for col in cols_to_drop]
    to_drop_actual = [normalized_to_original[nc] for nc in normalized_cols_to_drop if nc in normalized_to_original]

    if to_drop_actual:
        return df.drop(columns=to_drop_actual)
    return df


def save_df_to_excel(writer, df, sheet_name, index=False, empty_msg=None, rename_cols=None):
    if df is None or df.empty:
        info_msg = empty_msg or 'Data kosong / tidak tersedia.'
        info_df = pd.DataFrame({'Info': [info_msg]})
        info_df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        if rename_cols:
            df = df.rename(columns=rename_cols)
        df.to_excel(writer, sheet_name=sheet_name, index=index)


def save_classification_report(writer, y_test, y_pred, sheet_name='Classification Report'):
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

# List kolom yang mau di-drop dari export & preview drop
DROP_COLUMNS = [
    'currentoperator_1', 'createdat', 'closuretime', 'restore_duration',
    'resolve_duration', 'create_duration', 'ticketcreatedby',
    '92', '<1', '10nedownundersite14smg0266_usmanjanatin_mt,mc-semarangkotautara,java',
    'fo_ajiznurdin', '5gimpact', 'orderid_1', 'circle_id', 'subrootcause2'
]

def drop_columns(df):
    """
    Menghapus kolom-kolom tertentu dari DataFrame.
    Mengembalikan DataFrame baru tanpa kolom yang ada di DROP_COLUMNS.
    """
    cols_to_drop = [col for col in DROP_COLUMNS if col in df.columns]
    return df.drop(columns=cols_to_drop)

def generate_excel_output(df):
    """
    Menghasilkan file Excel (bytes) dari DataFrame yang sudah di-drop kolomnya.
    Fungsi ini memanggil drop_columns() otomatis.
    """
    df_clean = drop_columns(df)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Filtered Data')
    return output.getvalue()
