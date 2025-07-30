"""
Authentication middleware for LumiLens API.

Provides basic authentication and request logging for API access.
For production use, implement proper JWT or OAuth2 authentication.
"""

import logging
import uuid
from typing import Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from api.config import get_settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for API requests.
    
    Currently implements basic API key authentication and request ID generation.
    Can be extended for JWT, OAuth2, or other authentication methods.
    """
    
    def __init__(self, app):
        """Initialize authentication middleware."""
        super().__init__(app)
        self.settings = get_settings()
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/health",
            "/api",
            "/api/v1/health",
            "/api/v1/health/simple",
            "/api/v1/health/ready",
            "/api/v1/health/live",
            "/api/docs",
            "/api/redoc",
            "/openapi.json"
        }
        
        logger.info("🔐 Authentication middleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with authentication check.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: HTTP response
            
        Raises:
            HTTPException: If authentication fails
        """
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Skip authentication for public endpoints
        if request.url.path in self.public_endpoints:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Skip authentication in development mode
        if self.settings.ENVIRONMENT == "development":
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Check authentication
        if not self._authenticate_request(request):
            logger.warning(
                "🚫 Authentication failed for %s %s (Request ID: %s)",
                request.method,
                request.url.path,
                request_id
            )
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Process authenticated request
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _authenticate_request(self, request: Request) -> bool:
        """
        Authenticate incoming request.
        
        Args:
            request: HTTP request to authenticate
            
        Returns:
            bool: True if authenticated, False otherwise
        """
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return self._validate_api_key(api_key)
        
        # Check for Bearer token
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]  # Remove "Bearer " prefix
            return self._validate_bearer_token(token)
        
        # No authentication provided
        return False
    
    def _validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # TODO: Implement proper API key validation
        # For now, accept any non-empty API key in non-production environments
        if self.settings.ENVIRONMENT != "production":
            return len(api_key) > 0
        
        # In production, implement proper API key validation
        # This could involve database lookup, hash comparison, etc.
        return False
    
    def _validate_bearer_token(self, token: str) -> bool:
        """
        Validate Bearer token (JWT, etc.).
        
        Args:
            token: Bearer token to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # TODO: Implement proper JWT validation
        # This would involve:
        # 1. Decoding JWT token
        # 2. Validating signature
        # 3. Checking expiration
        # 4. Validating claims
        
        # For now, accept any non-empty token in non-production environments
        if self.settings.ENVIRONMENT != "production":
            return len(token) > 0
        
        return False
