"""
TalentFlow AI — Jobs API v1 Blueprint
CRUD for Job Postings, Candidate Applications to Jobs, and Recruiter Pipeline Tracking.
"""
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import require_auth, require_hr, current_user
from ..services.job_service import JobService, ApplicationService

logger = logging.getLogger(__name__)

jobs_v1 = Blueprint("jobs_v1", __name__)


@jobs_v1.route("", methods=["GET"])
@jobs_v1.route("/all_jobs", methods=["GET"])
def list_jobs():
    """List published jobs for candidates or all managed jobs for HR."""
    hr_only = request.args.get("hr_only", "").lower() in ("true", "1")
    hr_user_id = None
    if hr_only:
        try:
            user = current_user()
            if user and user.get("role") in ("hr", "admin", "org_admin", "super_admin"):
                hr_user_id = user.get("id")
        except Exception:
            pass

    with get_db_context() as db:
        service = JobService(db)
        jobs = service.list_jobs(hr_user_id=hr_user_id)
        return jsonify({
            "status": "success",
            "data": jobs,
            "jobs": jobs
        })


@jobs_v1.route("/<job_id>/publish", methods=["POST"])
@require_hr
def publish_job(job_id):
    """Publish a draft job posting (HR/Recruiter only)."""
    user = current_user()
    with get_db_context() as db:
        service = JobService(db)
        job = service.publish_job(job_id, user["id"])
        return jsonify({
            "status": "success",
            "message": "Job published successfully",
            "data": job,
            "job": job
        })



@jobs_v1.route("", methods=["POST"])
@require_hr
def create_job():
    """Create a new job posting (HR/Recruiter only)."""
    user = current_user()
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("description"):
        return jsonify({
            "status": "error",
            "error_code": "VALIDATION_ERROR",
            "message": "Job title and description are required."
        }), 400

    with get_db_context() as db:
        service = JobService(db)
        job = service.create_job(user["id"], data)
        return jsonify({
            "status": "success",
            "data": job,
            "job": job
        }), 201


@jobs_v1.route("/<job_id>", methods=["GET"])
def get_job(job_id):
    """Retrieve details for a single job posting by ID."""
    with get_db_context() as db:
        service = JobService(db)
        job = service.get_job(job_id)
        return jsonify({
            "status": "success",
            "data": job,
            "job": job
        })


@jobs_v1.route("/<job_id>", methods=["PUT"])
@require_hr
def update_job(job_id):
    """Update an existing job posting (HR/Recruiter only)."""
    user = current_user()
    data = request.get_json(silent=True) or {}
    with get_db_context() as db:
        service = JobService(db)
        job = service.update_job(job_id, data, user_id=user["id"])
        return jsonify({
            "status": "success",
            "data": job,
            "job": job
        })


@jobs_v1.route("/<job_id>", methods=["DELETE"])
@require_hr
def delete_job(job_id):
    """Delete a job posting (HR/Recruiter only)."""
    user = current_user()
    with get_db_context() as db:
        service = JobService(db)
        service.delete_job(job_id, user["id"])
        return jsonify({
            "status": "success",
            "message": "Job deleted successfully"
        })


@jobs_v1.route("/<job_id>/apply", methods=["POST"])
@require_auth
def job_apply(job_id):
    """Apply to a job directly via the jobs endpoint."""
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

        return jsonify({
            "status": "success",
            "data": app_res,
            "application": app_res
        }), 201


@jobs_v1.route("/<job_id>/applications", methods=["GET"])
@require_hr
def get_job_applications(job_id):
    """Get all candidate applications for a specific job (HR/Recruiter only)."""
    with get_db_context() as db:
        app_service = ApplicationService(db)
        apps = app_service.list_by_job(job_id)
        return jsonify({
            "status": "success",
            "data": apps,
            "applications": apps
        })

