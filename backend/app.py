"""
FlowATS API Server — Production v3.0
JWT-based auth, unified user system, production-grade error handling.
"""
import os
import time
import secrets
from dotenv import load_dotenv

load_dotenv()
import traceback
import sys
import gc
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import ClientDisconnected, BadRequest
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

import chatbot_rag
import ai_engine
from auth_utils import (
    create_jwt, create_access_token, create_refresh_token, decode_token, revoke_token,
    get_current_user, current_user,
    require_auth, require_role, require_hr, require_admin_secret
)
from app.core.config import settings
from app.core.middleware import register_security_headers, register_error_handlers, limiter

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.secret_key = settings.auth.flask_secret_key or secrets.token_hex(32)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = settings.storage.max_upload_size_mb * 1024 * 1024

# Register Enterprise Security Headers & Handlers
register_security_headers(app)
register_error_handlers(app)
limiter.init_app(app)

# --- DATABASE INITIALIZATION (single call) ---
try:
    db_manager.init_db()
    db_manager.add_extracted_skills_column()  # Ensure extracted_skills column exists
    logging.info(">>> DATABASE: Initialization Complete.")
except Exception as e:
    logging.error(f">>> DATABASE: Initialization Failed: {e}")

# --- CORS Configuration ---
CORS(app,
     origins=settings.cors_origins,
     allow_headers=["Content-Type", "Authorization", "X-Admin-Secret", "X-Request-ID"],
     supports_credentials=True)

if HAS_JOB_BP:
    app.register_blueprint(job_bp, url_prefix='/api')

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = set(settings.storage.allowed_extensions)
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



# ============================================
# Health & Warm-up
# ============================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "FlowATS AI Backend is Live",
        "version": "v3.0.0-Production",
        "port": int(os.environ.get("PORT", 5000))
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    hf_ok = bool(os.getenv("HF_TOKEN") or os.getenv("HF_API_TOKEN"))
    db_ok = False
    try:
        conn = db_manager.get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    rag_ready = chatbot_rag.is_index_ready()
    status = "online" if db_ok else "degraded"

    return jsonify({
        "status": status,
        "message": "FlowATS AI Backend is Live",
        "version": "v3.0.0-Production",
        "port": int(os.environ.get("PORT", 5000)),
        "checks": {
            "database": db_ok,
            "huggingface_token": hf_ok,
            "rag_index": rag_ready,
        },
    })


@app.route("/api/warm", methods=["GET", "POST"])
def warm_endpoint():
    """Optional wake-up endpoint (set WARMUP_SECRET in env to protect)."""
    secret = os.getenv("WARMUP_SECRET", "")
    if secret and request.headers.get("X-Warmup-Secret") != secret:
        return jsonify({"status": "forbidden"}), 403
    from startup import warm_services
    warm_services()
    return jsonify({"status": "ok", "rag_index": chatbot_rag.is_index_ready()})


