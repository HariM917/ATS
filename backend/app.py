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
from job_manager import job_bp


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
BERTVectorizer = train_model.BERTVectorizer

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024 

# Enable CORS - Support live Vercel and local dev
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "https://ats-brown.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    }
})

app.register_blueprint(job_bp)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# --- Initialize DB ---
try:
    db_manager.init_db()
except Exception as e:
    print(f"⚠️ Database Initialization Failed: {e}")

# --- Auto-Train Model on Startup ---
try:
    if not os.path.exists(train_model.MODEL_PATH):
        train_model.train()
    if hasattr(ai_engine, 'load_classifier'):
        ai_engine.load_classifier()
except Exception as e:
    print(f"⚠️ Model Initialization Failed: {e}")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "online", "message": "AI Hiring Backend is Running on Port 5000"})

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
                user = db_manager.login_candidate(email)
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
        return jsonify({"status": "error", "message": str(e)}), 500

# Other routes (upload, match, chat) follow the same logic as before...

if __name__ == "__main__":
    # UPDATED: Use port 5000 by default, or the environment's assigned port
    port = int(os.environ.get("PORT", 5001))
    print(f"✅ Flask Server starting on port {port}...", flush=True)
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)