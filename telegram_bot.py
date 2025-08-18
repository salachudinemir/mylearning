# chatbot/telegram_bot.py

import logging
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from chatbot.core import jawab_pertanyaan  # fungsi utama chatbot
from utils.preprocessing import load_cached_dataframe_if_any

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Load df langsung dari pickle ===
df = None
try:
    df = pd.read_pickle("df_clean.pkl")
    logger.info(f"✅ Data dimuat otomatis dari df_clean.pkl, total {len(df)} baris.")
except Exception as e:
    logger.warning(f"⚠️ Tidak menemukan df_clean.pkl: {e}")

# === Load df dari cache Streamlit (fallback) ===
if df is None:
    try:
        df = load_cached_dataframe_if_any()
        if df is not None:
            logger.info(f"✅ Data dimuat otomatis dari cache, total {len(df)} baris.")
        else:
            logger.warning("⚠️ Tidak ada data di cache. Upload dulu file via Streamlit.")
    except Exception as e:
        logger.error(f"❌ Gagal memuat data dari cache: {e}")

# === Normalisasi nama kolom agar konsisten (lowercase + strip) ===
if df is not None:
    df.columns = df.columns.str.strip().str.lower()
    logger.info(f"📑 Kolom dataframe: {list(df.columns)}")
    logger.info(f"📊 Contoh data:\n{df.head(3).to_string()}")

# === Command: /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if df is None or df.empty:
        await update.message.reply_text("❗ Data belum tersedia (df kosong atau tidak ditemukan).")
    else:
        await update.message.reply_text(
            "🤖 Halo! Saya Chatbot Incident Analytic.\n"
            "Silakan tanya sesuatu!"
        )

# === Handler pesan biasa ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if df is None or df.empty:
        await update.message.reply_text("❗ Data incident belum tersedia.")
        return

    user_input = update.message.text
    try:
        response = jawab_pertanyaan(df, user_input)
    except Exception as e:
        logger.exception("Error saat memproses pertanyaan")
        response = f"⚠️ Terjadi error: {type(e).__name__} → {e}"

    await update.message.reply_text(response, parse_mode="Markdown")

# === Main Runner ===
if __name__ == "__main__":
    
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
