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

def reset_password(email, new_password):
    """
    Fungsi untuk reset password user di tabel users Supabase.
    Menggunakan kolom 'password_hash' sebagai penyimpanan hash.
    """
    try:
        # Cari user berdasarkan email
        user = supabase.table("users").select("*").eq("email", email).execute().data

        if not user:
            st.error("❌ Email tidak ditemukan di database.")
            return False

        # Hash password baru
        import hashlib
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()

        # Update kolom password_hash
        supabase.table("users").update({"password_hash": hashed_pw}).eq("email", email).execute()

        st.success("✅ Password berhasil direset!")
        return True

    except Exception as e:
        st.error(f"⚠️ Gagal mereset password: {e}")
        return False



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
        st.subheader("🔑 Lupa Password")
    
        with st.form("forgot_pw_form"):
            email_fp = st.text_input("Masukkan email kamu")
            new_pw = st.text_input("Password baru", type="password")
            new_pw2 = st.text_input("Ulangi password baru", type="password")
            ok3 = st.form_submit_button("Reset Password")
    
            if ok3:
                if not email_fp or not new_pw or not new_pw2:
                    st.warning("⚠️ Harap isi semua kolom.")
                elif new_pw != new_pw2:
                    st.error("❌ Password tidak sama.")
                else:
                    success = reset_password(email_fp, new_pw)
                    if success:
                        st.success("✅ Password berhasil direset! Silakan login ulang.")
                    else:
                        st.error("⚠️ Email tidak ditemukan atau gagal mengupdate password.")




