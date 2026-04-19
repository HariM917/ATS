import os
import time
import traceback
import sys
import gc
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import db_manager
import train_model

try:
    from job_manager import job_bp
    HAS_JOB_BP = True
except ImportError:
    HAS_JOB_BP = False

try:
    import chatbot_rag
except ImportError:
    class MockChatbot:
        def get_response(self, msg):
            return "Chat module unavailable."
    chatbot_rag = MockChatbot()

# --- PICKLE FIX ---
BERTVectorizer = train_model.BERTVectorizer

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024 

CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["https://ats-brown.vercel.app", "http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS", "DELETE", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

if HAS_JOB_BP:
    app.register_blueprint(job_bp)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

try:
    db_manager.init_db()
except Exception as e:
    print(f"⚠️ DB Init Failed: {e}")

# 🚀 CRITICAL FIX: Removed "Auto-Train" startup sequence that was crashing Render!

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "online", "message": "AI Hiring Backend is Running!"})

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        role = data.get("role")
        mode = data.get("mode", "login")
        
        if role == "hr":
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")
            if mode == "login":
                if username == "admin" and password == "password123":
                    session["user"] = "admin"
                    session["role"] = "hr"
                    session["email"] = "admin@company.com"
                    return jsonify({"status": "success", "role": "hr", "user": "admin", "email": "admin@company.com"})
                hr_email = db_manager.verify_hr_login(username, password)
                if hr_email:
                    session["user"] = username
                    session["role"] = "hr"
                    session["email"] = hr_email
                    return jsonify({"status": "success", "role": "hr", "user": username, "email": hr_email})
                return jsonify({"status": "error", "message": "Invalid credentials"}), 401
            elif mode == "register":
                if db_manager.register_hr(username, password, email):
                    session["user"] = username
                    session["role"] = "hr"
                    session["email"] = email
                    return jsonify({"status": "success", "role": "hr", "user": username, "email": email})
                return jsonify({"status": "error", "message": "Registration failed"}), 409
        elif role == "candidate":
            username = data.get("username")
            email = data.get("email")
            if mode == "login":
                user = db_manager.login_candidate(email)
                if user:
                    session["user"] = user['username']
                    session["email"] = email
                    session["role"] = "candidate"
                    return jsonify({"status": "success", "role": "candidate", "user": user['username'], "email": email})
                return jsonify({"status": "error", "message": "Account not found"}), 401
            elif mode == "register":
                if db_manager.register_candidate(username, email):
                    session["user"] = username
                    session["email"] = email
                    session["role"] = "candidate"
                    return jsonify({"status": "success", "role": "candidate", "user": username, "email": email})
                return jsonify({"status": "error", "message": "Email already exists"}), 409
        return jsonify({"status": "error", "message": "Invalid role"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"})

@app.route("/api/profile", methods=["GET"])
def get_profile():
    email = session.get("email")
    if not email: return jsonify({"username": "Guest", "role": "guest"})
    user_data = db_manager.get_user_profile(email)
    return jsonify(user_data or {"username": session.get("user"), "email": email, "role": session.get("role")})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return jsonify({"status": "success", "filename": filename})
        return jsonify({"status": "error", "message": "Invalid file"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/candidate/match", methods=["POST"])
def candidate_match():
    try:
        # LAZY LOAD: Imports ai_engine here so the server boots instantly!
        import ai_engine
        gc.collect()
        
        data = request.get_json()
        filename = data.get("filename")
        jd_text = data.get("job_description")
        
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "File not found"}), 404
            
        resume_text = ai_engine.extract_text(filepath)
        result = ai_engine.compute_match_score(resume_text, jd_text)
        result["candidate_name"] = session.get("user", "Candidate")
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/batch_match", methods=["POST"])
def batch_match():
    try:
        import ai_engine
        gc.collect()
        
        data = request.get_json()
        candidates = data.get("candidates", [])
        jd_text = data.get("job_description")
        
        ranked_results = []
        for cand in candidates:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], cand.get("filename", ""))
            if os.path.exists(filepath):
                resume_text = ai_engine.extract_text(filepath)
                score = ai_engine.compute_match_score(resume_text, jd_text)
                score["candidate_name"] = cand.get("original_name", "Unknown")
                score["filename"] = cand.get("filename")
                ranked_results.append(score)
                
        ranked_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return jsonify({"ranked_candidates": ranked_results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        return jsonify({"response": chatbot_rag.get_response(request.get_json().get("message", ""))})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ Flask Server starting on port {port}...", flush=True)
    app.run(host="0.0.0.0", port=port, use_reloader=False)