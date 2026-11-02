"""
TalentFlow AI — Health, Readiness, and Liveness API v1 Blueprint
Used by Render, Docker healthchecks, and Kubernetes readiness probes.
"""
import logging
from flask import Blueprint, jsonify
from ..core.config import settings

logger = logging.getLogger(__name__)

health_v1 = Blueprint("health_v1", __name__)


@health_v1.route("", methods=["GET"])
@health_v1.route("/health", methods=["GET"])
def health():
    """System health check endpoint verifying database connectivity and service readiness."""
    from ..core.database import db_url, check_database_connection
    from ..core.redis_client import check_redis_health, check_celery_health

    if "postgresql" in db_url or "postgres" in db_url:
        db_engine = "postgresql"
    elif "sqlite" in db_url:
        db_engine = "sqlite"
    else:
        db_engine = "unknown"

    db_connected = check_database_connection()
    redis_status = check_redis_health()
    celery_status = check_celery_health()

    return jsonify({
        "status": "healthy" if db_connected else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "version": "v3.2.0",
        "database": {
            "engine": db_engine,
            "connected": db_connected,
        },
        "redis": redis_status,
        "celery": celery_status,
    })

