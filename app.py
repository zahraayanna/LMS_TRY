import streamlit as st
import sqlite3
import hashlib
import os
import io
from datetime import datetime, timedelta
import re

# === Set page config HARUS paling awal dan hanya sekali ===
st.set_page_config(page_title='ThinkVerse LMS', page_icon='🎓', layout='wide')

# =============================
# ThinkVerse LMS (Canvas-like) — FULL APP (revisi modul/quiz/assignments)
# =============================

DB_PATH = 'lms.db'
UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- Utilities ----------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def create_announcement(course_id: int, title: str, message: str, is_system: int = 1):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO announcements(course_id,title,message,is_system) VALUES(?,?,?,?)',
            (course_id, title, message, is_system)
        )
        conn.commit()

def render_user_chip():
    """Chip user di kanan atas halaman (foto + nama + role) tanpa caption gambar."""
    u = st.session_state.get('user')
    if not u: return
    col_sp, col_chip = st.columns([6, 1])
    with col_chip:
        st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
        if u.get('photo_path') and os.path.exists(u['photo_path']):
            st.image(u['photo_path'], width=64)  # tanpa caption
        st.markdown(
            f"<div style='font-size:0.85rem;color:#6b7280'>{u['name']} • {u['role']}</div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- DB ----------
def init_db():
    with get_conn() as conn:
        c = conn.cursor()

        # users (+ photo_path)
        c.execute('''CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','instructor','student')),
            photo_path TEXT
        )''')

        # courses
        c.execute('''CREATE TABLE IF NOT EXISTS courses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            youtube_url TEXT,
            access_code TEXT,
            instructor_id INTEGER
        )''')

        # enrollments
        c.execute('''CREATE TABLE IF NOT EXISTS enrollments(
            user_id INTEGER,
            course_id INTEGER,
            role TEXT NOT NULL CHECK(role IN ('instructor','student')),
            PRIMARY KEY(user_id,course_id)
        )''')

        # modules
        c.execute('''CREATE TABLE IF NOT EXISTS modules(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            youtube_url TEXT,
            image_path TEXT,
            order_index INTEGER DEFAULT 0
        )''')

        # module_images (multi-image per module)
        c.execute('''CREATE TABLE IF NOT EXISTS module_images(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            path TEXT NOT NULL,
            caption TEXT,
            order_index INTEGER DEFAULT 0
        )''')

        # assignments
        c.execute('''CREATE TABLE IF NOT EXISTS assignments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            module_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_at TEXT,
            points INTEGER DEFAULT 100,
            youtube_url TEXT,
            image_path TEXT,
            embed_url TEXT
        )''')

        # quizzes (tambah embed_url)
        c.execute('''CREATE TABLE IF NOT EXISTS quizzes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            module_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            time_limit_minutes INTEGER,
            total_points INTEGER DEFAULT 0,
            embed_url TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS quiz_questions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            qtype TEXT NOT NULL CHECK(qtype IN ('mcq','short')),
            prompt TEXT,
            latex TEXT,
            image_path TEXT,
            points INTEGER DEFAULT 1,
            correct_text TEXT,
            correct_regex TEXT,
            case_sensitive INTEGER DEFAULT 0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS quiz_choices(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            is_correct INTEGER DEFAULT 0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS quiz_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            started_at TEXT,
            submitted_at TEXT,
            score REAL
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS quiz_answers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            choice_id INTEGER,
            text_answer TEXT,
            is_correct INTEGER
        )''')

        # announcements
        c.execute('''CREATE TABLE IF NOT EXISTS announcements(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_system INTEGER DEFAULT 0,
            posted_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # books/resources (flipbook)
        c.execute('''CREATE TABLE IF NOT EXISTS course_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            embed_url TEXT NOT NULL
        )''')

        # attendance
        c.execute('''CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            session_date TEXT NOT NULL,
            access_code TEXT,
            is_open INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            marked_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, student_id)
        )''')

        # ---- light migrations ----
        def add_column_if_missing(table, column, coltype):
            c.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in c.fetchall()]
            if column not in cols:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

        # keep backwards compat / safe migrations
        add_column_if_missing('courses', 'youtube_url', 'TEXT')
        add_column_if_missing('courses', 'access_code', 'TEXT')
        add_column_if_missing('modules', 'youtube_url', 'TEXT')
        add_column_if_missing('modules', 'image_path', 'TEXT')
        add_column_if_missing('modules', 'order_index', 'INTEGER')
        add_column_if_missing('assignments', 'youtube_url', 'TEXT')
        add_column_if_missing('assignments', 'image_path', 'TEXT')
        add_column_if_missing('assignments', 'embed_url', 'TEXT')
        add_column_if_missing('assignments', 'module_id', 'INTEGER')
        add_column_if_missing('quizzes', 'module_id', 'INTEGER')
        add_column_if_missing('quizzes', 'embed_url', 'TEXT')  # migration
        add_column_if_missing('quiz_questions', 'correct_text', 'TEXT')
        add_column_if_missing('quiz_questions', 'correct_regex', 'TEXT')
        add_column_if_missing('quiz_questions', 'case_sensitive', 'INTEGER')
        add_column_if_missing('announcements', 'is_system', 'INTEGER')
        add_column_if_missing('users', 'photo_path', 'TEXT')

        conn.commit()

def seed_demo():
    with get_conn() as conn:
        c = conn.cursor()

        c.execute('SELECT COUNT(*) FROM users')
        if c.fetchone()[0] == 0:
            users = [
                ('Admin', 'admin@example.com', hash_pw('admin123'), 'admin', None),
                ('Dosen Fisika', 'instructor@example.com', hash_pw('teach123'), 'instructor', None),
                ('Zahra', 'student@example.com', hash_pw('learn123'), 'student', None)
            ]
            c.executemany('INSERT INTO users(name,email,password_hash,role,photo_path) VALUES(?,?,?,?,?)', users)

        c.execute('SELECT COUNT(*) FROM courses')
        if c.fetchone()[0] == 0:
            c.execute('SELECT id FROM users WHERE email=?', ('instructor@example.com',))
            instr_id = c.fetchone()[0]
            c.execute('''INSERT INTO courses(code,title,description,youtube_url,access_code,instructor_id)
                         VALUES(?,?,?,?,?,?)''',
                      ('PHY101', 'EFEK FOTOLISTRIK',
                       'Unit pembelajaran tentang efek fotolistrik.',
                       'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                       'PHY101-2025', instr_id))
            cid = c.lastrowid
            c.execute('SELECT id FROM users WHERE email=?', ('student@example.com',))
            stu_id = c.fetchone()[0]
            c.execute('INSERT OR IGNORE INTO enrollments(user_id,course_id,role) VALUES(?,?,?)', (instr_id, cid, 'instructor'))
            c.execute('INSERT OR IGNORE INTO enrollments(user_id,course_id,role) VALUES(?,?,?)', (stu_id, cid, 'student'))

        conn.commit()

# ---------- Deletion helpers ----------
def detach_module_items(module_id: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('UPDATE assignments SET module_id=NULL WHERE module_id=?', (module_id,))
        c.execute('UPDATE quizzes SET module_id=NULL WHERE module_id=?', (module_id,))
        conn.commit()

def delete_course(course_id: int):
    """Hapus kursus + seluruh data turunannya secara aman."""
    with get_conn() as conn:
        c = conn.cursor()

        # --- Quizzes: hapus attempts -> answers, questions -> choices, lalu quiz
        c.execute('SELECT id FROM quizzes WHERE course_id=?', (course_id,))
        quiz_ids = [r[0] for r in c.fetchall()]
        if quiz_ids:
            # attempts -> answers
            c.execute(f"SELECT id FROM quiz_attempts WHERE quiz_id IN ({','.join('?'*len(quiz_ids))})", quiz_ids)
            att_ids = [r[0] for r in c.fetchall()]
            if att_ids:
                c.execute(f"DELETE FROM quiz_answers WHERE attempt_id IN ({','.join('?'*len(att_ids))})", att_ids)
                c.execute(f"DELETE FROM quiz_attempts WHERE id IN ({','.join('?'*len(att_ids))})", att_ids)

            # questions -> choices
            c.execute(f"SELECT id FROM quiz_questions WHERE quiz_id IN ({','.join('?'*len(quiz_ids))})", quiz_ids)
            qn_ids = [r[0] for r in c.fetchall()]
            if qn_ids:
                c.execute(f"DELETE FROM quiz_choices WHERE question_id IN ({','.join('?'*len(qn_ids))})", qn_ids)
                c.execute(f"DELETE FROM quiz_questions WHERE id IN ({','.join('?'*len(qn_ids))})", qn_ids)

            # quizzes
            c.execute(f"DELETE FROM quizzes WHERE id IN ({','.join('?'*len(quiz_ids))})", quiz_ids)

        # --- Assignments
        c.execute('DELETE FROM assignments WHERE course_id=?', (course_id,))

        # --- Modules (and module images)
        c.execute('SELECT id FROM modules WHERE course_id=?', (course_id,))
        mod_ids = [r[0] for r in c.fetchall()]
        if mod_ids:
            c.execute(f"DELETE FROM module_images WHERE module_id IN ({','.join('?'*len(mod_ids))})", mod_ids)
        c.execute('DELETE FROM modules WHERE course_id=?', (course_id,))

        # --- Books / Flipbooks
        c.execute('DELETE FROM course_books WHERE course_id=?', (course_id,))

        # --- Announcements
        c.execute('DELETE FROM announcements WHERE course_id=?', (course_id,))

        # --- Attendance (logs dulu baru sessions)
        c.execute('SELECT id FROM attendance_sessions WHERE course_id=?', (course_id,))
        sess_ids = [r[0] for r in c.fetchall()]
        if sess_ids:
            c.execute(f"DELETE FROM attendance_logs WHERE session_id IN ({','.join('?'*len(sess_ids))})", sess_ids)
            c.execute(f"DELETE FROM attendance_sessions WHERE id IN ({','.join('?'*len(sess_ids))})", sess_ids)

        # --- Enrollments
        c.execute('DELETE FROM enrollments WHERE course_id=?', (course_id,))

        # --- Finally: Course
        c.execute('DELETE FROM courses WHERE id=?', (course_id,))
        conn.commit()

def delete_assignment(aid: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM assignments WHERE id=?', (aid,))
        conn.commit()

def delete_quiz(qid: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT id FROM quiz_attempts WHERE quiz_id=?', (qid,))
        atts = [r[0] for r in c.fetchall()]
        if atts:
            c.execute(f"DELETE FROM quiz_answers WHERE attempt_id IN ({','.join('?'*len(atts))})", atts)
            c.execute(f"DELETE FROM quiz_attempts WHERE id IN ({','.join('?'*len(atts))})", atts)
        c.execute('SELECT id FROM quiz_questions WHERE quiz_id=?', (qid,))
        qids = [r[0] for r in c.fetchall()]
        if qids:
            c.execute(f"DELETE FROM quiz_choices WHERE question_id IN ({','.join('?'*len(qids))})", qids)
            c.execute(f"DELETE FROM quiz_questions WHERE id IN ({','.join('?'*len(qids))})", qids)
        c.execute('DELETE FROM quizzes WHERE id=?', (qid,))
        conn.commit()

def delete_module(mid: int):
    with get_conn() as conn:
        c = conn.cursor()
        # delete module images
        c.execute('DELETE FROM module_images WHERE module_id=?', (mid,))
        detach_module_items(mid)
        c.execute('DELETE FROM modules WHERE id=?', (mid,))
        conn.commit()

def delete_announcement(anid: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM announcements WHERE id=?', (anid,))
        conn.commit()

def delete_book(bid: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM course_books WHERE id=?', (bid,))
        conn.commit()

def delete_question(qnid: int, quiz_id: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM quiz_answers WHERE question_id=?', (qnid,))
        c.execute('DELETE FROM quiz_choices WHERE question_id=?', (qnid,))
        c.execute('DELETE FROM quiz_questions WHERE id=?', (qnid,))
        c.execute('UPDATE quizzes SET total_points=(SELECT COALESCE(SUM(points),0) FROM quiz_questions WHERE quiz_id=?) WHERE id=?',
                  (quiz_id, quiz_id))
        conn.commit()

# ---------- Auth ----------
def login(email, pw):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT id,name,email,role,password_hash,photo_path FROM users WHERE email=?', (email,))
        r = c.fetchone()
        if r and r[4] == hash_pw(pw):
            return {'id': r[0], 'name': r[1], 'email': email, 'role': r[3], 'photo_path': r[5]}
    return None

# ---------- Landing Login ----------
def page_login():
    st.markdown('<div style="display:flex;justify-content:center;align-items:center;height:80vh;background:#2f4858">', unsafe_allow_html=True)
    st.markdown('<div style="background:#fff;padding:32px;border-radius:12px;width:520px;box-shadow:0 10px 30px rgba(0,0,0,.15)">', unsafe_allow_html=True)
    st.markdown('## Welcome to ThinkVerse LMS')

    # === Tab navigasi login / lupa password / register ===
    tabs = st.tabs(["🔑 Login", "🔁 Lupa Password", "🆕 Register"])

    # ---------------- LOGIN ----------------
    with tabs[0]:
        with st.form('login_form'):
            email = st.text_input('Email *')
            pw = st.text_input('Password *', type='password')
            ok = st.form_submit_button('Log In')
        if ok:
            user = login(email, pw)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error('Email atau password salah.')

    # ---------------- FORGOT PASSWORD ----------------
    with tabs[1]:
        st.write("Masukkan email akun kamu dan buat password baru.")
        with st.form("forgot_pw"):
            email_fp = st.text_input("Email akun *")
            new_pw = st.text_input("Password baru *", type='password')
            confirm_pw = st.text_input("Ulangi password baru *", type='password')
            ok_fp = st.form_submit_button("Reset Password")

        if ok_fp:
            if not email_fp.strip():
                st.error("Email wajib diisi.")
            elif new_pw != confirm_pw:
                st.error("Password baru tidak sama.")
            else:
                with get_conn() as conn:
                    c = conn.cursor()
                    c.execute("SELECT id FROM users WHERE email=?", (email_fp.strip(),))
                    user_row = c.fetchone()
                    if user_row:
                        uid = user_row[0]
                        c.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_pw(new_pw), uid))
                        conn.commit()
                        st.success("✅ Password berhasil direset! Silakan login kembali.")
                    else:
                        st.error("Email tidak ditemukan di sistem.")

    # ---------------- REGISTER ----------------
    with tabs[2]:
        with st.form('reg'):
            name = st.text_input('Full name')
            email_r = st.text_input('Email')
            pw_r = st.text_input('Password', type='password')
            role = st.selectbox('Role', ['student', 'instructor'])
            okr = st.form_submit_button('Register')
        if okr:
            try:
                with get_conn() as conn:
                    c = conn.cursor()
                    c.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',
                              (name, email_r, hash_pw(pw_r), role))
                    conn.commit()
                st.success('Akun berhasil dibuat! Silakan login di tab pertama.')
            except sqlite3.IntegrityError:
                st.error('Email sudah terdaftar.')

    st.markdown('</div></div>', unsafe_allow_html=True)

# ---------- Sidebar (dashboard mode) ----------
def sidebar_nav():
    st.sidebar.title('📚 ThinkVerse LMS')
    u = st.session_state.user
    if u:
        if u.get('photo_path') and os.path.exists(u['photo_path']):
            st.sidebar.image(u['photo_path'], width=72)  # tanpa caption
        st.sidebar.markdown(f"**{u['name']}**  \n_{u['role']}_")
        st.sidebar.success(f"Login sebagai {u['email']}")
        if st.sidebar.button('Logout'):
            st.session_state.user = None
            st.session_state.in_course = False
            st.session_state.current_course = None
            st.rerun()
    section = st.sidebar.radio('Navigasi', ['🏠 Beranda', '📘 Kursus', '👤 Akun'])
    return section

# ---------- Helper Dashboard ----------
def get_enrolled_courses_for_user(user_id: int):
    """Kursus yang diikuti user (student) atau diampu (instructor)."""
    with get_conn() as conn:
        c = conn.cursor()
        # Kursus diikuti (role student)
        c.execute('''SELECT c.id, c.code, c.title, u.name as instr_name, c.description
                     FROM enrollments e
                     JOIN courses c ON c.id = e.course_id
                     LEFT JOIN users u ON u.id = c.instructor_id
                     WHERE e.user_id=? AND e.role='student'
                     ORDER BY c.title''', (user_id,))
        enrolled = c.fetchall()

        # Kursus diampu (role instructor)
        c.execute('''SELECT c.id, c.code, c.title, u.name as instr_name, c.description
                     FROM courses c
                     LEFT JOIN users u ON u.id = c.instructor_id
                     WHERE c.instructor_id=? 
                     ORDER BY c.title''', (user_id,))
        teaching = c.fetchall()

    return enrolled, teaching

def render_course_tile(cid, code, title, instr, desc, button_key: str):
    """Tile kursus ala Canvas dengan key tombol unik untuk hindari duplikasi."""
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(f"{code} • Pengampu: {instr or '-'}")
        if desc:
            st.write(desc[:180] + ('…' if len(desc) > 180 else ''))
        ent = st.button('Masuk ke Kelas', key=button_key)
        if ent:
            st.session_state.current_course = cid
            st.session_state.in_course = True
            st.rerun()

# ---------- Dashboard pages ----------
def page_home():
    render_user_chip()
    st.title('Dashboard')
    st.write('Selamat datang di **ThinkVerse LMS**. Masuk ke **Kursus** untuk melihat/bergabung kelas.')
    st.info('Akun demo: instructor@example.com / teach123, student@example.com / learn123')

    u = st.session_state.user
    enrolled, teaching = get_enrolled_courses_for_user(u['id'])

    # Grid "Kursus Saya" ala Canvas
    st.subheader('📂 Kursus Saya')
    if not enrolled and u['role'] == 'student':
        st.caption('Belum ada kursus yang kamu ikuti. Buka tab **Kursus** untuk bergabung menggunakan kode akses.')
    else:
        cols_per_row = 3
        for i, (cid, code, title, instr, desc) in enumerate(enrolled):
            if i % cols_per_row == 0:
                cols = st.columns(cols_per_row)
            with cols[i % cols_per_row]:
                render_course_tile(
                    cid, code, title, instr, desc,
                    button_key=f"std_{cid}_{i}"  # unik per tile student
                )

    # Untuk instructor/admin, tampilkan juga kursus yang diampu
    if u['role'] in ['instructor', 'admin']:
        st.subheader('🧑‍🏫 Kursus yang Diampu')
        if not teaching:
            st.caption('Belum ada kursus yang kamu ampu.')
        else:
            cols_per_row = 3
            for j, (cid, code, title, instr, desc) in enumerate(teaching):
                if j % cols_per_row == 0:
                    cols = st.columns(cols_per_row)
                with cols[j % cols_per_row]:
                    render_course_tile(
                        cid, code, title, instr, desc,
                        button_key=f"tch_{cid}_{j}"  # unik per tile teaching
                    )

def page_account():
    st.header('👤 Kelola Akun')
    u = st.session_state.user

    colA, colB = st.columns([1,3])
    with colA:
        if u.get('photo_path') and os.path.exists(u['photo_path']):
            st.image(u['photo_path'], width=160)  # tanpa caption agar nama tak bertumpuk
            st.caption('Foto kamu')
        else:
            st.info('Belum ada foto.')
    with colB:
        up = st.file_uploader('Upload foto baru (jpg/png)', type=['jpg','jpeg','png'])
        remove = st.checkbox('Hapus foto profil')

    with st.form('upd_profile'):
        new_name = st.text_input('Nama', value=u['name'])
        new_email = st.text_input('Email', value=u['email'])
        submit = st.form_submit_button('Simpan Profil')
    if submit:
        new_photo_path = u.get('photo_path')
        if remove:
            if new_photo_path and os.path.exists(new_photo_path):
                try: os.remove(new_photo_path)
                except Exception: pass
            new_photo_path = None
        elif up is not None:
            fname = f"avatar_{u['id']}_{int(datetime.now().timestamp())}_{up.name}"
            fpath = os.path.join(UPLOAD_DIR, fname)
            with open(fpath, 'wb') as f: f.write(up.read())
            new_photo_path = fpath

        try:
            with get_conn() as conn:
                c = conn.cursor()
                c.execute('UPDATE users SET name=?, email=?, photo_path=? WHERE id=?',
                          (new_name.strip(), new_email.strip(), new_photo_path, u['id']))
                conn.commit()
            st.session_state.user['name'] = new_name.strip()
            st.session_state.user['email'] = new_email.strip()
            st.session_state.user['photo_path'] = new_photo_path
            st.success('Profil diperbarui.')
            st.rerun()
        except sqlite3.IntegrityError:
            st.error('Email sudah digunakan akun lain.')

    st.subheader('Ubah Password')
    with st.form('upd_pw'):
        cur = st.text_input('Password sekarang', type='password')
        npw = st.text_input('Password baru', type='password')
        npw2 = st.text_input('Ulangi password baru', type='password')
        submit2 = st.form_submit_button('Ganti Password')
    if submit2:
        if npw != npw2:
            st.error('Password baru tidak sama.')
        else:
            with get_conn() as conn:
                c = conn.cursor()
                c.execute('SELECT password_hash FROM users WHERE id=?', (u['id'],))
                old = c.fetchone()[0]
                if old != hash_pw(cur):
                    st.error('Password sekarang salah.')
                else:
                    c.execute('UPDATE users SET password_hash=? WHERE id=?', (hash_pw(npw), u['id']))
                    conn.commit()
                    st.success('Password berhasil diubah.')

def page_courses():
    render_user_chip()
    st.header('📘 Kursus')
    u = st.session_state.user

    # ====== Form BUAT KURSUS (hanya instructor/admin) ======
    if u['role'] in ['instructor', 'admin']:
        with st.expander('➕ Buat Kursus (Guru)', expanded=False):
            with st.form('new_course'):
                code = st.text_input('Kode (unik, mis. MATH101)')
                title = st.text_input('Judul Kursus')
                desc = st.text_area('Deskripsi')
                yt = st.text_input('YouTube URL (opsional)')
                access = st.text_input('Kode Akses untuk siswa (opsional)')
                ok_new = st.form_submit_button('Buat')
            if ok_new:
                if not code.strip() or not title.strip():
                    st.error('Kode dan Judul wajib diisi.')
                else:
                    try:
                        with get_conn() as conn:
                            c = conn.cursor()
                            c.execute('''INSERT INTO courses(code,title,description,youtube_url,access_code,instructor_id)
                                         VALUES(?,?,?,?,?,?)''',
                                      (code.strip(), title.strip(), desc, yt or None, access.strip() or None, u['id']))
                            conn.commit()
                        st.success('Kursus berhasil dibuat.')
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error('Kode kursus sudah dipakai. Gunakan kode lain.')

    # ====== Ambil semua kursus ======
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''SELECT c.id,c.code,c.title,c.description,c.youtube_url,u.name,c.instructor_id
                     FROM courses c LEFT JOIN users u ON c.instructor_id=u.id
                     ORDER BY c.title''')
        rows = c.fetchall()

    # ====== Daftar kursus ======
    for cid, code, title, desc, yt, instr, instr_id in rows:
        st.markdown(f"### {code} — {title}")
        st.caption(f"Pengampu: {instr or '-'}")
        if yt: st.video(yt)
        st.write(desc or '-')

        # status enroll user sekarang
        with get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT 1 FROM enrollments WHERE user_id=? AND course_id=?', (u['id'], cid))
            enrolled = c.fetchone() is not None

        cols = st.columns([2,2,2])
        # --- Kolom 1: Masuk / Gabung
        with cols[0]:
            if enrolled:
                if st.button('Masuk ke Kelas', key=f'ent_{cid}'):
                    st.session_state.current_course = cid
                    st.session_state.in_course = True
                    st.rerun()
            else:
                with st.form(f'join_{cid}'):
                    code_in = st.text_input('Kode Akses')
                    join = st.form_submit_button('Gabung')
                if join:
                    with get_conn() as conn:
                        c = conn.cursor()
                        c.execute('SELECT access_code FROM courses WHERE id=?', (cid,))
                        real = (c.fetchone() or [''])[0]
                        if (code_in or '').strip() == (real or '').strip():
                            c.execute('INSERT OR IGNORE INTO enrollments(user_id,course_id,role) VALUES(?,?,?)',
                                      (u['id'], cid, 'student'))
                            conn.commit()
                            st.session_state.current_course = cid
                            st.session_state.in_course = True
                            st.success('Berhasil bergabung!')
                            st.rerun()
                        else:
                            st.error('Kode akses salah.')

        # --- Kolom 2: Edit (Guru)
        with cols[1]:
            if u['role'] in ['instructor', 'admin'] and (u['id'] == instr_id or u['role']=='admin'):
                with st.expander('Edit Kursus (Guru)'):
                    with st.form(f'edit_{cid}'):
                        new_desc = st.text_area('Deskripsi', value=desc or '')
                        new_yt = st.text_input('YouTube URL', value=yt or '')
                        new_code = st.text_input('Kode Akses (opsional)', value='')
                        save = st.form_submit_button('Simpan')
                    if save:
                        with get_conn() as conn:
                            c = conn.cursor()
                            if new_code.strip():
                                c.execute('UPDATE courses SET description=?, youtube_url=?, access_code=? WHERE id=?',
                                          (new_desc, new_yt or None, new_code.strip(), cid))
                            else:
                                c.execute('UPDATE courses SET description=?, youtube_url=? WHERE id=?',
                                          (new_desc, new_yt or None, cid))
                            conn.commit()
                        st.success('Tersimpan.')

        # --- Kolom 3: HAPUS (Guru/Admin)
        with cols[2]:
            if u['role'] in ['instructor', 'admin'] and (u['id'] == instr_id or u['role']=='admin'):
                with st.expander('⚠️ Hapus Kursus'):
                    with st.form(f'del_course_{cid}'):
                        st.warning('Menghapus kursus akan menghapus semua data terkait (modules, assignments, quizzes, kehadiran, pengumuman, enrollments).')
                        cek = st.checkbox('Saya paham risikonya')
                        ketik = st.text_input(f"Ketik KODE kursus untuk konfirmasi: {code}")
                        go = st.form_submit_button('Hapus Permanen')
                    if go:
                        if not cek:
                            st.error('Centang konfirmasi dulu.')
                        elif ketik.strip() != code:
                            st.error('Kode konfirmasi tidak cocok.')
                        else:
                            delete_course(cid)
                            st.success('Kursus terhapus.')
                            st.rerun()

        st.divider()

