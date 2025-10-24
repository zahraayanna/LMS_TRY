import streamlit as st
from supabase import create_client, Client
import hashlib
import time

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

# ======================
# SUPABASE SETUP
# ======================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# STYLE
# ======================
st.markdown("""
<style>
body {
  background: linear-gradient(135deg,#c9d6ff,#e2e2e2);
  font-family:'Poppins',sans-serif;
}
.stButton>button {
  background:linear-gradient(135deg,#6e8efb,#a777e3);
  color:white;border:none;border-radius:8px;
  padding:0.6em 1.2em;font-weight:500;
  transition:0.2s;
}
.stButton>button:hover {
  background:linear-gradient(135deg,#a777e3,#6e8efb);
  transform:scale(1.03);
}
</style>
""", unsafe_allow_html=True)

# ======================
# UTILS
# ======================
def hash_pw(pw:str): return hashlib.sha256(pw.encode()).hexdigest()

def get_user(email,pw):
    res=supabase.table("users").select("*").eq("email",email).execute()
    if res.data and res.data[0]["password_hash"]==hash_pw(pw): return res.data[0]
    return None

def register_user(name,email,pw,role="student"):
    try:
        supabase.table("users").insert({
            "name":name,"email":email,
            "password_hash":hash_pw(pw),
            "role":role
        }).execute(); return True
    except Exception as e:
        st.error(f"Gagal daftar: {e}"); return False

def add_course(title,desc,instructor_id):
    supabase.table("courses").insert({
        "title":title,"description":desc,"instructor_id":instructor_id
    }).execute()

def update_course(cid,new_title,new_desc):
    supabase.table("courses").update({
        "title":new_title,"description":new_desc
    }).eq("id",cid).execute()

def delete_course(cid): supabase.table("courses").delete().eq("id",cid).execute()

# ======================
# LOGIN PAGE
# ======================
def page_login():
    st.title("🎓 ThinkVerse LMS")
    tab1,tab2=st.tabs(["🔑 Login","🆕 Register"])
    with tab1:
        email=st.text_input("Email"); pw=st.text_input("Password",type="password")
        if st.button("Masuk"):
            u=get_user(email,pw)
            if u:
                st.session_state.user=u
                st.success(f"Halo, {u['name']} 👋"); time.sleep(1); st.rerun()
            else: st.error("Email / password salah.")
    with tab2:
        name=st.text_input("Nama Lengkap",key="rn")
        email_r=st.text_input("Email",key="re")
        pw_r=st.text_input("Password",type="password",key="rp")
        role=st.selectbox("Peran",["student","instructor"])
        if st.button("Daftar Akun Baru"):
            if name and email_r and pw_r:
                if register_user(name,email_r,pw_r,role):
                    st.success("Akun dibuat! Silakan login."); time.sleep(1); st.rerun()
            else: st.error("Lengkapi semua kolom!")

# ======================
# SIDEBAR
# ======================
def sidebar_nav():
    st.sidebar.title("📚 ThinkVerse LMS")
    u=st.session_state.user
    st.sidebar.write(f"👋 **{u['name']}**"); st.sidebar.caption(f"Role: {u['role']}")
    page=st.sidebar.radio("Navigasi",["🏠 Beranda","📘 Kursus","👤 Akun"])
    return page

# ======================
# HOME
# ======================
def page_home():
    st.title("🏠 Dashboard")
    st.write("Selamat datang di **ThinkVerse LMS**, ruang belajar modern kamu 💫")
    courses=supabase.table("courses").select("*").execute().data
    st.subheader("📚 Semua Kursus")
    if not courses: st.info("Belum ada kursus.")
    else:
        for c in courses:
            st.markdown(f"### {c['title']}")
            st.caption(c.get("description","-"))

# ======================
# COURSES
# ======================
def page_courses():
    st.title("📘 Kursus")
    u=st.session_state.user

    if u["role"] in ["instructor","admin"]:
        with st.expander("➕ Tambah Kursus Baru"):
            title=st.text_input("Judul Kursus"); desc=st.text_area("Deskripsi")
            if st.button("Simpan Kursus"):
                if title: add_course(title,desc,u["id"]); st.success("Kursus dibuat."); st.rerun()
                else: st.error("Judul wajib diisi.")

    courses=supabase.table("courses").select("*").execute().data
    if not courses: st.info("Belum ada kursus."); return

    for c in courses:
        with st.container(border=True):
            st.markdown(f"### {c['title']}")
            st.caption(c.get("description","-"))
            col1,col2,col3=st.columns([1,1,2])
            with col1:
                if st.button("Masuk",key=f"enter_{c['id']}"):
                    st.session_state.current_course=c; st.session_state.page="detail"; st.rerun()
            if u["role"] in ["instructor","admin"]:
                with col2:
                    if st.button("Edit",key=f"edit_{c['id']}"):
                        new_t=st.text_input("Judul Baru",value=c['title'],key=f"t_{c['id']}")
                        new_d=st.text_area("Deskripsi Baru",value=c.get('description',''),key=f"d_{c['id']}")
                        if st.button("Simpan",key=f"s_{c['id']}"):
                            update_course(c['id'],new_t,new_d); st.success("Kursus diperbarui."); st.rerun()
                with col3:
                    if st.button("🗑️ Hapus",key=f"del_{c['id']}"):
                        delete_course(c["id"]); st.warning("Kursus dihapus."); st.rerun()

