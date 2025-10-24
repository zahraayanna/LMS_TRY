import streamlit as st
from supabase import create_client, Client
import hashlib
import time

# ==============================
# KONFIGURASI SUPABASE
# ==============================
SUPABASE_URL = "https://vdtxhoqizsehsfxrtxof.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkdHhob3FpenNlaHNmeHJ0eG9mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTI0NDUxMSwiZXhwIjoyMDc2ODIwNTExfQ.zakgEoddamB15sJvzi96hXZ5Ef9rnT-Qn5w8XGRuTl0"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# KONFIGURASI HALAMAN
# ==============================
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

# ==============================
# CSS GLOBAL
# ==============================
st.markdown("""
<style>
    html, body, .stApp {
        background: linear-gradient(135deg, #dcd6f7 0%, #f9d7e3 100%) !important;
        font-family: "Poppins", sans-serif !important;
        color: #222 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    [data-testid="stHeader"], header {display: none !important;}

    h1, h2, h3, h4 {color: #222 !important; font-weight: 700;}

    .glass-box {
        background: rgba(255,255,255,0.6);
        border-radius: 25px;
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 6px 24px rgba(0,0,0,0.08);
        padding: 40px;
        margin: 20px 0 25px 0;
    }

    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.55);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.4);
        color: #222 !important;
    }

    button[kind="primary"] {
        background: linear-gradient(90deg, #7c3aed, #ec4899);
        border-radius: 12px;
        font-weight: 600;
        color: white !important;
        border: none;
        transition: all 0.3s ease;
    }
    button[kind="primary"]:hover {filter: brightness(1.1); transform: scale(1.02);}
    input, select, textarea {background-color: rgba(255,255,255,0.85) !important;}
    label {font-weight: 600; color: #333 !important;}
</style>
""", unsafe_allow_html=True)

# ==============================
# UTILITAS
# ==============================
def hash_pw(password): return hashlib.sha256(password.encode()).hexdigest()

def register_user(name, email, password, role):
    try:
        hashed = hash_pw(password)
        supabase.table("users").insert({
            "name": name, "email": email,
            "password_hash": hashed, "role": role
        }).execute()
        return True
    except Exception as e:
        st.error(f"Gagal daftar: {e}")
        return False

def login(email, password):
    hashed = hash_pw(password)
    res = supabase.table("users").select("*").eq("email", email).execute()
    if len(res.data) == 0: return None
    user = res.data[0]
    if user["password_hash"] == hashed: return user
    return None

# ==============================
# HALAMAN LOGIN
# ==============================
def page_login():
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.title("🎓 ThinkVerse LMS")
    st.caption("Portal pembelajaran modern berbasis cloud Supabase")

    tabs = st.tabs(["🔑 Login", "🆕 Register"])

    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
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

    with tabs[1]:
        with st.form("reg_form"):
            name = st.text_input("Nama Lengkap")
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            role = st.selectbox("Peran", ["student", "instructor"])
            ok2 = st.form_submit_button("Daftar Akun Baru")
        if ok2:
            if register_user(name, email, pw, role):
                st.success("Akun berhasil dibuat! Silakan login.")
    st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# HALAMAN UTAMA
# ==============================
def sidebar_nav():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/906/906175.png", width=70)
    st.sidebar.markdown("<h2 style='color:#333;'>ThinkVerse LMS</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    user = st.session_state.get("user")
    st.sidebar.markdown(f"👋 **{user['name']}**  \n📧 {user['email']}")
    st.sidebar.markdown(f"🧩 Role: _{user['role']}_")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigasi", ["🏠 Dashboard", "📘 Kursus", "👤 Akun"])
    return page

def page_dashboard():
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.title("🏠 Dashboard")
    st.info("Selamat datang di ThinkVerse LMS ✨")
    st.markdown("</div>", unsafe_allow_html=True)

def page_courses():
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.title("📘 Kursus")

    user = st.session_state.get("user")
    role = user["role"]

    # FORM TAMBAH KURSUS UNTUK INSTRUCTOR
    if role == "instructor":
        with st.expander("➕ Tambah Kursus Baru"):
            with st.form("add_course_form"):
                title = st.text_input("Judul Kursus")
                desc = st.text_area("Deskripsi")
                yt = st.text_input("Link YouTube (opsional)")
                ok = st.form_submit_button("Simpan Kursus")
            if ok:
                try:
                    supabase.table("courses").insert({
                        "title": title,
                        "description": desc,
                        "youtube_url": yt,
                        "instructor_email": user["email"]
                    }).execute()
                    st.success("Kursus berhasil ditambahkan!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menambah kursus: {e}")

    # DAFTAR KURSUS
    try:
        data = supabase.table("courses").select("*").execute()
        if len(data.data) == 0:
            st.info("Belum ada kursus yang tersedia.")
        else:
            for c in data.data:
                st.markdown(f"""
                    <div style="
                        background: rgba(255,255,255,0.75);
                        border-radius: 18px;
                        padding: 20px 25px;
                        margin-top: 15px;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
                    ">
                        <h4>{c['title']}</h4>
                        <p>{c['description']}</p>
                        <p style="font-size:13px;opacity:0.7;">👩‍🏫 {c.get('instructor_email','-')}</p>
                    </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Gagal mengambil data kursus: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

def page_account():
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.title("👤 Akun")
    user = st.session_state.get("user")
    st.write(f"**Nama:** {user['name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Role:** {user['role']}")
    if st.button("🚪 Logout", type="primary"):
        st.session_state.clear()
        st.success("Berhasil logout. Mengarahkan ke halaman login...")
        time.sleep(0.7)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# MAIN
# ==============================
def main():
    if "user" not in st.session_state or not st.session_state.user:
        page_login()
    else:
        page = sidebar_nav()
        if page == "🏠 Dashboard": page_dashboard()
        elif page == "📘 Kursus": page_courses()
        elif page == "👤 Akun": page_account()

if __name__ == "__main__":
    main()

