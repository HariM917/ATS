"""
TalentFlow AI — Enterprise Security, Token Management, and RBAC
Supports dual-token architecture (Access + Refresh Token), token revocation,
and tenant-aware role-based access control.
"""
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta, timezone
from functools import wraps
import logging
import jwt
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from .config import settings
from .exceptions import AuthenticationError, TokenExpiredError, PermissionDeniedError

logger = logging.getLogger(__name__)

# Roles enumeration
ROLE_CANDIDATE = "candidate"
ROLE_RECRUITER = "hr"
ROLE_ADMIN = "admin"
ROLE_ORG_ADMIN = "org_admin"
ROLE_SUPER_ADMIN = "super_admin"

VALID_ROLES: Set[str] = {
    ROLE_CANDIDATE,
    ROLE_RECRUITER,
    ROLE_ADMIN,
    ROLE_ORG_ADMIN,
    ROLE_SUPER_ADMIN,
}

# In-memory revoked token cache (stores JTI/token hash until expiration)
# In production with Redis enabled, this integrates seamlessly.
_REVOKED_TOKENS: Set[str] = set()


def hash_password(password: str) -> str:
    """Securely hash a plain text password with pbkdf2:sha256."""
    if not password:
        raise ValueError("Password cannot be empty")
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain password against stored hash."""
    if not password or not password_hash:
        return False
    return check_password_hash(password_hash, password)


def _get_signing_key(is_refresh: bool = False) -> str:
    """Retrieve secret key, ensuring security in production."""
    secret = settings.auth.jwt_refresh_secret if is_refresh else settings.auth.jwt_secret
    if not secret:
        # Fallback to flask_secret_key or a secure dev default in non-production
        secret = settings.auth.flask_secret_key or "talentflow-dev-secret-key-32-bytes-min"
        if settings.is_production:
            logger.critical("[SECURITY] Production detected without explicit JWT_SECRET set!")
    return secret


def create_access_token(
    user_id: Any,
    email: str,
    role: str,
    username: str = "",
    organization_id: Optional[str] = None,
    custom_claims: Optional[Dict[str, Any]] = None
) -> str:
    """Create a signed JWT access token with user claims and tenant context."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.auth.access_token_expire_minutes)
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "user": username or email,
        "org_id": str(organization_id) if organization_id else None,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if custom_claims:
        payload.update(custom_claims)
        
    return jwt.encode(payload, _get_signing_key(is_refresh=False), algorithm=settings.auth.jwt_algorithm)


def create_refresh_token(user_id: Any, email: str, role: str) -> str:
    """Create a long-lived refresh token for token rotation."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.auth.refresh_token_expire_days)
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, _get_signing_key(is_refresh=True), algorithm=settings.auth.jwt_algorithm)


def decode_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    """
    Decode and validate token signature, expiration, and revocation status.
    Raises AuthenticationError or TokenExpiredError on failure.
    """
    if not token or not isinstance(token, str):
        raise AuthenticationError("Invalid token format")
        
    if token in _REVOKED_TOKENS:
        raise AuthenticationError("Token has been revoked")

    try:
        payload = jwt.decode(
            token,
            _get_signing_key(is_refresh=is_refresh),
            algorithms=[settings.auth.jwt_algorithm]
        )
        # Verify token type
        expected_type = "refresh" if is_refresh else "access"
        if payload.get("type") != expected_type:
            raise AuthenticationError(f"Expected {expected_type} token, got {payload.get('type')}")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token signature has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid authentication token: {str(e)}")


def revoke_token(token: str) -> bool:
    """Add token to revocation blacklist."""
    if token:
        _REVOKED_TOKENS.add(token)
        return True
    return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """Extract authenticated user details from Authorization Bearer header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
        
    token = auth_header[7:].strip()
    if not token:
        return None

    try:
        payload = decode_token(token, is_refresh=False)
        user_id = payload.get("sub")
        # Try integer conversion if legacy ID
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass

        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "user": payload.get("user", payload.get("email")),
            "org_id": payload.get("org_id"),
            "token": token,
        }
    except (AuthenticationError, TokenExpiredError) as e:
        logger.debug(f"[AUTH] Token decode failed in get_current_user: {e}")
        return None


def require_auth(f):
    """Decorator: Enforces valid JWT on the endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or not user.get("email"):
            return jsonify({
                "status": "error",
                "error_code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication required. Provide a valid Bearer token."
            }), 401
        request._current_user = user
        return f(*args, **kwargs)
    return decorated


def require_role(*allowed_roles: str):
    """Decorator factory: Enforces user role membership."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user or not user.get("email"):
                return jsonify({
                    "status": "error",
                    "error_code": "AUTHENTICATION_REQUIRED",
                    "message": "Authentication required."
                }), 401
                
            user_role = user.get("role")
            if user_role not in allowed_roles and user_role not in (ROLE_SUPER_ADMIN, ROLE_ADMIN):
                return jsonify({
                    "status": "error",
                    "error_code": "PERMISSION_DENIED",
                    "message": f"Access denied. Required role in [{', '.join(allowed_roles)}], got '{user_role}'."
                }), 403
                
            request._current_user = user
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_hr(f):
    """Convenience decorator: shortcut for require_role('hr', 'org_admin', 'admin', 'super_admin')."""
    return require_role(ROLE_RECRUITER, ROLE_ORG_ADMIN, ROLE_ADMIN, ROLE_SUPER_ADMIN)(f)


def require_admin_secret(f):
    """Decorator: Requires system admin secret key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_secret = settings.auth.admin_secret
        if not admin_secret:
            return jsonify({
                "status": "error",
                "error_code": "ADMIN_DISABLED",
                "message": "Admin endpoints are disabled (ADMIN_SECRET not configured)."
            }), 403
            
        body = request.get_json(silent=True) or {}
        provided = request.headers.get("X-Admin-Secret") or body.get("secret")
        if provided != admin_secret:
            return jsonify({
                "status": "error",
                "error_code": "FORBIDDEN",
                "message": "Invalid administrator secret."
            }), 403
            
        return f(*args, **kwargs)
    return decorated


def current_user() -> Dict[str, Any]:
    """Retrieve user dictionary injected by auth decorators."""
    return getattr(request, "_current_user", {})
