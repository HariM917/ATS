"""
TalentFlow AI — HTTP Middleware, Security Headers, Rate Limiter & Global Error Handlers
"""
import uuid
import time
import logging
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import settings
from .exceptions import AppException, RateLimitExceededError

logger = logging.getLogger(__name__)

# Initialize rate limiter with client IP extraction
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    storage_uri=settings.redis.url if settings.redis.enabled else "memory://",
    strategy="moving-window",
)


def register_security_headers(app: Flask) -> None:
    """Attach enterprise security headers to every HTTP response."""
    
    @app.before_request
    def before_request_hook():
        # Attach unique Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = request_id
        g.start_time = time.time()

    @app.after_request
    def after_request_hook(response):
        # 1. Attach Request ID
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id

        # 2. Timing header (non-sensitive metric)
        start_time = getattr(g, "start_time", None)
        if start_time:
            duration_ms = int((time.time() - start_time) * 1000)
            response.headers["X-Response-Time-Ms"] = str(duration_ms)

        # 3. Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # In production with HTTPS, enforce HSTS
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Content-Security-Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

        # 4. Remove leaky tech identifier headers
        response.headers.pop("X-Powered-By", None)
        response.headers.pop("Server", None)

        return response


def register_error_handlers(app: Flask) -> None:
    """Catch custom AppException and standard errors, returning uniform JSON format."""

    @app.errorhandler(AppException)
    def handle_app_exception(err: AppException):
        logger.warning(f"[{err.error_code}] {err.message} - Details: {err.details}")
        response = jsonify(err.to_dict())
        response.status_code = err.status_code
        return response

    @app.errorhandler(429)
    def handle_rate_limit(err):
        return jsonify({
            "status": "error",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please slow down and try again later."
        }), 429

    @app.errorhandler(404)
    def handle_404(err):
        return jsonify({
            "status": "error",
            "error_code": "NOT_FOUND",
            "message": "The requested endpoint was not found on this server."
        }), 404

    @app.errorhandler(405)
    def handle_405(err):
        return jsonify({
            "status": "error",
            "error_code": "METHOD_NOT_ALLOWED",
            "message": f"Method {request.method} is not allowed for this endpoint."
        }), 405

    @app.errorhandler(500)
    def handle_500(err):
        logger.error(f"[INTERNAL_ERROR] Unhandled exception: {err}", exc_info=True)
        return jsonify({
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal server error occurred."
        }), 500


def setup_cors(app: Flask) -> None:
    """Configure Cross-Origin Resource Sharing based on settings."""
    origins = settings.cors_origins
    logger.info(f"[CORS] Allowed Origins: {origins}")
    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Admin-Secret", "X-Request-ID"]
    )
