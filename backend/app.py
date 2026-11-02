"""
TalentFlow AI — Server Entrypoint Compatibility Wrapper
Redirects to the canonical wsgi entrypoint and create_app() factory.
Canonical entrypoint is: backend/wsgi.py -> app = create_app()
"""
import os
import sys
from pathlib import Path

# Prevent OpenMP thread contention across platforms
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from wsgi import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
