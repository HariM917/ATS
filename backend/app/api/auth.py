"""
TalentFlow AI — Auth & Job API v1 Blueprints
"""
from typing import Optional
import re
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

# Sensible validation regexes
NAME_REGEX = re.compile(r"^[A-Za-z][A-Za-z0-9 .'_ -]{2,49}$")
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,64}$")

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
        return jsonify({"status": "error", "message": "Email, password, and full name are required"}), 400

    if not NAME_REGEX.match(username):
        return jsonify({
            "status": "error",
            "message": "Full name must be 3–50 characters (letters, spaces, and common name punctuation)."
        }), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({
            "status": "error",
            "message": "Please enter a valid email address."
        }), 400

    if not PASSWORD_REGEX.match(password):
        return jsonify({
            "status": "error",
            "message": "Password must be 8–64 characters and include at least one letter, one number, and one special character (@$!%*#?&)."
        }), 400

    if role not in ("candidate", "hr", "admin"):
        return jsonify({"status": "error", "message": "Invalid role specified"}), 400

    with get_db_context() as db:
        if db.query(User).filter_by(email=email).first():
            return jsonify({"status": "error", "message": "Email already registered. Please sign in instead."}), 409

        # Default org if recruiter
        default_org = db.query(Organization).filter_by(slug="default-org").first()
        org_id: Optional[str] = str(default_org.id) if default_org and role in ("hr", "admin") else None

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

        token = create_access_token(str(user.id), email, role, username, organization_id=org_id)
        refresh = create_refresh_token(str(user.id), email, role)

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
    email = (data.get("email") or data.get("username") or "").strip().lower()
    password = data.get("password", "").strip()
    role = data.get("role")

    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400
    if not password:
        return jsonify({"status": "error", "message": "Password is required"}), 400

    with get_db_context() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"status": "error", "message": "Account not found. Please register first."}), 401

        # Role verification if role is specified
        if role and str(user.role) != str(role):
            return jsonify({
                "status": "error",
                "message": f"Account exists, but is registered as a '{user.role}'. Please select the '{str(user.role).upper()}' role tab."
            }), 401

        if not verify_password(password, str(user.password_hash)):
            return jsonify({"status": "error", "message": "Invalid password credentials"}), 401

        user_id = str(user.id)
        user_email = str(user.email)
        user_role = str(user.role)
        user_name = str(user.username) if user.username is not None else user_email
        user_org_id: Optional[str] = str(user.organization_id) if user.organization_id is not None else None

        token = create_access_token(
            user_id, user_email, user_role, user_name,
            organization_id=user_org_id
        )
        refresh = create_refresh_token(user_id, user_email, user_role)

        return jsonify({
            "status": "success",
            "role": user_role,
            "user": user_name,
            "email": user_email,
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
    user_id = str(payload.get("sub") or "")
    email = str(payload.get("email") or "")
    role = str(payload.get("role") or "candidate")

    if not user_id or not email:
        return jsonify({"status": "error", "message": "Invalid token payload"}), 401

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
@jobs_v1.route("/all_jobs", methods=["GET"])
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


@jobs_v1.route("/<job_id>/apply", methods=["POST"])
@require_auth
def job_apply_alias(job_id):
    from .endpoints import apply_to_job
    return apply_to_job(job_id)


@jobs_v1.route("/<job_id>/applications", methods=["GET"])
@require_hr
def get_job_applications(job_id):
    with get_db_context() as db:
        app_service = ApplicationService(db)
        apps = app_service.list_by_job(job_id)
        return jsonify({"status": "success", "applications": apps})
