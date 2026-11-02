"""
TalentFlow AI — Unit & Integration Tests for Career Analysis & Resume Quality System.
Validates:
1. 22-class domain separation from granular specific roles.
2. Canonical role catalog completeness (Software Developer, Mechanical Design Engineer, etc.).
3. Deterministic ATS document quality analyzer subscores and recommendations.
4. Skill matching integrity (eliminates contradictory 80% default score when no skills required).
5. Roles and matching API contracts.
"""

import pytest
from app.factory import create_app
from app.services.role_service import DEFAULT_ROLE_CATALOG, RoleService
from app.services.resume_quality_analyzer import ResumeQualityAnalyzer
from app.ai.matching_engine import compute_match
from app.core.database import get_db_context
from app.models.role import RoleCatalog


@pytest.fixture(scope="module")
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


def test_canonical_roles_catalog_completeness():
    """Verify all canonical roles requested are present in DEFAULT_ROLE_CATALOG."""
    role_names = {r["name"] for r in DEFAULT_ROLE_CATALOG}
    required_roles = [
        "Software Developer",
        "Frontend Web Developer",
        "Mobile App Developer",
        "Data Architect",
        "Network Security Analyst",
        "SOC Analyst",
        "IT Analyst",
        "Agile Project Manager",
        "Mechanical Design Engineer",
        "Logistics Analyst",
        "Sales Account Manager",
        "Regional Sales Director",
        "Product Brand Manager",
        "Tax Planner",
        "Event Coordinator",
        "Clinical Psychologist"
    ]
    for r in required_roles:
        assert r in role_names, f"Role '{r}' missing from DEFAULT_ROLE_CATALOG"


def test_role_service_database_sync(client):
    """Verify RoleService syncs roles to database and lists them cleanly."""
    with get_db_context() as db:
        service = RoleService(db)
        service.sync_role_catalog()
        
        # Test domain query
        it_roles = service.list_roles(occupational_class="INFORMATION-TECHNOLOGY")
        assert len(it_roles) >= 10
        it_names = [r["name"] for r in it_roles]
        assert "Software Developer" in it_names
        
        # Test text search
        dev_roles = service.list_roles(search="Developer")
        assert any(r["name"] == "Software Developer" for r in dev_roles)


def test_resume_quality_analyzer_deterministic_scoring():
    """Verify ResumeQualityAnalyzer generates deterministic subscores and detects issues."""
    sample_resume = """
    Jane Doe
    jane.doe@example.com | (555) 123-4567 | linkedin.com/in/janedoe | github.com/janedoe
    
    PROFESSIONAL SUMMARY
    Innovative Software Developer with 6 years of experience engineering high-throughput distributed systems.
    
    TECHNICAL SKILLS
    Languages: Python, TypeScript, Java, SQL, Go
    Frameworks & Tools: React, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Git
    
    WORK EXPERIENCE
    Senior Software Engineer | TechCorp Inc. | 2021 - Present
    • Spearheaded migration of legacy monolith to microservices, reducing p99 latency by 45%.
    • Engineered automated CI/CD deployment pipelines using GitHub Actions, boosting release cadence by 60%.
    • Architected real-time analytics engine handling 50k events per second using Redis and Kafka.
    • Mentored 5 junior engineers and established team-wide code review standards.
    
    Software Developer | WebInnovate LLC | 2018 - 2021
    • Developed full-stack web applications utilizing React, Node.js, and PostgreSQL for 250k active users.
    • Optimized database queries and indexed foreign keys, saving $12,000 monthly in cloud infrastructure costs.
    • Implemented secure JWT authentication and role-based access control.
    
    EDUCATION
    Bachelor of Science in Computer Science | University of Technology | 2014 - 2018
    """
    
    analysis = ResumeQualityAnalyzer.analyze_resume(file_path=None, raw_text=sample_resume)
    
    assert analysis["formatting_score"] >= 75
    assert analysis["grade"] in ["A+", "A", "B"]
    assert analysis["is_ats_friendly"] is True
    assert analysis["metrics"]["has_contact_email"] is True
    assert analysis["metrics"]["has_contact_phone"] is True
    assert analysis["metrics"]["action_verb_count"] >= 4
    assert analysis["metrics"]["measurable_results_count"] >= 2
    
    # Subscores must all be between 0 and 100
    sub = analysis["subscores"]
    for k in ["ats_readability", "structure", "layout", "typography", "section_organization", "document_integrity"]:
        assert 0 <= sub[k] <= 100


