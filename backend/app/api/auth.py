"""
TalentFlow AI — Auth & Job API v1 Blueprints
"""
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import (
    create_access_token, create_refresh_token, decode_token,
    revoke_token, require_auth, require_hr, current_user,
    hash_password, verify_password
)
from ..models import User, Candidate, Recruiter, Organization
from ..services.job_service import JobService, ApplicationService
from ..core.exceptions import ValidationError, AuthenticationError, ConflictError

logger = logging.getLogger(__name__)

auth_v1 = Blueprint("auth_v1", __name__)
jobs_v1 = Blueprint("jobs_v1", __name__)


@auth_v1.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    username = data.get("username", "").strip()
    role = data.get("role", "candidate")

    if not email or not password or not username:
        return jsonify({"status": "error", "message": "Email, password, and username are required"}), 400
    if len(password) < 6:
        return jsonify({"status": "error", "message": "Password must be at least 6 characters"}), 400

    with get_db_context() as db:
        if db.query(User).filter_by(email=email).first():
            return jsonify({"status": "error", "message": "Email already registered"}), 409

        # Default org if recruiter
        default_org = db.query(Organization).filter_by(slug="default-org").first()
        org_id = default_org.id if default_org and role in ("hr", "admin") else None

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            username=username,
            organization_id=org_id
        )
        db.add(user)
        db.flush()

        if role == "hr":
            rec = Recruiter(
                user_id=user.id,
                recruiter_name=username,
                company_name=data.get("company_name", "TalentFlow")
            )
            db.add(rec)
        else:
            cand = Candidate(
                user_id=user.id,
                name=username,
                branch=data.get("branch"),
                graduation_year=data.get("graduation_year")
            )
            db.add(cand)

        token = create_access_token(user.id, email, role, username, organization_id=org_id)
        refresh = create_refresh_token(user.id, email, role)

        return jsonify({
            "status": "success",
            "role": role,
            "user": username,
            "email": email,
            "token": token,
            "refresh_token": refresh
        }), 201


@auth_v1.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    with get_db_context() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"status": "error", "message": "Account not found. Please register first."}), 401

        if password and not verify_password(password, user.password_hash):
            return jsonify({"status": "error", "message": "Invalid password credentials"}), 401

        token = create_access_token(
            user.id, user.email, user.role, user.username or user.email,
            organization_id=user.organization_id
        )
        refresh = create_refresh_token(user.id, user.email, user.role)

        return jsonify({
            "status": "success",
            "role": user.role,
            "user": user.username or user.email,
            "email": user.email,
            "token": token,
            "refresh_token": refresh
        })


@auth_v1.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return jsonify({"status": "error", "message": "refresh_token required"}), 400

    payload = decode_token(refresh_token, is_refresh=True)
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    token = create_access_token(user_id, email, role)
    new_refresh = create_refresh_token(user_id, email, role)
    revoke_token(refresh_token)

    return jsonify({
        "status": "success",
        "token": token,
        "refresh_token": new_refresh
    })


@auth_v1.route("/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        revoke_token(auth_header[7:].strip())
    return jsonify({"status": "success", "message": "Logged out successfully"})


# --- Jobs Routes ---

@jobs_v1.route("", methods=["GET"])
def list_jobs():
    with get_db_context() as db:
        service = JobService(db)
        jobs = service.list_jobs()
        return jsonify({"status": "success", "jobs": jobs})


@jobs_v1.route("", methods=["POST"])
@require_hr
def create_job():
    user = current_user()
    data = request.get_json() or {}
    with get_db_context() as db:
        service = JobService(db)
        job = service.create_job(user["id"], data)
        return jsonify({"status": "success", "job": job}), 201


@jobs_v1.route("/<job_id>", methods=["GET"])
def get_job(job_id):
    with get_db_context() as db:
        service = JobService(db)
        job = service.get_job(job_id)
        return jsonify({"status": "success", "job": job})


@jobs_v1.route("/<job_id>", methods=["DELETE"])
@require_hr
def delete_job(job_id):
    user = current_user()
    with get_db_context() as db:
        service = JobService(db)
        service.delete_job(job_id, user["id"])
        return jsonify({"status": "success", "message": "Job deleted successfully"})


@jobs_v1.route("/<job_id>/applications", methods=["GET"])
@require_hr
def get_job_applications(job_id):
    with get_db_context() as db:
        app_service = ApplicationService(db)
        apps = app_service.list_by_job(job_id)
        return jsonify({"status": "success", "applications": apps})
