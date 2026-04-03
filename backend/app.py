import os
import time
import traceback
import sys
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import ai_engine
import db_manager
import train_model  # Imports the separate training module
from job_manager import job_bp  # <--- IMPORT THE NEW JOB ROUTES FILE

# --- Safe Import for Chatbot ---
try:
    import chatbot_rag
except ImportError:
    print("⚠️ Warning: chatbot_rag module not found. Chat functionality will be limited.")
    class MockChatbot:
        def get_response(self, msg):
            return "Chat module is currently unavailable. Please check backend logs."
    chatbot_rag = MockChatbot()

# --- PICKLE FIX ---
# Maps the BERTVectorizer class to the current '__main__' module.
BERTVectorizer = train_model.BERTVectorizer

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024 # 32MB Limit

# Enable CORS for frontend - supports credentials for session cookies
# Browsers block origins="*" when using credentials. We explicitly list the React/Vite ports.
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",   # Standard Create React App
            "http://127.0.0.1:3000",
            "http://localhost:5173",   # Vite React App
            "http://127.0.0.1:5173"
        ]
    }
})

# Register the external routes from job_manager.py
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
    
    # Force load the model into memory in ai_engine
    if hasattr(ai_engine, 'load_classifier'):
        ai_engine.load_classifier()
except Exception as e:
    print(f"⚠️ Model Initialization Failed: {e}")

# --- Logging Middleware (Debug) ---
@app.before_request
def log_request_info():
    """Log incoming requests to help debug connection issues."""
    print(f"📥 Received {request.method} request on {request.path} from {request.remote_addr}")

# --- Global Error Handler ---
@app.errorhandler(Exception)
def handle_global_error(e):
    """Catches any internal server crashes and ensures a JSON response with CORS headers."""
    print(f"🚨 Global Error Caught: {e}")
    traceback.print_exc()
    return jsonify({"status": "error", "message": f"Server processing error: {str(e)}"}), 500

# --- Helper Routes ---
@app.route("/", methods=["GET"])
def home():
    return "<h1>✅ AI Hiring Backend is Running!</h1>"

# --- Auth Routes ---
@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        role = data.get("role")
        mode = data.get("mode", "login") # Detects if user clicked 'Login' or 'Register'
        print(f"🔑 Auth attempt: Role={role}, Mode={mode}")
        
        if role == "hr":
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")
            
            if mode == "login":
                # Hardcoded Admin (Demo)
                if username == "admin" and password == "password123":
                     session["user"] = "admin"
                     session["role"] = "hr"
                     session["email"] = "admin@company.com"
                     print("✅ Admin login successful")
                     return jsonify({"status": "success", "role": "hr", "user": "admin", "email": "admin@company.com"})

                # DB Check for HR Login
                hr_email = db_manager.verify_hr_login(username, password)
                if hr_email:
                    session["user"] = username
                    session["role"] = "hr"
                    session["email"] = hr_email
                    print(f"✅ HR login successful: {username}")
                    return jsonify({"status": "success", "role": "hr", "user": username, "email": hr_email})
                else:
                    return jsonify({"status": "error", "message": "User not found or invalid credentials."}), 401
                    
            elif mode == "register":
                if not username or not password or not email:
                    return jsonify({"status": "error", "message": "Missing fields for HR registration"}), 400
                
                success = db_manager.register_hr(username, password, email)
                if success:
                    session["user"] = username
                    session["role"] = "hr"
                    session["email"] = email
                    return jsonify({"status": "success", "role": "hr", "user": username, "email": email})
                else:
                    return jsonify({"status": "error", "message": "Username or Email already exists. Please log in."}), 409
        
        elif role == "candidate":
            username = data.get("username")
            email = data.get("email")
            
            if mode == "login":
                if not email:
                    return jsonify({"status": "error", "message": "Email is required to login"}), 400
                    
                # Uses the separated login function
                user = db_manager.login_candidate(email)
                if user:
                    session["user"] = user['username']
                    session["email"] = email
                    session["role"] = "candidate"
                    print(f"✅ Candidate login successful: {user['username']}")
                    return jsonify({"status": "success", "role": "candidate", "user": user['username'], "email": email})
                else:
                    # STRICT LOGIN: Unregistered users are blocked and told to register
                    return jsonify({"status": "error", "message": "Account not found. Please register first."}), 401
                    
            elif mode == "register":
                if not username or not email:
                    return jsonify({"status": "error", "message": "Name and Email required"}), 400
                    
                # Uses the separated register function
                success = db_manager.register_candidate(username, email)
                if success:
                    session["user"] = username
                    session["email"] = email
                    session["role"] = "candidate"
                    print(f"✅ Candidate registered & logged in: {username}")
                    return jsonify({"status": "success", "role": "candidate", "user": username, "email": email})
                else:
                    return jsonify({"status": "error", "message": "Email already registered. Please log in."}), 409
            
        return jsonify({"status": "error", "message": "Invalid role"}), 400
    except Exception as e:
        # DETAILED ERROR REPORTING
        error_msg = str(e)
        trace = traceback.format_exc()
        print(f"⚠️ Server Error in /login: {error_msg}")
        print(trace)
        return jsonify({"status": "error", "message": f"Internal Server Error: {error_msg}"}), 500

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

