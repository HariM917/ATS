"""
TalentFlow AI — Unit & Integration Tests for 22-Class Occupational Classifier Service.

Tests:
1. Model loading & bundle validation
2. Missing model failure handling (ModelNotLoadedError)
3. 22-class canonical taxonomy verification
4. Output schema & contract conformity
5. Strict probability normalization
6. Accurate Top-2 margin calculation
7. Recruiter safety rules (low-confidence flag: < 0.40)
8. Recruiter safety rules (thin-margin flag: < 0.15)
9. Recruiter safety rules (clear decision: confidence >= 0.40 and margin >= 0.15)
10. Empty text handling
11. Batch prediction functionality
12. Integration with /api/v1/matching/evaluate endpoint
"""

import pytest
from app.services.occupational_classifier import (
    OccupationalClassifierService,
    ModelNotLoadedError,
    CLASSES_22,
    MODEL_VERSION,
    TAXONOMY_VERSION,
    MIN_CONFIDENCE_THRESHOLD,
    MIN_MARGIN_THRESHOLD,
    get_occupational_classifier
)


@pytest.fixture
def classifier_service():
    """Fixture providing initialized occupational classifier."""
    service = OccupationalClassifierService()
    service.load_model()
    return service


class TestOccupationalClassifierModelLoading:
    """Test suite for model loading and error handling."""

    def test_model_loading_success(self, classifier_service):
        assert classifier_service._is_loaded is True
        assert classifier_service.bundle is not None
        assert "classes" in classifier_service.bundle
        assert len(classifier_service.bundle["classes"]) == 22
        assert classifier_service.bundle["classes"] == CLASSES_22

    def test_missing_model_raises_model_not_loaded_error(self):
        non_existent_path = "non_existent_path_to_model.joblib"
        service = OccupationalClassifierService(model_bundle_path=non_existent_path)
        with pytest.raises(ModelNotLoadedError) as exc_info:
            service.load_model()
        assert "not found" in str(exc_info.value).lower()

    def test_predict_fails_gracefully_when_bundle_missing(self):
        service = OccupationalClassifierService(model_bundle_path="invalid_path.joblib")
        with pytest.raises(ModelNotLoadedError):
            service.predict("Software engineer with Python experience")


class TestOccupationalClassifierContract:
    """Test suite for response contract, probability normalization, and margins."""

    def test_22_class_canonical_taxonomy(self):
        assert len(CLASSES_22) == 22
        # Ensure non-occupational industry tags are completely excluded
        assert "AUTOMOBILE" not in CLASSES_22
        assert "BPO" not in CLASSES_22
        # Ensure key occupational categories are present
        assert "INFORMATION-TECHNOLOGY" in CLASSES_22
        assert "ACCOUNTANT" in CLASSES_22
        assert "CHEF" in CLASSES_22
        assert "ENGINEERING" in CLASSES_22

    def test_prediction_output_contract_keys(self, classifier_service):
        resume_text = (
            "Senior Backend Engineer with 7 years of experience in Python, Django, "
            "PostgreSQL, microservices, Docker, Kubernetes, and AWS architecture."
        )
        res = classifier_service.predict(resume_text)

        expected_keys = {
            "predicted_role",
            "confidence",
            "runner_up_role",
            "runner_up_confidence",
            "margin",
            "review_required",
            "review_reasons",
            "model_version",
            "taxonomy_version",
        }
        assert set(res.keys()) == expected_keys
        assert res["predicted_role"] in CLASSES_22
        assert res["runner_up_role"] in CLASSES_22
        assert res["predicted_role"] != res["runner_up_role"]
        assert res["model_version"] == MODEL_VERSION
        assert res["taxonomy_version"] == TAXONOMY_VERSION

    def test_probability_normalization_and_margin(self, classifier_service):
        resume_text = (
            "Certified Public Accountant (CPA) with 10 years experience in corporate tax auditing, "
            "financial reporting, general ledger, and GAAP compliance."
        )
        res = classifier_service.predict(resume_text)

        assert 0.0 <= res["confidence"] <= 1.0
        assert 0.0 <= res["runner_up_confidence"] <= 1.0
        assert res["confidence"] >= res["runner_up_confidence"]

        # Margin must equal confidence minus runner_up_confidence
        expected_margin = round(res["confidence"] - res["runner_up_confidence"], 4)
        assert abs(res["margin"] - expected_margin) < 1e-4

    def test_empty_input_handling(self, classifier_service):
        res_empty = classifier_service.predict("")
        assert res_empty["predicted_role"] == "UNKNOWN"
        assert res_empty["confidence"] == 0.0
        assert res_empty["review_required"] is True
        assert len(res_empty["review_reasons"]) > 0

        res_spaces = classifier_service.predict("   ")
        assert res_spaces["predicted_role"] == "UNKNOWN"
        assert res_spaces["review_required"] is True

    def test_batch_prediction(self, classifier_service):
        texts = [
            "Executive Chef specialized in Italian cuisine and pastry.",
            "Attorney at law practicing civil litigation and corporate compliance.",
        ]
        results = classifier_service.predict_batch(texts)
        assert len(results) == 2
        assert results[0]["predicted_role"] == "CHEF"
        assert results[1]["predicted_role"] == "ADVOCATE"


