from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str="postgresql://event_user:event_passsword@postgres_events:5432/events_db"

    SECRET_KEY: str="password_password_password_password1111"
    ALGORITHM: str = "HS256"

    PROJECT_NAME: str="Event Service"
    VERSION: str="1.0.0"

    class Config:
        env_file=".env"


settings=Settings()