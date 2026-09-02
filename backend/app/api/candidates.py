"""
TalentFlow AI — Candidate Profile & Application Tracking API v1
"""
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import require_auth, current_user
from ..services.candidate_service import CandidateService
from ..core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

candidates_v1 = Blueprint("candidates_v1", __name__)


@candidates_v1.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    """Get the authenticated candidate's profile."""
    user = current_user()
    with get_db_context() as db:
        service = CandidateService(db)
        profile = service.get_profile(user["id"])
        return jsonify({"status": "success", "profile": profile})


@candidates_v1.route("/profile", methods=["PUT"])
@require_auth
def update_profile():
    """Update the authenticated candidate's profile."""
    user = current_user()
    data = request.get_json() or {}
    with get_db_context() as db:
        service = CandidateService(db)
        profile = service.update_profile(user["id"], data)
        return jsonify({"status": "success", "profile": profile})


@candidates_v1.route("/applications", methods=["GET"])
@require_auth
def list_my_applications():
    """List all applications submitted by the authenticated candidate with status."""
    user = current_user()
    with get_db_context() as db:
        service = CandidateService(db)
        apps = service.list_applications(user["id"])
        return jsonify({"status": "success", "applications": apps})


@candidates_v1.route("/dashboard", methods=["GET"])
@require_auth
def candidate_dashboard():
    """Get candidate dashboard overview: profile, resume status, applications, recommendations."""
    user = current_user()
    with get_db_context() as db:
        service = CandidateService(db)
        dashboard = service.get_dashboard(user["id"])
        return jsonify({"status": "success", "data": dashboard})
