"""
Test configuration and fixtures for LumiLens API tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from api.main import app
from api.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        OPENAI_API_KEY="test-key-sk-123",
        CHROMA_PATH="./test_chroma_db",
        DATA_PATH="./test_data",
        RATE_LIMIT_REQUESTS=1000,  # High limit for tests
        RATE_LIMIT_WINDOW=3600
    )


@pytest.fixture
def client():
    """Provide synchronous test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide asynchronous test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_legal_text():
    """Provide sample legal text for testing."""
    return """
    This Agreement is entered into on January 1, 2024, between Company ABC ("Company") 
    and John Doe ("Employee"). The Employee shall receive a salary of $75,000 per year. 
    The term of this agreement shall be for two (2) years, commencing on the effective date. 
    Either party may terminate this agreement with thirty (30) days written notice.
    The Employee agrees to maintain confidentiality of all proprietary information.
    """


@pytest.fixture
def sample_chat_message():
    """Provide sample chat message for testing."""
    return "What are the key terms in this employment agreement?"


@pytest.fixture
def mock_vector_documents():
    """Provide mock vector search results."""
    return [
        {
            "page_content": "Sample legal document content about employment agreements...",
            "metadata": {
                "source": "employment_law.pdf",
                "page": 1,
                "id": "doc_1"
            }
        },
        {
            "page_content": "Additional content about contract termination clauses...",
            "metadata": {
                "source": "contract_law.pdf", 
                "page": 5,
                "id": "doc_2"
            }
        }
    ]
