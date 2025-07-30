"""
Vercel serverless entry point for LumiLens FastAPI backend.

This module provides the FastAPI app instance for Vercel's serverless
function deployment. Unlike run_server.py which starts a full server,
this exports the app instance for Vercel to handle.

Usage:
- Local development: python run_server.py
- Vercel deployment: Uses this api/index.py automatically
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the configured FastAPI application
from api.main import app

# Export for Vercel serverless deployment
__all__ = ["app"]

# Vercel will automatically use this app instance
# No uvicorn.run() needed - Vercel handles the server infrastructure
