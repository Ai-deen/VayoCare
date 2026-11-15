import os

class Settings:
    PROJECT_NAME: str = "VayoCare"
    PROJECT_VERSION: str = "1.0.0"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6ImPkTvFeS1qwMlZqQzWplSCKY3UxXxxjxbfUGvWXSt2A")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "vayocare.db")
    ROLLING_PIN_SALT: str = os.getenv("ROLLING_PIN_SALT", "vayocare_secret_salt_2026")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
