import os
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, session
import db_manager
from dotenv import load_dotenv

# Load the secret variables from the .env file
load_dotenv()

# Create a Flask Blueprint for all Job-related routes
job_bp = Blueprint('job_bp', __name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- EMAIL CONFIGURATION (SECURE) ---
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_application_email(candidate_email, candidate_name, job_title, company_name):
    """Sends a confirmation email to the candidate in the background."""
    print(f"⏳ [EMAIL THREAD] Preparing to send email to {candidate_email}...")
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ [EMAIL THREAD] ERROR: Email credentials missing. Please check your .env file.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = f"TalentFlow ATS <{SENDER_EMAIL}>"
        msg['To'] = candidate_email
        msg['Subject'] = f"Application Received: {job_title} at {company_name}"

        body = f"""Hi {candidate_name},

Thank you for applying for the {job_title} position at {company_name}!

We have successfully received your application and your resume. Our hiring team will review your profile to see if it's a strong match for the role.

We will be in touch with you regarding the next steps shortly.

Best Regards,
{company_name} Hiring Team
(Powered by TalentFlow)
"""
        msg.attach(MIMEText(body, 'plain'))

        # Using SMTP_SSL on Port 465 (Much more reliable and bypasses most firewalls)
        print("🔌 [EMAIL THREAD] Connecting to Google Servers via SSL (Port 465)...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ [EMAIL THREAD] SUCCESS! Application confirmation email sent to {candidate_email}")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ [EMAIL THREAD] ERROR: Google blocked the login. Please check your App Password in the .env file.")
    except Exception as e:
        print(f"❌ [EMAIL THREAD] ERROR: Failed to send confirmation email: {e}")

@job_bp.route("/api/jobs", methods=["GET", "POST"])
def manage_jobs():
    """HR route to post new jobs or fetch their own company jobs with applicants"""
    if "email" not in session or session.get("role") != "hr":
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    hr_email = session.get("email")
    
    if request.method == "POST":
        data = request.get_json()
        success = db_manager.add_job(
            hr_email,
            data.get("title"),
            data.get("description"),
            data.get("location", ""),
            data.get("job_type", "Full-time"),
            data.get("salary", "")
        )
        if success:
            return jsonify({"status": "success", "message": "Job posted successfully!"})
        return jsonify({"status": "error", "message": "Failed to post job."}), 500
        
    elif request.method == "GET":
        # Fetch HR's jobs
        jobs = db_manager.get_hr_jobs(hr_email)
        # Attach the list of applicants to each job
        for job in jobs:
            job['applications'] = db_manager.get_job_applications(job['id'])
        return jsonify({"status": "success", "jobs": jobs})

@job_bp.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
def apply_job(job_id):
    """Allows candidates to apply for a job and triggers an email"""
    print(f"\n--- 📥 NEW APPLICATION REQUEST RECEIVED FOR JOB ID: {job_id} ---")
    
    if "email" not in session or session.get("role") != "candidate":
        print("❌ DEBUG: Apply rejected. User is not logged in as candidate or session cookie is missing.")
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    # The frontend sends FormData (name, email, phone, resume)
    candidate_email = request.form.get("email")
    if not candidate_email:
        candidate_email = session.get("email")
        
    candidate_name = request.form.get("name")
    if not candidate_name:
        candidate_name = session.get("user")
        
    print(f"👤 DEBUG: Candidate recognized as Name: {candidate_name} | Email: {candidate_email}")
    
    # Save the application to the database
    is_saved = db_manager.apply_for_job(job_id, candidate_email, candidate_name)
    print(f"💾 DEBUG: Application saved to Database? -> {is_saved}")
    
    if is_saved:
        # Save the uploaded resume to the uploads folder
        if 'resume' in request.files:
            print("📄 DEBUG: Resume file successfully received in the request.")
            file = request.files['resume']
            if file and file.filename:
                from werkzeug.utils import secure_filename
                import time
                filename = secure_filename(f"app_{int(time.time())}_{file.filename}")
                upload_dir = os.path.join(BASE_DIR, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
        else:
            print("⚠️ DEBUG: No resume file was found in the request data.")

        # Fetch job details to customize the email
        import sqlite3
        conn = sqlite3.connect(os.path.join(BASE_DIR, 'hiring_system.db'))
        conn.row_factory = sqlite3.Row
        job = conn.execute('SELECT title, hr_email FROM jobs WHERE id = ?', (job_id,)).fetchone()
        conn.close()
        
        if job:
            job_title = job['title']
            # Extract Company name from HR email
            hr_email = job['hr_email']
            company_name = hr_email.split('@')[1].split('.')[0].capitalize() if '@' in hr_email else "Our Company"
            print(f"🏢 DEBUG: Job details found. Title: {job_title} | Company: {company_name}")
            print("🚀 DEBUG: Triggering background email thread now...")
            
            # Trigger the email in the background so the user doesn't have to wait!
            email_thread = threading.Thread(
                target=send_application_email, 
                args=(candidate_email, candidate_name, job_title, company_name)
            )
            email_thread.start()
        else:
            print("⚠️ DEBUG: Could not find job details in database to send email.")

        return jsonify({"status": "success", "message": "Applied successfully!"})
        
    print("❌ DEBUG: Database save failed. Did the candidate already apply?")
    return jsonify({"status": "error", "message": "Failed to apply."}), 500

@job_bp.route("/api/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    """HR route to delete their own job postings"""
    if "email" not in session or session.get("role") != "hr":
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    hr_email = session.get("email")
    if db_manager.delete_job(job_id, hr_email):
        return jsonify({"status": "success", "message": "Job deleted."})
    return jsonify({"status": "error", "message": "Failed to delete job."}), 500

@job_bp.route("/api/all_jobs", methods=["GET"])
def get_all_jobs():
    """Endpoint for Candidates to view all posted jobs (LinkedIn style feed)"""
    try:
        import sqlite3
        # Connect directly to ensure we can read all jobs from the feed
        db_path = os.path.join(BASE_DIR, 'hiring_system.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        jobs = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
        conn.close()
        
        formatted_jobs = []
        for job in jobs:
            job_dict = dict(job)
            # Extract 'Company Name' from hr_email (e.g., hr@google.com -> Google)
            email = job_dict.get('hr_email', '')
            if '@' in email:
                company = email.split('@')[1].split('.')[0].capitalize()
            else:
                company = "Company"
            
            job_dict['company_name'] = company
            formatted_jobs.append(job_dict)
            
        return jsonify({"status": "success", "jobs": formatted_jobs})
    except Exception as e:
        print(f"Error fetching all jobs: {e}")
        return jsonify({"status": "error", "message": "Failed to load job feed"}), 500