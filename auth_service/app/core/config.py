from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DB + JWT
    MONGO_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Frontend (para armar links de reset/verify)
    FRONTEND_BASE_URL: str = "http://localhost:8000"

    # Email (SMTP)
    EMAIL_HOST: str | None = None
    EMAIL_PORT: int | None = None
    EMAIL_USER: str | None = None
    EMAIL_PASSWORD: str | None = None
    EMAIL_FROM: str | None = None

    # Modo demo para no depender de SMTP
    DEBUG_EMAIL: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
