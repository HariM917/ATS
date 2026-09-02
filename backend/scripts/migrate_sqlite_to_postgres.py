"""
TalentFlow AI — SQLite to PostgreSQL Safe Data Migration Utility
Migrates data from authoritative hiring_system.db into target PostgreSQL (or SQLAlchemy-managed DB).
Preserves relationships, provisions tenant organizations, maps IDs, and performs validation.
"""
import os
import sys
import uuid
import sqlite3
import json
import logging
from pathlib import Path

# Set up module path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionFactory, init_database, engine as default_engine
from app.models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Organization, User, Candidate, Recruiter, Job,
    Resume, Application, MatchResult, Notification, ChatMessage
)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")


def run_migration(sqlite_path: str = None, target_db_url: str = None, dry_run: bool = False):
    if not sqlite_path:
        sqlite_path = str(BACKEND_DIR / "hiring_system.db")

    if not target_db_url:
        target_db_url = os.getenv("DATABASE_URL")
        if not target_db_url or "hiring_system.db" in target_db_url:
            target_path = BACKEND_DIR / "talentflow_dev.db"
            target_db_url = f"sqlite:///{target_path}"

    if not os.path.exists(sqlite_path):
        logger.error(f"Source SQLite database not found at {sqlite_path}")
        return False

    logger.info(f"=== Starting Migration from {sqlite_path} to {target_db_url} ===")
    src_conn = sqlite3.connect(sqlite_path)
    src_conn.row_factory = sqlite3.Row

    # Pre-flight check: ensure source SQLite database has required core tables
    required_tables = {"users", "candidates", "recruiters", "jobs", "applications"}
    existing_tables = {
        row[0]
        for row in src_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    missing_tables = required_tables - existing_tables
    if missing_tables:
        logger.error(
            f"Source SQLite database is invalid or empty. Missing required tables: {sorted(missing_tables)}"
        )
        src_conn.close()
        return False

    # Create target engine and tables
    target_engine = create_engine(target_db_url)
    Base.metadata.create_all(bind=target_engine)
    TargetSessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
    dest_session = TargetSessionFactory()


    # ID Mapping stores: (table, old_id) -> new_uuid
    id_map = {
        "users": {},
        "recruiters": {},
        "candidates": {},
        "jobs": {},
        "applications": {},
    }

    try:
        # 1. Provision Default Organization
        default_org = dest_session.query(Organization).filter_by(slug="default-org").first()
        if not default_org:
            default_org = Organization(
                id=str(uuid.uuid4()),
                name="TalentFlow Organization",
                slug="default-org",
                settings={"plan": "enterprise", "features": ["ai_screening", "rag_chatbot"]}
            )
            dest_session.add(default_org)
            dest_session.flush()
            logger.info(f"Provisioned default Organization: {default_org.name} ({default_org.id})")
        else:
            logger.info(f"Using existing Organization: {default_org.name}")

        # 2. Migrate Users
        user_rows = src_conn.execute("SELECT * FROM users").fetchall()
        logger.info(f"Found {len(user_rows)} users to migrate.")
        for row in user_rows:
            old_id = row["id"]
            email = row["email"]
            role = row["role"]
            created_at_str = row["created_at"]

            # Check if user already exists
            existing_user = dest_session.query(User).filter_by(email=email).first()
            if existing_user:
                id_map["users"][old_id] = existing_user.id
                logger.info(f"User {email} already exists -> mapped to {existing_user.id}")
            else:
                new_user_id = str(uuid.uuid4())
                new_user = User(
                    id=new_user_id,
                    email=email,
                    password_hash=row["password_hash"] if "password_hash" in row.keys() else "pbkdf2:sha256:260000$dummy",
                    role=role,
                    username=email.split("@")[0],
                    organization_id=default_org.id if role in ("hr", "admin", "org_admin") else None
                )
                dest_session.add(new_user)
                id_map["users"][old_id] = new_user_id
        dest_session.flush()

        # 3. Migrate Recruiters
        recruiter_rows = src_conn.execute("SELECT * FROM recruiters").fetchall()
        logger.info(f"Found {len(recruiter_rows)} recruiters to migrate.")
        for row in recruiter_rows:
            old_id = row["id"]
            old_user_id = row["user_id"]
            new_user_id = id_map["users"].get(old_user_id)

            if new_user_id:
                existing_rec = dest_session.query(Recruiter).filter_by(user_id=new_user_id).first()
                if existing_rec:
                    id_map["recruiters"][old_id] = existing_rec.id
                else:
                    new_rec_id = str(uuid.uuid4())
                    new_rec = Recruiter(
                        id=new_rec_id,
                        user_id=new_user_id,
                        recruiter_name=row["recruiter_name"] or "Recruiter",
                        company_name=row["company_name"] or default_org.name
                    )
                    dest_session.add(new_rec)
                    id_map["recruiters"][old_id] = new_rec_id
        dest_session.flush()

        # 4. Migrate Candidates
        candidate_rows = src_conn.execute("SELECT * FROM candidates").fetchall()
        logger.info(f"Found {len(candidate_rows)} candidates to migrate.")
        for row in candidate_rows:
            old_id = row["id"]
            old_user_id = row["user_id"]
            new_user_id = id_map["users"].get(old_user_id)

            if new_user_id:
                existing_cand = dest_session.query(Candidate).filter_by(user_id=new_user_id).first()
                if existing_cand:
                    id_map["candidates"][old_id] = existing_cand.id
                else:
                    new_cand_id = str(uuid.uuid4())
                    new_cand = Candidate(
                        id=new_cand_id,
                        user_id=new_user_id,
                        name=row["name"] or "Candidate",
                        branch=row["branch"],
                        graduation_year=row["graduation_year"]
                    )
                    dest_session.add(new_cand)
                    id_map["candidates"][old_id] = new_cand_id

                    # If candidate had a resume_path, migrate as Resume record
                    resume_path = row["resume_path"]
                    if resume_path:
                        skills_val = []
                        if "extracted_skills" in row.keys() and row["extracted_skills"]:
                            try:
                                skills_val = json.loads(row["extracted_skills"]) if isinstance(row["extracted_skills"], str) else row["extracted_skills"]
                            except Exception:
                                skills_val = [s.strip() for s in row["extracted_skills"].split(",") if s.strip()]

                        new_resume = Resume(
                            id=str(uuid.uuid4()),
                            candidate_id=new_cand_id,
                            version=1,
                            file_path=resume_path,
                            original_filename=os.path.basename(resume_path),
                            extracted_skills=skills_val,
                            predicted_role=row["predicted_role"] if "predicted_role" in row.keys() else None
                        )
                        dest_session.add(new_resume)
        dest_session.flush()

        # 5. Migrate Jobs
        job_rows = src_conn.execute("SELECT * FROM jobs").fetchall()
        logger.info(f"Found {len(job_rows)} jobs to migrate.")
        for row in job_rows:
            old_id = row["id"]
            old_rec_id = row["recruiter_id"]
            new_rec_id = id_map["recruiters"].get(old_rec_id)

            if not new_rec_id:
                # Assign to first available recruiter or create fallback
                first_rec = dest_session.query(Recruiter).first()
                new_rec_id = first_rec.id if first_rec else None

            if new_rec_id:
                new_job_id = str(uuid.uuid4())
                new_job = Job(
                    id=new_job_id,
                    organization_id=default_org.id,
                    recruiter_id=new_rec_id,
                    title=row["title"] or "Software Engineer",
                    department=row["branch"] or "Engineering",
                    company_name=row["company_name"] or default_org.name,
                    description=row["description"] or "",
                    required_skills=row["required_skills"] or "",
                    experience_required=row["experience_required"] or 0,
                    location=row["location"] or "Remote",
                    job_type=row["job_type"] or "Full-time",
                    salary=row["salary"] or "",
                    status="active"
                )
                dest_session.add(new_job)
                id_map["jobs"][old_id] = new_job_id
        dest_session.flush()

        # 6. Migrate Applications
        app_rows = src_conn.execute("SELECT * FROM applications").fetchall()
        logger.info(f"Found {len(app_rows)} applications to migrate.")
        for row in app_rows:
            old_id = row["id"]
            old_job_id = row["job_id"]
            old_cand_id = row["candidate_id"]

            new_job_id = id_map["jobs"].get(old_job_id)
            new_cand_id = id_map["candidates"].get(old_cand_id)

            if new_job_id and new_cand_id:
                new_app_id = str(uuid.uuid4())
                status_val = (row["status"] or "applied").lower()
                score_val = float(row["score"] or 0.0)

                new_app = Application(
                    id=new_app_id,
                    job_id=new_job_id,
                    candidate_id=new_cand_id,
                    status=status_val,
                    stage=status_val,
                    score=score_val
                )
                dest_session.add(new_app)
                id_map["applications"][old_id] = new_app_id
        dest_session.flush()

        # 7. Migrate Chat History
        chat_rows = src_conn.execute("SELECT * FROM chat_history").fetchall()
        logger.info(f"Found {len(chat_rows)} chat messages to migrate.")
        for row in chat_rows:
            old_user_id = row["user_id"]
            new_user_id = id_map["users"].get(old_user_id)
            new_chat = ChatMessage(
                id=str(uuid.uuid4()),
                user_id=new_user_id,
                session_id=str(uuid.uuid4()),
                role=row["role"] or "user",
                user_text=row["user_text"] or "",
                ai_text=row["ai_text"] or "",
                sources=[]
            )
            dest_session.add(new_chat)

        if not dry_run:
            dest_session.commit()
            logger.info("=== Migration Committed Successfully! ===")
        else:
            dest_session.rollback()
            logger.info("=== Dry Run Complete (Rolled Back) ===")

        # Summary Validation
        user_count = dest_session.query(User).count()
        job_count = dest_session.query(Job).count()
        cand_count = dest_session.query(Candidate).count()
        app_count = dest_session.query(Application).count()
        logger.info(f"Target DB Stats: {user_count} users, {cand_count} candidates, {job_count} jobs, {app_count} applications.")
        return True

    except Exception as e:
        dest_session.rollback()
        logger.error(f"Migration failed with error: {e}", exc_info=True)
        return False
    finally:
        src_conn.close()
        dest_session.close()


if __name__ == "__main__":
    run_migration()
