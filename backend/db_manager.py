import sqlite3
import os
import logging
import traceback
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'hiring_system.db')

def get_db_connection():
    """Production Database Connector with WAL mode for concurrency."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def get_cursor(conn):
    """Returns a standard SQLite cursor."""
    return conn.cursor()

def init_db():
    conn = get_db_connection()
    c = get_cursor(conn)
    
    pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    try:
        # 1. HR Users Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS hr_users (
                id {pk_type},
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        ''')
        
        # 2. Candidate Users Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS candidates (
                id {pk_type},
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
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS jobs (
                id {pk_type},
                hr_email TEXT NOT NULL,
                company_name TEXT,
                branch TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                required_skills TEXT,
                experience_required INTEGER,
                location TEXT,
                job_type TEXT,
                salary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 5. Applications Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS applications (
                id {pk_type},
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
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS chat_history (
                id {pk_type},
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                user_text TEXT NOT NULL,
                ai_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
    except Exception as e:
        logging.error(f"DB Init Error: {e}")
        traceback.print_exc()
    finally:
        conn.close()

# --- Authentication Methods ---

def verify_hr_login(username, password):
    """Verifies HR login credentials. Returns email string on success, None on failure."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "SELECT email, password FROM hr_users WHERE username = ?"
        c.execute(query, (username,))
        user = c.fetchone()
        if user:
            stored_pw = user['password']
            # Support both hashed and legacy plaintext passwords
            if stored_pw.startswith('pbkdf2:') or stored_pw.startswith('scrypt:'):
                if check_password_hash(stored_pw, password):
                    return user['email']
            else:
                # Legacy plaintext comparison (for existing users)
                if stored_pw == password:
                    # Auto-upgrade to hashed password
                    try:
                        c.execute("UPDATE hr_users SET password = ? WHERE username = ?", 
                                  (generate_password_hash(password), username))
                        conn.commit()
                        logging.info(f"Auto-upgraded password hash for user: {username}")
                    except Exception:
                        pass
                    return user['email']
        return None
    finally:
        conn.close()

def register_hr(username, password, email):
    """Registers a new HR user with hashed password."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        hashed_password = generate_password_hash(password)
        query = "INSERT INTO hr_users (username, password, email) VALUES (?, ?, ?)"
        c.execute(query, (username, hashed_password, email))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Registration Error: {e}")
        return False
    finally:
        conn.close()

def register_candidate(username, email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "INSERT OR IGNORE INTO candidates (username, email) VALUES (?, ?)"
        c.execute(query, (username, email))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Candidate Registration Error: {e}")
        return False
    finally:
        conn.close()

def login_candidate(email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "SELECT * FROM candidates WHERE email = ?"
        c.execute(query, (email,))
        user = c.fetchone()
        return user
    finally:
        conn.close()

# --- Job Management ---

def create_job(hr_email, company_name, branch, title, desc, req_skills, exp, location, job_type, salary):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        logging.info(f"[DB] Creating job: {title} for {company_name}")
        query = """
            INSERT INTO jobs 
            (hr_email, company_name, branch, title, description, required_skills, experience_required, location, job_type, salary) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        c.execute(query, (hr_email, company_name, branch, title, desc, req_skills, exp, location, job_type, salary))
        conn.commit()
        logging.info(f"[DB] Job '{title}' saved successfully.")
        return True
    except Exception as e:
        logging.error(f"[DB] Job Creation Error: {e}")
        traceback.print_exc()
        return False
    finally:
        conn.close()

def get_jobs_by_hr(hr_email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "SELECT * FROM jobs WHERE hr_email = ? ORDER BY created_at DESC"
        c.execute(query, (hr_email,))
        jobs = c.fetchall()
        return jobs
    finally:
        conn.close()

def get_all_jobs():
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        jobs = c.fetchall()
        return jobs
    finally:
        conn.close()

def delete_job(job_id, hr_email):
    """Deletes a job posting (only if owned by the requesting HR user)."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        # First delete associated applications
        c.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
        # Then delete the job itself (with ownership check)
        c.execute("DELETE FROM jobs WHERE id = ? AND hr_email = ?", (job_id, hr_email))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logging.error(f"[DB] Job Delete Error: {e}")
        return False
    finally:
        conn.close()

# --- Application Management ---

def apply_for_job(job_id, candidate_email, candidate_name, resume_path, score):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "INSERT OR REPLACE INTO applications (job_id, candidate_email, candidate_name, resume_path, score) VALUES (?, ?, ?, ?, ?)"
        c.execute(query, (job_id, candidate_email, candidate_name, resume_path, score))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Application Error: {e}")
        return False
    finally:
        conn.close()

def get_applications_for_job(job_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "SELECT * FROM applications WHERE job_id = ? ORDER BY score DESC"
        c.execute(query, (job_id,))
        apps = c.fetchall()
        return apps
    finally:
        conn.close()

def update_application_status(app_id, new_status):
    """Updates the status of an application (Shortlisted/Rejected/Pending/Hold)."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, app_id))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logging.error(f"[DB] Status Update Error: {e}")
        return False
    finally:
        conn.close()

# --- User Profiles ---

def update_user_profile(email, username, role, first_name, last_name, bio, phone, street, city, state):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "INSERT OR REPLACE INTO user_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        c.execute(query, (email, username, role, first_name, last_name, bio, phone, street, city, state))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Profile Update Error: {e}")
        return False
    finally:
        conn.close()

def get_user_profile(email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "SELECT * FROM user_profiles WHERE email = ?"
        c.execute(query, (email,))
        profile = c.fetchone()
        return profile
    finally:
        conn.close()

# --- Chat History ---

def add_chat_message(email, role, user_text, ai_text):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = "INSERT INTO chat_history (email, role, user_text, ai_text) VALUES (?, ?, ?, ?)"
        c.execute(query, (email, role, user_text, ai_text))
        conn.commit()
    except Exception as e:
        logging.error(f"Chat History Error: {e}")
    finally:
        conn.close()

def save_chat_message(email, role, user_text, ai_text):
    return add_chat_message(email, role, user_text, ai_text)

def get_chat_history(email, limit=None):
    """Returns chat history formatted for the frontend: [{user: ..., ai: ...}]"""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        if limit is not None:
            query = "SELECT user_text, ai_text, timestamp FROM (SELECT user_text, ai_text, timestamp FROM chat_history WHERE email = ? ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC"
            c.execute(query, (email, limit))
        else:
            query = "SELECT user_text, ai_text, timestamp FROM chat_history WHERE email = ? ORDER BY timestamp ASC"
            c.execute(query, (email,))
        history = c.fetchall()
        # Format matching frontend expectation: {user, ai} pairs
        formatted = []
        for row in history:
            formatted.append({
                "user": row["user_text"],
                "ai": row["ai_text"]
            })
        return formatted
    finally:
        conn.close()

def clear_all_data():
    """DANGEROUS: Wipes tables. Used for admin reset."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        tables = ["applications", "jobs", "hr_users", "candidates", "user_profiles", "chat_history"]
        for table in tables:
            c.execute(f"DELETE FROM {table}")
        conn.commit()
    finally:
        conn.close()