"""
TalentFlow AI — Roles Catalog API v1 Blueprint
Provides endpoints to fetch controlled occupational roles and specific role specializations.
"""
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..services.role_service import RoleService

logger = logging.getLogger(__name__)

roles_v1 = Blueprint("roles_v1", __name__)


@roles_v1.route("", methods=["GET"])
def get_roles():
    """
    List controlled roles with optional filtering by occupational_class or search query.
    Example: GET /api/v1/roles?occupational_class=INFORMATION-TECHNOLOGY&search=engineer
    """
    domain = request.args.get("domain") or request.args.get("occupational_class")
    search = request.args.get("search")

    with get_db_context() as db:
        service = RoleService(db)
        roles = service.list_roles(occupational_class=domain, search=search)
        return jsonify({
            "status": "success",
            "data": roles,
            "roles": roles,
            "count": len(roles)
        })

