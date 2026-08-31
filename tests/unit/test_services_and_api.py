"""
TalentFlow AI — Comprehensive API & Services Test Suite
"""
import pytest
import sys
import os
import json

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, BACKEND_DIR)

from app.factory import create_app
from app.core.database import Base, engine


@pytest.fixture(scope="module")
def app_client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


class TestAppFactoryAndSystem:
    def test_root_endpoint(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "online"
        assert data["app"] == "TalentFlow AI"

    def test_health_endpoint(self, app_client):
        resp = app_client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"


class TestAuthAPIEndpoints:
    def test_register_candidate(self, app_client):
        unique_email = f"candidate_{os.urandom(4).hex()}@example.com"
        payload = {
            "email": unique_email,
            "password": "Password123!",
            "username": "APICandidate",
            "role": "candidate",
            "branch": "Computer Science"
        }
        resp = app_client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "success"
        assert "token" in data
        assert "refresh_token" in data


    def test_login_and_refresh_flow(self, app_client):
        login_payload = {
            "email": "test_candidate_api@example.com",
            "password": "Password123!"
        }
        resp = app_client.post("/api/v1/auth/login", json=login_payload)
        assert resp.status_code == 200
        data = resp.get_json()
        token = data["token"]
        refresh_token = data["refresh_token"]

        # Rotate token
        ref_resp = app_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert ref_resp.status_code == 200
        ref_data = ref_resp.get_json()
        assert "token" in ref_data
        assert ref_data["token"] != token


class TestMatchingAndAIEngine:
    def test_evaluate_match_endpoint(self, app_client):
        # Register a candidate first to get token
        login_resp = app_client.post("/api/v1/auth/login", json={
            "email": "test_candidate_api@example.com",
            "password": "Password123!"
        })
        token = login_resp.get_json()["token"]

        payload = {
            "resume_text": "Experienced Python Backend Developer skilled in FastAPI, PostgreSQL, Docker, and Redis.",
            "job_description": "We need a Python Engineer with strong PostgreSQL, Docker, and API building expertise.",
            "required_skills": "Python, PostgreSQL, Docker",
            "experience_required": 2
        }
        headers = {"Authorization": f"Bearer {token}"}
        resp = app_client.post("/api/v1/matching/evaluate", json=payload, headers=headers)
        assert resp.status_code == 200
        result = resp.get_json()["result"]
        assert result["match_percentage"] >= 60
        assert "Python" in result["matched_skills"]
        assert "summary" in result["explanation"]


class TestRAGChatbotAPI:
    def test_chat_question_answering(self, app_client):
        resp = app_client.post("/api/v1/chat", json={"query": "How to make my resume ATS friendly?"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "answer" in data
        assert len(data["answer"]) > 20