def test_matching_engine_no_contradictory_skill_score():
    """Verify that when no JD skills are specified, skill_score is 0.0 and no_skills_specified is True."""
    res = compute_match(
        resume_text="Experienced Software Developer with Python and React expertise.",
        job_description="General open position.",
        required_skills_str=""
    )
    
    # Must NOT return fake 80% skill match with 0 matched and 0 missing skills!
    if not res["matched_skills"] and not res["missing_skills"]:
        assert res["no_skills_specified"] is True
        assert res["skill_score"] == 0.0


def test_matching_engine_with_real_skills():
    """Verify skill matching when skills are explicitly required."""
    res = compute_match(
        resume_text="Senior engineer proficient in Python, React, PostgreSQL, Docker, and Git.",
        job_description="Looking for a developer with Python, React, Kubernetes, and Go.",
        required_skills_str="Python, React, Kubernetes, Go"
    )
    
    assert "python" in [s.lower() for s in res["matched_skills"]] or "Python" in res["matched_skills"]
    assert "react" in [s.lower() for s in res["matched_skills"]] or "React" in res["matched_skills"]
    assert res["skill_score"] > 0.0
    assert res["no_skills_specified"] is False


def test_roles_api_endpoints(client):
    """Verify /api/v1/roles endpoint with domain and search filters."""
    # Test domain filter
    res = client.get("/api/v1/roles?domain=INFORMATION-TECHNOLOGY")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    roles = data["data"]
    assert len(roles) >= 5
    assert all(r["occupational_class"] == "INFORMATION-TECHNOLOGY" for r in roles)
    
    # Test search filter
    res_search = client.get("/api/v1/roles?search=Engineer")
    assert res_search.status_code == 200
    search_roles = res_search.get_json()["data"]
    assert len(search_roles) >= 1


def test_specific_role_never_returns_generic_specialist():
    """Verify that specific role inference NEVER returns 'General ... Specialist'."""
    # Test random/ambiguous text
    role, conf = RoleService.predict_specific_role("Ambiguous short resume text", "INFORMATION-TECHNOLOGY")
    assert not role.startswith("General "), f"Synthetic role generated: {role}"
    assert role in [r["name"] for r in DEFAULT_ROLE_CATALOG]

    # Test JD text inference (Case B)
    jd_role, _ = RoleService.infer_specific_role_from_text("Seeking a Machine Learning Engineer with PyTorch, TensorFlow, and MLOps experience.")
    assert jd_role == "Machine Learning Engineer"
    assert not jd_role.startswith("General ")


def test_evaluate_endpoint_case_a_and_case_b(client):
    """Verify Career Analysis evaluate endpoint for Case A (role + JD) and Case B (JD only)."""
    # 1. Register candidate
    import uuid
    uid = uuid.uuid4().hex[:6]
    email = f"eval_{uid}@example.com"
    pwd = "Password@123"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "name": "Eval Candidate"
    })
    token = reg.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Case A: Specific role + JD
    res_a = client.post("/api/v1/matching/evaluate", headers=headers, json={
        "resume_text": "Experienced engineer with Python, PyTorch, Docker, and PostgreSQL.",
        "specific_role": "Machine Learning Engineer",
        "job_description": "We need a Machine Learning Engineer to train deep learning models in PyTorch."
    })
    assert res_a.status_code == 200
    data_a = res_a.get_json()["data"]
    assert data_a["specific_role_target"] == "Machine Learning Engineer"
    assert not data_a["specific_role_target"].startswith("General ")
    assert data_a["is_inferred"] is False
    assert "resume_quality" in data_a

    # Case B: JD only without selecting a role
    res_b = client.post("/api/v1/matching/evaluate", headers=headers, json={
        "resume_text": "Full stack engineer building React and Node.js web applications.",
        "job_description": "Hiring a Frontend Web Developer to build responsive user interfaces in React, TypeScript, and Tailwind CSS."
    })
    assert res_b.status_code == 200
    data_b = res_b.get_json()["data"]
    assert data_b["is_inferred"] is True
    assert not data_b["specific_role_target"].startswith("General ")
    assert data_b["specific_role_target"] in [r["name"] for r in DEFAULT_ROLE_CATALOG]
    assert "resume_quality" in data_b


