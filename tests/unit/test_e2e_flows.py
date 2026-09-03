"""
TalentFlow AI — Comprehensive End-to-End (E2E) Integration Workflows
Tests Candidate, Recruiter, and AI screening journeys end-to-end against the modular architecture.
"""
import pytest
import sys
import os
import uuid

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, BACKEND_DIR)

from app.factory import create_app  # type: ignore
from app.ai.matching_engine import compute_match  # type: ignore
from app.ai.resume_parser import extract_sections  # type: ignore
from app.ai.skill_extractor import extract_skills  # type: ignore
from app.ai.rag import rag_coach  # type: ignore


@pytest.fixture(scope="module")
def app_client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


class TestCandidateEndToEndFlow:
    """Complete Candidate Journey: Register -> Login -> Refresh Token Rotation -> Apply to Job."""

    def test_candidate_complete_lifecycle(self, app_client):
        unique_id = uuid.uuid4().hex[:8]
        email = f"candidate_e2e_{unique_id}@talentflow.ai"
        password = "SecurePassword123!"
        username = f"Candidate_{unique_id}"

        # 1. Registration
        reg_resp = app_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "username": username,
            "role": "candidate",
            "branch": "Computer Science",
            "graduation_year": 2025
        })
        assert reg_resp.status_code == 201
        reg_data = reg_resp.get_json()
        assert reg_data["status"] == "success"
        assert reg_data["role"] == "candidate"
        initial_token = reg_data["token"]
        refresh_token = reg_data["refresh_token"]

        # 2. Login
        login_resp = app_client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_resp.status_code == 200
        login_data = login_resp.get_json()
        assert login_data["status"] == "success"
        assert login_data["email"] == email
        access_token = login_data["token"]
        new_refresh = login_data["refresh_token"]

        # 3. Token Rotation via Refresh Endpoint
        refresh_resp = app_client.post("/api/v1/auth/refresh", json={
            "refresh_token": new_refresh
        })
        assert refresh_resp.status_code == 200
        refreshed_data = refresh_resp.get_json()
        assert "token" in refreshed_data
        assert "refresh_token" in refreshed_data
        rotated_access = refreshed_data["token"]
        rotated_refresh = refreshed_data["refresh_token"]
        assert rotated_access != access_token

        # 4. Old refresh token is revoked and cannot be reused
        replay_resp = app_client.post("/api/v1/auth/refresh", json={
            "refresh_token": new_refresh
        })
        assert replay_resp.status_code in (401, 403, 422)

        # 5. Access protected candidate endpoint using the rotated access token
        headers = {"Authorization": f"Bearer {rotated_access}"}
        eval_resp = app_client.post("/api/v1/matching/evaluate", json={
            "resume_text": "Python Software Engineer with PostgreSQL and Docker experience",
            "job_description": "We need a Python developer experienced in databases and containerization",
            "required_skills": "Python, PostgreSQL, Docker",
            "experience_required": 2
        }, headers=headers)
        assert eval_resp.status_code == 200
        eval_data = eval_resp.get_json()
        assert eval_data["status"] == "success"
        assert eval_data["result"]["match_percentage"] > 50


class TestRecruiterEndToEndFlow:
    """Complete Recruiter Journey: Login/Register HR -> Create Job -> List Jobs -> View Applications -> Ranking."""

    def test_recruiter_complete_lifecycle(self, app_client):
        unique_id = uuid.uuid4().hex[:8]
        email = f"recruiter_e2e_{unique_id}@talentflow.ai"
        password = "SecurePassword123!"
        username = f"HR_{unique_id}"

        # 1. Register Recruiter (role="hr")
        reg_resp = app_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "username": username,
            "role": "hr",
            "company_name": "TalentFlow Enterprise"
        })
        assert reg_resp.status_code == 201
        hr_token = reg_resp.get_json()["token"]
        headers = {"Authorization": f"Bearer {hr_token}"}

        # 2. Create Job Opening
        create_resp = app_client.post("/api/v1/jobs", json={
            "title": f"Lead AI Engineer {unique_id}",
            "description": "Lead the development of generative AI pipelines using SentenceTransformers, FAISS, and PostgreSQL.",
            "required_skills": "Python, PyTorch, FAISS, PostgreSQL, Docker",
            "experience_required": 4,
            "location": "Remote",
            "job_type": "Full-time",
            "salary": "$160,000 - $190,000"
        }, headers=headers)
        assert create_resp.status_code == 201
        job_data = create_resp.get_json()["job"]
        job_id = job_data["id"]
        assert job_data["title"] == f"Lead AI Engineer {unique_id}"

        # 3. List Jobs (Public or Recruiter)
        list_resp = app_client.get("/api/v1/jobs")
        assert list_resp.status_code == 200
        jobs = list_resp.get_json()["jobs"]
        assert any(j["id"] == job_id for j in jobs)

        # 4. View Job Applications (HR Protected)
        apps_resp = app_client.get(f"/api/v1/jobs/{job_id}/applications", headers=headers)
        assert apps_resp.status_code == 200
        assert isinstance(apps_resp.get_json()["applications"], list)

        # 5. Check Candidate Rankings for Job (HR Protected)
        rank_resp = app_client.get(f"/api/v1/matching/rankings/{job_id}", headers=headers)
        assert rank_resp.status_code == 200
        assert "rankings" in rank_resp.get_json()


class TestAIPipelineEndToEndFlow:
    """Complete AI Pipeline: Resume Text + JD -> Parse -> Skill Extraction -> Matching -> Explanation -> RAG Q&A."""

    def test_ai_pipeline_end_to_end(self):
        resume_text = """
        John Applicant
        Email: john.applicant@example.com
        
        EXPERIENCE
        Senior Backend Engineer — TechCorp (4 years of experience)
        - Developed high-throughput microservices using Python, FastAPI, and PostgreSQL.
        - Orchestrated container deployments with Docker and Kubernetes.
        - Designed Redis caching layers improving query performance by 45%.
        
        SKILLS
        Python, FastAPI, PostgreSQL, Docker, Kubernetes, Redis, Machine Learning, Git
        
        EDUCATION
        Bachelor of Science in Computer Science, State University
        """

        job_description = """
        We are seeking a Senior Python Engineer with 3+ years experience.
        Required Skills: Python, PostgreSQL, Docker, Redis.
        Key Responsibilities: Build robust microservices and optimize database operations.
        Degree: Bachelor's degree in Computer Science or equivalent.
        """

        # 1. Section Extraction
        sections = extract_sections(resume_text)
        assert "experience" in sections or "skills" in sections

        # 2. Skill Extraction
        extracted_skills = extract_skills(resume_text)
        assert "Python" in extracted_skills
        assert "PostgreSQL" in extracted_skills
        assert "Docker" in extracted_skills

        # 3. Multidimensional Matching & Sigmoid Calibration
        match_result = compute_match(
            resume_text=resume_text,
            job_description=job_description,
            required_skills_str="Python, PostgreSQL, Docker, Redis",
            experience_required_years=3
        )

        assert match_result["final_score"] >= 0.70
        assert match_result["match_percentage"] >= 70
        assert "Python" in match_result["matched_skills"]
        assert "PostgreSQL" in match_result["matched_skills"]
        assert "Docker" in match_result["matched_skills"]
        assert "summary" in match_result["explanation"]
        assert len(match_result["explanation"]["summary"]) > 20

        # 4. RAG Assistant Query & Knowledge Retrieval
        rag_res = rag_coach.answer_query("How to make my resume ATS friendly?")
        assert rag_res["grounded"] is True
        assert len(rag_res["answer"]) > 20
        assert len(rag_res["sources"]) > 0
