"""
TalentFlow AI — Multidimensional ATS Match Engine & Calibrated Scoring
Combines:
1. Semantic Context Similarity (MPNet 768D)
2. Exact & Fuzzy Skill Match Ratio
3. Project & Domain Alignment
4. Experience Requirements Fulfillment
5. Education Credentials
6. Sigmoid calibration
"""
import math
import logging
from typing import Dict, Any, List
from .embeddings import get_embedding, cosine_similarity
from .skill_extractor import extract_skills
from .resume_parser import extract_sections

logger = logging.getLogger(__name__)


def compute_match(
    resume_text: str,
    job_description: str,
    required_skills_str: str = "",
    experience_required_years: int = 0,
    scoring_weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """Execute complete explainable match evaluation pipeline between resume and JD."""
    if not resume_text or not job_description:
        return _empty_match_result()

    weights = scoring_weights or {
        "semantic": 0.25,
        "skills": 0.40,
        "projects": 0.15,
        "experience": 0.10,
        "education": 0.10
    }

    # 1. Semantic Embedding Similarity
    res_vec = get_embedding(resume_text)
    jd_vec = get_embedding(job_description)
    semantic_score = cosine_similarity(res_vec, jd_vec)

    # 2. Skill Extraction & Overlap
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(job_description))
    if required_skills_str:
        for s in required_skills_str.split(","):
            s_clean = s.strip()
            if s_clean:
                jd_skills.add(s_clean)

    matched_skills = sorted(list(resume_skills.intersection(jd_skills)))
    missing_skills = sorted(list(jd_skills.difference(resume_skills)))

    if jd_skills:
        skill_score = min(1.0, len(matched_skills) / len(jd_skills))
    else:
        skill_score = 0.8  # Default baseline if no explicit skills required

    # 3. Section Extraction
    sections = extract_sections(resume_text)
    projects_text = sections.get("projects", "")
    projects_score = cosine_similarity(get_embedding(projects_text), jd_vec) if projects_text else semantic_score * 0.8

    # 4. Experience Fulfillment
    years_detected = _extract_experience_years(resume_text)
    if experience_required_years <= 0:
        experience_score = 1.0
    else:
        experience_score = min(1.0, years_detected / experience_required_years)

    # 5. Education Relevance
    education_text = sections.get("education", "")
    education_score = 1.0 if any(deg in education_text.lower() for deg in ["bachelor", "master", "phd", "b.tech", "b.e", "m.tech", "degree", "bs", "ms"]) else 0.75

    # 6. Weighted Sum & Sigmoid Calibration
    raw_score = (
        weights.get("semantic", 0.25) * semantic_score +
        weights.get("skills", 0.40) * skill_score +
        weights.get("projects", 0.15) * projects_score +
        weights.get("experience", 0.10) * experience_score +
        weights.get("education", 0.10) * education_score
    )

    # Sigmoid calibration: stretches scores around 0.35-0.85
    calibrated_score = 1.0 / (1.0 + math.exp(-8.0 * (raw_score - 0.35)))
    calibrated_score = float(max(0.10, min(0.98, calibrated_score)))

    # Explanation Generation
    explanation = _generate_explanation(
        calibrated_score=calibrated_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        years_detected=years_detected,
        years_required=experience_required_years,
        semantic_score=semantic_score
    )

    return {
        "final_score": round(calibrated_score, 3),
        "match_percentage": int(calibrated_score * 100),
        "semantic_score": round(semantic_score, 3),
        "skill_score": round(skill_score, 3),
        "experience_score": round(experience_score, 3),
        "projects_score": round(projects_score, 3),
        "education_score": round(education_score, 3),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extracted_skills": sorted(list(resume_skills)),
        "explanation": explanation,
        "model_version": "all-mpnet-base-v2-calibrated-v3.1"
    }


def _extract_experience_years(text: str) -> float:
    import re
    matches = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?', text.lower())
    if matches:
        try:
            return max(float(m) for m in matches)
        except ValueError:
            pass
    return 0.0


def _generate_explanation(
    calibrated_score: float,
    matched_skills: List[str],
    missing_skills: List[str],
    years_detected: float,
    years_required: int,
    semantic_score: float
) -> Dict[str, Any]:
    strengths = []
    improvements = []

    if len(matched_skills) >= 4:
        strengths.append(f"Strong skill coverage: {', '.join(matched_skills[:4])}")
    elif matched_skills:
        strengths.append(f"Matches key skills: {', '.join(matched_skills)}")

    if semantic_score >= 0.7:
        strengths.append("High contextual and semantic relevance to role requirements.")

    if years_required > 0:
        if years_detected >= years_required:
            strengths.append(f"Meets experience criteria ({years_detected:.1f} yrs detected vs {years_required} required).")
        else:
            improvements.append(f"Experience level ({years_detected:.1f} yrs) is below requested {years_required} years.")

    if missing_skills:
        improvements.append(f"Missing desired core competencies: {', '.join(missing_skills[:4])}")

    summary = (
        f"Candidate achieved a {int(calibrated_score*100)}% match. "
        f"Matched {len(matched_skills)} core skills with {len(missing_skills)} skill gaps identified."
    )

    return {
        "summary": summary,
        "strengths": strengths or ["Basic role eligibility met."],
        "improvement_areas": improvements or ["Profile closely aligns with the job profile."],
        "experience_check": {"detected": years_detected, "required": years_required}
    }


def _empty_match_result() -> Dict[str, Any]:
    return {
        "final_score": 0.0,
        "match_percentage": 0,
        "semantic_score": 0.0,
        "skill_score": 0.0,
        "experience_score": 0.0,
        "projects_score": 0.0,
        "education_score": 0.0,
        "matched_skills": [],
        "missing_skills": [],
        "extracted_skills": [],
        "explanation": {"summary": "Insufficient data provided for matching."},
        "model_version": "v3.1"
    }
