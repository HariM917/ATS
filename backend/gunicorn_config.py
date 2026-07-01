"""Gunicorn configuration for Render production deployments."""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = 5
preload_app = True


def post_fork(server, worker):
    """Warm AI subsystems in each worker after fork (safe with preload)."""
    try:
        from startup import warm_services

        warm_services()
    except Exception as exc:
        server.log.warning(f"Worker warm-up failed: {exc}")
