import streamlit as st
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

import uuid
from supabase import create_client
import time
from datetime import datetime
import json

# =========================
# === KONFIGURASI AWAL ===
# =========================

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
    st.title("🎓 ThinkVerse LMS — Login Portal")
    st.caption("Masuk untuk melanjutkan ke ruang belajar digital kamu.")

    tabs = st.tabs(["🔑 Login", "🆕 Register", "🔁 Forgot Password"])

    # --- LOGIN ---
    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login")

        if ok:
            user = login(email, pw)
            if user:
                st.session_state.user = user
                st.session_state.page = "dashboard"  # ⬅ pindah halaman otomatis
                st.success(f"Selamat datang, {user['name']} 👋")
                st.rerun()
            else:
                st.error("❌ Email atau password salah.")

    # --- REGISTER ---
    with tabs[1]:
        with st.form("reg_form"):
            name = st.text_input("Nama Lengkap")
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            role = st.selectbox("Peran", ["student", "instructor"])
            ok2 = st.form_submit_button("Daftar Akun Baru")

        if ok2:
            if register_user(name, email, pw, role):
                st.success("✅ Akun berhasil dibuat! Silakan login di tab pertama.")

    # --- LUPA PASSWORD ---
    with tabs[2]:
        with st.form("forgot_pw_form"):
            email_fp = st.text_input("Masukkan email kamu")
            new_pw = st.text_input("Password baru", type="password")
            new_pw2 = st.text_input("Ulangi password baru", type="password")
            ok3 = st.form_submit_button("Reset Password")

        if ok3:
            if new_pw != new_pw2:
                st.error("Password tidak sama.")
            elif reset_password(email_fp, new_pw):
                st.success("✅ Password berhasil direset! Silakan login ulang.")

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
    import uuid
    import random, string
    st.title("🎓 My Courses")

    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in to continue.")
        return

    # === INSTRUCTOR ONLY SECTION ===
    if user["role"] == "instructor":
        st.subheader("➕ Create New Course")

        with st.form("create_course_form", clear_on_submit=True):
            new_code = st.text_input("Course Code (unique, e.g. PHY101)")
            new_title = st.text_input("Course Title")
            new_desc = st.text_area("Course Description")
            yt_url = st.text_input("YouTube URL (optional)")
            access_code = st.text_input("Access Code (optional, auto-generated if empty)")
            submit = st.form_submit_button("Create Course")

        if submit:
            if not new_code.strip() or not new_title.strip():
                st.warning("Course code and title cannot be empty.")
            else:
                existing = supabase.table("courses").select("*") \
                    .eq("code", new_code.strip()) \
                    .eq("instructor_email", user["email"]) \
                    .execute().data

                if existing:
                    st.warning("⚠️ You already have a course with this code!")
                else:
                    if not access_code.strip():
                        access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

                    instr_row = supabase.table("users").select("id").eq("email", user["email"]).execute().data
                    instructor_id = instr_row[0]["id"] if instr_row else None

                    supabase.table("courses").insert({
                        "code": new_code.strip(),
                        "title": new_title.strip(),
                        "description": new_desc.strip(),
                        "youtube_url": yt_url or None,
                        "access_code": access_code,
                        "instructor_id": instructor_id,
                        "instructor_email": user["email"]
                    }).execute()

                    st.success(f"✅ Course '{new_title}' created successfully! Access code: `{access_code}`")
                    st.rerun()

    # === STUDENT SECTION ===
    else:
        st.subheader("📥 Join Course with Access Code")

        # siswa wajib masukin kode akses
        with st.form("join_form", clear_on_submit=True):
            join_code = st.text_input("Enter Course Access Code", placeholder="e.g. X7J9Q2")
            join_submit = st.form_submit_button("Join")

        if join_submit:
            if not join_code.strip():
                st.warning("Please enter a course access code.")
            else:
                # cek apakah access code valid
                course = supabase.table("courses").select("*").eq("access_code", join_code.strip()).execute().data
                if not course:
                    st.error("❌ Invalid access code. Please check with your instructor.")
                else:
                    course_id = course[0]["id"]
                    enrolled = supabase.table("enrollments").select("*") \
                        .eq("user_id", user["id"]) \
                        .eq("course_id", course_id).execute().data

                    if enrolled:
                        st.info("📚 You are already enrolled in this course.")
                    else:
                        supabase.table("enrollments").insert({
                            "user_id": user["id"],
                            "course_id": course_id,
                            "role": "student"
                        }).execute()
                        st.success(f"✅ Successfully joined the course '{course[0]['title']}'!")
                        st.rerun()

    st.divider()
    st.subheader("📘 My Courses")

    # === LOAD COURSES ===
    if user["role"] == "instructor":
        # tampilkan semua course yang dibuat instruktur
        courses = supabase.table("courses").select("*").eq("instructor_email", user["email"]).execute().data
    else:
        # siswa cuma bisa lihat course yang SUDAH dia join
        enrolled = supabase.table("enrollments").select("course_id").eq("user_id", user["id"]).execute().data
        course_ids = [c["course_id"] for c in enrolled]
        courses = supabase.table("courses").select("*").in_("id", course_ids).execute().data if course_ids else []

    if not courses:
        if user["role"] == "instructor":
            st.info("📭 You haven't created any courses yet.")
        else:
            st.info("📭 You haven't joined any courses yet.")
        return

    # === DISPLAY COURSE LIST ===
    for c in courses:
        with st.container():
            st.markdown(f"### 🎓 {c['title']}")
            st.caption(c.get("description", "No description provided."))
            st.markdown(f"**Course Code:** `{c['code']}`")

            if user["role"] == "instructor":
                st.markdown(f"**Access Code:** `{c.get('access_code', '-')}`")

            unique_key = f"open_{c['id']}_{uuid.uuid4().hex[:6]}"
           

            if st.button("📖 Open Course", key=f"open_{c['id']}"):
                st.session_state.current_course = c["id"]
                st.session_state.last_course = c["id"]
                st.session_state.page = "course_detail"

                # 🚀 rerender langsung halaman detail
                st.switch_page("app.py")  # pastikan nama file Streamlit utama kamu sesuai

            st.markdown("---")

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


