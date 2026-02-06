from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://auth_user:auth_password@postgres_auth:5432/auth_db"

    # JWT
    SECRET_KEY: str = "change-me-super-secret-key-for-jwt-32-characters-minimum!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    #App
    DEBUG: bool=True
    PROJECT_NAME: str="Auth Service"
    VERSION: str = "1.0.0"

    # CORS (для фронтенда)
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file="../../.env"
        case_sensitive=True


settings=Settings()