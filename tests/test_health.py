"""
Tests for health check router.

Tests all health check endpoints including basic health checks,
readiness checks, liveness checks, and system information.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.main import app


class TestHealthRouter:
    """Test cases for health check router."""
    
    def test_simple_health_check(self, client: TestClient):
        """Test simple health check endpoint."""
        response = client.get("/api/v1/health/simple")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_liveness_check(self, client: TestClient):
        """Test liveness check endpoint."""
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "pid" in data
    
    def test_comprehensive_health_check(self, client: TestClient):
        """Test comprehensive health check endpoint."""
        with patch('api.routers.health._check_vector_store') as mock_vector, \
             patch('api.routers.health._check_openai_api') as mock_openai, \
             patch('api.routers.health._check_data_directory') as mock_data, \
             patch('api.routers.health._check_system_resources') as mock_system:
            
            # Mock successful checks
            mock_vector.return_value = {"status": "ok", "message": "Vector store available"}
            mock_openai.return_value = {"status": "ok", "message": "OpenAI API configured"}
            mock_data.return_value = {"status": "ok", "message": "Data directory available"}
            mock_system.return_value = {"status": "ok", "message": "System resources checked"}
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert "environment" in data
            assert "uptime" in data
            assert "checks" in data
            assert len(data["checks"]) == 4
    
    def test_health_check_with_failures(self, client: TestClient):
        """Test health check with some service failures."""
        with patch('api.routers.health._check_vector_store') as mock_vector, \
             patch('api.routers.health._check_openai_api') as mock_openai, \
             patch('api.routers.health._check_data_directory') as mock_data, \
             patch('api.routers.health._check_system_resources') as mock_system:
            
            # Mock one failure
            mock_vector.return_value = {"status": "error", "message": "Vector store unavailable"}
            mock_openai.return_value = {"status": "ok", "message": "OpenAI API configured"}
            mock_data.return_value = {"status": "ok", "message": "Data directory available"}
            mock_system.return_value = {"status": "ok", "message": "System resources checked"}
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"  # Should be unhealthy due to error
    
    def test_readiness_check_success(self, client: TestClient):
        """Test successful readiness check."""
        with patch('api.routers.health._perform_readiness_checks') as mock_checks:
            mock_checks.return_value = {
                "vector_store": {"status": "ok"},
                "openai": {"status": "ok"}
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
    
    def test_readiness_check_failure(self, client: TestClient):
        """Test readiness check with critical service failure."""
        with patch('api.routers.health._perform_readiness_checks') as mock_checks:
            mock_checks.return_value = {
                "vector_store": {"status": "error"},
                "openai": {"status": "ok"}
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 503
    
    @patch('api.routers.health.psutil')
    def test_system_info_development(self, mock_psutil, client: TestClient):
        """Test system info endpoint in development environment."""
        # Mock psutil functions
        mock_psutil.virtual_memory.return_value = MagicMock(percent=45.0)
        mock_psutil.disk_usage.return_value = MagicMock(
            total=1000000000, used=500000000, free=500000000, percent=50.0
        )
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.cpu_count.return_value = 4
        
        with patch('api.config.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "development"
            
            response = client.get("/api/v1/system")
            
            assert response.status_code == 200
            data = response.json()
            assert "cpu_percent" in data
            assert "memory_percent" in data
            assert "disk_usage" in data
            assert "python_version" in data
    
    def test_system_info_production(self, client: TestClient):
        """Test system info endpoint blocked in production."""
        with patch('api.config.get_settings') as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "production"
            
            response = client.get("/api/v1/system")
            
            assert response.status_code == 404
