"""
TalentFlow AI — Resume Upload, Processing, Deduplication, and Health Analysis Service
"""
import os
import uuid
import hashlib
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from ..models import Candidate, Resume
from ..repositories import CandidateRepository, ResumeRepository
from ..core.config import settings
from ..core.exceptions import NotFoundError, ValidationError, FileUploadError
from ..ai.resume_parser import extract_text_from_file, extract_sections
from ..ai.skill_extractor import extract_skills, categorize_skills

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, db: Session):
        self.db = db
        self.cand_repo = CandidateRepository(db)
        self.resume_repo = ResumeRepository(db)

    def upload_and_process(
        self,
        user_id: str,
        file: FileStorage,
        trigger_async: bool = True
    ) -> Dict[str, Any]:
        """Upload resume, store file, extract metadata, optionally trigger async processing."""
        candidate = self.cand_repo.get_by_user_id(user_id)
        if not candidate:
            candidate = Candidate(user_id=str(user_id), name="Candidate")
            self.db.add(candidate)
            self.db.flush()

        # Save file to disk
        filename = secure_filename(file.filename or "resume.pdf")
        file_ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if file_ext not in settings.storage.allowed_extensions:
            raise FileUploadError(f"Unsupported file type '.{file_ext}'")

        unique_name = f"{uuid.uuid4().hex}_{filename}"
        upload_dir = settings.storage.local_upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_name)
        file.save(file_path)

        # Compute file hash for deduplication
        file_hash = self._compute_file_hash(file_path)
        file_size = os.path.getsize(file_path)

        # Check for duplicate
        existing = self.db.query(Resume).filter_by(
            candidate_id=candidate.id,
            file_hash_sha256=file_hash
        ).first()
        if existing:
            os.remove(file_path)
            return existing.to_dict()

        # Mark previous resumes as non-current
        current_resumes = self.db.query(Resume).filter_by(
            candidate_id=candidate.id, is_current=True
        ).all()
        for r in current_resumes:
            r.is_current = False

        # Determine version number
        version = self.db.query(Resume).filter_by(candidate_id=candidate.id).count() + 1

        # Synchronous processing (fast path)
        raw_text = extract_text_from_file(file_path)
        skills = extract_skills(raw_text)
        categorized = categorize_skills(skills)
        sections = extract_sections(raw_text)

        resume = Resume(
            candidate_id=candidate.id,
            version=version,
            is_current=True,
            file_path=file_path,
            original_filename=filename,
            file_size_bytes=file_size,
            file_hash_sha256=file_hash,
            mime_type=f"application/{file_ext}" if file_ext != "txt" else "text/plain",
            raw_text=raw_text,
            extracted_skills=skills,
            categorized_skills=categorized,
            sections=sections,
            parser_status="completed"
        )
        self.db.add(resume)
        self.db.flush()

        # Optionally trigger async heavy processing (embeddings, ATS scoring)
        if trigger_async:
            try:
                from ..workers.tasks import async_process_resume
                async_process_resume.delay(resume.id, file_path)
                resume.parser_status = "processing"
            except Exception as e:
                logger.debug(f"[RESUME] Celery dispatch skipped (no worker): {e}")
                resume.parser_status = "completed"

        return resume.to_dict()

    def list_resumes_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List all resumes for a candidate user."""
        candidate = self.cand_repo.get_by_user_id(user_id)
        if not candidate:
            return []
        resumes = self.db.query(Resume).filter_by(
            candidate_id=candidate.id
        ).order_by(Resume.version.desc()).all()
        return [r.to_dict() for r in resumes]

    def get_analysis(self, resume_id: str) -> Dict[str, Any]:
        """Get parsed analysis for a specific resume."""
        resume = self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise NotFoundError(f"Resume {resume_id} not found")
        return {
            "resume_id": resume.id,
            "version": resume.version,
            "original_filename": resume.original_filename,
            "extracted_skills": resume.extracted_skills or [],
            "categorized_skills": resume.categorized_skills or {},
            "sections": resume.sections or {},
            "ats_score": resume.ats_score,
            "health_analysis": resume.health_analysis or {},
            "parser_status": resume.parser_status,
            "parser_version": resume.parser_version,
        }

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """Compute SHA-256 hash for file deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
