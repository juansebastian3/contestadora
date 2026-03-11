"""Configuración centralizada de la aplicación."""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()


def _fix_database_url(url: str) -> str:
    """Railway y Render dan postgres:// pero SQLAlchemy necesita postgresql://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ElevenLabs
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")

    # Twilio
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    TU_CELULAR: str = os.getenv("TU_CELULAR", "")

    # Base de datos (soporta SQLite local y PostgreSQL en producción)
    DATABASE_URL: str = _fix_database_url(
        os.getenv("DATABASE_URL", "sqlite:///./filtro_llamadas.db")
    )

    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "60"))
    JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "30"))

    # App
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("PORT", os.getenv("APP_PORT", "8000")))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # URL pública del servidor (para generar URLs de audio, etc.)
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    # Google Calendar OAuth2 (para integración Pro/Premium)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Microsoft Outlook/365 Calendar OAuth2 (para integración Pro/Premium)
    OUTLOOK_CLIENT_ID: str = os.getenv("OUTLOOK_CLIENT_ID", "")
    OUTLOOK_CLIENT_SECRET: str = os.getenv("OUTLOOK_CLIENT_SECRET", "")

    # Nombre del asistente (legacy, ahora es por usuario)
    ASSISTANT_NAME: str = "Sofía"
    OWNER_NAME: str = "Juan Sebastián"


settings = Settings()
