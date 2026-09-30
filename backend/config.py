"""
FinSight – Configuration
Loads settings from environment variables with sensible defaults for local dev.
"""
import os
from dotenv import load_dotenv

# Load .env from project root or backend dir

_backend_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_backend_dir)
load_dotenv(os.path.join(_project_root, ".env"))
load_dotenv(os.path.join(_backend_dir, ".env"))


class Config:
    # ── Flask ────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # ── Database (PostgreSQL) ────────────────────────────────
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "finsight_ai")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET = os.getenv("JWT_SECRET", "jwt-dev-secret-change-me")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

    # ── Email / SMTP (for OTP) ───────────────────────────────
    SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "noreply@finsight.ai")
    EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "fake")  # "fake" | "smtp"

    # ── Financial Data API ───────────────────────────────────
    DATA_PROVIDER = os.getenv("DATA_PROVIDER", "mock")  # "mock" | "alphavantage" | ...
    DATA_API_KEY = os.getenv("DATA_API_KEY", "")
    DATA_API_BASE_URL = os.getenv("DATA_API_BASE_URL", "")
    DATA_REFRESH_INTERVAL = int(os.getenv("DATA_REFRESH_INTERVAL", "60"))

    # ── LLM / Chatbot ───────────────────────────────────────
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "stub")  # "stub" | "gemini" | "openai" | "anthropic"
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
    LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1")

    # ── Gemini (Google AI Studio – free tier) ────────────────
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ── OTP Settings ─────────────────────────────────────────
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))

    # ── Frontend serving ─────────────────────────────────────
    FRONTEND_DIR = os.getenv(
        "FRONTEND_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend"),
    )
