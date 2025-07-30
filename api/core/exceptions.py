"""
Exception handling and custom exceptions for LumiLens API.

This module provides custom exception classes and centralized exception
handling for the FastAPI application with proper HTTP status codes
and error responses.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Any, Dict
import traceback

from api.config import settings

logger = logging.getLogger(__name__)


class LumiLensException(Exception):
    """Base exception class for LumiLens API."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(LumiLensException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationException(LumiLensException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(LumiLensException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )


class ResourceNotFoundException(LumiLensException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class RateLimitException(LumiLensException):
    """Exception for rate limit errors."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class ExternalServiceException(LumiLensException):
    """Exception for external service errors (OpenAI, etc.)."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )


class VectorStoreException(LumiLensException):
    """Exception for vector store operations."""
    
    def __init__(self, message: str, operation: str = ""):
        super().__init__(
            message=f"Vector store error: {message}",
            status_code=500,
            error_code="VECTOR_STORE_ERROR",
            details={"operation": operation}
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Dict[str, Any] = None,
    request_id: str = None
) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Internal error code
        details: Additional error details
        request_id: Request ID for tracking
        
    Returns:
        Dict containing standardized error response
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    if settings.ENVIRONMENT == "development":
        error_response["error"]["timestamp"] = ""
    
    return error_response


async def lumilens_exception_handler(
    request: Request,
    exc: LumiLensException
) -> JSONResponse:
    """
    Handle LumiLens custom exceptions.
    
    Args:
        request: FastAPI request object
        exc: LumiLens exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Log error with appropriate level
    if exc.status_code >= 500:
        logger.error(
            "Internal error: %s - Status: %d - Details: %s",
            exc.message, exc.status_code, exc.details
        )
    else:
        logger.warning(
            "Client error: %s - Status: %d",
            exc.message, exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
            request_id=request_id
        )
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        "HTTP exception: %s - Status: %d",
        exc.detail, exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            error_code="HTTP_ERROR",
            request_id=request_id
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI validation exceptions.
    
    Args:
        request: FastAPI request object
        exc: Validation exception instance
        
    Returns:
        JSONResponse with validation error details
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning("Validation error: %s", exc.errors())
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            status_code=422,
            message="Validation error",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": exc.errors()},
            request_id=request_id
        )
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSONResponse with generic error message
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Log full traceback for debugging
    logger.error(
        "Unhandled exception: %s",
        exc,
        exc_info=True
    )
    
    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        message = "An internal error occurred"
        details = None
    else:
        message = str(exc)
        details = {"traceback": traceback.format_exc()}
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            status_code=500,
            message=message,
            error_code="INTERNAL_ERROR",
            details=details,
            request_id=request_id
        )
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(LumiLensException, lumilens_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("🛡️  Exception handlers configured")
