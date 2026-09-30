"""
Email Service - Sends OTP emails.
Uses a 'fake' adapter by default (prints to console) for local development.
Switch to 'smtp' via EMAIL_BACKEND env var for real email delivery.
"""
import smtplib
from email.mime.text import MIMEText
from config import Config


class FakeEmailAdapter:
    """Prints OTP to console instead of sending a real email."""

    def send(self, to: str, subject: str, body: str):
        print("\n" + "=" * 60)
        print("[DEV EMAIL] To: " + to)
        print("   Subject : " + subject)
        print("=" * 60 + "\n")
        return True


class SmtpEmailAdapter:
    """Sends email via SMTP. Always falls back if delivery fails."""

    def send(self, to: str, subject: str, body: str):
        print("\n" + "=" * 60)
        print("[EMAIL] To: " + to + "  |  Subject: " + subject)
        print("=" * 60 + "\n")

        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = Config.SMTP_FROM
        msg["To"] = to
        try:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                if Config.SMTP_USER:
                    server.starttls()
                    server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.send_message(msg)
            print("[EmailService] OK - Email sent to " + to)
            return True
        except Exception as e:
            print("[EmailService] SMTP failed (" + str(e) + ") - use console OTP above")
            return False


def _get_adapter():
    if Config.EMAIL_BACKEND == "smtp":
        return SmtpEmailAdapter()
    return FakeEmailAdapter()


def send_otp_email(to: str, otp_code: str) -> bool:
    """Send an OTP verification email."""
    subject = "FinSight - Verify Your Email"
    body = """
    <h2>Welcome to FinSight!</h2>
    <p>Your verification code is:</p>
    <h1 style="color: #FF9F1C; letter-spacing: 4px;">""" + otp_code + """</h1>
    <p>This code expires in """ + str(Config.OTP_EXPIRY_MINUTES) + """ minutes.</p>
    <p style="color: #888;">If you didn't sign up, please ignore this email.</p>
    """
    print("\n" + "=" * 60)
    print("[OTP] SIGNUP VERIFICATION CODE: " + otp_code + "  <<< USE THIS")
    print("      For: " + to)
    print("=" * 60 + "\n")
    adapter = _get_adapter()
    return adapter.send(to, subject, body)


def send_login_otp(to: str, otp_code: str, method: str = "email") -> bool:
    """Send/display a login OTP."""
    subject = "FinSight - Login OTP"
    body = """
    <h2>Login to FinSight</h2>
    <p>Your one-time login code is:</p>
    <h1 style="color: #2EC4B6; letter-spacing: 4px;">""" + otp_code + """</h1>
    <p>This code expires in """ + str(Config.OTP_EXPIRY_MINUTES) + """ minutes.</p>
    <p style="color: #888;">If you didn't request this, please ignore.</p>
    """
    print("\n" + "=" * 60)
    print("[OTP] LOGIN CODE: " + otp_code + "  <<< USE THIS")
    print("      For: " + to)
    print("=" * 60 + "\n")
    adapter = _get_adapter()
    return adapter.send(to, subject, body)


def send_password_reset_otp(to: str, otp_code: str) -> bool:
    """Send a password reset OTP."""
    subject = "FinSight - Password Reset"
    body = """
    <h2>Reset Your Password</h2>
    <p>Your password reset code is:</p>
    <h1 style="color: #E63946; letter-spacing: 4px;">""" + otp_code + """</h1>
    <p>This code expires in """ + str(Config.OTP_EXPIRY_MINUTES) + """ minutes.</p>
    <p style="color: #888;">If you didn't request this, please ignore.</p>
    """
    print("\n" + "=" * 60)
    print("[OTP] PASSWORD RESET CODE: " + otp_code + "  <<< USE THIS")
    print("      For: " + to)
    print("=" * 60 + "\n")
    adapter = _get_adapter()
    return adapter.send(to, subject, body)
