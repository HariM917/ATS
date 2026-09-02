"""
TalentFlow AI — Pytest Global Configuration & Shared Test Fixtures
Ensures test isolation, database initialization, and reproducible testing in CI environments.
"""
import sys
import os
from pathlib import Path
import pytest

# Ensure backend root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Force testing environment
os.environ["FLASK_ENV"] = "testing"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    """Initializes a dedicated test database and schema for isolated test execution."""
    test_db_dir = tmp_path_factory.mktemp("db")
    test_db_path = test_db_dir / "test_talentflow.db"

    # Set DATABASE_URL to our clean test database
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

    from app.core.config import settings
    settings.environment = "testing"
    settings.db.url = f"sqlite:///{test_db_path}"

    # Initialize all SQLAlchemy tables
    from app.core.database import init_database
    init_database()

    # Also prepare legacy db_manager path if legacy tests are invoked
    try:
        import db_manager
        legacy_db_path = str(test_db_dir / "legacy_hiring_system.db")
        db_manager.DB_PATH = legacy_db_path
        db_manager.init_db()
    except Exception:
        pass

    yield test_db_path


@pytest.fixture
def auth_candidate():
    """
    Ensures test_candidate_api@example.com exists with password 'Password123!'
    properly hashed using the standard auth service.
    Guarantees auth test isolation across test runs and arbitrary execution order.
    """
    from app.core.database import get_db_context
    from app.core.security import hash_password
    from app.models import User, Candidate

    email = "test_candidate_api@example.com"
    raw_password = "Password123!"

    with get_db_context() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                password_hash=hash_password(raw_password),
                role="candidate",
                username="test_candidate_api"
            )
            db.add(user)
            db.flush()

            cand = Candidate(
                user_id=user.id,
                name="Test Candidate API",
                branch="Computer Science",
                graduation_year=2025
            )
            db.add(cand)
            db.commit()
        else:
            # Ensure password hash is up to date
            user.password_hash = hash_password(raw_password)
            if not user.candidate_profile:
                cand = Candidate(
                    user_id=user.id,
                    name="Test Candidate API",
                    branch="Computer Science",
                    graduation_year=2025
                )
                db.add(cand)
            db.commit()

    return {"email": email, "password": raw_password}
