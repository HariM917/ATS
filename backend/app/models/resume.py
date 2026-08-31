"""
TalentFlow AI — Versioned Resume Storage and Parsing Metadata
"""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Resume(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resumes"

    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    file_hash_sha256 = Column(String(64), nullable=True, index=True)
    mime_type = Column(String(100), default="application/pdf")

    # Parsed Content & Extracted AI Metadata
    raw_text = Column(Text, nullable=True)
    extracted_skills = Column(JSON, default=list, nullable=False)  # List of skill strings
    categorized_skills = Column(JSON, default=dict, nullable=False)  # Skills grouped by domain
    predicted_role = Column(String(100), nullable=True)
    years_of_experience = Column(Float, default=0.0)
    sections = Column(JSON, default=dict, nullable=False)  # Extracted sections: skills, experience, etc.

    # Resume Health Analysis (ATS Compatibility)
    ats_score = Column(Float, default=0.0)
    health_analysis = Column(JSON, default=dict, nullable=False)

    # Parsing execution status
    parser_status = Column(String(50), default="completed", nullable=False)  # pending, processing, completed, failed
    parser_version = Column(String(50), default="v3.1", nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")
    match_results = relationship("MatchResult", back_populates="resume")
