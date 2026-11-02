"""
TalentFlow AI — Job Match Service
Evaluates Resume ↔ Job Description compatibility across:
1. Semantic Context Alignment
2. Required / Preferred Skills Overlap
3. Experience Fit (years & seniority)
4. Education & Qualifications Fit
5. Core Responsibilities Alignment

Performs rigorous deterministic JD quality/sufficiency checking.
Never fabricates optimistic non-zero scores when signals are missing or insufficient.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from ..ai.embeddings import get_embedding, cosine_similarity
from ..ai.skill_extractor import extract_skills
from ..ai.resume_parser import extract_sections

logger = logging.getLogger(__name__)


class JobMatchService:
    """Evaluates multi-dimensional alignment between a resume and a job description."""

    NOMINAL_WEIGHTS = {
        "semantic": 0.30,
        "skills": 0.35,
        "experience": 0.15,
        "education": 0.10,
        "responsibility": 0.10,
    }

    @classmethod
    def check_jd_sufficiency(
        cls,
        clean_jd: str,
        explicit_skills_req: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Deterministic JD quality check.
        Requires sufficient information across core signals:
        1. Role / Title
        2. Responsibilities / Duties
        3. Technical / Domain Skills
        4. Experience Requirements
        5. Education / Qualifications
        """
        if not clean_jd or not clean_jd.strip():
            return False, "No job description was provided. Please paste an employer job description to calculate Job Match."

        words = clean_jd.split()
        if len(words) < 12 and not explicit_skills_req:
            return False, (
                "The supplied job description does not contain enough role, responsibility, "
                "skill, experience, or qualification information for a reliable match analysis."
            )

        jd_lower = clean_jd.lower()

        # Signal 1: Role / Title
        role_keywords = [
            "developer", "engineer", "analyst", "manager", "specialist",
            "consultant", "lead", "architect", "executive", "associate",
            "administrator", "designer", "coordinator", "officer", "intern",
            "scientist", "accountant", "director", "technician", "programmer"
        ]
        has_role = any(r in jd_lower for r in role_keywords)

        # Signal 2: Responsibilities / Action verbs
        resp_keywords = [
            "responsibilities", "duties", "develop", "building", "build", "create",
            "analyze", "manage", "maintain", "collaborate", "coordinate", "lead",
            "design", "implement", "oversee", "execute", "handle", "support",
            "deliver", "architect", "deploy", "optimize", "test", "writing"
        ]
        has_resp = any(r in jd_lower for r in resp_keywords)

        # Signal 3: Skills
        skills_found = extract_skills(clean_jd)
        if explicit_skills_req:
            for s in explicit_skills_req.split(","):
                sc = s.strip()
                if sc and sc not in skills_found:
                    skills_found.append(sc)
        has_skills = len(skills_found) >= 1

        # Signal 4: Experience
        exp_keywords = [
            "year", "years", "yrs", "experience", "exp", "fresher",
            "freshers", "entry level", "entry-level", "senior", "junior"
        ]
        has_exp = any(e in jd_lower for e in exp_keywords)

        # Signal 5: Education
        edu_keywords = [
            "bachelor", "master", "phd", "b.tech", "b.e", "m.tech",
            "degree", "bs", "ms", "mba", "diploma", "graduate"
        ]
        has_edu = any(ed in jd_lower for ed in edu_keywords)

        signals_detected = [has_role, has_resp, has_skills, has_exp, has_edu]
        signal_count = sum(1 for s in signals_detected if s)

        # A short phrase like 'banking' or 'software developer' has <= 2 words and < 2 signals
        if len(words) < 15 and signal_count < 2:
            return False, (
                "The supplied job description does not contain enough role, responsibility, "
                "skill, experience, or qualification information for a reliable match analysis."
            )

        if signal_count < 2 and len(words) < 25:
            return False, (
                "The supplied job description does not contain enough role, responsibility, "
                "skill, experience, or qualification information for a reliable match analysis."
            )

        return True, None

    @classmethod
    def evaluate_match(
        cls,
        resume_text: str,
        job_description: str,
        explicit_skills_req: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate resume against a job description.
        Returns dimensional breakdown, matched/missing skills, and composite score.
        Never fabricates optimistic non-zero scores when information is missing.
        """
        clean_jd = (job_description or "").strip()
        clean_resume = (resume_text or "").strip()

        # 1. Deterministic JD Sufficiency Check
        is_sufficient, reason = cls.check_jd_sufficiency(clean_jd, explicit_skills_req)

        if not is_sufficient:
            res_years = cls._extract_experience_years(clean_resume)
            return {
                "overall": None,
                "job_match_score": None,
                "has_sufficient_jd": False,
                "reason": reason,
                "message": reason,
                "semantic": None,
                "skills": None,
                "has_explicit_skills": False,
                "experience": None,
                "education": None,
                "responsibility": None,
                "matched_skills": [],
                "missing_skills": [],
                "extracted_jd_skills": [],
                "years_detected": res_years,
                "years_required": None,
                "education_required": False,
                "applicable_dimensions": [],
                "unavailable_dimensions": ["semantic", "skills", "experience", "education", "responsibility"],
                "raw_jd_provided": clean_jd
            }

        # 2. Skill Extraction & Overlap
        resume_skills_list = extract_skills(clean_resume)
        resume_skills_lower = set(s.lower() for s in resume_skills_list)

        jd_skills_list = extract_skills(clean_jd)
        if explicit_skills_req:
            for s in explicit_skills_req.split(","):
                s_clean = s.strip()
                if s_clean and s_clean not in jd_skills_list:
                    jd_skills_list.append(s_clean)

        matched_skills: List[str] = []
        missing_skills: List[str] = []

        for skill in jd_skills_list:
            if skill.lower() in resume_skills_lower or re.search(r'\b' + re.escape(skill.lower()) + r'\b', clean_resume.lower()):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        matched_skills = sorted(list(set(matched_skills)))
        missing_skills = sorted(list(set(missing_skills)))

        if jd_skills_list:
            skills_match_pct = round((len(matched_skills) / len(jd_skills_list)) * 100)
            skills_match_pct = max(0, min(100, skills_match_pct))
            has_explicit_skills = True
        else:
            # No technical skills identified in JD text -> N/A
            skills_match_pct = None
            has_explicit_skills = False

        # 3. Semantic Embedding Match
        res_vec = get_embedding(clean_resume)
        jd_vec = get_embedding(clean_jd)
        if res_vec is not None and jd_vec is not None:
            raw_cosine = cosine_similarity(res_vec, jd_vec)
            # Normalize embedding similarity: stretches ~0.15 - 0.85 to 10% - 98%
            semantic_pct = round(max(0.05, min(0.98, (raw_cosine - 0.10) / 0.75)) * 100)
        else:
            semantic_pct = None

        # 4. Experience Requirements Match
        req_years = cls._extract_experience_years(clean_jd)
        res_years = cls._extract_experience_years(clean_resume)
        is_entry_level = any(
            k in clean_jd.lower()
            for k in ["fresher", "freshers", "entry level", "entry-level", "no experience required", "0+ years", "0 years"]
        )

        if req_years > 0:
            exp_pct = round(min(1.0, res_years / req_years) * 100)
        elif is_entry_level:
            exp_pct = 100
        else:
            # No explicit year requirement in JD -> N/A
            exp_pct = None

        # 5. Education Credentials Match
        sections = extract_sections(clean_resume)
        edu_text = sections.get("education", "").lower()
        jd_lower = clean_jd.lower()

        degree_keywords = ["bachelor", "master", "phd", "b.tech", "b.e", "m.tech", "degree", "bs", "ms", "mba", "diploma"]
        jd_mentions_degree = any(deg in jd_lower for deg in degree_keywords)

        if jd_mentions_degree:
            resume_has_degree = any(deg in edu_text or deg in clean_resume.lower() for deg in degree_keywords)
            edu_pct = 100 if resume_has_degree else 40
        else:
            # No education requirement in JD -> N/A
            edu_pct = None

        # 6. Responsibility & Alignment Match
        has_resp_signals = any(
            r in jd_lower for r in ["responsibilities", "duties", "you will", "role involves", "responsible for"]
        ) or len(clean_jd.split()) >= 30

        if has_resp_signals:
            proj_text = sections.get("experience", "") + " " + sections.get("projects", "")
            if proj_text.strip() and jd_vec is not None:
                proj_vec = get_embedding(proj_text)
                if proj_vec is not None:
                    resp_cosine = cosine_similarity(proj_vec, jd_vec)
                    resp_pct = round(max(0.05, min(0.98, (resp_cosine - 0.10) / 0.75)) * 100)
                else:
                    resp_pct = semantic_pct
            else:
                resp_pct = semantic_pct
        else:
            resp_pct = None

        # 7. Normalized Composite Job Match Score
        # Only participating (non-None) dimensions contribute to the composite score
        available_dims: Dict[str, int] = {}
        unavailable_dims: List[str] = []

        for dim_name, val in [
            ("semantic", semantic_pct),
            ("skills", skills_match_pct),
            ("experience", exp_pct),
            ("education", edu_pct),
            ("responsibility", resp_pct)
        ]:
            if val is not None:
                available_dims[dim_name] = val
            else:
                unavailable_dims.append(dim_name)

        if available_dims:
            total_nominal_weight = sum(cls.NOMINAL_WEIGHTS[d] for d in available_dims)
            overall = round(sum(available_dims[d] * (cls.NOMINAL_WEIGHTS[d] / total_nominal_weight) for d in available_dims))
            overall = max(0, min(100, overall))
        else:
            overall = None

        return {
            "overall": overall,
            "job_match_score": overall,
            "has_sufficient_jd": True,
            "reason": None,
            "message": None,
            "semantic": semantic_pct,
            "skills": skills_match_pct,
            "has_explicit_skills": has_explicit_skills,
            "experience": exp_pct,
            "education": edu_pct,
            "responsibility": resp_pct,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "extracted_jd_skills": jd_skills_list,
            "years_detected": res_years,
            "years_required": req_years if req_years > 0 else None,
            "education_required": jd_mentions_degree,
            "applicable_dimensions": list(available_dims.keys()),
            "unavailable_dimensions": unavailable_dims,
            "raw_jd_provided": clean_jd
        }

    @staticmethod
    def _extract_experience_years(text: str) -> float:
        """Extract number of years mentioned in text."""
        matches = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?', text.lower())
        if matches:
            try:
                return max(float(m) for m in matches)
            except ValueError:
                pass
        return 0.0
