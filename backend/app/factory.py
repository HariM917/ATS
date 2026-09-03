"""
TalentFlow AI — Flask Application Factory
Initializes middleware, security headers, database lifecycle, and registers versioned blueprints.
"""
import os
import logging
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from .core.config import settings
from .core.middleware import register_security_headers, register_error_handlers, setup_cors, limiter
from .core.database import init_database
from .api import auth_v1, jobs_v1, apps_v1, matching_v1, chat_v1, analytics_v1, health_v1, resumes_v1, candidates_v1

logger = logging.getLogger(__name__)


def create_app(config_override: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure an instance of the TalentFlow AI Flask application."""
    app = Flask(__name__)

    # Apply configuration
    app.config["SECRET_KEY"] = settings.auth.flask_secret_key or "talentflow-secret-key"
    app.config["MAX_CONTENT_LENGTH"] = settings.storage.max_upload_size_mb * 1024 * 1024
    if config_override:
        app.config.update(config_override)

    # Validate production configuration
    if settings.is_production:
        issues = settings.validate_production_readiness()
        if issues:
            error_msg = "[STARTUP FATAL] Production readiness validation failed:\n" + "\n".join(f"  - {i}" for i in issues)
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

    # Initialize Core Middleware & Security
    register_security_headers(app)
    register_error_handlers(app)
    setup_cors(app)
    limiter.init_app(app)

    # Ensure Upload Directory exists
    os.makedirs(settings.storage.local_upload_dir, exist_ok=True)

    # Database Initialization & Lifecycle Verification
    if settings.is_production:
        # In production, do NOT run Base.metadata.create_all(); expect migrations to be pre-applied
        from .core.database import check_database_connection
        if not check_database_connection():
            error_msg = "Database connectivity check failed during production startup. Ensure PostgreSQL is reachable and migrations have been executed."
            logger.critical(f"[APP_FACTORY] {error_msg}")
            raise RuntimeError(error_msg)
        logger.info("[APP_FACTORY] Production database connection verified (migrations managed via Alembic).")
    else:
        # In development/testing, auto-create tables if needed for zero-setup workflows
        try:
            init_database()
        except Exception as e:
            logger.warning(f"[APP_FACTORY] Database init warning in dev: {e}")

    # Register API v1 Blueprints
    api_prefix = settings.api_v1_prefix  # /api/v1
    app.register_blueprint(auth_v1, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(jobs_v1, url_prefix=f"{api_prefix}/jobs")
    app.register_blueprint(apps_v1, url_prefix=f"{api_prefix}/applications")
    app.register_blueprint(matching_v1, url_prefix=f"{api_prefix}/matching")
    app.register_blueprint(chat_v1, url_prefix=f"{api_prefix}/chat")
    app.register_blueprint(analytics_v1, url_prefix=f"{api_prefix}/analytics")
    app.register_blueprint(health_v1, url_prefix=f"{api_prefix}/system")
    app.register_blueprint(resumes_v1, url_prefix=f"{api_prefix}/resumes")
    app.register_blueprint(candidates_v1, url_prefix=f"{api_prefix}/candidates")

    # Backward-compatible legacy aliases with unique blueprint names
    app.register_blueprint(auth_v1, url_prefix="/api", name="auth_compat")
    app.register_blueprint(jobs_v1, url_prefix="/api/jobs_compat", name="jobs_compat")
    app.register_blueprint(chat_v1, url_prefix="/api/chat_compat", name="chat_compat")

    # Container / Cloud platform health check aliases (e.g., Render, Docker, Kubernetes)
    @app.route("/api/health", methods=["GET"])
    @app.route("/health", methods=["GET"])
    def health_alias():
        from .api.endpoints import health
        return health()

    @app.route("/api/warm", methods=["GET", "POST"])
    def warm_alias():
        from .core.warmup import warm_services
        warm_services()
        return jsonify({
            "status": "ok",
            "warmed": True,
            "message": "Subsystems successfully warmed"
        })

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "status": "online",
            "app": settings.app_name,
            "version": "v3.2.0",
            "docs": f"{api_prefix}/system/health"
        })

    logger.info(f">>> {settings.app_name} Initialized in '{settings.environment}' mode on port {settings.port}")
    return app
