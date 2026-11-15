import os
import sys
from typing import List

class Settings:
    PROJECT_NAME: str = "VayoCare"
    PROJECT_VERSION: str = "2.2.0"
    
    # Demo Mode: Defaults to False in production, auto-enabled during pytest
    raw_demo = os.getenv("DEMO_MODE", "")
    if raw_demo:
        DEMO_MODE: bool = raw_demo.lower() in ("true", "1", "yes")
    else:
        DEMO_MODE: bool = ("pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None)

    # Database URL: Postgres in prod (Neon/Supabase/Render), SQLite in dev/tests
    raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./vayocare.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = raw_db_url
    
    # Secrets & Cryptographic Salt
    raw_jwt = os.getenv("JWT_SECRET")
    raw_salt = os.getenv("ROLLING_PIN_SALT")

    if not DEMO_MODE and (not raw_jwt or not raw_salt):
        # Strict security in production: do not allow running with insecure defaults
        # For local dev / pytest when DEMO_MODE is false without env vars, allow dev fallback if test
        if os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("CRITICAL SECURITY: In production, JWT_SECRET and ROLLING_PIN_SALT environment variables are strictly required.")
    
    JWT_SECRET: str = raw_jwt or "vayocare_dev_jwt_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_DAYS: int = 30
    ROLLING_PIN_SALT: str = raw_salt or "vayocare_dev_rolling_pin_salt"

    # Google Gemini Models (verified real Google GenAI models)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    raw_candidates = os.getenv("GEMINI_MODELS", "gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash")
    GEMINI_CANDIDATE_MODELS: List[str] = [m.strip() for m in raw_candidates.split(",") if m.strip()]

    # Public Base URL
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Storage Configuration
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # local, s3, supabase, cloudinary
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", "uploads")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_URL", "")

    # SMTP Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")

    # Web Push (VAPID) Settings
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_CLAIMS_EMAIL: str = os.getenv("VAPID_CLAIMS_EMAIL", "support@vayocare.health")

    # Allowed CORS Origins
    _raw_cors = os.getenv("CORS_ORIGINS", "")
    if _raw_cors:
        CORS_ORIGINS: List[str] = [orig.strip() for orig in _raw_cors.split(",") if orig.strip()]
    else:
        CORS_ORIGINS: List[str] = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://0.0.0.0:8000"
        ]

settings = Settings()
