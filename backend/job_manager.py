"""
FlowATS Job Manager — Production v3.0
JWT-authenticated job routes, application management, email notifications.
"""
import os
import threading
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import Blueprint, request, jsonify
import db_manager
from auth_utils import get_current_user, require_role, require_hr
from dotenv import load_dotenv

load_dotenv()

# Create a Flask Blueprint for all Job-related routes
job_bp = Blueprint('job_bp', __name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- EMAIL CONFIGURATION (SECURE) ---
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_status_email(to_email, candidate_name, job_title, status):
    """Sends automated shortlisted or rejection emails."""
    if not SENDER_EMAIL or not SENDER_PASSWORD: return

    subject = f"Update on your application for {job_title}"
    company_name = "FlowATS"
    
    if status == 'Shortlisted':
        body = f"Hi {candidate_name},\n\nGreat news! Your profile is a strong match for the {job_title} role. We've shortlisted your application and will be in touch for an interview soon.\n\nBest,\n{company_name} Team"
    else:
        body = f"Hi {candidate_name},\n\nThank you for your interest in the {job_title} role. After reviewing your profile, we've decided to move forward with other candidates at this time.\n\nWe wish you the best in your search.\n\nBest,\n{company_name} Team"

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logging.warning(f"[EMAIL] Status email error: {e}")

def send_ai_application_email(candidate_email, candidate_name, job_title, hr_email, analysis_result, resume_path):
    """Sends AI-powered HTML notification emails to both candidate and HR."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logging.warning("[EMAIL] Credentials missing — skipping notification")
        return

    company_name = hr_email.split('@')[1].split('.')[0].capitalize() if '@' in hr_email else "Our Company"
    score = analysis_result.get('final_score', 0)
    score_pct = f"{score * 100:.1f}%"
    score_color = "#10b981" if score > 0.7 else "#f59e0b" if score > 0.4 else "#ef4444"
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # 1. EMAIL TO CANDIDATE
        msg_cand = MIMEMultipart()
        msg_cand['From'] = f"FlowATS <{SENDER_EMAIL}>"
        msg_cand['To'] = candidate_email
        msg_cand['Subject'] = f"Application Received: {job_title} at {company_name}"
        
        cand_html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; color: #374151;">
            <h2 style="color: #4f46e5; margin-bottom: 16px;">Application Received</h2>
            <p>Hi <b>{candidate_name}</b>,</p>
            <p>Thank you for applying for the <b>{job_title}</b> position at <b>{company_name}</b>.</p>
            <div style="background-color: #f9fafb; padding: 16px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #6b7280; font-weight: bold; text-transform: uppercase;">AI Match Score</p>
                <p style="margin: 4px 0 0 0; font-size: 32px; font-weight: 800; color: {score_color};">{score_pct}</p>
            </div>
            <p>Our hiring team will review your profile and get back to you soon.</p>
            <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
            <p style="font-size: 12px; color: #9ca3af; text-align: center;">Powered by FlowATS AI Hiring Intelligence</p>
        </div>
        """
        msg_cand.attach(MIMEText(cand_html, 'html'))
        server.send_message(msg_cand)

        # 2. EMAIL TO HR
        msg_hr = MIMEMultipart()
        msg_hr['From'] = f"FlowATS AI <{SENDER_EMAIL}>"
        msg_hr['To'] = hr_email
        msg_hr['Subject'] = f"NEW APPLICANT: {candidate_name} for {job_title} [{score_pct}]"

        skills_list = "".join([f'<span style="display:inline-block; background:#eef2ff; color:#4f46e5; padding:4px 8px; border-radius:4px; font-size:12px; margin:2px;">{s}</span>' for s in analysis_result.get('all_skills', [])[:15]])
        
        hr_html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; color: #374151;">
            <h2 style="color: #4f46e5; margin: 0;">New Applicant Alert</h2>
            <div style="margin: 20px 0;">
                <p style="margin: 0; font-size: 12px; text-transform: uppercase; color: #9ca3af;">Candidate</p>
                <p style="margin: 4px 0; font-size: 18px; font-weight: bold;">{candidate_name}</p>
                <p style="margin: 0; color: #6b7280;">{candidate_email}</p>
            </div>
            <div style="margin-bottom: 24px;">
                <p style="margin: 0; font-size: 12px; text-transform: uppercase; color: #9ca3af;">AI Insights</p>
                <p style="margin: 8px 0; font-size: 14px;"><b>Score:</b> <span style="color: {score_color}; font-weight: bold;">{score_pct}</span></p>
                <p style="margin: 8px 0; font-size: 14px;"><b>Predicted Role:</b> {analysis_result.get('predicted_role', 'N/A')}</p>
                <p style="margin: 8px 0; font-size: 14px;"><b>Summary:</b> {analysis_result.get('summary_reasoning', 'N/A')}</p>
            </div>
            <div style="margin-bottom: 24px;">
                <p style="margin: 0 0 8px 0; font-size: 12px; text-transform: uppercase; color: #9ca3af;">Skills Detected</p>
                <div>{skills_list}</div>
            </div>
            <p style="font-size: 14px; background: #fffbeb; border: 1px solid #fef3c7; color: #92400e; padding: 12px; border-radius: 8px;">
                The candidate's resume is attached to this email.
            </p>
        </div>
        """
        msg_hr.attach(MIMEText(hr_html, 'html'))

        # Attach Resume
        if os.path.exists(resume_path):
            with open(resume_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(resume_path)}")
            msg_hr.attach(part)

        server.send_message(msg_hr)
        server.quit()
        logging.info(f"[EMAIL] Notifications sent for {candidate_name}")
        
    except Exception as e:
        logging.error(f"[EMAIL] Failed: {e}")


# ============================================
# Routes
# ============================================

@job_bp.route("/test", methods=["GET"])
def test_backend():
    return jsonify({"status": "success", "message": "FlowATS Backend is ALIVE", "port": 5000})


@job_bp.route("/jobs", methods=["GET", "POST"])
def manage_jobs():
    """HR route to post new jobs or fetch their own company jobs with applicants"""
    try:
        # JWT Auth
        user = get_current_user()
        if not user or user.get("role") not in ("hr", "admin"):
            return jsonify({"status": "error", "message": "HR authentication required"}), 401

        hr_email = user["email"]
            
        if request.method == "POST":
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "Missing request data"}), 400
                
            title = data.get("job_title") or data.get("title") or "Untitled Role"
            
            success = db_manager.create_job(
                hr_email,
                data.get("company_name", "Unknown Company"),
                data.get("branch", "Main Branch"),
                title,
                data.get("description", ""),
                data.get("required_skills", ""),
                data.get("experience_required", 0),
                data.get("location", "Remote"),
                data.get("job_type", "Full-time"),
                data.get("salary", "Competitive")
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "status": "success",
                    "message": "Job posted successfully"
                }), 201
            return jsonify({"success": False, "message": "Database persistence failure"}), 500
            
        elif request.method == "GET":
            jobs = db_manager.get_jobs_by_hr(hr_email)
            jobs_list = []
            for job in jobs:
                job_dict = dict(job)
                job_dict['applications'] = [dict(app) for app in db_manager.get_applications_for_job(job['id'])]
                jobs_list.append(job_dict)
            return jsonify({"status": "success", "jobs": jobs_list})
            
    except Exception as e:
        logging.error(f"[JOB ROUTE] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Server error"}), 500


@job_bp.route("/jobs/<int:job_id>/apply", methods=["POST"])
def apply_job(job_id):
    """Allows candidates to apply for a job with validation and AI analysis"""
    try:
        # JWT Auth — candidates only
        user = get_current_user()
        if not user or user.get("role") != "candidate":
            logging.warning(f"[AUTH] Unauthorized apply attempt: {user}")
            return jsonify({"status": "error", "message": "Candidate authentication required"}), 401

        candidate_email = user["email"]
        candidate_name = user.get("user", candidate_email)

        if 'resume' not in request.files:
            return jsonify({"status": "error", "message": "Resume file required"}), 400
            
        file = request.files['resume']
        if not file or not file.filename:
            return jsonify({"status": "error", "message": "Invalid resume file"}), 400

        # 1. Save Resume Securely
        from werkzeug.utils import secure_filename
        import time
        import ai_engine
        
        filename = secure_filename(f"app_{int(time.time())}_{file.filename}")
        upload_dir = os.path.join(BASE_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        resume_path = os.path.join(upload_dir, filename)
        file.save(resume_path)
        logging.info(f"[APPLY] Resume saved: {filename}")
        
        # 2. Get job details
        job = db_manager.get_job_by_id(job_id)
        
        if not job:
            return jsonify({"status": "error", "message": "Job not found"}), 404
            
        # 3. Run AI Analysis
        resume_text = ai_engine.extract_text(resume_path)

        full_jd_context = f"{job['description']}\nREQUIRED SKILLS: {job['required_skills']}"
        analysis_result = ai_engine.compute_match_score(resume_text, full_jd_context)

        # Part 9A: Validate result
        analysis_result = ai_engine.validate_ats_result(analysis_result)
        score = analysis_result.get("final_score", 0.0)

        # 4. Automation thresholds
        automation_status = None
        if score >= 0.75:
            automation_status = "Shortlisted"
        elif score < 0.35:
            automation_status = "Rejected"
        initial_status = automation_status or "Pending"

        app_id = db_manager.apply_for_job(
            job_id, candidate_email, candidate_name, resume_path, score, status=initial_status
        )

        # 5. Background Notification
        job_title = job['title']
        hr_email = job['hr_email']

        def run_notifications():
            try:
                send_ai_application_email(candidate_email, candidate_name, job_title, hr_email, analysis_result, resume_path)
                if automation_status:
                    send_status_email(candidate_email, candidate_name, job_title, automation_status)
            except Exception as e:
                logging.error(f"[NOTIFY] Error: {e}")

        threading.Thread(target=run_notifications, daemon=True).start()

        return jsonify({
            "status": "success",
            "message": "Application successful",
            "analysis": analysis_result,
            "application_status": initial_status,
            "application_id": app_id,
        })

    except Exception as e:
        logging.error(f"[APPLY] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Application failed. Please try again."}), 500


@job_bp.route("/jobs/<int:job_id>/applications", methods=["GET"])
def list_applications(job_id):
    """HR route to see all candidates for a specific job, sorted by score"""
    user = get_current_user()
    if not user or user.get("role") not in ("hr", "admin"):
        return jsonify({"status": "error", "message": "HR authentication required"}), 401
    
    apps = [dict(app) for app in db_manager.get_applications_for_job(job_id)]
    return jsonify({"status": "success", "applications": apps})


@job_bp.route("/applications/<int:app_id>/status", methods=["POST"])
def change_status(app_id):
    """HR route to accept/reject/hold an application"""
    user = get_current_user()
    if not user or user.get("role") not in ("hr", "admin"):
        return jsonify({"status": "error", "message": "HR authentication required"}), 401
    
    data = request.json
    new_status = data.get("status")
    
    if db_manager.update_application_status(app_id, new_status):
        return jsonify({"status": "success", "message": f"Status updated to {new_status}"})
    
    return jsonify({"status": "error", "message": "Failed to update status"}), 500


@job_bp.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    """HR route to delete their own job postings"""
    user = get_current_user()
    if not user or user.get("role") not in ("hr", "admin"):
        return jsonify({"status": "error", "message": "HR authentication required"}), 401
    
    if db_manager.delete_job(job_id, user["email"]):
        return jsonify({"status": "success", "message": "Job deleted."})
    return jsonify({"status": "error", "message": "Failed to delete job."}), 500


@job_bp.route("/all_jobs", methods=["GET"])
def get_all_jobs():
    """Endpoint for Candidates to view all posted jobs"""
    try:
        jobs = db_manager.get_all_jobs()
        
        formatted_jobs = []
        for job in jobs:
            job_dict = dict(job)
            db_company = job_dict.get('company_name')
            if not db_company or db_company == "Company":
                email = job_dict.get('hr_email', '')
                if '@' in email:
                    company = email.split('@')[1].split('.')[0].capitalize()
                else:
                    company = "FlowATS Partner"
                job_dict['company_name'] = company
            formatted_jobs.append(job_dict)
            
        return jsonify({"status": "success", "jobs": formatted_jobs})
    except Exception as e:
        logging.error(f"[ALL_JOBS] Error: {e}")
        return jsonify({"status": "error", "message": "Failed to load job feed"}), 500