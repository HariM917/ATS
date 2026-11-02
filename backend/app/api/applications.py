"""
TalentFlow AI — Applications Pipeline API v1 Blueprint
Supports application submission, stage progression, recruiter review notes, and application tracking.
"""
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import require_auth, require_hr, current_user
from ..models import Candidate, Job, Resume
from ..services.job_service import ApplicationService
from ..ai.matching_engine import compute_match

logger = logging.getLogger(__name__)

apps_v1 = Blueprint("apps_v1", __name__)


@apps_v1.route("", methods=["GET"])
@require_auth
def list_applications():
    """List applications. Candidates see their own; HR/Recruiters see all applications."""
    user = current_user()
    is_hr = user.get("role") in ("hr", "admin", "org_admin", "super_admin")
    with get_db_context() as db:
        service = ApplicationService(db)
        apps = service.list_applications_for_user(user["id"], is_hr=is_hr)
        return jsonify({
            "status": "success",
            "data": apps,
            "applications": apps
        })


@apps_v1.route("", methods=["POST"])
@require_auth
def submit_application():
    """Submit a new job application."""
    user = current_user()
    data = request.get_json(silent=True) or {}
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({
            "status": "error",
            "error_code": "JOB_ID_REQUIRED",
            "message": "job_id is required to submit an application."
        }), 400

    resume_path = data.get("resume_path")
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

        resume_id = data.get("resume_id")
        service = ApplicationService(db)
        app_res = service.apply(user["id"], job_id, resume_path=resume_path, resume_id=resume_id)

        # Compute match feedback if possible
        analysis = None
        try:
            job = db.query(Job).filter_by(id=job_id).first()
            cand = db.query(Candidate).filter_by(user_id=user["id"]).first()
            res_record = db.query(Resume).filter_by(candidate_id=cand.id, is_current=True).first() if cand else None
            if job and res_record and res_record.raw_text:
                analysis = compute_match(
                    resume_text=str(res_record.raw_text),
                    job_description=str(job.description or ""),
                    required_skills_str=str(job.required_skills or ""),
                    experience_required_years=int(str(job.experience_required)) if job.experience_required else 0
                )
        except Exception as e:
            logger.debug(f"[APPLY] Match analysis skipped: {e}")

        return jsonify({
            "status": "success",
            "data": app_res,
            "application": app_res,
            "analysis": analysis
        }), 201


@apps_v1.route("/<application_id>", methods=["GET"])
@require_auth
def get_application_details(application_id):
    """Retrieve details of a single application."""
    with get_db_context() as db:
        service = ApplicationService(db)
        app_data = service.get_application(application_id)
        return jsonify({
            "status": "success",
            "data": app_data,
            "application": app_data
        })


@apps_v1.route("/<application_id>", methods=["PUT"])
@require_hr
def update_application(application_id):
    """Update application stage/status or recruiter review notes (HR only)."""
    data = request.get_json(silent=True) or {}
    stage = data.get("stage") or data.get("status")
    if not stage:
        return jsonify({
            "status": "error",
            "error_code": "STAGE_REQUIRED",
            "message": "stage or status is required"
        }), 400

    with get_db_context() as db:
        service = ApplicationService(db)
        app_res = service.update_stage(application_id, stage, notes=data.get("notes"))
        return jsonify({
            "status": "success",
            "data": app_res,
            "application": app_res
        })


@apps_v1.route("/<job_id>/apply", methods=["POST"])
@require_auth
def apply_to_job(job_id):
    """Direct application endpoint for /api/v1/applications/<job_id>/apply."""
    user = current_user()
    data = request.get_json(silent=True) or {}
    resume_path = data.get("resume_path")
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

        resume_id = data.get("resume_id")
        service = ApplicationService(db)
        app_res = service.apply(user["id"], job_id, resume_path=resume_path, resume_id=resume_id)

        analysis = None
        try:
            job = db.query(Job).filter_by(id=job_id).first()
            cand = db.query(Candidate).filter_by(user_id=user["id"]).first()
            res_record = db.query(Resume).filter_by(candidate_id=cand.id, is_current=True).first() if cand else None
            if job and res_record and res_record.raw_text:
                analysis = compute_match(
                    resume_text=str(res_record.raw_text),
                    job_description=str(job.description or ""),
                    required_skills_str=str(job.required_skills or ""),
                    experience_required_years=int(str(job.experience_required)) if job.experience_required else 0
                )
        except Exception as e:
            logger.debug(f"[APPLY] Match analysis skipped: {e}")

        return jsonify({
            "status": "success",
            "data": app_res,
            "application": app_res,
            "analysis": analysis
        }), 201


@apps_v1.route("/<app_id>/stage", methods=["POST", "PATCH"])
@apps_v1.route("/<app_id>/status", methods=["POST", "PATCH"])
@require_hr
def update_application_stage(app_id):
    """Compatibility alias for updating application stage."""
    data = request.get_json(silent=True) or {}
    stage = data.get("stage") or data.get("status")
    if not stage:
        return jsonify({
            "status": "error",
            "error_code": "STAGE_REQUIRED",
            "message": "Stage is required"
        }), 400

    with get_db_context() as db:
        service = ApplicationService(db)
        app_res = service.update_stage(app_id, stage, notes=data.get("notes"))
        return jsonify({
            "status": "success",
            "data": app_res,
            "application": app_res
        })

