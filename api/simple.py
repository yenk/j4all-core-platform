from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import uuid

# Create minimal FastAPI app
app = FastAPI(title="LumiLens Chat API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Simple models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: float

# Root endpoint
@app.get("/")
def root():
    return {
        "name": "LumiLens Chat API",
        "status": "online",
        "version": "1.0.0"
    }

# Health check - both root and v1 paths
@app.get("/health")
@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

# Simple chat endpoint - both root and v1 paths
@app.post("/chat", response_model=ChatResponse)
@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(message: ChatMessage):
    # Generate or use existing conversation ID
    conversation_id = message.conversation_id or str(uuid.uuid4())
    
    # Simple echo response for now
    response_text = f"I received your message: '{message.message}'. This is a simple chat response from LumiLens AI."
    
    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        timestamp=time.time()
    )

# List available endpoints
@app.get("/endpoints")
def endpoints():
    return {
        "available_endpoints": [
            "GET / - Root info",
            "GET /health - Health check",
            "GET /api/v1/health - Health check (v1)", 
            "POST /chat - Chat endpoint",
            "POST /api/v1/chat - Chat endpoint (v1)",
            "GET /endpoints - This list"
        ]
    }
