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

    def list_jobs(self, organization_id: Optional[str] = None, hr_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List published jobs for candidates or all owned jobs for an HR recruiter."""
        if hr_user_id:
            recruiter = self.db.query(Recruiter).filter_by(user_id=hr_user_id).first()
            if recruiter:
                jobs = self.db.query(Job).filter(Job.recruiter_id == recruiter.id).order_by(Job.created_at.desc()).all()
                return [j.to_dict() for j in jobs]

        # Candidate-visible jobs must be published/active and have valid recruiter and organization
        q = self.db.query(Job).filter(
            Job.status.in_(["published", "active"]),
            Job.recruiter_id.isnot(None),
            Job.organization_id.isnot(None)
        )
        if organization_id:
            q = q.filter(Job.organization_id == organization_id)
        jobs = q.order_by(Job.created_at.desc()).all()
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
            recruiter = self.db.query(Recruiter).filter_by(user_id=user_id).first()
            if not recruiter:
                rec_name = (user.username if user and user.username else None) or (user.email.split('@')[0] if user and user.email else "Recruiter")
                recruiter = Recruiter(
                    user_id=user_id,
                    recruiter_name=rec_name,
                    company_name=data.get("company_name", "TalentFlow")
                )
                self.db.add(recruiter)
                self.db.flush()
        else:
            recruiter = user.recruiter_profile

        # Guarantee organization association for recruiter
        org_id = str(user.organization_id) if user and user.organization_id else None
        if not org_id:
            default_org = self.db.query(Organization).first()
            if not default_org:
                default_org = Organization(
                    name=data.get("company_name", "TalentFlow"),
                    slug=f"org-{uuid.uuid4().hex[:8]}"
                )
                self.db.add(default_org)
                self.db.flush()
            org_id = str(default_org.id)
            if user:
                setattr(user, "organization_id", org_id)
                self.db.flush()

        initial_status = data.get("status", "published")
        if initial_status not in ("draft", "published", "active"):
            initial_status = "published"

        job = self.job_repo.create(
            recruiter_id=str(recruiter.id),
            organization_id=org_id,
            title=data["title"],
            description=data["description"],
            occupational_class=data.get("occupational_class"),
            specific_role=data.get("specific_role"),
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
            status=initial_status
        )
        return job.to_dict()

    def publish_job(self, job_id: str, user_id: str) -> Dict[str, Any]:
        """Publish a job posting so it becomes visible to candidates."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")
        recruiter = self.db.query(Recruiter).filter_by(user_id=user_id).first()
        if recruiter and job.recruiter_id != recruiter.id:
            raise PermissionDeniedError("You are not authorized to publish this job")
        setattr(job, "status", "published")
        self.db.flush()
        return job.to_dict()

    def delete_job(self, job_id: str, user_id: str) -> bool:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")
        return self.job_repo.delete(job)

    def update_job(self, job_id: str, data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")
        
        updatable_fields = [
            "title", "description", "occupational_class", "specific_role",
            "required_skills", "experience_required", "location", "job_type",
            "salary", "department", "company_name", "scoring_config", "status"
        ]
        for field in updatable_fields:
            if field in data:
                setattr(job, field, data[field])
        
        self.db.flush()
        return job.to_dict()


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.app_repo = ApplicationRepository(db)
        self.job_repo = JobRepository(db)
        self.cand_repo = CandidateRepository(db)
        self.user_repo = UserRepository(db)

    def apply(self, user_id: str, job_id: str, resume_path: Optional[str] = None, resume_id: Optional[str] = None) -> Dict[str, Any]:
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found")

        candidate = self.cand_repo.get_by_user_id(user_id)
        if not candidate:
            user = self.user_repo.get_by_id(user_id)
            cand_name = (user.username if user and user.username else None) or (user.email.split('@')[0] if user and user.email else "Candidate")
            candidate = Candidate(
                user_id=user_id,
                name=cand_name
            )
            self.db.add(candidate)
            self.db.flush()

        existing = self.app_repo.get_by_job_and_candidate(job_id, str(candidate.id))
        if existing:
            return existing.to_dict()

        # Check candidate resume
        resume = None
        if resume_id:
            resume = self.db.query(Resume).filter_by(id=resume_id).first()
        if not resume:
            resume = self.db.query(Resume).filter_by(candidate_id=candidate.id, is_current=True).first()

        app = self.app_repo.create(
            job_id=str(job.id),
            candidate_id=str(candidate.id),
            resume_id=str(resume.id) if resume else None,
            status="applied",
            stage="applied",
            score=0.85  # Initial baseline
        )

        # Notify via Email
        cand_user = self.user_repo.get_by_id(str(candidate.user_id))
        if cand_user and cand_user.email:
            email_service.send_application_received(
                str(cand_user.email),
                str(candidate.name),
                str(job.title)
            )

        return app.to_dict()

    def update_stage(self, application_id: str, stage: str, notes: Optional[str] = None) -> Dict[str, Any]:
        app = self.app_repo.get_by_id(application_id)
        if not app:
            raise NotFoundError("Application not found")

        setattr(app, "stage", stage.lower())
        setattr(app, "status", stage.lower())
        if notes:
            setattr(app, "notes", notes)
        self.db.flush()

        # Send status update notification
        if app.candidate and app.candidate.user and app.candidate.user.email:
            email_service.send_status_update(
                str(app.candidate.user.email),
                str(app.candidate.name),
                str(app.job.title if app.job else "Job Position"),
                stage
            )

        return app.to_dict()

    def get_application(self, application_id: str) -> Dict[str, Any]:
        app = self.app_repo.get_by_id(application_id)
        if not app:
            raise NotFoundError("Application not found")
        d = app.to_dict()
        if app.candidate:
            d["candidate_name"] = app.candidate.name
            d["email"] = app.candidate.user.email if app.candidate.user else ""
            d["branch"] = app.candidate.branch
            d["graduation_year"] = app.candidate.graduation_year
        if app.job:
            d["job_title"] = app.job.title
            d["company_name"] = app.job.company_name
        return d

    def list_applications_for_user(self, user_id: str, is_hr: bool = False) -> List[Dict[str, Any]]:
        results = []
        if is_hr:
            apps = self.db.query(Application).order_by(Application.created_at.desc()).all()
        else:
            candidate = self.cand_repo.get_by_user_id(user_id)
            if not candidate:
                return []
            apps = self.app_repo.get_by_candidate_id(str(candidate.id))

        for a in apps:
            d = a.to_dict()
            if a.candidate:
                d["candidate_name"] = a.candidate.name
                d["email"] = a.candidate.user.email if a.candidate.user else ""
                d["branch"] = a.candidate.branch
                d["graduation_year"] = a.candidate.graduation_year
            if a.job:
                d["job_title"] = a.job.title
                d["company_name"] = a.job.company_name
                d["location"] = a.job.location
            results.append(d)
        return results

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
