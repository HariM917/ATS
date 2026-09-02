"""
TalentFlow AI — Applications, Matching, Analytics, and Chat API v1 Blueprints
"""
import os
import uuid
import logging
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from ..core.database import get_db_context
from ..core.security import require_auth, require_hr, current_user
from ..core.config import settings
from ..models import Candidate, Application, Job, Resume, MatchResult, User
from ..services.job_service import ApplicationService
from ..services.analytics_service import AnalyticsService
from ..ai.matching_engine import compute_match
from ..ai.resume_parser import extract_text_from_file
from ..ai.skill_extractor import extract_skills, categorize_skills
from ..ai.rag import rag_coach

logger = logging.getLogger(__name__)

apps_v1 = Blueprint("apps_v1", __name__)
matching_v1 = Blueprint("matching_v1", __name__)
chat_v1 = Blueprint("chat_v1", __name__)
analytics_v1 = Blueprint("analytics_v1", __name__)
health_v1 = Blueprint("health_v1", __name__)


# --- Applications API ---

@apps_v1.route("/<job_id>/apply", methods=["POST"])
@require_auth
def apply_to_job(job_id):
    user = current_user()
    data = request.get_json(silent=True) or {}
    with get_db_context() as db:
        service = ApplicationService(db)
        app_res = service.apply(user["id"], job_id, resume_path=data.get("resume_path"))
        return jsonify({"status": "success", "application": app_res}), 201


@apps_v1.route("/<app_id>/stage", methods=["POST", "PATCH"])
@require_hr
def update_application_stage(app_id):
    data = request.get_json() or {}
    stage = data.get("stage") or data.get("status")
    if not stage:
        return jsonify({"status": "error", "message": "Stage is required"}), 400

    with get_db_context() as db:
        service = ApplicationService(db)
        app_res = service.update_stage(app_id, stage, notes=data.get("notes"))
        return jsonify({"status": "success", "application": app_res})


# --- Matching & Screening API ---

@matching_v1.route("/evaluate", methods=["POST"])
@require_auth
def evaluate_resume():
    data = request.get_json() or {}
    resume_text = data.get("resume_text", "")
    jd_text = data.get("job_description", "")
    required_skills = data.get("required_skills", "")
    exp_years = int(data.get("experience_required", 0))

    result = compute_match(
        resume_text=resume_text,
        job_description=jd_text,
        required_skills_str=required_skills,
        experience_required_years=exp_years
    )
    return jsonify({"status": "success", "result": result})


@matching_v1.route("/batch-screen/<job_id>", methods=["POST"])
@require_hr
def batch_screen_job(job_id):
    """Trigger batch AI screening for all applicants of a job. Uses Celery if available."""
    try:
        from ..workers.tasks import async_batch_screen
        task = async_batch_screen.delay(job_id)
        return jsonify({
            "status": "success",
            "message": "Batch screening started",
            "task_id": task.id
        }), 202
    except Exception as e:
        # Synchronous fallback
        logger.info(f"[MATCHING] Celery unavailable, running batch screen synchronously: {e}")
        from ..workers.tasks import async_batch_screen
        result = async_batch_screen(job_id)
        return jsonify({"status": "success", "result": result})


@matching_v1.route("/rankings/<job_id>", methods=["GET"])
@require_hr
def get_rankings(job_id):
    """Get ranked candidates for a job, sorted by match score descending."""
    with get_db_context() as db:
        from ..models import MatchResult
        results = db.query(MatchResult).filter_by(job_id=job_id).order_by(
            MatchResult.final_score.desc()
        ).all()
        rankings = []
        for i, r in enumerate(results, 1):
            d = r.to_dict()
            d["rank"] = i
            if r.candidate:
                d["candidate_name"] = r.candidate.name
            rankings.append(d)
        return jsonify({"status": "success", "rankings": rankings})


# --- Chat & RAG API ---

@chat_v1.route("", methods=["POST"])
def send_chat_message():
    data = request.get_json() or {}
    query = data.get("query") or data.get("message", "")
    response_data = rag_coach.answer_query(query)
    return jsonify({
        "status": "success",
        "answer": response_data["answer"],
        "sources": response_data["sources"]
    })


# --- Analytics API ---

@analytics_v1.route("/recruiter", methods=["GET"])
@require_hr
def get_recruiter_analytics():
    user = current_user()
    with get_db_context() as db:
        analytics = AnalyticsService(db)
        overview = analytics.get_recruiter_overview(organization_id=user.get("org_id"))
        return jsonify({"status": "success", "data": overview})


# --- Health & Readiness API ---

@health_v1.route("/health", methods=["GET"])
def health():
    from ..core.database import db_url, check_database_connection
    from ..core.redis_client import check_redis_health, check_celery_health

    # Determine database engine type
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

