from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    RABBITMQ_URL: str

    SERVICE_SECRET_RESOURCE: str

    PROJECT_NAME: str="Resource Service"
    VERSION: str="1.0.0"

    class Config:
        env_file=".env"


settings=Settings()