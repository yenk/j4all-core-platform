"""
Configuration settings for LumiLens API.

This module provides centralized configuration management using Pydantic settings
with support for environment variables and different deployment environments.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden by environment variables with the same name.
    For example, DATABASE_URL can be set via the DATABASE_URL environment variable.
    """
    
    # Application
    APP_NAME: str = "LumiLens API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="Deployment environment")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    
    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=1, description="Number of worker processes")
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token generation"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:4000",
            "https://lumilens.ai",
            "https://*.vercel.app"
        ],
        description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.vercel.app", "lumilens.ai"],
        description="Allowed hosts for TrustedHost middleware"
    )
    
    # OpenAI
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for embeddings and chat"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model for chat completion"
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-large",
        description="OpenAI model for text embeddings"
    )
    
    # Vector Database
    CHROMA_PATH: str = Field(
        default="./chroma_db",
        description="Path to ChromaDB database"
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default="contract_disputes_collection",
        description="ChromaDB collection name"
    )
    
    # Document Processing
    DATA_PATH: str = Field(
        default="./data",
        description="Path to document data directory"
    )
    CHUNK_SIZE: int = Field(
        default=300,
        description="Text chunk size for document splitting"
    )
    CHUNK_OVERLAP: int = Field(
        default=100,
        description="Text chunk overlap for document splitting"
    )
    MAX_FILE_SIZE: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="Maximum file upload size in bytes"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Rate limit requests per window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=3600,  # 1 hour
        description="Rate limit window in seconds"
    )
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    
    # Database (for future use with PostgreSQL/SQLite)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v):
        """Validate OpenAI API key is provided."""
        if not v:
            # Try to get from environment
            env_key = os.getenv("OPENAI_API_KEY")
            if env_key:
                return env_key
            raise ValueError("OPENAI_API_KEY must be provided")
        return v
    
    @validator("CHROMA_PATH", "DATA_PATH")
    def validate_paths(cls, v):
        """Ensure paths exist or can be created."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function to get settings instance.
    
    Returns:
        Settings: Application settings
    """
    return settings
