import streamlit as st
import hashlib
import os
import re
import io
import time
from datetime import datetime, timedelta
from supabase import create_client, Client

# ========= PAGE CONFIG (WAJIB DI ATAS SENDIRI) =========
st.set_page_config(page_title='ThinkVerse LMS', page_icon='🎓', layout='wide')

st.write("🔍 SUPABASE_URL ditemukan:", bool(SUPABASE_URL))
st.write("🔍 SUPABASE_KEY ditemukan:", bool(SUPABASE_KEY))

# ========= CEK ENVIRONMENT VARIABLE =========
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Secrets SUPABASE_URL / SUPABASE_KEY belum diset di Streamlit! Silakan buka Project → Settings → Secrets.")
    st.stop()

# ========= INISIALISASI SUPABASE =========
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========= UTILITAS DASAR =========
def hash_pw(pw: str) -> str:
    """Hash password pakai SHA-256"""
    return hashlib.sha256(pw.encode()).hexdigest()

def get_table(table_name: str):
    """Ambil tabel dari Supabase"""
    return supabase.table(table_name)

def ensure_tables():
    """Buat tabel-tabel awal di Supabase kalau belum ada"""
    try:
        # ⚠️ Supabase tidak pakai query langsung buat CREATE TABLE
        # Jadi pastikan tabel ini sudah kamu buat manual lewat Supabase Studio.
        st.info("Pastikan tabel `users`, `courses`, dan `enrollments` sudah ada di Supabase kamu.")
    except Exception as e:
        st.error(f"Error in ensure_tables: {e}")

# ========= CEK & INISIALISASI DB =========
def init_db():
    """Pastikan koneksi & tabel dasar siap"""
    try:
        users = get_table("users").select("*").limit(1).execute()
        st.session_state.db_ready = True
    except Exception as e:
        st.session_state.db_ready = False
        st.error(f"❌ Tidak bisa mengakses Supabase: {e}")
        st.stop()

# ========= SEED DEMO USERS =========
def seed_demo():
    """Tambah akun demo kalau belum ada"""
    try:
        result = get_table("users").select("*").eq("email", "admin@example.com").execute()
        if len(result.data) == 0:
            users = [
                {"name": "Admin", "email": "admin@example.com", "password_hash": hash_pw("admin123"), "role": "admin"},
                {"name": "Dosen Fisika", "email": "instructor@example.com", "password_hash": hash_pw("teach123"), "role": "instructor"},
                {"name": "Zahra", "email": "student@example.com", "password_hash": hash_pw("learn123"), "role": "student"},
            ]
            for u in users:
                get_table("users").insert(u).execute()
            st.success("✅ Demo accounts created in Supabase.")
    except Exception as e:
        st.warning(f"Gagal seed demo: {e}")







