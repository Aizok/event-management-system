from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "openrouter/free"

    PROJECT_NAME: str="AI Assistant Service"
    VERSION: str="1.0.0"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    TASK_SERVICE_URL: str = "http://task-service:8004"
    SERVICE_SECRET_AI: str

    class Config:
        env_file=".env"
        extra = "ignore"


settings=Settings()