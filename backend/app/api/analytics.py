"""
TalentFlow AI — Analytics and Dashboard Metrics API v1 Blueprint
"""
import logging
from flask import Blueprint, jsonify
from ..core.database import get_db_context
from ..core.security import require_hr, current_user
from ..services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

analytics_v1 = Blueprint("analytics_v1", __name__)


@analytics_v1.route("/overview", methods=["GET"])
def get_system_overview():
    """Get high-level ATS platform overview metrics."""
    with get_db_context() as db:
        analytics = AnalyticsService(db)
        data = analytics.get_overview()
        return jsonify({
            "status": "success",
            "data": data
        })


@analytics_v1.route("/recruiter", methods=["GET"])
@require_hr
def get_recruiter_analytics():
    """Get detailed hiring pipeline funnel and score distributions (HR/Recruiter only)."""
    user = current_user()
    org_id = user.get("org_id")
    with get_db_context() as db:
        analytics = AnalyticsService(db)
        overview = analytics.get_recruiter_overview(organization_id=str(org_id) if org_id else None)
        return jsonify({
            "status": "success",
            "data": overview
        })

