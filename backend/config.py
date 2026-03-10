import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    DEBUG: bool = True
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Groq Settings
    GROQ_API_KEY: str = ""  # Will be loaded from .env file
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Fast Groq model (updated)
    GROQ_TEMPERATURE: float = 0.7
    GROQ_MAX_TOKENS: int = 2048

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ISSUER: str = "devops-interview-ai"
    JWT_AUDIENCE: str = "devops-interview-ai-users"

    # Auth Cookies
    ACCESS_COOKIE_NAME: str = "devopsai_access"
    REFRESH_COOKIE_NAME: str = "devopsai_refresh"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str = ""

    # Verification & Reset Tokens
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Database Settings (MongoDB)
    MONGODB_URI: str = "mongodb://localhost:27017/devops_interview_ai"
    MONGODB_DB_NAME: str = "devops_interview_ai"

    # Speech Settings
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large

    # ElevenLabs TTS Settings
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    ELEVENLABS_STABILITY: float = 0.5
    ELEVENLABS_SIMILARITY: float = 0.75
    TTS_CACHE_ENABLED: bool = True
    TTS_CACHE_TTL_SECONDS: int = 604800
    TTS_CACHE_MAX_FILES: int = 500

    # Interview Settings
    MAX_QUESTION_COUNT: int = 10
    SESSION_TIMEOUT: int = 3600  # 1 hour in seconds

    # Storage
    AUDIO_UPLOAD_DIR: str = "./uploads/audio"
    AVATAR_UPLOAD_DIR: str = "./uploads/avatars"
    SESSION_RECORD_DIR: str = "./sessions"

    model_config = ConfigDict(
        env_file=[
            os.path.join(os.path.dirname(__file__), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        ],
        case_sensitive=True,
        protected_namespaces=(),
    )

settings = Settings()

# Create necessary directories
os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.AVATAR_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.SESSION_RECORD_DIR, exist_ok=True)
