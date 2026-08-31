"""
TalentFlow AI — Analytics and Dashboard Metrics Service
Computes hiring funnels, match distributions, applicant conversion rates, and skill demands.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Job, Application, Candidate, User, Resume


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_recruiter_overview(self, organization_id: str = None) -> Dict[str, Any]:
        job_query = self.db.query(Job)
        if organization_id:
            job_query = job_query.filter(Job.organization_id == organization_id)
        total_jobs = job_query.count()
        active_jobs = job_query.filter(Job.status == "active").count()

        total_apps = self.db.query(Application).count()
        shortlisted = self.db.query(Application).filter(Application.stage.in_(["shortlisted", "interview", "offer", "hired"])).count()
        hired = self.db.query(Application).filter(Application.stage == "hired").count()

        # Hiring Funnel Stages
        stages = ["applied", "screening", "shortlisted", "interview", "offer", "hired"]
        funnel = []
        for stage in stages:
            count = self.db.query(Application).filter(Application.stage == stage).count()
            funnel.append({"stage": stage.capitalize(), "count": count})

        # Match Score Distribution (e.g. 0-50%, 50-70%, 70-85%, 85-100%)
        scores = self.db.query(Application.score).all()
        score_distribution = [
            {"range": "90-100%", "count": sum(1 for s in scores if (s[0] or 0) >= 0.9)},
            {"range": "75-89%", "count": sum(1 for s in scores if 0.75 <= (s[0] or 0) < 0.9)},
            {"range": "60-74%", "count": sum(1 for s in scores if 0.60 <= (s[0] or 0) < 0.75)},
            {"range": "< 60%", "count": sum(1 for s in scores if (s[0] or 0) < 0.60)},
        ]

        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "total_applications": total_apps,
            "shortlisted_count": shortlisted,
            "hired_count": hired,
            "hiring_funnel": funnel,
            "score_distribution": score_distribution,
        }


analytics_service = None
