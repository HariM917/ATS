"""
TalentFlow AI — Baseline Smoke Tests
Tests critical existing functionality BEFORE refactoring begins.
Run with: pytest tests/baseline/test_smoke.py -v
"""
import sys
import os
import importlib

# Add backend to path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, BACKEND_DIR)


class TestSkillExtraction:
    """Verify the skill extraction pipeline produces correct results."""

    def test_extract_skills_from_python_resume(self):
        from ai_engine import extract_skills
        text = "I am proficient in Python, TensorFlow, PyTorch, and SQL. I have experience with React and Docker."
        skills = extract_skills(text)
        assert isinstance(skills, list)
        assert len(skills) >= 4
        assert "Python" in skills
        assert "SQL" in skills

    def test_extract_skills_empty_text(self):
        from ai_engine import extract_skills
        skills = extract_skills("")
        assert skills == []

    def test_synonym_expansion(self):
        from ai_engine import extract_skills
        text = "Experienced with ml, dl, nlp, k8s, and js frameworks"
        skills = extract_skills(text)
        # Should expand abbreviations
        skill_lower = [s.lower() for s in skills]
        assert any("machine learning" in s for s in skill_lower) or "Machine Learning" in skills

    def test_categorize_skills(self):
        from ai_engine import categorize_skills
        skills = ["Python", "React", "Docker", "PostgreSQL", "Machine Learning"]
        categories = categorize_skills(skills)
        assert isinstance(categories, dict)
        assert len(categories) > 0


class TestResumeParser:
    """Verify text extraction functions exist and handle edge cases."""

    def test_extract_text_nonexistent_file(self):
        from ai_engine import extract_text
        result = extract_text("/nonexistent/file.pdf")
        assert result == ""

    def test_extract_sections(self):
        from ai_engine import extract_sections
        text = "Skills: Python, React\nExperience: 3 years at Google\nEducation: BS Computer Science"
        sections = extract_sections(text)
        assert isinstance(sections, dict)
        assert "skills" in sections
        assert "experience" in sections

    def test_extract_years_of_experience(self):
        from ai_engine import extract_years_of_experience
        text = "I have 5 years of professional experience in software development"
        years = extract_years_of_experience(text)
        assert years == 5.0

    def test_extract_years_fresher(self):
        from ai_engine import extract_years_of_experience
        text = "Recent graduate looking for entry-level position"
        years = extract_years_of_experience(text)
        assert years == 0.0


class TestRolePrediction:
    """Verify role taxonomy is loaded and keyword detection works."""

    def test_keyword_role_detection_ml(self):
        from ai_engine import _keyword_role_detection
        text = "I work with tensorflow pytorch and deep learning neural networks"
        role = _keyword_role_detection(text)
        assert role == "Machine Learning Engineer"

    def test_keyword_role_detection_frontend(self):
        from ai_engine import _keyword_role_detection
        text = "React developer building responsive CSS interfaces"
        role = _keyword_role_detection(text)
        assert role == "Frontend Developer"

    def test_role_taxonomy_loaded(self):
        from ai_engine import ROLE_TAXONOMY
        assert len(ROLE_TAXONOMY) >= 10


class TestJDValidation:
    """Verify JD validation and expansion."""

    def test_valid_jd(self):
        from ai_engine import is_valid_job_description
        assert is_valid_job_description("Software Engineer with Python experience") is True

    def test_invalid_jd_empty(self):
        from ai_engine import is_valid_job_description
        assert is_valid_job_description("") is False

    def test_invalid_jd_gibberish(self):
        from ai_engine import is_valid_job_description
        assert is_valid_job_description("aaaaaaaaaaaaaaaaaaaaa") is False

    def test_expand_short_jd(self):
        from ai_engine import expand_job_description
        expanded = expand_job_description("data analyst")
        assert len(expanded) > len("data analyst")

    def test_no_expand_long_jd(self):
        from ai_engine import expand_job_description
        long_jd = "We are looking for a senior software engineer with strong Python skills and experience in distributed systems, databases, and cloud infrastructure."
        expanded = expand_job_description(long_jd)
        assert expanded == long_jd