# ---------- Course context ----------
def course_sidebar_nav(cid):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT code,title FROM courses WHERE id=?', (cid,))
        code, title = c.fetchone()

    st.sidebar.title(title)
    st.sidebar.caption(code)
    if st.sidebar.button('← Kembali ke Dashboard'):
        st.session_state.in_course = False
        st.session_state.current_course = None
        st.rerun()

    return st.sidebar.radio(
        'Menu Kelas',
        ['Home', 'Attendance', 'Books', 'Modules', 'Quizzes', 'Assignments', 'Announcements']
    )

# ----- Attendance / Absensi -----
def page_attendance(course_id):
    st.header('🗓️ Attendance / Absensi')
    u = st.session_state.user

    colL, colR = st.columns(2)
    if u['role'] in ['instructor', 'admin']:
        with colL:
            with st.form('new_session'):
                title = st.text_input('Judul Sesi (mis. Pertemuan 5)')
                sdate = st.date_input('Tanggal', value=datetime.now().date())
                code  = st.text_input('Kode Akses Absensi (opsional, biarkan kosong untuk auto)')
                open_now = st.checkbox('Buka Absensi Sekarang', value=True)
                ok = st.form_submit_button('Buat Sesi')
            if ok and title:
                if not code: code = str(int(datetime.now().timestamp()))[-6:]
                with get_conn() as conn:
                    c = conn.cursor()
                    c.execute('INSERT INTO attendance_sessions(course_id,title,session_date,access_code,is_open) VALUES(?,?,?,?,?)',
                              (course_id, title, sdate.isoformat(), code, 1 if open_now else 0))
                    conn.commit()
                create_announcement(course_id, 'Absensi baru dibuka', f'Sesi **{title}** tanggal {sdate.isoformat()} telah dibuka.', 1)
                st.success('Sesi absensi dibuat.'); st.rerun()
        with colR:
            st.caption('Instruktur dapat membuka/menutup sesi dan membagikan kode ke siswa.')

    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT id,title,session_date,access_code,is_open,created_at FROM attendance_sessions WHERE course_id=? ORDER BY id DESC', (course_id,))
        sess = c.fetchall()

    if not sess:
        st.info('Belum ada sesi absensi.')
        return

    for sid, title, sdate, code, is_open, created_at in sess:
        with st.expander(f"{title} • {sdate} {'🟢 OPEN' if is_open else '🔴 CLOSED'}"):
            st.caption(f"Kode: **{code or '-'}** • Dibuat: {created_at}")
            if u['role'] in ['instructor','admin']:
                c1, c2, c3 = st.columns([1,1,2])
                with c1:
                    if st.button('Buka', key=f'op_{sid}'):
                        with get_conn() as conn:
                            cur=conn.cursor(); cur.execute('UPDATE attendance_sessions SET is_open=1 WHERE id=?', (sid,)); conn.commit()
                        st.rerun()
                with c2:
                    if st.button('Tutup', key=f'cl_{sid}'):
                        with get_conn() as conn:
                            cur=conn.cursor(); cur.execute('UPDATE attendance_sessions SET is_open=0 WHERE id=?', (sid,)); conn.commit()
                        st.rerun()
                with c3:
                    with get_conn() as conn:
                        cur=conn.cursor()
                        cur.execute('''SELECT u.name, l.marked_at
                                       FROM attendance_logs l JOIN users u ON u.id=l.student_id
                                       WHERE l.session_id=? ORDER BY l.id ASC''', (sid,))
                        logs = cur.fetchall()
                    if logs:
                        import csv
                        from io import StringIO
                        buff = StringIO(); writer = csv.writer(buff)
                        writer.writerow(['Nama','Marked At'])
                        for nm, ts in logs: writer.writerow([nm, ts])
                        st.download_button('Unduh CSV Kehadiran', buff.getvalue().encode('utf-8'), file_name=f'absensi_{sid}.csv', mime='text/csv')
                    else:
                        st.caption('Belum ada kehadiran.')
            if u['role']=='student':
                if is_open:
                    with st.form(f'mark_{sid}'):
                        code_in = st.text_input('Masukkan kode absensi')
                        okm = st.form_submit_button('Saya Hadir')
                    if okm:
                        if (code_in or '').strip() != (code or '').strip():
                            st.error('Kode absensi salah.')
                        else:
                            with get_conn() as conn:
                                cur=conn.cursor()
                                try:
                                    cur.execute('INSERT INTO attendance_logs(session_id,student_id) VALUES(?,?)', (sid, u['id']))
                                    conn.commit()
                                    st.success('Kehadiran terekam!')
                                except sqlite3.IntegrityError:
                                    st.info('Kamu sudah menandai hadir untuk sesi ini.')
                else:
                    st.info('Sesi ini ditutup.')

