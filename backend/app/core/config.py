"""
Configuration Module for PolicyPilot.
Loads settings from environment variables with safe defaults.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "PolicyPilot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # PostgreSQL Database Config
    DB_USER: str = Field(default="postgres", env="POSTGRES_USER")
    DB_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    DB_HOST: str = Field(default="127.0.0.1", env="POSTGRES_HOST")
    DB_PORT: int = Field(default=5433, env="POSTGRES_PORT")
    DB_NAME: str = Field(default="policypilot", env="POSTGRES_DB")

    # Optional direct database URL override
    DATABASE_URL: str | None = Field(default=None, env="DATABASE_URL")

    # Storage paths
    STORAGE_DIR: str = str(BASE_DIR / "storage" / "pdfs")
    DEMO_MODE: bool = False
    SEED_POLICIES: bool = False

    # AI & Model Providers
    OPENAI_API_KEY: str | None = Field(default=None, env="OPENAI_API_KEY")
    GEMINI_API_KEY: str | None = Field(default=None, env="GEMINI_API_KEY")
    GROQ_API_KEY: str | None = Field(default=None, env="GROQ_API_KEY")
    
    # Provider preferences: "openai", "gemini", "groq", "local", or "mock"
    LLM_PROVIDER: str = Field(default="auto", env="LLM_PROVIDER")
    EMBEDDING_PROVIDER: str = Field(default="auto", env="EMBEDDING_PROVIDER")
    EMBEDDING_DIMENSION: int = 384  # 384 for all-MiniLM-L6-v2 / local mini dense vector

    # Chunking Configuration
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

    # RRF (Reciprocal Rank Fusion) Constant
    RRF_K: int = 60

    model_config = {
        "env_file": (str(BASE_DIR / ".env"), str(BASE_DIR / "backend" / ".env")),
        "extra": "ignore"
    }

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)

