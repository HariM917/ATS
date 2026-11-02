"""
TalentFlow AI — Controlled Role Catalog Model
Maps occupational domains to granular, specific industry job roles.
"""
from sqlalchemy import Column, String, Boolean, JSON, Text
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class RoleCatalog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"

    name = Column(String(150), nullable=False, unique=True, index=True)
    slug = Column(String(150), nullable=False, unique=True, index=True)
    occupational_class = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    aliases = Column(JSON, default=list, nullable=False)
    required_skills_default = Column(JSON, default=list, nullable=False)
    experience_level = Column(String(50), default="Mid-Level", nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    def to_dict(self):
        skills = self.required_skills_default or []
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "domain": self.occupational_class,
            "occupational_class": self.occupational_class,
            "description": self.description or "",
            "aliases": self.aliases or [],
            "required_skills_default": skills,
            "skills": skills,
            "experience_level": self.experience_level,
            "active": self.active,
        }