# ============================================
# Authentication (JWT)
# ============================================

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body required"}), 400

        role = data.get("role")
        username = data.get("username", "")
        password = data.get("password", "")
        email = data.get("email", "")

        if role == "hr":
            if not username or not password:
                return jsonify({"status": "error", "message": "Username and password required"}), 400

            # Try unified auth first
            user = db_manager.verify_login(email, password) if email else None

            # Fallback to legacy username-based HR login
            if not user:
                hr_email = db_manager.verify_hr_login(username, password)
                if hr_email:
                    user = db_manager.get_user_by_email(hr_email)
                    if not user:
                        # Legacy user not migrated — create in unified table
                        user = {
                            'id': 0, 'email': hr_email,
                            'role': 'hr', 'username': username
                        }

            if user:
                token = create_access_token(user['id'], user['email'], 'hr', user.get('username', username))
                refresh_token = create_refresh_token(user['id'], user['email'], 'hr')
                return jsonify({
                    "status": "success",
                    "role": "hr",
                    "user": user.get('username', username),
                    "email": user['email'],
                    "token": token,
                    "refresh_token": refresh_token
                })
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401

        elif role == "candidate":
            if not email:
                return jsonify({"status": "error", "message": "Email required"}), 400

            # Try unified auth with password
            if password:
                user = db_manager.verify_login(email, password)
                if user:
                    token = create_access_token(user['id'], user['email'], 'candidate', user.get('username', username))
                    refresh_token = create_refresh_token(user['id'], user['email'], 'candidate')
                    return jsonify({
                        "status": "success",
                        "role": "candidate",
                        "user": user.get('username', username),
                        "email": user['email'],
                        "token": token,
                        "refresh_token": refresh_token
                    })

            # Fallback: legacy candidate login
            candidate = db_manager.login_candidate(email)
            if candidate:
                token = create_access_token(candidate.get('id', 0), email, 'candidate', candidate.get('username', username))
                refresh_token = create_refresh_token(candidate.get('id', 0), email, 'candidate')
                return jsonify({
                    "status": "success",
                    "role": "candidate",
                    "user": candidate.get('username', username),
                    "email": email,
                    "token": token,
                    "refresh_token": refresh_token
                })

            return jsonify({"status": "error", "message": "Account not found. Please register first."}), 401

        return jsonify({"status": "error", "message": "Invalid role"}), 400
    except Exception as e:
        logging.error(f"[AUTH] Login error: {e}")
        return jsonify({"status": "error", "message": "Login failed. Please try again."}), 500


@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Request body required"}), 400

        role = data.get("role")
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        email = data.get("email", "").strip().lower()

        if not username or not email:
            return jsonify({"status": "error", "message": "Username and email are required"}), 400

        if not password or len(password) < 6:
            return jsonify({"status": "error", "message": "Password must be at least 6 characters"}), 400

        if role == "hr":
            user_id = db_manager.register_user(email, password, 'hr', username,
                                                company_name=data.get('company_name', 'Company'))
            if user_id:
                # Also insert into legacy hr_users for backward compat
                try:
                    db_manager.register_hr(username, password, email)
                except Exception:
                    pass

                token = create_access_token(user_id, email, 'hr', username)
                refresh_token = create_refresh_token(user_id, email, 'hr')
                return jsonify({
                    "status": "success",
                    "role": "hr",
                    "user": username,
                    "email": email,
                    "token": token,
                    "refresh_token": refresh_token
                })
            return jsonify({"status": "error", "message": "Email already exists"}), 409

        elif role == "candidate":
            user_id = db_manager.register_user(email, password, 'candidate', username,
                                                branch=data.get('branch'),
                                                graduation_year=data.get('graduation_year'))
            if user_id:
                token = create_access_token(user_id, email, 'candidate', username)
                refresh_token = create_refresh_token(user_id, email, 'candidate')
                return jsonify({
                    "status": "success",
                    "role": "candidate",
                    "user": username,
                    "email": email,
                    "token": token,
                    "refresh_token": refresh_token
                })
            return jsonify({"status": "error", "message": "Email already exists"}), 409

        return jsonify({"status": "error", "message": "Invalid role"}), 400
    except Exception as e:
        logging.error(f"[AUTH] Register error: {e}")
        return jsonify({"status": "error", "message": "Registration failed. Please try again."}), 500


