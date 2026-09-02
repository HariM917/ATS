"""
TalentFlow AI — Candidate Ranking Model
Sorts candidates by composite match score with configurable weights and pagination.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

logger = logging.getLogger(__name__)


DEFAULT_WEIGHTS = {
    "semantic": 0.25,
    "skills": 0.40,
    "projects": 0.15,
    "experience": 0.10,
    "education": 0.10,
}


def rank_candidates(
    db: Session,
    job_id: str,
    weights: Optional[Dict[str, float]] = None,
    page: int = 1,
    per_page: int = 50,
    min_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Rank all screened candidates for a job by composite weighted score.
    
    Args:
        db: Database session
        job_id: Job ID to rank candidates for
        weights: Optional custom scoring weights (overrides job defaults)
        page: Pagination page number
        per_page: Results per page
        min_score: Minimum score threshold
    
    Returns:
        Dict with rankings list, pagination info, and statistics
    """
    from ..models import MatchResult, Candidate

    query = db.query(MatchResult).filter(
        MatchResult.job_id == job_id,
        MatchResult.final_score >= min_score,
    ).order_by(desc(MatchResult.final_score))

    total = query.count()
    results = query.offset((page - 1) * per_page).limit(per_page).all()

    rankings = []
    for rank_offset, match in enumerate(results, start=(page - 1) * per_page + 1):
        entry = {
            "rank": rank_offset,
            "match_id": match.id,
            "candidate_id": match.candidate_id,
            "final_score": match.final_score,
            "semantic_score": match.semantic_score,
            "skill_score": match.skill_score,
            "experience_score": match.experience_score,
            "matched_skills": match.matched_skills or [],
            "missing_skills": match.missing_skills or [],
            "explanation": match.explanation or {},
            "model_version": match.model_version,
        }
        # Join candidate name
        if match.candidate:
            entry["candidate_name"] = match.candidate.name
        rankings.append(entry)

    # Score statistics
    if results:
        scores = [r.final_score for r in results]
        stats = {
            "total_candidates": total,
            "avg_score": round(sum(scores) / len(scores), 3),
            "max_score": round(max(scores), 3),
            "min_score": round(min(scores), 3),
            "above_80_pct": sum(1 for s in scores if s >= 0.80),
        }
    else:
        stats = {"total_candidates": 0, "avg_score": 0, "max_score": 0, "min_score": 0, "above_80_pct": 0}

    return {
        "rankings": rankings,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        },
        "statistics": stats,
    }


def compute_tier(score: float) -> str:
    """Classify a match score into hiring tiers."""
    if score >= 0.90:
        return "excellent"
    elif score >= 0.75:
        return "strong"
    elif score >= 0.60:
        return "moderate"
    elif score >= 0.40:
        return "below_average"
    else:
        return "poor"
