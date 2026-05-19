"""
Email Sender Driver - SMTP based.

Supports Gmail, custom SMTP, or any SMTP provider.
Configure via environment variables.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailSender:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.username)
        self.from_name = os.getenv("SMTP_FROM_NAME", "Gate Security System")
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

    def send(self, to_email: str, subject: str, html_body: str,
             text_body: Optional[str] = None) -> bool:
        """Send email via SMTP. Returns True if sent successfully."""
        if not self.enabled:
            print(f"  📧 [DRY RUN] To: {to_email} | Subject: {subject}")
            return False

        if not self.username or not self.password:
            print(f"  ⚠️  SMTP not configured, skipping email to {to_email}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            print(f"  ✅ Email sent to {to_email}")
            return True

        except Exception as e:
            print(f"  ❌ Email failed to {to_email}: {e}")
            return False