@app.route("/api/auth/refresh", methods=["POST"])
def refresh_token_endpoint():
    """Rotate access token using a valid refresh token."""
    try:
        data = request.get_json(silent=True) or {}
        refresh_token = data.get("refresh_token") or request.headers.get("X-Refresh-Token")
        if not refresh_token:
            return jsonify({"status": "error", "message": "refresh_token required"}), 400

        payload = decode_token(refresh_token, is_refresh=True)
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        new_access_token = create_access_token(user_id, email, role)
        new_refresh_token = create_refresh_token(user_id, email, role)

        # Invalidate old refresh token (rotation)
        revoke_token(refresh_token)

        return jsonify({
            "status": "success",
            "token": new_access_token,
            "refresh_token": new_refresh_token
        })
    except Exception as e:
        logging.warning(f"[AUTH] Refresh failed: {e}")
        return jsonify({"status": "error", "message": "Invalid or expired refresh token"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    """Revoke current access token on logout."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        revoke_token(token)
    return jsonify({"status": "success", "message": "Logged out successfully"})



# ============================================
# Profile
# ============================================

@app.route('/api/profile', methods=['GET', 'PUT'])
def profile():
    # Try to get user from JWT, but don't require it (GET can be anonymous)
    user = get_current_user()

    if request.method == 'GET':
        if user and user.get("email"):
            db_profile = db_manager.get_user_profile(user["email"])
            if db_profile:
                return jsonify(dict(db_profile))

        return jsonify({
            "username": user.get("user", "User") if user else "User",
            "email": user.get("email", "") if user else "",
            "role": user.get("role", "user") if user else "user"
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
                    data.get("state"),
                    branch=data.get("branch"),
                    graduation_year=data.get("graduation_year"),
                    resume_path=data.get("resume_path"),
                    company_name=data.get("company_name")
                )

            return jsonify({
                "success": True,
                "message": "Profile updated successfully"
            })
        except Exception as e:
            logging.error(f"[PROFILE] Update error: {e}")
            return jsonify({
                "success": False,
                "message": "Failed to update profile"
            }), 500


# ============================================
# File Upload
# ============================================

@app.route("/api/upload", methods=["POST"])
@require_auth
def upload_file():
    try:
        file = request.files.get("file")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            logging.info(f"[UPLOAD] Saved file: {filename}")
            return jsonify({"status": "success", "filename": filename})
        logging.warning(f"[UPLOAD] Invalid file: {file.filename if file else 'None'}")
        return jsonify({"status": "error", "message": "Invalid file type. Allowed: PDF, DOCX, TXT"}), 400
    except ClientDisconnected:
        logging.warning("[UPLOAD] Client disconnected during file upload.")
        return jsonify({"status": "error", "message": "Client disconnected before upload finished"}), 400
    except BadRequest as e:
        logging.warning(f"[UPLOAD] Bad Request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logging.error(f"[UPLOAD] ERROR: {e}")
        return jsonify({"status": "error", "message": "Upload failed"}), 500


@app.route("/api/upload_and_extract", methods=["POST"])
@require_auth
def upload_and_extract():
    """Upload a resume file and immediately extract all skills, role, experience.
    Returns structured extraction results so the frontend can display them instantly.
    """
    try:
        if "file" not in request.files:
            logging.warning("[UPLOAD+EXTRACT] 'file' key missing in multipart request")
            return jsonify({"status": "error", "message": "No file field in request"}), 400

        file = request.files.get("file")
        if not file or not file.filename:
            logging.warning("[UPLOAD+EXTRACT] Empty file object received")
            return jsonify({"status": "error", "message": "No file selected"}), 400

        if not allowed_file(file.filename):
            logging.warning(f"[UPLOAD+EXTRACT] Disallowed extension: {file.filename}")
            return jsonify({
                "status": "error",
                "message": f"File type not supported for '{file.filename}'. Allowed: PDF, DOCX, TXT"
            }), 400

        # 1. Save file
        filename = secure_filename(f"{int(time.time())}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        logging.info(f"[UPLOAD+EXTRACT] Saved file successfully: {filename}")

        # 2. Run full extraction
        extraction = ai_engine.extract_resume_data(filepath)
        extraction["filename"] = filename

        # 3. Persist extracted skills to candidate profile
        user = get_current_user()
        if user and user.get("email"):
            db_manager.save_extracted_skills(
                user["email"],
                extraction.get("extracted_skills", []),
                extraction.get("predicted_role")
            )
            # Also update resume_path on the candidate profile
            db_manager.update_user_profile(
                user["email"],
                username=None, role=None,
                first_name=None, last_name=None,
                bio=None, phone=None, street=None, city=None, state=None,
                resume_path=filename
            )

        return jsonify(extraction)

    except ClientDisconnected:
        logging.warning("[UPLOAD+EXTRACT] Client disconnected during file upload.")
        return jsonify({
            "status": "error",
            "message": "Upload aborted by client",
            "extracted_skills": [],
            "skill_categories": {},
            "predicted_role": "Unknown",
            "total_skills": 0
        }), 400
    except BadRequest as e:
        logging.warning(f"[UPLOAD+EXTRACT] Bad request: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "extracted_skills": [],
            "skill_categories": {},
            "predicted_role": "Unknown",
            "total_skills": 0
        }), 400
    except Exception as e:
        logging.error(f"[UPLOAD+EXTRACT] ERROR: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": "Upload and extraction failed",
            "extracted_skills": [],
            "skill_categories": {},
            "predicted_role": "Unknown",
            "total_skills": 0
        }), 500


@app.route("/api/resume/skills", methods=["GET"])
@require_auth
def get_resume_skills():
    """Retrieves previously extracted skills for the authenticated candidate."""
    try:
        user = get_current_user()
        if not user or not user.get("email"):
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        result = db_manager.get_extracted_skills(user["email"])
        if result:
            # Also categorize skills for display
            result["skill_categories"] = ai_engine.categorize_skills(result.get("extracted_skills", []))
            result["total_skills"] = len(result.get("extracted_skills", []))
            return jsonify(result)

        return jsonify({
            "extracted_skills": [],
            "predicted_role": "Unknown",
            "skill_categories": {},
            "total_skills": 0
        })
    except Exception as e:
        logging.error(f"[SKILLS] Error: {e}")
        return jsonify({"extracted_skills": [], "predicted_role": "Unknown"}), 200


# ============================================
# ATS / Resume Analysis
# ============================================

@app.route("/api/candidate/match", methods=["POST"])
@require_auth
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

        # Part 9A: Validate before returning
        result = ai_engine.validate_ats_result(result)

        user = get_current_user()
        result["candidate_name"] = user.get("user", "Candidate") if user else "Candidate"
        return jsonify(result)
    except Exception as e:
        logging.error(f"[MATCH] ERROR: {e}")
        return jsonify(ai_engine._empty_result()), 200


@app.route("/api/process_resumes", methods=["POST"])
@require_hr
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

        # 3. Combine Results + Validate each
        rankings = []
        for i, score in enumerate(batch_results):
            score = ai_engine.validate_ats_result(score)  # Part 9A guard
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
        return jsonify({"success": False, "error": "Processing failed. Please try again."}), 500


@app.route("/api/batch_match", methods=["POST"])
def batch_match():
    return jsonify({"status": "error", "message": "Deprecated. Use /api/process_resumes"}), 405


# ============================================
# AI Chat (Career Coach)
# ============================================

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

        user = get_current_user()
        user_email = user.get("email", "anonymous") if user else "anonymous"
        user_role = user.get("role", "candidate") if user else "candidate"
        logging.info(f"[CHAT] Query from {user_email}: {query[:60]}...")

        answer = chatbot_rag.get_response(
            query,
            user_role=user_role,
            user_email=user_email,
        )

        # Bulletproof: Never return empty/None answer
        if not answer or not str(answer).strip():
            logging.warning(f"[CHAT] Empty response from RAG for query: {query[:60]}")
            answer = SAFE_FALLBACK

        return jsonify({"answer": str(answer)})
    except Exception as e:
        logging.error(f"[CHAT ERROR] {e}")
        traceback.print_exc()
        return jsonify({"answer": SAFE_FALLBACK}), 200


@app.route("/api/chat_history", methods=["GET"])
def chat_history():
    try:
        user = get_current_user()
        email = user.get("email") if user else None
        if not email:
            return jsonify({"history": []})
        history = db_manager.get_chat_history(email)
        return jsonify({"history": history})
    except Exception as e:
        logging.warning(f"[CHAT_HISTORY] Error: {e}")
        return jsonify({"history": []})


# ============================================
# Admin
# ============================================

@app.route("/api/admin/clear_data", methods=["POST"])
@require_hr
@require_admin_secret
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
        return jsonify({"status": "error", "message": "Clear failed"}), 500


# ============================================
# Startup
# ============================================

if __name__ == "__main__":
    from startup import warm_services
    warm_services()

    port = int(os.environ.get("PORT", 5000))
    logging.info(f"\n{'='*50}")
    logging.info(f"FlowATS Backend v3.0.0 — Port {port}")
    logging.info(f"Path: {os.path.abspath(__file__)}")
    logging.info(f"Time: {time.strftime('%H:%M:%S')}")
    logging.info(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)