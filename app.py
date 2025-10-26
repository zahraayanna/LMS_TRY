import streamlit as st
from supabase import create_client
import time
from datetime import datetime
import json

# =========================
# === KONFIGURASI AWAL ===
# =========================
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* Background gradient */
    .main {
        background: linear-gradient(to bottom right, #f3e8ff, #ffe4f3);
        padding: 2rem;
        border-radius: 20px;
    }

    /* Card styling */
    div[data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        padding: 1rem;
    }

    /* Button */
    div.stButton > button {
        background: linear-gradient(90deg, #a855f7, #ec4899);
        color: white !important;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease-in-out;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(168,85,247,0.3);
    }

    /* Tabs */
    div[data-baseweb="tab-list"] button {
        font-weight: 600;
        color: #6b21a8;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f6f3ff;
    }

    </style>
""", unsafe_allow_html=True)


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# === AUTH FUNCTION ===
# =====================
import hashlib

def hash_sha256(password: str) -> str:
    """Buat hash SHA256 dari password."""
    return hashlib.sha256(password.encode()).hexdigest()


def login(email, password):
    # Ambil data user dari Supabase
    res = supabase.table("users").select("*").eq("email", email).execute()
    if not res.data:
        return None

    user = res.data[0]
    stored_pw = user.get("password_hash")

    if not stored_pw:
        return None

    # Hash input user dalam 2 format buat deteksi otomatis
    md5_hash = hashlib.md5(password.encode()).hexdigest()
    sha_hash = hash_sha256(password)

    # --- LOGIN OTOMATIS ---
    # 1️⃣ Kalau cocok SHA256 → login aman
    if stored_pw == sha_hash:
        return user

    # 2️⃣ Kalau cocok MD5 → ubah ke SHA256 biar aman
    elif stored_pw == md5_hash:
        supabase.table("users").update({"password_hash": sha_hash}).eq("email", email).execute()
        print(f"🔒 Password {email} otomatis diupgrade ke SHA256")
        return user

    # 3️⃣ Kalau cocok plaintext → ubah ke SHA256 juga
    elif stored_pw == password:
        supabase.table("users").update({"password_hash": sha_hash}).eq("email", email).execute()
        print(f"🔒 Password {email} otomatis diupgrade ke SHA256")
        return user

    return None


def register_user(name, email, password, role):
    """Registrasi user baru dengan password langsung di-hash SHA256."""
    hashed_pw = hash_sha256(password)

    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data:
        st.error("Email sudah terdaftar.")
        return False

    supabase.table("users").insert({
        "name": name,
        "email": email,
        "password_hash": hashed_pw,
        "role": role
    }).execute()

    st.success("Akun berhasil dibuat!")
    return True

# =====================
# === PAGE: LOGIN ===
# =====================
def page_login():
    st.markdown(
        """
        <style>
        .main { background: linear-gradient(145deg, #F6E6FF, #F8D3E2); color:#222 }
        h1, h2, h3, h4 { color: #3b2063; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🎓 ThinkVerse LMS")
    st.caption("Portal pembelajaran modern berbasis cloud Supabase")

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
                time.sleep(0.8)
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
            else:
                st.error("Email sudah terdaftar.")

    # --- RESET PASSWORD ---
    with tabs[2]:
        with st.form("forgot_pw_form_tab3"):
            email_fp = st.text_input("Email akun", key="fp_email_tab3")
            new_pw = st.text_input("Password baru", type="password", key="fp_pw_tab3")
            ok3 = st.form_submit_button("Reset Password")
        if ok3:
            res = supabase.table("users").update({"password_hash": new_pw}).eq("email", email_fp).execute()
            if res.data:
                st.success("Password berhasil direset!")
            else:
                st.error("Email tidak ditemukan.")


# ======================
# === DASHBOARD ===
# ======================
def page_dashboard():
    u = st.session_state.user
    st.sidebar.title("ThinkVerse LMS")
    st.sidebar.markdown(f"👋 **{u['name']}**\n\n📧 {u['email']}\n\nRole: *{u['role']}*")
    nav = st.sidebar.radio("Navigasi", ["🏠 Dashboard", "📘 Kursus", "👤 Akun"])
    if nav == "🏠 Dashboard":
        st.header("🏠 Dashboard Utama")
        st.info("Selamat datang di ThinkVerse LMS! Pilih menu di sebelah kiri untuk melanjutkan.")
    elif nav == "📘 Kursus":
        page_courses()
    elif nav == "👤 Akun":
        st.header("👤 Profil Pengguna")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()


# ======================
# === COURSE PAGE ===
# ======================
def page_courses():
    user = st.session_state.user  # ✅ Ambil user aktif
    st.header("🎓 My Courses")

    data = supabase.table("courses").select("*").execute().data
    if not data:
        st.info("No courses yet.")
        return

    for c in data:
        st.markdown(f"### {c['title']}")
        st.caption(c.get("description", ""))
        col1, col2 = st.columns([5, 1])
        with col2:
          open_course_id = None  # penanda sementara
    for c in data:
        st.markdown(f"### {c['title']}")
        st.caption(c.get("description", ""))
        col1, col2 = st.columns([5, 1])
        with col2:
            if st.button("📖 Open Course", key=f"open_{c['id']}"):
                open_course_id = c["id"]

    # Jalankan pindah halaman setelah loop selesai
    if open_course_id:
        st.session_state.current_course = open_course_id
        st.session_state.page = "course_detail"
        st.rerun()

    if user["role"] == "instructor":
        with st.expander("➕ Create New Course"):
            with st.form("new_course_form"):
                title = st.text_input("Course Title")
                desc = st.text_area("Description")
                yt = st.text_input("YouTube URL (optional)")
                ref = st.text_input("Reference Book URL (optional)")
                ok = st.form_submit_button("Create Course")
                if ok and title:
                    supabase.table("courses").insert({
                        "title": title,
                        "description": desc,
                        "youtube_url": yt,
                        "reference_book": ref,
                        "instructor_id": user["id"]
                    }).execute()
                    st.success("✅ New course created successfully!")
                    st.rerun()
                    
# ======================
# === COURSE DETAIL ===
# ======================
from io import BytesIO
import base64
import re
from datetime import datetime

# --- upload helper ---
def upload_to_supabase(file):
    """Upload file ke bucket thinkverse_uploads di Supabase."""
    if not file:
        return None
    file_bytes = file.read()
    file_path = f"uploads/{int(datetime.now().timestamp())}_{file.name}"
    supabase.storage.from_("thinkverse_uploads").upload(file_path, file_bytes)
    return f"{SUPABASE_URL}/storage/v1/object/public/thinkverse_uploads/{file_path}"


# --- halaman detail course ---
# ============================================
# PAGE: COURSE DETAIL — ThinkVerse v5.3
# Full LMS Course System (Supabase)
# ============================================

def page_course_detail():
    # --- Rerun safeguard ---
    if "current_course" not in st.session_state and "last_course" in st.session_state:
        st.session_state.current_course = st.session_state.last_course

    if "current_course" not in st.session_state:
        st.warning("⚠️ No course selected. Please return to the Courses page.")
        st.stop()

    cid = st.session_state.current_course
    user = st.session_state.user
    st.session_state.last_course = cid

    # --- Load course data ---
    try:
        c = supabase.table("courses").select("*").eq("id", cid).execute().data[0]
    except Exception as e:
        st.error(f"Error loading course data: {e}")
        return

    # --- Header ---
    st.title(f"📘 {c['title']}")
    st.caption(c.get("description", ""))

    # --- Tabs ---
    tabs = st.tabs([
        "🏠 Dashboard",
        "🕒 Attendance",
        "📦 Modules",
        "🧩 Assignments",
        "🧠 Quizzes",
        "📣 Announcements"
    ])

    # =====================================
    # DASHBOARD
    # =====================================
    with tabs[0]:
        st.subheader("🎯 Course Overview")

        st.markdown("### About this Course")
        st.write(c.get("description", "No description provided."))

        st.markdown("### 🎥 Course Video")
        yt_url = c.get("youtube_url", "")
        if yt_url:
            st.video(yt_url)
        else:
            st.info("No YouTube video attached.")

        st.markdown("### 📚 Reference Book (Embed)")
        ref_book = c.get("reference_book", "")
        if ref_book:
            st.markdown(f'<iframe src="{ref_book}" width="100%" height="500px"></iframe>', unsafe_allow_html=True)
        else:
            st.info("No embedded reference book.")

    # =====================================
    # ATTENDANCE
    # =====================================
    with tabs[1]:
        st.subheader("🕒 Attendance Tracker")

        att = supabase.table("attendance").select("*").eq("course_id", cid).execute().data
        if att:
            st.dataframe(att)
        else:
            st.info("No attendance records yet.")

        if user["role"] == "instructor":
            with st.form("add_attendance"):
                date = st.date_input("Date")
                topic = st.text_input("Topic")
                ok = st.form_submit_button("➕ Add Attendance")
                if ok and topic:
                    supabase.table("attendance").insert({
                        "course_id": cid,
                        "date": str(date),
                        "topic": topic
                    }).execute()
                    st.success("Attendance added successfully!")
                    st.rerun()

    # =====================================
    # MODULES
    # =====================================
    with tabs[2]:
        st.subheader("📦 Learning Modules")

        mods = supabase.table("modules").select("*").eq("course_id", cid).execute().data
        if mods:
            for m in mods:
                with st.expander(f"📘 {m['title']}"):
                    st.markdown(m.get("content", "No content."))
                    if m.get("video_url"):
                        st.video(m["video_url"])
        else:
            st.info("No modules added yet.")

        if user["role"] == "instructor":
            with st.form("add_module"):
                title = st.text_input("Module Title")
                content = st.text_area("Content (Markdown supported)")
                video_url = st.text_input("Video URL (optional)")
                ok = st.form_submit_button("➕ Add Module")
                if ok and title:
                    supabase.table("modules").insert({
                        "course_id": cid,
                        "title": title,
                        "content": content,
                        "video_url": video_url
                    }).execute()
                    st.success("Module added!")
                    st.rerun()

    # =====================================
    # ASSIGNMENTS
    # =====================================
    with tabs[3]:
        st.subheader("🧩 Assignments")

        asg = supabase.table("assignments").select("*").eq("course_id", cid).execute().data
        if asg:
            for a in asg:
                with st.expander(f"📄 {a['title']}"):
                    st.markdown(a.get("description", ""))
                    if a.get("embed_url"):
                        st.markdown(f'<iframe src="{a["embed_url"]}" width="100%" height="400px"></iframe>', unsafe_allow_html=True)
                    if user["role"] == "student":
                        st.write("### Submit Assignment")
                        file = st.file_uploader("Upload your work", key=f"up_{a['id']}")
                        if file:
                            st.success(f"✅ Submission received for '{a['title']}' (Simulated)")
        else:
            st.info("No assignments available.")

        if user["role"] == "instructor":
            with st.form("add_assignment"):
                title = st.text_input("Assignment Title")
                desc = st.text_area("Assignment Description")
                embed = st.text_input("Embed URL (Liveworksheet / YouTube / PDF Viewer)")
                file_type = st.selectbox("Accepted Submission Type", ["PDF", "Image", "Docx", "Any"])
                ok = st.form_submit_button("➕ Add Assignment")
                if ok and title:
                    supabase.table("assignments").insert({
                        "course_id": cid,
                        "title": title,
                        "description": desc,
                        "embed_url": embed,
                        "allowed_type": file_type
                    }).execute()
                    st.success("Assignment added!")
                    st.rerun()

    # =====================================
    # QUIZZES (FULL INTERACTIVE)
    # =====================================
    with tabs[4]:
        st.subheader("🧠 Quizzes")

        quizzes = supabase.table("quizzes").select("*").eq("course_id", cid).execute().data
        if quizzes:
            for q in quizzes:
                with st.expander(f"📝 {q['title']}"):
                    st.markdown(q.get("description", ""))
                    questions = supabase.table("quiz_questions").select("*").eq("quiz_id", q["id"]).execute().data
                    if questions:
                        for i, qs in enumerate(questions, 1):
                            st.markdown(f"**{i}. {qs['question']}**")
                            if qs["type"] == "multiple_choice":
                                choices = qs["choices"].split("|")
                                st.radio("Answer:", choices, key=f"q_{qs['id']}")
                            else:
                                st.text_input("Answer:", key=f"t_{qs['id']}")
                    else:
                        st.info("No questions yet.")
        else:
            st.info("No quizzes yet.")

        # --- Create quiz ---
        if user["role"] == "instructor":
            with st.form("add_quiz"):
                title = st.text_input("Quiz Title")
                desc = st.text_area("Quiz Description")
                ok = st.form_submit_button("➕ Create Quiz")
                if ok and title:
                    supabase.table("quizzes").insert({
                        "course_id": cid,
                        "title": title,
                        "description": desc
                    }).execute()
                    st.success("Quiz created!")
                    st.rerun()

        # --- Add Question to Quiz ---
        if user["role"] == "instructor" and quizzes:
            st.markdown("### ➕ Add Question to Quiz")
            quiz_list = {q["title"]: q["id"] for q in quizzes}
            selected_quiz = st.selectbox("Select Quiz", list(quiz_list.keys()))
            qid = quiz_list[selected_quiz]

            with st.form("add_question"):
                question = st.text_input("Question Text")
                q_type = st.selectbox("Type", ["multiple_choice", "short_answer"])
                if q_type == "multiple_choice":
                    choices = [st.text_input(f"Choice {ch}", key=f"ch_{i}") for i, ch in enumerate(["A", "B", "C", "D", "E"], 1)]
                    correct = st.selectbox("Correct Answer", ["A", "B", "C", "D", "E"])
                    ok = st.form_submit_button("➕ Add Question")
                    if ok and question:
                        supabase.table("quiz_questions").insert({
                            "quiz_id": qid,
                            "question": question,
                            "type": "multiple_choice",
                            "choices": "|".join(choices),
                            "correct_answer": correct
                        }).execute()
                        st.success("Question added successfully!")
                        st.rerun()
                else:
                    ans = st.text_input("Correct Answer")
                    ok = st.form_submit_button("➕ Add Question")
                    if ok and question:
                        supabase.table("quiz_questions").insert({
                            "quiz_id": qid,
                            "question": question,
                            "type": "short_answer",
                            "correct_answer": ans
                        }).execute()
                        st.success("Question added!")
                        st.rerun()

    # =====================================
    # ANNOUNCEMENTS
    # =====================================
    with tabs[5]:
        st.subheader("📣 Course Announcements")

        ann = supabase.table("announcements").select("*").eq("course_id", cid).execute().data
        if ann:
            for a in ann:
                st.markdown(f"**📢 {a['title']}** — *{a['date']}*")
                st.markdown(a["content"])
                st.divider()
        else:
            st.info("No announcements yet.")

        if user["role"] == "instructor":
            with st.form("add_announcement"):
                title = st.text_input("Title")
                content = st.text_area("Content")
                ok = st.form_submit_button("📣 Post Announcement")
                if ok and title:
                    from datetime import date
                    supabase.table("announcements").insert({
                        "course_id": cid,
                        "title": title,
                        "content": content,
                        "date": str(date.today())
                    }).execute()
                    st.success("Announcement posted!")
                    st.rerun()

# ======================
# === ROUTING ===
# ======================
def main():
    if "user" not in st.session_state:
        page_login()
        return

    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    if st.session_state.page == "dashboard":
        page_dashboard()
    elif st.session_state.page == "courses":
        page_courses()
    elif st.session_state.page == "course_detail":
        page_course_detail()

if __name__ == "__main__":
    main()

















