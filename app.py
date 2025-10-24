import streamlit as st
import hashlib
import time
from supabase import create_client, Client
import os

# =============================
# KONFIGURASI SUPABASE
# =============================
SUPABASE_URL = "https://vdtxhoqizsehsfxrtxof.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkdHhob3FpenNlaHNmeHJ0eG9mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI0NDUxMSwiZXhwIjoyMDc2ODIwNTExfQ.zakgEoddamB15sJvzi96hXZ5Ef9rnT-Qn5w8XGRuTl0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =============================
# UTILITAS PASSWORD
# =============================
def hash_pw(pw: str):
    return hashlib.sha256(pw.encode()).hexdigest()

# =============================
# FUNGSI DATABASE
# =============================

def login(email, password):
    """Cek user dari Supabase"""
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if res.data:
            u = res.data[0]
            if u["password_hash"] == hash_pw(password):
                return u
    except Exception as e:
        st.error(f"Kesalahan koneksi: {e}")
    return None


def register_user(name, email, password, role):
    """Daftarkan user baru ke Supabase"""
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


def reset_password(email, new_password):
    """Reset password pengguna berdasarkan email"""
    try:
        res = supabase.table("users").select("id").eq("email", email).execute()
        if not res.data:
            st.error("Email tidak ditemukan.")
            return False
        uid = res.data[0]["id"]
        supabase.table("users").update({
            "password_hash": hash_pw(new_password)
        }).eq("id", uid).execute()
        return True
    except Exception as e:
        st.error(f"Gagal reset password: {e}")
        return False


# =============================
# HALAMAN LOGIN
# =============================

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
            if not name or not email or not pw:
                st.error("Semua field wajib diisi.")
            elif register_user(name, email, pw, role):
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


# =============================
# ENTRY POINT UTAMA APLIKASI
# =============================
def main():
    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        page_login()
        return

    st.write(f"Halo, {st.session_state.user['name']}!")
    st.success("Login berhasil, halaman utama LMS bisa dikembangkan di sini 🎉")


if __name__ == "__main__":
    main()

import streamlit as st
from supabase import create_client, Client
import os

# ====== Supabase Client ======
SUPABASE_URL = "https://vdtxhoqizsehsfxrtxof.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkdHhob3FpenNlaHNmeHJ0eG9mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI0NDUxMSwiZXhwIjoyMDc2ODIwNTExfQ.zakgEoddamB15sJvzi96hXZ5Ef9rnT-Qn5w8XGRuTl0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ====== Warna Tema ======
THEME_COLOR = "#4F46E5"  # ungu ke-biru elegan
ACCENT_COLOR = "#E0E7FF"  # ungu muda lembut


# ====== Sidebar Navigasi ======
def sidebar_nav():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/906/906175.png", width=70)
    st.sidebar.markdown(f"<h2 style='color:{THEME_COLOR};'>ThinkVerse LMS</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    user = st.session_state.get("user")
    if user:
        st.sidebar.markdown(f"👋 **{user['name']}**  \n📧 {user['email']}")
        st.sidebar.markdown(f"🧩 Role: _{user['role']}_")
        st.sidebar.markdown("---")
    else:
        return None

    page = st.sidebar.radio("Navigasi", ["🏠 Dashboard", "📘 Kursus", "👤 Akun", "🚪 Logout"])
    return page


# ====== Dashboard Utama ======
def page_dashboard():
    st.markdown(
        f"""
        <div style="background-color:{ACCENT_COLOR};padding:20px;border-radius:12px;">
            <h2 style="color:{THEME_COLOR};">🎓 Selamat Datang di ThinkVerse LMS</h2>
            <p>Platform pembelajaran modern untuk pengajar dan pelajar fisika 💡</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    user = st.session_state["user"]
    st.write("")
    st.subheader("📊 Ringkasan Akun")
    st.write(f"Nama: **{user['name']}**")
    st.write(f"Email: **{user['email']}**")
    st.write(f"Role: **{user['role']}**")

    st.info("Gunakan tab *Kursus* di sidebar untuk membuat atau bergabung ke kelas.")


# ====== Manajemen Kursus ======
def page_courses():
    st.markdown(f"<h2 style='color:{THEME_COLOR};'>📘 Kursus</h2>", unsafe_allow_html=True)
    user = st.session_state["user"]

    # --- Jika instruktur ---
    if user["role"] in ["instructor", "admin"]:
        with st.expander("➕ Tambah Kursus Baru", expanded=False):
            title = st.text_input("Judul Kursus")
            code = st.text_input("Kode Kursus (unik, mis. PHY101)")
            desc = st.text_area("Deskripsi")
            ok = st.button("Buat Kursus", type="primary")
            if ok and title.strip() and code.strip():
                try:
                    supabase.table("courses").insert({
                        "title": title,
                        "code": code,
                        "description": desc,
                        "instructor_email": user["email"]
                    }).execute()
                    st.success("✅ Kursus berhasil dibuat!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal membuat kursus: {e}")

    st.markdown("---")

    # --- Daftar kursus yang diampu / diikuti ---
    st.subheader("📚 Daftar Kursus Saya")
    try:
        if user["role"] == "instructor":
            res = supabase.table("courses").select("*").eq("instructor_email", user["email"]).execute()
        else:
            res = supabase.table("enrollments").select("*, courses(title, code, description, instructor_email)").eq("student_email", user["email"]).execute()

        if not res.data:
            st.info("Belum ada kursus yang kamu ikuti atau buat.")
        else:
            for c in res.data:
                course = c["courses"] if "courses" in c else c
                with st.container(border=True):
                    st.markdown(f"### {course['title']} ({course['code']})")
                    st.caption(f"Pengampu: {course.get('instructor_email', '-')}")
                    st.write(course.get("description", "-"))
                    st.button("Masuk ke Kelas", key=f"enter_{course['code']}")
    except Exception as e:
        st.error(f"Kesalahan mengambil data kursus: {e}")


# ====== Halaman Akun ======
def page_account():
    st.markdown(f"<h2 style='color:{THEME_COLOR};'>👤 Akun Saya</h2>", unsafe_allow_html=True)
    user = st.session_state["user"]

    st.write(f"Nama: **{user['name']}**")
    st.write(f"Email: **{user['email']}**")
    st.write(f"Role: **{user['role']}**")
    st.markdown("---")

    if st.button("Logout", type="primary"):
        st.session_state.user = None
        st.success("Berhasil logout.")
        time.sleep(0.7)
        st.rerun()


# ====== MAIN APP (lanjutan dari login system) ======
def main():
    if "user" not in st.session_state or not st.session_state.user:
        from app import page_login
        page_login()
        return

    page = sidebar_nav()
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "📘 Kursus":
        page_courses()
    elif page == "👤 Akun":
        page_account()
    elif page == "🚪 Logout":
        st.session_state.user = None
        st.success("Logout berhasil.")
        time.sleep(0.7)
        st.rerun()


if __name__ == "__main__":
    main()


