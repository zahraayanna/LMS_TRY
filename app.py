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

def login(email, password):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if not res.data:
        return None

    user = res.data[0]
    stored_pw = user.get("password_hash")

    # Cek apakah password tersimpan sebagai hash atau plaintext
    if stored_pw is None:
        return None

    # Kalau hash — cocokkan dengan SHA256
    try:
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if stored_pw == hashed_input:
            return user
    except:
        pass

    # Kalau plaintext — cocokkan langsung
    if stored_pw == password:
        return user

    return None


def register_user(name, email, password, role="student"):
    res = supabase.table("users").select("email").eq("email", email).execute()
    if res.data:
        return False
    supabase.table("users").insert({
        "name": name,
        "email": email,
        "password_hash": password,
        "role": role
    }).execute()
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
def page_course_detail():
    cid = st.session_state.course_id
    c = supabase.table("courses").select("*").eq("id", cid).execute().data[0]
    st.title(f"📘 {c['title']}")
    st.caption(c["description"])

    tabs = st.tabs(["📄 Materi", "🧩 Tugas", "🧠 Kuis"])

    # --- ASSIGNMENTS ---
    with tabs[1]:
        st.subheader("🧩 Daftar Tugas")
        tasks = supabase.table("assignments").select("*").eq("course_id", cid).execute().data
        for t in tasks:
            with st.container(border=True):
                st.write(f"### {t['title']}")
                st.caption(t["description"])
                if "due_date" in t and t["due_date"]:
                    st.info(f"Deadline: {t['due_date']}")
                if st.session_state.user["role"] == "student":
                    answer = st.text_area(f"Jawaban kamu ({t['title']})", key=f"ans_{t['id']}")
                    if st.button("Kirim Jawaban", key=f"send_{t['id']}"):
                        supabase.table("submissions").insert({
                            "assignment_id": t["id"],
                            "student_id": st.session_state.user["id"],
                            "answer_text": answer
                        }).execute()
                        st.success("Jawaban dikirim!")

        if st.session_state.user["role"] == "instructor":
            with st.expander("➕ Tambah Tugas Baru"):
                title = st.text_input("Judul Tugas")
                desc = st.text_area("Deskripsi")
                if st.button("Simpan Tugas"):
                    supabase.table("assignments").insert({
                        "course_id": cid,
                        "title": title,
                        "description": desc
                    }).execute()
                    st.success("Tugas berhasil ditambahkan!")
                    st.rerun()

    # --- QUIZZES ---
    with tabs[2]:
        st.subheader("🧠 Kuis")
        quizzes = supabase.table("quizzes").select("*").eq("course_id", cid).execute().data
        for q in quizzes:
            st.write(f"### {q['title']}")
            st.caption(q["description"])
            if st.button(f"Kerjakan {q['title']}", key=f"quiz_{q['id']}"):
                st.session_state.quiz_id = q["id"]
                st.session_state.page = "quiz_page"
                st.rerun()

        if st.session_state.user["role"] == "instructor":
            with st.expander("➕ Tambah Kuis Baru"):
                title = st.text_input("Judul Kuis")
                desc = st.text_area("Deskripsi")
                if st.button("Simpan Kuis"):
                    supabase.table("quizzes").insert({
                        "course_id": cid,
                        "title": title,
                        "description": desc
                    }).execute()
                    st.success("Kuis berhasil ditambahkan!")
                    st.rerun()


# ======================
# === QUIZ PAGE ===
# ======================
def page_quiz():
    qid = st.session_state.quiz_id
    quiz = supabase.table("quizzes").select("*").eq("id", qid).execute().data[0]
    st.title(f"🧠 {quiz['title']}")
    st.caption(quiz["description"])

    questions = supabase.table("quiz_questions").select("*").eq("quiz_id", qid).execute().data

    score = 0
    for q in questions:
        st.write(f"### {q['question_text']}")
        if q["question_type"] == "mcq":
            options = json.loads(q["options"])
            choice = st.radio("Pilih jawaban:", options, key=f"q_{q['id']}")
            if st.button("Kirim Jawaban", key=f"ans_btn_{q['id']}"):
                correct = choice == q["correct_answer"]
                points = q["points"] if correct else 0
                supabase.table("quiz_responses").insert({
                    "quiz_id": qid,
                    "student_id": st.session_state.user["id"],
                    "question_id": q["id"],
                    "selected_option": choice,
                    "is_correct": correct,
                    "points_earned": points
                }).execute()
                if correct:
                    st.success("Jawaban benar!")
                else:
                    st.error(f"Jawaban salah. Jawaban benar: {q['correct_answer']}")
        else:
            ans = st.text_input("Jawaban singkat:", key=f"short_{q['id']}")
            if st.button("Kirim Jawaban", key=f"short_btn_{q['id']}"):
                correct = ans.strip().lower() == q["correct_answer"].strip().lower()
                points = q["points"] if correct else 0
                supabase.table("quiz_responses").insert({
                    "quiz_id": qid,
                    "student_id": st.session_state.user["id"],
                    "question_id": q["id"],
                    "answer_text": ans,
                    "is_correct": correct,
                    "points_earned": points
                }).execute()
                if correct:
                    st.success("✅ Benar!")
                else:
                    st.error(f"❌ Salah. Jawaban benar: {q['correct_answer']}")


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

