"""
TalentFlow AI — Resume Upload, Processing, and Analysis API v1
"""
import os
import uuid
import hashlib
import logging
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from ..core.database import get_db_context
from ..core.security import require_auth, current_user
from ..core.config import settings
from ..models import Candidate, Resume
from ..services.resume_service import ResumeService
from ..core.exceptions import ValidationError, NotFoundError, FileUploadError

logger = logging.getLogger(__name__)

resumes_v1 = Blueprint("resumes_v1", __name__)


@resumes_v1.route("/upload", methods=["POST"])
@require_auth
def upload_resume():
    """Upload a resume file (PDF, DOCX, TXT), store metadata, and trigger async processing."""
    user = current_user()
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part in request"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "message": "No file selected"}), 400

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in settings.storage.allowed_extensions:
        return jsonify({
            "status": "error",
            "message": f"Unsupported file type '.{ext}'. Allowed: {settings.storage.allowed_extensions}"
        }), 400

    with get_db_context() as db:
        service = ResumeService(db)
        result = service.upload_and_process(
            user_id=user["id"],
            file=file,
            trigger_async=True
        )
        return jsonify({"status": "success", "resume": result}), 201


@resumes_v1.route("/my-resumes", methods=["GET"])
@require_auth
def list_my_resumes():
    """List all resumes for the authenticated candidate."""
    user = current_user()
    with get_db_context() as db:
        service = ResumeService(db)
        resumes = service.list_resumes_for_user(user["id"])
        return jsonify({"status": "success", "resumes": resumes})


@resumes_v1.route("/<resume_id>/analysis", methods=["GET"])
@require_auth
def get_resume_analysis(resume_id):
    """Get parsed skills, sections, and ATS health score for a resume."""
    with get_db_context() as db:
        service = ResumeService(db)
        analysis = service.get_analysis(resume_id)
        return jsonify({"status": "success", "analysis": analysis})
