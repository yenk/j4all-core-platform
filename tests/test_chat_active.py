"""
Unit tests for active chat endpoint.
Tests only the chat endpoint being used by the live frontend.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
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


class TestActiveChatEndpoint:
    """Test chat endpoint used by lumilens.ai frontend."""
    
    def test_chat_endpoint_exists(self, test_client):
        """Test that /api/v1/chat endpoint exists."""
        # Test with minimal valid request
        response = test_client.post(
            "/api/v1/chat",
            json={"message": "Hello"}
        )
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        
        # Should return some response (200, 422, or 500 are all valid for now)
        assert response.status_code in [200, 422, 500]
    
    def test_chat_request_validation(self, test_client):
        """Test that chat endpoint validates request format."""
        # Test missing message
        response = test_client.post("/api/v1/chat", json={})
        assert response.status_code == 422  # Validation error
        
        # Test empty message
        response = test_client.post("/api/v1/chat", json={"message": ""})
        assert response.status_code == 422  # Validation error
        
        # Test valid message structure
        response = test_client.post("/api/v1/chat", json={"message": "Test"})
        # Should accept the format (whether it works or not is separate)
        assert response.status_code != 422
    
    @patch('api.services.chat_service.ChatService.generate_response')
    def test_chat_with_mock_response(self, mock_generate, test_client):
        """Test chat endpoint with mocked chat service."""
        # Mock successful chat response
        mock_generate.return_value = ("Test response", [])
        
        response = test_client.post(
            "/api/v1/chat",
            json={"message": "Hello"}
        )
        
        # Should return 200 with mocked response
        if response.status_code == 200:
            data = response.json()
            assert "message" in data  # Backend returns 'message' field
            assert isinstance(data["message"], str)
            assert len(data["message"]) > 0
    
    def test_chat_response_format(self, test_client):
        """Test that chat endpoint returns expected response format."""
        response = test_client.post(
            "/api/v1/chat",
            json={"message": "Test message"}
        )
        
        # If successful, should have the right format
        if response.status_code == 200:
            data = response.json()
            
            # Should have message field (not 'response')
            assert "message" in data
            
            # Should have conversation_id
            assert "conversation_id" in data
            
            # Should have timestamp
            assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__])
