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
from ..models import Candidate, Resume, User
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
            user = self.db.query(User).filter_by(id=user_id).first()
            cand_name = (user.username if user and user.username else None) or (user.email.split('@')[0] if user and user.email else "Candidate")
            candidate = Candidate(user_id=user_id, name=cand_name)
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
            r.is_current = False  # type: ignore

        # Determine version number
        version = self.db.query(Resume).filter_by(candidate_id=candidate.id).count() + 1

        # Synchronous processing (fast path)
        raw_text = extract_text_from_file(file_path)
        skills = extract_skills(raw_text)
        categorized = categorize_skills(skills)
        sections = extract_sections(raw_text)

        # Resume Quality & ATS Document Formatting Analysis
        from .resume_quality_analyzer import ResumeQualityAnalyzer
        quality_analysis = ResumeQualityAnalyzer.analyze_resume(file_path=file_path, raw_text=raw_text)

        # 22-Class Occupational Classification (Phase V21/V23 Champion)
        try:
            from .occupational_classifier import get_occupational_classifier
            classifier = get_occupational_classifier()
            occ_result = classifier.predict(raw_text, include_specific_role=True)
        except Exception as e:
            logger.warning(f"[RESUME] Occupational classification fallback: {e}")
            occ_result = {
                "predicted_role": "UNKNOWN",
                "confidence": 0.0,
                "runner_up_role": "UNKNOWN",
                "runner_up_confidence": 0.0,
                "margin": 0.0,
                "review_required": True,
                "review_reasons": [f"Classifier unavailable: {e}"],
                "model_version": "v21-v23-final",
                "taxonomy_version": "22-class-occupational-v1",
                "specific_role": "General Professional",
                "specific_role_confidence": 0.0,
                "occupational_domain": "Unknown"
            }

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
            predicted_role=occ_result.get("predicted_role"),
            ats_score=float(quality_analysis.get("formatting_score", 0)),
            health_analysis={
                "occupational_classification": occ_result,
                "quality_analysis": quality_analysis,
                "formatting_score": quality_analysis.get("formatting_score", 0),
                "is_ats_friendly": quality_analysis.get("is_ats_friendly", True)
            },
            parser_status="completed"
        )
        self.db.add(resume)
        self.db.flush()

        # Optionally trigger async heavy processing (embeddings, ATS scoring)
        if trigger_async:
            try:
                from ..workers.tasks import async_process_resume
                async_process_resume.delay(resume.id, file_path)  # type: ignore
                resume.parser_status = "processing"  # type: ignore
            except Exception as e:
                logger.debug(f"[RESUME] Celery dispatch skipped (no worker): {e}")
                resume.parser_status = "completed"  # type: ignore

        res_dict = resume.to_dict()
        res_dict["occupational_classification"] = occ_result
        return res_dict

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
        
        health = resume.health_analysis or {}
        occ = health.get("occupational_classification")
        predicted = getattr(resume, "predicted_role", None)
        if not occ and predicted:
            occ = {
                "predicted_role": str(predicted),
                "confidence": 1.0,
                "runner_up_role": "UNKNOWN",
                "runner_up_confidence": 0.0,
                "margin": 1.0,
                "review_required": False,
                "review_reasons": [],
                "model_version": "v21-v23-final",
                "taxonomy_version": "22-class-occupational-v1"
            }

        return {
            "resume_id": resume.id,
            "version": resume.version,
            "original_filename": resume.original_filename,
            "extracted_skills": resume.extracted_skills or [],
            "categorized_skills": resume.categorized_skills or {},
            "sections": resume.sections or {},
            "predicted_role": resume.predicted_role,
            "occupational_classification": occ,
            "ats_score": resume.ats_score,
            "health_analysis": health,
            "parser_status": resume.parser_status,
            "parser_version": resume.parser_version,
        }

    def get_resume(self, resume_id: str) -> Dict[str, Any]:
        """Get resume by ID."""
        resume = self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise NotFoundError(f"Resume {resume_id} not found")
        return resume.to_dict()

    def delete_resume(self, resume_id: str, user_id: str) -> bool:
        """Delete resume by ID, ensuring ownership."""
        candidate = self.cand_repo.get_by_user_id(user_id)
        resume = self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise NotFoundError(f"Resume {resume_id} not found")
        if candidate and resume.candidate_id != candidate.id:
            raise NotFoundError("Resume does not belong to candidate")

        # Delete physical file if exists
        try:
            file_path = str(resume.file_path) if resume.file_path else None
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"[RESUME] Could not remove physical file {resume.file_path}: {e}")

        self.db.delete(resume)
        self.db.flush()
        return True

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """Compute SHA-256 hash for file deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

