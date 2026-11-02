"""
TalentFlow AI — Canonical Production WSGI Entrypoint (Gunicorn / Render / Local Flask)
Used identically for both local development and production.
"""
import os
import sys
from pathlib import Path

# Prevent OpenMP runtime library deadlock / resource exhaustion across platforms
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
