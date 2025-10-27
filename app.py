import streamlit as st
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")


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
            # --- tambah sesi absensi baru ---
            with st.form("create_attendance_session"):
                st.markdown("### ➕ Create Attendance Session")
                date = st.date_input("Session Date")
                note = st.text_input("Session Note (optional)")
                ok = st.form_submit_button("Create Session")
                if ok:
                    supabase.table("attendance_sessions").insert({
                        "course_id": cid,
                        "date": str(date),
                        "note": note
                    }).execute()
                    st.success("✅ Attendance session created!")
                    st.rerun()

        # --- tampilkan semua sesi absensi ---
        if sessions:
            for s in sessions:
                st.markdown(f"#### 📅 {s['date']} — {s.get('note','') or '_No note_'}")

                # ambil semua kehadiran siswa di sesi ini
                records = supabase.table("attendance").select("*").eq("session_id", s["id"]).execute().data

                if user["role"] == "instructor":
                    # tampilkan daftar siswa hadir
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

                    # tombol hapus sesi absensi
                    if st.button(f"❌ Delete Session ({s['date']})", key=f"del_sess_{s['id']}"):
                        supabase.table("attendance").delete().eq("session_id", s["id"]).execute()
                        supabase.table("attendance_sessions").delete().eq("id", s["id"]).execute()
                        st.success("🗑️ Session deleted successfully!")
                        st.rerun()

                elif user["role"] == "student":
                    # cek apakah siswa sudah absen
                    existing = supabase.table("attendance").select("*") \
                        .eq("session_id", s["id"]).eq("user_id", user["id"]).execute().data

                    if existing:
                        st.success("✅ You are marked present for this session.")
                    else:
                        if st.button(f"🖋️ Mark as Present ({s['date']})", key=f"mark_{s['id']}"):
                            supabase.table("attendance").insert({
                                "session_id": s["id"],
                                "course_id": cid,
                                "user_id": user["id"],
                                "date": str(datetime.now().date()),
                                "status": "present"
                            }).execute()
                            st.success("✅ Your attendance has been recorded!")
                            st.rerun()
        else:
            st.info("No attendance sessions created yet.")


    # =====================================
    # MODULES
    # =====================================
    with tabs[2]:
        from PIL import Image
        import io
        import base64
        import markdown
        import streamlit.components.v1 as components

        st.subheader("📦 Learning Modules")

        # === Pastikan CID valid dan simpan di session_state ===
        if not cid:
            cid = st.session_state.get("current_course") or st.session_state.get("last_course")
        if not cid:
            st.error("⚠️ Course ID not found.")
            st.stop()

        # Simpan CID supaya gak hilang setelah rerun
        st.session_state.current_course = cid

        # === Load modules dari Supabase ===
        try:
            mods_response = supabase.table("modules").select("*").eq("course_id", int(cid)).execute()
            mods = mods_response.data or []
        except Exception as e:
            st.error(f"❌ Failed to load modules: {e}")
            mods = []

        # === Tampilkan modul ===
        if mods:
            for m in mods:
                with st.expander(f"📘 {m['title']}"):
                    raw_content = m.get("content", "No content available.")

                    # --- Convert Markdown (gambar, bold, dll) ke HTML ---
                    rendered_md = markdown.markdown(
                        raw_content,
                        extensions=["fenced_code", "tables", "md_in_html"]
                    )

                    # --- Bungkus dengan MathJax supaya LaTeX bisa tampil ---
                    html_content = f"""
                    <div style="font-size:16px; line-height:1.7;">
                        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
                        <script id="MathJax-script" async
                            src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
                        </script>
                        <article class="markdown-body">{rendered_md}</article>
                    </div>
                    """

                    # --- Tampilkan konten lengkap ---
                    components.html(html_content, height=600, scrolling=True)

                    # --- Tambahkan video kalau ada ---
                    if m.get("video_url"):
                        st.video(m["video_url"])

                    # --- Tombol Delete Module (khusus instruktur) ---
                    if user["role"] == "instructor":
                        col1, col2 = st.columns([0.2, 0.8])
                        with col1:
                            if st.button(f"🗑️ Delete Module '{m['title']}'", key=f"del_mod_{m['id']}"):
                                try:
                                    supabase.table("modules").delete().eq("id", m["id"]).execute()
                                    st.success(f"✅ Module '{m['title']}' deleted successfully!")
                                    time.sleep(1)
                                    st.session_state.refresh_modules = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to delete module: {e}")
        else:
            st.info("📭 No modules added yet.")

        # === Tambah modul baru (khusus instruktur) ===
        if user["role"] == "instructor":
            st.divider()
            st.markdown("### ➕ Add New Module (with Images & Equations)")

            with st.form("add_module_rich", clear_on_submit=True):
                title = st.text_input("Module Title")
                content = st.text_area("Content (Markdown + LaTeX supported)", height=200)
                uploaded_image = st.file_uploader("Upload Image (optional)", type=["png", "jpg", "jpeg"])
                video_url = st.text_input("Video URL (optional)")

                preview_btn = st.form_submit_button("🔍 Preview Content")

                if preview_btn:
                    st.markdown("---")
                    st.markdown("#### 🖼️ Preview Result:")
                    st.markdown(content, unsafe_allow_html=True)
                    st.info("You can include equations like this: `$$E = mc^2$$` or `$$F = ma$$`")

                submit_btn = st.form_submit_button("💾 Add Module")

                if submit_btn:
                    if not title.strip():
                        st.warning("Please enter a module title.")
                    else:
                        try:
                            # === Upload image ke Supabase Storage (jika ada) ===
                            img_markdown = ""
                            if uploaded_image:
                                img_bytes = uploaded_image.read()
                                file_path = f"uploads/{int(datetime.now().timestamp())}_{uploaded_image.name}"
                                supabase.storage.from_("thinkverse_uploads").upload(file_path, img_bytes)
                                img_url = f"{SUPABASE_URL}/storage/v1/object/public/thinkverse_uploads/{file_path}"
                                img_markdown = f"\n\n![Uploaded Image]({img_url})"

                            # === Gabungkan konten dan gambar ===
                            final_content = (content or "") + (img_markdown or "")

                            # === Insert module ke Supabase ===
                            response = supabase.table("modules").insert({
                                "course_id": int(cid),
                                "title": title.strip(),
                                "content": final_content.strip(),
                                "video_url": video_url.strip() if video_url else None
                            }).execute()

                            st.write("📤 Debug — Supabase insert response:", response)

                            if response.data:
                                st.success(f"✅ Module '{title}' added successfully!")

                                # Simpan module ke session biar tampil tanpa reload manual
                                if "modules_cache" not in st.session_state:
                                    st.session_state.modules_cache = []
                                st.session_state.modules_cache.append(response.data[0])

                                # 🚀 Force reload modul terbaru dari Supabase
                                st.session_state.refresh_modules = True
                                st.rerun()
                            else:
                                st.error("⚠️ Insert failed — no data returned from Supabase.")

                        except Exception as e:
                            st.error(f"❌ Failed to add module: {e}")

            # === Refresh otomatis setelah insert/delete ===
            if st.session_state.get("refresh_modules"):
                st.session_state.refresh_modules = False
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
                    if user["role"] == "instructor":
                        if st.button(f"🗑️ Delete Assignment '{a['title']}'", key=f"del_asg_{a['id']}"):
                            supabase.table("assignments").delete().eq("id", a["id"]).execute()
                            st.success("Assignment deleted!")
                            st.rerun()
        else:
            st.info("No assignments available.")

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

                            # 🗑️ Delete Question
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
                            opt_img = st.file_uploader(f"Upload Image for Option {ch}", type=["png", "jpg", "jpeg"], key=f"img_{ch}")

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
                            supabase.table("quiz_questions").insert({
                                "quiz_id": qid,
                                "question": final_question,
                                "type": "multiple_choice",
                                "choices": "|".join(choices),
                                "correct_answer": correct
                            }).execute()
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
                            supabase.table("quiz_questions").insert({
                                "quiz_id": qid,
                                "question": final_question,
                                "type": "short_answer",
                                "correct_answer": correct_ans
                            }).execute()
                            st.success("✅ Short-answer question added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add question: {e}")


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

                # 🗑️ Delete announcement
                if user["role"] == "instructor":
                    if st.button(f"🗑️ Delete Announcement '{a['title']}'", key=f"del_ann_{a['id']}"):
                        supabase.table("announcements").delete().eq("id", a["id"]).execute()
                        st.success("Announcement deleted!")
                        st.rerun()

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

