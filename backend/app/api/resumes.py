"""
TalentFlow AI — Resume Upload, Processing, and Analysis API v1
"""
import os
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import require_auth, current_user
from ..core.config import settings
from ..services.resume_service import ResumeService

logger = logging.getLogger(__name__)

resumes_v1 = Blueprint("resumes_v1", __name__)


@resumes_v1.route("/upload", methods=["POST"])
@require_auth
def upload_resume():
    """Upload a resume file (PDF, DOCX, TXT), store metadata, and extract parsed content."""
    user = current_user()
    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "error_code": "NO_FILE",
            "message": "No file part in request. Please select a resume file to upload."
        }), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({
            "status": "error",
            "error_code": "EMPTY_FILENAME",
            "message": "No file selected."
        }), 400

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in settings.storage.allowed_extensions:
        return jsonify({
            "status": "error",
            "error_code": "UNSUPPORTED_FILE_TYPE",
            "message": f"Unsupported file type '.{ext}'. Allowed types: {', '.join(settings.storage.allowed_extensions)}"
        }), 400

    with get_db_context() as db:
        service = ResumeService(db)
        result = service.upload_and_process(
            user_id=user["id"],
            file=file,
            trigger_async=True
        )
        return jsonify({
            "status": "success",
            "data": result,
            "resume": result
        }), 201


@resumes_v1.route("/my-resumes", methods=["GET"])
@require_auth
def list_my_resumes():
    """List all resumes for the authenticated candidate."""
    user = current_user()
    with get_db_context() as db:
        service = ResumeService(db)
        resumes = service.list_resumes_for_user(user["id"])
        return jsonify({
            "status": "success",
            "data": resumes,
            "resumes": resumes
        })


@resumes_v1.route("/<resume_id>", methods=["GET"])
@require_auth
def get_resume(resume_id):
    """Get single resume metadata and details by ID."""
    with get_db_context() as db:
        service = ResumeService(db)
        resume = service.get_resume(resume_id)
        return jsonify({
            "status": "success",
            "data": resume,
            "resume": resume
        })


@resumes_v1.route("/<resume_id>", methods=["DELETE"])
@require_auth
def delete_resume(resume_id):
    """Delete a resume by ID."""
    user = current_user()
    with get_db_context() as db:
        service = ResumeService(db)
        service.delete_resume(resume_id, user["id"])
        return jsonify({
            "status": "success",
            "message": "Resume deleted successfully"
        })


@resumes_v1.route("/<resume_id>/analysis", methods=["GET"])
@require_auth
def get_resume_analysis(resume_id):
    """Get parsed skills, sections, and ATS health score for a resume."""
    with get_db_context() as db:
        service = ResumeService(db)
        analysis = service.get_analysis(resume_id)
        return jsonify({
            "status": "success",
            "data": analysis,
            "analysis": analysis
        })


@resumes_v1.route("/<resume_id>/quality", methods=["GET", "POST"])
@require_auth
def analyze_resume_quality(resume_id):
    """Run or fetch deterministic ATS formatting & document quality analysis."""
    from ..models.resume import Resume
    from ..services.resume_quality_analyzer import ResumeQualityAnalyzer
    with get_db_context() as db:
        resume_obj = db.query(Resume).filter_by(id=resume_id).first()
        if not resume_obj:
            return jsonify({"status": "error", "message": "Resume not found"}), 404

        file_path = getattr(resume_obj, "file_path", None)
        raw_text = getattr(resume_obj, "raw_text", "")
        analysis = ResumeQualityAnalyzer.analyze_resume(file_path=file_path, raw_text=raw_text)

        # Update cached quality analysis
        current_health = dict(getattr(resume_obj, "health_analysis") or {})
        current_health["quality_analysis"] = analysis
        current_health["formatting_score"] = analysis.get("formatting_score", 0)
        current_health["is_ats_friendly"] = analysis.get("is_ats_friendly", True)
        setattr(resume_obj, "health_analysis", current_health)
        setattr(resume_obj, "ats_score", float(analysis.get("formatting_score", 0)))
        db.flush()

        return jsonify({
            "status": "success",
            "data": analysis,
            "quality": analysis
        })


@resumes_v1.route("/analyze-quality", methods=["POST"])
@require_auth
def analyze_text_quality():
    """Analyze quality directly from raw text or resume ID."""
    from ..models.resume import Resume
    from ..services.resume_quality_analyzer import ResumeQualityAnalyzer
    data = request.get_json(silent=True) or {}
    raw_text = data.get("raw_text", "")
    resume_id = data.get("resume_id")
    file_path = None

    if resume_id:
        with get_db_context() as db:
            r = db.query(Resume).filter_by(id=resume_id).first()
            if r:
                file_path = getattr(r, "file_path", None)
                if not raw_text:
                    raw_text = getattr(r, "raw_text", "")

    analysis = ResumeQualityAnalyzer.analyze_resume(file_path=file_path, raw_text=raw_text)
    return jsonify({
        "status": "success",
        "data": analysis,
        "quality": analysis
    })