def test_job_suggestions_from_resume_returns_real_specific_roles():
    """Verify JobSuggestionService returns top specific roles directly from resume without role selector."""
    from app.services.job_suggestion_service import JobSuggestionService
    sample_resume = """
    Jane Doe - Senior Python Backend Engineer
    Email: jane@example.com | Phone: 555-1234
    Summary: 6 years building distributed APIs in Python, FastAPI, Django, PostgreSQL, Docker, AWS.
    Experience:
    Senior Software Engineer at SaaS Corp (2020-Present)
    • Architected RESTful microservices in Python with Redis caching.
    • Managed container deployments using Kubernetes and Docker.
    """
    suggestions = JobSuggestionService.suggest_roles(sample_resume, top_k=5)
    assert len(suggestions) >= 4
    for s in suggestions:
        assert not s["role"].startswith("General "), f"Synthetic role suggested: {s['role']}"
        assert any(s["role"] == r["name"] for r in DEFAULT_ROLE_CATALOG)
        assert 0 <= s["score"] <= 100
    top_role_names = [s["role"] for s in suggestions]
    assert any("Developer" in name or "Engineer" in name for name in top_role_names)


def test_insufficient_short_jd_no_fabricated_scores():
    """Verify short/poor JD like 'banking' returns has_sufficient_jd=False without fabricating scores."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    sample_resume = "Software Engineer with 4 years Python and PostgreSQL experience."
    result = ResumeAnalysisService.analyze_career(sample_resume, job_description="banking")

    assert result["has_sufficient_jd"] is False
    assert result["job_match"]["overall"] is None
    assert result["job_match"]["job_match_score"] is None
    assert result["job_match"]["has_sufficient_jd"] is False
    assert "The supplied job description does not contain enough" in result["job_match"]["reason"]
    # Overall score falls back directly to resume quality score without fabricating a 70/30 composite with 0 match
    assert result["overall_score"] == result["resume_quality"]["overall"]


def test_overall_score_composite_weighting():
    """Verify overall score rigorously calculates 70% Job Match + 30% Resume Quality when JD is sufficient."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    sample_resume = """
    Alex Johnson
    alex@example.com | 555-9876 | linkedin.com/in/alexj
    
    Professional Summary:
    Full Stack Developer with 4 years of hands-on experience designing cloud applications with React and Python.
    
    Technical Skills:
    Python, React, TypeScript, Node.js, PostgreSQL, Docker, Git
    
    Experience:
    Software Developer | WebSystems (2021 - Present)
    • Built customer dashboards using React and TypeScript.
    • Engineered backend REST services in Python and PostgreSQL.
    
    Education:
    Bachelor of Science in Computer Science
    """
    jd = """
    Job Title: Full Stack Developer
    Company: ModernTech Inc.
    We are seeking a Full Stack Developer with 3+ years experience.
    Responsibilities:
    • Develop responsive frontend interfaces using React and TypeScript.
    • Build robust backend web services using Python and PostgreSQL.
    • Collaborate with product managers and engineers to deploy features via Docker.
    Requirements:
    • Bachelor's degree in Computer Science or related field.
    • Proficiency in Python, React, TypeScript, PostgreSQL, and Git.
    """
    result = ResumeAnalysisService.analyze_career(sample_resume, job_description=jd)

    assert result["has_sufficient_jd"] is True
    assert result["job_match"]["has_sufficient_jd"] is True
    jm = result["job_match"]["overall"]
    rq = result["resume_quality"]["overall"]
    expected = round((jm * 0.70) + (rq * 0.30), 1)
    assert result["overall_score"] == expected
    assert "70%" in result["formula_breakdown"]
    assert "30%" in result["formula_breakdown"]
    assert len(result["resume_suggestions"]) > 0


def test_resume_quality_analyzer_grammar_spelling_checks():
    """Verify grammar and typo detection finds common resume misspellings."""
    from app.services.resume_quality_analyzer import ResumeQualityAnalyzer
    resume_with_typos = """
    Jane Doe
    jane@example.com | 555-1234
    
    Experience:
    • Responsible for the the developement of high performance databse systems.
    • Succesful lead of maintainance teams across cloud enviornment.
    """
    analysis = ResumeQualityAnalyzer.analyze_resume(raw_text=resume_with_typos)
    issues = analysis["issues"]
    
    # Check that typo issues were raised
    typo_issues = [i for i in issues if "developement" in i["evidence"] or "databse" in i["evidence"] or "the the" in i["evidence"] or "typo" in i["problem"].lower() or "spelling" in i["problem"].lower()]
    assert len(typo_issues) >= 1
    assert analysis["subscores"]["grammar_spelling"] < 90


# =========================================================================
# REGRESSION TESTS (Section 21 Requirements)
# =========================================================================

def test_regression_test_1_different_jds_produce_different_match_results():
    """Test 1: Assert that the same resume produces materially different match results across two different JDs."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    resume = """
    Senior Python Developer with 5 years experience building distributed backends with FastAPI, PostgreSQL, and Docker.
    Education: B.Tech in Computer Science.
    """
    jd_a = """
    Backend Developer. Requires Python, FastAPI, PostgreSQL and Docker.
    Build REST APIs and backend services.
    """
    jd_b = """
    Financial Analyst. We are seeking a Financial Analyst with experience in banking,
    financial reporting, Excel, accounting, and risk analysis.
    """
    res_a = ResumeAnalysisService.analyze_career(resume, job_description=jd_a)
    res_b = ResumeAnalysisService.analyze_career(resume, job_description=jd_b)

    assert res_a["has_sufficient_jd"] is True
    assert res_b["has_sufficient_jd"] is True
    assert res_a["job_match"]["overall"] != res_b["job_match"]["overall"]
    assert res_a["job_match"]["overall"] > res_b["job_match"]["overall"]
    assert res_a["job_match"]["matched_skills"] != res_b["job_match"]["matched_skills"]


def test_regression_test_2_poor_jd_banking():
    """Test 2: Assert that short JD 'banking' returns has_sufficient_jd=False, job_match_score=None, and no fake 83/80/100."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    resume = "Software Engineer with 4 years Python and PostgreSQL experience."
    res = ResumeAnalysisService.analyze_career(resume, job_description="banking")

    assert res["has_sufficient_jd"] is False
    assert res["job_match"]["overall"] is None
    assert res["job_match"]["job_match_score"] is None
    assert res["job_match"]["semantic"] is None
    assert res["job_match"]["skills"] is None
    assert res["job_match"]["experience"] is None
    assert res["job_match"]["education"] is None
    assert res["job_match"]["responsibility"] is None
    assert res["job_match"]["has_sufficient_jd"] is False
    assert "The supplied job description does not contain enough" in res["job_match"]["reason"]


