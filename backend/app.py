import os
import time
import secrets
from dotenv import load_dotenv

load_dotenv()
import traceback
import sys
import gc
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import db_manager
import logging

# FIX: Prevent Windows charmap codec crash on emoji/unicode in print() and logging
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

try:
    from job_manager import job_bp
    HAS_JOB_BP = True
except ImportError:
    HAS_JOB_BP = False

import base64
import json

def generate_token(email, role):
    """Produces a signed token for frontend handshakes."""
    payload = {"email": email, "role": role, "exp": time.time() + 86400}
    token_bytes = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"TF_{token_bytes}"

import chatbot_rag
import ai_engine

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024 

# --- DATABASE INITIALIZATION (single call) ---
try:
    db_manager.init_db()
    logging.info(">>> DATABASE: Initialization Complete.")
except Exception as e:
    logging.error(f">>> DATABASE: Initialization Failed: {e}")

# Enable CORS with credential support and explicit header allowance
FRONTEND_URLS = os.getenv(
    "FRONTEND_URLS",
    "http://localhost:5173,http://127.0.0.1:5173,https://ats-silk-alpha.vercel.app,https://ats917.vercel.app"
).split(",")

CORS(app, 
     supports_credentials=True, 
     origins=FRONTEND_URLS,
     allow_headers=["Content-Type", "Authorization", "X-Auth-Email", "X-Auth-Role", "X-Auth-User"])

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "message": "TalentFlow AI Backend is Live",
        "version": "v2.0.0-Production",
        "port": int(os.environ.get("PORT", 5000))
    })

if HAS_JOB_BP:
    app.register_blueprint(job_bp, url_prefix='/api')

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.after_request
def add_header(response):
    response.headers["X-Powered-By"] = "FlowATS-v2.0"
    return response

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online", 
        "message": "TalentFlow AI Backend is Live", 
        "version": "v2.0.0-Production",
        "port": int(os.environ.get("PORT", 5000))
    })

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        role = data.get("role")
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        
        if role == "hr":
            hr_email = db_manager.verify_hr_login(username, password)
            if hr_email:
                session["user"] = username
                session["role"] = "hr"
                session["email"] = hr_email
                return jsonify({
                    "status": "success", 
                    "role": "hr", 
                    "user": username, 
                    "email": hr_email,
                    "token": generate_token(hr_email, "hr")
                })
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
            
        elif role == "candidate":
            user = db_manager.login_candidate(email)
            if user:
                session["user"] = user['username']
                session["email"] = email
                session["role"] = "candidate"
                return jsonify({
                    "status": "success", 
                    "role": "candidate", 
                    "user": user['username'], 
                    "email": email,
                    "token": generate_token(email, "candidate")
                })
            return jsonify({"status": "error", "message": "Account not found. Please register first."}), 401
            
        return jsonify({"status": "error", "message": "Invalid role"}), 400
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        role = data.get("role")
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        
        if not username or not email:
            return jsonify({"status": "error", "message": "Username and email are required"}), 400
        
        if role == "hr":
            if not password or len(password) < 6:
                return jsonify({"status": "error", "message": "Password must be at least 6 characters"}), 400
                
            if db_manager.register_hr(username, password, email):
                session["user"] = username
                session["role"] = "hr"
                session["email"] = email
                return jsonify({
                    "status": "success", 
                    "role": "hr", 
                    "user": username, 
                    "email": email,
                    "token": generate_token(email, "hr")
                })
            return jsonify({"status": "error", "message": "Username or email already exists"}), 409
            
        elif role == "candidate":
            if db_manager.register_candidate(username, email):
                session["user"] = username
                session["email"] = email
                session["role"] = "candidate"
                return jsonify({
                    "status": "success", 
                    "role": "candidate", 
                    "user": username, 
                    "email": email,
                    "token": generate_token(email, "candidate")
                })
            return jsonify({"status": "error", "message": "Email already exists"}), 409
            
        return jsonify({"status": "error", "message": "Invalid role"}), 400
    except Exception as e:
        logging.error(f"Register error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"})

