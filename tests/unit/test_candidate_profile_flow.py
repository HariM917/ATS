"""
TalentFlow AI — Candidate Profile Resolution & Auto-Provisioning Test Suite
Verifies:
1. Standard Registration -> Login -> GET /api/v1/candidates/profile returns 200.
2. User exists without Candidate profile -> GET /api/v1/candidates/profile auto-provisions Candidate profile.
3. User deleted / missing from DB but has valid signed JWT -> GET /api/v1/candidates/profile self-heals user & candidate records.
"""
import pytest
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, BACKEND_DIR)

from app.factory import create_app
from app.core.database import get_db_context
from app.core.security import create_access_token, hash_password
from app.models import User, Candidate


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


class TestCandidateProfileResolution:
    def test_standard_candidate_registration_and_profile_retrieval(self, client):
        email = f"standard_{os.urandom(4).hex()}@example.com"
        # 1. Register candidate
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password123!",
            "username": "Standard Candidate",
            "role": "candidate",
            "branch": "Computer Science",
            "graduation_year": 2025
        })
        assert reg_resp.status_code == 201
        token = reg_resp.get_json()["token"]

        # 2. Query profile
        headers = {"Authorization": f"Bearer {token}"}
        prof_resp = client.get("/api/v1/candidates/profile", headers=headers)
        assert prof_resp.status_code == 200
        data = prof_resp.get_json()
        assert data["status"] == "success"
        assert data["email"] == email
        assert "candidate_id" in data
        assert data["name"] == "Standard Candidate"
        assert data["branch"] == "Computer Science"

    def test_missing_candidate_row_auto_provisions(self, client):
        email = f"orphan_{os.urandom(4).hex()}@example.com"
        user_id = None
        # Create a user in the database directly WITHOUT a candidate profile row
        with get_db_context() as db:
            user = User(
                email=email,
                password_hash=hash_password("Password123!"),
                role="candidate",
                username="Orphan Candidate"
            )
            db.add(user)
            db.flush()
            user_id = str(user.id)
            db.commit()

        token = create_access_token(user_id, email, "candidate", username="Orphan Candidate")
        headers = {"Authorization": f"Bearer {token}"}

        # Query profile: should NOT return 404 User not found, should auto-provision Candidate row
        prof_resp = client.get("/api/v1/candidates/profile", headers=headers)
        assert prof_resp.status_code == 200
        data = prof_resp.get_json()
        assert data["status"] == "success"
        assert data["email"] == email
        assert "candidate_id" in data
        assert data["name"] == "Orphan Candidate"

        # Verify candidate row now exists in database
        with get_db_context() as db:
            cand = db.query(Candidate).filter_by(user_id=user_id).first()
            assert cand is not None
            assert cand.name == "Orphan Candidate"

    def test_missing_user_row_with_valid_jwt_self_heals(self, client):
        # User has a valid token issued by server, but user row is absent from database (e.g. wiped SQLite)
        ghost_id = f"ghost-{os.urandom(8).hex()}"
        ghost_email = f"ghost_{os.urandom(4).hex()}@example.com"
        token = create_access_token(ghost_id, ghost_email, "candidate", username="Ghost User")
        headers = {"Authorization": f"Bearer {token}"}

        prof_resp = client.get("/api/v1/candidates/profile", headers=headers)
        assert prof_resp.status_code == 200
        data = prof_resp.get_json()
        assert data["status"] == "success"
        assert data["email"] == ghost_email
        assert "candidate_id" in data

        # Verify User and Candidate are persisted
        with get_db_context() as db:
            user = db.query(User).filter_by(email=ghost_email).first()
            assert user is not None
            cand = db.query(Candidate).filter_by(user_id=str(user.id)).first()
            assert cand is not None
