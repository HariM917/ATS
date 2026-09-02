"""
TalentFlow AI — Candidate Profile, Application Tracking, and Dashboard Service
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..models import Candidate, User, Application, Resume, Job
from ..repositories import CandidateRepository, ApplicationRepository, ResumeRepository, UserRepository
from ..core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class CandidateService:
    def __init__(self, db: Session):
        self.db = db
        self.cand_repo = CandidateRepository(db)
        self.app_repo = ApplicationRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.user_repo = UserRepository(db)

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Get candidate profile with associated user info."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        candidate = self.cand_repo.get_by_user_id(user_id)
        profile = {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "role": user.role,
        }

        if candidate:
            profile.update({
                "candidate_id": str(candidate.id),
                "name": candidate.name,
                "branch": candidate.branch,
                "graduation_year": candidate.graduation_year,
            })

        return profile

    def update_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update candidate and user profile fields."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        # Update user fields
        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        if "phone" in data:
            user.phone = data["phone"]
        if "bio" in data:
            user.bio = data["bio"]
        if "username" in data:
            user.username = data["username"]

        # Update candidate fields
        candidate = self.cand_repo.get_by_user_id(user_id)
        if candidate:
            if "name" in data:
                candidate.name = data["name"]
            if "branch" in data:
                candidate.branch = data["branch"]
            if "graduation_year" in data:
                candidate.graduation_year = data["graduation_year"]

        self.db.flush()
        return self.get_profile(user_id)

    def list_applications(self, user_id: str) -> List[Dict[str, Any]]:
        """List all applications for a candidate with job and match details."""
        candidate = self.cand_repo.get_by_user_id(user_id)
        if not candidate:
            return []

        apps = self.app_repo.get_by_candidate_id(candidate.id)
        results = []
        for app in apps:
            d = app.to_dict()
            if app.job:
                d["job_title"] = app.job.title
                d["company_name"] = app.job.company_name
                d["job_location"] = app.job.location
                d["job_type"] = app.job.job_type
            if app.match_result:
                d["match_score"] = app.match_result.final_score
                d["matched_skills"] = app.match_result.matched_skills
            results.append(d)
        return results

    def get_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get candidate dashboard overview data."""
        profile = self.get_profile(user_id)
        applications = self.list_applications(user_id)

        candidate = self.cand_repo.get_by_user_id(user_id)
        current_resume = None
        if candidate:
            resume = self.resume_repo.get_current_resume(candidate.id)
            if resume:
                current_resume = {
                    "id": resume.id,
                    "filename": resume.original_filename,
                    "version": resume.version,
                    "extracted_skills": resume.extracted_skills or [],
                    "ats_score": resume.ats_score,
                    "parser_status": resume.parser_status,
                }

        # Application stats
        total_apps = len(applications)
        active_apps = sum(1 for a in applications if a.get("stage") not in ("rejected", "hired"))
        interviews = sum(1 for a in applications if a.get("stage") in ("interview", "technical", "final"))

        return {
            "profile": profile,
            "current_resume": current_resume,
            "application_stats": {
                "total": total_apps,
                "active": active_apps,
                "interviews_scheduled": interviews,
            },
            "recent_applications": applications[:10],
        }
