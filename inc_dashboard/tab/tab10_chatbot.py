# tab/tab10_chabot.py

import streamlit as st
from chatbot.helpers import (
    parse_user_input,
    filter_incident_count,
    count_per_circle,
    count_per_circle_and_severity,
    detect_datetime_column,
    extract_exact_orderid,
    orderid_details
)

def chatbot_ui():
    st.header("🤖 Chatbot Analytic Incident")

    # Ambil dataframe dari session_state
    df = st.session_state.get("df_clean", None)

    if df is None or df.empty:
        st.info("📂 Silakan upload dan proses data terlebih dahulu di tab Dashboard.")
        return
    
    required_cols = ['rootcause', 'severity', 'circle']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"❗ Kolom berikut tidak ditemukan di data: {', '.join(missing_cols)}")
        return

    if df is None or df.empty:
        st.info("📂 Silakan upload dan proses data terlebih dahulu di tab Dashboard.")
        return

    if "history" not in st.session_state:
        st.session_state.history = []

    if st.button("🗑️ Clear Chat History"):
        st.session_state.history = []
        st.rerun()

    def get_severity_emoji(severity):
        return {
            "Emergency": "🟥", "Critical": "🟧", "Major": "🟨", "Minor": "🟡"
        }.get(severity, "•")

    def tampilkan_histori_chat():
        for msg in reversed(st.session_state.history[-5:]):
            st.chat_message("user").write(msg["user"])
            st.chat_message("assistant").write(msg["bot"])

    def jawab_pertanyaan(df, parsed):
        orderid = parsed.get("orderid")
        circle = parsed.get("circle")
        rootcause = parsed.get("rootcause")
        severity = parsed.get("severity")
        month = parsed.get("month")
        year = parsed.get("year")
        month_str = parsed.get("month_str", "").title()

        # Tambahan untuk periode
        periode = parsed.get("periode", "month")  # default ke 'month'
        week = parsed.get("week")
        quarter = parsed.get("quarter")

        # Label waktu untuk ditampilkan di response
        if periode == "week" and week and year:
            week_str = str(week).zfill(2)
            period_label = f"Minggu ke-{week} Tahun {year}"
            period_filter_col = "week"
            period_filter_val = f"{year}-W{week_str}"

        elif periode == "quarter" and quarter and year:
            period_label = f"Kuartal {quarter} Tahun {year}"
            period_filter_col = "quarter"
            period_filter_val = f"{year}-Q{quarter}"

        elif periode == "year" and year:
            period_label = f"Tahun {year}"
            period_filter_col = "createtime"
            period_filter_val = year  # nanti pakai df[dt].dt.year == year

        else:  # default ke bulan
            period_label = f"{month_str} {year}"
            period_filter_col = "month"
            period_filter_val = f"{year}-{str(month).zfill(2)}"

        # Jika input berisi orderid
        if orderid:
            return orderid_details(df, orderid)
        
        # 🟡 Rootcause + Severity + Circle
        if rootcause and severity and circle:
            time_col = detect_datetime_column(df)
            filtered_df = df[
                (df[time_col].dt.month == month) &
                (df[time_col].dt.year == year) &
                (df["circle"].str.lower() == circle.lower()) &
                (df["severity"].str.lower() == severity.lower()) &
                (df["rootcause"].str.lower().str.contains(rootcause.lower(), na=False))
            ]

            return (
                f"#️⃣ Total Rootcause *{rootcause.title()}* "
                f"pada *{circle.title()}*, bulan *{month_str} {year}* "
                f"dengan Severity *{severity.title()}*: **{len(filtered_df)}** Incident."
            )

        # 🟡 Severity + Circle + Month + Year
        elif severity and circle:
            periode = parsed.get("periode", "month")  # default: month
            periode_value = None

            # Buat nilai periode_value berdasarkan parameter
            if periode == "week":
                week_str = str(parsed.get("week")).zfill(2)
                periode_value = f"{year}-W{week_str}"  # contoh: "2025-W02"
            elif periode == "month":
                periode_value = f"{year}-{str(month).zfill(2)}"  # contoh: "2025-01"
            elif periode == "quarter":
                quarter = parsed.get("quarter")
                periode_value = f"{year}-Q{quarter}"  # contoh: "2025-Q1"
            elif periode == "year":
                periode_value = str(year)
            
            # Bangun filter dinamis
            filters = (
                (df['circle'].str.lower() == circle.lower()) &
                (df['severity'].str.lower() == severity.lower())
            )
            if periode in ['week', 'month', 'quarter']:
                filters &= (df[periode] == periode_value)
            elif periode == 'year':
                filters &= (df['createtime'].dt.year == year)

            filtered_df = df[filters]

            if filtered_df.empty:
                return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

            # Urutkan dari Incident terbaru
            sorted_df = filtered_df.sort_values(by='createtime', ascending=False)

            # Ambil 10 orderid terakhir
            top_orderids = sorted_df['orderid'].dropna().drop_duplicates().head(10).tolist()

            # Nama periode untuk ditampilkan
            periode_label = {
                "week": f"Minggu {periode_value}",
                "month": f"{month_str} {year}",
                "quarter": f"Kuartal {periode_value[-1]} {year}",
                "year": f"Tahun {year}",
            }.get(periode, f"{month_str} {year}")

            response = (
                f"📊 Jumlah Incident *Severity {severity.title()}* di *{circle.title()}* pada {periode_label}:\n\n"
                f"#️⃣ Total: {filtered_df['orderid'].nunique()} Incident\n\n"
                f"📜 Last 10 Tickets:\n"
            )
            for i, oid in enumerate(top_orderids, 1):
                response += f"{i}. {oid}\n"

            return response

        # 🟡 Total count Circle (+ optional rootcause/severity)
        elif circle:
            count = filter_incident_count(df, parsed)
            desc_parts = []
            if rootcause:
                desc_parts.append(f"Rootcause *{rootcause}*")
            if severity:
                desc_parts.append(f"Severity *{severity}*")
            description = " dan ".join(desc_parts) if desc_parts else "Incident"
            return (
                f"📊 Jumlah {description} di *{circle}* pada {month_str} {year}:\n\n"
                f"#️⃣ Total: {count}"
            )

        # 🟡 Rootcause Only
        elif rootcause and not severity:
            result_df = count_per_circle_and_severity(df, rootcause, month, year)
            if result_df.empty:
                return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

            grouped = result_df.groupby('circle')
            total_count = 0

            # Hitung total count dulu
            for _, row in result_df.iterrows():
                total_count += row['Count']

            # Mulai bangun response string
            response = f"#️⃣ **Total Incident *{rootcause.title()} di {month_str} {year}*:** {total_count}\n\n"
            response += f"📊 Rincian Incident Rootcause *{rootcause.title()}* pada {month_str} {year}:\n\n"

            for circle_name, group in grouped:
                group = group.sort_values(
                    by='severity',
                    key=lambda x: x.map({'Emergency': 0, 'Critical': 1, 'Major': 2, 'Minor': 3})
                )
                response += f"**{circle_name.upper()}**\n\n"
                for _, row in group.iterrows():
                    emoji = get_severity_emoji(row["severity"])
                    response += f"{emoji} {row['severity']}: {row['Count']}\n\n"
                response += "\n"

            return response.strip()

        # 🟡 Rootcause + Severity
        elif rootcause and severity:
            result_df = count_per_circle(df, rootcause, severity, month, year)
            if result_df.empty:
                return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

            response = f"📊 Jumlah Incident Rootcause *{rootcause}* dan Severity *{severity}* pada {month_str} {year}:\n\n"
            for _, row in result_df.iterrows():
                response += f"📍 {row['circle']}: {row['Count']}\n"
            return response

        # 🟡 Severity Only
        elif severity and not rootcause and not circle:
            result_df = count_per_circle(df, rootcause=None, severity=severity, month=month, year=year)
            if result_df.empty:
                return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

            time_col = detect_datetime_column(df)
            response = f"📊 Jumlah Incident Severity *{severity.title()}* pada {month_str} {year}:\n\n"

            for _, row in result_df.iterrows():
                circle_name = row['circle']
                count = row['Count']

                filtered_df = df[
                    (df[time_col].dt.month == month) &
                    (df[time_col].dt.year == year) &
                    (df['severity'].str.lower() == severity.lower()) &
                    (df['circle'].str.lower() == circle_name.lower())
                ]

                # Urutkan berdasarkan waktu terbaru
                sorted_df = filtered_df.sort_values(by=time_col, ascending=False)
                orderids = sorted_df['orderid'].dropna().drop_duplicates().head(10).tolist()

                emoji = get_severity_emoji(severity)
                response += f"**{circle_name.upper()}**\n\n"
                response += f"{emoji} {severity.title()}: {count}\n\n"

                if orderids:
                    response += f"📜 Last 10 Tickets:\n"
                    for i, oid in enumerate(orderids, 1):
                        response += f"{i}. {oid}\n"
                response += "\n"

            return response.strip()

        # 🟥 Jika tidak ditemukan kriteria yang sesuai
        else:
            return "❗ Tidak ditemukan data yang cocok dengan kriteria tersebut."

    user_input = st.chat_input("Tanyakan sesuatu...")

    if user_input:
        parsed = parse_user_input(user_input)
        response = jawab_pertanyaan(df, parsed) if parsed else "❗ Maaf, saya belum bisa memahami pertanyaan tersebut."

        st.session_state.history.append({"user": user_input, "bot": response})
        if len(st.session_state.history) > 5:
            st.session_state.history = st.session_state.history[-5:]

    tampilkan_histori_chat()