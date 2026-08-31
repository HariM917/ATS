"""
TalentFlow AI — Job Posting Model
Includes configurable scoring weights (JSONB), tenant isolation, and status tracking.
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin


class Job(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantMixin):
    __tablename__ = "jobs"

    recruiter_id = Column(String(36), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    company_name = Column(String(150), nullable=True)
    branch = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=True)
    experience_required = Column(Integer, default=0, nullable=False)
    location = Column(String(100), default="Remote", nullable=False)
    job_type = Column(String(50), default="Full-time", nullable=False)  # Full-time, Part-time, Internship, Contract
    salary = Column(String(100), default="", nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)  # draft, active, paused, closed

    # Configurable Scoring Weights (stored per job for custom screening requirements)
    scoring_config = Column(
        JSON,
        default=lambda: {
            "semantic": 0.25,
            "skills": 0.40,
            "projects": 0.15,
            "experience": 0.10,
            "education": 0.10
        },
        nullable=False
    )

    # Relationships
    organization = relationship("Organization", back_populates="jobs")
    recruiter = relationship("Recruiter", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")