# ======================
# ASSIGNMENTS
# ======================
def page_assignments(cid):
    st.subheader("📝 Daftar Tugas")
    u=st.session_state.user

    if u["role"] in ["instructor","admin"]:
        with st.expander("➕ Tambah Tugas"):
            title=st.text_input("Judul Tugas"); desc=st.text_area("Deskripsi")
            due=st.date_input("Batas Waktu"); pts=st.number_input("Poin",0,100,10)
            if st.button("Simpan Tugas"):
                if title:
                    supabase.table("assignments").insert({
                        "course_id":cid,"title":title,
                        "description":desc,"due_date":str(due),"points":int(pts)
                    }).execute()
                    st.success("Tugas ditambahkan."); st.rerun()
                else: st.error("Judul wajib diisi.")

    rows=supabase.table("assignments").select("*").eq("course_id",cid).execute().data
    if not rows: st.info("Belum ada tugas."); return
    for a in rows:
        with st.container(border=True):
            st.markdown(f"### {a['title']}")
            st.caption(f"Batas: {a.get('due_date','-')} · Poin: {a.get('points',0)}")
            st.write(a.get("description","-"))
            if u["role"] in ["instructor","admin"]:
                if st.button("🗑️ Hapus Tugas",key=f"del_asg_{a['id']}"):
                    supabase.table("assignments").delete().eq("id",a["id"]).execute()
                    st.warning("Tugas dihapus."); st.rerun()

# ======================
# QUIZZES
# ======================
def page_quizzes(cid):
    st.subheader("🧪 Daftar Kuis")
    u=st.session_state.user

    if u["role"] in ["instructor","admin"]:
        with st.expander("➕ Tambah Kuis"):
            title=st.text_input("Judul Kuis"); desc=st.text_area("Deskripsi")
            tlim=st.number_input("Durasi (menit)",0,300,0)
            if st.button("Simpan Kuis"):
                if title:
                    supabase.table("quizzes").insert({
                        "course_id":cid,"title":title,
                        "description":desc,"time_limit":int(tlim)
                    }).execute()
                    st.success("Kuis dibuat."); st.rerun()
                else: st.error("Judul wajib diisi.")

    rows=supabase.table("quizzes").select("*").eq("course_id",cid).execute().data
    if not rows: st.info("Belum ada kuis."); return
    for q in rows:
        with st.container(border=True):
            st.markdown(f"### {q['title']}")
            st.caption(f"Durasi: {q.get('time_limit',0)} menit")
            st.write(q.get("description","-"))
            if u["role"] in ["instructor","admin"]:
                if st.button("🗑️ Hapus Kuis",key=f"del_q_{q['id']}"):
                    supabase.table("quizzes").delete().eq("id",q["id"]).execute()
                    st.warning("Kuis dihapus."); st.rerun()

# ======================
# COURSE DETAIL
# ======================
def page_course_detail():
    c=st.session_state.current_course
    st.title(f"📖 {c['title']}"); st.write(c.get("description","-"))
    tabs=st.tabs(["🏠 Home","📝 Assignments","🧪 Quizzes"])
    with tabs[0]: st.info("Selamat datang di halaman kursus ini.")
    with tabs[1]: page_assignments(c["id"])
    with tabs[2]: page_quizzes(c["id"])

# ======================
# MAIN
# ======================
def main():
    if "user" not in st.session_state: st.session_state.user=None
    if "page" not in st.session_state: st.session_state.page="home"
    if not st.session_state.user: page_login(); return

    if st.session_state.get("page")=="detail": page_course_detail(); return
    menu=sidebar_nav()

    if menu=="🏠 Beranda": page_home()
    elif menu=="📘 Kursus": page_courses()
    elif menu=="👤 Akun":
        st.title("👤 Akun Pengguna")
        u=st.session_state.user
        st.write(f"Nama: **{u['name']}**"); st.write(f"Email: {u['email']}")
        st.write(f"Role: {u['role']}")
        if st.button("🚪 Logout"):
            st.session_state.user=None; st.success("Logout berhasil."); time.sleep(1); st.rerun()

if __name__=="__main__":
    main()
