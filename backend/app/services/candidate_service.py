"""
TalentFlow AI — Candidate Profile, Application Tracking, and Dashboard Service
"""
import uuid
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

    def get_profile(
        self,
        user_id: Any,
        email: Optional[str] = None,
        user_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get candidate profile with associated user info, self-healing missing records."""
        user = None
        if user_id:
            user = self.user_repo.get_by_id(user_id)
        if not user and email:
            user = self.user_repo.get_by_email(email)

        # Self-heal user record if session has a valid JWT but user row is missing (e.g. ephemeral DB restart)
        if not user and user_claims and user_claims.get("email"):
            claim_id = str(user_claims.get("id") or user_id or uuid.uuid4())
            claim_email = str(user_claims.get("email")).strip().lower()
            claim_role = str(user_claims.get("role") or "candidate")
            claim_username = str(user_claims.get("user") or claim_email.split("@")[0])
            logger.info(f"[PROFILE] Self-healing user record for {claim_email} (id={claim_id})")
            user = User(
                id=claim_id,
                email=claim_email,
                password_hash="",
                role=claim_role,
                username=claim_username,
                is_active=True,
                organization_id=user_claims.get("org_id")
            )
            self.db.add(user)
            self.db.flush()

        if not user:
            raise NotFoundError("User not found")

        # Auto-provision Candidate profile if missing
        candidate = self.cand_repo.get_by_user_id(str(user.id))
        user_role = str(user.role or "")
        user_email_str = str(user.email or "")
        if not candidate and user_role == "candidate":
            logger.info(f"[PROFILE] Auto-provisioning Candidate profile for user {user.id}")
            candidate_name = str(user.username or (user_email_str.split("@")[0] if user_email_str else "Candidate"))
            candidate = Candidate(
                user_id=str(user.id),
                name=candidate_name,
                branch="",
                graduation_year=None
            )
            self.db.add(candidate)
            self.db.flush()

        profile: Dict[str, Any] = {
            "user_id": str(user.id),
            "email": str(user.email or ""),
            "username": str(user.username or ""),
            "first_name": str(user.first_name or ""),
            "last_name": str(user.last_name or ""),
            "phone": str(user.phone or ""),
            "bio": str(user.bio or ""),
            "avatar_url": str(user.avatar_url or ""),
            "role": str(user.role or ""),
        }

        if candidate:
            profile.update({
                "candidate_id": str(candidate.id),
                "name": str(candidate.name or ""),
                "branch": str(candidate.branch or ""),
                "graduation_year": candidate.graduation_year,
            })

        return profile

    def update_profile(
        self,
        user_id: Any,
        data: Dict[str, Any],
        email: Optional[str] = None,
        user_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update candidate and user profile fields, ensuring records exist."""
        profile = self.get_profile(user_id, email=email, user_claims=user_claims)
        user = self.user_repo.get_by_id(profile["user_id"])
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
        candidate = self.cand_repo.get_by_user_id(str(user.id))
        user_role = str(user.role or "")
        user_email_str = str(user.email or "")
        if not candidate and user_role == "candidate":
            default_cand_name = str(data.get("name") or user.username or (user_email_str.split("@")[0] if user_email_str else "Candidate"))
            candidate = Candidate(
                user_id=str(user.id),
                name=default_cand_name,
                branch=data.get("branch", ""),
                graduation_year=data.get("graduation_year")
            )
            self.db.add(candidate)
            self.db.flush()
        elif candidate:
            if "name" in data:
                candidate.name = data["name"]
            if "branch" in data:
                candidate.branch = data["branch"]
            if "graduation_year" in data:
                candidate.graduation_year = data["graduation_year"]

        self.db.flush()
        return self.get_profile(str(user.id), email=user_email_str if user_email_str else None)

    def list_applications(self, user_id: Any, email: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all applications for a candidate with job and match details."""
        candidate = self.cand_repo.get_by_user_id(str(user_id))
        if not candidate and email:
            user = self.user_repo.get_by_email(email)
            if user:
                candidate = self.cand_repo.get_by_user_id(str(user.id))
        if not candidate:
            return []

        apps = self.app_repo.get_by_candidate_id(str(candidate.id))
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

    def get_dashboard(
        self,
        user_id: Any,
        email: Optional[str] = None,
        user_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get candidate dashboard overview data."""
        profile = self.get_profile(user_id, email=email, user_claims=user_claims)
        applications = self.list_applications(profile["user_id"], email=profile.get("email"))

        candidate = self.cand_repo.get_by_user_id(profile["user_id"])
        current_resume = None
        if candidate:
            resume = self.resume_repo.get_current_resume(str(candidate.id))
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
