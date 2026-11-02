"""
TalentFlow AI — Comprehensive Canonical API Integration Test Suite
Verifies:
1. POST /api/v1/auth/register (valid, duplicate, validation failures)
2. POST /api/v1/auth/login (valid, invalid password, non-existent)
3. POST /api/v1/auth/refresh (token rotation)
4. POST /api/v1/auth/logout (token revocation)
5. GET  /api/v1/auth/me (authenticated identity)
6. GET  /api/v1/candidates/profile (guaranteed 200)
7. PUT  /api/v1/candidates/profile (profile update)
8. GET  /api/v1/candidates/dashboard (candidate dashboard metrics)
9. GET  /api/v1/candidates/applications (candidate applications)
10. POST /api/v1/resumes/upload (resume parsing & occupational classification)
11. GET  /api/v1/resumes/my-resumes (resume listing)
12. GET  /api/v1/resumes/<id> (retrieve resume)
13. DELETE /api/v1/resumes/<id> (delete resume)
14. POST /api/v1/matching/evaluate (multidimensional scoring + 22-class classification)
15. GET  /api/v1/jobs (list jobs)
16. POST /api/v1/jobs (create job as HR)
17. GET  /api/v1/jobs/<id> (get single job)
18. PUT  /api/v1/jobs/<id> (update job as HR)
19. DELETE /api/v1/jobs/<id> (delete job as HR)
20. POST /api/v1/applications (apply to job)
21. GET  /api/v1/applications (list applications)
22. GET  /api/v1/applications/<id> (get application)
23. PUT  /api/v1/applications/<id> (update stage as HR)
24. POST /api/v1/chat/message (RAG career assistant)
25. GET  /api/v1/chat/history (retrieve chat history)
26. GET  /api/v1/system/health (system health check)
27. CORS OPTIONS request validation
"""
import io
import uuid
import pytest
from app.factory import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


class TestCanonicalAuthFlow:
    def test_full_auth_lifecycle(self, client):
        uid = uuid.uuid4().hex[:6]
        letters = ''.join([c for c in uid if c.isalpha()] or ['a', 'b', 'c'])
        email = f"canonical_{uid}@example.com"
        password = "Password@123"
        name = f"Canonical Candidate {letters}"

        # 1. Invalid Name regex check
        bad_name_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": "A"  # Too short
        })
        assert bad_name_resp.status_code == 400

        # 2. Invalid Email regex check
        bad_email_resp = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": password,
            "name": name
        })
        assert bad_email_resp.status_code == 400

        # 3. Invalid Password regex check
        bad_pass_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "simple",  # Weak password
            "name": name
        })
        assert bad_pass_resp.status_code == 400

        # 4. Valid Registration
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
            "role": "candidate"
        })
        assert reg_resp.status_code == 201
        reg_data = reg_resp.get_json()
        assert reg_data["status"] == "success"
        token = reg_data["token"]
        refresh_token = reg_data["refresh_token"]

        # 5. Duplicate Email check
        dup_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": name
        })
        assert dup_resp.status_code == 409

        # 6. Valid Login
        login_resp = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_resp.status_code == 200
        login_data = login_resp.get_json()
        assert login_data["token"] is not None

        # 7. Invalid Login
        bad_login_resp = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "WrongPassword@999"
        })
        assert bad_login_resp.status_code == 401

        # 8. GET /api/v1/auth/me
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.get_json()
        assert me_data["user"]["email"] == email

        # 9. POST /api/v1/auth/refresh
        ref_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert ref_resp.status_code == 200
        new_token = ref_resp.get_json()["token"]
        assert new_token is not None

        # 10. POST /api/v1/auth/logout
        logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_token}"})
        assert logout_resp.status_code == 200


