"""
TalentFlow AI Authentication & RBAC Bridge — Production v3.1
Leverages app.core.security and app.core.config while preserving backwards compatibility.
"""
import logging
from typing import Optional, Dict, Any
from flask import request

# Import unified enterprise security services
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    get_current_user as core_get_current_user,
    require_auth as core_require_auth,
    require_role as core_require_role,
    require_hr as core_require_hr,
    require_admin_secret as core_require_admin_secret,
    current_user as core_current_user,
    hash_password,
    verify_password
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Legacy constants for backward compatibility
JWT_SECRET = settings.auth.jwt_secret
JWT_ALGORITHM = settings.auth.jwt_algorithm
JWT_EXPIRY_HOURS = int(settings.auth.access_token_expire_minutes / 60)
ADMIN_SECRET = settings.auth.admin_secret


def create_jwt(user_id: int, email: str, role: str, username: str = "") -> str:
    """Create a signed access JWT token."""
    return create_access_token(user_id=user_id, email=email, role=role, username=username)


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token. Returns payload dict or None."""
    try:
        return decode_token(token, is_refresh=False)
    except Exception as e:
        logger.warning(f"[AUTH] decode_jwt failed: {e}")
        return None


# Re-export decorator and context functions
get_current_user = core_get_current_user
require_auth = core_require_auth
require_role = core_require_role
require_hr = core_require_hr
require_admin_secret = core_require_admin_secret
current_user = core_current_user

__all__ = [
    "create_jwt",
    "decode_jwt",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "revoke_token",
    "get_current_user",
    "require_auth",
    "require_role",
    "require_hr",
    "require_admin_secret",
    "current_user",
    "hash_password",
    "verify_password"
]