# ----- Books / Flipbooks -----
def page_books(course_id):
    st.header('📖 Books & Bahan Ajar (Flipbook)')
    u = st.session_state.user
    if u['role'] in ['instructor','admin']:
        with st.form('new_book'):
            title = st.text_input('Judul Buku / Materi')
            embed = st.text_input('Embed URL (FlipHTML5/Anyflip/Issuu)')
            ok = st.form_submit_button('Tambah Buku')
        if ok and title and embed:
            with get_conn() as conn:
                c = conn.cursor()
                c.execute('INSERT INTO course_books(course_id,title,embed_url) VALUES(?,?,?)', (course_id, title, embed))
                conn.commit()
            create_announcement(course_id, 'Materi Flipbook baru', f'Bahan ajar **{title}** ditambahkan.', 1)
            st.success('Buku ditambahkan.'); st.rerun()

    with get_conn() as conn:
        c = conn.cursor(); c.execute('SELECT id,title,embed_url FROM course_books WHERE course_id=? ORDER BY id DESC', (course_id,))
        rows = c.fetchall()

    if not rows:
        st.info('Belum ada bahan ajar. Instruktur dapat menambahkan embed flipbook di atas.')

    for bid, title, url in rows:
        st.markdown(f"### {title}")
        st.components.v1.iframe(url, height=600)
        if u['role'] in ['instructor','admin']:
            with st.form(f'del_book_{bid}'):
                confirm = st.checkbox('Konfirmasi hapus')
                sub = st.form_submit_button('Hapus Buku')
            if sub and confirm:
                delete_book(bid)
                st.success('Buku dihapus.'); st.rerun()
        st.divider()

