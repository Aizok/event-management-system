from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    PROJECT_NAME: str="Event Service"
    VERSION: str="1.0.0"

    SERVICE_SECRET_EVENT: str
    SERVICE_SECRET_RESOURCE: str

    class Config:
        env_file=".env"
        extra = "ignore"


settings=Settings()