class TestValidationGuards:
    """Verify production validation guards."""

    def test_validate_empty_result(self):
        from ai_engine import validate_ats_result
        result = validate_ats_result({})
        assert result["match_percentage"] == 0
        assert result["final_score"] == 0.0
        assert isinstance(result["skills"], list)
        assert isinstance(result["predicted_role"], str)

    def test_validate_nan_score(self):
        from ai_engine import validate_ats_result
        import math
        result = validate_ats_result({"match_percentage": float('nan'), "final_score": float('nan')})
        assert not math.isnan(result["match_percentage"])
        assert not math.isnan(result["final_score"])

    def test_empty_result_function(self):
        from ai_engine import _empty_result
        result = _empty_result()
        assert result["match_percentage"] == 0
        assert isinstance(result["skills"], list)
        assert result["BACKEND_VERSION"] is not None


class TestSkillTaxonomy:
    """Verify skill taxonomy is properly loaded."""

    def test_skill_dictionary_loaded(self):
        from ai_engine import SKILL_DICTIONARY
        assert len(SKILL_DICTIONARY) >= 100

    def test_skill_lower_maps(self):
        from ai_engine import SKILL_LOWER_TO_ORIG
        assert "python" in SKILL_LOWER_TO_ORIG
        assert SKILL_LOWER_TO_ORIG["python"] == "Python"


class TestChatbotComponents:
    """Verify chatbot components are importable and functional."""

    def test_preprocess_query(self):
        from chatbot_rag import preprocess_query
        result = preprocess_query("How to learn ML?")
        assert "machine learning" in result

    def test_check_fast_path_greeting(self):
        from chatbot_rag import check_fast_path
        result = check_fast_path("hello")
        assert result is not None
        assert "career" in result.lower() or "coach" in result.lower()

    def test_check_fast_path_normal_query(self):
        from chatbot_rag import check_fast_path
        result = check_fast_path("How do I optimize my resume for ATS systems?")
        assert result is None  # Should not trigger fast path

    def test_detect_intent_and_domain(self):
        from chatbot_rag import detect_intent_and_domain
        intent, domain, tags = detect_intent_and_domain("How to improve my resume format?")
        assert intent in ("resume", "general", "learning")
        assert domain in ("resume", "general")

    def test_knowledge_base_loaded(self):
        from chatbot_rag import KNOWLEDGE_BASE
        assert len(KNOWLEDGE_BASE) >= 10

    def test_fallback_response(self):
        from chatbot_rag import fallback_response
        result = fallback_response("", "resume")
        assert isinstance(result, str)
        assert len(result) > 20


class TestDatabaseManager:
    """Verify database runtime and core job service functions."""

    def test_db_connection(self):
        from app.core.database import SessionFactory
        from sqlalchemy import text
        session = SessionFactory()
        try:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        finally:
            session.close()

    def test_get_all_jobs(self):
        from app.core.database import SessionFactory
        from app.services.job_service import JobService
        session = SessionFactory()
        try:
            service = JobService(session)
            jobs = service.list_jobs()
            assert isinstance(jobs, list)
        finally:
            session.close()


class TestAuthUtils:
    """Verify auth utilities."""

    def test_create_jwt(self):
        from auth_utils import create_jwt, decode_jwt
        token = create_jwt(1, "test@test.com", "candidate", "testuser")
        assert isinstance(token, str)
        assert len(token) > 50

        payload = decode_jwt(token)
        assert payload is not None
        assert payload["email"] == "test@test.com"
        assert payload["role"] == "candidate"

    def test_decode_invalid_jwt(self):
        from auth_utils import decode_jwt
        result = decode_jwt("invalid.token.here")
        assert result is None
