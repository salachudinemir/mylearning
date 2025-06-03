import json
from pathlib import Path

def baca_struktur_nama(path: Path):
    struktur = {}
    for item in path.iterdir():
        if item.is_dir():
            struktur[item.name] = baca_struktur_nama(item)
        else:
            struktur[item.name] = None  # File, tanpa isi
    return struktur

def simpan_ke_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    folder_input = input("Masukkan path folder yang ingin dieksplorasi: ").strip()
    root_path = Path(folder_input)

    if not root_path.exists() or not root_path.is_dir():
        print("Path tidak valid atau bukan folder.")
        return

    print(f"Membaca struktur folder {root_path}...")
    struktur = baca_struktur_nama(root_path)

    print(json.dumps(struktur, indent=4, ensure_ascii=False))

    file_export = input("Masukkan nama file export (misal struktur.json): ").strip()
    simpan_ke_file(struktur, file_export)
    print(f"Struktur disimpan ke {file_export}")

if __name__ == "__main__":
    main()
