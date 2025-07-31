"""
Chat router for LumiLens AI legal assistant.

Provides REST and WebSocket endpoints for AI-powered legal document analysis
and conversational assistance using RAG (Retrieval-Augmented Generation).
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import logging
import asyncio
from datetime import datetime
import uuid

from api.config import Settings, get_settings
from api.core.exceptions import (
    LumiLensException, 
    ExternalServiceException,
    ValidationException
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for type safety
class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")
    include_sources: bool = Field(default=True, description="Include source documents in response")
    max_sources: int = Field(default=5, ge=1, le=10, description="Maximum number of source documents")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM temperature for response generation")


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatHistory(BaseModel):
    """Chat conversation history model."""
    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StreamingChatResponse(BaseModel):
    """Streaming chat response chunk model."""
    type: str = Field(..., description="Chunk type: 'start', 'content', 'sources', 'end', 'error'")
    content: Optional[str] = Field(default=None, description="Content chunk")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Source documents")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Chunk metadata")
    timestamp: datetime = Field(default_factory=datetime.now)


# In-memory storage for conversations (replace with database in production)
_conversations: Dict[str, ChatHistory] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Generate AI chat completion for legal document analysis.
    
    This endpoint provides conversational AI assistance for legal matters,
    leveraging RAG to provide contextually relevant responses based on
    the legal document corpus.
    
    Args:
        request: Chat request containing user message and parameters
        settings: Application settings dependency
        
    Returns:
        ChatResponse: AI-generated response with sources and metadata
        
    Raises:
        HTTPException: If chat generation fails
    """
    try:
        logger.info("Processing chat request: %s", request.message[:100])
        
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        conversation = _conversations.get(conversation_id)
        if not conversation:
            conversation = ChatHistory(
                conversation_id=conversation_id,
                messages=[]
            )
            _conversations[conversation_id] = conversation
        
        # Add user message to conversation
        user_message = ChatMessage(
            role="user",
            content=request.message,
            metadata={"temperature": request.temperature}
        )
        conversation.messages.append(user_message)
        
        # Generate AI response using RAG
        response_content, sources = await _generate_chat_response(
            message=request.message,
            conversation_history=conversation.messages[:-1],  # Exclude current message
            settings=settings,
            include_sources=request.include_sources,
            max_sources=request.max_sources,
            temperature=request.temperature
        )
        
        # Add assistant message to conversation
        assistant_message = ChatMessage(
            role="assistant",
            content=response_content,
            metadata={
                "sources_count": len(sources),
                "temperature": request.temperature
            }
        )
        conversation.messages.append(assistant_message)
        conversation.updated_at = datetime.now()
        
        return ChatResponse(
            message=response_content,
            conversation_id=conversation_id,
            sources=sources,
            metadata={
                "message_count": len(conversation.messages),
                "temperature": request.temperature,
                "model": settings.OPENAI_MODEL
            }
        )
        
    except Exception as e:
        logger.error("Chat completion failed: %s", str(e))
        if isinstance(e, LumiLensException):
            raise
        raise ExternalServiceException("OpenAI", str(e))


@router.post("/chat/stream")
async def chat_completion_stream(
    request: ChatRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Generate streaming AI chat completion for real-time responses.
    
    This endpoint provides streaming responses for better user experience,
    allowing the frontend to display responses as they are generated.
    
    Args:
        request: Chat request containing user message and parameters
        settings: Application settings dependency
        
    Returns:
        StreamingResponse: Server-sent events with response chunks
        
    Raises:
        HTTPException: If streaming fails
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            # Send start event
            yield f"data: {json.dumps(StreamingChatResponse(type='start', conversation_id=conversation_id).dict())}\n\n"
            
            # Generate streaming response
            async for chunk in _generate_streaming_response(
                message=request.message,
                conversation_id=conversation_id,
                settings=settings,
                include_sources=request.include_sources,
                max_sources=request.max_sources,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps(chunk.dict())}\n\n"
                
        except Exception as e:
            error_chunk = StreamingChatResponse(
                type="error",
                content=f"Error: {str(e)}",
                metadata={"error_type": type(e).__name__}
            )
            yield f"data: {json.dumps(error_chunk.dict())}\n\n"
        
        # Send end event
        yield f"data: {json.dumps(StreamingChatResponse(type='end').dict())}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.websocket("/chat/ws")
async def websocket_chat(websocket: WebSocket, settings: Settings = Depends(get_settings)):
    """
    WebSocket endpoint for real-time chat communication.
    
    Provides bidirectional communication for real-time chat experience
    with support for multiple concurrent conversations.
    
    Args:
        websocket: WebSocket connection
        settings: Application settings dependency
    """
    await websocket.accept()
    conversation_id = str(uuid.uuid4())
    
    try:
        logger.info("WebSocket chat session started: %s", conversation_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "conversation_id": conversation_id,
            "message": "Connected to LumiLens AI Assistant"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            if data.get("type") == "chat":
                message = data.get("message", "").strip()
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Message cannot be empty"
                    })
                    continue
                
                try:
                    # Process chat message
                    async for chunk in _generate_streaming_response(
                        message=message,
                        conversation_id=conversation_id,
                        settings=settings,
                        include_sources=data.get("include_sources", True),
                        max_sources=data.get("max_sources", 5),
                        temperature=data.get("temperature", 0.0)
                    ):
                        await websocket.send_json(chunk.dict())
                        
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Unknown message type"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket chat session ended: %s", conversation_id)
    except Exception as e:
        logger.error("WebSocket error: %s", str(e))
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Connection error occurred"
            })
        except:
            pass


