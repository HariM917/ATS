"""
TalentFlow AI — Production WSGI Entrypoint (Gunicorn / Render)
"""
from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
