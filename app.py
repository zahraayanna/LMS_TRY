import streamlit as st
from supabase import create_client, Client

# --- KONFIGURASI DASAR STREAMLIT ---
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

# --- AMBIL KREDENSIAL SUPABASE DARI SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    st.write("🔍 SUPABASE_URL ditemukan:", True)
    st.write("🔍 SUPABASE_KEY ditemukan:", True)
except KeyError:
    st.error("❌ SUPABASE_URL atau SUPABASE_KEY belum ada di Secrets!")
    st.stop()

# --- BUAT CLIENT SUPABASE ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
st.success("✅ Koneksi ke Supabase berhasil dibuat!")

