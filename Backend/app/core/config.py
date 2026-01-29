#core/config
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    MONGO_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ALGORITHM: str
    UPLOAD_DIR: str
    EMAIL_HOST: str = Field(...)
    EMAIL_PORT: int = Field(...)
    EMAIL_USER: str = Field(...)
    EMAIL_PASSWORD: str = Field(...)
    EMAIL_FROM: str = Field(...)
    AUTH_SERVICE_URL: str = "http://127.0.0.1:8001"


    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
