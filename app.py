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

import time

# ========= AUTENTIKASI DASAR =========
def login(email, pw):
    """Login user dari Supabase"""
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if len(res.data) == 0:
            return None
        user = res.data[0]
        if user["password_hash"] == hash_pw(pw):
            return user
    except Exception as e:
        st.error(f"Login error: {e}")
    return None


def register_user(name, email, pw, role):
    """Daftarkan user baru"""
    try:
        user = {
            "name": name.strip(),
            "email": email.strip(),
            "password_hash": hash_pw(pw),
            "role": role,
        }
        supabase.table("users").insert(user).execute()
        return True
    except Exception as e:
        st.error(f"Gagal daftar: {e}")
        return False


def reset_password(email, new_pw):
    """Reset password lewat tab 'Lupa Password'"""
    hashed = hash_pw(new_pw)
    try:
        supabase.table("users").update({"password_hash": hashed}).eq("email", email).execute()
        return True
    except Exception as e:
        st.error(f"Gagal reset password: {e}")
        return False


# ========= HALAMAN LOGIN =========
def page_login():
    st.title("🎓 ThinkVerse LMS — Login Portal")
    st.caption("Masuk untuk melanjutkan ke ruang belajar digital kamu.")

    tabs = st.tabs(["🔑 Login", "🆕 Register", "🔁 Lupa Password"])

    # --- LOGIN ---
    with tabs[0]:
        with st.form("login_form_tab1"):
            email = st.text_input("Email", key="login_email_tab1")
            pw = st.text_input("Password", type="password", key="login_pw_tab1")
            ok = st.form_submit_button("Masuk")
        if ok:
            u = login(email, pw)
            if u:
                st.session_state.user = u
                st.success(f"Selamat datang, {u['name']} 👋")
                time.sleep(0.7)
                st.rerun()
            else:
                st.error("Email atau password salah.")

    # --- REGISTER ---
    with tabs[1]:
        with st.form("reg_form_tab2"):
            name = st.text_input("Nama Lengkap", key="reg_name_tab2")
            email = st.text_input("Email", key="reg_email_tab2")
            pw = st.text_input("Password", type="password", key="reg_pw_tab2")
            role = st.selectbox("Peran", ["student", "instructor"], key="reg_role_tab2")
            ok2 = st.form_submit_button("Daftar Akun Baru")
        if ok2:
            if register_user(name, email, pw, role):
                st.success("Akun berhasil dibuat! Silakan login di tab pertama.")

    # --- LUPA PASSWORD ---
    with tabs[2]:
        with st.form("forgot_pw_form_tab3"):
            email_fp = st.text_input("Masukkan email kamu", key="fp_email_tab3")
            new_pw = st.text_input("Password baru", type="password", key="fp_pw_tab3")
            new_pw2 = st.text_input("Ulangi password baru", type="password", key="fp_pw2_tab3")
            ok3 = st.form_submit_button("Reset Password")
        if ok3:
            if new_pw != new_pw2:
                st.error("Password tidak sama.")
            elif reset_password(email_fp, new_pw):
                st.success("Password berhasil direset! Silakan login ulang.")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    page_login()
else:
    st.success(f"Sudah login sebagai {st.session_state.user['name']} ({st.session_state.user['role']})")

# =========================================
# ============= DASHBOARD ================
# =========================================

def sidebar_nav():
    """Sidebar utama LMS"""
    u = st.session_state.user
    st.sidebar.title("📚 ThinkVerse LMS")
    if u:
        st.sidebar.markdown(f"**{u['name']}**")
        st.sidebar.caption(f"({u['role']}) - {u['email']}")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()

    section = st.sidebar.radio("Navigasi", ["🏠 Beranda", "📘 Kursus Saya", "👤 Akun"])
    return section


# ---------- GET COURSES ----------
def get_courses_for_user(user_id, role):
    """Ambil daftar kursus dari Supabase"""
    if role == "student":
        res = supabase.table("enrollments").select("course_id, courses(title,code,description,instructor_id)").eq("user_id", user_id).execute()
        return [r["courses"] for r in res.data] if res.data else []
    else:
        res = supabase.table("courses").select("*").eq("instructor_id", user_id).execute()
        return res.data


# ---------- PAGE HOME ----------
def page_home():
    u = st.session_state.user
    st.title(f"Selamat datang, {u['name']} 👋")
    st.write("ThinkVerse LMS adalah platform pembelajaran digital interaktif.")
    st.info("Gunakan sidebar untuk navigasi ke kursus atau profil kamu.")