# ----- Modules (Materi + multi-image + edit) -----
def page_modules(cid):
    st.header('📦 Modules (Materi per Bagian)')
    u = st.session_state.user

    # ===== Tambah Topik =====
    if u['role'] in ['instructor', 'admin']:
        with st.form('new_mod'):
            title = st.text_input('Judul Topik')
            content = st.text_area('Pembahasan (Markdown + bisa embed gambar, daftar, dll.)')
            yt = st.text_input('YouTube URL (opsional)')
            img = st.file_uploader('Gambar (opsional)')
            order = st.number_input('Urutan', 0, 1000, 0)
            ok = st.form_submit_button('Tambah Topik')
        if ok:
            img_path = None
            if img is not None:
                img_path = os.path.join(UPLOAD_DIR, f"mod_{cid}_{datetime.now().timestamp()}_{img.name}")
                with open(img_path, 'wb') as f: f.write(img.read())
            with get_conn() as conn:
                c = conn.cursor()
                c.execute('INSERT INTO modules(course_id,title,content,youtube_url,image_path,order_index) VALUES(?,?,?,?,?,?)',
                          (cid, title, content, yt, img_path, order))
                conn.commit()
            create_announcement(cid, 'Topik baru ditambahkan', f'Topik **{title}** telah dipublish.', 1)
            st.success('Topik dibuat.')
            st.rerun()

    # ===== Tampilkan Topik =====
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT id,title,content,youtube_url,image_path,order_index FROM modules WHERE course_id=? ORDER BY order_index', (cid,))
        mods = c.fetchall()

    for mid, t, cont, yt, ip, ordr in mods:
        with st.expander(f"{ordr}. {t}", expanded=False):
            if yt: st.video(yt)
            if ip and os.path.exists(ip): st.image(ip)
            if cont: st.markdown(cont)

            if u['role'] in ['instructor','admin']:
                if st.button(f"✏️ Edit Topik Ini", key=f"edit_btn_{mid}"):
                    st.session_state[f"editing_mod_{mid}"] = not st.session_state.get(f"editing_mod_{mid}", False)

        # === Form Edit (di luar expander utama agar tidak nested) ===
        if st.session_state.get(f"editing_mod_{mid}", False):
            st.markdown(f"### ✏️ Edit Topik: {t}")
            with st.form(f'edit_mod_{mid}'):
                new_title = st.text_input('Judul Topik', value=t)
                new_content = st.text_area('Isi Penjelasan (Markdown)', value=cont or '')
                new_yt = st.text_input('YouTube URL (opsional)', value=yt or '')
                new_img = st.file_uploader('Upload gambar tambahan (opsional)')
                new_order = st.number_input('Urutan', 0, 1000, value=ordr)
                ok_edit = st.form_submit_button('Simpan Perubahan')

            if ok_edit:
                img_path = ip
                if new_img is not None:
                    img_path = os.path.join(UPLOAD_DIR, f"mod_{cid}_{datetime.now().timestamp()}_{new_img.name}")
                    with open(img_path, 'wb') as f: f.write(new_img.read())

                with get_conn() as conn:
                    c = conn.cursor()
                    c.execute('UPDATE modules SET title=?, content=?, youtube_url=?, image_path=?, order_index=? WHERE id=?',
                              (new_title, new_content, new_yt, img_path, new_order, mid))
                    conn.commit()

                st.success(f'Topik "{new_title}" berhasil diperbarui.')
                st.session_state[f"editing_mod_{mid}"] = False
                st.rerun()

        # === Tombol Hapus Topik ===
        if u['role'] in ['instructor','admin']:
            with st.form(f'del_mod_{mid}'):
                st.warning('Menghapus topik **tidak** menghapus tugas/kuis, hanya melepas keterkaitan.')
                cfm = st.checkbox('Saya paham dan ingin menghapus topik ini.')
                sub = st.form_submit_button('Hapus Topik')
            if sub and cfm:
                delete_module(mid)
                st.success('Topik dihapus. Tugas/Kuis terkait dilepas dari topik.')
                st.rerun()


