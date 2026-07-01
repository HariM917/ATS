"""WSGI entrypoint for production (gunicorn wsgi:app)."""
from startup import warm_services

# Import app after env is loaded in app module
from app import app  # noqa: E402

warm_services()
