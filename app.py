import streamlit as st
from supabase import create_client, Client
import hashlib
import time

# ⚙️ HARUS PALING ATAS – SETEL HALAMAN
st.set_page_config(
    page_title="ThinkVerse LMS",
    page_icon="🎓",
    layout="wide"
)

# ======================
# SUPABASE SETUP
# ======================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# UTILS
# ======================
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

# ======================
# STYLING
# ======================
st.markdown("""
<style>
body {
  background: linear-gradient(135deg, #e2e2e2, #f9f9ff);
  font-family: 'Poppins', sans-serif;
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
</style>
""", unsafe_allow_html=True)

# ======================
# LOGIN PAGE
# ======================
def page_login():
    st.title("🎓 ThinkVerse LMS")
    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Register"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Masuk", key="login_btn"):
            u = get_user(email, pw)
            if u:
                st.session_state.user = u
                st.success(f"Halo, {u['name']} 👋")
                time.sleep(1)
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
                    st.success("Akun dibuat! Silakan login.")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Lengkapi semua kolom!")

# ======================
# MAIN
# ======================
def main():
    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        page_login()
        return

    st.sidebar.title("📚 ThinkVerse LMS")
    u = st.session_state.user
    st.sidebar.write(f"👋 **{u['name']}**")
    st.sidebar.caption(f"Role: {u['role']}")
    page = st.sidebar.radio("Navigasi", ["🏠 Beranda", "👤 Akun"])

    if page == "🏠 Beranda":
        st.title("🏠 Dashboard")
        st.write("Selamat datang di **ThinkVerse LMS**, ruang belajar modern kamu 💫")

    elif page == "👤 Akun":
        st.title("👤 Akun Pengguna")
        st.write(f"Nama: **{u['name']}**")
        st.write(f"Email: {u['email']}")
        st.write(f"Role: {u['role']}")
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.user = None
            st.success("Logout berhasil.")
            time.sleep(1)
            st.rerun()

if __name__ == "__main__":
    main()
