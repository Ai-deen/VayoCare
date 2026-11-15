import os
from typing import List

class Settings:
    PROJECT_NAME: str = "VayoCare"
    PROJECT_VERSION: str = "2.1.0"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    
    # Database URL: Postgres in prod (Neon/Supabase/Render), SQLite in dev/tests
    raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./vayocare.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = raw_db_url
    
    # Demo Mode flag: Only seed demo patient Ramesh Rao if DEMO_MODE=true
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    
    # Auth & Tokens
    JWT_SECRET: str = os.getenv("JWT_SECRET", "vayocare_production_jwt_secret_key_2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_DAYS: int = 30
    ROLLING_PIN_SALT: str = os.getenv("ROLLING_PIN_SALT", "vayocare_secure_dynamic_salt")
    
    # Public Base URL (never hardcoded IP)
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Storage Configuration (S3 / Supabase / Cloudinary / Local fallback)
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
    SMTP_FROM: str = os.getenv("SMTP_FROM", "alerts@vayocare.health")
    
    # Web Push (VAPID)
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_CLAIMS_EMAIL: str = os.getenv("VAPID_CLAIMS_EMAIL", "admin@vayocare.health")
    
    # Allowed CORS Origins (from env or defaults)
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