# ======================
# === DASHBOARD ===
# ======================
def page_dashboard():
    from datetime import date
    u = st.session_state.user

    # === SIDEBAR ===
    st.sidebar.title("ThinkVerse LMS")
    st.sidebar.markdown(f"👋 **{u['name']}**\n\n📧 {u['email']}\n\nRole: *{u['role']}*")
    nav = st.sidebar.radio("Navigasi", ["🏠 Dashboard", "📘 Kursus", "👤 Akun"])

    # === DASHBOARD UTAMA ===
    if nav == "🏠 Dashboard":
        st.header("🏠 Dashboard Utama")
        st.info("Selamat datang di ThinkVerse LMS! Pilih menu di sebelah kiri untuk melanjutkan.")

        # === Hanya untuk siswa: tampilkan notifikasi pengumuman baru ===
        if u["role"] == "student":
            import time
            import streamlit.components.v1 as components

            # Simpan waktu terakhir pengecekan pengumuman
            if "last_announcement_check" not in st.session_state:
                st.session_state.last_announcement_check = None

            try:
                # Ambil daftar kursus yang diikuti siswa
                enrolled = supabase.table("enrollments").select("course_id").eq("user_id", u["id"]).execute().data
                course_ids = [e["course_id"] for e in enrolled]

                if course_ids:
                    # Ambil pengumuman terbaru dari kursus yang diikuti
                    latest_ann = supabase.table("announcements")\
                        .select("*, courses(title)")\
                        .in_("course_id", course_ids)\
                        .order("date", desc=True)\
                        .limit(1)\
                        .execute().data

                    if latest_ann:
                        latest = latest_ann[0]
                        latest_date = latest["date"]
                        latest_title = latest["title"]
                        course_name = latest.get("courses", {}).get("title", "Unknown Course")

                        # Tampilkan hanya jika pengumuman ini baru
                        if st.session_state.last_announcement_check != latest_date:
                            st.markdown(f"""
                            <div style="
                                background-color:#EFF6FF;
                                border-left:6px solid #3B82F6;
                                padding:14px;
                                border-radius:10px;
                                margin-top:15px;">
                                <h4 style="margin:0;">📢 Pengumuman Baru!</h4>
                                <p style="margin:4px 0; color:#1e293b;">
                                    <b>{latest_title}</b> dari <i>{course_name}</i><br>
                                    <small>📅 {latest_date}</small>
                                </p>
                                <div style="color:#334155;">{latest['content']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.session_state.last_announcement_check = latest_date
                        else:
                            st.markdown("<p style='color:#64748b;'>Tidak ada pengumuman baru hari ini 💬</p>", unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color:#64748b;'>Belum ada pengumuman di kursusmu.</p>", unsafe_allow_html=True)
                else:
                    st.warning("Kamu belum terdaftar di kursus mana pun.")
            except Exception as e:
                st.error(f"Gagal memuat notifikasi pengumuman: {e}")

    # === KURSUS ===
    elif nav == "📘 Kursus":
        page_courses()

    # === AKUN ===
    elif nav == "👤 Akun":
        st.header("👤 Profil Pengguna")
    
        u = st.session_state.user
    
        # ====== FOTO PROFIL ======
        st.subheader("Foto Profil")
    
        col1, col2 = st.columns([1, 3])
    
        with col1:
            # tampilkan foto profil (kalau belum ada → generate avatar)
            if u.get("avatar_url"):
                st.image(u["avatar_url"], width=120)
            else:
                st.image(
                    "https://ui-avatars.com/api/?name=" + u["name"].replace(" ", "+"),
                    width=120
                )
    
        with col2:
            uploaded = st.file_uploader("Ganti foto profil", type=["png", "jpg", "jpeg"])
            if uploaded:
                import uuid
    
                file_bytes = uploaded.read()
                file_name = f"{uuid.uuid4()}.png"
    
                try:
                    # Upload ke Supabase Storage (folder: profile_pics)
                    supabase.storage.from_("profile_pics").upload(file_name, file_bytes)
    
                    public_url = supabase.storage.from_("profile_pics").get_public_url(file_name)
    
                    # Simpan ke tabel users
                    supabase.table("users").update({"avatar_url": public_url}).eq("id", u["id"]).execute()
    
                    u["avatar_url"] = public_url
                    st.success("Foto profil berhasil diperbarui!")
                    st.rerun()
    
                except Exception as e:
                    st.error(f"Gagal upload foto: {e}")
    
        st.markdown("---")
    
        # ====== INFORMASI AKUN ======
        st.subheader("Informasi Akun")
    
        st.write(f"**Nama Lengkap:** {u['name']}")
        st.write(f"**Email:** {u['email']}")
        st.write(f"**Role:** {'Guru' if u['role']=='instructor' else 'Siswa'}")
    
        st.markdown("---")
    
        # ====== LOGOUT ======
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
    from datetime import datetime

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

    # === Deteksi tab aktif (dari session state) ===
    active_tab = st.session_state.get("active_tab", "overview")
    
    # === Buat semua tab ===
    if user["role"] == "instructor":
        tabs = st.tabs([
            "📚 Overview",
            "🕒 Attendance",
            "📦 Learning Activity",
            "📋 Assignments",
            "🧠 Quiz",
            "📣 Announcements",
            "💬 Discussion Forum",
            "👥 Students"
        ])
    else:
        tabs = st.tabs([
            "📚 Overview",
            "🕒 Attendance",
            "📦 Learning Activity",
            "📋 Assignments",
            "🧠 Quiz",
            "📣 Announcements",
            "💬 Discussion Forum"
        ])

    st.write("Jumlah tab:", len(tabs))

    
    # === Map nama tab ke indeks ===
    tab_index = {
        "overview": 0,
        "attendance": 1,
        "module": 2,
        "assignment": 3,
        "quiz": 4,
        "announcement": 5,
        "discussion": 6     # 🆕 Tambahkan juga ke mapping
    }

    
    # === Inject JavaScript untuk auto-switch tab ===
    if active_tab in ["quiz", "assignment"]:
        target_index = tab_index[active_tab]
        js_code = f"""
        <script>
        const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
        if (tabs && tabs[{target_index}]) {{
            tabs[{target_index}].click();
        }}
        </script>
        """
        st.components.v1.html(js_code, height=0, width=0)
        st.session_state.active_tab = None  # reset supaya gak looping
    
        

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
    
        st.subheader("📦 Learning Activities")
    
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
                                # --- Pastikan variabel aman dulu ---
                                asg_id = None
                                if "asg_data" in locals() and isinstance(asg_data, dict):
                                    asg_id = asg_data.get("id")
                                
                                # --- Tombol untuk membuka assignment ---
                                btn_key = f"open_asg_{m.get('id', 'unknown')}_{asg_id or 'none'}"
                                if st.button("➡️ Open Assignment", key=btn_key):
                                    if asg_id:
                                        st.session_state.selected_assignment_id = asg_id
                                        st.session_state.active_tab = "assignment"
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Belum ada assignment yang terhubung dengan modul ini.")


    
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
                            st.success("🎯 learning activity marked as completed!")
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
            st.markdown("## ✏️ Edit Learning Activity")
            with st.form("edit_module_form"):
                new_title = st.text_input("Learning Activity Title", m["title"])
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
                        st.success(f"✅ Learning Acttivity '{title}' added successfully!")
                        st.rerun()








    # =====================================
    # ASSIGNMENTS
    # =====================================
    with tabs[3]:
        import re
        import streamlit.components.v1 as components
        from datetime import datetime
    
        st.subheader("📋 Assignments")
    
        # === Load assignments ===
        try:
            assignments = (
                supabase.table("assignments").select("*").eq("course_id", cid).execute().data or []
            )
            assignments = [a for a in assignments if a.get("id")]
        except Exception as e:
            st.error(f"❌ Failed to load assignments: {e}")
            assignments = []
    
        # === Display all assignments ===
        if assignments:
            for a in assignments:
                with st.expander(f"📄 {a['title']}"):
                    st.markdown(f"**Description:**\n\n{a.get('description', '_No description provided._')}")
    
                    # === EMBEDDED RESOURCES ===
                    embed_links = []
    
                    # handle dua kolom embed (baru)
                    if a.get("embed_url_1"):
                        embed_links.append(a["embed_url_1"].strip())
                    if a.get("embed_url_2"):
                        embed_links.append(a["embed_url_2"].strip())
    
                    # fallback kalau masih pakai kolom lama (gabungan)
                    if not embed_links and a.get("embed_url"):
                        embed_links = [url.strip() for url in a["embed_url"].split("|") if url.strip()]
    
                    # tampilkan masing-masing embed
                    # === Display embedded resources (PhET, Liveworksheet, HTML) ===
                    for i, link in enumerate(embed_links, 1):
                        st.markdown(f"### 🔗 Embedded Resource {i}:")
                        clean_link = link.strip()
                    
                        # kalau langsung iframe HTML (dari Supabase atau input form)
                        if "<iframe" in clean_link:
                            st.success(f"🧩 Embedded Custom HTML {i}:")
                            try:
                                # render langsung HTML asli
                                components.html(clean_link, height=800, scrolling=True)
                            except Exception as e:
                                st.warning(f"⚠️ Failed to render custom HTML: {e}")
                            continue
                    
                        # deteksi otomatis berdasarkan domain
                        if "phet.colorado.edu" in clean_link:
                            st.success("🧪 Embedded PhET Simulation:")
                            iframe_html = f"""
                            <iframe src="{clean_link}" width="100%" height="600"
                                    allowfullscreen style="border:1px solid #ccc; border-radius:10px;">
                            </iframe>
                            """
                            components.html(iframe_html, height=620, scrolling=False)
                    
                        elif "liveworksheets.com" in clean_link:
                            st.success("🧾 Embedded Liveworksheet:")
                            iframe_html = f"""
                            <iframe src="{clean_link}" width="100%" height="800"
                                    style="border:2px solid #ddd; border-radius:10px;" allowfullscreen>
                            </iframe>
                            """
                            components.html(iframe_html, height=820, scrolling=True)
                    
                        elif clean_link.endswith(".html"):
                            st.success("🧩 Embedded HTML Resource:")
                            components.html(f'<iframe src="{clean_link}" width="100%" height="700"></iframe>', height=720)
                    
                        elif re.match(r"^https?://", clean_link):
                            st.markdown(f"[🌐 Open External Resource]({clean_link})")
                    
                        else:
                            st.info("ℹ️ Invalid or unsupported embed link.")

    
                        # 1️⃣ PhET Simulation
                        if "phet.colorado.edu" in link:
                            st.success("🧪 Embedded PhET Simulation:")
                            iframe_html = f"""
                            <iframe src="{link}" width="800" height="600"
                                    allowfullscreen style="border:1px solid #ccc; border-radius:10px;">
                            </iframe>
                            """
                            components.html(iframe_html, height=620)
    
                        # 2️⃣ Liveworksheet
                        elif "liveworksheets.com" in link:
                            st.success("🧾 Embedded Liveworksheet:")
                            try:
                                iframe_html = f"""
                                <iframe src="{link}" width="100%" height="800"
                                        style="border:2px solid #ddd; border-radius:10px;"
                                        allowfullscreen></iframe>
                                """
                                components.html(iframe_html, height=820, scrolling=True)
                            except Exception as e:
                                st.warning(f"⚠️ Could not embed Liveworksheet: {e}")
    
                        # 3️⃣ Public HTML
                        elif link.endswith(".html"):
                            st.success("🧩 Embedded HTML Content:")
                            try:
                                components.iframe(link, height=700, scrolling=True)
                            except Exception as e:
                                st.warning(f"⚠️ Could not load HTML: {e}")
    
                        # 4️⃣ Default links (YouTube, Form, Drive)
                        elif re.match(r"^https?://", link):
                            st.markdown(f"[🌐 Open Resource {i}]({link})")
                        else:
                            st.info("ℹ️ Invalid embed link provided.")
    
                    # === Student submission ===
                    if user["role"] == "student":
                        st.markdown("### ✏️ Submit Assignment")
                        file = st.file_uploader("Upload your work (PDF, DOCX, ZIP, etc.)", key=f"up_{a['id']}")
                        if file and st.button("📤 Submit", key=f"submit_{a['id']}"):
                            try:
                                file_bytes = file.read()
                                file_path = f"assignments/{user['id']}_{int(datetime.now().timestamp())}_{file.name}"
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
    
                    # === Instructor Controls ===
                    if user["role"] == "instructor":
                        st.divider()
                        col1, col2 = st.columns(2)
    
                        # ✏️ Edit assignment
                        with col1:
                            with st.form(f"edit_asg_{a['id']}"):
                                st.markdown("### ✏️ Edit Assignment")
                                new_title = st.text_input("Title", a["title"])
                                new_desc = st.text_area("Description", a.get("description", ""), height=100)
                                new_url1 = st.text_input("Embed URL 1 (PhET / Liveworksheet / HTML)", a.get("embed_url_1", ""))
                                new_url2 = st.text_input("Embed URL 2 (Optional second resource)", a.get("embed_url_2", ""))
                                save = st.form_submit_button("💾 Save Changes")
                                if save:
                                    try:
                                        supabase.table("assignments").update({
                                            "title": new_title.strip(),
                                            "description": new_desc.strip(),
                                            "embed_url_1": new_url1.strip() if new_url1 else None,
                                            "embed_url_2": new_url2.strip() if new_url2 else None,
                                        }).eq("id", a["id"]).execute()
                                        st.success("✅ Assignment updated successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to update: {e}")
    
                        # 🗑️ Delete assignment
                        with col2:
                            if st.button(
                                f"🗑️ Delete Assignment '{a['title']}'", 
                                key=f"del_asg_{a['id']}", type="primary"
                            ):
                                try:
                                    supabase.table("assignments").delete().eq("id", a["id"]).execute()
                                    st.success("✅ Assignment deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to delete: {e}")
    
        else:
            st.info("📭 No assignments available.")
    
        # === Add new assignment (Instructor only) ===
        if user["role"] == "instructor":
            st.divider()
            st.markdown("### ➕ Add New Assignment")
    
            with st.form("add_assignment", clear_on_submit=True):
                title = st.text_input("Assignment Title")
                desc = st.text_area("Assignment Description", height=100)
                embed_url_1 = st.text_input("Embed URL 1 (PhET / Liveworksheet / HTML)")
                embed_url_2 = st.text_input("Embed URL 2 (Optional second resource)")
    
                submit_asg = st.form_submit_button("💾 Add Assignment")
                if submit_asg:
                    if not title.strip():
                        st.warning("⚠️ Please enter a title.")
                    elif st.session_state.get("saving_assignment", False):
                        st.info("⏳ Please wait, still saving previous assignment...")
                    else:
                        try:
                            st.session_state.saving_assignment = True
                            supabase.table("assignments").insert({
                                "course_id": cid,
                                "title": title.strip(),
                                "description": desc.strip() if desc else "",
                                "embed_url_1": embed_url_1.strip() if embed_url_1 else None,
                                "embed_url_2": embed_url_2.strip() if embed_url_2 else None,
                            }).execute()
                            st.success(f"✅ Assignment '{title}' added successfully!")
                            st.session_state.saving_assignment = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add assignment: {e}")
                            st.session_state.saving_assignment = False


                            
    # =====================================
    # QUIZZES (FULL INTERACTIVE)
    # =====================================
    with tabs[4]:
        import streamlit.components.v1 as components
        import re, markdown, json
        from datetime import datetime
        from PIL import Image
        import io, base64
    
        st.subheader("🧠 Quiz")
    
        # --- Helper: safe fetch quizzes for course ---
        def load_quizzes_for_course(course_id):
            return supabase.table("quizzes").select("*").eq("course_id", course_id).execute().data or []
    
        quizzes = load_quizzes_for_course(cid)
        selected_quiz_id = st.session_state.get("selected_quiz_id")
    
        if not quizzes:
            st.info("No quizzes yet.")
        else:
            for q in quizzes:
                expanded = selected_quiz_id == q["id"]
                with st.expander(f"📝 {q['title']}", expanded=expanded):
                    if expanded:
                        st.session_state.selected_quiz_id = None
    
                    # --- Render quiz description ---
                    desc = q.get("description","") or ""
                    if desc.strip():
                        st.markdown("### 📘 Quiz Description:")
                        youtube_match = re.search(r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w\-]+)", desc)
                        if youtube_match:
                            youtube_url = youtube_match.group(1)
                            video_id = youtube_url.split("v=")[-1] if "v=" in youtube_url else youtube_url.split("/")[-1]
                            st.video(f"https://www.youtube.com/watch?v={video_id}")
                            desc = desc.replace(youtube_url, "")
                        rendered_md = markdown.markdown(desc, extensions=["fenced_code", "tables", "md_in_html"])
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
    
                    # --- Instructor: Edit Quiz ---
                    if user["role"] == "instructor":
                        st.divider()
                        with st.container():
                            st.markdown("#### ✏️ Edit This Quiz")
                            with st.form(f"edit_quiz_{q['id']}"):
                                new_title = st.text_input("Quiz Title", q.get("title", ""))
                                new_desc = st.text_area("Quiz Description (Markdown/LaTeX allowed)", q.get("description", ""))
                                attempt_limit_val = q.get("attempt_limit",0)
                                attempt_limit = st.number_input("Attempt limit (0 = unlimited)", min_value=0, value=int(attempt_limit_val or 0), step=1)
                                save_edit = st.form_submit_button("💾 Save Changes")
                                if save_edit:
                                    try:
                                        supabase.table("quizzes").update({
                                            "title": new_title,
                                            "description": new_desc,
                                            "attempt_limit": int(attempt_limit)
                                        }).eq("id", q["id"]).execute()
                                        st.success("✅ Quiz updated successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to update quiz: {e}")
    
                    # --- Load questions ---
                    try:
                        questions = supabase.table("quiz_questions").select("*").eq("quiz_id", q["id"]).order("id", desc=False).execute().data or []
                    except Exception:
                        questions = supabase.table("quiz_questions").select("*").eq("quiz_id", q["id"]).execute().data or []
    
                    if questions:
                        st.markdown("### ✏️ Questions:")
                        answers = {}
                        q_rubrics = {}
                        for i, qs in enumerate(questions, 1):
                            st.markdown(f"**{i}.**")
                            st.markdown(f"<div style='font-size:15px; line-height:1.6;'>{qs.get('question','')}</div>", unsafe_allow_html=True)
    
                            # rubric
                            rubric_raw = qs.get("rubric","") or ""
                            rubric_data = None
                            if rubric_raw:
                                try:
                                    rubric_data = json.loads(rubric_raw)
                                except Exception:
                                    parts = rubric_raw.split("|",1)
                                    try:
                                        rubric_data = {"max_score": float(parts[0]), "note": parts[1] if len(parts)>1 else ""}
                                    except:
                                        rubric_data = None
                            q_rubrics[qs["id"]] = rubric_data
    
                            # Input type
                            if qs.get("type") == "multiple_choice":
                                choices = qs.get("choices","").split("|")
                            
                                # gunakan selectbox biar jadi dropdown ABCDE
                                ans = st.selectbox(
                                    "Pilih jawaban:",
                                    ["-- pilih jawaban --"] + choices,
                                    key=f"ans_{qs['id']}"
                                )
                            
                                # kalau user belum milih, simpan kosong biar gak error
                                answers[qs["id"]] = "" if ans.startswith("--") else ans

                            else:
                                ans = st.text_area("Jawaban singkat / esai:", key=f"ans_{qs['id']}", height=120)
                                answers[qs["id"]] = ans
    
                            if rubric_data:
                                st.caption(f"Rubrik: max {rubric_data.get('max_score')} — {rubric_data.get('note','')}")
    
                            # Instructor edit question
                            if user["role"] == "instructor":
                                st.markdown("— Instructor controls —")
                                with st.form(f"edit_q_{qs['id']}", clear_on_submit=False):
                                    new_q_text = st.text_area("Question Text (Markdown)", value=qs.get("question",""))
                                    q_type = st.selectbox("Type", ["multiple_choice","short_answer"], index=0 if qs.get("type")=="multiple_choice" else 1)
                                    new_choices = st.text_area("Choices (pipe | sep) — for MCQ", value=qs.get("choices",""))
                                    new_correct = st.text_input("Correct Answer (for MCQ exact string)", value=qs.get("correct_answer",""))
                                    new_rubric_max = st.text_input("Rubric max score", value=str((q_rubrics[qs['id']]['max_score']) if q_rubrics.get(qs['id']) else ""))
                                    new_rubric_note = st.text_input("Rubric note", value=(q_rubrics[qs['id']]['note'] if q_rubrics.get(qs['id']) else ""))
                                    save_q = st.form_submit_button("💾 Save Question")
                                    if save_q:
                                        rubric_store = None
                                        if new_rubric_max:
                                            try:
                                                rubric_store = json.dumps({"max_score": float(new_rubric_max), "note": new_rubric_note})
                                            except:
                                                rubric_store = None
                                        update_payload = {
                                            "question": new_q_text,
                                            "type": q_type,
                                            "correct_answer": new_correct
                                        }
                                        if q_type == "multiple_choice":
                                            update_payload["choices"] = new_choices
                                        if rubric_store is not None:
                                            update_payload["rubric"] = rubric_store
                                        supabase.table("quiz_questions").update(update_payload).eq("id", qs["id"]).execute()
                                        st.success("✅ Question updated!")
                                        st.rerun()
    
                                # Delete question
                                if st.button(f"🗑️ Delete Question {i}", key=f"del_q_{qs['id']}"):
                                    supabase.table("quiz_questions").delete().eq("id", qs['id']).execute()
                                    st.success("Question deleted.")
                                    st.rerun()
    
                        # --- Student submit ---
                        if user["role"] == "student":
                            attempt_limit = int(q.get("attempt_limit",0) or 0)
                            attempts = supabase.table("quiz_attempts").select("*").eq("quiz_id", q["id"]).eq("user_id", user["id"]).execute().data or []
                            attempts_made = len(attempts)
                            can_attempt = (attempt_limit == 0) or (attempts_made < attempt_limit)
                            
                            if not can_attempt:
                                st.warning(f"⚠️ Kamu sudah melakukan {attempts_made} percobaan. Batas percobaan = {attempt_limit}.")
                            else:
                                if st.button("✅ Kumpulkan Jawaban", key=f"submit_quiz_{q['id']}"):
                                    total_questions = len(questions)
                                    auto_score = 0
                                    total_auto_possible = 0
                                    answers_payload = []
                        
                                    for qs in questions:
                                        # Ambil jawaban siswa dan bersihkan
                                        user_ans_raw = answers.get(qs["id"]) or ""
                                        user_ans_clean = user_ans_raw.strip().lower()
                                        correct_clean = (qs.get("correct_answer") or "").strip().lower()
                        
                                        if qs.get("type") == "multiple_choice":
                                            # Compare cleaned strings
                                            is_correct = (user_ans_clean == correct_clean)
                        
                                            # Debug print (bisa dihapus setelah tes)
                                            print(f"QID {qs['id']} | Student answer: {user_ans_clean} | Correct: {correct_clean} | is_correct: {is_correct}")
                        
                                            answers_payload.append({
                                                "question_id": qs["id"],
                                                "choice_id": None,
                                                "text_answer": user_ans_raw,
                                                "is_correct": bool(is_correct)   # pastikan boolean
                                            })
                                            total_auto_possible += 1
                                            if is_correct:
                                                auto_score += 1
                                        else:
                                            # essay / short answer, perlu manual grading
                                            answers_payload.append({
                                                "question_id": qs["id"],
                                                "choice_id": None,
                                                "text_answer": user_ans_raw,
                                                "is_correct": None
                                            })
                        
                                    # Hitung skor MCQ sebagai persentase 0-100
                                    mcq_percent = (auto_score / total_auto_possible * 100) if total_auto_possible > 0 else 0
                        
                                    # Insert attempt
                                    attempt_number = attempts_made + 1
                                    try:
                                        attempt_res = supabase.table("quiz_attempts").insert({
                                            "quiz_id": q["id"],
                                            "user_id": user["id"],
                                            "student_id": user["id"], 
                                            "score": round(mcq_percent,2),  # simpan langsung % MCQ
                                            "total": total_questions,
                                            "submitted_at": datetime.now().isoformat(),
                                            "manual_score": None,
                                            "teacher_feedback": None,
                                            "attempt_number": attempt_number
                                        }).execute()
                                        attempt_id = attempt_res.data[0]["id"] if attempt_res.data else None
                                    except Exception as e:
                                        st.error(f"❌ Failed to create attempt record: {e}")
                                        attempt_id = None
                        
                                    # Insert jawaban ke quiz_answers
                                    if attempt_id:
                                        for a_payload in answers_payload:
                                            try:
                                                supabase.table("quiz_answers").insert({
                                                    "attempt_id": attempt_id,
                                                    "question_id": a_payload["question_id"],
                                                    "choice_id": a_payload["choice_id"],
                                                    "text_answer": a_payload["text_answer"],
                                                    "is_correct": a_payload["is_correct"]
                                                }).execute()
                                            except Exception as e:
                                                st.warning(f"Warning saving one answer: {e}")
                        
                                        st.success(f"✅ Jawaban terkirim! (Attempt #{attempt_number}) — Skor MCQ: {round(mcq_percent,2)}%")
                                        st.rerun()
                                    else:
                                        st.error("❌ Gagal menyimpan attempt. Coba ulang.")


    
                    else:
                        st.info("No questions yet for this quiz.")
    
                    # --- Instructor Submissions & Grading ---
                    if user["role"] == "instructor":
                        st.divider()
                        st.markdown("### 🧾 Submissions & Grading")
                        attempts_all = supabase.table("quiz_attempts").select("*").eq("quiz_id", q["id"]).order("submitted_at", desc=True).execute().data or []
                        if not attempts_all:
                            st.info("Belum ada submission untuk quiz ini.")
                        else:
                            users_attempts = {}
                            for at in attempts_all:
                                users_attempts.setdefault(at["user_id"],[]).append(at)
                            for uid, at_list in users_attempts.items():
                                for at in at_list:
                                    st.markdown(f"**User #{uid} — Attempt #{at.get('attempt_number','?')} — submitted {at.get('submitted_at','')}**")
                                    answers_for_attempt = supabase.table("quiz_answers").select("*").eq("attempt_id", at['id']).order("id", desc=False).execute().data or []
                                    manual_scores = {}
                                    total_manual_max = 0.0
                                    total_manual_obtained = 0.0
                                    for idx_q, ans_row in enumerate(answers_for_attempt,1):
                                        qrec = supabase.table("quiz_questions").select("*").eq("id", ans_row["question_id"]).execute().data
                                        qrec = qrec[0] if qrec else {}
                                        qtext_html = markdown.markdown(qrec.get("question",""), extensions=["fenced_code","md_in_html"])
                                        st.markdown(f"**Soal {idx_q}:**")
                                        st.components.v1.html(f"<div style='font-size:14px;'>{qtext_html}</div>", height=110, scrolling=False)
                                        if qrec.get("type") == "multiple_choice":
                                            st.markdown(f"- **Jawaban siswa:** {ans_row.get('text_answer','')}")
                                            is_corr = ans_row.get("is_correct")
                                            st.markdown(f"- **Auto-correct:** {'Benar' if is_corr else 'Salah'}")
                                        else:
                                            st.markdown(f"- **Jawaban siswa (esai):**")
                                            st.markdown(ans_row.get("text_answer",""))
                                            rubric = {}
                                            raw = qrec.get("rubric","")
                                            if raw:
                                                try:
                                                    rubric = json.loads(raw)
                                                except:
                                                    try:
                                                        parts = raw.split("|",1)
                                                        rubric = {"max_score": float(parts[0]), "note": parts[1] if len(parts)>1 else ""}
                                                    except:
                                                        rubric = {}
                                            max_score = rubric.get("max_score",0.0)
                                            if max_score:
                                                total_manual_max += float(max_score)
                                            ms_key = f"manual_{at['id']}_{ans_row['id']}"
                                            manual_scores[ans_row['id']] = st.number_input(f"Nilai Soal {idx_q} (max {max_score})", min_value=0.0, max_value=float(max_score or 9999), value=0.0, step=0.5, key=ms_key)
    
                                    st.markdown("---")
                                    st.markdown(f"**Auto-score (MCQ count):** {at.get('score')} / (MCQ raw count)")
                                    teacher_feedback = st.text_area(f"Teacher feedback (attempt {at['id']})", value=at.get("teacher_feedback") or "", key=f"tf_{at['id']}")
                                    manual_total_key = f"manual_total_{at['id']}"
                                    manual_total = st.number_input("Manual total (sum of essay scores)", min_value=0.0, value=float(at.get("manual_score") or 0.0), key=manual_total_key)
                                    if st.button("💾 Save Grade & Feedback", key=f"save_grade_{at['id']}"):
                                        try:
                                            q_answers = supabase.table("quiz_answers").select("*").eq("attempt_id", at['id']).execute().data or []
                                            num_mcq = 0
                                            mcq_correct = 0
                                            for a_r in q_answers:
                                                qrec = supabase.table("quiz_questions").select("type").eq("id", a_r["question_id"]).execute().data
                                                qtype = qrec[0]["type"] if qrec else None
                                                if qtype == "multiple_choice":
                                                    num_mcq += 1
                                                    if a_r.get("is_correct"):
                                                        mcq_correct += 1
                                            mcq_percent = (mcq_correct / num_mcq * 100) if num_mcq>0 else None
                                            essay_percent = (manual_total / total_manual_max * 100) if total_manual_max>0 else None
                                            if mcq_percent is None and essay_percent is None:
                                                final_percent = 0.0
                                            elif mcq_percent is None:
                                                final_percent = essay_percent
                                            elif essay_percent is None:
                                                final_percent = mcq_percent
                                            else:
                                                final_percent = (mcq_percent + essay_percent)/2.0
                                            final_score = round(final_percent,2)
                                            supabase.table("quiz_attempts").update({
                                                "manual_score": float(manual_total),
                                                "teacher_feedback": teacher_feedback,
                                                "score": final_score
                                            }).eq("id", at['id']).execute()
                                            st.success("✅ Grade saved.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Failed to save grade: {e}")
    
                    # --- Instructor: Delete Quiz ---
                    if user["role"] == "instructor":
                        st.divider()
                        if st.button(f"🗑️ Delete Quiz '{q['title']}'", key=f"del_quiz_{q['id']}"):
                            supabase.table("quiz_questions").delete().eq("quiz_id", q["id"]).execute()
                            supabase.table("quizzes").delete().eq("id", q["id"]).execute()
                            st.success("🗑️ Quiz deleted!")
                            st.rerun()
    
        # --- Create new quiz (instructor) ---
        if user["role"] == "instructor":
            st.divider()
            with st.form("add_quiz"):
                title = st.text_input("Quiz Title")
                desc = st.text_area("Quiz Description (supports Markdown, LaTeX, and YouTube link)")
                attempt_limit = st.number_input("Attempt limit (0 = unlimited)", min_value=0, value=0, step=1)
                ok = st.form_submit_button("➕ Create Quiz")
                if ok and title:
                    try:
                        supabase.table("quizzes").insert({
                            "course_id": cid,
                            "title": title,
                            "description": desc,
                            "attempt_limit": int(attempt_limit)
                        }).execute()
                        st.success("✅ Quiz created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to create quiz: {e}")
    
        # --- Add question (instructor) ---
        if user["role"] == "instructor" and quizzes:
            st.markdown("### ➕ Add Question to Quiz")
            quiz_list = {q["title"]: q["id"] for q in quizzes}
            selected_quiz = st.selectbox("Select Quiz", list(quiz_list.keys()))
            qid = quiz_list[selected_quiz]
            with st.form("add_question_rich"):
                question_text = st.text_area("Question Text (Markdown + LaTeX supported)", height=150)
                question_image = st.file_uploader("Upload Question Image (optional)", type=["png","jpg","jpeg"])
                q_type = st.selectbox("Type", ["multiple_choice","short_answer"])
                rubric_max = st.text_input("Rubric max score (leave empty for none)")
                rubric_note = st.text_input("Rubric note (optional)")
                img_markdown = ""
                if question_image:
                    try:
                        img_bytes = question_image.read()
                        file_path = f"uploads/{int(datetime.now().timestamp())}_{question_image.name}"
                        supabase.storage.from_("thinkverse_uploads").upload(file_path, img_bytes)
                        public_url = supabase.storage.from_("thinkverse_uploads").get_public_url(file_path).get("publicUrl")
                        img_markdown = f"![image]({public_url})"
                        question_text += "\n" + img_markdown
                    except Exception as e:
                        st.warning(f"❌ Failed to upload image: {e}")
                choices = ""
                correct = ""
                if q_type == "multiple_choice":
                    choices = st.text_area("Choices (pipe | sep)")
                    correct = st.text_input("Correct answer (exact string match)")
                submit_q = st.form_submit_button("➕ Add Question")
                if submit_q and question_text:
                    rubric_data = None
                    if rubric_max:
                        try:
                            rubric_data = json.dumps({"max_score": float(rubric_max), "note": rubric_note})
                        except:
                            rubric_data = None
                    insert_data = {
                        "quiz_id": qid,
                        "question": question_text,
                        "type": q_type,
                        "choices": choices if q_type=="multiple_choice" else None,
                        "correct_answer": correct if q_type=="multiple_choice" else None,
                        "rubric": rubric_data
                    }
                    try:
                        supabase.table("quiz_questions").insert(insert_data).execute()
                        st.success("✅ Question added successfully!")
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


    # =====================================
    # FORUM DISKUSI (REVISI: includes delete + safe insert)
    # =====================================
    with tabs[6]:
        from datetime import datetime
        import random
        import traceback
    
        st.subheader("💬 Forum Diskusi Kursus")
    
        # ---------------------------------------
        #  FUNGSI AVATAR WARNA
        # ---------------------------------------
        def user_avatar(uid):
            random.seed(uid)
            colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]
            return colors[uid % len(colors)]
    
        # ---------------------------------------
        #  FORM BUAT TOPIK DISKUSI (KHUSUS INSTRUCTOR)
        # ---------------------------------------
        if user["role"] == "instructor":
            with st.expander("➕ Buat Topik Diskusi Baru", expanded=False):
                with st.form("new_topic_form", clear_on_submit=True):
                    title = st.text_input("Judul Topik Diskusi")
                    content = st.text_area("Isi Diskusi", height=150)
                    submit_topic = st.form_submit_button("💬 Posting Topik")
    
                    if submit_topic:
                        if not title.strip() or not content.strip():
                            st.warning("Judul dan isi tidak boleh kosong.")
                        else:
                            supabase.table("discussions").insert({
                                "course_id": cid,
                                "user_id": user["id"],
                                "title": title.strip(),
                                "content": content.strip(),
                                "created_at": datetime.now().isoformat()
                            }).execute()
                            st.success("Topik diskusi berhasil dibuat!")
                            st.rerun()
    
        # ---------------------------------------
        #  AMBIL SEMUA TOPIK
        # ---------------------------------------
        topics = (
            supabase.table("discussions")
            .select("*")
            .eq("course_id", cid)
            .order("created_at", desc=True)
            .execute()
            .data
        )
    
        if not topics:
            st.info("📭 Belum ada topik diskusi.")
            st.stop()
    
        # ---------------------------------------
        #  LOOP SEMUA TOPIK
        # ---------------------------------------
        for t in topics:
    
            # — Ambil nama pembuat topik
            nq = supabase.table("users").select("name").eq("id", t["user_id"]).execute()
            topic_owner = nq.data[0]["name"] if nq.data else f"User #{t['user_id']}"
    
            # — TAMPILKAN TOPIK
            st.markdown(
                f"""
                <div style='background:#F1F5F9; padding:15px; border-radius:10px;
                            margin-bottom:8px; border-left:6px solid #3B82F6;'>
                    <h3 style='margin:0;'>💭 {t['title']}</h3>
                    <small><b>{topic_owner}</b></small><br>
                    <p style='margin-top:6px;color:#334155;'>{t['content']}</p>
                    <small style='color:#64748B;'>
                        🕒 {datetime.fromisoformat(t['created_at']).strftime('%d %b %Y, %H:%M')}
                    </small>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
            # — BUTTON HAPUS TOPIK
            if user["role"] == "instructor":
                if st.button(f"🗑️ Hapus Topik '{t['title']}'", key=f"del_topic_{t['id']}"):
                    supabase.table("discussion_replies").delete().eq("discussion_id", t["id"]).execute()
                    supabase.table("discussions").delete().eq("id", t["id"]).execute()
                    st.success("Topik & semua komentarnya terhapus.")
                    st.rerun()
    
            st.markdown("### 💬 Komentar")
    
            # ---------------------------------------
            #  AMBIL SEMUA KOMENTAR
            # ---------------------------------------
            replies = (
                supabase.table("discussion_replies")
                .select("*")
                .eq("discussion_id", t["id"])
                .order("created_at", desc=False)
                .execute()
                .data
            )
    
            # Map parent → children
            reply_map = {}
            for r in replies:
                reply_map.setdefault(r.get("parent_id"), []).append(r)
    
            top_level = reply_map.get(None, [])
    
            # ---------------------------------------
            #  TAMPILKAN KOMENTAR LEVEL 1
            # ---------------------------------------
            for r in top_level:
            
                # Ambil nama user
                try:
                    qname = supabase.table("users").select("name").eq("id", r["user_id"]).execute()
                    name = qname.data[0]["name"] if qname.data else f"User #{r['user_id']}"
                except Exception as e:
                    st.error("❌ SUPABASE ERROR SAAT AMBIL NAMA USER:")
                    st.error(str(e))
                    st.error(f"user_id yang dicari = {r['user_id']}")
                    st.stop()
            
                avatar_color = user_avatar(r["user_id"])
            
                html = f"""
                <div style="background:#F8FAFC; padding:12px; border-radius:10px;
                            margin-bottom:10px;">
                    <div style="display:flex; gap:10px;">
                        <div style="width:40px;height:40px;border-radius:50%;
                                    background:{avatar_color};
                                    color:white;display:flex;align-items:center;
                                    justify-content:center;font-weight:bold;">
                            {r['user_id'] % 100}
                        </div>
                        <div style="flex:1;">
                            <b>{name}</b><br>
                            <div style="margin-top:5px;">{r['reply']}</div>
                            <small style="color:#64748B;">
                                🕒 {datetime.fromisoformat(r['created_at']).strftime('%d %b %Y, %H:%M')}
                            </small>
                        </div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
            
                # DELETE KOMENTAR
                if user["role"] == "instructor" or user["id"] == r["user_id"]:
                    if st.button("🗑️ Hapus Komentar", key=f"del_reply_{r['id']}"):
                        supabase.table("discussion_replies").delete().eq("id", r["id"]).execute()
                        st.rerun()

    
                # ---------------------------------------
                #  TAMPILKAN BALASAN LEVEL 2
                # ---------------------------------------
                children = reply_map.get(r["id"], [])
                for child in children:
                    uq2 = supabase.table("users").select("name").eq("id", child["user_id"]).execute()
                    child_name = uq2.data[0]["name"] if uq2.data else f"User #{child['user_id']}"
                    child_color = user_avatar(child["user_id"])
    
                    st.markdown(
                        f"""
                        <div style='margin-left:45px; background:#EEF2FF; padding:12px;
                                    border-radius:10px; margin-bottom:10px;'>
                            <div style='display:flex; gap:10px;'>
                                <div style='width:34px;height:34px;border-radius:50%;
                                            background:{child_color};
                                            color:white;display:flex;
                                            align-items:center;justify-content:center;'>
                                    {child['user_id'] % 100}
                                </div>
                                <div style='flex:1;'>
                                    <b>{child_name}</b><br>
                                    <div style='margin-top:5px;'>{child['reply']}</div>
                                    <small style='color:#64748B;'>
                                        🕒 {datetime.fromisoformat(child['created_at']).strftime('%d %b %Y, %H:%M')}
                                    </small>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    
                    if user["role"] == "instructor" or user["id"] == child["user_id"]:
                        if st.button("🗑️ Hapus Balasan", key=f"del_child_{child['id']}"):
                            supabase.table("discussion_replies").delete().eq("id", child["id"]).execute()
                            st.rerun()
    
                # ---------------------------------------
                #  FORM BALAS (LEVEL 2)
                # ---------------------------------------
                with st.form(f"reply_child_form_{r['id']}", clear_on_submit=True):
                    reply2 = st.text_input("Balas komentar ini:", key=f"child_input_{r['id']}")
                    send2 = st.form_submit_button("↪ Balas")
    
                    if send2:
                        if reply2.strip():
                            supabase.table("discussion_replies").insert({
                                "discussion_id": t["id"],
                                "user_id": user["id"],
                                "reply": reply2.strip(),
                                "parent_id": r["id"],
                                "created_at": datetime.now().isoformat()
                            }).execute()
                            st.success("Balasan terkirim!")
                            st.rerun()
    
            # ---------------------------------------
            #  FORM KOMENTAR LEVEL 1
            # ---------------------------------------
            st.markdown("### ✏️ Tambah Komentar")
            with st.form(f"add_comment_{t['id']}", clear_on_submit=True):
                new_comment = st.text_area("Tulis komentar:", height=100)
                send_comment = st.form_submit_button("Kirim")
    
                if send_comment:
                    if new_comment.strip():
                        supabase.table("discussion_replies").insert({
                            "discussion_id": t["id"],
                            "user_id": user["id"],
                            "reply": new_comment.strip(),
                            "parent_id": None,
                            "created_at": datetime.now().isoformat()
                        }).execute()
                        st.success("Komentar ditambahkan!")
                        st.rerun()

    # =============================
    # TAB 7 — STUDENT PROGRESS + KICK STUDENT (GURU)
    # =============================
    if user["role"] == "instructor":
        with tabs[7]:
            st.subheader("👥 Daftar Siswa di Kursus Ini (Klik → lihat progress)")
    
            # Ambil semua siswa terdaftar
            try:
                enroll_resp = (
                    supabase.table("enrollments")
                    .select("user_id")
                    .eq("course_id", cid)
                    .eq("role", "student")
                    .execute()
                )
                enroll = enroll_resp.data or []
            except Exception as e:
                st.error("❌ Gagal memuat daftar enrollments:")
                st.error(str(e))
                st.stop()
    
            if not enroll:
                st.info("Belum ada siswa yang bergabung di kursus ini.")
                st.stop()
    
            student_ids = [e["user_id"] for e in enroll]
    
            # Ambil data siswa (users)
            try:
                users_resp = (
                    supabase.table("users")
                    .select("id, name, email")
                    .in_("id", student_ids)
                    .execute()
                )
                students = users_resp.data or []
            except Exception as e:
                st.error("❌ Gagal memuat data users:")
                st.error(str(e))
                st.stop()
    
            # tombol pilih siswa + tombol kick
            selected_student = st.session_state.get("selected_student", None)
    
            for s in students:
                col1, col2, col3 = st.columns([0.6, 0.25, 0.15])
    
                # DATA SISWA
                with col1:
                    st.markdown(
                        f"""
                        <div style='padding:10px; margin-bottom:8px; background:#F8FAFC;
                                    border-radius:8px; border-left:4px solid #10B981;'>
                            <b>{s.get('name','-')}</b><br>
                            <small>{s.get('email','-')}</small><br>
                            <small>User ID: {s.get('id')}</small>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )
    
                # LIHAT PROGRESS
                with col2:
                    if st.button("Lihat Progress", key=f"progress_{s['id']}"):
                        st.session_state["selected_student"] = s["id"]
                        st.rerun()
    
                # KICK STUDENT (FITUR BARU)
                with col3:
                    if st.button("❌ Kick", key=f"kick_{s['id']}"):
                        try:
                            supabase.table("enrollments").delete().eq("user_id", s["id"]).eq(
                                "course_id", cid
                            ).execute()
                            st.success(f"🚪 {s['name']} berhasil dikeluarkan dari course.")
                            st.rerun()
                        except Exception as e:
                            st.error("❌ Gagal mengeluarkan siswa:")
                            st.error(str(e))
    
            # Jika belum memilih siswa → stop
            selected_student = st.session_state.get("selected_student")
            if not selected_student:
                st.info("Klik tombol **Lihat Progress** untuk melihat perkembangan siswa.")
                st.stop()
    
            st.markdown("---")
            st.markdown(f"## 📊 Progress Siswa — ID {selected_student}")
    
            # ---------- Helper to safe fetch table ----------
            def safe_fetch(table_name, select="*", filters=None):
                try:
                    rb = supabase.table(table_name).select(select)
                    if filters:
                        for f in filters:
                            col, op, val = f
                            if op == "eq":
                                rb = rb.eq(col, val)
                            elif op == "in":
                                rb = rb.in_(col, val)
                            elif op == "neq":
                                rb = rb.neq(col, val)
                    resp = rb.execute()
                    return (resp.data or [], None)
                except Exception as e:
                    return (None, str(e))
    
            # ====================
            # 1) Kehadiran (attendance)
            # ====================
            st.markdown("### 🕒 Kehadiran")
            att_data, err = safe_fetch(
                "attendance",
                select="id,session_id,user_id,status,timestamp",
                filters=[("course_id", "eq", cid), ("user_id", "eq", selected_student)],
            )
            if err:
                st.error("❌ Gagal memuat data attendance:")
                st.error(err)
            else:
                total = len(att_data)
                hadir = sum(
                    1 for a in att_data if str(a.get("status", "")).lower() == "present"
                )
                percent = round((hadir / total) * 100, 2) if total > 0 else 0
                st.write(f"Hadir **{hadir}/{total}** — **{percent}%**")
                for a in att_data:
                    st.markdown(
                        f"- Sesi {a.get('session_id')} — {a.get('status')} — {a.get('timestamp')}"
                    )
    
            # ====================
            # 2) Assignments
            # ====================
            st.markdown("### 📝 Tugas / Assignment")
    
            assigns, err = safe_fetch(
                "assignments", select="id,title", filters=[("course_id", "eq", cid)]
            )
            if not err and assigns:
                for a in assigns:
                    subs, e2 = safe_fetch(
                        "assignment_submissions",
                        select="id,assignment_id,user_id,score,file_url,submitted_at",
                        filters=[
                            ("assignment_id", "eq", a["id"]),
                            ("user_id", "eq", selected_student),
                        ],
                    )
                    if subs:
                        s0 = subs[0]
                        score = s0.get("score")
                        if score is None:
                            st.markdown(
                                f"- **{a['title']}** — ⏳ Menunggu penilaian (submitted: {s0.get('submitted_at')})"
                            )
                        else:
                            st.markdown(
                                f"- **{a['title']}** — ✅ Dinilai — Skor: {score}"
                            )
                    else:
                        st.markdown(f"- **{a['title']}** — ❌ Belum mengumpulkan")
            else:
                st.info("Belum ada assignment untuk course ini.")
    
            # ====================
            # 3) Quiz
            # ====================
            st.markdown("### 🧠 Quiz")
    
            quizzes, errq = safe_fetch(
                "quizzes", select="id,title", filters=[("course_id", "eq", cid)]
            )
            if not errq and quizzes:
                for q in quizzes:
                    attempts, aerr = safe_fetch(
                        "quiz_attempts",
                        select="id,quiz_id,user_id,score,submitted_at,attempt_number",
                        filters=[
                            ("quiz_id", "eq", q["id"]),
                            ("user_id", "eq", selected_student),
                        ],
                    )
    
                    if attempts:
                        st.markdown(f"**{q['title']}** — Total percobaan: {len(attempts)}")
                        for at in attempts:
                            submitted_time = at.get("submitted_at")
                            status = "✅ Selesai" if submitted_time else "❌ Belum mengerjakan"
                            time_str = f"waktu: {submitted_time}" if submitted_time else ""
                            st.markdown(
                                f"- Skor: {at.get('score','-')} — {status} {time_str} — Attempt #{at.get('attempt_number','-')}"
                            )
                    else:
                        st.markdown(f"- **{q['title']}** — ❌ Belum mengerjakan")
            else:
                st.info("Belum ada quiz pada course ini.")

    
            # ====================
            # 3) Quiz
            # ====================
            st.markdown("### 🧠 Quiz")
    
            quizzes, errq = safe_fetch(
                "quizzes", select="id,title", filters=[("course_id", "eq", cid)]
            )
            if not errq and quizzes:
                for q in quizzes:
                    attempts, aerr = safe_fetch(
                        "quiz_attempts",
                        select="id,quiz_id,user_id,score,attempted_at",
                        filters=[
                            ("quiz_id", "eq", q["id"]),
                            ("user_id", "eq", selected_student),
                        ],
                    )
    
                    if attempts:
                        for at in attempts:
                            st.markdown(
                                f"- **{q['title']}** — Skor: {at.get('score')} — waktu: {at.get('attempted_at')}"
                            )
                    else:
                        st.markdown(f"- **{q['title']}** — ❌ Belum mengerjakan")
            else:
                st.info("Belum ada quiz pada course ini.")


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
    # === SIMPAN WAKTU TERAKHIR SISWA BACA PENGUMUMAN ===
    if "last_announcement_check" not in st.session_state:
        st.session_state.last_announcement_check = None

    # === NAVIGASI BALIK JIKA KELUAR DARI COURSE ===
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
        # === FALLBACK KE LOGIN ===
        st.session_state.page = "login"
        st.rerun()


# === Panggil fungsi utama ===
if __name__ == "__main__":
    main()















