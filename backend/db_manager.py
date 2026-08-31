"""
FlowATS Database Manager — Production v3.0
Unified users table with RBAC, proper foreign keys, and migration from v2 to v3.
"""
import sqlite3
import os
import logging
import traceback
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'hiring_system.db')

SCHEMA_VERSION = 3

# ============================================
# Connection
# ============================================

def get_db_connection():
    """Production Database Connector with WAL mode and foreign keys."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_cursor(conn):
    """Returns a standard SQLite cursor."""
    return conn.cursor()

# ============================================
# Schema
# ============================================

def init_db():
    conn = get_db_connection()
    c = get_cursor(conn)

    try:
        # Create schema_version first to track migrations
        c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
        row = c.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        current_version = row['version'] if row else 0

        # If it's a completely fresh DB, create the new schema directly and set version to 3
        if current_version == 0:
            logging.info("[DB] Fresh database detected. Initializing schema v3.")
            
            # 1. Users table (shared identity)
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('candidate', 'hr', 'admin')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 2. Candidate profiles
            c.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    branch TEXT,
                    graduation_year INTEGER,
                    resume_path TEXT,
                    extracted_skills TEXT,
                    predicted_role TEXT
                )
            ''')

            # 3. Recruiter profiles
            c.execute('''
                CREATE TABLE IF NOT EXISTS recruiters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    company_name TEXT NOT NULL,
                    recruiter_name TEXT NOT NULL
                )
            ''')

            # 4. Jobs table
            c.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recruiter_id INTEGER NOT NULL REFERENCES recruiters(id),
                    company_name TEXT,
                    branch TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    required_skills TEXT,
                    experience_required INTEGER DEFAULT 0,
                    location TEXT,
                    job_type TEXT DEFAULT 'Full-time',
                    salary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 5. Applications table
            c.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
                    resume_path TEXT,
                    score REAL,
                    status TEXT DEFAULT 'Pending',
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id, candidate_id)
                )
            ''')

            # 6. Chat History table
            c.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    role TEXT NOT NULL,
                    user_text TEXT NOT NULL,
                    ai_text TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 7. User Profiles
            c.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id),
                    first_name TEXT,
                    last_name TEXT,
                    bio TEXT,
                    phone TEXT,
                    street TEXT,
                    city TEXT,
                    state TEXT
                )
            ''')

            # 8. Notifications table
            c.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT,
                    read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Legacy compat: hr_users table
            c.execute('''
                CREATE TABLE IF NOT EXISTS hr_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL
                )
            ''')

            c.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.commit()
            logging.info("[DB] Fresh database v3 initialized successfully.")
        else:
            # Table already exists under old schema, let the migration system handle it.
            logging.info(f"[DB] Database exists with version {current_version}. Running migrations...")
            _run_migrations(conn)

    except Exception as e:
        logging.error(f"[DB] Init Error: {e}")
        traceback.print_exc()
    finally:
        conn.close()


def _run_migrations(conn):
    """Run incremental schema migrations."""
    c = get_cursor(conn)
    try:
        # Get current version
        c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
        row = c.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        current = row['version'] if row else 0

        if current < 1:
            _migrate_v0_to_v1(conn)
            _set_schema_version(conn, 1)
            current = 1

        if current < 2:
            _migrate_v1_to_v2(conn)
            _set_schema_version(conn, 2)
            current = 2

        if current < 3:
            _migrate_v2_to_v3(conn)
            _set_schema_version(conn, 3)
            current = 3

        conn.commit()
    except Exception as e:
        logging.error(f"[DB] Migration error: {e}")
        traceback.print_exc()


def _set_schema_version(conn, version):
    c = get_cursor(conn)
    c.execute("DELETE FROM schema_version")
    c.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()


def _migrate_v0_to_v1(conn):
    """Migrate legacy hr_users data into unified users table."""
    logging.info("[DB] Legacy migration v0->v1 requested.")


def _migrate_v1_to_v2(conn):
    """Add any new columns for v2."""
    logging.info("[DB] Legacy migration v1->v2 requested.")


def _migrate_v2_to_v3(conn):
    """Migrate the schema to use correct relational foreign keys instead of email strings."""
    c = get_cursor(conn)
    try:
        logging.info("[DB] Starting migration from v2 to v3...")
        # Disable foreign key checks temporarily during tables recreation
        c.execute("PRAGMA foreign_keys = OFF")
        
        # 1. Rename existing tables
        tables_to_rename = ["users", "candidates", "recruiters", "jobs", "applications", "chat_history", "user_profiles", "notifications"]
        for table in tables_to_rename:
            try:
                c.execute(f"ALTER TABLE {table} RENAME TO _old_{table}")
            except sqlite3.OperationalError:
                pass # Table didn't exist
        
        # 2. Create new tables
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('candidate', 'hr', 'admin')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                branch TEXT,
                graduation_year INTEGER,
                resume_path TEXT,
                extracted_skills TEXT,
                predicted_role TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS recruiters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                company_name TEXT NOT NULL,
                recruiter_name TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recruiter_id INTEGER NOT NULL REFERENCES recruiters(id),
                company_name TEXT,
                branch TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                required_skills TEXT,
                experience_required INTEGER DEFAULT 0,
                location TEXT,
                job_type TEXT DEFAULT 'Full-time',
                salary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                candidate_id INTEGER NOT NULL REFERENCES candidates(id),
                resume_path TEXT,
                score REAL,
                status TEXT DEFAULT 'Pending',
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id, candidate_id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                role TEXT NOT NULL,
                user_text TEXT NOT NULL,
                ai_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                first_name TEXT,
                last_name TEXT,
                bio TEXT,
                phone TEXT,
                street TEXT,
                city TEXT,
                state TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. Migrate Users data
        try:
            rows = c.execute("SELECT id, email, password_hash, role, created_at FROM _old_users").fetchall()
            for r in rows:
                c.execute(
                    "INSERT OR IGNORE INTO users (id, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                    (r['id'], r['email'], r['password_hash'], r['role'], r['created_at'])
                )
        except Exception as e:
            logging.warning(f"[DB] Migration users fail: {e}")

        # 4. Migrate Recruiters data
        try:
            rows = c.execute("SELECT user_id, company_name, recruiter_name FROM _old_recruiters").fetchall()
            for r in rows:
                c.execute(
                    "INSERT OR IGNORE INTO recruiters (user_id, company_name, recruiter_name) VALUES (?, ?, ?)",
                    (r['user_id'], r['company_name'], r['recruiter_name'])
                )
        except Exception:
            # Fallback: create recruiter profiles from users table
            try:
                rows = c.execute("SELECT id, email FROM users WHERE role = 'hr'").fetchall()
                for r in rows:
                    c.execute(
                        "INSERT OR IGNORE INTO recruiters (user_id, company_name, recruiter_name) VALUES (?, 'Company', ?)",
                        (r['id'], r['email'].split('@')[0])
                    )
            except Exception:
                pass

        # 5. Migrate Candidates data
        try:
            # In old candidatos, fields were id, username, email, role. We map candidate to user by email
            rows = c.execute("SELECT username, email FROM _old_candidates").fetchall()
            for r in rows:
                u = c.execute("SELECT id FROM users WHERE email = ?", (r['email'],)).fetchone()
                if u:
                    c.execute(
                        "INSERT OR IGNORE INTO candidates (user_id, name) VALUES (?, ?)",
                        (u['id'], r['username'])
                    )
        except Exception as e:
            # Fallback: create candidates profiles from users table
            try:
                rows = c.execute("SELECT id, email FROM users WHERE role = 'candidate'").fetchall()
                for r in rows:
                    c.execute(
                        "INSERT OR IGNORE INTO candidates (user_id, name) VALUES (?, ?)",
                        (r['id'], r['email'].split('@')[0])
                    )
            except Exception:
                pass

        # 6. Migrate Jobs data
        try:
            rows = c.execute("SELECT * FROM _old_jobs").fetchall()
            for r in rows:
                rec = c.execute("SELECT id FROM recruiters WHERE user_id = (SELECT id FROM users WHERE email = ?)", (r['hr_email'],)).fetchone()
                rec_id = rec['id'] if rec else None
                if not rec_id:
                    # Create placeholder recruiter
                    c.execute("INSERT OR IGNORE INTO users (email, password_hash, role) VALUES (?, ?, 'hr')", (r['hr_email'], generate_password_hash("changeme")))
                    u = c.execute("SELECT id FROM users WHERE email = ?", (r['hr_email'],)).fetchone()
                    c.execute("INSERT OR IGNORE INTO recruiters (user_id, company_name, recruiter_name) VALUES (?, ?, ?)", (u['id'], r['company_name'] or 'Company', r['hr_email'].split('@')[0]))
                    rec = c.execute("SELECT id FROM recruiters WHERE user_id = ?", (u['id'],)).fetchone()
                    rec_id = rec['id']
                
                c.execute(
                    """INSERT OR IGNORE INTO jobs (id, recruiter_id, company_name, branch, title, description, required_skills, 
                                        experience_required, location, job_type, salary, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (r['id'], rec_id, r['company_name'], r['branch'], r['title'], r['description'], r['required_skills'],
                     r['experience_required'], r['location'], r['job_type'], r['salary'], r['created_at'])
                )
        except Exception as e:
            logging.warning(f"[DB] Migration jobs fail: {e}")

        # 7. Migrate Applications data
        try:
            rows = c.execute("SELECT * FROM _old_applications").fetchall()
            for r in rows:
                cand = c.execute("SELECT id FROM candidates WHERE user_id = (SELECT id FROM users WHERE email = ?)", (r['candidate_email'],)).fetchone()
                cand_id = cand['id'] if cand else None
                if not cand_id:
                    # Create placeholder candidate
                    c.execute("INSERT OR IGNORE INTO users (email, password_hash, role) VALUES (?, ?, 'candidate')", (r['candidate_email'], generate_password_hash("changeme")))
                    u = c.execute("SELECT id FROM users WHERE email = ?", (r['candidate_email'],)).fetchone()
                    c.execute("INSERT OR IGNORE INTO candidates (user_id, name) VALUES (?, ?)", (u['id'], r['candidate_name'] or r['candidate_email'].split('@')[0]))
                    cand = c.execute("SELECT id FROM candidates WHERE user_id = ?", (u['id'],)).fetchone()
                    cand_id = cand['id']
                
                c.execute(
                    """INSERT OR IGNORE INTO applications (id, job_id, candidate_id, resume_path, score, status, applied_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (r['id'], r['job_id'], cand_id, r['resume_path'], r['score'], r['status'], r['applied_at'])
                )
        except Exception as e:
            logging.warning(f"[DB] Migration applications fail: {e}")

        # 8. Migrate Chat History data
        try:
            rows = c.execute("SELECT * FROM _old_chat_history").fetchall()
            for r in rows:
                u = c.execute("SELECT id FROM users WHERE email = ?", (r['email'],)).fetchone()
                if u:
                    c.execute(
                        "INSERT OR IGNORE INTO chat_history (id, user_id, role, user_text, ai_text, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                        (r['id'], u['id'], r['role'], r['user_text'], r['ai_text'], r['timestamp'])
                    )
        except Exception as e:
            logging.warning(f"[DB] Migration chat_history fail: {e}")

        # 9. Migrate User Profiles data
        try:
            rows = c.execute("SELECT * FROM _old_user_profiles").fetchall()
            for r in rows:
                u = c.execute("SELECT id FROM users WHERE email = ?", (r['email'],)).fetchone()
                if u:
                    c.execute(
                        """INSERT OR IGNORE INTO user_profiles (user_id, first_name, last_name, bio, phone, street, city, state)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (u['id'], r['first_name'], r['last_name'], r['bio'], r['phone'], r['street'], r['city'], r['state'])
                    )
        except Exception as e:
            logging.warning(f"[DB] Migration user_profiles fail: {e}")

        # 10. Migrate Notifications data
        try:
            rows = c.execute("SELECT * FROM _old_notifications").fetchall()
            for r in rows:
                u = c.execute("SELECT id FROM users WHERE email = ?", (r['email'],)).fetchone()
                if u:
                    c.execute(
                        """INSERT OR IGNORE INTO notifications (id, user_id, type, title, message, read, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (r['id'], u['id'], r['type'], r['title'], r['message'], r['read'], r['created_at'])
                    )
        except Exception as e:
            logging.warning(f"[DB] Migration notifications fail: {e}")

        # 11. Clean up old tables
        for table in tables_to_rename:
            try:
                c.execute(f"DROP TABLE IF EXISTS _old_{table}")
            except sqlite3.OperationalError:
                pass
        
        c.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        logging.info("[DB] Schema migrated to v3 (relational structure) successfully.")
    except Exception as e:
        logging.error(f"[DB] Migration v2->v3 failed: {e}")
        raise e


# ============================================
# Authentication (Unified users table)
# ============================================

def register_user(email, password, role, username, **profile_data):
    """Register a user in the unified users table + role-specific profile."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        password_hash = generate_password_hash(password)
        c.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, password_hash, role)
        )
        user_id = c.lastrowid

        if role == 'candidate':
            c.execute(
                "INSERT INTO candidates (user_id, name, branch, graduation_year, resume_path) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, profile_data.get('branch'), profile_data.get('graduation_year'), profile_data.get('resume_path'))
            )
        elif role == 'hr':
            c.execute(
                "INSERT INTO recruiters (user_id, company_name, recruiter_name) VALUES (?, ?, ?)",
                (user_id, profile_data.get('company_name', 'Company'), username)
            )

        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None  # Email already exists
    except Exception as e:
        logging.error(f"[DB] Registration Error: {e}")
        return None
    finally:
        conn.close()


