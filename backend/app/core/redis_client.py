"""
TalentFlow AI — Redis Connection Helper with Health Check and Graceful Fallback
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis_client():
    """Get or create Redis client. Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    from .config import settings
    if not settings.redis.enabled:
        logger.info("[REDIS] Redis is disabled in configuration.")
        return None

    try:
        import redis
        client = redis.Redis.from_url(
            settings.redis.url,
            socket_timeout=settings.redis.socket_timeout,
            decode_responses=True
        )
        client.ping()
        _redis_client = client
        logger.info(f"[REDIS] Connected successfully to {settings.redis.url}")
        return _redis_client
    except Exception as e:
        logger.warning(f"[REDIS] Connection failed: {e}. Running without Redis.")
        return None


def check_redis_health() -> dict:
    """Check Redis connectivity and return status info."""
    from .config import settings
    if not settings.redis.enabled:
        return {"status": "disabled", "url": None}

    try:
        client = get_redis_client()
        if client and client.ping():
            info = client.info("server")
            return {
                "status": "connected",
                "url": settings.redis.url.split("@")[-1] if "@" in settings.redis.url else settings.redis.url,
                "version": info.get("redis_version", "unknown"),
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}

    return {"status": "unavailable"}


def check_celery_health() -> dict:
    """Check if Celery workers are reachable."""
    try:
        from ..workers.tasks import celery_app
        inspector = celery_app.control.inspect(timeout=2.0)
        active = inspector.active()
        if active:
            worker_names = list(active.keys())
            return {
                "status": "connected",
                "workers": len(worker_names),
                "worker_names": worker_names[:5],
            }
        return {"status": "no_workers"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}
