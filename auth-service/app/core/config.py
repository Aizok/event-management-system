from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://auth_user:auth_password@postgres_auth:5432/auth_db"

    # JWT
    SECRET_KEY: str = "password_password_password_password_1111"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    #App
    DEBUG: bool=True
    PROJECT_NAME: str="Auth Service"
    VERSION: str = "1.0.0"

    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file=".env"
        case_sensitive=True


settings=Settings()