def page_account(): 
    st.header("👤 Account Page") 
    st.info("This section is under construction.")
# ======================
# === ROUTING ===
# ======================
def main():
    # Navigasi balik setelah keluar course
    if st.session_state.get("_nav_back"):
        del st.session_state["_nav_back"]
        return main()  # rerender penuh, sidebar muncul lagi
    
    # Handle soft navigation without experimental rerun
    if st.session_state.get("_nav_trigger"):
        del st.session_state["_nav_trigger"]
        return main()  # panggil ulang fungsi main() manual, rerender natural


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

    # === ROUTER HALAMAN ===
    if page == "login":
        page_login()

    elif page == "dashboard":
        page_dashboard()

    elif page == "courses":
        page_courses()

    elif page == "course_detail":
        # Pastikan course tetap tersimpan
        if st.session_state.get("current_course"):
            page_course_detail()
        elif st.session_state.get("last_course"):
            st.session_state.current_course = st.session_state.last_course
            raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))
        else:
            st.warning("⚠️ No course selected. Please return to the Courses page.")
            st.session_state.page = "courses"
            st.rerun()

    elif page == "account":
        page_account()

    else:
        # fallback ke login
        st.session_state.page = "login"
        st.rerun()

# jalankan aplikasi
if __name__ == "__main__":
    main()





















