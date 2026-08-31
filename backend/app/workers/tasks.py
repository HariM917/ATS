"""
TalentFlow AI — Celery Background Workers & Asynchronous Tasks
Offloads heavy PDF parsing, multi-candidate AI screening, and email notifications to Redis workers.
"""
import os
import logging
from celery import Celery
from ..core.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery
redis_url = settings.redis.url if settings.redis.enabled else "redis://localhost:6379/0"

celery_app = Celery(
    "talentflow_workers",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min hard limit
    worker_prefetch_multiplier=1
)


@celery_app.task(name="tasks.async_process_resume", bind=True)
def async_process_resume(self, resume_id: str, file_path: str):
    """Background task to extract text, extract skills, and compute embeddings for uploaded resume."""
    from ..core.database import get_db_context
    from ..models import Resume
    from ..ai.resume_parser import extract_text_from_file, extract_sections
    from ..ai.skill_extractor import extract_skills, categorize_skills

    logger.info(f"[WORKER] Starting async resume processing for ID={resume_id}")
    raw_text = extract_text_from_file(file_path)
    skills = extract_skills(raw_text)
    categorized = categorize_skills(skills)
    sections = extract_sections(raw_text)

    with get_db_context() as db:
        resume = db.query(Resume).filter_by(id=resume_id).first()
        if resume:
            resume.raw_text = raw_text
            resume.extracted_skills = skills
            resume.categorized_skills = categorized
            resume.sections = sections
            resume.parser_status = "completed"
            db.commit()
            logger.info(f"[WORKER] Completed processing resume ID={resume_id} ({len(skills)} skills found)")
            return {"status": "completed", "skills_count": len(skills)}

    return {"status": "not_found"}


@celery_app.task(name="tasks.async_batch_screen", bind=True)
def async_batch_screen(self, job_id: str):
    """Background task to evaluate all candidate applications for a specific job."""
    from ..core.database import get_db_context
    from ..models import Job, Application, MatchResult, Resume
    from ..ai.matching_engine import compute_match

    logger.info(f"[WORKER] Starting batch screening for Job ID={job_id}")
    with get_db_context() as db:
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            return {"status": "job_not_found"}

        apps = db.query(Application).filter_by(job_id=job_id).all()
        screened_count = 0

        for app in apps:
            resume = db.query(Resume).filter_by(candidate_id=app.candidate_id, is_current=True).first()
            if resume and resume.raw_text:
                result = compute_match(
                    resume_text=resume.raw_text,
                    job_description=job.description,
                    required_skills_str=job.required_skills or "",
                    experience_required_years=job.experience_required,
                    scoring_weights=job.scoring_config
                )
                app.score = result["final_score"]
                # Create or update MatchResult
                match_res = db.query(MatchResult).filter_by(application_id=app.id).first()
                if not match_res:
                    match_res = MatchResult(
                        job_id=job.id,
                        candidate_id=app.candidate_id,
                        resume_id=resume.id,
                        application_id=app.id,
                        final_score=result["final_score"],
                        semantic_score=result["semantic_score"],
                        skill_score=result["skill_score"],
                        matched_skills=result["matched_skills"],
                        missing_skills=result["missing_skills"],
                        explanation=result["explanation"]
                    )
                    db.add(match_res)
                else:
                    match_res.final_score = result["final_score"]
                    match_res.explanation = result["explanation"]
                screened_count += 1

        db.commit()
        logger.info(f"[WORKER] Batch screening complete for Job ID={job_id}: {screened_count} evaluated.")
        return {"status": "completed", "screened_count": screened_count}
