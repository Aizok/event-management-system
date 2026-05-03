from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SERVICE_SECRET_NOTIFICATION: str
    SERVICE_SECRET_TASK: str
    SERVICE_SECRET_USER: str
    SERVICE_SECRET_EVENT: str
    SERVICE_SECRET_RESOURCE: str
    SERVICE_SECRET_AI: str
    DEBUG: bool=True
    PROJECT_NAME: str="Auth Service"
    VERSION: str = "1.0.0"

    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file=".env"
        case_sensitive=True


settings=Settings()