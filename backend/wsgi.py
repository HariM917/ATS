"""
TalentFlow AI — Production WSGI Entrypoint (Gunicorn / Render)
"""
from app.factory import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
