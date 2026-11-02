"""
TalentFlow AI — Semantic Matching & Occupational Classification API v1 Blueprint
Preserves the production 22-Class Occupational Classifier (Phase V21/V23 Champion).
"""
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import require_auth, require_hr
from ..ai.matching_engine import compute_match
from ..models import MatchResult, RoleCatalog

logger = logging.getLogger(__name__)

matching_v1 = Blueprint("matching_v1", __name__)


@matching_v1.route("/evaluate", methods=["POST"])
@require_auth
def evaluate_resume():
    """
    Evaluate resume vs job description or target role.
    Integrates job suggestions, multi-dimensional job matching, ATS resume quality analyzer,
    and synthesized actionable suggestions.
    """
    data = request.get_json(silent=True) or {}
    resume_text = data.get("resume_text", "")
    resume_id = data.get("resume_id")
    jd_text = data.get("job_description", "")
    required_skills = data.get("required_skills", "")
    role_id = data.get("role_id")
    specific_role_param = data.get("specific_role")

    file_path = None
    if resume_id:
        with get_db_context() as db:
            from ..models.resume import Resume
            r_obj = db.query(Resume).filter_by(id=resume_id).first()
            if r_obj:
                file_path = getattr(r_obj, "file_path", None)
                db_raw_text = getattr(r_obj, "raw_text", "")
                if not resume_text:
                    resume_text = db_raw_text
                if not resume_text and file_path and os.path.exists(file_path):
                    from ..ai.resume_parser import extract_text_from_file
                    resume_text = extract_text_from_file(file_path)
                    if resume_text:
                        r_obj.raw_text = resume_text
                        db.commit()

    target_role_info = None
    if role_id or specific_role_param:
        with get_db_context() as db:
            query = db.query(RoleCatalog)
            if role_id:
                role_obj = query.filter_by(id=role_id).first()
            else:
                role_obj = query.filter(RoleCatalog.name.ilike(specific_role_param)).first()
            if role_obj:
                target_role_info = role_obj.to_dict()
                desc = target_role_info.get("description")
                if not jd_text and desc:
                    jd_text = desc
                role_skills = target_role_info.get("skills") or []
                if not required_skills and role_skills:
                    required_skills = ", ".join(str(s) for s in role_skills)

    try:
        exp_years = int(data.get("experience_required", 0))
    except (ValueError, TypeError):
        exp_years = 0

    from ..services.resume_analysis_service import ResumeAnalysisService
    result = ResumeAnalysisService.analyze_career(
        resume_text=resume_text,
        job_description=jd_text,
        file_path=file_path,
        explicit_skills_req=required_skills,
        target_role_info=target_role_info,
        experience_required_years=exp_years
    )

    return jsonify({
        "status": "success",
        "data": result,
        "result": result,
        "analysis": result
    })


@matching_v1.route("/batch-screen/<job_id>", methods=["POST"])
@require_hr
def batch_screen_job(job_id):
    """Trigger batch AI screening for all applicants of a job."""
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
        logger.info(f"[MATCHING] Celery unavailable, running batch screen synchronously: {e}")
        from ..workers.tasks import async_batch_screen
        result = async_batch_screen(None, job_id)
        return jsonify({
            "status": "success",
            "data": result,
            "result": result
        })


@matching_v1.route("/rankings/<job_id>", methods=["GET"])
@require_hr
def get_rankings(job_id):
    """Get ranked candidates for a job, sorted by match score descending."""
    with get_db_context() as db:
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
        return jsonify({
            "status": "success",
            "data": rankings,
            "rankings": rankings
        })

