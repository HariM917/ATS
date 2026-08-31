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


class TestMigrationUtility:
    def test_migration_execution(self, tmp_path):
        test_target_db = f"sqlite:///{tmp_path / 'migrated_test.db'}"
        success = run_migration(target_db_url=test_target_db)
        assert success is True
