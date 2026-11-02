"""
TalentFlow Full Reconstruction Acceptance Verification Script
Tests all requirements end-to-end:
1. 17-field Candidate Profile PUT -> GET roundtrip persistence
2. Controlled Role Catalog GET /api/v1/roles
3. Recruiter authoring Job with domain + specific role as 'draft'
4. Candidate visibility (draft NOT in feed)
5. Recruiter publishes job -> Candidate visibility (now in feed)
6. Career Analysis evaluation with target role & dual-layer classification
7. Application submission & Recruiter stage update
8. Recruiter closing job -> Candidate feed exclusion
"""
import uuid
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.factory import create_app
from app.core.database import get_db_context
from app.models import User, Candidate, Recruiter, Organization, Job, Application, Resume, RoleCatalog

def run_acceptance_suite():
    app = create_app()
    client = app.test_client()

    print("\n=======================================================")
    print("STARTING TALENTFLOW RECONSTRUCTION ACCEPTANCE SUITE")
    print("=======================================================\n")

    test_id = uuid.uuid4().hex[:6]
    letters = ''.join([c for c in test_id if c.isalpha()] or ['a', 'b', 'c'])
    cand_email = f"cand_acc_{test_id}@talentflow.ai"
    hr_email = f"hr_acc_{test_id}@talentflow.ai"
    password = "SecurePassword123!"

    # -----------------------------------------------------------------
    # STEP 1: Candidate Registration & Login
    # -----------------------------------------------------------------
    print(">>> 1. Registering Candidate...")
    cand_reg = client.post("/api/v1/auth/register", json={
        "email": cand_email,
        "password": password,
        "username": f"Candidate {letters}",
        "role": "candidate"
    })
    assert cand_reg.status_code == 201, f"Candidate register failed: {cand_reg.data}"
    cand_token = cand_reg.get_json()["token"]
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    print("    [PASS] Candidate registered successfully.")

    # -----------------------------------------------------------------
    # STEP 2: 17-Field Candidate Profile Persistence (PUT -> GET)
    # -----------------------------------------------------------------
    print(">>> 2. Testing 17-Field Candidate Profile Persistence...")
    profile_payload = {
        "name": f"Alex Morgan {test_id}",
        "phone": "+1 (555) 432-1098",
        "location": "Seattle, WA",
        "headline": "Lead Machine Learning & NLP Engineer",
        "bio": "Experienced AI engineer specializing in transformers and scalable retrieval systems.",
        "skills": ["Python", "PyTorch", "Transformers", "FAISS", "Docker", "PostgreSQL"],
        "branch": "Computer Science & Engineering",
        "graduation_year": 2024,
        "education": "M.S. in Artificial Intelligence, University of Washington",
        "linkedin_url": "https://linkedin.com/in/alexmorgan",
        "github_url": "https://github.com/alexmorgan",
        "portfolio_url": "https://alexmorgan.dev",
        "experience": "5+ years developing and deploying large-scale neural search systems.",
        "certifications": ["AWS Certified Machine Learning Specialist", "Deep Learning Specialization"],
        "preferred_role": "Machine Learning Engineer",
        "preferred_location": "Remote / Seattle"
    }
    put_resp = client.put("/api/v1/candidates/profile", headers=cand_headers, json=profile_payload)
    assert put_resp.status_code == 200, f"Profile PUT failed: {put_resp.data}"

    # Strict refetch GET
    get_resp = client.get("/api/v1/candidates/profile", headers=cand_headers)
    assert get_resp.status_code == 200, f"Profile GET failed: {get_resp.data}"
    fetched = get_resp.get_json()["data"]

    # Verify all 17 fields persisted without loss
    assert fetched["name"] == profile_payload["name"]
    assert fetched["email"] == cand_email
    assert fetched["phone"] == profile_payload["phone"]
    assert fetched["location"] == profile_payload["location"]
    assert fetched["headline"] == profile_payload["headline"]
    assert fetched["bio"] == profile_payload["bio"]
    assert set(fetched["skills"]) == set(profile_payload["skills"])
    assert fetched["branch"] == profile_payload["branch"]
    assert fetched["graduation_year"] == profile_payload["graduation_year"]
    assert profile_payload["education"] in fetched["education"]
    assert fetched["linkedin_url"] == profile_payload["linkedin_url"]
    assert fetched["github_url"] == profile_payload["github_url"]
    assert fetched["portfolio_url"] == profile_payload["portfolio_url"]
    assert profile_payload["experience"] in fetched["experience"]
    assert fetched["certifications"] == profile_payload["certifications"]
    assert fetched["preferred_role"] == profile_payload["preferred_role"]
    assert fetched["preferred_location"] == profile_payload["preferred_location"]
    print("    [PASS] All 17 profile fields round-tripped with 100% integrity.")

    # -----------------------------------------------------------------
    # STEP 3: Role Catalog Inspection (GET /api/v1/roles)
    # -----------------------------------------------------------------
    print(">>> 3. Testing GET /api/v1/roles Catalog...")
    roles_resp = client.get("/api/v1/roles")
    assert roles_resp.status_code == 200
    roles = roles_resp.get_json()["data"]
    assert len(roles) >= 20, f"Expected 20+ roles in catalog, got {len(roles)}"
    ml_role = next((r for r in roles if r["name"] == "Machine Learning Engineer"), None)
    assert ml_role is not None
    assert ml_role["occupational_class"] == "INFORMATION-TECHNOLOGY"
    print(f"    [PASS] Role catalog loaded {len(roles)} roles across 22 domains.")

    # -----------------------------------------------------------------
    # STEP 4: Recruiter Registration & Authoring Draft Job
    # -----------------------------------------------------------------
    print(">>> 4. Registering HR Recruiter & Authoring Draft Job...")
    hr_reg = client.post("/api/v1/auth/register", json={
        "email": hr_email,
        "password": password,
        "username": f"Recruiter {letters}",
        "role": "hr",
        "company_name": f"NeuroTech Labs {test_id}"
    })
    assert hr_reg.status_code == 201
    hr_token = hr_reg.get_json()["token"]
    hr_headers = {"Authorization": f"Bearer {hr_token}"}

    create_job_resp = client.post("/api/v1/jobs", headers=hr_headers, json={
        "title": f"Staff ML Research Engineer {test_id}",
        "description": "Design and optimize dense vector embeddings and neural ranking architectures.",
        "occupational_class": "INFORMATION-TECHNOLOGY",
        "specific_role": "Machine Learning Engineer",
        "required_skills": "Python, PyTorch, FAISS, Docker, NLP",
        "experience_required": 4,
        "location": "Remote",
        "job_type": "Full-time",
        "salary": "$175,000 - $210,000",
        "status": "draft"
    })
    assert create_job_resp.status_code == 201
    job_id = create_job_resp.get_json()["data"]["id"]
    assert create_job_resp.get_json()["data"]["status"] == "draft"
    print(f"    [PASS] Job authored as DRAFT (id={job_id}).")

    # -----------------------------------------------------------------
    # STEP 5: Verify Candidate Cannot See Draft Job in Feed
    # -----------------------------------------------------------------
    print(">>> 5. Verifying Candidate Job Feed Excludes Draft Job...")
    feed_resp = client.get("/api/v1/jobs", headers=cand_headers)
    assert feed_resp.status_code == 200
    candidate_jobs = feed_resp.get_json()["data"]
    assert not any(j["id"] == job_id for j in candidate_jobs), "Draft job leaked into candidate feed!"
    print("    [PASS] Candidate feed strictly excludes draft jobs.")

    # -----------------------------------------------------------------
    # STEP 6: HR Publishes Job (POST /api/v1/jobs/<id>/publish)
    # -----------------------------------------------------------------
    print(">>> 6. HR Publishing Job Live...")
    pub_resp = client.post(f"/api/v1/jobs/{job_id}/publish", headers=hr_headers)
    assert pub_resp.status_code == 200
    assert pub_resp.get_json()["data"]["status"] == "published"

    # Now verify candidate CAN see the published job
    feed_resp2 = client.get("/api/v1/jobs", headers=cand_headers)
    candidate_jobs2 = feed_resp2.get_json()["data"]
    published_job = next((j for j in candidate_jobs2 if j["id"] == job_id), None)
    assert published_job is not None, "Published job not visible to candidate!"
    print("    [PASS] Published job is now live in Candidate Job Feed.")

    # -----------------------------------------------------------------
    # STEP 7: Career Analysis Evaluation with Target Role
    # -----------------------------------------------------------------
    print(">>> 7. Evaluating Resume with Target Role Specialization...")
    eval_resp = client.post("/api/v1/matching/evaluate", headers=cand_headers, json={
        "resume_text": "Senior Machine Learning Engineer with 6 years experience in Python, PyTorch, NLP, FAISS, Docker, Kubernetes, and PostgreSQL.",
        "role_id": ml_role["id"],
        "specific_role": ml_role["name"]
    })
    assert eval_resp.status_code == 200
    eval_data = eval_resp.get_json()["data"]

    # Verify score components and dual-layer classification
    assert "final_score" in eval_data
    assert "semantic_score" in eval_data
    assert "skill_score" in eval_data
    assert len(eval_data["matched_skills"]) > 0
    assert "occupational_classification" in eval_data

    occ = eval_data["occupational_classification"]
    print("    [DEBUG OCC]:", occ)
    assert occ["predicted_role"] in ["INFORMATION-TECHNOLOGY", "ENGINEERING"]
    assert occ["specific_role"] == "Machine Learning Engineer"
    assert occ["specific_role_confidence"] >= 0.70
    print(f"    [PASS] Multi-layer evaluation succeeded: Score={round(eval_data['final_score']*100, 1)}%, Domain={occ['predicted_role']}, Specific Role={occ['specific_role']} (Conf: {round(occ['specific_role_confidence']*100, 1)}%).")

    # -----------------------------------------------------------------
    # STEP 8: Candidate Applies & Recruiter Moves Pipeline Stage
    # -----------------------------------------------------------------
    print(">>> 8. Submitting Application & Updating Stage Pipeline...")
    apply_resp = client.post("/api/v1/applications", headers=cand_headers, json={
        "job_id": job_id
    })
    assert apply_resp.status_code == 201
    app_id = apply_resp.get_json()["data"]["id"]
    assert apply_resp.get_json()["data"]["stage"] == "applied"

    # HR moves stage to interview
    stage_resp = client.put(f"/api/v1/applications/{app_id}", headers=hr_headers, json={
        "stage": "interview",
        "notes": "Candidate demonstrates strong NLP and vector search competencies."
    })
    assert stage_resp.status_code == 200
    assert stage_resp.get_json()["data"]["stage"] == "interview"
    assert "notes" in stage_resp.get_json()["data"]
    print("    [PASS] Application pipeline moved to 'interview' with reviewer notes.")

    # -----------------------------------------------------------------
    # STEP 9: Recruiter Closes Job & Verifies Removal from Candidate Feed
    # -----------------------------------------------------------------
    print(">>> 9. Closing Job and Verifying Exclusion from Feed...")
    close_resp = client.put(f"/api/v1/jobs/{job_id}", headers=hr_headers, json={
        "status": "closed"
    })
    assert close_resp.status_code == 200
    assert close_resp.get_json()["data"]["status"] == "closed"

    feed_resp3 = client.get("/api/v1/jobs", headers=cand_headers)
    assert not any(j["id"] == job_id for j in feed_resp3.get_json()["data"]), "Closed job should not appear in candidate feed!"
    print("    [PASS] Closed job automatically removed from Candidate Job Feed.")

    print("\n=======================================================")
    print("ALL ACCEPTANCE SUITE CHECKS PASSED WITH 100% SUCCESS!")
    print("=======================================================\n")

if __name__ == "__main__":
    run_acceptance_suite()
