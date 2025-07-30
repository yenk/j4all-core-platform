"""
Chat service for LumiLens AI legal assistant.

This service handles the core chat functionality using RAG (Retrieval-Augmented Generation)
to provide contextually relevant legal assistance based on the document corpus.
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema.output import ChatGenerationChunk

from api.config import get_settings
from api.services.vector_service import VectorService
from api.core.exceptions import ExternalServiceException, VectorStoreException

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses."""
    
    def __init__(self):
        self.tokens = []
        self.finished = False
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM."""
        self.tokens.append(token)
    
    def on_llm_end(self, response, **kwargs) -> None:
        """Handle LLM completion."""
        self.finished = True


class ChatService:
    """
    Service for handling AI chat interactions with RAG capabilities.
    
    Integrates with vector store for document retrieval and OpenAI for
    response generation to provide contextually aware legal assistance.
    """
    
    def __init__(self):
        """Initialize chat service with dependencies."""
        self.settings = get_settings()
        self.vector_service = VectorService()
        self._llm: Optional[ChatOpenAI] = None
        self._system_prompt = self._create_system_prompt()
    
    async def initialize(self) -> None:
        """Initialize chat service and dependencies."""
        try:
            logger.info("🔧 Initializing chat service...")
            
            # Initialize vector service
            await self.vector_service.initialize()
            
            # Initialize LLM
            self._llm = ChatOpenAI(
                model=self.settings.OPENAI_MODEL,
                temperature=0.0,
                api_key=self.settings.OPENAI_API_KEY,
                streaming=True
            )
            
            logger.info("✅ Chat service initialized successfully")
            
        except Exception as e:
            logger.error("❌ Failed to initialize chat service: %s", str(e))
            raise ExternalServiceException("Chat Service", f"Initialization failed: {str(e)}")
    
    async def generate_response(
        self,
        message: str,
        conversation_history: List[Any] = None,
        include_sources: bool = True,
        max_sources: int = 5,
        temperature: float = 0.0
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate AI response using RAG pipeline.
        
        Args:
            message: User message
            conversation_history: Previous messages in conversation
            include_sources: Whether to include source documents
            max_sources: Maximum number of source documents to return
            temperature: LLM temperature for generation
            
        Returns:
            Tuple of (response_content, source_documents)
            
        Raises:
            ExternalServiceException: If response generation fails
        """
        try:
            if not self._llm:
                await self.initialize()
            
            logger.info("💬 Generating response for message: %s", message[:100])
            
            # Retrieve relevant documents
            sources = []
            context = ""
            
            if include_sources:
                try:
                    docs = await self.vector_service.similarity_search(
                        query=message,
                        k=max_sources
                    )
                    
                    # Extract context from documents
                    context_parts = []
                    for i, doc in enumerate(docs[:max_sources]):
                        context_parts.append(f"[Document {i+1}]\n{doc.page_content}")
                        
                        # Create source information
                        sources.append({
                            "id": i + 1,
                            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "metadata": doc.metadata,
                            "relevance_score": getattr(doc, 'relevance_score', 0.0)
                        })
                    
                    context = "\n\n".join(context_parts)
                    logger.info("📄 Retrieved %d source documents", len(sources))
                    
                except VectorStoreException as e:
                    logger.warning("⚠️ Failed to retrieve documents: %s", str(e))
                    # Continue without sources
            
            # Create messages for LLM
            messages = self._create_chat_messages(
                user_message=message,
                context=context,
                conversation_history=conversation_history or []
            )
            
            # Generate response
            if self._llm:
                # Update temperature if different from default
                if temperature != self._llm.temperature:
                    self._llm.temperature = temperature
                
                response = self._llm.invoke(messages)
                response_content = response.content
            else:
                raise ExternalServiceException("OpenAI", "LLM not initialized")
            
            logger.info("✅ Generated response (%d chars)", len(response_content))
            
            return response_content, sources
            
        except Exception as e:
            logger.error("❌ Failed to generate response: %s", str(e))
            if isinstance(e, (ExternalServiceException, VectorStoreException)):
                raise
            raise ExternalServiceException("Chat Service", f"Response generation failed: {str(e)}")
    
    async def generate_streaming_response(
        self,
        message: str,
        conversation_history: List[Any] = None,
        include_sources: bool = True,
        max_sources: int = 5,
        temperature: float = 0.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming AI response using RAG pipeline.
        
        Args:
            message: User message
            conversation_history: Previous messages in conversation
            include_sources: Whether to include source documents
            max_sources: Maximum number of source documents to return
            temperature: LLM temperature for generation
            
        Yields:
            Dict containing response chunks and metadata
            
        Raises:
            ExternalServiceException: If streaming fails
        """
        try:
            if not self._llm:
                await self.initialize()
            
            logger.info("💬 Generating streaming response for message: %s", message[:100])
            
            # Retrieve relevant documents (same as non-streaming)
            sources = []
            context = ""
            
            if include_sources:
                try:
                    docs = await self.vector_service.similarity_search(
                        query=message,
                        k=max_sources
                    )
                    
                    context_parts = []
                    for i, doc in enumerate(docs[:max_sources]):
                        context_parts.append(f"[Document {i+1}]\n{doc.page_content}")
                        
                        sources.append({
                            "id": i + 1,
                            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            "metadata": doc.metadata,
                            "relevance_score": getattr(doc, 'relevance_score', 0.0)
                        })
                    
                    context = "\n\n".join(context_parts)
                    
                    # Yield sources first
                    yield {
                        "content": None,
                        "sources": sources,
                        "metadata": {"sources_count": len(sources)}
                    }
                    
                except VectorStoreException as e:
                    logger.warning("⚠️ Failed to retrieve documents: %s", str(e))
            
            # Create messages for LLM
            messages = self._create_chat_messages(
                user_message=message,
                context=context,
                conversation_history=conversation_history or []
            )
            
            # Generate streaming response
            if self._llm:
                # Update temperature if different from default
                if temperature != self._llm.temperature:
                    self._llm.temperature = temperature
                
                # Stream the response
                full_response = ""
                async for chunk in self._llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response += chunk.content
                        yield {
                            "content": chunk.content,
                            "sources": None,
                            "metadata": {
                                "is_streaming": True,
                                "full_response_length": len(full_response)
                            }
                        }
                
                # Final chunk with complete response metadata
                yield {
                    "content": None,
                    "sources": None,
                    "metadata": {
                        "is_streaming": False,
                        "complete": True,
                        "total_length": len(full_response),
                        "sources_count": len(sources)
                    }
                }
                
            else:
                raise ExternalServiceException("OpenAI", "LLM not initialized")
            
            logger.info("✅ Completed streaming response (%d chars)", len(full_response))
            
        except Exception as e:
            logger.error("❌ Failed to generate streaming response: %s", str(e))
            yield {
                "content": f"Error: {str(e)}",
                "sources": None,
                "metadata": {"error": True, "error_type": type(e).__name__}
            }
    
    def _create_system_prompt(self) -> str:
        """
        Create system prompt for the legal AI assistant.
        
        Returns:
            str: System prompt defining the assistant's behavior
        """
        return """You are LumiLens, an expert AI legal assistant specialized in contract law, appellate matters, and legal document analysis. You help lawyers, plaintiffs, defendants, journalists, and courts by providing accurate, contextual legal guidance.

Your key capabilities:
- Analyze legal documents including contracts, case law, and appellate decisions
- Provide insights on legal precedents and case strategies
- Explain complex legal concepts in accessible language
- Identify potential legal issues and risks
- Suggest relevant case law and legal authorities

Guidelines for responses:
1. ACCURACY: Base your responses on the provided legal documents and established legal principles
2. CONTEXT: Use the document context provided to give specific, relevant answers
3. CLARITY: Explain legal concepts clearly, avoiding unnecessary jargon
4. CAUTION: Always note when legal advice requires professional consultation
5. SOURCES: Reference specific documents or cases when applicable
6. OBJECTIVITY: Present balanced analysis without bias

Important disclaimers:
- You provide legal information, not legal advice
- Users should consult qualified attorneys for specific legal matters
- Laws vary by jurisdiction and change over time
- Your responses are based on available documents and may not reflect recent developments

Always strive to be helpful, accurate, and professional in your responses."""
    
    def _create_chat_messages(
        self,
        user_message: str,
        context: str,
        conversation_history: List[Any]
    ) -> List[BaseMessage]:
        """
        Create properly formatted messages for the LLM.
        
        Args:
            user_message: Current user message
            context: Retrieved document context
            conversation_history: Previous conversation messages
            
        Returns:
            List[BaseMessage]: Formatted messages for LLM
        """
        messages = []
        
        # System message
        messages.append(SystemMessage(content=self._system_prompt))
        
        # Add conversation history (limit to recent messages to stay within token limits)
        max_history = 10  # Keep last 10 messages
        recent_history = conversation_history[-max_history:] if len(conversation_history) > max_history else conversation_history
        
        for msg in recent_history:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
        
        # Create current user message with context
        if context:
            user_message_with_context = f"""Context from legal documents:
{context}

User question: {user_message}

Please provide a comprehensive answer based on the context above. If the context doesn't contain relevant information, please indicate that and provide general legal guidance where appropriate."""
        else:
            user_message_with_context = user_message
        
        messages.append(HumanMessage(content=user_message_with_context))
        
        return messages