# ---------- PAGE COURSES ----------
def page_courses():
    u = st.session_state.user
    st.header("📘 Kursus Saya")

    # Bagian 1 — daftar kursus user
    courses = get_courses_for_user(u["id"], u["role"])
    if not courses:
        st.warning("Belum ada kursus.")
    else:
        for c in courses:
            st.markdown(f"### {c['title']}")
            st.caption(f"Kode: {c['code']}")
            st.write(c.get("description") or "-")
            st.divider()

    # Bagian 2 — instruktur bisa buat kursus
    if u["role"] in ["instructor", "admin"]:
        st.subheader("➕ Buat Kursus Baru")
        with st.form("new_course"):
            code = st.text_input("Kode Kursus (unik)")
            title = st.text_input("Judul Kursus")
            desc = st.text_area("Deskripsi Kursus")
            ok = st.form_submit_button("Buat Kursus")
        if ok and code and title:
            try:
                supabase.table("courses").insert({
                    "code": code,
                    "title": title,
                    "description": desc,
                    "instructor_id": u["id"],
                }).execute()
                st.success("Kursus berhasil dibuat!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal membuat kursus: {e}")

    # Bagian 3 — siswa bisa join
    if u["role"] == "student":
        st.subheader("🔑 Gabung ke Kursus")
        with st.form("join_course"):
            code = st.text_input("Masukkan Kode Kursus")
            ok = st.form_submit_button("Gabung")
        if ok and code:
            res = supabase.table("courses").select("id").eq("code", code).execute()
            if res.data:
                cid = res.data[0]["id"]
                supabase.table("enrollments").insert({
                    "user_id": u["id"],
                    "course_id": cid,
                    "role": "student",
                }).execute()
                st.success("Berhasil bergabung ke kursus!")
                st.rerun()
            else:
                st.error("Kode kursus tidak ditemukan.")


# ---------- PAGE ACCOUNT ----------
def page_account():
    u = st.session_state.user
    st.header("👤 Profil Saya")
    st.write(f"Nama: {u['name']}")
    st.write(f"Email: {u['email']}")
    st.write(f"Peran: {u['role']}")
    st.caption("(Pengaturan profil akan ditambahkan di versi berikutnya)")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    page_login()
else:
    section = sidebar_nav()
    if section == "🏠 Beranda":
        page_home()
    elif section == "📘 Kursus Saya":
        page_courses()
    elif section == "👤 Akun":
        page_account()

# =========================================
# ============= MODULES ==================
# =========================================

def page_modules(course):
    st.header(f"📦 Modules — {course['title']}")
    u = st.session_state.user

    # --- tampilkan semua modul dari course ini ---
    res = supabase.table("modules").select("*").eq("course_id", course["id"]).order("order_index").execute()
    mods = res.data or []

    if not mods:
        st.info("Belum ada materi untuk kursus ini.")
    else:
        for m in mods:
            st.subheader(f"{m['order_index']}. {m['title']}")
            if m.get("youtube_url"):
                st.video(m["youtube_url"])
            if m.get("image_url"):
                st.image(m["image_url"])
            if m.get("content"):
                st.markdown(m["content"])
            st.divider()

    # --- bagian instruktur: tambah modul ---
    if u["role"] in ["instructor", "admin"]:
        st.subheader("➕ Tambah Modul Baru")
        with st.form("new_module"):
            title = st.text_input("Judul Modul")
            content = st.text_area("Isi Materi (Markdown boleh)")
            youtube_url = st.text_input("YouTube URL (opsional)")
            image_url = st.text_input("Link Gambar (opsional)")
            order_index = st.number_input("Urutan", 0, 100, 0)
            ok = st.form_submit_button("Tambah Modul")
        if ok and title.strip():
            supabase.table("modules").insert({
                "course_id": course["id"],
                "title": title,
                "content": content,
                "youtube_url": youtube_url or None,
                "image_url": image_url or None,
                "order_index": order_index,
            }).execute()
            st.success("Modul berhasil ditambahkan!")
            st.rerun()

def page_course_detail(course):
    st.title(course["title"])
    st.caption(f"Kode: {course['code']}")
    menu = st.radio("Navigasi Kelas", ["Home", "Modules", "Assignments", "Quizzes", "Announcements"])

    if menu == "Home":
        st.subheader("🏠 Beranda Kelas")
        st.write(course["description"] or "-")

    elif menu == "Modules":
        page_modules(course)

    elif menu == "Assignments":
        st.info("Fitur tugas akan ditambahkan di versi berikutnya 💡")

    elif menu == "Quizzes":
        st.info("Fitur kuis akan segera hadir 🧠")

    elif menu == "Announcements":
        st.info("Fitur pengumuman kelas akan ditambahkan 📢")

    if st.button("← Kembali ke Dashboard"):
        st.session_state.in_course = False
        st.session_state.current_course = None
        st.rerun()

for c in courses:
    st.markdown(f"### {c['title']}")
    st.caption(f"Kode: {c['code']}")
    st.write(c.get("description") or "-")
    if st.button(f"Masuk ke {c['title']}", key=f"go_{c['id']}"):
        st.session_state.in_course = True
        st.session_state.current_course = c
        st.rerun()
    st.divider()

if "user" not in st.session_state:
    st.session_state.user = None
if "in_course" not in st.session_state:
    st.session_state.in_course = False
if "current_course" not in st.session_state:
    st.session_state.current_course = None

if not st.session_state.user:
    page_login()
elif st.session_state.in_course and st.session_state.current_course:
    page_course_detail(st.session_state.current_course)
else:
    section = sidebar_nav()
    if section == "🏠 Beranda":
        page_home()
    elif section == "📘 Kursus Saya":
        page_courses()
    elif section == "👤 Akun":
        page_account()


