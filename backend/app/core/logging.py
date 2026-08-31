"""
TalentFlow AI — Structured Logging Configuration
"""
import sys
import logging
from .config import settings


def setup_logging(level: str = "INFO") -> None:
    """Configure standardized application logger with timestamps and levels."""
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Silence verbose 3rd party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.INFO if settings.is_development else logging.WARNING)
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("transformers").setLevel(logging.ERROR)
