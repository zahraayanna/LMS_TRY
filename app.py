import streamlit as st
from supabase import create_client, Client
import time
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

# =========================
# SUPABASE SETUP
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# STYLING
# =========================
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #c9d6ff, #e2e2e2);
        font-family: 'Poppins', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #a777e3, #6e8efb);
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# =========================
# HELPER FUNCTIONS
# =========================
def hash_pw(pw: str):
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()

def get_user(email, password):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data and res.data[0]["password_hash"] == hash_pw(password):
        return res.data[0]
    return None

def register_user(name, email, password, role="student"):
    try:
        supabase.table("users").insert({
            "name": name,
            "email": email,
            "password_hash": hash_pw(password),
            "role": role
        }).execute()
        return True
    except Exception as e:
        st.error(f"Gagal mendaftar: {e}")
        return False

def update_course(course_id, new_title, new_desc):
    supabase.table("courses").update({
        "title": new_title,
        "description": new_desc
    }).eq("id", course_id).execute()

def delete_course(course_id):
    supabase.table("courses").delete().eq("id", course_id).execute()

def add_course(title, description, instructor_id):
    supabase.table("courses").insert({
        "title": title,
        "description": description,
        "instructor_id": instructor_id
    }).execute()

# =========================
# LOGIN PAGE
# =========================
def page_login():
    st.title("🎓 ThinkVerse LMS")
    st.caption("Selamat datang kembali di ruang belajar digital kamu.")

    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Register"])

    with tab1:
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        if st.button("Masuk"):
            user = get_user(email, pw)
            if user:
                st.session_state.user = user
                st.success(f"Selamat datang, {user['name']} 👋")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Email atau password salah!")

    with tab2:
        name = st.text_input("Nama Lengkap", key="reg_name")
        email_r = st.text_input("Email", key="reg_email")
        pw_r = st.text_input("Password", type="password", key="reg_pw")
        role = st.selectbox("Peran", ["student", "instructor"])
        if st.button("Daftar Akun Baru"):
            if name and email_r and pw_r:
                ok = register_user(name, email_r, pw_r, role)
                if ok:
                    st.success("Akun berhasil dibuat! Silakan login.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Lengkapi semua kolom terlebih dahulu.")

# =========================
# SIDEBAR NAVIGATION
# =========================
def sidebar_nav():
    st.sidebar.title("📚 ThinkVerse LMS")
    u = st.session_state.user

    st.sidebar.write(f"👋 Halo, **{u['name']}**")
    st.sidebar.caption(f"Role: {u['role']}")

    page = st.sidebar.radio("Navigasi", ["🏠 Beranda", "📘 Kursus", "👤 Akun"])

    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.success("Logout berhasil!")
        time.sleep(1)
        st.rerun()

    return page

# =========================
# DASHBOARD PAGE
# =========================
def page_home():
    st.title("🏠 Dashboard")
    st.write("Selamat datang di ThinkVerse LMS, ruang belajar modern dan interaktif.")

    courses = supabase.table("courses").select("*").execute().data
    st.subheader("📚 Semua Kursus")
    if not courses:
        st.info("Belum ada kursus.")
    else:
        for c in courses:
            st.markdown(f"### {c['title']}")
            st.caption(c.get("description", "-"))

# =========================
# COURSES PAGE
# =========================
def page_courses():
    st.title("📘 Kursus")
    u = st.session_state.user

    # === Tambah Kursus ===
    if u["role"] in ["instructor", "admin"]:
        with st.expander("➕ Tambah Kursus Baru"):
            title = st.text_input("Judul Kursus")
            desc = st.text_area("Deskripsi")
            if st.button("Simpan Kursus"):
                if title:
                    add_course(title, desc, u["id"])
                    st.success("Kursus berhasil dibuat!")
                    st.rerun()
                else:
                    st.error("Judul tidak boleh kosong.")

    # === Daftar Kursus ===
    courses = supabase.table("courses").select("*").execute().data
    if not courses:
        st.info("Belum ada kursus yang tersedia.")
        return

    for course in courses:
        with st.container(border=True):
            st.markdown(f"### {course['title']}")
            st.caption(course.get("description", "-"))
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("Masuk", key=f"enter_{course['id']}"):
                    st.session_state.current_course = course
                    st.session_state.page = "course_detail"
                    st.rerun()
            with col2:
                if u["role"] in ["instructor", "admin"]:
                    if st.button("Edit", key=f"edit_{course['id']}"):
                        new_t = st.text_input("Judul baru", value=course['title'], key=f"t_{course['id']}")
                        new_d = st.text_area("Deskripsi baru", value=course.get('description', ''), key=f"d_{course['id']}")
                        if st.button("Simpan", key=f"s_{course['id']}"):
                            update_course(course['id'], new_t, new_d)
                            st.success("Kursus diperbarui.")
                            st.rerun()
            with col3:
                if u["role"] in ["instructor", "admin"]:
                    if st.button("🗑️ Hapus", key=f"del_{course['id']}"):
                        delete_course(course["id"])
                        st.warning("Kursus dihapus.")
                        st.rerun()

# =========================
# COURSE DETAIL PAGE
# =========================
def page_course_detail():
    course = st.session_state.current_course
    st.title(f"📖 {course['title']}")
    st.write(course.get("description", "-"))

    tabs = st.tabs(["🏠 Home", "📝 Assignments", "🧪 Quizzes"])
    with tabs[0]:
        st.info("Selamat datang di halaman kursus! Fitur ini akan diperluas di tahap berikutnya.")
    with tabs[1]:
        st.warning("Bagian tugas belum aktif (akan diaktifkan di Part 2).")
    with tabs[2]:
        st.warning("Bagian kuis belum aktif (akan diaktifkan di Part 3).")

# =========================
# MAIN APP
# =========================
def main():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if not st.session_state.user:
        page_login()
        return

    # Navigasi utama
    if st.session_state.get("page") == "course_detail":
        page_course_detail()
        return

    menu = sidebar_nav()

    if menu == "🏠 Beranda":
        page_home()
    elif menu == "📘 Kursus":
        page_courses()
    elif menu == "👤 Akun":
        st.title("👤 Akun Pengguna")
        st.write("Fitur profil akan ditambahkan di tahap berikutnya.")

if __name__ == "__main__":
    main()
