"""
TalentFlow AI — Phase 2 Unit & Integration Tests (Models & Data Layer)
"""
import pytest
import sys
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, BACKEND_DIR)

from app.models.base import Base
from app.models import (
    Organization, User, Candidate, Recruiter, Job,
    Resume, Application, MatchResult, Notification, AuditLog, ChatMessage
)
from scripts.migrate_sqlite_to_postgres import run_migration


@pytest.fixture(scope="module")
def test_db_session():
    """In-memory SQLite database session for model testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestModelRelationships:
    def test_organization_and_user_creation(self, test_db_session):
        org = Organization(
            name="Acme Corp",
            slug="acme-corp",
            settings={"plan": "pro"}
        )
        test_db_session.add(org)
        test_db_session.flush()

        user = User(
            email="recruiter@acme.com",
            password_hash="pbkdf2:sha256:test",
            role="hr",
            username="acme_recruiter",
            organization_id=org.id
        )
        test_db_session.add(user)
        test_db_session.flush()

        recruiter = Recruiter(
            user_id=user.id,
            recruiter_name="Jane Doe",
            company_name=org.name
        )
        test_db_session.add(recruiter)
        test_db_session.flush()

        assert recruiter.user.email == "recruiter@acme.com"
        assert user.organization.name == "Acme Corp"

    def test_job_and_application_kanban_flow(self, test_db_session):
        org = test_db_session.query(Organization).first()
        recruiter = test_db_session.query(Recruiter).first()

        job = Job(
            organization_id=org.id,
            recruiter_id=recruiter.id,
            title="Senior Fullstack Engineer",
            description="Build scalable microservices and React UIs",
            required_skills="Python, React, PostgreSQL",
            experience_required=3,
            scoring_config={"skills": 0.5, "semantic": 0.5}
        )
        test_db_session.add(job)
        test_db_session.flush()

        cand_user = User(
            email="candidate1@talentflow.ai",
            password_hash="pbkdf2:sha256:test",
            role="candidate",
            username="candidate1"
        )
        test_db_session.add(cand_user)
        test_db_session.flush()

        candidate = Candidate(
            user_id=cand_user.id,
            name="John Applicant",
            branch="Computer Science",
            graduation_year=2024
        )
        test_db_session.add(candidate)
        test_db_session.flush()

        resume = Resume(
            candidate_id=candidate.id,
            file_path="uploads/test_resume.pdf",
            original_filename="test_resume.pdf",
            extracted_skills=["Python", "React", "PostgreSQL"],
            predicted_role="Fullstack Developer"
        )
        test_db_session.add(resume)
        test_db_session.flush()

        app = Application(
            job_id=job.id,
            candidate_id=candidate.id,
            resume_id=resume.id,
            stage="applied",
            score=0.88
        )
        test_db_session.add(app)
        test_db_session.flush()

        # Advance Kanban stage
        app.stage = "shortlisted"
        test_db_session.commit()

        reloaded = test_db_session.query(Application).filter_by(id=app.id).first()
        assert reloaded.stage == "shortlisted"
        assert reloaded.candidate.name == "John Applicant"
        assert reloaded.job.title == "Senior Fullstack Engineer"


def init_minimal_legacy_sqlite(db_path):
    """Creates a realistic minimal legacy SQLite database schema and sample data."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('candidate', 'hr', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE recruiters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            recruiter_name TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            branch TEXT,
            graduation_year INTEGER,
            resume_path TEXT,
            extracted_skills TEXT,
            predicted_role TEXT
        )
    """)
    c.execute("""
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_id INTEGER NOT NULL,
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
    """)
    c.execute("""
        CREATE TABLE applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            resume_path TEXT,
            score REAL,
            status TEXT DEFAULT 'Pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            user_text TEXT NOT NULL,
            ai_text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Insert realistic sample data
    c.execute("INSERT INTO users (id, email, password_hash, role) VALUES (1, 'hr@legacy.com', 'pbkdf2:sha256:legacy', 'hr')")
    c.execute("INSERT INTO users (id, email, password_hash, role) VALUES (2, 'cand@legacy.com', 'pbkdf2:sha256:legacy', 'candidate')")
    c.execute("INSERT INTO recruiters (id, user_id, company_name, recruiter_name) VALUES (1, 1, 'Acme Inc', 'Alice HR')")
    c.execute("INSERT INTO candidates (id, user_id, name, branch, graduation_year) VALUES (1, 2, 'Bob Candidate', 'CS', 2024)")
    c.execute("INSERT INTO jobs (id, recruiter_id, company_name, title, description, required_skills) VALUES (1, 1, 'Acme Inc', 'Dev', 'Building APIs', 'Python')")
    c.execute("INSERT INTO applications (id, job_id, candidate_id, score, status) VALUES (1, 1, 1, 85.0, 'Pending')")
    conn.commit()
    conn.close()


class TestMigrationUtility:
    def test_migration_execution(self, tmp_path):
        """Valid legacy SQLite -> migration succeeds with complete data integrity."""
        source_db_path = tmp_path / "legacy_source.db"
        init_minimal_legacy_sqlite(source_db_path)

        test_target_db = f"sqlite:///{tmp_path / 'migrated_test.db'}"
        success = run_migration(sqlite_path=str(source_db_path), target_db_url=test_target_db)
        assert success is True

        target_engine = create_engine(test_target_db)
        TargetSession = sessionmaker(bind=target_engine)
        session = TargetSession()
        try:
            assert session.query(User).count() == 2
            assert session.query(Candidate).count() == 1
            assert session.query(Job).count() == 1
            assert session.query(Application).count() == 1
        finally:
            session.close()

    def test_migration_invalid_source(self, tmp_path):
        """Empty or invalid SQLite database -> migration fails clearly with False."""
        empty_db_path = tmp_path / "empty_source.db"
        import sqlite3
        conn = sqlite3.connect(empty_db_path)
        conn.close()

        test_target_db = f"sqlite:///{tmp_path / 'target_fail.db'}"
        success = run_migration(sqlite_path=str(empty_db_path), target_db_url=test_target_db)
        assert success is False
