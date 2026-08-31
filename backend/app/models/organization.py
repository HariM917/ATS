"""
TalentFlow AI — Organization Model (Multi-tenancy Root)
"""
from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organizations"

    name = Column(String(150), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    domain = Column(String(100), nullable=True)
    logo_url = Column(String(500), nullable=True)
    settings = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
