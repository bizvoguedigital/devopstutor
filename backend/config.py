import os
from typing import List

from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
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
    JWT_PREVIOUS_SECRET_KEYS: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ISSUER: str = "ops-mentor-ai"
    JWT_AUDIENCE: str = "ops-mentor-ai-users"

    # Auth Cookies
    ACCESS_COOKIE_NAME: str = "opsmentorai_access"
    REFRESH_COOKIE_NAME: str = "opsmentorai_refresh"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str = ""

    # Verification & Reset Tokens
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Database Settings (MongoDB)
    MONGODB_URI: str = "mongodb://localhost:27017/ops_mentor_ai"
    MONGODB_DB_NAME: str = "ops_mentor_ai"

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

    @staticmethod
    def _is_placeholder_secret(value: str) -> bool:
        candidate = (value or "").strip().lower()
        placeholders = {
            "",
            "change-me-in-production",
            "your_jwt_secret_key_here",
            "your-secret-key",
            "secret",
            "jwt_secret",
            "default",
            "changeme",
        }
        return candidate in placeholders or candidate.startswith("your_")

    @property
    def is_production(self) -> bool:
        env = (self.ENVIRONMENT or "").strip().lower()
        return (not self.DEBUG) or env in {"prod", "production", "staging"}

    @property
    def jwt_previous_secret_keys(self) -> List[str]:
        raw = (self.JWT_PREVIOUS_SECRET_KEYS or "").strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_jwt_security(self):
        secret = (self.JWT_SECRET_KEY or "").strip()
        if not secret:
            raise ValueError("JWT_SECRET_KEY must be set")

        if self._is_placeholder_secret(secret):
            if self.is_production:
                raise ValueError(
                    "JWT_SECRET_KEY uses a placeholder value. Set a strong random secret before running in production."
                )
            return self

        if self.is_production and len(secret) < 32:
            raise ValueError(
                "JWT_SECRET_KEY is too short for production. Use at least 32 characters (48+ recommended)."
            )

        for old_key in self.jwt_previous_secret_keys:
            if old_key == secret:
                raise ValueError("JWT_PREVIOUS_SECRET_KEYS must not include the current JWT_SECRET_KEY")

        return self

settings = Settings()

# Create necessary directories
os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.AVATAR_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.SESSION_RECORD_DIR, exist_ok=True)
