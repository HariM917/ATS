"""
TalentFlow AI — Match Results and Explainable AI Reasoning
Persists multidimensional scoring vectors, matched/missing skill lists, and human-readable explanations.
"""
from sqlalchemy import Column, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class MatchResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "match_results"

    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True, index=True)
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)

    # Scores
    final_score = Column(Float, default=0.0, nullable=False, index=True)
    semantic_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    projects_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)

    # Skill breakdown
    matched_skills = Column(JSON, default=list, nullable=False)
    missing_skills = Column(JSON, default=list, nullable=False)
    partial_skills = Column(JSON, default=list, nullable=False)

    # Explainable AI summary (reasons for score, strengths, improvement areas)
    explanation = Column(JSON, default=dict, nullable=False)

    # Metadata & Versioning
    model_version = Column(String(50), default="mpnet-base-v2", nullable=False)
    scoring_version = Column(String(50), default="calibrated-v3.1", nullable=False)

    # Relationships
    job = relationship("Job", back_populates="match_results")
    candidate = relationship("Candidate", back_populates="match_results")
    resume = relationship("Resume", back_populates="match_results")
    application = relationship("Application", back_populates="match_result")
