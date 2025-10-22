
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database URL with type validation
    MONGO_URI: str = Field(..., description="MongoDB connection URI")
    DB_NAME: str = Field(default="assessment")
    COLLECTION_NAME: str = Field(default="new_job_with_questions")
    OPENAI_API_KEY: str = Field(..., description="OpenAI's API key")
    # Debug mode
    DEBUG: bool = Field(default=False)
    # Example for future expansion
    APP_NAME: str = Field(default="HSE Assessment API")

    class Config:
        # Automatically read from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton settings object
settings = Settings()
