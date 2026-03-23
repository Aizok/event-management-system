from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    RABBITMQ_URL: str

    PROJECT_NAME: str="Notification Service"
    VERSION: str="1.0.0"

    SMTP_HOST: str
    SMTP_PORT: int = 587
    SENDER_EMAIL: str
    SENDER_PASSWORD: str

    SERVICE_SECRET_NOTIFICATION: str

    class Config:
        env_file=".env"
        extra = "ignore"


settings=Settings()