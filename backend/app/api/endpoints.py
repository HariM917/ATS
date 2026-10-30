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
    resume_path = data.get("resume_path")

    # Support direct resume file upload in application flow
    file = request.files.get("resume") or request.files.get("file")

    with get_db_context() as db:
        if file:
            try:
                from ..services.resume_service import ResumeService
                res_service = ResumeService(db)
                res_result = res_service.upload_and_process(user["id"], file, trigger_async=False)
                resume_path = res_result.get("file_path")
            except Exception as e:
                logger.warning(f"[APPLY] Inline resume upload warning: {e}")

        service = ApplicationService(db)
        app_res = service.apply(user["id"], job_id, resume_path=resume_path)

        # Compute match analysis feedback for the applicant
        analysis = None
        try:
            job = db.query(Job).filter_by(id=job_id).first()
            cand = db.query(Candidate).filter_by(user_id=user["id"]).first()
            res_record = db.query(Resume).filter_by(candidate_id=cand.id, is_current=True).first() if cand else None
            if job is not None and res_record is not None and res_record.raw_text is not None:
                analysis = compute_match(
                    resume_text=str(res_record.raw_text),
                    job_description=str(job.description or ""),
                    required_skills_str=str(job.required_skills or ""),
                    experience_required_years=int(str(job.experience_required)) if job.experience_required is not None else 0
                )
        except Exception as e:
            logger.debug(f"[APPLY] Match analysis generation skipped: {e}")

        return jsonify({
            "status": "success",
            "application": app_res,
            "analysis": analysis
        }), 201


@apps_v1.route("/<app_id>/stage", methods=["POST", "PATCH"])
@apps_v1.route("/<app_id>/status", methods=["POST", "PATCH"])
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

    # 22-Class Occupational Classification (Phase V21/V23 Champion)
    try:
        from ..services.occupational_classifier import get_occupational_classifier
        classifier = get_occupational_classifier()
        result["occupational_classification"] = classifier.predict(resume_text)
    except Exception as e:
        logger.warning(f"[MATCHING] Occupational classification fallback: {e}")
        result["occupational_classification"] = {
            "predicted_role": "UNKNOWN",
            "confidence": 0.0,
            "runner_up_role": "UNKNOWN",
            "runner_up_confidence": 0.0,
            "margin": 0.0,
            "review_required": True,
            "review_reasons": [f"Classifier unavailable: {e}"],
            "model_version": "v21-v23-final",
            "taxonomy_version": "22-class-occupational-v1"
        }

    return jsonify({"status": "success", "result": result})


@matching_v1.route("/batch-screen/<job_id>", methods=["POST"])
@require_hr
def batch_screen_job(job_id):
    """Trigger batch AI screening for all applicants of a job. Uses Celery if available."""
    try:
        from ..workers.tasks import async_batch_screen
        delay_fn = getattr(async_batch_screen, "delay", None)
        if callable(delay_fn):
            task = delay_fn(job_id)
            task_id = getattr(task, "id", "async")
            return jsonify({
                "status": "success",
                "message": "Batch screening started",
                "task_id": task_id
            }), 202
        raise RuntimeError("Celery delay not configured")
    except Exception as e:
        # Synchronous fallback
        logger.info(f"[MATCHING] Celery unavailable, running batch screen synchronously: {e}")
        from ..workers.tasks import async_batch_screen
        result = async_batch_screen(None, job_id)
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


@chat_v1.route("/history", methods=["GET"])
@chat_v1.route("/chat_history", methods=["GET"])
def get_chat_history():
    """Retrieve chat history."""
    return jsonify({"status": "success", "history": []})


# --- Analytics API ---

@analytics_v1.route("/recruiter", methods=["GET"])
@require_hr
def get_recruiter_analytics():
    user = current_user()
    org_id = user.get("org_id")
    with get_db_context() as db:
        analytics = AnalyticsService(db)
        overview = analytics.get_recruiter_overview(organization_id=str(org_id) if org_id else None)
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

