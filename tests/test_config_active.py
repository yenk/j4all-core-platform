"""
Unit tests for active API configuration.
Tests only the settings and configuration being used by the live deployment.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
from api.config import Settings, get_settings


class TestActiveConfiguration:
    """Test configuration management for active deployment."""
    
    def test_settings_initialization(self):
        """Test that settings can be initialized with defaults."""
        settings = Settings()
        
        # Test required settings exist
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'HOST')
        assert hasattr(settings, 'PORT')
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key-123',
        'HOST': '127.0.0.1',
        'PORT': '9000'
    })
    def test_settings_from_environment(self):
        """Test that settings load from environment variables."""
        settings = Settings()
        
        assert settings.OPENAI_API_KEY == 'test-key-123'
        assert settings.HOST == '127.0.0.1'
        assert settings.PORT == 9000
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'real-key'})
    def test_openai_configured_check(self):
        """Test OpenAI API key validation."""
        settings = Settings()
        
        # Should have an API key
        assert settings.OPENAI_API_KEY == 'real-key'
        assert len(settings.OPENAI_API_KEY) > 0


if __name__ == "__main__":
    pytest.main([__file__])
