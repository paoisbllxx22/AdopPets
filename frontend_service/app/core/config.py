import os

class Settings:
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend-service:8000")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:80")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_super_secret_key_frontend")
    ALGORITHM: str = "HS256"

settings = Settings()
