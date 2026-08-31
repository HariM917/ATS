"""
TalentFlow AI — Candidate and Recruiter Profiles
"""
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Candidate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "candidates"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    branch = Column(String(100), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    headline = Column(String(200), nullable=True)
    location = Column(String(100), nullable=True)
    linkedin_url = Column(String(300), nullable=True)
    github_url = Column(String(300), nullable=True)
    portfolio_url = Column(String(300), nullable=True)

    # Relationships
    user = relationship("User", back_populates="candidate_profile")
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")


class Recruiter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recruiters"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    recruiter_name = Column(String(150), nullable=False)
    company_name = Column(String(150), nullable=False)
    department = Column(String(100), nullable=True)
    title = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="recruiter_profile")
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")