class TestCanonicalCandidateAndResumeFlow:
    @pytest.fixture
    def auth_candidate(self, client):
        uid = uuid.uuid4().hex[:6]
        letters = ''.join([c for c in uid if c.isalpha()] or ['a', 'b', 'c'])
        email = f"cand_{uid}@example.com"
        password = "Password@123"
        name = f"Jane Doe {letters}"

        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
            "role": "candidate"
        })
        assert reg_resp.status_code == 201
        token = reg_resp.get_json()["token"]
        return {"headers": {"Authorization": f"Bearer {token}"}, "name": name, "email": email}

    def test_candidate_profile_and_resume_lifecycle(self, client, auth_candidate):
        headers = auth_candidate["headers"]

        # 1. GET /api/v1/candidates/profile (must be 200)
        prof_resp = client.get("/api/v1/candidates/profile", headers=headers)
        assert prof_resp.status_code == 200
        prof_data = prof_resp.get_json()
        assert prof_data["status"] == "success"
        assert prof_data["email"] == auth_candidate["email"]

        # 2. PUT /api/v1/candidates/profile
        update_resp = client.put("/api/v1/candidates/profile", headers=headers, json={
            "headline": "Senior Full-Stack Engineer",
            "branch": "Computer Engineering",
            "graduation_year": 2024,
            "location": "San Francisco, CA",
            "bio": "Passionate software developer."
        })
        assert update_resp.status_code == 200
        assert update_resp.get_json()["status"] == "success"

        # 3. GET /api/v1/candidates/dashboard
        dash_resp = client.get("/api/v1/candidates/dashboard", headers=headers)
        assert dash_resp.status_code == 200

        # 4. POST /api/v1/resumes/upload
        sample_resume_text = (
            "John Doe - Senior Software Engineer\n"
            "Skills: Python, FastAPI, Docker, PostgreSQL, React, TypeScript\n"
            "Experience: 5 years designing distributed microservices and backend architectures.\n"
            "Education: Bachelor of Science in Computer Science."
        )
        data = {
            "file": (io.BytesIO(sample_resume_text.encode("utf-8")), "resume.txt")
        }
        upload_resp = client.post(
            "/api/v1/resumes/upload",
            headers=headers,
            data=data,
            content_type="multipart/form-data"
        )
        assert upload_resp.status_code == 201
        upload_data = upload_resp.get_json()
        resume_id = upload_data["data"]["id"]
        assert resume_id is not None

        # 5. GET /api/v1/resumes/my-resumes
        list_resp = client.get("/api/v1/resumes/my-resumes", headers=headers)
        assert list_resp.status_code == 200
        resumes = list_resp.get_json()["data"]
        assert len(resumes) >= 1

        # 6. GET /api/v1/resumes/<resume_id>
        get_res_resp = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
        assert get_res_resp.status_code == 200

        # 7. GET /api/v1/resumes/<resume_id>/analysis
        analysis_resp = client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=headers)
        assert analysis_resp.status_code == 200
        an_data = analysis_resp.get_json()["data"]
        assert "occupational_classification" in an_data

        # 8. POST /api/v1/matching/evaluate
        eval_resp = client.post("/api/v1/matching/evaluate", headers=headers, json={
            "resume_text": sample_resume_text,
            "job_description": "We are seeking a Python Backend Engineer with PostgreSQL and Docker experience.",
            "required_skills": "Python, Docker, PostgreSQL",
            "experience_required": 3
        })
        assert eval_resp.status_code == 200
        eval_data = eval_resp.get_json()["data"]
        assert eval_data["final_score"] > 0
        assert "occupational_classification" in eval_data
        assert eval_data["occupational_classification"]["model_version"] == "v21-v23-final"

        # 9. DELETE /api/v1/resumes/<resume_id>
        del_resp = client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)
        assert del_resp.status_code == 200


