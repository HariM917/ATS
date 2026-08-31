"""
TalentFlow AI — SQLAlchemy Base Model and Mixins
Provides UUID primary keys, timestamp tracking, tenant-isolation, and serialization.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Root declarative base class for all TalentFlow AI models."""

    def to_dict(self) -> Dict[str, Any]:
        """Generic dictionary serializer for model attributes."""
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            elif isinstance(val, uuid.UUID):
                val = str(val)
            result[col.name] = val
        return result


class UUIDPrimaryKeyMixin:
    """Provides a UUID string primary key."""
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )


class TimestampMixin:
    """Provides automatic created_at and updated_at UTC timestamps."""
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class TenantMixin:
    """Enforces multi-tenancy isolation by associating records with an organization."""
    @declared_attr
    def organization_id(cls):
        return Column(
            String(36),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=True,
            index=True
        )


class SoftDeleteMixin:
    """Provides soft-deletion support."""
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
