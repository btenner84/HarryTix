from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    # Database - Railway provides DATABASE_URL, we need to convert to asyncpg format
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/harrytix"

    @field_validator("database_url", mode="before")
    @classmethod
    def convert_database_url(cls, v):
        # Railway provides postgres:// but asyncpg needs postgresql+asyncpg://
        if v and v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v and v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # CORS
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Scraping settings
    scrape_timeout: int = 30  # seconds
    scrape_rate_limit: int = 10  # requests per minute per platform

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # Handle JSON array format: ["url1", "url2"]
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated format
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
