"""
TalentFlow AI — Job, Application, and Candidate Core Services
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import Job, Application, Candidate, Recruiter, User, Resume, Organization, Notification
from ..repositories import JobRepository, ApplicationRepository, CandidateRepository, UserRepository, ResumeRepository
from ..core.exceptions import NotFoundError, ValidationError, PermissionDeniedError
from .email_service import email_service

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = JobRepository(db)
        self.user_repo = UserRepository(db)

    def list_jobs(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        jobs = self.job_repo.get_active_jobs(organization_id=organization_id)
        return [j.to_dict() for j in jobs]

    def get_job(self, job_id: str) -> Dict[str, Any]:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")
        return job.to_dict()

    def create_job(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.recruiter_profile:
            # Fallback or auto-create recruiter profile if missing
            recruiter = self.db.query(Recruiter).filter_by(user_id=str(user_id)).first()
            if not recruiter:
                recruiter = Recruiter(
                    user_id=str(user_id),
                    recruiter_name=user.username if user else "Recruiter",
                    company_name=data.get("company_name", "TalentFlow")
                )
                self.db.add(recruiter)
                self.db.flush()
        else:
            recruiter = user.recruiter_profile

        job = self.job_repo.create(
            recruiter_id=recruiter.id,
            organization_id=user.organization_id if user else None,
            title=data["title"],
            description=data["description"],
            required_skills=data.get("required_skills", ""),
            experience_required=data.get("experience_required", 0),
            location=data.get("location", "Remote"),
            job_type=data.get("job_type", "Full-time"),
            salary=data.get("salary", ""),
            department=data.get("department", ""),
            company_name=data.get("company_name", recruiter.company_name),
            scoring_config=data.get("scoring_config", {
                "semantic": 0.25,
                "skills": 0.40,
                "projects": 0.15,
                "experience": 0.10,
                "education": 0.10
            }),
            status="active"
        )
        return job.to_dict()

    def delete_job(self, job_id: str, user_id: str) -> bool:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")
        return self.job_repo.delete(job)


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.app_repo = ApplicationRepository(db)
        self.job_repo = JobRepository(db)
        self.cand_repo = CandidateRepository(db)
        self.user_repo = UserRepository(db)

    def apply(self, user_id: str, job_id: str, resume_path: Optional[str] = None) -> Dict[str, Any]:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found")

        candidate = self.cand_repo.get_by_user_id(user_id)
        if not candidate:
            user = self.user_repo.get_by_id(user_id)
            candidate = Candidate(
                user_id=str(user_id),
                name=user.username if user else "Candidate"
            )
            self.db.add(candidate)
            self.db.flush()

        existing = self.app_repo.get_by_job_and_candidate(job_id, candidate.id)
        if existing:
            return existing.to_dict()

        # Check candidate resume
        resume = self.db.query(Resume).filter_by(candidate_id=candidate.id, is_current=True).first()

        app = self.app_repo.create(
            job_id=job.id,
            candidate_id=candidate.id,
            resume_id=resume.id if resume else None,
            status="applied",
            stage="applied",
            score=0.85  # Initial baseline
        )

        # Notify via Email
        cand_user = self.user_repo.get_by_id(candidate.user_id)
        if cand_user and cand_user.email:
            email_service.send_application_received(cand_user.email, candidate.name, job.title)

        return app.to_dict()

    def update_stage(self, application_id: str, stage: str, notes: Optional[str] = None) -> Dict[str, Any]:
        app = self.app_repo.get_by_id(application_id)
        if not app:
            raise NotFoundError("Application not found")

        app.stage = stage.lower()
        app.status = stage.lower()
        if notes:
            app.notes = notes
        self.db.flush()

        # Send status update notification
        if app.candidate and app.candidate.user and app.candidate.user.email:
            email_service.send_status_update(
                app.candidate.user.email,
                app.candidate.name,
                app.job.title if app.job else "Job Position",
                stage
            )

        return app.to_dict()

    def list_by_job(self, job_id: str) -> List[Dict[str, Any]]:
        apps = self.app_repo.get_by_job_id(job_id)
        results = []
        for a in apps:
            d = a.to_dict()
            d["candidate_name"] = a.candidate.name if a.candidate else "Applicant"
            d["email"] = a.candidate.user.email if a.candidate and a.candidate.user else ""
            d["branch"] = a.candidate.branch if a.candidate else None
            d["graduation_year"] = a.candidate.graduation_year if a.candidate else None
            results.append(d)
        return results
