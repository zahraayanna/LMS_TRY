import streamlit as st
from supabase import create_client
import time
from datetime import datetime
import json

# =========================
# === KONFIGURASI AWAL ===
# =========================
st.set_page_config(page_title="ThinkVerse LMS", page_icon="🎓", layout="wide")

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
    u = st.session_state.user
    st.header("📘 Kursus")
    st.write("Daftar kursus yang tersedia di ThinkVerse.")

    res = supabase.table("courses").select("*").execute()
    courses = res.data

    for c in courses:
        with st.container(border=True):
            st.subheader(c["title"])
            st.caption(c["description"] or "Tanpa deskripsi.")
            if st.button(f"Masuk ke {c['title']}", key=f"enter_{c['id']}"):
                st.session_state.page = "course_detail"
                st.session_state.course_id = c["id"]
                st.rerun()

    if u["role"] == "instructor":
        with st.expander("➕ Tambah Kursus Baru"):
            title = st.text_input("Judul Kursus")
            desc = st.text_area("Deskripsi Kursus")
            if st.button("Simpan Kursus"):
                supabase.table("courses").insert({
                    "title": title,
                    "description": desc,
                    "instructor_id": u["id"]
                }).execute()
                st.success("Kursus berhasil ditambahkan!")
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
def page_course_detail():
    if "current_course" not in st.session_state:
        st.warning("⚠️ No course selected. Please go back to the Courses page.")
        st.stop()

    cid = st.session_state.current_course
    user = st.session_state.user


    st.title("🎓 Course Details")
    course_data = supabase.table("courses").select("*").eq("id", cid).execute().data[0]

    tabs = st.tabs(["🏠 Dashboard", "🕒 Attendance", "📦 Modules", "🧩 Assignments", "🧠 Quizzes", "📣 Announcements"])

    # ===================================================
    # 1️⃣ DASHBOARD
    # ===================================================
    with tabs[0]:
        st.subheader("🏠 Course Dashboard")

        if course_data.get("youtube_url"):
            st.video(course_data["youtube_url"])

        st.markdown("### 📝 Course Description")
        if course_data.get("description"):
            st.markdown(course_data["description"])
        else:
            st.info("This course has no description yet.")

        if course_data.get("book_embed"):
            st.markdown("### 📚 Course Book / Guide")
            st.components.v1.iframe(course_data["book_embed"], height=500)

        if user["role"] == "instructor":
            with st.expander("✏️ Edit Dashboard"):
                yt = st.text_input("YouTube URL", value=course_data.get("youtube_url", ""), key="yt_dash")
                desc = st.text_area("Course Description", value=course_data.get("description", ""), key="desc_dash")
                book = st.text_input("Book Embed Link (Google Drive / LiveBook / Issuu)", value=course_data.get("book_embed", ""), key="book_dash")
                if st.button("💾 Save Dashboard", key="save_dash"):
                    supabase.table("courses").update({
                        "youtube_url": yt,
                        "description": desc,
                        "book_embed": book
                    }).eq("id", cid).execute()
                    st.success("Course dashboard updated successfully!")
                    st.rerun()

    # ===================================================
    # 2️⃣ ATTENDANCE
    # ===================================================
    with tabs[1]:
        st.subheader("🕒 Attendance")
        if user["role"] == "instructor":
            with st.expander("➕ Create Attendance Session"):
                title = st.text_input("Session Title", key="att_title")
                date = st.date_input("Session Date", key="att_date")
                code = st.text_input("Access Code (optional)", key="att_code")
                open_now = st.checkbox("Open attendance immediately", value=True)
                if st.button("💾 Create Session", key="att_save"):
                    if not code:
                        code = str(int(datetime.now().timestamp()))[-6:]
                    supabase.table("attendance_sessions").insert({
                        "course_id": cid,
                        "title": title,
                        "session_date": str(date),
                        "access_code": code,
                        "is_open": open_now
                    }).execute()
                    st.success("Attendance session created successfully!")
                    st.rerun()

        sessions = supabase.table("attendance_sessions").select("*").eq("course_id", cid).order("id", desc=True).execute().data
        if not sessions:
            st.info("No attendance sessions yet.")
        else:
            for s in sessions:
                with st.expander(f"{s['title']} — {s['session_date']} {'🟢 OPEN' if s['is_open'] else '🔴 CLOSED'}"):
                    st.caption(f"Access Code: `{s['access_code']}`")

                    if user["role"] == "student":
                        if s["is_open"]:
                            code_in = st.text_input("Enter attendance code:", key=f"att_in_{s['id']}")
                            if st.button("✅ Mark Attendance", key=f"mark_{s['id']}"):
                                if code_in.strip() == (s.get("access_code") or "").strip():
                                    supabase.table("attendance_logs").insert({
                                        "session_id": s["id"],
                                        "student_id": user["id"],
                                        "marked_at": str(datetime.now())
                                    }).execute()
                                    st.success("Your attendance has been recorded!")
                                else:
                                    st.error("Incorrect code.")
                        else:
                            st.info("This session is closed.")

                    elif user["role"] == "instructor":
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            if st.button("🟢 Open", key=f"open_{s['id']}"):
                                supabase.table("attendance_sessions").update({"is_open": True}).eq("id", s["id"]).execute()
                                st.rerun()
                        with c2:
                            if st.button("🔴 Close", key=f"close_{s['id']}"):
                                supabase.table("attendance_sessions").update({"is_open": False}).eq("id", s["id"]).execute()
                                st.rerun()

                        logs = supabase.table("attendance_logs").select("*").eq("session_id", s["id"]).execute().data
                        if not logs:
                            st.caption("No attendance records yet.")
                        else:
                            st.markdown("#### Attendance List:")
                            for l in logs:
                                st.markdown(f"- 👤 **Student ID:** {l['student_id']} at {l['marked_at']}")

    # ===================================================
    # 3️⃣ MODULES
    # ===================================================
    with tabs[2]:
        st.subheader("📦 Course Modules")

        if user["role"] == "instructor":
            with st.expander("➕ Add New Module"):
                title = st.text_input("Module Title", key="mod_title")
                content = st.text_area("Module Content (Markdown supported)", key="mod_content")
                youtube = st.text_input("YouTube Link (optional)", key="mod_yt")
                order = st.number_input("Order Index", min_value=0, max_value=999, value=0, key="mod_order")
                img = st.file_uploader("Upload Image (optional)", type=["jpg","jpeg","png"], key="mod_img")
                if st.button("💾 Save Module", key="mod_save"):
                    img_url = None
                    if img:
                        file_bytes = img.getvalue()
                        file_path = f"modules/{cid}_{datetime.now().timestamp()}_{img.name}"
                        supabase.storage.from_("thinkverse_uploads").upload(file_path, file_bytes)
                        img_url = supabase.storage.from_("thinkverse_uploads").get_public_url(file_path)
                    supabase.table("modules").insert({
                        "course_id": cid,
                        "title": title,
                        "content": content,
                        "youtube_url": youtube,
                        "image_url": img_url,
                        "order_index": order
                    }).execute()
                    st.success("Module added successfully!")
                    st.rerun()

        modules = supabase.table("modules").select("*").eq("course_id", cid).order("order_index").execute().data
        if not modules:
            st.info("No modules have been added yet.")
        else:
            for m in modules:
                with st.expander(f"{m['order_index']}. {m['title']}"):
                    if m.get("youtube_url"):
                        st.video(m["youtube_url"])
                    if m.get("image_url"):
                        st.image(m["image_url"], use_container_width=True)
                    if m.get("content"):
                        st.markdown(m["content"])

                    if user["role"] == "instructor":
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("✏️ Edit", key=f"edit_mod_{m['id']}"):
                                st.session_state[f"edit_mod_{m['id']}"] = not st.session_state.get(f"edit_mod_{m['id']}", False)
                        with col2:
                            if st.button("🗑️ Delete", key=f"del_mod_{m['id']}"):
                                supabase.table("modules").delete().eq("id", m["id"]).execute()
                                st.success("Module deleted.")
                                st.rerun()

                    if st.session_state.get(f"edit_mod_{m['id']}", False):
                        st.markdown(f"### Editing: {m['title']}")
                        new_title = st.text_input("Title", value=m["title"], key=f"et_{m['id']}")
                        new_content = st.text_area("Content", value=m["content"] or "", key=f"ec_{m['id']}")
                        new_yt = st.text_input("YouTube URL", value=m.get("youtube_url",""), key=f"ey_{m['id']}")
                        new_order = st.number_input("Order", 0, 999, m["order_index"], key=f"eo_{m['id']}")
                        if st.button("💾 Save Changes", key=f"sv_{m['id']}"):
                            supabase.table("modules").update({
                                "title": new_title,
                                "content": new_content,
                                "youtube_url": new_yt,
                                "order_index": new_order
                            }).eq("id", m["id"]).execute()
                            st.success("Module updated.")
                            st.session_state[f"edit_mod_{m['id']}"] = False
                            st.rerun()

    # ===================================================
    # 2️⃣ TAB TUGAS
    # ===================================================
    with tabs[3]:
        st.subheader("🧩 Daftar Tugas")
        user = st.session_state.user
        tasks = supabase.table("assignments").select("*").eq("course_id", cid).execute().data

        # === Tampilkan semua tugas ===
        if not tasks:
            st.info("Belum ada tugas di kursus ini.")
        else:
            for t in tasks:
                with st.container(border=True):
                    st.markdown(f"### {t['title']}")
                    st.markdown(t.get("description", ""))

                    # tampilkan embed konten
                    if t.get("embed_url"):
                        if "youtube" in t["embed_url"]:
                            st.video(t["embed_url"])
                        else:
                            st.components.v1.iframe(t["embed_url"], height=400)

                    if t.get("image_url"):
                        st.image(t["image_url"], width=400)

                    if t.get("due_date"):
                        st.caption(f"🕒 Deadline: {t['due_date']}")

                    st.markdown(f"**Tipe Pengumpulan:** `{t.get('submission_type', 'Teks/Upload')}`")

                    # === Mode siswa ===
                    if user["role"] == "student":
                        st.markdown("#### Kirim Jawaban")

                        # cek tipe pengumpulan
                        submission_type = t.get("submission_type", "text")

                        if submission_type == "text":
                            answer = st.text_area("Tulis jawaban di sini:", key=f"ans_{t['id']}")
                            file = None

                        elif submission_type == "pdf":
                            file = st.file_uploader("Unggah file PDF jawaban kamu:", type=["pdf"], key=f"file_{t['id']}")
                            answer = None

                        elif submission_type == "image":
                            file = st.file_uploader("Unggah gambar jawaban kamu:", type=["jpg", "png"], key=f"file_{t['id']}")
                            answer = None

                        elif submission_type == "mixed":
                            answer = st.text_area("Tulis jawaban (opsional):", key=f"ans_{t['id']}")
                            file = st.file_uploader("Unggah file tambahan (PDF/Gambar):", type=["pdf", "jpg", "png"], key=f"file_{t['id']}")

                        if st.button("📤 Kirim Jawaban", key=f"submit_{t['id']}"):
                            file_url = upload_to_supabase(file) if file else None
                            supabase.table("submissions").insert({
                                "assignment_id": t["id"],
                                "student_id": user["id"],
                                "answer_text": answer,
                                "file_url": file_url,
                                "submitted_at": str(datetime.now())
                            }).execute()
                            st.success("✅ Jawaban kamu berhasil dikirim!")
                            st.rerun()

                    # === Mode guru ===
                    elif user["role"] == "instructor":
                        st.divider()
                        st.markdown("#### Kiriman Siswa:")
                        subs = supabase.table("submissions").select("*").eq("assignment_id", t["id"]).execute().data
                        if not subs:
                            st.caption("Belum ada jawaban siswa.")
                        else:
                            for s in subs:
                                st.markdown(f"👤 **Siswa ID:** {s['student_id']}")
                                if s.get("answer_text"):
                                    st.markdown(f"📝 **Jawaban:** {s['answer_text']}")
                                if s.get("file_url"):
                                    st.markdown(f"[📎 Lihat File]({s['file_url']})")
                                st.caption(f"🕒 {s.get('submitted_at', '-')}")
                                st.divider()

        # === Tambah tugas (guru) ===
        if user["role"] == "instructor":
            with st.expander("➕ Tambah Tugas Baru"):
                title = st.text_input("Judul Tugas", key="asg_title")
                desc = st.text_area("Deskripsi Tugas", key="asg_desc")
                embed_url = st.text_input("Link Embed (YouTube/LiveWorksheet/dsb)", key="asg_embed")
                submission_type = st.selectbox(
                    "Tipe Pengumpulan:",
                    ["text", "pdf", "image", "mixed"],
                    key="asg_type"
                )
                due = st.date_input("Batas Waktu (opsional)", key="asg_due")
                img = st.file_uploader("Gambar Pendukung (opsional)", key="asg_img")

                if st.button("💾 Simpan Tugas", key="asg_save"):
                    img_url = upload_to_supabase(img) if img else None
                    supabase.table("assignments").insert({
                        "course_id": cid,
                        "title": title,
                        "description": desc,
                        "embed_url": embed_url,
                        "submission_type": submission_type,
                        "due_date": str(due) if due else None,
                        "image_url": img_url
                    }).execute()
                    st.success("Tugas baru berhasil ditambahkan!")
                    st.rerun()

    # ===================================================
    # 3️⃣ TAB KUIS
    # ===================================================
    with tabs[4]:
        st.subheader("🧠 Kuis Kursus")
        user = st.session_state.user
        quizzes = supabase.table("quizzes").select("*").eq("course_id", cid).execute().data

        if not quizzes:
            st.info("Belum ada kuis untuk kursus ini.")
        else:
            for q in quizzes:
                with st.container(border=True):
                    st.markdown(f"### {q['title']}")
                    st.caption(q.get("description", ""))

                    # === Mode instruktur ===
                    if user["role"] == "instructor":
                        st.markdown("#### 📋 Daftar Soal:")
                        qs = supabase.table("quiz_questions").select("*").eq("quiz_id", q["id"]).execute().data
                        if qs:
                            for qq in qs:
                                st.markdown(f"- {qq['prompt']} ({qq['type']})")
                        else:
                            st.caption("_Belum ada soal dalam kuis ini._")

                        with st.expander("➕ Tambah Soal Baru"):
                            qtype = st.selectbox("Tipe Soal", ["mcq", "short"], key=f"qtype_{q['id']}")
                            prompt = st.text_area("Pertanyaan", key=f"prompt_{q['id']}")
                            image = st.file_uploader("Gambar (opsional)", key=f"img_{q['id']}")
                            correct_answer = st.text_input("Jawaban benar (untuk short answer)", key=f"corr_{q['id']}")
                            img_url = upload_to_supabase(image) if image else None
                            if st.button("💾 Simpan Soal", key=f"saveq_{q['id']}"):
                                data = {
                                    "quiz_id": q["id"],
                                    "prompt": prompt,
                                    "type": qtype,
                                    "image_url": img_url,
                                    "correct_answer": correct_answer if qtype == "short" else None
                                }
                                supabase.table("quiz_questions").insert(data).execute()
                                st.success("Soal berhasil ditambahkan!")
                                st.rerun()

                            # === Tambahkan pilihan jawaban (jika MCQ) ===
                            if qtype == "mcq":
                                st.markdown("**Tambahkan Pilihan Jawaban (maks 5)**")
                                opt_list = []
                                for i in range(5):  # Sekarang A sampai E
                                    text = st.text_input(f"Pilihan {chr(65+i)}", key=f"opt_{i}_{q['id']}")
                                    correct = st.checkbox(f"Benar?", key=f"corr_{i}_{q['id']}")
                                    if text:
                                        opt_list.append({"choice_text": text, "is_correct": correct})
                                if st.button("💾 Simpan Pilihan", key=f"saveopts_{q['id']}"):
                                    qq = supabase.table("quiz_questions").select("id").eq("quiz_id", q["id"]).order("id", desc=True).limit(1).execute().data
                                    if qq:
                                        qnid = qq[0]["id"]
                                        for opt in opt_list:
                                            opt["question_id"] = qnid
                                        supabase.table("quiz_choices").insert(opt_list).execute()
                                        st.success("Pilihan berhasil disimpan!")
                                        st.rerun()

                    # === Mode siswa ===
                    elif user["role"] == "student":
                        st.markdown("#### ✏️ Kerjakan Kuis Ini:")
                        qs = supabase.table("quiz_questions").select("*").eq("quiz_id", q["id"]).execute().data
                        if not qs:
                            st.caption("Belum ada soal untuk kuis ini.")
                        else:
                            total_questions = len(qs)
                            correct_count = 0

                            for qq in qs:
                                st.markdown(f"**{qq['prompt']}**")
                                if qq.get("image_url"):
                                    st.image(qq["image_url"], width=400)

                                # === Multiple Choice ===
                                if qq["type"] == "mcq":
                                    choices = supabase.table("quiz_choices").select("*").eq("question_id", qq["id"]).execute().data
                                    if choices:
                                        answer = st.radio(
                                            "Pilih jawaban:",
                                            [c["choice_text"] for c in choices],
                                            key=f"mcq_{qq['id']}"
                                        )
                                        if st.button("Kirim Jawaban", key=f"submit_mcq_{qq['id']}"):
                                            correct = any(c["is_correct"] and c["choice_text"] == answer for c in choices)
                                            supabase.table("quiz_responses").insert({
                                                "quiz_id": q["id"],
                                                "student_id": user["id"],
                                                "question_id": qq["id"],
                                                "answer_text": answer,
                                                "is_correct": correct,
                                                "submitted_at": str(datetime.now())
                                            }).execute()
                                            if correct:
                                                st.success("✅ Benar!")
                                                correct_count += 1
                                            else:
                                                st.error("❌ Salah.")

                                # === Short Answer ===
                                elif qq["type"] == "short":
                                    ans = st.text_input("Jawaban kamu:", key=f"short_{qq['id']}")
                                    if st.button("Kirim Jawaban", key=f"submit_short_{qq['id']}"):
                                        correct = False
                                        if qq.get("correct_answer"):
                                            correct = ans.strip().lower() == qq["correct_answer"].strip().lower()
                                        supabase.table("quiz_responses").insert({
                                            "quiz_id": q["id"],
                                            "student_id": user["id"],
                                            "question_id": qq["id"],
                                            "answer_text": ans,
                                            "is_correct": correct,
                                            "submitted_at": str(datetime.now())
                                        }).execute()
                                        if correct:
                                            st.success("✅ Jawaban Benar!")
                                            correct_count += 1
                                        else:
                                            st.error("❌ Jawaban Salah.")

                            st.markdown("---")
                            st.info(f"**Skor kamu:** {correct_count} / {total_questions}")

        # === Tambah kuis (guru) ===
        if user["role"] == "instructor":
            with st.expander("➕ Buat Kuis Baru"):
                title = st.text_input("Judul Kuis", key="quiz_title_new")
                desc = st.text_area("Deskripsi Kuis", key="quiz_desc_new")
                if st.button("💾 Simpan Kuis", key="quiz_save_new"):
                    supabase.table("quizzes").insert({
                        "course_id": cid,
                        "title": title,
                        "description": desc
                    }).execute()
                    st.success("Kuis baru berhasil dibuat!")
                    st.rerun()

    # ===================================================
    # 6️⃣ ANNOUNCEMENTS
    # ===================================================
    with tabs[5]:
        st.subheader("📣 Course Announcements")

        announcements = supabase.table("announcements").select("*").eq("course_id", cid).order("created_at", desc=True).execute().data
        if not announcements:
            st.info("No announcements yet.")
        else:
            for a in announcements:
                st.markdown(f"### 📢 {a['title']}")
                st.caption(f"Posted on {a['created_at']}")
                st.markdown(a["content"])
                st.divider()

        if user["role"] == "instructor":
            with st.expander("➕ Create Announcement"):
                title = st.text_input("Announcement Title", key="ann_title")
                content = st.text_area("Announcement Content", key="ann_content")
                if st.button("📤 Post Announcement", key="ann_post"):
                    supabase.table("announcements").insert({
                        "course_id": cid,
                        "title": title,
                        "content": content,
                        "created_at": str(datetime.now())
                    }).execute()
                    st.success("Announcement posted successfully!")
                    st.rerun()

# ======================
# === ROUTING ===
# ======================
def main():
    if "user" not in st.session_state:
        page_login()
    elif st.session_state.get("page") == "course_detail":
        page_course_detail()
    elif st.session_state.get("page") == "quiz_page":
        page_quiz()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()












