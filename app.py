import streamlit as st
from supabase import create_client, Client
import hashlib
import time
from datetime import datetime

# =========================================
# 🚀 PAGE CONFIG — HARUS PALING ATAS
# =========================================
st.set_page_config(
    page_title="ThinkVerse LMS",
    page_icon="🎓",
    layout="wide"
)

# =========================================
# 🔧 SUPABASE SETUP
# =========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================
# 🧠 UTIL FUNCTIONS
# =========================================
def hash_pw(pw: str):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_user(email, pw):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data and res.data[0]["password_hash"] == hash_pw(pw):
        return res.data[0]
    return None

def register_user(name, email, pw, role="student"):
    try:
        supabase.table("users").insert({
            "name": name,
            "email": email,
            "password_hash": hash_pw(pw),
            "role": role
        }).execute()
        return True
    except Exception as e:
        st.error(f"Gagal daftar: {e}")
        return False

# =========================================
# 🎨 STYLING
# =========================================
st.markdown("""
<style>
body {
  background: linear-gradient(135deg, #e6ebff, #fdfbff);
  font-family: 'Poppins', sans-serif;
  color: #222;
}
.stButton>button {
  background: linear-gradient(135deg, #6e8efb, #a777e3);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.6em 1.2em;
  font-weight: 500;
  transition: 0.2s;
}
.stButton>button:hover {
  background: linear-gradient(135deg, #a777e3, #6e8efb);
  transform: scale(1.03);
}
.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
  background: #f1f3fa;
  border-radius: 8px;
  padding: 6px 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================================
# 🔐 AUTH PAGES
# =========================================
def page_login():
    st.title("🎓 ThinkVerse LMS")
    tab1, tab2, tab3 = st.tabs(["🔑 Login", "🆕 Register", "🔁 Lupa Password"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Masuk", key="login_btn"):
            u = get_user(email, pw)
            if u:
                st.session_state.user = u
                st.success(f"Selamat datang, {u['name']} 👋")
                time.sleep(0.7)
                st.rerun()
            else:
                st.error("Email atau password salah.")

    with tab2:
        name = st.text_input("Nama Lengkap", key="reg_name")
        email_r = st.text_input("Email", key="reg_email")
        pw_r = st.text_input("Password", type="password", key="reg_pw")
        role = st.selectbox("Peran", ["student", "instructor"], key="reg_role")
        if st.button("Daftar Akun Baru", key="reg_btn"):
            if name and email_r and pw_r:
                if register_user(name, email_r, pw_r, role):
                    st.success("Akun berhasil dibuat! Silakan login.")
                    time.sleep(0.8)
                    st.rerun()
            else:
                st.error("Lengkapi semua kolom!")

    with tab3:
        email_fp = st.text_input("Email akun", key="fp_email")
        new_pw = st.text_input("Password baru", type="password", key="fp_pw")
        new_pw2 = st.text_input("Ulangi password", type="password", key="fp_pw2")
        if st.button("Reset Password", key="fp_btn"):
            if new_pw != new_pw2:
                st.error("Password tidak sama.")
            else:
                res = supabase.table("users").select("*").eq("email", email_fp).execute()
                if not res.data:
                    st.error("Email tidak ditemukan.")
                else:
                    supabase.table("users").update({"password_hash": hash_pw(new_pw)}).eq("email", email_fp).execute()
                    st.success("Password berhasil direset! Silakan login ulang.")

# =========================================
# 🧭 DASHBOARD NAVIGATION
# =========================================
def sidebar_nav():
    u = st.session_state.user
    st.sidebar.title("📚 ThinkVerse LMS")
    st.sidebar.write(f"👤 **{u['name']}**  \n📧 {u['email']}")
    st.sidebar.caption(f"Role: {u['role']}")
    menu = st.sidebar.radio("Navigasi", ["🏠 Beranda", "📘 Kursus", "👤 Akun"])
    return menu

# =========================================
# 📘 COURSES
# =========================================
def page_courses():
    st.title("📘 Kursus")
    u = st.session_state.user

    # === Tambah kursus (instructor only)
    if u["role"] in ["instructor", "admin"]:
        with st.expander("➕ Buat Kursus Baru"):
            code = st.text_input("Kode Kursus (unik)", key="crs_code")
            title = st.text_input("Judul Kursus", key="crs_title")
            desc = st.text_area("Deskripsi", key="crs_desc")
            if st.button("Buat Kursus", key="crs_btn"):
                if code and title:
                    supabase.table("courses").insert({
                        "code": code,
                        "title": title,
                        "description": desc,
                        "instructor_id": u["id"] if "id" in u else None
                    }).execute()
                    st.success("Kursus dibuat.")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Kode dan judul wajib diisi!")

    st.subheader("Daftar Kursus")
    rows = supabase.table("courses").select("*").execute().data
    if not rows:
        st.info("Belum ada kursus.")
        return

    for c in rows:
        with st.container(border=True):
            st.markdown(f"### {c['title']}  \n`{c['code']}`")
            st.write(c.get("description", "-"))
            if st.button("Masuk", key=f"go_{c['id']}"):
                st.session_state.page = "detail"
                st.session_state.current_course = c
                st.rerun()

# =========================================
# 🏠 COURSE DETAIL
# =========================================
def page_course_detail():
    c = st.session_state.current_course
    st.title(f"📖 {c['title']}")
    tabs = st.tabs(["🏠 Home", "📝 Assignments", "🧪 Quizzes"])
    with tabs[0]:
        st.write(c.get("description", "-"))

    with tabs[1]:
        page_assignments(c["id"])

    with tabs[2]:
        page_quizzes(c["id"])

# =========================================
# 📝 ASSIGNMENTS
# =========================================
def page_assignments(course_id):
    u = st.session_state.user
    st.subheader("📝 Tugas")

    if u["role"] in ["instructor", "admin"]:
        with st.expander("➕ Tambah Tugas"):
            title = st.text_input("Judul", key=f"title_a_{course_id}")
            desc = st.text_area("Deskripsi Tugas", key=f"desc_a_{course_id}")
            due = st.date_input("Tenggat", datetime.now())
            pts = st.number_input("Poin", 0, 100, 10)
            if st.button("Simpan", key=f"save_a_{course_id}"):
                supabase.table("assignments").insert({
                    "course_id": course_id,
                    "title": title,
                    "description": desc,
                    "due_date": str(due),
                    "points": pts
                }).execute()
                st.success("Tugas ditambahkan.")
                st.rerun()

    rows = supabase.table("assignments").select("*").eq("course_id", course_id).execute().data
    if not rows:
        st.info("Belum ada tugas.")
        return
    for a in rows:
        st.markdown(f"#### {a['title']}")
        st.caption(f"Batas waktu: {a.get('due_date', '-')} • {a.get('points', 0)} poin")
        st.write(a.get("description", "-"))

# =========================================
# 🧪 QUIZZES
# =========================================
def page_quizzes(course_id):
    u = st.session_state.user
    st.subheader("🧪 Kuis")

    if u["role"] in ["instructor", "admin"]:
        with st.expander("➕ Tambah Kuis"):
            title = st.text_input("Judul Kuis", key=f"title_q_{course_id}")
            desc = st.text_area("Deskripsi Kuis", key=f"desc_q_{course_id}")
            tlim = st.number_input("Batas Waktu (menit)", 0, 300, 0)
            if st.button("Simpan Kuis", key=f"save_q_{course_id}"):
                supabase.table("quizzes").insert({
                    "course_id": course_id,
                    "title": title,
                    "description": desc,
                    "time_limit": int(tlim)
                }).execute()
                st.success("Kuis ditambahkan.")
                st.rerun()

    rows = supabase.table("quizzes").select("*").eq("course_id", course_id).execute().data
    if not rows:
        st.info("Belum ada kuis.")
        return
    for q in rows:
        st.markdown(f"#### {q['title']}")
        st.caption(f"Waktu: {q.get('time_limit', 0)} menit")
        st.write(q.get("description", "-"))

# =========================================
# 👤 ACCOUNT PAGE
# =========================================
def page_account():
    u = st.session_state.user
    st.title("👤 Akun")
    st.write(f"Nama: **{u['name']}**")
    st.write(f"Email: {u['email']}")
    st.write(f"Peran: {u['role']}")
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.user = None
        st.session_state.page = "login"
        st.success("Logout berhasil.")
        time.sleep(1)
        st.rerun()

# =========================================
# 🧩 MAIN APP LOGIC
# =========================================
def main():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "login"

    if not st.session_state.user:
        page_login()
        return

    if st.session_state.get("page") == "detail":
        page_course_detail()
        if st.button("⬅️ Kembali ke Dashboard", key="back_btn"):
            st.session_state.page = "main"
            st.rerun()
        return

    menu = sidebar_nav()
    if menu == "🏠 Beranda":
        st.title("🏠 Dashboard")
        st.write("Selamat datang di ThinkVerse LMS 💡")
    elif menu == "📘 Kursus":
        page_courses()
    elif menu == "👤 Akun":
        page_account()

if __name__ == "__main__":
    main()
