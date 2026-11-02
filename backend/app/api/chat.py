"""
TalentFlow AI — AI Career Coach & RAG Assistant API v1 Blueprint
Hybrid FAISS/BM25 retrieval with curated career knowledge base and chat history.
"""
import uuid
import logging
from flask import Blueprint, request, jsonify
from ..core.database import get_db_context
from ..core.security import get_current_user
from ..ai.rag import rag_coach
from ..models import ChatMessage

logger = logging.getLogger(__name__)

chat_v1 = Blueprint("chat_v1", __name__)


@chat_v1.route("/message", methods=["POST"])
@chat_v1.route("", methods=["POST"])
def send_chat_message():
    """Send a query to the AI career coach and receive RAG-grounded response."""
    data = request.get_json(silent=True) or {}
    query = data.get("query") or data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not query:
        return jsonify({
            "status": "error",
            "error_code": "EMPTY_QUERY",
            "message": "Message query cannot be empty."
        }), 400

    response_data = rag_coach.answer_query(query)
    answer = response_data.get("answer", "")
    sources = response_data.get("sources", [])

    # Store in database if user is authenticated
    user = get_current_user()
    if user and user.get("id"):
        try:
            with get_db_context() as db:
                msg = ChatMessage(
                    user_id=user["id"],
                    session_id=session_id,
                    role="user",
                    user_text=query,
                    ai_text=answer,
                    sources=sources
                )
                db.add(msg)
        except Exception as e:
            logger.warning(f"[CHAT] Failed to persist chat message: {e}")

    result = {
        "answer": answer,
        "sources": sources,
        "session_id": session_id
    }
    return jsonify({
        "status": "success",
        "data": result,
        "answer": answer,
        "sources": sources
    })


@chat_v1.route("/history", methods=["GET"])
@chat_v1.route("/chat_history", methods=["GET"])
def get_chat_history():
    """Retrieve chat conversation history for the authenticated user."""
    user = get_current_user()
    if not user or not user.get("id"):
        return jsonify({
            "status": "success",
            "data": [],
            "history": []
        })

    with get_db_context() as db:
        messages = db.query(ChatMessage).filter_by(
            user_id=user["id"]
        ).order_by(ChatMessage.created_at.asc()).limit(50).all()

        history = [
            {
                "id": str(m.id),
                "user": m.user_text,
                "ai": m.ai_text,
                "sources": m.sources or [],
                "timestamp": int(m.created_at.timestamp() * 1000) if m.created_at else None
            }
            for m in messages
        ]
        return jsonify({
            "status": "success",
            "data": history,
            "history": history
        })

