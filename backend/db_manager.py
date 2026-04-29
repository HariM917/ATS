import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'hiring_system.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. HR Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS hr_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    
    # 2. Candidate Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    
    # 3. Settings Portal Table (User Profiles)
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            email TEXT PRIMARY KEY,
            username TEXT,
            role TEXT,
            first_name TEXT,
            last_name TEXT,
            bio TEXT,
            phone TEXT,
            street TEXT,
            city TEXT,
            state TEXT
        )
    ''')

    # 4. Jobs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hr_email TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            skills TEXT,
            experience_required INTEGER,
            location TEXT,
            job_type TEXT,
            salary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Applications Table (Candidates applying to HR Jobs)
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            candidate_email TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            resume_path TEXT,
            score REAL,
            status TEXT DEFAULT 'Pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_id, candidate_email)
        )
    ''')

    # 6. Chat History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            user_text TEXT NOT NULL,
            ai_text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# --- Authentication Methods ---

def verify_hr_login(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT email FROM hr_users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    return user['email'] if user else None

def register_hr(username, password, email):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO hr_users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_candidate(email):
    conn = get_db_connection()
    user = conn.execute('SELECT username, email FROM candidates WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def register_candidate(username, email):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO candidates (username, email) VALUES (?, ?)', (username, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# --- Profile Management Methods ---

def get_user_profile(email):
    conn = get_db_connection()
    profile = conn.execute('SELECT * FROM user_profiles WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(profile) if profile else None

def update_user_profile(email, data):
    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT email FROM user_profiles WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.execute('''
                UPDATE user_profiles 
                SET first_name=?, last_name=?, bio=?, phone=?, street=?, city=?, state=?
                WHERE email=?
            ''', (
                data.get('first_name', ''), data.get('last_name', ''), 
                data.get('bio', ''), data.get('phone', ''), 
                data.get('street', ''), data.get('city', ''), 
                data.get('state', ''), email
            ))
        else:
            conn.execute('''
                INSERT INTO user_profiles (email, username, role, first_name, last_name, bio, phone, street, city, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email, data.get('username', ''), data.get('role', ''),
                data.get('first_name', ''), data.get('last_name', ''), 
                data.get('bio', ''), data.get('phone', ''), 
                data.get('street', ''), data.get('city', ''), data.get('state', '')
            ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Profile Update Error: {e}")
        return False
    finally:
        conn.close()

# --- Job Management Methods ---

def add_job(hr_email, title, description, location, job_type, salary, skills=None, experience_required=0):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO jobs (hr_email, title, description, location, job_type, salary, skills, experience_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (hr_email, title, description, location, job_type, salary, skills, experience_required))
        conn.commit()
        return True
    except Exception as e:
        print(f"Add Job Error: {e}")
        return False
    finally:
        conn.close()

def get_hr_jobs(hr_email):
    conn = get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs WHERE hr_email = ? ORDER BY created_at DESC', (hr_email,)).fetchall()
    conn.close()
    return [dict(job) for job in jobs]

def delete_job(job_id, hr_email):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM jobs WHERE id = ? AND hr_email = ?', (job_id, hr_email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Delete Job Error: {e}")
        return False
    finally:
        conn.close()

# --- Application Methods (NEW) ---

def apply_for_job(job_id, candidate_email, candidate_name, resume_path=None, score=0.0):
    conn = get_db_connection()
    try:
        # Check to ensure the candidate hasn't already applied
        existing = conn.execute('SELECT id FROM applications WHERE job_id = ? AND candidate_email = ?', (job_id, candidate_email)).fetchone()
        if existing: 
            return "exists"
            
        conn.execute('''
            INSERT INTO applications (job_id, candidate_email, candidate_name, resume_path, score) 
            VALUES (?, ?, ?, ?, ?)
        ''', (job_id, candidate_email, candidate_name, resume_path, score))
        conn.commit()
        return True
    except Exception as e:
        print(f"Apply Error: {e}")
        return False
    finally:
        conn.close()

def get_job_applications(job_id):
    conn = get_db_connection()
    apps = conn.execute('''
        SELECT id, candidate_name, candidate_email, applied_at, resume_path, score, status
        FROM applications 
        WHERE job_id = ? 
        ORDER BY score DESC
    ''', (job_id,)).fetchall()
    conn.close()
    return [dict(a) for a in apps]

def update_application_status(app_id, status):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE applications SET status = ? WHERE id = ?', (status, app_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Status Update Error: {e}")
        return False
    finally:
        conn.close()



# --- Chat History Methods ---

def save_chat_message(email, role, user_text, ai_text):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO chat_history (email, role, user_text, ai_text)
            VALUES (?, ?, ?, ?)
        ''', (email, role, user_text, ai_text))
        conn.commit()
        return True
    except Exception as e:
        print(f"Save Chat Error: {e}")
        return False
    finally:
        conn.close()

def get_chat_history(email, limit=10):
    conn = get_db_connection()
    try:
        history = conn.execute('''
            SELECT user_text, ai_text FROM chat_history 
            WHERE email = ? 
            ORDER BY timestamp DESC LIMIT ?
        ''', (email, limit)).fetchall()
        # Return in chronological order
        return [{"user": row['user_text'], "ai": row['ai_text']} for row in reversed(history)]
    except Exception as e:
        print(f"Get Chat Error: {e}")
        return []
    finally:
        conn.close()