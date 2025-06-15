# tab/tab99_settings.py

import shutil
import os
import stat
import streamlit as st
from utils.preprocessing import (
    load_and_cache_data,
    clean_data,
    clear_cache
)

CACHE_DIR = ".streamlit_cache"

def clear_cache():
    """Hapus semua file cache termasuk metadata."""

    def handle_remove_readonly(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    if os.path.exists(CACHE_DIR):
        try:
            shutil.rmtree(CACHE_DIR, onerror=handle_remove_readonly)
            os.makedirs(CACHE_DIR)
            print(f"✅ Cache directory '{CACHE_DIR}' berhasil dihapus dan dibuat ulang.")
        except Exception as e:
            print(f"❌ Gagal menghapus cache directory: {e}")
    else:
        os.makedirs(CACHE_DIR)
        print(f"ℹ️ Cache directory '{CACHE_DIR}' tidak ditemukan, dibuat baru.")

def settings_ui():
    st.header("⚙️ Pengaturan Aplikasi")

    if st.button("🧹 Bersihkan Cache & Reset Sesi"):
        clear_cache()  # 🔥 Hapus file cache manual
        st.cache_data.clear()  # 🔁 Hapus cache dari fungsi @st.cache_data
        st.session_state.clear()
        st.success("✅ Cache dan session berhasil dibersihkan.")
        st.rerun()

    st.caption("Cache mencakup file yang diupload dan metadata-nya.")
