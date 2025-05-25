import os
import pandas as pd
from tkinter import Tk, filedialog

# Sembunyikan jendela utama
root = Tk()
root.withdraw()

# Dialog interaktif: pilih beberapa file Excel
file_paths = filedialog.askopenfilenames(
    title='Pilih Beberapa File Excel untuk Digabung',
    filetypes=[("Excel files", "*.xlsx *.xls")]
)

# Validasi input
if not file_paths:
    print("❌ Tidak ada file yang dipilih. Program dihentikan.")
else:
    all_data = []

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        print(f"📄 Menggabungkan file: {file_name}")
        df = pd.read_excel(file_path)
        df['Sumber_File'] = file_name  # Menambahkan kolom asal file
        all_data.append(df)

    # Gabungkan semua DataFrame
    combined_data = pd.concat(all_data, ignore_index=True)

    # Simpan hasil gabungan ke file baru
    output_dir = os.path.dirname(file_paths[0])
    output_path = os.path.join(output_dir, 'data_gabungan.xlsx')
    combined_data.to_excel(output_path, index=False)

    print(f"\n✅ Semua data berhasil digabungkan ke dalam file: {output_path}")
