# chatbot/core.py

from chatbot.helpers import (
    orderid_details,
    parse_user_input,
    extract_exact_orderid,
    filter_incidents,
    filter_incident_count,
    count_per_circle,
    count_per_circle_and_severity,
    detect_datetime_column,
    apply_time_filter
)

def get_severity_emoji(severity: str) -> str:
    """Mapping severity → emoji."""
    return {
        "Emergency": "🟥",
        "Critical": "🟧",
        "Major": "🟨",
        "Minor": "🟡",
    }.get(severity, "•")


def jawab_pertanyaan(df, user_input: str) -> str:
    """
    Fungsi utama chatbot untuk menjawab pertanyaan user berdasarkan dataframe incident.
    """

    # --- Parse user input ---
    parsed = parse_user_input(user_input)

    if not parsed or not isinstance(parsed, dict):
        return "❌ Maaf, saya tidak bisa memahami pertanyaan kamu. Coba gunakan format lain."

    # --- Ambil parameter hasil parsing ---
    orderid   = parsed.get("orderid")
    circle    = parsed.get("circle")
    rootcause = parsed.get("rootcause")
    severity  = parsed.get("severity")
    month     = parsed.get("month")
    year      = parsed.get("year")
    month_str = parsed.get("month_str", "").title()

    periode   = parsed.get("periode", "month")  # default: month
    week      = parsed.get("week")
    quarter   = parsed.get("quarter")

    # --- Label waktu ---
    if periode == "week" and week and year:
        periode_value = f"{year}-W{str(week).zfill(2)}"
        periode_label = f"Minggu ke-{week} Tahun {year}"
    elif periode == "quarter" and quarter and year:
        periode_value = f"{year}-Q{quarter}"
        periode_label = f"Kuartal {quarter} Tahun {year}"
    elif periode == "year" and year:
        periode_value = str(year)
        periode_label = f"Tahun {year}"
    else:  # default → bulan
        periode_value = f"{year}-{str(month).zfill(2)}" if year and month else None
        periode_label = f"{month_str} {year}" if year else "Periode Tidak Diketahui"

    # --- Filter waktu ---
    try:
        time_filter = apply_time_filter(df, periode, periode_value, month, year, week, quarter)
    except Exception:
        # kalau gagal deteksi kolom waktu, jangan sampai crash
        time_filter = df.index == df.index  

    # --- CASE 1: Ada OrderID ---
    if orderid:
        return orderid_details(df, orderid)

    # --- CASE 2: Rootcause + Severity + Circle ---
    if rootcause and severity and circle:
        filtered_df = df[
            time_filter &
            (df["circle"].str.lower() == circle.lower()) &
            (df["severity"].str.lower() == severity.lower()) &
            (df["rootcause"].str.lower().str.contains(rootcause.lower(), na=False))
        ]
        return (
            f"#️⃣ Total Rootcause *{rootcause.title()}* "
            f"pada *{circle.title()}* ({periode_label}) "
            f"dengan Severity *{severity.title()}*: **{len(filtered_df)}** Incident."
        )

    # --- CASE 3: Severity + Circle ---
    if severity and circle:
        filtered_df = df[
            time_filter &
            (df['circle'].str.lower() == circle.lower()) &
            (df['severity'].str.lower() == severity.lower())
        ]
        if filtered_df.empty:
            return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

        sorted_df = filtered_df.sort_values(by='createtime', ascending=False)
        top_orderids = sorted_df['orderid'].dropna().drop_duplicates().head(10).tolist()

        response = (
            f"📊 Jumlah Incident *Severity {severity.title()}* di *{circle.title()}* pada {periode_label}:\n\n"
            f"#️⃣ Total: {filtered_df['orderid'].nunique()} Incident\n\n"
        )
        if top_orderids:
            response += "📜 Last 10 Tickets:\n"
            response += "\n".join(f"{i+1}. {oid}" for i, oid in enumerate(top_orderids))
        return response.strip()

    # --- CASE 4: Circle Only ---
    if circle:
        filtered_df = df[time_filter & (df['circle'].str.lower() == circle.lower())]
        count = filtered_df['orderid'].nunique()

        desc_parts = []
        if rootcause:
            desc_parts.append(f"Rootcause *{rootcause}*")
        if severity:
            desc_parts.append(f"Severity *{severity}*")
        description = " dan ".join(desc_parts) if desc_parts else "Incident"

        return (
            f"📊 Jumlah {description} di *{circle}* pada {periode_label}:\n\n"
            f"#️⃣ Total: {count}"
        )

    # --- CASE 5: Rootcause Only ---
    if rootcause and not severity:
        filtered_df = df[time_filter & df['rootcause'].str.lower().str.contains(rootcause.lower(), na=False)]
        if filtered_df.empty:
            return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

        grouped = (
            filtered_df.groupby(['circle', 'severity'])
            .agg(Count=('orderid', 'nunique'))
            .reset_index()
        )

        total_count = grouped['Count'].sum()
        response = f"#️⃣ **Total Incident *{rootcause.title()}* di {periode_label}: {total_count}**\n\n"
        response += f"📊 Rincian Incident Rootcause *{rootcause.title()}*:\n\n"

        for circle_name, group in grouped.groupby('circle'):
            group = group.sort_values(
                by='severity',
                key=lambda x: x.map({'Emergency': 0, 'Critical': 1, 'Major': 2, 'Minor': 3})
            )
            response += f"**{circle_name.upper()}**\n\n"
            for _, row in group.iterrows():
                emoji = get_severity_emoji(row["severity"])
                response += f"{emoji} {row['severity']}: {row['Count']}\n\n"
        return response.strip()

    # --- CASE 6: Rootcause + Severity ---
    if rootcause and severity:
        filtered_df = df[
            time_filter &
            (df['severity'].str.lower() == severity.lower()) &
            (df['rootcause'].str.lower().str.contains(rootcause.lower(), na=False))
        ]
        if filtered_df.empty:
            return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

        grouped = filtered_df.groupby('circle').agg(Count=('orderid', 'nunique')).reset_index()
        response = f"📊 Jumlah Incident Rootcause *{rootcause}* dan Severity *{severity}* pada {periode_label}:\n\n"
        response += "\n".join(f"📍 {row['circle']}: {row['Count']}" for _, row in grouped.iterrows())
        return response.strip()

    # --- CASE 7: Severity Only ---
    if severity and not rootcause and not circle:
        filtered_df = df[time_filter & (df['severity'].str.lower() == severity.lower())]
        if filtered_df.empty:
            return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

        grouped = filtered_df.groupby('circle').agg(Count=('orderid', 'nunique')).reset_index()

        try:
            time_col = detect_datetime_column(df)
        except Exception:
            time_col = "createtime" if "createtime" in df.columns else None

        response = f"📊 Jumlah Incident Severity *{severity.title()}* pada {periode_label}:\n\n"
        for _, row in grouped.iterrows():
            circle_name, count = row['circle'], row['Count']
            sub_df = filtered_df[filtered_df['circle'].str.lower() == circle_name.lower()]
            if time_col:
                sub_df = sub_df.sort_values(by=time_col, ascending=False)
            orderids = sub_df['orderid'].dropna().drop_duplicates().head(10).tolist()

            emoji = get_severity_emoji(severity)
            response += f"**{circle_name.upper()}**\n\n{emoji} {severity.title()}: {count}\n\n"
            if orderids:
                response += "📜 Last 10 Tickets:\n"
                response += "\n".join(f"{i+1}. {oid}" for i, oid in enumerate(orderids))
                response += "\n\n"
        return response.strip()

    # --- DEFAULT ---
    return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."