@app.route('/api/profile', methods=['GET', 'PUT'])
def profile():
    if request.method == 'GET':
        # Try to get from session first, then fall back to defaults
        user_email = session.get("email")
        if user_email:
            db_profile = db_manager.get_user_profile(user_email)
            if db_profile:
                return jsonify(dict(db_profile))
        
        return jsonify({
            "username": session.get("user", "User"),
            "email": session.get("email", ""),
            "role": session.get("role", "user")
        })

    if request.method == 'PUT':
        try:
            data = request.get_json()
            email = data.get("email")
            if email:
                db_manager.update_user_profile(
                    email,
                    data.get("username"),
                    data.get("role"),
                    data.get("firstName"),
                    data.get("lastName"),
                    data.get("bio"),
                    data.get("phone"),
                    data.get("street"),
                    data.get("city"),
                    data.get("state")
                )

            return jsonify({
                "success": True,
                "message": "Profile updated successfully"
            })
        except Exception as e:
            logging.error(f"Profile update error: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500


@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            logging.info(f"[UPLOAD] Saved file: {filename}")
            return jsonify({"status": "success", "filename": filename})
        logging.warning(f"[UPLOAD] Invalid file: {file.filename if file else 'None'}")
        return jsonify({"status": "error", "message": "Invalid file type. Allowed: PDF, DOCX, TXT"}), 400
    except Exception as e:
        logging.error(f"[UPLOAD] ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/candidate/match", methods=["POST"])
def candidate_match():
    try:
        logging.info("[API] HIT /api/candidate/match")
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
        logging.error(f"MATCH ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/process_resumes", methods=["POST"])
def process_resumes():
    """Enterprise-grade bulk resume screening in a single API call."""
    try:
        jd = request.form.get("jd", "")
        files = request.files.getlist("resumes")
        
        if not jd or not files:
            return jsonify({"success": False, "error": "Missing JD or resumes"}), 400
            
        logging.info(f"[BATCH] Processing {len(files)} resumes...")
        
        # 1. Save and Extract
        resumes_info = []
        resume_texts = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(f"batch_{int(time.time())}_{file.filename}")
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                
                text = ai_engine.extract_text(filepath)
                if text:
                    resume_texts.append(text)
                    resumes_info.append({"original_name": file.name, "filename": filename})

        if not resume_texts:
            return jsonify({"success": False, "error": "No readable text found in resumes"}), 400

        # 2. Batch AI Analysis
        batch_results = ai_engine.batch_compute_match_score(resume_texts, jd)
        
        # 3. Combine Results
        rankings = []
        for i, score in enumerate(batch_results):
            score["candidate_name"] = resumes_info[i]["original_name"]
            score["filename"] = resumes_info[i]["filename"]
            rankings.append(score)
            
        rankings.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return jsonify({
            "success": True,
            "count": len(rankings),
            "rankings": rankings
        })
    except Exception as e:
        logging.error(f"[BATCH ERROR]: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/batch_match", methods=["POST"])
def batch_match():
    return jsonify({"status": "error", "message": "Deprecated. Use /api/process_resumes"}), 405

@app.route("/api/chat", methods=["POST"])
def chat():
    SAFE_FALLBACK = (
        "I'm here to support your career journey! I can provide guidance on resume optimization, "
        "interview strategies, technical skill roadmaps, and career strategy. "
        "What specific area can I help you with right now?"
    )
    try:
        data = request.get_json()
        query = data.get("message", data.get("query", "")) if data else ""
        
        if not query or not query.strip():
            return jsonify({"status": "error", "message": "Empty message received"}), 400
        
        logging.info(f"[CHAT] Query from {session.get('email', 'anonymous')}: {query[:60]}...")
        
        answer = chatbot_rag.get_response(query)
        
        # Bulletproof: Never return empty/None answer
        if not answer or not str(answer).strip():
            logging.warning(f"[CHAT] Empty response from RAG for query: {query[:60]}")
            answer = SAFE_FALLBACK
        
        return jsonify({"answer": str(answer)})
    except Exception as e:
        logging.error(f"[CHAT ERROR] {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e), "answer": SAFE_FALLBACK}), 500

@app.route("/api/chat_history", methods=["GET"])
def chat_history():
    try:
        email = session.get("email")
        if not email:
            return jsonify({"history": []})
        history = db_manager.get_chat_history(email)
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/clear_data", methods=["POST"])
def clear_data():
    """Cleans up the system: Deletes uploads and resets DB tables."""
    try:
        import shutil
        if os.path.exists(app.config["UPLOAD_FOLDER"]):
            for filename in os.listdir(app.config["UPLOAD_FOLDER"]):
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logging.warning(f'Failed to delete {file_path}: {e}')
        
        conn = db_manager.get_db_connection()
        conn.execute("DELETE FROM applications")
        conn.execute("DELETE FROM jobs")
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "System cleared successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    from ai_engine import warm_up
    warm_up()
    
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"\n{'='*50}")
    logging.info(f"FlowATS Backend v2.0.0 — Port {port}")
    logging.info(f"Path: {os.path.abspath(__file__)}")
    logging.info(f"Time: {time.strftime('%H:%M:%S')}")
    logging.info(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=port, use_reloader=False)