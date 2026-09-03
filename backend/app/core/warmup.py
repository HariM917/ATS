"""
TalentFlow AI — Production Subsystem Warm-Up
Pre-initializes embeddings, FAISS vector index, and database connectivity
post-fork in Gunicorn workers to eliminate cold-start latency.
"""
import logging
import threading

logger = logging.getLogger(__name__)

_warmed = False
_lock = threading.Lock()


def warm_services():
    """Execute subsystem warm-up idempotently."""
    global _warmed
    with _lock:
        if _warmed:
            return
        logger.info(">>> STARTUP: Warming AI and database subsystems...")

        # 1. Warm Database connectivity
        try:
            from .database import check_database_connection
            connected = check_database_connection()
            logger.info(f">>> STARTUP: Database connectivity check: {connected}")
        except Exception as e:
            logger.warning(f">>> STARTUP: Database warm-up ping failed: {e}")

        # 2. Warm AI Embeddings (sentence-transformers / HuggingFace)
        try:
            from ..ai.embeddings import get_embedding
            vec = get_embedding("warmup talentflow ai resume screening")
            dim = len(vec) if vec is not None else 0
            logger.info(f">>> STARTUP: Embedding warm-up complete (dim={dim})")
        except Exception as e:
            logger.warning(f">>> STARTUP: Embedding warm-up failed: {e}")

        # 3. Warm RAG Vector Index (FAISS knowledge base pre-build)
        try:
            from ..ai.rag import rag_coach
            rag_coach._ensure_index()
            kb_count = len(rag_coach.kb_items) if hasattr(rag_coach, "kb_items") else 0
            logger.info(f">>> STARTUP: RAG FAISS index warm-up complete ({kb_count} items)")
        except Exception as e:
            logger.warning(f">>> STARTUP: RAG warm-up failed: {e}")

        _warmed = True
        logger.info(">>> STARTUP: Subsystem warm-up complete.")