@router.get("/conversations/{conversation_id}", response_model=ChatHistory)
async def get_conversation(conversation_id: str):
    """
    Retrieve conversation history by ID.
    
    Args:
        conversation_id: Unique conversation identifier
        
    Returns:
        ChatHistory: Complete conversation history
        
    Raises:
        HTTPException: If conversation not found
    """
    conversation = _conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )
    
    return conversation

@router.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str, settings: Settings = Depends(get_settings)):
    """
    Retrieve chat history for a given conversation ID.
    """
    conversation = _conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.get("/conversations", response_model=List[ChatHistory])
async def list_conversations(limit: int = 10, skip: int = 0):
    """
    List recent conversations.
    
    Args:
        limit: Maximum number of conversations to return
        skip: Number of conversations to skip
        
    Returns:
        List[ChatHistory]: List of conversation histories
    """
    conversations = list(_conversations.values())
    conversations.sort(key=lambda x: x.updated_at, reverse=True)
    
    return conversations[skip:skip + limit]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation by ID.
    
    Args:
        conversation_id: Unique conversation identifier
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If conversation not found
    """
    if conversation_id not in _conversations:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )
    
    del _conversations[conversation_id]
    
    return {
        "message": f"Conversation {conversation_id} deleted successfully",
        "conversation_id": conversation_id
    }


async def _generate_chat_response(
    message: str,
    conversation_history: List[ChatMessage],
    settings: Settings,
    include_sources: bool = True,
    max_sources: int = 5,
    temperature: float = 0.0
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Generate chat response using RAG pipeline.
    
    Args:
        message: User message
        conversation_history: Previous conversation messages
        settings: Application settings
        include_sources: Whether to include source documents
        max_sources: Maximum number of sources to return
        temperature: LLM temperature for generation
        
    Returns:
        Tuple of response content and source documents
    """
    try:
        # Import here to avoid circular imports
        from api.services.chat_service import ChatService
        
        chat_service = ChatService()
        return await chat_service.generate_response(
            message=message,
            conversation_history=conversation_history,
            include_sources=include_sources,
            max_sources=max_sources,
            temperature=temperature
        )
        
    except Exception as e:
        logger.error("Failed to generate chat response: %s", str(e))
        raise ExternalServiceException("Chat Service", str(e))


async def _generate_streaming_response(
    message: str,
    conversation_id: str,
    settings: Settings,
    include_sources: bool = True,
    max_sources: int = 5,
    temperature: float = 0.0
) -> AsyncGenerator[StreamingChatResponse, None]:
    """
    Generate streaming chat response.
    
    Args:
        message: User message
        conversation_id: Conversation identifier
        settings: Application settings
        include_sources: Whether to include source documents
        max_sources: Maximum number of sources to return
        temperature: LLM temperature for generation
        
    Yields:
        StreamingChatResponse: Response chunks
    """
    try:
        # Import here to avoid circular imports
        from api.services.chat_service import ChatService
        
        chat_service = ChatService()
        
        # Get conversation history
        conversation = _conversations.get(conversation_id)
        history = conversation.messages if conversation else []
        
        # Generate streaming response
        async for chunk in chat_service.generate_streaming_response(
            message=message,
            conversation_history=history,
            include_sources=include_sources,
            max_sources=max_sources,
            temperature=temperature
        ):
            yield StreamingChatResponse(
                type="content",
                content=chunk.get("content"),
                conversation_id=conversation_id,
                sources=chunk.get("sources"),
                metadata=chunk.get("metadata")
            )
        
        # Update conversation history
        if conversation_id in _conversations:
            _conversations[conversation_id].messages.extend([
                ChatMessage(role="user", content=message),
                ChatMessage(role="assistant", content="[Streaming response]")
            ])
            _conversations[conversation_id].updated_at = datetime.now()
        
    except Exception as e:
        logger.error("Failed to generate streaming response: %s", str(e))
        yield StreamingChatResponse(
            type="error",
            content=f"Error: {str(e)}",
            conversation_id=conversation_id,
            metadata={"error_type": type(e).__name__}
        )
