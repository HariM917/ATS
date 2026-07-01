"""
Central warm-up for gunicorn and local dev — avoids cold-first-request latency on Render.
"""
import logging
import os
import threading

_warmed = False
_lock = threading.Lock()

logger = logging.getLogger(__name__)


def warm_services():
    global _warmed
    with _lock:
        if _warmed:
            return
        logger.info(">>> STARTUP: Warming AI services...")
        try:
            from ai_engine import warm_up

            warm_up()
        except Exception as e:
            logger.warning(f">>> STARTUP: ai_engine warm-up failed: {e}")

        try:
            from chatbot_rag import warm_rag_index

            warm_rag_index()
        except Exception as e:
            logger.warning(f">>> STARTUP: RAG warm-up failed: {e}")

        _warmed = True
        logger.info(">>> STARTUP: Warm-up complete.")
