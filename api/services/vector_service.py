"""
Vector store service for LumiLens AI.

This service provides an abstraction layer over ChromaDB for document
storage, retrieval, and similarity search operations with proper error
handling and connection management.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
from uuid import uuid4

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from api.config import get_settings
from api.core.exceptions import VectorStoreException, ExternalServiceException

logger = logging.getLogger(__name__)


class VectorService:
    """
    Service for managing vector store operations.
    
    Provides high-level interface for document ingestion, similarity search,
    and vector store management with proper error handling and logging.
    """
    
    def __init__(self):
        """Initialize vector service with configuration."""
        self.settings = get_settings()
        self._vector_store: Optional[Chroma] = None
        self._embedding_function: Optional[OpenAIEmbeddings] = None
        self._is_initialized = False
        
    async def initialize(self) -> None:
        """
        Initialize vector store and embedding function.
        
        Raises:
            VectorStoreException: If initialization fails
        """
        try:
            logger.info("🔧 Initializing vector service...")
            
            # Create embedding function
            self._embedding_function = OpenAIEmbeddings(
                model=self.settings.OPENAI_EMBEDDING_MODEL,
                api_key=self.settings.OPENAI_API_KEY
            )
            
            # Ensure ChromaDB directory exists
            chroma_path = Path(self.settings.CHROMA_PATH)
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB vector store
            self._vector_store = Chroma(
                collection_name=self.settings.CHROMA_COLLECTION_NAME,
                embedding_function=self._embedding_function,
                persist_directory=str(chroma_path)
            )
            
            self._is_initialized = True
            logger.info("✅ Vector service initialized successfully")
            
        except Exception as e:
            logger.error("❌ Failed to initialize vector service: %s", str(e))
            raise VectorStoreException(f"Initialization failed: {str(e)}", "initialize")
    
    async def health_check(self) -> bool:
        """
        Perform health check on vector store.
        
        Returns:
            bool: True if vector store is healthy
            
        Raises:
            VectorStoreException: If health check fails
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            
            # Try to get collection info
            if self._vector_store:
                collection = self._vector_store._collection
                count = collection.count()
                logger.info("📊 Vector store health check: %d documents", count)
                return True
            
            return False
            
        except Exception as e:
            logger.error("❌ Vector store health check failed: %s", str(e))
            raise VectorStoreException(f"Health check failed: {str(e)}", "health_check")
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Perform similarity search in vector store.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List[Document]: Similar documents with metadata
            
        Raises:
            VectorStoreException: If search fails
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            
            if not self._vector_store:
                raise VectorStoreException("Vector store not initialized", "search")
            
            logger.info("🔍 Performing similarity search: %s (k=%d)", query[:100], k)
            
            # Perform similarity search
            if filter_metadata:
                docs = self._vector_store.similarity_search(
                    query=query,
                    k=k,
                    filter=filter_metadata
                )
            else:
                docs = self._vector_store.similarity_search(
                    query=query,
                    k=k
                )
            
            logger.info("📄 Found %d similar documents", len(docs))
            return docs
            
        except Exception as e:
            logger.error("❌ Similarity search failed: %s", str(e))
            raise VectorStoreException(f"Search failed: {str(e)}", "similarity_search")
    
    async def similarity_search_with_scores(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Perform similarity search with relevance scores.
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List[Tuple[Document, float]]: Documents with similarity scores
            
        Raises:
            VectorStoreException: If search fails
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            
            if not self._vector_store:
                raise VectorStoreException("Vector store not initialized", "search")
            
            logger.info("🔍 Performing similarity search with scores: %s (k=%d)", query[:100], k)
            
            # Perform similarity search with scores
            if filter_metadata:
                results = self._vector_store.similarity_search_with_score(
                    query=query,
                    k=k,
                    filter=filter_metadata
                )
            else:
                results = self._vector_store.similarity_search_with_score(
                    query=query,
                    k=k
                )
            
            logger.info("📄 Found %d similar documents with scores", len(results))
            return results
            
        except Exception as e:
            logger.error("❌ Similarity search with scores failed: %s", str(e))
            raise VectorStoreException(f"Search failed: {str(e)}", "similarity_search_with_scores")
    
    async def add_documents(
        self,
        documents: List[Document],
        remove_duplicates: bool = True
    ) -> List[str]:
        """
        Add documents to vector store.
        
        Args:
            documents: List of documents to add
            remove_duplicates: Whether to remove duplicate documents
            
        Returns:
            List[str]: Document IDs that were added
            
        Raises:
            VectorStoreException: If adding documents fails
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            
            if not self._vector_store:
                raise VectorStoreException("Vector store not initialized", "add_documents")
            
            if not documents:
                logger.warning("⚠️ No documents provided to add")
                return []
            
            logger.info("📝 Adding %d documents to vector store", len(documents))
            
            # Remove duplicates if requested
            if remove_duplicates:
                documents = self._remove_duplicate_documents(documents)
                logger.info("📝 After deduplication: %d documents", len(documents))
            
            # Generate unique IDs for documents
            doc_ids = [str(uuid4()) for _ in documents]
            
            # Add documents to vector store
            self._vector_store.add_documents(
                documents=documents,
                ids=doc_ids
            )
            
            logger.info("✅ Successfully added %d documents", len(documents))
            return doc_ids
            
        except Exception as e:
            logger.error("❌ Failed to add documents: %s", str(e))
            raise VectorStoreException(f"Failed to add documents: {str(e)}", "add_documents")
    
    async def ingest_documents_from_directory(
        self,
        directory_path: Optional[str] = None,
        file_extensions: List[str] = None
    ) -> int:
        """
        Ingest documents from a directory into vector store.
        
        Args:
            directory_path: Path to directory containing documents
            file_extensions: List of file extensions to process
            
        Returns:
            int: Number of documents successfully ingested
            
        Raises:
            VectorStoreException: If ingestion fails
        """
        try:
            data_path = directory_path or self.settings.DATA_PATH
            extensions = file_extensions or [".pdf"]
            
            logger.info("📂 Starting document ingestion from: %s", data_path)
            
            # Check if directory exists
            if not os.path.exists(data_path):
                raise VectorStoreException(f"Directory not found: {data_path}", "ingest")
            
            # Load documents
            documents = await self._load_documents_from_directory(data_path, extensions)
            
            if not documents:
                logger.warning("⚠️ No documents found in directory: %s", data_path)
                return 0
            
            # Split documents into chunks
            chunks = await self._split_documents(documents)
            
            # Add chunks to vector store
            doc_ids = await self.add_documents(chunks)
            
            logger.info("✅ Successfully ingested %d document chunks", len(doc_ids))
            return len(doc_ids)
            
        except Exception as e:
            logger.error("❌ Document ingestion failed: %s", str(e))
            raise VectorStoreException(f"Ingestion failed: {str(e)}", "ingest_documents")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.
        
        Returns:
            Dict containing collection statistics
            
        Raises:
            VectorStoreException: If stats retrieval fails
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            
            if not self._vector_store:
                raise VectorStoreException("Vector store not initialized", "stats")
            
            collection = self._vector_store._collection
            count = collection.count()
            
            stats = {
                "document_count": count,
                "collection_name": self.settings.CHROMA_COLLECTION_NAME,
                "embedding_model": self.settings.OPENAI_EMBEDDING_MODEL,
                "path": self.settings.CHROMA_PATH
            }
            
            logger.info("📊 Collection stats: %d documents", count)
            return stats
            
        except Exception as e:
            logger.error("❌ Failed to get collection stats: %s", str(e))
            raise VectorStoreException(f"Stats retrieval failed: {str(e)}", "stats")
    
    async def cleanup(self) -> None:
        """Cleanup resources and connections."""
        try:
            logger.info("🧹 Cleaning up vector service...")
            
            # Persist vector store if needed
            if self._vector_store:
                # ChromaDB auto-persists, but we can call persist explicitly
                # self._vector_store.persist()
                pass
            
            self._vector_store = None
            self._embedding_function = None
            self._is_initialized = False
            
            logger.info("✅ Vector service cleanup completed")
            
        except Exception as e:
            logger.error("❌ Vector service cleanup failed: %s", str(e))
    
    def _remove_duplicate_documents(self, documents: List[Document]) -> List[Document]:
        """
        Remove duplicate documents based on content hash.
        
        Args:
            documents: List of documents to deduplicate
            
        Returns:
            List[Document]: Deduplicated documents
        """
        seen_hashes = set()
        unique_documents = []
        
        for doc in documents:
            # Create hash of document content
            content_hash = hashlib.sha256(doc.page_content.encode('utf-8')).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_documents.append(doc)
        
        removed_count = len(documents) - len(unique_documents)
        if removed_count > 0:
            logger.info("🔄 Removed %d duplicate documents", removed_count)
        
        return unique_documents
    
    async def _load_documents_from_directory(
        self,
        directory_path: str,
        extensions: List[str]
    ) -> List[Document]:
        """
        Load documents from directory.
        
        Args:
            directory_path: Path to directory
            extensions: File extensions to load
            
        Returns:
            List[Document]: Loaded documents
        """
        documents = []
        
        # Currently only supporting PDF files like existing pipeline
        if ".pdf" in extensions:
            loader = PyPDFDirectoryLoader(directory_path, recursive=True)
            pdf_documents = loader.load()
            documents.extend(pdf_documents)
            logger.info("📄 Loaded %d PDF documents", len(pdf_documents))
        
        return documents
    
    async def _split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: Documents to split
            
        Returns:
            List[Document]: Document chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info("✂️ Split documents into %d chunks", len(chunks))
        
        return chunks
