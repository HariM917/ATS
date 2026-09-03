"""
TalentFlow AI — Production Startup, Health Endpoints & Readiness Smoke Tests
Verifies app factory, fail-fast production configuration, PostgreSQL requirements,
and all container/health check endpoints.
"""
import pytest
import sys
import os
from unittest.mock import patch

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, BACKEND_DIR)

from app.factory import create_app  # type: ignore
from app.core.config import AppSettings  # type: ignore


@pytest.fixture(scope="module")
def app_client():
    """Testing client using standard factory initialization."""
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


class TestProductionReadinessValidation:
    """Verify strict fail-fast production guards."""

    def test_production_rejects_missing_or_default_jwt_secret(self):
        cfg = AppSettings(FLASK_ENV="production")
        cfg.auth.jwt_secret = "dev-secret-change-in-production"
        cfg.auth.flask_secret_key = "a-secure-production-flask-secret-32b"
        cfg.db.url = "postgresql://user:pass@localhost:5432/talentflow"

        issues = cfg.validate_production_readiness()
        assert any("JWT_SECRET" in i for i in issues)

    def test_production_rejects_sqlite_database(self):
        cfg = AppSettings(FLASK_ENV="production")
        cfg.auth.jwt_secret = "a-secure-production-jwt-secret-key-32b"
        cfg.auth.flask_secret_key = "a-secure-production-flask-secret-32b"
        cfg.db.url = "sqlite:///talentflow.db"

        issues = cfg.validate_production_readiness()
        assert any("SQLite is not allowed in production" in i for i in issues)

    def test_production_rejects_non_postgres_scheme(self):
        cfg = AppSettings(FLASK_ENV="production")
        cfg.auth.jwt_secret = "a-secure-production-jwt-secret-key-32b"
        cfg.auth.flask_secret_key = "a-secure-production-flask-secret-32b"
        cfg.db.url = "mysql://user:pass@localhost:3306/talentflow"

        issues = cfg.validate_production_readiness()
        assert any("postgresql://" in i or "postgres://" in i for i in issues)

    def test_production_accepts_valid_postgres_and_secrets(self):
        cfg = AppSettings(FLASK_ENV="production")
        cfg.auth.jwt_secret = "a-secure-production-jwt-secret-key-32b"
        cfg.auth.flask_secret_key = "a-secure-production-flask-secret-32b"
        cfg.db.url = "postgresql://user:pass@ep-cool-db.render.com:5432/talentflow"

        issues = cfg.validate_production_readiness()
        assert len(issues) == 0


class TestProductionStartupFailFast:
    """Verify create_app() raises RuntimeError when production requirements are violated."""

    def test_production_startup_fails_without_proper_config(self, monkeypatch):
        monkeypatch.setenv("FLASK_ENV", "production")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("JWT_SECRET", "secret")

        from app.core.config import settings
        orig_env = settings.environment
        orig_db = settings.db.url
        orig_jwt = settings.auth.jwt_secret

        try:
            settings.environment = "production"
            settings.db.url = "sqlite:///test.db"
            settings.auth.jwt_secret = "secret"

            with pytest.raises(RuntimeError, match="Production readiness validation failed"):
                create_app()
        finally:
            settings.environment = orig_env
            settings.db.url = orig_db
            settings.auth.jwt_secret = orig_jwt

    def test_production_startup_succeeds_with_valid_postgres_and_mocked_db_check(self, monkeypatch):
        from app.core.config import settings
        orig_env = settings.environment
        orig_db = settings.db.url
        orig_jwt = settings.auth.jwt_secret
        orig_flask_secret = settings.auth.flask_secret_key

        try:
            settings.environment = "production"
            settings.db.url = "postgresql://testuser:testpass@localhost:5432/testdb"
            settings.auth.jwt_secret = "a-secure-production-jwt-secret-key-32b"
            settings.auth.flask_secret_key = "a-secure-production-flask-secret-32b"

            with patch("app.core.database.check_database_connection", return_value=True):
                prod_app = create_app()
                assert prod_app is not None
        finally:
            settings.environment = orig_env
            settings.db.url = orig_db
            settings.auth.jwt_secret = orig_jwt
            settings.auth.flask_secret_key = orig_flask_secret


class TestHealthAndWarmEndpoints:
    """Verify all health check paths and warm endpoints required for production/Render."""

    def test_root_endpoint(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "online"
        assert data["app"] == "TalentFlow AI"

    def test_health_endpoint(self, app_client):
        resp = app_client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in ("healthy", "degraded")
        assert "database" in data
        assert "redis" in data

    def test_api_health_endpoint(self, app_client):
        resp = app_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in ("healthy", "degraded")

    def test_api_v1_system_health(self, app_client):
        resp = app_client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in ("healthy", "degraded")
        assert data["version"] == "v3.2.0"

    def test_api_warm_endpoint(self, app_client):
        resp = app_client.post("/api/warm")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["warmed"] is True
