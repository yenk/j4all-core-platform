# LumiLens FastAPI Backend

## Overview

This is the FastAPI backend for LumiLens AI, providing REST and WebSocket APIs for legal document analysis and AI-powered chat assistance. The backend integrates with your existing RAG pipeline and ChromaDB vector store.

## Architecture

```
api/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── run_server.py          # Server startup script
├── core/                  # Core utilities
│   ├── exceptions.py      # Custom exceptions and error handling
│   └── logging.py         # Logging configuration
├── routers/               # API route handlers
│   ├── chat.py           # Chat and WebSocket endpoints
│   ├── documents.py      # Document upload and processing
│   ├── analysis.py       # Document analysis endpoints
│   └── health.py         # Health check endpoints
├── services/             # Business logic services
│   ├── vector_service.py # Vector store operations
│   └── chat_service.py   # Chat and RAG functionality
├── middleware/           # Custom middleware
│   ├── auth.py          # Authentication middleware
│   └── rate_limit.py    # Rate limiting middleware
└── tests/               # Unit tests
    ├── conftest.py      # Test configuration
    └── test_*.py        # Test modules
```

## Key Features

### 🚀 **FastAPI Backend**
- **Modern async/await**: High-performance async request handling
- **Type safety**: Full Pydantic models with validation
- **Auto-documentation**: Swagger/OpenAPI docs at `/api/docs`
- **WebSocket support**: Real-time chat functionality

### 🔐 **Security & Middleware**
- **CORS**: Configured for React frontend integration
- **Rate limiting**: Token bucket algorithm with IP tracking
- **Authentication**: API key and Bearer token support
- **Request logging**: Comprehensive request/response logging

### 🤖 **AI Integration**
- **RAG Pipeline**: Integrates with existing LangChain setup
- **Vector Search**: ChromaDB similarity search
- **Streaming**: Real-time chat response streaming
- **Context Management**: Conversation history tracking

### 📄 **Document Processing**
- **Multi-format**: PDF, DOCX, TXT support
- **Batch upload**: Multiple document processing
- **Auto-ingestion**: Directory-based document processing
- **Analysis**: Entity extraction, summarization, key points

## Quick Start

### 1. Install Dependencies

```bash
# Update pyproject.toml with new dependencies
poetry install

# Or using pip
pip install fastapi uvicorn pydantic pydantic-settings python-multipart psutil
```

### 2. Environment Configuration

Create or update your `.env` file:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Server
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Paths
DATA_PATH=./data
CHROMA_PATH=./chroma_db

# Security
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:4000"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### 3. Start the Server

```bash
# Using the startup script (recommended)
python run_server.py

# Or directly with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Or using poetry
poetry run python run_server.py
```

### 4. Verify Installation

Visit the API documentation:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Health & System
- `GET /health` - Simple health check
- `GET /api/v1/health` - Comprehensive health check
- `GET /api/v1/health/ready` - Readiness check (K8s)
- `GET /api/v1/health/live` - Liveness check (K8s)
- `GET /api/v1/system` - System resources (dev only)

### Chat & AI
- `POST /api/v1/chat` - Generate AI chat response
- `POST /api/v1/chat/stream` - Streaming chat response
- `WebSocket /api/v1/chat/ws` - Real-time chat WebSocket
- `GET /api/v1/conversations` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation

### Documents
- `POST /api/v1/documents/upload` - Upload single document
- `POST /api/v1/documents/upload-batch` - Batch upload
- `POST /api/v1/documents/ingest-directory` - Ingest directory
- `GET /api/v1/documents/stats` - Document statistics
- `GET /api/v1/documents/supported-formats` - Supported formats

### Analysis
- `POST /api/v1/analysis/analyze` - Analyze document text
- `POST /api/v1/analysis/similar` - Find similar documents
- `GET /api/v1/analysis/capabilities` - Analysis capabilities

## Frontend Integration

### React Integration

```typescript
// API client example
const API_BASE_URL = 'http://localhost:8000/api/v1';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface ChatResponse {
  message: string;
  conversation_id: string;
  sources: Array<{
    id: number;
    content: string;
    metadata: Record<string, any>;
  }>;
}

// Chat API call
async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key', // In development
    },
    body: JSON.stringify({
      message,
      include_sources: true,
      max_sources: 5,
      temperature: 0.0
    })
  });
  
  return response.json();
}

// Streaming chat
async function streamChatMessage(message: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key',
    },
    body: JSON.stringify({ message })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'content' && data.content) {
          // Update UI with streaming content
          console.log(data.content);
        }
      }
    }
  }
}

// WebSocket chat
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'content') {
    // Handle streaming response
    console.log(data.content);
  }
};

ws.send(JSON.stringify({
  type: 'chat',
  message: 'What are the key terms in this contract?'
}));
```

### Document Upload

```typescript
// File upload
async function uploadDocument(file: File): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('process_immediately', 'true');

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  console.log('Upload result:', result);
}
```

## Testing

Run the test suite:

```bash
# Install test dependencies
poetry add --group dev pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

## Deployment

### Vercel Deployment

1. **Create `vercel.json`**:

```json
{
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/main.py"
    }
  ],
  "env": {
    "PYTHONPATH": "."
  }
}
```

2. **Set Environment Variables** in Vercel dashboard:
   - `OPENAI_API_KEY`
   - `ENVIRONMENT=production`
   - `ALLOWED_ORIGINS=["https://your-frontend-domain.vercel.app"]`

3. **Deploy**:
```bash
vercel --prod
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY . .

EXPOSE 8000

CMD ["python", "run_server.py"]
```

## Monitoring & Logging

### Health Checks
- **Basic**: `GET /health` - Returns 200 if server is running
- **Detailed**: `GET /api/v1/health` - Checks all dependencies
- **Kubernetes**: Ready/Live endpoints for container orchestration

### Logging
- **Structured logging** with timestamps and request IDs
- **Different levels** for development vs production
- **File rotation** in production environments
- **Request/response tracking** with timing information

### Rate Limiting
- **Token bucket algorithm** with configurable limits
- **Per-IP tracking**with automatic cleanup
- **Rate limit headers** for client awareness
- **Bypass for health checks** and documentation

## Next Steps

1. **Authentication**: Implement JWT or OAuth2 for production
2. **Database**: Add PostgreSQL for conversation persistence
3. **Caching**: Add Redis for improved performance
4. **Monitoring**: Integrate Prometheus/Grafana metrics
5. **Background Tasks**: Add Celery for long-running operations

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes project root
2. **CORS Issues**: Check `ALLOWED_ORIGINS` in settings
3. **Vector Store**: Verify ChromaDB path and permissions
4. **OpenAI**: Confirm API key is valid and has credits

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python run_server.py
```

This comprehensive FastAPI backend provides a production-ready foundation for your LumiLens AI platform while maintaining compatibility with your existing React frontend and RAG pipeline.
