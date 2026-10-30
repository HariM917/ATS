"""
TalentFlow AI — Step 3: Complete End-to-End TalentFlow Verification

Tests the complete integrated pipeline:
Resume (PDF/DOCX/TXT)
       ↓
/api/v1/resumes/upload
       ↓
Text extraction
       ↓
OccupationalClassifierService
       ↓
22-class prediction
       ↓
Confidence + margin
       ↓
Human-review flag
       ↓
Resume analysis
       ↓
/api/v1/matching/evaluate
       ↓
ATS / matching results
       ↓
Recruiter dashboard routing
"""

import io
import uuid
import pytest
from app.factory import create_app  # type: ignore
from app.services.occupational_classifier import CLASSES_22, MODEL_VERSION, TAXONOMY_VERSION  # type: ignore


@pytest.fixture(scope="module")
def app_client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_candidate(app_client):
    """Registers and authenticates a test candidate."""
    uid = uuid.uuid4().hex[:8]
    email = f"candidate_{uid}@talentflow.ai"
    password = "SecurePassword123!"
    username = f"Candidate_{uid}"

    reg_resp = app_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "username": username,
        "role": "candidate",
        "branch": "Computer Science",
        "graduation_year": 2024
    })
    assert reg_resp.status_code == 201
    token = reg_resp.get_json()["token"]
    return {
        "email": email,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


class TestEndToEndTalentFlowPipeline:
    """Verifies the complete Step 3 TalentFlow verification journey."""

    def test_full_pipeline_clear_candidate(self, app_client, auth_candidate):
        """
        Flow for a clear candidate (Information Technology):
        1. Upload resume -> /api/v1/resumes/upload
        2. Verify text extraction & 22-class classification
        3. Verify high confidence & margin, review_required == False
        4. Query /api/v1/resumes/<resume_id>/analysis
        5. Evaluate against job -> /api/v1/matching/evaluate
        6. Verify ATS score and matching results
        """
        resume_content = (
            "Senior Backend Engineer with 8 years of experience in Python, FastAPI, Django, "
            "PostgreSQL, microservices, Docker, Kubernetes, and AWS architecture. "
            "Led backend architecture and scalable distributed database systems."
        )
        data = {
            "file": (io.BytesIO(resume_content.encode("utf-8")), "senior_engineer_resume.txt")
        }

        # 1. Upload resume
        upload_resp = app_client.post(
            "/api/v1/resumes/upload",
            data=data,
            headers=auth_candidate["headers"],
            content_type="multipart/form-data"
        )
        assert upload_resp.status_code == 201
        upload_json = upload_resp.get_json()
        assert upload_json["status"] == "success"
        resume_obj = upload_json["resume"]
        resume_id = resume_obj["id"]

        # 2. Check Occupational Classification in upload response
        occ = resume_obj.get("occupational_classification")
        assert occ is not None
        assert occ["predicted_role"] == "INFORMATION-TECHNOLOGY"
        assert occ["predicted_role"] in CLASSES_22
        assert occ["confidence"] > 0.40
        assert occ["runner_up_role"] in CLASSES_22
        assert occ["predicted_role"] != occ["runner_up_role"]
        assert occ["model_version"] == MODEL_VERSION
        assert occ["taxonomy_version"] == TAXONOMY_VERSION
        assert occ["review_required"] is False

        # 3. Query analysis endpoint: /api/v1/resumes/<id>/analysis
        analysis_resp = app_client.get(
            f"/api/v1/resumes/{resume_id}/analysis",
            headers=auth_candidate["headers"]
        )
        assert analysis_resp.status_code == 200
        analysis_json = analysis_resp.get_json()
        assert analysis_json["status"] == "success"
        persisted_analysis = analysis_json["analysis"]
        health_occ = persisted_analysis.get("health_analysis", {}).get("occupational_classification")
        assert health_occ is not None
        assert health_occ["predicted_role"] == "INFORMATION-TECHNOLOGY"
        assert health_occ["review_required"] is False

        # 4. Job Matching Evaluation: /api/v1/matching/evaluate
        eval_payload = {
            "resume_text": resume_content,
            "job_description": (
                "Seeking a Senior Python Backend Engineer to build scalable microservices "
                "with PostgreSQL, Docker, and AWS."
            ),
            "required_skills": "Python, FastAPI, PostgreSQL, Docker, AWS",
            "experience_required": 5
        }
        eval_resp = app_client.post(
            "/api/v1/matching/evaluate",
            json=eval_payload,
            headers=auth_candidate["headers"]
        )
        assert eval_resp.status_code == 200
        eval_json = eval_resp.get_json()
        assert eval_json["status"] == "success"
        result = eval_json["result"]
        assert result["final_score"] >= 0.70
        assert result["match_percentage"] >= 70
        assert "occupational_classification" in result
        assert result["occupational_classification"]["predicted_role"] == "INFORMATION-TECHNOLOGY"
        assert result["occupational_classification"]["review_required"] is False

    def test_full_pipeline_ambiguous_candidate_triggers_recruiter_review(self, app_client, auth_candidate):
        """
        Flow for an ambiguous/dual-role candidate (Arts & High School Teacher):
        Verifies that thin margin or low confidence reliably triggers the
        Human-Review Flag (review_required = True) for recruiter dashboard routing.
        """
        # Ambiguous blend between Arts / High School Art Teacher
        ambiguous_resume_content = (
            "Art Teacher and Fine Arts Instructor. Conducted painting, sculpture, "
            "and gallery workshops in high school education while exhibiting contemporary art."
        )
        data = {
            "file": (io.BytesIO(ambiguous_resume_content.encode("utf-8")), "ambiguous_art_teacher.txt")
        }

        # 1. Upload ambiguous resume
        upload_resp = app_client.post(
            "/api/v1/resumes/upload",
            data=data,
            headers=auth_candidate["headers"],
            content_type="multipart/form-data"
        )
        assert upload_resp.status_code == 201
        upload_json = upload_resp.get_json()
        occ = upload_json["resume"]["occupational_classification"]

        # 2. Both predicted and runner-up must be valid canonical classes
        assert occ["predicted_role"] in ("ARTS", "TEACHER")
        assert occ["runner_up_role"] in ("ARTS", "TEACHER", "DESIGNER")
        assert occ["model_version"] == MODEL_VERSION

        # 3. Safety review rule check: thin margin or dual role flag
        # If margin < 0.15 or confidence < 0.40, review_required must be True
        if occ["confidence"] < 0.40 or occ["margin"] < 0.15:
            assert occ["review_required"] is True
            assert len(occ["review_reasons"]) > 0

        # 4. Job Matching Evaluation on ambiguous resume
        eval_payload = {
            "resume_text": ambiguous_resume_content,
            "job_description": "Secondary School Art Teacher for grades 9-12 curriculum.",
            "required_skills": "Teaching, Curriculum Design, Fine Arts",
            "experience_required": 2
        }
        eval_resp = app_client.post(
            "/api/v1/matching/evaluate",
            json=eval_payload,
            headers=auth_candidate["headers"]
        )
        assert eval_resp.status_code == 200
        eval_occ = eval_resp.get_json()["result"]["occupational_classification"]
        assert eval_occ["predicted_role"] in ("ARTS", "TEACHER")
        assert "review_required" in eval_occ
