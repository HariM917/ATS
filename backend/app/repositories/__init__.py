"""
TalentFlow AI — Domain Repositories
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from .base import BaseRepository
from ..models import User, Job, Candidate, Recruiter, Application, Resume, MatchResult, Organization, Notification, ChatMessage


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.strip().lower()).first()


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: Session):
        super().__init__(Job, db)

    def get_active_jobs(self, organization_id: Optional[str] = None) -> List[Job]:
        q = self.db.query(Job).filter(Job.status == "active")
        if organization_id:
            q = q.filter(Job.organization_id == organization_id)
        return q.order_by(desc(Job.created_at)).all()

    def get_by_recruiter(self, recruiter_id: str) -> List[Job]:
        return self.db.query(Job).filter(Job.recruiter_id == recruiter_id).order_by(desc(Job.created_at)).all()


class CandidateRepository(BaseRepository[Candidate]):
    def __init__(self, db: Session):
        super().__init__(Candidate, db)

    def get_by_user_id(self, user_id: str) -> Optional[Candidate]:
        return self.db.query(Candidate).filter(Candidate.user_id == str(user_id)).first()


class ApplicationRepository(BaseRepository[Application]):
    def __init__(self, db: Session):
        super().__init__(Application, db)

    def get_by_job_id(self, job_id: str) -> List[Application]:
        return self.db.query(Application).filter(Application.job_id == job_id).order_by(desc(Application.score)).all()

    def get_by_candidate_id(self, candidate_id: str) -> List[Application]:
        return self.db.query(Application).filter(Application.candidate_id == candidate_id).order_by(desc(Application.created_at)).all()

    def get_by_job_and_candidate(self, job_id: str, candidate_id: str) -> Optional[Application]:
        return self.db.query(Application).filter(
            Application.job_id == job_id,
            Application.candidate_id == candidate_id
        ).first()


class ResumeRepository(BaseRepository[Resume]):
    def __init__(self, db: Session):
        super().__init__(Resume, db)

    def get_current_resume(self, candidate_id: str) -> Optional[Resume]:
        return self.db.query(Resume).filter(
            Resume.candidate_id == candidate_id,
            Resume.is_current == True
        ).first()