# ============================================
# PAGE: COURSE DETAIL — ThinkVerse v5.4
# (All previous features + delete system)
# ============================================
def page_course_detail():
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

    st.title(f"📘 {c['title']}")
    st.caption(c.get("description", ""))

    # === ACTION BUTTONS ===
    col1, col2 = st.columns([0.25, 0.75])

    # 🔙 Tombol Kembali ke Courses
    with col1:
        if st.button("🔙 Back to Courses"):
            for key in ["current_course", "last_course"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.page = "dashboard"
            st.session_state.user = st.session_state.get("user")
            st.rerun()

    # 🚪 Tombol Resign dari Course (student only)
    with col2:
        if user and user["role"] == "student":
            if st.button("🚪 Leave this Course"):
                confirm = st.checkbox("Yes, I really want to leave this course")
                if confirm:
                    supabase.table("enrollments").delete().eq("user_id", user["id"]).eq("course_id", cid).execute()
                    st.success("✅ You have successfully left this course.")
                    time.sleep(1)
                    # reset state dan arahkan kembali via router utama
                    st.session_state.current_course = None
                    st.session_state.last_course = None
                    st.session_state.page = "dashboard"
                    st.session_state._nav_back = True
                    st.stop()


    # ⚠️ DELETE COURSE (Instructor only)
    if user["role"] == "instructor" and user["email"] == c["instructor_email"]:
        with st.expander("⚠️ Danger Zone — Delete this Course"):
            st.warning("This will permanently delete the course and all related data (modules, assignments, quizzes, announcements).")
            confirm = st.checkbox("Yes, I understand and want to delete this course")
            if confirm and st.button("🗑️ Delete Course Permanently"):
                supabase.table("modules").delete().eq("course_id", cid).execute()
                supabase.table("assignments").delete().eq("course_id", cid).execute()
                supabase.table("quiz_questions").delete().eq("quiz_id", cid).execute()
                supabase.table("quizzes").delete().eq("course_id", cid).execute()
                supabase.table("announcements").delete().eq("course_id", cid).execute()
                supabase.table("attendance").delete().eq("course_id", cid).execute()
                supabase.table("enrollments").delete().eq("course_id", cid).execute()
                supabase.table("courses").delete().eq("id", cid).execute()
                st.success("✅ Course deleted successfully!")
                time.sleep(1)
                st.session_state.page = "dashboard"
                st.session_state.current_course = None
                st.rerun()

    # --- Tabs ---
    tabs = st.tabs([
        "📚 Overview",
        "🕒 Attendance",
        "📦 Learning Modules",
        "📋 Assignments",
        "🧠 Quizzes",
        "📣 Announcements"
    ])

    # === Deteksi tab aktif dari session state ===
    active_tab = st.session_state.get("active_tab", "overview")
    
    # index tab sesuai urutan di atas
    tab_index = {
        "overview": 0,
        "attendance": 1,
        "module": 2,
        "assignment": 3,
        "quiz": 4,
        "announcement": 5
    }


    # =====================================
    # DASHBOARD
    # =====================================
    with tabs[0]:
        st.markdown("## 🎯 Course Overview")

        c = supabase.table("courses").select("*").eq("id", cid).execute().data[0]
        st.markdown("### About this Course")
        st.write(c.get("description") or "_No description provided._")

        st.markdown("### 🎥 Course Video")
        if c.get("youtube_url"):
            st.video(c["youtube_url"])
        else:
            st.info("No YouTube video attached.")

        st.markdown("### 📚 Reference Book (Embed)")
        if c.get("reference_book"):
            st.components.v1.iframe(c["reference_book"], height=400)
        else:
            st.info("No embedded reference book.")

        if user["role"] == "instructor":
            st.divider()
            st.subheader("🛠️ Edit Course Dashboard")
            with st.form("edit_course_dashboard"):
                new_desc = st.text_area("Update Course Description", c.get("description", ""), height=150)
                new_yt = st.text_input("YouTube Video URL", c.get("youtube_url", ""))
                new_book = st.text_input("Reference Book Embed URL (iframe link)", c.get("reference_book", ""))
                save_btn = st.form_submit_button("💾 Save Changes")
            if save_btn:
                supabase.table("courses").update({
                    "description": new_desc,
                    "youtube_url": new_yt,
                    "reference_book": new_book
                }).eq("id", cid).execute()
                st.success("✅ Course dashboard updated successfully!")
                st.rerun()

    # =====================================
    # ATTENDANCE (Improved)
    # =====================================
    with tabs[1]:
        st.subheader("🕒 Attendance Tracker")
    
        # ambil semua sesi absensi untuk course ini
        sessions = supabase.table("attendance_sessions").select("*").eq("course_id", cid).execute().data
    
        if user["role"] == "instructor":
            with st.form("create_attendance_session"):
                st.markdown("### ➕ Create Attendance Session")
                date = st.date_input("Session Date")
                start_time = st.time_input("Start Time")
                end_time = st.time_input("Attendance Deadline (End Time)")
                note = st.text_input("Session Note (optional)")
                ok = st.form_submit_button("Create Session")
    
                if ok:
                    start_dt = datetime.combine(date, start_time)
                    deadline_dt = datetime.combine(date, end_time)
    
                    if deadline_dt <= start_dt:
                        st.error("⚠️ Deadline must be after start time.")
                    else:
                        data_to_insert = {
                            "course_id": cid,
                            "date": date.strftime("%Y-%m-%d"),
                            "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "deadline": deadline_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "note": note or None
                        }
    
                        try:
                            result = supabase.table("attendance_sessions").insert(data_to_insert).execute()
                            st.success("✅ Attendance session created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Supabase error: {e}")
                            st.json(data_to_insert)
    
        if sessions:
            for s in sessions:
                st.markdown(f"#### 📅 {s['date']} — {s.get('note', '_No note_') or '_No note_'}")
    
                # tampilkan deadline
                if s.get("deadline"):
                    st.caption(f"🕔 Deadline: {s['deadline']}")
    
                records = supabase.table("attendance").select("*").eq("session_id", s["id"]).execute().data
    
                if user["role"] == "instructor":
                    st.write("**Attendance Records:**")
                    if records:
                        names = []
                        for r in records:
                            u = supabase.table("users").select("name").eq("id", r["user_id"]).execute().data
                            if u:
                                names.append(u[0]["name"])
                        st.markdown(", ".join(names) if names else "_No students marked present yet._")
                    else:
                        st.info("No attendance yet for this session.")
    
                    if st.button(f"❌ Delete Session ({s['date']})", key=f"del_sess_{s['id']}"):
                        supabase.table("attendance").delete().eq("session_id", s["id"]).execute()
                        supabase.table("attendance_sessions").delete().eq("id", s["id"]).execute()
                        st.success("🗑️ Session deleted successfully!")
                        st.rerun()
    
                elif user["role"] == "student":
                    existing = supabase.table("attendance").select("*") \
                        .eq("session_id", s["id"]).eq("user_id", user["id"]).execute().data
    
                    if existing:
                        st.success("✅ You are marked present for this session.")
                    else:
                        now = datetime.now()
                        try:
                            deadline_dt = datetime.strptime(s["deadline"], "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            deadline_dt = None
    
                        if deadline_dt and now > deadline_dt:
                            st.warning("⏰ Attendance time is over. You are marked absent.")
                        else:
                            if st.button(f"🖋️ Mark as Present ({s['date']})", key=f"mark_{s['id']}"):
                                data_att = {
                                    "session_id": s["id"],
                                    "course_id": cid,
                                    "user_id": user["id"],
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "status": "present"
                                }
                                try:
                                    supabase.table("attendance").insert(data_att).execute()
                                    st.success("✅ Your attendance has been recorded!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error saving attendance: {e}")
                                    st.json(data_att)
        else:
            st.info("No attendance sessions created yet.")


    # =====================================
    # MODULES
    # =====================================
    with tabs[2]:
        from datetime import datetime
        import markdown, re
        import streamlit.components.v1 as components
    
        st.subheader("📦 Learning Activities (Modules)")
    
        # === Pastikan CID valid ===
        if not cid:
            cid = st.session_state.get("current_course") or st.session_state.get("last_course")
        if not cid:
            st.error("⚠️ Course ID not found.")
            st.stop()
    
        st.session_state.current_course = cid
    
        # === Load data utama ===
        try:
            mods = (
                supabase.table("modules")
                .select("*")
                .eq("course_id", int(cid))
                .order("order_index", desc=False)
                .execute()
                .data
                or []
            )
        except Exception as e:
            st.error(f"❌ Failed to load modules: {e}")
            mods = []
    
        # === Load link module–quiz–assignment ===
        try:
            module_links = supabase.table("module_link").select("*").eq("course_id", cid).execute().data or []
        except Exception:
            module_links = []
    
        # === Load quiz dan assignment ===
        all_quizzes = supabase.table("quizzes").select("*").eq("course_id", cid).execute().data or []
        all_assignments = supabase.table("assignments").select("*").eq("course_id", cid).execute().data or []
    
        # === Load progress siswa ===
        if user["role"] == "student":
            try:
                progress_data = (
                    supabase.table("module_progress")
                    .select("*")
                    .eq("user_id", user["id"])
                    .eq("course_id", cid)
                    .execute()
                    .data
                )
                progress_dict = {p["module_id"]: p["status"] for p in progress_data}
            except Exception:
                progress_dict = {}
    
            total_modules = len(mods)
            completed_count = sum(1 for s in progress_dict.values() if s == "completed")
            ratio = completed_count / total_modules if total_modules > 0 else 0
    
            st.progress(ratio)
            st.caption(f"Learning Progress: {completed_count}/{total_modules} modules completed")
    
            if completed_count == total_modules and total_modules > 0:
                st.success("🎉 Congratulations! You have completed all learning activities.")
    
        # === Tampilkan setiap modul ===
        if mods:
            previous_completed = True
            for idx, m in enumerate(mods, start=1):
                title = f"📘 {idx}. {m['title']}"
                status = progress_dict.get(m["id"], "not_started") if user["role"] == "student" else None
                locked = not previous_completed and user["role"] == "student"
    
                # ikon status
                status_icon = ""
                if status == "completed":
                    status_icon = "✅"
                elif status == "in_progress":
                    status_icon = "⏳"
                elif locked:
                    status_icon = "🔒"
    
                with st.expander(f"{status_icon} {title}", expanded=(not locked)):
                    if locked:
                        st.warning("🔒 This module is locked. Complete the previous module first.")
                        continue
    
                    # === Auto set "in progress" saat dibuka ===
                    if user["role"] == "student":
                        existing = (
                            supabase.table("module_progress")
                            .select("id")
                            .eq("user_id", user["id"])
                            .eq("module_id", m["id"])
                            .execute()
                            .data
                        )
                        if not existing:
                            supabase.table("module_progress").insert({
                                "user_id": user["id"],
                                "module_id": m["id"],
                                "course_id": int(cid),
                                "status": "in_progress",
                                "updated_at": datetime.now().isoformat(),
                            }).execute()
    
                    # === Render konten modul ===
                    raw_content = m.get("content", "No content available.")
                    embed_pattern = r"<embed\s+src=\"([^\"]+)\"(?:\s+width=\"(\d+)\"|\s*)?(?:\s+height=\"(\d+)\"|\s*)?>"
    
                    def replace_embed(match):
                        src = match.group(1)
                        width = match.group(2) or "560"
                        height = match.group(3) or "315"
                        return f'<div style="text-align:center; margin:16px 0;"><iframe src="{src}" width="{width}" height="{height}" frameborder="0" allowfullscreen></iframe></div>'
    
                    content_with_embeds = re.sub(embed_pattern, replace_embed, raw_content)
                    rendered_md = markdown.markdown(content_with_embeds, extensions=["fenced_code", "tables", "md_in_html"])
    
                    html_content = f"""
                    <div style="font-size:16px; line-height:1.7; text-align:justify;">
                        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
                        <script id="MathJax-script" async
                            src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
                        <article class="markdown-body">{rendered_md}</article>
                    </div>
                    """
                    components.html(html_content, height=600, scrolling=True)
    
                    if m.get("video_url"):
                        st.video(m["video_url"])
    
                    # === Related Activities (Quiz & Assignment) ===
                    related_quiz = [l for l in module_links if l["module_id"] == m["id"] and l["type"] == "quiz"]
                    related_asg = [l for l in module_links if l["module_id"] == m["id"] and l["type"] == "assignment"]
                    
                    if related_quiz or related_asg:
                        st.markdown("### 🧩 Related Activities")
                    
                        # === Tampilkan quiz terkait ===
                        for i, rq in enumerate(related_quiz):
                            q = next((q for q in all_quizzes if q["id"] == rq["target_id"]), None)
                            if q:
                                stable_key = f"quiz_{cid}_{m['id']}_{q['id']}_{i}"
                                st.markdown(f"🧠 **Quiz:** {q.get('title', 'Untitled Quiz')}")
                                if st.button(f"➡️ Open Quiz", key=f"open_quiz_{m['id']}_{q['id']}"):
                                    st.session_state.selected_quiz_id = q["id"]
                                    st.session_state.active_tab = "quiz"
                                    st.rerun()
                    
                        # === Tampilkan assignment terkait ===
                        for j, ra in enumerate(related_asg):
                            a = next((a for a in all_assignments if a["id"] == ra["target_id"]), None)
                            if a:
                                stable_key = f"asg_{cid}_{m['id']}_{a['id']}_{j}"
                                st.markdown(f"📋 **Assignment:** {a.get('title', 'Untitled Assignment')}")
                                if st.button(f"➡️ Open Assignment", key=f"open_asg_{m['id']}_{asg_data['id']}"):
                                    st.session_state.selected_assignment_id = asg_data["id"]
                                    st.session_state.active_tab = "assignment"
                                    st.rerun()

    
                    # === Mark as Complete ===
                    if user["role"] == "student" and status != "completed":
                        done_key = f"done_{cid}_{m['id']}"
                        if st.button("✅ Mark as Completed", key=done_key):
                            existing = (
                                supabase.table("module_progress")
                                .select("id")
                                .eq("user_id", user["id"])
                                .eq("module_id", m["id"])
                                .execute()
                                .data
                            )
                            if not existing:
                                supabase.table("module_progress").insert({
                                    "user_id": user["id"],
                                    "module_id": m["id"],
                                    "course_id": int(cid),
                                    "status": "completed",
                                    "updated_at": datetime.now().isoformat(),
                                }).execute()
                            else:
                                supabase.table("module_progress").update({
                                    "status": "completed",
                                    "updated_at": datetime.now().isoformat(),
                                }).eq("user_id", user["id"]).eq("module_id", m["id"]).execute()
                            st.success("🎯 Module marked as completed!")
                            st.rerun()

                    # === Guru ===
                    if user["role"] == "instructor":
                        st.divider()
                        col1, col2, col3, col4, col5 = st.columns(5)
                    
                        with col1:
                            edit_key = f"edit_{cid}_{m['id']}"
                            if st.button(f"📝 Edit", key=edit_key):
                                st.session_state.edit_module_id = m["id"]
                                st.session_state.edit_module_data = m
                                st.session_state.show_edit_form = True
                                st.rerun()
                    
                        with col2:
                            del_key = f"del_{cid}_{m['id']}"
                            if st.button(f"🗑️ Delete", key=del_key):
                                supabase.table("modules").delete().eq("id", m["id"]).execute()
                                st.success(f"✅ Module '{m['title']}' deleted successfully!")
                                st.rerun()
                    
                        # 🔁 Tombol Reorder
                        with col3:
                            if idx > 1:
                                move_up_key = f"moveup_{cid}_{m['id']}"
                                if st.button("⬆️ Move Up", key=move_up_key):
                                    prev_module = mods[idx - 2]  # modul sebelumnya
                                    supabase.table("modules").update({"order_index": prev_module["order_index"]}).eq("id", m["id"]).execute()
                                    supabase.table("modules").update({"order_index": m["order_index"]}).eq("id", prev_module["id"]).execute()
                                    st.rerun()
                    
                        with col4:
                            if idx < len(mods):
                                move_down_key = f"movedown_{cid}_{m['id']}"
                                if st.button("⬇️ Move Down", key=move_down_key):
                                    next_module = mods[idx]
                                    supabase.table("modules").update({"order_index": next_module["order_index"]}).eq("id", m["id"]).execute()
                                    supabase.table("modules").update({"order_index": m["order_index"]}).eq("id", next_module["id"]).execute()
                                    st.rerun()
                    
                        with col5:
                            with st.form(f"link_form_{cid}_{m['id']}"):
                                link_type = st.selectbox("Link Type", ["quiz", "assignment"], key=f"linktype_{cid}_{m['id']}")
                                available = {q["title"]: q["id"] for q in all_quizzes} if link_type == "quiz" else {a["title"]: a["id"] for a in all_assignments}
                                if available:
                                    target = st.selectbox("Select Target", list(available.keys()), key=f"target_{cid}_{m['id']}")
                                    if st.form_submit_button("🔗 Link"):
                                        supabase.table("module_link").insert({
                                            "course_id": cid,
                                            "module_id": m["id"],
                                            "type": link_type,
                                            "target_id": available[target],
                                        }).execute()
                                        st.success(f"✅ {link_type.title()} linked successfully!")
                                        st.rerun()
                                else:
                                    st.info(f"No available {link_type}s to link.")

                    previous_completed = (
                        progress_dict.get(m["id"]) == "completed" if user["role"] == "student" else True
                    )
    
        else:
            st.info("No modules yet for this course.")
    
        # === FORM EDIT MODUL ===
        if st.session_state.get("show_edit_form"):
            m = st.session_state.edit_module_data
            st.markdown("## ✏️ Edit Module")
            with st.form("edit_module_form"):
                new_title = st.text_input("Module Title", m["title"])
                new_content = st.text_area("Content (Markdown + LaTeX supported)", m["content"], height=200)
                new_video = st.text_input("Video URL (optional)", m.get("video_url", ""))
                update_btn = st.form_submit_button("💾 Save Changes")
                if update_btn:
                    supabase.table("modules").update({
                        "title": new_title,
                        "content": new_content,
                        "video_url": new_video,
                    }).eq("id", m["id"]).execute()
                    st.success("✅ Module updated successfully!")
                    st.session_state.show_edit_form = False
                    st.rerun()
    
        # === TAMBAH MODUL BARU ===
        if user["role"] == "instructor":
            st.divider()
            st.markdown("### ➕ Add New Learning Activity")
    
            with st.form("add_module_rich", clear_on_submit=True):
                title = st.text_input("Module Title")
                order_index = st.number_input("Order (position in sequence)", min_value=1, value=len(mods) + 1)
                content = st.text_area("Content (Markdown + LaTeX supported)", height=200)
                uploaded_image = st.file_uploader("Upload Image (optional)", type=["png", "jpg", "jpeg"])
                video_url = st.text_input("Video URL (optional)")
                submit_btn = st.form_submit_button("💾 Add Module")
    
                if submit_btn:
                    if not title.strip():
                        st.warning("Please enter a module title.")
                    else:
                        img_markdown = ""
                        if uploaded_image:
                            img_bytes = uploaded_image.read()
                            file_path = f"uploads/{int(datetime.now().timestamp())}_{uploaded_image.name}"
                            supabase.storage.from_("thinkverse_uploads").upload(file_path, img_bytes)
                            img_url = f"{SUPABASE_URL}/storage/v1/object/public/thinkverse_uploads/{file_path}"
                            img_markdown = f"\n\n![Uploaded Image]({img_url})"
    
                        final_content = (content or "") + (img_markdown or "")
                        supabase.table("modules").insert({
                            "course_id": int(cid),
                            "title": title.strip(),
                            "order_index": int(order_index),
                            "content": final_content.strip(),
                            "video_url": video_url.strip() if video_url else None,
                        }).execute()
                        st.success(f"✅ Module '{title}' added successfully!")
                        st.rerun()








    # =====================================
    # ASSIGNMENTS
    # =====================================
    with tabs[3]:
        st.subheader("📋 Assignments")
    
        assignments = supabase.table("assignments").select("*").eq("course_id", cid).execute().data
        selected_asg_id = st.session_state.get("selected_assignment_id")
    
        if assignments:
            for a in assignments:
                expanded = selected_asg_id == a["id"]  # otomatis buka assignment yg diklik
                with st.expander(f"📄 {a['title']}", expanded=expanded):
                    if expanded:
                        # reset biar gak auto expand terus
                        st.session_state.selected_assignment_id = None
    
                    st.markdown(f"**Description:**\n\n{a.get('description', '_No description_')}")
    
                    if a.get("file_url"):
                        st.markdown(f"[📎 Download File]({a['file_url']})")
    
                    if user["role"] == "student":
                        uploaded = st.file_uploader("Upload your work:", key=f"upload_{a['id']}")
                        if uploaded and st.button("📤 Submit", key=f"submit_{a['id']}"):
                            try:
                                file_bytes = uploaded.read()
                                file_path = f"assignments/{user['id']}_{int(datetime.now().timestamp())}_{uploaded.name}"
                                supabase.storage.from_("thinkverse_uploads").upload(file_path, file_bytes)
                                file_url = f"{SUPABASE_URL}/storage/v1/object/public/thinkverse_uploads/{file_path}"
                                supabase.table("assignment_submissions").insert({
                                    "assignment_id": a["id"],
                                    "user_id": user["id"],
                                    "file_url": file_url,
                                    "submitted_at": str(datetime.now())
                                }).execute()
                                st.success("✅ Assignment submitted successfully!")
                            except Exception as e:
                                st.error(f"❌ Failed to upload: {e}")
        else:
            st.info("No assignments yet.")


        # === Load Assignments ===
        try:
            asg_response = supabase.table("assignments").select("*").eq("course_id", cid).execute()
            asg = asg_response.data or []
        except Exception as e:
            st.error(f"❌ Failed to load assignments: {e}")
            asg = []

        # === Display Assignments ===
        if asg:
            for a in asg:
                with st.expander(f"📄 {a['title']}"):
                    st.markdown(a.get("description", "No description provided."))

                    # === Smart Embed Handling ===
                    if a.get("embed_url"):
                        st.markdown("### 📎 Embedded Worksheet / Resource:")
                        embed_link = a["embed_url"].strip()

                        # 🔹 Jika link dari Liveworksheet → tampilkan tombol redirect, bukan iframe
                        if "liveworksheets.com" in embed_link:
                            st.warning("⚠️ Liveworksheet cannot be embedded directly due to site restrictions.")
                            st.markdown(
                                f"""
                                <div style='text-align:center;'>
                                    <a href="{embed_link}" target="_blank" 
                                       style='background:linear-gradient(90deg,#FF8C00,#FF4081);
                                              color:white;
                                              padding:10px 20px;
                                              border-radius:8px;
                                              text-decoration:none;
                                              font-weight:600;'>
                                       🔗 Open Liveworksheet
                                    </a>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # 🔹 Kalau file HTML publik → tampilkan embed iframe langsung
                        elif embed_link.endswith(".html"):
                            try:
                                components.iframe(embed_link, height=700, scrolling=True)
                            except Exception as e:
                                st.warning(f"⚠️ Could not load embedded HTML: {e}")

                        # 🔹 Kalau link dari platform lain (YouTube, Google Form, dst)
                        elif re.match(r"^https?://", embed_link):
                            st.markdown(f"[🌐 Open Resource]({embed_link})")
                        else:
                            st.info("ℹ️ Invalid embed link provided.")

                    # === Student submission ===
                    if user["role"] == "student":
                        st.markdown("### ✏️ Submit Assignment")
                        file = st.file_uploader("Upload your work (PDF, DOCX, ZIP, etc.)", key=f"up_{a['id']}")
                        if file:
                            st.success(f"✅ Submission received for '{a['title']}' (Simulated)")

                    # === Instructor delete ===
                    if user["role"] == "instructor":
                        if st.button(f"🗑️ Delete Assignment '{a['title']}'", key=f"del_asg_{a['id']}"):
                            supabase.table("assignments").delete().eq("id", a["id"]).execute()
                            st.success("✅ Assignment deleted!")
                            st.rerun()
        else:
            st.info("📭 No assignments available.")

        # === Add new assignment (Instructor only) ===
        if user["role"] == "instructor":
            st.divider()
            st.markdown("### ➕ Add New Assignment")

            with st.form("add_assignment", clear_on_submit=True):
                title = st.text_input("Assignment Title")
                desc = st.text_area("Assignment Description", height=100)
                embed_url = st.text_input(
                    "Embed URL (Link to Liveworksheet, Google Form, or HTML resource)"
                )

                submit_asg = st.form_submit_button("💾 Add Assignment")

                if submit_asg:
                    if not title.strip():
                        st.warning("⚠️ Please enter a title.")
                    else:
                        try:
                            supabase.table("assignments").insert({
                                "course_id": cid,
                                "title": title.strip(),
                                "description": desc.strip() if desc else "",
                                "embed_url": embed_url.strip() if embed_url else None
                            }).execute()

                            st.success(f"✅ Assignment '{title}' added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add assignment: {e}")

                            
    # =====================================
    # QUIZZES (FULL INTERACTIVE)
    # =====================================
    with tabs[4]:
        import streamlit.components.v1 as components
        import re, markdown
    
        st.subheader("🧠 Quizzes")
    
        quizzes = supabase.table("quizzes").select("*").eq("course_id", cid).execute().data
        selected_quiz_id = st.session_state.get("selected_quiz_id")
    
        if quizzes:
            for q in quizzes:
                expanded = selected_quiz_id == q["id"]  # auto buka quiz yang diklik dari modul
    
                with st.expander(f"📝 {q['title']}", expanded=expanded):
                    # setelah terbuka, hapus selection biar gak auto-expand terus
                    if expanded:
                        st.session_state.selected_quiz_id = None
                    ...

        # === Load all quizzes for this course ===
        quizzes = supabase.table("quizzes").select("*").eq("course_id", cid).execute().data

        if quizzes:
            for q in quizzes:
                with st.expander(f"📝 {q['title']}"):

                    # === Smart Description Rendering (Markdown + YouTube Embed) ===
                    desc = q.get("description", "")
                    if desc:
                        st.markdown("### 📘 Quiz Description:")

                        # Cek apakah mengandung link YouTube
                        youtube_match = re.search(
                            r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w\-]+)",
                            desc,
                        )
                        if youtube_match:
                            youtube_url = youtube_match.group(1)
                            video_id = (
                                youtube_url.split("v=")[-1]
                                if "v=" in youtube_url
                                else youtube_url.split("/")[-1]
                            )
                            st.video(f"https://www.youtube.com/watch?v={video_id}")

                            # Hapus link YouTube dari deskripsi agar tidak dobel
                            desc = desc.replace(youtube_url, "")

                        # Render Markdown dan LaTeX dari deskripsi
                        if desc.strip():
                            rendered_md = markdown.markdown(
                                desc, extensions=["fenced_code", "tables", "md_in_html"]
                            )    
                            html_content = f"""
                            <div style="font-size:16px; line-height:1.6;">
                                <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
                                <script id="MathJax-script" async
                                    src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
                                </script>
                                {rendered_md}
                            </div>
                            """
                            components.html(html_content, height=250, scrolling=True)

                    # === Show quiz questions ===
                    questions = (
                        supabase.table("quiz_questions").select("*").eq("quiz_id", q["id"]).execute().data
                    )

                    if questions:
                        st.markdown("### ✏️ Jawab Semua Pertanyaan di Bawah:")

                        answers = {}

                        for i, qs in enumerate(questions, 1):
                            st.markdown(f"**{i}. {qs['question']}**")

                            if qs["type"] == "multiple_choice":
                                choices = qs["choices"].split("|")
                                ans = st.radio(
                                    "Pilih jawaban:",
                                    choices,
                                    key=f"ans_{qs['id']}"
                                )
                            else:
                                ans = st.text_input(
                                    "Jawaban singkat:",
                                    key=f"ans_{qs['id']}"
                                )

                            answers[qs["id"]] = ans

                        # === Tombol Kumpulkan Jawaban ===
                        if user["role"] == "student":
                            if st.button("✅ Kumpulkan Jawaban", key=f"submit_quiz_{q['id']}"):
                                score = 0
                                total = len(questions)

                                for qs in questions:
                                    correct = qs["correct_answer"].strip()
                                    user_ans = answers.get(qs["id"], "").strip()

                                    if qs["type"] == "multiple_choice":
                                        if user_ans == correct:
                                            score += 1
                                    else:
                                        if user_ans.lower() == correct.lower():
                                            score += 1

                                # === Menampilkan hasil ===
                                st.success(f"🎉 Quiz Selesai! Skor kamu: {score}/{total}")

                                # === (Opsional) Simpan hasil ke database ===
                                try:
                                    supabase.table("quiz_submissions").insert({
                                        "quiz_id": q["id"],
                                        "user_id": user["id"],
                                        "score": score,
                                        "total": total,
                                        "submitted_at": str(datetime.now())
                                    }).execute()
                                except:
                                    pass  # kalau tabel belum ada, biarkan aja untuk sekarang

                            # 🗑️ Delete question
                            if user["role"] == "instructor":
                                if st.button(f"🗑️ Delete Question {i}", key=f"del_q_{qs['id']}"):
                                    supabase.table("quiz_questions").delete().eq("id", qs["id"]).execute()
                                    st.success(f"Question {i} deleted!")
                                    st.rerun()
                    else:
                        st.info("No questions yet.")

                    # 🗑️ Delete Entire Quiz
                    if user["role"] == "instructor":
                        if st.button(f"🗑️ Delete Quiz '{q['title']}'", key=f"del_quiz_{q['id']}"):
                            supabase.table("quiz_questions").delete().eq("quiz_id", q["id"]).execute()
                            supabase.table("quizzes").delete().eq("id", q["id"]).execute()
                            st.success("Quiz deleted!")
                            st.rerun()
        else:
            st.info("No quizzes yet.")

        # --- Create a new quiz ---
        if user["role"] == "instructor":
            with st.form("add_quiz"):
                title = st.text_input("Quiz Title")
                desc = st.text_area("Quiz Description (supports Markdown, LaTeX, and YouTube link)")
                ok = st.form_submit_button("➕ Create Quiz")

                if ok and title:
                    supabase.table("quizzes").insert(
                        {"course_id": cid, "title": title, "description": desc}
                    ).execute()
                    st.success("✅ Quiz created successfully!")
                    st.rerun()

        # --- Add Question to Quiz ---
        if user["role"] == "instructor" and quizzes:
            from PIL import Image
            import io
            import base64

            st.markdown("### ➕ Add Question to Quiz (Rich Version)")
            quiz_list = {q["title"]: q["id"] for q in quizzes}
            selected_quiz = st.selectbox("Select Quiz", list(quiz_list.keys()))
            qid = quiz_list[selected_quiz]

            with st.form("add_question_rich"):
                question_text = st.text_area("Question Text (Markdown + LaTeX supported)", height=150)
                question_image = st.file_uploader("Upload Question Image (optional)", type=["png", "jpg", "jpeg"])

                q_type = st.selectbox("Type", ["multiple_choice", "short_answer"])

                img_markdown = ""
                if question_image:
                    try:
                        img_bytes = question_image.read()
                        file_path = f"uploads/{int(datetime.now().timestamp())}_{question_image.name}"
                        supabase.storage.from_("thinkverse_uploads").upload(file_path, img_bytes)
                        img_url = f"{SUPABASE_URL}/storage/v1/object/public/thinkverse_uploads/{file_path}"
                        img_markdown = f"\n\n![Question Image]({img_url})"
                    except Exception as e:
                        st.error(f"⚠️ Failed to upload question image: {e}")

                if q_type == "multiple_choice":
                    st.markdown("#### ✏️ Multiple Choice Options")
                    choices = []
                    for ch in ["A", "B", "C", "D", "E"]:
                        col1, col2 = st.columns([3, 2])
                        with col1:
                            opt_text = st.text_input(f"Option {ch} Text (Markdown/Equation allowed)", key=f"text_{ch}")
                        with col2:
                            opt_img = st.file_uploader(
                                f"Upload Image for Option {ch}", type=["png", "jpg", "jpeg"], key=f"img_{ch}"
                            )

                        img_opt_md = ""
                        if opt_img:
                            try:
                                img_bytes = opt_img.read()
                                file_path = f"uploads/{int(datetime.now().timestamp())}_{opt_img.name}"
                                supabase.storage.from_("thinkverse_uploads").upload(file_path, img_bytes)
                                img_url = f"{SUPABASE_URL}/storage/v1/object/public/thinkverse_uploads/{file_path}"
                                img_opt_md = f"\n\n![Option {ch}]({img_url})"
                            except Exception as e:
                                st.error(f"⚠️ Failed to upload image for Option {ch}: {e}")

                        full_choice = (opt_text or "") + img_opt_md
                        choices.append(full_choice.strip())

                    correct = st.selectbox("Correct Answer", ["A", "B", "C", "D", "E"])
                    ok = st.form_submit_button("💾 Add Question")

                    if ok and question_text:
                        try:
                            final_question = question_text + img_markdown
                            supabase.table("quiz_questions").insert(
                                {
                                    "quiz_id": qid,
                                    "question": final_question,
                                    "type": "multiple_choice",
                                    "choices": "|".join(choices),
                                    "correct_answer": correct,
                                }
                            ).execute()
                            st.success("✅ Question added successfully with image/equation support!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add question: {e}")

                else:  # short answer
                    st.markdown("#### ✏️ Short Answer Question")
                    correct_ans = st.text_input("Correct Answer (text or equation)")
                    ok = st.form_submit_button("💾 Add Question")

                    if ok and question_text:
                        try:
                            final_question = question_text + img_markdown
                            supabase.table("quiz_questions").insert(
                                {
                                    "quiz_id": qid,
                                    "question": final_question,
                                    "type": "short_answer",
                                    "correct_answer": correct_ans,
                                }
                            ).execute()
                            st.success("✅ Short-answer question added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add question: {e}")


    # =====================================
    # ANNOUNCEMENTS
    # =====================================
    with tabs[5]:
        from datetime import date
        import streamlit.components.v1 as components

        st.subheader("📣 Course Announcements")

        # === Load announcements ===
        try:
            ann = supabase.table("announcements").select("*").eq("course_id", cid).order("date", desc=True).execute().data
        except Exception as e:
            st.error(f"❌ Failed to load announcements: {e}")
            ann = []

        # === Tampilkan semua pengumuman ===
        if ann:
            for a in ann:
                st.markdown(f"""
                <div style="
                    background-color:#f9fafb;
                    border-left:6px solid #4F46E5;
                    padding:15px;
                    border-radius:10px;
                    margin-bottom:10px;">
                    <h4 style="margin-bottom:4px;">📢 {a['title']}</h4>
                    <small style="color:#6b7280;">📅 {a['date']}</small>
                    <p style="margin-top:8px; font-size:15px; color:#1e293b;">{a['content']}</p>
                </div>
                """, unsafe_allow_html=True)

                # 🗑️ Tombol hapus hanya untuk guru
                if user["role"] == "instructor":
                    if st.button(f"🗑️ Delete '{a['title']}'", key=f"del_ann_{a['id']}"):
                        try:
                            supabase.table("announcements").delete().eq("id", a["id"]).execute()
                            st.success("🗑️ Announcement deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to delete announcement: {e}")
        else:
            st.info("No announcements yet.")

        # === Form untuk membuat pengumuman baru ===
        if user["role"] == "instructor":
            st.divider()
            st.markdown("### ➕ Post New Announcement")

            with st.form("add_announcement", clear_on_submit=True):
                title = st.text_input("Title")
                content = st.text_area("Content", height=150)
                submit = st.form_submit_button("📣 Post Announcement")

                if submit:
                    if not title.strip():
                        st.warning("Please enter a title before posting.")
                    else:
                        try:
                            supabase.table("announcements").insert({
                                "course_id": cid,
                                "title": title.strip(),
                                "content": content.strip(),
                                "date": str(date.today())
                            }).execute()
                            st.success("✅ Announcement posted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to post announcement: {e}")

    # === DASHBOARD — ANNOUNCEMENTS FOR STUDENTS ===
    if user["role"] == "student":
        st.subheader("📣 Latest Announcements from Your Courses")

        try:
            # Ambil semua course yang diikuti siswa
            enrolled = supabase.table("enrollments").select("course_id").eq("user_id", user["id"]).execute().data
            course_ids = [e["course_id"] for e in enrolled]

            if course_ids:
                # Ambil semua announcement dari course tersebut
                anns = supabase.table("announcements").select("*, courses(title)").in_("course_id", course_ids).order("date", desc=True).execute().data

                if anns:
                    for a in anns:
                        course_name = a.get("courses", {}).get("title", "Unknown Course")
                        st.markdown(f"""
                        <div style="
                            background-color:#f1f5f9;
                            border-left:5px solid #2563EB;
                            padding:12px 16px;
                            border-radius:8px;
                            margin-bottom:8px;">
                            <b style="font-size:16px;">📢 {a['title']}</b>
                            <div style="color:#6b7280; font-size:13px;">
                                {a['date']} — <i>{course_name}</i>
                            </div>
                            <div style="margin-top:6px; font-size:14px;">{a['content']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No new announcements from your courses yet.")
            else:
                st.info("You are not enrolled in any courses yet.")
        except Exception as e:
            st.error(f"❌ Failed to load announcements: {e}")


def page_account(): 
    st.header("👤 Account Page") 
    st.info("This section is under construction.")
# ======================
# === ROUTING ===
# ======================
# =========================
# === ROUTER UTAMA APP ===
# =========================
def main():
    # Navigasi balik setelah keluar course
    if st.session_state.get("_nav_back"):
        del st.session_state["_nav_back"]
        return main()

    if st.session_state.get("_nav_trigger"):
        del st.session_state["_nav_trigger"]
        return main()

    # === INISIALISASI SESSION STATE ===
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_course" not in st.session_state:
        st.session_state.current_course = None
    if "last_course" not in st.session_state:
        st.session_state.last_course = None

    page = st.session_state.page

    # === ROUTING LOGIC ===
    if page == "login":
        page_login()

    elif page == "dashboard":
        page_dashboard()

    elif page == "courses":
        page_courses()

    elif page == "course_detail":
        if st.session_state.get("current_course"):
            page_course_detail()
        elif st.session_state.get("last_course"):
            st.session_state.current_course = st.session_state.last_course
            st.rerun()
        else:
            st.warning("⚠️ No course selected.")
            st.session_state.page = "courses"
            st.rerun()

    elif page == "account":
        page_account()

    else:
        # fallback ke login
        st.session_state.page = "login"
        st.rerun()


# === Panggil fungsi utama ===
if __name__ == "__main__":
    main()





