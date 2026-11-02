"""
TalentFlow AI — Job Suggestion Service
Generates top specific job role suggestions independently from the resume.
Does NOT control the Job Match calculation or require user role selection.
Only suggests real, specific job titles (never broad or generic occupational classes).
"""

import re
import logging
from typing import List, Dict, Any, Optional
from .role_service import DEFAULT_ROLE_CATALOG
from ..ai.skill_extractor import extract_skills

logger = logging.getLogger(__name__)


class JobSuggestionService:
    """Evaluates a candidate's resume and suggests real, high-alignment specific job roles."""

    @classmethod
    def suggest_roles(
        cls,
        resume_text: str,
        extracted_skills: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze resume text and skills to produce top specific job role suggestions.
        Returns a list of real job titles with score and matched skills.
        """
        if not resume_text or not resume_text.strip():
            # Return standard default roles if empty
            return [
                {"role": "Software Engineer", "score": 75, "matching_skills": []},
                {"role": "Full Stack Developer", "score": 72, "matching_skills": []},
                {"role": "Data Analyst", "score": 70, "matching_skills": []},
            ]

        clean_text = resume_text.lower()
        candidate_skills = set(
            s.lower() for s in (extracted_skills or extract_skills(resume_text))
        )

        role_scores: List[Dict[str, Any]] = []

        for role in DEFAULT_ROLE_CATALOG:
            role_name = role["name"]
            # Exclude any generic fallback names just in case
            if role_name.lower().startswith("general "):
                continue

            score = 0.0
            matched_role_skills: List[str] = []

            # 1. Exact role title mention in resume (high signal)
            pattern = r'\b' + re.escape(role_name.lower()) + r'\b'
            if re.search(pattern, clean_text):
                score += 35.0

            # 2. Aliases match
            for alias in role.get("aliases", []):
                alias_pat = r'\b' + re.escape(alias.lower()) + r'\b'
                if re.search(alias_pat, clean_text):
                    score += 20.0
                    break

            # 3. Skills overlap
            role_skills = role.get("required_skills_default", [])
            for req_skill in role_skills:
                req_lower = req_skill.lower()
                if req_lower in candidate_skills or re.search(r'\b' + re.escape(req_lower) + r'\b', clean_text):
                    matched_role_skills.append(req_skill)

            if role_skills:
                skill_ratio = len(matched_role_skills) / len(role_skills)
                score += (len(matched_role_skills) * 8.0) + (skill_ratio * 35.0)

            # Calibrate to percentage (60% to 96%)
            if score > 0:
                calibrated = min(96, round(60 + (min(score, 60.0) / 60.0) * 36))
            else:
                calibrated = 55

            role_scores.append({
                "role": role_name,
                "score": calibrated,
                "matching_skills": matched_role_skills[:6],
                "raw_score": score,
                "experience_level": role.get("experience_level", "Mid-Level")
            })

        # Sort descending by raw score
        role_scores.sort(key=lambda x: (x["raw_score"], x["score"]), reverse=True)

        # Deduplicate by role name
        seen = set()
        suggestions: List[Dict[str, Any]] = []
        for r in role_scores:
            if r["role"] not in seen:
                seen.add(r["role"])
                suggestions.append({
                    "role": r["role"],
                    "score": r["score"],
                    "matching_skills": r["matching_skills"]
                })
            if len(suggestions) >= top_k:
                break

        return suggestions

