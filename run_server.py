"""
Startup script for LumiLens FastAPI server.

This script initializes the server with proper configuration,
logging, and error handling for both development and production.
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.config import settings
from api.core.logging import setup_logging


def main():
    """
    Main entry point for the FastAPI server.
    
    Configures logging, validates environment, and starts the server
    with appropriate settings for the deployment environment.
    """
    # Setup logging
    log_file = None
    if settings.ENVIRONMENT == "production":
        log_file = "logs/lumilens_api.log"
    
    setup_logging(log_file=log_file)
    logger = logging.getLogger(__name__)
    
    # Log startup information
    logger.info("🚀 Starting LumiLens API Server")
    logger.info("📊 Environment: %s", settings.ENVIRONMENT)
    logger.info("🐍 Python version: %s", sys.version.split()[0])
    logger.info("📁 Project root: %s", project_root)
    
    # Validate critical configuration
    try:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Ensure required directories exist
        Path(settings.DATA_PATH).mkdir(parents=True, exist_ok=True)
        Path(settings.CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Configuration validation successful")
        
    except Exception as e:
        logger.error("❌ Configuration validation failed: %s", str(e))
        sys.exit(1)
    
    # Configure uvicorn based on environment
    if settings.ENVIRONMENT == "development":
        # Development configuration
        uvicorn.run(
            "api.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            log_level="info",
            access_log=True,
            workers=1
        )
    else:
        # Production configuration
        uvicorn.run(
            "api.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            log_level="warning",
            access_log=False,
            workers=settings.WORKERS
        )


if __name__ == "__main__":
    main()
