"""
TalentFlow AI — Standardized Custom Exception Hierarchy
"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception with status code and error details."""
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "status": "error",
            "error_code": self.error_code,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        return result


class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_REQUIRED"
    message = "Authentication credentials are required or invalid."


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"
    message = "Authentication token has expired. Please refresh your session."


class PermissionDeniedError(AppException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action."


class TenantAccessViolationError(PermissionDeniedError):
    error_code = "TENANT_ACCESS_DENIED"
    message = "Access to requested resource belongs to another organization."


class NotFoundError(AppException):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found."


class ValidationError(AppException):
    status_code = 422
    error_code = "VALIDATION_FAILED"
    message = "Request validation failed."


class ConflictError(AppException):
    status_code = 409
    error_code = "RESOURCE_CONFLICT"
    message = "Resource already exists or is in conflict."


class RateLimitExceededError(AppException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please slow down."


class AIServiceError(AppException):
    status_code = 503
    error_code = "AI_SERVICE_UNAVAILABLE"
    message = "AI service temporarily unavailable."


class FileUploadError(AppException):
    status_code = 400
    error_code = "INVALID_FILE_UPLOAD"
    message = "The uploaded file is invalid or unsupported."
