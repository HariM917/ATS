"""
TalentFlow AI — Application Pipeline and Candidate Progression
Supports modern 8-stage Kanban recruitment pipeline:
applied -> screening -> shortlisted -> interview -> technical -> final -> offer -> hired (or rejected).
"""
from sqlalchemy import Column, String, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Application(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "applications"

    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)

    # Legacy & Pipeline Status
    status = Column(String(50), default="applied", nullable=False, index=True)  # applied, screening, shortlisted, interview, technical, final, offer, hired, rejected
    stage = Column(String(50), default="applied", nullable=False, index=True)
    score = Column(Float, default=0.0, nullable=False, index=True)

    # Recruiter notes & evaluation metadata
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    interview_scheduled_at = Column(String(50), nullable=True)
    rejection_reason = Column(String(300), nullable=True)

    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
    match_result = relationship("MatchResult", back_populates="application", uselist=False, cascade="all, delete-orphan")
