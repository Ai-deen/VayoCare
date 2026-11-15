import os
from typing import List

class Settings:
    PROJECT_NAME: str = "VayoCare"
    PROJECT_VERSION: str = "2.0.0"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "vayocare.db")
    ROLLING_PIN_SALT: str = os.getenv("ROLLING_PIN_SALT", "vayocare_secure_dynamic_salt")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # SMTP Email Configuration (Environment or Outbox Fallback)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "alerts@vayocare.health")
    
    # Allowed CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://192.168.1.44:8000",
        "http://0.0.0.0:8000"
    ]

settings = Settings()