# --- AI & File Routes ---
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
    """Single candidate matching for Candidate Dashboard"""
    data = request.get_json()
    filename = data.get("filename")
    jd_text = data.get("job_description")
    
    if not filename or not jd_text:
        return jsonify({"status": "error", "message": "Missing filename or JD"}), 400
        
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    try:
        resume_text = ai_engine.extract_text(filepath)
        result = ai_engine.compute_match_score(resume_text, jd_text)
        
        # Explicitly ensure the role prediction logic requested is mapped correctly
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
    """Bulk matching for HR Dashboard"""
    data = request.get_json()
    candidates_list = data.get("candidates", []) # List of {filename: '...'}
    jd_text = data.get("job_description")
    
    if not candidates_list or not jd_text:
        return jsonify({"status": "error", "message": "Missing data"}), 400
        
    ranked_results = []
    
    for cand in candidates_list:
        fname = cand.get("filename")
        if not fname: continue
        
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], fname)
        try:
            resume_text = ai_engine.extract_text(filepath)
            score_data = ai_engine.compute_match_score(resume_text, jd_text)
            
            # Ensure top_roles is populated for batch results too
            if "top_predicted_roles" in score_data:
                score_data["top_roles"] = score_data["top_predicted_roles"]
            else:
                if hasattr(ai_engine, 'predict_role'):
                    try:
                        roles = ai_engine.predict_role(resume_text, top_k=3)
                        score_data["predicted_role"] = roles[0] if roles else "Unknown"
                        score_data["top_roles"] = roles
                    except Exception as e:
                        print(f"Prediction fallback error for {fname}: {e}")
                        score_data["top_roles"] = []
                else:
                    score_data["top_roles"] = []
            
            score_data["candidate_name"] = cand.get("original_name", "Unknown")
            score_data["filename"] = fname
            ranked_results.append(score_data)
        except Exception as e:
            print(f"Error processing {fname}: {e}")
            
    # Sort by final_score descending (Safely use .get to prevent KeyError if missing)
    ranked_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    return jsonify({"ranked_candidates": ranked_results})

@app.route("/api/admin/retrain", methods=["POST"])
def retrain_model():
    """Endpoint for Admin/HR to trigger model retraining"""
    if session.get("role") != "hr":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        train_model.train()
        if hasattr(ai_engine, 'classifier_model'):
             ai_engine.classifier_model = None
        
        return jsonify({"status": "success", "message": "Model retrained and saved successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        # Safe call to get_response
        if hasattr(chatbot_rag, 'get_response'):
            response = chatbot_rag.get_response(user_message)
        else:
            response = "I'm having trouble accessing my knowledge base right now. Please try again later."
            
        return jsonify({"response": response})
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"response": "An error occurred while processing your message."})

if __name__ == "__main__":
    print("✅ Flask Server starting on port 5001...", flush=True)
    # use_reloader=False prevents Flask from restarting the server (and reloading the heavy AI models) 
    # whenever the SQLite database or the uploads folder is modified.
    app.run(debug=True, host="0.0.0.0", port=5001, use_reloader=False)