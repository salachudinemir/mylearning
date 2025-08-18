# tab/tab10_chabot.py

import streamlit as st
from chatbot.core import jawab_pertanyaan   # logika di core.py

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

    if "history" not in st.session_state:
        st.session_state.history = []

    if st.button("🗑️ Clear Chat History"):
        st.session_state.history = []
        st.rerun()

    def tampilkan_histori_chat():
        for msg in reversed(st.session_state.history[-5:]):
            st.chat_message("user").write(msg["user"])
            st.chat_message("assistant").write(msg["bot"])

    # Input user
    user_input = st.chat_input("Tanyakan sesuatu...")

    if user_input:
        response = jawab_pertanyaan(df, user_input)  # panggil core.py
        st.session_state.history.append({"user": user_input, "bot": response})
        if len(st.session_state.history) > 5:
            st.session_state.history = st.session_state.history[-5:]

    tampilkan_histori_chat()
