"""
FastAPI backend for LumiLens AI - Legal Document Analysis Platform
Main application entry point with routing and middleware configuration.

This module provides the core FastAPI application setup with:
- CORS middleware for React frontend integration
- Authentication middleware
- Rate limiting
- Health checks
- API routing
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from api.config import settings
from api.routers import chat, documents, health, analysis
from api.middleware.rate_limit import RateLimitMiddleware
from api.middleware.auth import AuthMiddleware
from api.core.exceptions import setup_exception_handlers
from api.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    
    Handles:
    - Vector store initialization
    - Database connections
    - Resource cleanup
    """
    logger.info("🚀 Starting LumiLens API server...")
    
    # Startup: Initialize services
    try:
        # Initialize vector store and embeddings
        from api.services.vector_service import VectorService
        vector_service = VectorService()
        await vector_service.initialize()
        
        # Store in app state for access across requests
        application.state.vector_service = vector_service
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error("❌ Failed to initialize services: %s", str(e))
        raise
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("🛑 Shutting down LumiLens API server...")
    if hasattr(application.state, 'vector_service'):
        await application.state.vector_service.cleanup()

# Create FastAPI app with custom lifespan
app = FastAPI(
    title="LumiLens API",
    description="AI-powered legal document analysis and chat assistant",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Authentication middleware
app.add_middleware(AuthMiddleware)

# Exception handlers
setup_exception_handlers(app)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing information."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "📥 %s %s - Client: %s",
        request.method,
        request.url.path,
        request.client.host if request.client else 'unknown'
    )
    
    response = await call_next(request)
    
    # Log response with timing
    process_time = time.time() - start_time
    logger.info(
        "📤 %s %s - Status: %d - Time: %.3fs",
        request.method,
        request.url.path,
        response.status_code,
        process_time
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])

@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        dict: API metadata and status
    """
    return {
        "name": "LumiLens API",
        "version": "1.0.0",
        "description": "AI-powered legal document analysis platform",
        "docs": "/api/docs" if settings.ENVIRONMENT == "development" else None,
        "status": "operational"
    }

@app.get("/api")
async def api_info():
    """API information endpoint."""
    return await root()

# Health check for deployment platforms
@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns:
        dict: Health status and system information
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
