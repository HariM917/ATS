import sqlite3
import os
import urllib.parse as urlparse
import logging
import traceback

# For Postgres support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'hiring_system.db')
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    """Elite Database Connector: Supports both SQLite and PostgreSQL (for Vercel/Supabase)."""
    if DATABASE_URL and HAS_POSTGRES:
        try:
            # PostgreSQL Connection (Supabase)
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            return conn
        except Exception as e:
            logging.error(f"Postgres Connection Failed, falling back to SQLite: {e}")
            
    # SQLite Connection (Local/Render)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_cursor(conn):
    """Returns a cursor that handles both SQLite and Postgres dictionary results."""
    if hasattr(conn, 'cursor_factory'): # Postgres
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()

def sql_fix(query):
    """Fixes SQL syntax differences between SQLite (?) and Postgres (%s)."""
    if DATABASE_URL and HAS_POSTGRES:
        return query.replace('?', '%s').replace('AUTOINCREMENT', '') # Postgres uses SERIAL, handle it in CREATE
    return query

def init_db():
    conn = get_db_connection()
    c = get_cursor(conn)
    
    # Use SERIAL for Postgres, AUTOINCREMENT for SQLite
    pk_type = "SERIAL PRIMARY KEY" if (DATABASE_URL and HAS_POSTGRES) else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
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
        print(f"DB Init Error: {e}")
        traceback.print_exc()
    finally:
        conn.close()

# --- Authentication Methods ---

def verify_hr_login(username, password):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = sql_fix("SELECT * FROM hr_users WHERE username = ? AND password = ?")
    c.execute(query, (username, password))
    user = c.fetchone()
    conn.close()
    return user

def register_hr(username, password, email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = sql_fix("INSERT INTO hr_users (username, password, email) VALUES (?, ?, ?)")
        c.execute(query, (username, password, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Registration Error: {e}")
        return False
    finally:
        conn.close()

def register_candidate(username, email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = sql_fix("INSERT OR IGNORE INTO candidates (username, email) VALUES (?, ?)")
        # Postgres doesn't support INSERT OR IGNORE the same way, use ON CONFLICT
        if DATABASE_URL and HAS_POSTGRES:
            query = "INSERT INTO candidates (username, email) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING"
        c.execute(query, (username, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Candidate Registration Error: {e}")
        return False
    finally:
        conn.close()

# --- Job Management ---

def create_job(hr_email, title, desc, skills, exp, location, job_type, salary):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = sql_fix("INSERT INTO jobs (hr_email, title, description, skills, experience_required, location, job_type, salary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        c.execute(query, (hr_email, title, desc, skills, exp, location, job_type, salary))
        conn.commit()
        return True
    except Exception as e:
        print(f"Job Creation Error: {e}")
        return False
    finally:
        conn.close()

def get_jobs_by_hr(hr_email):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = sql_fix("SELECT * FROM jobs WHERE hr_email = ? ORDER BY created_at DESC")
    c.execute(query, (hr_email,))
    jobs = c.fetchall()
    conn.close()
    return jobs

def get_all_jobs():
    conn = get_db_connection()
    c = get_cursor(conn)
    c.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs = c.fetchall()
    conn.close()
    return jobs

# --- Application Management ---

def apply_for_job(job_id, candidate_email, candidate_name, resume_path, score):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = sql_fix("INSERT INTO applications (job_id, candidate_email, candidate_name, resume_path, score) VALUES (?, ?, ?, ?, ?)")
        # Handle unique constraint for Postgres
        if DATABASE_URL and HAS_POSTGRES:
            query = "INSERT INTO applications (job_id, candidate_email, candidate_name, resume_path, score) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (job_id, candidate_email) DO UPDATE SET score = EXCLUDED.score, applied_at = CURRENT_TIMESTAMP"
        c.execute(query, (job_id, candidate_email, candidate_name, resume_path, score))
        conn.commit()
        return True
    except Exception as e:
        print(f"Application Error: {e}")
        return False
    finally:
        conn.close()

def get_applications_for_job(job_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = sql_fix("SELECT * FROM applications WHERE job_id = ? ORDER BY score DESC")
    c.execute(query, (job_id,))
    apps = c.fetchall()
    conn.close()
    return apps

# --- User Profiles ---

def update_user_profile(email, username, role, first_name, last_name, bio, phone, street, city, state):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        # Postgres ON CONFLICT syntax
        if DATABASE_URL and HAS_POSTGRES:
            query = """
                INSERT INTO user_profiles (email, username, role, first_name, last_name, bio, phone, street, city, state)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                username = EXCLUDED.username, role = EXCLUDED.role, first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name, bio = EXCLUDED.bio, phone = EXCLUDED.phone,
                street = EXCLUDED.street, city = EXCLUDED.city, state = EXCLUDED.state
            """
        else:
            query = "INSERT OR REPLACE INTO user_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        
        c.execute(sql_fix(query), (email, username, role, first_name, last_name, bio, phone, street, city, state))
        conn.commit()
        return True
    except Exception as e:
        print(f"Profile Update Error: {e}")
        return False
    finally:
        conn.close()

def get_user_profile(email):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = sql_fix("SELECT * FROM user_profiles WHERE email = ?")
    c.execute(query, (email,))
    profile = c.fetchone()
    conn.close()
    return profile

# --- Chat History ---

def add_chat_message(email, role, user_text, ai_text):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = sql_fix("INSERT INTO chat_history (email, role, user_text, ai_text) VALUES (?, ?, ?, ?)")
        c.execute(query, (email, role, user_text, ai_text))
        conn.commit()
    except Exception as e:
        print(f"Chat History Error: {e}")
    finally:
        conn.close()

def get_chat_history(email):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = sql_fix("SELECT role, user_text, ai_text, timestamp FROM chat_history WHERE email = ? ORDER BY timestamp ASC")
    c.execute(query, (email,))
    history = c.fetchall()
    conn.close()
    # Format for frontend
    formatted = []
    for row in history:
        formatted.append({"role": "user", "content": row["user_text"]})
        formatted.append({"role": "assistant", "content": row["ai_text"]})
    return formatted

def clear_all_data():
    """DANGEROUS: Wipes tables. Used for admin reset."""
    conn = get_db_connection()
    c = get_cursor(conn)
    tables = ["applications", "jobs", "hr_users", "candidates", "user_profiles", "chat_history"]
    for table in tables:
        c.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()