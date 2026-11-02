"""
TalentFlow AI — Canonical API v1 Blueprints Registration
Exporting all versioned endpoints: Auth, Candidates, Resumes, Matching, Jobs, Applications, Chat, Analytics, and Health.
"""
from .auth import auth_v1
from .candidates import candidates_v1
from .resumes import resumes_v1
from .matching import matching_v1
from .jobs import jobs_v1
from .applications import apps_v1
from .chat import chat_v1
from .analytics import analytics_v1
from .health import health_v1
from .roles import roles_v1

__all__ = [
    "auth_v1",
    "candidates_v1",
    "resumes_v1",
    "matching_v1",
    "jobs_v1",
    "apps_v1",
    "chat_v1",
    "analytics_v1",
    "health_v1",
    "roles_v1",
]
