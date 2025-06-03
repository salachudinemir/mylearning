import pandas as pd
import os
import argparse
from pathlib import Path
from datetime import datetime

def clean_dataframe(df):
    df.columns = df.columns.str.strip()
    for col in ['dt_id', 'createfaultfirstoccurtime', 'faultrecoverytime']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    if 'mttr' in df.columns:
        df['mttr'] = df['mttr'].astype(str).str.replace(',', '.', regex=False)
        df['mttr'] = pd.to_numeric(df['mttr'], errors='coerce')
    return df

def read_csv_large(file_path):
    print(f"📥 Membaca CSV besar: {file_path}")
    chunks = []
    try:
        for chunk in pd.read_csv(file_path, chunksize=100_000, encoding='utf-8'):
            chunk = clean_dataframe(chunk)
            chunks.append(chunk)
    except UnicodeDecodeError:
        for chunk in pd.read_csv(file_path, chunksize=100_000, encoding='latin1'):
            chunk = clean_dataframe(chunk)
            chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)
    return df

def read_excel(file_path):
    print(f"📥 Membaca Excel: {file_path}")
    df = pd.read_excel(file_path, engine='openpyxl')
    df = clean_dataframe(df)
    return df

def process_files(folder_path):
    all_data = []
    files = list(Path(folder_path).glob("*.xlsx")) + list(Path(folder_path).glob("*.xls")) + list(Path(folder_path).glob("*.csv"))

    if not files:
        print("⚠️ Tidak ada file Excel atau CSV ditemukan.")
        return

    for f in files:
        try:
            if f.suffix.lower() == '.csv':
                df = read_csv_large(f)
            else:
                df = read_excel(f)
            df['Sumber_File'] = f.name
            all_data.append(df)
            print(f"✅ Berhasil: {f.name}")
        except Exception as e:
            print(f"❌ Gagal membaca {f.name}: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        print("🔗 Menggabungkan semua data...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_excel = f"data_gabungan_{timestamp}.xlsx"
        output_csv = f"data_gabungan_{timestamp}.csv"

        combined.to_excel(output_excel, index=False)
        combined.to_csv(output_csv, index=False, encoding='utf-8-sig')

        print(f"💾 Disimpan sebagai:\n - {output_excel}\n - {output_csv}")
    else:
        print("⚠️ Tidak ada data berhasil dibaca.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gabungkan file Excel/CSV besar dalam satu folder.")
    parser.add_argument("folder", help="Path folder yang berisi file Excel/CSV")
    args = parser.parse_args()

    process_files(args.folder)
