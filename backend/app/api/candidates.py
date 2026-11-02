"""
TalentFlow AI — Candidate Profile & Application Tracking API v1
"""
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import require_auth, current_user
from ..services.candidate_service import CandidateService

logger = logging.getLogger(__name__)

candidates_v1 = Blueprint("candidates_v1", __name__)


@candidates_v1.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    """Get the authenticated candidate's profile (guaranteed 200 via auto-provisioning)."""
    user = current_user()
    with get_db_context() as db:
        service = CandidateService(db)
        profile = service.get_profile(user.get("id"), email=user.get("email"), user_claims=user)
        resp = {
            "status": "success",
            "success": True,
            "data": profile,
            "profile": profile
        }
        resp.update(profile)
        return jsonify(resp)


@candidates_v1.route("/profile", methods=["PUT"])
@require_auth
def update_profile():
    """Update the authenticated candidate's profile."""
    user = current_user()
    data = request.get_json(silent=True) or {}
    with get_db_context() as db:
        service = CandidateService(db)
        profile = service.update_profile(user.get("id"), data, email=user.get("email"), user_claims=user)
        resp = {
            "status": "success",
            "success": True,
            "data": profile,
            "profile": profile
        }
        resp.update(profile)
        return jsonify(resp)


@candidates_v1.route("/applications", methods=["GET"])
@require_auth
def list_my_applications():
    """List all applications submitted by the authenticated candidate with status."""
    user = current_user()
    with get_db_context() as db:
        service = CandidateService(db)
        apps = service.list_applications(user.get("id"), email=user.get("email"))
        return jsonify({
            "status": "success",
            "data": apps,
            "applications": apps
        })


@candidates_v1.route("/dashboard", methods=["GET"])
@require_auth
def candidate_dashboard():
    """Get candidate dashboard overview: profile, resume status, applications, recommendations."""
    user = current_user()
    with get_db_context() as db:
        service = CandidateService(db)
        dashboard = service.get_dashboard(user.get("id"), email=user.get("email"), user_claims=user)
        return jsonify({
            "status": "success",
            "data": dashboard
        })


@candidates_v1.route("", methods=["GET"])
@require_auth
def list_candidates():
    """List candidates for recruiters/HR with search, filter, and resume info."""
    search = request.args.get("search", "").strip()
    skill_filter = request.args.get("skill", "").strip()
    with get_db_context() as db:
        service = CandidateService(db)
        candidates = service.list_all_candidates(search=search, skill=skill_filter)
        return jsonify({
            "status": "success",
            "data": candidates,
            "candidates": candidates
        })