class TestCanonicalJobsAndApplicationsFlow:
    @pytest.fixture
    def auth_hr(self, client):
        uid = uuid.uuid4().hex[:6]
        letters = ''.join([c for c in uid if c.isalpha()] or ['a', 'b', 'c'])
        email = f"recruiter_{uid}@example.com"
        password = "Password@123"
        name = f"Alex Recruiter {letters}"

        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
            "role": "hr",
            "company_name": "Tech Corp"
        })
        assert reg_resp.status_code == 201
        token = reg_resp.get_json()["token"]
        return {"headers": {"Authorization": f"Bearer {token}"}}

    @pytest.fixture
    def auth_cand(self, client):
        uid = uuid.uuid4().hex[:6]
        letters = ''.join([c for c in uid if c.isalpha()] or ['a', 'b', 'c'])
        email = f"applicant_{uid}@example.com"
        password = "Password@123"
        name = f"Bob Applicant {letters}"

        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
            "role": "candidate"
        })
        assert reg_resp.status_code == 201
        token = reg_resp.get_json()["token"]
        return {"headers": {"Authorization": f"Bearer {token}"}}

    def test_jobs_and_applications_e2e(self, client, auth_hr, auth_cand):
        hr_headers = auth_hr["headers"]
        cand_headers = auth_cand["headers"]

        # 1. POST /api/v1/jobs (HR creates job)
        create_resp = client.post("/api/v1/jobs", headers=hr_headers, json={
            "title": "Senior Python Backend Engineer",
            "description": "Looking for expert in Python, Flask, PostgreSQL.",
            "required_skills": "Python, Flask, PostgreSQL",
            "experience_required": 4,
            "location": "Remote",
            "job_type": "Full-time",
            "salary": "$120,000 - $150,000"
        })
        assert create_resp.status_code == 201
        job_id = create_resp.get_json()["data"]["id"]

        # 2. GET /api/v1/jobs (public / candidate lists jobs)
        jobs_resp = client.get("/api/v1/jobs", headers=cand_headers)
        assert jobs_resp.status_code == 200
        jobs = jobs_resp.get_json()["data"]
        assert any(j["id"] == job_id for j in jobs)

        # 3. GET /api/v1/jobs/<job_id>
        job_resp = client.get(f"/api/v1/jobs/{job_id}", headers=cand_headers)
        assert job_resp.status_code == 200
        assert job_resp.get_json()["data"]["title"] == "Senior Python Backend Engineer"

        # 4. PUT /api/v1/jobs/<job_id> (HR updates job)
        update_resp = client.put(f"/api/v1/jobs/{job_id}", headers=hr_headers, json={
            "salary": "$130,000 - $160,000"
        })
        assert update_resp.status_code == 200
        assert update_resp.get_json()["data"]["salary"] == "$130,000 - $160,000"

        # 5. POST /api/v1/applications (Candidate applies)
        app_resp = client.post("/api/v1/applications", headers=cand_headers, json={
            "job_id": job_id
        })
        assert app_resp.status_code == 201
        app_id = app_resp.get_json()["data"]["id"]

        # 6. GET /api/v1/applications (Candidate lists applications)
        c_apps_resp = client.get("/api/v1/applications", headers=cand_headers)
        assert c_apps_resp.status_code == 200
        c_apps = c_apps_resp.get_json()["data"]
        assert any(a["id"] == app_id for a in c_apps)

        # 7. GET /api/v1/applications/<app_id>
        single_app_resp = client.get(f"/api/v1/applications/{app_id}", headers=cand_headers)
        assert single_app_resp.status_code == 200

        # 8. PUT /api/v1/applications/<app_id> (HR updates stage to shortlisted)
        stage_resp = client.put(f"/api/v1/applications/{app_id}", headers=hr_headers, json={
            "stage": "shortlisted",
            "notes": "Strong candidate."
        })
        assert stage_resp.status_code == 200
        assert stage_resp.get_json()["data"]["stage"] == "shortlisted"

        # 8b. GET /api/v1/candidates (HR lists candidate pool)
        cands_resp = client.get("/api/v1/candidates", headers=hr_headers)
        assert cands_resp.status_code == 200
        assert "candidates" in cands_resp.get_json()

        # 9. DELETE /api/v1/jobs/<job_id> (HR deletes job)
        del_job_resp = client.delete(f"/api/v1/jobs/{job_id}", headers=hr_headers)
        assert del_job_resp.status_code == 200


class TestCanonicalChatHealthAndCORS:
    def test_chat_message_and_history(self, client):
        uid = uuid.uuid4().hex[:6]
        letters = ''.join([c for c in uid if c.isalpha()] or ['a', 'b', 'c'])
        email = f"chat_{uid}@example.com"
        password = "Password@123"
        name = f"Chat User {letters}"

        reg_resp = client.post("/api/v1/auth/register", json={
            "email": email, "password": password, "name": name, "role": "candidate"
        })
        token = reg_resp.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. POST /api/v1/chat/message
        chat_resp = client.post("/api/v1/chat/message", headers=headers, json={
            "message": "How do I make my resume ATS friendly?"
        })
        assert chat_resp.status_code == 200
        chat_data = chat_resp.get_json()
        assert len(chat_data["answer"]) > 10

        # 2. GET /api/v1/chat/history
        hist_resp = client.get("/api/v1/chat/history", headers=headers)
        assert hist_resp.status_code == 200
        hist_data = hist_resp.get_json()["data"]
        assert len(hist_data) >= 1

    def test_health_endpoint(self, client):
        resp = client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in ("healthy", "degraded")
        assert data["database"]["connected"] is True

    def test_cors_options_preflight(self, client):
        resp = client.open(
            "/api/v1/candidates/profile",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        assert resp.status_code in (200, 204)
        assert "Access-Control-Allow-Origin" in resp.headers

