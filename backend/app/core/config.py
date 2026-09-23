from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MEMORA AI Cognitive Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"

    # Security (override via environment in production)
    SECRET_KEY: str = "dev_only_change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Supabase (anon/publishable key for user-scoped ops)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    # Service-role key (backend only, NEVER expose to frontend) for admin ops
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    # Optional JWT secret for offline verification (Supabase legacy JWT secret)
    SUPABASE_JWT_SECRET: Optional[str] = None

    # CORS: comma-separated origins, "*" for dev
    CORS_ORIGINS: str = "*"

    # Sarvam AI (Indian regional STT & TTS)
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_STT_URL: str = "https://api.sarvam.ai/speech-to-text"
    SARVAM_TTS_URL: str = "https://api.sarvam.ai/text-to-speech"
    
    # Environment
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), env_file_encoding="utf-8", extra="ignore")

settings = Settings()
