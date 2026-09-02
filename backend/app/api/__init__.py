"""
TalentFlow AI — API v1 Blueprints Registration
"""
from .auth import auth_v1, jobs_v1
from .endpoints import apps_v1, matching_v1, chat_v1, analytics_v1, health_v1
from .resumes import resumes_v1
from .candidates import candidates_v1

__all__ = [
    "auth_v1",
    "jobs_v1",
    "apps_v1",
    "matching_v1",
    "chat_v1",
    "analytics_v1",
    "health_v1",
    "resumes_v1",
    "candidates_v1",
]

