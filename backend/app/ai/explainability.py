"""
TalentFlow AI — Explainable AI Match Analysis
Generates structured explanations for match scores including skill gap analysis,
strength identification, and actionable improvement recommendations.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_match_explanation(
    calibrated_score: float,
    matched_skills: List[str],
    missing_skills: List[str],
    years_detected: float,
    years_required: int,
    semantic_score: float,
    skill_score: float = 0.0,
    experience_score: float = 0.0,
    projects_score: float = 0.0,
    education_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Generate a comprehensive, structured explanation for a match evaluation.
    
    Returns dict with: summary, strengths, improvement_areas, skill_gap_analysis,
    experience_check, score_breakdown, recommendations.
    """
    strengths = []
    improvements = []
    recommendations = []

    # Skill analysis
    if len(matched_skills) >= 6:
        strengths.append(f"Excellent skill coverage: matches {len(matched_skills)} required competencies including {', '.join(matched_skills[:4])}.")
    elif len(matched_skills) >= 4:
        strengths.append(f"Strong skill match: {', '.join(matched_skills[:4])}.")
    elif matched_skills:
        strengths.append(f"Matches key skills: {', '.join(matched_skills)}.")

    # Semantic relevance
    if semantic_score >= 0.8:
        strengths.append("Very high contextual relevance — resume content closely aligns with role requirements.")
    elif semantic_score >= 0.7:
        strengths.append("High semantic relevance to role requirements.")
    elif semantic_score >= 0.5:
        improvements.append("Moderate semantic alignment — consider tailoring resume language to match the job description more closely.")
    else:
        improvements.append("Low semantic alignment — resume may need significant restructuring to match the target role.")

    # Experience
    if years_required > 0:
        if years_detected >= years_required:
            strengths.append(f"Meets experience criteria ({years_detected:.1f} years detected vs {years_required} required).")
        elif years_detected >= years_required * 0.7:
            improvements.append(f"Experience is slightly below target ({years_detected:.1f} years vs {years_required} required). Consider highlighting project or freelance experience.")
        else:
            improvements.append(f"Experience gap: {years_detected:.1f} years detected vs {years_required} required.")
            recommendations.append("Gain experience through open-source contributions, freelance projects, or relevant certifications.")

    # Missing skills
    if len(missing_skills) > 5:
        improvements.append(f"Significant skill gaps: missing {len(missing_skills)} desired competencies including {', '.join(missing_skills[:4])}.")
        recommendations.append(f"Prioritize learning: {', '.join(missing_skills[:3])} to improve match score.")
    elif missing_skills:
        improvements.append(f"Missing desired competencies: {', '.join(missing_skills[:4])}.")
        recommendations.append(f"Consider adding coursework or projects in: {', '.join(missing_skills[:3])}.")

    # Score-based recommendations
    if calibrated_score < 0.5:
        recommendations.append("This role may not be the strongest fit. Consider roles that better align with your current skill set.")
    elif calibrated_score < 0.7:
        recommendations.append("Good potential — addressing the skill gaps identified above could significantly improve your match.")

    # Summary
    match_pct = int(calibrated_score * 100)
    summary = (
        f"Candidate achieved a {match_pct}% match. "
        f"Matched {len(matched_skills)} core skills with {len(missing_skills)} skill gaps identified."
    )

    return {
        "summary": summary,
        "strengths": strengths or ["Basic role eligibility met."],
        "improvement_areas": improvements or ["Profile closely aligns with the job profile."],
        "recommendations": recommendations or ["Continue refining your resume for ATS optimization."],
        "skill_gap_analysis": {
            "matched": matched_skills,
            "missing": missing_skills,
            "match_ratio": round(len(matched_skills) / max(len(matched_skills) + len(missing_skills), 1), 2),
        },
        "experience_check": {
            "detected": years_detected,
            "required": years_required,
            "meets_requirement": years_detected >= years_required if years_required > 0 else True,
        },
        "score_breakdown": {
            "semantic": round(semantic_score, 3),
            "skills": round(skill_score, 3),
            "experience": round(experience_score, 3),
            "projects": round(projects_score, 3),
            "education": round(education_score, 3),
        },
    }