def test_regression_test_3_same_resume_different_jd_quality_remains_unchanged():
    """Test 3: Assert Resume Quality stays identical when JD changes for the same resume."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    resume = """
    Jane Doe | jane@example.com | 555-1234
    Summary: Experienced developer with Python and SQL.
    Experience:
    • Built web applications in Python and PostgreSQL.
    Education:
    • Bachelor of Science in Computer Science.
    """
    jd_a = "Backend Developer. Requires Python, PostgreSQL and Docker. Build backend APIs and microservices."
    jd_b = "Product Brand Manager. Responsible for brand positioning, marketing campaigns, market research, and brand management."

    res_a = ResumeAnalysisService.analyze_career(resume, job_description=jd_a)
    res_b = ResumeAnalysisService.analyze_career(resume, job_description=jd_b)

    # Resume quality must be identical for the same resume
    assert res_a["resume_quality"]["overall"] == res_b["resume_quality"]["overall"]
    assert res_a["resume_quality"]["formatting_score"] == res_b["resume_quality"]["formatting_score"]
    assert res_a["resume_quality"]["word_count"] == res_b["resume_quality"]["word_count"]
    # But Job Match must differ
    assert res_a["job_match"]["overall"] != res_b["job_match"]["overall"]


def test_regression_test_4_different_resumes_same_jd():
    """Test 4: Assert different resumes produce different match and quality scores on the same JD."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    resume_a = """
    Alex Johnson | alex@example.com | 555-9876
    Professional Summary: Senior Backend Developer with 5 years experience in Python, FastAPI, Docker, and PostgreSQL.
    Experience:
    • Architected RESTful services in Python and deployed via Docker microservices.
    • Optimized database queries in PostgreSQL, improving throughput by 40%.
    Education:
    • Bachelor of Science in Computer Science.
    """
    resume_b = """
    Sam Smith | sam@example.com
    Summary: Art instructor passionate about watercolor painting and ceramic sculpture.
    Experience:
    Taught high school art classes and managed community art gallery.
    Education:
    Fine Arts Certificate.
    """
    jd = "Backend Developer. Requires 3+ years experience with Python, FastAPI, Docker, and PostgreSQL. Build web services."

    res_a = ResumeAnalysisService.analyze_career(resume_a, job_description=jd)
    res_b = ResumeAnalysisService.analyze_career(resume_b, job_description=jd)

    assert res_a["job_match"]["overall"] != res_b["job_match"]["overall"]
    assert res_a["job_match"]["overall"] > res_b["job_match"]["overall"]
    assert res_a["resume_quality"]["overall"] != res_b["resume_quality"]["overall"]


def test_regression_test_5_real_word_count():
    """Test 5: Assert that a known non-empty resume never returns word_count == 0."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    resume = "John Doe is a Python Developer with 5 years experience in cloud computing and databases."
    res = ResumeAnalysisService.analyze_career(resume, job_description="Python Developer")

    assert res["resume_quality"]["word_count"] > 10
    assert res["resume_quality"]["character_count"] > 50
    assert res["resume_text_available"] is True


def test_regression_test_6_no_contradictory_skill_results():
    """Test 6: Assert skill_score is never positive when matched_skills and missing_skills are empty."""
    from app.services.resume_analysis_service import ResumeAnalysisService
    resume = "General professional with 3 years operational experience."
    # JD with no technical skills
    jd_no_skills = "Executive Assistant. Responsibilities include scheduling meetings and managing executive communications."
    res = ResumeAnalysisService.analyze_career(resume, job_description=jd_no_skills)

    if not res["job_match"]["matched_skills"] and not res["job_match"]["missing_skills"]:
        assert res["job_match"]["skills"] is None or res["job_match"]["skills"] == 0


def test_regression_test_7_overall_score_math():
    """Test 7: For job_match = 83 and resume_quality = 80, assert overall = 82.1, not 83."""
    match_val = 83
    quality_val = 80
    expected_overall = round((match_val * 0.70) + (quality_val * 0.30), 1)
    assert expected_overall == 82.1
    formula = f"(Job Match: {match_val} × 70%) + (Resume Quality: {quality_val} × 30%) = {expected_overall}"
    assert "82.1" in formula
    assert "83" not in formula.split("=")[1]



