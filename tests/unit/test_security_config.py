"""
TalentFlow AI — Phase 1 Unit Tests (Security & Configuration)
"""
import pytest
import sys
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings, AppSettings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, revoke_token,
    ROLE_CANDIDATE, ROLE_RECRUITER
)
from app.core.exceptions import (
    AuthenticationError, TokenExpiredError,
    PermissionDeniedError, ValidationError, NotFoundError
)


class TestConfigManagement:
    def test_settings_initialization(self):
        assert settings.app_name == "TalentFlow AI"
        assert len(settings.cors_origins) > 0
        assert settings.storage.max_upload_size_mb >= 5

    def test_production_readiness_validation(self):
        from app.core.config import AppSettings
        custom = AppSettings(
            FLASK_ENV="production"
        )
        custom.auth.jwt_secret = "dev-secret-change-in-production"
        custom.db.url = "sqlite:///test.db"
        custom.ai.hf_token = ""
        issues = custom.validate_production_readiness()
        assert len(issues) >= 2




class TestSecurityAndTokens:
    def test_password_hashing_and_verification(self):
        raw = "SecureSecretPassword123!"
        hashed = hash_password(raw)
        assert hashed != raw
        assert verify_password(raw, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_access_token_creation_and_claims(self):
        token = create_access_token(
            user_id="user_123",
            email="recruiter@talentflow.ai",
            role=ROLE_RECRUITER,
            username="AliceRecruiter",
            organization_id="org_456"
        )
        payload = decode_token(token, is_refresh=False)
        assert payload["sub"] == "user_123"
        assert payload["email"] == "recruiter@talentflow.ai"
        assert payload["role"] == ROLE_RECRUITER
        assert payload["org_id"] == "org_456"
        assert payload["type"] == "access"

    def test_refresh_token_creation_and_validation(self):
        ref_token = create_refresh_token(
            user_id="cand_789",
            email="candidate@talentflow.ai",
            role=ROLE_CANDIDATE
        )
        payload = decode_token(ref_token, is_refresh=True)
        assert payload["sub"] == "cand_789"
        assert payload["type"] == "refresh"

        # Attempting to use refresh token as access token must fail
        with pytest.raises(AuthenticationError):
            decode_token(ref_token, is_refresh=False)

    def test_token_revocation(self):
        token = create_access_token(user_id="rev_1", email="rev@test.com", role=ROLE_CANDIDATE)
        assert decode_token(token, is_refresh=False)["email"] == "rev@test.com"

        revoke_token(token)
        with pytest.raises(AuthenticationError, match="revoked"):
            decode_token(token, is_refresh=False)


class TestCustomExceptions:
    def test_exception_serialization(self):
        err = ValidationError("Field missing", details={"field": "email"})
        data = err.to_dict()
        assert data["status"] == "error"
        assert data["error_code"] == "VALIDATION_FAILED"
        assert data["details"]["field"] == "email"
        assert err.status_code == 422
