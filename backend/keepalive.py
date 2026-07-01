"""Ping the API health endpoint to reduce Render free-tier spin-down (optional cron)."""
import os
import sys
import urllib.request

API_BASE = os.getenv("KEEPALIVE_URL", os.getenv("RENDER_EXTERNAL_URL", ""))
if not API_BASE:
    print("KEEPALIVE_URL or RENDER_EXTERNAL_URL not set; skipping.")
    sys.exit(0)

url = API_BASE.rstrip("/") + "/api/health"
try:
    with urllib.request.urlopen(url, timeout=30) as resp:
        print(f"Keep-alive OK: {resp.status} {url}")
except Exception as e:
    print(f"Keep-alive failed: {e}", file=sys.stderr)
    sys.exit(1)
