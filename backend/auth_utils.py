"""
FlowATS Authentication — Production v3.0
JWT-based auth with RBAC. Single source of truth for identity.
"""
import os
import time
import logging
from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import jsonify, request

import db_manager

# ============================================
# Configuration
# ============================================
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")

# ============================================
# JWT Token Management
# ============================================

def create_jwt(user_id: int, email: str, role: str, username: str = "") -> str:
    """Create a signed JWT token with user identity claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "user": username or email,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    """Decode and verify a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logging.warning("[AUTH] JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logging.warning(f"[AUTH] Invalid JWT: {e}")
        return None


def get_current_user() -> dict | None:
    """Extract authenticated user from the Authorization header.

    Returns dict: {id, email, role, user} or None if unauthenticated.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:].strip()
    if not token:
        return None

    payload = decode_jwt(token)
    if not payload:
        return None

    try:
        user_id_val = int(payload.get("sub"))
    except (TypeError, ValueError):
        user_id_val = payload.get("sub")

    return {
        "id": user_id_val,
        "email": payload.get("email"),
        "role": payload.get("role"),
        "user": payload.get("user", payload.get("email")),
    }


# ============================================
# Decorators
# ============================================

def require_auth(f):
    """Decorator: requires any valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or not user.get("email"):
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        # Inject user into request context
        request._current_user = user
        return f(*args, **kwargs)
    return decorated


def require_role(*allowed_roles):
    """Decorator factory: requires JWT with one of the allowed roles.

    Usage:
        @require_role("hr")
        @require_role("hr", "admin")
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user or not user.get("email"):
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            if user.get("role") not in allowed_roles:
                return jsonify({
                    "status": "error",
                    "message": f"Access denied. Required role: {', '.join(allowed_roles)}"
                }), 403
            request._current_user = user
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_hr(f):
    """Convenience decorator: shortcut for require_role('hr', 'admin')."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or not user.get("email"):
            return jsonify({"status": "error", "message": "HR authentication required"}), 401
        if user.get("role") not in ("hr", "admin"):
            return jsonify({"status": "error", "message": "HR access required"}), 403
        request._current_user = user
        return f(*args, **kwargs)
    return decorated


def require_admin_secret(f):
    """Decorator: requires admin secret header or body param."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not ADMIN_SECRET:
            return jsonify({"status": "error", "message": "Admin endpoint disabled"}), 403
        body = request.get_json(silent=True) or {}
        provided = request.headers.get("X-Admin-Secret") or body.get("secret")
        if provided != ADMIN_SECRET:
            return jsonify({"status": "error", "message": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated


# ============================================
# Helper: get user from request context
# ============================================

def current_user() -> dict:
    """Get the current user set by auth decorators. Must be called after require_auth/require_role."""
    return getattr(request, '_current_user', {})
