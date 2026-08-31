"""
TalentFlow AI — Notification, Audit Log, and Chat Models
"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), default="info", nullable=False)  # info, status_update, match_alert, system
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    link = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_id = Column(String(36), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # user_login, job_created, status_change, etc.
    entity_type = Column(String(50), nullable=False)  # job, application, resume, user
    entity_id = Column(String(36), nullable=True)
    ip_address = Column(String(45), nullable=True)
    request_id = Column(String(36), nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")


class ChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(50), default="user", nullable=False)  # user, assistant, system
    user_text = Column(Text, nullable=False)
    ai_text = Column(Text, nullable=False)
    sources = Column(JSON, default=list, nullable=False)  # Retrieved RAG context references
    sentiment = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="chat_history")