class TestRecruiterSafetyRules:
    """Test suite for recruiter safety rules established in Phase V23."""

    def test_low_confidence_triggers_review(self):
        # Case: Confidence 0.35 (< 0.40), even if margin is large
        review_req, reasons = OccupationalClassifierService._evaluate_safety_rules(
            confidence=0.35,
            margin=0.20,
            predicted_role="FITNESS",
            runner_up_role="ADVOCATE"
        )
        assert review_req is True
        assert any("Low prediction confidence" in r for r in reasons)

    def test_thin_margin_triggers_review(self):
        # Case: Confidence 0.55 (>= 0.40), but margin 0.08 (< 0.15)
        review_req, reasons = OccupationalClassifierService._evaluate_safety_rules(
            confidence=0.55,
            margin=0.08,
            predicted_role="TEACHER",
            runner_up_role="ARTS"
        )
        assert review_req is True
        assert any("Thin top-2 probability margin" in r for r in reasons)

    def test_dual_trigger_review(self):
        # Case: Low confidence AND thin margin (e.g. V23 error cases)
        review_req, reasons = OccupationalClassifierService._evaluate_safety_rules(
            confidence=0.28,
            margin=0.03,
            predicted_role="BANKING",
            runner_up_role="FINANCE"
        )
        assert review_req is True
        assert len(reasons) == 2

    def test_clear_decision_passes_safety_rule(self):
        # Case: Confidence 0.80 (>= 0.40) and margin 0.65 (>= 0.15)
        review_req, reasons = OccupationalClassifierService._evaluate_safety_rules(
            confidence=0.80,
            margin=0.65,
            predicted_role="INFORMATION-TECHNOLOGY",
            runner_up_role="ENGINEERING"
        )
        assert review_req is False
        assert len(reasons) == 0


from app.factory import create_app


@pytest.fixture(scope="module")
def app_client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


class TestAPIEndpointsIntegration:
    """Test integration of occupational classifier with Flask API endpoints."""

    def test_matching_evaluate_endpoint_includes_occupational_classification(self, app_client, auth_candidate):
        login_resp = app_client.post("/api/v1/auth/login", json={
            "email": auth_candidate["email"],
            "password": auth_candidate["password"]
        })
        assert login_resp.status_code == 200
        token = login_resp.get_json()["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "resume_text": "Experienced Python Software Engineer with Flask, React, and SQL database skills.",
            "job_description": "Looking for a Python Developer proficient in REST APIs and backend development.",
            "required_skills": "Python, SQL, REST",
            "experience_required": 3
        }
        res = app_client.post("/api/v1/matching/evaluate", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        result = data["result"]

        assert "occupational_classification" in result
        occ = result["occupational_classification"]
        assert occ["predicted_role"] in CLASSES_22
        assert "confidence" in occ
        assert "runner_up_role" in occ
        assert "margin" in occ
        assert "review_required" in occ
        assert occ["model_version"] == MODEL_VERSION

