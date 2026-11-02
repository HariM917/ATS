"""
TalentFlow AI — Authentication API v1 Blueprint
Supports registration with strict UX & backend regex validation,
PostgreSQL user lookup, bcrypt password verification, dual-token JWT lifecycle (access + refresh),
token refresh rotation, token revocation (logout), and /me identity lookup.
"""
import re
import logging
from typing import Optional
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import (
    create_access_token, create_refresh_token, decode_token,
    revoke_token, require_auth, current_user,
    hash_password, verify_password
)
from ..models import User, Candidate, Recruiter, Organization

logger = logging.getLogger(__name__)

# Canonical validation regexes per specification
NAME_REGEX = re.compile(r"^[A-Za-z][A-Za-z .'-]{2,49}$")
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,64}$")

auth_v1 = Blueprint("auth_v1", __name__)


@auth_v1.route("/register", methods=["POST"])
def register():
    """Register a new candidate or recruiter account with strict input validation."""
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()
    name = str(data.get("name") or data.get("username", "")).strip()
    role = str(data.get("role", "candidate")).strip().lower()

    if not email or not password or not name:
        return jsonify({
            "status": "error",
            "error_code": "VALIDATION_ERROR",
            "message": "Full name, email, and password are required."
        }), 400

    if not NAME_REGEX.match(name):
        return jsonify({
            "status": "error",
            "error_code": "INVALID_NAME",
            "message": "Full name must be 3–50 characters (letters, spaces, periods, apostrophes, and hyphens)."
        }), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({
            "status": "error",
            "error_code": "INVALID_EMAIL",
            "message": "Please enter a valid email address."
        }), 400

    if not PASSWORD_REGEX.match(password):
        return jsonify({
            "status": "error",
            "error_code": "WEAK_PASSWORD",
            "message": "Password must be 8–64 characters and include at least one letter, one number, and one special character (@$!%*#?&)."
        }), 400

    if role not in ("candidate", "hr", "admin"):
        return jsonify({
            "status": "error",
            "error_code": "INVALID_ROLE",
            "message": "Invalid role specified. Must be 'candidate' or 'hr'."
        }), 400

    with get_db_context() as db:
        if db.query(User).filter_by(email=email).first():
            return jsonify({
                "status": "error",
                "error_code": "EMAIL_EXISTS",
                "message": "Email already registered. An account with this email address already exists. Please sign in instead."
            }), 409

        # Default org if recruiter
        default_org = db.query(Organization).filter_by(slug="default-org").first()
        org_id: Optional[str] = str(default_org.id) if default_org and role in ("hr", "admin") else None

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            username=name,
            organization_id=org_id
        )
        db.add(user)
        db.flush()

        # Always provision the corresponding profile row
        if role == "hr":
            rec = Recruiter(
                user_id=user.id,
                recruiter_name=name,
                company_name=data.get("company_name", "TalentFlow")
            )
            db.add(rec)
        else:
            cand = Candidate(
                user_id=user.id,
                name=name,
                branch=data.get("branch", ""),
                graduation_year=data.get("graduation_year")
            )
            db.add(cand)

        token = create_access_token(str(user.id), email, role, name, organization_id=org_id)
        refresh = create_refresh_token(str(user.id), email, role)

        return jsonify({
            "status": "success",
            "role": role,
            "user": name,
            "email": email,
            "token": token,
            "refresh_token": refresh
        }), 201


@auth_v1.route("/login", methods=["POST"])
def login():
    """Authenticate existing user against PostgreSQL with bcrypt hash verification."""
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or data.get("username", "")).strip().lower()
    password = str(data.get("password", "")).strip()
    role = data.get("role")

    if not email:
        return jsonify({
            "status": "error",
            "error_code": "EMAIL_REQUIRED",
            "message": "Email is required."
        }), 400
    if not password:
        return jsonify({
            "status": "error",
            "error_code": "PASSWORD_REQUIRED",
            "message": "Password is required."
        }), 400

    with get_db_context() as db:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({
                "status": "error",
                "error_code": "ACCOUNT_NOT_FOUND",
                "message": "Account not found. Please register first."
            }), 401

        # Role verification if role is specified
        if role and str(user.role) != str(role):
            return jsonify({
                "status": "error",
                "error_code": "ROLE_MISMATCH",
                "message": f"Account exists, but is registered as a '{user.role}'. Please select the '{str(user.role).upper()}' role."
            }), 401

        if not verify_password(password, str(user.password_hash)):
            return jsonify({
                "status": "error",
                "error_code": "INVALID_CREDENTIALS",
                "message": "Invalid password credentials. Please check your password and try again."
            }), 401

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
    """Rotate JWT access token using a valid refresh token."""
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return jsonify({
            "status": "error",
            "error_code": "REFRESH_TOKEN_REQUIRED",
            "message": "refresh_token required"
        }), 400

    try:
        payload = decode_token(refresh_token, is_refresh=True)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "INVALID_REFRESH_TOKEN",
            "message": f"Invalid or expired refresh token: {e}"
        }), 401

    user_id = str(payload.get("sub") or "")
    email = str(payload.get("email") or "")
    role = str(payload.get("role") or "candidate")

    if not user_id or not email:
        return jsonify({
            "status": "error",
            "error_code": "INVALID_PAYLOAD",
            "message": "Invalid token payload"
        }), 401

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
    """Revoke authenticated session and blacklist current bearer token."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        revoke_token(auth_header[7:].strip())
    return jsonify({
        "status": "success",
        "message": "Logged out successfully"
    })


@auth_v1.route("/me", methods=["GET"])
@require_auth
def get_current_identity():
    """Return the authenticated user's identity details."""
    u = current_user()
    with get_db_context() as db:
        user = db.query(User).filter_by(id=u.get("id")).first()
        if not user:
            return jsonify({
                "status": "success",
                "user": {
                    "id": u.get("id"),
                    "email": u.get("email"),
                    "role": u.get("role"),
                    "name": u.get("user")
                }
            })

        candidate_id = None
        if user.candidate_profile:
            candidate_id = str(user.candidate_profile.id)

        return jsonify({
            "status": "success",
            "user": {
                "id": str(user.id),
                "email": str(user.email),
                "role": str(user.role),
                "name": str(user.username or user.email),
                "username": str(user.username or user.email),
                "candidate_id": candidate_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "bio": user.bio,
                "avatar_url": user.avatar_url
            }
        })