# ----- Assignments (global) -----
def page_assignments(cid):
    st.header('📝 Assignments')
    u=st.session_state.user
    if u['role'] in ['instructor','admin']:
        with get_conn() as conn:
            c=conn.cursor()
            c.execute('SELECT id,title FROM modules WHERE course_id=? ORDER BY order_index',(cid,))
            mod_opts=[(None,'(Tanpa Topik)')]+[(mid,mt) for mid,mt in c.fetchall()]
        with st.form('new_asg'):
            title=st.text_input('Judul Tugas')
            desc=st.text_area('Deskripsi (Markdown/LaTeX $...$)')
            due_date = st.date_input('Batas Waktu (tanggal)', value=(datetime.now()+timedelta(days=7)).date())
            due_time = st.time_input('Jam', value=datetime.now().time().replace(microsecond=0))
            due = datetime.combine(due_date, due_time)
            pts=st.number_input('Poin',0,1000,100)
            yt=st.text_input('YouTube URL (opsional)')
            embed=st.text_input('Embed LKPD URL (Liveworksheets/Form/HTML/PDF, opsional)')
            mod = st.selectbox('Letakkan di Topik', mod_opts, format_func=lambda x: x[1])
            ok=st.form_submit_button('Tambah Tugas')
        if ok and title.strip():
            with get_conn() as conn:
                c=conn.cursor()
                c.execute('''INSERT INTO assignments(course_id,module_id,title,description,due_at,points,youtube_url,embed_url)
                             VALUES(?,?,?,?,?,?,?,?)''',(cid,mod[0],title.strip(),desc,due.isoformat(),int(pts),yt,embed))
                conn.commit()
            create_announcement(cid, 'Tugas baru', f'Tugas **{title.strip()}** dipublish.', 1)
            st.success('Tugas dibuat.')
    with get_conn() as conn:
        c=conn.cursor()
        c.execute('''SELECT a.id,a.title,a.description,a.due_at,a.points,a.youtube_url,a.embed_url,m.title
                     FROM assignments a LEFT JOIN modules m ON a.module_id=m.id
                     WHERE a.course_id=? ORDER BY a.id DESC''',(cid,))
        rows=c.fetchall()
    for aid,at,ad,due,pts,yt,embed,mtitle in rows:
        cols = st.columns([6,1])
        with cols[0]:
            st.markdown(f"### {at}  {'· 🧩 '+mtitle if mtitle else ''}")
            st.caption(f"Batas: {due} · Poin: {pts}")
            if yt: st.video(yt)
            # smarter embed: jika url mengarah ke pdf -> tampilkan pdf iframe
            if embed:
                if '.pdf' in (embed or '').lower():
                    try:
                        st.components.v1.iframe(embed, height=700)
                    except Exception:
                        st.write("Embed PDF gagal tampil. Coba link lain.")
                else:
                    st.components.v1.iframe(embed, height=600)
            if ad: st.markdown(ad)
        if u['role'] in ['instructor','admin']:
            with cols[1]:
                with st.form(f'del_asg_{aid}'):
                    cfm = st.checkbox('Konfirmasi')
                    sub = st.form_submit_button('Hapus')
                if sub and cfm:
                    delete_assignment(aid)
                    st.success('Assignment dihapus.'); st.rerun()
        st.divider()