def verify_login(email, password):
    """Verify login credentials against unified users table.
    Returns user dict {id, email, role, username} or None.
    """
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("""
            SELECT u.id, u.email, u.password_hash, u.role, COALESCE(c.name, r.recruiter_name) as username
            FROM users u
            LEFT JOIN candidates c ON u.id = c.user_id
            LEFT JOIN recruiters r ON u.id = r.user_id
            WHERE u.email = ?
        """, (email,))
        user = c.fetchone()
        if not user:
            return None

        stored_hash = user['password_hash']
        if check_password_hash(stored_hash, password):
            return {
                'id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'username': user['username']
            }
        return None
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Lookup user by ID (for JWT verification)."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("""
            SELECT u.id, u.email, u.role, COALESCE(c.name, r.recruiter_name) as username
            FROM users u
            LEFT JOIN candidates c ON u.id = c.user_id
            LEFT JOIN recruiters r ON u.id = r.user_id
            WHERE u.id = ?
        """, (user_id,))
        user = c.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def get_user_by_email(email):
    """Lookup user by email."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("""
            SELECT u.id, u.email, u.role, COALESCE(c.name, r.recruiter_name) as username
            FROM users u
            LEFT JOIN candidates c ON u.id = c.user_id
            LEFT JOIN recruiters r ON u.id = r.user_id
            WHERE u.email = ?
        """, (email,))
        user = c.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


# ============================================
# Legacy Auth Compat (keeps old code working during transition)
# ============================================

def verify_hr_login(username, password):
    """Legacy: Verifies HR login."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("""
            SELECT u.id, u.email, u.password_hash, COALESCE(r.recruiter_name, u.email) as username 
            FROM users u
            JOIN recruiters r ON u.id = r.user_id
            WHERE r.recruiter_name = ? AND u.role = 'hr'
        """, (username,))
        user = c.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            return user['email']
        return None
    finally:
        conn.close()


def register_hr(username, password, email):
    """Legacy compat: Registers HR in new table."""
    user_id = register_user(email, password, 'hr', username)
    return user_id is not None


def register_candidate(username, email, password=None):
    """Legacy compat: Registers candidate."""
    pw = password or "changeme"
    user_id = register_user(email, pw, 'candidate', username)
    return user_id is not None


def login_candidate(email):
    """Legacy compat: Returns candidate info."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("""
            SELECT u.id, u.email, c.name as username 
            FROM users u
            JOIN candidates c ON u.id = c.user_id
            WHERE u.email = ? AND u.role = 'candidate'
        """, (email,))
        user = c.fetchone()
        if user:
            return {'id': user['id'], 'email': user['email'], 'username': user['username']}
        return None
    finally:
        conn.close()


# ============================================
# Job Management
# ============================================

def create_job(hr_email, company_name, branch, title, desc, req_skills, exp, location, job_type, salary):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        logging.info(f"[DB] Creating job: {title} for {company_name}")
        c.execute("SELECT id FROM recruiters WHERE user_id = (SELECT id FROM users WHERE email = ?)", (hr_email,))
        row = c.fetchone()
        if not row:
            logging.error(f"[DB] Recruiter not found for email: {hr_email}")
            return False
        recruiter_id = row['id']
        
        query = """
            INSERT INTO jobs
            (recruiter_id, company_name, branch, title, description, required_skills, experience_required, location, job_type, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        c.execute(query, (recruiter_id, company_name, branch, title, desc, req_skills, exp, location, job_type, salary))
        conn.commit()
        logging.info(f"[DB] Job '{title}' saved successfully.")
        return True
    except Exception as e:
        logging.error(f"[DB] Job Creation Error: {e}")
        traceback.print_exc()
        return False
    finally:
        conn.close()


def get_job_by_id(job_id):
    """Lookup single job by ID (including joining hr_email)."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = """
            SELECT jobs.*, users.email as hr_email 
            FROM jobs 
            JOIN recruiters ON jobs.recruiter_id = recruiters.id
            JOIN users ON recruiters.user_id = users.id
            WHERE jobs.id = ?
        """
        c.execute(query, (job_id,))
        return c.fetchone()
    finally:
        conn.close()


def get_jobs_by_hr(hr_email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = """
            SELECT jobs.*, users.email as hr_email 
            FROM jobs 
            JOIN recruiters ON jobs.recruiter_id = recruiters.id
            JOIN users ON recruiters.user_id = users.id
            WHERE users.email = ? 
            ORDER BY jobs.created_at DESC
        """
        c.execute(query, (hr_email,))
        return c.fetchall()
    finally:
        conn.close()


def get_all_jobs():
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = """
            SELECT jobs.*, users.email as hr_email 
            FROM jobs 
            JOIN recruiters ON jobs.recruiter_id = recruiters.id
            JOIN users ON recruiters.user_id = users.id
            ORDER BY jobs.created_at DESC
        """
        c.execute(query)
        return c.fetchall()
    finally:
        conn.close()


def delete_job(job_id, hr_email):
    """Deletes a job posting (only if owned by the requesting HR user)."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
        c.execute("""
            DELETE FROM jobs 
            WHERE id = ? AND recruiter_id = (
                SELECT r.id FROM recruiters r
                JOIN users u ON r.user_id = u.id
                WHERE u.email = ?
            )
        """, (job_id, hr_email))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logging.error(f"[DB] Job Delete Error: {e}")
        return False
    finally:
        conn.close()


# ============================================
# Application Management
# ============================================

def apply_for_job(job_id, candidate_email, candidate_name, resume_path, score, status="Pending"):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("SELECT id FROM candidates WHERE user_id = (SELECT id FROM users WHERE email = ?)", (candidate_email,))
        row = c.fetchone()
        if not row:
            logging.error(f"[DB] Candidate profile not found for email: {candidate_email}")
            return None
        candidate_id = row['id']

        query = """
            INSERT INTO applications
            (job_id, candidate_id, resume_path, score, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(job_id, candidate_id) DO UPDATE SET
                resume_path = excluded.resume_path,
                score = excluded.score,
                status = excluded.status
        """
        c.execute(query, (job_id, candidate_id, resume_path, score, status))
        conn.commit()
        row = c.execute(
            "SELECT id FROM applications WHERE job_id = ? AND candidate_id = ?",
            (job_id, candidate_id),
        ).fetchone()
        return row["id"] if row else None
    except Exception as e:
        logging.error(f"[DB] Application Error: {e}")
        return None
    finally:
        conn.close()


def get_applications_for_job(job_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = """
            SELECT apps.*, users.email as candidate_email, cands.name as candidate_name
            FROM applications apps
            JOIN candidates cands ON apps.candidate_id = cands.id
            JOIN users ON cands.user_id = users.id
            WHERE apps.job_id = ? 
            ORDER BY apps.score DESC
        """
        c.execute(query, (job_id,))
        return c.fetchall()
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


# ============================================
# User Profiles
# ============================================

def update_user_profile(email, username, role, first_name, last_name, bio, phone, street, city, state,
                        branch=None, graduation_year=None, resume_path=None, company_name=None):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("SELECT id, role FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        if not user:
            return False
        user_id = user['id']
        user_role = user['role']
        
        if username:
            if user_role == 'candidate':
                c.execute("UPDATE candidates SET name = ? WHERE user_id = ?", (username, user_id))
            elif user_role == 'hr':
                c.execute("UPDATE recruiters SET recruiter_name = ? WHERE user_id = ?", (username, user_id))

        # Update candidate-specific fields
        if user_role == 'candidate':
            if branch is not None:
                c.execute("UPDATE candidates SET branch = ? WHERE user_id = ?", (branch, user_id))
            if graduation_year is not None:
                c.execute("UPDATE candidates SET graduation_year = ? WHERE user_id = ?", (graduation_year, user_id))
            if resume_path is not None:
                c.execute("UPDATE candidates SET resume_path = ? WHERE user_id = ?", (resume_path, user_id))
        
        # Update recruiter-specific fields
        elif user_role == 'hr':
            if company_name is not None:
                c.execute("UPDATE recruiters SET company_name = ? WHERE user_id = ?", (company_name, user_id))
        
        c.execute("""
            INSERT INTO user_profiles (user_id, first_name, last_name, bio, phone, street, city, state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                bio = excluded.bio,
                phone = excluded.phone,
                street = excluded.street,
                city = excluded.city,
                state = excluded.state
        """, (user_id, first_name, last_name, bio, phone, street, city, state))
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"[DB] Profile Update Error: {e}")
        return False
    finally:
        conn.close()


def get_user_profile(email):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query = """
            SELECT u.email, u.role, 
                   COALESCE(c.name, r.recruiter_name) as username,
                   up.first_name, up.last_name, up.bio, up.phone, up.street, up.city, up.state,
                   c.branch, c.graduation_year, c.resume_path,
                   c.extracted_skills, c.predicted_role,
                   r.company_name
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            LEFT JOIN candidates c ON u.id = c.user_id
            LEFT JOIN recruiters r ON u.id = r.user_id
            WHERE u.email = ?
        """
        c.execute(query, (email,))
        profile = c.fetchone()
        return profile
    finally:
        conn.close()


# ============================================
# Extracted Skills Persistence
# ============================================

def save_extracted_skills(email, skills_list, predicted_role=None):
    """Saves extracted skills (as JSON) and predicted role to the candidates table."""
    import json
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        skills_json = json.dumps(skills_list) if isinstance(skills_list, list) else str(skills_list)
        c.execute("""
            UPDATE candidates SET extracted_skills = ?, predicted_role = ?
            WHERE user_id = (SELECT id FROM users WHERE email = ?)
        """, (skills_json, predicted_role, email))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logging.error(f"[DB] Save Extracted Skills Error: {e}")
        return False
    finally:
        conn.close()


def get_extracted_skills(email):
    """Retrieves extracted skills and predicted role for a candidate.
    Returns dict: {extracted_skills: [...], predicted_role: str} or None.
    """
    import json
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("""
            SELECT c.extracted_skills, c.predicted_role
            FROM candidates c
            JOIN users u ON c.user_id = u.id
            WHERE u.email = ?
        """, (email,))
        row = c.fetchone()
        if row:
            skills_raw = row['extracted_skills']
            skills = []
            if skills_raw:
                try:
                    skills = json.loads(skills_raw)
                except (json.JSONDecodeError, TypeError):
                    skills = [s.strip() for s in skills_raw.split(',') if s.strip()]
            return {
                'extracted_skills': skills,
                'predicted_role': row['predicted_role'] or 'Unknown'
            }
        return None
    finally:
        conn.close()


def add_extracted_skills_column():
    """Migration helper: adds extracted_skills and predicted_role columns if missing."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        # Check if column exists
        columns = [col[1] for col in c.execute("PRAGMA table_info(candidates)").fetchall()]
        if 'extracted_skills' not in columns:
            c.execute("ALTER TABLE candidates ADD COLUMN extracted_skills TEXT")
            logging.info("[DB] Added extracted_skills column to candidates table")
        if 'predicted_role' not in columns:
            c.execute("ALTER TABLE candidates ADD COLUMN predicted_role TEXT")
            logging.info("[DB] Added predicted_role column to candidates table")
        conn.commit()
    except Exception as e:
        logging.warning(f"[DB] Column migration warning: {e}")
    finally:
        conn.close()


# ============================================
# Chat History
# ============================================

def add_chat_message(email, role, user_text, ai_text):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        if not row:
            logging.warning(f"[DB] Chat History Warning: Cannot save chat message. User '{email}' does not exist.")
            return
        
        user_id = row[0] if isinstance(row, tuple) else row['id']
        c.execute("""
            INSERT INTO chat_history (user_id, role, user_text, ai_text) 
            VALUES (?, ?, ?, ?)
        """, (user_id, role, user_text, ai_text))
        conn.commit()
    except Exception as e:
        logging.error(f"[DB] Chat History Error: {e}")
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
            query = """
                SELECT user_text, ai_text, timestamp FROM (
                    SELECT user_text, ai_text, timestamp FROM chat_history 
                    WHERE user_id = (SELECT id FROM users WHERE email = ?) 
                    ORDER BY timestamp DESC LIMIT ?
                ) ORDER BY timestamp ASC
            """
            c.execute(query, (email, limit))
        else:
            query = """
                SELECT user_text, ai_text, timestamp FROM chat_history 
                WHERE user_id = (SELECT id FROM users WHERE email = ?) 
                ORDER BY timestamp ASC
            """
            c.execute(query, (email,))
        history = c.fetchall()
        formatted = []
        for row in history:
            formatted.append({
                "user": row["user_text"],
                "ai": row["ai_text"]
            })
        return formatted
    finally:
        conn.close()


# ============================================
# Notifications
# ============================================

def add_notification(email, notif_type, title, message=""):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("""
            INSERT INTO notifications (user_id, type, title, message) 
            VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, ?)
        """, (email, notif_type, title, message))
        conn.commit()
    except Exception as e:
        logging.error(f"[DB] Notification Error: {e}")
    finally:
        conn.close()


def get_notifications(email, unread_only=False):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        if unread_only:
            c.execute("""
                SELECT * FROM notifications 
                WHERE user_id = (SELECT id FROM users WHERE email = ?) AND read = 0 
                ORDER BY created_at DESC
            """, (email,))
        else:
            c.execute("""
                SELECT * FROM notifications 
                WHERE user_id = (SELECT id FROM users WHERE email = ?) 
                ORDER BY created_at DESC LIMIT 50
            """, (email,))
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()


# ============================================
# Admin
# ============================================

def clear_all_data():
    """DANGEROUS: Wipes tables. Used for admin reset."""
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        tables = ["applications", "jobs", "hr_users", "candidates", "recruiters", "users", "user_profiles", "chat_history", "notifications"]
        for table in tables:
            try:
                c.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()