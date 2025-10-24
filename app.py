import streamlit as st
from supabase import create_client, Client
import hashlib
import time
from datetime import datetime

# ==============================
# KONFIGURASI SUPABASE
# ==============================
SUPABASE_URL = "https://vdtxhoqizsehsfxrtxof.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkdHhob3FpenNlaHNmeHJ0eG9mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI0NDUxMSwiZXhwIjoyMDc2ODIwNTExfQ.zakgEoddamB15sJvzi96hXZ5Ef9rnT-Qn5w8XGRuTl0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# STYLE DASAR
# ==============================
THEME_COLOR = "#635BFF"  # warna ungu modern ThinkVerse
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: #f8f9fc;
        }}
        h1, h2, h3, h4, h5 {{
            color: #2f2f3a;
        }}
        div[data-testid="stSidebar"] {{
            background-color: #eef0f8;
        }}
        button[kind="primary"] {{
            background-color: {THEME_COLOR};
            color: white !important;
            border-radius: 8px;
            font-weight: 600;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# UTILITAS DASAR
# ==============================
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(name, email, password, role):
    hashed_pw = hash_pw(password)
    try:
        supabase.table("users").insert({
            "name": name,
            "email": email,
            "password_hash": hashed_pw,
            "role": role
        }).execute()
        return True
    except Exception as e:
        st.error(f"Gagal membuat akun: {e}")
        return False


def login(email, password):
    hashed_pw = hash_pw(password)
    res = supabase.table("users").select("*").eq("email", email).execute()
    if len(res.data) == 0:
        return None
    user = res.data[0]
    if user["password_hash"] == hashed_pw:
        return user
    return None


def reset_password(email, new_password):
    try:
        hashed_pw = hash_pw(new_password)
        res = supabase.table("users").update({"password_hash": hashed_pw}).eq("email", email).execute()
        return res.data is not None
    except Exception as e:
        st.error(f"Gagal reset password: {e}")
        return False


# ==============================
# HALAMAN LOGIN / REGISTER
# ==============================
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
                time.sleep(0.6)
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


# ==============================
# SIDEBAR NAVIGASI
# ==============================
def sidebar_nav():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/906/906175.png", width=70)
    st.sidebar.markdown(f"<h2 style='color:{THEME_COLOR};'>ThinkVerse LMS</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    user = st.session_state.get("user")
    if not user:
        st.sidebar.info("Silakan login terlebih dahulu.")
        return None

    st.sidebar.markdown(f"👋 **{user['name']}**  \n📧 {user['email']}")
    st.sidebar.markdown(f"🧩 Role: _{user['role']}_")
    st.sidebar.markdown("---")

    page = st.sidebar.radio("Navigasi", ["🏠 Dashboard", "📘 Kursus", "👤 Akun"])
    return page


# ==============================
# HALAMAN DASHBOARD
# ==============================
def page_dashboard():
    st.title("🏠 Dashboard")
    st.info("Selamat datang di ThinkVerse LMS! Pilih menu di sidebar untuk mulai belajar.")


# ==============================
# HALAMAN KURSUS
# ==============================
def page_courses():
    st.title("📘 Kursus")
    st.caption("Kelola kursus atau bergabung ke kelas sesuai peran kamu.")
    st.divider()

    try:
        courses = supabase.table("courses").select("*").execute()
        if len(courses.data) == 0:
            st.info("Belum ada kursus yang terdaftar.")
            return

        for c in courses.data:
            with st.container(border=True):
                st.markdown(f"### {c['title']}")
                st.write(c.get("description", ""))
                st.caption(f"👨‍🏫 Pengampu: {c.get('instructor_email', '-')}")
                st.divider()
    except Exception as e:
        st.error(f"Kesalahan mengambil data kursus: {e}")


# ==============================
# HALAMAN AKUN
# ==============================
def page_account():
    st.title("👤 Akun")
    user = st.session_state.get("user")

    st.markdown(f"### Halo, {user['name']}!")
    st.write(f"📧 Email: {user['email']}")
    st.write(f"🧩 Role: {user['role']}")

    st.divider()
    st.subheader("Keluar dari Akun")
    if st.button("🚪 Logout", type="primary"):
        st.session_state.clear()
        st.success("Berhasil logout. Mengarahkan ke halaman login...")
        time.sleep(0.6)
        st.rerun()


# ==============================
# MAIN APP
# ==============================
def main():
    if "user" not in st.session_state or not st.session_state.user:
        page_login()
        return

    page = sidebar_nav()
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "📘 Kursus":
        page_courses()
    elif page == "👤 Akun":
        page_account()


# ==============================
# JALANKAN APLIKASI
# ==============================
if __name__ == "__main__":
    main()
