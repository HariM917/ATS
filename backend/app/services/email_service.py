"""
TalentFlow AI — Email Delivery Service & Provider Abstraction
Supports Gmail SMTP, SendGrid/Resend (future), and Mock Provider for local/testing.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from typing import Optional, List
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        pass


class GmailProvider(EmailProvider):
    def __init__(self, sender_email: str, sender_password: str, smtp_host: str = "smtp.gmail.com", smtp_port: int = 465):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        if not self.sender_email or not self.sender_password:
            logger.warning("[EMAIL] Gmail SMTP credentials not configured. Skipping email dispatch.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"TalentFlow AI <{self.sender_email}>"
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())

            logger.info(f"[EMAIL] Successfully sent email to {to_email} (Subject: '{subject}')")
            return True
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send email to {to_email}: {e}")
            return False


class MockEmailProvider(EmailProvider):
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        logger.info(f"[MOCK_EMAIL] Dispatched to={to_email} subject='{subject}'")
        return True


class EmailService:
    def __init__(self, provider: Optional[EmailProvider] = None):
        if provider:
            self.provider = provider
        elif settings.email.provider == "smtp" and settings.email.sender_email and settings.email.sender_password:
            self.provider = GmailProvider(
                sender_email=settings.email.sender_email,
                sender_password=settings.email.sender_password,
                smtp_host=settings.email.smtp_host,
                smtp_port=settings.email.smtp_port
            )
        else:
            self.provider = MockEmailProvider()

    def send_application_received(self, candidate_email: str, candidate_name: str, job_title: str) -> bool:
        subject = f"Application Received: {job_title} at TalentFlow"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #4f46e5;">Application Confirmation</h2>
            <p>Dear {candidate_name},</p>
            <p>Thank you for applying for the position of <strong>{job_title}</strong>. Our AI-assisted hiring team has received your application and will review your profile shortly.</p>
            <p style="margin-top: 20px;">Best regards,<br><strong>TalentFlow AI Recruiting Team</strong></p>
        </div>
        """
        return self.provider.send_email(candidate_email, subject, html)

    def send_status_update(self, candidate_email: str, candidate_name: str, job_title: str, new_stage: str) -> bool:
        subject = f"Update on your application for {job_title}"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #4f46e5;">Application Status Update</h2>
            <p>Dear {candidate_name},</p>
            <p>Your application for <strong>{job_title}</strong> has moved to the next stage: <strong style="color: #059669; text-transform: uppercase;">{new_stage}</strong>.</p>
            <p>Log in to your candidate dashboard to view next steps or interview schedules.</p>
            <p style="margin-top: 20px;">Best regards,<br><strong>TalentFlow AI Team</strong></p>
        </div>
        """
        return self.provider.send_email(candidate_email, subject, html)


email_service = EmailService()
