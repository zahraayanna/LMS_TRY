import streamlit as st
from supabase import create_client, Client
import hashlib

# ====== Supabase Client ======
SUPABASE_URL = "https://vdtxhoqizsehsfxrtxof.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkdHhob3FpenNlaHNmeHJ0eG9mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI0NDUxMSwiZXhwIjoyMDc2ODIwNTExfQ.zakgEoddamB15sJvzi96hXZ5Ef9rnT-Qn5w8XGRuTl0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ====== Tema UI ======
THEME_COLOR = "#4F46E5"   # Ungu elegan
ACCENT_COLOR = "#EEF2FF"  # Latar lembut

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
        st.sidebar.info("Silakan login terlebih dahulu.")
        return None

    page = st.sidebar.radio("Navigasi", ["🏠 Dashboard", "📘 Kursus", "👤 Akun", "🚪 Logout"])
    return page



# ====== Dashboard ======
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

    # === Buat Kursus (untuk Instruktur/Admin) ===
    if user["role"] in ["instructor", "admin"]:
        with st.expander("➕ Tambah Kursus Baru", expanded=False):
            title = st.text_input("Judul Kursus")
            code = st.text_input("Kode Kursus (unik, mis. PHY101)")
            desc = st.text_area("Deskripsi")
            ok = st.button("Buat Kursus", type="primary")
            if ok and title.strip() and code.strip():
                try:
                    supabase.table("courses").insert({
                        "title": title.strip(),
                        "code": code.strip(),
                        "description": desc,
                        "instructor_email": user["email"]
                    }).execute()
                    st.success("✅ Kursus berhasil dibuat!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Gagal membuat kursus: {e}")

    st.markdown("---")

    # === Daftar Kursus yang Diampu / Diikuti ===
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

    if st.button("Logout 🔒", type="primary"):
        st.session_state.clear()
        st.success("Berhasil logout. Mengarahkan kembali...")
        st.experimental_rerun()


# ====== MAIN APP ======
def main():
    # Pastikan user login dulu
    if "user" not in st.session_state or not st.session_state.user:
        from app import page_login
        page_login()
        return

    # Sidebar navigasi
    page = sidebar_nav()
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "📘 Kursus":
        page_courses()
    elif page == "👤 Akun":
        page_account()
    elif page == "🚪 Logout":
        st.session_state.clear()
        st.success("Logout berhasil! Mengarahkan ulang...")
        st.experimental_rerun()


if __name__ == "__main__":
    main()

