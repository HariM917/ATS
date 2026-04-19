import os
import time
import traceback
import sys
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import ai_engine
import db_manager
import train_model

# --- Safe Import for Job Manager ---
try:
    from job_manager import job_bp
    HAS_JOB_BP = True
except ImportError:
    print("⚠️ Warning: job_manager module not found.")
    HAS_JOB_BP = False

# --- Safe Import for Chatbot ---
try:
    import chatbot_rag
except ImportError:
    print("⚠️ Warning: chatbot_rag module not found.")
    class MockChatbot:
        def get_response(self, msg):
            return "Chat module is currently unavailable."
    chatbot_rag = MockChatbot()

# --- PICKLE FIX ---
# This resolves the "Can't get attribute 'BERTVectorizer'" error
BERTVectorizer = train_model.BERTVectorizer

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024 # 32MB Limit

# Enable CORS for live Vercel and local dev
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "https://ats-brown.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    }
})

if HAS_JOB_BP:
    app.register_blueprint(job_bp)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Initialize DB ---
try:
    db_manager.init_db()
except Exception as e:
    print(f"⚠️ Database Initialization Failed: {e}")

# --- Auto-Train Model on Startup ---
try:
    if not os.path.exists(train_model.MODEL_PATH):
        print("⚠️ Model file not found. Starting initial training...")
        train_model.train()
        print("✅ Initial training complete.")
    
    # Load the model into memory
    if hasattr(ai_engine, 'load_classifier'):
        ai_engine.load_classifier()
except Exception as e:
    print(f"⚠️ Model Initialization Failed: {e}")

# --- Helper Routes ---

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "online", "message": "AI Hiring Backend is Running!"})

# --- Auth Routes ---

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        role = data.get("role")
        mode = data.get("mode", "login")
        
        if role == "hr":
            username = data.get("username")
            password = data.get("password")
            email = data.get("email", "")
            
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
                success = db_manager.register_hr(username, password, email)
                if success:
                    session["user"] = username
                    session["role"] = "hr"
                    session["email"] = email
                    return jsonify({"status": "success", "role": "hr", "user": username, "email": email})
                return jsonify({"status": "error", "message": "Registration failed"}), 409
        
        elif role == "candidate":
            username = data.get("username")
            email = data.get("email")
            
            if mode == "login":
                user = db_manager.login_candidate(email) # Frontend passes email in username field during login
                if user:
                    session["user"] = user['username']
                    session["email"] = email
                    session["role"] = "candidate"
                    return jsonify({"status": "success", "role": "candidate", "user": user['username'], "email": email})
                return jsonify({"status": "error", "message": "Account not found. Please register."}), 401
                    
            elif mode == "register":
                success = db_manager.register_candidate(username, email)
                if success:
                    session["user"] = username
                    session["email"] = email
                    session["role"] = "candidate"
                    return jsonify({"status": "success", "role": "candidate", "user": username, "email": email})
                return jsonify({"status": "error", "message": "Email already exists"}), 409
            
        return jsonify({"status": "error", "message": "Invalid role"}), 400
    except Exception as e:
        print(f"Login Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})

# --- Profile Routes ---

@app.route("/api/profile", methods=["GET"])
def get_profile():
    email = session.get("email")
    if not email:
        return jsonify({"username": "Guest", "email": "guest@example.com", "role": "guest"})
    
    user_data = db_manager.get_user_profile(email)
    if not user_data:
        user_data = {"username": session.get("user"), "email": email, "role": session.get("role")}
        
    return jsonify(user_data)

@app.route("/api/update_profile", methods=["POST"])
def update_profile():
    if "email" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    data = request.get_json()
    email = session.get("email")
    
    if db_manager.update_user_profile(email, data):
        return jsonify({"status": "success", "message": "Profile saved!"})
    else:
        return jsonify({"status": "error", "message": "Failed to save"}), 500

# --- AI & File Routes (Fixes "Error Analyzing" issue) ---

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
        
    file = request.files["file"]
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{int(time.time())}_{file.filename}")
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        return jsonify({"status": "success", "filename": filename})
        
    return jsonify({"status": "error", "message": "Invalid file type"}), 400

@app.route("/api/candidate/match", methods=["POST"])
def candidate_match():
    try:
        data = request.get_json()
        filename = data.get("filename")
        jd_text = data.get("job_description")
        
        if not filename or not jd_text:
            return jsonify({"status": "error", "message": "Missing filename or JD"}), 400
            
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "File not found"}), 404
            
        resume_text = ai_engine.extract_text(filepath)
        result = ai_engine.compute_match_score(resume_text, jd_text)
        
        # Ensure sets are converted to lists for JSON serialization
        if 'found_skills' in result:
            result['found_skills'] = list(result['found_skills'])
            
        if "top_predicted_roles" in result:
            result["top_roles"] = result["top_predicted_roles"]
        else:
            if hasattr(ai_engine, 'predict_role'):
                try:
                    roles = ai_engine.predict_role(resume_text, top_k=3)
                    result["predicted_role"] = roles[0] if roles else "Unknown"
                    result["top_roles"] = roles
                except Exception as e:
                    print(f"Prediction fallback error: {e}")
                    result["top_roles"] = []
            else:
                result["top_roles"] = []

        result["candidate_name"] = session.get("user", "Candidate")
        return jsonify(result)
    except Exception as e:
        print(f"Match Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/batch_match", methods=["POST"])
def batch_match():
    try:
        data = request.get_json()
        candidates_list = data.get("candidates", [])
        jd_text = data.get("job_description")
        
        if not candidates_list or not jd_text:
            return jsonify({"status": "error", "message": "Missing data"}), 400
            
        ranked_results = []
        
        for cand in candidates_list:
            fname = cand.get("filename")
            if not fname: continue
            
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], fname)
            if not os.path.exists(filepath): continue

            resume_text = ai_engine.extract_text(filepath)
            score_data = ai_engine.compute_match_score(resume_text, jd_text)
            
            # Convert sets to lists
            if 'found_skills' in score_data:
                score_data['found_skills'] = list(score_data['found_skills'])
                
            if "top_predicted_roles" in score_data:
                score_data["top_roles"] = score_data["top_predicted_roles"]
            else:
                if hasattr(ai_engine, 'predict_role'):
                    try:
                        roles = ai_engine.predict_role(resume_text, top_k=3)
                        score_data["predicted_role"] = roles[0] if roles else "Unknown"
                        score_data["top_roles"] = roles
                    except Exception:
                        score_data["top_roles"] = []
                else:
                    score_data["top_roles"] = []
            
            score_data["candidate_name"] = cand.get("original_name", "Unknown")
            score_data["filename"] = fname
            ranked_results.append(score_data)
                
        ranked_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return jsonify({"ranked_candidates": ranked_results})
    except Exception as e:
        print(f"Batch Match Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        response = chatbot_rag.get_response(user_message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ Flask Server starting on port {port}...", flush=True)
    app.run(host="0.0.0.0", port=port, use_reloader=False)