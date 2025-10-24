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

import hashlib
from datetime import datetime

# ---------- UTILITAS DASAR ----------
def hash_pw(pw: str) -> str:
    """Hash password dengan SHA256"""
    return hashlib.sha256(pw.encode()).hexdigest()


# ---------- INISIALISASI DATABASE ----------
def init_db():
    """Cek koneksi & akses tabel Supabase"""
    try:
        res = supabase.table("users").select("*").limit(1).execute()
        st.success("✅ Database Supabase aktif dan dapat diakses!")
    except Exception as e:
        st.error(f"❌ Gagal mengakses tabel users: {e}")
        st.stop()


# ---------- SEED DEMO ----------
def seed_demo():
    """Masukkan akun awal kalau tabel masih kosong"""
    try:
        users = supabase.table("users").select("*").execute().data
        if not users:
            demo_users = [
                {
                    "name": "Admin",
                    "email": "admin@example.com",
                    "password_hash": hash_pw("admin123"),
                    "role": "admin",
                },
                {
                    "name": "Dosen Fisika",
                    "email": "instructor@example.com",
                    "password_hash": hash_pw("teach123"),
                    "role": "instructor",
                },
                {
                    "name": "Zahra",
                    "email": "student@example.com",
                    "password_hash": hash_pw("learn123"),
                    "role": "student",
                },
            ]
            for u in demo_users:
                supabase.table("users").insert(u).execute()
            st.success("✅ Data demo berhasil dimasukkan ke tabel `users`.")
        else:
            st.info("ℹ️ Tabel users sudah memiliki data, skip seed demo.")
    except Exception as e:
        st.error(f"❌ Gagal menjalankan seed demo: {e}")

if __name__ == "__main__":
    init_db()
    seed_demo()
