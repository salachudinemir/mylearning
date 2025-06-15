# chatbot/helpers.py

import re
import pandas as pd

# Konversi nama bulan ke angka
MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
    "september": 9, "oktober": 10, "november": 11, "desember": 12
}

def orderid_details(df, orderid):
    required_cols = [
        'orderid', 'createtime', 'siteid', 'mccluster', 'siteregion',
        'circle', 'severity', 'rootcause', 'subcause',
        'serviceinterruptiontime', 'slastatus', 'restoreduration',
        'closetime', 'title'
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return f"❌ Kolom yang belum ada di data: {', '.join(missing_cols)}"

    row = df[df['orderid'] == orderid]
    if row.empty:
        return f"❌ Tidak ditemukan data untuk orderid '{orderid}'."

    row = row.iloc[0]

    slaviol = "Tidak"
    if pd.notna(row['slastatus']) and str(row['slastatus']).lower() == 'sla_violation':
        slaviol = "Ya"

    return (
        f"📄 Detail tiket **{orderid}**:\n"
        f"- 🕓 Create Time: {row['createtime']}\n"
        f"- 🛰️ Site ID: {row['siteid']}\n"
        f"- 🧭 MC-Cluster: {row['mccluster']}\n"
        f"- 🌐 Site Region: {row['siteregion']}\n"
        f"- 🟠 Circle: {row['circle']}\n"
        f"- 🚨 Severity: {row['severity']}\n"
        f"- 📡 Impact ke layanan: {row['serviceinterruptiontime']}\n"
        f"- 🛠️ Root Cause: {row['rootcause']}\n"
        f"- 🔎 Sub Cause: {row['subcause']}\n"
        f"- 📅 Close Time: {row['closetime']}\n"
        f"- 🏷️ Title: {row['title']}\n"
        f"- ⏱️ Restore Duration: {row['restoreduration']}\n"
        f"- ⚠️ SLA Violation: {slaviol}"
    )

def parse_user_input(user_input):
    import re

    user_input = user_input.lower()

    # Tangani orderid (misal: INC-20250102-00004500, INC2025010200004500)
    orderid = None
    orderid_match = re.search(r"(inc[-_]?\d{8}[-_]?\d{8})", user_input)
    if orderid_match:
        orderid = orderid_match.group(0).replace("-", "").replace("_", "").upper()
        return {"orderid": orderid}

    # Tangani severity
    severity_match = re.search(r"\b(emergency|critical|major|minor)\b", user_input)
    severity = severity_match.group(1).title() if severity_match else None

    # Tangani rootcause
    rootcause = None
    if "rootcause" in user_input:
        match = re.search(r"rootcause\s+([a-z0-9_]+)", user_input)
        if match:
            rootcause = match.group(1).title()

    # Tangani circle
    circle = None
    if "circle" in user_input:
        match = re.search(r"circle\s+([a-z0-9_]+)", user_input)
        if match:
            circle_word = match.group(1)
            circle = None if circle_word in ["mana", "mana saja", "semua"] else circle_word.title()

    # Tangani kuartal
    quarter_match = re.search(r"kuartal\s+(\d)", user_input)
    if quarter_match:
        quarter = int(quarter_match.group(1))
        year_match = re.search(r"(?:kuartal\s+\d\s+dari\s+)?(?:tahun\s+)?(\d{4})", user_input)
        year = int(year_match.group(1)) if year_match else None
        return {
            "severity": severity,
            "rootcause": rootcause,
            "circle": circle,
            "quarter": quarter,
            "year": year,
            "periode": "quarter"
        }

    # Tangani minggu
    week_match = re.search(r"minggu(?:\ske|-ke)?\s*(\d{1,2})", user_input)
    if week_match:
        week = int(week_match.group(1))
        year_match = re.search(r"(?:minggu\s+\d{1,2}\s+dari\s+)?(?:tahun\s+)?(\d{4})", user_input)
        year = int(year_match.group(1)) if year_match else None
        return {
            "severity": severity,
            "rootcause": rootcause,
            "circle": circle,
            "week": week,
            "year": year,
            "periode": "week"
        }

    # Tangani tahun saja
    year_only_match = re.search(r"tahun\s+(\d{4})", user_input)
    if year_only_match:
        year = int(year_only_match.group(1))
        return {
            "severity": severity,
            "rootcause": rootcause,
            "circle": circle,
            "year": year,
            "periode": "year"
        }

    # Tangani bulan dan tahun
    month_year_match = re.search(r"(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})", user_input)
    if month_year_match:
        month_str = month_year_match.group(1).lower()
        year = int(month_year_match.group(2))
        month = MONTHS.get(month_str)
        return {
            "severity": severity,
            "rootcause": rootcause,
            "circle": circle,
            "month": month,
            "month_str": month_str.title(),
            "year": year,
            "periode": "month"
        }

    return None  # Jika tidak ada pola yang terdeteksi

def extract_exact_orderid(question: str) -> str | None:
    """
    Cari dan kembalikan orderid dengan pola INC-XXXXXXXX-XXXXXXXX
    Contoh: INC-20241231-00015439
    """
    match = re.search(r'(INC-\d{8}-\d{8})', question.upper())
    return match.group(1) if match else None

# Untuk testing lokal, bukan bagian dari aplikasi
if __name__ == "__main__":
    df = pd.read_csv("data.csv")  # pastikan df didefinisikan
    user_input = "Berikan tiket INC-20250102-00004500"
    exact_orderid = extract_exact_orderid(user_input)

    if exact_orderid:
        orderid_cleaned = exact_orderid.replace("-", "")
        print(orderid_details(df, orderid_cleaned))

def filter_incidents(df, params):
    time_col = detect_datetime_column(df)
    df = df[
        (df[time_col].dt.month == params["month"]) &
        (df[time_col].dt.year == params["year"])
    ]

    if params.get("rootcause"):
        df = df[df["rootcause"].str.contains(params["rootcause"], case=False, na=False)]
    if params.get("circle"):
        df = df[df["circle"].str.contains(params["circle"], case=False, na=False)]
    if params.get("severity"):
        df = df[df["severity"].str.strip().str.lower() == params["severity"].strip().lower()]

    return df

def filter_incident_count(df, params):
    return len(filter_incidents(df, params))

def count_per_circle(df, rootcause, severity, month, year):
    time_col = detect_datetime_column(df)

    filtered = df[
        (df[time_col].dt.month == month) & 
        (df[time_col].dt.year == year)
    ]

    if severity:
        filtered = filtered[filtered['severity'].str.lower() == severity.lower()]
    if rootcause:
        filtered = filtered[filtered['rootcause'].str.lower().str.contains(rootcause.lower(), na=False)]

    result = filtered.groupby('circle').size().reset_index(name='Count')
    return result

def count_per_circle_and_severity(df, rootcause, month, year):
    time_col = detect_datetime_column(df)

    filtered = df[
        (df[time_col].dt.month == month) & 
        (df[time_col].dt.year == year)
    ]

    if rootcause:
        filtered = filtered[
            filtered['rootcause'].str.contains(rootcause, case=False, na=False)
        ]

    result = (
        filtered.groupby(['circle', 'severity'])
        .size()
        .reset_index(name='Count')
        .sort_values(['circle', 'severity'])
    )

    return result

def detect_datetime_column(df):
    possible_cols = ["createtime"]
    for col in possible_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            return col
    raise KeyError("Kolom waktu tidak ditemukan. Harap sertakan salah satu: createTime")