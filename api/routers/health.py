"""
Health check router for LumiLens API.

Provides endpoints for monitoring application health, system status,
and service availability for load balancers and monitoring systems.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import time
import psutil
import os
from pathlib import Path

from api.config import Settings, get_settings

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: str
    environment: str
    uptime: float
    checks: Dict[str, Any]


class SystemInfo(BaseModel):
    """System information response model."""
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    python_version: str
    process_id: int


# Store startup time for uptime calculation
_startup_time = time.time()


@router.get("/health", response_model=HealthStatus)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Comprehensive health check endpoint.
    
    Returns detailed information about the application's health status,
    including external service connectivity and system resources.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        HealthStatus: Detailed health information
        
    Raises:
        HTTPException: If critical services are unavailable
    """
    current_time = time.time()
    uptime = current_time - _startup_time
    
    # Perform health checks
    checks = await _perform_health_checks(settings)
    
    # Determine overall status
    status = "healthy"
    if any(check.get("status") == "error" for check in checks.values()):
        status = "unhealthy"
    elif any(check.get("status") == "warning" for check in checks.values()):
        status = "degraded"
    
    return HealthStatus(
        status=status,
        timestamp=current_time,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime=uptime,
        checks=checks
    )


@router.get("/health/simple")
async def simple_health_check():
    """
    Simple health check for basic load balancer monitoring.
    
    Returns:
        dict: Basic status information
    """
    return {
        "status": "ok",
        "timestamp": time.time()
    }


@router.get("/health/ready")
async def readiness_check(settings: Settings = Depends(get_settings)):
    """
    Readiness check for Kubernetes and container orchestration.
    
    Verifies that the application is ready to serve requests by checking
    critical dependencies like vector store and external services.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        dict: Readiness status
        
    Raises:
        HTTPException: If application is not ready
    """
    checks = await _perform_readiness_checks(settings)
    
    # Check if any critical service is down
    critical_services = ["vector_store", "openai"]
    for service in critical_services:
        if service in checks and checks[service].get("status") == "error":
            raise HTTPException(
                status_code=503,
                detail=f"Service not ready: {service}"
            )
    
    return {
        "status": "ready",
        "timestamp": time.time(),
        "checks": checks
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes and container orchestration.
    
    Simple check to verify the application process is alive and responding.
    
    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": time.time(),
        "pid": os.getpid()
    }


@router.get("/system", response_model=SystemInfo)
async def system_info():
    """
    Get system resource information.
    
    Provides detailed information about system resources for monitoring
    and debugging purposes. Only available in development environment.
    
    Returns:
        SystemInfo: System resource information
        
    Raises:
        HTTPException: In production environment
    """
    # Only allow in development
    settings = get_settings()
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=404,
            detail="System info not available in production"
        )
    
    # Get system information
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return SystemInfo(
        cpu_percent=psutil.cpu_percent(interval=1),
        memory_percent=memory.percent,
        disk_usage={
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        },
        python_version=f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        process_id=os.getpid()
    )


async def _perform_health_checks(settings: Settings) -> Dict[str, Any]:
    """
    Perform comprehensive health checks.
    
    Args:
        settings: Application settings
        
    Returns:
        Dict containing health check results
    """
    checks = {}
    
    # Check vector store
    checks["vector_store"] = await _check_vector_store(settings)
    
    # Check OpenAI API
    checks["openai"] = await _check_openai_api(settings)
    
    # Check data directory
    checks["data_directory"] = _check_data_directory(settings)
    
    # Check system resources
    checks["system"] = _check_system_resources()
    
    return checks


async def _perform_readiness_checks(settings: Settings) -> Dict[str, Any]:
    """
    Perform readiness checks for critical services.
    
    Args:
        settings: Application settings
        
    Returns:
        Dict containing readiness check results
    """
    checks = {}
    
    # Check vector store availability
    checks["vector_store"] = await _check_vector_store(settings)
    
    # Check OpenAI API availability
    checks["openai"] = await _check_openai_api(settings)
    
    return checks


async def _check_vector_store(settings: Settings) -> Dict[str, Any]:
    """
    Check ChromaDB vector store connectivity.
    
    Args:
        settings: Application settings
        
    Returns:
        Dict containing check results
    """
    try:
        # Check if ChromaDB directory exists
        chroma_path = Path(settings.CHROMA_PATH)
        if not chroma_path.exists():
            return {
                "status": "error",
                "message": "ChromaDB directory not found",
                "details": {"path": str(chroma_path)}
            }
        
        # Try to initialize vector store (basic check)
        from api.services.vector_service import VectorService
        vector_service = VectorService()
        await vector_service.health_check()
        
        return {
            "status": "ok",
            "message": "Vector store available",
            "details": {"path": str(chroma_path)}
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Vector store check failed: {str(e)}",
            "details": {"error": str(e)}
        }


async def _check_openai_api(settings: Settings) -> Dict[str, Any]:
    """
    Check OpenAI API connectivity.
    
    Args:
        settings: Application settings
        
    Returns:
        Dict containing check results
    """
    try:
        if not settings.OPENAI_API_KEY:
            return {
                "status": "error",
                "message": "OpenAI API key not configured"
            }
        
        # Basic API key format check
        if not settings.OPENAI_API_KEY.startswith("sk-"):
            return {
                "status": "warning",
                "message": "OpenAI API key format appears invalid"
            }
        
        # TODO: Implement actual API connectivity test
        # For now, just check configuration
        return {
            "status": "ok",
            "message": "OpenAI API configured",
            "details": {"model": settings.OPENAI_MODEL}
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"OpenAI API check failed: {str(e)}",
            "details": {"error": str(e)}
        }


def _check_data_directory(settings: Settings) -> Dict[str, Any]:
    """
    Check data directory availability.
    
    Args:
        settings: Application settings
        
    Returns:
        Dict containing check results
    """
    try:
        data_path = Path(settings.DATA_PATH)
        
        if not data_path.exists():
            return {
                "status": "warning",
                "message": "Data directory not found",
                "details": {"path": str(data_path)}
            }
        
        # Count PDF files
        pdf_count = len(list(data_path.rglob("*.pdf")))
        
        return {
            "status": "ok",
            "message": "Data directory available",
            "details": {
                "path": str(data_path),
                "pdf_files": pdf_count
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Data directory check failed: {str(e)}",
            "details": {"error": str(e)}
        }


def _check_system_resources() -> Dict[str, Any]:
    """
    Check system resource availability.
    
    Returns:
        Dict containing system resource information
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine status based on resource usage
        status = "ok"
        if memory.percent > 90 or disk.percent > 95:
            status = "error"
        elif memory.percent > 80 or disk.percent > 85:
            status = "warning"
        
        return {
            "status": status,
            "message": "System resources checked",
            "details": {
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "cpu_count": psutil.cpu_count()
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"System resource check failed: {str(e)}",
            "details": {"error": str(e)}
        }
