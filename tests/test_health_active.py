"""
Unit tests for active health check endpoint.
Tests only the health endpoint being used by the live frontend.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from api.main import app
    return TestClient(app)


class TestActiveHealthEndpoint:
    """Test health check endpoint used by lumilens.ai frontend."""
    
    def test_health_endpoint_exists(self, test_client):
        """Test that /api/v1/health endpoint exists and responds."""
        response = test_client.get("/api/v1/health")
        
        # Should return 200 OK
        assert response.status_code == 200
        
        # Should return JSON
        data = response.json()
        assert isinstance(data, dict)
        
        # Should have status field
        assert "status" in data
    
    @patch('api.routers.health.test_openai_connection')
    def test_health_with_openai_success(self, mock_openai, test_client):
        """Test health check when OpenAI is working."""
        # Mock successful OpenAI connection
        mock_openai.return_value = (True, "OpenAI connection successful")
        
        response = test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should indicate healthy status
        assert data["status"] == "healthy"
        
        # Should have OpenAI status
        if "openai" in data:
            assert data["openai"]["status"] == "ok"
    
    @patch('api.routers.health.test_openai_connection')
    def test_health_with_openai_failure(self, mock_openai, test_client):
        """Test health check when OpenAI is failing."""
        # Mock failed OpenAI connection
        mock_openai.return_value = (False, "API key invalid")
        
        response = test_client.get("/api/v1/health")
        
        # Should still return 200 (service is up, just OpenAI failing)
        assert response.status_code == 200
        data = response.json()
        
        # Should still report as healthy (service itself is running)
        assert data["status"] in ["healthy", "degraded"]


if __name__ == "__main__":
    pytest.main([__file__])