# helper: grade short answer based on question id & given text
def grade_short_answer_for_question(question_id, answer_text):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT correct_text, correct_regex, case_sensitive, points FROM quiz_questions WHERE id=?', (question_id,))
        row = c.fetchone()
    if not row:
        return False, 0
    ct, cr, cs, pts = row
    ans = (answer_text or '')
    ok = None
    if ct:
        if cs:
            ok = (ans == ct)
        else:
            ok = (ans.lower() == (ct or '').lower())
    if ok is not True and cr:
        try:
            flags = 0 if cs else re.IGNORECASE
            ok = re.fullmatch(cr, ans, flags) is not None
        except re.error:
            ok = False
    return (True if ok else False), (pts or 0)

# ----- Quizzes (editor + embed + inline short answer submission) -----
def page_quizzes(cid):
    st.header('🧪 Quizzes')
    u = st.session_state.user

    if u['role'] in ['instructor', 'admin']:
        with get_conn() as conn:
            c=conn.cursor()
            c.execute('SELECT id,title FROM modules WHERE course_id=? ORDER BY order_index',(cid,))
            mod_opts=[(None,'(Tanpa Topik)')]+[(mid,mt) for mid,mt in c.fetchall()]
        with st.form('new_quiz'):
            qtitle = st.text_input('Judul Kuis')
            qdesc  = st.text_area('Deskripsi (opsional)')
            tlim   = st.number_input('Batas Waktu (menit)', 0, 300, 0)
            embed = st.text_input('Embed / Video URL (opsional)')
            mod = st.selectbox('Letakkan di Topik', mod_opts, format_func=lambda x: x[1])
            ok = st.form_submit_button('Buat Kuis')
        if ok and qtitle.strip():
            with get_conn() as conn:
                c = conn.cursor()
                c.execute('INSERT INTO quizzes(course_id,module_id,title,description,time_limit_minutes,embed_url) VALUES(?,?,?,?,?,?)',
                          (cid, mod[0], qtitle.strip(), qdesc, int(tlim), embed or None))
                conn.commit()
            create_announcement(cid, 'Quiz baru', f'Quiz **{qtitle.strip()}** dipublish.', 1)
            st.success('Kuis dibuat.'); st.rerun()

    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''SELECT q.id,q.title,q.description,q.time_limit_minutes,q.total_points,q.embed_url,m.title
                     FROM quizzes q LEFT JOIN modules m ON q.module_id=m.id
                     WHERE q.course_id=? ORDER BY q.id DESC''', (cid,))
        quizzes = c.fetchall()

    for qid, qt, qdesc, tlim, tpts, qembed, mtitle in quizzes:
        with st.expander(f"{qt} {'· 🧩 '+mtitle if mtitle else ''} — {tpts or 0} pts"):
            # show embed if present
            if qembed:
                # if looks like youtube link, show video widget; else iframe
                if 'youtube' in (qembed or '') or 'youtu.be' in (qembed or ''):
                    try:
                        st.video(qembed)
                    except Exception:
                        st.components.v1.iframe(qembed, height=600)
                else:
                    try:
                        st.components.v1.iframe(qembed, height=600)
                    except Exception:
                        st.write("Embed tidak dapat ditampilkan.")

            st.write(qdesc or '-')
            st.caption(f"Time limit: {tlim or '—'} menit")

            if u['role'] in ['instructor','admin']:
                st.markdown('**Tambah Soal**')
                with st.form(f'new_q_{qid}'):
                    qtype  = st.selectbox('Tipe', ['mcq','short'], key=f'qtype_{qid}')
                    prompt = st.text_area('Prompt (Markdown)')
                    latex  = st.text_input('LaTeX (opsional, tanpa $)')
                    img    = st.file_uploader('Gambar (opsional)', key=f'qi_{qid}')
                    pts    = st.number_input('Poin', 1, 100, 1, key=f'pts_{qid}')
                    if qtype == 'short':
                        st.caption('Opsi penilaian otomatis (pilih salah satu atau keduanya).')
                        correct_text   = st.text_input('Jawaban persis (teks) — kosongkan jika pakai regex', key=f'ct_{qid}')
                        correct_regex  = st.text_input('Regex benar (opsional)', key=f'cr_{qid}')
                        case_sensitive = st.checkbox('Case-sensitive (untuk jawaban persis)', value=False, key=f'cs_{qid}')
                    else:
                        correct_text = ''
                        correct_regex = ''
                        case_sensitive = False
                    ok_q = st.form_submit_button('Tambah Soal')

                if ok_q:
                    img_path = None
                    if img is not None:
                        img_path = os.path.join(UPLOAD_DIR, f"qq_{qid}_{datetime.now().timestamp()}_{img.name}")
                        with open(img_path, 'wb') as f: f.write(img.read())
                    with get_conn() as conn:
                        c = conn.cursor()
                        c.execute(
                            'INSERT INTO quiz_questions(quiz_id,qtype,prompt,latex,image_path,points,correct_text,correct_regex,case_sensitive) VALUES(?,?,?,?,?,?,?,?,?)',
                            (qid, qtype, prompt, latex, img_path, int(pts), correct_text or None, correct_regex or None, 1 if case_sensitive else 0)
                        )
                        qnid = c.lastrowid
                        if qtype == 'mcq':
                            for lbl in ['A','B','C','D']:
                                c.execute('INSERT INTO quiz_choices(question_id,label,is_correct) VALUES(?,?,0)', (qnid, lbl))
                        c.execute('UPDATE quizzes SET total_points=(SELECT COALESCE(SUM(points),0) FROM quiz_questions WHERE quiz_id=?) WHERE id=?', (qid, qid))
                        conn.commit()
                    st.success('Soal ditambahkan.'); st.rerun()

            with get_conn() as conn:
                c = conn.cursor()
                c.execute('SELECT id,qtype,prompt,latex,image_path,points FROM quiz_questions WHERE quiz_id=?', (qid,))
                qs = c.fetchall()

            for qnid, qt_, pr, ltx, ip, pp in qs:
                cols_top = st.columns([6,1])
                with cols_top[0]:
                    st.markdown(f"**[{qt_.upper()}]** {pr or ''}")
                if u['role'] in ['instructor','admin']:
                    with cols_top[1]:
                        with st.form(f'del_q_{qnid}'):
                            cfmq = st.checkbox('Konfirmasi')
                            subq = st.form_submit_button('Hapus Soal')
                        if subq and cfmq:
                            delete_question(qnid, qid)
                            st.success('Soal dihapus.'); st.rerun()

                if ltx:
                    try: st.latex(ltx)
                    except Exception: st.info('LaTeX tidak valid.')
                if ip and os.path.exists(ip): st.image(ip)
                st.caption(f"Poin: {pp}")

                # Instructor view for MCQ: manage choices (existing behavior)
                if qt_ == 'mcq' and u['role'] in ['instructor','admin']:
                    with get_conn() as conn:
                        c = conn.cursor()
                        c.execute('SELECT id,label,is_correct FROM quiz_choices WHERE question_id=?', (qnid,))
                        ch = c.fetchall()
                    with st.form(f'ch_{qnid}'):
                        cols = st.columns(max(1, len(ch)))
                        new_correct = None
                        edited = []
                        for i, (cid_, lbl, is_ok) in enumerate(ch):
                            with cols[i % len(cols)]:
                                new_lbl = st.text_input(f'Pilihan {lbl}', value=lbl, key=f'lbl_{cid_}')
                                to_del  = st.checkbox(f'Hapus {lbl}', key=f'del_{cid_}')
                                edited.append((cid_, new_lbl, to_del))
                                if st.checkbox(f'Benar {lbl}', value=bool(is_ok), key=f'ok_{cid_}'):
                                    new_correct = cid_
                        save = st.form_submit_button('Simpan Perubahan Pilihan')
                    if save:
                        with get_conn() as conn:
                            c = conn.cursor()
                            for cid_, nlbl, to_del in edited:
                                if to_del: c.execute('DELETE FROM quiz_choices WHERE id=?', (cid_,))
                                else: c.execute('UPDATE quiz_choices SET label=? WHERE id=?', (nlbl, cid_))
                            if new_correct:
                                c.execute('UPDATE quiz_choices SET is_correct=0 WHERE question_id=?', (qnid,))
                                c.execute('UPDATE quiz_choices SET is_correct=1 WHERE id=?', (new_correct,))
                            conn.commit()
                        st.success('Pilihan diperbarui.'); st.rerun()

                # STUDENT inline short-answer quick submit
                if qt_ == 'short' and u['role'] == 'student':
                    # show last submission if exists
                    with get_conn() as conn:
                        c = conn.cursor()
                        c.execute('''SELECT qa.text_answer, qa.is_correct, qa.attempt_id, a.submitted_at
                                     FROM quiz_answers qa JOIN quiz_attempts a ON qa.attempt_id=a.id
                                     WHERE qa.question_id=? AND a.student_id=? ORDER BY a.id DESC LIMIT 1''', (qnid, u['id']))
                        prev = c.fetchone()
                    if prev:
                        prev_txt, prev_ok, prev_attid, prev_ts = prev
                        st.caption(f"Terakhir dikirim: '{prev_txt}' — {'Benar' if prev_ok==1 else 'Salah' if prev_ok==0 else 'Belum dinilai'} • {prev_ts}")
                    with st.form(f'inline_short_{qnid}'):
                        ans = st.text_input('Kirim jawaban singkat', key=f'ins_{qnid}')
                        submit_short = st.form_submit_button('Kirim Jawaban')
                    if submit_short:
                        # grade answer
                        is_correct, pts = grade_short_answer_for_question(qnid, ans)
                        # create attempt & answer
                        with get_conn() as conn:
                            c = conn.cursor()
                            now = datetime.now().isoformat()
                            c.execute('INSERT INTO quiz_attempts(quiz_id,student_id,started_at,submitted_at,score) VALUES(?,?,?,?,?)',
                                      (qid, u['id'], now, now, 0))
                            att_id = c.lastrowid
                            c.execute('INSERT INTO quiz_answers(attempt_id,question_id,choice_id,text_answer,is_correct) VALUES(?,?,?,?,?)',
                                      (att_id, qnid, None, ans, 1 if is_correct else 0))
                            # update attempt score
                            c.execute('UPDATE quiz_attempts SET score=? WHERE id=?', (pts if is_correct else 0, att_id))
                            conn.commit()
                        st.success(f'Jawaban terkirim. {"Benar" if is_correct else "Salah"} — mendapat {pts if is_correct else 0} poin.')

            if u['role'] in ['instructor','admin']:
                with st.form(f'del_quiz_{qid}'):
                    cfm = st.checkbox('Hapus kuis ini **beserta** semua soal & data hasilnya.')
                    sub = st.form_submit_button('Hapus Kuis')
                if sub and cfm:
                    delete_quiz(qid)
                    st.success('Kuis dan seluruh datanya dihapus.'); st.rerun()

            if u['role'] == 'student':
                with get_conn() as conn:
                    c = conn.cursor()
                    c.execute('SELECT score,submitted_at FROM quiz_attempts WHERE quiz_id=? AND student_id=? ORDER BY id DESC', (qid, u['id']))
                    att = c.fetchone()
                if att:
                    st.info(f"Percobaan terakhir: skor {att[0]} • {att[1]}")
                if st.button('Kerjakan Kuis (Full)', key=f'do_{qid}'):
                    do_quiz(cid, qid)

            if u['role'] in ['instructor','admin']:
                st.markdown('---')
                st.markdown('**Hasil Kuis (Dashboard Guru)**')
                with get_conn() as conn:
                    c = conn.cursor()
                    c.execute('''SELECT qa.id, u.name, qa.submitted_at, qa.score
                                 FROM quiz_attempts qa JOIN users u ON u.id=qa.student_id
                                 WHERE qa.quiz_id=? ORDER BY qa.id DESC''', (qid,))
                    attempts = c.fetchall()
                    c.execute('SELECT COALESCE(SUM(points),0), COUNT(*) FROM quiz_questions WHERE quiz_id=?', (qid,))
                    tp, nqs = c.fetchone()
                if attempts:
                    buf = io.StringIO()
                    buf.write('Nama,Submitted At,Score,Total Points\n')
                    for _id, nm, ts, sc in attempts:
                        buf.write(f'{nm},{ts},{sc},{tp}\n')
                    st.download_button('Unduh Rekap CSV', data=buf.getvalue().encode('utf-8'),
                                       file_name=f'rekap_quiz_{qid}.csv', mime='text/csv')
                    for _id, nm, ts, sc in attempts:
                        st.write(f"• {nm} — {ts} — skor: {sc}/{tp}")
                else:
                    st.caption('Belum ada percobaan kuis.')

# --- take quiz helper ---
def do_quiz(cid, qid):
    st.session_state.in_quiz = {'course': cid, 'quiz': qid}
    st.rerun()

def page_take_quiz():
    info = st.session_state.get('in_quiz')
    if not info: return
    cid, qid = info['course'], info['quiz']

    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT title FROM quizzes WHERE id=?', (qid,))
        qtitle = c.fetchone()[0]
        c.execute('SELECT id,qtype,prompt,latex,image_path,points FROM quiz_questions WHERE quiz_id=?', (qid,))
        qs = c.fetchall()

    st.header(f'Kerjakan Kuis — {qtitle}')
    answers = {}
    correct_count = 0
    total_points = 0

    for qnid, qt, pr, ltx, ip, pts in qs:
        total_points += pts
        st.markdown(f"**{pr or ''}**")
        if ltx:
            try: st.latex(ltx)
            except Exception: st.info('LaTeX tidak valid.')
        if ip and os.path.exists(ip): st.image(ip)

        if qt == 'mcq':
            with get_conn() as conn:
                c = conn.cursor()
                c.execute('SELECT id,label FROM quiz_choices WHERE question_id=?', (qnid,))
                opts = c.fetchall()
            choice = st.radio('Pilih:', options=[(oid, lbl) for oid, lbl in opts],
                              format_func=lambda x: x[1], key=f'a_{qnid}')
            answers[qnid] = {'type':'mcq', 'choice_id': choice[0], 'text': None, 'points': pts}
        else:
            txt = st.text_input('Jawaban singkat', key=f'a_{qnid}')
            answers[qnid] = {'type':'short', 'choice_id': None, 'text': txt, 'points': pts}

        st.caption(f"Poin: {pts}")
        st.divider()

    if st.button('Kumpulkan Kuis'):
        score = 0
        with get_conn() as conn:
            c = conn.cursor()
            c.execute('INSERT INTO quiz_attempts(quiz_id,student_id,started_at,submitted_at,score) VALUES(?,?,?,?,?)',
                      (qid, st.session_state.user['id'], datetime.now().isoformat(), datetime.now().isoformat(), 0))
            att_id = c.lastrowid

            for qnid, meta in answers.items():
                correct = None
                if meta['type'] == 'mcq':
                    c.execute('SELECT is_correct FROM quiz_choices WHERE id=?', (meta['choice_id'],))
                    row = c.fetchone()
                    is_ok = (row and row[0] == 1)
                    correct = 1 if is_ok else 0
                    if correct == 1:
                        score += meta['points']
                        correct_count += 1
                else:
                    c.execute('SELECT correct_text, correct_regex, case_sensitive FROM quiz_questions WHERE id=?', (qnid,))
                    ct, cr, cs = c.fetchone()
                    ans = (meta['text'] or '')
                    ok = None
                    if ct:
                        ok = (ans == ct) if cs else (ans.lower() == (ct or '').lower())
                    if ok is not True and cr:
                        flags = 0 if cs else re.IGNORECASE
                        try:
                            ok = re.fullmatch(cr, ans, flags) is not None
                        except re.error:
                            ok = False
                    correct = 1 if ok else (0 if ok is not None else None)
                    if correct == 1:
                        score += meta['points']
                        correct_count += 1

                c.execute('INSERT INTO quiz_answers(attempt_id,question_id,choice_id,text_answer,is_correct) VALUES(?,?,?,?,?)',
                          (att_id, qnid, meta['choice_id'], meta['text'], correct))

            c.execute('UPDATE quiz_attempts SET score=? WHERE id=?', (score, att_id))
            conn.commit()

        st.success(f'Kuis dikumpulkan. Skor: {score}/{total_points} • Benar: {correct_count} dari {len(qs)} soal')
        del st.session_state['in_quiz']

# ----- Announcements -----
def page_announcements(cid):
    st.header('📣 Announcements')
    u = st.session_state.user
    if u['role'] in ['instructor','admin']:
        with st.form('new_announce'):
            title = st.text_input('Judul')
            msg = st.text_area('Pesan (Markdown diperbolehkan)')
            ok = st.form_submit_button('Kirim Pengumuman')
        if ok and title.strip():
            create_announcement(cid, title.strip(), msg or '', 0)
            st.success('Pengumuman dikirim.'); st.rerun()
    with get_conn() as conn:
        c=conn.cursor()
        c.execute('SELECT id,title,message,is_system,posted_at FROM announcements WHERE course_id=? ORDER BY id DESC',(cid,))
        rows=c.fetchall()
    for anid,t,m,is_sys,ts in rows:
        badge = '🔔 Sistem' if is_sys==1 else '📣 Guru'
        cols = st.columns([6,1])
        with cols[0]:
            with st.expander(f"{badge} • {t} • {ts}"):
                st.markdown(m or '-')
        if u['role'] in ['instructor','admin']:
            with cols[1]:
                with st.form(f'del_ann_{anid}'):
                    cfm = st.checkbox('Konfirmasi')
                    sub = st.form_submit_button('Hapus')
                if sub and cfm:
                    delete_announcement(anid)
                    st.success('Pengumuman dihapus.'); st.rerun()

# ---------- App ----------
def main():
    # HAPUS set_page_config dari sini (sudah di atas file)
    init_db()
    seed_demo()

    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'in_course' not in st.session_state:
        st.session_state.in_course = False

    if not st.session_state.user:
        page_login()
        return

    # in-quiz view
    if st.session_state.get('in_quiz'):
        page_take_quiz()
        return

    # course view
    if st.session_state.in_course and st.session_state.get('current_course'):
        cid = st.session_state.current_course
        menu = course_sidebar_nav(cid)

        if menu == 'Home':
            with get_conn() as conn:
                c=conn.cursor(); c.execute('SELECT title,description,youtube_url FROM courses WHERE id=?', (cid,))
                t,d,y=c.fetchone()
            st.header(f"{t} — Home")
            render_user_chip()
            if y: st.video(y)
            st.markdown(d or '-')

        elif menu == 'Attendance':
            page_attendance(cid)

        elif menu == 'Books':
            page_books(cid)

        elif menu == 'Modules':
            page_modules(cid)

        elif menu == 'Quizzes':
            page_quizzes(cid)

        elif menu == 'Assignments':
            page_assignments(cid)

        elif menu == 'Announcements':
            page_announcements(cid)

        return

    # dashboard
    sec = sidebar_nav()
    if sec == '🏠 Beranda':
        page_home()
    elif sec == '📘 Kursus':
        page_courses()
    elif sec == '👤 Akun':
        page_account()

if __name__ == '__main__':
    main()


